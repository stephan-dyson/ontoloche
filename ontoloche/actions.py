"""The ACTIONS.md shapes -- governed verbs over the registry and the edge store.

Separate from ``types.py`` and from ``edges.py`` for the reason those two are separate
from each other: they answer to separate specifications. ``types.py`` is INTERFACE.md 2
and 5, ``edges.py`` is EDGES.md 2/4/5, and this is ACTIONS.md 2/3/6/8/10. The three meet
in exactly one place and it is the load-bearing one: **an action FAMILY is a
``TypeEntry`` with ``kind="action"``** (ACTIONS.md 2.1), so a verb gets the
proposal loop, the lifecycle, the consumer analysis and the provenance a noun gets, and
this module adds no registry of its own for it.

Four rules of this file are worth stating before the code, because each was a defect
before it was a rule -- three of them in row #6's own adversarial loop, which is why
they are transposed here rather than re-derived:

* **Every declaration rule binds at all THREE doors.** ``propose_type``, ``approve`` and
  ``import_types``. Rule 2.2-4 exists because a reviewer imported an *active*
  ``kind="action"`` family declaring ``merge_types`` as an effect, through the shipped
  registry, with no warning at all. :func:`family_declaration_problem` is the one place
  the rules live, exactly as ``edges.family_declaration_problem`` is for one kind along.
* **A MISSING declaration is not a breach.** A ``kind="action"`` entry with none of the
  eight keys is a legal ``TypeEntry`` (INTERFACE.md 2.1 requires no attributes at all),
  and refusing its *registration* would reject types INTERFACE.md says are legal. The
  hole that opens -- declare nothing, then invoke anything -- is closed at the other
  end, in ``preflight``. That is ``edges.family_declaration_problem``'s own recorded
  decision for the identical case, and row #6's round 1 found ACTIONS.md silently taking
  the opposite position.
* **The ``propose_type`` effect rule is an ALLOWLIST.** Round 2 reached ROADMAP.md's
  kill row through a blocklist by simply *omitting* ``kind`` -- the round-1 rule tested
  ``kind == "predicate"`` and ``Effect.kind`` is ``str | None`` -- and reached it a
  second way with ``kind="action"``, which mints a live *verb* unattended.
* **``holds`` is three-valued and so is ``below``.** Rule U, on the two comparisons this
  layer makes. Unknown is never satisfied and never a confident false.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from .edges import InstanceRef, TypeRef
from .types import Evidence, ProvenanceEvent, Refusal

__all__ = [
    "EdgeRef",
    "InputSpec",
    "Precondition",
    "Effect",
    "ActionFamily",
    "InvocationProvenance",
    "Invocation",
    "PreconditionResult",
    "Preflight",
    "InvocationReport",
    "ProjectionReport",
    "action_attributes",
    "ACTION_ATTRIBUTE_KEYS",
    "EFFECT_OPS",
    "GOVERNANCE_CALLS",
    "PRECONDITION_KINDS",
    "PROPOSABLE_KINDS",
    "REVERSIBILITY",
    "APPROVAL_MODES",
    "OUTCOMES",
    "GATE_VERDICTS",
    "EVALUATORS",
    "REF_SHAPES",
    "ACTION_PAYLOAD_KIND",
    "ADMISSION_RULE",
    "family_declaration_problem",
    "declared_family",
    "effect_identity",
    "effect_target",
    "ref_shape",
    "ref_kind",
    "ref_key",
    "is_person",
]

# --------------------------------------------------------------------------- 2.2

#: ACTIONS.md 2.2 -- the family's declared shape, all eight in ``TypeEntry.attributes``.
#: ``created_by`` and ``namespace`` are deliberately NOT among them: both are
#: ``TypeEntry``'s already, and restating either would be a second home for one fact
#: (EDGES.md 2.4's rule, inherited rather than the mistake).
ACTION_ATTRIBUTE_KEYS = (
    "inputs",
    "preconditions",
    "effects",
    "reversibility",
    "approval_mode",
    "min_auto_tier",
    "reachability",
    "payload_schema",
)

#: ACTIONS.md 2.6. Three values, which is beacon's two-value ``undoable: bool`` with the
#: middle filled in: a boolean cannot tell *"the protocol can undo this"* from
#: *"somebody wrote a compensating handler"*, and the difference is who is on the hook
#: when the handler is missing.
REVERSIBILITY = ("reversible", "compensable", "irreversible")

#: ACTIONS.md 5.2. Who must sign off on an INVOCATION. Closed at three; a fourth (a
#: quorum, a two-person rule) is a policy language arriving one value at a time and
#: 15.2 records the recommendation to make ``approved_by`` a list first.
APPROVAL_MODES = ("auto", "review", "human")

#: ACTIONS.md 2.4. Four kinds, each answered by a call that ALREADY EXISTS, and there is
#: no fifth. *"Anything else"* is not a precondition in v0 -- it is the action's own
#: code, and the registry does not pretend to know it.
PRECONDITION_KINDS = ("type_active", "predicate_holds", "edge_exists", "edge_absent")

#: ACTIONS.md 2.5. The closed operation vocabulary. The fourth is an admission rather
#: than a capability: ``host_state`` means *this action changes something this protocol
#: does not model*, and it carries a mandatory sentence saying what -- because an empty
#: list standing in for *"we did not look"* is what Rule U forbids by name.
EFFECT_OPS = ("add_edge", "retract_edge", "propose_type", "host_state")

#: ACTIONS.md 2.5 -- the six calls that may NEVER be an effect, as a GENERAL rule rather
#: than a family's opt-in. They are the governance loop itself: an action that can
#: ``approve`` closes the proposal->approval loop with no human in it; an action that can
#: ``merge_types`` is ROADMAP.md's kill row wearing a verb; an action that can
#: ``register_consumer`` can make itself look gated. **An action may PROPOSE; only a
#: human, or an auto-policy a deployment set deliberately, may APPROVE.**
GOVERNANCE_CALLS = (
    "approve",
    "reject",
    "retire",
    "reinstate",
    "merge_types",
    "register_consumer",
)

#: ACTIONS.md 2.5 rule 2.5-8 -- the kinds a ``propose_type`` EFFECT may name. An
#: **ALLOWLIST**, and the shape is the whole point.
#:
#: ``predicate`` is excluded because a predicate's extent is a set of TYPES and a
#: freshly minted one is EMPTY -- so it is byte-identical to any other empty extent and
#: INTERFACE.md 5.10's refusal #2 does *not* fire on it (`C10-09` is the record of that
#: being the kill row's second trip). ``action`` is excluded because 15.1 ranks a verb
#: above a noun: a live verb minted unattended is mechanism 1 arriving through the very
#: layer this document adds.
#:
#: **A blocklist was the wrong shape and it was tried.** Round 1's rule tested
#: ``kind == "predicate"``; round 2 walked past it by OMITTING the key, because
#: ``Effect.kind`` is ``str | None``.
PROPOSABLE_KINDS = ("entity", "edge", "value_set")

#: ACTIONS.md 3.4. Closed at four. ``failed`` is NOT a refusal -- a refusal is a
#: decision and a failure is an accident, and collapsing them loses the only distinction
#: an operator cares about at 3am. There is deliberately no ``pending``: a mode-``human``
#: invocation awaiting a decision is not an invocation yet, and inventing the value
#: would make this layer own a queue, which ACTIONS.md 1 rules out in its first line.
OUTCOMES = ("applied", "refused", "failed", "compensated")

#: ACTIONS.md 3.1. THREE values and not a bool, because ``not_asked`` is a real and
#: common state: a host may record an invocation it ran without consulting ``preflight``
#: at all, and ``False`` would say *the gate refused*, which is a different and much
#: worse claim. Rule U, on a three-state field.
GATE_VERDICTS = ("allowed", "refused", "not_asked")

#: ACTIONS.md 6.1 -- the closed set of calls that may answer a precondition, and 2.4's
#: no-query-language claim made mechanical. ``resolve_type`` is deliberately NOT among
#: them: it needs a ``tier`` and a column-shaped ``ResolveContext`` that ``preflight``
#: does not have (contortion ACT2/ACT6).
EVALUATORS = ("list_types", "predicates", "neighbors")

#: ACTIONS.md 2.3. Three reference shapes, and the third is this document's.
REF_SHAPES = ("type", "instance", "edge")

#: ACTIONS.md 2.7, ruling **R10**, row 6b -- the ``AttributeSchema.kind`` an invocation's
#: INPUTS schema is keyed under, and it is **not** ``"action"``.
#:
#: 2.7 as written says `payload_schema` names a schema keyed
#: ``(namespace, "action", <family name>)`` -- which is exactly the key R10 already gave
#: the name-level schema governing that family's OWN eight declaration keys. One key,
#: two dicts, and contortion **ACT1** predicted the collision in the abstract:
#: *"it works because the two objects never share a store, which is a fact OUTSIDE the
#: mechanism."* **They do share one**, `oo_attr_schema`, under one key.
#:
#: **[Observed, row 6b's first adversarial round]** registering
#: ``AttributeSchema(namespace="beacon", kind="action", name="q_fam", mode="enforce")``
#: made ``propose_type(kind="action", name="q_fam")`` refuse
#: ``attributes_schema_violation`` -- *the family became unregisterable by the act of
#: governing its own inputs*, and 2.7's headline is *"this one is not inert"*.
#:
#: This is `edges.EDGE_PAYLOAD_KIND` one kind along, deviation **D-4c-1** reproduced by
#: the row that inherited the mechanism. A schema kind of its own separates the two
#: spaces with no new table, no new primitive and no possible collision, and it makes
#: ``attribute_census(kind="action_payload")`` the same enumeration for invocation inputs
#: that PACKAGE.md 5.5 gives type attributes.
ACTION_PAYLOAD_KIND = "action_payload"

#: ACTIONS.md 10.4. The ONE admission rule the registry computes, labelled so a caller
#: can see that it is one. Ruling **R42**: it stays one host's convention for v0 --
#: ``counts`` is rule-independent and a host with a different rule computes from it.
ADMISSION_RULE = "greedy_whole_group"

#: ACTIONS.md 2.3 / EDGES.md 2.4.1's third clause, as a value. A predicate is never an
#: action input, at any ref level and whatever the family declared: an action taking two
#: predicates is ``merge_capabilities(commentable, searchable)`` -- ROADMAP.md's kill row
#: spelled as a tool call. Round 1 constructed exactly that, end to end.
_FORBIDDEN_INPUT_KIND = "predicate"


# --------------------------------------------------------------------------- 2.3 refs


@dataclass(frozen=True)
class EdgeRef:
    """ACTIONS.md 2.3's third reference shape -- one EDGE.

    ``family`` and ``namespace`` are carried although ``edge_id`` alone identifies the
    edge, because an invocation record is read long after the edge store has moved on
    and a bare id is unreadable without a join -- the objection EDGES.md 2.1 raises
    against a surrogate endpoint. A retracted edge still has a family and a namespace; a
    bare id has nothing. It costs two strings.
    """

    edge_id: str
    #: the NAME of the ``kind="edge"`` TypeEntry, carried so the reference can be READ
    #: without a store round trip
    family: str
    #: the FAMILY's namespace -- never the endpoints'. EDGES.md 2.2's rule, verbatim
    namespace: str = "default"

    def __str__(self) -> str:  # pragma: no cover - a display form
        return f"{self.namespace}:edge:{self.family}#{self.edge_id}"


InputRef = TypeRef | InstanceRef | EdgeRef


def ref_shape(ref: Any) -> str | None:
    """Which of ACTIONS.md 2.3's three shapes this reference is, or ``None``.

    **``None`` and not ``"type"``, and the difference is a kill-row door.** The first
    cut returned ``"type"`` for anything that was not an ``EdgeRef`` or an
    ``InstanceRef`` -- so a bare string, a dict or a tuple was accepted as a type ref,
    ``ref_kind`` found no ``kind`` on it, the general ``predicate`` exclusion never saw
    it, and ``preflight`` answered ``verdict="allowed"`` for
    ``merge_capabilities(commentable, searchable)``. **That is row #6's own R1-B1 walk,
    alive through a different ref SHAPE** -- and 2.3's rule is *"the exclusion is general
    or it is nothing."*

    It is the same mistake ``is_person`` records one section along, in the same shape: a
    permissive fallback for an unrecognised value. **Rule U: unknown is not a type ref**,
    exactly as unknown is not a person. Found by row 6b's first adversarial round.
    """
    if isinstance(ref, EdgeRef):
        return "edge"
    if isinstance(ref, InstanceRef):
        return "instance"
    if isinstance(ref, TypeRef):
        return "type"
    return None


def ref_kind(ref: Any) -> str | None:
    """The registry ``kind`` this reference is about, or ``None`` when it names none."""
    if isinstance(ref, EdgeRef):
        return "edge"
    if isinstance(ref, InstanceRef):
        return ref.type.kind
    return getattr(ref, "kind", None)


def ref_key(ref: Any) -> str:
    """The identity string a precondition compares two references by."""
    if isinstance(ref, EdgeRef):
        return f"{ref.namespace}:edge:{ref.family}#{ref.edge_id}"
    if isinstance(ref, InstanceRef):
        t = ref.type
        return f"{t.namespace}:{t.kind}:{t.name}#{ref.id}"
    return f"{ref.namespace}:{ref.kind}:{ref.name}"


@dataclass(frozen=True)
class InputSpec:
    """ACTIONS.md 2.3 -- one typed argument the action takes.

    Like every other declaration shape in this module it is a **view over JSON**: the
    eight keys of 2.2 live in ``TypeEntry.attributes``, which is a JSON blob in every
    reference store, so the stored form is a plain dict and this is what a reader and a
    guard work with. :func:`action_attributes` builds the stored form from these; the
    registry parses it back with :meth:`from_dict`.
    """

    #: the argument name, as the host's tool schema spells it
    name: str
    ref: Literal["type", "instance", "edge"]
    required: bool = True
    #: for ``ref="type"``/``"instance"``: which registry kinds are acceptable.
    #: ``None`` = any but ``predicate``
    kinds: tuple[str, ...] | None = None
    #: for ``ref="edge"``: which families are acceptable
    families: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ref": self.ref,
            "required": self.required,
            "kinds": None if self.kinds is None else list(self.kinds),
            "families": None if self.families is None else list(self.families),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "InputSpec":
        kinds = d.get("kinds")
        families = d.get("families")
        return cls(
            name=d.get("name"),
            ref=d.get("ref"),
            required=bool(d.get("required", True)),
            kinds=None if kinds is None else tuple(kinds),
            families=None if families is None else tuple(families),
        )


@dataclass(frozen=True)
class Precondition:
    """ACTIONS.md 2.4 -- what must be true before the action runs."""

    kind: str
    #: the ``InputSpec.name`` this is about, or a literal identity ref
    subject: str
    #: REQUIRED, non-empty. What this condition protects -- PACKAGE.md 5.2's reasoning
    #: for ``FieldSpec.description``: a precondition nobody can read is a precondition
    #: nobody will ever delete when it stops being true.
    why: str
    predicate: str | None = None
    family: str | None = None
    object: str | None = None
    #: the FAMILY's namespace, for the edge kinds. ``Registry.neighbors`` makes
    #: ``namespace`` keyword-only WITHOUT a default *precisely because ``"default"`` is a
    #: wrong answer nobody notices* -- so it is on the shape. Row #6's round 1 found the
    #: printed shape missing it while the probe kit had silently added it, and the two
    #: readings gave OPPOSITE verdicts on UC3's own fixture.
    namespace: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "subject": self.subject,
            "why": self.why,
            "predicate": self.predicate,
            "family": self.family,
            "object": self.object,
            "namespace": self.namespace,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Precondition":
        return cls(
            kind=d.get("kind"),
            subject=d.get("subject"),
            why=d.get("why") or "",
            predicate=d.get("predicate"),
            family=d.get("family"),
            object=d.get("object"),
            namespace=d.get("namespace") or "default",
        )


@dataclass(frozen=True)
class Effect:
    """ACTIONS.md 2.5 -- an operation the family is PERMITTED to perform."""

    op: str
    family: str | None = None
    namespace: str | None = None
    #: for ``op="propose_type"``. REQUIRED there, and an ALLOWLIST
    kind: str | None = None
    #: REQUIRED for ``op="host_state"``, non-empty. Rule U
    why: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "family": self.family,
            "namespace": self.namespace,
            "kind": self.kind,
            "why": self.why,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Effect":
        return cls(
            op=d.get("op"),
            family=d.get("family"),
            namespace=d.get("namespace"),
            kind=d.get("kind"),
            why=d.get("why") or "",
        )


def effect_identity(effect: Effect) -> tuple:
    """ACTIONS.md 2.5 -- what makes two effects the SAME effect.

    ``(op, namespace, family, kind)``, with ``why`` excluded for the three protocol ops
    so that amending a sentence does not turn one declared effect into two.
    **``host_state`` has no target at all, so its ``why`` IS its identity** -- two
    admissions differing by a full stop are two effects, and that cost is stated
    (contortion **ACT9**, ruling **R46**) rather than hidden behind a sixth key.

    ``namespace=None`` on an edge op is a DECLARATION -- *the namespace comes from this
    invocation's inputs* -- not an omission, and it keeps that identity so
    :func:`Registry.record_invocation` can satisfy it against the inputs' own
    namespaces. Round 2 measured the alternative at **2,394 of 2,399 correct
    invocations** carrying ``effect_undeclared``: a detector that fires on 99.8% of a
    correct run is not a detector.
    """
    if effect.op == "host_state":
        return ("host_state", effect.why)
    return (effect.op, effect.namespace, effect.family, effect.kind)


def effect_target(effect: Effect) -> str:
    """The ``<target>`` half of ``effect_undeclared:<op>:<target>``.

    ``host_state`` has no target, so it is the ``why`` -- round 1 found
    ``effect_undeclared:host_state:None:None`` being printed against a spec whose
    ``<op>:<target>`` format had no reading for an op with no target.
    """
    if effect.op == "host_state":
        return effect.why
    if effect.op == "propose_type":
        return f"{effect.namespace}:{effect.kind}"
    return f"{effect.namespace}:{effect.family}"


# ----------------------------------------------------------------------- 3 records


@dataclass(frozen=True)
class InvocationProvenance:
    """ACTIONS.md 3.2 -- a narrowing of ``Provenance`` that runs the OTHER way from
    ``EdgeProvenance``'s.

    The field names are INTERFACE.md 2.4's and EDGES.md 5.1's, character for character,
    including ``created_at`` and ``created_by_actor`` for a thing that reads more
    naturally as *invoked at* and *invoked by*. The nicer names were considered and
    refused: three shapes for one concept with three spellings of *when* is precisely
    the drift ``check_spec_drift.py`` was written to catch.

    **``approved_by`` comes BACK**, and that is the interesting half. EDGES.md 5.1
    dropped it from ``EdgeProvenance`` because *"a field whose only honest value is a lie
    should not be on the shape"* -- edge instances have no approval loop. An invocation
    DOES have an approval decision, so INTERFACE.md 2.4's never-null rule is inherited
    verbatim, bounded to where the gate actually decided: when the gate was not asked, or
    asked and refused, the field is ``None`` and the record carries
    ``approval_unrecorded``. The first draft filled ``"auto:<policy>"`` on every applied
    invocation, which wrote an approval nobody performed into ``delete_person``'s ledger.
    """

    created_at: datetime
    #: ``"user:sd"``, ``"ai:classifier"``, ``"auto:nightly"``, ``"derived:<rule>"``.
    #: INTERFACE.md 2.4's field, verbatim
    created_by_actor: str
    #: DERIVED from the actor, never passed -- INTERFACE.md 2.1's own rule
    created_by: str = "user"
    #: R20. The tier of the ACTOR THAT INVOKED -- not the tier that proposed the family.
    #: Two different facts about two different objects, and both matter: a family
    #: proposed by Haiku and invoked by Opus is not the same risk as the reverse.
    model_tier: str | None = None
    #: ``None`` = nothing scored it. NOT ``0.0`` -- Rule U
    confidence: float | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    evidence: tuple[Evidence, ...] = ()
    #: R21's field -- the SOURCE's own version
    source_version: str | None = None
    #: append-only. INTERFACE.md 5.8
    history: tuple[ProvenanceEvent, ...] = ()
    #: why ``history`` is empty, when it is. Rule U
    history_why: str | None = None


@dataclass(frozen=True)
class Invocation:
    """ACTIONS.md 3.1 -- one use of one verb."""

    #: opaque, generated ABOVE the store. PACKAGE.md 4.2
    invocation_id: str
    #: the NAME of a ``kind="action"`` TypeEntry
    family: str
    #: the FAMILY's namespace. EDGES.md 2.2's rule
    namespace: str
    inputs: dict[str, Any]
    #: COPIED from what the GATE judged, never referenced. A family's declaration may be
    #: amended after an invocation ran, and a record pointing at the *current*
    #: declaration would silently re-describe its own blast radius every time somebody
    #: edited the family -- so ``invocations(effect_undeclared=True)`` would answer a
    #: different question each time the vocabulary moved.
    declared_effects: tuple[Effect, ...]
    #: what the host REPORTS it actually did. The registry cannot verify it, and 3.3
    #: says so plainly because the alternative reading -- that this layer detects what an
    #: action really did -- is the reading that would make the mechanism worthless the
    #: first time someone relied on it.
    observed_effects: tuple[Effect, ...]
    #: ``approval_mode`` / ``min_auto_tier`` / ``reversibility`` / the precondition
    #: kinds / the tier order, ALSO as the gate judged them. Rule 3-8: the copy is taken
    #: for one of the five things that decide a verdict, and an auditor asking *"was
    #: Haiku permitted to run this unattended in March?"* had no field to read.
    declared_policy: dict
    #: the declaration generation this was judged against
    family_version: int
    outcome: str
    gate_verdict: str
    provenance: InvocationProvenance
    #: REQUIRED when ``outcome == "refused"``
    refusal: Refusal | None = None
    #: the ``invocation_id`` this one compensates
    compensates: str | None = None
    #: the ``invocation_id`` that compensated this one -- DERIVED by the facade; the
    #: store holds only the forward pointer (ACTIONS.md 9)
    compensated_by: str | None = None
    #: set by an ``invocation_reviewed`` event. ACTIONS.md 5.2
    reviewed_at: datetime | None = None
    #: INTERFACE.md 5.4's vocabulary
    warnings: tuple[str, ...] = ()
    #: the inputs schema in force when this was written
    attr_schema_version: int | None = None


@dataclass(frozen=True)
class PreconditionResult:
    """ACTIONS.md 6.1 -- one condition's answer, and ``holds`` is three-valued."""

    condition: Precondition
    #: ``None`` = could not be evaluated. Rule U -- NOT ``False``. Treating unknown as
    #: *satisfied* would let a degraded backend approve everything; treating it as
    #: *unsatisfied* would be a confident ``False`` the registry did not earn.
    holds: bool | None
    #: the existing call that answered this, from ``EVALUATORS``. Not decoration -- it
    #: is 2.4's no-query-language claim made checkable, so a reviewer can confirm
    #: mechanically that nothing evaluated a condition by some fifth route.
    evaluated_by: str
    #: REQUIRED when ``holds`` is ``None``
    why: str | None = None


@dataclass(frozen=True)
class Preflight:
    """ACTIONS.md 6.1 -- may this run, and what does it declare?

    It **records nothing**. It is a question, it is idempotent, and it may be called a
    hundred times. A host that wants the question answered *and* the answer recorded
    calls ``record_invocation`` with the verdict it received.
    """

    family: str
    namespace: str
    #: bumped at every declaration door. 3.1
    family_version: int
    reversibility: str
    verdict: str
    #: the blast radius, before anything runs
    declared_effects: tuple[Effect, ...]
    preconditions: tuple[PreconditionResult, ...]
    approval_mode: str
    #: ``len(preconditions)``. Rule K
    known: int
    #: ``False`` when ANY condition is unknown
    complete: bool
    #: REQUIRED when ``verdict == "refused"``
    refusal: Refusal | None = None
    #: ``"auto:<policy>"`` when the gate approves
    approved_by: str | None = None
    #: the family's ``min_auto_tier``
    tier_floor: str | None = None
    #: REQUIRED when ``tier_floor`` is ``None``. Rule U -- the honest surface for a
    #: legitimate no-floor configuration is a stated absence, not an alarm
    tier_floor_why: str | None = None
    why_incomplete: str | None = None


@dataclass(frozen=True)
class InvocationReport:
    """ACTIONS.md 6.3 -- the read.

    ``known`` is ``int | None`` and not ``int``, because INTERFACE.md 3's amendment
    settled that a backend entitled to say *"we did not count"* must have somewhere to
    say it, and ``0`` would falsify it. ``complete`` is ``False`` whenever a filter
    suppressed rows or ``limit`` truncated the answer -- so EVERY filtered answer,
    including 4's override query, is a floor rather than a total.
    """

    invocations: tuple[Invocation, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectionReport:
    """ACTIONS.md 10.3 -- the tool-slot arithmetic, and what it refuses to answer.

    ``counts`` and ``admitted`` are two numbers because ``reachability`` is a *list*: a
    family may declare two groups, and *"how many families declare alpha?"* and *"how
    many slots does alpha cost under this order?"* are different questions with different
    answers. Round 1 found ``counts`` changing with the order, which made 10.4's
    *"the useful half of this call is the counting"* rest on a guarantee that did not
    hold -- and no design test found it because beacon's ``ActionSpec.category`` is a
    single string, so the fixture the section was built from cannot exercise it.
    """

    #: a LABEL for the report -- the context being assembled -- not a filter
    surface: str
    budget: int
    reserved: int
    #: families DECLARING each group. RULE-INDEPENDENT: a family in two groups is
    #: counted in both, and this dict is identical under every permutation of ``order``
    counts: dict[str, int]
    #: families CHARGED to each group by ``rule`` -- one slot each, in the first group
    #: of ``order`` they match
    admitted: dict[str, int]
    rule: str
    #: ``None`` = no order supplied. Rule U, and rule 10-2's marker: with no order the
    #: registry answers ``counts`` and nothing else, because *the registry never decides
    #: which families reach a surface*
    order_source: str | None
    fits: tuple[str, ...]
    would_evict: tuple[str, ...]
    over_by: int
    #: consumer ids gating on an evicted family. It is NEVER complete and the report
    #: says so: INTERFACE.md 5.1 makes ``ConsumerReport.complete`` always ``false`` in
    #: v0, so this is a list of KNOWN casualties and never the list of all of them
    consumers_at_risk: tuple[str, ...]
    #: families this report SELECTED, not the size of the registry
    known: int | None
    complete: bool
    why_incomplete: str | None = None


# ------------------------------------------------------------------- 5.2 the gate


def is_person(actor: str | None) -> bool:
    """ACTIONS.md 5.2 -- a TRUE allowlist, and the distinction is the whole rule.

    ``Registry``'s own ``_created_by`` maps an UNRECOGNISED prefix to ``"user"``, which
    is INTERFACE.md 2.1's reading of an actor string and right for *provenance*. It is
    wrong for an approval *gate*: round 1 walked ``bot:reaper``, ``svc:cleanup``,
    ``AI:bot`` and ``nobody`` through a three-prefix blocklist, and round 2 walked the
    same five through the ``created_by == "user"`` allowlist that replaced it, because
    every one of them falls through to ``"user"``.

    INTERFACE.md line 58 names the failure by name -- *"a ``created_by_actor`` string
    convention that nothing validates"* -- so a human approver must be RECOGNISABLE as
    one, and everything the registry does not recognise is refused. **Rule U: unknown is
    not a person.**
    """
    return bool(actor) and actor.startswith("user:") and bool(actor[len("user:") :].strip())


# ------------------------------------------------------- 2.2/2.3/2.4/2.5 the door


@dataclass(frozen=True)
class ActionFamily:
    """A ``kind="action"`` ``TypeEntry``, read through ACTIONS.md 2.2's eight keys.

    A VIEW, not a second store -- exactly as ``edges.EdgeFamily`` is. The eight live in
    ``TypeEntry.attributes`` under one ``AttributeSchema`` keyed
    ``(namespace, "action")``, which is PACKAGE.md 5.2's mechanism used on a kind where
    every entry has the same shape.

    ``reversibility`` and ``approval_mode`` are ``str | None``, and ``None`` means *this
    entry is a legal ``kind="action"`` TypeEntry that is not (yet) a declared action
    family*. Rule 2.2-1: refusing its registration would reject types INTERFACE.md says
    are legal; ``preflight`` and ``record_invocation`` are where the hole is closed.
    """

    name: str
    namespace: str
    status: str
    reversibility: str | None = None
    approval_mode: str | None = None
    inputs: tuple[InputSpec, ...] = ()
    preconditions: tuple[Precondition, ...] = ()
    effects: tuple[Effect, ...] = ()
    min_auto_tier: str | None = None
    reachability: tuple[str, ...] = ()
    payload_schema: str | None = None
    #: the declaration generation. ACTIONS.md 3.1 -- bumped at every declaration door,
    #: because rule 3-1's copy is only meaningful if a record can say WHICH declaration
    #: it was judged against. Derived from ``TypeEntry.attr_schema_version``'s sibling
    #: on the record rather than stored twice.
    version: int = 1

    @property
    def declared(self) -> bool:
        """Is this a usable action family, or a bare ``kind="action"`` entry?"""
        return self.reversibility is not None and self.approval_mode is not None

    @classmethod
    def from_attributes(
        cls,
        name: str,
        namespace: str,
        attributes: dict[str, Any],
        status: str,
        version: int = 1,
    ) -> "ActionFamily":
        return cls(
            name=name,
            namespace=namespace,
            status=status,
            reversibility=attributes.get("reversibility"),
            approval_mode=attributes.get("approval_mode"),
            inputs=tuple(_as_specs(attributes.get("inputs") or ())),
            preconditions=tuple(_as_conditions(attributes.get("preconditions") or ())),
            effects=tuple(_as_effects(attributes.get("effects") or ())),
            min_auto_tier=attributes.get("min_auto_tier"),
            reachability=tuple(attributes.get("reachability") or ()),
            payload_schema=attributes.get("payload_schema"),
            version=version,
        )


def _as_specs(raw) -> list[InputSpec]:
    return [s if isinstance(s, InputSpec) else InputSpec.from_dict(s) for s in raw]


def _as_conditions(raw) -> list[Precondition]:
    return [c if isinstance(c, Precondition) else Precondition.from_dict(c) for c in raw]


def _as_effects(raw) -> list[Effect]:
    return [e if isinstance(e, Effect) else Effect.from_dict(e) for e in raw]


def action_attributes(
    *,
    reversibility: str | None = None,
    approval_mode: str | None = None,
    inputs: tuple[InputSpec, ...] | list[InputSpec] = (),
    preconditions: tuple[Precondition, ...] | list[Precondition] = (),
    effects: tuple[Effect, ...] | list[Effect] = (),
    min_auto_tier: str | None = None,
    reachability: tuple[str, ...] | list[str] | None = None,
    payload_schema: str | None = None,
) -> dict[str, Any]:
    """Build the STORED form of ACTIONS.md 2.2's eight keys from the typed shapes.

    ``TypeEntry.attributes`` is a JSON blob in every reference store, so a caller cannot
    put an ``InputSpec`` in it and expect it back. This is the one place that
    translation lives, so a family declared in a test, in a probe and in a host all
    produce the same eight keys.

    ``reachability`` defaults to ``()`` and **an empty list is a positive declaration**
    -- *this host exposes me on no named surface* -- not a forgotten field. It is
    required for the section (10) its own customer deletes, and it stays required
    because Rule U's standard applies to 10's own field.
    """
    return {
        "inputs": [s.to_dict() for s in inputs],
        "preconditions": [c.to_dict() for c in preconditions],
        "effects": [e.to_dict() for e in effects],
        "reversibility": reversibility,
        "approval_mode": approval_mode,
        "min_auto_tier": min_auto_tier,
        "reachability": list(reachability if reachability is not None else ()),
        "payload_schema": payload_schema,
    }


def _is_literal_ref(token: str | None) -> bool:
    """ACTIONS.md 2.4: ``subject`` is *"the InputSpec.name this is about, or a literal
    ref"*, and a literal ref carries its identity triple and is recognisable by it."""
    return bool(token) and token.count(":") >= 2


def _spec_problem(spec: InputSpec) -> tuple[str, str, dict] | None:
    """ACTIONS.md 2.3, checked at the DOOR rather than at construction.

    Round 2 found this rule and two of 2.4's raising a bare ``ValueError`` in
    ``__post_init__``, so they fired before any door was reached -- carrying no ``door``,
    returning no ``Refusal``, and unable to produce ``import_refused`` on the
    ``import_types`` path. **Rule 2.2-4 says every declaration rule binds at all three
    doors; three of them bound at none.**
    """
    if not spec.name or not spec.name.strip():
        return (
            "attributes_schema_violation",
            "every InputSpec needs a non-empty `name` -- it is what an invocation keys "
            "its inputs by (ACTIONS.md 2.3)",
            {"field": "inputs"},
        )
    if spec.ref not in REF_SHAPES:
        return (
            "attributes_schema_violation",
            f"`ref` must be one of {list(REF_SHAPES)}; got {spec.ref!r} (ACTIONS.md 2.3)",
            {"field": "inputs", "input": spec.name, "got": spec.ref},
        )
    if spec.kinds and _FORBIDDEN_INPUT_KIND in spec.kinds:
        return (
            "input_kind_mismatch",
            "`predicate` may not be an input kind, at any ref level -- EDGES.md 2.4.1's "
            "rule inherited, because an action taking two predicates is "
            "`merge_capabilities(commentable, searchable)`: ROADMAP.md's kill row "
            "spelled as a tool call (ACTIONS.md 2.3)",
            {"field": "inputs", "input": spec.name, "kinds": list(spec.kinds)},
        )
    return None


def _condition_problem(
    condition: Precondition, input_names: set[str]
) -> tuple[str, str, dict] | None:
    """ACTIONS.md 2.4, at the door. Rule 2.4-6: *the precondition door is shut where the
    effect door is* -- a condition naming no input is a declaration error, not a runtime
    unknown indistinguishable from a degraded backend."""
    if condition.kind not in PRECONDITION_KINDS:
        return (
            "attributes_schema_violation",
            f"{condition.kind!r} is not one of {list(PRECONDITION_KINDS)} -- the "
            f"precondition vocabulary is closed at four (ACTIONS.md 2.4)",
            {"field": "preconditions", "got": condition.kind},
        )
    if not condition.why or not condition.why.strip():
        return (
            "attributes_schema_violation",
            "`why` is required and non-empty on every precondition: an undescribed "
            "condition is how an escape hatch re-forms one level down, and a "
            "precondition nobody can read is one nobody will delete when it stops being "
            "true (ACTIONS.md 2.4)",
            {"field": "preconditions", "kind": condition.kind},
        )
    if not (condition.subject in input_names or _is_literal_ref(condition.subject)):
        return (
            "attributes_schema_violation",
            f"the condition's subject {condition.subject!r} names no InputSpec and is "
            f"not a literal identity ref (ACTIONS.md 2.4)",
            {"field": "preconditions", "subject": condition.subject},
        )
    if condition.kind == "predicate_holds" and not condition.predicate:
        return (
            "attributes_schema_violation",
            "a `predicate_holds` condition must name the predicate it asks about "
            "(ACTIONS.md 2.4)",
            {"field": "preconditions", "kind": condition.kind},
        )
    if condition.kind in ("edge_exists", "edge_absent"):
        if not condition.family:
            return (
                "attributes_schema_violation",
                "an edge condition must name the edge family it asks about "
                "(ACTIONS.md 2.4)",
                {"field": "preconditions", "kind": condition.kind},
            )
        if not (condition.object in input_names or _is_literal_ref(condition.object)):
            return (
                "attributes_schema_violation",
                f"the condition's object {condition.object!r} names no InputSpec and is "
                f"not a literal identity ref (ACTIONS.md 2.4)",
                {"field": "preconditions", "object": condition.object},
            )
    return None


def _effect_problem(effect: Effect) -> tuple[str, str, dict] | None:
    """ACTIONS.md 2.5, at the door -- and the door IS the declaration.

    EDGES.md 2.4.1 spent a whole adversarial round learning that *a rule checked only at
    write time is a rule a family author opts out of by declaring something permissive*,
    and the lesson transfers without modification.
    """
    if effect.op in GOVERNANCE_CALLS:
        return (
            "effect_not_permitted",
            f"{effect.op!r} is one of the six governance calls that may never be an "
            f"effect: an action that can `approve` closes the proposal->approval loop "
            f"with no human in it, and an action that can `merge_types` is ROADMAP.md's "
            f"kill row wearing a verb. An action may PROPOSE; only a human, or an "
            f"auto-policy a deployment set deliberately, may APPROVE (ACTIONS.md 2.5)",
            {"op": effect.op, "governance_calls": list(GOVERNANCE_CALLS)},
        )
    if effect.op not in EFFECT_OPS:
        return (
            "effect_not_permitted",
            f"{effect.op!r} is not one of {list(EFFECT_OPS)} -- the effect vocabulary is "
            f"closed at four operations (ACTIONS.md 2.5)",
            {"op": effect.op, "operations": list(EFFECT_OPS)},
        )
    if effect.op == "host_state":
        if not effect.why or not effect.why.strip():
            return (
                "effect_not_permitted",
                "`host_state` means *this action changes something this protocol does "
                "not model*, and it carries a mandatory sentence saying what. An empty "
                "list standing in for `we did not look` is what Rule U forbids by name "
                "(ACTIONS.md 2.5)",
                {"op": effect.op},
            )
        return None
    if effect.op == "propose_type":
        if not effect.namespace:
            return (
                "effect_not_permitted",
                "a `propose_type` effect must name the namespace it may propose into. "
                "`namespace=None` is a DECLARATION for the two edge ops (rule 2.5-10) "
                "and is simply unsatisfiable here -- the `warns on everything` escape "
                "2.5 names and refuses (ACTIONS.md 2.5)",
                {"op": effect.op},
            )
        if effect.kind not in PROPOSABLE_KINDS:
            return (
                "effect_not_permitted",
                f"a `propose_type` effect must NAME a kind, and only "
                f"{list(PROPOSABLE_KINDS)} may be proposed by an action -- an ALLOWLIST, "
                f"because a blocklist was walked past by OMITTING the key. A predicate's "
                f"extent is a set of TYPES and a freshly minted one is EMPTY, so it is "
                f"byte-identical to any other empty extent and INTERFACE.md 5.10's "
                f"refusal #2 does NOT fire on it; `action` is excluded because "
                f"ACTIONS.md 15.1 ranks a verb above a noun (ACTIONS.md 2.5, the kill "
                f"row)",
                {"op": effect.op, "kind": effect.kind, "allowed": list(PROPOSABLE_KINDS)},
            )
        return None
    # add_edge / retract_edge
    if not effect.family:
        return (
            "edge_family_unknown",
            "an edge effect must name the `kind=\"edge\"` family it may write "
            "(ACTIONS.md 2.5)",
            {"op": effect.op, "family": effect.family},
        )
    return None


def declared_family(attributes: dict[str, Any]) -> bool:
    """Does this ``kind="action"`` entry declare an action family at all?

    Rule **2.2-1**: an entry declaring NONE of the eight keys is a legal ``TypeEntry``
    and is NOT refused -- it is simply not yet usable as an action family, and
    ``preflight`` / ``record_invocation`` refuse on it with
    ``attributes_schema_violation``.

    **Round 2 reached the kill row through the first version of this test**, which
    returned early on the two REQUIRED keys alone: an entry declaring ``merge_types`` as
    an effect and nothing else was written at all three doors, so rule 2.5-5's *"the
    exclusion binds at declaration"* was bypassed by declaring LESS. Any of the eight
    makes the entry a declaration.
    """
    return any(attributes.get(key) not in (None, (), [], "", {}) for key in ACTION_ATTRIBUTE_KEYS)


def family_declaration_problem(
    attributes: dict[str, Any],
) -> tuple[str, str, dict] | None:
    """Is this a legal ``kind="action"`` declaration? ACTIONS.md 2.2/2.3/2.4/2.5.

    Returns ``(refusal reason, sentence, detail)`` or ``None``. The reason is returned
    rather than derived by the caller because the breaches are genuinely different
    failures -- ``effect_not_permitted`` for the effect vocabulary,
    ``input_kind_mismatch`` for a predicate input, ``edge_family_unknown`` for an effect
    naming a family that is not registered, and ``attributes_schema_violation`` for
    everything the attribute-schema mechanism owns, R18's cross-field rule included.

    **The cross-field rule returns R18's OWN value.** PACKAGE.md 5.6 records R18 as an
    exception list of length one *inside the attribute-schema mechanism*, and the shipped
    ``edges.family_declaration_problem`` returns ``attributes_schema_violation`` for
    exactly this shape. ACTIONS.md's first draft minted ``human_approval_required`` for
    it, which would have made two instances of one ruling return two different reasons;
    5.6's exception list goes to length two, one rule per kind, which is the shape R18
    licensed. ``human_approval_required`` survives for the *invocation* door only.

    **Whether an edge effect's family is REGISTERED is not checked here** -- this
    function is pure, and the registry checks the registration at the same door
    (rule 2.5-7, ``edge_family_unknown``, EDGES.md 4.3's existing value).
    """
    if not declared_family(attributes):
        return None

    for key in ("inputs", "preconditions", "effects"):
        value = attributes.get(key)
        if value is not None and not isinstance(value, (tuple, list)):
            return (
                "attributes_schema_violation",
                f"`{key}` is a list; got {type(value).__name__} (ACTIONS.md 2.2)",
                {"field": key, "got": type(value).__name__},
            )
    try:
        inputs = _as_specs(attributes.get("inputs") or ())
        conditions = _as_conditions(attributes.get("preconditions") or ())
        effects = _as_effects(attributes.get("effects") or ())
    except (AttributeError, TypeError) as exc:
        # A malformed row -- a string where a mapping belongs, most often out of an
        # `import_types` dump. It is a DECLARATION problem and returns one, rather than
        # raising out of a door whose contract is *"an import returns entries, not
        # exceptions"*. Row 4c's `_alias_identity_breach` records the same lesson: an
        # identity guard must never be the thing that blows up.
        return (
            "attributes_schema_violation",
            f"the declared shape could not be read as ACTIONS.md 2.2's eight keys: {exc}",
            {"field": "attributes"},
        )

    for spec in inputs:
        problem = _spec_problem(spec)
        if problem is not None:
            return problem

    input_names = {spec.name for spec in inputs}
    for condition in conditions:
        problem = _condition_problem(condition, input_names)
        if problem is not None:
            return problem

    for effect in effects:
        problem = _effect_problem(effect)
        if problem is not None:
            return problem

    # Rule 2.2-2: a family declaring SOME of the eight must declare `reversibility` and
    # `approval_mode`, and each must be a value of its closed vocabulary. A fourth
    # `approval_mode` or a fifth `reversibility` is `attributes_schema_violation`, never
    # a bare exception -- which is where three of these rules bound before round 2.
    reversibility = attributes.get("reversibility")
    if reversibility not in REVERSIBILITY:
        return (
            "attributes_schema_violation",
            f"`reversibility` is REQUIRED on a declared action family and must be one of "
            f"{list(REVERSIBILITY)}; got {reversibility!r}. There is no default: a family "
            f"that does not say is a family whose gate cannot be set (ACTIONS.md 2.6)",
            {"field": "reversibility", "got": reversibility},
        )
    approval_mode = attributes.get("approval_mode")
    if approval_mode not in APPROVAL_MODES:
        return (
            "attributes_schema_violation",
            f"`approval_mode` is REQUIRED on a declared action family and must be one of "
            f"{list(APPROVAL_MODES)}; got {approval_mode!r} (ACTIONS.md 5.2)",
            {"field": "approval_mode", "got": approval_mode},
        )

    # Rule 2.2-3 -- THE one cross-field rule, in R18's shape and with R18's own value.
    if reversibility == "irreversible" and approval_mode != "human":
        return (
            "attributes_schema_violation",
            "a family declaring `reversibility=\"irreversible\"` MUST declare "
            "`approval_mode=\"human\"`: a family saying that it cannot be undone AND "
            "that a model may run it unattended has written the failure mode this "
            "project exists to prevent into its own configuration (ACTIONS.md 2.2, the "
            "one cross-field rule, in ruling R18's shape)",
            {
                "field": "approval_mode",
                "reversibility": reversibility,
                "approval_mode": approval_mode,
            },
        )

    reachability = attributes.get("reachability")
    if reachability is not None and not isinstance(reachability, (tuple, list)):
        return (
            "attributes_schema_violation",
            "`reachability` is a list of opaque host-surface strings, and an EMPTY list "
            "is a positive declaration -- *this host exposes me on no named surface* -- "
            "not a forgotten field (ACTIONS.md 2.2, 10.2)",
            {"field": "reachability", "got": type(reachability).__name__},
        )
    for group in reachability or ():
        if not isinstance(group, str) or not group.strip():
            return (
                "attributes_schema_violation",
                "every `reachability` value is a non-empty opaque string in the HOST's "
                "vocabulary; the registry never interprets one (ACTIONS.md 10.2)",
                {"field": "reachability", "got": group},
            )

    min_auto_tier = attributes.get("min_auto_tier")
    if min_auto_tier is not None and not isinstance(min_auto_tier, str):
        return (
            "attributes_schema_violation",
            "`min_auto_tier` is an opaque tier string or None -- INTERFACE.md 2.7's "
            "posture, and the registry does not order tiers (ACTIONS.md 5.2)",
            {"field": "min_auto_tier", "got": type(min_auto_tier).__name__},
        )
    payload_schema = attributes.get("payload_schema")
    if payload_schema is not None and not isinstance(payload_schema, str):
        return (
            "attributes_schema_violation",
            "`payload_schema` names an AttributeSchema governing `Invocation.inputs`, "
            "or is None (ACTIONS.md 2.7)",
            {"field": "payload_schema", "got": type(payload_schema).__name__},
        )
    return None
