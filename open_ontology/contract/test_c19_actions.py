"""C19 -- governed actions. `ACTIONS.md` v0, roadmap row 6b.

Three things shape this group, and each is something the spec row already paid for.

**Every numbered rule of `ACTIONS.md` is mapped to an id here, one by one** (ruling
**R31**, standing constraint 8). The spec row planned **58** ids and **4** `prose-only:`
tags across eight sections, and §14 says exactly why it did not point
`check_spec_drift.py` at the document: *"pointing it at this document today would fail
fifty-eight times... the extension lands in the build row, in the same change that lands
the tests, which is the only order in which the gate is ever telling the truth."* This
file is that change.

**Every BLOCKING finding of the spec row's three adversarial rounds is an assertion
here.** That loop found fifteen, reached ROADMAP.md's kill row **five** times, and every
one of the five was CONSTRUCTED rather than read. They were fixed in a throwaway probe
kit under `docs/tools/`, which the package does not import and the suite does not know
about -- so until this file they were fixed nowhere a backend author could be held to.
§14 names that as row 4b's own recorded lesson and asks for exactly this transposition.

**The declaration rules bind at THREE doors and this file asks all three.** Rule 2.2-4
exists because a reviewer imported an *active* `kind="action"` family declaring
`merge_types` as an effect through the shipped `import_types` with no warning at all,
while the same call refused a breaching *edge* family correctly. `propose_type`,
`approve` and `import_types` -- *a rule with one enforcement point is a rule with one
door left open*.

**Why so many of these need `stores_attributes`, which is a finding rather than a
fixture detail**, and it is EDGES.md's one row along: ACTIONS.md 2.2 puts a family's
eight declared keys in `TypeEntry.attributes`, so **a backend that stores no arbitrary
attributes cannot DECLARE an action family at all**. The escape hatch is the one
PACKAGE.md 5.7 already built -- name the eight in `attribute_projections` -- and it is
skipped with a reason here rather than hidden.
"""

from __future__ import annotations

import pytest

from ..actions import (
    APPROVAL_MODES,
    EFFECT_OPS,
    EVALUATORS,
    GATE_VERDICTS,
    GOVERNANCE_CALLS,
    OUTCOMES,
    PRECONDITION_KINDS,
    PROPOSABLE_KINDS,
    REVERSIBILITY,
    ActionFamily,
    Effect,
    InputSpec,
    Precondition,
    ProjectionReport,
    action_attributes,
    effect_identity,
)
from ..adapter import ACTION_CAPABILITY_FLAGS, CAPABILITY_FLAGS, Capabilities
from ..edges import InstanceRef, TypeRef
from ..errors import NotSupported, UnknownType
from ..policy import TierOrder
from ..types import Evidence, Proposal, Refusal, TypeEntry
from ._support import action_family, edge_family, seed
from .doubles import DegradedAdapter

EVIDENCE = [Evidence(kind="data", summary="the C19 fixture")]

#: ACTIONS.md 2.2 puts the eight declared keys in `TypeEntry.attributes`.
NEEDS_ATTRIBUTES = pytest.mark.requires_capability("stores_attributes")

#: ...and 6.2/6.3 need the store 8's first flag declares.
NEEDS_INVOCATIONS = pytest.mark.requires_capability(
    "stores_attributes", "stores_invocations"
)

NO_EDGES = {
    "stores_edges": "this backend is a type registry only; no table holds relationships"
}
NO_INVOCATIONS = {
    "stores_invocations": "this backend is a type registry only; no table holds invocations"
}


def _propose(registry, name, attributes, *, kind="action", namespace="default"):
    """The FIRST door. Returns whatever `propose_type` returned -- a `Refusal` when a
    declaration rule bit, a `Proposal` or `TypeEntry` when it did not."""
    return registry.propose_type(
        name,
        f"the {name} action, for the purposes of this test",
        EVIDENCE,
        "user:sd",
        kind=kind,
        namespace=namespace,
        attributes=attributes,
    )


def _import(registry, name, attributes, *, kind="action", namespace="default"):
    """The THIRD door. `import_types` returns entries and cannot return a `Refusal`, so
    a breach comes back as `import_refused:<reason>` with nothing written."""
    return registry.import_types(
        [
            {
                "name": name,
                "kind": kind,
                "definition": f"the {name} action, imported",
                "status": "active",
                "attributes": attributes,
            }
        ],
        namespace=namespace,
        kind=kind,
    )[0]


def _refused_at_every_door(registry, name, attributes, reason):
    """Rule 2.2-4, as one assertion. Every declaration rule binds at all three doors."""
    first = _propose(registry, f"{name}_a", attributes)
    assert isinstance(first, Refusal), f"propose_type wrote {first!r}"
    assert first.reason == reason, first
    assert first.detail.get("why", "").strip(), "a refusal a caller can act on"

    entry = _import(registry, f"{name}_c", attributes)
    assert f"import_refused:{reason}" in entry.warnings, entry.warnings
    return first


# ------------------------------------------------------------------- 2.2 the shape


@NEEDS_ATTRIBUTES
def test_c19_26_a_bare_kind_action_entry_is_legal_and_is_not_refused(adapter, make_registry):
    """Rule **2.2-1**. A `kind="action"` entry declaring none of the eight keys is a
    legal `TypeEntry` and is NOT refused.

    It is simply not yet usable as an action family. Refusing the *registration* would
    reject entries INTERFACE.md 2.1 says are legal -- `edges.family_declaration_problem`'s
    own recorded decision for the identical case one kind along, which **round 1 found
    ACTIONS.md silently taking the opposite position on**. The hole that opens (declare
    nothing, then invoke anything) is closed at the other end, in `preflight`.

    `kind` is an OPEN vocabulary (INTERFACE.md 2.1) and `C16-05` deliberately does not
    check it, so adding `action` as a fifth kind costs no amendment and trips no gate --
    §2.1 makes its argument on the shape of the thing rather than on the absence of one.
    """
    registry = make_registry(adapter)
    entry = seed(registry, "search_tasks", kind="action")
    assert entry.kind == "action"
    assert entry.status == "active"

    # And with the eight keys present but empty -- which is what a host that has not
    # decided yet writes. Still legal, still not a declared family.
    entry = seed(registry, "list_tasks", kind="action", attributes=action_attributes())
    family = ActionFamily.from_attributes(
        entry.name, entry.namespace, dict(entry.attributes or {}), entry.status
    )
    assert not family.declared


@NEEDS_ATTRIBUTES
def test_c19_27_a_partial_declaration_must_declare_both_required_keys_from_closed_sets(
    adapter, make_registry
):
    """Rule **2.2-2**. A family declaring SOME of the eight must declare `reversibility`
    and `approval_mode`, and each must be a value of its closed vocabulary.

    A fourth `approval_mode` or a fifth `reversibility` is `attributes_schema_violation`,
    **never a bare exception** -- which is where three of these rules bound before round
    2 found them raising `ValueError` in `__post_init__`, firing before any door was
    reached, carrying no `door`, returning no `Refusal`, and unable to produce
    `import_refused` on the `import_types` path.

    **And "declaring some" means ANY of the eight, not the two required ones.** Round 2
    reached the kill row through the first version of this test: it returned early on
    the two required keys alone, so an entry declaring `merge_types` as an effect and
    nothing else was written at all three doors -- rule 2.5-5 bypassed by declaring LESS.
    """
    registry = make_registry(adapter)

    # `reachability` alone makes this a declaration, and the two required keys are then
    # required. This is the round-2 hole, asserted.
    _refused_at_every_door(
        registry,
        "reach_only",
        {"reachability": ["task_detail"]},
        "attributes_schema_violation",
    )

    for key, bad in (("reversibility", "undoable"), ("approval_mode", "quorum")):
        attributes = action_attributes(reversibility="reversible", approval_mode="auto")
        attributes[key] = bad
        refusal = _refused_at_every_door(
            registry, f"bad_{key}", attributes, "attributes_schema_violation"
        )
        assert refusal.detail["field"] == key
        assert refusal.detail["got"] == bad

    # Missing entirely is the same refusal: there is no default, because a family that
    # does not say is a family whose gate cannot be set.
    for key in ("reversibility", "approval_mode"):
        attributes = action_attributes(reversibility="reversible", approval_mode="auto")
        attributes[key] = None
        _refused_at_every_door(
            registry, f"missing_{key}", attributes, "attributes_schema_violation"
        )

    assert REVERSIBILITY == ("reversible", "compensable", "irreversible")
    assert APPROVAL_MODES == ("auto", "review", "human")


@NEEDS_ATTRIBUTES
def test_c19_28_irreversible_forces_human_and_returns_r18s_own_refusal_value(
    adapter, make_registry
):
    """Rule **2.2-3** -- THE one cross-field rule, in ruling **R18**'s shape.

    A family declaring that it cannot be undone *and* that a model may run it unattended
    has written the failure mode this project exists to prevent into its own
    configuration. Refused at declaration with **`attributes_schema_violation`**, which
    is R18's own value.

    **The first draft minted `human_approval_required` for it**, which would have made
    two instances of one ruling return two different reasons. PACKAGE.md 5.6 records R18
    as an exception list *inside the attribute-schema mechanism*, and the shipped
    `edges.family_declaration_problem` returns `attributes_schema_violation` for exactly
    this shape -- so the list goes to length two, one rule per kind, which is the shape
    R18 licensed. `human_approval_required` survives for the INVOCATION door only.
    """
    registry = make_registry(adapter)
    for mode in ("auto", "review"):
        refusal = _refused_at_every_door(
            registry,
            f"delete_person_{mode}",
            action_attributes(reversibility="irreversible", approval_mode=mode),
            "attributes_schema_violation",
        )
        assert refusal.detail["reversibility"] == "irreversible"
        assert refusal.detail["approval_mode"] == mode

    # NARROWED, not banned: irreversible + human is the whole point of the rule, and a
    # guard that refuses everything passes a checker that only tests refusals.
    entry = action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )
    assert isinstance(entry, TypeEntry)
    assert entry.attributes["approval_mode"] == "human"


@NEEDS_ATTRIBUTES
def test_c19_44_every_declaration_rule_binds_at_all_three_doors(adapter, make_registry):
    """Rule **2.2-4**. `propose_type`, `approve` AND `import_types`.

    *A rule with one enforcement point is a rule with one door left open* -- the shipped
    `_edge_family_refusal`'s own docstring, and the thing on the other side of this one
    is the ROADMAP.md kill row wearing a verb.

    **The third door is the one round 1 walked through.** ACTIONS.md said *"at
    declaration"* eleven times and named no call site; a reviewer imported an **active**
    `kind="action"` family declaring `merge_types` as an effect *and* breaching 2.2's
    cross-field rule, through the shipped registry, with **no warning at all** -- while
    the same call refused a breaching edge family correctly.

    The SECOND door is asked with a proposal that predates the rule, which is R18's own
    reason for naming `approve()`: a pending proposal written before a rule landed must
    meet it on the way in, and `approve(definition=..., predicates=...)` is the one call
    that amends one.
    """
    from ..adapter import ProposalRecord

    registry = make_registry(adapter)
    if not registry.caps.stores_proposals:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_proposals=False, so there is "
            "no pending proposal for the `approve` door to be asked about. The other two "
            "doors are asserted by C19-27, C19-28, C19-07 and C19-48 on every leg."
        )

    breaching = action_attributes(reversibility="irreversible", approval_mode="auto")
    _refused_at_every_door(registry, "predates", breaching, "attributes_schema_violation")

    # The `approve` door, with a proposal whose stored attributes breach the rule --
    # exactly what a proposal written before the rule landed looks like.
    proposal = _propose(
        registry,
        "predates_rule",
        action_attributes(reversibility="reversible", approval_mode="auto"),
    )
    assert isinstance(proposal, Proposal), proposal
    record = registry.adapter.get_proposal(proposal.id)
    registry.adapter.put_proposal(
        ProposalRecord(**{**record.__dict__, "attributes": breaching})
    )
    out = registry.approve(proposal.id, "user:sd")
    assert isinstance(out, Refusal), f"the approve door wrote {out!r}"
    assert out.reason == "attributes_schema_violation"

    # And the entry is not there: a refused declaration writes nothing at any door.
    assert registry.adapter.get_type("default", "predates_a", kind="action") is None
    assert registry.adapter.get_type("default", "predates_c", kind="action") is None


# ------------------------------------------------------------ 2.4 the preconditions


@NEEDS_ATTRIBUTES
def test_c19_01_the_precondition_vocabulary_is_closed_at_four(adapter, make_registry):
    """Rule **2.4-1**. A family declaring a fifth kind is refused at declaration.

    The rule this section is built on: *a precondition is a question the registry can
    already answer with a call it already has.* There are four kinds, there is no fifth,
    and *"anything else"* is not a precondition in v0 -- it is the action's own code, and
    the registry does not pretend to know it.

    UC2's own action wants a FIFTH -- *"this facility has a citation whose Scope
    Severity Code is in {J, K, L}"* -- and does not get one. That is contortion **ACT4**,
    the third surface reaching for one missing mechanism, routed to Phase 3 by rulings
    **R22**/**R41**/**R60** rather than taken here. Rule 2.4-9 is `prose-only:` for it.
    """
    registry = make_registry(adapter)
    assert PRECONDITION_KINDS == (
        "type_active",
        "predicate_holds",
        "edge_exists",
        "edge_absent",
    )
    refusal = _refused_at_every_door(
        registry,
        "flag_facility",
        action_attributes(
            reversibility="reversible",
            approval_mode="auto",
            inputs=[InputSpec("facility", "instance")],
            preconditions=[
                Precondition(
                    kind="value_in_set",
                    subject="facility",
                    why="Immediate Jeopardy only",
                )
            ],
        ),
        "attributes_schema_violation",
    )
    assert refusal.detail["got"] == "value_in_set"
    assert refusal.detail["field"] == "preconditions"


@NEEDS_ATTRIBUTES
def test_c19_03_a_precondition_why_is_required_and_non_empty(adapter, make_registry):
    """Rule **2.4-3**, on PACKAGE.md 5.2's reasoning for `FieldSpec.description` and
    INTERFACE.md 2.1's for a non-empty `definition`.

    An undescribed condition is how an escape hatch re-forms one level down. **A
    precondition nobody can read is a precondition nobody will ever delete when it stops
    being true.**
    """
    registry = make_registry(adapter)
    for empty in ("", "   "):
        _refused_at_every_door(
            registry,
            f"blank_why_{len(empty)}",
            action_attributes(
                reversibility="reversible",
                approval_mode="auto",
                inputs=[InputSpec("a", "type")],
                preconditions=[Precondition("type_active", "a", empty)],
            ),
            "attributes_schema_violation",
        )

    # Narrowed, not banned.
    entry = action_family(
        registry,
        "with_why",
        inputs=[InputSpec("a", "type")],
        preconditions=[Precondition("type_active", "a", "the word must still be live")],
    )
    assert entry.attributes["preconditions"][0]["why"]


@NEEDS_ATTRIBUTES
def test_c19_45_a_precondition_naming_no_input_is_refused_at_declaration(
    adapter, make_registry
):
    """Rule **2.4-6**. *The precondition door is shut where the effect door is.*

    A `subject` or `object` naming neither an `InputSpec` nor a literal identity ref, a
    `predicate_holds` with no `predicate`, an edge condition with no `family`: each is a
    DECLARATION error, not a runtime unknown indistinguishable from a degraded backend.
    Found by round 1, which noticed that the effect door was shut and this one was not.
    """
    registry = make_registry(adapter)
    base = dict(reversibility="reversible", approval_mode="auto", inputs=[InputSpec("a", "type")])

    cases = {
        "no_such_subject": Precondition("type_active", "nobody", "protects nothing"),
        "no_predicate": Precondition("predicate_holds", "a", "must be searchable"),
        "no_family": Precondition("edge_exists", "a", "must be linked", object="a"),
        "no_object": Precondition("edge_exists", "a", "must be linked", family="blocks"),
        "bad_object": Precondition(
            "edge_absent", "a", "must not be linked", family="blocks", object="ghost"
        ),
    }
    for label, condition in cases.items():
        _refused_at_every_door(
            registry,
            label,
            action_attributes(preconditions=[condition], **base),
            "attributes_schema_violation",
        )

    # A LITERAL identity ref is legal and is recognisable by its triple -- 2.4's own
    # words, *"the InputSpec.name this is about, OR a literal ref"*.
    entry = action_family(
        registry,
        "literal_subject",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition(
                "type_active",
                "cms:value_set:scope_severity_code",
                "the scale must still be in the vocabulary",
            )
        ],
    )
    assert isinstance(entry, TypeEntry)


# ----------------------------------------------------------------- 2.5 the effects


@NEEDS_ATTRIBUTES
def test_c19_06_the_effect_vocabulary_is_closed_at_four_operations(adapter, make_registry):
    """Rule **2.5-1**. A fifth operation is refused at declaration with
    `effect_not_permitted`.

    `attributes_schema_violation` is about a schema's field TYPES; this is a rule about
    the vocabulary of one field's VALUES, and §7 argues the difference: nothing in the
    twenty-one said *"you may not declare that"*.
    """
    registry = make_registry(adapter)
    assert EFFECT_OPS == ("add_edge", "retract_edge", "propose_type", "host_state")
    refusal = _refused_at_every_door(
        registry,
        "fifth_op",
        action_attributes(
            reversibility="reversible",
            approval_mode="auto",
            effects=[Effect(op="delete_row")],
        ),
        "effect_not_permitted",
    )
    assert refusal.detail["op"] == "delete_row"
    assert set(refusal.detail["operations"]) == set(EFFECT_OPS)


@NEEDS_ATTRIBUTES
def test_c19_07_the_six_governance_calls_may_never_be_an_effect(adapter, make_registry):
    """Rule **2.5-2**, and it is ROADMAP.md's kill row arriving through a door no
    previous row had.

    `approve` · `reject` · `retire` · `reinstate` · `merge_types` · `register_consumer`.
    A GENERAL rule, not a family's opt-in: an action that can `approve` closes the
    proposal->approval loop with no human in it -- mechanism **1** restored through the
    very layer this document adds. **An action that can `merge_types` is the kill row
    wearing a verb.** An action that can `register_consumer` can make itself look gated.

    Refused at DECLARATION, so the action never exists rather than being refused when it
    runs -- EDGES.md 2.4.1 spent a whole adversarial round learning that a rule checked
    only at write time is a rule a family author opts out of by declaring something
    permissive.
    """
    registry = make_registry(adapter)
    assert set(GOVERNANCE_CALLS) == {
        "approve",
        "reject",
        "retire",
        "reinstate",
        "merge_types",
        "register_consumer",
    }
    for call in GOVERNANCE_CALLS:
        refusal = _refused_at_every_door(
            registry,
            f"gov_{call}",
            action_attributes(
                reversibility="reversible",
                approval_mode="auto",
                effects=[Effect(op=call, namespace="default", kind="entity")],
            ),
            "effect_not_permitted",
        )
        assert refusal.detail["op"] == call
        assert registry.adapter.get_type("default", f"gov_{call}_a", kind="action") is None
        assert registry.adapter.get_type("default", f"gov_{call}_c", kind="action") is None


@NEEDS_ATTRIBUTES
def test_c19_08_an_action_may_propose_and_only_a_human_or_a_policy_may_approve(
    adapter, make_registry
):
    """Rule **2.5-3**. `propose_type` IS in the vocabulary, precisely so the line has a
    legal side.

    *An action may PROPOSE; only a human, or an auto-policy a deployment set
    deliberately, may APPROVE.* An ingestion action meeting a new word may say so, and
    what it says is a request -- which is the whole proposal->approval loop applied one
    level up.
    """
    registry = make_registry(adapter)
    entry = action_family(
        registry,
        "ingest_dataset",
        effects=[Effect(op="propose_type", namespace="dpr", kind="entity")],
    )
    assert isinstance(entry, TypeEntry)
    family = ActionFamily.from_attributes(
        entry.name, entry.namespace, dict(entry.attributes or {}), entry.status
    )
    assert family.effects[0].op == "propose_type"
    assert family.effects[0].kind == "entity"


@NEEDS_ATTRIBUTES
def test_c19_09_a_host_state_effect_requires_a_non_empty_why(adapter, make_registry):
    """Rule **2.5-4**. The fourth operation is an ADMISSION rather than a capability.

    `host_state` means *this action changes something this protocol does not model*, and
    it carries a mandatory sentence saying what. It exists because the alternative is
    worse: a family that mutates the host's database and declares `effects: []` is
    claiming a blast radius of zero, and **an empty list standing in for "we did not
    look" is what Rule U forbids by name.**

    **[Observed]** `delete_person` in beacon deletes one row and fifteen foreign keys
    reference `people.id`; three edge families are declarable and **eleven FKs are
    expressible only as `host_state`**. UC1 would be *served* by a `host_state` that
    needs no sentence, and the rule requires it anyway -- CMS's rule beating UC1's
    convenience, per the rule of the ordering.
    """
    registry = make_registry(adapter)
    for empty in ("", "  "):
        _refused_at_every_door(
            registry,
            f"silent_host_state_{len(empty)}",
            action_attributes(
                reversibility="irreversible",
                approval_mode="human",
                effects=[Effect(op="host_state", why=empty)],
            ),
            "effect_not_permitted",
        )

    entry = action_family(
        registry,
        "delete_person",
        reversibility="irreversible",
        approval_mode="human",
        effects=[
            Effect(op="host_state", why="cascades 11 foreign keys on people.id"),
            Effect(
                op="host_state",
                why="connection_service.unlink COMMITS before the delete",
            ),
        ],
    )
    assert len(entry.attributes["effects"]) == 2


@NEEDS_ATTRIBUTES
def test_c19_10_the_effect_exclusion_binds_at_declaration_not_only_at_invocation(
    adapter, make_registry
):
    """Rule **2.5-5**. **The door is the declaration.**

    EDGES.md 2.4.1 spent a whole adversarial round learning that a rule checked only at
    write time is a rule a family author opts out of by declaring something permissive,
    and the lesson transfers without modification. A family declaring one of the six is
    refused before it exists -- there is no approved `reconcile_borough` sitting in the
    registry waiting for somebody to notice its `merge_types` effect.

    Asserted as an absence AND as a presence: nothing is written at any door, and the
    same family with the effect removed declares cleanly.
    """
    registry = make_registry(adapter)
    breaching = action_attributes(
        reversibility="reversible",
        approval_mode="auto",
        effects=[Effect(op="merge_types")],
    )
    _refused_at_every_door(registry, "reconcile_borough", breaching, "effect_not_permitted")
    listing = registry.list_types(kind="action", include_retired=True)
    assert not [e for e in listing.types if e.name.startswith("reconcile_borough")]

    clean = action_family(registry, "reconcile_borough", effects=[])
    assert isinstance(clean, TypeEntry)


@NEEDS_ATTRIBUTES
def test_c19_12_an_effect_naming_an_unregistered_edge_family_is_refused(
    adapter, make_registry
):
    """Rule **2.5-7**. `edge_family_unknown` -- EDGES.md 4.3's EXISTING value, not a new
    one.

    An effect that may `add_edge` on a family nobody registered has declared a blast
    radius the registry cannot check against anything, which is the same failure
    `edge_family_unknown` already names one layer down. Minting a second value for it
    would be INTERFACE.md 2.3's Cause B.

    This is the one declaration rule that is not pure -- it needs the store -- so it
    lives on `Registry` rather than in `actions.family_declaration_problem`, and it is
    asserted at the doors like every other.
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_edges:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_edges=False. The REFUSAL "
            "half is asserted on every leg below; the narrowing half needs a registered "
            "`kind=\"edge\"` family, which needs the edge store this backend declines."
        )
    attributes = action_attributes(
        reversibility="reversible",
        approval_mode="auto",
        effects=[Effect(op="add_edge", family="flagged_for_review", namespace="default")],
    )
    refusal = _refused_at_every_door(
        registry, "flag_facility", attributes, "edge_family_unknown"
    )
    assert refusal.detail["family"] == "flagged_for_review"

    # Register the family, and the identical declaration is accepted. The guard is
    # narrowed, not banned -- refusing everything passes a checker that tests refusals.
    edge_family(registry, "flagged_for_review", level="instance")
    entry = action_family(
        registry,
        "flag_facility_ok",
        effects=[Effect(op="add_edge", family="flagged_for_review", namespace="default")],
    )
    assert isinstance(entry, TypeEntry)


@NEEDS_ATTRIBUTES
def test_c19_48_a_propose_type_effect_must_name_a_kind_from_an_allowlist(
    adapter, make_registry
):
    """Rule **2.5-8**, and it is the kill row's SECOND trip in this document's loop.

    Round 1 closed a `propose_type` effect naming `kind="predicate"`. **Round 2 walked
    past the fix by OMITTING the key** -- the round-1 rule tested `kind == "predicate"`
    and `Effect.kind` is `str | None` -- and walked past it a second way with
    `kind="action"`, which mints a live **verb** unattended, the case 15.1 ranks above
    the noun. A blocklist was the wrong shape.

    **Why `predicate` is excluded at all, and it is not belt-and-braces.** A predicate's
    extent is a set of TYPES and a freshly minted one is EMPTY -- so it is byte-identical
    to any other empty extent, and INTERFACE.md 5.10's refusal #2 does **not** fire on
    it. A reviewer minted two predicates through an action on an auto-approving namespace
    (**[Observed]**, UC1's own configuration) and then merged them, against the shipped
    `Registry`. `C10-09` pins the guard downstream; this pins the door upstream.
    """
    registry = make_registry(adapter)
    assert PROPOSABLE_KINDS == ("entity", "edge", "value_set")

    for label, effect in (
        ("predicate", Effect(op="propose_type", namespace="default", kind="predicate")),
        ("omitted", Effect(op="propose_type", namespace="default")),
        ("verb", Effect(op="propose_type", namespace="default", kind="action")),
        ("no_namespace", Effect(op="propose_type", kind="entity")),
    ):
        refusal = _refused_at_every_door(
            registry,
            f"mint_{label}",
            action_attributes(
                reversibility="reversible", approval_mode="auto", effects=[effect]
            ),
            "effect_not_permitted",
        )
        assert refusal.detail["op"] == "propose_type"

    for kind in PROPOSABLE_KINDS:
        entry = action_family(
            registry,
            f"propose_{kind}",
            effects=[Effect(op="propose_type", namespace="default", kind=kind)],
        )
        assert isinstance(entry, TypeEntry), kind


def test_c19_49_effect_identity_excludes_why_except_for_host_state(adapter, make_registry):
    """Rule **2.5-9**. Two effects are the same effect when `(op, namespace, family,
    kind)` match, and `why` is NOT part of identity -- so amending a sentence does not
    turn one declared effect into two.

    **`host_state` has no target at all, so its `why` IS its identity**, which means two
    admissions differing by a full stop are two effects. That cost is stated rather than
    hidden: contortion **ACT9**, measured by round 2 at ~2 of 5 effects on UC1's
    `delete_person` and ~9 of 10 at ingest, and ruled **R46** -- a slug field would be a
    sixth key on `Effect` for a case one fixture has.

    A pure function over the shapes, so it needs no backend and asserts on every leg.
    Round 1 found `effect_undeclared:host_state:None:None` being printed against a spec
    whose `<op>:<target>` format had no reading for an op with no target.
    """
    add = Effect(op="add_edge", family="blocks", namespace="default")
    assert effect_identity(add) == effect_identity(
        Effect(op="add_edge", family="blocks", namespace="default", why="a sentence")
    )
    assert effect_identity(add) != effect_identity(
        Effect(op="add_edge", family="blocks", namespace="dpr")
    )

    here = Effect(op="host_state", why="cascades 11 foreign keys")
    there = Effect(op="host_state", why="cascades 11 foreign keys.")
    assert effect_identity(here) != effect_identity(there), "ACT9, stated rather than fixed"
    assert effect_identity(here) == effect_identity(
        Effect(op="host_state", why="cascades 11 foreign keys")
    )

    # An input-determined namespace keeps its own identity (rule 2.5-10): it DECLARES
    # *the namespace comes from this invocation's inputs* rather than omitting one.
    assert effect_identity(Effect(op="add_edge", family="cites")) == (
        "add_edge",
        None,
        "cites",
        None,
    )


# --------------------------------------------------------------------- 5.2 the gate


@NEEDS_ATTRIBUTES
def test_c19_13_approval_mode_is_closed_at_three_values(adapter, make_registry):
    """Rule **5.2-1**. A family declaring a fourth is refused at declaration.

    A fourth value -- a two-person rule, a quorum -- is a policy language arriving one
    value at a time, and 15.2 records the recommendation: make `approved_by` a list
    before making the mode vocabulary bigger. Not taken; no fixture needs it.
    """
    registry = make_registry(adapter)
    refusal = _refused_at_every_door(
        registry,
        "two_person",
        action_attributes(reversibility="reversible", approval_mode="two_person"),
        "attributes_schema_violation",
    )
    assert refusal.detail["field"] == "approval_mode"
    for mode in APPROVAL_MODES:
        entry = action_family(registry, f"mode_{mode}", approval_mode=mode)
        assert entry.attributes["approval_mode"] == mode


# ------------------------------------------------------------------- 10 reachability


@NEEDS_ATTRIBUTES
def test_c19_19_reachability_values_are_opaque_strings_the_registry_never_interprets(
    adapter, make_registry
):
    """Rule **10-1**. INTERFACE.md 2.7's posture for `model_tier`, and for the same
    reason: *the registry does not know what a surface is.*

    **[Observed]** beacon's `ActionSpec.category` is exactly this field, already present,
    already validated against a closed list, and already the unit its selector drops.
    The registry validates that each value is a non-empty string and nothing else -- a
    closed list here would be beacon's routing table living in the registry.

    **An EMPTY list is a positive declaration** -- *this host exposes me on no named
    surface* -- not a forgotten field, and §10.6 is honest that this is the field 2.2
    makes required on every family for the section its own customer deletes. Round 2's
    ingestion lens declared four families with `reachability=()` and got `counts={}`;
    that is the correct answer and it stays required because Rule U's standard applies
    to §10's own field.
    """
    registry = make_registry(adapter)
    entry = action_family(
        registry, "cross_agency", reachability=["catalogue_console", "任意のサーフェス"]
    )
    assert entry.attributes["reachability"] == ["catalogue_console", "任意のサーフェス"]

    silent = action_family(registry, "ingest_dataset", reachability=[])
    assert silent.attributes["reachability"] == []

    for bad in ([""], ["  "], [None], [7]):
        _refused_at_every_door(
            registry,
            f"bad_reach_{len(str(bad))}",
            action_attributes(
                reversibility="reversible", approval_mode="auto", reachability=bad
            ),
            "attributes_schema_violation",
        )


@NEEDS_ATTRIBUTES
def test_c19_02_each_precondition_kind_is_answered_by_a_call_that_already_exists(
    adapter, make_registry
):
    """Rule **2.4-2**, and it is 2.4's no-query-language claim made MECHANICAL.

    ``PreconditionResult.evaluated_by`` names the existing call that produced the answer,
    from a closed set of three -- ``list_types`` / ``predicates`` / ``neighbors`` -- so a
    reviewer can confirm that nothing evaluated a condition by some fifth route.
    **[Inferred]** this is the field a later reader will use to notice that a query
    language grew.

    And the claim it makes about the surface is asserted too: **this document adds no
    call to `INTERFACE.md` §5.** `resolve_type` is deliberately NOT an evaluator -- it
    needs a `tier` and a column-shaped `ResolveContext` that `preflight` has neither of
    (contortions ACT2 and ACT6).
    """
    registry = make_registry(adapter)
    seed(registry, "facility", kind="entity")
    seed(registry, "commentable", kind="predicate")
    if registry.caps.stores_edges:
        edge_family(registry, "cites", level="instance")
    facility = TypeRef("default", "entity", "facility")

    expected = {
        "type_active": "list_types",
        "predicate_holds": "predicates",
        "edge_exists": "neighbors",
        "edge_absent": "neighbors",
    }
    for kind, call in expected.items():
        condition = Precondition(
            kind,
            "a",
            "the checker's fixture",
            predicate="commentable" if kind == "predicate_holds" else None,
            family="cites" if kind.startswith("edge_") else None,
            object="b" if kind.startswith("edge_") else None,
        )
        action_family(
            registry,
            f"eval_{kind}",
            inputs=[InputSpec("a", "type"), InputSpec("b", "type", required=False)],
            preconditions=[condition],
        )
        out = registry.preflight(
            f"eval_{kind}", {"a": facility, "b": facility}, actor="user:sd"
        )
        assert not isinstance(out, Refusal), out
        assert out.preconditions[0].evaluated_by == call, kind
        assert out.preconditions[0].evaluated_by in EVALUATORS

    assert "resolve_type" not in EVALUATORS, (
        "ACT2/ACT6 -- resolve_type needs a tier and a column-shaped context preflight "
        "does not have"
    )


@pytest.mark.requires_capability("stores_attributes", "indexes_membership")
def test_c19_04_a_precondition_that_does_not_hold_names_the_failing_condition(
    adapter, make_registry
):
    """Rule **2.4-4**. ``Refusal(reason="precondition_unmet")`` naming the failing
    condition's ``subject`` and ``kind`` in ``detail`` -- **never a bare `False`**.

    ``precondition_unmet`` is the first value in INTERFACE.md 5.12's vocabulary that is
    about a *runtime state of the world* rather than about the vocabulary: the fourteen
    policy refusals are about words, and this one is about data.

    **`indexes_membership` is scaffolding here, not the subject.** On a backend that
    cannot compute an extent, a `predicate_holds` miss is honestly **unknown** rather
    than false -- which is C19-05's and C19-36's subject, and is the FIRST kill-row
    trip's own lesson applied at this surface. This test needs a condition that is
    definitively FALSE, and only a backend that can answer the membership question can
    produce one.
    """
    registry = make_registry(adapter)
    seed(registry, "facility", kind="entity")
    seed(registry, "commentable", kind="predicate")
    facility = TypeRef("default", "entity", "facility")
    action_family(
        registry,
        "needs_commentable",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition("predicate_holds", "a", "only commentable things", predicate="commentable")
        ],
    )
    out = registry.preflight("needs_commentable", {"a": facility}, actor="user:sd")
    assert out.verdict == "refused"
    assert out.refusal.reason == "precondition_unmet"
    # One value, TWO states, and the states are in `detail` rather than in two words --
    # `endpoint_kind_mismatch`'s own precedent. `state` was added by round 1, without
    # which a caller cannot tell a real miss from a backend that could not look.
    assert out.refusal.detail["state"] == "false"
    assert out.refusal.detail["kind"] == "predicate_holds"
    assert out.refusal.detail["subject"] == "a"
    assert out.preconditions[0].holds is False


def test_c19_05_an_unknown_precondition_is_none_plus_a_why_and_is_never_satisfied(
    adapter, make_registry
):
    """Rule **2.4-5**. A precondition the backend cannot answer is ``None`` plus a
    ``why``, and ``preflight`` **refuses** rather than treating unknown as satisfied.

    Treating unknown as *satisfied* would let a degraded backend approve everything;
    treating it as *unsatisfied* would be a confident ``False`` the registry did not
    earn. So the condition carries ``None`` plus the adapter's own sentence, ``complete``
    goes ``False``, and the verdict is refused with ``detail["state"] == "unknown"``.

    **This test's SUBJECT is the declined capability**, so it does not skip on a backend
    that declines one: PACKAGE.md 6.1 rule 1, unchanged. It runs on all three legs, and
    on `sqlite_minimal` it runs against a store whose `oo_edge` is absent from the SQL
    rather than hidden behind a Python `if`.
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_attributes:
        pytest.skip(
            "ACTIONS.md 2.2 puts the eight declared keys in `TypeEntry.attributes`, so a "
            "backend that stores no arbitrary attributes cannot DECLARE a family at all "
            "-- the escape hatch is PACKAGE.md 5.7's `attribute_projections`, and this "
            "leg names one key rather than eight. C19-39 asserts the invocation-store "
            "half of Rule U on this leg without needing a declaration."
        )
    seed(registry, "facility", kind="entity")
    facility = InstanceRef(TypeRef("default", "entity", "facility"), "1")
    action_family(
        registry,
        "needs_edge",
        inputs=[InputSpec("a", "instance"), InputSpec("b", "instance")],
        preconditions=[
            Precondition("edge_exists", "a", "must already cite", family="cites", object="b")
        ],
    )
    blind = make_registry(
        DegradedAdapter(adapter, stores_edges=False, why=NO_EDGES)
        if registry.caps.stores_edges
        else adapter
    )
    out = blind.preflight("needs_edge", {"a": facility, "b": facility}, actor="user:sd")
    assert out.verdict == "refused"
    assert out.refusal.reason == "precondition_unmet"
    assert out.refusal.detail["state"] == "unknown", (
        "unknown is NOT false -- Rule U, and the whole reason `holds` is three-valued"
    )
    assert out.preconditions[0].holds is None
    assert out.preconditions[0].why.strip(), "the adapter's own sentence, surfaced"
    assert out.complete is False
    assert out.why_incomplete.strip()


@NEEDS_ATTRIBUTES
def test_c19_46_a_preconditions_namespace_is_the_familys_and_reaches_neighbors(
    adapter, make_registry
):
    """Rule **2.4-7**. ``Precondition.namespace`` is the **family's**, and the edge kinds
    pass it to ``neighbors``, which has no default for it.

    ``Registry.neighbors`` makes ``namespace`` keyword-only **without** a default
    *precisely because ``"default"`` is a wrong answer nobody notices* -- UC3's whole
    subject. **The printed shape omitted this field until round 1**, while the probe kit
    had silently added it: *"fixed only in the throwaway probe kit"*, which is the
    failure row 4b names and which that row reproduced **inside the document that quotes
    it**. Two readings of the missing field gave OPPOSITE verdicts on UC3's own fixture
    -- one found the edge, the other returned `edge_family_unknown`.
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_edges:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_edges=False, so there is no "
            "edge for a namespaced family to be found in. C19-05 is the subject for the "
            "declined capability itself."
        )
    seed(registry, "borough", kind="value_set", namespace="dpr")
    seed(registry, "boro", kind="value_set", namespace="oti_311")
    edge_family(
        registry,
        "equivalent_to_x",
        level="type",
        namespace="dpr",
        src_kinds=("value_set",),
        dst_kinds=("value_set",),
    )
    a = TypeRef("dpr", "value_set", "borough")
    b = TypeRef("oti_311", "value_set", "boro")
    registry.add_edge("equivalent_to_x", a, b, "user:sd", namespace="dpr")

    for label, ns, expected in (("the family's", "dpr", True), ("the default", "default", None)):
        action_family(
            registry,
            f"reconcile_{ns}",
            inputs=[InputSpec("a", "type"), InputSpec("b", "type")],
            preconditions=[
                Precondition(
                    "edge_exists",
                    "a",
                    "the two must already be asserted equivalent",
                    family="equivalent_to_x",
                    object="b",
                    namespace=ns,
                )
            ],
        )
        out = registry.preflight(f"reconcile_{ns}", {"a": a, "b": b}, actor="user:sd")
        assert out.preconditions[0].holds is expected, f"{label}: {out.preconditions[0]}"


@NEEDS_ATTRIBUTES
def test_c19_47_the_edge_kinds_search_both_directions_and_are_conservative(
    adapter, make_registry
):
    """Rule **2.4-8**. The edge kinds search ``direction="both"``, so a **directed**
    family's ``edge_absent`` is conservative rather than exact.

    EDGES.md 2.2 records a confident, complete **false negative** produced by filtering a
    symmetric family on direction, so a precondition that filtered would inherit it. The
    cost is stated rather than hidden: for a directed family, ``edge_absent(a, b)`` is
    **false when the edge runs `b -> a`**. That is the conservative answer -- it refuses
    more than it must, never less -- and there is deliberately no ``direction`` key,
    because it is a fifth field on a shape whose whole argument is that it is not a query
    language.
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_edges:
        pytest.skip(
            "PACKAGE.md 3.2 -- stores_edges=False; there is no edge to have a direction."
        )
    seed(registry, "task", kind="entity")
    edge_family(registry, "blocks", level="instance", inverse_label="blocked_by")
    one = InstanceRef(TypeRef("default", "entity", "task"), "1")
    two = InstanceRef(TypeRef("default", "entity", "task"), "2")
    registry.add_edge("blocks", two, one, "user:sd")  # the edge runs b -> a

    action_family(
        registry,
        "link_tasks",
        inputs=[InputSpec("a", "instance"), InputSpec("b", "instance")],
        preconditions=[
            Precondition("edge_absent", "a", "do not link twice", family="blocks", object="b")
        ],
    )
    out = registry.preflight("link_tasks", {"a": one, "b": two}, actor="user:sd")
    assert out.preconditions[0].holds is False, (
        "the walk is direction='both', so an edge running b -> a makes edge_absent(a, b) "
        "FALSE -- conservative, and stated rather than sharpened"
    )
    assert out.verdict == "refused"
    assert out.refusal.detail["state"] == "false"


@NEEDS_ATTRIBUTES
def test_c19_55_an_input_determined_namespace_is_a_declaration_not_an_omission(
    adapter, make_registry
):
    """Rule **2.5-10**, and round 2's ingestion lens measured what the alternative costs.

    A catalogue ingester serves **84 publishing agencies** through one `ingest_dataset`
    family **[Observed, the pinned Socrata catalog: 2,399 datasets, 84 agencies]**, and
    the namespace it writes into is a property of the row being ingested. With a FIXED
    namespace on the effect, **2,394 of 2,399 correct invocations carried
    `effect_undeclared`** -- and the one invocation that ingested into the *wrong*
    agency's namespace carried the identical warning. **A detector that fires on 99.8%
    of a correct run is not a detector.**

    So ``namespace=None`` on an edge op **declares** *the namespace comes from this
    invocation's inputs*, and is satisfied only when the observed namespace is one the
    invocation's **own inputs** carry. The correct ingest stops warning; the
    wrong-publisher one still warns.
    """
    registry = make_registry(adapter)
    if not (registry.caps.stores_invocations and registry.caps.stores_edges):
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declines the invocation store or the edge "
            "store, and this rule is about an EFFECT compared against a RECORD."
        )
    seed(registry, "dataset", kind="entity", namespace="dpr")
    edge_family(registry, "same_tax_lot", level="instance")
    action_family(
        registry,
        "ingest_dataset",
        effects=[Effect(op="add_edge", family="same_tax_lot", namespace=None)],
        inputs=[InputSpec("row", "instance")],
    )
    row = InstanceRef(TypeRef("dpr", "entity", "dataset"), "uvpi-gqnh")

    right = registry.record_invocation(
        "ingest_dataset",
        {"row": row},
        actor="derived:catalogue_rule",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
        observed_effects=[Effect(op="add_edge", family="same_tax_lot", namespace="dpr")],
    )
    assert not [w for w in right.warnings if w.startswith("effect_undeclared:")], (
        "the CORRECT ingest must go quiet, or the detector fires on 99.8% of a good run"
    )

    wrong = registry.record_invocation(
        "ingest_dataset",
        {"row": row},
        actor="derived:catalogue_rule",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
        observed_effects=[Effect(op="add_edge", family="same_tax_lot", namespace="dot")],
    )
    assert [w for w in wrong.warnings if w.startswith("effect_undeclared:")], (
        "the WRONG-publisher invocation must still warn, which is the whole point"
    )


# ------------------------------------------------------------------- 3 invocations


@NEEDS_INVOCATIONS
def test_c19_29_declared_effects_are_copied_from_the_family_at_invocation_time(
    adapter, make_registry
):
    """Rule **3-1**. Amending the family does not re-describe an existing invocation's
    blast radius.

    An invocation that pointed at the *current* declaration would silently re-describe
    its own blast radius every time somebody edited the family -- so the record carries
    the declaration **it was judged against**, the same way ``attr_schema_version``
    carries which generation of a schema validated an entry. Without the copy,
    ``invocations(effect_undeclared=True)`` would answer a different question each time
    the vocabulary moved.
    """
    registry = make_registry(adapter)
    edge_family(registry, "stakes", level="instance") if registry.caps.stores_edges else None
    effects = (
        [Effect(op="add_edge", family="stakes", namespace="default")]
        if registry.caps.stores_edges
        else [Effect(op="host_state", why="writes a row this protocol does not model")]
    )
    action_family(registry, "add_stake", effects=effects)
    invocation = registry.record_invocation(
        "add_stake",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
    )
    assert len(invocation.declared_effects) == 1

    widened = list(effects) + [
        Effect(op="host_state", why="and something else entirely, added later")
    ]
    registry.import_types(
        [
            {
                "name": "add_stake",
                "kind": "action",
                "definition": "widened",
                "status": "active",
                "attributes": action_attributes(
                    reversibility="reversible", approval_mode="auto", effects=widened
                ),
            }
        ],
        namespace="default",
        kind="action",
    )
    again = [
        i
        for i in registry.invocations().invocations
        if i.invocation_id == invocation.invocation_id
    ][0]
    assert len(again.declared_effects) == 1, (
        "the RECORD's declaration is the one the gate judged, not the one the family now "
        "carries -- rule 3-1's whole subject"
    )


@NEEDS_INVOCATIONS
def test_c19_30_gate_verdict_has_three_values_and_not_asked_is_one_of_them(
    adapter, make_registry
):
    """Rule **3-2**. ``not_asked`` is a real and common state, and ``False`` would say
    *the gate refused* -- a different and much worse claim.

    A host may record an invocation it ran without consulting ``preflight`` at all. Rule
    U, on a three-state field.
    """
    registry = make_registry(adapter)
    assert GATE_VERDICTS == ("allowed", "refused", "not_asked")
    action_family(registry, "search_tasks")
    for verdict in GATE_VERDICTS:
        out = registry.record_invocation(
            "search_tasks",
            {},
            actor="user:sd",
            outcome="applied" if verdict != "refused" else "refused",
            gate_verdict=verdict,
            approved_by="auto:auto" if verdict == "allowed" else None,
            refusal=Refusal("precondition_unmet", {}) if verdict == "refused" else None,
        )
        assert out.gate_verdict == verdict
    with pytest.raises(ValueError):
        registry.record_invocation(
            "search_tasks", {}, actor="user:sd", outcome="applied", gate_verdict="maybe"
        )


@NEEDS_INVOCATIONS
def test_c19_31_approved_by_is_never_fabricated_and_never_null_where_the_gate_decided(
    adapter, make_registry
):
    """Rule **3-3**, and it is the kill row's sibling: an approval nobody performed.

    **The first draft got this exactly backwards and round 1 caught it.** It filled
    ``"auto:<policy>"`` on every ``applied`` invocation, so an ``irreversible``/``human``
    family -- the class 2.2's cross-field rule exists to make un-auto-approvable --
    recorded ``outcome="applied"``, ``gate_verdict="not_asked"``,
    ``approved_by="auto:action_policy"``, actor ``ai:reaper``, **no human and no
    warning**. That is precisely the field EDGES.md 5.1 dropped from ``EdgeProvenance``
    because *"a field whose only honest value is a lie should not be on the shape."*

    A null plus a named warning is the honest third answer the first draft did not look
    for -- and the never-null rule binds **only where the gate decided**.
    """
    registry = make_registry(adapter)
    action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )

    # The gate was not asked, and the host claims a policy approved it anyway.
    lied = registry.record_invocation(
        "delete_person",
        {},
        actor="ai:reaper",
        outcome="applied",
        gate_verdict="not_asked",
        approved_by="auto:action_policy",
    )
    assert lied.provenance.approved_by is None, "an approval nobody performed"
    assert "approval_unrecorded" in lied.warnings

    # And where the gate DID decide, the value is whatever preflight returned.
    gate = registry.preflight("delete_person", {}, actor="user:sd", approved_by="user:sd")
    assert gate.verdict == "allowed"
    honest = registry.record_invocation(
        "delete_person",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by=gate.approved_by,
        judged=gate,
    )
    assert honest.provenance.approved_by == "user:sd"
    assert honest.provenance.approved_at is not None
    assert "approval_unrecorded" not in honest.warnings


@NEEDS_INVOCATIONS
def test_c19_32_a_refused_outcome_requires_a_refusal_from_the_closed_vocabulary(
    adapter, make_registry
):
    """Rule **3-4**. A refused invocation with no reason is an unexplained *"no"* in the
    ledger whose whole purpose is explaining.

    And ``outcome`` is closed at four: ``failed`` is **not** a refusal, because a refusal
    is a decision and a failure is an accident, and collapsing them loses the only
    distinction an operator cares about at 3am. There is deliberately no ``pending`` --
    a mode-``human`` invocation awaiting a decision is not an invocation yet, and
    inventing the value would make this layer own a queue.
    """
    registry = make_registry(adapter)
    assert OUTCOMES == ("applied", "refused", "failed", "compensated")
    assert "pending" not in OUTCOMES
    action_family(registry, "search_tasks")
    with pytest.raises(ValueError):
        registry.record_invocation(
            "search_tasks", {}, actor="user:sd", outcome="refused", gate_verdict="refused"
        )
    out = registry.record_invocation(
        "search_tasks",
        {},
        actor="user:sd",
        outcome="refused",
        gate_verdict="refused",
        refusal=Refusal("tier_below_action_policy", {"state": "false"}),
    )
    assert out.outcome == "refused"
    assert out.refusal is not None and out.refusal.reason == "tier_below_action_policy"
    with pytest.raises(ValueError):
        registry.record_invocation(
            "search_tasks", {}, actor="user:sd", outcome="pending", gate_verdict="allowed"
        )


@NEEDS_INVOCATIONS
def test_c19_33_a_surplus_effect_warns_and_a_subset_warns_nothing(adapter, make_registry):
    """Rule **3-5**, and the asymmetry is deliberate.

    ``observed ⊄ declared`` warns per surplus effect and the record is **kept** -- 2.5's
    argument: refusing to record what already occurred destroys the only evidence that
    the undeclared effect happened. ``observed ⊊ declared`` warns **nothing**: a
    permission is not a promise, and warning on an unused permission would train hosts to
    declare narrowly and amend often, which is worse than declaring broadly and being
    measured.
    """
    registry = make_registry(adapter)
    declared = [
        Effect(op="host_state", why="deletes the person row"),
        Effect(op="host_state", why="cascades eleven foreign keys"),
    ]
    action_family(
        registry,
        "delete_person",
        reversibility="irreversible",
        approval_mode="human",
        effects=declared,
    )
    subset = registry.record_invocation(
        "delete_person",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="user:sd",
        observed_effects=[declared[0]],
    )
    assert not [w for w in subset.warnings if w.startswith("effect_undeclared:")]

    surplus = registry.record_invocation(
        "delete_person",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="user:sd",
        observed_effects=[*declared, Effect(op="host_state", why="and unlinked an account")],
    )
    warned = [w for w in surplus.warnings if w.startswith("effect_undeclared:")]
    assert len(warned) == 1, warned
    assert "and unlinked an account" in warned[0]
    # The record is KEPT, which is the half a refusal would have destroyed.
    assert surplus.outcome == "applied"
    assert registry.invocations(effect_undeclared=True).known == 1


@NEEDS_INVOCATIONS
def test_c19_56_the_copy_is_taken_from_what_the_gate_judged(adapter, make_registry):
    """Rule **3-7**, and it is round 2's finding: the gate-to-record window laundered an
    undeclared effect.

    Rule 3-1 copies the declaration *"so amending the family does not re-describe an
    existing invocation's blast radius"* -- and the copy was being taken at **record**
    time from the **current** family, which does exactly what the rule forbids. A
    reviewer widened a family between the two calls and watched an undeclared
    ``retract_edge`` enter the ledger with no warning.

    The fix is ``family_version`` plus ``record_invocation(judged=…)``, and
    ``declaration_amended:<from>:<to>`` as the twenty-fifth warning value. *(My proposed
    fix -- copy the whole policy -- was refused by the reviewer with the right argument:
    it WIDENS the lie, because the ledger would file a `human`/`opus` gate approval
    against a family it describes as `auto` with no floor.)*
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_events:
        pytest.skip(
            "PACKAGE.md 3.2 -- stores_events=False, and ACTIONS.md 3.1's generation is "
            "counted from the append-only log rather than stored twice, so this backend "
            "cannot tell one declaration from another. It therefore never emits "
            "`declaration_amended` rather than emitting it wrongly -- Rule U."
        )
    narrow = [Effect(op="host_state", why="writes one row")]
    action_family(registry, "ingest", effects=narrow)
    gate = registry.preflight("ingest", {}, actor="user:sd")
    assert gate.verdict == "allowed"

    registry.import_types(
        [
            {
                "name": "ingest",
                "kind": "action",
                "definition": "widened between the gate and the record",
                "status": "active",
                "attributes": action_attributes(
                    reversibility="reversible",
                    approval_mode="auto",
                    effects=[*narrow, Effect(op="host_state", why="and a second row")],
                ),
            }
        ],
        namespace="default",
        kind="action",
    )
    out = registry.record_invocation(
        "ingest",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by=gate.approved_by,
        judged=gate,
        observed_effects=[Effect(op="host_state", why="and a second row")],
    )
    assert any(w.startswith("declaration_amended:") for w in out.warnings), out.warnings
    assert out.family_version == gate.family_version
    # And the laundering is closed: the second effect was NOT in what the gate judged,
    # so it is surplus and it warns.
    assert [w for w in out.warnings if w.startswith("effect_undeclared:")]


@NEEDS_INVOCATIONS
def test_c19_57_declared_policy_carries_the_four_facts_that_decide_a_verdict(
    adapter, make_registry
):
    """Rule **3-8**. ``declared_policy`` carries ``approval_mode``, ``min_auto_tier``,
    ``reversibility`` and the precondition kinds, **for the reason rule 3-1 carries the
    effects**.

    Round 2's auditor asking *"was Haiku permitted to run this unattended in March?"* had
    no field to read, because the copy was taken for one of the five things that decide a
    verdict. Round 3 then found the fix itself defective in two ways: it ran *after* the
    approval logic, and ``declared_policy["reversibility"]`` was the **current** family's
    while its three neighbours were the gate's -- *one dict, two moments, no marker*.
    """
    registry = make_registry(adapter)
    action_family(
        registry,
        "flag_facility",
        min_auto_tier="sonnet",
        inputs=[InputSpec("a", "type")],
        preconditions=[Precondition("type_active", "a", "the scale must still be live")],
    )
    facility = TypeRef("default", "entity", "facility")
    seed(registry, "facility", kind="entity")
    gate = registry.preflight("flag_facility", {"a": facility}, actor="ai:c", tier="opus")
    assert gate.verdict == "allowed"
    out = registry.record_invocation(
        "flag_facility",
        {"a": facility},
        actor="ai:c",
        tier="opus",
        outcome="applied",
        gate_verdict="allowed",
        approved_by=gate.approved_by,
        judged=gate,
    )
    policy = out.declared_policy
    assert policy["approval_mode"] == "auto"
    assert policy["min_auto_tier"] == "sonnet"
    assert policy["reversibility"] == "reversible"
    assert list(policy["preconditions"]) == ["type_active"]
    assert policy["tier_order"], "the deployment's order, so the comparison is auditable"
    # Every one of the four comes from the GATE, not from the family as it stands now.
    assert policy["reversibility"] == gate.reversibility
    assert policy["min_auto_tier"] == gate.tier_floor
    assert policy["approval_mode"] == gate.approval_mode


# --------------------------------------------------------------------- 5.2 the gate


@NEEDS_ATTRIBUTES
def test_c19_14_human_mode_refuses_an_approver_the_registry_cannot_recognise(
    adapter, make_registry
):
    """Rule **5.2-2** -- an **allowlist**, not a prefix blocklist, and it took two rounds.

    Round 1's blocklist refused ids prefixed ``ai:``, ``auto:`` or ``derived:``; a
    reviewer got ``bot:reaper``, ``svc:cleanup``, ``AI:bot`` and ``nobody`` past it on an
    ``irreversible``/``human`` family. **Round 2 found the replacement was still a
    blocklist**: the derived ``created_by`` maps an *unrecognised* prefix to ``"user"``,
    which is right for provenance and wrong for a gate, so the same five walked through
    the fix for the blocklist.

    INTERFACE.md line 58 names the failure by name -- *"a `created_by_actor` string
    convention that nothing validates"*. **A human approver must be RECOGNISABLE as one.
    Rule U: unknown is not a person.**
    """
    registry = make_registry(adapter)
    action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )
    for impostor in (None, "", "bot:reaper", "svc:cleanup", "AI:bot", "agent:claude",
                     "nobody", "ai:reaper", "auto:nightly", "derived:rule", "user:"):
        out = registry.preflight(
            "delete_person", {}, actor="ai:reaper", approved_by=impostor
        )
        assert out.verdict == "refused", f"{impostor!r} was accepted as a person"
        assert out.refusal.reason == "human_approval_required"
        assert out.approved_by is None

    ok = registry.preflight("delete_person", {}, actor="ai:reaper", approved_by="user:sd")
    assert ok.verdict == "allowed" and ok.approved_by == "user:sd"


@NEEDS_ATTRIBUTES
def test_c19_15_a_tier_below_the_floor_refuses_with_state_false(adapter, make_registry):
    """Rule **5.2-3**. ``tier_below_action_policy``, with ``detail["state"] == "false"``,
    the family's floor and the actor's tier.

    **`tier_below_auto_approve_policy` is NOT reused**, and the temptation to reuse it is
    exactly INTERFACE.md 2.3's Cause B. That value is about **approving a proposed
    type**; this one is about **invoking an approved action**. Two policies, two objects,
    two lifecycles: a deployment may auto-approve Haiku's *proposals* and refuse Haiku's
    *invocations*, and one word could not express that.

    The fixture is 0.5's own failure: `scope_severity_code` is the value set the cheapest
    tier **inverted** -- reporting that higher letters are less serious when J/K/L are
    Immediate Jeopardy -- with every number it produced still correct and nothing
    erroring. An action gated on that scale, invoked by that tier, unattended, is 0.5's
    failure with a write attached.
    """
    registry = make_registry(adapter)
    action_family(registry, "flag_facility", min_auto_tier="sonnet")
    low = registry.preflight("flag_facility", {}, actor="ai:haiku_classifier", tier="haiku")
    assert low.verdict == "refused"
    assert low.refusal.reason == "tier_below_action_policy"
    assert low.refusal.detail["state"] == "false"
    assert low.refusal.detail["tier"] == "haiku"
    assert low.refusal.detail["min_auto_tier"] == "sonnet"
    assert low.tier_floor == "sonnet"

    high = registry.preflight("flag_facility", {}, actor="ai:c", tier="opus")
    assert high.verdict == "allowed"
    assert high.approved_by and high.approved_by.startswith("auto:")


@NEEDS_ATTRIBUTES
def test_c19_16_no_floor_is_a_legal_configuration_reported_as_a_stated_absence(
    adapter, make_registry
):
    """Rule **5.2-4**. ``min_auto_tier=None`` under ``approval_mode="auto"`` is a
    **legitimate configuration** -- a single-tier deployment has nothing to compare.

    It is **not** a warning value, deliberately: minting one would put a vocabulary entry
    on a correct configuration. What the caller gets instead is Rule U on the report --
    ``tier_floor=None`` with a ``tier_floor_why`` saying so. **The honest surface is a
    stated absence, not an alarm.**
    """
    registry = make_registry(adapter)
    action_family(registry, "search_tasks", min_auto_tier=None)
    out = registry.preflight("search_tasks", {}, actor="user:sd")
    assert out.verdict == "allowed"
    assert out.tier_floor is None
    assert out.tier_floor_why and out.tier_floor_why.strip()
    assert out.refusal is None


@NEEDS_ATTRIBUTES
def test_c19_17_all_three_unknown_tier_causes_refuse_and_none_of_them_says_false(
    adapter, make_registry
):
    """Rule **5.2-5**. The comparison is ``bool | None``, and **all three** unknown causes
    -- no order, no tier, a tier outside the order -- refuse with
    ``detail["state"] == "unknown"`` and a ``why`` naming which. **None of them raises,
    and none says `false`.**

    The shipped comment on ``TierOrder.below`` gives the reason for the second: returning
    ``False`` would *"auto-approve an unknown model on the strength of not recognising
    its name"*. Round 1 found the first draft returning a confident below-the-floor
    refusal for a tier nobody supplied, and **raising an uncaught `ValueError`** for a
    tier outside the order -- in the one place 5.2 flags mixed vendors as **[Assumed]**
    and possibly wrong.
    """
    registry = make_registry(adapter)
    action_family(registry, "flag_facility", min_auto_tier="sonnet")

    no_tier = registry.preflight("flag_facility", {}, actor="ai:c", tier=None)
    outside = registry.preflight("flag_facility", {}, actor="ai:c", tier="gpt5")

    orderless = make_registry(adapter, tier_order=TierOrder(()))
    action_family(orderless, "flag_facility_x", min_auto_tier="sonnet")
    no_order = orderless.preflight("flag_facility_x", {}, actor="ai:c", tier="haiku")

    whys = set()
    for label, out in (("no tier", no_tier), ("outside", outside), ("no order", no_order)):
        assert out.verdict == "refused", label
        assert out.refusal.reason == "tier_below_action_policy", label
        assert out.refusal.detail["state"] == "unknown", label
        assert out.refusal.detail["why"].strip(), label
        whys.add(out.refusal.detail["why"])
    assert len(whys) == 3, f"each cause needs its own sentence, got {whys}"


@NEEDS_INVOCATIONS
def test_c19_18_model_tier_on_an_invocation_is_the_invoking_actors(adapter, make_registry):
    """Rule **5.2-6**. ``InvocationProvenance.model_tier`` is the tier of the **invoking**
    actor, distinct from the family's own ``provenance.model_tier``.

    Those are two different facts about two different objects and both matter: **a family
    proposed by Haiku and invoked by Opus is not the same risk as the reverse.**
    """
    registry = make_registry(adapter)
    proposal = registry.propose_type(
        "infer_person_relationships",
        "classifies person pairs and applies the confident ones",
        EVIDENCE,
        "ai:proposer",
        tier="haiku",
        kind="action",
        attributes=action_attributes(reversibility="reversible", approval_mode="auto"),
    )
    entry = proposal if isinstance(proposal, TypeEntry) else registry.approve(
        proposal.id, "user:sd"
    )
    assert isinstance(entry, TypeEntry), entry
    assert entry.provenance.model_tier == "haiku", "the tier that PROPOSED the verb"

    out = registry.record_invocation(
        "infer_person_relationships",
        {},
        actor="ai:classifier",
        tier="opus",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
    )
    assert out.provenance.model_tier == "opus", "the tier that INVOKED it"


@pytest.mark.requires_capability(
    "stores_attributes", "stores_invocations", "stores_invocation_events"
)
def test_c19_50_review_mode_records_a_policy_approval_and_joins_the_review_queue(
    adapter, make_registry
):
    """Rule **5.2-7**. ``approval_mode="review"`` records ``approved_by="auto:<policy>"``
    and the invocation is enumerable by ``invocations(unreviewed=True)`` **until an
    ``invocation_reviewed`` event sets ``reviewed_at``**.

    Round 1 found ``review`` mode and ``compensated`` *"specified and executed by
    nothing"*, and 11.5 claiming UC3 showed the second while UC3's probe contained no
    compensation at all -- *a false claim in a walk-through*, which `USE-CASES.md` calls
    a silent accommodation rather than a pass.

    **The writer of that event is deviation D-6b-3**: 5.2 names the read and 3.5 mints
    the value, and 6's four calls contain nothing that appends one, so the queue could
    never drain. `review_invocation` is a fifth call the specification does not have, and
    it is recorded in `6B-RUN.md` rather than smuggled in.
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_events:
        pytest.skip(
            "PACKAGE.md 3.2 -- a review IS an event, and this backend keeps none, so "
            "`review_invocation` refuses `cannot_record_override` rather than claiming "
            "a review nothing recorded. Asserted below on the legs that can keep one."
        )
    action_family(registry, "reconcile_borough", approval_mode="review")
    action_family(registry, "search_tasks", approval_mode="auto")
    gate = registry.preflight("reconcile_borough", {}, actor="user:sd")
    assert gate.verdict == "allowed"
    assert gate.approved_by.startswith("auto:"), "a POLICY approved it, and says so"

    out = registry.record_invocation(
        "reconcile_borough",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by=gate.approved_by,
        judged=gate,
    )
    assert out.provenance.approved_by.startswith("auto:")
    assert out.reviewed_at is None

    # An `auto`-mode invocation is NOT in the queue: the filter is about the family's
    # mode as well as about the row, which is the half that stays above the store.
    registry.record_invocation(
        "search_tasks",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
    )
    queue = registry.invocations(unreviewed=True)
    assert queue.known == 1, [i.family for i in queue.invocations]
    assert queue.invocations[0].family == "reconcile_borough"

    registry.review_invocation(out.invocation_id, reviewed_by="user:boss")
    assert registry.invocations(unreviewed=True).known == 0
    again = [
        i for i in registry.invocations().invocations if i.invocation_id == out.invocation_id
    ][0]
    assert again.reviewed_at is not None


# ------------------------------------------------------------------------- 6 the calls


@NEEDS_ATTRIBUTES
def test_c19_34_preflight_records_nothing_and_is_idempotent(adapter, make_registry):
    """Rule **6-1**. Calling it N times leaves the invocation store unchanged.

    It is a question, and a host that wants the question answered *and* the answer
    recorded calls ``record_invocation`` with the verdict it received. This matters
    because 12's T2.5 turns on it: a tier-refused ``preflight`` records **nothing**, and
    the host may record the refusal itself with ``outcome="refused"``.
    """
    registry = make_registry(adapter)
    action_family(registry, "flag_facility", min_auto_tier="sonnet")
    before = (
        registry.invocations().known if registry.caps.stores_invocations else None
    )
    for _ in range(5):
        registry.preflight("flag_facility", {}, actor="ai:c", tier="opus")
        registry.preflight("flag_facility", {}, actor="ai:c", tier="haiku")
    if registry.caps.stores_invocations:
        assert registry.invocations().known == before == 0
    else:
        assert isinstance(registry.invocations(), Refusal)


@NEEDS_ATTRIBUTES
def test_c19_35_every_precondition_result_names_the_call_that_answered_it(
    adapter, make_registry
):
    """Rule **6-2**. ``evaluated_by`` is drawn from the closed set ``list_types`` /
    ``predicates`` / ``neighbors``.

    2.4's no-query-language claim, made mechanical. C19-02 asserts the mapping kind by
    kind; this asserts the *closure* -- that no result can name anything else, whatever
    the condition.
    """
    registry = make_registry(adapter)
    seed(registry, "facility", kind="entity")
    seed(registry, "commentable", kind="predicate")
    facility = TypeRef("default", "entity", "facility")
    action_family(
        registry,
        "many_conditions",
        inputs=[InputSpec("a", "type"), InputSpec("b", "type")],
        preconditions=[
            Precondition("type_active", "a", "must be live"),
            Precondition("predicate_holds", "a", "must be commentable", predicate="commentable"),
            Precondition("edge_exists", "a", "must be linked", family="cites", object="b"),
            Precondition("edge_absent", "b", "must not be linked back", family="cites", object="a"),
        ],
    )
    out = registry.preflight(
        "many_conditions", {"a": facility, "b": facility}, actor="user:sd"
    )
    assert out.known == 4
    for result in out.preconditions:
        assert result.evaluated_by in EVALUATORS, result


def test_c19_36_holds_none_is_refused_as_unknown_and_never_treated_as_satisfied(
    adapter, make_registry
):
    """Rule **6-3**. ``holds=None`` is refused, and the refusal's ``detail`` says
    **unknown** rather than **false**; unknown is never treated as satisfied.

    Its own id rather than an assertion inside C19-05, because the two rules are about
    different halves: C19-05 is that a degraded backend PRODUCES the unknown, and this is
    that the gate REFUSES on it. A backend that produced honest unknowns and a gate that
    approved on them would pass one and fail the other.
    """
    registry = make_registry(adapter)
    if not registry.caps.stores_attributes:
        pytest.skip(
            "ACTIONS.md 2.2 puts the eight keys in `TypeEntry.attributes`; this backend "
            "stores no arbitrary keys, so no family can be declared on it."
        )
    seed(registry, "facility", kind="entity")
    facility = TypeRef("default", "entity", "facility")
    action_family(
        registry,
        "needs_unknown_predicate",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition(
                "predicate_holds", "a", "must be searchable", predicate="never_registered"
            )
        ],
    )
    out = registry.preflight("needs_unknown_predicate", {"a": facility}, actor="user:sd")
    assert out.preconditions[0].holds is None
    assert out.verdict == "refused", "unknown is NEVER satisfied"
    assert out.refusal.detail["state"] == "unknown"
    assert out.complete is False


@NEEDS_INVOCATIONS
def test_c19_37_record_invocation_does_not_re_evaluate_and_keeps_a_refused_gate(
    adapter, make_registry
):
    """Rule **6-4**, and it is the TOCTOU gap named rather than closed.

    Between ``preflight`` returning ``allowed`` and this call filing a report the world
    may change. ``record_invocation`` does **not** re-evaluate the preconditions, and
    that is deliberate -- re-evaluating would mean refusing to record something that
    already happened, and recording a stale ``allowed`` is at least *true about what the
    host was told*. What closes the gap is not a lock; it is that the record carries the
    verdict it acted on and the timestamp it acted at, so a divergence is reconstructible
    after the fact.

    **And an invocation whose gate REFUSED is recorded rather than discarded**, which is
    4's whole argument: the gate is advisory by construction, and what makes it
    not-nothing is that every override is enumerable.
    """
    registry = make_registry(adapter)
    seed(registry, "facility", kind="entity")
    facility = TypeRef("default", "entity", "facility")
    action_family(
        registry,
        "flag_facility",
        inputs=[InputSpec("a", "type")],
        preconditions=[Precondition("type_active", "a", "the word must still be live")],
    )
    gate = registry.preflight("flag_facility", {"a": facility}, actor="user:sd")
    assert gate.verdict == "allowed"

    # The world moves: the type the precondition required is retired.
    registry.retire("facility", "superseded", retired_by="user:sd", force=True)

    out = registry.record_invocation(
        "flag_facility",
        {"a": facility},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by=gate.approved_by,
        judged=gate,
    )
    assert out.outcome == "applied", "a stale allowed is RECORDED, not refused"
    assert out.gate_verdict == "allowed"

    override = registry.record_invocation(
        "flag_facility",
        {"a": facility},
        actor="ai:reaper",
        outcome="applied",
        gate_verdict="refused",
    )
    assert override.outcome == "applied"
    assert "approval_unrecorded" in override.warnings
    floor = registry.invocations(gate_verdict="refused", outcome="applied")
    assert floor.known == 1
    assert floor.complete is False, "every filtered answer is a FLOOR, not a total"


@NEEDS_INVOCATIONS
def test_c19_38_the_report_is_a_floor_whenever_a_filter_or_a_limit_bit(
    adapter, make_registry
):
    """Rule **6-5**. ``known`` is ``int | None`` and ``complete`` is ``False`` whenever a
    filter suppressed rows or ``limit`` truncated the answer.

    ``known: int | None`` and not ``int``, because INTERFACE.md 3's amendment settled that
    a backend entitled to say *"we did not count"* must have somewhere to say it, and
    ``0`` would falsify it.

    *(The first draft's implementation stamped `complete=True` through a dead
    sub-expression -- `(not filtered or True)` -- in the one query 4 asks an operator to
    act on.)*
    """
    registry = make_registry(adapter)
    action_family(registry, "search_tasks")
    for _ in range(3):
        registry.record_invocation(
            "search_tasks",
            {},
            actor="user:sd",
            outcome="applied",
            gate_verdict="allowed",
            approved_by="auto:auto",
        )
    whole = registry.invocations()
    assert whole.known == 3 and whole.complete is True

    filtered = registry.invocations(family="search_tasks")
    assert filtered.known == 3
    assert filtered.complete is False and filtered.why_incomplete.strip()

    bounded = registry.invocations(limit=2)
    assert bounded.known == 2
    assert bounded.complete is False and bounded.why_incomplete.strip()


@NEEDS_ATTRIBUTES
def test_c19_51_both_invocation_calls_refuse_a_predicate_ref_whatever_was_declared(
    adapter, make_registry
):
    """Rule **6-6**, and **this is the kill row, constructed end to end**.

    Round 1 declared a family with ``kinds=None``, handed ``preflight`` two
    ``kind="predicate"`` refs, got ``verdict="allowed"`` and recorded it ``applied``:
    **`merge_capabilities(commentable, searchable)`, through the one door 2.3 called
    unconstructible.** EDGES.md 2.4.1 binds its endpoint rule at BOTH layers and spent
    its own round 1 learning why; ACTIONS.md claimed to inherit that rule *unchanged*
    while inheriting one half, and 17 audited it as shut.

    So both calls validate every supplied ``InputRef`` -- ref shape, ``kinds``,
    ``families``, and required-but-missing -- and refuse with ``input_kind_mismatch``.
    **A `kind="predicate"` ref is refused whatever the family declared.**
    """
    registry = make_registry(adapter)
    seed(registry, "commentable", kind="predicate")
    seed(registry, "searchable", kind="predicate")
    left = TypeRef("default", "predicate", "commentable")
    right = TypeRef("default", "predicate", "searchable")
    action_family(
        registry,
        "merge_capabilities",
        inputs=[InputSpec("a", "type", kinds=None), InputSpec("b", "type", kinds=None)],
    )
    gate = registry.preflight("merge_capabilities", {"a": left, "b": right}, actor="ai:c")
    assert isinstance(gate, Refusal), f"the gate said {gate!r} -- the kill row is open"
    assert gate.reason == "input_kind_mismatch"
    assert gate.detail["problem"] == "predicate"

    if registry.caps.stores_invocations:
        recorded = registry.record_invocation(
            "merge_capabilities",
            {"a": left, "b": right},
            actor="ai:c",
            outcome="applied",
            gate_verdict="not_asked",
        )
        assert isinstance(recorded, Refusal), "the second door must refuse it too"
        assert recorded.reason == "input_kind_mismatch"
        assert registry.invocations().known == 0, "nothing was written"

    # And the ordinary shape checks bind at the same door.
    seed(registry, "task", kind="entity")
    task = TypeRef("default", "entity", "task")
    action_family(
        registry, "narrow", inputs=[InputSpec("a", "type", kinds=("value_set",))]
    )
    assert registry.preflight("narrow", {"a": task}, actor="user:sd").reason == (
        "input_kind_mismatch"
    )
    assert registry.preflight("narrow", {}, actor="user:sd").detail["problem"] == "missing"
    assert (
        registry.preflight("narrow", {"z": task}, actor="user:sd").detail["problem"]
        == "undeclared"
    )


@NEEDS_ATTRIBUTES
def test_c19_52_a_shipped_call_that_raises_becomes_holds_none_plus_a_why(
    adapter, make_registry
):
    """Rule **6-7**. ``preflight`` never raises where it could return.

    The shipped ``predicates(of=…)`` and ``consumers(…)`` raise ``UnknownType`` for an
    unregistered subject, and a ``predicate_holds`` condition naming one would escape the
    return type entirely. It is **caught** and becomes ``holds=None`` plus a ``why`` --
    Rule U's unknown, which the verdict then refuses. **Round 1 found the escape.**
    """
    registry = make_registry(adapter)
    seed(registry, "commentable", kind="predicate")
    ghost = TypeRef("default", "entity", "never_registered")
    action_family(
        registry,
        "ph",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition("predicate_holds", "a", "must be commentable", predicate="commentable")
        ],
    )
    out = registry.preflight("ph", {"a": ghost}, actor="user:sd")
    assert not isinstance(out, Exception)
    assert out.preconditions[0].holds is None
    assert out.preconditions[0].why.strip()
    assert out.verdict == "refused"

    # And the shipped call really does raise, so the catch is load-bearing rather than
    # defensive. Asserted here so a later change that stops it raising is visible.
    with pytest.raises(UnknownType):
        registry.predicates(of="never_registered")


# ---------------------------------------------------------------- 8 capability flags


def test_c19_39_no_invocation_store_refuses_rather_than_returning_an_empty_report(
    adapter, make_registry
):
    """Rule **8-1**. ``stores_invocations=False`` makes every call that **reads or writes
    the invocation store** return ``Refusal(reason="action_store_absent")``, never an
    empty report.

    An empty ``InvocationReport`` reads as *"nothing has ever run"*, which is Rule U's
    forbidden empty in the one call a caller would believe -- the fifth capability
    refusal of that shape after ``proposals_not_stored``, ``cannot_record_override``,
    ``consumer_source_read_only`` and ``edge_store_absent``.

    **``preflight`` and ``projection`` touch no invocation and are unaffected**;
    *"every invocation call"* was undefined until round 1 asked which four.

    This test's SUBJECT is the declined capability, so it does not skip on a backend that
    declines it (PACKAGE.md 6.1 rule 1). On `sqlite_minimal` it runs against a store
    whose `oo_invocation` is absent from the SQL rather than hidden behind a Python `if`.
    """
    caps = adapter.capabilities()
    blind = make_registry(
        DegradedAdapter(adapter, stores_invocations=False, why=NO_INVOCATIONS)
        if caps.stores_invocations
        else adapter
    )
    outcomes = [
        blind.record_invocation("f", {}, actor="user:sd", outcome="applied"),
        blind.invocations(),
        blind.review_invocation("inv1", reviewed_by="user:sd"),
    ]
    for out in outcomes:
        assert isinstance(out, Refusal), out
        assert out.reason == "action_store_absent"
        assert out.detail["why"].strip(), "the backend's own sentence, surfaced verbatim"

    # `preflight` and `projection` are unaffected: they touch no invocation.
    assert isinstance(blind.projection("s", budget=10), ProjectionReport)
    assert blind.preflight("f", {}, actor="user:sd").reason == "action_family_unknown"

    # And the primitive underneath raises rather than pretending to store and lose.
    if not caps.stores_invocations:
        with pytest.raises(NotSupported):
            adapter.find_invocations()


def test_c19_40_every_false_action_flag_carries_a_why_and_two_are_vacuous(
    adapter, make_registry
):
    """Rule **8-2**, and it is ``C0-01``'s carve-out shape applied to a third group.

    Every ``False`` action flag carries a non-empty ``Capabilities.why`` -- and when
    ``stores_invocations`` is ``False`` the other two are **vacuous rather than
    declined**. There is no invocation store, so *"why do you not index invocations by
    family?"* has no answer beyond the first sentence, and requiring two more teaches an
    adapter author to write sentences nobody reads, which is how a ``why`` dict stops
    being a mechanism.
    """
    caps = adapter.capabilities()
    assert set(ACTION_CAPABILITY_FLAGS) <= set(CAPABILITY_FLAGS), (
        "an action flag living outside CAPABILITY_FLAGS is one that the capability "
        "matrix, C0-01 and the degraded double all fail to reach"
    )
    assert caps.missing_why() == (), caps.missing_why()

    absent = Capabilities(
        **{f: True for f in CAPABILITY_FLAGS if f not in ACTION_CAPABILITY_FLAGS},
        stores_invocations=False,
        stores_invocation_events=False,
        indexes_invocations_by_family=False,
        why={"stores_invocations": "this backend is a type registry only"},
    )
    assert absent.missing_why() == (), "the other two are VACUOUS, not declined"

    partial = Capabilities(
        **{f: True for f in CAPABILITY_FLAGS if f not in ACTION_CAPABILITY_FLAGS},
        stores_invocations=True,
        stores_invocation_events=True,
        indexes_invocations_by_family=False,
        why={},
    )
    assert "indexes_invocations_by_family" in partial.missing_why(), (
        "with a store present, declining an index is a DECLINE and needs its sentence"
    )


def test_c19_41_two_scopes_on_one_connection_is_non_conformant(adapter, make_registry):
    """Rule **8-3**. With ``action_store_shares_connection=True``,
    ``action_transaction_scope`` MUST equal ``transaction_scope``.

    An adapter declaring otherwise is claiming that half its writes are the host's to
    commit and half its own, on one transaction, which is not a thing that can be true.
    ``Capabilities.scope_conflict()`` **RETURNS** the sentence and does not raise -- the
    shipped method's own contract, *"so a `Capabilities` stays a plain frozen record that
    a test can construct in any shape it likes"*. Round 1 found the probe kit raising
    instead, which would have made the rule testable two incompatible ways.

    **With a third store there are now two independent pairs and one sentence.** Which
    one it names when both conflict is unspecified -- question **Q42**, ruled **R46**:
    record it, and do not change a shipped signature for a case no backend has produced.
    """
    base = {f: True for f in CAPABILITY_FLAGS}
    clean = Capabilities(**base, why={})
    assert clean.scope_conflict() is None

    conflict = Capabilities(
        **base,
        why={"action_transaction_scope": "the host owns the invocation table"},
        action_transaction_scope="savepoint",
        action_store_shares_connection=True,
    )
    sentence = conflict.scope_conflict()
    assert sentence is not None and "action_transaction_scope" in sentence
    assert "ACTIONS.md 8.2" in sentence

    # Two CONNECTIONS may legitimately differ, and then there is no conflict to report.
    two_stores = Capabilities(
        **base,
        why={"action_transaction_scope": "a host-owned audit table on its own connection"},
        action_transaction_scope="savepoint",
        action_store_shares_connection=False,
    )
    assert two_stores.scope_conflict() is None

    # The shipped backends derive the scope rather than declaring it, so the rule cannot
    # be broken by forgetting.
    assert adapter.capabilities().scope_conflict() is None


@NEEDS_INVOCATIONS
def test_c19_42_savepoint_scope_is_stamped_on_the_write_and_not_on_the_read(
    adapter, make_registry
):
    """Rule **8-4**. Under ``action_transaction_scope="savepoint"``,
    ``record_invocation`` stamps ``not_durable_until_host_commits`` **itself**, and
    ``invocations`` does not.

    Stamped by the write call site because row 3d's lesson is that *a signal that never
    turns off is noise*; and stamped by ``record_invocation`` **itself** rather than
    carried forward from anywhere, because EDGES.md 6.2 records ``retract_edge`` getting
    exactly that wrong and it is the second time this repository has seen the bug. No new
    warning value: INTERFACE.md 5.4's existing one, on one more carrier.
    """
    registry = make_registry(adapter)
    action_family(registry, "search_tasks")
    borrowed = make_registry(
        DegradedAdapter(
            adapter,
            transaction_scope="savepoint",
            why={
                "transaction_scope": "the connection is the host's",
                "edge_transaction_scope": "the connection is the host's",
                "action_transaction_scope": "the connection is the host's",
            },
        )
    )
    out = borrowed.record_invocation(
        "search_tasks",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
    )
    assert any(w.startswith("not_durable_until_host_commits") for w in out.warnings), (
        out.warnings
    )
    report = borrowed.invocations()
    assert not [
        w for w in report.warnings if w.startswith("not_durable_until_host_commits")
    ], "a READ is not a write, and a signal that never turns off is noise"


def test_c19_43_the_action_flags_default_false_so_an_older_adapter_claims_no_store(
    adapter, make_registry
):
    """Rule **8-5**. An adapter written against the eighteen-primitive protocol claims no
    invocation store.

    Defaulting ``True`` would make every pre-6b adapter claim one, and this package would
    then call ``put_invocation`` on an object without the method. The
    ``action_store_absent`` refusal is the honest answer for a backend that predates this
    row, and it is what the default produces -- the same load-bearing choice EDGES.md 6
    made for its four, one row along.
    """
    minimal = Capabilities(
        enforces_unique_name=True,
        transactional=True,
        stores_proposals=True,
        stores_events=True,
        stores_attributes=True,
        stores_aliases=True,
        indexes_membership=True,
        counts_usage=True,
        timestamps_usage=True,
        owns_schema=True,
        why={
            "stores_edges": "a type registry only",
            "stores_invocations": "a type registry only",
        },
    )
    assert minimal.stores_invocations is False
    assert minimal.stores_invocation_events is False
    assert minimal.indexes_invocations_by_family is False
    assert minimal.action_transaction_scope == "owned"
    assert minimal.action_store_shares_connection is True
    assert minimal.missing_why() == ()


# --------------------------------------------------------- 10 the tool-slot ceiling
#
# **[Observed 2026-08-29, beacon at `a895a872`]** the numbers this section is built on,
# re-derived rather than cited by `docs/tools/actions_beacon_probe.py`: a provider cap of
# **128**, an effective budget of **127** (`MAX_TOOLS_PER_REQUEST - 1`, twice, because
# the array also carries `finalize_reply`), **222** action modules in **19** categories,
# and `task_detail` summing to exactly the budget -- common **45** + task **48** +
# project **21** + person **13** = **127**. beacon's own source says what that costs: *"a
# 49th `task` tool evicts `person` outright... a bad trade, and a silent one."*
#
# These ids use those counts as a FIXTURE rather than re-measuring beacon, because a
# contract test may not depend on another repository being checked out. The probe
# re-derives them from the pinned tree; this asserts the arithmetic reproduces.

_BEACON = {"common": 45, "task": 48, "project": 21, "person": 13}
_BUDGET = 127


def _beacon_families(registry, extra_task: int = 0) -> None:
    """beacon's four busiest categories, as families in this registry. Read-only about
    beacon: nothing in that repository is imported, executed or written."""
    for group, count in _BEACON.items():
        for i in range(count + (extra_task if group == "task" else 0)):
            action_family(registry, f"{group}_{i:03d}", reachability=[group])


@NEEDS_ATTRIBUTES
def test_c19_20_with_no_order_the_registry_answers_counts_and_nothing_else(
    adapter, make_registry
):
    """Rule **10-2**, and it is 10.2's rule made STRUCTURAL rather than promised.

    > The registry never decides which families reach a surface. That is the host's,
    > always.

    So with ``order=None`` the report carries ``counts`` only, and **``order_source is
    None`` is the marker** -- not ``complete``, which is ``False`` on *every* projection
    for the independent reason in rule 10-5. **The one question this layer most obviously
    COULD have answered -- which 128? -- is the one it is built to be unable to answer.**
    """
    registry = make_registry(adapter)
    action_family(registry, "a1", reachability=["task"])
    action_family(registry, "a2", reachability=["common"])
    out = registry.projection("task_detail", budget=_BUDGET)
    assert out.order_source is None, "the MARKER"
    assert out.counts == {"task": 1, "common": 1}
    assert out.fits == () and out.would_evict == () and out.over_by == 0
    assert out.admitted == {}
    assert out.complete is False
    assert "does not choose" in out.why_incomplete

    # And `complete=False` is NOT the marker, because it is False either way.
    ordered = registry.projection("task_detail", budget=_BUDGET, order=("task", "common"))
    assert ordered.complete is False and ordered.order_source == "caller"


@NEEDS_ATTRIBUTES
def test_c19_21_counts_is_rule_independent_under_every_permutation(adapter, make_registry):
    """Rule **10-3**. A family declaring two ordered groups is counted in **both** and
    charged to **one**, and ``counts`` is identical under every permutation of ``order``.

    **Round 1 found `counts` changing with the order** -- ``{alpha: 2, beta: 2}``
    unordered, ``{alpha: 2, beta: 1}`` under one order and the mirror image under the
    other -- which made 10.4's *"the useful half of this call is the counting"* rest on a
    guarantee that did not hold. **No design test found it, because [Observed] beacon's
    `ActionSpec.category` is a single string**, so the fixture the section was built from
    cannot exercise it. This one can.
    """
    import itertools

    registry = make_registry(adapter)
    action_family(registry, "both_a", reachability=["alpha", "beta"])
    action_family(registry, "both_b", reachability=["alpha", "beta"])

    seen = []
    for order in itertools.permutations(("alpha", "beta")):
        out = registry.projection("s", budget=10, order=order)
        seen.append(out.counts)
        assert sum(out.admitted.values()) == 2, "each family is CHARGED once"
        assert out.admitted[order[0]] == 2 and out.admitted[order[1]] == 0
    assert all(counts == {"alpha": 2, "beta": 2} for counts in seen), seen


@NEEDS_ATTRIBUTES
def test_c19_22_greedy_whole_group_admits_groups_whole_in_the_callers_order(
    adapter, make_registry
):
    """Rule **10-4**. Groups are admitted **whole**, in the caller's order, while
    ``used + len(group) <= budget - reserved``.

    **Whole groups, because that is what the only observed host does.** **[Observed]**
    beacon's `_select_categories_for_context` *"bounds it by dropping whole
    categories"*, and its exclusions are written in exactly those terms. A report
    computed under a rule the host does not use would be worse than no report -- and the
    rule is LABELLED so a caller can see that it is one (ruling **R42**: it stays one
    host's convention for v0, because `counts` is rule-independent).
    """
    registry = make_registry(adapter)
    for i in range(3):
        action_family(registry, f"big_{i}", reachability=["big"])
    action_family(registry, "small_0", reachability=["small"])

    out = registry.projection("s", budget=3, order=("big", "small"))
    assert out.rule == "greedy_whole_group"
    assert out.fits == ("big",) and out.would_evict == ("small",)
    assert out.over_by == 1

    # `reserved` comes off the budget before the arithmetic, not after.
    reserved = registry.projection("s", budget=4, order=("big", "small"), reserved=1)
    assert reserved.fits == ("big",) and reserved.would_evict == ("small",)

    everything = registry.projection("s", budget=4, order=("big", "small"))
    assert everything.fits == ("big", "small") and everything.over_by == 0


@NEEDS_ATTRIBUTES
def test_c19_23_consumers_at_risk_can_never_be_a_complete_casualty_list(
    adapter, make_registry
):
    """Rule **10-5**. ``consumers_at_risk`` inherits ``ConsumerReport.complete == False``.

    INTERFACE.md 5.1 makes that field **always `false`** in v0, so this is a list of
    *known* casualties and never the list of *all* of them, ``complete`` on the report
    inherits the ``false``, and **a caller printing this number without the caveat is
    making a claim this document did not authorise.**

    **[Observed]** beacon registers no consumers in this registry, so on UC1's own
    fixture the list is EMPTY -- and *an empty `consumers_at_risk` is
    `ConsumerReport.complete == False` wearing a different name*, which is the sentence
    11.3's T1.9 exists to force somebody to write down.
    """
    registry = make_registry(adapter)
    seed(registry, "commentable", kind="predicate")
    for i in range(2):
        action_family(registry, f"evicted_{i}", reachability=["gone"])
    action_family(registry, "kept", reachability=["stays"])

    out = registry.projection("s", budget=1, order=("stays", "gone"))
    assert out.would_evict == ("gone",)
    assert out.complete is False
    assert "ConsumerReport.complete" in out.why_incomplete
    assert out.consumers_at_risk == (), (
        "empty, and the empty is the point: it reads as `no casualties` and is not"
    )


@NEEDS_ATTRIBUTES
def test_c19_24_a_projection_over_an_entirely_unknown_vocabulary_is_refused(
    adapter, make_registry
):
    """Rule **10-6**. An ``order`` naming only groups no family carries is refused with
    ``action_family_unknown``, not answered with an empty report.

    A projection over an entirely unknown vocabulary is a **typo**, and an empty report
    for a typo is mechanism C committed by the call that exists to surface it.

    And a MIX is not a typo: unknown groups appear in ``counts`` with ``0`` and
    ``complete`` goes ``False`` with a ``why``, because a host legitimately assembles a
    context from groups that happen to be empty today.
    """
    registry = make_registry(adapter)
    action_family(registry, "real", reachability=["task"])
    refusal = registry.projection("s", budget=10, order=("nonesuch", "alsonot"))
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "action_family_unknown"
    assert refusal.detail["why"].strip()

    mixed = registry.projection("s", budget=10, order=("task", "nonesuch"))
    assert not isinstance(mixed, Refusal)
    assert mixed.counts == {"task": 1, "nonesuch": 0}
    assert mixed.complete is False
    assert "nonesuch" in mixed.why_incomplete


@NEEDS_ATTRIBUTES
def test_c19_25_the_ceiling_is_a_providers_and_budget_has_no_default(
    adapter, make_registry
):
    """Rule **10-7**. The **128** is a provider's, and this registry neither enforces nor
    assumes it -- ``budget`` is a caller's argument **with no default**.

    **[Observed, beacon spec §10.7]** the comment above the constant names OpenAI and
    Gemini's OpenAI-compat endpoint as both rejecting a larger array, and beacon's own
    document is careful that *"binds every live route"* is an inference with one
    unverified link. This section inherits the caution rather than restating the claim
    more confidently than its source -- so **no number from that measurement is in this
    package's code at all.**
    """
    import inspect

    registry = make_registry(adapter)
    signature = inspect.signature(registry.projection)
    assert signature.parameters["budget"].default is inspect.Parameter.empty, (
        "a default budget would be this registry assuming a provider's cap"
    )
    with pytest.raises(TypeError):
        registry.projection("s")

    action_family(registry, "one", reachability=["task"])
    # Any budget at all, including an absurd one, is the caller's to name.
    assert registry.projection("s", budget=1, order=("task",)).fits == ("task",)
    assert registry.projection("s", budget=0, order=("task",)).would_evict == ("task",)
    assert registry.projection("s", budget=10_000, order=("task",)).over_by == 0


@NEEDS_ATTRIBUTES
def test_c19_53_known_is_what_the_report_selected_and_not_the_size_of_the_registry(
    adapter, make_registry
):
    """Rule **10-8**. ``known`` is the number of families this report **selected**.

    A ``known`` that meant *the size of the registry* would answer a question nobody
    asked, in a report whose whole subject is a bounded selection -- and it would move
    every time an unrelated family was registered somewhere else.
    """
    registry = make_registry(adapter)
    action_family(registry, "in_order", reachability=["task"])
    action_family(registry, "out_of_order", reachability=["billing"])
    action_family(registry, "no_surface", reachability=[])
    seed(registry, "not_an_action", kind="entity")

    out = registry.projection("s", budget=10, order=("task",))
    assert out.known == 1, "one family SELECTED, out of three action families"


@NEEDS_ATTRIBUTES
def test_c19_54_a_host_with_no_surfaces_gets_zeroes_rather_than_a_typo_refusal(
    adapter, make_registry
):
    """Rule **10-9**, and it is **the part of this document the venture's own customer
    deletes**, misfiring on that customer.

    **[Observed, round 2]** four ingestion families declared with ``reachability=()``
    produced ``counts={}`` and a projection over the host's own surface name **refused as
    a typo** -- rule 10-6 firing on a host that simply has no surfaces. An ingestion
    pipeline has no chat surface, no tool array and no provider cap.

    So the typo judgement requires that **some** family somewhere declares a surface at
    all; and it is made against **every registered family**, not against the
    ``namespace``-filtered pool, because an empty *namespace* is a legitimate scope where
    an unknown *group* is a misspelling. Round 1 found the filtered version refusing a
    real projection over an empty namespace.
    """
    registry = make_registry(adapter)
    for i in range(4):
        action_family(registry, f"ingest_{i}", reachability=[])

    out = registry.projection("catalogue_ingest", budget=10, order=("catalogue_ingest",))
    assert not isinstance(out, Refusal), "a host with no surfaces is not a typo"
    assert out.counts == {"catalogue_ingest": 0}
    assert out.known == 0

    # An empty NAMESPACE is a legitimate scope, judged against every registered family.
    action_family(registry, "elsewhere", reachability=["task"], namespace="dpr")
    scoped = registry.projection("s", budget=10, order=("task",), namespace="default")
    assert not isinstance(scoped, Refusal), "an empty namespace answers with zeroes"
    assert scoped.counts == {"task": 0}


@NEEDS_ATTRIBUTES
def test_c19_58_a_repeated_group_is_charged_once_and_fits_never_intersects_evicted(
    adapter, make_registry
):
    """Rule **10-10**. A group repeated in ``order`` is charged **once**, so ``fits`` and
    ``would_evict`` can never intersect.

    Round 2 found ``order`` typed as a ``Sequence`` with no uniqueness rule, and a
    duplicated group charged twice and appearing in **both** sets -- a pair rule 10-4
    defines as disjoint. De-duplicated, first occurrence winning, because that is the
    position the caller's own order gives it.
    """
    registry = make_registry(adapter)
    for i in range(2):
        action_family(registry, f"t_{i}", reachability=["task"])
    action_family(registry, "c_0", reachability=["common"])

    out = registry.projection("s", budget=2, order=("task", "common", "task"))
    assert set(out.fits) & set(out.would_evict) == set(), (out.fits, out.would_evict)
    assert out.fits == ("task",) and out.would_evict == ("common",)
    assert sum(out.admitted.values()) == 3, "each FAMILY charged once, not each mention"
    assert list(out.counts) == ["task", "common"], "first occurrence wins"


@NEEDS_ATTRIBUTES
def test_c19_59_beacons_own_arithmetic_reproduces_through_projection(
    adapter, make_registry
):
    """**UC1, design test T1.7, driven through the SHIPPED registry.**

    `projection("task_detail", budget=127, order=("common","task","project","person"))`
    over beacon's real counts -> ``counts`` = 45 / 48 / 21 / 13, all four in ``fits``,
    ``over_by=0``. Then a **49th** ``task`` family -> ``would_evict=("person",)``,
    ``over_by=1``.

    **beacon's own comment, reproduced arithmetically rather than quoted:** *"a 49th
    `task` tool evicts `person` outright, so shipping a `reorder_subtasks` ActionSpec
    would trade 'chat can reorder sub-tasks' for 'chat can no longer add a person to this
    task' -- a bad trade, and a silent one."* **[Observed]** two routes are excluded from
    that product on this arithmetic alone.

    This is mechanism **C** with a number attached: a new family is invisible on a
    surface that had no room for it, and the invisibility is silent -- `FINDINGS-0.1`'s
    incident shape with a provider cap playing the allowlist.
    """
    registry = make_registry(adapter)
    _beacon_families(registry)
    order = ("common", "task", "project", "person")
    out = registry.projection("task_detail", budget=_BUDGET, order=order)
    assert out.counts == _BEACON
    assert sum(_BEACON.values()) == _BUDGET, "the busiest page sits AT the budget"
    assert out.fits == order and out.would_evict == () and out.over_by == 0

    action_family(registry, "task_the_49th", reachability=["task"])
    tipped = registry.projection("task_detail", budget=_BUDGET, order=order)
    assert tipped.counts["task"] == 49
    assert tipped.would_evict == ("person",), tipped.would_evict
    assert tipped.over_by == 1


@NEEDS_INVOCATIONS
def test_c19_60_the_override_census_is_a_floor_the_store_can_actually_compute(
    adapter, make_registry
):
    """**ACTIONS.md 4's one measurement, and round 2 found it returning zero.**

    ``invocations(gate_verdict="refused", outcome="applied")`` is the query 4 offers in
    place of enforcement, and `VISION.md` §7's proposed first deliverable (**Q48**) is a
    monthly signed census of exactly it. ``gate_verdict``, ``effect_undeclared`` and
    ``unreviewed`` were on the facade and on **no primitive** -- so on a pinned
    **2,399-dataset** ledger with one override at row 1,200 the query returned **zero
    rows**, ``complete=False``.

    **A floor of zero is not a conservative measurement; it is the wrong one, and it is
    indistinguishable from a clean deployment.** The three filters with no push-down were
    exactly the three governance reads. This drives the same shape at a size that would
    have returned zero before the push-down: the override sits past the default
    ``limit``, and the query still finds it.
    """
    registry = make_registry(adapter)
    action_family(registry, "ingest_dataset")
    for i in range(120):
        registry.record_invocation(
            "ingest_dataset",
            {},
            actor="derived:catalogue_rule",
            outcome="applied",
            gate_verdict="allowed",
            approved_by="auto:auto",
        )
    registry.record_invocation(
        "ingest_dataset",
        {},
        actor="ai:reaper",
        outcome="applied",
        gate_verdict="refused",
    )
    census = registry.invocations(gate_verdict="refused", outcome="applied")
    assert census.known == 1, (
        "the override is past the default limit and the filter is pushed down; a floor "
        "of zero here is indistinguishable from a clean deployment"
    )
    assert census.complete is False, "it is a FLOOR, and the report says so"
    assert census.invocations[0].provenance.created_by_actor == "ai:reaper"


@NEEDS_INVOCATIONS
def test_c19_11_an_undeclared_effect_warns_on_a_KEPT_record_and_never_refuses(
    adapter, make_registry
):
    """Rule **2.5-6**, and it is the departure from this row's own brief, recorded rather
    than quietly taken.

    The brief for row #6 offered ``effect_undeclared`` as a candidate
    ``Refusal.reason``. Driving UC1 through the model moved it, and the argument is the
    one 2.5 gives twice: **if `record_invocation` REFUSED a report because the host
    observed an effect the family had not declared, this registry would be destroying the
    only evidence that the undeclared effect happened.** Refusing to record what already
    occurred is the worst available answer, and it is the failure shape of a
    `register_consumer` that quietly no-ops.

    So: **declaration time** -- an op outside the four, or one of the six governance
    calls -> `Refusal(reason="effect_not_permitted")` (C19-06, C19-07). **Record time** --
    an observed effect not in the declared set -> the invocation **is recorded**,
    `outcome` is whatever the host reports, and the record carries
    `warnings: ["effect_undeclared:<op>:<target>"]`, which
    `invocations(effect_undeclared=True)` enumerates. That is the move
    `list_types(unverified_semantics=True)` makes for a proposal nobody cited.

    **[Observed]** `delete_person` in beacon deletes one row, and **fifteen foreign keys
    reference `people.id`** -- 7 `ON DELETE CASCADE`, 6 `SET NULL`, and 2 with no
    `ondelete` clause at all. Its `prompt_docs` says *"Not reversible via undo."*, and
    its declared surface says nothing about the other fourteen tables. A registry that
    refused the report would leave that invisible.

    Its own id rather than an assertion inside C19-33, because the two rules make
    different claims: 3-5 is about the SHAPE of the comparison (surplus warns, subset does
    not) and this is about the CONSEQUENCE (the record survives, and is enumerable).
    """
    registry = make_registry(adapter)
    action_family(
        registry,
        "delete_person",
        reversibility="irreversible",
        approval_mode="human",
        effects=[Effect(op="host_state", why="deletes the person row")],
    )
    undeclared = [
        Effect(op="host_state", why="cascades seven foreign keys"),
        Effect(op="host_state", why="nulls six more"),
        Effect(op="host_state", why="connection_service.unlink COMMITS before the delete"),
    ]
    out = registry.record_invocation(
        "delete_person",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="user:sd",
        observed_effects=[Effect(op="host_state", why="deletes the person row"), *undeclared],
    )
    assert not isinstance(out, Refusal), "refusing DESTROYS the only evidence"
    assert out.outcome == "applied", "the record is KEPT"
    warned = [w for w in out.warnings if w.startswith("effect_undeclared:")]
    assert len(warned) == 3, warned
    for effect in undeclared:
        assert any(effect.why in w for w in warned), effect

    # ...and every one of them is one query away, which is what makes the warning worth
    # more than a log line.
    census = registry.invocations(effect_undeclared=True)
    assert census.known == 1
    assert census.invocations[0].invocation_id == out.invocation_id
    assert registry.invocations(effect_undeclared=False).known == 0
