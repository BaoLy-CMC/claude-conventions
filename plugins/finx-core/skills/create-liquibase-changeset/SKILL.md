---
name: create-liquibase-changeset
description: Scaffold a new Liquibase changeset in the non-prod-liquibase repo following the strictly-enforced format. Use when the user wants a DB migration, schema change, "add column/table/index/enum", reference-data change, or says "create changeset", "new migration", "liquibase change". DB changes must NOT go in the service repo — they belong in non-prod-liquibase as XML changesets.
---

# Create Liquibase Changeset

Create a new changeset in the `non-prod-liquibase` repo. The repo's own `CLAUDE.md` and `templates/changeset-template.xml` are the source of truth — read them first if unsure; this skill mirrors their rules.

## Steps

1. **Locate the repo** (`non-prod-liquibase/`, sibling of the service repos).
2. **Determine target `<env>/<db>`**: list `changelogs/` to see valid environments (`dev`, `uat`, `stg`, `fsap-dev`, `fsap-uat`, `digital-uat`, `digital-stg`) and the db folders under each. If the env/db pair or which environments to target is unclear, **ask the user** — a wrong path silently targets the wrong DB.
3. **Next sequence number**: list `changelogs/<env>/<db>/changes/`, take the highest `NNN_` prefix, add 1, zero-pad to 3 digits.
4. **Author + date + slug**: author = the committing engineer (ask if unknown, don't guess); date = today `DD.MM.YYYY`; slug = short kebab description.
5. **Write the file** `changes/NNN_<slug>.xml` using the exact structure below.
6. **Validate**: `make lint FILES="changelogs/<env>/<db>/changes/NNN_<slug>.xml"` — must pass before done.
7. If the same change applies to multiple environments, create one file per env path (do not point one file at multiple DBs).

## Exact format (enforced by scripts/check-changeset-format.sh)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                   http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.4.xsd">

    <!-- changeset <author>:DD.MM.YYYY:<slug> -->
    <changeSet id="DD.MM.YYYY:<slug>" author="<author>">
        <comment>Human-readable description</comment>
        <sql>
            -- forward SQL
        </sql>
        <rollback>
            <sql>-- rollback SQL (required; never leave empty)</sql>
        </rollback>
    </changeSet>
</databaseChangeLog>
```

## Hard rules (each is CI-blocking)

- Exactly **one** `<changeSet>` per file, and exactly **one** `<!-- changeset ... -->` comment.
- Comment format: `<!-- changeset author:DD.MM.YYYY:slug -->` (dots or hyphens in date).
- `changeSet id` must equal `DD.MM.YYYY:slug` from the comment; `author` must match the comment author.
- File name `NNN_description.xml`, `NNN` zero-padded.
- **`<rollback>` is required** — for irreversible ops (e.g. PostgreSQL enum add) put an explicit rollback strategy comment + SQL, never leave it blank.
- **No raw `.sql`** files under `changelogs/` (pre-commit + CI block them). Wrap SQL inside the XML `<sql>` element. `changelogs/legacy/*.sql` is reference only.
- A changeset that creates a table, sequence, or inserts new data **must include the `GRANT` statements** the service DB user needs to read it.
- One atomic change per file: do not mix independent statements, and a change to another table gets its own changeset.

## Schema design rules

- Explicit primary key, single `BIGSERIAL`/`SERIAL`. A UUID is an extra column with a secondary index, never the PK (full-page-write cost).
- **No foreign keys** — they cause transitive lock contention and block online schema changes; keep consistency in application logic.
- Lower-case `snake_case` names, collective/plural table names. Booleans as `is_xxx`. `timestamptz` for `created_at` / `last_modified_at`.
- Every table carries `created_at`, `created_by`, `last_modified_at`, `last_modified_by` for audit.
- JSON column type for genuinely flexible extra fields or deferred-processing payloads.
- Never store data computed from other columns of the same table.

## Backward compatibility (every change, no exceptions)

- Adding a column → give it a DB-populated default.
- Removing a column → prove no service reads it for 2–3 weeks or 2–3 rollouts first; drop only once the new version is live and stable.
- Never change a column type incompatibly — add a new column and migrate the data.
- Keep column types consistent with what the schema already uses (`varchar(n)`, not `character varying(n)`).

## Banking caveats

- Index on a large table → `CREATE INDEX CONCURRENTLY`, and set `runInTransaction="false"` on the changeSet: Liquibase wraps a changeset in a transaction and CIC fails inside one. Full pre-flight in the `ops-runtime` skill.
- Never put secrets or PII literals in reference-data SQL.

> Confluence EN/514526405 (2022) says "No rollbacks in the changesets". That predates this repo: `README.md` requires an explicit `<rollback>` and the review checklist asks for a meaningful one. The repo wins.
