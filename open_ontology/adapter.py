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

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable

__all__ = [
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
    "StorageAdapter",
    "AttributeStore",
    "AttrSchemaRecord",
    "AttrObservedRecord",
    "CAPABILITY_FLAGS",
    "TRANSACTION_SCOPES",
]


CAPABILITY_FLAGS = (
    "enforces_unique_name",
    "transactional",
    "stores_proposals",
    "stores_events",
    "stores_attributes",
    "stores_aliases",
    "indexes_membership",
    "counts_usage",
    "timestamps_usage",
    "owns_schema",
)

#: The two that are not optional. False on either is non-conformant, full stop
#: (PACKAGE.md 3.2). Every other flag may be False and the backend can still be
#: conformant, because the suite asserts honest unknowns rather than values.
REQUIRED_CAPABILITIES = ("enforces_unique_name", "transactional")

#: PACKAGE.md 3.5, ruling R5. ``transactional`` stays REQUIRED True either way -- a
#: savepoint adapter IS transactional; what differs is who owns the commit.
TRANSACTION_SCOPES = ("owned", "savepoint")


@dataclass(frozen=True)
class Capabilities:
    """What this backend can and cannot answer -- PACKAGE.md 3.2.

    ``why`` is the mechanism, not decoration. When a flag is False the registry does
    not invent an explanation; it surfaces the adapter's sentence.
    """

    enforces_unique_name: bool
    transactional: bool
    stores_proposals: bool
    stores_events: bool
    stores_attributes: bool
    stores_aliases: bool
    indexes_membership: bool
    counts_usage: bool
    timestamps_usage: bool
    owns_schema: bool
    why: dict[str, str] = field(default_factory=dict)
    #: Ruling R5 / PACKAGE.md 3.5. ``"owned"`` -- this adapter owns the connection and
    #: ``transaction()`` commits at depth 0. ``"savepoint"`` -- the connection is the
    #: host's: ``transaction()`` brackets its writes in a SAVEPOINT, RELEASEs on clean
    #: exit, ROLLBACKs TO on exception, and NEVER commits. Atomicity (G2) holds inside
    #: the host's transaction; durability at clean exit belongs to the host, and
    #: ``why["transaction_scope"]`` is the sentence that says so.
    transaction_scope: Literal["owned", "savepoint"] = "owned"

    def missing_why(self) -> tuple[str, ...]:
        """Flags that are False with no sentence explaining it. Invariant C0-01.

        ``transaction_scope="savepoint"`` is held to the same rule though it is not a
        bool: it is the one declaration that changes what a *successful* return means --
        the write is atomic but not yet durable -- so ruling R5 requires the sentence
        that surfaces wherever a result would otherwise imply durability.
        """
        missing = [
            f for f in CAPABILITY_FLAGS if not getattr(self, f) and not self.why.get(f, "").strip()
        ]
        if self.transaction_scope == "savepoint" and not self.why.get(
            "transaction_scope", ""
        ).strip():
            missing.append("transaction_scope")
        return tuple(missing)

    def reason(self, flag: str) -> str:
        """The adapter's own sentence for a False flag, verbatim."""
        return self.why.get(flag) or f"this backend does not provide {flag}"


# --------------------------------------------------------------------------- records


@dataclass(frozen=True)
class TypeRecord:
    """Identity is ``(namespace, kind, name)``. No surrogate -- PACKAGE.md 4.2."""

    namespace: str
    kind: str
    name: str
    definition: str
    created_by: str
    status: str
    predicates: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    attr_schema_version: int | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retire_reason: str | None = None
    retired_by: str | None = None
    retired_at: datetime | None = None
    successor: str | None = None


@dataclass(frozen=True)
class ProposalRecord:
    """``status`` is stored as given. The adapter validates no transition."""

    proposal_id: str
    namespace: str
    kind: str
    name: str
    definition: str
    proposed_by: str
    proposed_at: datetime
    status: str
    predicates: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence: list[Any] = field(default_factory=list)
    tier: str | None = None
    warnings: tuple[str, ...] = ()
    near_matches: list[Any] = field(default_factory=list)
    decided_by: str | None = None
    decided_at: datetime | None = None
    decision_reason: str | None = None
    superseded_by: str | None = None


@dataclass(frozen=True)
class ConsumerRecord:
    namespace: str
    consumer_id: str
    gate: str
    on_unknown: str
    registered_at: datetime
    owner: str | None = None
    locator: str | None = None


@dataclass(frozen=True)
class UsageRecord:
    namespace: str
    kind: str
    name: str
    count: int | None
    first_seen: datetime | None
    last_seen: datetime | None


@dataclass(frozen=True)
class EventRecord:
    """Append-only. There is no update or delete path for these anywhere."""

    event_id: str
    namespace: str
    at: datetime
    actor: str
    event: str
    kind: str | None = None
    name: str | None = None
    proposal_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- queries


@dataclass(frozen=True)
class TypeQuery:
    """Queries are objects so the protocol has fifteen methods rather than fifteen
    plus a signature that grows every time a filter is added.

    Two filters from INTERFACE.md 5.6 are deliberately absent: ``unverified_semantics``
    and ``orphaned``. Both are derived, and pushing them here would put registry policy
    inside the backend.
    """

    namespace: str | None = None
    kind: str | None = None
    status: str | None = None
    name_in: tuple[str, ...] | None = None
    predicate: str | None = None
    created_by: str | None = None
    include_retired: bool = False
    limit: int | None = None
    after: str | None = None


@dataclass(frozen=True)
class TypePage:
    records: tuple[TypeRecord, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    next_after: str | None = None


@dataclass(frozen=True)
class ProposalQuery:
    namespace: str | None = None
    name: str | None = None
    status: str | None = None
    limit: int | None = None
    after: str | None = None


@dataclass(frozen=True)
class ProposalPage:
    records: tuple[ProposalRecord, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    next_after: str | None = None


# -------------------------------------------------------------------------- protocol


@runtime_checkable
class StorageAdapter(Protocol):
    """The fifteen primitives -- PACKAGE.md 3.4.

    The uniform uncertainty rule: a primitive that cannot answer returns ``None`` (or a
    page with ``known=None, complete=False``) plus a ``why`` drawn from
    ``Capabilities.why`` -- never ``0``, never ``[]``, never ``False``.
    """

    # 1
    def capabilities(self) -> Capabilities: ...

    # 2
    def migrate(self) -> int: ...

    # 3
    def transaction(self) -> AbstractContextManager[None]: ...

    # 4
    def put_type(self, rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord: ...

    # 5
    def get_type(
        self, namespace: str, name: str, *, kind: str | None = None
    ) -> TypeRecord | None: ...

    # 6
    def find_types(self, q: TypeQuery) -> TypePage: ...

    # 7
    def put_proposal(
        self, rec: ProposalRecord, *, expect_absent: bool = False
    ) -> ProposalRecord: ...

    # 8
    def get_proposal(self, proposal_id: str) -> ProposalRecord | None: ...

    # 9
    def find_proposals(self, q: ProposalQuery) -> ProposalPage: ...

    # 10
    def put_consumer(self, rec: ConsumerRecord) -> ConsumerRecord: ...

    # 11
    def find_consumers(
        self, namespace: str, *, gate: str | None = None, consumer_id: str | None = None
    ) -> list[ConsumerRecord]: ...

    # 12
    def bump_usage(
        self,
        namespace: str,
        kind: str,
        name: str,
        *,
        at: datetime | None,
        by: str | None,
    ) -> None: ...

    # 13
    def get_usage(self, namespace: str, kind: str, name: str) -> UsageRecord | None: ...

    # 14
    def append_event(self, rec: EventRecord) -> None: ...

    # 15
    def read_events(
        self,
        namespace: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
    ) -> list[EventRecord]: ...


# ---------------------------------------------------------------- optional extension


@dataclass(frozen=True)
class AttrSchemaRecord:
    namespace: str
    kind: str
    version: int
    fields_json: dict[str, Any]
    additional: str
    mode: str
    registered_at: datetime
    registered_by: str


@dataclass(frozen=True)
class AttrObservedRecord:
    namespace: str
    kind: str
    key: str
    n: int
    first_seen: datetime
    last_seen: datetime
    example: Any = None
    schema_versions: tuple[int | None, ...] = ()


@runtime_checkable
class AttributeStore(Protocol):
    """An OPTIONAL extension, outside the fifteen and outside conformance.

    PACKAGE.md 5 specifies two more tables (``oo_attr_schema``, ``oo_attr_observed``)
    and one facade method, but adds no primitive to carry them, and ruling R2 keeps
    ``attribute_census`` package-local and outside the conformance definition. So it is
    here as a separate protocol: a backend that implements it gets the census and
    schema modes; a backend that does not is still fully conformant, and the registry
    reports the absence rather than pretending. Recorded as deviation D-2.
    """

    def put_attr_schema(self, rec: AttrSchemaRecord) -> AttrSchemaRecord: ...

    def get_attr_schema(
        self, namespace: str, kind: str, *, version: int | None = None
    ) -> AttrSchemaRecord | None: ...

    def observe_attributes(
        self,
        namespace: str,
        kind: str,
        attributes: dict[str, Any],
        *,
        at: datetime,
        schema_version: int | None,
    ) -> None: ...

    def read_attr_observed(
        self, namespace: str, *, kind: str | None = None
    ) -> list[AttrObservedRecord]: ...
