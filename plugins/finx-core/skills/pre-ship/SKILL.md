---
name: pre-ship
description: Run the full verification gate before a PR or ship — build, Checkstyle, tests with coverage, the finx review skills, and (if available) the SonarQube quality gate — and emit one PASS/FAIL report. Use when the user says "pre-ship", "ready to ship", "run checks", "verify before PR", or at the review phase of the flow. Distinct from the personal `/verify` command: this also runs the review skills and Sonar and aggregates a single verdict.
---

# Pre-Ship Gate

One gate that must be green before opening a PR. Run each check, then emit a single PASS/FAIL table. Stop being "done" until CRITICAL/HIGH are cleared.

## Scope

Default to the working diff (`git diff --name-only` + staged). For a multi-module Gradle service, run Gradle from the service root.

## Checks (run in order; report all, don't stop at the first failure)

1. **Compile** — `./gradlew compileJava` (fast fail on build breakage).
2. **Checkstyle** — `./gradlew checkstyleMain` if the task exists (Google Java Style). Report violations.
3. **Tests + coverage** — `./gradlew test jacocoTestReport`. Coverage target **80%** for changed code (Confluence coding standard: 70-80% minimum). Report failing tests and the coverage number.
4. **Convention reviews** on the diff — invoke `logging-review`, `error-handling-review`, and `api-response-standards` when the diff touches a controller, envelope, or money path (plus `security-review` if installed). Collect their CRITICAL/HIGH findings.
5. **SonarQube** (optional, if the `sonarqube` MCP is connected) — check the project quality gate status and new-code issues on the branch/PR.
6. **Diff sanity** — no `System.out`/`printStackTrace`, no committed secrets, no `TODO`/`FIXME` left in shipped code, no debug logging left at INFO.
7. **Skill lint** — only when the diff touches this conventions repo: `python3 plugins/finx-core/scripts/check-skills.py` must exit 0.

## Verdict

- **FAIL** if: build fails, any test fails, coverage below target on changed code, a failed quality gate, or any CRITICAL/HIGH review finding.
- **PASS** otherwise. MEDIUM/LOW findings are listed but don't block.

## Output format

```
pre-ship gate — <PASS|FAIL>
compile        PASS
checkstyle     PASS (0 violations)
tests          FAIL (2 failing: OrderServiceTest.shouldReject...)
coverage       WARN (74% < 80% on changed files)
logging-review PASS
error-handling FAIL (1 HIGH: OTP_BLOCKED mapped to 500)
sonar          PASS (quality gate OK)
diff-sanity    PASS
skill-lint     SKIPPED (not a conventions-repo diff)
--> FAIL: fix tests + error-handling HIGH before PR.
```

## Notes

- Report honestly — if a check was skipped (task absent, MCP not connected), say `SKIPPED (reason)`, never mark it PASS.
- This is the natural last step of `/flow review`; on PASS, proceed to `/ship`.
