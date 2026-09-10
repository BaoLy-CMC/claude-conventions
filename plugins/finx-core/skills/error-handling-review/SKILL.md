---
name: error-handling-review
description: Use when writing or reviewing exceptions, error codes, HTTP status mapping, a GlobalExceptionHandler, or response envelopes, or when asked to "check error handling" before a PR.
---

# Error Handling Review

Review the target Java files (default: uncommitted diff; else the files named) against the FinX error-handling standards and report violations. **Report only — do not rewrite unless asked.**

## How to run

1. Scope: changed `*.java` (controllers, services, exception classes, `*ExceptionHandler`, `*ControllerAdvice`).
2. Identify the repo cluster to apply the right envelope rule (see check 4):
   - `fsap-*` repo → `com.finx.common.fsap.pojo.FsapApiResponse`
   - non-fsap repo → `com.finx.spring.service.api.ResponseApi`
3. First-pass greps, then confirm by reading:

```bash
rg -n 'throw new \w+Exception\("' <files>                      # free-form message — check for error CODE, not just text
rg -n 'HttpStatus\.(INTERNAL_SERVER_ERROR|BAD_REQUEST)' <files> # candidate wrong mapping (OTP block/amount limit → 429/422)
rg -n 'log\.(error|warn).*;\s*throw' <files>                    # candidate log-and-throw
rg -n 'class \w*ResponseApi|record \w*ResponseApi' <files>      # new local envelope (forbidden)
rg -n '@RestControllerAdvice|@ExceptionHandler' <files>         # ad-hoc advice vs shared handler
```

## Checklist (report each violation with file:line)

| # | Rule |
|---|---|
| 1 | Error codes use the `ErrorCode` enum in `DOMAIN.CODE` format (e.g. `PAYMENT.INSUFFICIENT_FUNDS`) — no free-form strings like `"Transaction duplicated"` |
| 2 | HTTP mapping correct: business rule → **422**; duplicate/idempotency/version conflict → **409**; OTP/KYC/approval required → **428**; validation only → **400**; unauthenticated → **401**; missing functional permission → **403**; not-found → **404**; rate limit → **429** + `Retry-After`; a bug in this service → **500**; dependency down → **503**. A business rule must never be 400 or 500; OTP is 428, not 429. Detail: `api-response-standards` |
| 3 | "Log once, handle once": service layer **throws**, does not log; `GlobalExceptionHandler` (single boundary) logs + translates. Kafka consumers log + route to DLQ at the consumer boundary. |
| 4 | Response envelope matches the repo cluster (fsap vs non-fsap, see step 2). No new local `ResponseApi` definition. |
| 5 | Exceptions extend the shared hierarchy (`FsapException`/`common.fsap` for fsap; the project's base for non-fsap) — not bare `RuntimeException` with no code |
| 6 | Error meta includes `traceId`, `timestamp`, `retryable` where the envelope supports it |
| 7 | No stack trace / debug info returned to the client (custom error response only) |
| 8 | Retryable/transient downstream failures flagged `retryable=true`; wrapped with original cause on re-throw |
| 9 | Downstream on a money path branches on whether a side effect can have happened: nothing sent → **503** (safe retry); sent then timeout/unknown → **200 + `PROCESSING`/`UNKNOWN`** + transaction id + poll endpoint, intent persisted first. Never FAILURE while unknown, never a 5xx that invites an automatic retry |
| 10 | Log level pairs with the status: 4xx → `WARN`, 5xx → `ERROR` with the exception as the last argument (see `logging-review`) |
| 11 | Mutating/external call carries an idempotency key, deduped by a real unique key/constraint (not best-effort). Same key + same payload replays the first response; same key + different payload → 409 `IDEMPOTENCY_KEY_CONFLICT`; missing key → 400 |
| 12 | Empty result answers **200 + `[]`/`null`**, never 404 for a collection. Another user's resource answers **404/empty, never 403** (id enumeration) |
| 13 | Every `status.code` comes from the central catalog enum — no new hardcoded string |

## Output format

```
error-handling-review — <N> findings
CRITICAL  file:line  [rule 7] stack trace exposed in response body
HIGH      file:line  [rule 2] OTP_BLOCKED mapped to 500 → should be 429
HIGH      file:line  [rule 1] free-form throw new RuntimeException("dup") → ErrorCode.PAYMENT.DUPLICATE_TRANSACTION
MEDIUM    file:line  [rule 4] non-fsap repo defines local ResponseApi → use com.finx.spring.service.api.ResponseApi
```
Severity: client-facing stack trace / wrong-cluster envelope = CRITICAL/HIGH; wrong HTTP status or free-form code = HIGH; missing meta fields = MEDIUM. If clean, say so.
