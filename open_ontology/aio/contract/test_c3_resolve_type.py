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

@pytest.mark.requires_capability("indexes_membership")
async def test_c3_10_a_retired_name_is_named_in_the_resolution_not_silently_omitted(registry):
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
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    resolution = await registry.resolve_type(
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
async def test_c3_11_a_retired_name_with_a_live_successor_resolves_to_the_successor(registry):
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
        await seed(registry, name, definition=definition)

    await registry.retire("capture", "superseded", retired_by="user:sd", successor="archive_link")

    resolution = await registry.resolve_type("capture", ResolveContext(), tier="opus")
    assert resolution.outcome == "existing", "the old word resolves (5.10)"
    assert resolution.type is not None and resolution.type.name == "archive_link"
    assert resolution.type.status == "active", "to the LIVE successor, never the tombstone"
    assert "successor" in resolution.reason
    assert ("capture", None) in resolution.alternatives, "and the dead name is still named"

    # ...and it is still not reusable. Resolving through a name is not reusing it.
    answer = await registry.propose_type("capture", "something else", [], "user:pm")
    assert answer.status == "retired" and "name_previously_retired" in answer.warnings

async def test_c3_12_a_word_taken_in_another_namespace_is_found_when_the_caller_asks(registry):
    """**Ruling R6, row 3e -- UC3's W1.3, the finding the kill-criterion row rests on.**

    docs/findings/3C-VALIDATION.md W1.3, reproduced verbatim: the Department of Parks
    registers ``status``; the 311 team asks for ``status`` in its own namespace and is
    told *"nothing in the vocabulary fits 'status'"* with an **empty** ``alternatives``.
    The same context asked in ``dpr`` returns ``existing`` at confidence 1.0. **The
    answer was decided by which namespace the caller picked before asking**, and
    scoping -- INTERFACE.md 2.6's answer to mechanism 4 -- had reintroduced mechanism 2.

    ``search_namespaces`` is the additive fix. Three things are asserted here and they
    are the whole ruling:

    1. **The default is unchanged.** ``None`` reads nothing, finds nothing, and still
       says ``complete=False``. No v0 caller changes.
    2. **A hit elsewhere is reported, and never resolved through.** The outcome stays
       ``proposal`` -- resolving across namespaces would be 2.6's answer to mechanism 4
       deleting itself -- and the taken name lands in ``alternatives`` prefixed with the
       namespace it was found in.
    3. **``complete`` is True only when the caller named every namespace that exists**,
       and when it is False the namespaces left out are named. *"We searched four of
       the six"* without saying which two is the confident partial answer Rule U
       forbids, which is the failure the empty ``alternatives`` above already was.
    """
    await seed(registry, "status", namespace="dpr", definition="the state of a parks work order")
    await seed(registry, "borough", namespace="default", definition="one of the five NYC boroughs")

    # 1. The default: exactly the v0 behaviour, and it still says it is partial.
    blind = await registry.resolve_type("status", ResolveContext(), namespace="oti_311", tier="opus")
    assert blind.outcome == "proposal"
    assert blind.alternatives == (), "the finding, reproduced: the word looks free"
    assert blind.complete is False and blind.searched_namespaces == ()
    assert "oti_311" in blind.why_incomplete

    # 2. Naming one namespace finds the word -- and does not resolve to it.
    partial = await registry.resolve_type(
        "status", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr"],
    )
    assert partial.outcome == "proposal", "a hit elsewhere never resolves across namespaces"
    assert "dpr:status" in [name for name, _ in partial.alternatives]
    assert "TAKEN" in partial.reason and "dpr" in partial.reason
    assert partial.searched_namespaces == ("oti_311", "dpr")

    # 3. ...and the search is honest about what it did not cover.
    assert partial.complete is False, "'default' has types and was not named"
    assert "default" in partial.why_incomplete

    whole = await registry.resolve_type(
        "status", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr", "default"],
    )
    assert whole.complete is True, "every namespace that exists was named"
    assert whole.why_incomplete == ""
    assert set(whole.searched_namespaces) == {"oti_311", "dpr", "default"}
    assert "dpr:status" in [name for name, _ in whole.alternatives]
    assert whole.known == len(whole.alternatives), "Rule K"
