---
name: logging-review
description: Review Java/Spring Boot logging against the FinX logging convention. Use when reviewing or writing logging code, adding log statements, or when asked to "check logging", "review logs", or before a PR touching log lines. Checks DEBUG-by-default, no PII/secrets in logs, mask() usage, SLF4J parameterization, no log-and-throw, no full-object/collection logging. Source: Confluence EN/1448280077 (Backend - Logging Convention v1.6).
---

# Logging Review

Review the target Java files (default: the uncommitted diff; else the files named) against the FinX logging convention and report violations. **Report only — do not rewrite unless asked.**

## How to run

1. Scope the files: `git diff --name-only` for `*.java`, or the files the user named.
2. For each file, check every `log.` statement and `catch` block against the checklist below.
3. Use these greps as a first pass, then read the surrounding code to confirm (grep finds candidates; judgment confirms):

```bash
rg -n 'System\.out|System\.err|printStackTrace'                     # prohibited
rg -n 'log\.[a-z]+\([^"]*\+' <files>                                # string concatenation in log
rg -n 'log\.(info|debug).*(password|otp|token|cardNumber|pan|cvv|phone|email|nationalId|accountNumber)' <files>  # PII/secret
rg -n 'log\.[a-z]+\("[^"]*",\s*[a-zA-Z]+\)\s*;' <files>             # candidate full-object logging
rg -n 'catch\s*\([^)]*\)\s*\{\s*\}' <files>                          # empty catch
```

## Checklist (Confluence §14 — report each violation with file:line)

| # | Rule |
|---|---|
| 1 | No `System.out.println` / `System.err` / `e.printStackTrace()` / `main()` |
| 2 | SLF4J parameterized (`"... [k={}]", v`) — never string concatenation |
| 3 | **Most statements are `log.debug()`**; `INFO` only for key business milestones (challenge every INFO) |
| 4 | No PII/secret logged: password, OTP, token, apiKey, card/PAN/CVV, full account no., phone, email, national id, biometric, IP |
| 5 | Sensitive identifiers masked via `mask()` |
| 6 | External-system calls have before/after logging at DEBUG |
| 7 | Exceptions logged with stack trace (exception as **last** arg: `log.error("... [id={}]", id, e)`) |
| 8 | No log-and-throw (choose one) |
| 9 | No empty catch blocks |
| 10 | Messages in English, concise, context as `[key=value]` |
| 11 | Collections logged by size (`accounts.size()`), not content |
| 12 | No full object graph (`log.debug("{}", user)`) — log identifiers only |
| 13 | Guard null before `log.x(..., obj.getX())` (avoid NPE side effects) |
| 14 | requestId/traceId propagated on inter-service calls (MDC) |
| 15 | Level mirrors the response: business error answered with 4xx → `WARN` (never `ERROR`); system failure answered with 5xx → `ERROR` + exception as last arg |
| 16 | `INFO` only for: service lifecycle, business milestone, cronjob summary, kafka consumer, important state change — everything else `DEBUG` |
| 17 | No duplicate log of the same event — log once, at the service boundary. `FATAL` is banned |

## Output format

```
logging-review — <N> findings
CRITICAL  file:line  [rule 4] PII 'phone' logged raw → mask(phone)
HIGH      file:line  [rule 8] log.error + throw same exception → remove one
MEDIUM    file:line  [rule 3] log.info for validation step → log.debug
```
Severity: PII/secret leak = CRITICAL; log-and-throw / lost stack trace / empty catch / `ERROR` for a business rule = HIGH; INFO overuse / duplicate log / missing context = MEDIUM. If clean, say so.
