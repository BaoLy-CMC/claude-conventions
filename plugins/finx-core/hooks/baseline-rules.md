# FinX Backend Conventions — always-on baseline

Applies to new/modified code in FinX / Vikki banking platform (SBV-compliant) (Java 21 or 25 (LTS) + Spring Boot 3 or 4 microservices, per project). Source of truth: Confluence space EN (Engineering). For detail, the `finx-core` plugin skills load on demand.

> Generated from `canonical/conventions.json` — edit there, then run `canonical/generate.py`. Do not hand-edit.

## Working principles & guardrails
- Think first — state your assumptions explicitly before acting. NEVER assume silently: if a requirement is ambiguous, or you hit a concern (security, data loss, breaking change, unclear scope, irreversible op), STOP and ask immediately — and always ask WITH a recommendation, not an open question.
- Best practice, not over-engineering (KISS) — write the minimum code that correctly solves the problem. No speculative features, no abstraction for a single use, no flexibility nobody asked for. If 50 lines do the job, don't write 200.
- Think deep, ship simple — reason through the full complexity of the problem (edge cases, trade-offs, failure modes, second-order effects) before deciding, then deliver the simplest solution that is still correct. Depth of thinking must NOT leak into complexity of the output.
- Surgical — change only what the request needs. Match surrounding style. Note adjacent issues, never fix them silently (unintended changes create review burden).
- Verifiable success — define a concrete check per step before starting; loop until it passes. Weak criteria ("make it work") → clarify before starting.
- Honest reporting — if the build/tests fail, say so with the output; if a step was skipped, say that. Never claim success you did not verify; never fabricate results.
- Reversible-first — hard-to-reverse or outward-facing actions (delete/overwrite, push, external calls, prod-facing changes, DB migration) need confirmation first. Never overwrite or delete a file you did not create without surfacing what it is.

## Communication style
- Lead with the answer. Keep responses short, clear, and skimmable — no rambling, no restating what is already settled, no narrating options you won't take.
- Cite references for factual claims — `file:line`, Confluence page id, or doc URL — so the reader can verify, not just trust.

## Non-negotiable
- Google Java Style (Checkstyle enforced). Lombok allowed. No `var` in new/modified code — explicit types.
- Currency: BigDecimal, never double/float.
- Constructor injection only — no @Autowired field injection.
- Config externalised — ${ENV_VAR:default} in yml, never hardcoded (URLs, timeouts, limits, topics, flags). Secrets via env/secret-manager, never committed.

## Runtime versions (per project)
- Java (21 or 25 LTS) and Spring Boot (3 or 4) vary by project. DETECT the target from the build files (Gradle toolchain / `libs.versions.toml` / Maven `java.version` + the spring-boot plugin/parent version) and follow that version's rules. Never use a language feature or API newer than the project's declared version; if a newer feature would help, flag it and ask.
- Spring Boot 4 = Jakarta EE 11 / Servlet 6.1 / Jackson 3, minimum Java 21, all Boot-3 deprecations removed, Undertow/JUnit4 dropped. Spring Boot 3 = Jakarta EE 9-10 (`jakarta.*`), Java 17+. Use the `runtime-stack` skill for the per-version do/don't.

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

## Cross-repo operations (NON-PROD only; prod = separate release)
- DB migration -> non-prod-liquibase (strict changeset format; rollback required; make lint).
- Important env (secret, external endpoint, prod-behavior flag) -> ASK & CONFIRM first, then non-prod-application-workload.
- New Kafka topic -> non-prod-kafka-gitops.
- Public API (mobile/partner) -> register in non-prod-apigw-configs + non-prod-openapi-configs.

## Architecture decisions (ask, don't assume)
- For significant architecture choices — hexagonal vs onion vs layered, module/bounded-context boundaries, sync vs event-driven, saga vs 2PC, share vs duplicate — STOP and ASK the user first. Present the trade-offs and a clear recommendation; never silently pick.
- Default recommendation for a new service: multi-module hexagonal (common/core/application/infra/api), matching the existing fleet — deviate only with an explicit, stated reason.

## Discipline
- Surgical — change only what the request needs; note adjacent issues, don't fix them. @Transactional at service layer, scope minimal. Reuse common-libs / common.fsap before writing local equivalents.
