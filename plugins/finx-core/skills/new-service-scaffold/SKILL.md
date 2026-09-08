---
name: new-service-scaffold
description: Scaffold a new FinX backend microservice or a new endpoint/module following the standard project structure and conventions. Use when the user wants to "create a new service", "bootstrap a service", "scaffold a module", "add a new controller/endpoint" from scratch, or asks how to lay out a new backend service. Source: Confluence EN/514528555 (Project structure template).
---

# New Service / Endpoint Scaffold

Lay out a new service (or new module/endpoint) matching the existing FinX services. Read an existing sibling (e.g. `fsap-onboarding-service`) and Confluence EN/514528555 as the reference — mirror their structure, don't invent a new one.

## Module layout (multi-module Gradle, hexagonal)

```
<service-name>/                 # settings.gradle: rootProject.name = '<service-name>'
├── common/       # DTOs, constants, shared enums, response types
├── core/         # domain model + business logic (ports, services) — no framework leakage
├── application/  # use-case orchestration / saga wiring
├── infra/        # adapters: persistence (JPA), HTTP clients, messaging
├── api/          # controllers, exception handlers, API config (the web edge)
└── tests/        # integration/component tests
```

Base package: `com.finx.<serviceslug>` with sub-packages per module (`...api.controller`, `...api.exception`, `...core.service`, `...infra.client`, etc.).

## Conventions to bake in from the start

- **API**: controllers under `api.controller.v{N}`; path `/{resource}/v{N}/...`, internal `/{resource}/v{N}/internal/...`. No DTO shared across versions.
- **Envelope** (by cluster):
  - `fsap-*` service → `com.finx.common.fsap.pojo.FsapApiResponse` + reuse `common.fsap` (`FsapControllerAdvice`, `FsapHeaderContext`, `JwtExtractor`) — do **not** hand-write a `@RestControllerAdvice`.
  - non-fsap service → `com.finx.spring.service.api.ResponseApi`.
- **Errors**: `ErrorCode` enum (`DOMAIN.CODE`); domain exceptions extend the shared base; single `GlobalExceptionHandler`.
- **Logging**: SLF4J `private static final Logger log = LoggerFactory.getLogger(X.class);` DEBUG-by-default; MDC `X-Request-ID`/traceId filter; `mask()` for sensitive ids.
- **Config**: everything externalised in `application.yml` via `${ENV_VAR:default}`; secrets via env/secret-manager. Actuator on its own port `${MANAGEMENT_SERVER_PORT:8081}`, exposing `health`, `prometheus`, `metrics`, with `health.probes.enabled: true` so `/actuator/health/{liveness,readiness}` exist — the k8s probes must point at those, never at the aggregate `/actuator/health`. Tag every metric with the application name and enable percentile histograms for `http.server.requests`. Full snippet + workload `values.yaml`: `ops-runtime` skill.
- **Persistence**: JPA; UUID secondary keys; `created_at/created_by/last_modified_at/last_modified_by` audit columns; no foreign keys; `timestamptz`. Schema changes go to `non-prod-liquibase` (use `create-liquibase-changeset`), never auto-DDL in prod.
- **Java**: Java 21+, records for DTOs, constructor injection only, Lombok allowed, **no `var`**, `BigDecimal` for money.

## Architecture decision — ask first (mandatory)

Before generating anything, **ask the user** which architecture style to use — do not assume. Present the trade-offs and a recommendation:

- **Hexagonal / ports-&-adapters (RECOMMENDED)** — matches the existing FinX fleet (`common/core/application/infra/api`); domain isolated from framework; easy to test; consistent with siblings. Cost: more modules/boilerplate for a tiny service.
- **Onion** — similar dependency-inversion benefits, layered as concentric rings; fewer Gradle modules. Cost: diverges from the fleet's module convention.
- **Simple layered (controller→service→repository)** — least ceremony, fine for a genuinely small/CRUD service. Cost: weaker boundaries as it grows; inconsistent with core services.

Recommend hexagonal unless the service is trivially small; wait for the user's decision before scaffolding. Apply the same ask-first rule to other significant choices (module/bounded-context boundaries, sync vs event-driven, saga vs 2PC).

## Steps

1. Confirm: service name, fsap vs non-fsap cluster, DB name (if any), first resource/endpoint, **and the architecture style chosen above**.
2. Copy the module skeleton from the closest existing service; rename root + base package.
3. Wire the cluster-correct envelope + exception handling + header/JWT context (reuse `common-libs` / `common.fsap`).
4. Add the first `v1` controller + core service + infra adapter following the layers.
5. `application.yml` with externalised config + actuator; register health check.
6. If it exposes a public (mobile/partner) API → also register in gateway/openapi (see `cross-repo-operations`).
7. Build to verify: `./gradlew compileJava` then `./gradlew build`.

Keep it minimal (KISS) — only the modules/classes the first endpoint needs; do not pre-create empty layers "for later".
