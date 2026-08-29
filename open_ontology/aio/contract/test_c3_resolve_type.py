# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c3_resolve_type.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C3 -- ``resolve_type`` (9). Mechanism 2, with mechanism 1 as the gate.

No test here may pass or fail because of resolver *quality*: the assertions are about
outcomes and shapes, never about a score's value.
"""

from __future__ import annotations
import pytest
from open_ontology.types import ResolveContext
from open_ontology.aio.contract._support import seed, snapshot


CMS_SIBLINGS = ("Provider Address", "City/Town", "State", "ZIP Code")

async def test_c3_01_an_existing_type_comes_back_with_a_float_confidence(registry):
    await seed(registry, "facility", definition="a Medicare-certified nursing home")
    resolution = await registry.resolve_type("facility", ResolveContext(), tier="opus")
    assert resolution.outcome == "existing"
    assert resolution.type is not None and resolution.type.name == "facility"
    assert isinstance(resolution.confidence, float)

async def test_c3_02_a_proposal_outcome_persists_nothing(registry, adapter):
    await seed(registry, "facility", definition="a Medicare-certified nursing home")
    before = await snapshot(adapter)

    resolution = await registry.resolve_type(
        "deficiency_tag",
        ResolveContext(definition_hint="the F-tag a citation was written under"),
        tier="opus",
    )
    assert resolution.outcome == "proposal"
    assert resolution.proposal is not None and resolution.proposal.name == "deficiency_tag"
    assert await snapshot(adapter) == before, "resolve_type is the call that must not write"
    assert await adapter.get_type("default", "deficiency_tag") is None

async def test_c3_03_below_min_confidence_is_none_with_alternatives(registry):
    await seed(registry, "facility", definition="a Medicare-certified nursing home")
    resolution = await registry.resolve_type(
        "facilty", ResolveContext(), tier="opus", min_confidence=0.99
    )
    assert resolution.outcome == "none", "never the best of a bad set"
    assert resolution.alternatives, "the near misses go to the caller so a human can overrule"
    assert "facility" in [name for name, _ in resolution.alternatives]

    # Rule K (INTERFACE.md 3, 5.3): alternatives is a list result, and it is scored in
    # ONE namespace. complete is therefore always False, so an empty alternatives can
    # never be read as "there is nothing like this anywhere" -- contortion 8 reported
    # rather than implied.
    assert resolution.complete is False
    assert resolution.known == len(resolution.alternatives)
    assert resolution.scoped_to == "default"
    assert "default" in resolution.why_incomplete

async def test_c3_04_confidence_is_none_when_no_scorer_ran_and_none_is_not_zero(registry):
    resolution = await registry.resolve_type("facility", ResolveContext(), tier="opus")
    assert resolution.outcome == "proposal"
    assert resolution.confidence is None
    assert resolution.confidence != 0.0

async def test_c3_05_tier_is_required_not_defaulted(registry):
    with pytest.raises(TypeError):
        await registry.resolve_type("facility", ResolveContext())

@pytest.mark.requires_capability("stores_proposals")
async def test_c3_06_tier_is_echoed_and_lands_in_provenance_unchanged(registry):
    resolution = await registry.resolve_type(
        "facility", ResolveContext(definition_hint="a nursing home"), tier="haiku"
    )
    assert resolution.tier == "haiku"

    proposal = await registry.propose_type(
        "facility", "a nursing home", [], "ai:proposer", tier=resolution.tier
    )
    entry = await registry.approve(proposal.id, "user:sd")
    assert entry.provenance.model_tier == "haiku"
    assert (await registry.provenance("facility")).model_tier == "haiku"

@pytest.mark.requires_capability("stores_proposals")
async def test_c3_07_a_prior_rejection_surfaces_in_alternatives(registry):
    proposal = await registry.propose_type(
        "widget", "a thing somebody wanted once", [], "user:pm"
    )
    await registry.reject(
        proposal.id, "user:sd", "not a domain concept; use `component`", superseded_by=None
    )

    resolution = await registry.resolve_type("widget", ResolveContext(), tier="opus")
    assert "widget" in [name for name, _ in resolution.alternatives]
    score = dict(resolution.alternatives)["widget"]
    assert score is None, "nothing scored a rejection; 0.0 would be a claim we did not make"
    assert "rejected" in resolution.reason

@pytest.mark.resolver_dependent
async def test_c3_08_cms_location_is_a_redundant_projection_not_a_type(registry):
    """T3: `Location` is exactly rebuilt from four sibling columns in 419,428 of 419,479
    rows and 400 of 400 in the sample. Under a three-outcome surface this returns None,
    which reads as "go propose it" -- the registry handing the pollution machine its
    first type."""
    await seed(registry, "facility", definition="a Medicare-certified nursing home")
    resolution = await registry.resolve_type(
        "location",
        ResolveContext(
            source="NH_HealthCitations_Aug2026.csv#Location",
            sibling_columns=CMS_SIBLINGS,
            sample_values=("2621 15TH AVE S,GREAT FALLS,MT,59405",),
        ),
        tier="opus",
    )
    assert resolution.outcome == "not_a_type"
    assert resolution.reason == "redundant_projection"

@pytest.mark.resolver_dependent
async def test_c3_09_cms_processing_date_is_an_export_artefact(registry):
    """T7: single-valued (2026-08-01) across the whole file. Zero information."""
    resolution = await registry.resolve_type(
        "processing_date",
        ResolveContext(
            source="NH_HealthCitations_Aug2026.csv#Processing Date",
            sample_values=("2026-08-01",) * 12,
            sibling_columns=("Survey Date", "Correction Date"),
        ),
        tier="opus",
    )
    assert resolution.outcome == "not_a_type"
    assert resolution.reason == "export_artefact"
