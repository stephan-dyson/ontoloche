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
    "EdgeRecord",
    "EdgeQuery",
    "EdgePage",
    "InvocationRecord",
    "InvocationPage",
    "StorageAdapter",
    "AttributeStore",
    "AttrSchemaRecord",
    "AttrObservedRecord",
    "CAPABILITY_FLAGS",
    "EDGE_CAPABILITY_FLAGS",
    "ACTION_CAPABILITY_FLAGS",
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
    # EDGES.md 6, row 4b. Four flags, and they are ORDINARY capability flags rather
    # than a separate tuple: `check_capability_matrix.py` declines one flag at a time
    # off this tuple, C0-01 requires a `why` off this tuple, and a `DegradedAdapter`
    # validates its kwargs against this tuple. An edge flag that lived somewhere else
    # would be an edge flag none of those three reached -- which is the shape of hole
    # row 3c measured when six of eight optional flags turned out to be undeclinable.
    "stores_edges",
    "stores_edge_events",
    "indexes_edges_by_family",
    "stores_edge_attributes",
    # ACTIONS.md 8, row 6b. Three flags, and they are ORDINARY capability flags for the
    # reason the edge four are: `check_capability_matrix.py` declines one flag at a time
    # off this tuple, C0-01 requires a `why` off this tuple, and a degraded double
    # validates its kwargs against this tuple. A flag that lived somewhere else would be
    # a flag none of those three reached -- the shape of hole row 3c measured when six of
    # eight optional flags turned out to be undeclinable.
    "stores_invocations",
    "stores_invocation_events",
    "indexes_invocations_by_family",
)

#: ACTIONS.md 8's three, named separately for the places that must talk about the
#: invocation store alone. `stores_invocations=False` means there is no invocation store,
#: and the other two are then **vacuous rather than declined** -- asking a type-only
#: registry to explain why it does not index invocations by family teaches an adapter
#: author to write sentences nobody reads, which is how a `why` dict stops being a
#: mechanism. C0-01's carve-out shape, applied to a third group; ACTIONS.md 8.1 says so
#: in those words.
ACTION_CAPABILITY_FLAGS = (
    "stores_invocations",
    "stores_invocation_events",
    "indexes_invocations_by_family",
)

#: EDGES.md 6's four, named separately for the places that must talk about the edge
#: store alone. `stores_edges=False` means there is no edge store, and the other three
#: are then vacuous rather than declined -- so a backend that declares the first False
#: is not required to explain the other three (`missing_why` below).
EDGE_CAPABILITY_FLAGS = (
    "stores_edges",
    "stores_edge_events",
    "indexes_edges_by_family",
    "stores_edge_attributes",
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
    #: EDGES.md 6, row 4b. Defaulted True-shaped? No -- `stores_edges` defaults to
    #: **False**, and that is the load-bearing choice. An adapter written against the
    #: fifteen-primitive protocol has no edge store; defaulting it True would make every
    #: such adapter claim one, and the registry would then call `put_edge` on an object
    #: that does not have it. The `edge_store_absent` refusal is the honest answer for a
    #: backend that predates this row, and it is what the default produces. (Naming the
    #: class it belongs to would trip C0-04, which forbids seven -- now twelve --
    #: identifiers in this file even in prose. Caught by the suite, not by me.)
    stores_edges: bool = False
    stores_edge_events: bool = False
    indexes_edges_by_family: bool = False
    stores_edge_attributes: bool = False
    #: ACTIONS.md 8, row 6b -- and the default is **False** for the same load-bearing
    #: reason `stores_edges` is. An adapter written against the eighteen-primitive
    #: protocol has no invocation store; defaulting True would make every such adapter
    #: claim one, and this package would then call the write primitive on an object that
    #: does not have it. The `action_store_absent` refusal is the honest answer for a
    #: backend that predates this row, and it is what the default produces.
    stores_invocations: bool = False
    stores_invocation_events: bool = False
    indexes_invocations_by_family: bool = False
    why: dict[str, str] = field(default_factory=dict)
    #: Ruling R5 / PACKAGE.md 3.5. ``"owned"`` -- this adapter owns the connection and
    #: ``transaction()`` commits at depth 0. ``"savepoint"`` -- the connection is the
    #: host's: ``transaction()`` brackets its writes in a SAVEPOINT, RELEASEs on clean
    #: exit, ROLLBACKs TO on exception, and NEVER commits. Atomicity (G2) holds inside
    #: the host's transaction; durability at clean exit belongs to the host, and
    #: ``why["transaction_scope"]`` is the sentence that says so.
    transaction_scope: Literal["owned", "savepoint"] = "owned"
    #: Beacon finding U3 / PACKAGE.md 3.2 and 5. The attribute keys this backend owns as
    #: TYPED COLUMNS: they round-trip through the column, not through the JSON blob.
    #: ``stores_attributes`` was binary, and a host-owned schema with pre-existing typed
    #: columns could not say "I own two named keys faithfully AND store no arbitrary
    #: ones". A key listed here survives a round trip whatever ``stores_attributes``
    #: says; a key not listed, on a ``stores_attributes=False`` backend, comes back
    #: ABSENT with a why -- never wrong, never invented.
    attribute_projections: frozenset[str] = frozenset()
    #: EDGES.md 6.2, ruling R5 inherited. The edge store may be a DIFFERENT store from
    #: the type store -- a host-owned edge table beside a package-owned registry -- so
    #: it gets its own declaration. One binding rule, checked by `scope_conflict()`
    #: below: when the two share a connection they MUST agree, because an adapter
    #: claiming that half its writes are the host's to commit and half are its own, on
    #: one transaction, is claiming something that cannot be true.
    edge_transaction_scope: Literal["owned", "savepoint"] = "owned"
    #: EDGES.md 6.3 -- beacon finding U3's shape, reused verbatim for edge payloads.
    #: `work_links` has `description` and `confidence` as real typed columns and no JSON
    #: blob: `stores_edge_attributes=True` would silently lose arbitrary keys and False
    #: alone would disclaim two the backend round-trips perfectly.
    edge_attribute_projections: frozenset[str] = frozenset()
    #: True when the edge store and the type store are the same store on one connection.
    #: The reference backends put `oo_edge` in the same schema as `oo_type`, so it is
    #: True there; a host-owned edge table beside a package-owned registry sets it False
    #: and may then declare two different scopes.
    edge_store_shares_connection: bool = True
    #: ACTIONS.md 8.2, ruling R5 inherited a second time. The invocation store may be a
    #: DIFFERENT store from the type store -- a host-owned audit table beside a
    #: package-owned registry is the obvious shape -- so it gets its own declaration,
    #: with the same binding rule `scope_conflict()` already enforces for edges. **With a
    #: third store there are now two independent pairs and `scope_conflict()` returns ONE
    #: sentence**; which one it names when both conflict is unspecified, recorded as Q42
    #: and ruled **R46**: the one-sentence return stays, because a list return changes a
    #: shipped signature for a case no backend has produced.
    action_transaction_scope: Literal["owned", "savepoint"] = "owned"
    #: The PREMISE of that rule, declared up front rather than discovered. EDGES.md 6's
    #: printed block omitted its own twin while PACKAGE.md printed it and the code
    #: carried it -- *a rule whose premise is unstated is a rule an adapter author can
    #: miss by reading* -- and that omission cost an adversarial round. Repeating the
    #: finding one row later would be worse than the original.
    action_store_shares_connection: bool = True

    def missing_why(self) -> tuple[str, ...]:
        """Flags that are False with no sentence explaining it. Invariant C0-01.

        ``transaction_scope="savepoint"`` is held to the same rule though it is not a
        bool: it is the one declaration that changes what a *successful* return means --
        the write is atomic but not yet durable -- so ruling R5 requires the sentence
        that surfaces wherever a result would otherwise imply durability.
        """
        skip: set[str] = set()
        if not self.stores_edges:
            # EDGES.md 6: `stores_edges=False` means there is no edge store behind this
            # adapter. The other three flags are then not DECLINED, they are vacuous --
            # asking a type-only registry to explain why it does not index edges by
            # family teaches an adapter author to write three sentences nobody reads,
            # which is how a `why` dict stops being the mechanism 3.2 says it is.
            skip = {"stores_edge_events", "indexes_edges_by_family", "stores_edge_attributes"}
        if not self.stores_invocations:
            # ACTIONS.md 8.1, C0-01's carve-out shape applied to a third group: with no
            # invocation store the other two are VACUOUS, not declined -- *"why do you
            # not index invocations by family?"* has no answer beyond the first sentence.
            skip |= {"stores_invocation_events", "indexes_invocations_by_family"}
        missing = [
            f
            for f in CAPABILITY_FLAGS
            if f not in skip and not getattr(self, f) and not self.why.get(f, "").strip()
        ]
        if self.transaction_scope == "savepoint" and not self.why.get(
            "transaction_scope", ""
        ).strip():
            missing.append("transaction_scope")
        # The same rule for the edge scope, and it is NOT a duplicate of the line above:
        # EDGES.md 6.2 permits the two to differ when they are two connections, and it
        # is then the edge scope's own sentence a caller needs -- "who commits an edge
        # write" is a different question from "who commits a type write" the moment the
        # answers differ.
        if self.edge_transaction_scope == "savepoint" and not self.why.get(
            "edge_transaction_scope", ""
        ).strip():
            missing.append("edge_transaction_scope")
        # ACTIONS.md 8.2, and NOT a duplicate of the two lines above for the reason the
        # edge one is not a duplicate of the type one: the rule permits the scopes to
        # differ when they are different connections, and *"who commits an invocation
        # write"* is a different question from *"who commits a type write"* the moment
        # the answers differ.
        if self.action_transaction_scope == "savepoint" and not self.why.get(
            "action_transaction_scope", ""
        ).strip():
            missing.append("action_transaction_scope")
        return tuple(missing)

    def scope_conflict(self) -> str | None:
        """EDGES.md 6.2's binding rule, as a value rather than as prose.

        > When the edge store and the type store share a connection,
        > ``edge_transaction_scope`` MUST equal ``transaction_scope``. A ``Capabilities``
        > that declares two different scopes on one connection is non-conformant.

        Returned as a sentence rather than raised, so the conformance suite can report
        it the way it reports every other declaration problem, and so a `Capabilities`
        stays a plain frozen record that a test can construct in any shape it likes.
        """
        if self.edge_store_shares_connection and (
            self.edge_transaction_scope != self.transaction_scope
        ):
            return (
                f"edge_transaction_scope={self.edge_transaction_scope!r} and "
                f"transaction_scope={self.transaction_scope!r} on ONE connection "
                f"(edge_store_shares_connection=True): half the writes cannot be the "
                f"host's to commit and half this adapter's, on one transaction "
                f"(EDGES.md 6.2)"
            )
        # ACTIONS.md 8.2, the SECOND independent pair. The edge pair is reported first
        # when both conflict, and which one it names is **unspecified** rather than
        # decided here -- Q42, ruled **R46**: a list return would change a shipped
        # method's signature for a case no backend has produced. It is recorded as an
        # open question rather than left as an accident of statement order.
        if self.action_store_shares_connection and (
            self.action_transaction_scope != self.transaction_scope
        ):
            return (
                f"action_transaction_scope={self.action_transaction_scope!r} and "
                f"transaction_scope={self.transaction_scope!r} on ONE connection "
                f"(action_store_shares_connection=True): half the writes cannot be the "
                f"host's to commit and half this adapter's, on one transaction "
                f"(ACTIONS.md 8.2)"
            )
        return None

    def stores_edge_attribute(self, key: str) -> bool:
        """Does THIS edge payload key survive a round trip? -- EDGES.md 6.3, U3's shape."""
        return self.stores_edge_attributes or key in self.edge_attribute_projections

    def surviving_edge_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """The subset of an edge payload this backend will hand back. EDGES.md 6.3."""
        if self.stores_edge_attributes:
            return dict(attributes)
        return {k: v for k, v in attributes.items() if k in self.edge_attribute_projections}

    def reason(self, flag: str) -> str:
        """The adapter's own sentence for a False flag, verbatim."""
        return self.why.get(flag) or f"this backend does not provide {flag}"

    def stores_attribute(self, key: str) -> bool:
        """Does THIS key survive a round trip? -- beacon finding U3.

        ``stores_attributes`` answers for arbitrary keys; ``attribute_projections``
        answers for the ones the backend owns as typed columns. A caller asking about a
        single key wants this, not either field alone.
        """
        return self.stores_attributes or key in self.attribute_projections

    def surviving_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """The subset of ``attributes`` this backend will hand back. U3."""
        if self.stores_attributes:
            return dict(attributes)
        return {k: v for k, v in attributes.items() if k in self.attribute_projections}


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
    #: Ruling R21, row 3e. The SOURCE's own version at the moment the proposal was
    #: made, carried to the ``Provenance`` written at approval. Not a column of its own
    #: on ``oo_type``: on an approved entry it lives inside ``provenance_json``, which
    #: is where every other provenance field lives.
    source_version: str | None = None


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
    #: EDGES.md 5.2 -- the edge this event concerns, if any. `EventRecord` had
    #: kind/name/proposal_id and no slot for an edge, so an edge event had
    #: nowhere to go. Additive, defaulted, and set by no v0 code path, because
    #: row #4 is a spec. It is added in the change that specifies it for the
    #: reason ruling R3 gives about the closed reason vocabulary: a shape a
    #: document says exists and the code does not have is drift, whichever side
    #: moved. (Naming that class here would trip C0-04, which forbids the
    #: identifier in this file even in prose -- caught by the suite, not by me.)
    #: The three event values that go with it are `edge_added`,
    #: `edge_retracted` and `edge_amended` -- stored, never judged (PACKAGE 3.1).
    edge_id: str | None = None
    #: ACTIONS.md 3.5 -- the invocation this event concerns, if any. Same shape and
    #: same reason as the line above, one object along: `EventRecord` had no slot for
    #: an invocation, so an invocation event had nowhere to go and an invocation's
    #: provenance history would have been permanently empty with a fabricated `why`.
    #: (Naming the provenance class here would trip C0-04, exactly as naming the edge
    #: class one field above would -- row 6b extended that list the day it landed the
    #: shapes, and this line is the first thing it caught.) Additive, defaulted, and
    #: set by no v0 code path, because row #6 is a spec. The three event values are
    #: `invocation_recorded`, `invocation_reviewed` and `invocation_compensated` --
    #: stored, never judged (PACKAGE 3.1).
    #:
    #: Added by row #6's FIRST adversarial round, which found the specification
    #: describing this field, `read_events`' filter for it and a `review` mode that
    #: reads it -- while the change that landed six refusal values never touched this
    #: file. The edge line above is the precedent it failed to follow.
    invocation_id: str | None = None
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


# ----------------------------------------------------------------------- edges (7.1)
#
# EDGES.md 7.1. Flat, JSON-shaped, and deliberately NOT the facade objects: the store
# holds `(family, src, dst)` with a blob of provenance and a `status` string it never
# judges. The rich shapes -- the ones with structured references, a computed warnings
# list and a depth-bounded report -- live in `ontoloche/edges.py` and are forbidden
# here by 3.1, which C0-04 enforces by source inspection.


@dataclass(frozen=True)
class EdgeRecord:
    """One stored relationship. EDGES.md 7.1.

    ``edge_id`` is generated ABOVE the store, exactly as ``proposal_id`` and
    ``event_id`` are (4.2), so there is no uniqueness flag for it to need and no
    surrogate key for a rebuild to renumber.

    The four retraction columns are here for the reason ``TypeRecord``'s are: a backend
    with ``stores_edge_events=False`` still has to answer *"why is this retracted?"*.
    EDGES.md 2.6 turns on that -- the record IS the audit trail, so an unrecordable
    retraction warns rather than refusing, which is a deliberate departure from 3.6.
    """

    edge_id: str
    namespace: str  # the FAMILY's namespace -- never the endpoints'. EDGES.md 2.2
    family: str
    src_namespace: str
    src_kind: str
    src_name: str
    src_instance_id: str | None
    dst_namespace: str
    dst_kind: str
    dst_name: str
    dst_instance_id: str | None
    attributes: dict[str, Any] = field(default_factory=dict)
    attr_schema_version: int | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    status: str = "active"  # "active" | "retracted" -- STORED, never judged (3.1)
    warnings: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retract_reason: str | None = None
    retracted_by: str | None = None
    retracted_at: datetime | None = None


@dataclass(frozen=True)
class EdgeQuery:
    """EDGES.md 7.1. ``incident_to`` is what makes one call serve a whole depth level.

    Traversal is deliberately NOT pushed down: an adapter that knew about ``depth``
    would know about the report shape, and 3.1's source-inspection rule would have a new
    identifier to police. The registry issues one ``find_edges`` per level with the whole
    frontier in ``incident_to``, and pages it to exhaustion.
    """

    namespace: str | None = None  # the family's namespace. None = any
    families: tuple[str, ...] | None = None
    #: ``(namespace, kind, name, instance_id)`` per frontier node; ``instance_id`` is
    #: ``None`` for a type-level reference, and that ``None`` is a value to match on,
    #: not a wildcard -- a type node and an instance of it are two different endpoints.
    incident_to: tuple[tuple[str, str, str, str | None], ...] | None = None
    direction: str = "both"  # "both" | "out" | "in"
    include_retracted: bool = False
    edge_ids: tuple[str, ...] | None = None
    limit: int | None = None  # the ADAPTER pages. R13: the facade does not
    after: str | None = None  # opaque cursor; ordering is (created_at, edge_id)


@dataclass(frozen=True)
class EdgePage:
    records: tuple[EdgeRecord, ...]
    #: ``None`` = the backend cannot count. NOT ``0``. Rule U -- and unlike
    #: the read seam's own ``known`` (a plain ``int``, because that report materialises
    #: its edges) a store genuinely may be unable to count without materialising.
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    next_after: str | None = None


@dataclass(frozen=True)
class InvocationRecord:
    """One stored use of one verb. ACTIONS.md 9.

    ``invocation_id`` is generated ABOVE the store, exactly as ``proposal_id``,
    ``event_id`` and ``edge_id`` are (PACKAGE.md 4.2), so there is no uniqueness flag for
    it to need -- a key this package mints is unique by construction, and a flag would
    assert nothing.

    **Both effect lists are on the record and neither is optional.** ACTIONS.md 8 argues
    the absence of a `stores_invocation_effects` flag from exactly this: an invocation
    whose ``declared_effects`` did not round-trip cannot answer 3.3's comparison, which
    is the mechanism. Same for ``inputs`` -- an invocation without its inputs is not a
    degraded record, it is not a record, so there is one flag rather than two because
    there is no partial case.

    **Evidence and history are NOT here.** They go through ``append_event``'s existing
    path with ``invocation_id`` set (ACTIONS.md 3.5), which is where a provenance history
    already lives. Putting them on this record would give one concept two homes and would
    make a backend that stores invocations but not events undescribable.
    """

    invocation_id: str
    #: the FAMILY's namespace -- never the inputs'. EDGES.md 2.2's rule, inherited
    namespace: str
    family: str
    #: JSON-serialisable. The typed reference shapes live in `ontoloche/actions.py`
    #: and are forbidden here by PACKAGE.md 3.1, which C0-04 enforces by source
    #: inspection
    inputs: dict[str, Any] = field(default_factory=dict)
    declared_effects: tuple = ()
    observed_effects: tuple = ()
    #: the policy the gate judged, copied for the reason the effects are (rule 3-8)
    declared_policy: dict[str, Any] = field(default_factory=dict)
    family_version: int = 1
    #: STORED, never judged (PACKAGE.md 3.1). The adapter holds the string
    outcome: str = "applied"
    refusal_reason: str | None = None
    #: three values, and `not_asked` is one of them -- STORED, never judged
    gate_verdict: str = "not_asked"
    #: the FORWARD pointer only. The store never rewrites a row (INTERFACE.md 5.8), and
    #: the compensating invocation is written AFTER the one it compensates, so the
    #: backward pointer is DERIVED by the facade. Stated because the asymmetry is real
    #: and a reader who saw only the surface would look for a field this does not have
    compensates: str | None = None
    created_at: datetime | None = None
    created_by_actor: str = ""
    created_by: str = "user"
    model_tier: str | None = None
    confidence: float | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    source_version: str | None = None
    attr_schema_version: int | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class InvocationPage:
    """ACTIONS.md 9 -- a Page, not a 2-tuple, and the reason is ``known``.

    The read seam requires ``known`` to be ``int | None`` because *a backend entitled to
    say "we did not count" must have somewhere to say it*. A ``(page, truncated)`` tuple
    gives the backend nowhere, so the facade could only ever report ``len(rows)`` -- the
    falsification that rule forbids -- or ``None`` by fiat regardless of what the backend
    knew. Every other paging primitive in this package already returns this shape; the
    2-tuple was a round-1 finding and the fix is to stop being different.
    """

    records: tuple[InvocationRecord, ...]
    #: ``None`` = the BACKEND cannot count. NOT ``0``. Rule U
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    #: keyset: ``(created_at, invocation_id)``. The registry does NOT expose this
    #: (ruling **R25**/**R58** route paging to Phase 3); the primitive has one so the
    #: facade can bound its own reads honestly. An offset page over an append-only table
    #: shifts under a concurrent write, and an invocation ledger is append-only by
    #: construction
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
        edge_id: str | None = None,
        # **Row 6b lands this, and the ORDER is the whole lesson.** ACTIONS.md 9.1
        # specifies the filter and says the build row owes *"one keyword, one
        # `oo_event` column, six implementations"* -- because row #6's first fix
        # pass added it to this Protocol ALONE: `runtime_checkable` matches on
        # method NAMES so `isinstance` stayed True, `check_spec_drift.py` compares
        # the printed signature against this Protocol rather than against the
        # backends, and every shipped adapter raised `TypeError` on the keyword.
        # That is deviation D-4b-2 reproduced inside the fix that quotes it, and
        # row #6's second adversarial round took the amendment back out. It lands
        # here in the change that lands the six implementations and the column,
        # which is the only order in which the Protocol is telling the truth.
        invocation_id: str | None = None,
    ) -> list[EventRecord]: ...

    # ------------------------------------------------------------------ 19 to 21
    # ACTIONS.md 9. Three, not eight -- and as in EDGES.md 7.1 that number is the
    # strongest available evidence that 2.1's decision was right: **families need no new
    # primitive, because put_type/get_type/find_types already serve them.**
    #
    # On the protocol rather than in a separate optional extension, with the
    # `stores_proposals=False` treatment: the methods exist, `stores_invocations=False`
    # raises `NotSupported`, and this package checks the capability first and never calls
    # them. An adapter written before this row declares `stores_invocations=False` by
    # default and every invocation call returns `action_store_absent`.

    # 19
    def put_invocation(self, rec: InvocationRecord) -> InvocationRecord: ...

    # 20
    def get_invocation(self, invocation_id: str) -> InvocationRecord | None: ...

    # 21
    def find_invocations(
        self,
        *,
        family: str | None = None,
        namespace: str | None = None,
        actor: str | None = None,
        outcome: str | None = None,
        since: datetime | None = None,
        # **The last three are round 2's, and their omission was ACTIONS.md 4's whole
        # argument failing quietly.** They are the three reads a governance layer exists
        # to serve -- the override query, the blast-radius query and the review queue --
        # and they were on the facade and on NO primitive, so *"the registry filters
        # above the store"* meant *read a page, then filter it*: on a pinned
        # 2,399-dataset ledger with one override at row 1,200 the query returned **zero
        # rows**, `complete=False`. A floor of zero is not a conservative measurement; it
        # is the wrong one, and it is indistinguishable from a clean deployment.
        gate_verdict: str | None = None,
        effect_undeclared: bool | None = None,
        unreviewed: bool | None = None,
        # **Row 6b's round 2.** ACTIONS.md 9 stores only the FORWARD pointer and the
        # facade derives the backward one, and the first cut derived it by WALKING the
        # ledger -- bounded, so it reported the wrong `outcome` past the bound, and
        # O(limit x ledger) because it ran once per returned row (measured at 200,020
        # row reads for twenty rows). It is one indexed lookup now. That is round 2 of
        # the SPEC row's own finding, one derivation along: *the three filters with no
        # push-down were exactly the three governance reads.*
        compensates: str | None = None,
        after: str | None = None,
        limit: int = 100,
    ) -> InvocationPage: ...

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
    def put_edge(self, rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord: ...

    # 17
    def get_edge(self, edge_id: str) -> EdgeRecord | None: ...

    # 18
    def find_edges(self, q: EdgeQuery) -> EdgePage: ...


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
    #: Ruling R10, row 3e -- ``None`` is the per-kind schema, a string is a schema for
    #: that one type which shadows it. Stored as the empty string, which no type name
    #: can be (INTERFACE.md 2.1's ``^[a-z][a-z0-9_]{0,63}$``), so the store needs no
    #: nullable primary-key column and the two cases stay distinguishable.
    name: str | None = None


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
        self,
        namespace: str,
        kind: str,
        *,
        name: str | None = None,
        version: int | None = None,
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
