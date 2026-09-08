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

- Google Java Style (Checkstyle enforced). Lombok is allowed - use it where it removes real boilerplate (`@RequiredArgsConstructor` for constructor injection, `@Getter`, `@Builder`, `@Slf4j`); never `@Data` on a JPA entity. No `var` in new or modified code - use explicit types.
- Currency is `BigDecimal`, never `double` or `float`.
- Constructor injection only; no `@Autowired` field injection.
- Config is externalized (`${ENV_VAR:default}`), never hardcoded. Secrets go through env or a secret manager.

## Response envelope (by cluster)

- `fsap-*` repos use `com.finx.common.fsap.pojo.FsapApiResponse` and the shared `common.fsap` helpers (controller advice, header context, JWT).
- Non-fsap repos use `com.finx.spring.service.api.ResponseApi`. Do not define a new local `ResponseApi`.

## Errors and logging

- Error codes use the `ErrorCode` enum in `DOMAIN.CODE` format (e.g. `PAYMENT.INSUFFICIENT_FUNDS`); every `status.code` value comes from the central catalog, extended by PR - no free-form strings. Business-rule violations map to 4xx, never 500.
- "Log once, handle once" at the `GlobalExceptionHandler`.
- Logging is SLF4J parameterized, DEBUG by default. Never log PII, secrets, OTP, tokens, card or full account numbers - mask sensitive identifiers. Do not log full objects or collections. Never log-and-throw.
- The level mirrors the response: a business error answered with 4xx logs `WARN` (never `ERROR`); a system failure answered with 5xx logs `ERROR` with the exception as the last argument, so the stack trace survives. `FATAL` is banned.
- `INFO` is only for service lifecycle, a business milestone, a cronjob summary, a kafka consumer, or an important state change; everything else is `DEBUG`. Message format is `<Action description>. [key1={}, key2={}]` in English: no string concatenation, no duplicate log of the same event (log once at the service boundary), no empty catch.

## API versioning

- Every endpoint carries a major version in the path: `/{resource}/v{N}/...`; internal is `/{resource}/v{N}/internal/...`.
- No DTO sharing across versions. A breaking change means a new major version.
- The package layout mirrors the URL version (`controller/v{N}/`, `dto/v{N}/`); a `v{N}` controller imports only `v{N}` DTOs.
- A deprecated endpoint emits `Deprecation` and `Sunset` headers on every response and returns 410 at sunset; notice is at least 6 months for external APIs, 3 months for internal ones.
- Every endpoint registers a static `x-api-id` (`X##`: module letter + 2-digit sequence) in `internal-apis.yaml`.

## API contract (ARB decision, 2026-08)

- Response envelope: exactly three top-level blocks - `status{code,message,errors}` / `payload` / `meta{requestId,nextCursor}`. Success carries an empty message; a failure carries the message, per-field errors, and a null payload.
- HTTP status is the transport verdict, `status.code` the business one: business rule refused 422; duplicate/idempotency/version conflict 409; extra step needed (OTP/KYC/approval) 428; validation only 400; unauthenticated 401; missing functional permission 403; rate limit 429 with `Retry-After`; our own bug 500; dependency down 503. A business rule is never 400 or 500.
- An empty result is success: 200 with `[]` or `null`, never 404 for a collection. A user reaching another user's resource gets 404/empty, never 403, so ids cannot be enumerated.
- Money movement: the create endpoint requires an idempotency key. Same key and payload replays the first response; same key with a different payload returns 409; a missing key returns 400. Partial batch: 200 + `PARTIAL` with a per-item reason. Async: 202 + `jobId` plus a poll endpoint.
- Downstream call on a money path: branch on whether a side effect can have happened, not on whether it timed out. Nothing sent - 503, safe to retry. Sent then timeout or unknown - persist the intent, answer 200 with `PROCESSING`/`UNKNOWN` and the transaction id, and have the client poll; never `FAILURE`, never resend the create.
- Tracing: W3C `traceparent` (lowercase hex) propagated to every outgoing call including Kafka publishes and partner APIs; the gateway generates one when an external caller omits it; `trace-id` is reused as `meta.requestId`. Amounts are `BigDecimal`, timestamps ISO 8601 UTC, `nextCursor` opaque, and `status.message` never leaks internals.
- Details and the PR checklist: the `api-response-standards` skill.

## Banking domain

- Balance changes go through the ledger; never mutate balances directly.
- Every mutating or external operation needs an idempotency key and must be safe to retry. Distributed transactions use saga/outbox. Dedup is enforced by a real key or unique constraint, never best-effort - state the mechanism in the plan's trade-offs.
- A downstream timeout on a money path never returns FAILURE (a client retry would double-charge); return pending/unknown and reconcile.
- OTP / SBV: block after N failures and audit every attempt.

## Concurrency and transactions

- Spring beans are stateless by default. Identify the shared mutable state before touching it, then guard it explicitly (`synchronized`, `ReentrantLock`, `java.util.concurrent`).
- `@Transactional` at the service layer, propagation `REQUIRED` by default; `REQUIRES_NEW` only when isolation is genuinely required. Never hold a lock (DB row or in-process) across a network call.

## Memory and data access

- No allocation above 512KB on a hot path. Never keep a large collection in an instance field of a Spring bean.
- Always paginate; never load a full table or an unbounded result set into memory.
- Every table has an explicit `BIGSERIAL`/`SERIAL` primary key; a UUID is only an extra column with a secondary index. No foreign keys in the database - keep consistency in application logic.
- Every query carries its own timeout on top of the global query and connection timeouts, and connections go through a pool (client-side or pgBouncer).

## Common libs (strict routing)

- Each cluster uses its own lib and never another cluster's: vikki uses `finx/vikki/common-libs` (`com.finx.common-libs`); fsap uses `finx/fsap/fsap-common-libs` (`com.finx.fsap`); bff/galaxy-g lives in the fsap repo (`com.finx.galaxyg`).
- grep the repo and the cluster lib before writing any new util.

## Comments

- The default is no comment; naming carries the meaning. Comment only to explain *why* (a workaround, an unusual business rule), in one short line.
- Never comment *what* the code does. Delete a redundant comment when you are already editing that code.

## Cross-repo operations (non-prod; prod is a separate release)

- DB migrations go to `non-prod-liquibase` (strict changeset format; rollback required; `make lint`).
- An important env var (a secret, an external endpoint, or a flag that changes production behavior) requires confirmation, then goes into `non-prod-application-workload`.
- New Kafka topics go to `non-prod-kafka-gitops`.
- Public (mobile/partner) APIs are registered in `non-prod-apigw-configs` and `non-prod-openapi-configs`.

## Commits and PRs

- Branch: `<type>/<JIRA-KEY>-<short-description>` (e.g. `feat/VRHE-66-user-authentication`); deployment branch: `release/<YYYY-MM-DD>-<short-description>`. Source: Confluence EN/514556795.
- Commit: `<type>(<optional scope>): <description>` - imperative present tense, lowercase first letter, no trailing dot. A `!` before the colon marks a breaking change; issue ids belong in the body, never as the scope. Types: feat, fix, refactor, perf, style, test, docs, build, cicd, ops, chore. Repos that additionally prefix the subject with `[JIRA-KEY]` keep one key per commit and never guess a key. No attribution trailers.
- PR description length is proportional to the diff: What & Why (1-2 sentences), Notes (non-obvious decisions, breaking changes, deploy order, deliberate omissions), Verification (the commands actually run and their real results; if untested, say so). No file lists, no copied commit log, no emoji, no fake checklists.

## Architecture decisions

- Significant choices (hexagonal vs onion vs layered, module/bounded-context boundaries, sync vs event-driven, saga vs 2PC, share vs duplicate) must be raised with the user, with trade-offs and a recommendation - never picked silently.
- Default recommendation for a new service: multi-module hexagonal, matching the existing fleet; deviate only with a stated reason.
- Every design decision - library choice, data model, retry strategy - comes with explicit pros and cons, never a bare verdict.

## Discipline

- `@Transactional` at the service layer, scope minimal. Reuse `common-libs` / `common.fsap` before writing local equivalents.
- No code before an approved plan for anything non-trivial - run the `flow` skill (explore -> plan -> execute -> review).
