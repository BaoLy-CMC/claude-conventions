# Code Convention — FinX Steering

Product: FinX / Vikki banking platform (SBV-compliant). Stack: Java 21 or 25 (LTS) + Spring Boot 3 or 4 microservices, per project. Source: Confluence space EN (Engineering).

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
- Google Java Style (Checkstyle enforced). Lombok is allowed — use it where it removes real boilerplate (@RequiredArgsConstructor for constructor injection, @Getter, @Builder, @Slf4j); never @Data on a JPA entity. No `var` in new/modified code — explicit types.
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
- Error codes: ErrorCode enum, DOMAIN.CODE format; every status.code value comes from the central catalog (extended by PR) — no hardcoded strings. Business rule -> 4xx, never 500. Log once, handle once at GlobalExceptionHandler.
- Logging: SLF4J parameterised, DEBUG-by-default. Never log PII/secrets/OTP/tokens/card/account — mask() them. No full objects/collections. Never log-and-throw.
- Log level mirrors the response: 4xx business error -> WARN (never ERROR/5xx for a business rule such as a wrong OTP or an insufficient balance); 5xx system failure -> ERROR with the exception as the last argument so the stack trace is kept. FATAL is banned.
- INFO only for: service lifecycle, business milestone, cronjob summary, kafka consumer, important state change — everything else DEBUG. Message format: `<Action description>. [key1={}, key2={}]` in English. No string concatenation, no duplicate log of the same event (log once at the service boundary), no empty catch.

## API
- Every endpoint versioned in path: /{resource}/v{N}/...; internal = /v{N}/internal/.... No DTO sharing across versions. Breaking change -> new major version.
- Package layout mirrors the URL version (controller/v{N}/, dto/v{N}/); a v{N} controller imports only v{N} DTOs. A deprecated endpoint emits Deprecation + Sunset headers on every response and returns 410 at sunset; notice is >= 6 months for external APIs, >= 3 months for internal. Every endpoint registers a static x-api-id (`X##`) in internal-apis.yaml.

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

## Concurrency & transactions
- Spring beans are stateless by default — identify the shared mutable state before you touch it, then guard it explicitly (synchronized / ReentrantLock / java.util.concurrent). No lock-free trick without stating why it is safe.
- @Transactional at the service layer, propagation REQUIRED by default; REQUIRES_NEW only when isolation is genuinely required. NEVER hold a lock (DB row or in-process) across a network call.

## Memory & data access
- No allocation > 512KB on a hot path. Never keep a large collection in an instance field of a Spring bean.
- Always paginate — never load a full table or an unbounded result set into memory.
- Every table has an explicit BIGSERIAL/SERIAL primary key — a UUID only as an extra column with a secondary index. No foreign keys in the DB; keep consistency in application logic. Every query carries its own timeout on top of the global query/connection timeouts, and connections go through a pool (client-side or pgBouncer).

## Common libs (strict routing, no cross-import)
- Each cluster uses its own lib and never another cluster's: vikki -> finx/vikki/common-libs (com.finx.common-libs); fsap -> finx/fsap/fsap-common-libs (com.finx.fsap); bff/galaxy-g -> lives in the fsap repo (com.finx.galaxyg).
- grep the repo and the cluster lib before writing any new util — reuse beats re-implementing.

## Comments
- Default is NO comment — naming carries the meaning. Comment only to explain WHY (a workaround, an unusual business rule), and keep it to one short line.
- Never comment WHAT the code does ("looping over...", "check condition", "fixed bug"). Delete a redundant comment when you are already editing that code.

## Commits & PRs
- Branch: `<type>/<JIRA-KEY>-<short-description>` (e.g. `feat/VRHE-66-user-authentication`); deployment branch: `release/<YYYY-MM-DD>-<short-description>`. Source: Confluence EN/514556795.
- Commit: `<type>(<optional scope>): <description>` — imperative present tense, lowercase first letter, no trailing dot; breaking change marked with `!` before the colon; issue ids go in the body, never as the scope. Types: feat, fix, refactor, perf, style, test, docs, build, cicd, ops, chore. Some repos additionally prefix the subject with `[JIRA-KEY]` — then one key per commit, and never guess a key. No attribution trailers (Co-authored-by).
- PR description length is proportional to the diff. What & Why (1-2 sentences), Notes (non-obvious decisions, breaking changes, deploy order, deliberate omissions), Verification (commands actually run + their real results; if untested, say "not verified"). No file lists, no copied commit log, no emoji, no fake checklists.

## Architecture decisions (ask, don't assume)
- For significant architecture choices — hexagonal vs onion vs layered, module/bounded-context boundaries, sync vs event-driven, saga vs 2PC, share vs duplicate — STOP and ASK the user first. Present the trade-offs and a clear recommendation; never silently pick.
- Default recommendation for a new service: multi-module hexagonal (common/core/application/infra/api), matching the existing fleet — deviate only with an explicit, stated reason.
- Every design decision — library choice, data model, retry strategy — is presented with explicit pros/cons, never a bare verdict.

## Discipline
- Surgical — change only what the request needs; note adjacent issues, don't fix them. @Transactional at service layer, scope minimal. Reuse common-libs / common.fsap before writing local equivalents.
- No code before an approved plan for anything non-trivial — run the `flow` skill (explore -> plan -> execute -> review).
