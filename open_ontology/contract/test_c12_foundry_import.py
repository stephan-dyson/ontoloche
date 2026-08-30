"""C12 -- the Foundry import mapping, and the fourth door into the kill row (12). From 0.3 consequence 2 / INTERFACE.md 2.5.

The mapping is stated in the interface rather than left to an importer, so it is tested
here. It lands on ``Registry.import_types``, a method beyond the twelve, because no 5.x
call performs it -- deviation D-8 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations

import pytest

from ..types import Evidence, Refusal, ResolveContext, TypeEntry
from ._support import seed

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
