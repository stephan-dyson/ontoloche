"""The third reference leg -- a real SQLite backend that is **natively** degraded.

PACKAGE.md 6.1 says a backend is conformant iff the whole suite passes against it, and
PACKAGE.md 7.4 says Tenshen's one-table registry is conformant *"as a third backend"*.
Until row 3d nothing in this repository checked the second claim against a real store:
degradation was **simulated**, by wrapping a fully capable adapter in
``contract/doubles.py``'s ``DegradedAdapter`` and taking flags away from it. That is a
test double reporting on itself. beacon's finding **U2** said so, and PACKAGE.md 6
now names three reference legs rather than two.

**What "natively" means here, concretely.** This backend is not a wrapper. Its store has
**five tables where the reference schema has nine** (PACKAGE.md 4.1 plus §5's two), and
the four that are missing are missing *from the SQL*, not hidden behind a Python
``if``:

===========================  ===========================================================
absent                       consequence
===========================  ===========================================================
``oo_proposal``              ``stores_proposals=False``. ``put_proposal`` /
                             ``get_proposal`` / ``find_proposals`` raise ``NotSupported``
                             -- they do not pretend to store and lose (PACKAGE.md 7.3 B4)
``oo_event``                 ``stores_events=False``. No audit trail, so a destructive
                             override that cannot be recorded is refused (PACKAGE.md 3.6)
``oo_type_predicate``        ``indexes_membership=False``. ``find_types(predicate=...)``
                             answers ``known=None, complete=False`` and a ``why`` --
                             never ``known=0``
``oo_type.attributes_json``  ``stores_attributes=False``, and this is the interesting
                             one: the column is gone, but ``oo_type.primary_key_json``
                             is a real typed column this schema owns, so
                             ``attribute_projections={"primary_key"}`` and that ONE key
                             round-trips through its own column. Beacon finding U3, and
                             the shape ``stores_attributes`` alone could not describe
===========================  ===========================================================

**And the schema belongs to the host** (``owns_schema=False``): ``migrate()`` is
verify-only, exactly as it is for beacon's Alembic-owned ``work_link_types``.
:meth:`MinimalSQLiteAdapter.create_host_schema` is the *host's* DDL, kept here so the
conformance run has a host to play; this adapter never issues it.

Five of the ten capability flags are declined at once, which is precisely what
``check_capability_matrix.py`` cannot cover (it declines one at a time) and what ruling
**R12** asked the coverage report to make honest. A backend this degraded cannot
exercise every contract id -- and the run now says which, per leg, rather than exiting 0
with a wall of passes.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from ..adapter import Capabilities, EventRecord, ProposalQuery, ProposalRecord
from ..errors import NotSupported
from .sqlite import SQLiteAdapter

__all__ = ["MinimalSQLiteAdapter"]

#: The columns this store's ``oo_type`` actually has. Note what is NOT here:
#: ``attributes_json``. And note what is: ``primary_key_json``, a typed column this
#: schema owns, which is why ``primary_key`` is a projection rather than a loss.
MINIMAL_TYPE_COLUMNS = (
    "namespace",
    "kind",
    "name",
    "definition",
    "created_by",
    "status",
    "aliases_json",
    "primary_key_json",
    "attr_schema_version",
    "provenance_json",
    "warnings_json",
    "retire_reason",
    "retired_by",
    "retired_at",
    "successor",
    "created_at",
    "updated_at",
)

#: ``{column: attribute key}`` -- PACKAGE.md 5.7.
MINIMAL_TYPE_PROJECTIONS = {"primary_key_json": "primary_key"}

#: The host application's DDL. This adapter never issues it: ``owns_schema=False``.
HOST_SCHEMA = """
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
    -- the host's own typed column. NOT a JSON blob for arbitrary keys.
    primary_key_json    TEXT,
    attr_schema_version INTEGER,
    provenance_json     TEXT NOT NULL DEFAULT '{}',
    warnings_json       TEXT NOT NULL DEFAULT '[]',
    retire_reason       TEXT,
    retired_by          TEXT,
    retired_at          TEXT,
    successor           TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    -- guarantee G1, from a real constraint, exactly as the full schema has it.
    PRIMARY KEY (namespace, kind, name),
    CHECK (length(name) BETWEEN 1 AND 64 AND name GLOB '[a-z]*')
);

CREATE INDEX oo_type_ns_status ON oo_type (namespace, status);
CREATE INDEX oo_type_ns_kind   ON oo_type (namespace, kind);

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

CREATE TABLE oo_attr_observed (
    namespace            TEXT NOT NULL,
    kind                 TEXT NOT NULL,
    key                  TEXT NOT NULL,
    n                    INTEGER NOT NULL,
    first_seen           TEXT NOT NULL,
    last_seen            TEXT NOT NULL,
    example_json         TEXT,
    schema_versions_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (namespace, kind, key)
);

INSERT INTO oo_schema_version (version, applied_at, note)
VALUES (1, '2026-08-29T00:00:00.000000Z', 'host-owned minimal schema');
"""

#: One sentence per declined flag, surfaced verbatim as Rule U's ``why``. These are the
#: sentences a caller reads, so they say what is missing and not merely that something is.
MINIMAL_WHY = {
    "stores_proposals": (
        "this store has no proposal table: a decision is recorded on the type row and "
        "a pending proposal has nowhere to live"
    ),
    "stores_events": (
        "this store has no event table, so there is no audit trail to append to and no "
        "history to read back"
    ),
    "stores_attributes": (
        "this store has no attributes column: the host schema owns its columns and "
        "arbitrary keys have nowhere to go"
    ),
    "indexes_membership": (
        "this store has no predicate-membership table, so which types satisfy a "
        "predicate is not a question it can answer"
    ),
}


class MinimalSQLiteAdapter(SQLiteAdapter):
    """A real SQLite store with four of the nine reference tables missing.

    Everything it *can* do it does through the same code path the full SQLite backend
    uses -- same dialect, same row mapping, same G1 constraint, same transaction. What
    differs is the schema, and the declarations follow from the schema rather than the
    other way round.
    """

    backend_name = "sqlite"  # the migration directory it reads `latest` from
    type_columns = MINIMAL_TYPE_COLUMNS
    type_projections = MINIMAL_TYPE_PROJECTIONS
    has_predicate_table = False

    def __init__(self, path: str = ":memory:", *, connection: Any | None = None):
        # owns_schema is not a parameter: this backend exists to be the host-owned case.
        super().__init__(path, connection=connection, owns_schema=False)

    @classmethod
    def create_host_schema(cls, path: str) -> None:
        """The HOST's migration, not ours. Run it, then hand this adapter the store.

        Kept in this module so the conformance run has a host to play, and separated
        from the adapter so ``migrate()``'s verify-only promise stays testable: nothing
        the adapter does can create these tables.
        """
        conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        try:
            conn.executescript(HOST_SCHEMA)
        finally:
            conn.close()

    # ---------------------------------------------------------------- 1 capabilities
    def capabilities(self) -> Capabilities:
        return Capabilities(
            enforces_unique_name=True,  # the composite PRIMARY KEY is still there
            transactional=True,  # BEGIN IMMEDIATE is still there
            stores_proposals=False,
            stores_events=False,
            stores_attributes=False,
            stores_aliases=True,
            indexes_membership=False,
            counts_usage=True,
            timestamps_usage=True,
            owns_schema=False,
            why={**MINIMAL_WHY, **self._why()},
            transaction_scope="savepoint" if self._borrowed else "owned",
            # ...and the one key this schema DOES own, as a typed column. U3.
            attribute_projections=frozenset(MINIMAL_TYPE_PROJECTIONS.values()),
        )

    # -------------------------------------------------------------------- 2 migrate
    def _required_columns(self) -> dict[str, tuple[str, ...]]:
        """Verify-only checks what THIS backend needs, which is not what the full one does.

        Asking the host for ``oo_proposal`` would be asking for a table this adapter
        declares it does not use -- ``SchemaMismatch`` naming a column nothing reads is
        the kind of refusal that teaches a host to stop reading refusals.
        """
        return {
            "oo_type": MINIMAL_TYPE_COLUMNS,
            "oo_consumer": ("namespace", "consumer_id", "gate", "on_unknown"),
            "oo_usage": ("namespace", "kind", "name", "count"),
        }

    # --------------------------------------------------------------------- 7 to 9
    def _no_proposals(self):
        return NotSupported(MINIMAL_WHY["stores_proposals"])

    def put_proposal(
        self, rec: ProposalRecord, *, expect_absent: bool = False
    ) -> ProposalRecord:
        raise self._no_proposals()

    def get_proposal(self, proposal_id: str) -> ProposalRecord | None:
        raise self._no_proposals()

    def find_proposals(self, q: ProposalQuery):
        raise self._no_proposals()

    # ------------------------------------------------------------------ 14 and 15
    def _no_events(self):
        return NotSupported(MINIMAL_WHY["stores_events"])

    def append_event(self, rec: EventRecord) -> None:
        raise self._no_events()

    def read_events(
        self,
        namespace: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
    ) -> list[EventRecord]:
        raise self._no_events()
