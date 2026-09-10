---
name: runtime-stack
description: Use before writing or upgrading code, choosing an API, or when the user mentions Java 21/25, Spring Boot 3/4, Jakarta, Jackson, or a version migration. Never use features newer than the declared version.
---

# Runtime Stack (per project)

Java and Spring Boot versions differ across FinX services. Detect the target first, then apply that version's rules. Sources: [Spring Boot 4.0 Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide), [Java 25 notes](https://www.jrebel.com/blog/java-25).

## Step 1 — detect

- **Java**: Gradle `settings.gradle`/`build.gradle` toolchain (`JavaLanguageVersion.of(21|25)`), `sourceCompatibility`/`release`, `libs.versions.toml`; Maven `<java.version>` / `<maven.compiler.release>`.
- **Spring Boot**: the `org.springframework.boot` plugin version, the parent POM version, or `libs.versions.toml`.

State the detected stack (e.g. "Java 25 + Spring Boot 4") before editing. If the build files disagree or are unclear, ask.

## Java 21 vs 25 (both LTS)

| | Java 21 project | Java 25 project |
|---|---|---|
| Allowed | Virtual threads (stable), pattern matching for switch, records, sealed classes | Everything in 21 **plus** finalized: scoped values, module import declarations, flexible constructor bodies, compact source files |
| Avoid | Any 22-25-only syntax; no `--enable-preview` features | Preview features (structured concurrency, primitive patterns in switch, stable values) unless the build explicitly enables preview — in production banking, default to **no preview** |
| Ops note | — | Compact object headers give 10-22% heap savings via a JVM flag (an ops/deployment change, not code) |

Rule: write to the project's release level. Do not introduce newer-than-declared syntax "because it's cleaner."

## Spring Boot 3 vs 4

| | Spring Boot 3 | Spring Boot 4 |
|---|---|---|
| Baseline | Java 17+ | Java 21 minimum |
| Jakarta EE | 9/10 (`jakarta.*`; no `javax.*`) | 11, Servlet 6.1 |
| JSON | Jackson 2 | Jackson 3 (verify serialization config on upgrade) |
| Deprecations | 3.x deprecations still present | **All 3.x deprecations removed — no grace period** |
| Dropped | — | Undertow starter, JUnit 4 |
| Packaging | monolithic starters | modularized into many focused JARs — depend on the specific modules in use |

## Rules

- **Match the project.** Use only APIs/features available in the detected Java + Spring Boot version.
- **In a Spring Boot 3 project**, do not use Boot 4-only APIs; keep `jakarta.*` (never re-introduce `javax.*`).
- **In a Spring Boot 4 project**, do not use any API deprecated in 3.x (it is gone); do not add Undertow or JUnit 4; assume Jackson 3.
- **Upgrades** (3 → 4): go through Spring Boot 3.5 and clear every deprecation warning first, then move to 4.0. Treat it as planned work (`/flow plan`), not an ad-hoc edit. Follow the official migration guide linked above; do not guess removed-API replacements — look them up.
- If a newer feature/version would genuinely help, **flag it and ask** with a recommendation (baseline principle) rather than silently bumping the version.
