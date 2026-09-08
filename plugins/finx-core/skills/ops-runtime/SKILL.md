---
name: ops-runtime
description: Runtime standards for a FinX Java workload — Kubernetes probes, JVM heap and GC flags, HPA, graceful shutdown, actuator/metrics wiring, and creating an index on a production PostgreSQL/Aurora table. Use when editing values.yaml in non-prod-application-workload or prod-application-workload, tuning resources or autoscaling, wiring health checks or Prometheus, diagnosing OOMKill / rollout downtime / traffic during shutdown, or planning a CREATE INDEX on a large production table. Source: Confluence EN/1897496583, EN/1707409479, EN/514541756.
---

# Ops Runtime

Two areas that break production silently: how a Java pod is configured, and how an index reaches a live table.

## 1. Kubernetes workload (`values.yaml`)

Audit of 347 Java services found the same eight defects repeatedly. Check all of them.

| # | Defect | Fix |
|---|---|---|
| 1 | Probes point at the aggregate `/actuator/health` | Split: liveness and startup on `/actuator/health/liveness`, readiness on `/actuator/health/readiness` |
| 2 | No `startupProbe`, `readiness initialDelaySeconds: 30` | Add `startupProbe` (`periodSeconds: 5`, `failureThreshold: 30` = 150s cold-start budget), then set liveness/readiness `initialDelaySeconds: 0` |
| 3 | HPA scales on memory | Remove `targetMemoryUtilizationPercentage` — CPU only |
| 4 | CPU limit `< 1` core | Limit `>= 1` (typically `"2"`), request `500m` |
| 5 | No heap flags | Set `JAVA_TOOL_OPTIONS` (below) |
| 6 | `replicaCount: 1` with HPA off | `>= 2` |
| 7 | memory request `!=` limit | Make them equal |
| 8 | Shutdown not coordinated with k8s | Istio drain annotation + `terminationGracePeriodSeconds: 60` |

```yaml
application:
  deployment:
    terminationGracePeriodSeconds: 60
    podAnnotations:
      proxy.istio.io/config: '{"terminationDrainDuration":"30s","holdApplicationUntilProxyStarts":true}'
    resources:
      requests: { cpu: 500m, memory: 2Gi }
      limits:   { cpu: "2",  memory: 2Gi }     # request == limit
    extraEnvs:
      - name: JAVA_TOOL_OPTIONS
        value: >-
          -XX:MaxRAMPercentage=70
          -XX:InitialRAMPercentage=50
          -XX:+UseG1GC
          -XX:+ExitOnOutOfMemoryError
      - name: MANAGEMENT_ENDPOINT_HEALTH_PROBES_ENABLED
        value: "true"
    startupProbe:
      httpGet: { path: /actuator/health/liveness, port: metrics }
      periodSeconds: 5
      failureThreshold: 30
      timeoutSeconds: 3
    livenessProbe:
      httpGet: { path: /actuator/health/liveness, port: metrics }
      initialDelaySeconds: 0
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet: { path: /actuator/health/readiness, port: metrics }
      initialDelaySeconds: 0
      periodSeconds: 5
      failureThreshold: 3
  replicaCount: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 8
    targetCPUUtilizationPercentage: 70
```

Why each one matters:

- **Aggregate health endpoint breaks shutdown.** `ReadinessStateHealthIndicator` is not registered in the aggregate endpoint (`management.health.readinessstate.enabled` defaults to `false`), so `/actuator/health` keeps answering 200 all the way through shutdown and kubelet keeps routing new requests until the process dies. Only the `readiness` group reflects `REFUSING_TRAFFIC`.
- **CPU limit below 1 core** makes the JVM see a single CPU: SerialGC and one JIT compiler thread.
- **No heap flags** leaves the heap at 25% of the container.
- **memory request != limit** makes the container's memory view inconsistent with the heap sizing → OOMKill.
- **HPA on memory never scales down** — the JVM does not return heap to the OS, so utilisation stays high forever.
- **`replicaCount: 1`** makes every rollout a downtime window.
- `holdApplicationUntilProxyStarts` fixes the opposite race at startup: without it the JVM boots before Envoy and the first 1–2s of outbound calls fail.

Graceful shutdown: from **Spring Boot 3.4** `server.shutdown=graceful` is the default (30s per-phase timeout). **Do not set `SERVER_SHUTDOWN` in `values.yaml` — reject PRs that add it.** Only Boot <= 3.3 needs it, and upgrading beats patching. Check with:

```bash
kubectl -n stg logs deploy/<service> --tail=200 | grep -i "Starting .* using Java\|Spring Boot"
```

Known gap: the `application` chart has no `deployment.lifecycle` key yet, so `preStop: sleep 5` (which covers the SIGTERM-vs-Endpoints-propagation race) cannot be set; the Istio annotation covers most of it. Autoscaling needs chart `application` version **1.3.2**.

## 2. Actuator and metrics wiring (new service)

```yaml
management:
  server:
    port: ${MANAGEMENT_SERVER_PORT:8081}
  endpoints:
    web:
      base-path: /
      exposure:
        include: [prometheus, health, metrics]
      path-mapping:
        health: /actuator/health
        prometheus: /actuator/prometheus
  endpoint:
    prometheus: { enabled: true }
    health:
      probes: { enabled: true }
      show-components: always
  metrics:
    distribution:
      percentiles-histogram: { "http.server.requests": true }
      percentiles: { "http.server.requests": 0.5, 0.90, 0.95, 0.99 }
```

Plus one bean tagging every metric with the application name:

```java
@Bean
MeterRegistryCustomizer<MeterRegistry> metricsCommonTags(
        @Value("${spring.application.name}") String applicationName) {
    return registry -> registry.config().commonTags("application", applicationName);
}
```

## 3. Creating an index on a production table

Golden rules (PostgreSQL / Aurora, tables >= 1M rows):

1. **Never** plain `CREATE INDEX` on production — it takes a `ShareLock` and blocks every INSERT/UPDATE/DELETE until the build finishes (hours on a 100M-row table).
2. Always `CREATE INDEX CONCURRENTLY` (CIC), and always `DROP INDEX CONCURRENTLY`.
3. **Never** run CIC inside `BEGIN ... COMMIT` — it fails immediately.
4. Every new index needs a reviewed PR (DBA or Tech Lead approval) and a rollback plan.
5. After the build, verify `pg_index.indisvalid` / `indisready` / `indislive`, then `ANALYZE` (CIC does not).

```sql
SET statement_timeout = 0;        -- do not let the session be cut mid-build
SET lock_timeout = '60s';         -- fail fast instead of queueing
SET maintenance_work_mem = '2GB';

CREATE INDEX CONCURRENTLY idx_account_transactions_account_id_created_at
    ON account_transactions (account_id, created_at DESC);

ANALYZE account_transactions;
```

Before running:

- Justify it: `EXPLAIN ANALYZE` the real query, check `pg_stat_statements`, confirm no existing index (or composite prefix) already serves it, and that read benefit beats the write cost (`pg_stat_user_tables.n_tup_*`).
- Composite column order: **equality → range → ORDER BY**. Low-selectivity leading column = planner skips the index.
- Low-cardinality column (boolean, 2–3 statuses) → partial index `WHERE col = 'value'`, not a plain index.
- Free disk >= `2 x estimated_index_size`.
- No transaction older than 5 minutes (`pg_stat_activity`) — CIC waits for writers before the build *and* before validation, so a long transaction blocks it indefinitely.
- Check replica lag; CIC generates a lot of WAL.
- Window 00:00–04:00, avoiding month-end, holidays, and GL/posting batches. One index per window, never several in parallel.
- Naming: `idx_<table>_<col1>_<col2>[_partial|_unique]`, `uq_<table>_<cols>`.
- Notify affected teams, especially where the table feeds HDBank/NAPAS integrations.

Unique index adds one mandatory step: **pre-check duplicates** (`GROUP BY ... HAVING count(*) > 1`). If any exist, stop, find the cause (race condition? missing app-layer validation? old migration?), clean up with an audited plan, then create. A failed CIC unique leaves an **INVALID** index — it is still maintained on every DML but never used by the planner, so drop it immediately (`DROP INDEX CONCURRENTLY`).

Monitor progress from another session via `pg_stat_progress_create_index` (`phase`, `blocks_done/blocks_total`). Alert if a phase stalls > 30 minutes, replica lag passes the tier threshold, or primary free disk < 20%.

Dropping an unused index: only after >= 2 weeks of `pg_stat_user_indexes` data that includes a month-end close (`idx_scan = 0`, not unique, not primary).
