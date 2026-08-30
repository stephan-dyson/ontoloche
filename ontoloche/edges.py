"""The EDGES.md shapes -- typed relationships over the registry.

Separate from ``types.py`` because they answer to a separate specification. ``types.py``
is INTERFACE.md 2 and 5; this is EDGES.md 2, 4 and 5. The two meet in exactly one place
and it is the load-bearing one: **an edge FAMILY is a ``TypeEntry`` with
``kind="edge"``** (EDGES.md 2.3), so a relationship label gets the proposal loop, the
lifecycle, the consumer analysis and the provenance that a noun gets, and this module
adds no registry of its own for it.

Three rules of this file are worth stating before the code, because each was a defect
before it was a rule:

* **``NeighborReport.known`` is a plain ``int``.** INTERFACE.md 3 already settled the
  case for ``ConsumerReport.known``: the report materialises its edges, so ``known`` is
  a length and there is nothing there to fail to count. ``EdgePage.known`` (the
  adapter's) stays ``int | None``, because a store genuinely may be unable to count.
* **``complete`` CAN be ``True``** -- an edge is a stored row, so there is no edge that
  exists in the store and is invisible to a query over it -- **and it is only readable
  next to ``families_searched``**, which is why that field is required rather than an
  echo of the argument (EDGES.md 4.4, ruling R12's rule).
* **``at_depth`` is not decoration.** ``equivalent_to`` is non-transitive, so a depth-2
  report that a caller reads as a depth-1 claim has manufactured the transitive closure
  the family refused to license. ``neighbors`` returns reachability; it never returns
  entailment.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Literal

from .types import CREATED_BY, Evidence, ProvenanceEvent

__all__ = [
    "TypeRef",
    "InstanceRef",
    "NodeRef",
    "EdgeProvenance",
    "Edge",
    "NeighborEdge",
    "NeighborReport",
    "EdgeFamily",
    "EDGE_STATUSES",
    "EDGE_LEVELS",
    "DIRECTIONS",
    "FAMILY_ATTRIBUTE_KEYS",
    "EDGE_PAYLOAD_KIND",
    "UNCHANGED",
    "DEFAULT_MAX_EDGES",
    "DEPTH_CAP",
    "EQUIVALENT_TO",
    "EQUIVALENT_TO_DEFINITION",
    "EQUIVALENT_TO_ATTRIBUTES",
    "family_declaration_problem",
    "node_ref",
    "node_key",
]

#: EDGES.md 2.6. Two states, and there is no ``proposed``: the governance lives one
#: level up, on the family, where it is affordable and where it bites.
EDGE_STATUSES = ("active", "retracted")

#: EDGES.md 2.4. Which shape the endpoints take. REQUIRED on a family, no default.
EDGE_LEVELS = ("type", "instance")

DIRECTIONS = ("both", "out", "in")


class _Unchanged:
    """The sentinel ``amend_edge`` needs because ``None`` is a MEANINGFUL value.

    EDGES.md 5.1 makes the point for the field that matters most: ``confidence`` is
    ``float | None`` and ``None`` is *"nothing scored it"*, not ``0.0``. So a default of
    ``None`` on an amend parameter could not distinguish *"leave the confidence alone"*
    from *"a re-classification decided nothing scores this any more"*, and the second is
    a correction a caller must be able to make -- beacon's `interview_service` selects
    on exactly that state.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - a debugging aid
        return "UNCHANGED"


#: EDGES.md 5.2, ruling **R34**/**R37**, row 4c. Pass nothing to leave a field alone.
UNCHANGED = _Unchanged()

#: EDGES.md 4.2. ``depth`` may be 1 or 2; 3 or more raises ``ValueError``. The cap and
#: ruling R13's no-paging rule are ONE decision -- if R13 is revisited the cap is
#: revisited in the same change.
DEPTH_CAP = 2

#: EDGES.md 4.2, round 3. The assembly bound is **on by default**, and that is the
#: point: a circuit breaker nobody has to switch on is not a circuit breaker. With none
#: in force, ``neighbors`` loops ``find_edges`` until the cursor is exhausted, which is
#: exactly the unbounded materialisation R13 exists to prevent -- on a fixture whose own
#: data has a node of degree 9,738,128. Disabling it (``max_edges=None``) is a
#: deliberate act by a deployment that has chosen the unbounded fetch.
DEFAULT_MAX_EDGES = 10_000

#: EDGES.md 2.4 -- the family's declared shape, all five in ``TypeEntry.attributes``.
#: ``created_by`` is deliberately NOT among them: it is ``TypeEntry.created_by``, with
#: the same vocabulary, and restating it here would be a second home for one fact.
FAMILY_ATTRIBUTE_KEYS = (
    "level",
    "symmetric",
    "inverse_label",
    "endpoint_kinds",
    "payload_schema",
)

#: EDGES.md 2.5, ruling **R34**, row 4c. The `AttributeSchema.kind` an edge PAYLOAD
#: schema is keyed under -- **not** `"edge"`, and the difference is a defect this row
#: reproduced before it designed around it.
#:
#: 2.5 as written said `payload_schema` names a schema keyed
#: `(namespace, "edge", <family name>)` -- which is exactly the key ruling **R10**
#: already gave the name-level schema governing that family's OWN `TypeEntry.attributes`
#: (its `level`, `symmetric`, `inverse_label`, `endpoint_kinds`, `payload_schema`). One
#: key, two dicts. **[Observed, row 4c]**: registering a payload schema
#: `{"role": str}` with `additional="forbid"` under `(default, "edge", "blocks")` made
#: `propose_type(kind="edge", name="blocks", ...)` refuse
#: `attributes_schema_violation` with all five declaration keys "not declared in the
#: schema" -- the family became unregisterable by the act of governing its payload.
#:
#: That is INTERFACE.md 2.3's Cause B: one container meaning two things. A schema kind
#: of its own separates the two spaces with no new table, no new primitive and no
#: possible collision, and it makes `attribute_census(kind="edge_payload")` the same
#: enumeration for edge payloads that PACKAGE.md 5.5 gives type attributes. Deviation
#: **D-4c-1**; 2.5 amended in the same change.
EDGE_PAYLOAD_KIND = "edge_payload"

#: EDGES.md 2.4.1's third clause, as a value. A predicate is never an endpoint, at
#: either level, and the rule is GENERAL rather than a family's opt-in: two predicates
#: being "equivalent" is a claim about extents, ``merge_types``' refusal #2 is
#: non-overridable for exactly that reason, and a type-level edge asserting equivalence
#: between two predicates is the ROADMAP.md kill row one indirection away.
_FORBIDDEN_ENDPOINT_KIND = "predicate"


# --------------------------------------------------------------------------- 2.1 refs


@dataclass(frozen=True)
class TypeRef:
    """A row of the vocabulary -- INTERFACE.md 2.1's identity, unchanged.

    Not a surrogate id, for PACKAGE.md 3.3's reason: an endpoint naming a surrogate
    would be unreadable without a join and unstable across a store rebuild.
    """

    namespace: str
    kind: str
    name: str

    def __str__(self) -> str:  # "dpr:value_set:borough"
        return f"{self.namespace}:{self.kind}:{self.name}"


@dataclass(frozen=True)
class InstanceRef:
    """One thing of that type. ``type.kind`` MUST be ``"entity"`` -- EDGES.md 2.4.1.

    ``id`` is an opaque ``str`` and that is a decision, not an oversight. Beacon's ids
    are integers, CMS's facility key is a CCN string, a Socrata row has a ``:id``
    system field: typing it ``str`` costs a cast on one of those three and lets the
    other two work, and typing it ``int`` excludes CMS outright. The cast is recorded
    as EDGES.md contortion E4.
    """

    type: TypeRef
    id: str

    def __post_init__(self) -> None:
        """``id`` is a ``str``, and a non-``str`` RAISES rather than being coerced.

        **The one place this can be defended, and it was defended nowhere** (row 4c,
        round 2, found by the lens that builds beacon's slice 1). Beacon's endpoint ids
        are ``Integer`` -- EDGES.md 2.1 records the cast as contortion **E4** and says
        plainly that it is *"where a silent key mismatch lives"*. It was living there:

        * ``str(InstanceRef(TASK, 41)) == str(InstanceRef(TASK, "41"))`` -- **identical**;
        * ``InstanceRef(TASK, 41) != InstanceRef(TASK, "41")`` -- **not equal**;
        * ``add_edge`` accepted the int and stored it;
        * ``neighbors`` with the int returned ``known=0, complete=True, warnings=()`` on
          SQLite -- **a confident, complete, false negative**, Rule U's forbidden empty
          in the one call a caller would believe -- and raised a raw psycopg
          ``UndefinedFunction: operator does not exist: text = smallint`` on Postgres,
          three frames below the facade.

        **One input, two reference backends, two different wrong answers.** EDGES.md 4.2
        promises a ``ValueError`` for a caller's mistake and `C17-32` pins that promise
        for ``depth``, ``node`` and ``edge_families``; the field the host actually
        differs on was checked by nothing.

        Raising rather than coercing is the same decision `AttributeSchema.name` makes
        about the store's empty-string sentinel: **the cast belongs to the caller, and a
        cast this package performs silently is a cast nobody reviews.**
        """
        if not isinstance(self.id, str):
            raise TypeError(
                f"InstanceRef.id is an opaque str (EDGES.md 2.1); got "
                f"{type(self.id).__name__} {self.id!r}. Beacon's ids are integers and "
                f"the cast is contortion E4 -- str(id) at the boundary, once, where "
                f"somebody can see it. Coercing here would make "
                f"InstanceRef(t, 41) and InstanceRef(t, '41') two references that print "
                f"the same and compare unequal"
            )

    def __str__(self) -> str:  # "cms:entity:facility#275012"
        return f"{self.type}#{self.id}"


NodeRef = TypeRef | InstanceRef


def type_of(node: NodeRef) -> TypeRef:
    return node.type if isinstance(node, InstanceRef) else node


def level_of(node: NodeRef) -> str:
    return "instance" if isinstance(node, InstanceRef) else "type"


def node_key(node: NodeRef) -> tuple[str, str, str, str | None]:
    """The adapter-side shape of a reference -- ``EdgeQuery.incident_to``'s element."""
    t = type_of(node)
    return (t.namespace, t.kind, t.name, node.id if isinstance(node, InstanceRef) else None)


def node_ref(namespace: str, kind: str, name: str, instance_id: str | None) -> NodeRef:
    """The inverse of :func:`node_key`."""
    t = TypeRef(namespace, kind, name)
    return InstanceRef(t, instance_id) if instance_id is not None else t


# -------------------------------------------------------------------- 5.1 provenance


@dataclass(frozen=True)
class EdgeProvenance:
    """EDGES.md 5.1 -- a NARROWING of ``Provenance``, and the narrowing is the argument.

    ``Provenance`` carries ``proposed_by``, ``approved_by`` and ``approved_at``, and
    INTERFACE.md 2.4 makes a rule of one of them: *"``approved_by`` is never null on an
    ``active`` type"*. EDGES.md 2.6 establishes that edge INSTANCES have no approval
    loop, so carrying the field would force one of two bad answers on every edge ever
    written -- ``None``, which breaks the rule the field exists for, or a manufactured
    ``"auto:..."`` that asserts an approval nobody performed. **A field whose only
    honest value is a lie should not be on the shape.**

    ``model_tier`` IS here, by ruling **R20**: additive, symmetric with ``Provenance``,
    and the reason is beacon's ``infer_person_relationships`` classifying person pairs
    with a named cheap tier and auto-applying at 0.7 -- finding 0.5's failure shape one
    level down. R20 declines the *gate* (a product decision about beacon's behaviour)
    and takes the *field*.
    """

    created_at: datetime
    created_by_actor: str
    created_by: str  # INTERFACE.md 2.1's vocabulary, unchanged -- incl. R17's `derived`
    #: ``None`` = nothing scored it. NOT ``0.0``: beacon's `interview_service` selects
    #: rows *"with a null relationship_type or confidence below 0.7"*, so null
    #: confidence is a live, meaningful state in the one host this must sit over.
    confidence: float | None = None
    evidence: tuple[Evidence, ...] = ()
    #: EDGES.md 5.3 / ruling R21. The SOURCE's own version, never ours. A cross-agency
    #: edge is ENTIRELY a claim about two source snapshots, and the difference between
    #: a 2017 tree census and a daily 311 feed is nine years of trees.
    source_version: str | None = None
    #: Ruling **R20**.
    model_tier: str | None = None
    retracted_by: str | None = None
    retracted_at: datetime | None = None
    retract_reason: str | None = None
    history: tuple[ProvenanceEvent, ...] = ()
    #: Rule U applied to the history itself, exactly as on ``Provenance``: a backend
    #: with ``stores_edge_events=False`` returns an empty history and this says why,
    #: rather than letting ``()`` read as "nothing happened".
    history_why: str | None = None

    def __post_init__(self) -> None:
        if self.created_by not in CREATED_BY:
            raise ValueError(
                f"EdgeProvenance.created_by must be one of {CREATED_BY}, "
                f"got {self.created_by!r}"
            )
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "history", tuple(self.history))


# -------------------------------------------------------------------------- 2.2 edge


@dataclass(frozen=True)
class Edge:
    """EDGES.md 2.2. ``(family, src, dst)`` with provenance.

    ``namespace`` is the FAMILY's, and the endpoints keep their own. A ``dot`` consumer
    may write an ``equivalent_to`` edge (family registered in ``default``) between a
    ``dpr`` type and an ``oti_311`` type: three namespaces, one edge, no contradiction,
    because the field answers *"whose word is ``equivalent_to``?"* and not *"whose data
    is this?"*. The obvious alternative -- deriving the edge's namespace from its
    endpoints -- has no answer when the endpoints disagree, which in UC3 is the normal
    case.

    **There is no ``direction`` field.** ``src`` and ``dst`` are ordered; whether the
    order carries meaning is the family's business (``symmetric``), not the edge's.
    """

    edge_id: str
    family: str
    namespace: str
    src: NodeRef
    dst: NodeRef
    provenance: EdgeProvenance
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    warnings: tuple[str, ...] = ()
    attr_schema_version: int | None = None

    def with_warnings(self, *extra: str) -> "Edge":
        seen = list(self.warnings)
        for w in extra:
            if w not in seen:
                seen.append(w)
        return replace(self, warnings=tuple(seen))


# ------------------------------------------------------------------------ 4.1 report


@dataclass(frozen=True)
class NeighborEdge:
    edge: Edge
    #: 1 = incident on the origin. **A property of the edge's DISCOVERY, not of a
    #: newly-reached node**: in a triangle ``A->B, A->C, B->C`` walked from ``A``, the
    #: ``B->C`` edge is ``at_depth=2`` although both of its endpoints were reached at
    #: depth 1.
    at_depth: int
    #: The node this edge newly reached, or ``None`` when it reached nobody new -- a
    #: self-loop, a triangle's closing edge whose two ends were both already there, or
    #: **an endpoint already reached under ANOTHER NAME of the same identity** (row 4c,
    #: round 2: the third case is not a third meaning, it is the same rule applied to
    #: the identity rather than to the written name, and ruling R38 is what makes those
    #: two differ. A caller reading EDGES.md 9.3's worked example, which filters on
    #: ``reached is not None``, drops such an edge from the projection -- correctly,
    #: because it reaches nobody new -- and the report's ``edge_family_merged`` /
    #: ``endpoint_type_merged`` markers are what say an identity was folded).
    #:
    #: **Filled by the walk, because a consumer cannot compute it from the report**, and
    #: row 4b's third adversarial round proved that by implementing EDGES.md 9.3's own
    #: worked example -- the grounding bundle's ``relations`` slot, which is the reason
    #: this row exists -- the obvious way: comparing each edge's endpoints against the
    #: ORIGIN. At depth 2 that is silently wrong, because the far end of a second-hop
    #: edge was never incident on the origin: the node actually reached never appears
    #: and the intermediate one appears twice, with no error and no ``complete=False``.
    #: **Mechanism C, inside the example written to show a consumer how to avoid it.**
    reached: NodeRef | None = None
    #: **Rule K, and it is the honesty rule ruling R38 comes with.** ``None`` when this
    #: edge was found under the very reference the walk was given; otherwise the
    #: reference it was actually found under -- a name now joined to the origin's by a
    #: merge or a retirement-with-successor.
    #:
    #: R38 makes an edge endpoint reference resolve to *the identity it now belongs to*
    #: rather than to *the reference that was written*, which is what makes
    #: ``merge_types`` safe on a store with edges in it: without it a merge silently
    #: orphans every edge ever written against the merged-away name. **The written
    #: reference stays readable** -- ``edge.src`` and ``edge.dst`` are untouched, because
    #: nothing in this package edits a stored reference -- so a caller can always tell a
    #: written reference from a followed one, which is the whole point of this field.
    #: ``complete`` stays about what was SEARCHED and says nothing about this.
    via_successor: str | None = None


@dataclass(frozen=True)
class NeighborReport:
    """EDGES.md 4.1. One read call, bounded at depth 2, no traversal language."""

    origin: NodeRef
    depth_requested: int
    #: The deepest level at which a **NEW** edge was found, and "new" is load-bearing.
    #: Under the default ``direction="both"`` the level-2 frontier contains the node
    #: reached at level 1, and that node is incident on the very edge the walk arrived
    #: on -- so a ``depth_reached`` computed from *"did the scan return any records"*
    #: reports ``depth_reached == depth_requested`` on a genuine dead end.
    #:
    #: A dead end is ``depth_reached < depth_requested`` **with ``complete=True``**.
    #: Truncation is a SEPARATE signal: ``complete=False`` plus a ``why``.
    depth_reached: int
    direction: str
    #: What was ACTUALLY consulted. Required, not an echo of the argument: ``complete``
    #: is over THESE and over the edge store, never over the host's relationships, so a
    #: report printed without this list is the same category of claim as a conformance
    #: verdict printed without its coverage line (ruling R12).
    families_searched: tuple[str, ...]
    edges: tuple[NeighborEdge, ...]
    #: Distinct endpoints reached; the origin is excluded. A **self-loop** therefore
    #: counts in ``known`` and contributes nothing here -- ``known=1, nodes=()`` is a
    #: correct report of one real edge, not an inconsistency.
    nodes: tuple[NodeRef, ...]
    known: int  # a plain int, NOT int | None -- INTERFACE.md 3
    complete: bool
    why_incomplete: str | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "known", len(self.edges))
        if self.complete and self.why_incomplete:
            raise ValueError(
                "NeighborReport.complete=True carries no why_incomplete "
                "(EDGES.md 4.3: a dead end is complete, and truncation is the other row)"
            )
        if not self.complete and not self.why_incomplete:
            raise ValueError(
                "NeighborReport.complete=False requires why_incomplete naming the bound "
                "(EDGES.md 4.3: never a silently shallower answer)"
            )


# -------------------------------------------------------------------- 2.4 the family


@dataclass(frozen=True)
class EdgeFamily:
    """A ``kind="edge"`` ``TypeEntry``, read through EDGES.md 2.4's five keys.

    A VIEW, not a second store. The five live in ``TypeEntry.attributes`` under one
    ``AttributeSchema`` keyed ``(namespace, "edge")`` -- PACKAGE.md 5.2's mechanism,
    used for the first time on a kind where every entry has the same shape, which is
    the case that mechanism was designed for.
    """

    name: str
    namespace: str
    level: str
    symmetric: bool
    inverse_label: str | None
    endpoint_kinds: dict[str, tuple[str, ...]]
    payload_schema: str | None
    status: str

    @classmethod
    def from_attributes(
        cls, name: str, namespace: str, attributes: dict[str, Any], status: str
    ) -> "EdgeFamily":
        kinds = attributes.get("endpoint_kinds") or {}
        return cls(
            name=name,
            namespace=namespace,
            level=attributes.get("level"),
            symmetric=bool(attributes.get("symmetric", False)),
            inverse_label=attributes.get("inverse_label"),
            endpoint_kinds={
                "src": tuple(kinds.get("src") or ("entity",)),
                "dst": tuple(kinds.get("dst") or ("entity",)),
            },
            payload_schema=attributes.get("payload_schema"),
            status=status,
        )


def family_declaration_problem(
    attributes: dict[str, Any],
) -> tuple[str, str, dict] | None:
    """Is this a legal ``kind="edge"`` declaration? EDGES.md 2.4.1 and ruling R18.

    Returns ``(refusal reason, sentence, detail)`` or ``None``. The reason is returned
    rather than derived by the caller because the two breaches are genuinely different
    failures: a family naming ``predicate`` as an endpoint kind is an
    ``endpoint_kind_mismatch`` and says so, while R18's cross-field rule is an
    ``attributes_schema_violation`` -- PACKAGE.md 5.6 records R18 as an exception list
    of length one *inside the attribute-schema mechanism*, so that is the vocabulary it
    belongs to. Neither needed a new value; INTERFACE.md 5.12 stays at twenty-one.

    Checked at DECLARATION time -- in
    ``propose_type``, in ``approve`` (R18 names it) and in ``import_types`` -- and not
    only at write time, because *a rule checked only when an edge is written is a rule a
    family author can opt out of by declaring a permissive ``endpoint_kinds``*. Both
    halves of EDGES.md 2.4.1 were exactly that in its first draft, and a round-1
    reviewer walked a predicate-to-predicate edge through the door.

    **A MISSING declaration is not a breach and is not refused here.** A
    ``kind="edge"`` entry with no ``level`` is a perfectly legal ``TypeEntry``
    (INTERFACE.md 2.1 requires no attributes at all, and beacon's `work_link_types`
    rows carry none of these five) -- it is simply not yet usable as an edge family, and
    ``add_edge`` refuses on it with ``attributes_schema_violation`` naming the missing
    key. Refusing the *registration* would make this row reject types INTERFACE.md says
    are legal, on data the one real host already has. The hole that would open -- declare
    nothing, then write anything -- is closed at the other end: an edge cannot be
    written on a family that declared nothing.
    """
    declared = {k for k in FAMILY_ATTRIBUTE_KEYS if k in attributes}
    if not declared:
        return None

    level = attributes.get("level")
    if "level" in declared and level not in EDGE_LEVELS:
        return (
            "attributes_schema_violation",
            f"a kind='edge' family declares level in {list(EDGE_LEVELS)}; "
            f"got {level!r} (EDGES.md 2.4)",
            {"rule": "EDGES 2.4", "key": "level", "value": level},
        )

    # Ruling **R18** / EDGES.md 2.4 -- the ONE cross-field rule the registry knows about
    # `kind="edge"` attributes. PACKAGE.md 5.6 says plainly that `FieldSpec` is
    # per-field and does not validate cross-field rules, so INTERFACE.md 9 contortion 1
    # ("cannot enforce that a symmetric type has no inverse label"), open since
    # deliverable #1, has nowhere else to be checked. R18 accepts it narrowly and
    # records it as an exception list of length one.
    if attributes.get("symmetric") and attributes.get("inverse_label") is not None:
        return (
            "attributes_schema_violation",
            "a symmetric family has no inverse_label: 'A->B' asserts 'B->A', so a name "
            "for reading dst->src is a name for a direction the family says does not "
            "exist (EDGES.md 2.4, ruling R18)",
            {
                "rule": "EDGES 2.4 / R18",
                "symmetric": True,
                "inverse_label": attributes.get("inverse_label"),
            },
        )

    kinds = attributes.get("endpoint_kinds")
    if kinds is not None:
        if not isinstance(kinds, dict) or set(kinds) - {"src", "dst"}:
            return (
                "attributes_schema_violation",
                "endpoint_kinds is {'src': [kind...], 'dst': [kind...]} (EDGES.md 2.4)",
                {"rule": "EDGES 2.4", "key": "endpoint_kinds", "value": kinds},
            )
        for end in ("src", "dst"):
            listed = tuple(kinds.get(end) or ())
            if _FORBIDDEN_ENDPOINT_KIND in listed:
                return (
                    "endpoint_kind_mismatch",
                    f"`predicate` may not be an endpoint kind ({end}), at either level "
                    "and in any family: two predicates being equivalent is a claim about "
                    "EXTENTS, which INTERFACE.md 5.10 refusal #2 makes non-overridable, "
                    "and a type-level edge asserting it is the ROADMAP.md kill row one "
                    "indirection away (EDGES.md 2.4.1)",
                    {
                        "rule": "EDGES 2.4.1",
                        "endpoint": end,
                        "declared": list(listed),
                        "forbidden": _FORBIDDEN_ENDPOINT_KIND,
                    },
                )
            if level == "instance" and set(listed) - {"entity"}:
                return (
                    "endpoint_kind_mismatch",
                    f"a level='instance' family may only declare `entity` endpoints "
                    f"({end} declares {sorted(listed)}): only an entity has instances, "
                    "and a family declaring `edge` at instance level would reify an edge "
                    "-- which EDGES.md 1 rules out (EDGES.md 2.4.1)",
                    {
                        "rule": "EDGES 2.4.1",
                        "endpoint": end,
                        "declared": sorted(listed),
                        "level": "instance",
                    },
                )
    return None


# ------------------------------------------------------------- 3.1 the first family

EQUIVALENT_TO = "equivalent_to"

EQUIVALENT_TO_DEFINITION = (
    "The two types denote the same thing in their respective vocabularies. "
    "It does NOT assert that they are interchangeable, that their value sets "
    "match, that their consumers accept each other, or that either may be "
    "retired in favour of the other. It licenses a reader to join them and "
    "requires that reader to look at both definitions first."
)

#: EDGES.md 3.1, verbatim. ``kind="edge"`` IS in the list and that is not reification:
#: ``dpr:edge:concerns == oti_311:edge:relates_to`` relates two ROWS OF THE VOCABULARY,
#: which is precisely what a type-level edge is for, and it is the shape UC3 predicts
#: when two agencies name the same real-world relation differently. ``predicate`` is
#: absent because 2.4.1 forbids it GENERALLY, not because this family opted out -- and
#: that distinction is the whole point, because a per-family exclusion holds only as
#: long as every future family author remembers it.
EQUIVALENT_TO_ATTRIBUTES: dict[str, Any] = {
    "level": "type",
    "symmetric": True,
    "inverse_label": None,
    "endpoint_kinds": {
        "src": ["entity", "value_set", "edge"],
        "dst": ["entity", "value_set", "edge"],
    },
    "payload_schema": None,
}
