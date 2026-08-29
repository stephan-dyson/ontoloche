"""C8 -- ``provenance`` (5). Mechanisms 1 and 3.

Who added this, when, on what evidence, and did anybody actually approve it.
"""

from __future__ import annotations

import pytest

from datetime import UTC, datetime, timedelta

from ..types import Citation, Evidence
from ._support import DOC_EVIDENCE_URL, seed


@pytest.mark.requires_capability("stores_proposals")
def test_c8_01_missing_evidence_is_empty_never_a_reconstructed_narrative(registry):
    proposal = registry.propose_type("facility", "a nursing home", [], "user:pm")
    registry.approve(proposal.id, "user:sd")

    provenance = registry.provenance("facility")
    assert provenance.evidence == ()
    assert provenance.proposed_by == "user:pm"
    assert provenance.approved_by == "user:sd"


@pytest.mark.requires_capability("stores_proposals")
def test_c8_02_history_is_append_only(registry, clock):
    proposal = registry.propose_type("watch", "a thing a user watches", [], "user:pm")
    registry.approve(proposal.id, "user:sd")
    before = list(registry.provenance("watch").history)
    assert [e.event for e in before] == ["proposed", "approved"]

    clock.advance(timedelta(minutes=5))
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    after = list(registry.provenance("watch").history)
    assert [e.event for e in after] == ["proposed", "approved", "retired"]
    assert after[: len(before)] == before, (
        "a correction is a new event, never an edit -- no prior event's bytes changed"
    )


def test_c8_03_an_auto_approved_entry_says_auto(adapter, make_registry):
    registry = make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    registry.propose_type("blocks", "this blocks that", [], "ai:classifier", tier="opus")

    provenance = registry.provenance("blocks")
    assert provenance.approved_by == "auto:classifier"
    assert provenance.approved_by.startswith("auto:")


def test_c8_04_an_imported_row_says_unknown_imported_never_null(registry):
    registry.import_types(
        [{"name": "flight", "status": "active", "apiName": "Flight", "rid": "ri.o.1"}]
    )
    provenance = registry.provenance("flight")
    assert provenance.approved_by == "unknown:imported"
    assert provenance.imported_from == {
        "system": "foundry",
        "apiName": "Flight",
        "rid": "ri.o.1",
    }


@pytest.mark.requires_capability("stores_proposals")
def test_c8_05_model_tier_is_never_overwritten(registry, clock):
    proposal = registry.propose_type(
        "scope_severity_code",
        "an ordered severity scale",
        [
            Evidence(
                kind="external_doc",
                summary="CMS scope-and-severity grid runs A to L",
                citation=Citation(
                    url=DOC_EVIDENCE_URL,
                    title="CMS QSO-23-01",
                    retrieved_at=datetime(2026, 8, 28, tzinfo=UTC),
                ),
            )
        ],
        "ai:proposer",
        kind="value_set",
        tier="haiku",
    )
    registry.approve(
        proposal.id,
        "user:sd",
        definition="an ordered severity scale A-L; J, K and L are Immediate Jeopardy",
        note="corrected the wording",
    )
    assert registry.provenance("scope_severity_code").model_tier == "haiku", (
        "the tier that produced the proposal, not the tier of whoever touched it last -- "
        "this is what answers 'which types were proposed by a cheap model?'"
    )

    clock.advance(timedelta(days=1))
    registry.retire("scope_severity_code", "replaced", retired_by="user:sd")
    assert registry.provenance("scope_severity_code").model_tier == "haiku"
