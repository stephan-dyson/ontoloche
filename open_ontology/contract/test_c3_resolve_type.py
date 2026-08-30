"""C3 -- ``resolve_type`` (14). Mechanism 2, with mechanism 1 as the gate.

No test here may pass or fail because of resolver *quality*: the assertions are about
outcomes and shapes, never about a score's value.
"""

from __future__ import annotations

import pytest

from ..types import Resolution, ResolveContext, TypeEntry
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


def test_c3_04_confidence_is_none_when_no_scorer_ran_and_none_is_not_zero(
    adapter, make_registry
):
    """The subject is an EMPTY vocabulary, so this one builds one.

    A version-4 store ships `default:edge:equivalent_to` seeded (EDGES.md 3.1), and a
    scorer with something to score against returns a float -- `resolve_type("facility")`
    scored 0.2857 against it. That is correct behaviour and it is not what this test is
    about: `confidence is None` means *nothing scored this*, and the only way to reach
    it is a vocabulary with nothing in it. `seed_equivalent_to=False` is the honest way
    to say so, rather than asserting `is None or is a float`.
    """
    registry = make_registry(adapter, seed_equivalent_to=False)
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


def test_c3_12_a_word_taken_in_another_namespace_is_found_when_the_caller_asks(
    registry, adapter
):
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
    seed(registry, "status", namespace="dpr", definition="the state of a parks work order")
    seed(registry, "borough", namespace="default", definition="one of the five NYC boroughs")

    # 1. The default: exactly the v0 behaviour, and it still says it is partial.
    blind = registry.resolve_type("status", ResolveContext(), namespace="oti_311", tier="opus")
    assert blind.outcome == "proposal"
    assert blind.alternatives == (), "the finding, reproduced: the word looks free"
    assert blind.complete is False and blind.searched_namespaces == ()
    assert "oti_311" in blind.why_incomplete

    # 2. Naming one namespace finds the word -- and does not resolve to it.
    partial = registry.resolve_type(
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

    whole = registry.resolve_type(
        "status", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr", "default"],
    )
    assert set(whole.searched_namespaces) == {"oti_311", "dpr", "default"}
    assert "dpr:status" in [name for name, _ in whole.alternatives]
    assert whole.known == len(whole.alternatives), "Rule K"
    if adapter.capabilities().stores_proposals:
        assert whole.complete is True, "every namespace that exists was named"
        assert whole.why_incomplete == ""
    else:
        # **`alternatives` is fed from TWO stores** (§5.5's prior rejections come from
        # `find_proposals`), so on a backend that has no proposal table the list can
        # never be whole -- which is UC1 Tenshen's own declared shape. This branch is
        # the finding rather than a concession: [Observed, row 3e second adversarial
        # round] the first cut computed `complete` from the type store alone and
        # returned `complete=True, why_incomplete=""` on `sqlite_minimal` next to a
        # `reason` saying rejections had been omitted -- and *this test asserted it*,
        # so the suite pinned the contradiction.
        assert whole.complete is False
        assert "REJECTIONS" in whole.why_incomplete

    # 4. **`kind=` narrows the SCORING and must not hide the collision.** UC3's own
    # shape: DPR publishes `status` as a `value_set`, the 311 team asks for `status` as
    # an `entity`. The first cut passed `kind=` into the cross-namespace probe, so the
    # taken word vanished and `complete=True` sealed the answer -- contortion 8's own
    # sentence, now stamped as a whole search, which is worse than what R6 replaced.
    # Uniqueness is per `(namespace, kind)` (§2.1), so the other entry is not the same
    # entry; it is the same WORD, and that is what R6 owes the caller. Row 3e, round 1.
    seed(registry, "permit", namespace="dob", kind="value_set",
         definition="the DOB permit states")
    kinded = registry.resolve_type(
        "permit", ResolveContext(), namespace="oti_311", tier="opus",
        kind="entity", search_namespaces=["dob", "dpr", "default"],
    )
    assert ("dob:permit", None) in kinded.alternatives, (
        "a name taken under ANOTHER kind is still a name that is taken -- and its "
        "score is None, never 0.0, because nothing scored it (§5.3.1 rule 5, Rule U). "
        "C3-11 pins the same thing for the in-namespace case; the cross-namespace one "
        "is what rule 5 exists for and it was checked by name alone until row 3e's "
        "second adversarial round mutated it to 0.0 and ran both suites green"
    )
    assert "TAKEN" in kinded.reason

    # 5. **A namespace whose only type is RETIRED still counts as a namespace.**
    # Retirement burns the name permanently (§5.9); a namespace somebody published into
    # and then emptied is still a place we did not look, and calling the search complete
    # without it is a claim about it. Row 3e, round 1 -- a mutation that dropped
    # `include_retired` from the census ran the whole suite green.
    seed(registry, "old_word", namespace="archive", definition="a word nobody uses now")
    registry.retire("old_word", "no longer published", retired_by="user:sd",
                    namespace="archive")
    without = registry.resolve_type(
        "status", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr", "default", "dob"],
    )
    assert without.complete is False, "'archive' holds only a retired type and was omitted"
    assert "archive" in without.why_incomplete
    named = registry.resolve_type(
        "status", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr", "default", "dob", "archive"],
    )
    assert named.complete is adapter.capabilities().stores_proposals

    # 6. **A word RETIRED in a searched namespace is LISTED, not merely counted.** The
    # census reads retired rows to decide which namespaces exist; the first cut then
    # threw the records away, so a burned word came back invisible under `complete`.
    # [Observed, row 3e third adversarial round] deleting that branch ran the whole
    # suite green -- the fix was made in round 2 and asserted by nothing.
    seen_burned = registry.resolve_type(
        "old_word", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["archive"],
    )
    burned = adapter.get_type("archive", "old_word", kind="entity")
    if burned is not None and burned.status == "retired":
        assert ("archive:old_word", None) in seen_burned.alternatives, (
            "the tombstone is listed the same way both sides of the namespace boundary,"
            " with a None score because nothing scored it"
        )
        assert "RETIRED" in seen_burned.reason
    else:
        # A backend that cannot compute an extent refuses the retirement itself
        # (`C9-07`), so there is no tombstone here to list -- the word is simply active.
        assert "archive:old_word" in [n for n, _ in seen_burned.alternatives]

    # 7. **And a word REJECTED in a searched namespace.** §5.5 calls a retained
    # rejection the cheapest record of *we already decided against this word*; it is
    # exactly as useful one namespace along. Same story: fixed in round 2, asserted by
    # nothing until a mutation deleted it and the suite stayed green.
    if adapter.capabilities().stores_proposals:
        spurned = registry.propose_type(
            "footway", "a DOB footway, proposed and then declined", [], "user:dob",
            namespace="dob",
        )
        if not isinstance(spurned, TypeEntry):
            registry.reject(spurned.id, "user:dob", "we do not publish this")
            seen_rejected = registry.resolve_type(
                "footway", ResolveContext(), namespace="oti_311", tier="opus",
                search_namespaces=["dob"],
            )
            assert "dob:footway" in [n for n, _ in seen_rejected.alternatives], (
                "a rejection elsewhere is a decision the second publisher should see"
            )


def test_c3_13_a_truncated_page_cannot_support_a_completeness_claim(adapter, make_registry):
    """**Rule U, in the one call that gained a `complete=True` to get wrong.**

    `TypePage` carries `complete` / `why_incomplete` / `next_after` precisely so a
    backend may cap an unlimited query and *say so* (PACKAGE.md 3.3), and `_extent`
    already honours it. `resolve_type`'s cross-namespace search did not: it read the
    records off the page and reported `complete=True` over rows the backend had told it
    were missing. Harmless while `Resolution.complete` was hard-wired `False`; not
    harmless once ruling R6 made it a claim.

    [Observed, row 3e first adversarial round] with five types in `dpr` and a backend
    capping at two, the exact match was row four and was never reached -- and the answer
    came back `complete=True, why_incomplete=""`.
    """
    from .doubles import DegradedAdapter

    capped = make_registry(DegradedAdapter(adapter, page_cap=2))
    for name in ("alpha", "beta", "gamma", "status", "delta"):
        seed(capped, name, namespace="dpr", definition=f"the {name} of a work order")

    resolution = capped.resolve_type(
        "statuses", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr"],
    )
    assert resolution.complete is False, (
        "the backend said its page was partial; a completeness claim over it is a lie"
    )
    assert resolution.why_incomplete, "and Rule U wants the reason, not just the flag"
    assert "cap" in resolution.why_incomplete

    # **The other store `alternatives` is fed from.** §5.5's prior rejections come from
    # `find_proposals`, and ruling R6's completeness verdict was computed from the type
    # store alone -- so a backend that cannot store proposals at all returned
    # `complete=True` next to a `reason` saying rejections had been omitted from the
    # very list it had just called whole. [Observed, row 3e second adversarial round]
    # on `sqlite_minimal`, a reference leg and UC1's own declared shape.
    no_proposals = make_registry(DegradedAdapter(adapter, stores_proposals=False))
    seed(no_proposals, "borough", namespace="dpr", definition="one of the five boroughs")
    blind = no_proposals.resolve_type(
        "agency", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr"],
    )
    assert blind.complete is False, (
        "rejections could not be searched, so the list cannot be called whole"
    )
    assert "REJECTIONS" in blind.why_incomplete

    # **§5.3.1 rule 7: a completeness claim without its scope line is not a claim.**
    with pytest.raises(ValueError):
        Resolution(outcome="none", reason="", tier="opus", complete=True)


def test_c3_14_a_redirect_whose_identity_claim_went_stale_says_so(registry):
    """**The Q56 default, row 4d -- an identity claim is re-verified where it is MADE.**

    Every identity guard in this registry compares predicate extents at the moment an
    identity is **written** -- `merge_types`, `retire(successor=)`, `import_types`,
    `reinstate`, `propose_type`. This call grants confidence **1.0** at the moment it is
    **read**, and `INTERFACE.md` 5.3 calls that a guarantee. Between the two, the
    vocabulary moves: a row is created under the aliased word, a `status` flips, an
    extent grows, an alias is transferred by a later merge.

    That is `ROADMAP.md`'s kill row's **sixth trip**, and it is the first that is
    *different in kind*. Trips 1-5 were all *the guard did not look properly* -- at an
    unknowable extent, at an empty one, at all, through a different field, at a partial
    page. This one is **the guard looked correctly, and then the fact changed**; the
    claim was TRUE WHEN IT WAS MADE. **Rule U's fourth operand: unknowable is not equal,
    empty is not equal, partial is not equal, and STALE is not equal.**

    **Both halves are asserted, and the second is the one a careless fix breaks.** A
    still-agreeing pair carries **no** warning: a signal that never turns off is noise,
    which is exactly what row 4c's first adversarial round found `predicate_requires_
    review` had become when it rode onto every approved predicate and stayed.

    **The confidence is untouched at 1.0 on purpose.** Refusing to answer, or answering
    below 1.0, changes what this registry declines to serve under 5.3's shipped
    guarantee -- that half of **Q56** is the founder's and is open.
    """
    if not registry.caps.indexes_membership:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend cannot compute an extent, so it cannot tell "
            "an agreeing pair from a stale one. `C9-08` and `C10-11` hold the Rule U "
            "reading -- an extent that could not be computed is not an identical extent "
            "-- and `check_merge_guard.py`'s stale axis asserts the same thing at the "
            "read on three degraded doubles"
        )
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])

    retired = registry.retire(
        "commentable", "superseded", retired_by="user:sd", successor="searchable"
    )
    assert isinstance(retired, TypeEntry), (
        f"the extents are non-empty and identical, so this retirement is LEGAL and must "
        f"stay legal -- the identity guards are narrowed, not banned (C10-09): {retired}"
    )

    # The claim, while it is still true.
    agreeing = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert agreeing.outcome == "existing"
    assert agreeing.type is not None and agreeing.type.name == "searchable"
    assert agreeing.confidence == 1.0
    assert "identity_stale" not in agreeing.type.warnings, (
        "the two extents still agree; a warning here is a signal that never turns off"
    )

    # **And then the fact changes -- with no governance act at all.** Somebody adds a
    # type. `searchable` now has a member `commentable` does not, and the identity
    # claim written above is no longer one this registry would write today.
    seed(registry, "doc", predicates=["searchable"])

    stale = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert stale.outcome == "existing", "5.10 promises the old word still resolves"
    assert stale.type is not None and stale.type.name == "searchable"
    assert stale.confidence == 1.0, (
        "the redirect is a GUARANTEE (5.3). Lowering it is the founder's half of Q56"
    )
    assert "identity_stale" in stale.type.warnings, (
        "the two predicate extents this 1.0 stands on no longer agree, and the answer "
        "said nothing about it -- the kill row's sixth trip, at the read"
    )
    assert "STALE" in stale.reason, "Rule U wants the reason, not only the flag"

    # **A non-predicate redirect pays nothing** -- no extent is read and no claim about
    # members was ever made, so there is nothing that can have gone stale.
    for name in ("capture", "archive_link"):
        seed(registry, name, definition=f"a {name}")
    registry.retire("capture", "superseded", retired_by="user:sd", successor="archive_link")
    plain = registry.resolve_type("capture", ResolveContext(), tier="opus")
    assert plain.outcome == "existing" and plain.type is not None
    assert "identity_stale" not in plain.type.warnings
