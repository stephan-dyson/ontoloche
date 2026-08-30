-- ontoloche store, schema version 1. Postgres dialect. PACKAGE.md 4.1 / 4.4.
--
-- The same seven-plus-two tables as SQLite. Three things differ, and all three are the
-- adapter's content rather than an abstraction leak: jsonb instead of TEXT,
-- timestamptz instead of ISO text, and the full name regex natively in a CHECK.
--
-- Deliberately not used, so the two backends stay honest about the same things:
-- SERIAL/IDENTITY (4.2 -- the key is natural), ON CONFLICT DO UPDATE as a substitute
-- for reading inside the transaction (it would hide already_decided), array columns
-- (SQLite has none, and the join table is the shared shape), and LISTEN/NOTIFY.

CREATE TABLE oo_schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL,
    note       TEXT
);

CREATE TABLE oo_type (
    namespace           TEXT NOT NULL,
    kind                TEXT NOT NULL,
    name                TEXT NOT NULL,
    definition          TEXT NOT NULL CHECK (length(definition) > 0),
    created_by          TEXT NOT NULL,
    status              TEXT NOT NULL,
    aliases_json        JSONB NOT NULL DEFAULT '[]'::jsonb,
    attributes_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
    attr_schema_version INTEGER,
    provenance_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
    warnings_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    retire_reason       TEXT,
    retired_by          TEXT,
    retired_at          TIMESTAMPTZ,
    successor           TEXT,
    created_at          TIMESTAMPTZ NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (namespace, kind, name),
    CONSTRAINT oo_type_name_shape CHECK (name ~ '^[a-z][a-z0-9_]{0,63}$')
);

CREATE INDEX oo_type_ns_status ON oo_type (namespace, status);
CREATE INDEX oo_type_ns_kind   ON oo_type (namespace, kind);
CREATE INDEX oo_type_created_by ON oo_type (created_by);
-- the census reads attributes_json, and a deployment may want to grep the escape hatch
CREATE INDEX oo_type_attributes_gin ON oo_type USING GIN (attributes_json);

CREATE TABLE oo_type_predicate (
    namespace      TEXT NOT NULL,
    member_kind    TEXT NOT NULL,
    member_name    TEXT NOT NULL,
    predicate_name TEXT NOT NULL,
    PRIMARY KEY (namespace, member_kind, member_name, predicate_name),
    FOREIGN KEY (namespace, member_kind, member_name)
        REFERENCES oo_type (namespace, kind, name) ON DELETE CASCADE
);

CREATE INDEX oo_type_predicate_extent ON oo_type_predicate (namespace, predicate_name);

CREATE TABLE oo_proposal (
    proposal_id       TEXT PRIMARY KEY,
    namespace         TEXT NOT NULL,
    kind              TEXT NOT NULL,
    name              TEXT NOT NULL,
    definition        TEXT NOT NULL,
    predicates_json   JSONB NOT NULL DEFAULT '[]'::jsonb,
    attributes_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_json     JSONB NOT NULL DEFAULT '[]'::jsonb,
    near_matches_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings_json     JSONB NOT NULL DEFAULT '[]'::jsonb,
    proposed_by       TEXT NOT NULL,
    proposed_at       TIMESTAMPTZ NOT NULL,
    tier              TEXT,
    status            TEXT NOT NULL,
    decided_by        TEXT,
    decided_at        TIMESTAMPTZ,
    decision_reason   TEXT,
    superseded_by     TEXT
);

CREATE INDEX oo_proposal_lookup ON oo_proposal (namespace, name, status);

CREATE TABLE oo_consumer (
    namespace     TEXT NOT NULL,
    consumer_id   TEXT NOT NULL,
    gate          TEXT NOT NULL,
    on_unknown    TEXT NOT NULL,
    owner         TEXT,
    registered_at TIMESTAMPTZ NOT NULL,
    locator       TEXT,
    PRIMARY KEY (namespace, consumer_id)
);

CREATE INDEX oo_consumer_gate ON oo_consumer (namespace, gate);

CREATE TABLE oo_usage (
    namespace  TEXT NOT NULL,
    kind       TEXT NOT NULL,
    name       TEXT NOT NULL,
    count      INTEGER,
    first_seen TIMESTAMPTZ,
    last_seen  TIMESTAMPTZ,
    PRIMARY KEY (namespace, kind, name)
);

-- INSERT only. A deployment that wants this enforced rather than promised should
-- REVOKE UPDATE, DELETE ON oo_event; the package does not issue grants.
CREATE TABLE oo_event (
    event_id    TEXT PRIMARY KEY,
    namespace   TEXT NOT NULL,
    kind        TEXT,
    name        TEXT,
    proposal_id TEXT,
    at          TIMESTAMPTZ NOT NULL,
    actor       TEXT NOT NULL,
    event       TEXT NOT NULL,
    detail_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    seq         BIGSERIAL
);

CREATE INDEX oo_event_subject ON oo_event (namespace, kind, name, at);
CREATE INDEX oo_event_proposal ON oo_event (proposal_id);

CREATE TABLE oo_attr_schema (
    namespace     TEXT NOT NULL,
    kind          TEXT NOT NULL,
    version       INTEGER NOT NULL,
    fields_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    additional    TEXT NOT NULL DEFAULT 'allow',
    mode          TEXT NOT NULL DEFAULT 'off',
    registered_at TIMESTAMPTZ NOT NULL,
    registered_by TEXT NOT NULL,
    PRIMARY KEY (namespace, kind, version)
);

CREATE TABLE oo_attr_observed (
    namespace            TEXT NOT NULL,
    kind                 TEXT NOT NULL,
    key                  TEXT NOT NULL,
    n                    INTEGER NOT NULL,
    first_seen           TIMESTAMPTZ NOT NULL,
    last_seen            TIMESTAMPTZ NOT NULL,
    example_json         JSONB,
    schema_versions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    PRIMARY KEY (namespace, kind, key)
);
