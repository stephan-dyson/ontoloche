"""C3 -- ``resolve_type`` (9). Mechanism 2, with mechanism 1 as the gate.

No test here may pass or fail because of resolver *quality*: the assertions are about
outcomes and shapes, never about a score's value.
"""

from __future__ import annotations

import pytest

from ..types import ResolveContext
from ._support import seed, snapshot

CMS_SIBLINGS = ("Provider Address", "City/Town", "State", "ZIP Code")


def test_c3_01_an_existing_type_comes_back_with_a_float_confidence(registry):
    seed(registry, "facility", definition="a Medicare-certified nursing home")
    resolution = registry.resolve_type("facility", ResolveContext(), tier="opus")
    assert resolution.outcome == "existing"
    assert resolution.type is not None and resolution.type.name == "facility"
    assert isinstance(resolution.confidence, float)


def test_c3_02_a_proposal_outcome_persists_nothing(registry, adapter):
    seed(registry, "facility", definition="a Medicare-certified nursing home")
    before = snapshot(adapter)

    resolution = registry.resolve_type(
        "deficiency_tag",
        ResolveContext(definition_hint="the F-tag a citation was written under"),
        tier="opus",
    )
    assert resolution.outcome == "proposal"
    assert resolution.proposal is not None and resolution.proposal.name == "deficiency_tag"
    assert snapshot(adapter) == before, "resolve_type is the call that must not write"
    assert adapter.get_type("default", "deficiency_tag") is None


def test_c3_03_below_min_confidence_is_none_with_alternatives(registry):
    seed(registry, "facility", definition="a Medicare-certified nursing home")
    resolution = registry.resolve_type(
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


def test_c3_04_confidence_is_none_when_no_scorer_ran_and_none_is_not_zero(registry):
    resolution = registry.resolve_type("facility", ResolveContext(), tier="opus")
    assert resolution.outcome == "proposal"
    assert resolution.confidence is None
    assert resolution.confidence != 0.0


def test_c3_05_tier_is_required_not_defaulted(registry):
    with pytest.raises(TypeError):
        registry.resolve_type("facility", ResolveContext())


@pytest.mark.requires_capability("stores_proposals")
def test_c3_06_tier_is_echoed_and_lands_in_provenance_unchanged(registry):
    resolution = registry.resolve_type(
        "facility", ResolveContext(definition_hint="a nursing home"), tier="haiku"
    )
    assert resolution.tier == "haiku"

    proposal = registry.propose_type(
        "facility", "a nursing home", [], "ai:proposer", tier=resolution.tier
    )
    entry = registry.approve(proposal.id, "user:sd")
    assert entry.provenance.model_tier == "haiku"
    assert registry.provenance("facility").model_tier == "haiku"


@pytest.mark.requires_capability("stores_proposals")
def test_c3_07_a_prior_rejection_surfaces_in_alternatives(registry):
    proposal = registry.propose_type(
        "widget", "a thing somebody wanted once", [], "user:pm"
    )
    registry.reject(
        proposal.id, "user:sd", "not a domain concept; use `component`", superseded_by=None
    )

    resolution = registry.resolve_type("widget", ResolveContext(), tier="opus")
    assert "widget" in [name for name, _ in resolution.alternatives]
    score = dict(resolution.alternatives)["widget"]
    assert score is None, "nothing scored a rejection; 0.0 would be a claim we did not make"
    assert "rejected" in resolution.reason


@pytest.mark.resolver_dependent
def test_c3_08_cms_location_is_a_redundant_projection_not_a_type(registry):
    """T3: `Location` is exactly rebuilt from four sibling columns in 419,428 of 419,479
    rows and 400 of 400 in the sample. Under a three-outcome surface this returns None,
    which reads as "go propose it" -- the registry handing the pollution machine its
    first type."""
    seed(registry, "facility", definition="a Medicare-certified nursing home")
    resolution = registry.resolve_type(
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
def test_c3_09_cms_processing_date_is_an_export_artefact(registry):
    """T7: single-valued (2026-08-01) across the whole file. Zero information."""
    resolution = registry.resolve_type(
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


@pytest.mark.requires_capability("indexes_membership")
def test_c3_10_a_retired_name_is_named_in_the_resolution_not_silently_omitted(registry):
    """**Rule U, third instance.** `resolve_type` is the call INTERFACE.md 5.3 says is
    *"designed against mechanism 2 -- nobody could find the existing types"*, and it
    could not find a retired one.

    A retired exact match is correctly not an `existing` outcome -- 5.9 makes the name
    permanently unusable. But the registry had just read the tombstone and threw it
    away, and then answered *"nothing in the vocabulary fits 'watch'"*: a confident
    negative about a word it knew was burned. A classifier that trusts it calls
    `propose_type` and gets the old retired `TypeEntry` back, distinguishable from a
    fresh success only by inspecting `.status`.

    The fix needs no new field: it is surfaced the way 5.5 already surfaces a prior
    rejection -- named in `reason`, listed in `alternatives` with a `None` score,
    because nothing scored it. Added by row 3c after an adversarial review round
    reproduced it live.
    """
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    resolution = registry.resolve_type(
        "watch", ResolveContext(definition_hint="something else entirely"), tier="opus"
    )
    assert resolution.outcome != "existing", "a retired name is not usable (5.9)"
    assert "retired" in resolution.reason, "the tombstone must be named, not discarded"
    assert "superseded by `capture`" in resolution.reason, "with the reason it was retired"
    assert "capture" in resolution.reason, "and the successor, so the caller has somewhere to go"
    assert ("watch", None) in resolution.alternatives, (
        "listed like a prior rejection, scored None because nothing scored it"
    )
    assert "nothing in the vocabulary fits" not in resolution.reason, (
        "the confident negative this test exists to remove"
    )


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c3_11_a_retired_name_with_a_live_successor_resolves_to_the_successor(registry):
    """**One fact, and it used to have four answers.** INTERFACE.md 5.10 promises that
    after a merge *"the old word still resolves"*. [Observed] that promise was kept by
    accident: a merge writes the old name into the survivor's `aliases`, and the shipped
    `DeterministicResolver` happens to score an exact alias 1.0, clearing
    `existing_threshold`. Nothing in the registry -- and nothing in the `Resolver`
    protocol -- required it.

    So the identical situation gave four different answers:

    | | via `merge_types` | via `retire(successor=)` |
    |---|---|---|
    | shipped resolver | `existing` | `proposal` |
    | a resolver that does not alias-match | `proposal` | `proposal` |

    `retire(successor=)` writes no alias, and PACKAGE.md 2.6 calls a caller-supplied
    resolver **the production path** -- so the promise held in exactly one of the four
    cells. It is now the registry's answer, not the resolver's, down both lifecycle
    paths. Added by row 3c after an adversarial review round drove all four.

    Note what stays true: the retired name is **not reusable** (5.9). `propose_type` on
    it still returns the tombstone. Resolving *through* it to a live successor and
    *reusing* it are different acts, and only the first is allowed.
    """
    for name, definition in (("capture", "a captured watch"), ("archive_link", "an archived link")):
        seed(registry, name, definition=definition)

    registry.retire("capture", "superseded", retired_by="user:sd", successor="archive_link")

    resolution = registry.resolve_type("capture", ResolveContext(), tier="opus")
    assert resolution.outcome == "existing", "the old word resolves (5.10)"
    assert resolution.type is not None and resolution.type.name == "archive_link"
    assert resolution.type.status == "active", "to the LIVE successor, never the tombstone"
    assert "successor" in resolution.reason
    assert ("capture", None) in resolution.alternatives, "and the dead name is still named"

    # ...and it is still not reusable. Resolving through a name is not reusing it.
    answer = registry.propose_type("capture", "something else", [], "user:pm")
    assert answer.status == "retired" and "name_previously_retired" in answer.warnings
