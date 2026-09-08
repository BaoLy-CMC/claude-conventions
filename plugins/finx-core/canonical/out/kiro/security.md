# Security Policies — FinX Steering

Product: FinX / Vikki banking platform (SBV-compliant). Stack: Java 21 or 25 (LTS) + Spring Boot 3 or 4 microservices, per project. Source: Confluence space EN (Engineering).

> Generated from the FinX canonical convention source. Do not hand-edit.

## Errors & logging
- Error codes: ErrorCode enum, DOMAIN.CODE format; every status.code value comes from the central catalog (extended by PR) — no hardcoded strings. Business rule -> 4xx, never 500. Log once, handle once at GlobalExceptionHandler.
- Logging: SLF4J parameterised, DEBUG-by-default. Never log PII/secrets/OTP/tokens/card/account — mask() them. No full objects/collections. Never log-and-throw.
- Log level mirrors the response: 4xx business error -> WARN (never ERROR/5xx for a business rule such as a wrong OTP or an insufficient balance); 5xx system failure -> ERROR with the exception as the last argument so the stack trace is kept. FATAL is banned.
- INFO only for: service lifecycle, business milestone, cronjob summary, kafka consumer, important state change — everything else DEBUG. Message format: `<Action description>. [key1={}, key2={}]` in English. No string concatenation, no duplicate log of the same event (log once at the service boundary), no empty catch.

## API contract (ARB decision, 2026-08)
- Response envelope: exactly three top-level blocks — status{code,message,errors} / payload / meta{requestId,nextCursor}. Success carries an empty message; a failure carries the message plus per-field errors and a null payload. Source: Confluence EN/1881178169.
- HTTP status is the transport verdict, status.code the business one: business rule refused -> 422; duplicate / idempotency / version conflict -> 409; an extra step is needed (OTP/KYC/approval) -> 428; validation only -> 400; unauthenticated -> 401; missing functional permission -> 403; rate limit -> 429 + Retry-After; our own bug -> 500; a dependency is down -> 503. Never answer a business rule with 400 or 500.
- An empty result is success: 200 with [] or null — never 404 for a collection. A user reaching another user's resource gets 404/empty, never 403, so ids cannot be enumerated.
- Money movement: the create endpoint requires an idempotency key. Same key + same payload -> replay the first response, never a second transaction; same key + different payload -> 409 IDEMPOTENCY_KEY_CONFLICT; missing key -> 400. Batch -> 200 + PARTIAL with a per-item result and reason; async -> 202 + jobId plus a poll endpoint that always answers 200.
- Downstream call on a money path — branch on whether a side effect can already have happened, not on whether it timed out. Nothing can have happened (connection refused, rejected before send, circuit open) -> 503, safe for the client to retry. Something may have happened (request sent, then timeout or unknown) -> persist the intent first, answer 200 with PROCESSING/UNKNOWN + the transaction id, and make the client poll the status endpoint; never FAILURE, never let the client resend the create. Reconcile asynchronously.
- Tracing: W3C traceparent (tracestate optional), lowercase hex, propagated to every outgoing call including Kafka publishes and partner APIs; the gateway generates one when an external caller omits it; reuse trace-id as meta.requestId. amount is BigDecimal, timestamps are ISO 8601 UTC, meta.nextCursor is opaque, and status.message never leaks internals.

## Banking domain
- Balance changes go through the ledger — never mutate balances directly.
- Every mutating/external op needs an idempotency key (safe to retry). Distributed tx -> saga/outbox. Dedup is enforced by a real key/unique constraint, never best-effort — state the mechanism in the plan's trade-offs.
- OTP/SBV: block after N failures, audit every attempt.
