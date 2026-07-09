# Rules (always-on baseline)

Tiếng Việt: [../vi/rules.md](../vi/rules.md) | Back to [README](../../README.md)

These rules are injected into every session by the `SessionStart` hook, generated from `canonical/conventions.json`. To change any of them, edit that file and cut a release (see [Releasing](releasing.md)).

## Working principles

- Think first; state assumptions. Never assume silently: on any concern (security, data loss, breaking change, unclear scope, irreversible operation), stop and ask, and always ask with a recommendation.
- KISS, not over-engineering: minimum code that solves the problem; no speculative features or single-use abstractions.
- Think deep, ship simple: reason through the full complexity, then deliver the simplest correct solution; depth of thinking must not leak into the output.
- Surgical: change only what the request needs; note adjacent issues, do not fix them silently.
- Verifiable success: define a concrete check per step before starting.
- Honest reporting: if the build or tests fail, say so with the output; never fabricate results.
- Reversible-first: irreversible or outward-facing actions need confirmation; never overwrite or delete a file you did not create without surfacing it.

## Communication

- Lead with the answer; keep responses short, clear, skimmable; no rambling.
- Cite references for factual claims (`file:line`, Confluence page id, URL).

## Runtime versions (per project)

- Java (21 or 25 LTS) and Spring Boot (3 or 4) vary by project. Detect the target from build files and follow that version's rules. Never use a feature or API newer than the project's declared version; if a newer one would help, flag and ask.
- Spring Boot 4: Jakarta EE 11 / Servlet 6.1 / Jackson 3, minimum Java 21, all Boot-3 deprecations removed, Undertow and JUnit 4 dropped. Spring Boot 3: Jakarta EE 9-10 (`jakarta.*`), Java 17+.
- Details and the upgrade path: the `runtime-stack` skill (see [Reference](reference.md)).

## Java and Spring conventions

- Google Java Style (Checkstyle enforced). Lombok is allowed. No `var` in new or modified code - use explicit types.
- Currency is `BigDecimal`, never `double` or `float`.
- Constructor injection only; no `@Autowired` field injection.
- Config is externalized (`${ENV_VAR:default}`), never hardcoded. Secrets go through env or a secret manager.

## Response envelope (by cluster)

- `fsap-*` repos use `com.finx.common.fsap.pojo.FsapApiResponse` and the shared `common.fsap` helpers (controller advice, header context, JWT).
- Non-fsap repos use `com.finx.spring.service.api.ResponseApi`. Do not define a new local `ResponseApi`.

## Errors and logging

- Error codes use the `ErrorCode` enum in `DOMAIN.CODE` format (e.g. `PAYMENT.INSUFFICIENT_FUNDS`); no free-form strings. Business-rule violations map to 4xx (422/429), not 500.
- "Log once, handle once" at the `GlobalExceptionHandler`.
- Logging is SLF4J parameterized, DEBUG by default. Never log PII, secrets, OTP, tokens, card or full account numbers - mask sensitive identifiers. Do not log full objects or collections. Never log-and-throw.

## API versioning

- Every endpoint carries a major version in the path: `/{resource}/v{N}/...`; internal is `/{resource}/v{N}/internal/...`.
- No DTO sharing across versions. A breaking change means a new major version.

## Banking domain

- Balance changes go through the ledger; never mutate balances directly.
- Every mutating or external operation needs an idempotency key and must be safe to retry. Distributed transactions use saga/outbox.
- OTP / SBV: block after N failures and audit every attempt.

## Cross-repo operations (non-prod; prod is a separate release)

- DB migrations go to `non-prod-liquibase` (strict changeset format; rollback required; `make lint`).
- An important env var (a secret, an external endpoint, or a flag that changes production behavior) requires confirmation, then goes into `non-prod-application-workload`.
- New Kafka topics go to `non-prod-kafka-gitops`.
- Public (mobile/partner) APIs are registered in `non-prod-apigw-configs` and `non-prod-openapi-configs`.

## Architecture decisions

- Significant choices (hexagonal vs onion vs layered, module/bounded-context boundaries, sync vs event-driven, saga vs 2PC, share vs duplicate) must be raised with the user, with trade-offs and a recommendation - never picked silently.
- Default recommendation for a new service: multi-module hexagonal, matching the existing fleet; deviate only with a stated reason.

## Discipline

- `@Transactional` at the service layer, scope minimal. Reuse `common-libs` / `common.fsap` before writing local equivalents.
