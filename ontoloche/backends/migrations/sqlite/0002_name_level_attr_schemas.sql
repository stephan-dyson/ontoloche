-- Store version 2 -- ruling R10, row 3e.
--
-- `oo_attr_schema` was keyed (namespace, kind, version): ONE schema per kind. CMS has
-- two kind="value_set" entries with different shapes (PACKAGE.md 5.6, asserted by
-- C15-07), so one schema per kind gives one of two wrong answers and there is no
-- third. The key gains `name`, and a name-level schema shadows the per-kind one.
--
-- `name` is NOT NULL with '' meaning "the per-kind schema". No type name can be empty
-- (INTERFACE.md 2.1: ^[a-z][a-z0-9_]{0,63}$), so one column carries both cases and the
-- primary key stays a primary key rather than a partial index over a nullable column.
--
-- DROP AND RECREATE, not ALTER. PACKAGE.md 9.4 says in terms that a v0 store may be
-- dropped and rebuilt rather than migrated and that this package promises no migration
-- path between v0 schema revisions. What that permits is taken here and its cost is
-- stated: **every attribute schema registered against a v0 store is discarded by this
-- migration.** An AttributeSchema is deployment configuration, reproducible from the
-- deployment's own source, and 9.4's rule is that anything in a v0 store that matters
-- must be reproducible from its source. Nothing in `oo_type`, `oo_proposal`,
-- `oo_event`, `oo_consumer`, `oo_usage`, `oo_type_predicate` or `oo_attr_observed` is
-- touched: the vocabulary, its provenance and the census all survive untouched. Nor is
-- `oo_type.attr_schema_version`, which records the version in force at write and is
-- never rewritten (5.4) -- so an entry written under a schema this migration drops
-- keeps saying which generation it belongs to, and the census keeps saying so too.

DROP TABLE oo_attr_schema;

CREATE TABLE oo_attr_schema (
    namespace     TEXT NOT NULL,
    kind          TEXT NOT NULL,
    name          TEXT NOT NULL DEFAULT '',
    version       INTEGER NOT NULL,
    fields_json   TEXT NOT NULL DEFAULT '{}',
    additional    TEXT NOT NULL DEFAULT 'allow',
    mode          TEXT NOT NULL DEFAULT 'off',
    registered_at TEXT NOT NULL,
    registered_by TEXT NOT NULL,
    PRIMARY KEY (namespace, kind, name, version)
);
