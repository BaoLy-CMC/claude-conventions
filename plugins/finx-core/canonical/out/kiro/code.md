# Code Convention — FinX Steering

Product: FinX / Vikki banking platform (SBV-compliant). Stack: Java 21 + Spring Boot microservices. Source: Confluence space EN (Engineering).

> Generated from the FinX canonical convention source. Do not hand-edit.

## Working principles & guardrails
- Think first — state your assumptions explicitly before acting. NEVER assume silently: if a requirement is ambiguous, or you hit a concern (security, data loss, breaking change, unclear scope, irreversible op), STOP and ask immediately — and always ask WITH a recommendation, not an open question.
- Best practice, not over-engineering (KISS) — write the minimum code that correctly solves the problem. No speculative features, no abstraction for a single use, no flexibility nobody asked for. If 50 lines do the job, don't write 200.
- Think deep, ship simple — reason through the full complexity of the problem (edge cases, trade-offs, failure modes, second-order effects) before deciding, then deliver the simplest solution that is still correct. Depth of thinking must NOT leak into complexity of the output.
- Surgical — change only what the request needs. Match surrounding style. Note adjacent issues, never fix them silently (unintended changes create review burden).
- Verifiable success — define a concrete check per step before starting; loop until it passes. Weak criteria ("make it work") → clarify before starting.
- Honest reporting — if the build/tests fail, say so with the output; if a step was skipped, say that. Never claim success you did not verify; never fabricate results.
- Reversible-first — hard-to-reverse or outward-facing actions (delete/overwrite, push, external calls, prod-facing changes, DB migration) need confirmation first. Never overwrite or delete a file you did not create without surfacing what it is.

## Non-negotiable
- Google Java Style (Checkstyle enforced). Lombok allowed. No `var` in new/modified code — explicit types.
- Currency: BigDecimal, never double/float.
- Constructor injection only — no @Autowired field injection.
- Config externalised — ${ENV_VAR:default} in yml, never hardcoded (URLs, timeouts, limits, topics, flags). Secrets via env/secret-manager, never committed.

## Response envelope (by cluster)
- Repo fsap-* -> com.finx.common.fsap.pojo.FsapApiResponse (+ common.fsap exception/advice/header/JWT helpers).
- Repo non-fsap -> com.finx.spring.service.api.ResponseApi. Do not define a new local ResponseApi.

## Errors & logging
- Error codes: ErrorCode enum, DOMAIN.CODE format. Business rule -> 4xx (422/429), not 500. Log once, handle once at GlobalExceptionHandler.
- Logging: SLF4J parameterised, DEBUG-by-default. Never log PII/secrets/OTP/tokens/card/account — mask() them. No full objects/collections. Never log-and-throw.

## API
- Every endpoint versioned in path: /{resource}/v{N}/...; internal = /v{N}/internal/.... No DTO sharing across versions. Breaking change -> new major version.

## Banking domain
- Balance changes go through the ledger — never mutate balances directly.
- Every mutating/external op needs an idempotency key (safe to retry). Distributed tx -> saga/outbox.
- OTP/SBV: block after N failures, audit every attempt.

## Architecture decisions (ask, don't assume)
- For significant architecture choices — hexagonal vs onion vs layered, module/bounded-context boundaries, sync vs event-driven, saga vs 2PC, share vs duplicate — STOP and ASK the user first. Present the trade-offs and a clear recommendation; never silently pick.
- Default recommendation for a new service: multi-module hexagonal (common/core/application/infra/api), matching the existing fleet — deviate only with an explicit, stated reason.

## Discipline
- Surgical — change only what the request needs; note adjacent issues, don't fix them. @Transactional at service layer, scope minimal. Reuse common-libs / common.fsap before writing local equivalents.
