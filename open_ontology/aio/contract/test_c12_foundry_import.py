# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c12_foundry_import.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C12 -- the Foundry import mapping (7). From 0.3 consequence 2 / INTERFACE.md 2.5.

The mapping is stated in the interface rather than left to an importer, so it is tested
here. It lands on ``AsyncRegistry.import_types``, a method beyond the twelve, because no 5.x
call performs it -- deviation D-8 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations
import pytest
from open_ontology.aio.contract._support import seed


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
    assert sorted([t.name for t in (await registry.list_types()).types]) == ["cycle_track"]

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
