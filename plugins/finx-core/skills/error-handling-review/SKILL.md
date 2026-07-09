---
name: error-handling-review
description: Review Java/Spring Boot error handling against the FinX error-handling & exception standards. Use when reviewing or writing exceptions, error codes, HTTP status mapping, GlobalExceptionHandler, or API response envelopes, or when asked to "check error handling" before a PR. Checks ErrorCode DOMAIN.CODE enum usage, correct HTTP status (business→4xx not 500), log-once-handle-once, and cluster-correct response envelope. Source: Confluence EN/1448247327 (Backend - Error handling & exception standards).
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
| 2 | HTTP mapping correct: business-rule violation → **422**; rate-limit/OTP block → **429**; not-found → **404**; conflict/duplicate → **409**; only infra/unexpected → **500**. (OTP block, amount-limit must NOT be 500.) |
| 3 | "Log once, handle once": service layer **throws**, does not log; `GlobalExceptionHandler` (single boundary) logs + translates. Kafka consumers log + route to DLQ at the consumer boundary. |
| 4 | Response envelope matches the repo cluster (fsap vs non-fsap, see step 2). No new local `ResponseApi` definition. |
| 5 | Exceptions extend the shared hierarchy (`FsapException`/`common.fsap` for fsap; the project's base for non-fsap) — not bare `RuntimeException` with no code |
| 6 | Error meta includes `traceId`, `timestamp`, `retryable` where the envelope supports it |
| 7 | No stack trace / debug info returned to the client (custom error response only) |
| 8 | Retryable/transient downstream failures flagged `retryable=true`; wrapped with original cause on re-throw |

## Output format

```
error-handling-review — <N> findings
CRITICAL  file:line  [rule 7] stack trace exposed in response body
HIGH      file:line  [rule 2] OTP_BLOCKED mapped to 500 → should be 429
HIGH      file:line  [rule 1] free-form throw new RuntimeException("dup") → ErrorCode.PAYMENT.DUPLICATE_TRANSACTION
MEDIUM    file:line  [rule 4] non-fsap repo defines local ResponseApi → use com.finx.spring.service.api.ResponseApi
```
Severity: client-facing stack trace / wrong-cluster envelope = CRITICAL/HIGH; wrong HTTP status or free-form code = HIGH; missing meta fields = MEDIUM. If clean, say so.
