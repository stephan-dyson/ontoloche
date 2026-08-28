-- open_ontology store, schema version 1. SQLite dialect. PACKAGE.md 4.1 / 4.3.
--
-- JSON columns are TEXT, encoded and decoded in Python: SQLite's JSON functions are
-- built in only as of 3.38.0 and JSONB only as of 3.45.0, and the version bundled with
-- CPython varies by platform build. This package never uses a SQLite JSON function.
--
-- Timestamps are TEXT, ISO-8601, UTC, Z-suffixed, microsecond precision -- a format
-- that sorts correctly as text, which is what the event ordering and the orphan-window
-- comparison need.

CREATE TABLE oo_schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    note       TEXT
);

CREATE TABLE oo_type (
    namespace           TEXT NOT NULL,
    kind                TEXT NOT NULL,
    name                TEXT NOT NULL,
    definition          TEXT NOT NULL CHECK (length(definition) > 0),
    created_by          TEXT NOT NULL,
    status              TEXT NOT NULL,
    aliases_json        TEXT NOT NULL DEFAULT '[]',
    attributes_json     TEXT NOT NULL DEFAULT '{}',
    attr_schema_version INTEGER,
    provenance_json     TEXT NOT NULL DEFAULT '{}',
    warnings_json       TEXT NOT NULL DEFAULT '[]',
    retire_reason       TEXT,
    retired_by          TEXT,
    retired_at          TEXT,
    successor           TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    -- guarantee G1. Per (namespace, kind): `facility` as an entity and `facility` as a
    -- value_set may coexist (INTERFACE.md 2.1).
    PRIMARY KEY (namespace, kind, name),
    -- A first-character and length guard only; SQLite has no regex in core. The full
    -- ^[a-z][a-z0-9_]{0,63}$ rule is enforced above the adapter on both backends, so
    -- the two behave identically. This is belt-and-braces against a direct INSERT.
    CHECK (length(name) BETWEEN 1 AND 64 AND name GLOB '[a-z]*')
);

CREATE INDEX oo_type_ns_status ON oo_type (namespace, status);
CREATE INDEX oo_type_ns_kind   ON oo_type (namespace, kind);
CREATE INDEX oo_type_created_by ON oo_type (created_by);

-- The normalised form of TypeRecord.predicates. Membership lives on the member; the
-- extent is a query against this table in the other direction. Nothing is ever written
-- to the predicate's own row -- if an implementation grows a consumer-membership table,
-- it has stored the extent twice and INTERFACE.md 2.3 has been missed.
CREATE TABLE oo_type_predicate (
    namespace      TEXT NOT NULL,
    member_kind    TEXT NOT NULL,
    member_name    TEXT NOT NULL,
    predicate_name TEXT NOT NULL,
    PRIMARY KEY (namespace, member_kind, member_name, predicate_name),
    FOREIGN KEY (namespace, member_kind, member_name)
        REFERENCES oo_type (namespace, kind, name) ON DELETE CASCADE
    -- deliberately NO foreign key on predicate_name: a member may claim a predicate
    -- that is only proposed. Refusing that would be propose_type refusing a
    -- near-duplicate.
);

CREATE INDEX oo_type_predicate_extent ON oo_type_predicate (namespace, predicate_name);

CREATE TABLE oo_proposal (
    proposal_id       TEXT PRIMARY KEY,
    namespace         TEXT NOT NULL,
    kind              TEXT NOT NULL,
    name              TEXT NOT NULL,
    definition        TEXT NOT NULL,
    predicates_json   TEXT NOT NULL DEFAULT '[]',
    attributes_json   TEXT NOT NULL DEFAULT '{}',
    evidence_json     TEXT NOT NULL DEFAULT '[]',
    near_matches_json TEXT NOT NULL DEFAULT '[]',
    warnings_json     TEXT NOT NULL DEFAULT '[]',
    proposed_by       TEXT NOT NULL,
    proposed_at       TEXT NOT NULL,
    tier              TEXT,
    status            TEXT NOT NULL,
    decided_by        TEXT,
    decided_at        TEXT,
    decision_reason   TEXT,
    superseded_by     TEXT
    -- NO unique constraint on (namespace, kind, name): several proposals for one word
    -- over time is normal, and one of them being a retained rejection is the point.
);

CREATE INDEX oo_proposal_lookup ON oo_proposal (namespace, name, status);

CREATE TABLE oo_consumer (
    namespace     TEXT NOT NULL,
    consumer_id   TEXT NOT NULL,
    gate          TEXT NOT NULL,
    on_unknown    TEXT NOT NULL,
    owner         TEXT,
    registered_at TEXT NOT NULL,
    locator       TEXT,
    PRIMARY KEY (namespace, consumer_id)
);

CREATE INDEX oo_consumer_gate ON oo_consumer (namespace, gate);

CREATE TABLE oo_usage (
    namespace  TEXT NOT NULL,
    kind       TEXT NOT NULL,
    name       TEXT NOT NULL,
    count      INTEGER,
    first_seen TEXT,
    last_seen  TEXT,
    PRIMARY KEY (namespace, kind, name)
);

-- Append-only. No UPDATE, no DELETE anywhere in this package: a correction is a new
-- event, never an edit (INTERFACE.md 5.8).
CREATE TABLE oo_event (
    event_id    TEXT PRIMARY KEY,
    namespace   TEXT NOT NULL,
    kind        TEXT,
    name        TEXT,
    proposal_id TEXT,
    at          TEXT NOT NULL,
    actor       TEXT NOT NULL,
    event       TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    seq         INTEGER
);

CREATE INDEX oo_event_subject ON oo_event (namespace, kind, name, at);
CREATE INDEX oo_event_proposal ON oo_event (proposal_id);

CREATE TABLE oo_attr_schema (
    namespace     TEXT NOT NULL,
    kind          TEXT NOT NULL,
    version       INTEGER NOT NULL,
    fields_json   TEXT NOT NULL DEFAULT '{}',
    additional    TEXT NOT NULL DEFAULT 'allow',
    mode          TEXT NOT NULL DEFAULT 'off',
    registered_at TEXT NOT NULL,
    registered_by TEXT NOT NULL,
    PRIMARY KEY (namespace, kind, version)
);

-- The floor that applies even in `off` mode: every distinct attribute key ever
-- written is recorded, so the escape hatch accumulates visibly.
CREATE TABLE oo_attr_observed (
    namespace           TEXT NOT NULL,
    kind                TEXT NOT NULL,
    key                 TEXT NOT NULL,
    n                   INTEGER NOT NULL,
    first_seen          TEXT NOT NULL,
    last_seen           TEXT NOT NULL,
    example_json        TEXT,
    schema_versions_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (namespace, kind, key)
);
