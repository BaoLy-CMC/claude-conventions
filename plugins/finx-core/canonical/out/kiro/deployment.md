# Deployment Workflow — FinX Steering

Product: FinX / Vikki banking platform (SBV-compliant). Stack: Java 21 or 25 (LTS) + Spring Boot 3 or 4 microservices, per project. Source: Confluence space EN (Engineering).

> Generated from the FinX canonical convention source. Do not hand-edit.

## Cross-repo operations (NON-PROD only; prod = separate release)
- DB migration -> non-prod-liquibase (strict changeset format; rollback required; make lint).
- Important env (secret, external endpoint, prod-behavior flag) -> ASK & CONFIRM first, then non-prod-application-workload.
- New Kafka topic -> non-prod-kafka-gitops.
- Public API (mobile/partner) -> register in non-prod-apigw-configs + non-prod-openapi-configs.

## Commits & PRs
- Branch: `<type>/<JIRA-KEY>-<short-description>` (e.g. `feat/VRHE-66-user-authentication`); deployment branch: `release/<YYYY-MM-DD>-<short-description>`. Source: Confluence EN/514556795.
- Commit: `<type>(<optional scope>): <description>` — imperative present tense, lowercase first letter, no trailing dot; breaking change marked with `!` before the colon; issue ids go in the body, never as the scope. Types: feat, fix, refactor, perf, style, test, docs, build, cicd, ops, chore. Some repos additionally prefix the subject with `[JIRA-KEY]` — then one key per commit, and never guess a key. No attribution trailers (Co-authored-by).
- PR description length is proportional to the diff. What & Why (1-2 sentences), Notes (non-obvious decisions, breaking changes, deploy order, deliberate omissions), Verification (commands actually run + their real results; if untested, say "not verified"). No file lists, no copied commit log, no emoji, no fake checklists.
