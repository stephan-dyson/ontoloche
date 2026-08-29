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
* ACTIONS 2.3 ``InputSpec`` and the third reference shape, ``EdgeRef``
* ACTIONS 2.4 the four precondition kinds, each answered by an existing call
* ACTIONS 3 ``Invocation`` and ``InvocationProvenance``, incl. declared-vs-
  observed effects and the ``effect_undeclared`` warning
* ACTIONS 5.2 ``approval_mode`` and ``min_auto_tier``, with the deployment's
  tier order supplied from outside (INTERFACE 2.7: the registry does not order
  tiers)
* ACTIONS 6 ``preflight`` / ``record_invocation`` / ``invocations``
* ACTIONS 10 ``projection`` and the greedy-whole-group admission rule
* ACTIONS 8 the three capability flags, enough of them to make the refusals real

Edges are NOT re-implemented: ``edges_probe_kit`` is imported, so an
``edge_exists`` precondition is answered by the same ``neighbors`` row #4 wrote
and by nothing this file invented. That is the point of the precondition
vocabulary and it should be checkable rather than asserted.

The refusal and warning vocabularies are imported from ``open_ontology.types``
rather than re-declared, so a probe that invented a value fails here rather
than in a reviewer's head.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
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

#: An actor id whose prefix marks it as NOT a person. ACTIONS 5.2.
NON_HUMAN_PREFIXES = ("ai:", "auto:", "derived:", "seed", "import:")


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
    namespace: str = "default"      # the FAMILY's namespace, for edge_* kinds

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

    def __str__(self) -> str:
        # ACTIONS 2.5's warning is `effect_undeclared:<op>:<target>`, and
        # `host_state` HAS no target -- found by running the CMS probe, which
        # printed `effect_undeclared:host_state:None:None`. Its `why` is the
        # only identifier it has, and an admission with no name is not one.
        if self.op == "host_state":
            return f"host_state:{self.why}"
        if self.op == "propose_type":
            return f"propose_type:{self.namespace}:{self.kind}"
        return f"{self.op}:{self.family}"


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
        # ACTIONS 8.2, EDGES 6.2's binding rule on a third store.
        if (
            self.action_store_shares_connection
            and self.action_transaction_scope != self.transaction_scope
        ):
            raise ValueError(
                "one connection cannot have two transaction scopes -- ACTIONS 8.2"
            )


# --------------------------------------------------------------------------
# ACTIONS 2.2 -- the family


@dataclass(frozen=True)
class ActionFamily:
    """A ``kind="action"`` TypeEntry, reduced to the eight keys ACTIONS 2.2
    declares. In the real design these live in ``TypeEntry.attributes`` under an
    ``AttributeSchema`` keyed ``(namespace, "action")``; here they are fields,
    because the probe is not testing PACKAGE 5."""

    name: str
    reversibility: str                      # REQUIRED, no default -- ACTIONS 2.2
    approval_mode: str                      # REQUIRED, no default
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

    A refusal at DECLARATION time is raised rather than returned, because the
    probe's families are frozen dataclasses and the design tests need the door
    to be the declaration (ACTIONS 2.5-5). The registry's real surface returns a
    ``Refusal``; the vocabulary is the same one and it is checked here.
    """

    def __init__(self, reason: str, detail: dict | None = None) -> None:
        if reason not in REFUSAL_REASONS:
            raise ValueError(f"{reason!r} is not in the closed vocabulary")
        self.reason = reason
        self.detail = detail or {}
        super().__init__(f"{reason}: {self.detail}")


@dataclass(frozen=True)
class Refusal:
    refused: bool
    reason: str
    detail: dict = field(default_factory=dict)

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
    """ACTIONS 6's four calls, plus the declaration door of 2.2/2.4/2.5."""

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
    ) -> None:
        self.edges = edges
        self.caps = caps or ActionCapabilities()
        # INTERFACE 2.7: the deployment supplies the order. ``None`` means the
        # registry cannot compare two tiers and must say so rather than guess.
        self.tier_order = tuple(tier_order) if tier_order else None
        self.registered_types = {str(t): t for t in registered_types}
        self.registered_predicates = dict(registered_predicates or {})
        self.edge_families = set(edge_families)
        # {predicate_name: (consumer_id, ...)} -- INTERFACE 5.1's answer, and
        # ACTIONS 10.5 reads it through the family's own `predicates`.
        self.consumers = dict(consumers or {})
        self.family_predicates = dict(family_predicates or {})
        self.families: dict[tuple[str, str], ActionFamily] = {}
        self._log: list[Invocation] = []
        self._seq = 0

    # -- the declaration door ------------------------------------------

    def declare(self, family: ActionFamily) -> ActionFamily:
        """ACTIONS 2.2/2.3/2.5: every rule that binds at DECLARATION time.

        EDGES 2.4.1 spent an adversarial round establishing that a rule checked
        only at write time is a rule a family author opts out of by declaring
        something permissive. The lesson transfers verbatim: the door is here.
        """
        if family.reversibility not in REVERSIBILITY:
            raise ValueError(f"reversibility must be one of {REVERSIBILITY}")
        if family.approval_mode not in APPROVAL_MODES:
            # ACTIONS 5.2-1. A closed vocabulary; a fourth mode is not a typo to
            # be tolerated.
            raise DeclarationRefused(
                "human_approval_required",
                {"door": "declaration", "problem": "approval_mode", "got": family.approval_mode},
            )
        # ACTIONS 2.2 -- the ONE cross-field rule, in R18's shape.
        if family.reversibility == "irreversible" and family.approval_mode != "human":
            raise DeclarationRefused(
                "human_approval_required",
                {
                    "door": "declaration",
                    "family": family.name,
                    "reversibility": "irreversible",
                    "approval_mode": family.approval_mode,
                },
            )
        for eff in family.effects:
            # ACTIONS 2.5-2: the six governance calls, as a general rule.
            if eff.op in GOVERNANCE_CALLS:
                raise DeclarationRefused(
                    "effect_not_permitted",
                    {
                        "door": "declaration",
                        "op": eff.op,
                        "why": "the governance loop is not an effect -- ACTIONS 2.5",
                    },
                )
            # ACTIONS 2.5-1: closed at four.
            if eff.op not in EFFECT_OPS:
                raise DeclarationRefused(
                    "effect_not_permitted",
                    {"door": "declaration", "op": eff.op, "why": "not one of the four"},
                )
            # ACTIONS 2.5-4: host_state admits an unknown and must name it.
            if eff.op == "host_state" and not eff.why.strip():
                raise DeclarationRefused(
                    "effect_not_permitted",
                    {"door": "declaration", "op": eff.op, "why": "host_state needs a why"},
                )
            # ACTIONS 2.5-7: an edge effect naming an unregistered family reuses
            # EDGES' existing value rather than minting one.
            if eff.op in ("add_edge", "retract_edge") and eff.family not in self.edge_families:
                raise DeclarationRefused(
                    "edge_family_unknown",
                    {"door": "declaration", "family": eff.family},
                )
        self.families[(family.namespace, family.name)] = family
        return family

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
            return Refusal(True, "action_family_unknown", {"family": family, "namespace": namespace})

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

        # ACTIONS 6.1: unknown is refused, and the refusal says UNKNOWN rather
        # than false. Treating it as satisfied would let a degraded backend
        # approve everything.
        if unknown:
            return Preflight(
                verdict="refused",
                refusal=Refusal(
                    True,
                    "precondition_unmet",
                    {
                        "state": "unknown",
                        "kind": unknown[0].condition.kind,
                        "subject": unknown[0].condition.subject,
                        "why": unknown[0].why,
                    },
                ),
                **base,
            )
        if failed:
            return Preflight(
                verdict="refused",
                refusal=Refusal(
                    True,
                    "precondition_unmet",
                    {
                        "state": "false",
                        "kind": failed[0].condition.kind,
                        "subject": failed[0].condition.subject,
                    },
                ),
                **base,
            )

        # ACTIONS 5.2 -- the approval gate.
        if fam.approval_mode == "human":
            if not approved_by or approved_by.startswith(NON_HUMAN_PREFIXES):
                return Preflight(
                    verdict="refused",
                    refusal=Refusal(
                        True,
                        "human_approval_required",
                        {"door": "preflight", "approved_by": approved_by},
                    ),
                    **base,
                )
            return Preflight(verdict="allowed", approved_by=approved_by, **base)

        if fam.min_auto_tier is not None:
            if self.tier_order is None:
                # INTERFACE 2.7: the registry does not order tiers. With no
                # deployment order the floor cannot be evaluated, and Rule U
                # forbids a confident pass.
                return Preflight(
                    verdict="refused",
                    refusal=Refusal(
                        True,
                        "tier_below_action_policy",
                        {
                            "state": "unknown",
                            "why": "no deployment tier order supplied; the registry "
                            "does not order tiers (INTERFACE 2.7)",
                            "min_auto_tier": fam.min_auto_tier,
                            "tier": tier,
                        },
                    ),
                    **base,
                )
            if tier is None or self._rank(tier) < self._rank(fam.min_auto_tier):
                return Preflight(
                    verdict="refused",
                    refusal=Refusal(
                        True,
                        "tier_below_action_policy",
                        {"tier": tier, "min_auto_tier": fam.min_auto_tier},
                    ),
                    **base,
                )
        return Preflight(verdict="allowed", approved_by="auto:action_policy", **base)

    def _rank(self, tier: str) -> int:
        assert self.tier_order is not None
        if tier not in self.tier_order:
            raise ValueError(f"tier {tier!r} is not in the deployment's order")
        return self.tier_order.index(tier)

    def _evaluate(self, c: Precondition, inputs: dict[str, InputRef]) -> PreconditionResult:
        """ACTIONS 2.4: four kinds, each answered by a call that already exists."""
        if c.kind == "type_active":
            ref = inputs.get(c.subject)
            target = str(ref) if ref is not None else c.subject
            return PreconditionResult(
                condition=c,
                holds=target in self.registered_types,
                evaluated_by="resolve_type",
            )
        if c.kind == "predicate_holds":
            ref = inputs.get(c.subject)
            key = str(ref) if ref is not None else c.subject
            members = self.registered_predicates.get(c.predicate or "")
            if members is None:
                return PreconditionResult(
                    condition=c,
                    holds=None,
                    evaluated_by="predicates",
                    why=f"no registered predicate named {c.predicate!r}",
                )
            return PreconditionResult(
                condition=c, holds=key in members, evaluated_by="predicates"
            )
        if c.kind in ("edge_exists", "edge_absent"):
            src = inputs.get(c.subject)
            dst = inputs.get(c.object or "")
            if self.edges is None:
                return PreconditionResult(
                    condition=c,
                    holds=None,
                    evaluated_by="neighbors",
                    why="this backend declares stores_edges=False",
                )
            if src is None or dst is None:
                return PreconditionResult(
                    condition=c,
                    holds=None,
                    evaluated_by="neighbors",
                    why=f"input {c.subject!r} or {c.object!r} was not supplied",
                )
            report = self.edges.neighbors(src, [c.family], 1, namespace=c.namespace)
            if getattr(report, "refused", False):
                return PreconditionResult(
                    condition=c,
                    holds=None,
                    evaluated_by="neighbors",
                    why=f"neighbors refused: {getattr(report, 'reason', '?')}",
                )
            found = str(dst) in {str(n) for n in report.nodes}
            return PreconditionResult(
                condition=c,
                holds=found if c.kind == "edge_exists" else not found,
                evaluated_by="neighbors",
            )
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
        created_by: str = "user",
        confidence: float | None = None,
        source_version: str | None = None,
        refusal: Refusal | None = None,
        compensates: str | None = None,
        at: datetime = NOW,
    ) -> Invocation | Refusal:
        if not self.caps.stores_invocations:
            return Refusal(
                True,
                "action_store_absent",
                {"family": family, "why": self.caps.why.get("stores_invocations")},
            )
        fam = self.families.get((namespace, family))
        if fam is None:
            return Refusal(True, "action_family_unknown", {"family": family})
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        if gate_verdict not in GATE_VERDICTS:
            raise ValueError(f"gate_verdict must be one of {GATE_VERDICTS}")
        # ACTIONS 3.4: a refused invocation with no reason is an unexplained no.
        if outcome == "refused" and refusal is None:
            raise ValueError("outcome='refused' requires a refusal (ACTIONS 3.4)")
        # ACTIONS 3.2: never blank-implying-human on an applied invocation.
        if outcome == "applied" and not approved_by:
            approved_by = "auto:action_policy"

        warnings: list[str] = []
        declared = {str(e) for e in fam.effects}
        for eff in observed_effects:
            if str(eff) not in declared:
                # ACTIONS 2.5-6: a WARNING on a kept record, never a refusal.
                warnings.append(f"effect_undeclared:{eff}")
        # ACTIONS 8.2, and it is stamped HERE rather than carried forward.
        if self.caps.action_transaction_scope == "savepoint":
            warnings.append(
                "not_durable_until_host_commits:"
                + self.caps.why.get("action_transaction_scope", "host owns the commit")
            )
        for w in warnings:
            if w.split(":", 1)[0] not in WARNING_VALUES:
                raise ValueError(f"{w!r} is not in the closed warnings vocabulary")

        self._seq += 1
        inv = Invocation(
            invocation_id=f"inv{self._seq:04d}",
            family=family,
            namespace=namespace,
            inputs=dict(inputs),
            # ACTIONS 3.1: COPIED, not referenced.
            declared_effects=tuple(fam.effects),
            observed_effects=tuple(observed_effects),
            outcome=outcome,
            gate_verdict=gate_verdict,
            refusal=refusal,
            compensates=compensates,
            provenance=InvocationProvenance(
                created_at=at,
                created_by_actor=actor,
                created_by=created_by,
                model_tier=tier,
                confidence=confidence,
                approved_by=approved_by,
                approved_at=at if approved_by else None,
                source_version=source_version,
                history_why=(
                    None
                    if self.caps.stores_invocation_events
                    else self.caps.why.get("stores_invocation_events")
                ),
            ),
            warnings=tuple(warnings),
        )
        self._log.append(inv)
        return inv

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
        limit: int = 100,
    ) -> InvocationReport | Refusal:
        if not self.caps.stores_invocations:
            return Refusal(
                True,
                "action_store_absent",
                {"why": self.caps.why.get("stores_invocations")},
            )
        rows = list(self._log)
        filtered = False
        for value, pred in (
            (family, lambda i: i.family == family),
            (namespace, lambda i: i.namespace == namespace),
            (actor, lambda i: i.provenance.created_by_actor == actor),
            (outcome, lambda i: i.outcome == outcome),
            (gate_verdict, lambda i: i.gate_verdict == gate_verdict),
        ):
            if value is not None:
                rows = [r for r in rows if pred(r)]
                filtered = True
        if effect_undeclared is not None:
            rows = [
                r
                for r in rows
                if any(w.startswith("effect_undeclared:") for w in r.warnings)
                is effect_undeclared
            ]
            filtered = True
        truncated = len(rows) > limit
        why = None
        if truncated:
            why = f"the answer was bounded at limit={limit}"
        elif not self.caps.indexes_invocations_by_family and family is not None:
            why = self.caps.why.get("indexes_invocations_by_family")
        return InvocationReport(
            invocations=tuple(rows[:limit]),
            known=len(rows) if self.caps.indexes_invocations_by_family else None,
            complete=not truncated and (not filtered or True) and why is None,
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
        pool = [
            f
            for f in self.families.values()
            if f.status == "active" and (namespace is None or f.namespace == namespace)
        ]
        if order is None:
            # ACTIONS 10.3: counts and nothing else. The one question this call
            # could obviously answer is the one it is built to refuse.
            counts: dict[str, int] = {}
            for f in pool:
                for group in f.reachability:
                    counts[group] = counts.get(group, 0) + 1
            return ProjectionReport(
                surface=surface,
                budget=budget,
                reserved=reserved,
                counts=counts,
                rule="greedy_whole_group",
                order_source=None,
                fits=(),
                would_evict=(),
                over_by=0,
                consumers_at_risk=(),
                known=len(pool),
                complete=False,
                why_incomplete="no order supplied; the registry does not choose "
                "which families reach a surface",
            )

        order = tuple(order)
        counts = {g: 0 for g in order}
        grouped: dict[str, list[ActionFamily]] = {g: [] for g in order}
        for f in pool:
            for group in order:                      # first match wins
                if group in f.reachability:
                    counts[group] += 1
                    grouped[group].append(f)
                    break
        if all(c == 0 for c in counts.values()):
            # ACTIONS 10.3: an entirely unknown order is a typo, and an empty
            # report for a typo is mechanism C committed by the call that exists
            # to surface it.
            return Refusal(
                True,
                "action_family_unknown",
                {"order": list(order), "surface": surface},
            )

        capacity = budget - reserved
        used = 0
        fits: list[str] = []
        evict: list[str] = []
        for group in order:
            if not evict and used + counts[group] <= capacity:
                used += counts[group]
                fits.append(group)
            else:
                evict.append(group)
        over_by = max(0, (used + sum(counts[g] for g in evict)) - capacity)

        at_risk: list[str] = []
        for group in evict:
            for f in grouped[group]:
                for pred in self.family_predicates.get(f.name, ()):
                    at_risk.extend(self.consumers.get(pred, ()))

        unknown_groups = [g for g in order if counts[g] == 0]
        return ProjectionReport(
            surface=surface,
            budget=budget,
            reserved=reserved,
            counts=counts,
            rule="greedy_whole_group",
            order_source="caller",
            fits=tuple(fits),
            would_evict=tuple(evict),
            over_by=over_by,
            consumers_at_risk=tuple(dict.fromkeys(at_risk)),
            known=len(pool),
            # ACTIONS 10.5: consumers_at_risk inherits ConsumerReport.complete
            # == False (INTERFACE 5.1), so this report can never be complete
            # once it names casualties -- and an EMPTY casualty list is that
            # same False wearing a different name.
            complete=False,
            why_incomplete=(
                "consumers_at_risk inherits ConsumerReport.complete == False "
                "(INTERFACE 5.1); it is known casualties, never all of them"
                + (
                    f"; groups with no registered family: {unknown_groups}"
                    if unknown_groups
                    else ""
                )
            ),
        )


def assert_vocabularies_closed() -> None:
    """The six refusal values and the one warning value this spec adds are in
    the package's closed tuples, not in this file's head."""
    for r in (
        "action_family_unknown",
        "precondition_unmet",
        "human_approval_required",
        "tier_below_action_policy",
        "effect_not_permitted",
        "action_store_absent",
    ):
        assert r in REFUSAL_REASONS, f"{r} missing from types.REFUSAL_REASONS"
    assert "effect_undeclared" in WARNING_VALUES
