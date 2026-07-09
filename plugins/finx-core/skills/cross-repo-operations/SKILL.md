---
name: cross-repo-operations
description: Route infrastructure changes to the correct GitOps repo instead of the service repo. Use when adding a Kafka topic, an important environment variable, or exposing a public API to mobile/partners, or when asked where a DB migration / topic / env / gateway route belongs. Applies to NON-PROD only; prod goes through a separate release process.
---

# Cross-Repo Operations Routing

Infrastructure changes do **not** live in the service repo. Route them to the dedicated GitOps repo. **Non-prod only** — prod changes go through the separate release process; do not touch prod repos here.

| Change | Repo | Notes |
|---|---|---|
| DB migration / changelog | `non-prod-liquibase` | Use the `create-liquibase-changeset` skill — strict XML format, `make lint`. |
| **Important env var** | `deployment/non-prod-application-workload/workloads/<env>/<service>` | See gate below. Also externalise in the service (`${ENV_VAR:default}`). |
| New Kafka topic | `deployment/non-prod-kafka-gitops/<env>/` | Declare via GitOps (kafka-gitops), never create topics manually or from app code. |
| Public API (mobile/partner) | `deployment/non-prod-apigw-configs/` **and** `deployment/non-prod-openapi-configs/` | Register in the correct env / `-portal` / `-fsap` variant. Internal-only endpoints: skip. |

## Important-env gate (mandatory)

An env var is **important** if it is a secret/credential, an external-system endpoint, or a flag that changes production behavior.

For an important env var:
1. **STOP and ask the user to confirm** before adding it (name, value source, which environments). This is an outward-facing config change — do not add silently.
2. Never commit the real secret value; secrets go through env / secret-manager, yml default is empty/placeholder.
3. After confirmation, add the key to `non-prod-application-workload` for the target env(s), and wire it in the service via `@ConfigurationProperties`/`@Value` with `${ENV_VAR:default}`.

Local/dev-only, non-sensitive vars with a safe default do not need the gate — just externalise them in yml.

## Kafka topic checklist
- Name follows the existing convention in the env folder; set partitions/replication/retention explicitly.
- Add to every target env (`dev`/`stg`/`uat`/`sit`) that needs it.

## Public API checklist
- Endpoint is versioned (`/{resource}/v{N}/...`) before exposing.
- Register the route in `non-prod-apigw-configs` (gateway) and the schema in `non-prod-openapi-configs` (OpenAPI), matching the env/portal/fsap variant.
- Confirm the endpoint is truly meant to be public (mobile/partner) — internal service-to-service stays off the gateway.
