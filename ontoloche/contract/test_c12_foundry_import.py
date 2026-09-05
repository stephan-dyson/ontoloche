"""C12 -- the Foundry import mapping, and the fourth door into the kill row (13). From 0.3 consequence 2 / INTERFACE.md 2.5.

The mapping is stated in the interface rather than left to an importer, so it is tested
here. It lands on ``Registry.import_types``, a method beyond the twelve, because no 5.x
call performs it -- deviation D-8 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations

import pytest

from ..types import Consumer, Evidence, Refusal, ResolveContext, TypeEntry
from ._support import seed
from .doubles import DegradedAdapter

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
def imported(registry):
    registry.import_types(FOUNDRY_ROWS)
    return registry


@pytest.mark.requires_capability("indexes_membership")
def test_c12_01_experimental_becomes_active_plus_a_predicate_never_proposed(imported):
    """`proposed` here means *no one has approved it*; a Foundry experimental type has
    been approved and is in use. Collapsing them silently un-approves a customer's live
    vocabulary."""
    entry = imported.list_types(include_retired=True, status=None, namespace=None)
    by_name = {t.name: t for t in entry.types}

    assert by_name["gate_assignment"].status == "active"
    assert by_name["gate_assignment"].status != "proposed"
    assert "experimental" in by_name["gate_assignment"].predicates
    assert "experimental" not in by_name["flight"].predicates
    assert [t.name for t in imported.list_types(predicate="experimental").types] == [
        "gate_assignment"
    ]


def test_c12_02_deprecated_becomes_retired_with_the_reason_recorded(imported, adapter):
    rec = adapter.get_type("default", "legacy_slot")
    assert rec.status == "retired"
    assert rec.retire_reason == "imported: foundry deprecated"


def test_c12_03_foreign_identifiers_land_in_provenance_not_in_fields_of_our_own(imported):
    provenance = imported.provenance("flight")
    assert provenance.imported_from == {
        "system": "foundry",
        "apiName": "Flight",
        "rid": "ri.ontology.main.object-type.1",
    }
    entry = [t for t in imported.list_types().types if t.name == "flight"][0]
    assert "apiName" not in entry.attributes
    assert "rid" not in entry.attributes
    assert entry.name == "flight", "our identity is our own name, not theirs"


@pytest.mark.requires_capability("stores_attributes")
def test_c12_04_visibility_and_groups_land_in_attributes(imported):
    entry = [t for t in imported.list_types().types if t.name == "gate_assignment"][0]
    assert entry.attributes["visibility"] == "PROMINENT"
    assert entry.attributes["groups"] == ["ops"]


@pytest.mark.requires_capability("indexes_membership")
def test_c12_05_an_import_does_not_un_retire_a_local_name(registry, adapter):
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
    seed(registry, "cycle_track", definition="A DOT bike facility, current term.")
    seed(registry, "bike_lane", definition="A DOT bike facility, older term.")
    registry.retire(
        "bike_lane", "superseded by cycle_track", retired_by="user:tlc",
        successor="cycle_track",
    )

    imported = registry.import_types(
        [{"name": "bike_lane", "status": "active", "definition": "from the dump"}]
    )
    assert len(imported) == 1
    assert imported[0].status == "retired", "an import does not reverse a retirement"
    assert "name_previously_retired" in imported[0].warnings

    stored = adapter.get_type("default", "bike_lane", kind="entity")
    assert stored is not None and stored.status == "retired"
    assert getattr(stored, "retire_reason", None) == "superseded by cycle_track", (
        "and the tombstone was not overwritten"
    )
    assert sorted(t.name for t in registry.list_types().types) == [
        "cycle_track",
        "equivalent_to",  # seeded at store creation -- EDGES.md 3.1
    ]


@pytest.mark.requires_capability("indexes_membership")
def test_c12_06_an_import_does_not_retire_a_type_something_still_gates_on(registry):
    """**The mirror of `C12-05`, and it was open.** Row 3e, third adversarial round.

    `retire()` refuses `live_consumers` when something still gates on the type
    (`INTERFACE.md` §5.9). A Foundry `deprecated` row did the identical act with **no
    refusal, no warning and no `retired` event** -- so `PACKAGE.md` §3.6's rule that a
    destructive change nobody can audit is refused was bypassed on every backend, and
    `consumers()` went on naming the retired type as gated.
    """
    from ..types import Consumer

    seed(registry, "commentable", kind="predicate", definition="a code path accepts it")
    seed(registry, "billable", predicates=["commentable"], definition="a billable unit")
    registry.register_consumer(
        Consumer(id="billing.charge", gate="commentable", on_unknown="drop")
    )
    assert registry.retire("billable", "no", retired_by="user:sd").reason == "live_consumers"

    out = registry.import_types([{"name": "billable", "status": "deprecated"}])
    assert out[0].status == "active", "the same act through an import is refused too"
    assert "import_refused:live_consumers" in out[0].warnings


def test_c12_07_source_version_survives_the_import(registry):
    """R21 on the ingestion path, which is UC3's actual wedge (`INTERFACE.md` §2.4a).

    A dump has a version, and §10b.5's whole finding is that it had nowhere to go.
    Dropping it from `import_types`' `Provenance` ran the whole suite green until this
    -- row 3e, third adversarial round.
    """
    out = registry.import_types(
        [{"name": "tree_census_record", "status": "active",
          "definition": "one row of the street tree census",
          "source_version": "2017-10-04"}]
    )
    assert out[0].provenance.source_version == "2017-10-04"
    assert registry.provenance("tree_census_record").source_version == "2017-10-04"


def test_c12_08_an_imported_alias_cannot_collapse_two_predicate_identities(registry):
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
    seed(registry, "commentable", kind="predicate", definition="a capability")
    seed(registry, "searchable", kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable"])
    seed(registry, "doc", predicates=["searchable"])
    if not registry.caps.indexes_membership:
        # Rule U makes the answer here the same for a different reason -- an extent that
        # cannot be computed is not an identical extent -- so the assertion below still
        # holds and the fixture's premise does not. Asserted rather than skipped.
        pass

    refused = registry.merge_types(
        "commentable", "searchable", "they look alike", merged_by="user:sd",
        acknowledge=[
            "definitions_diverge", "no_consumer_evidence", "retired_operand",
            "predicate_merge", "kind_mismatch",
        ],
    )
    assert isinstance(refused, Refusal) and refused.reason == "predicate_merge", refused
    assert refused.detail["overridable"] is False

    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement, so the "
            f"fixture's first step is unreachable here: {retired.reason}"
        )

    entry = registry.import_types(
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
    )[0]
    assert "import_refused:predicate_merge" in entry.warnings, (
        "the alias door reaches the same collapse merge_types refuses non-overridably, "
        "and it must be refused there too -- this is the kill row's fourth trip"
    )
    assert "commentable" not in (entry.aliases or ()), "refused, and nothing written"

    resolution = registry.resolve_type(
        "commentable", ResolveContext(), tier="unspecified"
    )
    assert not (
        resolution.outcome == "existing" and resolution.type == "searchable"
    ), (
        "`resolve_type('commentable')` must not answer `searchable` at confidence 1.0 -- "
        "that IS the merge, whichever call wrote the alias"
    )


@pytest.mark.requires_capability("stores_aliases")
def test_c12_09_an_imported_alias_between_identical_extents_is_still_written(registry):
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
    seed(registry, "commentable", kind="predicate", definition="a capability")
    seed(registry, "searchable", kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])

    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement: "
            f"{retired.reason}"
        )

    entry = registry.import_types(
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
    )[0]
    assert not any(w.startswith("import_refused:") for w in entry.warnings), entry.warnings
    assert "commentable" in entry.aliases, (
        "two predicates with non-empty identical extents may be collapsed -- C10-09 "
        "narrowed the guard, and a fix that banned the operation would pass a checker "
        "that only tested refusals"
    )


@pytest.mark.requires_capability("stores_aliases")
def test_c12_10_the_identity_guard_survives_a_word_registered_under_two_kinds(registry):
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
    seed(registry, "facility", definition="a nursing home")
    seed(registry, "facility", kind="value_set", definition="the set of facility codes")
    seed(registry, "surveyed", kind="predicate", definition="a capability")
    seed(registry, "home", predicates=["surveyed"])

    entries = registry.import_types(
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
    ok = registry.import_types(
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
    )[0]
    assert not any(w.startswith("import_refused:") for w in ok.warnings), ok.warnings
    assert ok.aliases == ("previously_annotated",)
    assert ok.kind == "predicate"


@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
def test_c12_11_an_imported_row_declaring_a_moved_predicate_is_warned(
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
    registry = make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable", "untouched"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])
    merged = registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert hasattr(merged, "aliases_added"), merged

    entries = registry.import_types(
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
    listing = registry.list_types(predicate="searchable", namespace="default")
    assert {"note", "memo", "card"} & {t.name for t in listing.types} == {"note", "memo"}


@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
def test_c12_12_an_imported_row_whose_name_is_spoken_for_is_refused(adapter, make_registry):
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
    registry = make_registry(adapter, approval_policy="auto")
    seed(registry, "searchable", kind="predicate", definition="a capability")
    seed(registry, "aaa_note", predicates=["searchable"])
    registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentable"], "status": "active"}],
        namespace="default", kind="predicate",
    )

    # The control: `propose_type` refuses this, and has since row 4c.
    refused = registry.propose_type(
        "commentable", "a capability", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(refused, Refusal) and refused.reason == "alias_collision"

    entry = registry.import_types(
        [{"name": "commentable", "kind": "predicate", "definition": "a capability",
          "status": "active"}],
        namespace="default", kind="predicate",
    )[0]
    assert "import_refused:alias_collision" in entry.warnings, (
        "the sibling write door must give the same answer to the same act"
    )
    live = registry.list_types(namespace="default").types
    holders = [t.name for t in live if t.name == "commentable" or "commentable" in (t.aliases or ())]
    assert holders == ["searchable"], (
        f"two live entries answering to one word is mechanism 4 itself: {holders}"
    )


@pytest.mark.requires_capability("stores_aliases")
def test_c12_13_a_legal_import_is_not_banned_by_a_backend_that_pages(adapter, make_registry):
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
    registry = make_registry(adapter, approval_policy="auto")
    for i in range(6):
        seed(registry, f"row_{i}", definition="a row")

    capped = make_registry(DegradedAdapter(adapter, page_cap=3), approval_policy="auto")
    entry = capped.import_types(
        [{"name": "imported_here", "kind": "entity", "definition": "a row",
          "aliases": ["a_brand_new_word"], "status": "active"}],
        namespace="default", kind="entity",
    )[0]
    assert not any(w.startswith("import_refused:") for w in entry.warnings), (
        f"nothing holds `a_brand_new_word`; refusing this bans the ingestion path on "
        f"every paging backend: {entry.warnings}"
    )
    assert entry.status == "active" and "a_brand_new_word" in (entry.aliases or ())

    # The truncation is REPORTED, exactly once.
    said = [w for w in entry.warnings if w.startswith("alias_check_incomplete:")]
    assert len(said) == 1, f"reported once, not zero and not twice: {entry.warnings}"


@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
def test_c12_14_the_ninth_trip_a_row_that_does_not_exist_yet_has_no_consumers_to_read(
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
    registry = make_registry(adapter)
    registry.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    seed(registry, "meta_p", kind="predicate")
    seed(registry, "commentable", kind="predicate", predicates=["meta_p"])
    for member in ("aaa_note", "bbb_memo"):
        seed(registry, member, predicates=["commentable"])

    # The two extents are non-empty and IDENTICAL, so refusal #2 has nothing to say --
    # which is what makes this a #1 walk rather than another #2 walk.
    assert registry._written_extent("default", "commentable", include_retired=True)[0] == (
        "aaa_note",
        "bbb_memo",
    )
    assert {c.id for c in registry.consumers("commentable").gates_on} == {"svc:meta"}

    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement, so the "
            f"fixture's first step is unreachable here: {retired.reason}"
        )

    entry = registry.import_types(
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
    )[0]
    assert "import_refused:different_consumer_sets" in entry.warnings, entry.warnings
    assert "commentable" not in (entry.aliases or ()), "refused and wrote the alias anyway"

    resolution = registry.resolve_type(
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
    control = make_registry(adapter)
    control.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    seed(control, "meta_p", kind="predicate")
    seed(control, "commentable", kind="predicate", predicates=["meta_p"])
    seed(control, "gamma", kind="predicate")
    for member in ("aaa_note", "bbb_memo"):
        seed(control, member, predicates=["commentable", "gamma"])
    refusal = control.merge_types(
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
def test_c12_15_a_new_row_whose_consumers_agree_is_still_aliased(adapter, make_registry):
    """`C12-14`'s narrowing, and it is the half a careless fix deletes.

    The guard is **narrowed, not banned**: an import that creates a row whose computed
    consumer set MATCHES the word it is aliasing is still written. Every guard fix in this
    repository ships with this assertion beside it -- `C10-09`, `C12-09`, `C10-19`,
    `C4-14` -- because *refusing everything passes a checker that only tests refusals and
    deletes a legal operation*.
    """
    registry = make_registry(adapter)
    registry.register_consumer(
        Consumer(id="svc:c", gate="commentable", on_unknown="drop", owner="ops")
    )
    seed(registry, "commentable", kind="predicate")
    seed(registry, "note", kind="entity", predicates=["commentable"])
    retired = registry.retire("note", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement: "
            f"{retired.reason}"
        )

    entry = registry.import_types(
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
    )[0]
    assert not [w for w in entry.warnings if w.startswith("import_refused:")], entry.warnings
    assert "note" in (entry.aliases or ()), "the legal alias must still be written"


@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
def test_c12_16_the_tenth_trip_the_guard_read_a_state_the_call_destroys(
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
    registry = make_registry(adapter)
    registry.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    seed(registry, "meta_p", kind="predicate")
    seed(registry, "commentable", kind="predicate", predicates=["meta_p"])
    seed(registry, "gamma", kind="predicate", predicates=["meta_p"])
    for member in ("aaa_note", "bbb_memo"):
        seed(registry, member, predicates=["commentable", "gamma"])

    # Both guards pass HONESTLY on the pre-import reading -- that is the whole trap.
    assert registry._written_extent("default", "commentable", include_retired=True)[0] == (
        registry._written_extent("default", "gamma", include_retired=True)[0]
    )
    assert {c.id for c in registry.consumers("commentable").gates_on} == {
        c.id for c in registry.consumers("gamma").gates_on
    } == {"svc:meta"}

    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement, so the "
            f"fixture's first step is unreachable here: {retired.reason}"
        )

    entry = registry.import_types(
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
    )[0]
    assert "import_refused:different_consumer_sets" in entry.warnings, entry.warnings
    assert "commentable" not in (entry.aliases or ())

    resolution = registry.resolve_type(
        "commentable", ResolveContext(source="the C12-16 fixture"), tier="opus"
    )
    assert resolution.outcome != "existing", (
        "the tenth trip: the guard read the consumer set the import was about to "
        "overwrite, and answered two ways for one final state"
    )


@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
def test_c12_17_the_eleventh_trip_one_call_site_of_four(adapter, make_registry):
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
    registry = make_registry(adapter)
    seed(registry, "meta_p", kind="predicate")
    seed(registry, "commentable", kind="predicate")
    seed(registry, "gamma", kind="predicate", predicates=["meta_p"])
    for member in ("aaa_note", "bbb_memo"):
        seed(registry, member, predicates=["commentable", "gamma"])

    retired = registry.retire("commentable", "superseded", retired_by="user:sd", force=True)
    if isinstance(retired, Refusal):
        pytest.skip(
            "PACKAGE.md 3.6 -- this backend cannot record a forced retirement: "
            f"{retired.reason}"
        )
    legal = registry.import_types(
        [
            {
                "name": "gamma", "kind": "predicate", "definition": "a capability",
                "predicates": ["meta_p"], "aliases": ["commentable"], "status": "active",
            }
        ],
        namespace="default", kind="predicate",
    )[0]
    assert not [w for w in legal.warnings if w.startswith("import_refused:")], (
        "the alias is LEGAL at this moment -- both gate sets are empty -- and a guard "
        "that refused here would be banned rather than narrowed"
    )
    assert registry.retire("gamma", "dormant", retired_by="user:sd", force=True)

    # The world moves between the write and the reinstatement, which is trip 6's shape.
    registry.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    assert {c.id for c in registry.consumers("gamma").gates_on} == {"svc:meta"}
    assert {c.id for c in registry.consumers("commentable").gates_on} == set()

    out = registry.reinstate("gamma", "back in service", reinstated_by="user:sd")
    assert isinstance(out, Refusal), f"reinstate performed the collapse: {out!r}"
    assert out.reason == "different_consumer_sets", out
    resolution = registry.resolve_type(
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

    from ..registry import Registry

    parameter = inspect.signature(Registry._alias_identity_breach).parameters[
        "declared_predicates"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty, (
        "a default here is what let three of four callers omit the operand refusal #1 "
        "cannot work without -- R64's own reasoning, one guard along"
    )


@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
def test_c12_19_an_import_that_removes_a_standing_alias_says_so_and_records_it(
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
    registry = make_registry(adapter)
    seed(registry, "alpha", kind="predicate", definition="a capability")
    seed(registry, "beta", kind="predicate", definition="a capability")
    seed(registry, "aaa_note", predicates=["alpha", "beta"])
    seed(registry, "bbb_memo", predicates=["alpha", "beta"])
    registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a capability"}],
        kind="predicate",
    )
    assert isinstance(
        registry.retire(
            "alpha", "beta says it better", retired_by="user:sd", successor="beta",
            force=True,
        ),
        TypeEntry,
    )
    survivor = [t for t in registry.list_types("predicate").types if t.name == "beta"][0]
    assert "zzz_moved" in survivor.aliases, "R75's transfer happened"

    rows = registry.import_types(
        [{"name": "beta", "status": "active", "aliases": [], "definition": "a capability"}],
        kind="predicate",
    )
    assert rows and isinstance(rows[0], TypeEntry), rows
    assert "aliases_removed:zzz_moved" in rows[0].warnings, (
        "the call that took the word away says which word",
        rows[0].warnings,
    )
    after = [t for t in registry.list_types("predicate").types if t.name == "beta"][0]
    assert "zzz_moved" not in after.aliases, "the removal itself is still permitted"

    removed = [
        e
        for e in registry.provenance("beta", namespace="default").history
        if e.event == "aliases_removed"
    ]
    assert removed, (
        "INTERFACE.md 5.8 -- a correction is a NEW EVENT, never an edit; the removal "
        "half owed one too, or the transfer's own record stands alone asserting a fact "
        "the store no longer holds"
    )
    assert removed[0].detail["aliases_removed"] == ["zzz_moved"], removed[0].detail

    # ...and an import that removes NOTHING does not claim it did.
    quiet = registry.import_types(
        [{"name": "beta", "status": "active", "aliases": [], "definition": "a capability"}],
        kind="predicate",
    )
    assert not [
        w for w in quiet[0].warnings if w.startswith("aliases_removed")
    ], ("a signal that never turns off is noise", quiet[0].warnings)


@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
def test_c12_20_the_alias_diff_runs_against_the_row_this_call_overwrites(
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
    registry = make_registry(adapter)
    seed(registry, "beta_", kind="predicate", definition="one and the same thing")
    written = registry.import_types(
        [{"name": "beta_", "status": "active", "aliases": ["zzz_word"],
          "definition": "one and the same thing"}],
        kind="predicate",
    )
    if not written or "zzz_word" not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the imported alias")
    assert not isinstance(
        registry.retire("beta_", "withdrawn", retired_by="user:sd", force=True), Refusal
    )

    out = registry.import_types(
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
             registry.list_types("predicate", include_retired=True).types}
    assert every.get("beta_") == ("zzz_word",), ("the word is still where it was", every)
    assert every.get("beta", ()) == (), every

    fabricated = [
        e
        for e in registry.provenance("beta", namespace="default").history
        if e.event == "aliases_removed"
    ]
    assert not fabricated, (
        "an event asserting a removal that did not happen is the class C12-19 was "
        "minted to remove, committed by C12-19 itself",
        fabricated,
    )


@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
def test_c12_21_a_word_a_tombstone_answers_to_is_not_free_at_import_types(
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
    registry = make_registry(adapter)
    seed(registry, "alpha", kind="predicate", definition="a capability")
    seed(registry, "aaa_note", predicates=["alpha"])
    written = registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or "zzz_moved" not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")
    assert "zzz_moved" in (gone.aliases or ()), gone.aliases

    out = registry.import_types(
        [{"name": "zzz_moved", "status": "active", "definition": "a foreign word"}],
        kind="predicate",
    )
    assert out and isinstance(out[0], TypeEntry), out
    assert out[0].name == "alpha", ("the holder comes back, not a new row", out[0].name)
    assert "word_previously_retired:alpha" in out[0].warnings, out[0].warnings
    assert not [
        t for t in registry.list_types("predicate", include_retired=True).types
        if t.name == "zzz_moved"
    ], "nothing is written"

    back = registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry), (
        "R11's governance act must still be available", back
    )


def _tombstone_holding(registry, word="zzz_moved"):
    """A RETIRED predicate that still answers to ``word``, and nothing named ``word``."""
    seed(registry, "alpha", kind="predicate", definition="a capability")
    seed(registry, "aaa_note", predicates=["alpha"])
    written = registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": [word],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or word not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")
    return gone


def test_c12_22_the_import_name_door_holds_the_word_across_kinds(adapter, make_registry):
    """**The FIFTEENTH trip at the third mint door.** Row 6d; ruling **R91**.

    `import_types` is a NAME door in its own right, and shipping the kind-blind scan at
    `propose_type` alone would be *a fix applied at one call site of three* — the single
    sentence of the ninth, tenth and eleventh trips.
    """
    registry = make_registry(adapter)
    tombstone = _tombstone_holding(registry)

    out = registry.import_types(
        [{"name": "zzz_moved", "status": "active", "definition": "another kind"}],
        kind="entity",
    )
    assert out and out[0].name == tombstone.name, out
    assert f"word_previously_retired:{tombstone.name}" in (out[0].warnings or ()), (
        out[0].warnings
    )
    assert isinstance(
        registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd"), TypeEntry
    )


def test_c12_23_the_import_alias_door_refuses_a_word_a_tombstone_answers_to(
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
    registry = make_registry(adapter)
    tombstone = _tombstone_holding(registry)

    out = registry.import_types(
        [{"name": "beta", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a brand new row"}],
        kind="predicate",
    )
    assert out, out
    assert "import_refused:word_held_by_tombstone" in (out[0].warnings or ()), (
        out[0].warnings
    )
    written = adapter.get_type("default", "beta", kind="predicate")
    assert written is None or "zzz_moved" not in (written.aliases or ()), (
        "nothing is written -- a refusal is not a warning on a completed act"
    )
    # ...and the whole point: the tombstone can still be brought back.
    assert isinstance(
        registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd"), TypeEntry
    ), "R11's governance act must survive the write that used to burn it"
    assert tombstone.name == "alpha"


def test_c12_24_a_skipped_identity_guard_says_so(adapter, make_registry):
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
    degraded = make_registry(
        DegradedAdapter(adapter, indexes_membership=False), approval_policy="auto"
    )
    seed(degraded, "meta_p", kind="predicate", definition="a meta capability")
    seed(degraded, "ent_a", kind="entity", definition="a thing", predicates=["meta_p"])
    seed(degraded, "ent_b", kind="entity", definition="a thing")
    out = degraded.register_consumer(
        Consumer(id="svc:meta", gate="meta_p", on_unknown="drop", owner="ops")
    )
    if isinstance(out, Refusal):
        pytest.skip(f"this backend cannot register a consumer ({out.reason})")
    gone = degraded.retire("ent_a", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the row ({gone.reason})")

    rows = degraded.import_types(
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


def test_c12_25_a_field_this_call_ignores_is_stated(adapter, make_registry):
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
    registry = make_registry(adapter, approval_policy="auto")
    out = registry.import_types(
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
    quiet = registry.import_types(
        [{"name": "esplanade", "namespace": "dpr", "definition": "a walk",
          "status": "active"}],
        namespace="dpr", kind="entity",
    )
    assert not any(
        w.startswith("import_field_ignored") for w in (quiet[0].warnings or ())
    ), quiet[0].warnings


def test_c12_26_the_import_name_door_holds_the_byte_identical_tombstone(
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
    registry = make_registry(adapter, approval_policy="auto")
    seed(registry, "w", kind="entity", definition="a thing")
    gone = registry.retire("w", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")

    # CONTROL: `propose_type` has no such exclusion and answers this way.
    control = registry.propose_type(
        "w", "another kind entirely", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(control, TypeEntry)
    assert "name_previously_retired" in (control.warnings or ()), control.warnings

    out = registry.import_types(
        [{"name": "w", "kind": "predicate", "definition": "another kind entirely",
          "status": "active"}],
        namespace="default", kind="predicate",
    )
    assert out and out[0].name == "w" and out[0].kind == "entity", (
        "the holder comes back, and it is the entity tombstone", out[0].name, out[0].kind
    )
    assert "name_previously_retired" in (out[0].warnings or ()), out[0].warnings
    assert not [
        t for t in registry.list_types("predicate").types if t.name == "w"
    ], "nothing is written"
    assert isinstance(
        registry.reinstate("w", "we were wrong", reinstated_by="user:sd"), TypeEntry
    ), "the tombstone must still be reachable"
