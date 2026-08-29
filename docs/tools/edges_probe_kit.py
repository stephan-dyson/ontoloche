"""A THROWAWAY in-memory implementation of EDGES.md v0, for the design tests.

Row #4 is a spec and ships no edge store. But 3c's lesson was blunt -- *every
finding of substance came from driving the real registry through a real
scenario, none from reading* -- so the three design tests in EDGES.md 9-11 are
walked by executing the spec against real rows rather than by reasoning about
it. This module is that execution: it is deliberately in ``docs/tools`` and not
in ``open_ontology``, it is not imported by the package, and the contract suite
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

The refusal vocabulary is imported from ``open_ontology.types`` rather than
re-declared, so a probe that invented a reason would fail here rather than in a
reviewer's head.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Iterable, Literal, Sequence

from open_ontology.types import REFUSAL_REASONS

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
# EDGES 7.1 -- the three primitives, and the registry facade over them


class EdgeStore:
    """Primitives 16, 17, 18. Stores records, decides nothing (PACKAGE 3.1)."""

    def __init__(self, caps: EdgeCapabilities | None = None) -> None:
        self.caps = caps or EdgeCapabilities()
        self._edges: dict[str, Edge] = {}
        self._n = 0

    def put_edge(self, edge: Edge) -> Edge:
        self._edges[edge.edge_id] = edge
        return edge

    def get_edge(self, edge_id: str) -> Edge | None:
        return self._edges.get(edge_id)

    def find_edges(
        self,
        *,
        incident_to: Sequence[NodeRef] | None = None,
        families: Sequence[str] | None = None,
        symmetric_families: frozenset[str] = frozenset(),
        direction: str = "both",
        include_retracted: bool = False,
        limit: int | None = None,
        after: int | None = None,
    ) -> tuple[tuple[Edge, ...], bool, str | None, int | None]:
        """Primitive 18. Returns (records, complete, why_incomplete, next_after).

        `after` is an opaque cursor -- an index into the store's stable order,
        which is all a probe needs. EDGES 7.1 keyset-pages on
        (created_at, edge_id); the registry's obligation is the same either way:
        exhaust the pages for a level, or say the level is incomplete.
        """
        keys = {str(n) for n in incident_to} if incident_to is not None else None
        matched: list[Edge] = []
        suppressed = 0
        # EDGES 6: indexes_edges_by_family=False means the store CANNOT apply the
        # family filter. It returns the node's edges unfiltered and complete for
        # what it was asked; the registry narrows above. This is the deliberate
        # deviation from find_types' rule -- see EDGES 7.1.
        apply_family_filter = families is not None and self.caps.indexes_edges_by_family
        for e in self._edges.values():
            if e.status == "retracted" and not include_retracted:
                if keys is None or str(e.src) in keys or str(e.dst) in keys:
                    suppressed += 1
                continue
            if apply_family_filter and e.family not in families:
                continue
            if keys is not None:
                out_hit = str(e.src) in keys
                in_hit = str(e.dst) in keys
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
            nxt = start + limit
        return tuple(page), suppressed == 0, why, nxt


class EdgeRegistry:
    """The facade: EDGES 2.4.1's endpoint rule, 2.6's lifecycle, 4's read seam."""

    def __init__(
        self,
        families: Iterable[Family] = (),
        store: EdgeStore | None = None,
        registered_types: Iterable[TypeRef] = (),
        max_edges: int | None = None,
        page_size: int | None = None,
    ) -> None:
        # EDGES 4.2: the depth cap bounds HOPS, not degree. `max_edges` is the
        # deployment's assembly bound; hitting it is an incomplete report with a
        # why, never a silently truncated one.
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
        return self.store.put_edge(edge)

    def retract_edge(self, edge_id: str, reason: str, *, retracted_by: str, at: datetime):
        if not reason or not reason.strip():
            raise ValueError("retract_edge requires a non-empty reason (EDGES 2.6)")
        if self.store is None or not self.store.caps.stores_edges:
            return Refusal(True, "edge_store_absent", {"edge_id": edge_id})
        edge = self.store.get_edge(edge_id)
        if edge is None:
            return Refusal(True, "edge_family_unknown", {"edge_id": edge_id})
        warnings = list(edge.warnings)
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
        return self.store.put_edge(out)

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
            cursor: int | None = None
            while True:
                page, page_complete, page_why, cursor = self.store.find_edges(
                    incident_to=frontier,
                    families=searched,
                    symmetric_families=symmetric,
                    direction=direction,
                    include_retracted=include_retracted,
                    limit=self.page_size,
                    after=cursor,
                )
                if not page_complete:
                    complete = False
                    why = why or page_why
                recs.extend(page)
                if self.max_edges is not None and len(seen_edges) + len(recs) >= self.max_edges:
                    bound_hit = True
                    break
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
