# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c12_foundry_import.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C12 -- the Foundry import mapping, and the fourth door into the kill row (13). From 0.3 consequence 2 / INTERFACE.md 2.5.

The mapping is stated in the interface rather than left to an importer, so it is tested
here. It lands on ``AsyncRegistry.import_types``, a method beyond the twelve, because no 5.x
call performs it -- deviation D-8 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations
import pytest
from open_ontology.types import Consumer, Evidence, Refusal, ResolveContext, TypeEntry
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


FOUNDRY_ROWS = [
    {
        "name": "flight",
        "status": "active",
        "definition": "a scheduled aircraft movement",
        "apiName": "Flight",
        "rid": "ri.ontology.main.object-type.1",
        "visibility": "NORMAL",
        "groups": ["ops", "planning"],
    },
    {
        "name": "gate_assignment",
        "status": "experimental",
        "definition": "a provisional gate allocation",
        "apiName": "GateAssignment",
        "rid": "ri.ontology.main.object-type.2",
        "visibility": "PROMINENT",
        "groups": ["ops"],
    },
    {
        "name": "legacy_slot",
        "status": "deprecated",
        "definition": "the pre-2024 slot model",
        "apiName": "LegacySlot",
        "rid": "ri.ontology.main.object-type.3",
        "visibility": "HIDDEN",
        "groups": [],
    },
]

@pytest.fixture
async def imported(registry):
    await registry.import_types(FOUNDRY_ROWS)
    return registry

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_01_experimental_becomes_active_plus_a_predicate_never_proposed(imported):
    """`proposed` here means *no one has approved it*; a Foundry experimental type has
    been approved and is in use. Collapsing them silently un-approves a customer's live
    vocabulary."""
    entry = await imported.list_types(include_retired=True, status=None, namespace=None)
    by_name = {t.name: t for t in entry.types}

    assert by_name["gate_assignment"].status == "active"
    assert by_name["gate_assignment"].status != "proposed"
    assert "experimental" in by_name["gate_assignment"].predicates
    assert "experimental" not in by_name["flight"].predicates
    assert [t.name for t in (await imported.list_types(predicate="experimental")).types] == [
        "gate_assignment"
    ]

async def test_c12_02_deprecated_becomes_retired_with_the_reason_recorded(imported, adapter):
    rec = await adapter.get_type("default", "legacy_slot")
    assert rec.status == "retired"
    assert rec.retire_reason == "imported: foundry deprecated"

async def test_c12_03_foreign_identifiers_land_in_provenance_not_in_fields_of_our_own(imported):
    provenance = await imported.provenance("flight")
    assert provenance.imported_from == {
        "system": "foundry",
        "apiName": "Flight",
        "rid": "ri.ontology.main.object-type.1",
    }
    entry = [t for t in (await imported.list_types()).types if t.name == "flight"][0]
    assert "apiName" not in entry.attributes
    assert "rid" not in entry.attributes
    assert entry.name == "flight", "our identity is our own name, not theirs"

@pytest.mark.requires_capability("stores_attributes")
async def test_c12_04_visibility_and_groups_land_in_attributes(imported):
    entry = [t for t in (await imported.list_types()).types if t.name == "gate_assignment"][0]
    assert entry.attributes["visibility"] == "PROMINENT"
    assert entry.attributes["groups"] == ["ops"]

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_05_an_import_does_not_un_retire_a_local_name(registry, adapter):
    """**The fourth door into mechanism 4, and it was open.** Row 3e, second
    adversarial round.

    `import_types` writes a fresh `TypeRecord` per row, so a name this deployment had
    **retired** came back `active` with `retire_reason`, `retired_by`, `retired_at` and
    `successor` all wiped, `created_by` reset to `seed`, definition and provenance
    overwritten -- in one call, with **none** of §5.9b's three guards and no
    `reinstated` event. That falsified two sentences: §5.9b's claim that mechanism 4
    "was unreachable through the surface", and its stated cost that a
    `stores_events=False` store "cannot un-burn a name".

    A retired row is a governance decision this deployment made; a foreign dump saying
    the word is active is not a reversal of it. The behaviour is now `propose_type`'s,
    verbatim (§5.9, `C4-08`): the retired entry comes back carrying
    `name_previously_retired` and **nothing is written**. `reinstate` is the call that
    reverses a retirement, and it is the call that carries the guards.
    """
    await seed(registry, "cycle_track", definition="A DOT bike facility, current term.")
    await seed(registry, "bike_lane", definition="A DOT bike facility, older term.")
    await registry.retire(
        "bike_lane", "superseded by cycle_track", retired_by="user:tlc",
        successor="cycle_track",
    )

    imported = await registry.import_types(
        [{"name": "bike_lane", "status": "active", "definition": "from the dump"}]
    )
    assert len(imported) == 1
    assert imported[0].status == "retired", "an import does not reverse a retirement"
    assert "name_previously_retired" in imported[0].warnings

    stored = await adapter.get_type("default", "bike_lane", kind="entity")
    assert stored is not None and stored.status == "retired"
    assert getattr(stored, "retire_reason", None) == "superseded by cycle_track", (
        "and the tombstone was not overwritten"
    )
    assert sorted([t.name for t in (await registry.list_types()).types]) == [
        "cycle_track",
        "equivalent_to",  # seeded at store creation -- EDGES.md 3.1
    ]

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_06_an_import_does_not_retire_a_type_something_still_gates_on(registry):
    """**The mirror of `C12-05`, and it was open.** Row 3e, third adversarial round.

    `retire()` refuses `live_consumers` when something still gates on the type
    (`INTERFACE.md` §5.9). A Foundry `deprecated` row did the identical act with **no
    refusal, no warning and no `retired` event** -- so `PACKAGE.md` §3.6's rule that a
    destructive change nobody can audit is refused was bypassed on every backend, and
    `consumers()` went on naming the retired type as gated.
    """
    from open_ontology.types import Consumer

    await seed(registry, "commentable", kind="predicate", definition="a code path accepts it")
    await seed(registry, "billable", predicates=["commentable"], definition="a billable unit")
    await registry.register_consumer(
        Consumer(id="billing.charge", gate="commentable", on_unknown="drop")
    )
    assert (await registry.retire("billable", "no", retired_by="user:sd")).reason == "live_consumers"

    out = await registry.import_types([{"name": "billable", "status": "deprecated"}])
    assert out[0].status == "active", "the same act through an import is refused too"
    assert "import_refused:live_consumers" in out[0].warnings

async def test_c12_07_source_version_survives_the_import(registry):
    """R21 on the ingestion path, which is UC3's actual wedge (`INTERFACE.md` §2.4a).

    A dump has a version, and §10b.5's whole finding is that it had nowhere to go.
    Dropping it from `import_types`' `Provenance` ran the whole suite green until this
    -- row 3e, third adversarial round.
    """
    out = await registry.import_types(
        [{"name": "tree_census_record", "status": "active",
          "definition": "one row of the street tree census",
          "source_version": "2017-10-04"}]
    )
    assert out[0].provenance.source_version == "2017-10-04"
    assert (await registry.provenance("tree_census_record")).source_version == "2017-10-04"

async def test_c12_08_an_imported_alias_cannot_collapse_two_predicate_identities(registry):
    """**`ROADMAP.md`'s kill row, FOURTH trip -- found by `check_merge_guard.py`'s own
    caller enumeration, which is the artefact row 4c was told to build instead of a
    fourth patch.**

    The three before it: `0e89037` (`merge_types`, an unknowable extent compared equal),
    `fcb05b3` (`merge_types`, two EMPTY extents compared byte-identical), `05b8e04`
    (`retire(successor=)`, the collapse reached by a call carrying none of the merge's
    guards). The supervisor's diagnosis after the third was *a guard written for one
    call, over a fact that more than one call can change* -- and the ruling was that the
    fix owed is a checker that enumerates the **callers**.

    It found this on its first run. **[Observed, row 4c]**, reproduced end to end
    against the shipped registry:

    * `commentable` and `searchable` are two live predicates whose extents are
      non-empty and genuinely different (`{note}` and `{doc}`);
    * `merge_types` refuses that pair **non-overridably**, under every acknowledgement;
    * `commentable` is retired -- an ordinary, permitted governance act, no successor;
    * `import_types` writes `aliases: ["commentable"]` onto `searchable` with **no
      refusal, no warning and no acknowledgement**;
    * `resolve_type("commentable")` goes from `proposal / None / 0.4762` to **`existing
      / searchable / 1.0`**, a confidence `INTERFACE.md` §5.3 calls a registry
      GUARANTEE, while the two extents stay different.

    **Why `alias_collision` did not see it.** That guard refuses an alias that is a
    **live** entry's name, because it exists to stop *two active entries holding one
    word between them* (§5.9b). A retired name is not a live entry -- but **a retired
    predicate name still resolves, and a retired predicate still has an extent.** The
    guard was written for a collision; the failure is a collapse. Same write, different
    question.

    The diagnosis widens once more: the fourth caller reaches the collapse through a
    different **field** (`aliases` rather than `successor`) as well as through a
    different call, so both fields carry §5.10's identity guards now.
    """
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable"])
    await seed(registry, "doc", predicates=["searchable"])
    if not registry.caps.indexes_membership:
        # Rule U makes the answer here the same for a different reason -- an extent that
        # cannot be computed is not an identical extent -- so the assertion below still
        # holds and the fixture's premise does not. Asserted rather than skipped.
        pass

    refused = await registry.merge_types(
        "commentable", "searchable", "they look alike", merged_by="user:sd",
        acknowledge=[
            "definitions_diverge", "no_consumer_evidence", "retired_operand",
            "predicate_merge", "kind_mismatch",
        ],
    )
    assert isinstance(refused, Refusal) and refused.reason == "predicate_merge", refused
    assert refused.detail["overridable"] is False

    retired = await registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement, so the "
            f"fixture's first step is unreachable here: {retired.reason}"
        )

    entry = (await registry.import_types(
        [
            {
                "name": "searchable",
                "kind": "predicate",
                "definition": "a capability",
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    ))[0]
    assert "import_refused:predicate_merge" in entry.warnings, (
        "the alias door reaches the same collapse merge_types refuses non-overridably, "
        "and it must be refused there too -- this is the kill row's fourth trip"
    )
    assert "commentable" not in (entry.aliases or ()), "refused, and nothing written"

    resolution = await registry.resolve_type(
        "commentable", ResolveContext(), tier="unspecified"
    )
    assert not (
        resolution.outcome == "existing" and resolution.type == "searchable"
    ), (
        "`resolve_type('commentable')` must not answer `searchable` at confidence 1.0 -- "
        "that IS the merge, whichever call wrote the alias"
    )

@pytest.mark.requires_capability("stores_aliases")
async def test_c12_09_an_imported_alias_between_identical_extents_is_still_written(registry):
    """The other half of `C12-08`, and the half a careless fix deletes.

    **The guard is narrowed, not banned.** `INTERFACE.md` §5.10 refusal #2 permits a
    predicate merge when the two extents are **non-empty and byte-identical** -- that is
    the whole content of `C10-09`, which narrowed the guard rather than closing the
    operation. An `import_types` alias between two predicates in exactly that state is a
    legal write, and a fix that refused every predicate alias would pass a test suite
    that only asserted refusals while deleting an operation the specification allows.

    A non-predicate alias is likewise untouched: the identity guards are about what a
    collapse would ASSERT, and two entities sharing a word is `alias_collision`'s
    question, not this one's.
    """
    if not registry.caps.indexes_membership:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend declares indexes_membership=False, so every "
            "extent is unknowable and Rule U refuses the write for a different reason. "
            "`C12-08` asserts that half; this one needs a computable extent as "
            "scaffolding, not as its subject"
        )
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable"])

    retired = await registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement: "
            f"{retired.reason}"
        )

    entry = (await registry.import_types(
        [
            {
                "name": "searchable",
                "kind": "predicate",
                "definition": "a capability",
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    ))[0]
    assert not any(w.startswith("import_refused:") for w in entry.warnings), entry.warnings
    assert "commentable" in entry.aliases, (
        "two predicates with non-empty identical extents may be collapsed -- C10-09 "
        "narrowed the guard, and a fix that banned the operation would pass a checker "
        "that only tested refusals"
    )

@pytest.mark.requires_capability("stores_aliases")
async def test_c12_10_the_identity_guard_survives_a_word_registered_under_two_kinds(registry):
    """`PACKAGE.md` §4.1 blesses one word under two kinds. Row 4c, first round.

    `C0-11` pins that `get_type(namespace, name)` with **no** `kind` **raises**
    `AmbiguousKind` there — that is the adapter refusing to guess, and it is correct.
    Row 4c's new identity guard called it exactly that way, so **a Foundry dump whose
    alias names a two-kind word blew the exception out of `import_types`** — a call
    whose whole contract is *"an import cannot return a `Refusal`; it returns entries"*
    — aborting the batch with earlier rows already committed.

    The guard's question is per-kind anyway, so a query answers it without asking the
    adapter to choose. **The fix for a guard that cannot look is never to look less
    carefully.**

    The second half is the shape of what comes back. `_refused_import` hard-coded
    `kind="entity"`, so a refused `kind="predicate"` import returned an entry describing
    itself as an entity while its own `import_refused:predicate_merge` reason said
    otherwise — two answers about `kind`, in the field `INTERFACE.md` §2.3's whole
    argument rests on.
    """
    await seed(registry, "facility", definition="a nursing home")
    await seed(registry, "facility", kind="value_set", definition="the set of facility codes")
    await seed(registry, "surveyed", kind="predicate", definition="a capability")
    await seed(registry, "home", predicates=["surveyed"])

    entries = await registry.import_types(
        [
            {
                "name": "inspected",
                "kind": "predicate",
                "definition": "a capability",
                "aliases": ["facility"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    )
    assert len(entries) == 1, "the batch completed rather than raising"
    entry = entries[0]
    assert any(w.startswith("import_refused:") for w in entry.warnings), entry.warnings
    assert entry.kind == "predicate", (
        "a refused import is shaped like the row it refused, not like an entity -- the "
        "reason and the shape must agree about `kind`"
    )

    # And a batch whose aliases are clean still imports, so the guard did not simply
    # start refusing everything on a two-kind store.
    ok = (await registry.import_types(
        [
            {
                "name": "annotated",
                "kind": "predicate",
                "definition": "a capability",
                "aliases": ["previously_annotated"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    ))[0]
    assert not any(w.startswith("import_refused:") for w in ok.warnings), ok.warnings
    assert ok.aliases == ("previously_annotated",)
    assert ok.kind == "predicate"

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c12_11_an_imported_row_declaring_a_moved_predicate_is_warned(
    adapter, make_registry
):
    """**Ruling R55, row 4d, at the SECOND write door.**

    A Foundry dump names its own predicates, and nothing here checked them against this
    deployment's vocabulary — so an imported row declaring a word that had been **merged
    away** landed silently in the survivor's identity. It is the same fact `C4-11` asserts
    at `propose_type`, reported the same way, because §2.5's rule is that an import is a
    vocabulary arriving **already decided** by whoever ran the source system: warning is
    all this call may do about a declaration, exactly as it is for `predicate_requires_
    review`.

    The negative is asserted too — an imported row declaring a live, unmerged predicate
    carries no such warning.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable", "untouched"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable"])
    merged = await registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert hasattr(merged, "aliases_added"), merged

    entries = await registry.import_types(
        [
            {"name": "memo", "definition": "a short note", "predicates": ["commentable"]},
            {"name": "card", "definition": "a card", "predicates": ["untouched"]},
        ],
        namespace="default",
    )
    moved, plain = entries
    assert "declared_predicate_merged:commentable:searchable" in moved.warnings, (
        "the dump declared a word this deployment merged away; the row landed in "
        "`searchable`'s identity and said nothing about it"
    )
    assert moved.predicates == ("commentable",), (
        "the declaration is WRITTEN -- 2.5 imports a vocabulary already decided, and "
        "refusing it would make this call reject a customer's live vocabulary"
    )
    assert not [w for w in plain.warnings if w.startswith("declared_predicate_merged")]

    # And the survivor's extent holds both of them, which is ruling R54's half of the
    # same seam: the fact is now VISIBLE as well as announced.
    listing = await registry.list_types(predicate="searchable", namespace="default")
    assert {"note", "memo", "card"} & {t.name for t in listing.types} == {"note", "memo"}

@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
async def test_c12_12_an_imported_row_whose_name_is_spoken_for_is_refused(adapter, make_registry):
    """**The row's own NAME is a word too, and this door never asked.** Row 4d, round 1.

    `import_types`' alias block runs only `if incoming:` — only when the imported row
    carries aliases of its own. So a row whose **name** a live entry already answers to,
    carrying no aliases, was written with no refusal and no warning, and two active
    entries came to hold one word between them.

    `propose_type` refuses that exact act (`alias_collision`, non-overridable, row 4c's
    Door-4 fix). The sibling write door did not ask, which is the third trip's diagnosis
    on a fourth axis: **a guard written for one call, over a fact more than one call can
    change.** `C16-06`'s whole-store invariant, in one ordinary import row.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["searchable"])
    await registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentable"], "status": "active"}],
        namespace="default", kind="predicate",
    )

    # The control: `propose_type` refuses this, and has since row 4c.
    refused = await registry.propose_type(
        "commentable", "a capability", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(refused, Refusal) and refused.reason == "alias_collision"

    entry = (await registry.import_types(
        [{"name": "commentable", "kind": "predicate", "definition": "a capability",
          "status": "active"}],
        namespace="default", kind="predicate",
    ))[0]
    assert "import_refused:alias_collision" in entry.warnings, (
        "the sibling write door must give the same answer to the same act"
    )
    live = (await registry.list_types(namespace="default")).types
    holders = [t.name for t in live if t.name == "commentable" or "commentable" in (t.aliases or ())]
    assert holders == ["searchable"], (
        f"two live entries answering to one word is mechanism 4 itself: {holders}"
    )

@pytest.mark.requires_capability("stores_aliases")
async def test_c12_13_a_legal_import_is_not_banned_by_a_backend_that_pages(adapter, make_registry):
    """**The guard is narrowed, not banned — for the third time in one row.** Round 2.

    Round 1 replaced `_alias_identity_breach`'s one-row `name_in` probe with an
    **unfiltered namespace scan**, and fed that scan's partial `why` into a
    **non-overridable** refusal. So on any backend that caps an unlimited query —
    `PACKAGE.md` §3.3 explicitly permits one — an import row carrying a **brand-new,
    unheld** alias came back `import_refused:kind_mismatch`: a legal row refused, with a
    reason naming two kinds where no two kinds are involved.

    That is what round 1 had learned one call along at `_alias_holder` (*refusing does
    not narrow the guard, it bans the call on every paging backend*), repeated inside the
    function round 1 wrote. `import_types` is UC1 Tenshen's Foundry migration path and
    UC3's Socrata shape, so the banned call is the ingestion wedge.

    The probe is bounded now — `{word, identity_key(word)}`, never a scan — and the row
    is **written**, with the truncation reported rather than suppressed.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for i in range(6):
        await seed(registry, f"row_{i}", definition="a row")

    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=3), approval_policy="auto")
    entry = (await capped.import_types(
        [{"name": "imported_here", "kind": "entity", "definition": "a row",
          "aliases": ["a_brand_new_word"], "status": "active"}],
        namespace="default", kind="entity",
    ))[0]
    assert not any(w.startswith("import_refused:") for w in entry.warnings), (
        f"nothing holds `a_brand_new_word`; refusing this bans the ingestion path on "
        f"every paging backend: {entry.warnings}"
    )
    assert entry.status == "active" and "a_brand_new_word" in (entry.aliases or ())

    # The truncation is REPORTED, exactly once.
    said = [w for w in entry.warnings if w.startswith("alias_check_incomplete:")]
    assert len(said) == 1, f"reported once, not zero and not twice: {entry.warnings}"

@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
async def test_c12_14_the_ninth_trip_a_row_that_does_not_exist_yet_has_no_consumers_to_read(
    adapter, make_registry
):
    """**The kill row's NINTH trip**, found by row 6b's first adversarial lens -- which is
    the review ruling **R53** and the seventh-trip countersignature say those guards
    never got.

    `_alias_identity_breach` compared consumer sets by reading the row being aliased ONTO
    -- and `import_types` routinely creates that row **in the same call that writes the
    alias**. With no row to read, the shipped guard fell back to comparing the *other*
    row against **itself**, so 5.10's refusal #1 was equal by construction and **could
    not fire**. Row 6b's extraction found the fallback, named it, and raised it as a
    question; the lens then walked it, on the kill row's own noun:

    1. `commentable` and `gamma` are predicates whose written extents are **non-empty and
       identical**, so refusal **#2 passes honestly** -- this is not a #2 evasion;
    2. `commentable` declares `meta_p` and a consumer gates on `meta_p`, so
       `commentable.gates_on == ['svc:meta']` and `gamma`'s is empty. **The gate is not
       the aliased word**, so the alias cannot equalise them;
    3. `commentable` is retired -- *an ordinary, permitted governance act*, the fourth
       trip's own words;
    4. `import_types` creates `gamma` carrying `aliases: ["commentable"]`. **Written,
       with no refusal and no warning about the collapse**;
    5. `resolve_type("commentable")` -> **`gamma` at confidence 1.0**, which
       `INTERFACE.md` 5.3 calls a **guarantee** -- on a pair `merge_types` refuses
       `different_consumer_sets` **non-overridably** under all five acknowledgements, and
       that `retire(successor=)` refuses too.

    **[Observed]** on both fully-capable legs and on the async mirror, with the full suite
    green and `check_merge_guard.py` exiting 0 -- the **fifth consecutive** trip whose
    question that checker's fixtures could not pose.

    **The fix is a computed set, not a refusal, and the distinction is this row's own
    most-repeated lesson.** *A guard with nothing to compare has not said the collapse is
    safe* is `successor_unregistered`'s rule (trip 7) and would have been the obvious
    transposition -- and it is **wrong here**, because there IS something to compare: the
    incoming row declares its own `predicates`, so the consumer set it will have the
    moment it is written is a **fact**. Refusing instead would ban `import_types` from
    writing any aliased new row on any backend, which is `C10-09`'s lesson and `C3-13`'s
    and `C12-13`'s: *never turn "we could not finish looking" into a refusal* -- and
    worse, this would turn **"we did not look"** into one.
    """
    registry = await make_registry(adapter)
    await registry.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    await seed(registry, "meta_p", kind="predicate")
    await seed(registry, "commentable", kind="predicate", predicates=["meta_p"])
    for member in ("aaa_note", "bbb_memo"):
        await seed(registry, member, predicates=["commentable"])

    # The two extents are non-empty and IDENTICAL, so refusal #2 has nothing to say --
    # which is what makes this a #1 walk rather than another #2 walk.
    assert (await registry._written_extent("default", "commentable", include_retired=True))[0] == (
        "aaa_note",
        "bbb_memo",
    )
    assert {c.id for c in (await registry.consumers("commentable")).gates_on} == {"svc:meta"}

    retired = await registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement, so the "
            f"fixture's first step is unreachable here: {retired.reason}"
        )

    entry = (await registry.import_types(
        [
            {
                "name": "gamma",
                "kind": "predicate",
                "definition": "a capability, imported with an alias",
                "predicates": [],
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    ))[0]
    assert "import_refused:different_consumer_sets" in entry.warnings, entry.warnings
    assert "commentable" not in (entry.aliases or ()), "refused and wrote the alias anyway"

    resolution = await registry.resolve_type(
        "commentable", ResolveContext(source="the C12-14 fixture"), tier="opus"
    )
    assert resolution.outcome != "existing", (
        "the ninth trip: a capability predicate merged as a duplicate, at the confidence "
        "INTERFACE.md 5.3 calls a guarantee"
    )

    # **The control, and it is what makes this a KILL-ROW walk rather than a style
    # complaint: one registry may not answer two ways about one claim.** Asked directly,
    # `merge_types` refuses this exact pair NON-OVERRIDABLY under all five
    # acknowledgements. It is asked on a second store because the fix means `gamma` was
    # never written on the first -- which is the point.
    control = await make_registry(adapter)
    await control.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    await seed(control, "meta_p", kind="predicate")
    await seed(control, "commentable", kind="predicate", predicates=["meta_p"])
    await seed(control, "gamma", kind="predicate")
    for member in ("aaa_note", "bbb_memo"):
        await seed(control, member, predicates=["commentable", "gamma"])
    refusal = await control.merge_types(
        "commentable",
        "gamma",
        "the same claim, asked directly",
        merged_by="user:sd",
        acknowledge=[
            "definitions_diverge",
            "no_consumer_evidence",
            "retired_operand",
            "predicate_merge",
            "kind_mismatch",
        ],
    )
    assert isinstance(refusal, Refusal), f"the control merge was ALLOWED: {refusal!r}"
    assert refusal.reason == "different_consumer_sets", refusal
    assert refusal.detail["overridable"] is False

@pytest.mark.requires_capability("stores_aliases")
async def test_c12_15_a_new_row_whose_consumers_agree_is_still_aliased(adapter, make_registry):
    """`C12-14`'s narrowing, and it is the half a careless fix deletes.

    The guard is **narrowed, not banned**: an import that creates a row whose computed
    consumer set MATCHES the word it is aliasing is still written. Every guard fix in this
    repository ships with this assertion beside it -- `C10-09`, `C12-09`, `C10-19`,
    `C4-14` -- because *refusing everything passes a checker that only tests refusals and
    deletes a legal operation*.
    """
    registry = await make_registry(adapter)
    await registry.register_consumer(
        Consumer(id="svc:c", gate="commentable", on_unknown="drop", owner="ops")
    )
    await seed(registry, "commentable", kind="predicate")
    await seed(registry, "note", kind="entity", predicates=["commentable"])
    retired = await registry.retire("note", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement: "
            f"{retired.reason}"
        )

    entry = (await registry.import_types(
        [
            {
                "name": "memo",
                "kind": "entity",
                "definition": "a note by another name",
                # The SAME declared predicates, so the computed gate set is the same one.
                "predicates": ["commentable"],
                "aliases": ["note"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="entity",
    ))[0]
    assert not [w for w in entry.warnings if w.startswith("import_refused:")], entry.warnings
    assert "note" in (entry.aliases or ()), "the legal alias must still be written"
