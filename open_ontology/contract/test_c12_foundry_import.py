"""C12 -- the Foundry import mapping (4). From 0.3 consequence 2 / INTERFACE.md 2.5.

The mapping is stated in the interface rather than left to an importer, so it is tested
here. It lands on ``Registry.import_types``, a method beyond the twelve, because no 5.x
call performs it -- deviation D-8 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations

import pytest

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
