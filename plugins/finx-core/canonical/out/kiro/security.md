# Security Policies — FinX Steering

Product: FinX / Vikki banking platform (SBV-compliant). Stack: Java 21 + Spring Boot microservices. Source: Confluence space EN (Engineering).

> Generated from the FinX canonical convention source. Do not hand-edit.

## Errors & logging
- Error codes: ErrorCode enum, DOMAIN.CODE format. Business rule -> 4xx (422/429), not 500. Log once, handle once at GlobalExceptionHandler.
- Logging: SLF4J parameterised, DEBUG-by-default. Never log PII/secrets/OTP/tokens/card/account — mask() them. No full objects/collections. Never log-and-throw.

## Banking domain
- Balance changes go through the ledger — never mutate balances directly.
- Every mutating/external op needs an idempotency key (safe to retry). Distributed tx -> saga/outbox.
- OTP/SBV: block after N failures, audit every attempt.
