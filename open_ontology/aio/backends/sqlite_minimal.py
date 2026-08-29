"""Async mirror of ``backends/sqlite_minimal.py`` -- the natively-degraded third leg.

Hand-written for the same reason the other two async drivers are (3B-ASYNC.md D-A12):
the driver layer is where a constructor becomes ``await Adapter.open(...)``, and
``tools/unasync.py`` does not touch it. Everything that is not the driver -- the reduced
column list, the projection map, the ``why`` sentences, the host DDL -- is **imported
from the sync module**, not copied, so there is exactly one statement of what this
backend is and the two stacks cannot drift on it.
"""

from __future__ import annotations

from typing import Any

from open_ontology.adapter import (
    Capabilities,
    EdgeQuery,
    EdgeRecord,
    EventRecord,
    ProposalQuery,
    ProposalRecord,
)
from open_ontology.aio.backends.sqlite import AsyncSQLiteAdapter
from open_ontology.backends.sqlite_minimal import (
    HOST_SCHEMA,
    MINIMAL_TYPE_COLUMNS,
    MINIMAL_TYPE_PROJECTIONS,
    MINIMAL_WHY,
    MinimalSQLiteAdapter,
)
from open_ontology.errors import NotSupported

__all__ = ["AsyncMinimalSQLiteAdapter", "HOST_SCHEMA"]


class AsyncMinimalSQLiteAdapter(AsyncSQLiteAdapter):
    """Five tables where the reference schema has nine. See the sync module's docstring."""

    backend_name = "sqlite"
    type_columns = MINIMAL_TYPE_COLUMNS
    type_projections = MINIMAL_TYPE_PROJECTIONS
    has_predicate_table = False

    @classmethod
    async def open(  # type: ignore[override]
        cls,
        path: str = ":memory:",
        *,
        connection: Any | None = None,
        owns_schema: bool = False,
    ) -> "AsyncMinimalSQLiteAdapter":
        # owns_schema is accepted and ignored: this backend exists to be the host-owned
        # case, and a caller who could turn that off would be testing something else.
        return await super().open(path, connection=connection, owns_schema=False)

    @classmethod
    def create_host_schema(cls, path: str) -> None:
        """The HOST's migration -- the sync module's, unchanged."""
        MinimalSQLiteAdapter.create_host_schema(path)

    # ---------------------------------------------------------------- 1 capabilities
    async def capabilities(self) -> Capabilities:
        return Capabilities(
            enforces_unique_name=True,
            transactional=True,
            stores_proposals=False,
            stores_events=False,
            stores_attributes=False,
            stores_aliases=True,
            indexes_membership=False,
            counts_usage=True,
            timestamps_usage=True,
            owns_schema=False,
            # EDGES.md 6 -- the sync twin's declaration, and for the same reason: this
            # store has no `oo_edge` at all. The other three are vacuous rather than
            # declined, which `Capabilities.missing_why()` knows about.
            stores_edges=False,
            stores_edge_events=False,
            indexes_edges_by_family=False,
            stores_edge_attributes=False,
            why={**MINIMAL_WHY, **self._why()},
            transaction_scope="savepoint" if self._borrowed else "owned",
            attribute_projections=frozenset(MINIMAL_TYPE_PROJECTIONS.values()),
        )

    # -------------------------------------------------------------------- 2 migrate
    def _required_columns(self) -> dict[str, tuple[str, ...]]:
        return {
            "oo_type": MINIMAL_TYPE_COLUMNS,
            "oo_consumer": ("namespace", "consumer_id", "gate", "on_unknown"),
            "oo_usage": ("namespace", "kind", "name", "count"),
        }

    # --------------------------------------------------------------------- 7 to 9
    async def put_proposal(
        self, rec: ProposalRecord, *, expect_absent: bool = False
    ) -> ProposalRecord:
        raise NotSupported(MINIMAL_WHY["stores_proposals"])

    async def get_proposal(self, proposal_id: str) -> ProposalRecord | None:
        raise NotSupported(MINIMAL_WHY["stores_proposals"])

    async def find_proposals(self, q: ProposalQuery):
        raise NotSupported(MINIMAL_WHY["stores_proposals"])

    # ------------------------------------------------------------------ 14 and 15
    async def append_event(self, rec: EventRecord) -> None:
        raise NotSupported(MINIMAL_WHY["stores_events"])

    async def read_events(
        self,
        namespace: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
        edge_id: str | None = None,
    ) -> list[EventRecord]:
        raise NotSupported(MINIMAL_WHY["stores_events"])

    # ------------------------------------------------------------------ 16 to 18
    async def put_edge(self, rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord:
        raise NotSupported(MINIMAL_WHY["stores_edges"])

    async def get_edge(self, edge_id: str) -> EdgeRecord | None:
        raise NotSupported(MINIMAL_WHY["stores_edges"])

    async def find_edges(self, q: EdgeQuery):
        raise NotSupported(MINIMAL_WHY["stores_edges"])
