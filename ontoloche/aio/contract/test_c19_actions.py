# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c19_actions.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

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
from ontoloche.actions import (
    APPROVAL_MODES,
    EdgeRef,
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
    parse_ref,
    ref_key,
)
from ontoloche.aio.adapter import ACTION_CAPABILITY_FLAGS, CAPABILITY_FLAGS, Capabilities
from ontoloche.edges import InstanceRef, TypeRef
from ontoloche.errors import NotSupported, UnknownType
from ontoloche.policy import TierOrder
from ontoloche.types import REFUSAL_REASONS, Evidence, Proposal, Refusal, TypeEntry
from ontoloche.aio.contract._support import action_family, edge_family, seed
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter


EVIDENCE = [Evidence(kind="data", summary="the C19 fixture")]

NEEDS_ATTRIBUTES = pytest.mark.requires_capability("stores_attributes")

NEEDS_INVOCATIONS = pytest.mark.requires_capability(
    "stores_attributes", "stores_invocations"
)

NO_EDGES = {
    "stores_edges": "this backend is a type registry only; no table holds relationships"
}

NO_INVOCATIONS = {
    "stores_invocations": "this backend is a type registry only; no table holds invocations"
}

async def _propose(registry, name, attributes, *, kind="action", namespace="default"):
    """The FIRST door. Returns whatever `propose_type` returned -- a `Refusal` when a
    declaration rule bit, a `Proposal` or `TypeEntry` when it did not."""
    return await registry.propose_type(
        name,
        f"the {name} action, for the purposes of this test",
        EVIDENCE,
        "user:sd",
        kind=kind,
        namespace=namespace,
        attributes=attributes,
    )

async def _import(registry, name, attributes, *, kind="action", namespace="default"):
    """The THIRD door. `import_types` returns entries and cannot return a `Refusal`, so
    a breach comes back as `import_refused:<reason>` with nothing written."""
    return (await registry.import_types(
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
    ))[0]

async def _refused_at_every_door(registry, name, attributes, reason):
    """Rule 2.2-4, as one assertion. Every declaration rule binds at all three doors."""
    first = await _propose(registry, f"{name}_a", attributes)
    assert isinstance(first, Refusal), f"propose_type wrote {first!r}"
    assert first.reason == reason, first
    assert first.detail.get("why", "").strip(), "a refusal a caller can act on"

    entry = await _import(registry, f"{name}_c", attributes)
    assert f"import_refused:{reason}" in entry.warnings, entry.warnings
    return first

@NEEDS_ATTRIBUTES
async def test_c19_26_a_bare_kind_action_entry_is_legal_and_is_not_refused(adapter, make_registry):
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
    registry = await make_registry(adapter)
    entry = await seed(registry, "search_tasks", kind="action")
    assert entry.kind == "action"
    assert entry.status == "active"

    # And with the eight keys present but empty -- which is what a host that has not
    # decided yet writes. Still legal, still not a declared family.
    entry = await seed(registry, "list_tasks", kind="action", attributes=action_attributes())
    family = ActionFamily.from_attributes(
        entry.name, entry.namespace, dict(entry.attributes or {}), entry.status
    )
    assert not family.declared

@NEEDS_ATTRIBUTES
async def test_c19_27_a_partial_declaration_must_declare_both_required_keys_from_closed_sets(
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
    registry = await make_registry(adapter)

    # `reachability` alone makes this a declaration, and the two required keys are then
    # required. This is the round-2 hole, asserted.
    await _refused_at_every_door(
        registry,
        "reach_only",
        {"reachability": ["task_detail"]},
        "attributes_schema_violation",
    )

    for key, bad in (("reversibility", "undoable"), ("approval_mode", "quorum")):
        attributes = action_attributes(reversibility="reversible", approval_mode="auto")
        attributes[key] = bad
        refusal = await _refused_at_every_door(
            registry, f"bad_{key}", attributes, "attributes_schema_violation"
        )
        assert refusal.detail["field"] == key
        assert refusal.detail["got"] == bad

    # Missing entirely is the same refusal: there is no default, because a family that
    # does not say is a family whose gate cannot be set.
    for key in ("reversibility", "approval_mode"):
        attributes = action_attributes(reversibility="reversible", approval_mode="auto")
        attributes[key] = None
        await _refused_at_every_door(
            registry, f"missing_{key}", attributes, "attributes_schema_violation"
        )

    assert REVERSIBILITY == ("reversible", "compensable", "irreversible")
    assert APPROVAL_MODES == ("auto", "review", "human")

@NEEDS_ATTRIBUTES
async def test_c19_28_irreversible_forces_human_and_returns_r18s_own_refusal_value(
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
    registry = await make_registry(adapter)
    for mode in ("auto", "review"):
        refusal = await _refused_at_every_door(
            registry,
            f"delete_person_{mode}",
            action_attributes(reversibility="irreversible", approval_mode=mode),
            "attributes_schema_violation",
        )
        assert refusal.detail["reversibility"] == "irreversible"
        assert refusal.detail["approval_mode"] == mode

    # NARROWED, not banned: irreversible + human is the whole point of the rule, and a
    # guard that refuses everything passes a checker that only tests refusals.
    entry = await action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )
    assert isinstance(entry, TypeEntry)
    assert entry.attributes["approval_mode"] == "human"

@NEEDS_ATTRIBUTES
async def test_c19_44_every_declaration_rule_binds_at_all_three_doors(adapter, make_registry):
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
    from ontoloche.aio.adapter import ProposalRecord

    registry = await make_registry(adapter)
    if not registry.caps.stores_proposals:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_proposals=False, so there is "
            "no pending proposal for the `approve` door to be asked about. The other two "
            "doors are asserted by C19-27, C19-28, C19-07 and C19-48 on every leg."
        )

    breaching = action_attributes(reversibility="irreversible", approval_mode="auto")
    await _refused_at_every_door(registry, "predates", breaching, "attributes_schema_violation")

    # The `approve` door, with a proposal whose stored attributes breach the rule --
    # exactly what a proposal written before the rule landed looks like.
    proposal = await _propose(
        registry,
        "predates_rule",
        action_attributes(reversibility="reversible", approval_mode="auto"),
    )
    assert isinstance(proposal, Proposal), proposal
    record = await registry.adapter.get_proposal(proposal.id)
    await registry.adapter.put_proposal(
        ProposalRecord(**{**record.__dict__, "attributes": breaching})
    )
    out = await registry.approve(proposal.id, "user:sd")
    assert isinstance(out, Refusal), f"the approve door wrote {out!r}"
    assert out.reason == "attributes_schema_violation"

    # And the entry is not there: a refused declaration writes nothing at any door.
    assert await registry.adapter.get_type("default", "predates_a", kind="action") is None
    assert await registry.adapter.get_type("default", "predates_c", kind="action") is None

@NEEDS_ATTRIBUTES
async def test_c19_01_the_precondition_vocabulary_is_closed_at_four(adapter, make_registry):
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
    registry = await make_registry(adapter)
    assert PRECONDITION_KINDS == (
        "type_active",
        "predicate_holds",
        "edge_exists",
        "edge_absent",
    )
    refusal = await _refused_at_every_door(
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
async def test_c19_03_a_precondition_why_is_required_and_non_empty(adapter, make_registry):
    """Rule **2.4-3**, on PACKAGE.md 5.2's reasoning for `FieldSpec.description` and
    INTERFACE.md 2.1's for a non-empty `definition`.

    An undescribed condition is how an escape hatch re-forms one level down. **A
    precondition nobody can read is a precondition nobody will ever delete when it stops
    being true.**
    """
    registry = await make_registry(adapter)
    for empty in ("", "   "):
        await _refused_at_every_door(
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
    entry = await action_family(
        registry,
        "with_why",
        inputs=[InputSpec("a", "type")],
        preconditions=[Precondition("type_active", "a", "the word must still be live")],
    )
    assert entry.attributes["preconditions"][0]["why"]

@NEEDS_ATTRIBUTES
async def test_c19_45_a_precondition_naming_no_input_is_refused_at_declaration(
    adapter, make_registry
):
    """Rule **2.4-6**. *The precondition door is shut where the effect door is.*

    A `subject` or `object` naming neither an `InputSpec` nor a literal identity ref, a
    `predicate_holds` with no `predicate`, an edge condition with no `family`: each is a
    DECLARATION error, not a runtime unknown indistinguishable from a degraded backend.
    Found by round 1, which noticed that the effect door was shut and this one was not.
    """
    registry = await make_registry(adapter)
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
        await _refused_at_every_door(
            registry,
            label,
            action_attributes(preconditions=[condition], **base),
            "attributes_schema_violation",
        )

    # A LITERAL identity ref is legal and is recognisable by its triple -- 2.4's own
    # words, *"the InputSpec.name this is about, OR a literal ref"*.
    entry = await action_family(
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

@NEEDS_ATTRIBUTES
async def test_c19_06_the_effect_vocabulary_is_closed_at_four_operations(adapter, make_registry):
    """Rule **2.5-1**. A fifth operation is refused at declaration with
    `effect_not_permitted`.

    `attributes_schema_violation` is about a schema's field TYPES; this is a rule about
    the vocabulary of one field's VALUES, and §7 argues the difference: nothing in the
    twenty-one said *"you may not declare that"*.
    """
    registry = await make_registry(adapter)
    assert EFFECT_OPS == ("add_edge", "retract_edge", "propose_type", "host_state")
    refusal = await _refused_at_every_door(
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
async def test_c19_07_the_six_governance_calls_may_never_be_an_effect(adapter, make_registry):
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
    registry = await make_registry(adapter)
    assert set(GOVERNANCE_CALLS) == {
        "approve",
        "reject",
        "retire",
        "reinstate",
        "merge_types",
        "register_consumer",
    }
    for call in GOVERNANCE_CALLS:
        refusal = await _refused_at_every_door(
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
        assert await registry.adapter.get_type("default", f"gov_{call}_a", kind="action") is None
        assert await registry.adapter.get_type("default", f"gov_{call}_c", kind="action") is None

@NEEDS_ATTRIBUTES
async def test_c19_08_an_action_may_propose_and_only_a_human_or_a_policy_may_approve(
    adapter, make_registry
):
    """Rule **2.5-3**. `propose_type` IS in the vocabulary, precisely so the line has a
    legal side.

    *An action may PROPOSE; only a human, or an auto-policy a deployment set
    deliberately, may APPROVE.* An ingestion action meeting a new word may say so, and
    what it says is a request -- which is the whole proposal->approval loop applied one
    level up.
    """
    registry = await make_registry(adapter)
    entry = await action_family(
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
async def test_c19_09_a_host_state_effect_requires_a_non_empty_why(adapter, make_registry):
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
    registry = await make_registry(adapter)
    for empty in ("", "  "):
        await _refused_at_every_door(
            registry,
            f"silent_host_state_{len(empty)}",
            action_attributes(
                reversibility="irreversible",
                approval_mode="human",
                effects=[Effect(op="host_state", why=empty)],
            ),
            "effect_not_permitted",
        )

    entry = await action_family(
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
async def test_c19_10_the_effect_exclusion_binds_at_declaration_not_only_at_invocation(
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
    registry = await make_registry(adapter)
    breaching = action_attributes(
        reversibility="reversible",
        approval_mode="auto",
        effects=[Effect(op="merge_types")],
    )
    await _refused_at_every_door(registry, "reconcile_borough", breaching, "effect_not_permitted")
    listing = await registry.list_types(kind="action", include_retired=True)
    assert not [e for e in listing.types if e.name.startswith("reconcile_borough")]

    clean = await action_family(registry, "reconcile_borough", effects=[])
    assert isinstance(clean, TypeEntry)

@NEEDS_ATTRIBUTES
async def test_c19_12_an_effect_naming_an_unregistered_edge_family_is_refused(
    adapter, make_registry
):
    """Rule **2.5-7**. `edge_family_unknown` -- EDGES.md 4.3's EXISTING value, not a new
    one.

    An effect that may `add_edge` on a family nobody registered has declared a blast
    radius the registry cannot check against anything, which is the same failure
    `edge_family_unknown` already names one layer down. Minting a second value for it
    would be INTERFACE.md 2.3's Cause B.

    This is the one declaration rule that is not pure -- it needs the store -- so it
    lives on `AsyncRegistry` rather than in `actions.family_declaration_problem`, and it is
    asserted at the doors like every other.
    """
    registry = await make_registry(adapter)
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
    refusal = await _refused_at_every_door(
        registry, "flag_facility", attributes, "edge_family_unknown"
    )
    assert refusal.detail["family"] == "flagged_for_review"

    # Register the family, and the identical declaration is accepted. The guard is
    # narrowed, not banned -- refusing everything passes a checker that tests refusals.
    await edge_family(registry, "flagged_for_review", level="instance")
    entry = await action_family(
        registry,
        "flag_facility_ok",
        effects=[Effect(op="add_edge", family="flagged_for_review", namespace="default")],
    )
    assert isinstance(entry, TypeEntry)

@NEEDS_ATTRIBUTES
async def test_c19_48_a_propose_type_effect_must_name_a_kind_from_an_allowlist(
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
    `AsyncRegistry`. `C10-09` pins the guard downstream; this pins the door upstream.
    """
    registry = await make_registry(adapter)
    assert PROPOSABLE_KINDS == ("entity", "edge", "value_set")

    for label, effect in (
        ("predicate", Effect(op="propose_type", namespace="default", kind="predicate")),
        ("omitted", Effect(op="propose_type", namespace="default")),
        ("verb", Effect(op="propose_type", namespace="default", kind="action")),
        ("no_namespace", Effect(op="propose_type", kind="entity")),
    ):
        refusal = await _refused_at_every_door(
            registry,
            f"mint_{label}",
            action_attributes(
                reversibility="reversible", approval_mode="auto", effects=[effect]
            ),
            "effect_not_permitted",
        )
        assert refusal.detail["op"] == "propose_type"

    for kind in PROPOSABLE_KINDS:
        entry = await action_family(
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

@NEEDS_ATTRIBUTES
async def test_c19_13_approval_mode_is_closed_at_three_values(adapter, make_registry):
    """Rule **5.2-1**. A family declaring a fourth is refused at declaration.

    A fourth value -- a two-person rule, a quorum -- is a policy language arriving one
    value at a time, and 15.2 records the recommendation: make `approved_by` a list
    before making the mode vocabulary bigger. Not taken; no fixture needs it.
    """
    registry = await make_registry(adapter)
    refusal = await _refused_at_every_door(
        registry,
        "two_person",
        action_attributes(reversibility="reversible", approval_mode="two_person"),
        "attributes_schema_violation",
    )
    assert refusal.detail["field"] == "approval_mode"
    for mode in APPROVAL_MODES:
        entry = await action_family(registry, f"mode_{mode}", approval_mode=mode)
        assert entry.attributes["approval_mode"] == mode

@NEEDS_ATTRIBUTES
async def test_c19_19_reachability_values_are_opaque_strings_the_registry_never_interprets(
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
    registry = await make_registry(adapter)
    entry = await action_family(
        registry, "cross_agency", reachability=["catalogue_console", "任意のサーフェス"]
    )
    assert entry.attributes["reachability"] == ["catalogue_console", "任意のサーフェス"]

    silent = await action_family(registry, "ingest_dataset", reachability=[])
    assert silent.attributes["reachability"] == []

    for bad in ([""], ["  "], [None], [7]):
        await _refused_at_every_door(
            registry,
            f"bad_reach_{len(str(bad))}",
            action_attributes(
                reversibility="reversible", approval_mode="auto", reachability=bad
            ),
            "attributes_schema_violation",
        )

@NEEDS_ATTRIBUTES
async def test_c19_02_each_precondition_kind_is_answered_by_a_call_that_already_exists(
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
    registry = await make_registry(adapter)
    await seed(registry, "facility", kind="entity")
    await seed(registry, "commentable", kind="predicate")
    if registry.caps.stores_edges:
        await edge_family(registry, "cites", level="instance")
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
        await action_family(
            registry,
            f"eval_{kind}",
            inputs=[InputSpec("a", "type"), InputSpec("b", "type", required=False)],
            preconditions=[condition],
        )
        out = await registry.preflight(
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
async def test_c19_04_a_precondition_that_does_not_hold_names_the_failing_condition(
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
    registry = await make_registry(adapter)
    await seed(registry, "facility", kind="entity")
    await seed(registry, "commentable", kind="predicate")
    facility = TypeRef("default", "entity", "facility")
    await action_family(
        registry,
        "needs_commentable",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition("predicate_holds", "a", "only commentable things", predicate="commentable")
        ],
    )
    out = await registry.preflight("needs_commentable", {"a": facility}, actor="user:sd")
    assert out.verdict == "refused"
    assert out.refusal.reason == "precondition_unmet"
    # One value, TWO states, and the states are in `detail` rather than in two words --
    # `endpoint_kind_mismatch`'s own precedent. `state` was added by round 1, without
    # which a caller cannot tell a real miss from a backend that could not look.
    assert out.refusal.detail["state"] == "false"
    assert out.refusal.detail["kind"] == "predicate_holds"
    assert out.refusal.detail["subject"] == "a"
    assert out.preconditions[0].holds is False

async def test_c19_05_an_unknown_precondition_is_none_plus_a_why_and_is_never_satisfied(
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
    registry = await make_registry(adapter)
    if not registry.caps.stores_attributes:
        pytest.skip(
            "ACTIONS.md 2.2 puts the eight declared keys in `TypeEntry.attributes`, so a "
            "backend that stores no arbitrary attributes cannot DECLARE a family at all "
            "-- the escape hatch is PACKAGE.md 5.7's `attribute_projections`, and this "
            "leg names one key rather than eight. C19-39 asserts the invocation-store "
            "half of Rule U on this leg without needing a declaration."
        )
    await seed(registry, "facility", kind="entity")
    facility = InstanceRef(TypeRef("default", "entity", "facility"), "1")
    await action_family(
        registry,
        "needs_edge",
        inputs=[InputSpec("a", "instance"), InputSpec("b", "instance")],
        preconditions=[
            Precondition("edge_exists", "a", "must already cite", family="cites", object="b")
        ],
    )
    blind = await make_registry(
        AsyncDegradedAdapter(adapter, stores_edges=False, why=NO_EDGES)
        if registry.caps.stores_edges
        else adapter
    )
    out = await blind.preflight("needs_edge", {"a": facility, "b": facility}, actor="user:sd")
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
async def test_c19_46_a_preconditions_namespace_is_the_familys_and_reaches_neighbors(
    adapter, make_registry
):
    """Rule **2.4-7**. ``Precondition.namespace`` is the **family's**, and the edge kinds
    pass it to ``neighbors``, which has no default for it.

    ``AsyncRegistry.neighbors`` makes ``namespace`` keyword-only **without** a default
    *precisely because ``"default"`` is a wrong answer nobody notices* -- UC3's whole
    subject. **The printed shape omitted this field until round 1**, while the probe kit
    had silently added it: *"fixed only in the throwaway probe kit"*, which is the
    failure row 4b names and which that row reproduced **inside the document that quotes
    it**. Two readings of the missing field gave OPPOSITE verdicts on UC3's own fixture
    -- one found the edge, the other returned `edge_family_unknown`.
    """
    registry = await make_registry(adapter)
    if not registry.caps.stores_edges:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_edges=False, so there is no "
            "edge for a namespaced family to be found in. C19-05 is the subject for the "
            "declined capability itself."
        )
    await seed(registry, "borough", kind="value_set", namespace="dpr")
    await seed(registry, "boro", kind="value_set", namespace="oti_311")
    await edge_family(
        registry,
        "equivalent_to_x",
        level="type",
        namespace="dpr",
        src_kinds=("value_set",),
        dst_kinds=("value_set",),
    )
    a = TypeRef("dpr", "value_set", "borough")
    b = TypeRef("oti_311", "value_set", "boro")
    await registry.add_edge("equivalent_to_x", a, b, "user:sd", namespace="dpr")

    for label, ns, expected in (("the family's", "dpr", True), ("the default", "default", None)):
        await action_family(
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
        out = await registry.preflight(f"reconcile_{ns}", {"a": a, "b": b}, actor="user:sd")
        assert out.preconditions[0].holds is expected, f"{label}: {out.preconditions[0]}"

@NEEDS_ATTRIBUTES
async def test_c19_47_the_edge_kinds_search_both_directions_and_are_conservative(
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
    registry = await make_registry(adapter)
    if not registry.caps.stores_edges:
        pytest.skip(
            "PACKAGE.md 3.2 -- stores_edges=False; there is no edge to have a direction."
        )
    await seed(registry, "task", kind="entity")
    await edge_family(registry, "blocks", level="instance", inverse_label="blocked_by")
    one = InstanceRef(TypeRef("default", "entity", "task"), "1")
    two = InstanceRef(TypeRef("default", "entity", "task"), "2")
    await registry.add_edge("blocks", two, one, "user:sd")  # the edge runs b -> a

    await action_family(
        registry,
        "link_tasks",
        inputs=[InputSpec("a", "instance"), InputSpec("b", "instance")],
        preconditions=[
            Precondition("edge_absent", "a", "do not link twice", family="blocks", object="b")
        ],
    )
    out = await registry.preflight("link_tasks", {"a": one, "b": two}, actor="user:sd")
    assert out.preconditions[0].holds is False, (
        "the walk is direction='both', so an edge running b -> a makes edge_absent(a, b) "
        "FALSE -- conservative, and stated rather than sharpened"
    )
    assert out.verdict == "refused"
    assert out.refusal.detail["state"] == "false"

@NEEDS_ATTRIBUTES
async def test_c19_55_an_input_determined_namespace_is_a_declaration_not_an_omission(
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
    registry = await make_registry(adapter)
    if not (registry.caps.stores_invocations and registry.caps.stores_edges):
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declines the invocation store or the edge "
            "store, and this rule is about an EFFECT compared against a RECORD."
        )
    await seed(registry, "dataset", kind="entity", namespace="dpr")
    await edge_family(registry, "same_tax_lot", level="instance")
    await action_family(
        registry,
        "ingest_dataset",
        effects=[Effect(op="add_edge", family="same_tax_lot", namespace=None)],
        inputs=[InputSpec("row", "instance")],
    )
    row = InstanceRef(TypeRef("dpr", "entity", "dataset"), "uvpi-gqnh")

    right = await registry.record_invocation(
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

    wrong = await registry.record_invocation(
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

@NEEDS_INVOCATIONS
async def test_c19_29_declared_effects_are_copied_from_the_family_at_invocation_time(
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
    registry = await make_registry(adapter)
    await edge_family(registry, "stakes", level="instance") if registry.caps.stores_edges else None
    effects = (
        [Effect(op="add_edge", family="stakes", namespace="default")]
        if registry.caps.stores_edges
        else [Effect(op="host_state", why="writes a row this protocol does not model")]
    )
    await action_family(registry, "add_stake", effects=effects)
    invocation = await registry.record_invocation(
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
    await registry.import_types(
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
        for i in (await registry.invocations()).invocations
        if i.invocation_id == invocation.invocation_id
    ][0]
    assert len(again.declared_effects) == 1, (
        "the RECORD's declaration is the one the gate judged, not the one the family now "
        "carries -- rule 3-1's whole subject"
    )

@NEEDS_INVOCATIONS
async def test_c19_30_gate_verdict_has_three_values_and_not_asked_is_one_of_them(
    adapter, make_registry
):
    """Rule **3-2**. ``not_asked`` is a real and common state, and ``False`` would say
    *the gate refused* -- a different and much worse claim.

    A host may record an invocation it ran without consulting ``preflight`` at all. Rule
    U, on a three-state field.
    """
    registry = await make_registry(adapter)
    assert GATE_VERDICTS == ("allowed", "refused", "not_asked")
    await action_family(registry, "search_tasks")
    for verdict in GATE_VERDICTS:
        out = await registry.record_invocation(
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
        await registry.record_invocation(
            "search_tasks", {}, actor="user:sd", outcome="applied", gate_verdict="maybe"
        )

@NEEDS_INVOCATIONS
async def test_c19_31_approved_by_is_never_fabricated_and_never_null_where_the_gate_decided(
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
    registry = await make_registry(adapter)
    await action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )

    # The gate was not asked, and the host claims a policy approved it anyway.
    lied = await registry.record_invocation(
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
    gate = await registry.preflight("delete_person", {}, actor="user:sd", approved_by="user:sd")
    assert gate.verdict == "allowed"
    honest = await registry.record_invocation(
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
async def test_c19_32_a_refused_outcome_requires_a_refusal_from_the_closed_vocabulary(
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
    registry = await make_registry(adapter)
    assert OUTCOMES == ("applied", "refused", "failed", "compensated")
    assert "pending" not in OUTCOMES
    await action_family(registry, "search_tasks")
    with pytest.raises(ValueError):
        await registry.record_invocation(
            "search_tasks", {}, actor="user:sd", outcome="refused", gate_verdict="refused"
        )
    out = await registry.record_invocation(
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
        await registry.record_invocation(
            "search_tasks", {}, actor="user:sd", outcome="pending", gate_verdict="allowed"
        )

@NEEDS_INVOCATIONS
async def test_c19_33_a_surplus_effect_warns_and_a_subset_warns_nothing(adapter, make_registry):
    """Rule **3-5**, and the asymmetry is deliberate.

    ``observed ⊄ declared`` warns per surplus effect and the record is **kept** -- 2.5's
    argument: refusing to record what already occurred destroys the only evidence that
    the undeclared effect happened. ``observed ⊊ declared`` warns **nothing**: a
    permission is not a promise, and warning on an unused permission would train hosts to
    declare narrowly and amend often, which is worse than declaring broadly and being
    measured.
    """
    registry = await make_registry(adapter)
    declared = [
        Effect(op="host_state", why="deletes the person row"),
        Effect(op="host_state", why="cascades eleven foreign keys"),
    ]
    await action_family(
        registry,
        "delete_person",
        reversibility="irreversible",
        approval_mode="human",
        effects=declared,
    )
    subset = await registry.record_invocation(
        "delete_person",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="user:sd",
        observed_effects=[declared[0]],
    )
    assert not [w for w in subset.warnings if w.startswith("effect_undeclared:")]

    surplus = await registry.record_invocation(
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
    assert (await registry.invocations(effect_undeclared=True)).known == 1

@NEEDS_INVOCATIONS
async def test_c19_56_the_copy_is_taken_from_what_the_gate_judged(adapter, make_registry):
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
    registry = await make_registry(adapter)
    if not registry.caps.stores_events:
        pytest.skip(
            "PACKAGE.md 3.2 -- stores_events=False, and ACTIONS.md 3.1's generation is "
            "counted from the append-only log rather than stored twice, so this backend "
            "cannot tell one declaration from another. It therefore never emits "
            "`declaration_amended` rather than emitting it wrongly -- Rule U."
        )
    narrow = [Effect(op="host_state", why="writes one row")]
    await action_family(registry, "ingest", effects=narrow)
    gate = await registry.preflight("ingest", {}, actor="user:sd")
    assert gate.verdict == "allowed"

    await registry.import_types(
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
    out = await registry.record_invocation(
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
async def test_c19_57_declared_policy_carries_the_four_facts_that_decide_a_verdict(
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
    registry = await make_registry(adapter)
    await action_family(
        registry,
        "flag_facility",
        min_auto_tier="sonnet",
        inputs=[InputSpec("a", "type")],
        preconditions=[Precondition("type_active", "a", "the scale must still be live")],
    )
    facility = TypeRef("default", "entity", "facility")
    await seed(registry, "facility", kind="entity")
    gate = await registry.preflight("flag_facility", {"a": facility}, actor="ai:c", tier="opus")
    assert gate.verdict == "allowed"
    out = await registry.record_invocation(
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

@NEEDS_ATTRIBUTES
async def test_c19_14_human_mode_refuses_an_approver_the_registry_cannot_recognise(
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
    registry = await make_registry(adapter)
    await action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )
    for impostor in (None, "", "bot:reaper", "svc:cleanup", "AI:bot", "agent:claude",
                     "nobody", "ai:reaper", "auto:nightly", "derived:rule", "user:"):
        out = await registry.preflight(
            "delete_person", {}, actor="ai:reaper", approved_by=impostor
        )
        assert out.verdict == "refused", f"{impostor!r} was accepted as a person"
        assert out.refusal.reason == "human_approval_required"
        assert out.approved_by is None

    ok = await registry.preflight("delete_person", {}, actor="ai:reaper", approved_by="user:sd")
    assert ok.verdict == "allowed" and ok.approved_by == "user:sd"

@NEEDS_ATTRIBUTES
async def test_c19_15_a_tier_below_the_floor_refuses_with_state_false(adapter, make_registry):
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
    registry = await make_registry(adapter)
    await action_family(registry, "flag_facility", min_auto_tier="sonnet")
    low = await registry.preflight("flag_facility", {}, actor="ai:haiku_classifier", tier="haiku")
    assert low.verdict == "refused"
    assert low.refusal.reason == "tier_below_action_policy"
    assert low.refusal.detail["state"] == "false"
    assert low.refusal.detail["tier"] == "haiku"
    assert low.refusal.detail["min_auto_tier"] == "sonnet"
    assert low.tier_floor == "sonnet"

    high = await registry.preflight("flag_facility", {}, actor="ai:c", tier="opus")
    assert high.verdict == "allowed"
    assert high.approved_by and high.approved_by.startswith("auto:")

@NEEDS_ATTRIBUTES
async def test_c19_16_no_floor_is_a_legal_configuration_reported_as_a_stated_absence(
    adapter, make_registry
):
    """Rule **5.2-4**. ``min_auto_tier=None`` under ``approval_mode="auto"`` is a
    **legitimate configuration** -- a single-tier deployment has nothing to compare.

    It is **not** a warning value, deliberately: minting one would put a vocabulary entry
    on a correct configuration. What the caller gets instead is Rule U on the report --
    ``tier_floor=None`` with a ``tier_floor_why`` saying so. **The honest surface is a
    stated absence, not an alarm.**
    """
    registry = await make_registry(adapter)
    await action_family(registry, "search_tasks", min_auto_tier=None)
    out = await registry.preflight("search_tasks", {}, actor="user:sd")
    assert out.verdict == "allowed"
    assert out.tier_floor is None
    assert out.tier_floor_why and out.tier_floor_why.strip()
    assert out.refusal is None

@NEEDS_ATTRIBUTES
async def test_c19_17_all_three_unknown_tier_causes_refuse_and_none_of_them_says_false(
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
    registry = await make_registry(adapter)
    await action_family(registry, "flag_facility", min_auto_tier="sonnet")

    no_tier = await registry.preflight("flag_facility", {}, actor="ai:c", tier=None)
    outside = await registry.preflight("flag_facility", {}, actor="ai:c", tier="gpt5")

    orderless = await make_registry(adapter, tier_order=TierOrder(()))
    await action_family(orderless, "flag_facility_x", min_auto_tier="sonnet")
    no_order = await orderless.preflight("flag_facility_x", {}, actor="ai:c", tier="haiku")

    whys = set()
    for label, out in (("no tier", no_tier), ("outside", outside), ("no order", no_order)):
        assert out.verdict == "refused", label
        assert out.refusal.reason == "tier_below_action_policy", label
        assert out.refusal.detail["state"] == "unknown", label
        assert out.refusal.detail["why"].strip(), label
        whys.add(out.refusal.detail["why"])
    assert len(whys) == 3, f"each cause needs its own sentence, got {whys}"

@NEEDS_INVOCATIONS
async def test_c19_18_model_tier_on_an_invocation_is_the_invoking_actors(adapter, make_registry):
    """Rule **5.2-6**. ``InvocationProvenance.model_tier`` is the tier of the **invoking**
    actor, distinct from the family's own ``provenance.model_tier``.

    Those are two different facts about two different objects and both matter: **a family
    proposed by Haiku and invoked by Opus is not the same risk as the reverse.**
    """
    registry = await make_registry(adapter)
    proposal = await registry.propose_type(
        "infer_person_relationships",
        "classifies person pairs and applies the confident ones",
        EVIDENCE,
        "ai:proposer",
        tier="haiku",
        kind="action",
        attributes=action_attributes(reversibility="reversible", approval_mode="auto"),
    )
    entry = proposal if isinstance(proposal, TypeEntry) else await registry.approve(
        proposal.id, "user:sd"
    )
    assert isinstance(entry, TypeEntry), entry
    assert entry.provenance.model_tier == "haiku", "the tier that PROPOSED the verb"

    out = await registry.record_invocation(
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
async def test_c19_50_review_mode_records_a_policy_approval_and_joins_the_review_queue(
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
    registry = await make_registry(adapter)
    if not registry.caps.stores_events:
        pytest.skip(
            "PACKAGE.md 3.2 -- a review IS an event, and this backend keeps none, so "
            "`review_invocation` refuses `cannot_record_override` rather than claiming "
            "a review nothing recorded. Asserted below on the legs that can keep one."
        )
    await action_family(registry, "reconcile_borough", approval_mode="review")
    await action_family(registry, "search_tasks", approval_mode="auto")
    gate = await registry.preflight("reconcile_borough", {}, actor="user:sd")
    assert gate.verdict == "allowed"
    assert gate.approved_by.startswith("auto:"), "a POLICY approved it, and says so"

    out = await registry.record_invocation(
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
    await registry.record_invocation(
        "search_tasks",
        {},
        actor="user:sd",
        outcome="applied",
        gate_verdict="allowed",
        approved_by="auto:auto",
    )
    queue = await registry.invocations(unreviewed=True)
    assert queue.known == 1, [i.family for i in queue.invocations]
    assert queue.invocations[0].family == "reconcile_borough"

    await registry.review_invocation(out.invocation_id, reviewed_by="user:boss")
    assert (await registry.invocations(unreviewed=True)).known == 0
    again = [
        i for i in (await registry.invocations()).invocations if i.invocation_id == out.invocation_id
    ][0]
    assert again.reviewed_at is not None

@NEEDS_ATTRIBUTES
async def test_c19_34_preflight_records_nothing_and_is_idempotent(adapter, make_registry):
    """Rule **6-1**. Calling it N times leaves the invocation store unchanged.

    It is a question, and a host that wants the question answered *and* the answer
    recorded calls ``record_invocation`` with the verdict it received. This matters
    because 12's T2.5 turns on it: a tier-refused ``preflight`` records **nothing**, and
    the host may record the refusal itself with ``outcome="refused"``.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "flag_facility", min_auto_tier="sonnet")
    before = (
        (await registry.invocations()).known if registry.caps.stores_invocations else None
    )
    for _ in range(5):
        await registry.preflight("flag_facility", {}, actor="ai:c", tier="opus")
        await registry.preflight("flag_facility", {}, actor="ai:c", tier="haiku")
    if registry.caps.stores_invocations:
        assert (await registry.invocations()).known == before == 0
    else:
        assert isinstance(await registry.invocations(), Refusal)

@NEEDS_ATTRIBUTES
async def test_c19_35_every_precondition_result_names_the_call_that_answered_it(
    adapter, make_registry
):
    """Rule **6-2**. ``evaluated_by`` is drawn from the closed set ``list_types`` /
    ``predicates`` / ``neighbors``.

    2.4's no-query-language claim, made mechanical. C19-02 asserts the mapping kind by
    kind; this asserts the *closure* -- that no result can name anything else, whatever
    the condition.
    """
    registry = await make_registry(adapter)
    await seed(registry, "facility", kind="entity")
    await seed(registry, "commentable", kind="predicate")
    facility = TypeRef("default", "entity", "facility")
    await action_family(
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
    out = await registry.preflight(
        "many_conditions", {"a": facility, "b": facility}, actor="user:sd"
    )
    assert out.known == 4
    for result in out.preconditions:
        assert result.evaluated_by in EVALUATORS, result

async def test_c19_36_holds_none_is_refused_as_unknown_and_never_treated_as_satisfied(
    adapter, make_registry
):
    """Rule **6-3**. ``holds=None`` is refused, and the refusal's ``detail`` says
    **unknown** rather than **false**; unknown is never treated as satisfied.

    Its own id rather than an assertion inside C19-05, because the two rules are about
    different halves: C19-05 is that a degraded backend PRODUCES the unknown, and this is
    that the gate REFUSES on it. A backend that produced honest unknowns and a gate that
    approved on them would pass one and fail the other.
    """
    registry = await make_registry(adapter)
    if not registry.caps.stores_attributes:
        pytest.skip(
            "ACTIONS.md 2.2 puts the eight keys in `TypeEntry.attributes`; this backend "
            "stores no arbitrary keys, so no family can be declared on it."
        )
    await seed(registry, "facility", kind="entity")
    facility = TypeRef("default", "entity", "facility")
    await action_family(
        registry,
        "needs_unknown_predicate",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition(
                "predicate_holds", "a", "must be searchable", predicate="never_registered"
            )
        ],
    )
    out = await registry.preflight("needs_unknown_predicate", {"a": facility}, actor="user:sd")
    assert out.preconditions[0].holds is None
    assert out.verdict == "refused", "unknown is NEVER satisfied"
    assert out.refusal.detail["state"] == "unknown"
    assert out.complete is False

@NEEDS_INVOCATIONS
async def test_c19_37_record_invocation_does_not_re_evaluate_and_keeps_a_refused_gate(
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
    registry = await make_registry(adapter)
    await seed(registry, "facility", kind="entity")
    facility = TypeRef("default", "entity", "facility")
    await action_family(
        registry,
        "flag_facility",
        inputs=[InputSpec("a", "type")],
        preconditions=[Precondition("type_active", "a", "the word must still be live")],
    )
    gate = await registry.preflight("flag_facility", {"a": facility}, actor="user:sd")
    assert gate.verdict == "allowed"

    # The world moves: the type the precondition required is retired.
    await registry.retire("facility", "superseded", retired_by="user:sd", force=True)

    out = await registry.record_invocation(
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

    override = await registry.record_invocation(
        "flag_facility",
        {"a": facility},
        actor="ai:reaper",
        outcome="applied",
        gate_verdict="refused",
    )
    assert override.outcome == "applied"
    assert "approval_unrecorded" in override.warnings
    floor = await registry.invocations(gate_verdict="refused", outcome="applied")
    assert floor.known == 1
    assert floor.complete is False, "every filtered answer is a FLOOR, not a total"

@NEEDS_INVOCATIONS
async def test_c19_38_the_report_is_a_floor_whenever_a_filter_or_a_limit_bit(
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
    registry = await make_registry(adapter)
    await action_family(registry, "search_tasks")
    for _ in range(3):
        await registry.record_invocation(
            "search_tasks",
            {},
            actor="user:sd",
            outcome="applied",
            gate_verdict="allowed",
            approved_by="auto:auto",
        )
    whole = await registry.invocations()
    assert whole.known == 3 and whole.complete is True

    filtered = await registry.invocations(family="search_tasks")
    assert filtered.known == 3
    assert filtered.complete is False and filtered.why_incomplete.strip()

    bounded = await registry.invocations(limit=2)
    assert bounded.known == 2
    assert bounded.complete is False and bounded.why_incomplete.strip()

@NEEDS_ATTRIBUTES
async def test_c19_51_both_invocation_calls_refuse_a_predicate_ref_whatever_was_declared(
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
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate")
    await seed(registry, "searchable", kind="predicate")
    left = TypeRef("default", "predicate", "commentable")
    right = TypeRef("default", "predicate", "searchable")
    await action_family(
        registry,
        "merge_capabilities",
        inputs=[InputSpec("a", "type", kinds=None), InputSpec("b", "type", kinds=None)],
    )
    gate = await registry.preflight("merge_capabilities", {"a": left, "b": right}, actor="ai:c")
    assert isinstance(gate, Refusal), f"the gate said {gate!r} -- the kill row is open"
    assert gate.reason == "input_kind_mismatch"
    assert gate.detail["problem"] == "predicate"

    if registry.caps.stores_invocations:
        recorded = await registry.record_invocation(
            "merge_capabilities",
            {"a": left, "b": right},
            actor="ai:c",
            outcome="applied",
            gate_verdict="not_asked",
        )
        assert isinstance(recorded, Refusal), "the second door must refuse it too"
        assert recorded.reason == "input_kind_mismatch"
        assert (await registry.invocations()).known == 0, "nothing was written"

    # And the ordinary shape checks bind at the same door.
    await seed(registry, "task", kind="entity")
    task = TypeRef("default", "entity", "task")
    await action_family(
        registry, "narrow", inputs=[InputSpec("a", "type", kinds=("value_set",))]
    )
    assert (await registry.preflight("narrow", {"a": task}, actor="user:sd")).reason == (
        "input_kind_mismatch"
    )
    assert (await registry.preflight("narrow", {}, actor="user:sd")).detail["problem"] == "missing"
    assert (
        (await registry.preflight("narrow", {"z": task}, actor="user:sd")).detail["problem"]
        == "undeclared"
    )

@NEEDS_ATTRIBUTES
async def test_c19_52_a_shipped_call_that_raises_becomes_holds_none_plus_a_why(
    adapter, make_registry
):
    """Rule **6-7**. ``preflight`` never raises where it could return.

    The shipped ``predicates(of=…)`` and ``consumers(…)`` raise ``UnknownType`` for an
    unregistered subject, and a ``predicate_holds`` condition naming one would escape the
    return type entirely. It is **caught** and becomes ``holds=None`` plus a ``why`` --
    Rule U's unknown, which the verdict then refuses. **Round 1 found the escape.**
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate")
    ghost = TypeRef("default", "entity", "never_registered")
    await action_family(
        registry,
        "ph",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            Precondition("predicate_holds", "a", "must be commentable", predicate="commentable")
        ],
    )
    out = await registry.preflight("ph", {"a": ghost}, actor="user:sd")
    assert not isinstance(out, Exception)
    assert out.preconditions[0].holds is None
    assert out.preconditions[0].why.strip()
    assert out.verdict == "refused"

    # And the shipped call really does raise, so the catch is load-bearing rather than
    # defensive. Asserted here so a later change that stops it raising is visible.
    with pytest.raises(UnknownType):
        await registry.predicates(of="never_registered")

async def test_c19_39_no_invocation_store_refuses_rather_than_returning_an_empty_report(
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
    caps = await adapter.capabilities()
    blind = await make_registry(
        AsyncDegradedAdapter(adapter, stores_invocations=False, why=NO_INVOCATIONS)
        if caps.stores_invocations
        else adapter
    )
    outcomes = [
        await blind.record_invocation("f", {}, actor="user:sd", outcome="applied"),
        await blind.invocations(),
        await blind.review_invocation("inv1", reviewed_by="user:sd"),
    ]
    for out in outcomes:
        assert isinstance(out, Refusal), out
        assert out.reason == "action_store_absent"
        assert out.detail["why"].strip(), "the backend's own sentence, surfaced verbatim"

    # `preflight` and `projection` are unaffected: they touch no invocation.
    assert isinstance(await blind.projection("s", budget=10), ProjectionReport)
    assert (await blind.preflight("f", {}, actor="user:sd")).reason == "action_family_unknown"

    # And the primitive underneath raises rather than pretending to store and lose.
    if not caps.stores_invocations:
        with pytest.raises(NotSupported):
            await adapter.find_invocations()

async def test_c19_40_every_false_action_flag_carries_a_why_and_two_are_vacuous(
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
    caps = await adapter.capabilities()
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

async def test_c19_41_two_scopes_on_one_connection_is_non_conformant(adapter, make_registry):
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
    assert (await adapter.capabilities()).scope_conflict() is None

@NEEDS_INVOCATIONS
async def test_c19_42_savepoint_scope_is_stamped_on_the_write_and_not_on_the_read(
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
    registry = await make_registry(adapter)
    await action_family(registry, "search_tasks")
    borrowed = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            transaction_scope="savepoint",
            why={
                "transaction_scope": "the connection is the host's",
                "edge_transaction_scope": "the connection is the host's",
                "action_transaction_scope": "the connection is the host's",
            },
        )
    )
    out = await borrowed.record_invocation(
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
    report = await borrowed.invocations()
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

_BEACON = {"common": 45, "task": 48, "project": 21, "person": 13}

_BUDGET = 127

async def _beacon_families(registry, extra_task: int = 0) -> None:
    """beacon's four busiest categories, as families in this registry. Read-only about
    beacon: nothing in that repository is imported, executed or written."""
    for group, count in _BEACON.items():
        for i in range(count + (extra_task if group == "task" else 0)):
            await action_family(registry, f"{group}_{i:03d}", reachability=[group])

@NEEDS_ATTRIBUTES
async def test_c19_20_with_no_order_the_registry_answers_counts_and_nothing_else(
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
    registry = await make_registry(adapter)
    await action_family(registry, "a1", reachability=["task"])
    await action_family(registry, "a2", reachability=["common"])
    out = await registry.projection("task_detail", budget=_BUDGET)
    assert out.order_source is None, "the MARKER"
    assert out.counts == {"task": 1, "common": 1}
    assert out.fits == () and out.would_evict == () and out.over_by == 0
    assert out.admitted == {}
    assert out.complete is False
    assert "does not choose" in out.why_incomplete

    # And `complete=False` is NOT the marker, because it is False either way.
    ordered = await registry.projection("task_detail", budget=_BUDGET, order=("task", "common"))
    assert ordered.complete is False and ordered.order_source == "caller"

@NEEDS_ATTRIBUTES
async def test_c19_21_counts_is_rule_independent_under_every_permutation(adapter, make_registry):
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

    registry = await make_registry(adapter)
    await action_family(registry, "both_a", reachability=["alpha", "beta"])
    await action_family(registry, "both_b", reachability=["alpha", "beta"])

    seen = []
    for order in itertools.permutations(("alpha", "beta")):
        out = await registry.projection("s", budget=10, order=order)
        seen.append(out.counts)
        assert sum(out.admitted.values()) == 2, "each family is CHARGED once"
        assert out.admitted[order[0]] == 2 and out.admitted[order[1]] == 0
    assert all(counts == {"alpha": 2, "beta": 2} for counts in seen), seen

@NEEDS_ATTRIBUTES
async def test_c19_22_greedy_whole_group_admits_groups_whole_in_the_callers_order(
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
    registry = await make_registry(adapter)
    for i in range(3):
        await action_family(registry, f"big_{i}", reachability=["big"])
    await action_family(registry, "small_0", reachability=["small"])

    out = await registry.projection("s", budget=3, order=("big", "small"))
    assert out.rule == "greedy_whole_group"
    assert out.fits == ("big",) and out.would_evict == ("small",)
    assert out.over_by == 1

    # `reserved` comes off the budget before the arithmetic, not after.
    reserved = await registry.projection("s", budget=4, order=("big", "small"), reserved=1)
    assert reserved.fits == ("big",) and reserved.would_evict == ("small",)

    everything = await registry.projection("s", budget=4, order=("big", "small"))
    assert everything.fits == ("big", "small") and everything.over_by == 0

@NEEDS_ATTRIBUTES
async def test_c19_23_consumers_at_risk_can_never_be_a_complete_casualty_list(
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
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate")
    for i in range(2):
        await action_family(registry, f"evicted_{i}", reachability=["gone"])
    await action_family(registry, "kept", reachability=["stays"])

    out = await registry.projection("s", budget=1, order=("stays", "gone"))
    assert out.would_evict == ("gone",)
    assert out.complete is False
    assert "ConsumerReport.complete" in out.why_incomplete
    assert out.consumers_at_risk == (), (
        "empty, and the empty is the point: it reads as `no casualties` and is not"
    )

@NEEDS_ATTRIBUTES
async def test_c19_24_a_projection_over_an_entirely_unknown_vocabulary_is_refused(
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
    registry = await make_registry(adapter)
    await action_family(registry, "real", reachability=["task"])
    refusal = await registry.projection("s", budget=10, order=("nonesuch", "alsonot"))
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "action_family_unknown"
    assert refusal.detail["why"].strip()

    mixed = await registry.projection("s", budget=10, order=("task", "nonesuch"))
    assert not isinstance(mixed, Refusal)
    assert mixed.counts == {"task": 1, "nonesuch": 0}
    assert mixed.complete is False
    assert "nonesuch" in mixed.why_incomplete

@NEEDS_ATTRIBUTES
async def test_c19_25_the_ceiling_is_a_providers_and_budget_has_no_default(
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

    registry = await make_registry(adapter)
    signature = inspect.signature(registry.projection)
    assert signature.parameters["budget"].default is inspect.Parameter.empty, (
        "a default budget would be this registry assuming a provider's cap"
    )
    with pytest.raises(TypeError):
        await registry.projection("s")

    await action_family(registry, "one", reachability=["task"])
    # Any budget at all, including an absurd one, is the caller's to name.
    assert (await registry.projection("s", budget=1, order=("task",))).fits == ("task",)
    assert (await registry.projection("s", budget=0, order=("task",))).would_evict == ("task",)
    assert (await registry.projection("s", budget=10_000, order=("task",))).over_by == 0

@NEEDS_ATTRIBUTES
async def test_c19_53_known_is_what_the_report_selected_and_not_the_size_of_the_registry(
    adapter, make_registry
):
    """Rule **10-8**. ``known`` is the number of families this report **selected**.

    A ``known`` that meant *the size of the registry* would answer a question nobody
    asked, in a report whose whole subject is a bounded selection -- and it would move
    every time an unrelated family was registered somewhere else.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "in_order", reachability=["task"])
    await action_family(registry, "out_of_order", reachability=["billing"])
    await action_family(registry, "no_surface", reachability=[])
    await seed(registry, "not_an_action", kind="entity")

    out = await registry.projection("s", budget=10, order=("task",))
    assert out.known == 1, "one family SELECTED, out of three action families"

@NEEDS_ATTRIBUTES
async def test_c19_54_a_host_with_no_surfaces_gets_zeroes_rather_than_a_typo_refusal(
    adapter, make_registry
):
    """Rule **10-9**, and it is **the part of this document the venture's own customer
    deletes**, misfiring on that customer.

    **[Observed, round 2]** four ingestion families declared with ``reachability=()``
    produced ``counts={}`` and a projection over the host's own surface name **refused as
    a typo** -- rule 10-6 firing on a host that simply has no surfaces. An ingestion
    pipeline has no chat surface, no tool array and no provider cap.

    So the typo judgement requires that a family declares a surface at all -- and
    **ruling R70, row 6c**, narrows *where it looks* to **this scope**: the
    ``namespace``-filtered pool, not the store-wide one. An empty *namespace* is a
    legitimate scope where an unknown *group* is a misspelling; round 1 of the spec row
    found a filtered version with no such condition refusing a real projection over an
    empty namespace, and ``C19-74`` holds the other direction.
    """
    registry = await make_registry(adapter)
    for i in range(4):
        await action_family(registry, f"ingest_{i}", reachability=[])

    out = await registry.projection("catalogue_ingest", budget=10, order=("catalogue_ingest",))
    assert not isinstance(out, Refusal), "a host with no surfaces is not a typo"
    assert out.counts == {"catalogue_ingest": 0}
    assert out.known == 0

    # An empty NAMESPACE is a legitimate scope: it declares no surface, so it answers
    # with zeroes rather than refusing. Round 1 of the spec row's own finding.
    await action_family(registry, "elsewhere", reachability=["task"], namespace="dpr")
    scoped = await registry.projection("s", budget=10, order=("task",), namespace="default")
    assert not isinstance(scoped, Refusal), "an empty namespace answers with zeroes"
    assert scoped.counts == {"task": 0}

@NEEDS_ATTRIBUTES
async def test_c19_74_a_co_tenants_surface_cannot_make_a_neighbours_projection_a_typo(
    adapter, make_registry
):
    """Rule **10-9** as **ruling R70** narrows it, and the design test that decided it.

    **The defect [Observed, row 6b's Q72, reproduced by row 6c's design test over UC3's
    many-publishers catalogue].** The typo judgement was made against the **store-wide**
    pool, so an ingestion host whose families all declare ``reachability=()`` got zeroes
    while it was **alone** on the store and a **refusal** the moment an unrelated
    co-tenant registered one family with a surface. Nothing about the ingestion host
    changed between the two calls. UC3 is dozens of publishers in one catalogue, so
    *"somebody else's namespace"* is the ordinary condition rather than the exotic one --
    and a rule whose answer depends on data outside the scope it was asked about is
    mechanism **C** committed by the call built to surface it.

    The narrowed rule: *a typo is an ``order`` naming groups no family in **this scope**
    carries, where the scope declared any surface at all.* Both prior readings were
    wrong and each cost a round -- ``C19-54`` holds the empty-namespace direction, this
    id holds the co-tenant direction, and the third assertion holds the half a careless
    fix deletes: **a scope that does use surfaces still catches a misspelling.**
    """
    registry = await make_registry(adapter)
    for i in range(4):
        await action_family(registry, f"ingest_dataset_{i}", reachability=[], namespace="dpr")

    alone = await registry.projection(
        "catalogue_ingest", budget=10, order=("catalogue_ingest",), namespace="dpr"
    )
    assert not isinstance(alone, Refusal), "a host with no surfaces is not a typo"
    assert alone.counts == {"catalogue_ingest": 0}

    # A CO-TENANT registers a surfaced family. Nothing about `dpr` changed.
    await action_family(
        registry, "close_311_request", reachability=["catalogue_console"],
        namespace="oti_311",
    )
    after = await registry.projection(
        "catalogue_ingest", budget=10, order=("catalogue_ingest",), namespace="dpr"
    )
    assert not isinstance(after, Refusal), (
        "a co-tenant's surface is out of scope and cannot make this a typo"
    )
    assert after.counts == alone.counts, "the same call gives the same answer"

    # ...and the half a careless fix deletes: a scope that DOES use surfaces still
    # catches a misspelling.
    typo = await registry.projection(
        "console", budget=10, order=("catalogue_consle",), namespace="oti_311"
    )
    assert isinstance(typo, Refusal) and typo.reason == "action_family_unknown"

@NEEDS_ATTRIBUTES
async def test_c19_58_a_repeated_group_is_charged_once_and_fits_never_intersects_evicted(
    adapter, make_registry
):
    """Rule **10-10**. A group repeated in ``order`` is charged **once**, so ``fits`` and
    ``would_evict`` can never intersect.

    Round 2 found ``order`` typed as a ``Sequence`` with no uniqueness rule, and a
    duplicated group charged twice and appearing in **both** sets -- a pair rule 10-4
    defines as disjoint. De-duplicated, first occurrence winning, because that is the
    position the caller's own order gives it.
    """
    registry = await make_registry(adapter)
    for i in range(2):
        await action_family(registry, f"t_{i}", reachability=["task"])
    await action_family(registry, "c_0", reachability=["common"])

    out = await registry.projection("s", budget=2, order=("task", "common", "task"))
    assert set(out.fits) & set(out.would_evict) == set(), (out.fits, out.would_evict)
    assert out.fits == ("task",) and out.would_evict == ("common",)
    assert sum(out.admitted.values()) == 3, "each FAMILY charged once, not each mention"
    assert list(out.counts) == ["task", "common"], "first occurrence wins"

@NEEDS_ATTRIBUTES
async def test_c19_59_beacons_own_arithmetic_reproduces_through_projection(
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
    registry = await make_registry(adapter)
    await _beacon_families(registry)
    order = ("common", "task", "project", "person")
    out = await registry.projection("task_detail", budget=_BUDGET, order=order)
    assert out.counts == _BEACON
    assert sum(_BEACON.values()) == _BUDGET, "the busiest page sits AT the budget"
    assert out.fits == order and out.would_evict == () and out.over_by == 0

    await action_family(registry, "task_the_49th", reachability=["task"])
    tipped = await registry.projection("task_detail", budget=_BUDGET, order=order)
    assert tipped.counts["task"] == 49
    assert tipped.would_evict == ("person",), tipped.would_evict
    assert tipped.over_by == 1

@NEEDS_INVOCATIONS
async def test_c19_60_the_override_census_is_a_floor_the_store_can_actually_compute(
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
    registry = await make_registry(adapter)
    await action_family(registry, "ingest_dataset")
    for i in range(120):
        await registry.record_invocation(
            "ingest_dataset",
            {},
            actor="derived:catalogue_rule",
            outcome="applied",
            gate_verdict="allowed",
            approved_by="auto:auto",
        )
    await registry.record_invocation(
        "ingest_dataset",
        {},
        actor="ai:reaper",
        outcome="applied",
        gate_verdict="refused",
    )
    census = await registry.invocations(gate_verdict="refused", outcome="applied")
    assert census.known == 1, (
        "the override is past the default limit and the filter is pushed down; a floor "
        "of zero here is indistinguishable from a clean deployment"
    )
    assert census.complete is False, "it is a FLOOR, and the report says so"
    assert census.invocations[0].provenance.created_by_actor == "ai:reaper"

@NEEDS_INVOCATIONS
async def test_c19_11_an_undeclared_effect_warns_on_a_KEPT_record_and_never_refuses(
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
    registry = await make_registry(adapter)
    await action_family(
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
    out = await registry.record_invocation(
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
    census = await registry.invocations(effect_undeclared=True)
    assert census.known == 1
    assert census.invocations[0].invocation_id == out.invocation_id
    assert (await registry.invocations(effect_undeclared=False)).known == 0

@NEEDS_INVOCATIONS
async def test_c19_61_every_filter_is_re_applied_above_the_store(adapter, make_registry):
    """**BLOCKING, round 1.** `invocations(family=X)` returned invocations of OTHER
    families on a backend declaring `indexes_invocations_by_family=False`.

    §8's table says that flag leaves *"correctness unchanged -- the registry filters above
    the store"*. It did not filter: the family went down to the primitive and nothing came
    back up. The shipped `AsyncDegradedAdapter` **drops** the family filter on such a backend,
    modelling `find_edges`' deliberate deviation from `find_types`' rule -- and that
    deviation is only sound because a `find_edges` query is **already bounded by
    `incident_to`** and `neighbors` narrows above it. **A ledger read has no such bound.**

    **[Observed]** six rows returned for a family with one, five of them a different
    family, `known=6`, in the one query §4 asks an operator to act on and `VISION.md` §7's
    proposed first deliverable (**Q48**) is a monthly signed census of.

    Every filter is re-applied above the store now, not just the one the reference double
    drops -- which answers `C0-10`'s question at this surface (*can a BROKEN backend
    PASS?*) for all of them: a backend that silently ignores `outcome` or `since` can no
    longer make this call return a wrong answer, only a slow one.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "wanted")
    await action_family(registry, "noise")
    blind = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            indexes_invocations_by_family=False,
            why={"indexes_invocations_by_family": "the host's audit table has no family column"},
        )
    )
    for _ in range(5):
        await blind.record_invocation(
            "noise", {}, actor="user:sd", outcome="applied",
            gate_verdict="allowed", approved_by="auto:auto",
        )
    await blind.record_invocation(
        "wanted", {}, actor="ai:c", outcome="failed", gate_verdict="not_asked",
    )

    report = await blind.invocations(family="wanted")
    assert {i.family for i in report.invocations} == {"wanted"}, (
        "the registry filters ABOVE the store, or `indexes_invocations_by_family=False` "
        "is not a performance declaration but a correctness one"
    )
    assert report.known == 1
    # ...and the same holds for every other filter. (`registry` and `blind` sit on ONE
    # store, which is the point: the degraded wrapper takes a capability away and adds
    # no data, so the same six rows are read through both.)
    assert (await blind.invocations(outcome="failed")).known == 1
    assert (await blind.invocations(actor="ai:c")).known == 1
    assert (await blind.invocations(gate_verdict="allowed")).known == 5

@NEEDS_INVOCATIONS
async def test_c19_62_the_backward_pointer_is_an_indexed_lookup_and_not_a_walk(
    adapter, make_registry
):
    """**BLOCKING in round 1, and BLOCKING AGAIN in round 2 — one cause, three defects.**

    ACTIONS.md §9 stores only the FORWARD pointer, because the compensating invocation is
    written after the one it compensates and a store never rewrites a row
    (INTERFACE.md §5.8), so the façade derives the backward one. **The first cut derived
    it by WALKING the ledger, bounded**, and every round found a different face of that:

    * **round 1** — past the bound it returned a bare ``None``, so a compensated
      invocation read back ``outcome="applied"``. *The ledger reported the wrong OUTCOME*,
      in the field §2.6 says **is** the mechanism for `compensable`;
    * **round 1's fix** returned ``(id, why)`` and wired the sentence into
      ``invocations()`` — and **round 2** found the second call site,
      ``review_invocation``, destructuring the sentence into ``_why`` and dropping it. *A
      fix is only as good as its application*, which is the eighth kill-row trip's own
      sentence about a published key;
    * **round 2** also measured the walk: it ran **once per returned row**, at
      O(limit × ledger) — **200,020 row reads for twenty returned rows** on a 10,070-row
      ledger, and 1,000,000 at the default `limit=100`.

    **Pushing the question down removes all three at once**, which is why the fix is a
    primitive and not a fourth patch: there is no bound to lie about, no sentence to drop
    and no walk. `find_invocations(compensates=…)` is an indexed equality on a column the
    store already holds — and it is round 2 of the SPEC row's own finding one derivation
    along, where *the three filters with no push-down were exactly the three governance
    reads*.

    This drives it past the size the old bound sat at, through **both** call sites.
    """
    from ontoloche.aio.adapter import InvocationRecord

    registry = await make_registry(adapter)
    await action_family(registry, "f")
    await action_family(registry, "undo")
    original = await registry.record_invocation(
        "f", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )

    # Padding written straight through primitive 19, so the compensator is far past where
    # a bounded walk would have stopped looking.
    for i in range(10_200):
        await registry.adapter.put_invocation(
            InvocationRecord(
                invocation_id=f"pad{i:06d}",
                namespace="default",
                family="f",
                created_by_actor="user:sd",
            )
        )
    compensator = await registry.record_invocation(
        "undo", {}, actor="user:sd", outcome="applied", gate_verdict="allowed",
        approved_by="auto:auto", compensates=original.invocation_id,
    )

    # Call site 1 -- the listing.
    listed = [
        i for i in (await registry.invocations(family="f", limit=5)).invocations
        if i.invocation_id == original.invocation_id
    ]
    assert listed, "the original is in the first page, ordered by created_at"
    assert listed[0].outcome == "compensated", (
        "the ledger must not report `applied` for an invocation that was compensated -- "
        "that is the field 2.6 says IS the mechanism for `compensable`"
    )
    assert listed[0].compensated_by == compensator.invocation_id

    # Call site 2 -- `review_invocation`, which round 1's fix did not visit.
    if registry.caps.stores_events and registry.caps.stores_invocation_events:
        reviewed = await registry.review_invocation(
            original.invocation_id, reviewed_by="user:boss"
        )
        assert not isinstance(reviewed, Refusal), reviewed
        assert reviewed.outcome == "compensated", (
            "one registry may not answer two ways about one invocation, and a fix "
            "applied at one call site out of two is how the eighth trip happened"
        )
        assert reviewed.compensated_by == compensator.invocation_id

    # An invocation nothing compensates is a FACT, not an unknown, and says nothing.
    assert await registry._compensated_by(compensator.invocation_id, "default") is None

@NEEDS_ATTRIBUTES
async def test_c19_63_a_payload_schema_is_keyed_apart_from_the_familys_own_eight_keys(
    adapter, make_registry
):
    """**BLOCKING, round 1** -- and it is deviation **D-4c-1** reproduced by the row that
    inherited the mechanism.

    §2.7 says `payload_schema` names an `AttributeSchema` keyed
    `(namespace, "action", <family name>)`, and that *"this one is not inert"*. **That is
    exactly the key ruling R10 already gave the name-level schema governing the family's
    OWN eight declaration keys.** One key, two dicts.

    Contortion **ACT1** predicted it in the abstract -- *"it works because the two objects
    never share a store, which is a fact OUTSIDE the mechanism"* -- and they do share one,
    `oo_attr_schema`. **[Observed]** registering the schema made the family
    **unregisterable**: `propose_type(kind="action")` refused
    `attributes_schema_violation` with every one of the eight declaration keys reported
    *"not declared in the schema"*. *The family became undeclarable by the act of
    governing its own inputs.*

    A schema kind of its own separates the two spaces with no new table, no new primitive
    and no possible collision -- `edges.EDGE_PAYLOAD_KIND` one kind along.
    """
    from ontoloche.actions import ACTION_PAYLOAD_KIND
    from ontoloche.attributes import AttributeSchema, FieldSpec

    registry = await make_registry(adapter)
    if registry._attribute_store() is None:
        pytest.skip(
            "PACKAGE.md 5 -- the AsyncAttributeStore extension is optional (ruling R2) and "
            "this backend declines it, so no schema can be registered to collide."
        )
    assert ACTION_PAYLOAD_KIND != "action", "the collision is the key being the same one"

    await registry.register_attribute_schema(
        AttributeSchema(
            namespace="default",
            kind=ACTION_PAYLOAD_KIND,
            name="close_ticket",
            version=1,
            fields={"ticket": FieldSpec(type="str", description="the ticket id", required=True)},
            mode="enforce",
        )
    )
    entry = await action_family(registry, "close_ticket", payload_schema="close_ticket")
    assert isinstance(entry, TypeEntry), (
        "governing a family's INPUTS must not make the family undeclarable"
    )

    if not registry.caps.stores_invocations:
        pytest.skip(
            "PACKAGE.md 3.2 -- the DECLARATION half above is this test's subject and ran "
            "on this leg; the second half needs the invocation store 8's first flag "
            "declares, and `record_invocation` refuses `action_store_absent` before any "
            "schema is consulted (rule 8-1)."
        )

    # ...and the schema is live rather than inert: it governs the INVOCATION's inputs.
    refusal = await registry.record_invocation(
        "close_ticket", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "attributes_schema_violation"
    assert any("ticket" in v for v in refusal.detail["violations"]), refusal.detail

@NEEDS_INVOCATIONS
async def test_c19_64_omitting_judged_is_recorded_rather_than_silent(adapter, make_registry):
    """**MAJOR, round 1.** `record_invocation(judged=…)` is optional and its ABSENCE was
    silent.

    Rule **3-7** copies the declaration and the policy the GATE judged. A host that asked
    the gate and then reports **without** handing that back gets the family's CURRENT
    declaration copied onto the record -- which is what rule 3-1 says it prevents, and
    round 2 of the spec row watched an undeclared `retract_edge` laundered into the ledger
    through exactly that window.

    **[Observed]** the same invocation, the same family widened between the two calls:
    with `judged=` it files `declaration_amended:1:2` **and** an `effect_undeclared`;
    without it, a **clean row**. Nothing said the guarantee had been dropped.

    A host that never asked the gate is not warned -- there was no judgement to hand back,
    and warning there would put a vocabulary entry on the honest `not_asked` path §4 exists
    to keep legal. `declaration_unjudged` is the thirty-third warning value, added to
    INTERFACE.md §5.4 in this change per ruling **R3**.
    """
    registry = await make_registry(adapter)
    if not registry.caps.stores_events:
        pytest.skip(
            "PACKAGE.md 3.2 -- stores_events=False, so ACTIONS.md 3.1's generation "
            "cannot be counted and `declaration_amended` is never emitted. The warning "
            "asserted here is about the ABSENCE of `judged=`, which is orthogonal, but "
            "the fixture's second half needs the generation to move."
        )
    await action_family(registry, "ingest", effects=[Effect(op="host_state", why="writes a row")])
    gate = await registry.preflight("ingest", {}, actor="user:sd")

    honest = await registry.record_invocation(
        "ingest", {}, actor="user:sd", outcome="applied", gate_verdict="allowed",
        approved_by=gate.approved_by, judged=gate,
    )
    assert "declaration_unjudged" not in honest.warnings

    silent = await registry.record_invocation(
        "ingest", {}, actor="user:sd", outcome="applied", gate_verdict="allowed",
        approved_by=gate.approved_by,
    )
    assert "declaration_unjudged" in silent.warnings, silent.warnings

    # A host that never asked the gate is NOT warned: there was nothing to hand back.
    never = await registry.record_invocation(
        "ingest", {}, actor="ai:reaper", outcome="applied", gate_verdict="not_asked",
    )
    assert "declaration_unjudged" not in never.warnings

@NEEDS_ATTRIBUTES
async def test_c19_65_the_no_floor_sentence_is_about_auto_mode_and_says_so(
    adapter, make_registry
):
    """**MAJOR, round 1.** `tier_floor_why` said *"every tier auto-approves"* on families
    no tier can auto-approve.

    §5.2 mints that sentence for `min_auto_tier=None` **under `approval_mode="auto"`**,
    where it is Rule U's honest stated absence. It was emitted unconditionally -- so on
    the `irreversible`/`human` `delete_person`, **the exact class §2.2's cross-field rule
    exists to make un-auto-approvable**, the report said every tier auto-approves it.

    Rule U's own failure mode, one turn along: not a confident answer to the question, a
    confident answer to a *different* question.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "search_tasks", approval_mode="auto")
    await action_family(
        registry, "delete_person", reversibility="irreversible", approval_mode="human"
    )
    await action_family(registry, "reconcile", approval_mode="review")

    auto = await registry.preflight("search_tasks", {}, actor="user:sd")
    assert "every tier auto-approves" in auto.tier_floor_why

    human = await registry.preflight("delete_person", {}, actor="ai:c", approved_by="user:sd")
    assert human.tier_floor is None
    assert "auto-approves" not in human.tier_floor_why, human.tier_floor_why
    assert "human" in human.tier_floor_why

    review = await registry.preflight("reconcile", {}, actor="user:sd")
    assert "auto-approves" not in review.tier_floor_why, review.tier_floor_why

@NEEDS_INVOCATIONS
async def test_c19_66_an_undrainable_review_queue_says_why(adapter, make_registry):
    """**MAJOR, round 1.** `invocations(unreviewed=True)` implies *awaiting review*, and on
    a backend that cannot keep an `invocation_reviewed` event nothing can ever leave.

    Rule **8-2** requires a `False` flag's sentence to be surfaced *"wherever a result
    would otherwise imply a fact"*. The queue answered `known=1, complete=False` with
    `why_incomplete` saying only *"a filter suppressed rows"* -- true, and not the fact a
    caller needed: **every row is unreviewed by construction there**, forever, and
    `review_invocation` refuses `cannot_record_override`.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "reconcile", approval_mode="review")
    eventless = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            stores_invocation_events=False,
            why={"stores_invocation_events": "the host owns the schema and has no event table"},
        )
    )
    out = await eventless.record_invocation(
        "reconcile", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )
    assert not isinstance(out, Refusal), out

    queue = await eventless.invocations(unreviewed=True)
    assert queue.complete is False
    assert "never LEAVE" in queue.why_incomplete or "unreviewed by construction" in (
        queue.why_incomplete or ""
    ), queue.why_incomplete

    refusal = await eventless.review_invocation(out.invocation_id, reviewed_by="user:boss")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override", refusal

@NEEDS_INVOCATIONS
async def test_c19_67_a_payload_schema_naming_nothing_is_not_the_same_as_naming_none(
    adapter, make_registry
):
    """**MAJOR, round 1.** A family naming a schema nobody registered was byte-identical,
    on the record, to a family naming none.

    That is ruling **R34**'s inert `payload_schema` arriving back through the *absence* of
    a warning: `attr_schema_version=None` and empty `warnings` in both cases, so nothing a
    caller reads distinguishes *governed by a schema that is not in force* from *not
    governed*. EDGES.md §2.5 minted `payload_schema_unregistered` for exactly this fact one
    kind along -- **reused rather than re-minted**, because a second value for one fact is
    INTERFACE.md §2.3's Cause B.

    Rule U in one value: *the payload was not validated, and here is the name nobody
    registered.*
    """
    registry = await make_registry(adapter)
    await action_family(registry, "named", payload_schema="no_such_schema_anywhere")
    await action_family(registry, "unnamed", payload_schema=None)

    named = await registry.record_invocation(
        "named", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )
    unnamed = await registry.record_invocation(
        "unnamed", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )
    warned = [w for w in named.warnings if w.startswith("payload_schema_unregistered:")]
    assert warned == ["payload_schema_unregistered:no_such_schema_anywhere"], named.warnings
    assert not [
        w for w in unnamed.warnings if w.startswith("payload_schema_unregistered:")
    ], "a family that names NO schema is not missing one"

@NEEDS_ATTRIBUTES
async def test_c19_68_a_declared_predicates_filter_is_answered_above_a_store_that_drops_it(
    adapter, make_registry
):
    """**MAJOR, round 2.** `invocations(unreviewed=False)` answered `known=0` on the
    fully capable leg with a row that belonged in the answer.

    The `unreviewed` filter is **half** pushed down: the store applies
    `NOT EXISTS(invocation_reviewed)`, and the half asking whether the FAMILY is in
    `review` mode stays above it. For `unreviewed=True` the store's half is a
    **narrowing** of the façade's predicate and the arrangement is sound. For `False` it
    is not: the answer to *"which invocations are NOT awaiting review?"* is *every
    auto-mode row plus every reviewed review-mode row*, and the store's `EXISTS` half
    returns only the second -- **dropping the larger half**, which the registry can only
    narrow, never widen.

    Fix 2's guarantee -- *a backend that silently ignores a filter can no longer make
    this call return a WRONG answer, only a slow one* -- holds exactly where the
    push-down narrows. Where it does not, the filter is not pushed at all.
    """
    registry = await make_registry(adapter)
    if not registry.caps.stores_invocations:
        pytest.skip(
            "PACKAGE.md 3.2 -- stores_invocations=False; there is no ledger to filter."
        )
    await action_family(registry, "auto_fam", approval_mode="auto")
    await action_family(registry, "rev_fam", approval_mode="review")
    for family in ("auto_fam", "rev_fam"):
        await registry.record_invocation(
            family, {}, actor="user:sd", outcome="applied",
            gate_verdict="allowed", approved_by="auto:auto",
        )

    assert [i.family for i in (await registry.invocations(unreviewed=True)).invocations] == ["rev_fam"]
    assert [i.family for i in (await registry.invocations(unreviewed=False)).invocations] == [
        "auto_fam"
    ], "an auto-mode invocation is not awaiting review, and the store's half cannot say so"
    assert (await registry.invocations(unreviewed=None)).known == 2

@NEEDS_INVOCATIONS
async def test_c19_69_a_naive_since_is_read_as_utc_rather_than_raising(adapter, make_registry):
    """**MAJOR, round 2**, and a regression fix 2 introduced.

    Re-applying every filter above the store put a Python-side `rec.created_at >= since`
    where none existed before -- and **primitive 21 accepts a naive `since` and answers**
    while the façade raised `TypeError: can't compare offset-naive and offset-aware
    datetimes`. A façade that crashes on a value its own primitive takes is not a
    narrower answer, it is a broken one.

    The registry stores UTC throughout (PACKAGE.md §4.4), so reading a naive value as UTC
    is the same reading every adapter already makes of one.
    """
    from datetime import UTC, datetime

    registry = await make_registry(adapter)
    await action_family(registry, "f")
    await registry.record_invocation(
        "f", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )
    long_ago_naive = datetime(2020, 1, 1)
    long_ago_aware = datetime(2020, 1, 1, tzinfo=UTC)
    assert (await registry.invocations(since=long_ago_naive)).known == 1
    assert (await registry.invocations(since=long_ago_aware)).known == 1
    assert (await registry.invocations(since=datetime(2099, 1, 1))).known == 0

@NEEDS_INVOCATIONS
async def test_c19_70_the_invocation_input_census_enumerates_what_was_written(
    adapter, make_registry
):
    """**MAJOR, round 2.** `attribute_census(kind="action_payload")` answered `keys=[]`
    with **`complete=True`** after an invocation had carried an input.

    `actions.ACTION_PAYLOAD_KIND` justifies the separate schema kind partly on *"it makes
    `attribute_census(kind="action_payload")` the same enumeration for invocation inputs
    that PACKAGE.md 5.5 gives type attributes"* — and nothing called `observe_attributes`
    for them. The edge side has `_observe_edge_payload`; the action side had no twin.

    PACKAGE.md §5.5 calls the census *"the floor that applies even in `off` mode"* and
    argues it on `attributes` accumulating unwatched. **An empty census claiming
    completeness is Rule U's forbidden empty in the one call whose only job is
    enumerating what got written.**
    """
    from ontoloche.edges import TypeRef

    registry = await make_registry(adapter)
    if registry._attribute_store() is None:
        pytest.skip(
            "PACKAGE.md 5.5 -- the AsyncAttributeStore extension is optional (ruling R2) and "
            "this backend declines it, so there is no census to take."
        )
    await seed(registry, "task", kind="entity")
    await action_family(registry, "close_ticket", inputs=[InputSpec("ticket", "type")])
    await registry.record_invocation(
        "close_ticket",
        {"ticket": TypeRef("default", "entity", "task")},
        actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="auto:auto",
    )
    census = await registry.attribute_census(kind="action_payload")
    assert [e.key for e in census.entries] == ["ticket"], census
    assert census.entries[0].example == "default:entity:task"

@NEEDS_ATTRIBUTES
async def test_c19_71_the_kind_on_a_reference_is_a_claim_and_the_stored_row_is_the_fact(
    adapter, make_registry
):
    """**BLOCKING, round 3** — the ACTIONS door's own kill-row walk, alive through a
    mislabelled string.

    `C19-51` closed *"a `kind="predicate"` ref is refused whatever the family declared"*
    — and it closed it against `ref_kind`, which returns
    ``getattr(ref, "kind", None)``: **the kind the CALLER wrote on the reference, never
    checked against the stored row.** So a `TypeRef("default", "entity", "commentable")`
    naming a real capability predicate — or a misspelled `"Predicate"` — walked straight
    past the exclusion, and **[Observed]** `merge_capabilities(commentable, searchable)`
    reached `verdict="allowed"` at `preflight` and was **recorded `applied`** on two live
    predicates.

    That is the **seventh** trip's diagnosis one surface along: *a guard comparing a byte
    where the registry holds a stored fact.* Row 6b hardened `ref_shape` to refuse an
    unrecognised **shape** and left the sibling hole in the **kind** open. §2.3's rule is
    *"the exclusion is general or it is nothing"*, and **a general exclusion cannot rest
    on the caller spelling one word correctly.**

    **A ref naming no registered row is deliberately NOT refused here.** §1's last
    non-goal is that an `InstanceRef` names an id the host already has and this registry
    does not resolve instances; `type_active` is the precondition that asks about
    registration. What is refused is a claim the registry can **see** is false.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate")
    await seed(registry, "searchable", kind="predicate")
    await action_family(
        registry,
        "merge_capabilities",
        inputs=[InputSpec("a", "type", kinds=None), InputSpec("b", "type", kinds=None)],
    )

    for label, left, right in (
        ("honest", TypeRef("default", "predicate", "commentable"),
         TypeRef("default", "predicate", "searchable")),
        ("misspelled", TypeRef("default", "Predicate", "commentable"),
         TypeRef("default", "Predicate", "searchable")),
        ("mislabelled", TypeRef("default", "entity", "commentable"),
         TypeRef("default", "entity", "searchable")),
    ):
        gate = await registry.preflight("merge_capabilities", {"a": left, "b": right}, actor="ai:c")
        assert isinstance(gate, Refusal), f"{label}: the gate said {gate!r}"
        assert gate.reason == "input_kind_mismatch", (label, gate)
        if registry.caps.stores_invocations:
            recorded = await registry.record_invocation(
                "merge_capabilities", {"a": left, "b": right},
                actor="ai:c", outcome="applied", gate_verdict="not_asked",
            )
            assert isinstance(recorded, Refusal), f"{label}: recorded {recorded!r}"
    if registry.caps.stores_invocations:
        assert (await registry.invocations()).known == 0, "nothing was written by any of the three"

    # A ref to a row nobody registered is NOT refused on this axis -- there is no stored
    # fact to contradict, and inventing one would be the confident answer Rule U forbids.
    await seed(registry, "task", kind="entity")
    await action_family(registry, "ordinary", inputs=[InputSpec("a", "type")])
    assert not isinstance(
        await registry.preflight(
            "ordinary", {"a": TypeRef("default", "entity", "never_registered")},
            actor="user:sd",
        ),
        Refusal,
    )

@NEEDS_ATTRIBUTES
async def test_c19_72_the_payload_schema_binds_at_both_invocation_doors(adapter, make_registry):
    """**MAJOR, round 3.** `preflight` never evaluated the family's `payload_schema`, so
    the gate said *may this run* → **yes** for inputs the recorder then refused
    `attributes_schema_violation` **non-overridably**.

    `_input_refusal`'s own docstring states the rule it broke: *a rule with one
    enforcement point is a rule with one door left open* — the sentence rule **2.2-4**
    was written from, and the reason the declaration rules bind at three doors rather
    than one. It is round 2's `C19-63` fix reaching one call site of two, which the
    tenth-trip countersignature made a standing thing to check.

    **A gate a recorder overrules is worse than no gate**: it tells a host the action may
    run, and §4's whole argument is that the host acts on what the gate said.
    """
    from ontoloche.actions import ACTION_PAYLOAD_KIND
    from ontoloche.attributes import AttributeSchema, FieldSpec

    registry = await make_registry(adapter)
    if registry._attribute_store() is None:
        pytest.skip(
            "PACKAGE.md 5 -- the AsyncAttributeStore extension is optional (ruling R2) and "
            "this backend declines it, so no schema can be in force."
        )
    await registry.register_attribute_schema(
        AttributeSchema(
            namespace="default",
            kind=ACTION_PAYLOAD_KIND,
            name="ticket_inputs",
            version=1,
            fields={"ticket": FieldSpec(type="str", description="the ticket id", required=True)},
            mode="enforce",
        )
    )
    await action_family(registry, "close_ticket", payload_schema="ticket_inputs")

    gate = await registry.preflight("close_ticket", {}, actor="user:sd")
    assert isinstance(gate, Refusal), f"the gate allowed inputs the recorder refuses: {gate!r}"
    assert gate.reason == "attributes_schema_violation"
    assert any("ticket" in v for v in gate.detail["violations"]), gate.detail

    if registry.caps.stores_invocations:
        recorded = await registry.record_invocation(
            "close_ticket", {}, actor="user:sd", outcome="applied",
            gate_verdict="not_asked",
        )
        assert isinstance(recorded, Refusal) and recorded.reason == gate.reason, (
            "one registry may not answer two ways about one set of inputs"
        )

@NEEDS_ATTRIBUTES
async def test_c19_73_a_precondition_names_a_predicate_by_the_registrys_notion_of_one_word(
    adapter, make_registry
):
    """**MAJOR, round 3**, and it is the seventh trip's surface that `6B-RUN.md` §6.2
    predicted this round would reach.

    `preflight`'s `predicate_holds` found its predicate with `p.name == condition.
    predicate` — an exact **byte** match — on a registry whose published notion of *the
    same word* is `same_word`/`identity_key`, minted by the seventh trip precisely so
    that *the registry cannot disagree with the scorer that delivers its 1.0*.

    **The direction was safe** — Rule U, `holds=None`, verdict refused — so this is not a
    collapse. What it was is a **confident false sentence**: *"no registered predicate
    named `commentable`"* about a word `resolve_type` answers at confidence 1.0. The
    seventh trip's rule is that one registry has one notion of a word, and a gate is not
    exempt from it.
    """
    registry = await make_registry(adapter)
    if not registry.caps.indexes_membership:
        pytest.skip(
            "PACKAGE.md 3.2 -- indexes_membership=False, so every extent is unknowable "
            "and `predicate_holds` is Rule U's unknown for a reason that is not this one."
        )
    await seed(registry, "commentable_", kind="predicate")
    await seed(registry, "note", predicates=["commentable_"])
    await action_family(
        registry,
        "ph",
        inputs=[InputSpec("a", "type")],
        preconditions=[
            # The condition spells the word the way a host would -- and the registry
            # holds `commentable_`, which `identity_key` says is the same word.
            Precondition("predicate_holds", "a", "must be commentable", predicate="commentable")
        ],
    )
    out = await registry.preflight(
        "ph", {"a": TypeRef("default", "entity", "note")}, actor="user:sd"
    )
    assert out.preconditions[0].holds is True, (
        "the registry answers `resolve_type('commentable')` with `commentable_` at "
        "confidence 1.0; a gate that calls the same word unregistered is one registry "
        "disagreeing with itself"
    )
    assert out.verdict == "allowed"

@NEEDS_ATTRIBUTES
@pytest.mark.requires_capability("stores_edges", "stores_events")
async def test_c19_75_preflight_warns_when_a_declared_edge_family_has_been_retired(
    adapter, make_registry
):
    """Rule **2.5-11**, ruling **R71** -- the GATE half.

    **The hole.** Rule 2.5-7 checks that an effect names a registered `kind="edge"`
    family **at declaration**, and §2.5's headline is *"the door is the declaration"* --
    which has no answer for the family being retired **afterwards**. A steward's
    ordinary retirement left every family declaring that word with a blast radius aimed
    at something withdrawn, and `preflight` went on answering `allowed` in silence.

    **A warning and never a refusal**: refusing would make an ordinary retirement break
    every host mid-flight, the shape §2.5 refuses twice. **No value is minted** --
    `edge_family_retired:<name>` already carries this exact fact one layer down
    (`EDGES.md` §4.3, on the read *and* on the write), which is `INTERFACE.md` §2.3's own
    discipline.

    The verdict is untouched, and that assertion is the whole rule: this is information,
    not a gate.
    """
    registry = await make_registry(adapter)
    await edge_family(registry, "person_links", level="instance")
    await action_family(
        registry,
        "link_people",
        effects=[Effect(op="add_edge", family="person_links", namespace="default")],
    )

    before = await registry.preflight("link_people", {}, actor="user:sd")
    assert before.verdict == "allowed"
    assert before.warnings == (), "nothing is retired yet"

    retired = await registry.retire(
        "person_links", reason="superseded", retired_by="user:sd", force=True
    )
    assert not isinstance(retired, Refusal), retired

    after = await registry.preflight("link_people", {}, actor="user:sd")
    assert after.verdict == "allowed", "an ordinary retirement does not break every host"
    assert "edge_family_retired:person_links" in after.warnings

    # One per FAMILY and not one per effect: a family declaring both edge ops on one
    # retired family has one retired family, which is one fact.
    await action_family(
        registry,
        "link_and_unlink",
        effects=[
            Effect(op="add_edge", family="person_links", namespace="default"),
            Effect(op="retract_edge", family="person_links", namespace="default"),
        ],
    )
    both = await registry.preflight("link_and_unlink", {}, actor="user:sd")
    assert both.warnings == ("edge_family_retired:person_links",)

@NEEDS_INVOCATIONS
@pytest.mark.requires_capability("stores_edges", "stores_events")
async def test_c19_76_record_invocation_warns_on_a_retired_declared_edge_family(
    adapter, make_registry
):
    """Rule **2.5-11**, ruling **R71** -- the LEDGER half, and the reason there are two
    ids rather than one.

    Shipping this at `record_invocation` alone would be *a fix applied at one call site
    of two*, which is the single sentence of the kill row's ninth, tenth and eleventh
    trips (`C12-14`, `C12-16`, `C12-17`) and the reason `declared_predicates` became a
    required keyword. `C19-75` holds the gate; this holds the record; both read the same
    list off `AsyncRegistry._retired_blast_radius`.

    **Judged over the DECLARATION OF RECORD**, not over today's family: rule 3-7's own
    reason is that the record says what the gate judged, and a warning about a blast
    radius the actor never declared would be a true sentence about the wrong moment.
    """
    registry = await make_registry(adapter)
    await edge_family(registry, "person_links", level="instance")
    await action_family(
        registry,
        "link_people",
        effects=[Effect(op="add_edge", family="person_links", namespace="default")],
    )
    judged = await registry.preflight("link_people", {}, actor="user:sd")
    assert judged.warnings == ()

    clean = await registry.record_invocation(
        "link_people", {}, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by=judged.approved_by, judged=judged,
    )
    assert not isinstance(clean, Refusal), clean
    assert not [w for w in clean.warnings if w.startswith("edge_family_retired")]

    await registry.retire("person_links", reason="superseded", retired_by="user:sd", force=True)

    late = await registry.record_invocation(
        "link_people", {}, actor="user:sd", outcome="applied",
        gate_verdict="not_asked", approved_by="user:sd",
    )
    assert not isinstance(late, Refusal), late
    assert "edge_family_retired:person_links" in late.warnings, (
        "the record is KEPT and it says the blast radius points at a withdrawn word"
    )
    assert late.outcome == "applied", "a warning is not a refusal"

async def test_c19_77_ref_key_and_parse_ref_round_trip_over_every_reference_shape(
    adapter, make_registry
):
    """§2.3, ruling **R72** -- the flat identity string reads back as the ref it was.

    **Why the parser exists.** §2.3 argues at length that `EdgeRef` carries `family` and
    `namespace` so *"the reference can be READ without a store round trip"* a year
    later, and `InvocationRecord.inputs` is JSON (`PACKAGE.md` §3.3) -- so what the
    ledger holds is `"beacon:edge:b_edges#e-abc123"`, and the package exported only the
    half that WRITES it. Every consumer hand-split the string the document promised was
    readable.

    The property is stated as a property rather than as three examples: for every ref
    shape, `parse_ref(ref_key(r)) == r`, **and** `ref_key(parse_ref(k)) == k`. The
    second half is not redundant -- a parser that dropped a namespace would satisfy
    neither, but a parser that normalised one would satisfy only the first.

    The opaque halves are exercised with the characters that break a naive split: an
    instance id and an `edge_id` are *"the host's identifier"* and may contain `:` and
    `#`, which is why the split is on the FIRST `#` and the head is exactly three
    colon-separated segments.
    """
    refs = [
        TypeRef("beacon", "entity", "person"),
        TypeRef("default", "predicate", "commentable"),
        InstanceRef(TypeRef("beacon", "entity", "person"), "41"),
        InstanceRef(TypeRef("dpr", "value_set", "borough"), "a:b#c"),
        EdgeRef("e-abc123", "b_edges", "beacon"),
        EdgeRef("e#x:y", "b_edges", "beacon"),
    ]
    for ref in refs:
        key = ref_key(ref)
        assert parse_ref(key) == ref, key
        assert ref_key(parse_ref(key)) == key, key

    # `kind == "edge"` with an id has exactly ONE legal reading, because §2.3 requires
    # an `InstanceRef`'s type to be `kind="entity"`. A fact about the FORMAT, pinned so
    # a reader of a year-old ledger does not discover it.
    assert isinstance(parse_ref("beacon:edge:b_edges#e-1"), EdgeRef)

    # And it is the same string the LEDGER stores, not a parallel format: drive one
    # through the shipped registry and read the stored key back.
    if not (registry := await make_registry(adapter)).caps.stores_invocations:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares stores_invocations=False; the "
            "round-trip property above is asserted on every leg"
        )
    if not registry.caps.stores_attributes:
        pytest.skip("PACKAGE.md 3.2 -- ACTIONS.md 2.2 needs stores_attributes")
    await seed(registry, "person")
    await action_family(registry, "touch_person", inputs=[InputSpec("who", "instance")])
    who = InstanceRef(TypeRef("default", "entity", "person"), "41")
    out = await registry.record_invocation(
        "touch_person", {"who": who}, actor="user:sd", outcome="applied",
        approved_by="user:sd",
    )
    assert not isinstance(out, Refusal), out
    assert parse_ref(out.inputs["who"]) == who, (
        "the ledger's stored string is the one this parser reads; a second format "
        "would be two homes for one fact"
    )

def test_c19_78_parse_ref_refuses_what_it_did_not_recognise_and_never_defaults(
    adapter, make_registry
):
    """§2.3, ruling **R72** -- and this id is the one that matters.

    **A permissive default for a value you did not recognise is the single shape row 6b
    shipped twice.** `ref_shape` returned `"type"` for anything that was not an
    `EdgeRef` or an `InstanceRef`, so a bare string walked past the general `predicate`
    exclusion and `merge_capabilities(commentable, searchable)` reached
    `verdict="allowed"`; `_alias_identity_breach` fell back to comparing a row against
    itself, which is the kill row's **ninth** trip; and `is_person` records the same
    mistake one section along, its own docstring naming the rule -- *unknown is not a
    person.* It is also not a type ref, and it is not a reference at all.

    So `parse_ref` **raises** for everything outside §2.3's grammar. There is no `None`
    fallback and no *"probably a type ref"* branch: a caller that gets a value back got
    one this function actually read, and a caller that passed something else finds out
    **at the call** -- R64's required-keyword rule applied to a parser.
    """
    for bad in (None, 42, b"beacon:entity:person", ("beacon", "entity", "person")):
        with pytest.raises(ValueError):
            parse_ref(bad)

    for bad in ("", "person", "beacon:person", "beacon:entity:person:extra",
                "beacon:entity:person:extra#41", "#41"):
        with pytest.raises(ValueError):
            parse_ref(bad)

    # The narrowing half: refusing everything passes a test that only tests refusals.
    assert parse_ref("beacon:entity:person") == TypeRef("beacon", "entity", "person")

@NEEDS_INVOCATIONS
async def test_c19_79_review_invocation_is_a_fifth_call_and_never_a_write_call_parameter(
    adapter, make_registry
):
    """Rule **6-9**, ruling **R73**, adopting deviation **D-6b-3** in full.

    **A review is a second act by a second person at a later time.** A `reviewed_by=`
    on `record_invocation` would let the actor who ran the action mark their own
    invocation reviewed -- a `register_consumer` that quietly no-ops, one object along,
    which is the mechanism this whole layer exists to make visible. So the drain is a
    **fifth call**, §6.5, and the write call has no such parameter.

    The absence is asserted mechanically rather than asserted in prose: the signature of
    `record_invocation` carries no reviewer parameter, and a caller who passes one gets
    a `TypeError` at the call rather than a silently ignored keyword.
    """
    import inspect

    registry = await make_registry(adapter)
    params = set(inspect.signature(registry.record_invocation).parameters)
    assert not params & {"reviewed_by", "reviewed_at", "review"}, sorted(params)

    await action_family(registry, "reconcile_borough", approval_mode="review")
    with pytest.raises(TypeError):
        await registry.record_invocation(
            "reconcile_borough", {}, actor="user:sd", outcome="applied",
            approved_by="auto:auto", reviewed_by="user:sd",
        )

    # ...and the fifth call takes `reviewed_by` as a REQUIRED keyword: a review with no
    # reviewer is the unsigned approval §3.2 refuses to fabricate.
    fifth = inspect.signature(registry.review_invocation).parameters
    assert fifth["reviewed_by"].kind is inspect.Parameter.KEYWORD_ONLY
    assert fifth["reviewed_by"].default is inspect.Parameter.empty

@NEEDS_INVOCATIONS
async def test_c19_80_an_unknown_invocation_id_refuses_unknown_invocation_and_not_the_family(
    adapter, make_registry
):
    """Rule **6-10**, ruling **R73** -- the thirty-first `Refusal.reason`.

    §7 argued this value and **declined** it, and the argument was explicitly
    conditional: *"no call in this document names an existing invocation by id."*
    §6.5's fifth call names one, so the condition expired and R3's rule -- a value is
    minted in the change that introduces it -- puts the value and the call together.

    **Not `action_family_unknown`**, which the build row reused and recorded as a
    mismatch rather than defended. That value names a missing **family**; this names a
    missing **invocation**. One word for two objects is `INTERFACE.md` §2.3's Cause B,
    the same argument that keeps `unknown_edge` separate from `edge_family_unknown` --
    and it is not abstract: a host draining a review queue and told *no such action
    family* would go looking for a family that is registered, live, and not the problem.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "reconcile_borough", approval_mode="review")

    out = await registry.review_invocation("no-such-invocation", reviewed_by="user:boss")
    assert isinstance(out, Refusal)
    assert out.reason == "unknown_invocation", out.reason
    assert out.detail["invocation_id"] == "no-such-invocation"
    assert "unknown_invocation" in REFUSAL_REASONS

@NEEDS_INVOCATIONS
async def test_c19_81_the_review_queue_drains_end_to_end(adapter, make_registry):
    """Rule **6-11**. `review` mode's queue, from the mode to the empty queue.

    §5.2 specified the READ (`invocations(unreviewed=True)`) and §3.5 minted the EVENT,
    and v0's four calls appended none -- so `approval_mode="review"` shipped as a mode
    whose queue could never drain, and three adversarial rounds read both sections
    without finding it. **What found it was writing the ids**, which is §14's own
    argument arriving as evidence.

    `C19-50` holds the mode's approval and the filter; this holds the DRAIN as one
    sequence, because a queue that empties in a unit test and not in the order a host
    performs it is the failure `C19-50` could not pose.
    """
    registry = await make_registry(adapter)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        # **BOTH flags, and naming one of the two was the defect.**
        # `review_invocation` refuses `cannot_record_override` on
        # `not (stores_events and stores_invocation_events)`, so a backend that keeps
        # events but declines INVOCATION events reached the drain and got a `Refusal`.
        # PACKAGE.md 8b.5: a capability used as SCAFFOLDING for a subject that is
        # something else is declared, not assumed -- and the declaration has to name
        # every flag the scaffolding actually needs.
        pytest.skip(
            "PACKAGE.md 3.2 -- a review IS an event and this backend cannot keep one "
            "(stores_events / stores_invocation_events), so `review_invocation` "
            "refuses `cannot_record_override` rather than claiming a review nothing "
            "recorded"
        )
    await action_family(registry, "infer_person_relationships", approval_mode="review")
    gate = await registry.preflight("infer_person_relationships", {}, actor="ai:nightly")
    filed = [
        await registry.record_invocation(
            "infer_person_relationships", {}, actor="ai:nightly", outcome="applied",
            gate_verdict="allowed", approved_by=gate.approved_by, judged=gate,
        )
        for _ in range(3)
    ]
    assert (await registry.invocations(unreviewed=True)).known == 3

    for i, one in enumerate(filed):
        reviewed = await registry.review_invocation(one.invocation_id, reviewed_by="user:boss")
        assert not isinstance(reviewed, Refusal), reviewed
        assert reviewed.reviewed_at is not None
        assert (await registry.invocations(unreviewed=True)).known == 2 - i

    # The event is the record, and it names the reviewer -- a review nobody signed is
    # the unsigned approval §3.2 refuses to fabricate.
    read_back = [
        i
        for i in (await registry.invocations()).invocations
        if i.invocation_id == filed[0].invocation_id
    ][0]
    events = [
        e for e in read_back.provenance.history if e.event == "invocation_reviewed"
    ]
    assert events and events[0].actor == "user:boss", read_back.provenance.history

    # Reviewing an already-reviewed invocation is not refused -- it is an append-only
    # log and a second reviewer is a fact, not an error. Rule U: the queue is empty
    # because the event exists, not because a flag was flipped.
    again = await registry.review_invocation(filed[0].invocation_id, reviewed_by="user:other")
    assert not isinstance(again, Refusal), again
    assert (await registry.invocations(unreviewed=True)).known == 0

@NEEDS_INVOCATIONS
async def test_c19_82_a_ref_the_flat_form_cannot_carry_is_refused_at_both_doors(
    adapter, make_registry
):
    """Rule **2.5-13**. **BLOCKING, round 1** -- and it is worse than the failure R72
    was written to prevent.

    `NAME_RE` binds `propose_type`'s **name**, binds no `namespace` at all, and neither
    bound a reference **supplied at an invocation door**. So a `TypeRef` whose `name`
    carried a `#` was accepted, stored as ``"beacon:entity:person#p-1"``, and read back
    by `parse_ref` as an **`InstanceRef` naming an object that never existed** -- with no
    exception anywhere. A `namespace` carrying a `:` produced the loud half: a ledger row
    `parse_ref` refuses, written by this layer itself.

    `ref_shape` returning ``"type"`` for a bare string was *the most permissive reading
    of something it did not recognise*; **this is a confident reading of the wrong
    thing** -- the seventh trip's shape (*a guard comparing a byte where the registry
    holds a stored fact*) arriving in a parser.

    **The refusal belongs at the WRITE door and not in the parser**: a parser that
    guessed which of two readings a caller meant would be the permissive default again.
    Refusing here keeps every string in the ledger parseable **by construction**.
    """
    registry = await make_registry(adapter)
    await seed(registry, "person")
    await action_family(registry, "touch", inputs=[InputSpec("who", "type")])

    for bad, why in (
        (TypeRef("beacon", "entity", "person#p-1"), "a '#' in the name"),
        (TypeRef("beacon:crm", "entity", "person"), "a ':' in the namespace"),
        (TypeRef("beacon", "ent#ity", "person"), "a '#' in the kind"),
    ):
        gate = await registry.preflight("touch", {"who": bad}, actor="user:sd")
        assert isinstance(gate, Refusal), (why, gate)
        assert gate.reason == "input_kind_mismatch"
        assert gate.detail["problem"] == "unrepresentable", why

        filed = await registry.record_invocation(
            "touch", {"who": bad}, actor="user:sd", outcome="applied",
            approved_by="user:sd",
        )
        assert isinstance(filed, Refusal), (why, filed)
        assert filed.detail["problem"] == "unrepresentable", why

    # The narrowing half: refusing everything passes a test that only tests refusals.
    good = TypeRef("default", "entity", "person")
    ok = await registry.record_invocation(
        "touch", {"who": good}, actor="user:sd", outcome="applied", approved_by="user:sd",
    )
    assert not isinstance(ok, Refusal), ok
    assert parse_ref(ok.inputs["who"]) == good, (
        "and the ledger's string reads back as the ref that was written"
    )

    # The opaque halves are still the host's business: an id may carry either character.
    opaque = InstanceRef(TypeRef("default", "entity", "person"), "a:b#c")
    await action_family(registry, "touch_one", inputs=[InputSpec("who", "instance")])
    out = await registry.record_invocation(
        "touch_one", {"who": opaque}, actor="user:sd", outcome="applied",
        approved_by="user:sd",
    )
    assert not isinstance(out, Refusal), out
    assert parse_ref(out.inputs["who"]) == opaque

@NEEDS_INVOCATIONS
@pytest.mark.requires_capability("stores_edges", "stores_events")
async def test_c19_83_an_input_determined_effect_is_judged_over_the_inputs_namespaces(
    adapter, make_registry
):
    """Rule **2.5-12**. **MAJOR, round 1** -- and it was a false answer in **both**
    directions.

    Rule 2.5-10 says `namespace=None` on an edge op declares an **input-determined**
    namespace: the edge lands where the invocation's own inputs point. Rule 2.5-11's
    first cut inherited the DECLARATION door's reading (*the effect's namespace, or the
    family's own*), which is correct there because a declaration has no inputs.

    **[Observed]** with the family retired in the namespace the inputs point at and
    active in the family's own: **no warning at all**, while the edge landed exactly
    where the word is withdrawn. And the mirror -- retired in the family's namespace,
    active where the inputs point: **a warning about a family that is live where the
    edge went.** `record_invocation` was already computing the input namespaces two
    blocks along for `effect_undeclared`; the derivation is shared now rather than
    doubled.
    """
    registry = await make_registry(adapter)
    await seed(registry, "person", namespace="tenant_a")
    await edge_family(registry, "person_links", level="instance", namespace="tenant_a")
    await edge_family(registry, "person_links", level="instance", namespace="default")
    await action_family(
        registry, "link_people",
        inputs=[InputSpec("who", "instance")],
        # `namespace=None` -- rule 2.5-10, input-determined.
        effects=[Effect(op="add_edge", family="person_links")],
    )
    who = {"who": InstanceRef(TypeRef("tenant_a", "entity", "person"), "1")}

    assert (await registry.preflight("link_people", who, actor="user:sd")).warnings == ()

    # THE FALSE NEGATIVE: retired where the inputs point, live in the family's own.
    assert not isinstance(
        await registry.retire(
            "person_links", reason="superseded", retired_by="user:sd",
            namespace="tenant_a", force=True,
        ),
        Refusal,
    )
    gate = await registry.preflight("link_people", who, actor="user:sd")
    assert "edge_family_retired:person_links" in gate.warnings, (
        "the edge lands in tenant_a and the family is withdrawn there"
    )
    filed = await registry.record_invocation(
        "link_people", who, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by=gate.approved_by, judged=gate,
    )
    assert "edge_family_retired:person_links" in filed.warnings

    # THE FALSE POSITIVE: an invocation whose inputs point at the namespace where the
    # family is still live must NOT be warned about the family's own namespace.
    await seed(registry, "person")
    elsewhere = {"who": InstanceRef(TypeRef("default", "entity", "person"), "1")}
    quiet = await registry.preflight("link_people", elsewhere, actor="user:sd")
    assert quiet.warnings == (), (
        "the edge lands in `default`, where the family is active", quiet.warnings
    )

@NEEDS_INVOCATIONS
async def test_c19_84_the_review_queue_reads_the_mode_of_record_not_todays_mode(
    adapter, make_registry
):
    """Rule **6-12**. **MAJOR, round 1**, and it is rule 3-1's argument one call along.

    `Invocation.declared_policy` carries *"the policy the gate judged"* (rule 3-8)
    precisely so an amendment cannot re-describe an invocation after the fact, and this
    read took `approval_mode` off the **live family** instead.

    **[Observed]** three invocations filed under `review` and never reviewed left the
    queue the moment a steward flipped the family to `auto` -- no event, no warning,
    `known` moving from 3 to 0 -- and the flip the other way made historical `auto`
    invocations *awaiting review* retroactively. Their own `declared_policy` said
    `review` and `auto` throughout. **A queue that empties because somebody edited an
    unrelated field is a governance mechanism nobody can operate.**
    """
    registry = await make_registry(adapter)
    await action_family(registry, "merge_contacts", approval_mode="review")
    gate = await registry.preflight("merge_contacts", {}, actor="ai:nightly")
    for _ in range(3):
        await registry.record_invocation(
            "merge_contacts", {}, actor="ai:nightly", outcome="applied",
            gate_verdict="allowed", approved_by=gate.approved_by, judged=gate,
        )
    assert (await registry.invocations(unreviewed=True)).known == 3

    # An ordinary amendment: the steward decides new invocations may auto-approve.
    await action_family(registry, "merge_contacts", approval_mode="auto")
    after = await registry.invocations(unreviewed=True)
    assert after.known == 3, (
        "the three were judged under `review` and none has been reviewed; an amendment "
        "does not review them"
    )
    assert all(
        i.declared_policy["approval_mode"] == "review" for i in after.invocations
    )

    # ...and the other direction: a historical `auto` invocation does not join the queue.
    await action_family(registry, "search_tasks", approval_mode="auto")
    auto_gate = await registry.preflight("search_tasks", {}, actor="ai:nightly")
    await registry.record_invocation(
        "search_tasks", {}, actor="ai:nightly", outcome="applied",
        gate_verdict="allowed", approved_by=auto_gate.approved_by, judged=auto_gate,
    )
    await action_family(registry, "search_tasks", approval_mode="review")
    queue = await registry.invocations(unreviewed=True)
    assert {i.family for i in queue.invocations} == {"merge_contacts"}, (
        "a family flipped INTO review does not retroactively enqueue what ran under auto"
    )

@NEEDS_INVOCATIONS
async def test_c19_85_review_invocation_honours_its_namespace_and_needs_a_reviewer(
    adapter, make_registry
):
    """Rule **6-13**. **MAJOR + MINOR, round 1.**

    The `namespace` argument reached only the `action_store_absent` detail dict: the id
    lookup was store-wide and the event was appended to `rec.namespace`, so **a
    review-queue operator scoped to one tenant drained another tenant's queue with no
    refusal** -- in a registry where §2.6 makes `namespace` the answer to mechanism 4,
    and on the UC3 shape where dozens of publishers share one catalogue. *A parameter
    that cannot change an outcome is worse than no parameter.*

    And a review with **no reviewer** was accepted, which is the unsigned approval §3.2
    refuses to fabricate. A `ValueError` rather than a `Refusal`, exactly as `retire`
    and `reinstate` answer an empty `reason`: a caller's mistake about its own
    arguments is not a decision about the vocabulary.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "reconcile", approval_mode="review", namespace="dpr")
    gate = await registry.preflight("reconcile", {}, actor="user:sd", namespace="dpr")
    filed = await registry.record_invocation(
        "reconcile", {}, actor="user:sd", namespace="dpr", outcome="applied",
        gate_verdict="allowed", approved_by=gate.approved_by, judged=gate,
    )
    assert not isinstance(filed, Refusal), filed

    wrong = await registry.review_invocation(
        filed.invocation_id, reviewed_by="user:boss", namespace="oti_311"
    )
    assert isinstance(wrong, Refusal), wrong
    assert wrong.reason == "unknown_invocation"
    assert wrong.detail["namespace"] == "oti_311"

    for empty in ("", "   "):
        with pytest.raises(ValueError):
            await registry.review_invocation(filed.invocation_id, reviewed_by=empty)

    # The narrowing half: the right scope still drains, and the record says WHO.
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        # Both flags -- see `C19-81`. The scope and reviewer rules above need neither.
        pytest.skip(
            "PACKAGE.md 3.2 -- a review IS an event and this backend cannot keep one "
            "(stores_events / stores_invocation_events); the scope and reviewer rules "
            "above are asserted on every leg"
        )
    right = await registry.review_invocation(
        filed.invocation_id, reviewed_by="user:boss", namespace="dpr"
    )
    assert not isinstance(right, Refusal), right
    assert right.reviewed_at is not None
    assert right.reviewed_by == "user:boss", (
        "two reviewers are allowed and `reviewed_at` re-points to the last, so the "
        "record answers *who cleared this* directly rather than only through history"
    )

@NEEDS_ATTRIBUTES
async def test_c19_86_projection_names_its_scope_and_says_which_empty_it_is(
    adapter, make_registry
):
    """Rules **10-11** and **10-12**. **MAJOR + MINOR, round 1.**

    `namespace` is optional, its default is the **whole store**, and nothing on the
    report said which answer a caller was holding. **[Observed]** one publisher's
    families with a co-tenant on the store: scoped, two surfaces fit; unscoped, the same
    call charged slots the publisher does not own and reported surfaces evicted that
    would have shipped. **Ruling R70 narrowed the TYPO judgement to the scope in the row
    that left the ANSWER's scope unnamed** -- the guard scoped and the report silent.

    And an all-zero answer has four causes that are not interchangeable. A typo'd
    `namespace` produced zeroes, `fits` naming every ordered group and `over_by=0` --
    **the call affirmatively answering *everything fits* about a scope holding
    nothing**, which is rule 10-9's own sentence pointing at itself.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "publish", reachability=["console"], namespace="dpr")
    await action_family(registry, "close", reachability=["console"], namespace="oti_311")

    scoped = await registry.projection("s", budget=10, order=("console",), namespace="dpr")
    assert scoped.namespace == "dpr", "the report echoes the scope it answered over"
    assert scoped.counts == {"console": 1}

    wide = await registry.projection("s", budget=10, order=("console",))
    assert wide.namespace is None, "None says the answer is store-wide"
    assert wide.counts == {"console": 2}, "and it charged the co-tenant's family too"

    # Which empty is it? A scope that holds no `kind="action"` row at all.
    absent = await registry.projection("s", budget=10, order=("console",), namespace="dpr_typo")
    assert not isinstance(absent, Refusal), "an empty scope is not a typo'd GROUP"
    assert "the SCOPE is empty" in (absent.why_incomplete or ""), absent.why_incomplete

    # ...against a scope that holds rows and simply declares no surfaces, which is the
    # one case rule 10-9 exists to protect.
    await action_family(registry, "ingest", reachability=[], namespace="pipeline")
    quiet = await registry.projection(
        "s", budget=10, order=("console",), namespace="pipeline"
    )
    assert "the SCOPE is empty" not in (quiet.why_incomplete or "")
    assert "groups no family in this scope carries" in (quiet.why_incomplete or "")

    # Rule 10-12: a caller's mistake about its own arithmetic.
    for budget, reserved in ((-5, 0), (10, -1), (3, 4)):
        with pytest.raises(ValueError):
            await registry.projection("s", budget=budget, reserved=reserved, order=("console",))

@NEEDS_INVOCATIONS
@pytest.mark.requires_capability("stores_edges", "stores_events")
async def test_c19_87_an_unrelated_input_does_not_drag_its_namespace_into_the_warning(
    adapter, make_registry
):
    """Rule **2.5-12**. **MAJOR, round 2's fix-auditor lens** -- *`C19-83`'s fix
    reintroduced the false positive it was written to remove.*

    `_input_namespaces` unions every namespace **any** input mentions, so an input with
    nothing to do with the edge drags its namespace into the candidate set and the
    warning fires about a family that is live where the edge went -- the exact second
    direction `C19-83` exists to close, one field along.

    **[Observed]** `person_links` ACTIVE in `default` where the edge lands, retired in
    `tenant_a` named only by an unrelated `cfg` input:
    ``('edge_family_retired:person_links',)`` at **both** doors.

    Two fixes, because the two doors know different things. The ledger door is handed
    ``observed_effects`` and therefore knows **where the edge went**, so an
    input-determined declaration is judged there and nowhere else. The gate has no such
    fact -- the invocation has not happened -- so it warns only when **every** candidate
    that has the family has retired it: *we do not know where it lands* is not *it was
    retired*, which is Rule U in the field 2.5-11 added to state an absence.
    """
    registry = await make_registry(adapter)
    await seed(registry, "person")
    await seed(registry, "cfg", namespace="tenant_a")
    await edge_family(registry, "person_links", level="instance")
    await edge_family(registry, "person_links", level="instance", namespace="tenant_a")
    await action_family(
        registry, "link_people",
        inputs=[InputSpec("who", "instance"), InputSpec("cfg", "instance", required=False)],
        effects=[Effect(op="add_edge", family="person_links")],
    )
    assert not isinstance(
        await registry.retire(
            "person_links", reason="superseded", retired_by="user:sd",
            namespace="tenant_a", force=True,
        ),
        Refusal,
    )
    inputs = {
        "who": InstanceRef(TypeRef("default", "entity", "person"), "1"),
        "cfg": InstanceRef(TypeRef("tenant_a", "entity", "cfg"), "c1"),
    }
    gate = await registry.preflight("link_people", inputs, actor="user:sd")
    assert gate.warnings == (), (
        "the family is ACTIVE in `default`, where the edge lands; the retired one is in "
        "a namespace only an unrelated input mentions",
        gate.warnings,
    )
    filed = await registry.record_invocation(
        "link_people", inputs, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by=gate.approved_by, judged=gate,
        observed_effects=[
            Effect(op="add_edge", family="person_links", namespace="default")
        ],
    )
    assert not [
        w for w in filed.warnings if w.startswith("edge_family_retired")
    ], ("the ledger knows the edge landed in `default`", filed.warnings)

    # ...and `C19-83`'s TRUE direction still fires: retired in every candidate that has
    # it. Narrowing a guard that must keep refusing is how a fix deletes a rule.
    await seed(registry, "person", namespace="tenant_a")
    only_a = {
        "who": InstanceRef(TypeRef("tenant_a", "entity", "person"), "1"),
        "cfg": InstanceRef(TypeRef("tenant_a", "entity", "cfg"), "c1"),
    }
    still = await registry.preflight("link_people", only_a, actor="user:sd")
    assert "edge_family_retired:person_links" in still.warnings, (
        "every candidate holding this family has retired it", still.warnings
    )

@pytest.mark.requires_capability("stores_attributes", "stores_events")
async def test_c19_88_the_scope_census_tells_an_all_retired_scope_from_a_typod_one(
    adapter, make_registry
):
    """Rule **10-11**. **MAJOR, round 2's fix-auditor lens** -- *`C19-86`'s scope
    sentence asserts a falsehood.*

    `projection` probed the scope with ``list_types("action", namespace=...)``, which
    defaults to ``include_retired=False`` -- so ``scope_rows`` counted **active** rows,
    which makes it the same number as ``scope_active``, leaves the ``scope_active == 0``
    branch **unreachable on all three legs**, and tells an all-retired scope that it
    *"holds no kind=action row of any status"*.

    **[Observed]** ``list_types("action", namespace="tenant_a")`` -> ``[]`` while
    ``include_retired=True`` -> ``[('publish_doc', 'retired')]``, with the retired-only
    sentence **byte-identical** to the typo'd-scope one. A report whose job is saying
    *which* empty this is earns nothing if it cannot tell them apart.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "publish_doc", reachability=["console"], namespace="tenant_a")
    assert not isinstance(
        await registry.retire(
            "publish_doc", reason="withdrawn", retired_by="user:sd",
            namespace="tenant_a", force=True,
        ),
        Refusal,
    )
    retired = await registry.projection(
        "s", budget=10, order=("console",), namespace="tenant_a"
    )
    typo = await registry.projection(
        "s", budget=10, order=("console",), namespace="tenant_zzz"
    )
    assert retired.counts == {"console": 0} and typo.counts == {"console": 0}
    assert "the SCOPE is empty" in (typo.why_incomplete or ""), typo.why_incomplete
    assert "the SCOPE is empty" not in (retired.why_incomplete or ""), (
        "a scope holding a retired family is not a scope holding nothing",
        retired.why_incomplete,
    )
    assert "0 active" in (retired.why_incomplete or ""), retired.why_incomplete
    assert "retired" in (retired.why_incomplete or ""), retired.why_incomplete

    # ...and the pool stays ACTIVE-ONLY: a retired family is not selectable, and
    # counting one would change the arithmetic this call exists for.
    assert retired.known == 0, retired.known

@NEEDS_INVOCATIONS
async def test_c19_89_the_review_queues_rule_u_fallback_is_stated_and_counted(
    adapter, make_registry
):
    """Rule **6-12**. **MINOR, round 2's fix-auditor lens** -- *`C19-84`'s Rule-U
    fallback is unwarned.*

    A row carrying no ``declared_policy.approval_mode`` -- filed before the field
    existed, or by a backend that keeps none -- falls back to the family's mode
    **today**, which is the entire defect `C19-84` closed, fully live for that row. The
    comment claimed *"the report says the set is a floor either way"*; that was true
    only of ``complete=False``, which is a sentence about the **filter**.

    The clause names **how many** rows fell back, because *some of these rows* and *all
    of these rows* are different facts to an operator draining a queue.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "publish", approval_mode="review")
    filed = await registry.record_invocation(
        "publish", {}, actor="user:sd", outcome="applied", approved_by="user:sd",
    )
    assert not isinstance(filed, Refusal), filed

    ordinary = await registry.invocations(unreviewed=True)
    assert not isinstance(ordinary, Refusal), ordinary
    assert "judged against the family's mode TODAY" not in (
        ordinary.why_incomplete or ""
    ), ("every row here carries its own mode of record", ordinary.why_incomplete)

    # **A backend that kept no policy of record, as a READ-SIDE double.** The store
    # cannot be edited into that shape -- `put_invocation` refuses to overwrite an
    # existing id, which is the ledger's own append-only rule -- so the condition is
    # constructed the way round 2's own lens constructed it: a proxy that answers the
    # read with the field absent. That is exactly what a backend filing rows before the
    # field existed looks like from here.
    class _NoPolicyOfRecord:
        def __init__(self, inner):
            object.__setattr__(self, "inner", inner)

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def __setattr__(self, name, value):
            setattr(self.inner, name, value)

        async def find_invocations(self, **kwargs):
            page = await self.inner.find_invocations(**kwargs)
            return type(page)(
                **{
                    **page.__dict__,
                    "records": tuple(
                        type(r)(**{**r.__dict__, "declared_policy": {}})
                        for r in page.records
                    ),
                }
            )

    stripped = list((await registry.adapter.find_invocations(namespace="default")).records)
    assert stripped, "the fixture filed one"
    blind = await make_registry(_NoPolicyOfRecord(adapter))
    fell_back = await blind.invocations(unreviewed=True)
    assert "judged against the family's mode TODAY" in (
        fell_back.why_incomplete or ""
    ), ("a fallback nobody can see is a fallback nobody can act on",
        fell_back.why_incomplete)
    assert f"{len(stripped)} of " in (fell_back.why_incomplete or ""), (
        "some and all are different facts", fell_back.why_incomplete
    )

def test_c19_90_the_flat_form_refusal_says_which_of_its_two_failures_this_is():
    """Rule **2.5-13**. **MAJOR, round 2's fix-auditor lens** -- *`C19-82`'s `why` is
    wrong for one of the two cases it covers.*

    A segment carrying ``#`` makes `ref_key` write a string `parse_ref` reads back as a
    **different reference** -- the BLOCKING of round 1, and the sentence was written for
    it. A **namespace** carrying ``:`` makes `ref_key` write a string `parse_ref`
    **raises** on: nothing is misread, the ledger row is simply unreadable.

    **[Observed]** ``"org:beacon:entity:person"`` -> ``ValueError`` naming four
    segments, under a `why` telling the caller it *"reads back as a DIFFERENT
    reference"* -- which sends it looking for a misreading that does not happen, in the
    one field this refusal exists to make actionable.
    """
    from ontoloche.actions import flat_form_problem

    misread = flat_form_problem(TypeRef("beacon", "entity", "person#p-1"))
    assert misread and "DIFFERENT reference" in misread, misread
    assert parse_ref(ref_key(TypeRef("beacon", "entity", "person#p-1"))) != TypeRef(
        "beacon", "entity", "person#p-1"
    ), "and the misreading is real, which is why that sentence is right for this case"

    unreadable = flat_form_problem(TypeRef("org:beacon", "entity", "person"))
    assert unreadable and "RAISES" in unreadable, unreadable
    assert "DIFFERENT reference" not in unreadable, (
        "nothing is misread here; the row cannot be read at all", unreadable
    )
    with pytest.raises(ValueError):
        parse_ref(ref_key(TypeRef("org:beacon", "entity", "person")))

@NEEDS_INVOCATIONS
@pytest.mark.requires_capability("stores_edges", "stores_events")
async def test_c19_91_a_landing_in_a_retired_namespace_is_warned_however_many_live_ones(
    adapter, make_registry
):
    """Rule **2.5-12**. **MAJOR, round 3's own fix-auditor lens** — a defect in
    `C19-87`, one commit old.

    **A LANDING is a fact and a candidate is a maybe.** `C19-87` applied Rule U's
    *every candidate that has the family has retired it* quantifier to both, and
    `landed` is a set of namespaces the edge **actually reached** — so one additional
    real landing in a live namespace silently deleted the warning about the landing in
    the withdrawn one.

    **[Observed, before the fix]** one invocation landing `person_links` in `tenant_a`
    (retired) *and* in `default` (active) answered ``()`` where the `tenant_a`-only
    landing answers ``('edge_family_retired:person_links',)``. That is `C19-83`'s FIRST
    direction — *no warning at all while the edge landed exactly where the family is
    withdrawn* — restored by the fix for its second.

    It is also the answer to *can a host suppress this?*: nothing verifies an observed
    effect against the edge store, so one appended `add_edge` in a live namespace did it.
    """
    registry = await make_registry(adapter)
    for space in ("default", "tenant_a"):
        await seed(registry, "person", namespace=space)
        await edge_family(registry, "person_links", level="instance", namespace=space)
    assert not isinstance(
        await registry.retire(
            "person_links", reason="superseded", retired_by="user:sd",
            namespace="tenant_a", force=True,
        ),
        Refusal,
    )
    await action_family(
        registry, "link_people",
        inputs=[InputSpec("a", "instance"), InputSpec("b", "instance", required=False)],
        effects=[Effect(op="add_edge", family="person_links")],
    )
    inputs = {
        "a": InstanceRef(TypeRef("tenant_a", "entity", "person"), "1"),
        "b": InstanceRef(TypeRef("default", "entity", "person"), "2"),
    }
    both = await registry.record_invocation(
        "link_people", inputs, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="user:sd",
        observed_effects=[
            Effect(op="add_edge", family="person_links", namespace="tenant_a"),
            Effect(op="add_edge", family="person_links", namespace="default"),
        ],
    )
    assert "edge_family_retired:person_links" in both.warnings, (
        "an edge that reached a withdrawn family is warned about however many live "
        "families it also reached",
        both.warnings,
    )
    only_live = await registry.record_invocation(
        "link_people", inputs, actor="user:sd", outcome="applied",
        gate_verdict="allowed", approved_by="user:sd",
        observed_effects=[
            Effect(op="add_edge", family="person_links", namespace="default")
        ],
    )
    assert not [
        w for w in only_live.warnings if w.startswith("edge_family_retired")
    ], ("...and an edge that reached only live families is not warned about",
        only_live.warnings)

@pytest.mark.requires_capability("stores_attributes", "stores_events")
async def test_c19_92_projection_reads_its_pool_to_exhaustion_and_says_so_when_it_cannot(
    adapter, make_registry
):
    """Rule **10-11**. **Found independently by BOTH remaining lenses of round 3** — the
    integrator graded it BLOCKING, the fix-auditor MAJOR — and it is a defect in
    `C19-88`, one commit old.

    `projection` built its POOL from a single un-paged `list_types` while `_scope_census`
    paged the same scope to exhaustion **in the same call**. Three wrongs in one answer:
    `counts` short by most of the scope; `over_by=0` saying *everything fits* about a
    scope §10 exists to say does not; and `why_incomplete` **positively asserting**
    *"groups no family in this scope carries"* about groups families carry. And a
    truncated pool **refused a live group as a typo** — *we could not find it* turned
    into a refusal, in the method whose own comment forbids exactly that.

    Also the **fourth** empty cause rule 10-11 did not enumerate: a scope of active rows
    that DECLARE no family said nothing at all.
    """
    registry = await make_registry(adapter)
    for i in range(4):
        await action_family(
            registry, f"verb_{i}", reachability=["ingest"], namespace="agency"
        )
    await action_family(registry, "zzz_rare_one", reachability=["rare"], namespace="agency")

    whole = await registry.projection("s", budget=10, order=("ingest", "rare"), namespace="agency")
    assert whole.counts == {"ingest": 4, "rare": 1}, whole.counts

    paged = await make_registry(AsyncDegradedAdapter(adapter, page_cap=2, page_cursor=True))
    honest = await paged.projection("s", budget=10, order=("ingest", "rare"), namespace="agency")
    assert not isinstance(honest, Refusal), honest
    assert honest.counts == {"ingest": 4, "rare": 1}, (
        "the pool is read to exhaustion, exactly as the census beside it is",
        honest.counts,
    )
    # ...and a live group is never a typo on a backend that simply pages.
    rare = await paged.projection("s", budget=10, order=("rare",), namespace="agency")
    assert not isinstance(rare, Refusal), (
        "`zzz_rare_one` is registered, active and declares `rare`", rare
    )

    # A read that could NOT finish says so, and asserts nothing about the scope.
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=2))
    short = await capped.projection("s", budget=10, order=("rare",), namespace="agency")
    assert not isinstance(short, Refusal), short
    assert "could not be read to exhaustion" in (short.why_incomplete or ""), (
        short.why_incomplete
    )
    assert "groups no family in this scope carries" not in (short.why_incomplete or ""), (
        "a truncated read makes no positive claim about what the scope carries",
        short.why_incomplete,
    )

@NEEDS_INVOCATIONS
async def test_c19_93_the_review_fallback_clause_divides_by_the_rows_it_examined(
    adapter, make_registry
):
    """Rule **6-12**. **Found independently by both remaining lenses of round 3**,
    MINOR — a defect in `C19-89`, one commit old.

    `judged_live` counted the pre-filter loop and the denominator was the POST-filter
    row count, so the clause printed **`5 of 0 row(s)`** — an arithmetic impossibility
    attached to an empty queue, in the sentence whose whole justification is that *some*
    and *all* are different facts to an operator draining one.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "auto_verb", approval_mode="auto")
    for _ in range(3):
        assert not isinstance(
            await registry.record_invocation(
                "auto_verb", {}, actor="user:sd", outcome="applied",
                approved_by="user:sd",
            ),
            Refusal,
        )

    class _NoPolicyOfRecord:
        def __init__(self, inner):
            object.__setattr__(self, "inner", inner)

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def __setattr__(self, name, value):
            setattr(self.inner, name, value)

        async def find_invocations(self, **kwargs):
            page = await self.inner.find_invocations(**kwargs)
            return type(page)(
                **{
                    **page.__dict__,
                    "records": tuple(
                        type(r)(**{**r.__dict__, "declared_policy": {}})
                        for r in page.records
                    ),
                }
            )

    blind = await make_registry(_NoPolicyOfRecord(adapter))
    # every row is `auto` mode, so `unreviewed=True` keeps NONE of them
    out = await blind.invocations(unreviewed=True)
    assert not isinstance(out, Refusal), out
    assert out.known == 0, out.known
    assert "3 of 3 row(s) examined" in (out.why_incomplete or ""), (
        "the denominator is what this call LOOKED at, not what it kept",
        out.why_incomplete,
    )

def test_c19_94_the_flat_form_consequence_is_asked_of_parse_ref_not_classified():
    """Rule **2.5-13**. **MINOR, round 3's own fix-auditor lens** — a defect in
    `C19-90`, one commit old.

    It hard-coded ``field == "namespace" and separator == ":"`` and was right about
    **one of three identity segments**: a ``:`` anywhere before the ``#`` yields four
    colon-separated segments, so `parse_ref` **raises** for a `:` in `name`, in `kind`
    and in an `EdgeRef.family` too. **[Observed]** all three said *"reads back as a
    DIFFERENT reference"* while `parse_ref` raised.

    The function ASKS now instead of classifying — a case analysis over
    ``(field, separator)`` is a second home for `parse_ref`'s grammar, which is
    `EDGES.md` §2.4's own objection, and it is what went stale here within one commit.
    """
    from ontoloche.actions import EdgeRef, flat_form_problem

    misreads = [TypeRef("beacon", "entity", "person#p-1")]
    raises = [
        TypeRef("org:beacon", "entity", "person"),
        TypeRef("beacon", "entity", "person:extra"),
        TypeRef("beacon", "ent:ity", "person"),
        EdgeRef("beacon", "person:links", "e-1"),
    ]
    for ref in misreads:
        why = flat_form_problem(ref)
        assert why and "DIFFERENT reference" in why, (ref, why)
        assert parse_ref(ref_key(ref)) != ref, "and the misreading is real"
    for ref in raises:
        why = flat_form_problem(ref)
        assert why and "RAISES" in why, (ref, why)
        assert "DIFFERENT reference" not in why, (
            "nothing is misread here; the row cannot be read at all", ref, why
        )
        with pytest.raises(ValueError):
            parse_ref(ref_key(ref))

@pytest.mark.requires_capability("stores_attributes", "stores_events")
async def test_c19_95_consumers_at_risk_reads_one_report_per_family_and_names_what_it_could_not(
    adapter, make_registry
):
    """Rule **10-5**. **MINOR, round 3's integrator lens.**

    `_consumer_report` was recomputed **inside the predicate loop**, so a family
    declaring four predicates read the consumer table four times for an answer that does
    not change — **[Observed]** five `find_consumers` calls where two suffice, the
    resulting tuple identical, on the call §10.1 measures at 222 families.

    And the half that IS an answer: an evicted family `get_type` cannot return
    contributed **nothing and said nothing**, so *no consumer is at risk* and *we could
    not look* were the same tuple. §10's `complete=False` covers the casualty list being
    a floor; it does not cover the registry failing to read a row it had just enumerated.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "early_verb", reachability=["early"], namespace="ns")
    await action_family(registry, "late_verb", reachability=["late"], namespace="ns")

    # `budget=1` admits the first ordered group and evicts the second.
    report = await registry.projection(
        "s", budget=1, order=("early", "late"), namespace="ns"
    )
    assert not isinstance(report, Refusal), report
    assert report.fits == ("early",) and report.would_evict == ("late",), report

    class _CannotReRead:
        def __init__(self, inner):
            object.__setattr__(self, "inner", inner)

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def __setattr__(self, name, value):
            setattr(self.inner, name, value)

        async def get_type(self, namespace, name, *, kind=None):
            if kind == "action" and name == "late_verb":
                return None
            return await self.inner.get_type(namespace, name, kind=kind)

    blind = await make_registry(_CannotReRead(adapter))
    short = await blind.projection("s", budget=1, order=("early", "late"), namespace="ns")
    assert not isinstance(short, Refusal), short
    assert "could not be re-read" in (short.why_incomplete or ""), (
        "*no consumer is at risk* and *we could not look* must not be the same answer",
        short.why_incomplete,
    )
    assert "late_verb" in (short.why_incomplete or ""), short.why_incomplete

@NEEDS_INVOCATIONS
async def test_c19_96_a_review_says_whether_the_invocation_was_ever_in_a_queue(
    adapter, make_registry
):
    """§6.5. **MINOR, round 3's integrator lens.**

    `review_invocation` accepts a review of an `auto`-mode invocation that was never in
    any queue — and it **should**: refusing to record a review a person performed is the
    answer §2.5 calls *the worst available* one call along, and a steward may
    legitimately review anything. What was wrong is that the resulting event was
    **indistinguishable from a genuine drain** — **[Observed]** ``queue before: []`` and
    an `invocation_reviewed` standing on a row §5.2 never enqueued.

    The **mode of record** is the operand, not the family's mode today: this event
    describes the moment the gate judged, which is rule 3-8's own reason.
    """
    registry = await make_registry(adapter)
    await action_family(registry, "auto_verb", approval_mode="auto")
    await action_family(registry, "review_verb", approval_mode="review")

    never_queued = await registry.record_invocation(
        "auto_verb", {}, actor="user:sd", outcome="applied", approved_by="user:sd",
    )
    queued = await registry.record_invocation(
        "review_verb", {}, actor="user:sd", outcome="applied", approved_by="user:sd",
    )
    assert not isinstance(never_queued, Refusal) and not isinstance(queued, Refusal)

    before = await registry.invocations(unreviewed=True)
    assert [i.invocation_id for i in before.invocations] == [queued.invocation_id], (
        "the auto-mode row was never in the queue", before.invocations
    )

    for filed in (never_queued, queued):
        assert not isinstance(
            await registry.review_invocation(filed.invocation_id, reviewed_by="user:carol"),
            Refusal,
        ), "a steward may review anything, and refusing to record it is the worse answer"

    events = {}
    for filed, family in ((never_queued, "auto_verb"), (queued, "review_verb")):
        rows = [
            e
            for e in await registry.adapter.read_events(
                "default", invocation_id=filed.invocation_id
            )
            if e.event == "invocation_reviewed"
        ]
        assert rows, family
        events[family] = rows[0].detail

    assert events["review_verb"]["was_queued"] is True, events["review_verb"]
    assert events["auto_verb"]["was_queued"] is False, (
        "a review of something never enqueued must not read as a queue drain",
        events["auto_verb"],
    )
    assert events["auto_verb"]["approval_mode_of_record"] == "auto", events["auto_verb"]
