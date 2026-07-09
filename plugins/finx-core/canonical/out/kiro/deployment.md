# Deployment Workflow — FinX Steering

Product: FinX / Vikki banking platform (SBV-compliant). Stack: Java 21 + Spring Boot microservices. Source: Confluence space EN (Engineering).

> Generated from the FinX canonical convention source. Do not hand-edit.

## Cross-repo operations (NON-PROD only; prod = separate release)
- DB migration -> non-prod-liquibase (strict changeset format; rollback required; make lint).
- Important env (secret, external endpoint, prod-behavior flag) -> ASK & CONFIRM first, then non-prod-application-workload.
- New Kafka topic -> non-prod-kafka-gitops.
- Public API (mobile/partner) -> register in non-prod-apigw-configs + non-prod-openapi-configs.
