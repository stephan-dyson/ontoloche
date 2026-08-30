"""C5 -- ``approve`` / ``reject`` (11). Mechanism 1.

Approval is the review that A1 says the partner agency never had.
"""

from __future__ import annotations

import pytest

from ..adapter import ProposalQuery, TypeQuery
from ..types import Evidence, Proposal, Refusal, Rejection, TypeEntry
from ._support import seed
from .doubles import DegradedAdapter

DATA_EVIDENCE = Evidence(kind="data", summary="counted in the sample", locator="sample.csv")


@pytest.mark.requires_capability("stores_proposals")
def test_c5_01_approve_records_who_and_when_and_activates(registry, clock):
    proposal = registry.propose_type("facility", "a nursing home", [DATA_EVIDENCE], "user:pm")
    entry = registry.approve(proposal.id, "user:sd")
    assert isinstance(entry, TypeEntry)
    assert entry.status == "active"
    assert entry.provenance.approved_by == "user:sd"
    assert entry.provenance.approved_at == clock.now()


def test_c5_02_no_active_entry_anywhere_has_a_null_approver(registry, adapter, make_registry):
    seed(registry, "facility", definition="a nursing home")
    seed(registry, "survey", definition="an inspection visit")
    auto = make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    auto.propose_type("citation", "one deficiency, one row", [], "ai:classifier", tier="opus")
    registry.import_types([{"name": "imported_thing", "status": "active"}])

    page = adapter.find_types(TypeQuery(include_retired=True))
    active = [r for r in page.records if r.status == "active"]
    assert active
    for rec in active:
        approver = (rec.provenance or {}).get("approved_by")
        assert approver, f"{rec.name} is active with no approver -- 2.4's invariant"


@pytest.mark.requires_capability("stores_proposals")
def test_c5_03_the_severity_case_verbatim(adapter, make_registry):
    """INTERFACE.md 10, end to end: 0.5's worst result, made operational."""
    registry = make_registry(adapter, min_auto_approve_tier="sonnet")
    proposal = registry.propose_type(
        name="scope_severity_code",
        kind="value_set",
        definition="Ordered severity scale A-L. Higher letters are LESS serious.",
        evidence=[],
        proposed_by="ai:proposer",
        tier="haiku",
    )
    assert set(proposal.warnings) >= {"no_evidence", "unverified_semantics"}

    refusal = registry.approve(proposal.id, "ai:proposer", mode="auto")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "tier_below_auto_approve_policy"
    assert refusal.detail["tier"] == "haiku"
    assert refusal.detail["min_auto_approve_tier"] == "sonnet"

    # The caller may escalate to a human, and the type then carries the warning forever.
    entry = registry.approve(proposal.id, "user:sd")
    assert isinstance(entry, TypeEntry)
    assert "unverified_semantics" in entry.warnings


@pytest.mark.requires_capability("stores_proposals")
def test_c5_04_approving_a_decided_proposal_is_an_idempotent_refusal(registry):
    proposal = registry.propose_type("facility", "a nursing home", [DATA_EVIDENCE], "user:pm")
    first = registry.approve(proposal.id, "user:sd")
    assert isinstance(first, TypeEntry)

    second = registry.approve(proposal.id, "user:other")
    assert isinstance(second, Refusal), "a refusal, not an exception"
    assert second.reason == "already_decided"
    assert second.detail["decided_by"] == "user:sd"

    third = registry.reject(proposal.id, "user:other", "changed my mind")
    assert isinstance(third, Refusal) and third.reason == "already_decided"


@pytest.mark.requires_capability("stores_proposals")
def test_c5_05_an_unknown_proposal_id_is_a_refusal(registry):
    refusal = registry.approve("no-such-proposal", "user:sd")
    assert isinstance(refusal, Refusal) and refusal.reason == "unknown_proposal"


@pytest.mark.requires_capability("stores_proposals")
def test_c5_06_approving_with_unverified_semantics_succeeds_and_keeps_the_warning(registry):
    proposal = registry.propose_type(
        "deficiency_grade",
        "An ordered scale where a higher grade is more serious.",
        [DATA_EVIDENCE],
        "user:pm",
        kind="value_set",
    )
    assert "unverified_semantics" in proposal.warnings

    entry = registry.approve(proposal.id, "user:sd")
    assert isinstance(entry, TypeEntry)
    assert "unverified_semantics" in entry.warnings

    # Permanently: still there on a fresh read, so list_types can enumerate it later.
    listing = registry.list_types(unverified_semantics=True)
    assert [t.name for t in listing.types] == ["deficiency_grade"]


@pytest.mark.requires_capability("stores_proposals", "stores_events", "indexes_membership")
def test_c5_07_an_approvers_amendment_keeps_the_original_in_history(registry):
    proposal = registry.propose_type(
        "facility", "a nursing home, roughly", [DATA_EVIDENCE], "user:pm", predicates=["searchable"]
    )
    entry = registry.approve(
        proposal.id,
        "user:sd",
        definition="a Medicare/Medicaid-certified nursing home, identified by its CCN",
        predicates=["searchable", "addressable"],
        note="tightened the wording and added addressable",
    )
    assert entry.definition.startswith("a Medicare/Medicaid-certified")
    assert entry.predicates == ("addressable", "searchable")

    approved = [e for e in registry.provenance("facility").history if e.event == "approved"]
    assert approved
    detail = approved[0].detail
    assert detail["definition_before"] == "a nursing home, roughly"
    assert detail["predicates_before"] == ["searchable"]
    assert detail["note"] == "tightened the wording and added addressable"


@pytest.mark.requires_capability("stores_proposals")
def test_c5_08_reject_requires_a_reason(registry):
    proposal = registry.propose_type("widget", "a thing", [DATA_EVIDENCE], "user:pm")
    with pytest.raises(ValueError):
        registry.reject(proposal.id, "user:sd", "")
    with pytest.raises(ValueError):
        registry.reject(proposal.id, "user:sd", "   ")


@pytest.mark.requires_capability("stores_proposals")
def test_c5_09_a_rejection_is_retained_and_findable(registry, adapter):
    """The record that stops a re-proposal in six months."""
    proposal = registry.propose_type("widget", "a thing", [DATA_EVIDENCE], "user:pm")
    rejection = registry.reject(proposal.id, "user:sd", "not a domain concept; use `component`")
    assert isinstance(rejection, Rejection)

    page = adapter.find_proposals(ProposalQuery(namespace="default", status="rejected"))
    assert [r.name for r in page.records] == ["widget"]
    assert page.records[0].decision_reason == "not a domain concept; use `component`"
    assert page.records[0].decided_by == "user:sd"


@pytest.mark.requires_capability("stores_proposals")
def test_c5_10_reject_records_the_successor(registry, adapter):
    seed(registry, "component", definition="the type the proposer should have used")
    proposal = registry.propose_type("widget", "a thing", [DATA_EVIDENCE], "user:pm")
    rejection = registry.reject(
        proposal.id, "user:sd", "use the existing word", superseded_by="component"
    )
    assert rejection.superseded_by == "component"
    stored = adapter.get_proposal(proposal.id)
    assert stored.superseded_by == "component"


@pytest.mark.requires_capability("stores_proposals", "stores_events")
def test_c5_11_an_approval_is_atomic(registry, adapter, monkeypatch):
    """An injected failure between the type write and the event write leaves no type and
    no decided proposal. A half-commit produces an active type with no approval record,
    which is the rubber-stamping failure arriving through the data model."""
    proposal = registry.propose_type("facility", "a nursing home", [DATA_EVIDENCE], "user:pm")

    class Boom(RuntimeError):
        pass

    def explode(rec):
        if rec.event == "approved":
            raise Boom("the event write failed after the type write")
        return original(rec)

    original = adapter.append_event
    monkeypatch.setattr(adapter, "append_event", explode)

    with pytest.raises(Boom):
        registry.approve(proposal.id, "user:sd")

    monkeypatch.undo()
    assert adapter.get_type("default", "facility") is None
    assert adapter.get_proposal(proposal.id).status == "pending"
    assert adapter.get_proposal(proposal.id).decided_by is None


def test_c5_12_a_backend_with_no_proposal_table_refuses_to_decide(adapter, make_registry):
    """**`proposals_not_stored`, tested.** PACKAGE.md 3.6 introduces three refusal
    reasons; §6.3's coverage table named `C9-02`, `C10-08` and `C15-04` for them, but
    those cover only two -- `cannot_record_override` twice and
    `attributes_schema_violation` once. **`proposals_not_stored` had no test anywhere in
    either suite**, which is UC1's own path: PACKAGE.md 7.3 B4 says a backend with no
    proposal table is conformant, `propose_type` becomes the decision, and
    `approve`/`reject` must refuse rather than pretend. Added by row 3c after an
    adversarial review round; see docs/findings/3C-VALIDATION.md.

    The valuable half of B4 is that the price of a review step becomes legible: *one
    table*. This test is what makes "conformant without one" mean something.
    """
    blind = make_registry(DegradedAdapter(adapter, stores_proposals=False))

    # propose_type IS the decision -- an entry, immediately, auto-approved and legible.
    entry = blind.propose_type(
        "blocks", "this work item blocks that one", [], "ai:classifier", tier="opus"
    )
    assert isinstance(entry, TypeEntry), "no proposal table means no proposal to return"
    assert entry.status == "active"
    assert entry.provenance.approved_by.startswith("auto:"), "never blank -- INTERFACE 2.4"

    # And the other half of the loop refuses, honestly, rather than raising or lying.
    refused = blind.approve("any-id-at-all", "user:sd")
    assert isinstance(refused, Refusal)
    assert refused.reason == "proposals_not_stored", (
        "not `unknown_proposal` -- that would be a confident wrong answer about a "
        "proposal that was never storable in the first place (Rule U)"
    )

    rejected = blind.reject("any-id-at-all", "user:sd", "no")
    assert isinstance(rejected, Refusal)
    assert rejected.reason == "proposals_not_stored"
