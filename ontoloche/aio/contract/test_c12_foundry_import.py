# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c12_foundry_import.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C12 -- the Foundry import mapping, and the fourth door into the kill row (13). From 0.3 consequence 2 / INTERFACE.md 2.5.

The mapping is stated in the interface rather than left to an importer, so it is tested
here. It lands on ``AsyncRegistry.import_types``, a method beyond the twelve, because no 5.x
call performs it -- deviation D-8 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations
import pytest
from ontoloche.actions import action_attributes
from ontoloche.types import Consumer, Evidence, Refusal, ResolveContext, TypeEntry
from ontoloche.aio.contract._support import seed
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter
from ontoloche.aio.contract._support import foundry_fixture  # noqa: E402
from ontoloche.foundry import NO_HOME_REASONS, land  # noqa: E402
from ontoloche.foundry import source_type as foundry_source_type  # noqa: E402
from ontoloche.properties import declaration_problem, entity_declaration  # noqa: E402


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
    from ontoloche.types import Consumer

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

    The three before it: `c08998b` (`merge_types`, an unknowable extent compared equal),
    `7a0ee34` (`merge_types`, two EMPTY extents compared byte-identical), `7c26e0b`
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

    # **The truncation is REPORTED, once per SCAN, and this assertion was amended in
    # round 3.** It read `len(said) == 1`, written when this method had ONE scan that
    # could truncate. It now has two -- the tombstone NAME scan (whose truncation means a
    # tombstone may have been missed, which is the twentieth and twenty-first trips) and
    # the alias-holder scan (whose truncation means a LIVE holder may have been missed).
    # **Those are two facts, and one value for two facts is INTERFACE.md 2.3's Cause B**
    # -- the EIGHTEENTH trip's own sentence, which `merge_types` already answers by
    # naming the scan in its detail. So: at least one report, no duplicates, and a
    # caller can tell which look came up short.
    said = [w for w in entry.warnings if w.startswith("alias_check_incomplete:")]
    assert said, f"the truncation must be reported at all: {entry.warnings}"
    assert len(said) == len(set(said)), (
        f"each scan reports at most once -- a repeated line is noise, not a second "
        f"fact: {entry.warnings}"
    )

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

@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
async def test_c12_16_the_tenth_trip_the_guard_read_a_state_the_call_destroys(
    adapter, make_registry
):
    """**The kill row's TENTH trip**, found by round 2's fix-auditor lens -- pointed at
    round 1's own fixes, because this project has counted where its next defect lives.

    `C12-14` closed the case where the row being aliased ONTO does not exist yet, by
    computing its consumer set from the incoming row's declared `predicates`. **It applied
    that on one branch only.** When the row already exists the guard took the other branch
    and read `_consumer_report` off the STORED row -- *the row this same call is about to
    overwrite*, because `import_types` writes `predicates` from the incoming dict.

    So the guard evaluated a state the call destroys, and the same declared row, the same
    alias and the same final state got **two different answers depending on whether the
    name happened to exist already**:

    1. `commentable` and `gamma` are predicates with non-empty IDENTICAL extents, so
       refusal #2 passes honestly;
    2. `gamma` **already exists** declaring `meta_p`, and `svc:meta` gates on `meta_p` --
       so both gate sets read `['svc:meta']` **at guard time** and refusal #1 passes
       honestly too;
    3. `commentable` is retired -- an ordinary, permitted governance act;
    4. `import_types` writes `gamma` with `predicates: []` and
       `aliases: ["commentable"]`. **Written, unrefused, unwarned**;
    5. post-import the sets are `['svc:meta']` against `[]`, and
       `resolve_type("commentable")` answers **`gamma` at confidence 1.0** -- a pair
       `merge_types` AND `retire(successor=)` both refuse `different_consumer_sets`
       NON-OVERRIDABLY.

    **[Observed]** on sqlite, Postgres and both async legs, with the full suite green and
    `check_merge_guard.py` exiting 0 -- the sixth consecutive trip its fixtures could not
    pose.

    **It is the sixth trip's diagnosis applied to a FIX rather than to a guard** -- *a
    guard written for one call, over a fact more than one call can change* -- which is
    also the eighth trip's shape, where a published key reached five callers out of six.
    Refusal #1 now compares the sets **this write will produce**, on both branches and
    computed the same way on both sides.
    """
    registry = await make_registry(adapter)
    await registry.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    await seed(registry, "meta_p", kind="predicate")
    await seed(registry, "commentable", kind="predicate", predicates=["meta_p"])
    await seed(registry, "gamma", kind="predicate", predicates=["meta_p"])
    for member in ("aaa_note", "bbb_memo"):
        await seed(registry, member, predicates=["commentable", "gamma"])

    # Both guards pass HONESTLY on the pre-import reading -- that is the whole trap.
    assert (await registry._written_extent("default", "commentable", include_retired=True))[0] == (
        (await registry._written_extent("default", "gamma", include_retired=True))[0]
    )
    assert {c.id for c in (await registry.consumers("commentable")).gates_on} == {
        c.id for c in (await registry.consumers("gamma")).gates_on
    } == {"svc:meta"}

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
                "definition": "a capability, re-imported without its predicates",
                "predicates": [],
                "aliases": ["commentable"],
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    ))[0]
    assert "import_refused:different_consumer_sets" in entry.warnings, entry.warnings
    assert "commentable" not in (entry.aliases or ())

    resolution = await registry.resolve_type(
        "commentable", ResolveContext(source="the C12-16 fixture"), tier="opus"
    )
    assert resolution.outcome != "existing", (
        "the tenth trip: the guard read the consumer set the import was about to "
        "overwrite, and answered two ways for one final state"
    )

@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
async def test_c12_17_the_eleventh_trip_one_call_site_of_four(adapter, make_registry):
    """**The kill row's ELEVENTH trip**, found by round 3's kill-row lens — the questions
    round 2's lens never got to ask, because it died on a rate limit before reporting.

    `C12-14` and `C12-16` closed refusal #1's missing operand at `import_types`. It was
    passed at **one of `_alias_identity_breach`'s four call sites**: `retire(successor=)`,
    `reinstate` and `merge_types` all called it bare, and the async mirror was identical.
    Without it `_gates_on`'s `member_of` is empty, so **every consumer gating on a
    predicate the target row itself declares is invisible to refusal #1** — the exact
    fact trips 9 and 10 were built on.

    The walk, through `reinstate`, in seven ordinary calls and with refusal #2 passing
    honestly throughout:

    1. `commentable` and `gamma` are predicates with identical non-empty extents;
    2. `commentable` is retired — an ordinary, permitted governance act;
    3. the alias is imported and **correctly allowed**: no consumer exists yet, both gate
       sets are empty, and the write asserts nothing false;
    4. `gamma` is retired — the alias goes dormant. Also ordinary;
    5. a consumer is registered on `meta_p`, which only `gamma` declares. **The world
       moves**: the sets now differ;
    6. `reinstate("gamma")` → `TypeEntry`, **no refusal, no warning**;
    7. `resolve_type("commentable")` → **`gamma` at confidence 1.0**, up from
       `proposal / 0.4706` the call before.

    **This is the sixth trip's diagnosis applied to a FIX for the third consecutive
    round** — trip 9 the missing operand, trip 10 the operand on one branch of two, trip
    11 the operand at one call site of four.

    `declared_predicates` is a **required keyword** now, which is ruling **R64**'s
    treatment of `_extent`'s `identity` for the same reason: *no caller can take a
    reading by accident.*
    """
    registry = await make_registry(adapter)
    await seed(registry, "meta_p", kind="predicate")
    await seed(registry, "commentable", kind="predicate")
    await seed(registry, "gamma", kind="predicate", predicates=["meta_p"])
    for member in ("aaa_note", "bbb_memo"):
        await seed(registry, member, predicates=["commentable", "gamma"])

    retired = await registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement: "
            f"{retired.reason}"
        )
    legal = (await registry.import_types(
        [
            {
                "name": "gamma", "kind": "predicate", "definition": "a capability",
                "predicates": ["meta_p"], "aliases": ["commentable"], "status": "active",
            }
        ],
        namespace="default", kind="predicate",
    ))[0]
    assert not [w for w in legal.warnings if w.startswith("import_refused:")], (
        "the alias is LEGAL at this moment -- both gate sets are empty -- and a guard "
        "that refused here would be banned rather than narrowed"
    )
    assert await registry.retire("gamma", "dormant", retired_by="user:sd", force=True)

    # The world moves between the write and the reinstatement, which is trip 6's shape.
    await registry.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    assert {c.id for c in (await registry.consumers("gamma")).gates_on} == {"svc:meta"}
    assert {c.id for c in (await registry.consumers("commentable")).gates_on} == set()

    out = await registry.reinstate("gamma", "back in service", reinstated_by="user:sd")
    assert isinstance(out, Refusal), f"reinstate performed the collapse: {out!r}"
    assert out.reason == "different_consumer_sets", out
    resolution = await registry.resolve_type(
        "commentable", ResolveContext(source="the C12-17 fixture"), tier="opus"
    )
    assert resolution.outcome != "existing", (
        "the eleventh trip: a capability predicate merged as a duplicate, through the "
        "one door of four the ninth trip's fix did not reach"
    )

def test_c12_18_declared_predicates_is_a_required_keyword(adapter, make_registry):
    """`C12-17`'s narrowing, in the shape ruling **R64** chose for `_extent`.

    The eleventh trip was three callers **silently defaulting** an operand refusal #1
    cannot work without. A default is what let them: R64 made `_extent`'s `identity` a
    required keyword precisely so *no caller can take a reading by accident*, and the
    same treatment here means a fifth caller cannot arrive bare — it fails at the call,
    not at a kill-row walk two rounds later.

    Asserted by signature rather than by behaviour, because the thing being pinned is
    that **there is no default to fall back to** — a behavioural test would pass just as
    happily with one.
    """
    import inspect

    from ontoloche.aio.registry import AsyncRegistry

    parameter = inspect.signature(AsyncRegistry._alias_identity_breach).parameters[
        "declared_predicates"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty, (
        "a default here is what let three of four callers omit the operand refusal #1 "
        "cannot work without -- R64's own reasoning, one guard along"
    )

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c12_19_an_import_that_removes_a_standing_alias_says_so_and_records_it(
    adapter, make_registry
):
    """Row 6c, round 1 kill-row `m1` and round 2 kill-row `m4`, closed in round 3 —
    *an import writes `aliases` wholesale, and dropping one was silent.*

    Every word the standing row answered to and the dump does not name is **erased**,
    with no refusal, no warning and no event — including one ruling **R75** had just
    transferred there in the same store. A word that resolved at confidence 1.0 stops
    resolving, and `INTERFACE.md` §5.3 calls that confidence a guarantee.

    **[Observed, before the fix]** ``beta.aliases`` went ``('zeta',)`` → ``()`` on an
    ordinary import whose warnings were ``('predicate_requires_review',)``, with the
    `aliases_transferred` event **still standing** and asserting a fact the store no
    longer held.

    Not a refusal: removing an alias is a legitimate act and an import is a vocabulary
    arriving *already decided*, which is why this call refuses almost nothing. What it
    owes is what §5.8 asks of any correction — **say it, and record it as a new event
    rather than as an edit.**
    """
    registry = await make_registry(adapter)
    await seed(registry, "alpha", kind="predicate", definition="a capability")
    await seed(registry, "beta", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["alpha", "beta"])
    await seed(registry, "bbb_memo", predicates=["alpha", "beta"])
    await registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a capability"}],
        kind="predicate",
    )
    assert isinstance(
        await registry.retire(
            "alpha", "beta says it better", retired_by="user:sd", successor="beta",
            force=True,
        ),
        TypeEntry,
    )
    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "beta"][0]
    assert "zzz_moved" in survivor.aliases, "R75's transfer happened"

    rows = await registry.import_types(
        [{"name": "beta", "status": "active", "aliases": [], "definition": "a capability"}],
        kind="predicate",
    )
    assert rows and isinstance(rows[0], TypeEntry), rows
    assert "aliases_removed:zzz_moved" in rows[0].warnings, (
        "the call that took the word away says which word",
        rows[0].warnings,
    )
    after = [t for t in (await registry.list_types("predicate")).types if t.name == "beta"][0]
    assert "zzz_moved" not in after.aliases, "the removal itself is still permitted"

    removed = [
        e
        for e in (await registry.provenance("beta", namespace="default")).history
        if e.event == "aliases_removed"
    ]
    assert removed, (
        "INTERFACE.md 5.8 -- a correction is a NEW EVENT, never an edit; the removal "
        "half owed one too, or the transfer's own record stands alone asserting a fact "
        "the store no longer holds"
    )
    assert removed[0].detail["aliases_removed"] == ["zzz_moved"], removed[0].detail

    # ...and an import that removes NOTHING does not claim it did.
    quiet = await registry.import_types(
        [{"name": "beta", "status": "active", "aliases": [], "definition": "a capability"}],
        kind="predicate",
    )
    assert not [
        w for w in quiet[0].warnings if w.startswith("aliases_removed")
    ], ("a signal that never turns off is noise", quiet[0].warnings)

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c12_20_the_alias_diff_runs_against_the_row_this_call_overwrites(
    adapter, make_registry
):
    """Row 6c, round 3's own fix-auditor lens, MAJOR — *a defect in `C12-19`, one commit
    old, and it fabricates the very thing `C12-19` was minted to stop fabricating.*

    `standing` falls back to the EIGHTH trip's **variant-spelling** row (``r.name !=
    name``). That is right for the `name_previously_retired` and `live_consumers` guards
    — they ask *is this WORD spoken for?* — and wrong for an alias diff, which asks
    *what is this ROW losing?* With an incoming `deprecated` row the
    `name_previously_retired` branch is skipped, so the diff ran against a row the call
    never touches.

    **[Observed, before the fix]** ``beta_`` retired holding ``zzz_word``; an import of a
    `deprecated` ``beta`` answered ``('aliases_removed:zzz_word',)`` and filed the event
    on ``beta`` — while ``beta_`` **still held the word** and ``beta`` never had. A
    fabricated correction in the audit trail `INTERFACE.md` §5.8 exists to keep truthful.

    `_word_rows`' own docstring names ``borough_`` and ``commentable_`` as spellings two
    agencies normalising column headers produce, so UC3 reaches this ordinarily.
    """
    registry = await make_registry(adapter)
    await seed(registry, "beta_", kind="predicate", definition="one and the same thing")
    written = await registry.import_types(
        [{"name": "beta_", "status": "active", "aliases": ["zzz_word"],
          "definition": "one and the same thing"}],
        kind="predicate",
    )
    if not written or "zzz_word" not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the imported alias")
    assert not isinstance(
        await registry.retire("beta_", "withdrawn", retired_by="user:sd", force=True), Refusal
    )

    out = await registry.import_types(
        [{"name": "beta", "status": "deprecated", "aliases": [],
          "definition": "one and the same thing"}],
        kind="predicate",
    )
    assert out and isinstance(out[0], TypeEntry), out
    assert not [
        w for w in out[0].warnings if w.startswith("aliases_removed")
    ], ("`beta` never held `zzz_word`; `beta_` did, and this call did not touch it",
        out[0].warnings)

    every = {t.name: tuple(t.aliases or ()) for t in
             (await registry.list_types("predicate", include_retired=True)).types}
    assert every.get("beta_") == ("zzz_word",), ("the word is still where it was", every)
    assert every.get("beta", ()) == (), every

    fabricated = [
        e
        for e in (await registry.provenance("beta", namespace="default")).history
        if e.event == "aliases_removed"
    ]
    assert not fabricated, (
        "an event asserting a removal that did not happen is the class C12-19 was "
        "minted to remove, committed by C12-19 itself",
        fabricated,
    )

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c12_21_a_word_a_tombstone_answers_to_is_not_free_at_import_types(
    adapter, make_registry
):
    """THE KILL ROW'S FOURTEENTH TRIP, at the third mint door.

    `import_types` is a NAME door in its own right — it was the second door of the
    EIGHTH trip for the same reason — and it minted the identical row in the trip's own
    reproduction. Shipping the fix at `propose_type` alone would be *a fix applied at
    one call site of three*, which is the single sentence of the ninth, tenth and
    eleventh kill-row trips.

    **[Observed]** ``alpha`` retired still answering to ``zzz_moved`` by §5.8's design;
    ``import_types([{"name": "zzz_moved"}])`` wrote a live row with no refusal and no
    warning, and ``reinstate("alpha")`` was refused ``alias_collision`` for ever after —
    so ruling **R11**'s governance act was permanently unavailable through calls every
    guard permitted.

    The holder comes back with `word_previously_retired`, nothing is written, which is
    `name_previously_retired`'s own treatment at this door for the fact one field along.
    """
    registry = await make_registry(adapter)
    await seed(registry, "alpha", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["alpha"])
    written = await registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or "zzz_moved" not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = await registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")
    assert "zzz_moved" in (gone.aliases or ()), gone.aliases

    out = await registry.import_types(
        [{"name": "zzz_moved", "status": "active", "definition": "a foreign word"}],
        kind="predicate",
    )
    assert out and isinstance(out[0], TypeEntry), out
    assert out[0].name == "alpha", ("the holder comes back, not a new row", out[0].name)
    assert "word_previously_retired:alpha" in out[0].warnings, out[0].warnings
    assert not [
        t for t in (await registry.list_types("predicate", include_retired=True)).types
        if t.name == "zzz_moved"
    ], "nothing is written"

    back = await registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry), (
        "R11's governance act must still be available", back
    )

async def _tombstone_holding(registry, word="zzz_moved"):
    """A RETIRED predicate that still answers to ``word``, and nothing named ``word``."""
    await seed(registry, "alpha", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["alpha"])
    written = await registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": [word],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or word not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = await registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        # NOT REACHABLE, never a pass. `retire`'s `if force and not
        # self.caps.stores_events` refuses a destructive override that cannot be
        # written down, whichever guard it is overriding -- so on such a store this
        # fixture cannot be built at all. **Gated on the CAPABILITY**, so a store that
        # CAN record events and still refused this way is a finding and not a skip.
        #
        # The guard is narrowed to the ONE reason the capability explains, following the
        # four-file precedent rather than asserting `stores_events` under a bare
        # `isinstance(gone, Refusal)` -- which would tell a backend refusing for an
        # unrelated reason, while recording events perfectly well, that it had failed.
        # That is `C19-100`'s defect, a legal operation closed by a gate.
        assert registry.caps.stores_events is False, (
            "this backend records events, so the refusal is not a capability", gone.detail,
        )
        pytest.skip(
            "NOT REACHABLE: stores_events=False refuses the forced retire before there "
            "is a tombstone to hold the word"
        )
    assert not isinstance(gone, Refusal), (
        "the fixture's forced retire refused for a reason no capability explains", gone,
    )
    assert word in (gone.aliases or ()), (
        "INTERFACE.md 5.8 -- a tombstone keeps its words by design", gone.aliases
    )
    return gone

async def test_c12_22_the_import_name_door_holds_the_word_across_kinds(adapter, make_registry):
    """**The FIFTEENTH trip at the third mint door.** Row 6d; ruling **R91**.

    `import_types` is a NAME door in its own right, and shipping the kind-blind scan at
    `propose_type` alone would be *a fix applied at one call site of three* — the single
    sentence of the ninth, tenth and eleventh trips.
    """
    registry = await make_registry(adapter)
    tombstone = await _tombstone_holding(registry)

    out = await registry.import_types(
        [{"name": "zzz_moved", "status": "active", "definition": "another kind"}],
        kind="entity",
    )
    assert out and out[0].name == tombstone.name, out
    assert f"word_previously_retired:{tombstone.name}" in (out[0].warnings or ()), (
        out[0].warnings
    )
    assert isinstance(
        await registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd"), TypeEntry
    )

async def test_c12_23_the_import_alias_door_refuses_a_word_a_tombstone_answers_to(
    adapter, make_registry
):
    """**The kill row's SIXTEENTH trip** — the trip-14 rule bound the incoming NAME only.

    A word a tombstone still answers to, arriving in the incoming row's **`aliases`**,
    was written with **no refusal and no warning**; `resolve_type` then answered the new
    row at 1.0 and `reinstate` refused `alias_collision` non-overridably **with
    `path_back=None`** — worse than the door it descends from. `_alias_identity_breach`'s
    keyed scan defaults `match_aliases=False`, and `_alias_clash` reads ACTIVE rows only.

    **[Observed, row 6d round 1]** five ordinary calls, no `force`, no acknowledgement;
    countersigned as the sixteenth trip by ruling **R91**. `word_held_by_tombstone`, the
    thirty-second `Refusal.reason`.
    """
    registry = await make_registry(adapter)
    tombstone = await _tombstone_holding(registry)

    out = await registry.import_types(
        [{"name": "beta", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a brand new row"}],
        kind="predicate",
    )
    assert out, out
    assert "import_refused:word_held_by_tombstone" in (out[0].warnings or ()), (
        out[0].warnings
    )
    written = await adapter.get_type("default", "beta", kind="predicate")
    assert written is None or "zzz_moved" not in (written.aliases or ()), (
        "nothing is written -- a refusal is not a warning on a completed act"
    )
    # ...and the whole point: the tombstone can still be brought back.
    assert isinstance(
        await registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd"), TypeEntry
    ), "R11's governance act must survive the write that used to burn it"
    assert tombstone.name == "alpha"

async def test_c12_24_a_skipped_identity_guard_says_so(adapter, make_registry):
    """**The kill row's NINETEENTH trip.** Row 6d, round 1; countersigned by **R92**.

    §5.10's refusal **#1** compares CONSUMER SETS. On a backend declaring
    `indexes_membership=False` a stored row's `predicates` come back empty, so both sides
    read blank and #1 compares equal **vacuously** — and the door said **nothing at all**.
    The same five ordinary calls were refused `different_consumer_sets`
    **non-overridably** where the capability is present and written with `warnings=()`
    where it is not, with `resolve_type` answering at **1.0**.

    That is UC1 Tenshen's own declared shape and the **FIRST** trip's backend. Trips 1 and
    9 asked whether *unknowable* equals *equal* or *different*; **this asks whether it
    equals nothing to say, and the shipped answer was yes.**

    **The comparison is deliberately unchanged.** R53's boundary forbids this row to
    change what a guard compares, and refusing instead would ban `import_types` from
    writing any aliased row on that backend — `C10-09`'s lesson, `C3-13`'s and `C12-13`'s.
    What changes is that the caller is told: `identity_guard_skipped:<guard>:<capability>`,
    the thirty-eighth warning value.

    **ENTITIES, not predicates, and that is what isolates #1** — the extents are
    unknowable on this backend too, so a predicate pair is refused by #2 for a reason that
    has nothing to do with the skip.
    """
    degraded = await make_registry(
        AsyncDegradedAdapter(adapter, indexes_membership=False), approval_policy="auto"
    )
    await seed(degraded, "meta_p", kind="predicate", definition="a meta capability")
    await seed(degraded, "ent_a", kind="entity", definition="a thing", predicates=["meta_p"])
    await seed(degraded, "ent_b", kind="entity", definition="a thing")
    out = await degraded.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    if isinstance(out, Refusal):
        pytest.skip(f"this backend cannot register a consumer ({out.reason})")
    gone = await degraded.retire("ent_a", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the row ({gone.reason})")

    rows = await degraded.import_types(
        [{"name": "ent_b", "kind": "entity", "definition": "a thing",
          "aliases": ["ent_a"], "status": "active"}],
        namespace="default", kind="entity",
    )
    assert rows, rows
    warnings = rows[0].warnings or ()
    if any(w.startswith("import_refused:") for w in warnings):
        pytest.skip(f"this backend refused for another reason ({warnings})")
    assert any(
        w.startswith("identity_guard_skipped:different_consumer_sets:")
        for w in warnings
    ), (
        "a guard that was never ASKED is not a guard that PASSED -- the door must say "
        "which guard it skipped and which capability it needed",
        warnings,
    )

async def test_c12_25_a_field_this_call_ignores_is_stated(adapter, make_registry):
    """**Finding X6, row 6d round 1 (ruling R90).** Accepted-and-ignored, said out loud.

    `import_types` takes ONE `namespace` for the whole batch — §2.5's Foundry mapping is a
    per-call scope, not a per-row one — and a row carrying its own `namespace` had that key
    **silently dropped**: the identity was written into the CALLER's scope with
    `warnings=()`, so a dump with a namespace column landed its rows in the wrong place
    with nothing said.

    **Not a refusal.** The write is legal and the mapping is the documented one; what was
    missing is that it says so. Accepted-and-ignored is the `mark_reviewed` shape row 6c
    fixed one call along: a caller who supplies a field and sees no effect is owed the
    sentence.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    out = await registry.import_types(
        [{"name": "plaza", "namespace": "dot", "definition": "a public space",
          "status": "active"}],
        namespace="dpr", kind="entity",
    )
    assert out, out
    assert out[0].namespace == "dpr", "the call's namespace is the one that applies"
    assert any(
        w.startswith("import_field_ignored:namespace:") for w in (out[0].warnings or ())
    ), out[0].warnings

    # ...and a row that asks for the call's own namespace is not warned about.
    quiet = await registry.import_types(
        [{"name": "esplanade", "namespace": "dpr", "definition": "a walk",
          "status": "active"}],
        namespace="dpr", kind="entity",
    )
    assert not any(
        w.startswith("import_field_ignored") for w in (quiet[0].warnings or ())
    ), quiet[0].warnings

async def test_c12_26_the_import_name_door_holds_the_byte_identical_tombstone(
    adapter, make_registry
):
    """**The kill row's TWENTY-FIRST trip.** Row 6d, round 2; countersigned by **R93**.

    `named = [r for r in retired_here if r.name != name and same_word(r.name, name)]`
    discarded the **byte-identical** tombstone. `standing` is `None` exactly when no row
    *of that kind* carries the name, so such a row can only be a tombstone of **another
    kind** — precisely the cell change 1 dropped `kind=` to expose. **The clause was inert
    while the scan was kind-scoped and became live the moment it was widened**, so the fix
    walked past it.

    Worse than the fifteenth trip's own outcome: the tombstone is not refused, it is
    **unreachable** — `reinstate` takes no `kind`, so no call exists that could bring it
    back. That residual is declined in this change and carried as **Q96**.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "w", kind="entity", definition="a thing")
    gone = await registry.retire("w", "no longer used", retired_by="user:sd", force=True)
    # NOT REACHABLE, never a pass. `retire`'s `if force and not self.caps.stores_events`
    # (`registry.py:3969`) refuses a destructive override that cannot be written down, so
    # on such a store this fixture cannot be built at all. **Gated on the CAPABILITY**, so
    # a store that CAN record events and still refused this way is a finding, not a skip.
    #
    # Narrowed to the ONE reason the capability explains, on the four-file precedent. With
    # `force=True` and no `successor` it is the only refusal `retire` can reach -- 9 of its
    # 12 are gated behind `successor is not None` and the other 2 behind `not force`. The
    # bare form this line used to carry told a backend refusing for an unrelated reason,
    # while recording events perfectly well, that it had failed: `C19-100`'s defect.
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert registry.caps.stores_events is False, (
            "this backend records events, so the refusal is not a capability", gone.detail,
        )
        pytest.skip(
            "NOT REACHABLE: stores_events=False refuses the forced retire before there "
            "is a byte-identical tombstone for the name door to hold"
        )
    assert not isinstance(gone, Refusal), (
        "the fixture's forced retire refused for a reason no capability explains", gone,
    )

    # CONTROL: `propose_type` has no such exclusion and answers this way.
    control = await registry.propose_type(
        "w", "another kind entirely", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(control, TypeEntry)
    assert "name_previously_retired" in (control.warnings or ()), control.warnings

    out = await registry.import_types(
        [{"name": "w", "kind": "predicate", "definition": "another kind entirely",
          "status": "active"}],
        namespace="default", kind="predicate",
    )
    assert out and out[0].name == "w" and out[0].kind == "entity", (
        "the holder comes back, and it is the entity tombstone", out[0].name, out[0].kind
    )
    assert "name_previously_retired" in (out[0].warnings or ()), out[0].warnings
    assert not [
        t for t in (await registry.list_types("predicate")).types if t.name == "w"
    ], "nothing is written"
    assert isinstance(
        await registry.reinstate("w", "we were wrong", reinstated_by="user:sd"), TypeEntry
    ), "the tombstone must still be reachable"

async def test_c12_27_a_declined_row_still_carries_what_the_call_could_not_check(
    adapter, make_registry
):
    """**Finding X11**, row 6d round 2 — the accumulator family at the door that does not
    return a `Refusal` at all.

    `_refused_import` returned `warnings=("import_refused:<reason>",)` **alone**, so every
    note `import_types` had collected on the way to declining the row was thrown away by
    the `continue` that followed: X6's own `import_field_ignored`, and the
    `alias_check_incomplete` values beside it that say a scan did not finish. The
    accumulator is filled at **five** sites and was read at exactly **one** — the success
    path.

    Same sentence as `C10-27` at a different shape, which is why both land in one change:
    *a rule applied at the success path is half-applied until the commit names the decline
    paths it also binds* — **standing rule (d)**. And the decline path is where it counts
    most: `import_field_ignored:namespace` means **this row went somewhere other than
    where its own column said**, and a caller who is also being told the row was refused
    has MORE need of that sentence, not less.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "plaza", kind="entity", definition="a public space", namespace="dpr")

    # `esplanade` carries its own `namespace` (ignored, per X6) AND an alias the live
    # `plaza` already answers to, so the row is DECLINED after the note was collected.
    out = await registry.import_types(
        [{"name": "esplanade", "namespace": "dot", "definition": "a walk",
          "aliases": ["plaza"], "status": "active"}],
        namespace="dpr", kind="entity",
    )
    assert out, out
    warnings = tuple(out[0].warnings or ())
    if not any(w.startswith("import_refused:") for w in warnings):
        # NOT REACHABLE, never a pass: without stored aliases there is no collision to
        # decline the row, so this fixture cannot pose the question on this backend.
        assert registry.caps.stores_aliases is False, (
            "this backend stores aliases, so the row should have been declined -- that "
            "is a finding, not a capability", warnings,
        )
        pytest.skip(
            "NOT REACHABLE: stores_aliases=False drops the alias that declines the row"
        )
    assert any(w.startswith("import_field_ignored:namespace:") for w in warnings), (
        "the row was declined AND its namespace was ignored; the caller is owed both "
        "sentences, and the decline path dropped the second one",
        warnings,
    )

async def test_c12_28_each_truncated_scan_in_this_method_names_itself(adapter, make_registry):
    """**Finding A3 and its sibling — Rule U at the CALL SITE, not at the comparison.**
    Row 6d, round 3; ruling **R94**'s change 4.

    `import_types` runs several scans that can come up short, and two of them **bound the
    `why` and never read it**: the tombstone NAME scan (`variants, _variant_why`) and the
    action-declaration scan (`named, _named_why`). On a **legal** `PACKAGE.md` §3.4
    backend that cannot finish a page the list came back SHORT and the guard below
    concluded *nothing found* — **the guard was skipped and the row was written**, which
    is *we could not finish looking* read as *there is nothing to find*.

    Each report **names its scan**, because a truncated NAME scan means a tombstone may
    have been missed (the twentieth and twenty-first trips) and a truncated ALIAS scan
    means a live holder may have been missed. Two facts; one value for two facts is §2.3's
    Cause B, and the EIGHTEENTH trip already answered it at `merge_types` this way.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.stores_aliases:
        pytest.skip("this backend stores no aliases, so no scan of them can truncate")
    for i in range(6):
        await seed(registry, f"row_{i}", definition="a row")

    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=3), approval_policy="auto")
    entry = (await capped.import_types(
        [{"name": "imported_here", "kind": "entity", "definition": "a row",
          "aliases": ["a_brand_new_word"], "status": "active"}],
        namespace="default", kind="entity",
    ))[0]
    assert any(
        w.startswith("alias_check_incomplete:tombstone name scan:")
        for w in (entry.warnings or ())
    ), (
        "the scan that asks whether a TOMBSTONE holds this name came up short, and a "
        "caller told nothing would read the silence as `no tombstone holds it` -- which "
        "is what let the row be minted over one",
        entry.warnings,
    )

async def test_c12_29_a_truncated_action_declaration_scan_says_so(adapter, make_registry):
    """**Finding A3 itself**, at the site ruling **R94** named. Row 6d, round 3.

    `registry.py`'s action-declaration loop read `named, _named_why = self._word_rows(...)`
    — bound and never used. A truncating backend therefore made
    `_action_declarations_diverge` see fewer rows, find no divergence, and **write the
    alias**: `resolve_type` answering at 1.0 one way while `preflight` refused the other,
    which is A3's own harm with A3's fix live.

    **And it is change A's consumer table one line short.** `db3fb6b` enumerated five
    consumers of the widened `_word_rows` and did not list this one. Its *kind* claim
    holds — a non-action row is discarded by the guard's own first line — but the widening
    made the scan LARGER, which makes an incomplete page MORE likely, at the one call site
    that read incompleteness as agreement.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.stores_attributes:
        pytest.skip("this backend stores no attributes, so a family cannot be declared")
    if not registry.caps.stores_aliases:
        pytest.skip("this backend stores no aliases, so the alias write cannot happen")
    for i in range(6):
        await seed(registry, f"verb_{i}", kind="action", definition="a verb",
             attributes=action_attributes(reversibility="reversible",
                                          approval_mode="auto"))

    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=3), approval_policy="auto")
    rows = await capped.import_types(
        [{"name": "pay_out", "kind": "action", "definition": "a verb",
          "aliases": ["verb_0"], "status": "active",
          "attributes": action_attributes(reversibility="irreversible",
                                          approval_mode="human")}],
        namespace="default", kind="action",
    )
    warnings = tuple(rows[0].warnings or ())
    assert any(
        w.startswith("alias_check_incomplete:action declaration scan:") for w in warnings
    ), (
        "the scan that asks whether this word already names a family with CONTRADICTORY "
        "governance came up short, and a caller told nothing would read that as `no "
        "divergence` -- which writes the alias and leaves one word with two policies",
        warnings,
    )

_WRITE_PRIMITIVES = (
    "put_type",
    "put_proposal",
    "put_consumer",
    "bump_usage",
    "append_event",
    "put_edge",
    "put_invocation",
    "put_attr_schema",
)

def _count_writes(adapter, monkeypatch) -> list[str]:
    """Wrap each write primitive on THIS adapter instance and record every call."""
    calls: list[str] = []
    for attr in _WRITE_PRIMITIVES:
        original = getattr(adapter, attr, None)
        if original is None:
            continue

        def wrapped(*args, _attr=attr, _original=original, **kwargs):
            calls.append(_attr)
            return _original(*args, **kwargs)

        monkeypatch.setattr(adapter, attr, wrapped)
    return calls

def _items(report, **match):
    return [
        item
        for item in report.items
        if all(getattr(item, key) == value for key, value in match.items())
    ]

def _names(report, **match):
    return sorted(item.name for item in _items(report, **match))

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_30_endorsed_becomes_active_plus_the_endorsed_predicate(registry, adapter):
    """**Defect 1** (`FOUNDRY-PARITY.md` §2). `ENDORSED` imported as plain `active` with
    no predicate and no warning, so a type an ontology owner vetted was
    indistinguishable from any other on arrival. It now follows the `experimental`
    precedent of `C12-01`: `active`, plus the predicate, so the endorsement survives the
    move and `list_types(predicate=...)` can find it."""
    out = await registry.import_types(
        [
            {"name": "vetted_type", "status": "ENDORSED", "definition": "an owner-vetted type"},
            {"name": "plain_type", "status": "active", "definition": "an ordinary type"},
        ]
    )
    assert [e.status for e in out] == ["active", "active"]
    assert "endorsed" in out[0].predicates
    assert "endorsed" not in out[1].predicates
    stored = await adapter.get_type("default", "vetted_type", kind="entity")
    assert stored.status == "active"
    assert [t.name for t in (await registry.list_types(predicate="endorsed")).types] == ["vetted_type"]

async def test_c12_31_example_and_unknown_statuses_are_held_and_no_status_is_still_active(
    registry, adapter
):
    """**Defect 2.** Foundry's Example status imported as `active`, so demo types entered
    the vocabulary as live types through the migration door, which is the pollution
    `VISION.md` §1 names. Any status outside the four this mapping knows was the same
    defect one value along: it fell through to `active`. Neither is written now, and
    each says why. A row with NO status still imports `active`, which `C12-01`'s own
    fixture relies on."""
    out = await registry.import_types(
        [
            {"name": "demo_type", "status": "EXAMPLE", "definition": "a template's demo"},
            {"name": "odd_type", "status": "promoted", "definition": "an unknown status"},
            {"name": "bare_type", "definition": "no status at all"},
        ]
    )
    assert "import_refused:foundry_example" in out[0].warnings
    assert "import_refused:status_unknown" in out[1].warnings
    assert await adapter.get_type("default", "demo_type", kind="entity") is None
    assert await adapter.get_type("default", "odd_type", kind="entity") is None
    assert out[2].status == "active" and out[2].warnings == ()
    assert (await adapter.get_type("default", "bare_type", kind="entity")).status == "active"

async def test_c12_32_a_bad_name_is_refused_never_raised_and_the_batch_continues(registry, adapter):
    """**Defect 3.** A camelCase Foundry apiName raised `sqlite3.IntegrityError` out of a
    call whose contract is *it returns entries, not exceptions*: a raw backend error,
    on one backend, with the rest of the batch unprocessed. Every name outside
    `^[a-z][a-z0-9_]{0,63}$` now comes back `import_refused:name_invalid` on every
    backend, and the valid row after it is written."""
    bad = ["NursingHome", "9lives", "", "a" * 65, "has space", "trailing-dash"]
    rows = [{"name": n, "status": "active", "definition": "a bad name"} for n in bad]
    rows.append({"name": "good_after", "status": "active", "definition": "after the bad ones"})

    out = await registry.import_types(rows)

    assert len(out) == len(rows)
    for entry in out[:-1]:
        assert "import_refused:name_invalid" in entry.warnings, entry
    assert out[-1].status == "active" and "import_refused:name_invalid" not in out[-1].warnings
    assert await adapter.get_type("default", "good_after", kind="entity") is not None
    assert sorted([t.name for t in (await registry.list_types()).types]) == ["equivalent_to", "good_after"]

async def test_c12_33_a_row_with_no_definition_is_never_written_with_one_it_did_not_have(
    registry, adapter
):
    """**Defect 4, under R109 (`hold + override map`).** A missing description became the
    definition `"imported from foundry"` on a LIVE type, and `INTERFACE.md` §2.1 says a
    type without a definition *"is how collision starts"*. The brief asked for
    `proposed`. In this registry `proposed` is a proposal record, which needs a
    definition too, so the founder ruled the row is held: nothing written, the row
    handed back shaped `proposed` with `import_refused:definition_missing`.

    **An import over a STANDING row is an update, and keeps that row's definition.**
    Nothing the caller did not supply is written, which is the rule. The standing
    definition was supplied, by whoever wrote it. `C12-06` and `C12-19` import
    definition-less rows over standing ones and depend on this."""
    out = await registry.import_types(
        [
            {"name": "no_definition", "status": "active"},
            {"name": "empty_definition", "status": "active", "definition": ""},
            {"name": "blank_definition", "status": "active", "definition": "   "},
            {"name": "gone_type", "status": "deprecated"},
        ]
    )
    for entry in out:
        assert "import_refused:definition_missing" in entry.warnings, entry
        assert entry.status == "proposed", "the row as it would have looked, unwritten"
        assert await adapter.get_type("default", entry.name, kind="entity") is None

    await seed(registry, "standing_type", definition="a definition someone wrote")
    updated = (await registry.import_types([{"name": "standing_type", "status": "active"}]))[0]
    assert "import_refused:definition_missing" not in updated.warnings
    assert (await adapter.get_type("default", "standing_type")).definition == "a definition someone wrote"

    every = (await registry.list_types(include_retired=True)).types
    assert all(t.definition != "imported from foundry" for t in every)

async def test_c12_34_a_dry_run_over_palantirs_employee_ontology_writes_nothing(
    adapter, make_registry, monkeypatch
):
    """`8A-RUN.md` §0.3's `employee` column, and §0.5 item 4: **the dry run calls no
    adapter write primitive.** The document is generated by Palantir's own `@osdk/faux`
    from its `EmployeeOntology`."""
    registry = await make_registry(adapter)
    calls = _count_writes(adapter, monkeypatch)

    report = await registry.import_foundry(foundry_fixture("faux_employee"))

    assert calls == [], f"a dry run wrote: {calls}"
    assert report.dry_run is True
    assert _names(report, kind="predicate", outcome="would_write") == ["foo_interface"]
    assert _names(report, kind="entity", outcome="would_write") == ["employee", "office"]
    assert report.count(outcome="would_write") == 3
    assert _names(report, kind="edge", reason="definition_missing") == [
        "lead", "office_link", "visited_offices",
    ]
    assert report.count(outcome="held") == 3
    unpaired = [i.name for i in _items(report, kind="edge") if i.detail.get("inverse_label") is None]
    assert unpaired == ["visited_offices"]
    assert sum(i.carried_properties for i in report.items) == 19
    # Row 8c: shared property types are imported now (`C12-69`), so not counted here.
    assert report.not_imported == {"queryTypes": 0, "valueTypes": 0}
    assert report.looks_like == ()
    employee = _items(report, name="employee")[0]
    assert employee.detail["predicates"] == ["foo_interface"]

async def test_c12_35_a_dry_run_over_palantirs_legacy_ontology(registry):
    """`8A-RUN.md` §0.3's `legacy` column: Palantir's `LegacyFauxFoundry` default
    ontology, the largest test ontology `@osdk/faux` ships."""
    report = await registry.import_foundry(foundry_fixture("faux_legacy"))

    assert report.count(outcome="would_write", kind="predicate") == 3
    assert _names(report, kind="entity", outcome="would_write") == [
        "complex_implementation_object", "employee", "object_type_with_all_property_types",
        "object_with_timestamp_primary_key", "office",
    ]
    assert report.count(outcome="would_write", kind="action") == 11
    # Row 8c: `fooSpt` is the twentieth, a `kind="property"` entry (`C12-69`).
    assert report.count(outcome="would_write", kind="property") == 1
    assert report.count(outcome="would_write") == 20
    assert report.count(outcome="held", reason="definition_missing") == 16
    assert _names(report, kind="entity", reason="definition_missing") == [
        "bgao_nfl_player", "equipment", "person", "task", "todo",
    ]
    assert _names(report, kind="action", reason="definition_missing") == [
        "action_takes_decimal", "add_geoshape", "create_foo_interface",
        "delete_bar_interface", "delete_foo_interface",
    ]
    assert report.count(kind="edge") == 6
    assert sorted(i.name for i in _items(report, kind="edge")
                  if i.detail.get("inverse_label") is None) == [
        "linked_object_type", "rp", "todos", "visited_offices",
    ], "§1.1's unpaired link sides (round 4)"
    assert report.count(outcome="held") == 16, "no collision, no bad name, no odd status"
    assert sum(i.carried_properties for i in report.items) == 75
    assert report.not_imported == {"queryTypes": 21, "valueTypes": 0}
    assert report.looks_like == (), "the [Observed] legacy cell of §1.1 (round 2)"
    ops = [e["op"] for i in _items(report, outcome="would_write", kind="action")
           for e in i.detail["effects"]]
    assert ops.count("host_state") == 6 and "add_edge" not in ops and "retract_edge" not in ops

async def test_c12_36_a_real_import_writes_the_would_write_set_and_carries_properties(
    registry, adapter
):
    """The non-dry import of `employee` writes the would-write set and nothing else.
    Only the importer writes: one `import_types` call, which is §0.5 item 1. The
    Foundry apiName lands in provenance and is NOT an alias (§0.2)."""
    doc = foundry_fixture("faux_employee")
    planned = await registry.import_foundry(doc)
    report = await registry.import_foundry(doc, dry_run=False)

    assert report.dry_run is False
    assert sorted((i.kind, i.name) for i in _items(report, outcome="written")) == sorted(
        (i.kind, i.name) for i in _items(planned, outcome="would_write")
    )
    assert report.count(outcome="refused") == 0
    for item in _items(report, outcome="written"):
        assert await adapter.get_type("default", item.name, kind=item.kind) is not None
    for item in _items(report, outcome="held"):
        assert await adapter.get_type("default", item.name, kind=item.kind) is None

    employee = await adapter.get_type("default", "employee", kind="entity")
    assert employee.status == "active"
    assert employee.definition == doc["objectTypes"]["Employee"]["objectType"]["description"]
    provenance = await registry.provenance("employee")
    assert provenance.imported_from["apiName"] == "Employee"
    assert provenance.imported_from["system"] == "foundry"
    assert "Employee" not in (employee.aliases or ())

    # R105's `carry`, marked not validated, and narrowed by row 8c to what a slot has
    # no field for: the key and title moved to `primary_key` and `title_property`
    # (`C12-70`), and what stays per property is `C12-73`'s.
    if (await adapter.capabilities()).stores_attributes:
        carried = employee.attributes["foundry_properties"]
        source = doc["objectTypes"]["Employee"]["objectType"]
        assert carried["validated"] is False
        assert "primaryKey" not in carried and "titleProperty" not in carried
        assert employee.attributes["primary_key"] == [source["primaryKey"]]
        assert employee.attributes["title_property"] == source["titleProperty"]

async def test_c12_37_a_converted_name_collision_is_held_whole_and_names_resolves_it(
    registry, adapter
):
    """**R110, `hold both + names map`.** `NursingHome` and `Nursing_Home` both convert
    to `nursing_home`, and `import_types` overwrites a standing row of the same kind
    and name, so without a rule the second silently replaced the first. Every member
    of the collision is held. `_9Lives` converts to a leading digit and is held
    `name_invalid`. `names=` resolves both, and is checked the same way."""
    doc = foundry_fixture("edge_cases")
    report = await registry.import_foundry(doc, dry_run=False)

    clash = _items(report, reason="name_collision_after_conversion")
    assert sorted(i.api_name for i in clash) == ["NursingHome", "Nursing_Home"]
    assert all(i.name == "nursing_home" for i in clash)
    assert await adapter.get_type("default", "nursing_home", kind="entity") is None
    assert _items(report, api_name="_9Lives")[0].reason == "name_invalid"
    assert _items(report, api_name="Ward3D")[0].name == "ward3_d"

    fixed = await registry.import_foundry(
        doc,
        dry_run=False,
        names={"Nursing_Home": "care_home", "_9Lives": "nine_lives"},
    )
    assert _items(fixed, api_name="NursingHome")[0].outcome == "written"
    assert _items(fixed, api_name="Nursing_Home")[0].name == "care_home"
    assert await adapter.get_type("default", "care_home", kind="entity") is not None
    assert await adapter.get_type("default", "nine_lives", kind="entity") is not None

    remapped = await registry.import_foundry(doc, names={"Nursing_Home": "nursing_home"})
    assert len(_items(remapped, reason="name_collision_after_conversion")) == 2, (
        "a mapped name cannot create a collision the map was meant to remove"
    )
    bad = await registry.import_foundry(doc, names={"Nursing_Home": "Care Home"})
    assert _items(bad, api_name="Nursing_Home")[0].reason == "name_invalid"

@pytest.mark.requires_capability("stores_attributes")
async def test_c12_38_definitions_import_held_rows_and_links_become_edge_families(registry, adapter):
    """**R109's override map, and link types.** A Foundry link side carries no
    description, so every link is held for one, and `definitions=` supplies it. The two
    MANY sides of `treats` / `treatedBy` pair by `linkTypeRid` into ONE family, named
    for the first side by `(objectType, apiName)`, and cardinality, which `EDGES.md`
    has no key for, is carried in `attributes["foundry_link"]` (brief question 3).
    The statuses: ENDORSED lands active, EXAMPLE is held, DEPRECATED lands retired."""
    doc = foundry_fixture("edge_cases")
    report = await registry.import_foundry(
        doc,
        dry_run=False,
        definitions={
            "Doctor.treats": "A doctor treats a patient.",
            "NoDescription": "Supplied by the operator at import time.",
        },
    )
    treats = _items(report, kind="edge")
    assert [(i.name, i.outcome) for i in treats] == [("treats", "written")]
    stored = await adapter.get_type("default", "treats", kind="edge")
    assert stored.definition == "A doctor treats a patient."
    assert stored.attributes["level"] == "instance"
    assert stored.attributes["symmetric"] is False
    assert stored.attributes["inverse_label"] == "treated_by"
    link = stored.attributes["foundry_link"]
    assert [s["cardinality"] for s in link["sides"]] == ["MANY", "MANY"]
    assert (link["src_type"], link["dst_type"]) == ("doctor", "patient")
    assert (await adapter.get_type("default", "no_description", kind="entity")).definition == (
        "Supplied by the operator at import time."
    )
    assert (await adapter.get_type("default", "endorsed_thing", kind="entity")).status == "active"
    assert _items(report, api_name="ExampleThing")[0].reason == "status_not_imported"
    assert await adapter.get_type("default", "example_thing", kind="entity") is None
    assert (await adapter.get_type("default", "legacy_ward", kind="entity")).status == "retired"

async def test_c12_39_the_dry_run_names_the_word_the_vocabulary_already_has(registry):
    """`FOUNDRY-PARITY.md` §3.1: *"you already have `facility`, and Foundry's
    `Facilities` looks like it"*, before anything is written. The answer is
    `resolve_type`'s, filtered at the namespace's `near_duplicate_threshold`: this row
    adds no scoring of its own. A name that is
    already STANDING is reported as standing, because importing it replaces that row."""
    await seed(registry, "facility", definition="A licensed nursing home.")
    await seed(registry, "survey", definition="An inspection visit.")
    doc = foundry_fixture("uc2_cms")
    doc["objectTypes"]["Facilities"] = doc["objectTypes"].pop("Facility")
    doc["objectTypes"]["Facilities"]["objectType"]["apiName"] = "Facilities"

    report = await registry.import_foundry(doc)

    looks = {(look.name, look.matched) for look in report.looks_like}
    assert ("facilities", "facility") in looks
    assert _items(report, name="survey")[0].detail["standing"] is True
    assert _items(report, name="citation")[0].detail["standing"] is False

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_40_the_name_door_guards_are_inherited_through_import_foundry(registry, adapter):
    """`8A-RUN.md` §0.5 item 3. `import_foundry` is a planner in front of the existing
    door, not a new one: every state that makes `import_types` refuse a row makes
    `import_foundry` refuse it the same way, and write nothing."""
    await seed(registry, "commentable", kind="predicate", definition="a code path accepts it")
    await seed(registry, "doctor", predicates=["commentable"], definition="a physician")
    await registry.register_consumer(Consumer(id="rounds.assign", gate="commentable", on_unknown="drop"))
    await seed(registry, "ward_old", definition="the old ward model")
    await registry.retire("ward_old", "superseded", retired_by="user:sd")

    doc = foundry_fixture("edge_cases")
    doc["objectTypes"]["Doctor"]["objectType"]["status"] = "DEPRECATED"
    doc["objectTypes"]["WardOld"] = doc["objectTypes"].pop("LegacyWard")
    doc["objectTypes"]["WardOld"]["objectType"].update(apiName="WardOld", status="ACTIVE")

    report = await registry.import_foundry(doc, dry_run=False)

    doctor = _items(report, name="doctor")[0]
    assert doctor.outcome == "refused" and "import_refused:live_consumers" in doctor.warnings
    assert (await adapter.get_type("default", "doctor", kind="entity")).status == "active"
    ward = _items(report, name="ward_old")[0]
    assert ward.outcome == "refused" and "name_previously_retired" in ward.warnings
    assert (await adapter.get_type("default", "ward_old", kind="entity")).status == "retired"

@pytest.mark.requires_capability("stores_attributes")
async def test_c12_41_action_types_declare_no_family_and_report_their_effect_mapping(
    registry, adapter
):
    """Brief question 4. Foundry gives no reversibility and no approval mode, so an
    imported action declares **none** of `ACTIONS.md` §2.2's eight keys (rule 2.2-1: a
    legal entry, not yet usable as a family) rather than guessing two required ones.
    The `Effect.op` each logic rule WOULD map to is reported, not declared: a link rule
    to `add_edge`, a function rule to `host_state` with a `why` naming it.
    `fullLogicRules` is read in preference to `operations` when both exist."""
    from ontoloche.actions import ACTION_ATTRIBUTE_KEYS

    report = await registry.import_foundry(foundry_fixture("edge_cases"), dry_run=False)

    assign = _items(report, api_name="assignDoctor")[0]
    assert assign.outcome == "written" and assign.name == "assign_doctor"
    effects = assign.detail["effects"]
    assert [e["op"] for e in effects] == ["add_edge", "host_state"]
    assert effects[0]["link"] == "treats"
    assert "function" in effects[1]["why"]
    stored = await adapter.get_type("default", "assign_doctor", kind="action")
    assert not any(key in stored.attributes for key in ACTION_ATTRIBUTE_KEYS)
    assert stored.attributes["foundry_action"]["apiName"] == "assignDoctor"

async def test_c12_42_uc2_cms_as_a_foundry_ontology(registry, adapter):
    """**Design test UC2** (standing constraint 7, `8A-RUN.md` §0.6). The CMS vocabulary
    re-expressed as Foundry object types and link types imports to the four entity
    names `cms_vocabulary()` holds, with its definitions verbatim, and the three edge
    family names `C18` loads. The two CMS value sets do not import, because value
    types are outside this row: a recorded gap, not a pass."""
    from ontoloche.aio.contract._support import cms_vocabulary, sample_facts

    expected = cms_vocabulary(sample_facts())
    cms = await registry.import_foundry(
        foundry_fixture("uc2_cms"),
        dry_run=False,
        definitions={
            "Citation.issuedDuring": "A citation was issued during a survey.",
            "Survey.conductedAt": "A survey was conducted at a facility.",
            "Citation.cites": "A citation names a deficiency tag.",
        },
    )
    entities = {s["name"] for s in expected if s["kind"] == "entity"}
    assert set(_names(cms, kind="entity", outcome="written")) == entities
    assert set(_names(cms, kind="edge", outcome="written")) == {
        "issued_during", "conducted_at", "cites",
    }
    for spec in expected:
        if spec["kind"] == "entity":
            stored = await adapter.get_type("default", spec["name"], kind="entity")
            assert stored.definition == spec["definition"]
    assert cms.count(kind="value_set") == 0

async def test_c12_43_uc3_one_foundry_ontology_lands_in_one_namespace(registry):
    """**Design test UC3**, and the evidence for brief question 2. UC3 splits
    `street_tree` into `dpr` and `service_request` into `oti_311`, joined by
    `same_tax_lot`. A Foundry link joins object types inside ONE ontology, so the only
    Foundry shape that holds the link holds both types, and one call imports one
    document into one namespace. The split is **not** reproduced."""
    nyc = await registry.import_foundry(
        foundry_fixture("uc3_nyc"),
        namespace="nyc",
        dry_run=False,
        definitions={
            "ServiceRequest.sameTaxLot": (
                "Both endpoints sit on the same borough-block-lot. It asserts the "
                "shared lot and nothing more."
            )
        },
    )
    assert {(i.kind, i.name) for i in _items(nyc, outcome="written")} == {
        ("entity", "street_tree"), ("entity", "service_request"), ("edge", "same_tax_lot"),
    }
    assert _items(nyc, kind="edge")[0].detail["inverse_label"] == "shares_tax_lot_with"
    assert {t.namespace for t in (await registry.list_types(namespace="nyc")).types} == {"nyc"}
    assert (await registry.list_types(namespace="dpr")).types == ()
    assert (await registry.list_types(namespace="oti_311")).types == ()

def _ontology(interfaces=None, objects=None, actions=None, links=None):
    """A minimal ``OntologyFullMetadata``. ``objects`` maps apiName to
    ``(description, status, implementsInterfaces)``; ``links`` maps an object type
    apiName to its ``linkTypes`` sides."""
    return {
        "ontology": {"apiName": "probe", "rid": "ri.ontology.main.ontology.probe"},
        "interfaceTypes": {
            api: {"apiName": api, "rid": f"ri.i.{api}", "description": text}
            for api, text in (interfaces or {}).items()
        },
        "objectTypes": {
            api: {
                "objectType": {
                    "apiName": api, "rid": f"ri.o.{api}", "description": text,
                    "status": status, "properties": {},
                },
                "linkTypes": list((links or {}).get(api, ())),
                "implementsInterfaces": list(implements),
                "implementsInterfaces2": {i: {} for i in implements},
            }
            for api, (text, status, implements) in (objects or {}).items()
        },
        "actionTypes": dict(actions or {}),
        "actionTypesFullMetadata": {},
        "queryTypes": {},
        "sharedPropertyTypes": {},
        "valueTypes": {},
    }

def _side(api, target, rid, fk=None):
    side = {"apiName": api, "objectTypeApiName": target, "linkTypeRid": rid,
            "cardinality": "MANY", "status": "ACTIVE"}
    if fk:
        side["foreignKeyPropertyApiName"] = fk
    return side

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_44_a_deprecated_reimport_never_rewrites_a_local_tombstone(registry, adapter):
    """**Round 1, guards lens.** The un-retire guard fired only when the incoming
    status was NOT retired, so a Foundry `DEPRECATED` row over a name this deployment
    had retired itself went straight to `put_type` and rewrote the tombstone:
    `retire_reason`, `retired_by` and `retired_at` replaced with the import's. **That is
    the ordinary re-run of a migration**, and it is the harm the guard's own comment
    names. The tombstone comes back with `name_previously_retired`, unwritten."""
    await seed(registry, "legacy_ward", definition="a ward model")
    await registry.retire("legacy_ward", "replaced by care units", retired_by="user:sd")
    before = await adapter.get_type("default", "legacy_ward", kind="entity")

    entries = await registry.import_types(
        [{"name": "legacy_ward", "status": "deprecated", "definition": "a ward model"}]
    )
    assert "name_previously_retired" in entries[0].warnings
    after = await adapter.get_type("default", "legacy_ward", kind="entity")
    assert (after.retire_reason, after.retired_by, after.retired_at) == (
        before.retire_reason, before.retired_by, before.retired_at,
    )

    doc = _ontology(objects={"LegacyWard": ("a ward model", "DEPRECATED", ())})
    item = _items(await registry.import_foundry(doc, dry_run=False), api_name="LegacyWard")[0]
    assert item.outcome == "refused" and item.reason == "name_previously_retired"
    assert (await adapter.get_type("default", "legacy_ward", kind="entity")).retired_by == "user:sd"

async def test_c12_45_a_reference_to_a_row_this_import_does_not_write_is_reported(registry):
    """**Round 1, mapping lens.** An interface with no description is held (R109), and
    the entity implementing it was written declaring a predicate nobody wrote. The same
    happened to an edge whose endpoint entity was held, and to an interface the
    document never defines. The item said `written` and nothing else. Each dependent
    item now names what it points at and why that is not there. Holding the dependent
    too would decide a refusal, which is not this row's to make."""
    doc = _ontology(
        interfaces={"Iface": None},
        objects={
            "Ward": ("a hospital ward", "ACTIVE", ("Iface", "Undefined")),
            "Bed": (None, "ACTIVE", ()),
        },
        links={"Ward": [_side("beds", "Bed", "ri.l.1")]},
    )
    report = await registry.import_foundry(doc, definitions={"Ward.beds": "A ward has beds."})

    ward = _items(report, api_name="Ward")[0]
    assert ward.outcome == "would_write"
    assert ward.detail["unresolved"] == [
        {"predicate": "iface", "why": "held:definition_missing"},
        {"predicate": "undefined", "why": "not_in_document"},
    ]
    beds = _items(report, kind="edge")[0]
    assert beds.detail["unresolved"] == [{"dst": "bed", "why": "held:definition_missing"}]

    await seed(registry, "undefined", kind="predicate", definition="already in the vocabulary")
    again = await registry.import_foundry(doc, definitions={"Ward.beds": "A ward has beds."})
    assert _items(again, api_name="Ward")[0].detail["unresolved"] == [
        {"predicate": "iface", "why": "held:definition_missing"},
    ], "a word the store already holds is not unresolved"

async def test_c12_46_every_hold_names_the_key_that_lifts_it(registry, adapter):
    """**Round 1, mapping lens.** `LinkTypeSideV2.apiName` is unique per object type,
    not per ontology, so `Task.owner` and `Project.owner` collide. The item said
    `api_name="owner"` and `colliding=["owner", "owner"]`, and the key `names=` needs
    for a link (`"Task.owner"`) appeared nowhere, so `names={"owner": ...}` matched
    nothing and nothing said so. Every item now carries its `key`, a collision lists
    keys, and a `names=` or `definitions=` key matching nothing is reported. A name
    with a trailing newline passed `NAME_RE.match`, because `$` matches before a final
    newline, and is now refused at both the planner and `import_types`."""
    doc = _ontology(
        objects={"Task": ("a task", "ACTIVE", ()), "Project": ("a project", "ACTIVE", ()),
                 "Person": ("a person", "ACTIVE", ())},
        links={"Task": [_side("owner", "Person", "ri.l.t", fk="ownerId")],
               "Project": [_side("owner", "Person", "ri.l.p", fk="ownerId")]},
    )
    report = await registry.import_foundry(doc, names={"owner": "task_owner"})
    clash = _items(report, reason="name_collision_after_conversion")
    assert sorted(i.detail["key"] for i in clash) == ["Project.owner", "Task.owner"]
    assert clash[0].detail["colliding"] == ["Project.owner", "Task.owner"]
    assert _items(report, api_name="Task")[0].detail["key"] == "Task"
    assert report.unmatched == {"names": ["owner"], "definitions": []}

    fixed = await registry.import_foundry(
        doc, names={"Task.owner": "task_owner"}, definitions={"Task.typo": "x"}
    )
    assert not _items(fixed, reason="name_collision_after_conversion")
    assert fixed.unmatched == {"names": [], "definitions": ["Task.typo"]}

    newline = await registry.import_foundry(doc, names={"Person": "person\n"})
    assert _items(newline, api_name="Person")[0].reason == "name_invalid"
    entries = await registry.import_types([{"name": "person\n", "definition": "a person"}])
    assert "import_refused:name_invalid" in entries[0].warnings
    assert await adapter.get_type("default", "person\n", kind="entity") is None
    with pytest.raises(TypeError):
        await registry.import_foundry(doc, names={"Person": 5})

async def test_c12_47_implements_interfaces2_and_interface_link_rules_are_read(registry):
    """**Round 1, mapping lens.** The published `ObjectTypeFullMetadata` carries
    `implementsInterfaces2` beside `implementsInterfaces`, and only the list was read,
    so an object type declaring an interface only in the map arrived with no
    predicate. And `createInterfaceLink` / `deleteInterfaceLink`, which the SDK
    publishes as link rules, were reported as `host_state`."""
    doc = _ontology(
        interfaces={"Located": "has a place"},
        objects={"Ward": ("a hospital ward", "ACTIVE", ())},
        actions={"linkWard": {"apiName": "linkWard", "description": "link a ward",
                              "status": "ACTIVE", "parameters": {}, "operations": []}},
    )
    doc["objectTypes"]["Ward"]["implementsInterfaces2"] = {"Located": {}}
    doc["actionTypesFullMetadata"] = {"linkWard": {"fullLogicRules": [
        {"type": "createInterfaceLink", "interfaceTypeApiName": "Located",
         "interfaceLinkTypeApiName": "near"},
        {"type": "deleteInterfaceLink", "interfaceTypeApiName": "Located",
         "interfaceLinkTypeApiName": "near"},
    ]}}
    report = await registry.import_foundry(doc)
    assert _items(report, api_name="Ward")[0].detail["predicates"] == ["located"]
    effects = _items(report, api_name="linkWard")[0].detail["effects"]
    assert [(e["op"], e["link"]) for e in effects] == [
        ("add_edge", "Located.near"), ("retract_edge", "Located.near"),
    ]

@pytest.mark.requires_capability("stores_attributes")
async def test_c12_48_a_diverging_action_row_never_swallows_the_next_row(registry, adapter):
    """**Round 1, guards lens, a pre-existing defect on the import door.** After the
    action-alias scan, `import_types` asked whether `out[-1]` was a divergence refusal,
    without asking whether THIS row had appended it. So the action row after a refused
    one hit `continue` with no entry: three rows in, two entries out, one row neither
    written nor reported. `import_foundry` pairs entries to rows by position, so a
    dropped row would mislabel every row after it."""
    from ontoloche.actions import action_attributes

    def declared(reversibility, mode):
        return action_attributes(reversibility=reversibility, approval_mode=mode,
                                 reachability=())

    await registry.import_types([{"name": "f1", "kind": "action", "definition": "d",
                            "attributes": declared("irreversible", "human")}])
    rows = [
        {"name": "g1", "kind": "action", "definition": "d", "aliases": ["f1"],
         "attributes": declared("reversible", "auto")},
        {"name": "g2", "kind": "action", "definition": "d", "aliases": ["ok_alias"],
         "attributes": declared("reversible", "auto")},
        {"name": "g3", "kind": "entity", "definition": "d"},
    ]
    entries = await registry.import_types(rows)
    assert [e.name for e in entries] == ["g1", "g2", "g3"]
    assert "import_refused:action_declarations_diverge" in entries[0].warnings
    assert await adapter.get_type("default", "g2", kind="action") is not None

async def _every(registry):
    return {
        (t.kind, t.name)
        for kind in KIND_ORDER_FOR_TESTS
        for t in (await registry.list_types(kind, include_retired=True)).types
    }

KIND_ORDER_FOR_TESTS = ("predicate", "property", "entity", "edge", "action")

async def test_c12_49_a_real_import_is_one_import_types_call_and_writes_nothing_else(
    registry, adapter, monkeypatch
):
    """**Round 1, tests lens: `8A-RUN.md` §0.5 item 1 had no falsifier on a real run.**
    `C12-34` counted write primitives on the dry run only, so one `import_types` call
    per item, a stray second call, or a `register_consumer` added after the call all
    left the suite green. Here the real run is spied on: exactly one `import_types`
    call, its rows in the order predicates, entities, edges, actions, no consumer
    written, and the store gains exactly the written set. Also pinned: the two
    `NAME_RE`s are one pattern, a predicate and an entity converting to one word are
    not a collision (different kinds never overwrite each other), and the RIDs,
    `imported_by` and the document's ontology are carried."""
    from ontoloche import foundry
    from ontoloche import registry as registry_module

    assert foundry.NAME_RE.pattern == registry_module.NAME_RE.pattern

    doc = _ontology(
        interfaces={"Facility": "something with a location"},
        objects={"Facility": ("a care facility", "ACTIVE", ("Facility",)),
                 "Person": ("a person", "ACTIVE", ())},
        links={"Facility": [_side("staff", "Person", "ri.l.staff", fk="facilityId")]},
        actions={"admit": {"apiName": "admit", "rid": "ri.a.admit",
                           "description": "admit a patient", "status": "ACTIVE",
                           "parameters": {}, "operations": []}},
    )
    definitions = {"Facility.staff": "A facility employs a person."}
    planned = await registry.import_foundry(doc, definitions=definitions)
    assert sorted(i.kind for i in _items(planned, name="facility")) == ["entity", "predicate"]
    assert all(i.outcome == "would_write" for i in _items(planned, name="facility"))

    calls = []
    real_import_types = registry.import_types

    def spy(rows, **kwargs):
        calls.append([r["kind"] for r in rows])
        return real_import_types(rows, **kwargs)

    monkeypatch.setattr(registry, "import_types", spy)
    writes = _count_writes(adapter, monkeypatch)
    before = await _every(registry)
    report = await registry.import_foundry(
        doc, dry_run=False, definitions=definitions, imported_by="user:migrator"
    )

    assert len(calls) == 1, calls
    assert calls[0] == sorted(calls[0], key=KIND_ORDER_FOR_TESTS.index)
    assert "put_consumer" not in writes
    written = {(i.kind, i.name) for i in _items(report, outcome="written")}
    assert written == {(i.kind, i.name) for i in _items(planned, outcome="would_write")}
    assert await _every(registry) - before == written
    assert report.ontology == {"apiName": "probe", "rid": "ri.ontology.main.ontology.probe"}

    # `provenance()` takes no kind, and `facility` is two rows here, so read the entry's.
    provenance = (await adapter.get_type("default", "facility", kind="entity")).provenance
    assert provenance["imported_from"]["rid"] == "ri.o.Facility"
    assert provenance["created_by_actor"] == "user:migrator"
    assert (await registry.provenance("staff")).imported_from["apiName"] == "Facility.staff"

async def test_c12_50_a_link_sides_status_is_mapped_like_every_other_kind(registry, adapter):
    """**Round 1, tests lens.** Every link in the shipped fixtures is ACTIVE, so the
    edge row's `status` could be dropped with the suite green, and a `DEPRECATED` link
    would have landed live: defect 1 and 2's class on the one kind nothing exercised.
    The FORWARD side's status governs the family (`INTERFACE.md` §2.5a), and every
    side's own status stays in `attributes["foundry_link"]["sides"]`."""
    doc = _ontology(
        objects={"Ward": ("a hospital ward", "ACTIVE", ()),
                 "Bed": ("a bed", "ACTIVE", ())},
        links={"Ward": [{**_side("oldBeds", "Bed", "ri.l.old", fk="wardId"),
                         "status": "DEPRECATED"},
                        {**_side("demoBeds", "Bed", "ri.l.demo", fk="wardId"),
                         "status": "EXAMPLE"}]},
    )
    report = await registry.import_foundry(
        doc, dry_run=False,
        definitions={"Ward.oldBeds": "a former bed link", "Ward.demoBeds": "a demo link"},
    )
    old = _items(report, api_name="oldBeds")[0]
    assert old.outcome == "written"
    assert (await adapter.get_type("default", "old_beds", kind="edge")).status == "retired"
    demo = _items(report, api_name="demoBeds")[0]
    assert demo.outcome == "held" and demo.reason == "status_not_imported"
    assert await adapter.get_type("default", "demo_beds", kind="edge") is None

@pytest.mark.requires_capability("stores_events")
async def test_c12_51_the_word_and_alias_guards_are_inherited_through_import_foundry(
    registry, adapter
):
    """**Round 1, tests lens: §0.5 item 3 was tested for two of its guards.** A
    retired predicate still answering to `zzz_moved` makes `import_types` answer
    `word_previously_retired`, and a live predicate answering to `commentable` makes
    it answer `import_refused:alias_collision`. Through `import_foundry` each comes
    back `refused` with that reason, and neither word is written."""
    await _tombstone_holding(registry, "zzz_moved")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentable"], "status": "active"}],
        kind="predicate",
    )
    doc = _ontology(interfaces={"ZzzMoved": "a moved word", "Commentable": "a capability"})
    report = await registry.import_foundry(doc, dry_run=False)

    moved = _items(report, api_name="ZzzMoved")[0]
    assert (moved.outcome, moved.reason) == ("refused", "word_previously_retired")
    clash = _items(report, api_name="Commentable")[0]
    assert (clash.outcome, clash.reason) == ("refused", "alias_collision")
    assert await adapter.get_type("default", "zzz_moved", kind="predicate") is None
    assert await adapter.get_type("default", "commentable", kind="predicate") is None

async def test_c12_52_a_reference_is_resolved_against_what_was_actually_written(registry, adapter):
    """**Round 2, guards lens.** `unresolved` was computed before the write and only
    knew holds and absence from the document, and the store check counted ANY row,
    retired or not, as resolving a reference. So on the ordinary re-run of a partly
    retired migration, an edge to an entity `import_types` refused, or to a local
    tombstone, was written with nothing reported, and an edge to an entity the same
    document deprecates the same. A reference resolves only to a row that is live
    after the import, and the reason says which case it is: `refused:<reason>` for a
    referent the real run refused and the store does not hold, `retired` for one that
    is (or will be) retired."""
    # The alias-collision half needs a stored alias to collide with (PACKAGE.md 3.2):
    # scaffolding, not the subject, so it runs only where aliases are stored.
    aliases = (await adapter.capabilities()).stores_aliases
    await registry.import_types(
        [{"name": "ward", "kind": "entity", "definition": "a ward", "status": "deprecated"}]
        + ([{"name": "widget", "kind": "entity", "definition": "a widget",
             "aliases": ["gadget"]}] if aliases else [])
    )
    doc = _ontology(
        objects={"Ward": ("a ward", "ACTIVE", ()), "Gadget": ("a gadget", "ACTIVE", ()),
                 "Gone": ("a gone thing", "DEPRECATED", ()), "Bed": ("a bed", "ACTIVE", ())},
        links={"Bed": [_side("inWard", "Ward", "ri.l.w", fk="wardId"),
                       _side("hasGadget", "Gadget", "ri.l.g", fk="gadgetId"),
                       _side("hadGone", "Gone", "ri.l.x", fk="goneId")]},
    )
    definitions = {"Bed.inWard": "a bed is in a ward", "Bed.hasGadget": "a bed has a gadget",
                   "Bed.hadGone": "a bed had a gone thing"}

    planned = await registry.import_foundry(doc, definitions=definitions)
    assert _items(planned, api_name="inWard", kind="edge")[0].detail["unresolved"] == [
        {"dst": "ward", "why": "retired"},
    ], "the dry run sees the local tombstone"
    assert _items(planned, api_name="hadGone", kind="edge")[0].detail["unresolved"] == [
        {"dst": "gone", "why": "retired"},
    ], "the dry run sees the document's own DEPRECATED"

    # Edge names unlike any entity word: a tombstone holds its word across kinds
    # (`C12-21`), so an edge called `ward` would itself be refused.
    report = await registry.import_foundry(doc, dry_run=False, definitions=definitions)
    assert _items(report, api_name="Ward")[0].reason == "name_previously_retired"
    by_side = {i.api_name: i for i in _items(report, kind="edge")}
    assert by_side["inWard"].outcome == "written"
    # The store first (round 3): the tombstone reads `retired`, and the refusal is
    # on `Ward`'s own item.
    assert by_side["inWard"].detail["unresolved"] == [{"dst": "ward", "why": "retired"}]
    if aliases:
        assert _items(report, api_name="Gadget")[0].reason == "alias_collision"
        assert by_side["hasGadget"].detail["unresolved"] == [
            {"dst": "gadget", "why": "refused:alias_collision"},
        ]
    assert by_side["hadGone"].detail["unresolved"] == [{"dst": "gone", "why": "retired"}]
    assert "unresolved" not in _items(report, api_name="Bed")[0].detail

async def test_c12_53_a_retired_row_beside_a_retired_row_of_another_kind_is_written(
    registry, adapter
):
    """**Round 2, guards lens.** Round 1's retired-over-retired refusal matched on the
    name alone, and `standing` can be a tombstone of ANOTHER kind with the identical
    name (the twenty-first trip's cell, `C12-21`). Writing a retired `old` entity
    beside a retired `old` predicate touches no tombstone, so it is written, as it was
    before round 1. Only the row the call would overwrite is protected."""
    await registry.import_types(
        [{"name": "old", "kind": "predicate", "definition": "an old capability",
          "status": "deprecated"}]
    )
    entries = await registry.import_types(
        [{"name": "old", "kind": "entity", "definition": "an old thing",
          "status": "deprecated"}]
    )
    assert not [w for w in entries[0].warnings if w == "name_previously_retired"], entries
    assert (await adapter.get_type("default", "old", kind="entity")).status == "retired"
    assert (await adapter.get_type("default", "old", kind="predicate")).definition == (
        "an old capability"
    )

async def test_c12_54_the_inverse_label_and_the_interface_mapping_are_the_customers_too(
    registry, adapter
):
    """**Round 2, mapping lens.** Three things a migrating customer said and lost.

    1. A `names=` key on a link's INVERSE side (`"Dept.staff"`) renamed the
       `inverse_label` and was reported in `unmatched` as matching nothing, because only
       forward keys were item keys. It is now `detail["inverse_key"]`, and a label
       that is not a legal name is held `name_invalid` rather than written unchecked.
    2. `implementsInterfaces2`'s VALUES (which local property implements which
       interface property) and `sharedPropertyTypeMapping` sit beside `objectType`, so
       the carry never reached them. They are carried, not validated.
    3. A predicate word that fails `NAME_RE` was written into the entity's
       `predicates`; it stays reported in `unresolved` and is not written."""
    long_iface = "I" + "x" * 70
    doc = _ontology(
        interfaces={"Located": "has a place", long_iface: "too long to be a name"},
        objects={"Dept": ("a department", "ACTIVE", ()),
                 "Employee": ("an employee", "ACTIVE", ("Located", long_iface))},
        links={"Employee": [_side("dept", "Dept", "ri.l.d", fk="deptId")],
               "Dept": [_side("staff", "Employee", "ri.l.d")]},
    )
    implementation = {"properties": {"place": "officeName"}, "links": {}}
    doc["objectTypes"]["Employee"]["implementsInterfaces2"]["Located"] = implementation
    doc["objectTypes"]["Employee"]["sharedPropertyTypeMapping"] = {"spt": "officeName"}
    definitions = {"Employee.dept": "an employee works in a department"}

    named = await registry.import_foundry(
        doc, names={"Dept.staff": "employs"}, definitions=definitions
    )
    edge = _items(named, kind="edge")[0]
    assert (edge.detail["inverse_label"], edge.detail["inverse_key"]) == (
        "employs", "Dept.staff",
    )
    assert named.unmatched == {"names": [], "definitions": []}

    bad = await registry.import_foundry(
        doc, names={"Dept.staff": "Bad Name"}, definitions=definitions
    )
    held = _items(bad, kind="edge")[0]
    assert (held.outcome, held.reason, held.detail["invalid"]) == (
        "held", "name_invalid", "inverse_label",
    )

    report = await registry.import_foundry(doc, dry_run=False, definitions=definitions)
    employee = _items(report, api_name="Employee")[0]
    assert employee.outcome == "written"
    assert {"predicate": long_iface.lower(), "why": "held:name_invalid"} in (
        employee.detail["unresolved"]
    )
    stored = await adapter.get_type("default", "employee", kind="entity")
    assert long_iface.lower() not in (stored.predicates or ())
    if (await adapter.capabilities()).stores_attributes:
        carried = stored.attributes["foundry_object_type_metadata"]
        assert carried["validated"] is False
        assert carried["implementsInterfaces2"]["Located"] == implementation
        assert carried["sharedPropertyTypeMapping"] == {"spt": "officeName"}

async def test_c12_55_what_the_record_says_is_tested_is_tested(adapter, make_registry):
    """**Round 2, tests lens.** Four claims the record made that no test could fail on,
    and a fifth found while fixing them.

    1. A non-str value in EITHER map raises a ``TypeError`` naming the key. Only
       ``names`` was exercised, so dropping the ``definitions`` check left the suite
       green and ``definitions={"Ward": 5}`` read as "no definition supplied".
    2. ``operations`` (``ActionTypeV2``) spells a link rule ``CreateLinkRule`` with
       ``linkTypeApiNameAtoB`` (``foundry_sdk.v2.ontologies.models.CreateLinkRule``),
       not ``linkTypeApiName``: an action read from ``operations`` named no link.
    3. The look-alike filter reads the namespace's ``near_duplicate_threshold``
       (``8A-RUN.md`` §1.2 item 1); it was pinned only at its extremes.
    4. ``definition_missing`` and ``status_not_imported`` say how to lift the hold.
    """
    registry = await make_registry(adapter)
    doc = foundry_fixture("uc2_cms")
    with pytest.raises(TypeError, match=r"definitions\['Ward'\] must be a str, got int"):
        await registry.import_foundry(doc, definitions={"Ward": 5})
    with pytest.raises(TypeError, match=r"names\['Ward'\] must be a str, got NoneType"):
        await registry.import_foundry(doc, names={"Ward": None})

    edge_cases = foundry_fixture("edge_cases")
    edge_cases.pop("actionTypesFullMetadata")
    action = _items(await registry.import_foundry(edge_cases), api_name="assignDoctor")[0]
    assert action.detail["effects"][0] == {
        "op": "add_edge", "rule": "createLink", "link": "treats", "source": "operations",
        "inverse_link": "treatedBy",
    }

    def facilities():
        moved = foundry_fixture("uc2_cms")
        moved["objectTypes"]["Facilities"] = moved["objectTypes"].pop("Facility")
        moved["objectTypes"]["Facilities"]["objectType"]["apiName"] = "Facilities"
        return moved

    await seed(registry, "facility", definition="A licensed nursing home.")
    for threshold, expected in ((0.77, True), (0.78, False)):
        strict = await make_registry(adapter, near_duplicate_threshold=threshold)
        looks = {(lk.name, lk.matched) for lk in (await strict.import_foundry(facilities())).looks_like}
        assert (("facilities", "facility") in looks) is expected, (threshold, looks)

    status_doc = _ontology(objects={"Draft": ("a draft", "EXAMPLE", ())})
    held = _items(await registry.import_foundry(status_doc), api_name="Draft")[0]
    assert (held.reason, held.detail["foundry_status"]) == ("status_not_imported", "EXAMPLE")
    bare = _ontology(objects={"Bare": (None, "ACTIVE", ())})
    held = _items(await registry.import_foundry(bare), api_name="Bare")[0]
    assert (held.reason, held.detail["definitions_key"]) == ("definition_missing", "Bare")

    # 5. A name `resolve_type` answers with ANOTHER row (a variant spelling) is a
    #    look-alike, reported ONCE: the answer and its first alternative were both read.
    await seed(registry, "widget", definition="a widget")
    widgets = _ontology(objects={"Widgets": ("some widgets", "ACTIVE", ())})
    assert [(lk.name, lk.matched) for lk in (await registry.import_foundry(widgets)).looks_like] == [
        ("widgets", "widget"),
    ]

async def test_c12_56_every_action_and_its_logic_reaches_the_store(registry, adapter):
    """**Round 3, mapping lens.** `OntologyFullMetadata` carries actions in two maps,
    `actionTypes` and `actionTypesFullMetadata` (whose `actionType` is a whole
    `ActionTypeV2`, beside its `fullLogicRules`), and only the first was walked. An
    action in the second alone produced no item and no count. And `fullLogicRules`
    was read for the report but never stored, while `ActionTypeV2.operations` has no
    `function` or interface rule variants, so for those the logic left with the
    report. An action is now the union of both maps, and its `fullLogicRules` are
    carried. An `operations` link rule also reports its B-to-A name."""
    doc = _ontology()
    doc["actionTypesFullMetadata"] = {
        "doIt": {
            "actionType": {"apiName": "doIt", "description": "does it", "status": "ACTIVE",
                           "parameters": {}, "operations": []},
            "fullLogicRules": [{"type": "function", "functionRid": "ri.f.1",
                                "functionVersion": "1.0.0"}],
        }
    }
    report = await registry.import_foundry(doc, dry_run=False)
    action = _items(report, api_name="doIt")[0]
    assert (action.kind, action.outcome) == ("action", "written")
    assert [e["op"] for e in action.detail["effects"]] == ["host_state"]
    if (await adapter.capabilities()).stores_attributes:
        stored = await adapter.get_type("default", "do_it", kind="action")
        assert stored.attributes["foundry_action"]["fullLogicRules"] == (
            doc["actionTypesFullMetadata"]["doIt"]["fullLogicRules"]
        )

    edge_cases = foundry_fixture("edge_cases")
    edge_cases.pop("actionTypesFullMetadata")
    effect = _items(await registry.import_foundry(edge_cases), api_name="assignDoctor")[0].detail[
        "effects"
    ][0]
    assert (effect["link"], effect["inverse_link"]) == ("treats", "treatedBy")

async def test_c12_57_a_document_that_is_not_full_metadata_is_refused_not_emptied(registry):
    """**Round 3, mapping lens.** A dict with none of `OntologyFullMetadata`'s type
    maps (a pydantic `model_dump()` without `by_alias=True` gives `object_types`) was
    read as an empty ontology: a clean dry run, and a real run that wrote nothing. A
    caller's mistake, said as one. An empty ontology still has its keys."""
    with pytest.raises(ValueError, match="by_alias=True"):
        await registry.import_foundry({"ontology": {}, "object_types": {"Person": {}}})
    with pytest.raises(TypeError, match="dict"):
        await registry.import_foundry([])
    assert (await registry.import_foundry(_ontology())).items == ()

async def test_c12_58_a_definitions_key_on_an_inverse_side_is_unmatched(registry):
    """**Round 3, mapping lens.** `definitions=` keyed by an inverse side was checked
    against the inverse keys `names=` takes, so it read as matched and defined
    nothing. Only an item's own key takes a definition."""
    doc = _ontology(
        objects={"Pet": ("a pet", "ACTIVE", ()), "Owner": ("an owner", "ACTIVE", ())},
        links={"Pet": [_side("owner", "Owner", "ri.l.o", fk="ownerId")],
               "Owner": [_side("pets", "Pet", "ri.l.o")]},
    )
    report = await registry.import_foundry(doc, definitions={"Owner.pets": "an owner has pets"})
    assert report.unmatched == {"names": [], "definitions": ["Owner.pets"]}
    assert _items(report, kind="edge")[0].reason == "definition_missing"

async def test_c12_59_a_referent_the_store_holds_live_is_resolved(registry, adapter):
    """**Round 3, guards lens.** `unresolved` trusted the plan before the store. A
    migration re-run without `definitions=` holds a standing interface
    `definition_missing` (the plan never asks the store), while its row stays active,
    and every entity implementing it was told its predicate was missing. The store is
    asked first: a live row resolves the reference, whatever the plan held."""
    doc = _ontology(
        interfaces={"Auditable": None},
        objects={"Flight": ("a flight", "ACTIVE", ("Auditable",))},
    )
    first = await registry.import_foundry(
        doc, dry_run=False, definitions={"Auditable": "a record keeps an audit trail"}
    )
    assert "unresolved" not in _items(first, api_name="Flight")[0].detail

    again = await registry.import_foundry(doc, dry_run=False)
    assert _items(again, api_name="Auditable")[0].reason == "definition_missing"
    assert (await adapter.get_type("default", "auditable", kind="predicate")).status == "active"
    assert "unresolved" not in _items(again, api_name="Flight")[0].detail

async def test_c12_60_the_rest_of_round_3s_record_is_pinned(registry, adapter, make_registry):
    """**Round 3, tests lens.** Four claims the record made that a narrower mutant passed.

    1. `foundry_object_type_metadata` is EVERY sibling but `objectType` and
       `linkTypes`. Only the two keys `C12-54` names were asserted, so keeping
       `objectType` or `linkTypes` in it, or dropping `implementsInterfaces`, passed.
    2. A dry run reads a referent the document deprecates as `retired` even while the
       store holds it live, and Foundry's status is matched in any case.
    3. A look-alike at EXACTLY the namespace's `near_duplicate_threshold` is reported.
    4. `detail["standing"]` asks the store for the item's own kind: a predicate named
       like an entity is not that entity standing."""
    doc = _ontology(objects={"Crew": ("a crew", "ACTIVE", ())})
    doc["objectTypes"]["Crew"]["extraSibling"] = {"kept": True}
    await registry.import_foundry(doc, dry_run=False)
    if (await adapter.capabilities()).stores_attributes:
        stored = await adapter.get_type("default", "crew", kind="entity")
        full = doc["objectTypes"]["Crew"]
        assert stored.attributes["foundry_object_type_metadata"] == {
            "validated": False,
            **{k: v for k, v in full.items() if k not in ("objectType", "linkTypes")},
        }

    pets = _ontology(
        objects={"Pet": ("a pet", "ACTIVE", ()), "Owner": ("an owner", "ACTIVE", ())},
        links={"Pet": [_side("owner", "Owner", "ri.l.o", fk="ownerId")],
               "Owner": [_side("pets", "Pet", "ri.l.o")]},
    )
    defined = {"Pet.owner": "a pet has an owner"}
    await registry.import_foundry(pets, dry_run=False, definitions=defined)
    assert (await adapter.get_type("default", "owner", kind="entity")).status == "active"
    pets["objectTypes"]["Owner"]["objectType"]["status"] = "deprecated"
    edge = _items(await registry.import_foundry(pets, definitions=defined), kind="edge")[0]
    assert {"dst": "owner", "why": "retired"} in edge.detail["unresolved"]

    await seed(registry, "facility", kind="predicate", definition="a facility predicate")
    cms = foundry_fixture("uc2_cms")
    facility = _items(await registry.import_foundry(cms), api_name="Facility")[0]
    assert facility.detail["standing"] is False

    await seed(registry, "widget", definition="a widget")
    widgets = _ontology(objects={"Widgets": ("some widgets", "ACTIVE", ())})
    [score] = [lk.score for lk in (await (await make_registry(
        adapter, near_duplicate_threshold=0.0
    )).import_foundry(widgets)).looks_like if lk.matched == "widget"]
    at = await make_registry(adapter, near_duplicate_threshold=score)
    assert [lk.matched for lk in (await at.import_foundry(widgets)).looks_like] == ["widget"]

async def test_c12_61_what_a_write_would_lose_is_said_before_it_is_lost(registry, adapter):
    """**Round 4, guards and mapping lenses.**

    1. A live local row with the item's name was overwritten (`import_types` replaces
       a standing row's predicates, aliases and attributes, and its definition when
       one is supplied), its predicate dropped from under a consumer's gate, and the
       item said `written` with `standing: True` and nothing else. What would be lost
       is now `detail["replaces"]`, on the dry run as well, and an idempotent re-run
       reports nothing. Whether to REFUSE it is the founder's.
    2. An action only in `actionTypesFullMetadata` reported `effects: []`: its
       `operations` sit in that map's `actionType`, and only `actionTypes` was read.
    3. `visibility: None`, as `model_dump(by_alias=True)` emits an unset field, was
       stored as an attribute."""
    doc = _ontology(objects={"Employee": ("an employee", "ACTIVE", ())})
    doc["objectTypes"]["Employee"]["objectType"]["visibility"] = None
    doc["actionTypesFullMetadata"] = {
        "relocate": {
            "actionType": {
                "apiName": "relocate", "description": "moves an employee",
                "status": "ACTIVE", "parameters": {},
                "operations": [{"type": "createLink", "linkTypeApiNameAtoB": "office",
                                "linkTypeApiNameBtoA": "employees",
                                "aSideObject": "a", "bSideObject": "b"}],
            },
            "fullLogicRules": [],
        }
    }
    action = _items(await registry.import_foundry(doc), api_name="relocate")[0]
    assert action.detail["effects"] == [{
        "op": "add_edge", "rule": "createLink", "link": "office",
        "source": "operations", "inverse_link": "employees",
    }]

    await seed(registry, "employee", definition="a locally approved employee",
         predicates=["audited"])
    dry = _items(await registry.import_foundry(doc), api_name="Employee")[0]
    lost = dry.detail["replaces"]
    held = sorted((await adapter.get_type("default", "employee", kind="entity")).predicates or ())
    assert (lost["imported_from"], lost.get("predicates_dropped", []), lost["definition_replaced"]) == (
        None, held, True,
    )

    written = _items(await registry.import_foundry(doc, dry_run=False), api_name="Employee")[0]
    assert (written.outcome, written.detail["replaces"]) == ("written", lost)
    stored = await adapter.get_type("default", "employee", kind="entity")
    assert "audited" not in (stored.predicates or ())
    if (await adapter.capabilities()).stores_attributes:
        assert "visibility" not in stored.attributes

    again = _items(await registry.import_foundry(doc, dry_run=False), api_name="Employee")[0]
    assert "replaces" not in again.detail

async def test_c12_62_a_namespace_reads_its_own_store(registry):
    """**Round 4, tests lens.** `namespace=` was pinned only where it reaches
    `import_types`. `standing`, the look-alike `resolve_type`, the store read behind
    `unresolved` and `report.namespace` could each read `"default"` with the suite
    green, so a customer importing into its own namespace would be told about
    another namespace's vocabulary."""
    await seed(registry, "pet", namespace="vet", definition="an animal in the care of a vet")
    await seed(registry, "auditable", namespace="vet", kind="predicate",
         definition="a record keeps an audit trail")
    await seed(registry, "pets", definition="the pets a household keeps")
    doc = _ontology(objects={"Pet": ("a pet", "ACTIVE", ()),
                             "Flight": ("a flight", "ACTIVE", ("Auditable",))})

    vet = await registry.import_foundry(doc, namespace="vet")
    assert vet.namespace == "vet"
    assert _items(vet, api_name="Pet")[0].detail["standing"] is True
    assert vet.looks_like == ()
    assert "unresolved" not in _items(vet, api_name="Flight")[0].detail

    default = await registry.import_foundry(doc)
    assert default.namespace == "default"
    assert _items(default, api_name="Pet")[0].detail["standing"] is False
    assert ("pet", "pets") in {(lk.name, lk.matched) for lk in default.looks_like}
    assert _items(default, api_name="Flight")[0].detail["unresolved"] == [
        {"predicate": "auditable", "why": "not_in_document"},
    ]

async def test_c12_63_every_link_rule_and_an_actions_status(registry, adapter):
    """**Round 4, tests lens.** Only `createLink`, `createInterfaceLink` and
    `deleteInterfaceLink` were pinned, so `deleteLink` could become `host_state` with
    the suite green; a retract's `inverse_link` and `source` were unpinned; and an
    action's `status` was never exercised (`C12-50`'s twin, fixed for links only).
    `addLink` and `removeLink`, named at pre-registration, are not rule types the SDK
    defines, so they are `host_state`. A dry run reads a deprecated referent the
    planner HOLDS as held, not retired, and an edge reports its source too."""
    link = {"linkTypeApiNameAtoB": "owner", "linkTypeApiNameBtoA": "pets",
            "aSideObject": "a", "bSideObject": "b"}
    ops = [{"type": t, **link} for t in ("createLink", "deleteLink", "addLink", "removeLink")]
    doc = _ontology(actions={
        "rehome": {"apiName": "rehome", "description": "rehomes a pet", "status": "ACTIVE",
                   "parameters": {}, "operations": ops},
        "draft": {"apiName": "draft", "description": "a draft", "status": "EXAMPLE",
                  "parameters": {}, "operations": []},
        "old": {"apiName": "old", "description": "an old action", "status": "DEPRECATED",
                "parameters": {}, "operations": []},
    })
    doc["actionTypesFullMetadata"] = {
        "stale": {"actionType": {"apiName": "stale", "description": "a stale action",
                                 "status": "DEPRECATED", "parameters": {}, "operations": []},
                  "fullLogicRules": [{"type": "deleteLink", "linkTypeApiName": "owner"}]},
    }
    report = await registry.import_foundry(doc, dry_run=False)
    effects = _items(report, api_name="rehome")[0].detail["effects"]
    assert [(e["op"], e.get("inverse_link"), e["source"]) for e in effects] == [
        ("add_edge", "pets", "operations"), ("retract_edge", "pets", "operations"),
        ("host_state", None, "operations"), ("host_state", None, "operations"),
    ]
    stale = _items(report, api_name="stale")[0]
    assert stale.detail["effects"][0]["op"] == "retract_edge"
    assert stale.detail["effects"][0]["source"] == "fullLogicRules"
    assert _items(report, api_name="draft")[0].reason == "status_not_imported"
    for name in ("old", "stale"):
        assert _items(report, api_name=name)[0].outcome == "written"
        assert (await adapter.get_type("default", name, kind="action")).status == "retired"

    pets = _ontology(
        objects={"Pet": (None, "ACTIVE", ()), "Owner": (None, "DEPRECATED", ())},
        links={"Pet": [_side("owner", "Owner", "ri.l.o", fk="ownerId")],
               "Owner": [_side("pets", "Pet", "ri.l.o")]},
    )
    defined = {"Pet.owner": "a pet has an owner"}
    for dry_run in (True, False):
        edge = _items(await registry.import_foundry(pets, dry_run=dry_run, definitions=defined),
                      kind="edge")[0]
        assert edge.detail["unresolved"] == [
            {"src": "pet", "why": "held:definition_missing"},
            {"dst": "owner", "why": "held:definition_missing"},
        ], dry_run

async def test_c12_64_the_mapping_the_record_states_is_the_mapping(registry, adapter):
    """**Round 4, tests lens.** Mapping claims a narrower mutant passed: the foreign
    `rid` in provenance for every kind (only entities were checked), the forward side
    of a self-link with no foreign key chosen by `(objectType, side)` whatever the
    document order, the name conversion's acronym rule and its strip, the
    `implementsInterfaces` list read on its own (and a repeat written once), an
    entity's `visibility` through `import_foundry`, `report.entries`, the inverse
    label's `fullmatch`, a blank description held at the planner, and a document
    carrying only some of the type maps."""
    from ontoloche.foundry import convert_name

    names = ("NFLPlayer", "HTTPServer", "_Foo", "Foo_", "Route66Bus")
    assert [convert_name(n) for n in names] == [
        "nfl_player", "http_server", "foo", "foo", "route66_bus",
    ]

    doc = _ontology(
        interfaces={"Located": "has a place", "Named": "has a name"},
        objects={"Pet": ("a pet", "ACTIVE", ()), "Owner": ("an owner", "ACTIVE", ())},
        links={"Pet": [_side("owner", "Owner", "ri.l.o", fk="ownerId")],
               "Owner": [_side("pets", "Pet", "ri.l.o")]},
        actions={"feed": {"apiName": "feed", "rid": "ri.a.feed", "description": "feeds",
                          "status": "ACTIVE", "parameters": {}, "operations": []}},
    )
    pet = doc["objectTypes"]["Pet"]
    pet["implementsInterfaces"] = ["Located", "Located"]
    pet.pop("implementsInterfaces2")
    doc["objectTypes"]["Owner"]["implementsInterfaces"] = ["Named"]
    doc["objectTypes"]["Owner"]["implementsInterfaces2"] = {"Located": {}}
    pet["objectType"]["visibility"] = "PROMINENT"
    defined = {"Pet.owner": "a pet has an owner"}
    report = await registry.import_foundry(doc, dry_run=False, definitions=defined)
    assert _items(report, api_name="Pet")[0].detail["predicates"] == ["located"]
    assert _items(report, api_name="Owner")[0].detail["predicates"] == ["named", "located"]
    assert [e.name for e in report.entries] == [
        i.name for i in report.items if i.outcome in ("written", "refused")
    ]
    assert len(report.entries) == 6
    expected = {("predicate", "located"): ("Located", "ri.i.Located"),
                ("entity", "pet"): ("Pet", "ri.o.Pet"),
                ("edge", "owner"): ("Pet.owner", "ri.l.o"),
                ("action", "feed"): ("feed", "ri.a.feed")}
    for (kind, name), (api, rid) in expected.items():
        stored = await adapter.get_type("default", name, kind=kind)
        assert stored.provenance["imported_from"] == {
            "system": "foundry", "apiName": api, "rid": rid,
        }, (kind, name)
    if (await adapter.capabilities()).stores_attributes:
        assert (await adapter.get_type("default", "pet", kind="entity")).attributes[
            "visibility"] == "PROMINENT"

    for order in ((0, 1), (1, 0)):
        sides = [_side("boss", "Employee", "ri.l.b"), _side("reports", "Employee", "ri.l.b")]
        selfie = _ontology(objects={"Employee": ("an employee", "ACTIVE", ())},
                           links={"Employee": [sides[i] for i in order]})
        edge = _items(await registry.import_foundry(selfie), kind="edge")[0]
        assert (edge.name, edge.detail["inverse_label"]) == ("boss", "reports"), order

    held = _items(await registry.import_foundry(
        doc, names={"Owner.pets": "owned_pets\n"}, definitions=defined,
    ), kind="edge")[0]
    assert (held.reason, held.detail["invalid"]) == ("name_invalid", "inverse_label")

    blank = _ontology(objects={"Blank": ("   ", "ACTIVE", ())})
    assert _items(await registry.import_foundry(blank), api_name="Blank")[0].reason == (
        "definition_missing"
    )
    solo = _ontology(objects={"Solo": ("a solo", "ACTIVE", ())})["objectTypes"]
    only = {"ontology": {}, "objectTypes": solo}
    assert [i.name for i in (await registry.import_foundry(only)).items] == ["solo"]

async def test_c12_65_what_a_write_would_lose_is_what_it_would_write(registry, adapter):
    """**Round 5, guards, mapping and tests lenses.** `replaces` diffed the stored row
    against the row it hands `import_types`, but `import_types` appends `experimental`
    or `endorsed` for those statuses, so every idempotent re-run of such an item
    reported the marker dropped. It also omitted the two largest losses, a live row a
    `DEPRECATED` import would retire and a human approver overwritten with
    `unknown:imported`. And `aliases_dropped`, `attributes_dropped`, the
    `imported_from` system and the live-only gate were each unpinned."""
    caps = await adapter.capabilities()
    for status in ("EXPERIMENTAL", "ENDORSED"):
        doc = _ontology(objects={"Ward": ("a hospital ward", status, ())})
        await registry.import_foundry(doc, dry_run=False)
        for dry_run in (True, False):
            again = _items(await registry.import_foundry(doc, dry_run=dry_run), api_name="Ward")[0]
            assert "replaces" not in again.detail, (status, dry_run, again.detail)

    await seed(registry, "employee", definition="an employee", approved_by="user:sd")
    gone = _ontology(objects={"Employee": ("an employee", "DEPRECATED", ())})
    lost = _items(await registry.import_foundry(gone), api_name="Employee")[0].detail["replaces"]
    approver = (await adapter.get_type("default", "employee", kind="entity")).provenance["approved_by"]
    assert approver and approver != "unknown:imported"
    assert (lost.get("retires"), lost.get("approved_by_replaced")) == (True, approver)
    assert "definition_replaced" not in lost

    await registry.import_types(
        [{"name": "contractor", "kind": "entity", "definition": "a contractor",
          "aliases": ["temp_worker"], "attributes": {"cost_centre": "c1"}}],
        system="hr",
    )
    doc = _ontology(objects={"Contractor": ("a contractor", "ACTIVE", ())})
    lost = _items(await registry.import_foundry(doc), api_name="Contractor")[0].detail["replaces"]
    assert lost["imported_from"] == "hr"
    assert "approved_by_replaced" not in lost
    if caps.stores_aliases:
        assert lost["aliases_dropped"] == ["temp_worker"]
    if caps.stores_attributes:
        assert lost["attributes_dropped"] == ["cost_centre"]

    looked = _ontology(objects={"Desk": ("a desk", "ACTIVE", ("Located",))},
                       interfaces={"Located": "has a place"})
    await registry.import_foundry(looked, dry_run=False)
    looked["objectTypes"]["Desk"]["implementsInterfaces"] = []
    looked["objectTypes"]["Desk"]["implementsInterfaces2"] = {}
    if "located" in ((await adapter.get_type("default", "desk", kind="entity")).predicates or ()):
        lost = _items(await registry.import_foundry(looked), api_name="Desk")[0].detail["replaces"]
        assert (lost["imported_from"], lost["predicates_dropped"]) == ("foundry", ["located"])

    if caps.indexes_membership:
        # `retire` reads consumers through the membership index (`C12-44`'s marker).
        await seed(registry, "chair", definition="a chair", predicates=["audited"])
        await registry.retire("chair", "replaced by seating", retired_by="user:sd")
        assert (await adapter.get_type("default", "chair", kind="entity")).status == "retired"
        chair = _ontology(objects={"Chair": ("something to sit on", "ACTIVE", ())})
        item = _items(await registry.import_foundry(chair), api_name="Chair")[0]
        assert "replaces" not in item.detail

async def test_c12_66_a_backend_that_keeps_no_attributes_says_what_it_drops(
    adapter, make_registry
):
    """**Round 5, mapping lens.** The importer routes most of its mapping through
    attributes, and on a backend declining `stores_attributes` every key outside
    `attribute_projections` was dropped while the item said `written`. The item names
    the keys this backend would not keep, on a dry run and a real run, and a projected
    key is not among them. Reported, not held."""
    doc = _ontology(objects={"Pet": ("a pet", "ACTIVE", ())})
    doc["objectTypes"]["Pet"]["objectType"]["visibility"] = "PROMINENT"

    full = await make_registry(adapter, approval_policy="auto")
    if (await adapter.capabilities()).stores_attributes:
        item = _items(await full.import_foundry(doc), api_name="Pet")[0]
        assert "attributes_not_stored" not in item.detail

    bare = await make_registry(
        AsyncDegradedAdapter(adapter, stores_attributes=False, attribute_projections=("visibility",)),
        approval_policy="auto",
    )
    for dry_run in (True, False):
        item = _items(await bare.import_foundry(doc, dry_run=dry_run), api_name="Pet")[0]
        dropped = item.detail["attributes_not_stored"]
        assert "foundry_object_type" in dropped and "visibility" not in dropped, dry_run
        assert dropped == sorted(dropped)
        assert item.outcome == ("would_write" if dry_run else "written")

async def test_c12_67_a_rename_reaches_an_edge_and_a_blank_definition_is_no_definition(
    registry, adapter
):
    """**Round 5, tests lens.** A `names=` rename of an object type was not pinned on
    an edge's `src_type` and `dst_type`, the flow R110's collision lift depends on,
    and a blank `definitions=` value was not pinned: loosening the check made a dry run
    say `would_write` for a row the real run refuses."""
    doc = _ontology(
        objects={"Pet": (None, "ACTIVE", ()), "Owner": ("an owner", "ACTIVE", ())},
        links={"Pet": [_side("owner", "Owner", "ri.l.o", fk="ownerId")],
               "Owner": [_side("pets", "Pet", "ri.l.o")]},
    )
    names = {"Pet": "animal", "Owner": "keeper"}
    edge = _items(await registry.import_foundry(
        doc, names=names, definitions={"Pet.owner": "an animal has a keeper"},
    ), kind="edge")[0]
    assert edge.detail["unresolved"] == [{"src": "animal", "why": "held:definition_missing"}]

    defined = {"Pet": "a pet", "Pet.owner": "an animal has a keeper"}
    await registry.import_foundry(doc, dry_run=False, names=names, definitions=defined)
    if (await adapter.capabilities()).stores_attributes:
        link = (await adapter.get_type("default", "owner", kind="edge")).attributes["foundry_link"]
        assert (link["src_type"], link["dst_type"]) == ("animal", "keeper")

    blank = {"Pet": "a pet", "Pet.owner": "   "}
    for dry_run in (True, False):
        edge = _items(await registry.import_foundry(doc, dry_run=dry_run, definitions=blank),
                      kind="edge")[0]
        assert (edge.outcome, edge.reason) == ("held", "definition_missing"), dry_run
    fresh = {"Pet": "pet", "Owner": "guardian"}
    await registry.import_foundry(doc, dry_run=False, names=fresh, definitions={"Owner": "  "})
    assert (await adapter.get_type("default", "guardian", kind="entity")).definition == "an owner"

async def test_c12_68_a_changed_value_is_a_loss_and_a_held_item_reports_none(
    registry, adapter, make_registry
):
    """**Round 6, guards and tests lenses** (item 27, ruled `fix and land`).

    1. `replaces` compared attribute KEYS and never values, so a local
       `visibility: "restricted"` written as `NORMAL`, or an edge family's
       `symmetric: True` written as `False`, was silent. `attributes_changed` names
       each shared key whose value the write changes. A `foundry_*` carry key is left
       out only when the standing row was imported from Foundry, and an idempotent
       re-run of an edge reports nothing.
    2. `replaces` and `attributes_not_stored` describe a write, so a HELD item beside a
       standing row carries neither (the `p.reason is None` gate, unpinned)."""
    if (await adapter.capabilities()).stores_attributes:
        await seed(registry, "employee", definition="an employee",
             attributes={"visibility": "restricted", "foundry_object_type": {"local": 1}})
        doc = _ontology(objects={"Employee": ("an employee", "ACTIVE", ())})
        doc["objectTypes"]["Employee"]["objectType"]["visibility"] = "NORMAL"
        for dry_run in (True, False):
            lost = _items(await registry.import_foundry(doc, dry_run=dry_run),
                          api_name="Employee")[0].detail["replaces"]
            assert lost["attributes_changed"] == ["foundry_object_type", "visibility"], dry_run

        doc["objectTypes"]["Employee"]["objectType"]["icon"] = {"type": "blueprint"}
        doc["objectTypes"]["Employee"]["objectType"]["visibility"] = "PROMINENT"
        lost = _items(await registry.import_foundry(doc), api_name="Employee")[0].detail["replaces"]
        assert lost == {"imported_from": "foundry", "attributes_changed": ["visibility"]}

        await seed(registry, "person", definition="a person")
        await seed(registry, "friends", kind="edge", definition="people who are friends",
             attributes={"level": "instance", "symmetric": True, "inverse_label": None,
                         "endpoint_kinds": {"src": ["entity"], "dst": ["entity"]},
                         "payload_schema": None})
        people = _ontology(
            objects={"Person": ("a person", "ACTIVE", ())},
            links={"Person": [_side("friends", "Person", "ri.l.f", fk="friendId"),
                              _side("friendOf", "Person", "ri.l.f")]},
        )
        defined = {"Person.friends": "people who are friends"}
        edge = _items(await registry.import_foundry(people, definitions=defined), kind="edge")[0]
        assert edge.detail["replaces"]["attributes_changed"] == ["inverse_label", "symmetric"]
        await registry.import_foundry(people, dry_run=False, definitions=defined)
        again = _items(await registry.import_foundry(people, definitions=defined), kind="edge")[0]
        assert "replaces" not in again.detail

    await seed(registry, "solo", definition="a local solo", predicates=["audited"])
    bare = await make_registry(AsyncDegradedAdapter(adapter, stores_attributes=False),
                         approval_policy="auto")
    held_doc = _ontology(objects={"Solo": (None, "ACTIVE", ())})
    for reg in (registry, bare):
        for dry_run in (True, False):
            item = _items(await reg.import_foundry(held_doc, dry_run=dry_run), api_name="Solo")[0]
            assert (item.outcome, item.reason) == ("held", "definition_missing")
            assert "replaces" not in item.detail and "attributes_not_stored" not in item.detail

FIXTURES = ("faux_employee", "faux_legacy", "uc2_cms", "uc3_nyc", "edge_cases")

async def _stores(adapter, key):
    return (await adapter.capabilities()).stores_attribute(key)

def _slots(report_or_doc_planned, api):
    from ontoloche.foundry import plan

    planned, *_ = plan(report_or_doc_planned)
    return next(p for p in planned if p.kind == "entity" and p.api_name == api).row["attributes"]

async def test_c12_69_shared_property_types_import_as_property_entries_first(registry, adapter):
    doc = foundry_fixture("faux_legacy")
    dry = await registry.import_foundry(doc)
    kinds = [i.kind for i in dry.items]
    assert kinds.index("property") < kinds.index("entity") and kinds.index("property") > kinds.index("predicate")
    (foo,) = _items(dry, kind="property")
    assert (foo.api_name, foo.name, foo.outcome) == ("fooSpt", "foo_spt", "would_write")

    real = await registry.import_foundry(doc, dry_run=False)
    (written,) = _items(real, kind="property")
    assert written.outcome == "written"
    assert not [w for w in written.warnings if w.startswith("property_reference")]
    entry = await adapter.get_type("default", "foo_spt", kind="property")
    assert entry.definition == "A foo"
    if await _stores(adapter, "base_type"):
        assert entry.attributes["base_type"] == "str" and entry.attributes["display_name"] == "Foo"
        assert entry.attributes["foundry_shared_property"] == {"validated": False, "typeClasses": []}
    else:
        assert "property_declaration_not_stored:base_type" in written.warnings

    # R109 at the property door: no description, no definition, held; `definitions=` lifts it.
    bare = {"objectTypes": {}, "sharedPropertyTypes": {"barSpt": {"apiName": "barSpt", "dataType": {"type": "long"}}}}
    held = _items(await registry.import_foundry(bare, dry_run=False), kind="property")[0]
    assert (held.outcome, held.reason) == ("held", "definition_missing")
    assert await adapter.get_type("default", "bar_spt", kind="property") is None
    lifted = _items(
        await registry.import_foundry(bare, dry_run=False, definitions={"barSpt": "a bar count"}), kind="property"
    )[0]
    assert lifted.outcome == "written"

async def test_c12_70_object_type_properties_become_local_and_shared_slots(registry, adapter):
    doc = foundry_fixture("faux_legacy")
    source = doc["objectTypes"]["Employee"]["objectType"]
    attributes = _slots(doc, "Employee")
    slots = attributes["properties"]
    assert [s["name"] for s in slots] == list(source["properties"])
    assert {s["name"]: s.get("shared") for s in slots if "shared" in s} == {"fullName": "foo_spt"}
    full_name = next(s for s in slots if s["name"] == "fullName")
    assert set(full_name) <= {"name", "shared", "display_name"}
    assert attributes["primary_key"] == [source["primaryKey"]]
    assert attributes["title_property"] == source["titleProperty"]
    assert declaration_problem("entity", attributes) is None

    await registry.import_foundry(doc, dry_run=False)
    stored = await adapter.get_type("default", "employee", kind="entity")
    view = entity_declaration(stored, await adapter.capabilities())
    if await _stores(adapter, "properties"):
        assert [p.name for p in view.properties] == list(source["properties"])
        assert next(p for p in view.properties if p.name == "fullName").shared == "foo_spt"
    else:
        assert view.why_absent["properties"] == "not_stored"
    if await _stores(adapter, "primary_key"):
        assert view.primary_key == (source["primaryKey"],)

@pytest.mark.parametrize(
    "data_type, expected",
    [
        ({"type": "string"}, ("str", None, None)),
        ({"type": "integer"}, ("int", None, None)),
        ({"type": "long"}, ("int", None, "long")),
        ({"type": "short"}, ("int", None, "short")),
        ({"type": "byte"}, ("int", None, "byte")),
        ({"type": "double"}, ("float", None, None)),
        ({"type": "float"}, ("float", None, "float")),
        ({"type": "decimal"}, ("decimal", None, "decimal")),
        ({"type": "decimal", "precision": 10, "scale": 2},
         ("decimal", None, '{"precision":10,"scale":2,"type":"decimal"}')),
        ({"type": "decimal", "precision": None, "scale": None}, ("decimal", None, "decimal")),
        ({"type": "boolean"}, ("bool", None, None)),
        ({"type": "date"}, ("date", None, None)),
        ({"type": "timestamp"}, ("datetime", None, None)),
        ({"type": "array", "subType": {"type": "string"}, "reducers": []}, ("list", "str", None)),
        ({"type": "array", "subType": {"type": "double"}, "reducers": [{"direction": "DESCENDING_NULLS_LAST"}]},
         ("list", "float",
          '{"reducers":[{"direction":"DESCENDING_NULLS_LAST"}],"subType":{"type":"double"},"type":"array"}')),
        ({"type": "array", "subType": {"type": "long"}, "reducers": []},
         ("list", "int", '{"reducers":[],"subType":{"type":"long"},"type":"array"}')),
        ({"type": "array", "subType": {"type": "geopoint"}, "reducers": []},
         ("list", "opaque", '{"reducers":[],"subType":{"type":"geopoint"},"type":"array"}')),
        ({"type": "array", "subType": {"type": "array", "subType": {"type": "string"}}},
         ("list", "opaque", '{"subType":{"subType":{"type":"string"},"type":"array"},"type":"array"}')),
        ({"type": "struct", "structFieldTypes": [{"apiName": "a", "dataType": {"type": "string"}, "rid": None}],
          "mainValue": None},
         ("dict", None, '{"structFieldTypes":[{"apiName":"a","dataType":{"type":"string"}}],"type":"struct"}')),
        ({"type": "vector", "dimension": 3, "embeddingModel": None}, ("opaque", None, '{"dimension":3,"type":"vector"}')),
        *[({"type": t}, ("opaque", None, t)) for t in (
            "geopoint", "geoshape", "attachment", "mediaReference", "timeseries",
            "geotimeSeriesReference", "vector", "cipherText", "marking")],
        ({"type": "notYetPublished", "x": 1}, ("opaque", None, '{"type":"notYetPublished","x":1}')),
        # Round 4: not a type object, or a type that is not a str, keeps its wire form.
        (None, ("opaque", None, "{}")),
        ("string", ("opaque", None, '"string"')),
        (["string"], ("opaque", None, '["string"]')),
        ({"type": ["string"]}, ("opaque", None, '{"type":["string"]}')),
        ({"type": "array", "subType": {"type": {"k": 1}}}, ("list", "opaque", '{"subType":{"type":{"k":1}},"type":"array"}')),
    ],
)
def test_c12_71_the_type_table_and_the_source_type_wire_form(data_type, expected):
    base, item, source, _ = land(data_type)
    assert (base, item, source) == expected
    slot = {"name": "x", "base_type": base, "description": "d"}
    slot.update({k: v for k, v in (("item_type", item), ("source_type", source)) if v is not None})
    assert declaration_problem("entity", {"properties": [slot]}) is None, "every landing is a legal slot (2.10-6)"
    assert foundry_source_type({"type": "geopoint", "srid": None}) == "geopoint"

async def test_c12_72_an_undescribed_property_is_written_with_no_description_and_no_warning(registry, adapter):
    """Rule 2.10-21 as today, measured: `reserved: Q106`. Not filled, not warned."""
    doc = foundry_fixture("faux_legacy")
    dry = await registry.import_foundry(doc)
    assert sum(e["undescribed"] for e in dry.properties["entities"].values()) == 60
    report = await registry.import_foundry(doc, dry_run=False)
    assert report.count(outcome="refused") == 0
    for item in _items(report, kind="entity", outcome="written"):
        assert not [w for w in item.warnings if w.startswith("property_reference")], item.warnings
    blank = _slots(doc, "Employee")["properties"]
    source = doc["objectTypes"]["Employee"]["objectType"]["properties"]
    for slot in blank:
        if "shared" in slot:
            continue
        said = (source[slot["name"]].get("description") or "").strip()
        assert ("description" in slot) == bool(said)
    if await _stores(adapter, "properties"):
        office = await adapter.get_type("default", "office", kind="entity")
        assert any("description" not in s for s in office.attributes["properties"])

async def test_c12_73_the_narrowed_carry_keeps_only_what_has_no_field(registry, adapter):
    doc = foundry_fixture("faux_legacy")
    source = doc["objectTypes"]["Employee"]["objectType"]["properties"]
    attributes = _slots(doc, "Employee")
    carry = attributes["foundry_properties"]
    assert carry["validated"] is False and set(carry) == {"validated", "properties"}
    for name, prop in source.items():
        slot = next(s for s in attributes["properties"] if s["name"] == name)
        mapped = {"displayName"} if "shared" in slot else {"dataType", "description", "displayName"}
        assert carry["properties"].get(name, {}) == {k: v for k, v in prop.items() if k not in mapped}, name
    assert carry["properties"]["fullName"]["dataType"] == {"type": "string"}, "a shared slot's own type is kept"
    await registry.import_foundry(doc, dry_run=False)
    if await _stores(adapter, "foundry_properties"):
        stored = (await adapter.get_type("default", "employee", kind="entity")).attributes["foundry_properties"]
        assert stored == carry

async def test_c12_74_every_fixture_property_is_a_slot_or_has_a_reason(registry):
    seen = slots = shared = undescribed = 0
    for i, name in enumerate(FIXTURES):
        report = await registry.import_foundry(foundry_fixture(name), namespace=f"c12_74_{i}")
        props = report.properties
        invalid = sum(1 for n in props["no_home"] if n["reason"] == "slot_name_invalid")
        assert props["seen"] == props["slots"] + invalid, name
        for entry in props["no_home"]:
            assert entry["reason"].split(":", 1)[0] in NO_HOME_REASONS, entry
        seen += props["seen"]
        slots += props["slots"]
        shared += sum(e["shared"] for e in props["entities"].values())
        undescribed += sum(e["undescribed"] for e in props["entities"].values())
    assert (seen, slots, shared, undescribed) == (110, 110, 2, 81)

    legacy = (await registry.import_foundry(foundry_fixture("faux_legacy"), namespace="c12_74_x")).properties
    assert {e["name"] for e in legacy["entities"].values() if e["held"] == "definition_missing"} == {
        "bgao_nfl_player", "equipment", "person", "task", "todo",
    }
    reasons = {(n["type"], n["property"], n["reason"]) for n in legacy["no_home"]}
    assert ("Employee", None, "implements_interfaces2") in reasons
    assert ("Employee", "bonusHistory", "struct_fields") in reasons
    assert ("Employee", "performanceScores", "array_reducers") in reasons
    assert ("Employee", "fullName", "no_slot_field:dataType") in reasons
    assert any(r == "interface_property_contract" and t == "FooInterface" for t, _, r in reasons)

    odd = {"objectTypes": {"Thing": {"objectType": {
        "apiName": "Thing", "description": "a thing", "primaryKey": "bad-key",
        "properties": {"bad-key": {"dataType": {"type": "string"}}, "ok": {"dataType": {"type": "string"}}},
    }}}}
    report = await registry.import_foundry(odd, namespace="c12_74_odd")
    assert report.properties["seen"] == 2 and report.properties["slots"] == 1
    assert {n["reason"] for n in report.properties["no_home"]} == {"slot_name_invalid", "no_slot_field:primaryKey"}
    attributes = _slots(odd, "Thing")
    assert "primary_key" not in attributes and attributes["foundry_properties"]["properties"]["bad-key"]
    assert declaration_problem("entity", attributes) is None

async def test_c12_74_a_document_of_shared_property_types_alone_imports(registry):
    """Round 2: lens B finding 2 (a document holding only sharedPropertyTypes is one)
    and lens C finding 3 (a shared property type's facts with no field are in no_home)."""
    spt = dict(foundry_fixture("faux_legacy")["sharedPropertyTypes"]["fooSpt"])
    spt["valueTypeApiName"] = "some_value_type"
    report = await registry.import_foundry({"sharedPropertyTypes": {"fooSpt": spt}}, namespace="c12_74_2")
    assert _names(report, kind="property") == ["foo_spt"]
    assert {"type": "fooSpt", "property": None, "reason": "no_slot_field:valueTypeApiName"} in report.properties["no_home"]

async def test_c12_75_palantirs_dangling_mapping_is_written_and_warned(registry, adapter):
    """`employee` maps `fooSpt` onto `fullName` and never defines `fooSpt`."""
    report = await registry.import_foundry(foundry_fixture("faux_employee"), dry_run=False)
    employee = _items(report, kind="entity", name="employee")[0]
    assert employee.outcome == "written"
    assert "property_reference_unregistered:fullName:foo_spt" in employee.warnings
    assert report.properties["entities"]["Employee"]["unresolved_shared"] == [
        {"shared": "foo_spt", "why": "not_in_document"}
    ]
    legacy = await registry.import_foundry(foundry_fixture("faux_legacy"), dry_run=False, namespace="c12_75")
    item = _items(legacy, kind="entity", name="employee")[0]
    assert not [w for w in item.warnings if w.startswith("property_reference")]
    assert legacy.properties["entities"]["Employee"]["unresolved_shared"] == []

async def test_c12_74_no_shape_of_a_property_key_or_title_is_lost(registry):
    """Round 4 (lens A 2 and 3, lens C 4 and 6): a property that is not an object lands
    opaque with its wire form, a key or title of any shape is carried, a shared property
    type's status is its lifecycle and not no_home, and a properties list is refused."""
    doc = {
        "objectTypes": {"Thing": {"objectType": {
            "apiName": "Thing", "description": "t", "primaryKey": 5, "titleProperty": ["x"],
            "properties": {"x": ["oops"], "y": {"dataType": {"type": "string"}, "description": "d"}},
        }}},
        "sharedPropertyTypes": {"aSpt": {
            "apiName": "aSpt", "description": "a", "dataType": {"type": "string"}, "status": "ACTIVE",
        }},
    }
    report = await registry.import_foundry(doc, namespace="c12_74_3")
    thing = _items(report, kind="entity", name="thing")[0]
    assert thing.outcome == "would_write", thing
    no_home = report.properties["no_home"]
    assert {"type": "Thing", "property": None, "reason": "no_slot_field:primaryKey"} in no_home
    assert {"type": "Thing", "property": None, "reason": "no_slot_field:titleProperty"} in no_home
    assert not [e for e in no_home if e["type"] == "aSpt"], no_home
    assert land(["oops"]) == ("opaque", None, '["oops"]', [])
    bad = {"objectTypes": {"Thing": {"objectType": {"apiName": "Thing", "description": "t", "properties": ["x"]}}}}
    with pytest.raises(TypeError, match="Thing"):
        await registry.import_foundry(bad, namespace="c12_74_3")

async def test_c12_76_no_fixture_breaches_a_declaration_rule_on_any_backend(registry, adapter):
    for i, name in enumerate(FIXTURES):
        report = await registry.import_foundry(foundry_fixture(name), dry_run=False, namespace=f"c12_76_{i}")
        assert report.count(outcome="refused") == 0, (name, [(x.name, x.reason) for x in _items(report, outcome="refused")])
        for entry in report.entries:
            assert "import_refused:attributes_schema_violation" not in entry.warnings
    cms = await registry.import_foundry(foundry_fixture("uc2_cms"), namespace="c12_76_2")
    assert _names(cms, kind="entity") == sorted(e["name"] for e in cms.properties["entities"].values())
    for item in _items(cms, kind="entity"):
        stored = await adapter.get_type("c12_76_2", item.name, kind="entity")
        assert stored is not None
        if await _stores(adapter, "primary_key"):
            assert entity_declaration(stored, await adapter.capabilities()).primary_key is not None

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c12_75_a_shared_slot_reaching_a_live_property_is_resolved(registry):
    """Round 2, lens C MAJOR 1: unresolved_shared asks rule 2.10-11's reader, so a word
    answering to a live property by alias or by successor is resolved, exactly as the
    entity's own warning says redirected."""
    doc = foundry_fixture("faux_employee")

    def row(name, **kw):
        return {"name": name, "definition": f"the {name}", "status": "active",
                "attributes": {"base_type": "str"}, **kw}

    await registry.import_types([row("person_name", aliases=["foo_spt"])], kind="property",
                          system="c12", namespace="c12_75_a", imported_by="import:c12")
    await registry.import_types([row("foo_spt"), row("person_name")], kind="property",
                          system="c12", namespace="c12_75_s", imported_by="import:c12")
    await registry.retire("foo_spt", "renamed", retired_by="user:sd", successor="person_name",
                    force=True, namespace="c12_75_s")
    for namespace in ("c12_75_a", "c12_75_s"):
        report = await registry.import_foundry(doc, dry_run=False, namespace=namespace)
        employee = _items(report, kind="entity", name="employee")[0]
        assert "property_reference_redirected:fullName:foo_spt:person_name" in employee.warnings
        assert report.properties["entities"]["Employee"]["unresolved_shared"] == [], namespace

async def test_c12_75_a_deprecated_shared_property_type_reads_retired_dry_and_real(registry):
    """Round 3, lens B finding 1: a dry run reports what the real run will, and a
    blank displayName lands nowhere (lens C finding 2)."""
    import copy

    doc = copy.deepcopy(foundry_fixture("faux_legacy"))
    doc["sharedPropertyTypes"]["fooSpt"]["status"] = "DEPRECATED"
    doc["sharedPropertyTypes"]["fooSpt"]["displayName"] = "   "
    dry = await registry.import_foundry(doc, namespace="c12_75_d")
    real = await registry.import_foundry(doc, dry_run=False, namespace="c12_75_d")
    for report in (dry, real):
        assert report.properties["entities"]["Employee"]["unresolved_shared"] == [
            {"shared": "foo_spt", "why": "retired"}
        ]
    stored = await registry.adapter.get_type("c12_75_d", "foo_spt", kind="property")
    assert stored.status == "retired"
    if await _stores(registry.adapter, "display_name"):
        assert "display_name" not in (stored.attributes or {})

async def test_c12_77_two_shared_property_types_converting_to_one_word_are_both_held(registry, adapter):
    """K6 in 8C-RUN.md 0.7, pinned (round 1, lens B finding 2): ruling R110 holds
    every member of a collision for kind="property" as for every other kind, nothing
    of that kind is written, and the slot that names the word says why it is unresolved."""
    import copy

    doc = copy.deepcopy(foundry_fixture("faux_legacy"))
    twin = dict(doc["sharedPropertyTypes"]["fooSpt"], apiName="foo_spt", rid="ri.spt.twin")
    doc["sharedPropertyTypes"]["foo_spt"] = twin
    report = await registry.import_foundry(doc, dry_run=False, namespace="c12_77")
    held = _items(report, kind="property")
    assert sorted(i.api_name for i in held) == ["fooSpt", "foo_spt"]
    assert {(i.outcome, i.reason) for i in held} == {("held", "name_collision_after_conversion")}
    assert await adapter.get_type("c12_77", "foo_spt", kind="property") is None
    assert report.properties["entities"]["Employee"]["unresolved_shared"] == [
        {"shared": "foo_spt", "why": "held:name_collision_after_conversion"}
    ]
    employee = _items(report, kind="entity", name="employee")[0]
    assert "property_reference_unregistered:fullName:foo_spt" in employee.warnings

D14_KINDS = ("entity", "edge", "property", "value_set", "action")

def _d14_attributes(kind):
    return {"base_type": "str"} if kind == "property" else None

async def _d14_store(registry, kind, namespace):
    attributes = _d14_attributes(kind)
    await seed(registry, "zip_code", kind=kind, attributes=attributes, namespace=namespace)
    await seed(registry, "postal_code", kind=kind, attributes=attributes, namespace=namespace)
    retired = await registry.retire("zip_code", "duplicate", retired_by="user:sd",
                              successor="postal_code", namespace=namespace)
    assert isinstance(retired, TypeEntry) and retired.status == "retired", retired
    return attributes

def _d14_row(name, kind, attributes, *, status="active", aliases=("zip_code",)):
    row = {"name": name, "definition": f"the {name}", "status": status,
           "aliases": list(aliases)}
    if attributes is not None:
        row["attributes"] = attributes
    return row

@pytest.mark.requires_capability("indexes_membership", "stores_aliases")
@pytest.mark.parametrize("kind", D14_KINDS)
async def test_c12_78_an_alias_over_a_tombstone_with_a_live_successor_is_warned(registry, kind):
    """Row 8d, D14 (8B-RUN.md 2.5 finding 10, probe line D14). An import writing a
    retired row's NAME as an alias, while that row's successor is live, leaves the word
    with two live claimants. Warned `alias_word_succeeded:<word>:<successor>`.

    **The default in force is pinned beside the warning** (DECISIONS-OPEN item 35): the
    alias is written, the reader answers the successor, and the tombstone cannot be
    reinstated while the successor lives. Refusing the write, or answering the alias
    holder, is the founder's."""
    namespace = f"c12_78_{kind}"
    attributes = await _d14_store(registry, kind, namespace)
    entry = (await registry.import_types([_d14_row("post_code", kind, attributes)], kind=kind,
                                  namespace=namespace))[0]
    assert entry.status == "active" and "zip_code" in entry.aliases, entry
    assert "alias_word_succeeded:zip_code:postal_code" in entry.warnings, entry.warnings
    found = await registry.resolve_type("zip_code", ResolveContext(source="c12_78"), kind=kind,
                                  namespace=namespace, tier="opus")
    assert found.outcome == "existing" and found.type.name == "postal_code", found
    back = await registry.reinstate("zip_code", "bring it back", reinstated_by="user:sd",
                              namespace=namespace)
    assert isinstance(back, Refusal) and back.reason == "successor_active", back

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_78_one_claimant_is_not_warned(registry):
    """D14's negatives: the successor itself taking the word, a dead-end chain, and a
    tombstone with no successor (C12-09's succession) each leave one live claimant."""
    namespace = "c12_78_one"
    await _d14_store(registry, "entity", namespace)
    own = (await registry.import_types([_d14_row("postal_code", "entity", None)],
                                namespace=namespace))[0]
    assert not [w for w in own.warnings if w.startswith("alias_word_succeeded")], own.warnings
    await seed(registry, "lone", namespace=namespace)
    await registry.retire("lone", "gone", retired_by="user:sd", namespace=namespace)
    plain = (await registry.import_types([_d14_row("solo", "entity", None, aliases=("lone",))],
                                  namespace=namespace))[0]
    assert plain.status == "active", plain
    assert not [w for w in plain.warnings if w.startswith("alias_word_succeeded")]

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c12_78_a_chain_is_walked_to_its_live_end(registry):
    """The walk is the reader's: `a -> b -> c` with `c` live warns `c`, and a chain whose
    end is retired is one claimant (8B-RUN.md 2.5 finding 2's dead end).
    stores_events: the second hop retires a successor, which needs a forced retire."""
    namespace = "c12_78_chain"
    for name in ("a_word", "b_word", "c_word"):
        await seed(registry, name, namespace=namespace)
    await registry.retire("a_word", "dup", retired_by="user:sd", successor="b_word",
                    namespace=namespace)
    await registry.retire("b_word", "dup", retired_by="user:sd", successor="c_word",
                    namespace=namespace, force=True)
    entry = (await registry.import_types([_d14_row("d_word", "entity", None, aliases=("a_word",))],
                                  namespace=namespace))[0]
    assert "alias_word_succeeded:a_word:c_word" in entry.warnings, entry.warnings
    await registry.retire("c_word", "gone", retired_by="user:sd", namespace=namespace, force=True)
    again = (await registry.import_types([_d14_row("e_word", "entity", None, aliases=("b_word",))],
                                  namespace=namespace))[0]
    assert not [w for w in again.warnings if w.startswith("alias_word_succeeded")], again.warnings

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c12_79_reinstating_the_live_end_of_a_chain_is_warned(registry):
    """Row 8d round 1 (door lens, MAJOR 1). A chain whose end is retired is one claimant,
    so an alias over its first word is written unwarned. Reinstating that end makes the
    reader answer it again while the alias holder still answers the word: D14's state,
    reached by a third door, warned there. stores_events: forced retire and reinstate."""
    namespace = "c12_79_end"
    for name in ("a_word", "b_word", "c_word"):
        await seed(registry, name, namespace=namespace)
    await registry.retire("a_word", "dup", retired_by="user:sd", successor="b_word",
                    namespace=namespace)
    await registry.retire("b_word", "dup", retired_by="user:sd", successor="c_word",
                    namespace=namespace, force=True)
    await registry.retire("c_word", "gone", retired_by="user:sd", namespace=namespace, force=True)
    entry = (await registry.import_types([_d14_row("e_word", "entity", None, aliases=("a_word",))],
                                  namespace=namespace))[0]
    assert not [w for w in entry.warnings if w.startswith("alias_word_succeeded")], entry.warnings
    back = await registry.reinstate("c_word", "we were wrong", reinstated_by="user:sd",
                              namespace=namespace)
    assert back.status == "active", back
    assert "alias_word_succeeded:a_word:c_word" in back.warnings, back.warnings
    assert (await registry.resolve_type("a_word", ResolveContext(), kind="entity", namespace=namespace,
                                 tier="unspecified")).type.name == "c_word"

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c12_79_merging_a_chains_retired_end_into_a_live_row_is_warned(registry):
    """Row 8d round 2 (door lens, MAJOR 1). `merge_types` with a retired `from_` points
    the dead end of a chain at a live row, which the reader then answers for the chain's
    first word while another live row holds that word as an alias: D14's state through a
    fourth door, warned on the `MergeResult`. stores_events: forced retires."""
    namespace = "c12_79_merge"
    for name in ("alpha", "beta", "delta"):
        await seed(registry, name, namespace=namespace)
    await registry.retire("alpha", "dup", retired_by="user:sd", successor="beta",
                    namespace=namespace, force=True)
    await registry.retire("beta", "gone", retired_by="user:sd", namespace=namespace, force=True)
    entry = (await registry.import_types([_d14_row("carrier", "entity", None, aliases=("alpha",))],
                                  namespace=namespace))[0]
    assert not [w for w in entry.warnings if w.startswith("alias_word_succeeded")], entry.warnings
    merged = await registry.merge_types(
        "beta", "delta", "m", merged_by="user:sd", namespace=namespace,
        acknowledge=["retired_operand", "definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    assert "alias_word_succeeded:alpha:delta" in merged.warnings, merged.warnings
    assert (await registry.resolve_type("alpha", ResolveContext(), kind="entity", namespace=namespace,
                                 tier="unspecified")).type.name == "delta"

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c12_79_merging_a_dead_end_into_a_retired_row_whose_chain_ends_live_is_warned(registry):
    """Row 8d round 3 (implementer lens, MAJOR 1). The fourth door, when `into` is itself
    retired with a live successor: the dead end now walks through `into` to that row, so
    the claimant to name is the chain's new live end, not `into`."""
    namespace = "c12_79_merge2"
    for name in ("alpha", "beta", "gamma", "delta"):
        await seed(registry, name, namespace=namespace)
    await registry.retire("alpha", "dup", retired_by="user:sd", successor="beta",
                    namespace=namespace, force=True)
    await registry.retire("beta", "gone", retired_by="user:sd", namespace=namespace, force=True)
    await registry.retire("gamma", "dup", retired_by="user:sd", successor="delta",
                    namespace=namespace, force=True)
    await registry.import_types([_d14_row("carrier", "entity", None, aliases=("alpha",))],
                          namespace=namespace)
    merged = await registry.merge_types(
        "beta", "gamma", "m", merged_by="user:sd", namespace=namespace,
        acknowledge=["retired_operand", "definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    assert (await registry.resolve_type("alpha", ResolveContext(), kind="entity", namespace=namespace,
                                 tier="unspecified")).type.name == "delta"
    assert "alias_word_succeeded:alpha:delta" in merged.warnings, merged.warnings

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
@pytest.mark.parametrize("kind", D14_KINDS)
async def test_c12_79_merging_a_retired_rows_dormant_alias_into_a_live_row_is_warned(registry, kind):
    """Row 8d round 3 (door lens, MAJOR 1). A retired row's aliases are dormant, so the
    import that wrote them did not warn. `merge_types` moves them onto a live `into`, which
    makes them live: D14's state through a fifth door, warned on the `MergeResult`."""
    namespace = f"c12_79_dorm_{kind}"
    attributes = await _d14_store(registry, kind, namespace)
    await registry.import_types([_d14_row("rr", kind, attributes, aliases=())], kind=kind,
                          namespace=namespace)
    entry = (await registry.import_types([_d14_row("carrier", kind, attributes, status="deprecated")],
                                  kind=kind, namespace=namespace))[0]
    assert entry.status == "retired", entry
    assert not [w for w in entry.warnings if w.startswith("alias_word_succeeded")], entry.warnings
    merged = await registry.merge_types(
        "carrier", "rr", "m", merged_by="user:sd", namespace=namespace,
        acknowledge=["retired_operand", "definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    assert "alias_word_succeeded:zip_code:postal_code" in merged.warnings, merged.warnings

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c12_78_the_walk_reaches_as_far_as_the_reader(registry):
    """Row 8d round 1 (implementer lens, MINOR 3). The reader takes the first hop and up to
    `_IDENTITY_CHAIN_CAP` more; the warning's walk takes the same, so a chain the reader
    finishes is never warned `?` (could not finish)."""
    from ontoloche.registry import _IDENTITY_CHAIN_CAP

    namespace = "c12_78_cap"
    names = [f"w{i:02d}" for i in range(_IDENTITY_CHAIN_CAP + 2)]
    for name in names:
        await seed(registry, name, namespace=namespace)
    for here, there in zip(names, names[1:]):
        await registry.retire(here, "dup", retired_by="user:sd", successor=there,
                        namespace=namespace, force=True)
    assert (await registry.resolve_type(names[0], ResolveContext(), kind="entity", namespace=namespace,
                                 tier="unspecified")).type.name == names[-1]
    entry = (await registry.import_types([_d14_row("holder", "entity", None, aliases=(names[0],))],
                                  namespace=namespace))[0]
    assert f"alias_word_succeeded:{names[0]}:{names[-1]}" in entry.warnings, entry.warnings

@pytest.mark.requires_capability("indexes_membership")
async def test_c12_78_an_alias_the_backend_does_not_keep_is_not_warned(adapter, make_registry):
    """Row 8d round 0 (the capability matrix, 8D-RUN.md 1.6): on `stores_aliases=False`
    the alias is never stored, so no second claimant exists and the warning would state a
    false fact (Rule U)."""
    registry = await make_registry(AsyncDegradedAdapter(adapter, stores_aliases=False))
    await _d14_store(registry, "entity", "c12_78_na")
    entry = (await registry.import_types([_d14_row("post_code", "entity", None)],
                                  namespace="c12_78_na"))[0]
    assert entry.aliases == (), entry
    assert not [w for w in entry.warnings if w.startswith("alias_word_succeeded")], entry.warnings

async def test_c12_78_without_a_membership_index_no_successor_can_be_named(registry):
    """D14 on the third backend: with `indexes_membership=False` the retire that would
    build the tombstone is refused `no_consumer_evidence` (overridable only by a forced
    retire, which needs `stores_events`), so the two-claimant state cannot arise there.
    On a backend that indexes membership the same retire succeeds."""
    await seed(registry, "zip_code", namespace="c12_78_m")
    await seed(registry, "postal_code", namespace="c12_78_m")
    out = await registry.retire("zip_code", "duplicate", retired_by="user:sd",
                          successor="postal_code", namespace="c12_78_m")
    if registry.caps.indexes_membership:
        assert isinstance(out, TypeEntry) and out.status == "retired", out
    else:
        assert isinstance(out, Refusal) and out.reason == "no_consumer_evidence", out

async def test_c12_78_the_predicate_version_is_refused_at_retire(registry):
    """D14 does not reach the kill row: a predicate cannot be retired into a successor."""
    await seed(registry, "zip_code", kind="predicate", namespace="c12_78_p")
    await seed(registry, "postal_code", kind="predicate", namespace="c12_78_p")
    out = await registry.retire("zip_code", "duplicate", retired_by="user:sd",
                          successor="postal_code", namespace="c12_78_p")
    assert isinstance(out, Refusal) and out.reason == "predicate_merge", out

@pytest.mark.requires_capability("indexes_membership", "stores_aliases", "stores_events")
@pytest.mark.parametrize("kind", D14_KINDS)
async def test_c12_79_reinstating_an_alias_over_a_tombstone_with_a_live_successor_is_warned(
    registry, kind
):
    """Row 8d, D14's second door (8D-RUN.md 0.1 item 4): a `deprecated` import carries the
    word as an alias while retired, and `reinstate` makes it live beside the successor.
    Warned on the reinstated entry. Default in force: it is reinstated."""
    namespace = f"c12_79_{kind}"
    attributes = await _d14_store(registry, kind, namespace)
    stored = (await registry.import_types(
        [_d14_row("post_code", kind, attributes, status="deprecated")], kind=kind,
        namespace=namespace,
    ))[0]
    assert stored.status == "retired", stored
    # A retired row is not a claimant yet, so the import does not warn it.
    assert not [w for w in stored.warnings if w.startswith("alias_word_succeeded")], stored.warnings
    back = await registry.reinstate("post_code", "in use again", reinstated_by="user:sd",
                              namespace=namespace)
    assert isinstance(back, TypeEntry) and back.status == "active", back
    assert "alias_word_succeeded:zip_code:postal_code" in back.warnings, back.warnings

def _b5_shared_twin():
    """`faux_employee` (whose Employee maps the absent `fooSpt` onto `fullName`) plus a
    shared property type `FooSpt`, which converts to the same word `foo_spt`."""
    import copy

    doc = copy.deepcopy(foundry_fixture("faux_employee"))
    twin = dict(foundry_fixture("faux_legacy")["sharedPropertyTypes"]["fooSpt"],
                apiName="FooSpt", rid="ri.spt.FooSpt")
    doc.setdefault("sharedPropertyTypes", {})["FooSpt"] = twin
    return doc

def _b5_interface_twin():
    """The interface case: the document defines `fooInterface` and Employee still
    implements the absent `FooInterface`. Both convert to `foo_interface`."""
    import copy

    doc = copy.deepcopy(foundry_fixture("faux_employee"))
    iface = doc["interfaceTypes"].pop("FooInterface")
    doc["interfaceTypes"]["fooInterface"] = dict(iface, apiName="fooInterface")
    return doc

def _b5_endpoint_twin():
    """The link case: a new Employee side points at the absent object type `office`,
    which converts to the same word as the defined `Office`."""
    import copy

    doc = copy.deepcopy(foundry_fixture("faux_employee"))
    doc["objectTypes"]["Employee"]["linkTypes"].append({
        "apiName": "homeOffice", "status": "ACTIVE", "objectTypeApiName": "office",
        "cardinality": "ONE", "displayName": "Home office", "linkTypeRid": "rid.link-type.b5",
        "foreignKeyPropertyApiName": "homeOffice",
    })
    return doc

@pytest.mark.parametrize("case,kind,api_name,expected", [
    ("shared", "entity", "Employee", ("shared", "foo_spt", "fooSpt", "FooSpt")),
    ("interface", "entity", "Employee", ("predicate", "foo_interface", "FooInterface", "fooInterface")),
    ("endpoint", "edge", "homeOffice", ("dst", "office", "office", "Office")),
])
async def test_c12_80_a_reference_bound_to_a_converting_twin_is_reported_dry_and_real(
    registry, case, kind, api_name, expected
):
    """Row 8d, B5-1 and B5-2 (8C-RUN.md 2.5). A reference to an apiName the document does
    not define, while another apiName it does define converts to the same word, is bound
    to that other row by the real run. It is reported on the plan and the result alike:
    `reference_bound_by_conversion:<label>:<absent>:<twin>` on the item and
    `bound_by_conversion` in its detail, and the dry run no longer says `not_in_document`
    for what the real run resolves. Default in force: report, never hold (item 36)."""
    label, word, absent, twin = expected
    doc = {"shared": _b5_shared_twin, "interface": _b5_interface_twin,
           "endpoint": _b5_endpoint_twin}[case]()
    namespace = f"c12_80_{case}"
    seen = {}
    for dry in (True, False):
        report = await registry.import_foundry(doc, dry_run=dry, namespace=namespace)
        item = [i for i in report.items if i.kind == kind and i.api_name == api_name][0]
        warning = f"reference_bound_by_conversion:{label}:{absent}:{twin}"
        assert warning in item.warnings, (dry, item.warnings)
        assert item.detail.get("bound_by_conversion") == [
            {label: word, "api": absent, "bound_to": twin}
        ], (dry, item.detail)
        assert not [u for u in item.detail.get("unresolved", ()) if u.get(label) == word], (
            dry, item.detail.get("unresolved"))
        seen[dry] = (item.detail.get("unresolved"), item.detail.get("bound_by_conversion"),
                     report.properties["entities"]["Employee"]["unresolved_shared"])
    assert seen[True] == seen[False], seen

async def test_c12_80_a_held_twin_binds_nothing(registry):
    """B5's negative: a twin the planner holds (here `definition_missing`) binds nothing,
    so the reference reads `held:<reason>` on both runs and nothing is reported bound."""
    doc = _b5_shared_twin()
    doc["sharedPropertyTypes"]["FooSpt"].pop("description", None)
    for dry in (True, False):
        report = await registry.import_foundry(doc, dry_run=dry, namespace="c12_80_h")
        employee = [i for i in report.items if i.kind == "entity" and i.name == "employee"][0]
        assert "bound_by_conversion" not in employee.detail, employee.detail
        assert report.properties["entities"]["Employee"]["unresolved_shared"] == [
            {"shared": "foo_spt", "why": "held:definition_missing"}
        ], (dry, report.properties["entities"]["Employee"]["unresolved_shared"])

async def test_c12_80_a_twin_that_is_not_live_binds_nothing(registry):
    """Row 8d round 1 (implementer lens, MAJOR 1 and MINOR 2). A twin the import writes
    retired (DEPRECATED in the document) or that the real run refuses leaves nothing for
    the reference to bind to, so the item carries no `reference_bound_by_conversion` and
    the reference reads unresolved. A refusal is known only on the real run, so the dry run
    may still report the binding there (8D-RUN.md 0.3 item 1)."""
    import copy

    deprecated = _b5_endpoint_twin()
    deprecated["objectTypes"]["Office"]["objectType"]["status"] = "DEPRECATED"
    for dry in (True, False):
        report = await registry.import_foundry(deprecated, dry_run=dry, namespace="c12_80_dep")
        side = [i for i in report.items if i.api_name == "homeOffice"][0]
        assert not [w for w in side.warnings if w.startswith("reference_bound")], (dry, side)
        assert "bound_by_conversion" not in side.detail, (dry, side.detail)
        assert {"dst": "office", "why": "retired"} in side.detail.get("unresolved", []), (dry, side.detail)

@pytest.mark.requires_capability("stores_events")
async def test_c12_80_a_twin_the_real_run_refuses_binds_nothing(registry):
    """Round 1 and round 2 (implementer lens). A twin the real run refuses was never
    written, so nothing is bound to it, on the entity path and the shared-property path.
    stores_events: each store is built with a forced retire."""
    namespace = "c12_80_ref"
    await registry.import_types([{"name": "bureau", "definition": "a bureau", "status": "active",
                            "aliases": ["office"]}], namespace=namespace)
    await registry.retire("bureau", "gone", retired_by="user:sd", namespace=namespace, force=True)
    report = await registry.import_foundry(_b5_endpoint_twin(), dry_run=False, namespace=namespace)
    office = [i for i in report.items if i.api_name == "Office"][0]
    assert office.outcome == "refused", office
    side = [i for i in report.items if i.api_name == "homeOffice"][0]
    assert not [w for w in side.warnings if w.startswith("reference_bound")], side
    assert "bound_by_conversion" not in side.detail, side.detail
    assert [u for u in side.detail.get("unresolved", []) if u.get("dst") == "office"], side.detail

    # Round 2 (implementer lens, MAJOR 1): the shared-property path. The reader redirects
    # the slot down a property tombstone's chain, so it never reads unresolved, and the
    # refused twin was still reported bound beside `property_reference_redirected`.
    namespace = "c12_80_spt"
    await registry.import_types([{"name": "foo_spt", "definition": "a foo", "status": "active"},
                           {"name": "bar_prop", "definition": "a bar", "status": "active"}],
                          namespace=namespace, kind="property")
    await registry.retire("foo_spt", "gone", retired_by="user:sd", namespace=namespace,
                    successor="bar_prop", force=True)
    report = await registry.import_foundry(_b5_shared_twin(), dry_run=False, namespace=namespace)
    assert [i for i in report.items if i.api_name == "FooSpt"][0].outcome == "refused"
    employee = [i for i in report.items if i.api_name == "Employee"][0]
    assert not [w for w in employee.warnings if w.startswith("reference_bound")], employee.warnings
    assert "bound_by_conversion" not in employee.detail, employee.detail

async def test_c12_81_two_shared_property_types_on_one_property_list_the_word_once(registry):
    """Row 8d, 8C-RUN.md 2.5 C5-4: two shared property types mapped onto one property
    leave one slot naming one word, so an unresolved word is listed once, on both runs."""
    import copy

    doc = copy.deepcopy(foundry_fixture("faux_employee"))
    doc["objectTypes"]["Employee"]["sharedPropertyTypeMapping"]["barSpt"] = "fullName"
    for dry in (True, False):
        report = await registry.import_foundry(doc, dry_run=dry, namespace="c12_81")
        unresolved = report.properties["entities"]["Employee"]["unresolved_shared"]
        assert len(unresolved) == len({tuple(sorted(u.items())) for u in unresolved}), (dry, unresolved)
        assert len(unresolved) == 1, (dry, unresolved)
