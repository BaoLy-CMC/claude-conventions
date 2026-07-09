---
name: write-docs
description: Write or update documentation and place it where the user wants — local repo, Confluence, or a given path — in the format they choose (Markdown, Confluence page, or HTML). Use when the user says "write docs", "document this", "create a doc/guide/runbook", "publish to Confluence", "generate documentation". Always asks format + destination before writing; never publishes externally without confirmation.
---

# Write Docs

Produce a doc and put it where it belongs. **Ask format + destination first** (don't assume), then generate concise, well-structured content with references.

## Step 1 — ask (use AskUserQuestion), with recommended defaults

**Language:** ask **English or Vietnamese** (no default — confirm each time). Write the whole doc in the chosen language consistently; keep code, identifiers, and commands as-is.

**Format:**
| Format | Use |
|---|---|
| **Markdown** (recommended) | Repo docs, READMEs, runbooks — portable, diff-friendly |
| Confluence | Shared/durable knowledge for the team |
| HTML | Standalone styled page |

**Destination:**
| Destination | Where | When |
|---|---|---|
| **Repo `docs/`** (recommended for repo-scoped) | `<repo>/docs/<slug>.md`, committed | Lives with the code it documents |
| **Confluence** | Atlassian MCP, space `EN` (Engineering) by default | Durable / cross-team — the source-of-truth per FinX conventions |
| **Local scratch** | `.finx/docs/<slug>.md` (git-ignored) | Personal working notes |
| **Custom path** | user-provided | Anything else |

If unsure which, recommend: **repo `docs/` in Markdown** for anything tied to one service; **Confluence** for anything the whole team must find.

## Step 2 — generate

- Write in the chosen language, consistently.
- **Clear and complete** — full structure, not a stub: title, one-line purpose, then the sections the doc type needs (e.g. overview, prerequisites, steps, examples, configuration, troubleshooting, references). Don't leave "TBD" sections; if information is missing, ask.
- Lead with the purpose; short sections; tables over prose where they help; concrete examples.
- **Cite references**: `file:line`, Confluence page ids, URLs, ticket ids.
- **No icons or emoji** anywhere in the document — plain, professional text and standard Markdown/HTML structure only.
- Skimmable (headings, bullets), no filler.

## Step 3 — place it

- **Local / repo / custom path** → `Write` the file. Create `docs/` if missing. Report the path.
- **Confluence** → this is an **outward-facing publish; confirm space + parent page + title first**. Then:
  - New page: `createConfluencePage` (needs `cloudId`, `spaceId`, title, body). Default space `EN`; ask for the parent page if it should nest.
  - Update existing: fetch with `getConfluencePage`, then `updateConfluencePage`.
  - Convert the Markdown to Confluence-friendly content (the MCP accepts markdown/adf/html via `contentFormat`).
  - Report the published page URL.

## Guardrails

- Never publish to Confluence (or any external destination) without confirming space/parent/title — publishing is outward-facing and hard to fully undo.
- Don't overwrite an existing file or Confluence page without surfacing that it exists and confirming.
- For durable design/architecture docs, prefer Confluence (source of truth) and leave a pointer in the repo, rather than duplicating long prose in both.
