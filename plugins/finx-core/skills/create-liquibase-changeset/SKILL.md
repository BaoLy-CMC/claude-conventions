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
- **No raw `.sql`** files under `changelogs/` (pre-commit + CI block them). Wrap SQL inside the XML `<sql>` element.

## Banking caveats

- Index creation on large tables → `CREATE INDEX CONCURRENTLY` (avoid synchronous lock).
- No foreign keys (per coding standards). Prefer `timestamptz` for datetime, `is_xxx` for booleans.
- Never put secrets or PII literals in reference-data SQL.
