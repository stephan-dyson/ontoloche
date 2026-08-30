"""A THROWAWAY in-memory implementation of EDGES.md v0, for the design tests.

Row #4 is a spec and ships no edge store. But 3c's lesson was blunt -- *every
finding of substance came from driving the real registry through a real
scenario, none from reading* -- so the three design tests in EDGES.md 9-11 are
walked by executing the spec against real rows rather than by reasoning about
it. This module is that execution: it is deliberately in ``docs/tools`` and not
in ``ontoloche``, it is not imported by the package, and the contract suite
does not know it exists.

What it implements, and nothing more:

* EDGES 2.1 ``TypeRef`` / ``InstanceRef``
* EDGES 2.2 ``Edge``
* EDGES 2.4 the family's declared shape, incl. ``level`` and ``endpoint_kinds``
* EDGES 2.4.1 the endpoint rule, enforced at family-DECLARATION time:
  instance-level declares only ``entity``; no family at either level may
  declare ``predicate``
* EDGES 4 ``neighbors`` with the depth cap, Rule K/U fields, ``at_depth``,
  per-level page exhaustion and the assembly bound
* EDGES 6 the four capability flags and two declarations, enough of them to
  make the refusals real (driven by ``edges_capability_probe.py``)

The refusal vocabulary is imported from ``ontoloche.types`` rather than
re-declared, so a probe that invented a reason would fail here rather than in a
reviewer's head.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Iterable, Literal, Sequence

from ontoloche.types import REFUSAL_REASONS

# --------------------------------------------------------------------------
# EDGES 2.1 -- references


@dataclass(frozen=True)
class TypeRef:
    namespace: str
    kind: str
    name: str

    def __str__(self) -> str:  # "dpr:value_set:borough"
        return f"{self.namespace}:{self.kind}:{self.name}"


@dataclass(frozen=True)
class InstanceRef:
    type: TypeRef
    id: str  # EDGES 2.1 -- opaque str, deliberately not int

    def __str__(self) -> str:
        return f"{self.type}#{self.id}"


NodeRef = TypeRef | InstanceRef


def _type_of(node: NodeRef) -> TypeRef:
    return node.type if isinstance(node, InstanceRef) else node


def _level_of(node: NodeRef) -> str:
    return "instance" if isinstance(node, InstanceRef) else "type"


# --------------------------------------------------------------------------
# EDGES 2.4 -- the family, which in the real design is a TypeEntry(kind="edge")


@dataclass(frozen=True)
class Family:
    """A ``kind="edge"`` TypeEntry, reduced to the fields EDGES 2.4 declares.

    In the real design these five live in ``TypeEntry.attributes`` under one
    ``AttributeSchema`` keyed ``(namespace, "edge")``. Here they are fields,
    because the probe is not testing PACKAGE 5.
    """

    name: str
    level: Literal["type", "instance"]   # REQUIRED, no default -- EDGES 2.4
    namespace: str = "default"
    definition: str = ""
    symmetric: bool = False
    inverse_label: str | None = None
    endpoint_kinds: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {"src": ("entity",), "dst": ("entity",)}
    )
    payload_schema: str | None = None
    status: Literal["proposed", "active", "retired"] = "active"

    def __post_init__(self) -> None:
        # EDGES 2.4: the one cross-field rule the schema mechanism cannot check
        # (PACKAGE 5.6), so the registry checks it at family-approval time. Q13.
        if self.symmetric and self.inverse_label is not None:
            raise ValueError(
                f"family {self.name!r}: symmetric families have no inverse_label "
                "(EDGES 2.4)"
            )
        if self.level not in ("type", "instance"):
            raise ValueError("level must be 'type' or 'instance'")
        # EDGES 2.4.1, general rule (NOT a per-family opt-in): a predicate is
        # never an endpoint. Two predicates being "equivalent" is a claim about
        # extents, and merge_types refusal #2 is non-overridable for that reason.
        # Leaving it to each family author to remember is the kind of protection
        # this project refuses to depend on.
        for end, kinds in self.endpoint_kinds.items():
            if "predicate" in kinds:
                raise ValueError(
                    f"family {self.name!r}: `predicate` may not be an endpoint kind "
                    f"({end}) -- EDGES 2.4.1, the kill row"
                )
            # The instance clause is structural too, for the same reason: a
            # level="instance" family that DECLARES `edge` as an endpoint kind
            # would reify an edge instance, and checking only membership let it
            # through. Found by writing the test for the predicate clause.
            if self.level == "instance" and set(kinds) - {"entity"}:
                raise ValueError(
                    f"family {self.name!r}: a level='instance' family may only "
                    f"declare `entity` endpoints ({end} declares {sorted(kinds)}) "
                    "-- EDGES 2.4.1, the reification ban"
                )


@dataclass(frozen=True)
class EdgeProvenance:
    created_at: datetime
    created_by_actor: str
    created_by: Literal["seed", "ai", "user"]
    confidence: float | None = None  # None != 0.0, Rule U
    evidence: tuple[dict, ...] = ()
    source_version: str | None = None  # EDGES 5.3
    retracted_by: str | None = None
    retracted_at: datetime | None = None
    retract_reason: str | None = None
    history: tuple[dict, ...] = ()
    history_why: str | None = None


@dataclass(frozen=True)
class Edge:
    edge_id: str
    family: str
    namespace: str
    src: NodeRef
    dst: NodeRef
    provenance: EdgeProvenance
    attributes: dict = field(default_factory=dict)
    status: Literal["active", "retracted"] = "active"
    warnings: tuple[str, ...] = ()
    attr_schema_version: int | None = None


@dataclass(frozen=True)
class Refusal:
    refused: bool
    reason: str
    detail: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # The vocabulary is closed (INTERFACE 5.12, ruling R3). Imported, not
        # re-declared, so a probe cannot quietly widen it.
        if self.reason not in REFUSAL_REASONS:
            raise ValueError(f"{self.reason!r} is not in the closed vocabulary")


@dataclass(frozen=True)
class NeighborEdge:
    edge: Edge
    at_depth: int  # EDGES 4.4 -- not decoration


@dataclass(frozen=True)
class NeighborReport:
    origin: NodeRef
    depth_requested: int
    depth_reached: int
    direction: str
    families_searched: tuple[str, ...]
    edges: tuple[NeighborEdge, ...]
    nodes: tuple[NodeRef, ...]
    known: int          # plain int, NOT int | None -- INTERFACE 3. See EDGES 4.1
    complete: bool
    why_incomplete: str | None = None
    warnings: tuple[str, ...] = ()


# --------------------------------------------------------------------------
# EDGES 6 -- capabilities


# EDGES 4.2 -- the assembly bound's default. A number, not None: an opt-in
# circuit breaker is not a circuit breaker.
DEFAULT_MAX_EDGES = 10_000


@dataclass(frozen=True)
class EdgeCapabilities:
    stores_edges: bool = True
    stores_edge_events: bool = True
    indexes_edges_by_family: bool = True
    stores_edge_attributes: bool = True
    edge_transaction_scope: Literal["owned", "savepoint"] = "owned"
    edge_attribute_projections: frozenset[str] = frozenset()
    why: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # PACKAGE 3.2's invariant, applied to the edge flags: every False flag
        # carries a non-empty sentence.
        for flag in (
            "stores_edges",
            "stores_edge_events",
            "indexes_edges_by_family",
            "stores_edge_attributes",
        ):
            if getattr(self, flag) is False and not self.why.get(flag):
                raise ValueError(f"{flag}=False needs a non-empty why (PACKAGE 3.2)")


# --------------------------------------------------------------------------
# EDGES 7.1 -- the flat record shapes the ADAPTER speaks.
#
# Round 3: the first version of this kit had `EdgeStore` storing and returning
# `Edge` objects -- the rich facade dataclass with structured NodeRefs, an
# EdgeProvenance and computed warnings. So the boundary EDGES 7.1 calls "the
# strongest evidence that 2.3's decision was right", and which PACKAGE 3.1 makes
# a testable rule ("the identifiers ... do not appear in adapter.py"), was
# asserted and never exercised: the probe's adapter was coupled to the facade.
# It now speaks flat records, and `_assert_boundary()` below checks it the way
# C0-04 checks the real one.


@dataclass(frozen=True)
class EdgeRecord:
    edge_id: str
    namespace: str
    family: str
    src_namespace: str; src_kind: str; src_name: str; src_instance_id: str | None
    dst_namespace: str; dst_kind: str; dst_name: str; dst_instance_id: str | None
    attributes: dict
    attr_schema_version: int | None
    provenance: dict                # the whole EdgeProvenance, JSON-shaped. Opaque.
    status: str                     # STORED, never judged
    warnings: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    retract_reason: str | None
    retracted_by: str | None
    retracted_at: datetime | None


@dataclass(frozen=True)
class EdgeQuery:
    namespace: str | None = None
    families: tuple[str, ...] | None = None
    incident_to: tuple[tuple[str, str, str, str | None], ...] | None = None
    symmetric_families: frozenset[str] = frozenset()
    direction: str = "both"
    include_retracted: bool = False
    edge_ids: tuple[str, ...] | None = None
    limit: int | None = None
    after: str | None = None


@dataclass(frozen=True)
class EdgePage:
    records: tuple[EdgeRecord, ...]
    known: int | None               # None = the backend cannot count. NOT 0. Rule U
    complete: bool
    why_incomplete: str | None
    next_after: str | None


def _key(node: NodeRef) -> tuple[str, str, str, str | None]:
    t = _type_of(node)
    return (t.namespace, t.kind, t.name,
            node.id if isinstance(node, InstanceRef) else None)


def _to_record(e: Edge) -> EdgeRecord:
    sk, dk = _key(e.src), _key(e.dst)
    return EdgeRecord(
        edge_id=e.edge_id, namespace=e.namespace, family=e.family,
        src_namespace=sk[0], src_kind=sk[1], src_name=sk[2], src_instance_id=sk[3],
        dst_namespace=dk[0], dst_kind=dk[1], dst_name=dk[2], dst_instance_id=dk[3],
        attributes=dict(e.attributes), attr_schema_version=e.attr_schema_version,
        provenance={
            "created_at": e.provenance.created_at,
            "created_by_actor": e.provenance.created_by_actor,
            "created_by": e.provenance.created_by,
            "confidence": e.provenance.confidence,
            "evidence": list(e.provenance.evidence),
            "source_version": e.provenance.source_version,
            "history": list(e.provenance.history),
            "history_why": e.provenance.history_why,
        },
        status=e.status, warnings=tuple(e.warnings),
        created_at=e.provenance.created_at, updated_at=e.provenance.created_at,
        retract_reason=e.provenance.retract_reason,
        retracted_by=e.provenance.retracted_by,
        retracted_at=e.provenance.retracted_at,
    )


def _ref(ns: str, kind: str, name: str, iid: str | None) -> NodeRef:
    t = TypeRef(ns, kind, name)
    return InstanceRef(t, iid) if iid is not None else t


def _from_record(r: EdgeRecord) -> Edge:
    pr = r.provenance
    return Edge(
        edge_id=r.edge_id, family=r.family, namespace=r.namespace,
        src=_ref(r.src_namespace, r.src_kind, r.src_name, r.src_instance_id),
        dst=_ref(r.dst_namespace, r.dst_kind, r.dst_name, r.dst_instance_id),
        provenance=EdgeProvenance(
            created_at=pr["created_at"], created_by_actor=pr["created_by_actor"],
            created_by=pr["created_by"], confidence=pr["confidence"],
            evidence=tuple(pr["evidence"]), source_version=pr["source_version"],
            retracted_by=r.retracted_by, retracted_at=r.retracted_at,
            retract_reason=r.retract_reason,
            history=tuple(pr["history"]), history_why=pr["history_why"],
        ),
        attributes=dict(r.attributes), status=r.status,
        warnings=tuple(r.warnings), attr_schema_version=r.attr_schema_version,
    )


# --------------------------------------------------------------------------
# EDGES 7.1 -- the three primitives, and the registry facade over them


class EdgeStore:
    """Primitives 16, 17, 18. Stores records, decides nothing (PACKAGE 3.1)."""

    def __init__(self, caps: EdgeCapabilities | None = None) -> None:
        self.caps = caps or EdgeCapabilities()
        self._edges: dict[str, EdgeRecord] = {}
        self._n = 0

    def put_edge(self, rec: EdgeRecord) -> EdgeRecord:
        """Primitive 16. Stores the record as given; validates no transition."""
        self._edges[rec.edge_id] = rec
        return rec

    def get_edge(self, edge_id: str) -> EdgeRecord | None:
        """Primitive 17. ``None`` means absent, which is a fact, not an unknown."""
        return self._edges.get(edge_id)

    def find_edges(self, q: EdgeQuery) -> EdgePage:
        """Primitive 18. Takes an EdgeQuery, returns an EdgePage.

        `after` is an opaque cursor -- here, a stringified index into the store's
        stable order, which is all a probe needs. EDGES 7.1 keyset-pages on
        (created_at, edge_id); the registry's obligation is the same either way:
        exhaust the pages for a level, or say the level is incomplete.
        """
        incident_to = q.incident_to
        families = q.families
        symmetric_families = q.symmetric_families
        direction = q.direction
        include_retracted = q.include_retracted
        limit, after = q.limit, (int(q.after) if q.after is not None else None)
        keys = set(incident_to) if incident_to is not None else None
        matched: list[EdgeRecord] = []
        suppressed = 0
        # EDGES 6: indexes_edges_by_family=False means the store CANNOT apply the
        # family filter. It returns the node's edges unfiltered and complete for
        # what it was asked; the registry narrows above. This is the deliberate
        # deviation from find_types' rule -- see EDGES 7.1.
        apply_family_filter = families is not None and self.caps.indexes_edges_by_family
        for e in self._edges.values():
            src_k = (e.src_namespace, e.src_kind, e.src_name, e.src_instance_id)
            dst_k = (e.dst_namespace, e.dst_kind, e.dst_name, e.dst_instance_id)
            if e.status == "retracted" and not include_retracted:
                if keys is None or src_k in keys or dst_k in keys:
                    suppressed += 1
                continue
            if apply_family_filter and e.family not in families:
                continue
            if keys is not None:
                out_hit = src_k in keys
                in_hit = dst_k in keys
                # EDGES 2.2/4.1: a SYMMETRIC family has no direction. `A eq B`
                # IS `B eq A`, so filtering on stored src/dst would make the
                # answer depend on which publisher happened to write it first --
                # a confident, complete, FALSE negative. Round 2's BLOCKING.
                if e.family in symmetric_families:
                    if not (out_hit or in_hit):
                        continue
                elif direction == "out" and not out_hit:
                    continue
                elif direction == "in" and not in_hit:
                    continue
                elif direction == "both" and not (out_hit or in_hit):
                    continue
            matched.append(e)
        why = None
        if suppressed:
            why = (
                f"{suppressed} retracted edge(s) suppressed by include_retracted=False; "
                "a default that hides things sets complete=False (INTERFACE 5.6)"
            )
        start = after or 0
        page = matched[start:] if limit is None else matched[start:start + limit]
        nxt = None
        if limit is not None and start + limit < len(matched):
            nxt = str(start + limit)
        return EdgePage(
            records=tuple(page),
            known=len(matched),
            complete=suppressed == 0,
            why_incomplete=why,
            next_after=nxt,
        )


class EdgeRegistry:
    """The facade: EDGES 2.4.1's endpoint rule, 2.6's lifecycle, 4's read seam."""

    def __init__(
        self,
        families: Iterable[Family] = (),
        store: EdgeStore | None = None,
        registered_types: Iterable[TypeRef] = (),
        max_edges: int | None = DEFAULT_MAX_EDGES,
        page_size: int | None = None,
    ) -> None:
        # EDGES 4.2: the depth cap bounds HOPS, not degree. The assembly bound
        # is what bounds degree, and it is ON BY DEFAULT -- round 3 pointed out
        # that an opt-in circuit breaker leaves the DEFAULT as exactly the
        # unbounded materialisation R13 exists to prevent. Passing
        # ``max_edges=None`` disables it, which is a deliberate act.
        self.max_edges = max_edges
        self.page_size = page_size
        self.families = {f.name: f for f in families}
        self.store = store
        # EDGES 2.7: endpoint_kind_mismatch fires only when the endpoint's type
        # IS registered. Anything absent from this set is unknown, not wrong.
        self.registered_types = {str(t) for t in registered_types}
        self._seq = 0

    # -- writes ---------------------------------------------------------

    def add_edge(
        self,
        family: str,
        src: NodeRef,
        dst: NodeRef,
        provenance: EdgeProvenance,
        *,
        namespace: str = "default",
        attributes: dict | None = None,
    ) -> Edge | Refusal:
        if self.store is None or not self.store.caps.stores_edges:
            return Refusal(True, "edge_store_absent", {"family": family})
        fam = self.families.get(family)
        if fam is None or fam.namespace != namespace:
            return Refusal(True, "edge_family_unknown", {"families": [family]})

        for end, node in (("src", src), ("dst", dst)):
            # Level first: a level mismatch makes the kind question meaningless.
            if _level_of(node) != fam.level:
                return Refusal(
                    True,
                    "endpoint_kind_mismatch",
                    {
                        "endpoint": end,
                        "problem": "level",
                        "family_level": fam.level,
                        "node_level": _level_of(node),
                        "node": str(node),
                    },
                )
            kind = _type_of(node).kind
            if kind not in fam.endpoint_kinds[end]:
                return Refusal(
                    True,
                    "endpoint_kind_mismatch",
                    {
                        "endpoint": end,
                        "problem": "kind",
                        "declared": list(fam.endpoint_kinds[end]),
                        "node_kind": kind,
                        "node": str(node),
                    },
                )

        warnings: list[str] = []
        for node in (src, dst):
            t = _type_of(node)
            if str(t) not in self.registered_types:
                # Rule U: a positive claim about a mismatch requires having
                # looked. Same shape as gate_unregistered (ruling R8).
                warnings.append(f"endpoint_type_unregistered:{t}")

        attrs = dict(attributes or {})
        caps = self.store.caps
        if not caps.stores_edge_attributes:
            # PACKAGE 3.4 primitive 4's mechanism, unchanged: the RETURNED record
            # is the signal -- a key that did not round-trip is absent from it,
            # and Capabilities.why says why. No warning value is minted for this;
            # the type side does not have one either.
            attrs = {k: v for k, v in attrs.items()
                     if k in caps.edge_attribute_projections}
        if caps.edge_transaction_scope == "savepoint":
            warnings.append(
                "not_durable_until_host_commits:"
                + caps.why.get("edge_transaction_scope", "")
            )

        self._seq += 1
        edge = Edge(
            edge_id=f"e{self._seq}",
            family=family,
            namespace=namespace,
            src=src,
            dst=dst,
            provenance=provenance,
            attributes=attrs,
            warnings=tuple(warnings),
        )
        return _from_record(self.store.put_edge(_to_record(edge)))

    def retract_edge(self, edge_id: str, reason: str, *, retracted_by: str, at: datetime):
        if not reason or not reason.strip():
            raise ValueError("retract_edge requires a non-empty reason (EDGES 2.6)")
        if self.store is None or not self.store.caps.stores_edges:
            return Refusal(True, "edge_store_absent", {"edge_id": edge_id})
        rec = self.store.get_edge(edge_id)
        if rec is None:
            # Round 3: this reused `edge_family_unknown`, which is a different
            # failure -- INTERFACE 5.12's own Cause-B argument against reusing
            # `kind_mismatch`. `unknown_edge` is the nineteenth value, added to
            # INTERFACE 5.12 in the same change per ruling R3.
            return Refusal(True, "unknown_edge", {"edge_id": edge_id})
        edge = _from_record(rec)
        warnings = list(edge.warnings)
        if (self.store.caps.edge_transaction_scope == "savepoint"
                and not any(w.startswith("not_durable_until_host_commits:")
                            for w in warnings)):
            # EDGES 6.2 says the stamp is applied at EVERY write call site.
            # Round 3 [Observed]: this one inherited it from the edge's prior
            # state instead of applying it, so retracting an already-durable
            # edge over a borrowed connection came back with no warning at all.
            # That is PACKAGE 3.4 primitive 3's own recorded bug class, again.
            warnings.append(
                "not_durable_until_host_commits:"
                + self.store.caps.why.get("edge_transaction_scope", "")
            )
        if not self.store.caps.stores_edge_events:
            # EDGES 2.6: NOT refused -- the record is the row. Warned.
            warnings.append(
                "retracted_without_event_trail:"
                + self.store.caps.why.get("stores_edge_events", "")
            )
        out = replace(
            edge,
            status="retracted",
            warnings=tuple(warnings),
            provenance=replace(
                edge.provenance,
                retracted_by=retracted_by,
                retracted_at=at,
                retract_reason=reason,
            ),
        )
        return _from_record(self.store.put_edge(_to_record(out)))

    # -- the read seam --------------------------------------------------

    def neighbors(
        self,
        node: NodeRef,
        edge_families: Sequence[str] | None = None,
        depth: int = 1,
        *,
        namespace: str,
        direction: str = "both",
        include_retracted: bool = False,
    ) -> NeighborReport | Refusal:
        if depth < 1 or depth >= 3:
            # EDGES 4.2. A caller error, not a policy refusal -- the closed
            # vocabulary does not grow a value for a typo.
            raise ValueError(
                f"depth must be 1 or 2 (EDGES 4.2, the cap is R13's consequence); got {depth}"
            )
        if self.store is None or not self.store.caps.stores_edges:
            return Refusal(True, "edge_store_absent", {"node": str(node)})

        warnings: list[str] = []
        if edge_families is None:
            # EDGES 4.3/4.5: EVERY family the store can answer, across EVERY
            # namespace. Scoping this to `namespace` silently dropped families
            # registered elsewhere -- Cause C inside the read seam, on the axis
            # UC3 exists to stress. `namespace` resolves NAMED families only.
            searched = tuple(sorted(f.name for f in self.families.values()))
        else:
            unknown = [
                f
                for f in edge_families
                if f not in self.families or self.families[f].namespace != namespace
            ]  # named families ARE resolved in `namespace` -- that is its only job
            if unknown:
                # EDGES 4.3: the whole call. A typo'd family returning a clean
                # empty set is mechanism C committed by the read seam.
                return Refusal(True, "edge_family_unknown", {"families": unknown})
            searched = tuple(edge_families)
            for f in searched:
                if self.families[f].status == "retired":
                    warnings.append(f"edge_family_retired:{f}")

        if str(_type_of(node)) not in self.registered_types:
            warnings.append(f"origin_type_unregistered:{_type_of(node)}")

        symmetric = frozenset(
            name for name in searched if self.families[name].symmetric
        )
        seen_edges: dict[str, NeighborEdge] = {}
        frontier: list[NodeRef] = [node]
        visited = {str(node)}
        complete = True
        why: str | None = None
        depth_reached = 0
        bound_hit = False

        for d in range(1, depth + 1):
            if not frontier or bound_hit:
                break
            # EDGES 4.2/7.1: the registry EXHAUSTS the adapter's pages for a
            # level. A level assembled from one page of many would be silently
            # partial, which is the failure Rule K exists for.
            recs: list[Edge] = []
            fresh: set[str] = set()
            cursor: str | None = None
            while True:
                page = self.store.find_edges(EdgeQuery(
                    incident_to=tuple(_key(n) for n in frontier),
                    families=tuple(searched),
                    symmetric_families=symmetric,
                    direction=direction,
                    include_retracted=include_retracted,
                    limit=self.page_size,
                    after=cursor,
                ))
                if not page.complete:
                    complete = False
                    why = why or page.why_incomplete
                for rec in page.records:
                    # Round 3 BLOCKING: the bound was compared against the RAW
                    # page, and at depth >= 2 a frontier legitimately re-finds
                    # edges already counted -- so a walk well under budget
                    # reported complete=False with a why naming a bound nothing
                    # crossed, AND dropped the edges it had not reached yet.
                    # The bound counts DISTINCT edges. Dedupe first, then check.
                    if rec.edge_id in seen_edges or rec.edge_id in fresh:
                        continue
                    fresh.add(rec.edge_id)
                    recs.append(_from_record(rec))
                if self.max_edges is not None and len(seen_edges) + len(recs) >= self.max_edges:
                    bound_hit = True
                    break
                cursor = page.next_after
                if cursor is None:
                    break
            # EDGES 7.1: when the store could not apply the family filter
            # (indexes_edges_by_family=False) the REGISTRY narrows above it.
            # The first version of this only implemented the store half, and the
            # test written for it found the registry half missing.
            if not self.store.caps.indexes_edges_by_family:
                recs = [e for e in recs if e.family in searched]
            next_frontier: list[NodeRef] = []
            new_at_this_depth = 0
            for e in recs:
                if e.edge_id in seen_edges:
                    continue
                if self.max_edges is not None and len(seen_edges) >= self.max_edges:
                    bound_hit = True
                    break
                seen_edges[e.edge_id] = NeighborEdge(edge=e, at_depth=d)
                new_at_this_depth += 1
                for far in (e.src, e.dst):
                    if str(far) not in visited:
                        visited.add(str(far))
                        next_frontier.append(far)
            # EDGES 4.3: depth_reached counts levels that found something NEW.
            # Counting "the scan returned records" instead made a genuine dead
            # end report depth_reached == depth_requested under the DEFAULT
            # direction="both", because the frontier re-finds the edge it
            # arrived on. Round 2's second BLOCKING.
            if new_at_this_depth:
                depth_reached = d
            frontier = next_frontier

        if bound_hit:
            complete = False
            why = why or (
                f"assembly bound of {self.max_edges} edges reached; the depth cap "
                "bounds hops, not node degree (EDGES 4.2)"
            )
        # EDGES 4.3: a dead end is depth_reached < depth_requested with
        # complete=True. Truncation is a SEPARATE signal (complete=False plus a
        # why). Conflating them would make complete=False the common case.

        edges = tuple(sorted(seen_edges.values(), key=lambda ne: (ne.at_depth, ne.edge.edge_id)))
        nodes = tuple(
            n
            for n in _dedupe(
                x for ne in edges for x in (ne.edge.src, ne.edge.dst)
            )
            if str(n) != str(node)
        )
        return NeighborReport(
            origin=node,
            depth_requested=depth,
            depth_reached=depth_reached,
            direction=direction,
            families_searched=searched,
            edges=edges,
            nodes=nodes,
            known=len(edges),
            complete=complete,
            why_incomplete=why,
            warnings=tuple(warnings),
        )


def _dedupe(items: Iterable[NodeRef]) -> list[NodeRef]:
    out: list[NodeRef] = []
    seen: set[str] = set()
    for i in items:
        if str(i) not in seen:
            seen.add(str(i))
            out.append(i)
    return out


def prov(actor: str, by: str = "user", **kw: Any) -> EdgeProvenance:
    return EdgeProvenance(
        created_at=datetime(2026, 8, 29, 12, 0, 0),
        created_by_actor=actor,
        created_by=by,  # type: ignore[arg-type]
        **kw,
    )


def assert_adapter_boundary() -> None:
    """PACKAGE 3.1 / C0-04's rule, applied to this kit's own adapter.

    The store speaks flat records and knows nothing about the facade shapes.
    Checked by source inspection, exactly as C0-04 checks the real adapter --
    because round 3 found this boundary asserted in EDGES 7.1 and exercised
    nowhere, with the probe's own "adapter" handing back facade objects.
    """
    import inspect

    src = inspect.getsource(EdgeStore)
    for forbidden in ("NeighborReport", "NeighborEdge", "Refusal", "EdgeRegistry",
                      "EdgeProvenance"):
        if forbidden in src:
            raise AssertionError(
                f"EdgeStore mentions {forbidden!r} -- the adapter stores records "
                "and decides nothing (PACKAGE 3.1)"
            )
    for name, ann in (("put_edge", "EdgeRecord"), ("get_edge", "EdgeRecord"),
                      ("find_edges", "EdgePage")):
        sig = str(inspect.signature(getattr(EdgeStore, name)))
        if ann not in sig:
            raise AssertionError(f"EdgeStore.{name} does not speak {ann}: {sig}")
