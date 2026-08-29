# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c4_propose_type.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C4 -- ``propose_type`` (9). Mechanism 1: no review.

The call that makes an addition a *request* rather than a fact. It refuses exactly two
things and warns about everything else -- refusing a near-duplicate is how you flatten a
capability predicate.
"""

from __future__ import annotations
from datetime import UTC, datetime
import pytest
from open_ontology.policy import NamespacePolicy
from open_ontology.types import Citation, Evidence, Proposal, TypeEntry
from open_ontology.aio.contract._support import DOC_EVIDENCE_URL, seed


DATA_EVIDENCE = Evidence(
    kind="data",
    summary="14,627 distinct CCNs over 419,479 rows; CCN->name is 1:1",
    locator="NH_HealthCitations_Aug2026.csv",
)

async def test_c4_01_an_empty_definition_is_refused(registry):
    with pytest.raises(ValueError):
        await registry.propose_type("facility", "", [DATA_EVIDENCE], "user:sd")
    with pytest.raises(ValueError):
        await registry.propose_type("facility", "   ", [DATA_EVIDENCE], "user:sd")

async def test_c4_02_an_ai_proposer_without_a_tier_is_refused(registry):
    with pytest.raises(ValueError):
        await registry.propose_type("facility", "a nursing home", [], "ai:proposer")
    ok = await registry.propose_type("facility", "a nursing home", [], "ai:proposer", tier="opus")
    assert isinstance(ok, Proposal) and ok.tier == "opus"

async def test_c4_03_a_name_already_taken_returns_the_existing_entry(registry):
    original = await seed(registry, "facility", definition="a Medicare-certified nursing home")
    answer = await registry.propose_type(
        "facility", "some other idea of what a facility is", [DATA_EVIDENCE], "user:pm"
    )
    assert isinstance(answer, TypeEntry), "not an error; the proposer's question is answered"
    assert answer.definition == original.definition
    assert answer.status == "active"

async def test_c4_04_a_near_duplicate_warns_and_does_not_refuse(registry):
    """The kill-row protection: refusing here is how a locally-correct new predicate
    gets folded into an existing one instead of being created."""
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    proposal = await registry.propose_type(
        "commentible",
        "a code path will accept it -- a second, differently spelled list",
        [DATA_EVIDENCE],
        "user:pm",
        kind="predicate",
    )
    assert isinstance(proposal, Proposal)
    assert any(w.startswith("near_duplicate:") for w in proposal.warnings)
    assert "near_duplicate:commentable" in proposal.warnings
    assert proposal.near_matches

async def test_c4_05_no_evidence_warns_and_the_proposal_is_still_created(registry):
    proposal = await registry.propose_type("facility", "a nursing home", [], "user:sd")
    assert isinstance(proposal, Proposal)
    assert "no_evidence" in proposal.warnings, "an honest empty beats a fabricated citation"
    assert proposal.evidence == ()

async def test_c4_06_a_domain_semantic_without_an_external_doc_is_unverified(registry):
    asserting = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L. Higher letters are LESS serious.",
        [DATA_EVIDENCE],
        "ai:proposer",
        kind="value_set",
        tier="haiku",
    )
    assert "unverified_semantics" in asserting.warnings
    assert "no_evidence" not in asserting.warnings, "there IS evidence; it is just not a citation"

    cited = await registry.propose_type(
        "scope_severity_code_v2",
        "Ordered severity scale A-L. J, K and L are Immediate Jeopardy.",
        [
            Evidence(
                kind="external_doc",
                summary="CMS scope-and-severity grid runs A (least serious) to L (most).",
                citation=Citation(
                    url=DOC_EVIDENCE_URL,
                    title="CMS QSO-23-01",
                    retrieved_at=datetime(2026, 8, 28, tzinfo=UTC),
                    quote="J, K and L constitute Immediate Jeopardy.",
                ),
            )
        ],
        "ai:proposer",
        kind="value_set",
        tier="opus",
    )
    assert "unverified_semantics" not in cited.warnings

async def test_c4_07_auto_approval_is_legible_never_blank(adapter, make_registry):
    registry = await make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    entry = await registry.propose_type("blocks", "this work item blocks that one", [], "ai:classifier", tier="haiku")
    assert isinstance(entry, TypeEntry)
    assert entry.status == "active"
    assert entry.provenance.approved_by == "auto:classifier"
    assert entry.provenance.approved_by is not None, (
        "a blank field invites a reader to assume a human signed off"
    )

async def test_c4_08_a_retired_name_is_not_silently_reusable(registry, adapter):
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    answer = await registry.propose_type("watch", "something else entirely", [DATA_EVIDENCE], "user:pm")
    assert isinstance(answer, TypeEntry)
    assert answer.status == "retired"
    assert "name_previously_retired" in answer.warnings
    assert (await adapter.get_type("default", "watch")).status == "retired", "and no new entry"

@pytest.mark.parametrize(
    "name",
    ["Facility", "1facility", "facility-name", "facility name", "", "f" * 65, "_facility"],
)
async def test_c4_09_the_name_rule_is_enforced_identically_on_every_backend(registry, name):
    with pytest.raises(ValueError):
        await registry.propose_type(name, "a definition", [DATA_EVIDENCE], "user:sd")
