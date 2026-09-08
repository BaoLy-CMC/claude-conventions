---
name: api-response-standards
description: Apply the FinX API request/response contract — the status/payload/meta envelope, the ARB HTTP-status mapping (422 business, 409 conflict, 428 action required), empty vs not-found, idempotency and retry on money paths, downstream-timeout handling, partial batches, async jobs, and W3C trace propagation. Use when writing or reviewing a controller, a response DTO, a GlobalExceptionHandler, an idempotency key, a money-movement endpoint, or when choosing between 400/422/428/409/503/504. Source: Confluence EN/1881178169 + EN/1896415349.
---

# API Response Standards

The contract every FinX HTTP endpoint answers to. **HTTP status is the transport verdict; `status.code` is the business verdict.** A refused business rule is a valid answer to a valid request, not a system failure.

## Envelope

Exactly three top-level blocks, always present:

```json
{
  "status": { "code": "SUCCESS", "message": "", "errors": [] },
  "payload": { },
  "meta":   { "requestId": null, "nextCursor": null }
}
```

| Field | Rule |
|---|---|
| `status.code` | Business result. From the central catalog enum only — never a new hardcoded string. |
| `status.message` | Human-readable. Empty (`""`) on success. Never leaks stack traces, table names, internal service names, or another customer's data. |
| `status.errors[]` | Per-field detail (`field`, `code`, `message`). Only when `code != SUCCESS`. |
| `payload` | Object for one item, array for a collection, `null` on failure. |
| `meta.requestId` | Server-generated trace id, echoed from the incoming header. Reuse the W3C `trace-id`. |
| `meta.nextCursor` | Opaque pagination cursor — never an internal DB id. `null` on the last page. |

Do not define a new envelope: the cluster's shared type carries this shape (`FsapApiResponse` for `fsap-*`, `ResponseApi` otherwise).

## HTTP status (ARB decision, 2026-08)

| Situation | HTTP | `status.code` |
|---|---|---|
| Success / accepted-and-processing / empty | 200 | `SUCCESS`, `PENDING`, `PROCESSING` |
| Business rule refused (balance, limit, locked account) | **422** | the specific business code |
| Duplicate transaction, idempotency-key or version conflict | **409** | `DUPLICATE_TRANSACTION`, `IDEMPOTENCY_KEY_CONFLICT` |
| Extra step required (OTP / KYC / approval) | **428** | `OTP_REQUIRED`, `KYC_REQUIRED`, `APPROVAL_REQUIRED` |
| Validation only — wrong format, missing field, bad enum | 400 | `FAILURE` + `errors[]` |
| No / invalid / expired token | 401 | `FAILURE` |
| Authenticated but missing a *functional* permission | 403 | `FAILURE` |
| Rate limit / throttling | 429 + `Retry-After` | `FAILURE` |
| Our own bug (NPE, unexpected exception) | 500 | `FAILURE` |
| A dependency is down (Aurora/Redis/Kafka/partner 5xx) | 503 | `FAILURE` |

Hard rules: a business rule never answers 400 or 500. `400` only exists at the validation layer, before the service is reached. `500` only comes from the global exception handler — never thrown deliberately for a business outcome. `429` is rate limiting only; OTP is `428`.

## Empty, not-found, and id enumeration

- Empty is a correct result: **200 + `[]` / `null`**. Never 404 for a collection.
- 404 is only for a direct single-resource lookup whose id does not exist.
- A user reaching **another user's** resource gets **404 / empty, never 403** — 403 would confirm the resource exists. 403 stays for missing functional permissions (e.g. no admin role).
- "No rows" and "filtered out by permission" both return `[]`. Do not distinguish them.

## Money movement: idempotency and retry

Every transaction-creating endpoint (transfer, payment, top-up, withdrawal) requires an idempotency key. The server stores key + first result.

| Retry | HTTP | `status.code` | Behaviour |
|---|---|---|---|
| Same key, same payload | 200 | `SUCCESS` (replay) | Return the **first** result. Never create a second transaction, never answer FAILURE/DUPLICATE. |
| Same key, different payload | 409 | `IDEMPOTENCY_KEY_CONFLICT` | Reject. |
| Key missing on an endpoint that requires it | 400 | `FAILURE` | Missing mandatory header. |

## Downstream calls on a money path

Branch on **whether a side effect can already have happened** — not on whether the call timed out:

| Case | Answer | Client |
|---|---|---|
| Nothing can have happened — connection refused, circuit open, rejected before send | **503** | Safe to retry the create. |
| Something may have happened — request sent, then timeout / connection lost / unknown | **200 + `PROCESSING` or `UNKNOWN` + the transaction id** | Poll the status endpoint. **Never** resend the create. |
| Downstream answered with a definite failure | 200 + `FAILURE` | Safe to send a new command. |

Two preconditions: persist the intent **before** calling downstream (outbox), and run a reconciliation job. Never answer `FAILURE` while the downstream state is unknown, and do not use 5xx for it — gateways, mobile SDKs and retry middleware treat 5xx as retryable, which is exactly the double-charge this rule prevents.

## Batches and async

- Partial batch: HTTP 200, `status.code = PARTIAL`, per-item result **and reason** in the payload. Never one shared `FAILURE` for a partly successful batch.
- Long-running work: `POST` returns **202** + `jobId` + `state`, with a separate `GET /jobs/{jobId}` that always answers 200 (`QUEUED → PROCESSING → COMPLETED/FAILED`). Do not hold the connection.

## Tracing (W3C Trace Context)

- `traceparent` is mandatory service-to-service; `tracestate` is optional. `trace-id` (32 hex) and `parent-id` (16 hex) must be **lowercase**.
- Propagate to **every** outgoing call: other services, Kafka publishes, partner APIs. Mutate `parent-id` for a child span; keep `trace-id`.
- External caller without `traceparent` → the gateway generates one.
- If `traceparent` fails to parse, do not parse `tracestate`. When editing `tracestate`, the `finx` entry goes first.
- Check Istio / LB / CDN do not strip the header — the usual cause of a trace breaking at a service edge.

## Review checklist

```
api-response-standards — <N> findings
CRITICAL  file:line  business rule answered with 500 → 422 + business status.code
CRITICAL  file:line  FAILURE returned on downstream timeout → 200 + PROCESSING + poll endpoint
HIGH      file:line  403 for another user's resource → 404/empty (id enumeration)
HIGH      file:line  404 returned for an empty collection → 200 + []
HIGH      file:line  OTP_REQUIRED mapped to 429 → 428
MEDIUM    file:line  hardcoded status.code string → central catalog enum
MEDIUM    file:line  traceparent not propagated to the Kafka producer
```

Severity: anything that can double-charge or leak data = CRITICAL; wrong status class = HIGH; envelope/format drift = MEDIUM.

**Known doc inconsistency (2026-09):** EN/1881178169 §9 tabulates downstream timeout as `504 CLIENT_TIMEOUT` while its own prose and the §17 PR checklist say 200 + `PROCESSING`/`UNKNOWN`; the child catalog EN/1896415349 still maps every business code to HTTP 200, predating the ARB decision by two days. This skill follows the newer ARB parent page and the never-FAILURE invariant both agree on.
