-- Store version 5 -- ACTIONS.md v0, roadmap row 6b.
--
-- One new table and one new column. The table holds invocations; the column is the
-- `EventRecord.invocation_id` amendment ACTIONS.md 3.5 specified and 9.2 priced at
-- "an ALTER, not a recreate" -- landed in `adapter.py` by the spec row (#6) and, until
-- now, in neither reference store. That is exactly the shape of row 4b's D-4b-2, which
-- ACTIONS.md 9.1 quotes at length as the reason the FILTER and the COLUMN and the six
-- implementations must land in ONE change: `runtime_checkable` matches on method names,
-- so `isinstance` stays True while every shipped adapter raises `TypeError` on the
-- keyword, and a spec-drift checker that compares a printed signature against the
-- Protocol rather than against the backends cannot see it.
--
-- What is deliberately absent, and each absence is a decision:
--
--   * NO unique constraint beyond the primary key. `invocation_id` is minted ABOVE the
--     store (PACKAGE.md 4.2, as `proposal_id`, `event_id` and `edge_id` are), so a key
--     this package generates is unique by construction and `enforces_unique_invocation`
--     is a flag ACTIONS.md 8 argues out of existence: it would assert nothing.
--   * NO foreign key from `family` to `oo_type`. Same argument EDGES.md 2.7 makes for
--     `oo_edge.family` and PACKAGE.md 3.4 primitive 10 makes for `put_consumer`: the
--     registry checks the family, the store does not. An invocation naming a family
--     nobody registered is a fact about what a host did, and refusing to STORE it moves
--     the failure into a log nobody reads -- which is ACTIONS.md 2.5's own argument for
--     why an undeclared effect warns rather than refusing.
--   * NO foreign key from `compensates` to `oo_invocation`. A `compensates` pointing at
--     nothing is recorded with a warning rather than refused, because refusing would
--     discard the compensation record itself.
--   * NO UPDATE or DELETE path. The ledger is append-only by construction; `outcome`
--     moving to `compensated` is DERIVED by the facade from the forward pointer, not
--     written back over the original row (INTERFACE.md 5.8).
--
-- Timestamps are TIMESTAMPTZ and the JSON columns are JSONB -- the same choices the
-- rest of this schema makes, so the invocation store is not the one table with its own
-- conventions. The invocation cursor is a keyset on (created_at, invocation_id), which
-- is what makes `find_invocations` pageable; both columns are indexed below.

CREATE TABLE oo_invocation (
    invocation_id          TEXT PRIMARY KEY,
    -- the FAMILY's namespace. Never the inputs' -- they carry their own, which is what
    -- makes a cross-agency invocation cheap (ACTIONS.md 3.1, EDGES.md 2.2's rule).
    namespace              TEXT NOT NULL,
    family                 TEXT NOT NULL,
    inputs_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- COPIED from what the GATE judged, never a pointer at the current declaration:
    -- an invocation that pointed at the live family would silently re-describe its own
    -- blast radius every time somebody edited the family (ACTIONS.md 3.1).
    declared_effects_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- the HOST's claim. The registry records it and cannot verify it (ACTIONS.md 3.3).
    observed_effects_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
    declared_policy_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    family_version         INTEGER NOT NULL DEFAULT 1,
    -- STORED, never judged (PACKAGE.md 3.1). The CHECKs are belt-and-braces against a
    -- direct INSERT and are not the adapter validating a transition.
    outcome                TEXT NOT NULL DEFAULT 'applied',
    refusal_reason         TEXT,
    gate_verdict           TEXT NOT NULL DEFAULT 'not_asked',
    compensates            TEXT,
    created_at             TIMESTAMPTZ NOT NULL,
    created_by_actor       TEXT NOT NULL,
    created_by             TEXT NOT NULL DEFAULT 'user',
    model_tier             TEXT,
    confidence             DOUBLE PRECISION,
    -- NEVER blank-implying-human. When the gate was not asked, or asked and refused,
    -- this is NULL and the record carries `approval_unrecorded` (ACTIONS.md 3.2).
    approved_by            TEXT,
    approved_at            TIMESTAMPTZ,
    source_version         TEXT,
    attr_schema_version    INTEGER,
    warnings_json          JSONB NOT NULL DEFAULT '[]'::jsonb,
    CHECK (outcome IN ('applied', 'refused', 'failed', 'compensated')),
    CHECK (gate_verdict IN ('allowed', 'refused', 'not_asked'))
);

-- `indexes_invocations_by_family=True` is a claim about THIS index existing. A backend
-- without it declares False and the registry filters above the store, which stays
-- CORRECT and may hit `limit` -- and then `complete=False` carries the backend's own
-- sentence (ACTIONS.md 8).
CREATE INDEX oo_invocation_family ON oo_invocation (namespace, family);
-- The three governance reads ACTIONS.md 4, 2.5 and 5.2 ask for. The override query
-- (`gate_verdict='refused' AND outcome='applied'`) is the one 4 asks an operator to act
-- on, and round 2 measured what it costs when the filter is not pushed down: zero rows
-- from a 2,399-row ledger that had one.
CREATE INDEX oo_invocation_gate ON oo_invocation (gate_verdict, outcome);
CREATE INDEX oo_invocation_actor ON oo_invocation (created_by_actor);
-- The keyset order. Without it `find_invocations` pages by sorting, which is the thing
-- keyset pagination exists to avoid -- and an offset page over an append-only table
-- shifts under a concurrent write.
CREATE INDEX oo_invocation_order ON oo_invocation (created_at, invocation_id);

-- ACTIONS.md 3.5. `EventRecord` had `kind`, `name`, `proposal_id` and `edge_id` and no
-- slot for an invocation, so an invocation event had nowhere to go. Additive, nullable,
-- and it carries the three new `event` values `invocation_recorded`,
-- `invocation_reviewed` and `invocation_compensated` -- stored, never judged, exactly
-- like every other value in that vocabulary.
ALTER TABLE oo_event ADD COLUMN invocation_id TEXT;

-- `find_invocations(unreviewed=)` pushes down as far as *"no `invocation_reviewed`
-- event exists for this row"*, which is a correlated EXISTS over this index.
CREATE INDEX oo_event_invocation ON oo_event (invocation_id, at);
