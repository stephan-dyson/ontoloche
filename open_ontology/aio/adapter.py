# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/adapter.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""The storage-adapter protocol -- PACKAGE.md 3.

One rule builds this module:

    The adapter stores records. It does not know what a proposal, an approval or a
    refusal is.

Mechanically, and testable at C0-04: the interface shapes from ``types.py`` appear
nowhere in this file or under ``backends/``. What crosses the boundary is flat,
JSON-serialisable record dataclasses -- projections of the interface shapes with no
computed fields. A ``status`` string is *stored*, never judged; a warnings list is
*stored*, never derived.

The other load-bearing idea is ``Capabilities``. Across two unlike backends, Rule U
("unknown is None plus a why") is unimplementable unless the backend says in advance
what it cannot answer -- otherwise the registry must either guess or probe. So every
flag that is False carries a sentence, and that sentence is surfaced verbatim as the
``why`` a caller reads.
"""

from __future__ import annotations
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable

# The records, queries, pages and capability flags are storage shapes with no I/O in
# them, so the async mirror does not copy them -- it re-exports the sync package's.
# One definition, two protocols over it.
from open_ontology.adapter import (
    CAPABILITY_FLAGS,
    EDGE_CAPABILITY_FLAGS,
    REQUIRED_CAPABILITIES,
    AttrObservedRecord,
    AttrSchemaRecord,
    Capabilities,
    ConsumerRecord,
    EdgePage,
    EdgeQuery,
    EdgeRecord,
    EventRecord,
    ProposalPage,
    ProposalQuery,
    ProposalRecord,
    TypePage,
    TypeQuery,
    TypeRecord,
    UsageRecord,
)

__all__ = [
    "AsyncStorageAdapter",
    "AsyncAttributeStore",
    "Capabilities",
    "TypeRecord",
    "ProposalRecord",
    "ConsumerRecord",
    "UsageRecord",
    "EventRecord",
    "TypeQuery",
    "TypePage",
    "ProposalQuery",
    "ProposalPage",
    "AttrSchemaRecord",
    "AttrObservedRecord",
    "EdgeRecord",
    "EdgeQuery",
    "EdgePage",
    "CAPABILITY_FLAGS",
    "EDGE_CAPABILITY_FLAGS",
    "REQUIRED_CAPABILITIES",
]


@runtime_checkable
class AsyncStorageAdapter(Protocol):
    """The fifteen primitives -- PACKAGE.md 3.4.

    The uniform uncertainty rule: a primitive that cannot answer returns ``None`` (or a
    page with ``known=None, complete=False``) plus a ``why`` drawn from
    ``Capabilities.why`` -- never ``0``, never ``[]``, never ``False``.
    """

    # 1
    async def capabilities(self) -> Capabilities: ...

    # 2
    async def migrate(self) -> int: ...

    # 3
    def transaction(self) -> AbstractAsyncContextManager[None]: ...

    # 4
    async def put_type(self, rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord: ...

    # 5
    async def get_type(
        self, namespace: str, name: str, *, kind: str | None = None
    ) -> TypeRecord | None: ...

    # 6
    async def find_types(self, q: TypeQuery) -> TypePage: ...

    # 7
    async def put_proposal(
        self, rec: ProposalRecord, *, expect_absent: bool = False
    ) -> ProposalRecord: ...

    # 8
    async def get_proposal(self, proposal_id: str) -> ProposalRecord | None: ...

    # 9
    async def find_proposals(self, q: ProposalQuery) -> ProposalPage: ...

    # 10
    async def put_consumer(self, rec: ConsumerRecord) -> ConsumerRecord: ...

    # 11
    async def find_consumers(
        self, namespace: str, *, gate: str | None = None, consumer_id: str | None = None
    ) -> list[ConsumerRecord]: ...

    # 12
    async def bump_usage(
        self,
        namespace: str,
        kind: str,
        name: str,
        *,
        at: datetime | None,
        by: str | None,
    ) -> None: ...

    # 13
    async def get_usage(self, namespace: str, kind: str, name: str) -> UsageRecord | None: ...

    # 14
    async def append_event(self, rec: EventRecord) -> None: ...

    # 15
    async def read_events(
        self,
        namespace: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
        edge_id: str | None = None,
        # NOTE: there is deliberately NO `invocation_id` filter here yet.
        # `ACTIONS.md` 9.1 specifies it and the BUILD row lands it, together with
        # the six implementations and the `oo_event` column -- because row #6's
        # first fix pass added it to this Protocol alone, `runtime_checkable`
        # kept `isinstance` green, `check_spec_drift.py` compares the printed
        # signature against this Protocol rather than the backends, and every
        # shipped adapter raised `TypeError` on the keyword. That is deviation
        # D-4b-2 (PACKAGE.md 3.4) reproduced inside the fix that quotes it, and
        # row #6's second adversarial round found it.
    ) -> list[EventRecord]: ...

    # ------------------------------------------------------------------ 16 to 18
    # EDGES.md 7.1. Three, not eight -- and the count is the evidence that making a
    # family an ordinary row of the vocabulary was the right decision, because families
    # need no primitive at all: put_type/get_type/find_types already serve them.
    #
    # These are on the protocol rather than in a separate optional extension, because
    # EDGES.md 6 puts the four flags on `Capabilities` and 7.1 gives them the
    # `stores_proposals=False` treatment: the methods exist, `stores_edges=False`
    # raises `NotSupported`, and the registry checks the capability first and never
    # calls them. An adapter written before this row declares `stores_edges=False` by
    # default and every edge call returns `edge_store_absent`.

    # 16
    async def put_edge(self, rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord: ...

    # 17
    async def get_edge(self, edge_id: str) -> EdgeRecord | None: ...

    # 18
    async def find_edges(self, q: EdgeQuery) -> EdgePage: ...


@runtime_checkable
class AsyncAttributeStore(Protocol):
    """An OPTIONAL extension, outside the fifteen and outside conformance.

    PACKAGE.md 5 specifies two more tables (``oo_attr_schema``, ``oo_attr_observed``)
    and one facade method, but adds no primitive to carry them, and ruling R2 keeps
    ``attribute_census`` package-local and outside the conformance definition. So it is
    here as a separate protocol: a backend that implements it gets the census and
    schema modes; a backend that does not is still fully conformant, and the registry
    reports the absence rather than pretending. Recorded as deviation D-2.
    """

    async def put_attr_schema(self, rec: AttrSchemaRecord) -> AttrSchemaRecord: ...

    async def get_attr_schema(
        self,
        namespace: str,
        kind: str,
        *,
        name: str | None = None,
        version: int | None = None,
    ) -> AttrSchemaRecord | None: ...

    async def observe_attributes(
        self,
        namespace: str,
        kind: str,
        attributes: dict[str, Any],
        *,
        at: datetime,
        schema_version: int | None,
    ) -> None: ...

    async def read_attr_observed(
        self, namespace: str, *, kind: str | None = None
    ) -> list[AttrObservedRecord]: ...
