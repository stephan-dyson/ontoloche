"""The three design tests, re-run through **`open_ontology.Registry`** rather than
through the throwaway kit they were written against. Row 6b, brief item 5.

**Why this module exists, in one sentence:** row #6's own §17 had to record that its
`import_types` kill-row fix *"exists only in the probe kit, which is a legitimate
spec-row boundary -- the row ships no action store -- but §19.2 said `Fixed` without the
qualifier, two paragraphs after §14 quotes row 4b's lesson about findings fixed only in
a throwaway probe kit the package does not import."*

So each of the four `actions_*_probe.py` files keeps its kit leg exactly as it was --
that is what makes its 96 pre-registered numbers comparable run to run -- and calls
:func:`shipped_leg` to ask the **same questions of the shipped registry**. Where the two
engines disagree, the disagreement is the finding; where they agree, the spec row's
verdicts have stopped being claims about a model and started being claims about the
package.

This is `actions_nyc_probe.py`'s own *"two engines on purpose"* arrangement, generalised
to all four -- and it is what `C19` transposes into the contract suite, where a backend
author can be held to it.

Run indirectly: ``py docs/tools/actions_cms_probe.py`` (and the other three).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from open_ontology import Registry  # noqa: E402
from open_ontology.actions import (  # noqa: E402
    Effect,
    InputSpec,
    Precondition,
    action_attributes,
)
from open_ontology.backends.sqlite import SQLiteAdapter  # noqa: E402
from open_ontology.edges import InstanceRef, TypeRef  # noqa: E402
from open_ontology.types import Evidence, Refusal, TypeEntry  # noqa: E402

EVIDENCE = [Evidence(kind="data", summary="the shipped-leg fixture")]


def _registry() -> Registry:
    return Registry(SQLiteAdapter(":memory:"))


def _seed(registry, name, *, kind="entity", namespace="default", predicates=(), attributes=None):
    out = registry.propose_type(
        name,
        f"a {name}, for the purposes of the shipped leg",
        EVIDENCE,
        "user:sd",
        kind=kind,
        namespace=namespace,
        predicates=list(predicates),
        attributes=attributes,
    )
    if isinstance(out, (TypeEntry, Refusal)):
        return out
    return registry.approve(out.id, "user:sd")


def _edge_family(registry, name, *, namespace="default", level="instance", kinds=("entity",)):
    return _seed(
        registry,
        name,
        kind="edge",
        namespace=namespace,
        attributes={
            "level": level,
            "symmetric": False,
            "inverse_label": None,
            "endpoint_kinds": {"src": list(kinds), "dst": list(kinds)},
            "payload_schema": None,
        },
    )


def _family(registry, name, *, namespace="default", **keys):
    return _seed(
        registry,
        name,
        kind="action",
        namespace=namespace,
        attributes=action_attributes(**keys),
    )


def shipped_leg(check, *, fixture: str) -> None:
    """Ask the shipped registry the questions ``fixture``'s design test asked the kit.

    ``check(label, ok, detail="")`` is the probe's own recorder, so these rows land in
    the same tally and the same failure report. ``fixture`` is ``"beacon"``, ``"cms"``,
    ``"nyc"`` or ``"governance"`` and selects which of the three walks to re-run.
    """
    print(f"\n  the SHIPPED registry, asked {fixture.upper()}'s own questions:")
    {
        "beacon": _beacon,
        "cms": _cms,
        "nyc": _nyc,
        "governance": _governance,
    }[fixture](check)


# --------------------------------------------------------------------------- UC1


def _beacon(check) -> None:
    """T1.1, T1.3, T1.4, T1.6 and T1.7 against `open_ontology.Registry`.

    Nothing in `beacon` is imported, executed or written here either: the three families
    are declared in a registry BESIDE it, about its actions, which is 11's own method.
    """
    registry = _registry()
    _edge_family(registry, "person_links")
    _edge_family(registry, "task_stakeholders")
    _edge_family(registry, "project_stakeholders")

    # T1.1 -- all three express, with the eight keys and no key missing.
    stakeholder = _family(
        registry,
        "add_task_stakeholder",
        reversibility="compensable",
        approval_mode="auto",
        inputs=[InputSpec("task", "instance"), InputSpec("person", "instance")],
        preconditions=[
            Precondition(
                "edge_absent",
                "task",
                "beacon returns one opaque `mutation_failed` for two unrelated causes; "
                "this is the *already linked* half",
                family="task_stakeholders",
                object="person",
            )
        ],
        effects=[Effect(op="add_edge", family="task_stakeholders", namespace="default")],
        reachability=["task"],
    )
    search = _family(
        registry,
        "search_tasks",
        reversibility="reversible",
        approval_mode="auto",
        effects=[],
        reachability=["common"],
    )
    check(
        "T1.1s  all three express as kind='action' entries in the SHIPPED registry",
        isinstance(stakeholder, TypeEntry) and isinstance(search, TypeEntry),
        f"{stakeholder!r} {search!r}",
    )

    # T1.3 -- irreversible + auto is refused at the DECLARATION door, with R18's value.
    refused = registry.propose_type(
        "delete_person",
        "Delete a Person from the CRM. Not reversible via undo.",
        EVIDENCE,
        "user:sd",
        kind="action",
        attributes=action_attributes(reversibility="irreversible", approval_mode="auto"),
    )
    check(
        "T1.3s  irreversible+auto is refused at declaration with R18's own value",
        isinstance(refused, Refusal) and refused.reason == "attributes_schema_violation",
        f"{refused!r}",
    )

    # T1.4 / T1.5 -- 3 declarable edge families + 2 host_state admissions, one of which
    # is the mid-action commit no field can express (contortion ACT5).
    delete_person = _family(
        registry,
        "delete_person",
        reversibility="irreversible",
        approval_mode="human",
        effects=[
            Effect(op="retract_edge", family="person_links", namespace="default"),
            Effect(op="retract_edge", family="task_stakeholders", namespace="default"),
            Effect(op="retract_edge", family="project_stakeholders", namespace="default"),
            Effect(op="host_state", why="11 of 15 foreign keys on people.id"),
            Effect(
                op="host_state",
                why="connection_service.unlink COMMITS before the delete (ACT5)",
            ),
        ],
        reachability=["person"],
    )
    declared = delete_person.attributes["effects"]
    check(
        "T1.4s  3 edge families declarable and 2 host_state admissions, in the store",
        len([e for e in declared if e["op"] == "retract_edge"]) == 3
        and len([e for e in declared if e["op"] == "host_state"]) == 2,
        str(len(declared)),
    )
    check(
        "T1.6s  `effects: []` is honest, and the no-floor case is a stated absence",
        search.attributes["effects"] == []
        and registry.preflight("search_tasks", {}, actor="user:sd").tier_floor_why,
    )

    # T1.7 -- the 127/128 arithmetic, through the shipped `projection`.
    for group, count in (("common", 45), ("task", 48), ("project", 21), ("person", 13)):
        for i in range(count - (1 if group in ("task", "common", "person") else 0)):
            _family(
                registry,
                f"{group}_pad_{i:03d}",
                reversibility="reversible",
                approval_mode="auto",
                reachability=[group],
            )
    order = ("common", "task", "project", "person")
    report = registry.projection("task_detail", budget=127, order=order)
    check(
        "T1.7s  beacon's counts reproduce through the SHIPPED projection",
        report.counts == {"common": 45, "task": 48, "project": 21, "person": 13},
        str(report.counts),
    )
    check(
        "T1.7s2 all four fit at 127 and over_by is 0",
        report.fits == order and report.over_by == 0,
        f"{report.fits} over_by={report.over_by}",
    )
    _family(
        registry,
        "task_the_49th",
        reversibility="reversible",
        approval_mode="auto",
        reachability=["task"],
    )
    tipped = registry.projection("task_detail", budget=127, order=order)
    check(
        "T1.7s3 a 49th `task` family evicts `person` outright, over_by=1",
        tipped.would_evict == ("person",) and tipped.over_by == 1,
        f"{tipped.would_evict} over_by={tipped.over_by}",
    )
    check(
        "T1.9s  consumers_at_risk is empty AND complete is False -- the same false, renamed",
        tipped.consumers_at_risk == () and tipped.complete is False,
    )


# --------------------------------------------------------------------------- UC2


def _cms(check) -> None:
    """T2.1–T2.7 and T2.9 against `open_ontology.Registry`."""
    registry = _registry()
    _seed(registry, "facility", kind="entity", namespace="cms")
    _seed(registry, "scope_severity_code", kind="value_set", namespace="cms")
    facility = InstanceRef(TypeRef("cms", "entity", "facility"), "275020")

    # T2.9 -- the effect names an edge family that must ALREADY be registered.
    early = registry.propose_type(
        "flag_facility_for_review",
        "flag a facility whose citations warrant review",
        EVIDENCE,
        "user:sd",
        kind="action",
        namespace="cms",
        attributes=action_attributes(
            reversibility="reversible",
            approval_mode="auto",
            effects=[Effect(op="add_edge", family="flagged_for_review", namespace="cms")],
        ),
    )
    check(
        "T2.9s  an effect on an unregistered edge family is refused at declaration",
        isinstance(early, Refusal) and early.reason == "edge_family_unknown",
        f"{early!r}",
    )

    _edge_family(registry, "flagged_for_review", namespace="cms")
    # T2.2 -- the severity precondition is NOT expressible. The fifth kind is refused.
    fifth = registry.propose_type(
        "flag_by_severity",
        "flag a facility with an Immediate-Jeopardy citation",
        EVIDENCE,
        "user:sd",
        kind="action",
        namespace="cms",
        attributes=action_attributes(
            reversibility="reversible",
            approval_mode="auto",
            inputs=[InputSpec("facility", "instance")],
            preconditions=[
                Precondition(
                    "value_in_set", "facility", "Scope Severity Code in {J, K, L}"
                )
            ],
        ),
    )
    check(
        "T2.2s  the value-level condition has no kind and is refused -- ACT4, shipped",
        isinstance(fifth, Refusal) and fifth.detail.get("got") == "value_in_set",
        f"{fifth!r}",
    )

    # T2.4 -- what IS expressible is a question about the VOCABULARY, not about the data.
    family = _family(
        registry,
        "flag_facility_for_review",
        namespace="cms",
        reversibility="reversible",
        approval_mode="auto",
        min_auto_tier="sonnet",
        inputs=[InputSpec("facility", "instance")],
        preconditions=[
            Precondition(
                "type_active",
                "cms:value_set:scope_severity_code",
                "the A-L scale must still be in the vocabulary -- which is NOT a gate on "
                "the data, and presenting it as one would be the confident wrong answer "
                "Rule U forbids",
            )
        ],
        effects=[Effect(op="add_edge", family="flagged_for_review", namespace="cms")],
    )
    check("T2.1s  the family expresses under 2.2's eight keys", isinstance(family, TypeEntry))

    # T2.5 / T2.6 / T2.7 -- the tier gate, three states.
    low = registry.preflight(
        "flag_facility_for_review",
        {"facility": facility},
        namespace="cms",
        actor="ai:haiku_classifier",
        tier="haiku",
    )
    check(
        "T2.5s  the cheap tier is refused, and `state` says FALSE",
        low.verdict == "refused"
        and low.refusal.reason == "tier_below_action_policy"
        and low.refusal.detail["state"] == "false",
        f"{low.refusal!r}",
    )
    high = registry.preflight(
        "flag_facility_for_review",
        {"facility": facility},
        namespace="cms",
        actor="ai:c",
        tier="opus",
    )
    check(
        "T2.6s  the same invocation at `opus` is allowed by the policy",
        high.verdict == "allowed" and (high.approved_by or "").startswith("auto:"),
        f"{high.verdict} {high.approved_by}",
    )

    from open_ontology.policy import NamespacePolicy, TierOrder

    orderless = Registry(
        registry.adapter, policy=NamespacePolicy(tier_order=TierOrder(())), seed_equivalent_to=False
    )
    unknown = orderless.preflight(
        "flag_facility_for_review",
        {"facility": facility},
        namespace="cms",
        actor="ai:c",
        tier="haiku",
    )
    check(
        "T2.7s  with no deployment order the floor is UNKNOWN, never a confident false",
        unknown.verdict == "refused" and unknown.refusal.detail["state"] == "unknown",
        f"{unknown.refusal!r}",
    )

    # The record path: a refused invocation is recordable, an undeclared effect warns,
    # and every override is enumerable -- 4's one measurement, on the shipped store.
    registry.record_invocation(
        "flag_facility_for_review",
        {"facility": facility},
        namespace="cms",
        actor="ai:haiku_classifier",
        tier="haiku",
        outcome="refused",
        gate_verdict="refused",
        refusal=low.refusal,
    )
    over = registry.record_invocation(
        "flag_facility_for_review",
        {"facility": facility},
        namespace="cms",
        actor="user:sd",
        outcome="applied",
        gate_verdict="refused",
        observed_effects=[
            Effect(op="add_edge", family="flagged_for_review", namespace="cms"),
            Effect(op="host_state", why="wrote a note nobody declared"),
        ],
    )
    check(
        "       an undeclared effect is a WARNING on a kept record, in the shipped ledger",
        any(w.startswith("effect_undeclared:") for w in over.warnings),
        str(over.warnings),
    )
    census = registry.invocations(gate_verdict="refused", outcome="applied")
    check(
        "       every override is enumerable, and the answer is a FLOOR",
        census.known == 1 and census.complete is False,
        f"{census.known} override(s), complete={census.complete}",
    )


# --------------------------------------------------------------------------- UC3


def _nyc(check) -> None:
    """T3.1, T3.3, T3.4 and T3.5 against `open_ontology.Registry`.

    **T3.5 is the load-bearing one** and it was already a claim about the shipped
    registry in the kit-driven probe: with the `equivalent_to` edge present and
    `reconcile_borough` declared, `merge_types` across namespaces must STILL refuse, and
    refuse again under acknowledgement.
    """
    registry = _registry()
    for namespace in ("dpr", "oti_311", "dot"):
        _seed(registry, "borough", kind="value_set", namespace=namespace)
    _edge_family(
        registry, "reconciled_with", namespace="dpr", level="type", kinds=("value_set",)
    )
    a = TypeRef("dpr", "value_set", "borough")
    b = TypeRef("oti_311", "value_set", "borough")
    c = TypeRef("dot", "value_set", "borough")
    # The realistic write order is a CHAIN, not a triangle: each publisher joins the one
    # it found. EDGES 3.1's `equivalent_to` is seeded at store creation.
    registry.add_edge("equivalent_to", a, b, "derived:catalogue_rule", namespace="default")
    registry.add_edge("equivalent_to", b, c, "derived:catalogue_rule", namespace="default")

    # T3.1 -- two `value_set` TypeRef inputs are legal; `predicate` is not.
    predicate_input = registry.propose_type(
        "merge_capabilities",
        "the kill row with a verb in front of it",
        EVIDENCE,
        "user:sd",
        kind="action",
        attributes=action_attributes(
            reversibility="reversible",
            approval_mode="auto",
            inputs=[InputSpec("a", "type", kinds=("predicate",))],
        ),
    )
    check(
        "T3.1s  `predicate` may not be an input kind -- refused at declaration",
        isinstance(predicate_input, Refusal)
        and predicate_input.reason == "input_kind_mismatch",
        f"{predicate_input!r}",
    )

    family = _family(
        registry,
        "reconcile_borough",
        reversibility="reversible",
        approval_mode="auto",
        inputs=[
            InputSpec("a", "type", kinds=("value_set",)),
            InputSpec("b", "type", kinds=("value_set",)),
        ],
        preconditions=[
            Precondition(
                "edge_exists",
                "a",
                "somebody must have ASSERTED these two are equivalent; reachability is "
                "not an assertion",
                family="equivalent_to",
                object="b",
                namespace="default",
            )
        ],
        effects=[Effect(op="add_edge", family="reconciled_with", namespace="dpr")],
    )
    check("T3.1s2 two `value_set` type refs are legal", isinstance(family, TypeEntry))

    # T3.3 -- THE sharpest result: an action cannot manufacture the transitivity
    # `equivalent_to` refuses. The adjacent pair passes; the two-hop pair does not.
    adjacent = registry.preflight("reconcile_borough", {"a": a, "b": b}, actor="user:sd")
    two_hop = registry.preflight("reconcile_borough", {"a": a, "b": c}, actor="user:sd")
    check(
        "T3.2s  the condition is answered by `neighbors` and by nothing invented",
        adjacent.preconditions[0].evaluated_by == "neighbors" and adjacent.known == 1,
    )
    check(
        "T3.3s  the ADJACENT pair is allowed and the TWO-HOP pair is refused",
        adjacent.verdict == "allowed" and two_hop.verdict == "refused",
        f"adjacent={adjacent.verdict} two_hop={two_hop.verdict}",
    )
    reach = registry.neighbors(a, ["equivalent_to"], 2, namespace="default")
    check(
        "T3.3s2 ...while `neighbors(depth=2)` REACHES it perfectly well -- reachability "
        "is not entailment",
        any(getattr(n, "name", None) == "borough" and n.namespace == "dot" for n in reach.nodes),
        str([f"{n.namespace}:{n.name}" for n in reach.nodes]),
    )

    # T3.4 -- `merge_types` as an effect, refused at each of the three shipped doors.
    breaching = action_attributes(
        reversibility="reversible",
        approval_mode="auto",
        effects=[Effect(op="merge_types")],
    )
    door_one = registry.propose_type(
        "reconcile_by_merge", "the kill row", EVIDENCE, "user:sd",
        kind="action", attributes=breaching,
    )
    door_three = registry.import_types(
        [
            {
                "name": "reconcile_by_import",
                "kind": "action",
                "definition": "the kill row, imported active",
                "status": "active",
                "attributes": breaching,
            }
        ],
        namespace="default",
        kind="action",
    )[0]
    check(
        "T3.4s  `merge_types` as an effect is refused at `propose_type`",
        isinstance(door_one, Refusal) and door_one.reason == "effect_not_permitted",
        f"{door_one!r}",
    )
    check(
        "T3.4s2 ...and at `import_types`, which returns entries and warns instead",
        "import_refused:effect_not_permitted" in door_three.warnings
        and registry.adapter.get_type("default", "reconcile_by_import", kind="action")
        is None,
        str(door_three.warnings),
    )

    # T3.5 -- the shipped `merge_types` still refuses, with both edges present.
    registry.add_edge("reconciled_with", a, b, "derived:catalogue_rule", namespace="dpr")
    plain = registry.merge_types(
        "borough", "borough", "the catalogue says they are the same",
        merged_by="user:sd", namespace="dpr", into_namespace="oti_311",
    )
    acknowledged = registry.merge_types(
        "borough", "borough", "the catalogue says they are the same",
        merged_by="user:sd", namespace="dpr", into_namespace="oti_311",
        acknowledge=["cross_namespace_merge", "definitions_diverge"],
    )
    check(
        "T3.5s  the SHIPPED merge_types still refuses cross_namespace_merge",
        isinstance(plain, Refusal) and plain.reason == "cross_namespace_merge",
        f"{plain!r}",
    )
    check(
        "T3.5s2 ...and refuses AGAIN under two acknowledgements",
        isinstance(acknowledged, Refusal)
        and acknowledged.reason == "cross_namespace_merge",
        f"{acknowledged!r}",
    )

    # T3.6 -- `created_by` is DERIVED, and a deterministic rule lands `derived` (R17).
    invocation = registry.record_invocation(
        "reconcile_borough",
        {"a": a, "b": b},
        actor="derived:catalogue_rule",
        outcome="applied",
        gate_verdict="allowed",
        approved_by=adjacent.approved_by,
        judged=adjacent,
        source_version="uvpi-gqnh@2017-10-04 / erm2-nwe9@2026-08-28",
    )
    check(
        "T3.6s  `created_by` is DERIVED from the actor and lands `derived` -- R17",
        invocation.provenance.created_by == "derived",
        invocation.provenance.created_by,
    )
    check(
        "T3.7s  `source_version` carries both dataset versions -- a nine-year gap",
        invocation.provenance.source_version
        == "uvpi-gqnh@2017-10-04 / erm2-nwe9@2026-08-28",
    )
    check(
        "T3.8s  the invocation's namespace is the FAMILY's; the inputs keep their own",
        invocation.namespace == "default",
        invocation.namespace,
    )


# ------------------------------------------------------- the machinery no fixture walks


def _governance(check) -> None:
    """The machinery no fixture walks, through the shipped registry.

    Round 1 and round 2 both found their sharpest defects here rather than in the three
    use cases, which is why the spec row added a fourth probe at all.
    """
    registry = _registry()

    # The bare entry: legal to register, refused to USE. Both halves of rule 2.2-1.
    bare = _seed(registry, "half_declared", kind="action")
    check("G1s    a bare kind='action' entry is a legal TypeEntry", isinstance(bare, TypeEntry))
    gate = registry.preflight("half_declared", {}, actor="user:sd")
    check(
        "G2s    ...and `preflight` refuses on it -- the hole closed at the other end",
        isinstance(gate, Refusal) and gate.reason == "attributes_schema_violation",
        f"{gate!r}",
    )

    # A family that declares LESS is not a family that escapes the rules (round 2).
    less = registry.propose_type(
        "declares_less",
        "an entry declaring merge_types as an effect and nothing else",
        EVIDENCE,
        "user:sd",
        kind="action",
        attributes={"effects": [Effect(op="merge_types").to_dict()]},
    )
    check(
        "G3s    declaring LESS does not bypass the effect rule -- round 2's own hole",
        isinstance(less, Refusal) and less.reason == "effect_not_permitted",
        f"{less!r}",
    )

    # The unknown family, and the empty Preflight that would have been mechanism C.
    typo = registry.preflight("flag_facilty_for_review", {}, actor="user:sd")
    check(
        "G4s    a typo'd family REFUSES rather than answering an empty Preflight",
        isinstance(typo, Refusal) and typo.reason == "action_family_unknown",
        f"{typo!r}",
    )

    # `preflight` records nothing, N times.
    _family(registry, "search_tasks", reversibility="reversible", approval_mode="auto")
    for _ in range(10):
        registry.preflight("search_tasks", {}, actor="user:sd")
    check(
        "G5s    `preflight` records NOTHING -- ten calls, an empty ledger",
        registry.invocations().known == 0,
        str(registry.invocations().known),
    )
