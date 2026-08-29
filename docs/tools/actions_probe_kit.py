"""A THROWAWAY in-memory implementation of ACTIONS.md v0, for the design tests.

Row #6 is a spec and ships no action store. But the lesson of rows 3c, 3d, 3e
and 4b is blunt -- *nothing of substance came from reading* -- so the three
design tests in ``ACTIONS.md`` 11-13 are walked by executing the spec against
real rows rather than by reasoning about it. This module is that execution: it
lives in ``docs/tools`` and not in ``open_ontology``, the package does not
import it, and the contract suite does not know it exists.

What it implements, and nothing more:

* ACTIONS 2.2 the family's eight declared keys, with the declaration-time
  refusals: the one cross-field rule (irreversible => human), the closed
  precondition vocabulary, the closed effect vocabulary, and the six governance
  calls that may never be an effect
* ACTIONS 2.3 ``InputSpec``, ``EdgeRef``, and the rule at BOTH layers --
  declaration AND invocation
* ACTIONS 2.4 the four precondition kinds, each answered by an existing call
* ACTIONS 3 ``Invocation`` and ``InvocationProvenance``, incl. declared-vs-
  observed effects, compensation, and the ``effect_undeclared`` and
  ``approval_unrecorded`` warnings
* ACTIONS 5.2 ``approval_mode`` and ``min_auto_tier``, with the deployment's
  tier order supplied from outside (INTERFACE 2.7: the registry does not order
  tiers) and an unknown answer that is ``None`` rather than ``False``
* ACTIONS 6 ``preflight`` / ``record_invocation`` / ``invocations``
* ACTIONS 10 ``projection`` and the greedy-whole-group admission rule
* ACTIONS 8 the three capability flags, enough of them to make the refusals real

Edges are NOT re-implemented: ``edges_probe_kit`` is imported, so an
``edge_exists`` precondition is answered by the same ``neighbors`` row #4 wrote
and by nothing this file invented.

The refusal and warning vocabularies are imported from ``open_ontology.types``
rather than re-declared, so a probe that invented a value fails here rather
than in a reviewer's head. The shapes deliberately match the SHIPPED ones --
``Refusal(reason, detail, refused=True)`` in the package's own field order --
because ACTIONS 14 asks the build row to transpose these checks into the suite,
and a kit whose constructors are inverted is a kit nobody can transpose. That
inversion was a round-1 finding.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from edges_probe_kit import (  # noqa: E402
    EdgeRegistry,
    InstanceRef,
    NodeRef,
    TypeRef,
)
from open_ontology.types import REFUSAL_REASONS, WARNING_VALUES  # noqa: E402

NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)

# ACTIONS 2.5 -- the closed operation vocabulary, and the six calls excluded
# from it as a GENERAL rule rather than a family's opt-in.
EFFECT_OPS = ("add_edge", "retract_edge", "propose_type", "host_state")
GOVERNANCE_CALLS = (
    "approve",
    "reject",
    "retire",
    "reinstate",
    "merge_types",
    "register_consumer",
)
PRECONDITION_KINDS = ("type_active", "predicate_holds", "edge_exists", "edge_absent")
REVERSIBILITY = ("reversible", "compensable", "irreversible")
APPROVAL_MODES = ("auto", "review", "human")
OUTCOMES = ("applied", "refused", "failed", "compensated")
GATE_VERDICTS = ("allowed", "refused", "not_asked")
#: ACTIONS 6.1 -- the closed set of calls that may answer a precondition.
#: `resolve_type` is NOT among them; see `_evaluate` and contortion ACT6.
EVALUATORS = ("list_types", "predicates", "neighbors")


def created_by_of(actor: str) -> str:
    """INTERFACE 2.1: the registry reads `created_by` OFF THE ACTOR.

    Mirrors the shipped derivation rather than taking a parameter -- a round-1
    finding, because the spec's printed ``record_invocation`` signature had no
    ``created_by`` and the first kit invented one.
    """
    if actor.startswith("ai:"):
        return "ai"
    if actor.startswith("derived:"):
        return "derived"
    if actor == "seed" or actor.startswith("import:"):
        return "seed"
    if actor.startswith("auto:"):
        # An auto-policy is not a person and not a model. `derived` is the honest
        # value: a deterministic rule with no human and no model in the loop.
        return "derived"
    return "user"


# --------------------------------------------------------------------------
# ACTIONS 2.3 -- references


@dataclass(frozen=True)
class EdgeRef:
    """The third reference shape. ACTIONS 2.3."""

    edge_id: str
    family: str
    namespace: str = "default"

    def __str__(self) -> str:
        return f"{self.namespace}:edge:{self.family}#{self.edge_id}"


InputRef = TypeRef | InstanceRef | EdgeRef


def ref_shape(ref: InputRef) -> str:
    if isinstance(ref, EdgeRef):
        return "edge"
    if isinstance(ref, InstanceRef):
        return "instance"
    return "type"


def ref_kind(ref: InputRef) -> str | None:
    if isinstance(ref, EdgeRef):
        return "edge"
    if isinstance(ref, InstanceRef):
        return ref.type.kind
    return ref.kind


@dataclass(frozen=True)
class InputSpec:
    name: str
    ref: Literal["type", "instance", "edge"]
    required: bool = True
    kinds: tuple[str, ...] | None = None
    families: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.ref not in ("type", "instance", "edge"):
            raise ValueError(f"input {self.name!r}: ref must be type|instance|edge")
        # ACTIONS 2.3, inherited from EDGES 2.4.1 as a GENERAL rule: an action
        # taking two predicates is the kill row with a verb in front of it.
        if self.kinds and "predicate" in self.kinds:
            raise ValueError(
                f"input {self.name!r}: `predicate` may not be an input kind "
                "-- ACTIONS 2.3, EDGES 2.4.1's rule inherited"
            )


@dataclass(frozen=True)
class Precondition:
    kind: str
    subject: str
    why: str
    predicate: str | None = None
    family: str | None = None
    object: str | None = None
    #: ACTIONS 2.4 -- the FAMILY's namespace, for the edge kinds. Required by
    #: `Registry.neighbors`, which makes `namespace` keyword-only WITHOUT a
    #: default precisely because "default" is a wrong answer nobody notices.
    #: Round 1 found the spec's printed shape missing it while this kit had
    #: silently added it -- the "fixed only in the probe" failure, exactly.
    namespace: str = "default"

    def __post_init__(self) -> None:
        if self.kind not in PRECONDITION_KINDS:
            raise ValueError(
                f"precondition kind {self.kind!r} is not one of {PRECONDITION_KINDS} "
                "-- ACTIONS 2.4, the vocabulary is closed at four"
            )
        # ACTIONS 2.4-3, on PACKAGE 5.2's reasoning for FieldSpec.description.
        if not self.why.strip():
            raise ValueError(
                f"precondition {self.kind}/{self.subject}: `why` is required and "
                "non-empty -- ACTIONS 2.4"
            )


@dataclass(frozen=True)
class Effect:
    op: str
    family: str | None = None
    namespace: str | None = None
    kind: str | None = None
    why: str = ""

    def identity(self) -> tuple:
        """ACTIONS 2.5 -- what makes two effects the same effect.

        ``why`` is NOT part of identity for the three protocol ops, so amending a
        sentence does not turn one declared effect into two. ``host_state`` has no
        target at all, so its ``why`` is its only identifier -- found by running
        the CMS probe, which printed ``effect_undeclared:host_state:None:None``.
        """
        if self.op == "host_state":
            return ("host_state", self.why)
        return (self.op, self.namespace, self.family, self.kind)

    def __str__(self) -> str:
        if self.op == "host_state":
            return f"host_state:{self.why}"
        if self.op == "propose_type":
            return f"propose_type:{self.namespace}:{self.kind}"
        return f"{self.op}:{self.namespace}:{self.family}"


# --------------------------------------------------------------------------
# ACTIONS 8 -- capabilities


@dataclass(frozen=True)
class ActionCapabilities:
    stores_invocations: bool = True
    stores_invocation_events: bool = True
    indexes_invocations_by_family: bool = True
    action_transaction_scope: Literal["owned", "savepoint"] = "owned"
    action_store_shares_connection: bool = True
    transaction_scope: Literal["owned", "savepoint"] = "owned"
    why: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # PACKAGE 3.2's invariant. C0-01's carve-out shape: when the store is
        # absent the other two are VACUOUS, not declined (ACTIONS 8.1).
        if not self.stores_invocations:
            if not self.why.get("stores_invocations"):
                raise ValueError("stores_invocations=False needs a non-empty why")
        else:
            for flag in ("stores_invocation_events", "indexes_invocations_by_family"):
                if getattr(self, flag) is False and not self.why.get(flag):
                    raise ValueError(f"{flag}=False needs a non-empty why (PACKAGE 3.2)")

    def scope_conflict(self) -> str | None:
        """ACTIONS 8.2 -- RETURNS the sentence rather than raising, exactly as the
        shipped ``Capabilities.scope_conflict()`` does, so a capability record
        stays a plain frozen object a test can construct in any shape it likes.
        Raising here was a round-1 finding."""
        if (
            self.action_store_shares_connection
            and self.action_transaction_scope != self.transaction_scope
        ):
            return (
                "one connection cannot have two transaction scopes: "
                f"transaction_scope={self.transaction_scope!r} but "
                f"action_transaction_scope={self.action_transaction_scope!r} "
                "-- ACTIONS 8.2"
            )
        return None


# --------------------------------------------------------------------------
# ACTIONS 2.2 -- the family


@dataclass(frozen=True)
class ActionFamily:
    """A ``kind="action"`` TypeEntry, reduced to the eight keys ACTIONS 2.2
    declares. In the real design these live in ``TypeEntry.attributes`` under an
    ``AttributeSchema`` keyed ``(namespace, "action")``; here they are fields,
    because the probe is not testing PACKAGE 5.

    ``reversibility`` and ``approval_mode`` default to ``None`` -- meaning *not
    declared as an action family*. A ``kind="action"`` entry with no attributes
    is a legal ``TypeEntry`` (INTERFACE 2.1 requires none), and refusing its
    REGISTRATION would reject types INTERFACE says are legal. The hole that
    opens -- declare nothing, then invoke anything -- is closed at the other end,
    in ``preflight``. That is ``edges.family_declaration_problem``'s own recorded
    decision for the identical case one kind along; round 1 found this document
    silently taking the opposite position.
    """

    name: str
    reversibility: str | None = None
    approval_mode: str | None = None
    namespace: str = "default"
    definition: str = ""
    inputs: tuple[InputSpec, ...] = ()
    preconditions: tuple[Precondition, ...] = ()
    effects: tuple[Effect, ...] = ()
    min_auto_tier: str | None = None
    reachability: tuple[str, ...] = ()
    payload_schema: str | None = None
    status: Literal["proposed", "active", "retired"] = "active"


class DeclarationRefused(Exception):
    """A declaration refusal, carrying the closed-vocabulary reason.

    Raised rather than returned because the probe's families are frozen
    dataclasses and the design tests need the door to be the declaration
    (ACTIONS 2.5-5). The registry's real surface returns a ``Refusal`` from
    ``propose_type`` / ``approve`` and an ``import_refused:<reason>`` warning
    from ``import_types``; the vocabulary is the same one and it is checked here.
    """

    def __init__(self, reason: str, detail: dict | None = None) -> None:
        if reason not in REFUSAL_REASONS:
            raise ValueError(f"{reason!r} is not in the closed vocabulary")
        self.reason = reason
        self.detail = detail or {}
        super().__init__(f"{reason}: {self.detail}")


@dataclass(frozen=True)
class Refusal:
    """The SHIPPED field order (``open_ontology.types.Refusal``), deliberately."""

    reason: str
    detail: dict = field(default_factory=dict)
    refused: bool = True

    def __post_init__(self) -> None:
        if self.reason not in REFUSAL_REASONS:
            raise ValueError(f"{self.reason!r} is not in the closed vocabulary")


# --------------------------------------------------------------------------
# ACTIONS 3 -- invocations


@dataclass(frozen=True)
class InvocationProvenance:
    created_at: datetime
    created_by_actor: str
    created_by: str = "user"
    model_tier: str | None = None
    confidence: float | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    evidence: tuple = ()
    source_version: str | None = None
    history: tuple = ()
    history_why: str | None = None


@dataclass(frozen=True)
class Invocation:
    invocation_id: str
    family: str
    namespace: str
    inputs: dict[str, InputRef]
    declared_effects: tuple[Effect, ...]
    observed_effects: tuple[Effect, ...]
    outcome: str
    gate_verdict: str
    provenance: InvocationProvenance
    refusal: Refusal | None = None
    compensates: str | None = None
    compensated_by: str | None = None
    reviewed_at: datetime | None = None
    warnings: tuple[str, ...] = ()
    attr_schema_version: int | None = None


@dataclass(frozen=True)
class PreconditionResult:
    condition: Precondition
    holds: bool | None          # None = could not be evaluated. Rule U, NOT False
    evaluated_by: str
    why: str | None = None


@dataclass(frozen=True)
class Preflight:
    family: str
    namespace: str
    verdict: str
    declared_effects: tuple[Effect, ...]
    preconditions: tuple[PreconditionResult, ...]
    approval_mode: str
    known: int
    complete: bool
    refusal: Refusal | None = None
    approved_by: str | None = None
    tier_floor: str | None = None
    tier_floor_why: str | None = None
    why_incomplete: str | None = None


@dataclass(frozen=True)
class InvocationReport:
    invocations: tuple[Invocation, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectionReport:
    surface: str
    budget: int
    reserved: int
    counts: dict[str, int]
    admitted: dict[str, int]
    rule: str
    order_source: str | None
    fits: tuple[str, ...]
    would_evict: tuple[str, ...]
    over_by: int
    consumers_at_risk: tuple[str, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None


# --------------------------------------------------------------------------
# The facade


class ActionRegistry:
    """ACTIONS 6's four calls, plus the declaration door of 2.2/2.3/2.4/2.5."""

    def __init__(
        self,
        edges: EdgeRegistry | None = None,
        *,
        caps: ActionCapabilities | None = None,
        registered_types: Iterable[TypeRef] = (),
        registered_predicates: dict[str, tuple[str, ...]] | None = None,
        edge_families: Iterable[str] = (),
        tier_order: Sequence[str] | None = None,
        consumers: dict[str, tuple[str, ...]] | None = None,
        family_predicates: dict[str, tuple[str, ...]] | None = None,
        types_listing_complete: bool = True,
    ) -> None:
        self.edges = edges
        self.caps = caps or ActionCapabilities()
        # INTERFACE 2.7: the DEPLOYMENT supplies the order. An empty order means
        # the registry cannot compare two tiers and must say so rather than guess.
        self.tier_order = tuple(tier_order) if tier_order is not None else ()
        self.registered_types = {str(t): t for t in registered_types}
        # INTERFACE 5.6: a FILTERED listing is not complete. `type_active` can
        # therefore say True on a hit and never False on a miss unless the
        # listing it scanned came back complete. ACT6.
        self.types_listing_complete = types_listing_complete
        self.registered_predicates = dict(registered_predicates or {})
        self.edge_families = set(edge_families)
        self.consumers = dict(consumers or {})
        self.family_predicates = dict(family_predicates or {})
        self.families: dict[tuple[str, str], ActionFamily] = {}
        self._log: list[Invocation] = []
        self._seq = 0

    # -- the declaration door ------------------------------------------

    def declare(self, family: ActionFamily, *, door: str = "propose_type") -> ActionFamily:
        """ACTIONS 2.2/2.3/2.4/2.5: every rule that binds at DECLARATION time.

        ``door`` names which of the three shipped enforcement sites this is --
        ``propose_type``, ``approve`` or ``import_types`` -- because the shipped
        ``_edge_family_refusal`` is called from all three, *"because a rule with
        one enforcement point is a rule with one door left open"*. Round 1 found
        ``import_types`` unmentioned by the spec and unguarded here.
        """
        if family.reversibility is None and family.approval_mode is None:
            # 2.2-1: a MISSING declaration is not a breach; it is simply not yet
            # usable as an action family, and `preflight` refuses on it.
            self.families[(family.namespace, family.name)] = family
            return family
        problem = self.declaration_problem(family)
        if problem is not None:
            reason, detail = problem
            extra = {"door": door}
            if door == "import_types":
                # `import_types` returns entries, never a Refusal, so the shipped
                # edge path warns instead. Nothing is written either way.
                extra["warning"] = f"import_refused:{reason}"
            raise DeclarationRefused(reason, {**detail, **extra})
        self.families[(family.namespace, family.name)] = family
        return family

    def declaration_problem(self, family: ActionFamily) -> tuple[str, dict] | None:
        """Every declaration-time rule, in one place, so all three doors share it."""
        if family.reversibility not in REVERSIBILITY:
            return ("attributes_schema_violation",
                    {"field": "reversibility", "got": family.reversibility,
                     "why": f"must be one of {REVERSIBILITY} -- ACTIONS 2.6"})
        if family.approval_mode not in APPROVAL_MODES:
            return ("attributes_schema_violation",
                    {"field": "approval_mode", "got": family.approval_mode,
                     "why": f"must be one of {APPROVAL_MODES} -- ACTIONS 5.2"})
        # ACTIONS 2.2 -- the ONE cross-field rule, in R18's shape, returning R18's
        # OWN refusal value: PACKAGE 5.6 records R18 as an exception list inside
        # the attribute-schema mechanism, and the shipped
        # `family_declaration_problem` returns `attributes_schema_violation` for
        # exactly this shape. Round 1 found this kit minting a new value for it.
        if family.reversibility == "irreversible" and family.approval_mode != "human":
            return ("attributes_schema_violation",
                    {"field": "approval_mode", "reversibility": "irreversible",
                     "approval_mode": family.approval_mode,
                     "why": "an irreversible family must declare approval_mode='human' "
                            "-- ACTIONS 2.2, the one cross-field rule"})
        names = {i.name for i in family.inputs}

        def resolvable(token: str | None) -> bool:
            # ACTIONS 2.4: `subject` is "the InputSpec.name this is about, OR a
            # literal ref". A literal ref carries its identity triple and is
            # recognisable by it; anything else that names no input is a typo.
            return bool(token) and (token in names or token.count(":") >= 2)

        for c in family.preconditions:
            # The precondition door is shut where the effect door is (round 1): a
            # condition naming no input is a declaration error, not a runtime
            # unknown indistinguishable from a degraded backend.
            if not resolvable(c.subject):
                return ("attributes_schema_violation",
                        {"field": "preconditions", "subject": c.subject,
                         "why": "names no InputSpec and is not a literal ref "
                                "-- ACTIONS 2.4"})
            if c.kind in ("edge_exists", "edge_absent"):
                if not resolvable(c.object):
                    return ("attributes_schema_violation",
                            {"field": "preconditions", "object": c.object,
                             "why": "names no InputSpec and is not a literal ref "
                                    "-- ACTIONS 2.4"})
                if not c.family:
                    return ("attributes_schema_violation",
                            {"field": "preconditions",
                             "why": "an edge condition needs a family -- ACTIONS 2.4"})
            if c.kind == "predicate_holds" and not c.predicate:
                return ("attributes_schema_violation",
                        {"field": "preconditions",
                         "why": "predicate_holds needs a predicate -- ACTIONS 2.4"})
        for eff in family.effects:
            if eff.op in GOVERNANCE_CALLS:
                return ("effect_not_permitted",
                        {"op": eff.op,
                         "why": "the governance loop is not an effect -- ACTIONS 2.5"})
            if eff.op not in EFFECT_OPS:
                return ("effect_not_permitted",
                        {"op": eff.op, "why": "not one of the four -- ACTIONS 2.5"})
            if eff.op == "host_state" and not eff.why.strip():
                return ("effect_not_permitted",
                        {"op": eff.op, "why": "host_state needs a why -- ACTIONS 2.5"})
            if eff.op == "propose_type" and eff.kind == "predicate":
                # Round 1's THIRD predicate door: an action that may propose a
                # predicate, on a namespace whose policy auto-approves, mints a
                # live capability set unattended. UC1's deployment IS that policy.
                return ("effect_not_permitted",
                        {"op": eff.op, "kind": "predicate",
                         "why": "an action may not propose a `predicate`: its extent is "
                                "a set of TYPES and INTERFACE 5.10 refusal #2 is "
                                "non-overridable -- ACTIONS 2.5, the kill row"})
            if eff.op in ("add_edge", "retract_edge") and eff.family not in self.edge_families:
                return ("edge_family_unknown", {"family": eff.family})
        return None

    # -- ACTIONS 2.3, the SECOND layer ----------------------------------

    def _input_problem(
        self, fam: ActionFamily, inputs: dict[str, InputRef]
    ) -> Refusal | None:
        """The invocation-time half of ACTIONS 2.3, and it closes the kill row.

        Round 1 declared a family with ``kinds=None``, supplied two
        ``kind="predicate"`` refs and got ``verdict="allowed"``:
        ``merge_capabilities(commentable, searchable)``, end to end. EDGES 2.4.1
        binds at BOTH layers; this is the layer that was missing.
        """
        by_name = {i.name: i for i in fam.inputs}
        for name, ref in inputs.items():
            spec = by_name.get(name)
            if spec is None:
                return Refusal("input_kind_mismatch",
                               {"input": name, "problem": "undeclared",
                                "why": "the family declares no input by that name"})
            if ref_shape(ref) != spec.ref:
                return Refusal("input_kind_mismatch",
                               {"input": name, "problem": "ref",
                                "declared": spec.ref, "supplied": ref_shape(ref)})
            kind = ref_kind(ref)
            # GENERAL, not a family's opt-in: a predicate is refused whatever the
            # family declared, exactly as EDGES 2.4.1 excludes it at both levels.
            if kind == "predicate":
                return Refusal("input_kind_mismatch",
                               {"input": name, "problem": "predicate",
                                "why": "a predicate is never an action input -- "
                                       "ACTIONS 2.3, the kill row one indirection away"})
            if spec.ref == "instance" and kind != "entity":
                return Refusal("input_kind_mismatch",
                               {"input": name, "problem": "kind",
                                "declared": "entity", "supplied": kind})
            if spec.kinds is not None and kind not in spec.kinds:
                return Refusal("input_kind_mismatch",
                               {"input": name, "problem": "kind",
                                "declared": list(spec.kinds), "supplied": kind})
            if spec.ref == "edge" and spec.families is not None:
                if getattr(ref, "family", None) not in spec.families:
                    return Refusal("input_kind_mismatch",
                                   {"input": name, "problem": "family",
                                    "declared": list(spec.families),
                                    "supplied": getattr(ref, "family", None)})
        for spec in fam.inputs:
            if spec.required and spec.name not in inputs:
                return Refusal("input_kind_mismatch",
                               {"input": spec.name, "problem": "missing"})
        return None

    # -- ACTIONS 6.1 ----------------------------------------------------

    def preflight(
        self,
        family: str,
        inputs: dict[str, InputRef],
        *,
        namespace: str = "default",
        actor: str,
        tier: str | None = None,
        approved_by: str | None = None,
    ) -> Preflight | Refusal:
        fam = self.families.get((namespace, family))
        if fam is None:
            return Refusal("action_family_unknown",
                           {"family": family, "namespace": namespace})
        if fam.reversibility is None or fam.approval_mode is None:
            # 2.2-1's other end: registered as a type, not declared as a family.
            return Refusal("attributes_schema_violation",
                           {"family": family,
                            "why": "this kind='action' entry declares no `reversibility` "
                                   "or `approval_mode`, so it is not yet usable as an "
                                   "action family -- ACTIONS 2.2"})
        bad = self._input_problem(fam, inputs)
        if bad is not None:
            return bad

        results = [self._evaluate(c, inputs) for c in fam.preconditions]
        unknown = [r for r in results if r.holds is None]
        failed = [r for r in results if r.holds is False]
        complete = not unknown

        base = dict(
            family=family,
            namespace=namespace,
            declared_effects=fam.effects,
            preconditions=tuple(results),
            approval_mode=fam.approval_mode,
            known=len(results),
            complete=complete,
            tier_floor=fam.min_auto_tier,
            tier_floor_why=(
                None
                if fam.min_auto_tier
                else "the family declares no floor; every tier auto-approves"
            ),
            why_incomplete=(
                None if complete else "; ".join(r.why or "unknown" for r in unknown)
            ),
        )

        if unknown:
            return Preflight(
                verdict="refused",
                refusal=Refusal("precondition_unmet",
                                {"state": "unknown",
                                 "kind": unknown[0].condition.kind,
                                 "subject": unknown[0].condition.subject,
                                 "why": unknown[0].why}),
                **base,
            )
        if failed:
            return Preflight(
                verdict="refused",
                refusal=Refusal("precondition_unmet",
                                {"state": "false",
                                 "kind": failed[0].condition.kind,
                                 "subject": failed[0].condition.subject}),
                **base,
            )

        # ACTIONS 5.2 -- the approval gate.
        if fam.approval_mode == "human":
            # An ALLOWLIST off `created_by`, not a three-prefix blocklist: round 1
            # got `bot:reaper`, `svc:cleanup`, `AI:bot` and `nobody` past the
            # blocklist. INTERFACE 2.1 already derives `created_by` from the actor
            # and the record already carries it.
            if not approved_by or created_by_of(approved_by) != "user":
                return Preflight(
                    verdict="refused",
                    refusal=Refusal("human_approval_required",
                                    {"door": "preflight", "approved_by": approved_by,
                                     "created_by": created_by_of(approved_by)
                                     if approved_by else None}),
                    **base,
                )
            return Preflight(verdict="allowed", approved_by=approved_by, **base)

        if fam.min_auto_tier is not None:
            below = self._below(tier, fam.min_auto_tier)
            if below is None:
                # Rule U: unknown, never a confident "below". Three ways to get
                # here -- no deployment order, no tier supplied, a tier the order
                # does not contain -- and `detail` says which.
                return Preflight(
                    verdict="refused",
                    refusal=Refusal("tier_below_action_policy",
                                    {"state": "unknown",
                                     "why": self._why_unknown_tier(tier),
                                     "min_auto_tier": fam.min_auto_tier,
                                     "tier": tier}),
                    **base,
                )
            if below:
                return Preflight(
                    verdict="refused",
                    refusal=Refusal("tier_below_action_policy",
                                    {"state": "false", "tier": tier,
                                     "min_auto_tier": fam.min_auto_tier}),
                    **base,
                )
        return Preflight(verdict="allowed", approved_by="auto:action_policy", **base)

    def _below(self, tier: str | None, minimum: str) -> bool | None:
        """``bool | None`` -- the shipped ``TierOrder.below()``'s own contract."""
        if not self.tier_order:
            return None
        if tier is None or tier not in self.tier_order or minimum not in self.tier_order:
            return None
        return self.tier_order.index(tier) < self.tier_order.index(minimum)

    def _why_unknown_tier(self, tier: str | None) -> str:
        if not self.tier_order:
            return ("no deployment tier order supplied; the registry does not order "
                    "tiers (INTERFACE 2.7)")
        if tier is None:
            return "no tier was supplied for the invoking actor"
        return f"tier {tier!r} is not in this deployment's order"

    def _evaluate(self, c: Precondition, inputs: dict[str, InputRef]) -> PreconditionResult:
        """ACTIONS 2.4: four kinds, each answered by a call that already exists."""
        if c.kind == "type_active":
            ref = inputs.get(c.subject)
            target = str(ref) if ref is not None else c.subject
            if target in self.registered_types:
                return PreconditionResult(c, True, "list_types")
            # A MISS off a filtered listing is not a fact. INTERFACE 5.6:
            # `TypeListing.complete` is False whenever a filter suppressed rows,
            # and the facade has no name filter that would make a listing narrow
            # and complete at once. ACT6.
            if self.types_listing_complete:
                return PreconditionResult(c, False, "list_types")
            return PreconditionResult(
                c, None, "list_types",
                why="the listing that would have answered this came back incomplete; "
                    "a miss off an incomplete listing is not a fact (INTERFACE 5.6)")
        if c.kind == "predicate_holds":
            ref = inputs.get(c.subject)
            key = str(ref) if ref is not None else c.subject
            members = self.registered_predicates.get(c.predicate or "")
            if members is None:
                # What the shipped `predicates(of=...)` RAISES; ACTIONS 6.1
                # requires it caught, because a raise escapes the return type.
                return PreconditionResult(
                    c, None, "predicates",
                    why=f"no registered predicate named {c.predicate!r} "
                        "(the shipped call raises UnknownType here; caught per 6.1)")
            return PreconditionResult(c, key in members, "predicates")
        if c.kind in ("edge_exists", "edge_absent"):
            src = inputs.get(c.subject)
            dst = inputs.get(c.object or "")
            if self.edges is None:
                return PreconditionResult(
                    c, None, "neighbors",
                    why="this backend declares stores_edges=False")
            if src is None or dst is None:
                return PreconditionResult(
                    c, None, "neighbors",
                    why=f"input {c.subject!r} or {c.object!r} was not supplied")
            report = self.edges.neighbors(src, [c.family], 1, namespace=c.namespace)
            if getattr(report, "refused", False):
                return PreconditionResult(
                    c, None, "neighbors",
                    why=f"neighbors refused: {getattr(report, 'reason', '?')}")
            found = str(dst) in {str(n) for n in report.nodes}
            return PreconditionResult(
                c, found if c.kind == "edge_exists" else not found, "neighbors")
        raise AssertionError(f"unreachable precondition kind {c.kind!r}")

    # -- ACTIONS 6.2 ----------------------------------------------------

    def record_invocation(
        self,
        family: str,
        inputs: dict[str, InputRef],
        *,
        namespace: str = "default",
        actor: str,
        outcome: str,
        tier: str | None = None,
        observed_effects: Sequence[Effect] = (),
        gate_verdict: str = "not_asked",
        approved_by: str | None = None,
        confidence: float | None = None,
        evidence: Sequence[Any] = (),
        source_version: str | None = None,
        refusal: Refusal | None = None,
        compensates: str | None = None,
    ) -> Invocation | Refusal:
        if not self.caps.stores_invocations:
            return Refusal("action_store_absent",
                           {"family": family,
                            "why": self.caps.why.get("stores_invocations")})
        fam = self.families.get((namespace, family))
        if fam is None:
            return Refusal("action_family_unknown", {"family": family})
        bad = self._input_problem(fam, inputs)
        if bad is not None:
            return bad
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        if gate_verdict not in GATE_VERDICTS:
            raise ValueError(f"gate_verdict must be one of {GATE_VERDICTS}")
        if outcome == "refused" and refusal is None:
            raise ValueError("outcome='refused' requires a refusal (ACTIONS 3.4)")

        warnings: list[str] = []
        # ACTIONS 3.2 -- NEVER FABRICATED. The never-null rule binds where the
        # gate decided; everywhere else a null plus this warning is the honest
        # form. Round 1 found `auto:<policy>` being written for an
        # irreversible/human family invoked by `ai:reaper`.
        if outcome == "applied" and not approved_by:
            warnings.append("approval_unrecorded")
        declared = {e.identity() for e in fam.effects}
        for eff in observed_effects:
            if eff.identity() not in declared:
                warnings.append(f"effect_undeclared:{eff}")
        if self.caps.action_transaction_scope == "savepoint":
            warnings.append(
                "not_durable_until_host_commits:"
                + self.caps.why.get("action_transaction_scope", "host owns the commit"))
        for w in warnings:
            if w.split(":", 1)[0] not in WARNING_VALUES:
                raise ValueError(f"{w!r} is not in the closed warnings vocabulary")

        self._seq += 1
        inv = Invocation(
            invocation_id=f"inv{self._seq:04d}",
            family=family,
            namespace=namespace,
            inputs=dict(inputs),
            declared_effects=tuple(fam.effects),      # ACTIONS 3.1 -- COPIED
            observed_effects=tuple(observed_effects),
            outcome=outcome,
            gate_verdict=gate_verdict,
            refusal=refusal,
            compensates=compensates,
            provenance=InvocationProvenance(
                created_at=NOW,
                created_by_actor=actor,
                created_by=created_by_of(actor),      # DERIVED, INTERFACE 2.1
                model_tier=tier,
                confidence=confidence,
                approved_by=approved_by,
                approved_at=NOW if approved_by else None,
                evidence=tuple(evidence),
                source_version=source_version,
                history_why=(
                    None if self.caps.stores_invocation_events
                    else self.caps.why.get("stores_invocation_events")),
            ),
            warnings=tuple(warnings),
        )
        self._log.append(inv)
        # ACTIONS 3.4 -- a compensation makes the original `compensated`, and the
        # facade derives the backward pointer (9). Round 1 found neither half.
        if compensates:
            for i, prior in enumerate(self._log[:-1]):
                if prior.invocation_id == compensates:
                    self._log[i] = replace(prior, outcome="compensated",
                                           compensated_by=inv.invocation_id)
                    break
        return inv

    def review(self, invocation_id: str, *, reviewed_by: str) -> Invocation | Refusal:
        """The ``invocation_reviewed`` event, and the only thing that clears
        ``unreviewed``. ACTIONS 3.5 / 5.2."""
        for i, inv in enumerate(self._log):
            if inv.invocation_id == invocation_id:
                self._log[i] = replace(inv, reviewed_at=NOW)
                return self._log[i]
        return Refusal("action_family_unknown", {"invocation_id": invocation_id})

    # -- ACTIONS 6.3 ----------------------------------------------------

    def invocations(
        self,
        *,
        family: str | None = None,
        namespace: str | None = None,
        actor: str | None = None,
        outcome: str | None = None,
        gate_verdict: str | None = None,
        effect_undeclared: bool | None = None,
        unreviewed: bool | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> InvocationReport | Refusal:
        if not self.caps.stores_invocations:
            return Refusal("action_store_absent",
                           {"why": self.caps.why.get("stores_invocations")})
        rows = list(self._log)
        filtered = False
        for value, pred in (
            (family, lambda i: i.family == family),
            (namespace, lambda i: i.namespace == namespace),
            (actor, lambda i: i.provenance.created_by_actor == actor),
            (outcome, lambda i: i.outcome == outcome),
            (gate_verdict, lambda i: i.gate_verdict == gate_verdict),
            (since, lambda i: i.provenance.created_at >= since),
        ):
            if value is not None:
                rows = [r for r in rows if pred(r)]
                filtered = True
        if effect_undeclared is not None:
            rows = [r for r in rows
                    if any(w.startswith("effect_undeclared:") for w in r.warnings)
                    is effect_undeclared]
            filtered = True
        if unreviewed is not None:
            fams = self.families
            rows = [
                r for r in rows
                if ((fams.get((r.namespace, r.family)) is not None
                     and fams[(r.namespace, r.family)].approval_mode == "review"
                     and r.reviewed_at is None) is unreviewed)
            ]
            filtered = True
        truncated = len(rows) > limit
        why = None
        if truncated:
            why = f"the answer was bounded at limit={limit}"
        elif filtered:
            # Rule K, INTERFACE 5.6's rule for TypeListing: a filter suppressed
            # rows, so this is not a complete answer. Round 1 found the previous
            # expression `(not filtered or True)` -- always True -- stamping the
            # override query complete.
            why = "a filter suppressed rows; this is a floor, not a total"
        elif not self.caps.indexes_invocations_by_family:
            why = self.caps.why.get("indexes_invocations_by_family")
        return InvocationReport(
            invocations=tuple(rows[:limit]),
            # `known` is None only where the backend genuinely cannot count a
            # FILTERED answer -- an unfiltered census is a length it materialised.
            known=(len(rows)
                   if self.caps.indexes_invocations_by_family or not filtered
                   else None),
            complete=why is None,
            why_incomplete=why,
        )

    # -- ACTIONS 6.4 / 10 ------------------------------------------------

    def projection(
        self,
        surface: str,
        *,
        budget: int,
        order: Sequence[str] | None = None,
        reserved: int = 0,
        namespace: str | None = None,
    ) -> ProjectionReport | Refusal:
        pool = [f for f in self.families.values()
                if f.status == "active" and f.reversibility is not None
                and (namespace is None or f.namespace == namespace)]
        # `counts` is RULE-INDEPENDENT: a family declaring two groups is counted
        # in both, whatever the order. Round 1 found `counts` changing with the
        # order, because it was being built by the admission loop.
        counts: dict[str, int] = {}
        for f in pool:
            for group in f.reachability:
                if order is None or group in order:
                    counts[group] = counts.get(group, 0) + 1

        if order is None:
            return ProjectionReport(
                surface=surface, budget=budget, reserved=reserved,
                counts=counts, admitted={}, rule="greedy_whole_group",
                order_source=None, fits=(), would_evict=(), over_by=0,
                consumers_at_risk=(), known=len(pool), complete=False,
                why_incomplete="no order supplied; the registry does not choose "
                               "which families reach a surface")

        order = tuple(order)
        counts = {g: counts.get(g, 0) for g in order}
        # `admitted` is the RULE's charge: a family occupies ONE slot, in the
        # first group of `order` it declares. `counts` and `admitted` differ
        # exactly when a family declares two of the ordered groups.
        admitted: dict[str, int] = {g: 0 for g in order}
        grouped: dict[str, list[ActionFamily]] = {g: [] for g in order}
        selected = 0
        for f in pool:
            for group in order:
                if group in f.reachability:
                    admitted[group] += 1
                    grouped[group].append(f)
                    selected += 1
                    break
        if not any(g in f.reachability
                   for f in self.families.values()
                   if f.reversibility is not None
                   for g in order):
            # A typo, judged against EVERY registered family rather than against
            # the namespace-filtered pool: an empty NAMESPACE is a legitimate
            # scope, not a misspelling. Round 1 found the filtered version
            # refusing a real projection over an empty namespace.
            return Refusal("action_family_unknown",
                           {"order": list(order), "surface": surface,
                            "why": "no registered family carries any of these groups"})

        capacity = budget - reserved
        used = 0
        fits: list[str] = []
        evict: list[str] = []
        for group in order:
            if not evict and used + admitted[group] <= capacity:
                used += admitted[group]
                fits.append(group)
            else:
                evict.append(group)
        over_by = max(0, (used + sum(admitted[g] for g in evict)) - capacity)

        at_risk: list[str] = []
        for group in evict:
            for f in grouped[group]:
                for pred in self.family_predicates.get(f.name, ()):
                    at_risk.extend(self.consumers.get(pred, ()))

        unknown_groups = [g for g in order if counts[g] == 0]
        return ProjectionReport(
            surface=surface, budget=budget, reserved=reserved,
            counts=counts, admitted=admitted, rule="greedy_whole_group",
            order_source="caller", fits=tuple(fits), would_evict=tuple(evict),
            over_by=over_by, consumers_at_risk=tuple(dict.fromkeys(at_risk)),
            # `known` is what the report SELECTED, not the whole registry.
            known=selected,
            # ACTIONS 10.5: consumers_at_risk inherits ConsumerReport.complete ==
            # False (INTERFACE 5.1), so this can never be complete -- and an EMPTY
            # casualty list is that same False wearing a different name.
            complete=False,
            why_incomplete=(
                "consumers_at_risk inherits ConsumerReport.complete == False "
                "(INTERFACE 5.1); it is known casualties, never all of them"
                + (f"; groups with no registered family: {unknown_groups}"
                   if unknown_groups else "")))


def assert_vocabularies_closed() -> None:
    """The seven refusal values and the two warning values this spec adds are in
    the package's closed tuples, not in this file's head."""
    for r in (
        "action_family_unknown", "precondition_unmet", "human_approval_required",
        "tier_below_action_policy", "effect_not_permitted", "action_store_absent",
        "input_kind_mismatch",
    ):
        assert r in REFUSAL_REASONS, f"{r} missing from types.REFUSAL_REASONS"
    for w in ("effect_undeclared", "approval_unrecorded"):
        assert w in WARNING_VALUES, f"{w} missing from types.WARNING_VALUES"
