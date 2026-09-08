---
name: integration-test
description: Apply the FinX integration-test standard — which layer a test belongs to, the opt-in src/integrationTest source set that skips without configuration, containers vs a shared environment, captured-payload inputs, value/shape/behaviour assertions, run-marker cleanup on a shared database, and separate coverage gating. Use when adding or reviewing an integration test, wiring an integrationTest Gradle task, choosing between a Testcontainer and STG, deciding what to assert, or debugging a flaky/duplicate-dropped test. Source: Confluence EN/1936294017 (standard) + EN/1941569537 (port procedure, reference implementation transaction-posting-service).
---

# Integration Test

The org-wide standard already exists in Confluence together with a port procedure and a reference implementation. **Do not invent a second setup** — copy the reference and change only package names, tables, and the scenario catalogue. This skill is the rule summary plus the checks a reviewer applies.

## Which layer

| Layer | Boots | Infrastructure | Answers |
|---|---|---|---|
| Unit | nothing | none | Does this branch/mapping/calculation behave? |
| Slice | one adapter | containers | Does this SQL, deserialiser, listener wire up? |
| **Integration** | whole application | containers, plus a shared environment only where unavoidable | Does the path across adapters produce the right result? |
| Cross-service E2E | many services | dedicated environment | Does the business flow work across teams? |

**Rule L1** — a test belongs one layer down unless it needs something only this layer provides; the cheapest layer that can fail for the right reason wins. **Rule L2** — cross-service E2E does not live in a service repository.

## Where the suite lives

- **S1** Own source set `src/integrationTest`, never `src/test` — Testcontainers and Awaitility stay off the unit-test classpath.
- **S2** Own Gradle task, deliberately **not** wired into `check` or `build`. A suite needing Docker, VPN and credentials must never break somebody's ordinary build.
- **S3** Absent configuration means **skip, not fail**. Gate on an env var (`STG_IT_ENABLED`) and assert it with `Assumptions.assumeTrue(...)` in the base `@BeforeAll` — `@EnabledIfEnvironmentVariable` on a base class silently never applies (it is `@Repeatable`, not `@Inherited`).
- **S4** One base class per suite holding containers, property overrides and cleanup hooks; every test class extends it and adds nothing to the Spring configuration. Differing `@ActiveProfiles`, `@MockitoBean` sets or `@DirtiesContext` fragment the TestContext cache and each fragment costs another full application startup.
- **S5** Package `<root>.it`, classes suffixed `IT`, so no `*Test` pattern ever picks them up.

## Containers or a shared environment

- **E1 Container by default** — isolated, repeatable, cannot damage anything. Kafka and Redis are always Testcontainers.
- **E2** A shared environment only when what the test exercises **exists nowhere else** (typically: the schema, when the repo owns no migrations; and downstream contracts, where a mock would only assert this service's own assumptions). Write the reason in the class javadoc.
- **E3** Every such exception is a debt item, not a design choice.
- **E4 Never point a test at shared messaging or shared caches.** Joining a live consumer group steals partitions from running pods and processes real traffic on a laptop; a fresh group id consumes the whole topic and writes duplicates; shared counters (sequences, vouchers) get consumed for real.
- **E5** Containers are shared across the suite, not per class, and coordinates are injected by overriding the **env-var placeholder names the YAML already references** (`KAFKA_PLAINTEXT_SERVERS`, `REDIS_HOST`, …) via `@DynamicPropertySource`. `@ServiceConnection` cannot reach nested per-consumer `properties[bootstrap.servers]` keys or hand-rolled `@Value` blocks.

## Input

- **I1 Input is a file, not a builder.** A captured JSON payload describes what a caller actually sends, including the fields nobody modelled — where the interesting failures are.
- **I2** Fixed locations: `src/integrationTest/resources/scenarios/<area>/<name>.json` for request bodies, `<module>/src/testFixtures/resources/fixtures/<domain>/` for domain payloads shared with unit tests (two copies drift invisibly).
- **I3** Only two things may be templated: the per-test run marker, and dates relative to today. Fail loudly on a leftover `${...}` rather than sending it to the service.
- **I4** Every input carries the run marker in every identifier the service will persist.
- **I5/I6** One catalogue per flow (a record with a mandatory one-sentence `description` — if no sentence distinguishes it from every other scenario, it is a duplicate), replayed through **every** entry point (Kafka *and* REST) against the **same** expected files. A transport that legitimately differs gets its own expected file and a comment, never a quietly relaxed assertion.

## Assertions

| Mode | Use when | Mechanism |
|---|---|---|
| Value | the test created the data, or the response is a fixed envelope | whole-document compare against a committed golden file |
| Shape | the environment owns the data (downstream payloads, pre-existing rows) | compare which keys exist and each type |
| Behaviour | the claim is not a document (idempotency, eviction, retries, ordering) | hand-written assertion named after the behaviour |

- **A1** Assert values only for data the test created. A golden file that breaks because somebody edited a shared record teaches people to regenerate golden files without reading them — worse than no test.
- **A2** Shape assertions still catch the only thing worth asserting about a downstream service: a field disappearing or changing type.
- **A3** Read the whole object (`SELECT *`, the entire response body). A hand-picked projection excludes exactly the fields nobody thought to assert.
- **A4** Never assert against a serialised string — `assertThat(body).contains("SUCCESS")` passes on an empty payload, a wrong payload, and a payload where `SUCCESS` appears inside an error message. Parse, then assert.
- **A5** Assert transport and payload separately: a service that wraps everything in an envelope returns HTTP 200 for business failures too.
- **A6** Normalise, do not delete: `<run>` for marker-bearing identifiers, `<dynamic>` for surrogate keys, counters, audit timestamps and any per-request envelope UUID (`meta.requestId`). Sort arrays canonically so row order does not leak into the assertion.
- **A7** Wait for the output to be final: wait for the expected count, then poll until two consecutive reads are identical, and only then compare. Otherwise the comparison races the pipeline and fails intermittently — which trains people to re-run instead of investigate.
- **A8** Golden files are reviewed like code. Bootstrap with `./gradlew :api:integrationTest -Pit.golden.update=true`; the run writes the files and **fails on purpose**. Read the diff — an empty payload in a test named "found" is a bug, not an expectation.
- **A9** Behaviour tests are named after the behaviour: `redeliveringTheSameBatchWritesNothingNew()`, not `testKafkaConsumer()`.

## Test data on a shared database

- **D1 Marker plus watermark, both.** The marker is a per-run prefix stamped into every persisted identifier; the watermark is `MAX(id)` captured before the test. Delete only rows matching both, so nothing pre-existing can be removed however the marker matches.
- **D2 A marker per test method, not per run.** Idempotency filters remember identifiers for hours: two tests sharing a marker means the second delivery is silently dropped as a duplicate and the test that should have failed passes.
- **D3** Clean up after each test **and** sweep at the start of the run — `@AfterEach` does not run when the JVM is killed. Sweep markers older than a few hours.
- **D4** After cleanup, count what is left; if anything survived, log the exact SQL to remove it.
- **D5** Write the blind spots down: tables with no marker column can only be narrowed heuristically; say so in code and docs, and pick fixtures that keep the blast radius small.

## Coverage

- **C1** Report integration coverage separately, attributed across every module the suite exercises (a report scoped to the module the tests live in shows near zero).
- **C2 Never gate on a merged unit + integration number.** Booting a Spring context executes configuration classes, mappers and constructors no assertion looks at, so a merged gate rewards adding `@SpringBootTest` classes over writing assertions. Example separate floors: 40% line for the suite, 70% for the core service package.
- **C3** Read the integration report for a different question than the gate: which paths does the suite reach at all, and which parts of the flow has nothing ever exercised end to end.

## Gotchas worth checking on any port

- Raw JDBC writes in tests silently do nothing when Hikari runs with `auto-commit=false` — every test-side write (seeds, cleanup, sweep) goes through a `TransactionTemplate`.
- `Could not resolve placeholder 'SPRING_PROFILE_ACTIVE'`: `@ActiveProfiles` selects a profile but does not make the placeholder resolvable — register it in `@DynamicPropertySource`.
- Pin `apache/kafka:3.8.1` (or `4.0.0`). The `3.9.0` image's `KafkaDockerWrapper` ignores `KAFKA_ADVERTISED_LISTENERS` when it arrives via the Testcontainers startup script, and the container dies with *"advertised.listeners cannot use the nonroutable meta-address 0.0.0.0"*.
- Committed profile (`application-stg-it.yml`) holds everything non-secret with `FILL-ME` markers; only the gate and credentials come from the environment. A guard should refuse to run while a marker remains, and refuse any endpoint matching `(?i)(?<!non)prod|uat`.

## Bring-up verification

When porting or first wiring a suite, run these in order — each is a decision point, not a formality:

```
Bring-up progress:
- [ ] 1. ./gradlew build on a machine with no Docker/VPN/credentials → green
- [ ] 2. integrationTest with nothing configured → every test SKIPPED, build green
- [ ] 3. Gate env var set, credentials absent → fail-fast listing what is missing
- [ ] 4. An endpoint pointed at a uat/prod host → refuses to run before any write
- [ ] 5. First real run bootstraps golden files and fails on purpose → read every file
- [ ] 6. Re-run → green. Run twice in a row → still green (idempotency + settle races)
- [ ] 7. kill -9 mid-run, then re-run → sweeper reports what it removed, verify stays quiet
- [ ] 8. Golden files committed; nightly job wired with the separate coverage verification
```

## Review checklist

- Does it need the whole application, or would a slice fail for the same reason? (L1)
- Does it touch shared messaging or shared caches? (E4 — it must not)
- Is the input a captured payload rather than a Java builder? (I1)
- Does it pin values it does not own? (A1) Does it assert on a serialised string? (A4)
- Does it wait for a final state, or race the pipeline? (A7)
- Does the suite still skip cleanly with no configuration? (S3)
- Does cleanup cover every table the scenario writes, marker **and** watermark bound? (D1/D3)
