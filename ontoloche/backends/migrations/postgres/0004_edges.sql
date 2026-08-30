-- Store version 4 -- EDGES.md v0, roadmap row 4b.
--
-- One new table and one new column. The table holds edges; the column is the
-- `EventRecord.edge_id` amendment EDGES.md 5.2 specified and 7.1 priced at
-- "one nullable column" -- landed in `adapter.py` by the spec row and, until now,
-- in neither reference store. (Round 3 of that row's loop found the amendment
-- claimed in two places and made in neither; `check_spec_drift.py` could not see it,
-- because PACKAGE.md and the code agreed with EACH OTHER on the old shape and a third
-- document asserting a change nobody made is invisible to a two-way diff.)
--
-- What is deliberately absent, and each absence is a decision:
--
--   * NO unique constraint on (namespace, family, src..., dst...). EDGES.md 6.1: two
--     `blocks` edges between one pair, written by a human in March and by a classifier
--     in August, are TWO FACTS with different provenance. A uniqueness constraint would
--     force the second write to fail or to overwrite the first, and overwriting is an
--     edit of a provenance-bearing record, which INTERFACE.md 5.8 forbids. Beacon's own
--     `work_links` has no unique constraint on its endpoint columns either; that is
--     corroboration, not the reason.
--   * NO foreign key from `family` to `oo_type`. EDGES.md 2.7: an edge pointing at a
--     family or an endpoint nobody registered is the ingestion layer's mistake MADE
--     VISIBLE, and refusing the write moves the failure into a log nobody reads. It is
--     the same argument PACKAGE.md 3.4 primitive 10 makes for `put_consumer` accepting
--     a gate that names no predicate. The registry checks the family; the store does
--     not, and beacon's `work_links` has no FK to `work_link_types` either -- its own
--     documentation calls the registry "advisory rather than enforced".
--   * NO DELETE path. Retraction is a `status` change plus a tombstone in the four
--     `retract_*` columns, and nothing in this package deletes.
--
-- Timestamps are TIMESTAMPTZ and JSON columns are JSONB, as everywhere else in this
-- dialect. The edge cursor is a keyset on (created_at, edge_id); the cursor itself is
-- an opaque string in both dialects, so the two backends page identically.

CREATE TABLE oo_edge (
    edge_id             TEXT PRIMARY KEY,
    -- the FAMILY's namespace. Never the endpoints' -- they carry their own, which is
    -- what makes a cross-agency edge cheap (EDGES.md 2.1, 4.5).
    namespace           TEXT NOT NULL,
    family              TEXT NOT NULL,
    src_namespace       TEXT NOT NULL,
    src_kind            TEXT NOT NULL,
    src_name            TEXT NOT NULL,
    -- NULL means a TYPE-level endpoint. It is a value to match on, not a wildcard:
    -- a type node and an instance of it are two different endpoints.
    src_instance_id     TEXT,
    dst_namespace       TEXT NOT NULL,
    dst_kind            TEXT NOT NULL,
    dst_name            TEXT NOT NULL,
    dst_instance_id     TEXT,
    attributes_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
    attr_schema_version INTEGER,
    provenance_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- STORED, never judged (PACKAGE.md 3.1). The CHECK is belt-and-braces against a
    -- direct INSERT and is not the adapter validating a transition.
    status              TEXT NOT NULL DEFAULT 'active',
    warnings_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL,
    retract_reason      TEXT,
    retracted_by        TEXT,
    retracted_at        TIMESTAMPTZ,
    CHECK (status IN ('active', 'retracted'))
);

-- The two the frontier query uses. `neighbors` asks "which edges are incident on these
-- nodes?", once per depth level, so both ends are indexed.
CREATE INDEX oo_edge_src ON oo_edge (src_namespace, src_kind, src_name, src_instance_id);
CREATE INDEX oo_edge_dst ON oo_edge (dst_namespace, dst_kind, dst_name, dst_instance_id);
-- `indexes_edges_by_family=True` is a claim about THIS index existing. A backend
-- without it declares False and the registry filters above the store (EDGES.md 6, 7.1).
CREATE INDEX oo_edge_family ON oo_edge (namespace, family);
-- The keyset order. Without it `find_edges` pages by sorting, which is the thing
-- keyset pagination exists to avoid.
CREATE INDEX oo_edge_order ON oo_edge (created_at, edge_id);

-- EDGES.md 5.2. `EventRecord` had `kind`, `name` and `proposal_id` and no slot for an
-- edge, so an edge event had nowhere to go. Additive, nullable, and it carries the
-- three new `event` values `edge_added`, `edge_retracted` and `edge_amended` -- stored,
-- never judged, exactly like every other value in that vocabulary.
ALTER TABLE oo_event ADD COLUMN edge_id TEXT;

CREATE INDEX oo_event_edge ON oo_event (edge_id, at);
