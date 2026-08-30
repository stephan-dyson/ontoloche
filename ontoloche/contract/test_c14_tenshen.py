"""C14 -- the Tenshen contortions, documented (7). One per contortion in INTERFACE.md 9.

**Every one of these passes when the interface behaves as specified -- not when Tenshen
is accommodated.** Two of them are the interface telling beacon something true about its
own instrumentation rather than complaining about a field, and those are the valuable
half.
"""

from __future__ import annotations

import pytest

import re
from datetime import timedelta
from pathlib import Path

import ontoloche
from .. import registry as registry_module
from ..adapter import TypeQuery
from ._support import seed
from .doubles import DegradedAdapter

NO_TIMESTAMPS = {"timestamps_usage": "work_link_types has no last_used_at column"}


@pytest.mark.requires_capability("stores_attributes")
def test_c14_01_contortion_1_edge_shape_lives_unvalidated_in_attributes(registry):
    """`is_symmetric` and `inverse_label` are edge-shape fields and edges are #4. In v0
    they survive only in `attributes`, which the registry never reads -- so a symmetric
    type carrying an inverse label is accepted and nothing complains. Recorded, not
    fixed: this is the strongest argument that EDGES must follow INTERFACE closely."""
    entry = seed(
        registry,
        "related_to",
        kind="edge",
        definition="an unspecified relationship between two work items",
        attributes={"is_symmetric": True, "inverse_label": "also related to"},
    )
    assert entry.attributes["is_symmetric"] is True
    assert entry.attributes["inverse_label"] == "also related to"
    assert entry.warnings == () or "attributes_invalid" not in " ".join(entry.warnings), (
        "v0 cannot enforce that a symmetric type has no inverse label, and does not "
        "pretend to"
    )


@pytest.mark.requires_capability("counts_usage")
def test_c14_02_contortion_2_a_bare_counter_leaves_orphaned_unknowable(
    adapter, make_registry
):
    """The venture's rot sensor cannot fire on this backend, and the interface says so
    rather than reporting a number it cannot support. This test is of the interface, not
    of beacon: it keeps passing unchanged if `last_used_at` is ever added."""
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")
    setup.record_use("blocks")
    setup.record_use("blocks")

    tenshen = make_registry(DegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    report = tenshen.usage("blocks")
    assert report.count == 2
    assert report.last_seen is None
    assert report.orphaned is None
    assert report.why == NO_TIMESTAMPS["timestamps_usage"]
    assert report.complete is False


@pytest.mark.requires_capability("stores_events")
def test_c14_03_contortion_3_no_status_column_means_everything_migrates_active(registry):
    """Tenshen types are born live and never retired. Migration sets every row active;
    there is no historical retirement to import, and none is invented."""
    rows = [
        {"name": name, "definition": definition, "kind": "edge"}
        for name, definition in (
            ("blocks", "this work item blocks that one"),
            ("related_to", "an unspecified relationship"),
            ("part_of", "this work item is part of that one"),
            ("duplicates", "this work item duplicates that one"),
            ("follows", "this work item follows that one"),
        )
    ]
    entries = registry.import_types(rows, system="tenshen", imported_by="import:tenshen")
    assert len(entries) == 5
    assert {e.status for e in entries} == {"active"}

    for entry in entries:
        history = registry.provenance(entry.name).history
        assert [e.event for e in history] == ["imported"], (
            "no retirement history is invented for a source that never had one"
        )


def test_c14_04_contortion_4_auto_approval_becomes_legible_and_enumerable(
    adapter, make_registry
):
    """The highest-value thing the interface does for Tenshen: not a new capability,
    but making an existing silent auto-approval visible."""
    registry = make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    entry = registry.propose_type(
        "supersedes", "this work item supersedes that one", [], "ai:classifier", tier="opus"
    )
    assert entry.status == "active"
    assert entry.provenance.approved_by == "auto:classifier"

    machine_made = registry.list_types(created_by="ai")
    assert [t.name for t in machine_made.types] == ["supersedes"]
    assert all(t.provenance.approved_by.startswith("auto:") for t in machine_made.types), (
        "the query 'which of our types were never seen by a human?' is now answerable"
    )


def test_c14_05_contortion_5_a_discarded_fit_score_leaves_the_evidence_slot_empty(
    adapter, make_registry
):
    """`fit_score` justifies creation and is then discarded, and the user's free text is
    persisted on the link rather than on the type. Honest, and unflattering."""
    registry = make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    entry = registry.propose_type(
        "supersedes", "this work item supersedes that one", [], "ai:classifier", tier="haiku"
    )
    assert entry.provenance.evidence == ()
    assert "no_evidence" in entry.warnings
    assert registry.provenance("supersedes").evidence == ()


def test_c14_06_contortion_6_zero_registered_consumers_is_a_reported_null_result(registry):
    """Not a defect of the interface: the interface reporting that Tenshen has exactly
    the blind spot finding 0.1 diagnosed. The registration is the work."""
    seed(registry, "blocks", kind="edge", definition="this work item blocks that one")
    report = registry.consumers("blocks")
    assert report.known == 0
    assert report.complete is False
    assert report.why_incomplete
    assert report.gates_on == () and report.would_drop == () and report.would_error == ()


def test_c14_07_contortion_7_the_package_ships_no_default_type():
    """A registry that ships a default type is a registry that quietly labels things
    wrong at scale. The `related_to` fallback is caller policy and stays there.

    Recorded so nobody adds `default_type` in a later pass thinking it was an oversight.
    """
    assert not hasattr(ontoloche, "default_type")
    assert not hasattr(ontoloche, "DEFAULT_TYPE")
    assert "default_type" not in dir(ontoloche)

    public = [
        Path(ontoloche.__file__),
        Path(registry_module.__file__),
        Path(ontoloche.__file__).parent / "types.py",
        Path(ontoloche.__file__).parent / "policy.py",
        Path(ontoloche.__file__).parent / "adapter.py",
    ]
    for path in public:
        source = path.read_text(encoding="utf-8")
        assert not re.search(r"\bdefault_type\b", source), f"{path.name} names a default type"
        assert not re.search(r"^\s*\w*DEFAULT_TYPE\w*\s*=", source, re.M), (
            f"{path.name} defines a fallback type constant"
        )
        # `related_to` may be discussed in a test; it must not be a constant here.
        assert not re.search(r'^\s*\w+\s*=\s*"related_to"', source, re.M), (
            f"{path.name} ships a stock fallback type"
        )
