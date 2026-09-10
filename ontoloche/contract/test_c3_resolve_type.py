"""C3 -- ``resolve_type`` (29). Mechanism 2, with mechanism 1 as the gate.

No test here may pass or fail because of resolver *quality*: the assertions are about
outcomes and shapes, never about a score's value.
"""

from __future__ import annotations

import pytest

from .._resolve import identity_key
from ..actions import Effect, InputSpec, Precondition, action_attributes
from .doubles import DegradedAdapter
from ..types import Refusal, Resolution, ResolveContext, TypeEntry
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
    # **`capture` is seeded, then retired** (row 4d, round 1). This fixture used to name
    # a successor it never created, which `retire` now refuses `successor_unregistered`
    # -- an identity guard that cannot be EVALUATED has not said the collapse is safe.
    # The subject is unchanged and sharper: a retired name whose successor is not LIVE is
    # still named in the resolution rather than silently omitted, and the state is now
    # one a governed vocabulary can actually be in.
    seed(registry, "capture", definition="the word that replaced it")
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")
    registry.retire("capture", "and then that one went too", retired_by="user:sd")

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
    # **SUPERSEDED BY R99, 2026-09-09.** This assertion used to read
    # `stale.confidence == 1.0`, with the reason *"the redirect is a GUARANTEE (5.3).
    # Lowering it is the founder's half of Q56."* **The founder took that half** -- his
    # word was `read` -- so the id now pins the OPPOSITE, and INTERFACE.md rule 5.3.2-3
    # is struck rather than deleted for the same reason this comment exists.
    assert stale.confidence is not None and stale.confidence < 1.0, (
        "R99 took Q56's expensive half: a redirect whose identity claim went stale no "
        "longer answers at the guarantee (INTERFACE.md 5.3, rule 5.3.2-9)"
    )
    assert stale.outcome == "existing", (
        "and it is NOT a refusal -- rule 5.3.2-11. 5.10 still promises the old word "
        "resolves, so the answer is handed over with the vouching withdrawn"
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

    # **A near miss is not an identity claim (§5.3.2-5).** Nobody wrote that these two
    # words denote one thing; the scorer merely rated them alike. Re-verifying every
    # `existing` outcome would read two extents for a coincidence of spelling and would
    # attach a merge's warning to a word no merge ever touched.
    near = registry.resolve_type("commentables", ResolveContext(), tier="opus")
    if near.outcome == "existing" and near.type is not None:
        assert "identity_stale" not in near.type.warnings, (
            "the resolver scored a near miss; that is not an identity anybody claimed"
        )


@pytest.mark.requires_capability("stores_events")
def test_c3_15_a_vocabulary_curated_twice_still_resolves(registry):
    """**§5.10's promise across TWO curation passes.** Row 4d, round 2.

    `resolve_type` read **one** successor and required it to be live, so a word retired
    toward a word that was later retired again answered `proposal` — while
    `list_types(predicate=)`, `predicates(of=)` and `propose_type`'s R55 warning all said
    the identity was live. **One store, two contradictory answers about one word**, which
    `_identity_closure`'s own docstring calls *"a defect rather than a choice"*.

    Two ordinary curation passes on one word is the ordinary UC3 outcome, and §5.10
    promises *"the old word still resolves"*. The anti-mechanism-2 call was telling the
    proposer to create a new type.

    Capped and cycle-guarded, because §5.9 does not forbid constructing a cycle.
    """
    for name in ("status_bearing", "svc_status", "service_status"):
        seed(registry, name, definition="a word about status")

    # `force=True` so the subject stays reachable on a backend that cannot compute an
    # extent: the consumer guard is scaffolding here, and `C9-18` is its subject.
    first = registry.retire(
        "status_bearing", "renamed", retired_by="user:sd", successor="svc_status",
        force=True,
    )
    assert isinstance(first, TypeEntry), first
    second = registry.retire(
        "svc_status", "renamed again", retired_by="user:sd",
        successor="service_status", force=True,
    )
    assert isinstance(second, TypeEntry), second

    resolution = registry.resolve_type("status_bearing", ResolveContext(), tier="opus")
    assert resolution.outcome == "existing", (
        "5.10 promises the old word still resolves; one hop lost it on the second pass"
    )
    assert resolution.type is not None and resolution.type.name == "service_status"
    assert resolution.type.status == "active"
    assert resolution.confidence == 1.0

    # **...and a CYCLE is SURVIVED rather than refused.** Nothing in 5.9 forbids
    # constructing one -- `_identity_closure`'s own docstring says so, and this test's
    # first draft asserted a refusal that does not exist. What the walk owes is
    # termination and an honest answer: both words are retired, so neither redirects.
    for name in ("alpha", "beta"):
        seed(registry, name, definition="a word")
    assert isinstance(
        registry.retire(
            "alpha", "folded", retired_by="user:sd", successor="beta", force=True
        ),
        TypeEntry,
    )
    assert isinstance(
        registry.retire(
            "beta", "folded back", retired_by="user:sd", successor="alpha", force=True
        ),
        TypeEntry,
    )
    for word in ("alpha", "beta"):
        looped = registry.resolve_type(word, ResolveContext(), tier="opus")
        assert looped.outcome != "existing", (
            f"both words are retired, so {word!r} redirects to nothing -- and the walk "
            f"must terminate rather than follow the cycle"
        )


@pytest.mark.requires_capability("stores_events")
def test_c3_16_the_successor_walk_never_raises_and_says_when_it_stopped(registry):
    """**Two ways the guaranteed call was not honest.** Row 4d, round 3.

    **(a) It raised.** The successor lookups omitted `kind=`, and `get_type` with no kind
    **RAISES** on a word registered under two kinds — which `PACKAGE.md` §4.1 explicitly
    blesses and `C0-11` pins. `retire`'s own guard says exactly why that is wrong (*"an
    identity guard must never be the thing that blows up"*) and the lesson had not
    travelled to the resolver. Three ordinary calls, on a store the specification
    permits, threw `AmbiguousKind` out of the call designed against mechanism 2 — and a
    proposer that gets an exception finds nothing and re-proposes.

    **(b) It stopped without saying so.** Past `_IDENTITY_CHAIN_CAP` the walk gave up and
    the answer said *"nothing ACTIVE in the vocabulary fits this"* while blaming
    **namespaces** in `why_incomplete`. `_identity_closure` and `list_types` both name
    the cap. Rule U's confident negative, in the call §5.3 calls a guarantee.
    """
    for name in ("commentable", "searchable"):
        seed(registry, name, definition="a word")
    registry.retire(
        "commentable", "renamed", retired_by="user:sd", successor="searchable", force=True
    )
    assert registry.resolve_type(
        "commentable", ResolveContext(), kind="entity", tier="opus"
    ).type.name == "searchable"

    # PACKAGE.md 4.1 blesses one word under two kinds; C0-11 pins that `get_type` raises.
    seed(registry, "searchable", kind="value_set", definition="a different thing")
    resolution = registry.resolve_type(
        "commentable", ResolveContext(), kind="entity", tier="opus"
    )
    assert resolution.type is not None and resolution.type.name == "searchable", (
        "the caller passed `kind=` and did everything right; a store 4.1 permits must "
        "not throw out of the call designed against mechanism 2"
    )

    # (b) the cap is named, in the answer and in `why_incomplete`.
    names = [f"pp{i:02d}" for i in range(20)]
    for name in names:
        seed(registry, name, definition="a word")
    for here, nxt in zip(names, names[1:]):
        assert isinstance(
            registry.retire(here, "chain", retired_by="user:sd", successor=nxt, force=True),
            TypeEntry,
        )
    capped = registry.resolve_type("pp00", ResolveContext(), tier="opus")
    assert "longer than" in capped.reason and "hops" in capped.reason, (
        f"the walk stopped before it found a live row and must say so: {capped.reason}"
    )
    assert "hops" in capped.why_incomplete


def test_c3_17_a_tombstone_elsewhere_is_found_by_the_words_it_answers_to(
    adapter, make_registry
):
    """**Finding X1, row 6d round 1 (ruling R90).** The cross-namespace read was built out
    of **none** of the identity machinery.

    `_search_namespaces` is the only guard in this package that reads more than one
    namespace, and it tested `rec.status == "retired" and rec.name == candidate` — the
    row's **name only**. So a word a live tombstone in another namespace still answers to
    **as an alias** was invisible, and invisible under a **`complete=True` seal**: Rule
    U's confident negative in the very call ruling **R6** exists to prevent, whose own
    words are *"scoping without lookup reintroduces mechanism 2"*.

    §5.8 keeps a tombstone's words **by design** and standing rule (c) calls them an
    *unconsumed permission*. This is that rule at the one read that crosses a namespace.
    """
    registry = make_registry(adapter, approval_policy="auto")
    seed(registry, "boroname", namespace="dpr", definition="the borough of a park")
    written = registry.import_types(
        [{"name": "boroname", "status": "active", "aliases": ["boro_nm"],
          "definition": "the borough of a park"}],
        namespace="dpr", kind="entity",
    )
    if not written or "boro_nm" not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = registry.retire(
        "boroname", "consolidated", retired_by="user:sd", namespace="dpr", force=True
    )
    # NOT REACHABLE, never a pass. `retire`'s `if force and not self.caps.stores_events`
    # (`registry.py:3969`) refuses a destructive override that cannot be written down, so
    # on such a store this fixture cannot be built at all. **Gated on the CAPABILITY**, so
    # a store that CAN record events and still refused this way is a finding, not a skip.
    #
    # Narrowed to the ONE reason the capability explains, on the four-file precedent. With
    # `force=True` and no `successor` it is the only refusal `retire` can reach -- 9 of its
    # 12 are gated behind `successor is not None` and the other 2 behind `not force`. The
    # bare form this line used to carry told a backend refusing for an unrelated reason,
    # while recording events perfectly well, that it had failed: `C19-100`'s defect.
    if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
        assert registry.caps.stores_events is False, (
            "this backend records events, so the refusal is not a capability", gone.detail,
        )
        pytest.skip(
            "NOT REACHABLE: stores_events=False refuses the forced retire before there "
            "is a tombstone for the other namespace to find"
        )
    assert not isinstance(gone, Refusal), (
        "the fixture's forced retire refused for a reason no capability explains", gone,
    )

    # CONTROL: the tombstone's own NAME has been surfaced since row 3e.
    by_name = registry.resolve_type(
        "boroname", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr"],
    )
    assert "RETIRED" in by_name.reason, by_name.reason

    # ...and a word the SAME tombstone answers to must be surfaced too.
    by_alias = registry.resolve_type(
        "boro_nm", ResolveContext(), namespace="oti_311", tier="opus",
        search_namespaces=["dpr"],
    )
    assert "RETIRED" in by_alias.reason, (
        "a tombstone's aliases are an unconsumed permission -- 5.8 keeps them by design",
        by_alias.reason,
    )


def test_c3_18_the_cross_namespace_read_compares_words_not_bytes(adapter, make_registry):
    """**Finding X2, row 6d round 1 (ruling R90).** One word is not one string — at the
    one read that crosses a namespace, which had never been told.

    `_word_rows`, `_alias_holder` and `_alias_clash` have compared by `identity_key` since
    the **SEVENTH** trip. `_search_namespaces` compared **bytes**, so `dpr:bike__lane` was
    a near miss to a `dot` caller asking for `bike_lane` rather than the loud *already
    taken* the byte-exact case gets — and `NAME_RE` admits `foo__bar`, so this is UC3's
    ordinary case rather than a contrivance.
    """
    registry = make_registry(adapter, approval_policy="auto")
    seed(registry, "bike__lane", namespace="dpr", definition="a cycle route")

    out = registry.resolve_type(
        "bike_lane", ResolveContext(), namespace="dot", tier="opus",
        search_namespaces=["dpr"],
    )
    assert "TAKEN" in out.reason and "dpr" in out.reason, (
        "a variant spelling is the same WORD and R6 owes the caller that word",
        out.reason,
    )


def test_c3_19_every_alternative_label_names_a_row(adapter, make_registry):
    """**Finding X7, row 6d round 2.** A confident POSITIVE about a row nobody holds.

    Until this row keyed the cross-namespace probe, `exact_elsewhere` fired only on a
    **byte-exact** match — so the candidate WAS the row's name and `f"{other}:{candidate}"`
    named a real row. **Keying the probe widened the producer and left this consumer
    alone**, so `alternatives` carried `('dpr:bike_lane', None)` for a store holding only
    `dpr:bike__lane`, under a **`complete=True` seal**.

    It broke three shipped rules at once: §5.3.1 rule 3 (`<namespace>:<name>`, and the
    `<name>` named nothing); rule 5 (`None` means *nothing scored it*, while that row had
    been scored at **1.0** two entries above); and rule 5's note that a taken word is
    listed **once**, *"because listing it twice would double-count Rule K's `known`"* —
    `known` counted 3 for 2 rows.

    **In the call ruling R6 added to end confident NEGATIVES.** The general form is the
    assertion this id makes and the suite never made: `grep` the 25 `alternatives`
    mentions in this file and **not one** resolved a returned label back to a row.
    """
    registry = make_registry(adapter, approval_policy="auto")
    seed(registry, "bike__lane", namespace="dpr", definition="a cycle route")
    seed(registry, "park", namespace="dpr", definition="a green space")
    seed(registry, "roadway", namespace="dot", definition="a carriageway")

    out = registry.resolve_type(
        "bike_lane", ResolveContext(), namespace="dot", tier="opus",
        search_namespaces=["dpr"],
    )
    assert out.alternatives, out
    for label, _score in out.alternatives:
        namespace, _, name = label.rpartition(":")
        if not namespace:
            namespace = "dot"          # a home-namespace alternative is bare
        found = [
            t
            for t in registry.list_types(
                namespace=namespace, include_retired=True
            ).types
            if t.name == name
        ]
        assert found, (
            "every alternative label must name a ROW -- 5.3.1 rule 3", label,
            out.alternatives,
        )
    assert out.known == len(out.alternatives), ("Rule K", out.known, out.alternatives)
    assert len({label for label, _ in out.alternatives}) == len(out.alternatives), (
        "a taken word is listed once, or `known` double-counts it", out.alternatives
    )


# ============================================================ R99, row 6f: Q56's
# expensive half. INTERFACE.md rules 5.3.2-9 to 5.3.2-13. Founder ruling R99,
# 2026-09-09, his word `read`: the claim is verified where it is MADE, and this call
# may act on what the verification found.


def _stale_predicate_store(registry):
    """A LEGAL join, then ordinary vocabulary growth. Door 1's own walk.

    Returns nothing; the store is left with `commentable` retired toward `searchable`,
    written extents `{note}` and `{doc, note}`, and no governance act in between.
    """
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])
    retired = registry.retire(
        "commentable", "superseded", retired_by="user:sd", successor="searchable"
    )
    assert isinstance(retired, TypeEntry), retired
    seed(registry, "doc", predicates=["searchable"])


@pytest.mark.requires_capability("indexes_membership")
def test_c3_20_the_stale_confidence_is_derived_from_the_extents_not_chosen(registry):
    """**Rule 5.3.2-9.** The number is `min(resolver_score, Jaccard(L, R))`.

    **This id exists to make a CONSTANT fail.** Row 6f pre-registered, before the
    resolver was opened, that the confidence *"must be computed from a quantity this
    call already reads"* and that *"replacing the derivation with a constant must make
    at least one contract id fail"* -- because row 4d's third round found two rule rows
    that could be deleted with the whole suite green. So this test drives **two stores
    whose Jaccard differs** and asserts each answer equals the value computed from the
    extents the test reads back itself. Any constant fails one of them, and a
    containment ratio fails the first.
    """
    _stale_predicate_store(registry)

    stale = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    left, _, _ = registry._written_extent("default", "commentable", include_retired=True)
    right, _, _ = registry._written_extent("default", "searchable", include_retired=True)
    lset, rset = set(left), set(right)
    expected = len(lset & rset) / len(lset | rset)
    assert stale.confidence == pytest.approx(expected), (
        f"5.3.2-9: the confidence is the extents' own Jaccard, not a chosen number. "
        f"L={sorted(lset)} R={sorted(rset)} -> {expected}, got {stale.confidence}"
    )
    assert expected == pytest.approx(0.5), (
        "the fixture's own arithmetic, stated so a silent fixture change is visible"
    )
    # **Containment would score this 1.0 and hide it** -- `{note}` is a subset of
    # `{doc, note}`. 5.3.2's own note refuses containment for the warning in those
    # words, and this line is why the same objection binds the score.
    assert stale.confidence < 1.0, "containment would have answered 1.0 here"

    # A SECOND store with a different cardinality, so no single constant passes both.
    for name in ("taggable", "labelable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "post", predicates=["taggable", "labelable"])
    assert isinstance(
        registry.retire("taggable", "superseded", retired_by="user:sd", successor="labelable"),
        TypeEntry,
    )
    for extra in ("page", "clip", "reel"):
        seed(registry, extra, predicates=["labelable"])
    second = registry.resolve_type("taggable", ResolveContext(), tier="opus")
    l2, _, _ = registry._written_extent("default", "taggable", include_retired=True)
    r2, _, _ = registry._written_extent("default", "labelable", include_retired=True)
    expected2 = len(set(l2) & set(r2)) / len(set(l2) | set(r2))
    assert second.confidence == pytest.approx(expected2)
    assert expected2 != pytest.approx(expected), (
        "the two stores must disagree, or a constant passes this test"
    )


@pytest.mark.requires_capability("stores_attributes", "indexes_membership")
def test_c3_21_an_action_familys_identity_is_verified_by_its_declaration(registry):
    """**Rule 5.3.2-10.** `kind="action"` has no extent, so its own operand is used.

    This is the governance register's entry **A3** at the read: `resolve_type` answered
    the dead word with the survivor at **1.0** while `preflight` answered it with the
    tombstone's policy, and a Haiku-tier actor recorded `applied`. Statement `E` at
    `kind="action"`, and the 4d gate could not see it -- it requires BOTH sides to be
    `kind="predicate"`.

    **A3 is NOT closed by this id.** Its write doors still let the collapse through on
    a key they do not compare; this pins only that the READ stops delivering a clean
    1.0 over it.

    > **AMENDED by row 6g, founder ruling R102 (`Q99` ruled `all eight`).** This id's
    > fixture was two families agreeing on the four compared governance keys and
    > differing on `inputs` and `preconditions`, and it asserted that **the write doors
    > PERMIT that collapse** -- *"that is the point of the fixture, and it is Q99's
    > subject."* **R102 ruled `all eight` and the write doors now REFUSE it**, so the
    > fixture asserts something that can no longer happen. The superseded assertion is
    > kept in a comment below rather than deleted, for the same reason rule 5.3.2-3 is
    > struck rather than removed.
    >
    > **The replacement fixture is the ONE shape on which the two sides still part
    > company, and choosing it is the point.** R102 §2 dissolved the read/write
    > asymmetry on contradictions -- both sides now take all eight keys. What it
    > deliberately did **not** decide is **absence**: a key present on one side and
    > absent on the other. The read treats that as *not agreeing* and scores below 1.0
    > (5.3.2-10). The write does **not** read it as a contradiction on the four keys
    > R102 added, because R102 §4 leaves it unruled and row 6g took the least-refusing
    > option (`C19-106`). **So this id keeps asserting exactly what it always asserted --
    > a pair the write door permits, redirecting below 1.0 at the read -- on the only
    > operand for which that sentence is still true.**
    >
    > **AND THIS ID WILL MOVE AGAIN, which is written here so the next move does not read
    > as drift.** Per-key absence is the subject of **`Q101`**, minted by the supervisor
    > on 2026-09-09 out of row 6g's finding that the write door reads an absence as
    > agreement in one case and as a contradiction in the other, with nobody having
    > decided either. **This fixture therefore pins the very thing the founder is about
    > to rule on**, and his ruling gets to change it.
    """
    common = dict(
        approval_mode="auto",
        min_auto_tier="haiku",
        reversibility="reversible",
        effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
    )
    # SUPERSEDED FIXTURE, row 6d..6f (kept, not deleted): `new_verb` declared `inputs`
    # and a `preconditions` guardrail the absorbed family did not, and this id asserted
    #     assert isinstance(retired, TypeEntry), (
    #         "the four governance keys AGREE, so the write doors permit this collapse "
    #         "-- that is the point of the fixture, and it is Q99's subject")
    # **R102 ruled `all eight` and that collapse is now REFUSED `action_declarations_
    # diverge`, non-overridably, at all three doors** (`C19-104`). The assertion above
    # cannot hold and is not weakened to fit -- the fixture moves to the operand that
    # still has the property the id is about.
    survivor = action_attributes(reachability=("mcp",), **common)
    absorbed = dict(survivor)
    # **A per-key ABSENCE, and it is the whole fixture.** `ACTIONS.md` 2.2 makes
    # `reachability` required, so leaving it out is not "declaring nothing" -- this
    # family declares, and is silent on one key. The write door does not read that as a
    # contradiction (R102 4 leaves absence unruled; `C19-106`), and the read does not
    # read it as agreement (*unknowable is not equal*).
    absorbed.pop("reachability")
    seed(registry, "old_verb", kind="action", attributes=absorbed)
    seed(registry, "new_verb", kind="action", attributes=survivor)
    retired = registry.retire(
        "old_verb", "superseded", retired_by="user:sd", successor="new_verb"
    )
    assert isinstance(retired, TypeEntry), (
        f"an ABSENT key is not a key declared differently, so the write door still "
        f"permits this collapse -- R102 4 leaves absence unruled and C19-106 pins the "
        f"least-refusing answer: {retired}"
    )

    answer = registry.resolve_type("old_verb", ResolveContext(), tier="haiku")
    assert answer.outcome == "existing" and answer.type is not None
    assert answer.type.name == "new_verb", "5.10 still promises the old word resolves"
    assert answer.confidence is not None and answer.confidence < 1.0, (
        "A3's delivery step: a machine actor must not receive a CLEAN 1.0 over two "
        "families whose declarations do not agree (rule 5.3.2-10)"
    )
    assert "identity_stale" in answer.type.warnings, (
        "the SAME value, not a minted variant -- it names the same fact, and R71's "
        "precedent is that a value gains carriers rather than growing a twin"
    )

    # **The control, and it is the half a careless fix breaks:** two families whose
    # declarations agree are NOT stale, and still answer at 1.0.
    seed(registry, "alpha_verb", kind="action", attributes=action_attributes(**common))
    seed(registry, "beta_verb", kind="action", attributes=action_attributes(**common))
    assert isinstance(
        registry.retire(
            "alpha_verb", "superseded", retired_by="user:sd", successor="beta_verb"
        ),
        TypeEntry,
    )
    agreeing = registry.resolve_type("alpha_verb", ResolveContext(), tier="haiku")
    assert agreeing.confidence == 1.0, (
        "identical declarations are not a stale identity; a warning here is a signal "
        "that never turns off"
    )
    assert agreeing.type is not None
    assert "identity_stale" not in agreeing.type.warnings


@pytest.mark.requires_capability("indexes_membership")
def test_c3_22_a_stale_redirect_is_never_a_refusal(registry):
    """**Rule 5.3.2-11.** R99 authorised refusing. This call does not, and here is why.

    In every state reachable by ordinary calls the registry **can** name the correct
    answer -- 5.10 promises the old word still resolves -- so refusing would withhold a
    correct answer. Refusing on an *unknowable* read would additionally ban this door on
    a legal declared-degraded backend, which is `C10-09`'s, `C3-13`'s and `C12-13`'s
    lesson three times over.

    **The id exists so that a later row cannot quietly turn the score into a refusal**
    without a founder ruling saying so.
    """
    _stale_predicate_store(registry)
    answer = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert not isinstance(answer, Refusal), "5.3 returns a Resolution; it has no refusal"
    assert answer.outcome == "existing", (
        "R99 permits refusing and row 6f declines to -- the answer is handed over with "
        "the vouching withdrawn, not withheld"
    )
    assert answer.type is not None and answer.type.name == "searchable"


@pytest.mark.requires_capability("indexes_membership", "stores_events")
def test_c3_23_min_confidence_governs_the_redirect_path(registry):
    """**Rule 5.3.2-12.** The CALLER's bar decides, and until row 6f it could not.

    **[Observed, row 6f]** the exact-hit redirect returned at `registry.py:1705`,
    *before* the `min_confidence` test at `1707`, so `min_confidence=2.0` still answered
    `existing` at 1.0. That was invisible while the redirect always answered 1.0 and
    goes live the moment 5.3.2-9 lowers it: a score no bar can act on is decoration.

    Honouring the bar here is **5.3's own stated rule** -- *"Below `min_confidence`,
    return `none` with `alternatives` populated. Never return the best of a bad set as
    `existing`"* -- applied to the one path that returned before reaching it.
    """
    _stale_predicate_store(registry)

    baseline = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    scored = baseline.confidence
    assert scored is not None and scored < 1.0

    # **A caller that set no bar is untouched.** This is the v0-caller line: R99 costs
    # a caller who never asked for anything exactly nothing.
    default = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert default.outcome == "existing", "min_confidence defaults to 0.0 -- no change"

    at_bar = registry.resolve_type(
        "commentable", ResolveContext(), tier="opus", min_confidence=scored
    )
    assert at_bar.outcome == "existing", "the bar is a floor, not a strict inequality"

    above = registry.resolve_type(
        "commentable", ResolveContext(), tier="opus", min_confidence=1.0
    )
    assert above.outcome == "none", (
        "5.3: never return the best of a bad set as `existing` -- and this path used to"
    )
    assert above.type is None
    assert any(label == "searchable" for label, _ in above.alternatives), (
        "the survivor is still NAMED. Rule 5.3.2-11 refuses nothing, so a caller that "
        "wants it anyway can take it out of `alternatives`"
    )
    _assert_rule_k(above, "the successor path, below the bar")

    # **The ALIAS path below the bar, and it is here because the first cut of this id
    # drove only the successor path -- so the defect two reviewers found lived on the
    # branch no new test reached.** A merge writes the alias, and a variant spelling
    # reaches the survivor through the near-miss list, whose first entry is the winner
    # itself. Appending the survivor there listed one word twice.
    for name in ("taggable", "labelable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "post", predicates=["taggable", "labelable"])
    merged = registry.merge_types(
        "taggable", "labelable", "same capability", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    seed(registry, "clip", predicates=["labelable"])

    for spelling in ("taggable", "Taggable", "TAGGABLE"):
        under = registry.resolve_type(
            spelling, ResolveContext(), tier="opus", min_confidence=1.0
        )
        _assert_rule_k(under, f"the alias path below the bar, spelled {spelling!r}")


def _assert_rule_k(resolution, where: str) -> None:
    """Rule K, asserted on a path this row added. `C3-19`'s sentence, at a new door.

    One word names one row, so it is listed ONCE -- otherwise `known` counts a single
    taken word twice, and a caller reading `alternatives` gets two different confidences
    for the same name and cannot tell which this call stands behind.
    """
    labels = [label for label, _ in resolution.alternatives]
    assert len(labels) == len(set(labels)), (
        f"a taken word is listed once, or `known` double-counts it ({where}): "
        f"{resolution.alternatives}"
    )
    assert resolution.known == len(resolution.alternatives), (
        f"Rule K ({where}): known={resolution.known} vs "
        f"{len(resolution.alternatives)} alternatives"
    )


# ---------------------------------------------------------------- ROUND 1's SURVIVORS
# Four mutations of rules 5.3.2-9, -10 and -12 passed the entire C3+C10 suite. Each id
# below exists because of one of them, and each names the mutation it kills. An id that
# does not kill a mutation of its own rule is decoration -- row 4d proved that by
# deleting two rule rows with the suite green.


@pytest.mark.requires_capability("stores_attributes", "indexes_membership")
def test_c3_24_a_reordered_declaration_is_the_SAME_declaration(registry):
    """**Rule 5.3.2-10, the order half.** Kills: `_unordered` returning a list.

    **This is row 6d's round-3 defect, one call along.** Its A3 fix compared `effects`
    with `!=`, so two families whose governance was IDENTICAL and whose effects were
    merely written in a different order were refused **non-overridably at all three
    doors** -- it **CLOSED A LEGAL OPERATION** for two rounds. This row's read reuses
    `effect_identity` and compares the other declared lists as sets so it cannot repeat
    that, and `ACTIONS.md` §1's non-goals say *"no ordering"* outright.

    **That protection was UNPINNED until this id.** Round 1's mutation lens reverted the
    frozenset in `_unordered` to a plain list -- making the comparison order-sensitive
    again -- and the entire C3 and C10 suite stayed green, because every fixture wrote
    its lists in the same order on both sides.
    """
    first = Effect(op="propose_type", namespace="default", kind="entity")
    second = Effect(
        op="host_state",
        why="the family also mutates state this protocol does not model",
    )
    common = dict(approval_mode="human", min_auto_tier=None, reversibility="irreversible")
    # **`reachability` is here because the first cut of this id varied only `effects`,
    # and `effects` is compared by `_effect_identities` -- a DIFFERENT helper.** Round
    # 2's record lens caught it: the id was credited with killing the `_unordered`
    # mutation and did not exercise `_unordered` at all. Worse, the row's own mutation
    # script had reported a kill, because its unanchored string replace hit BOTH helpers'
    # identical `return frozenset(out)` line and the kill belonged to the other one.
    # These two lists differ only in order and go through `_unordered`.
    reach_a = ["mcp", "http", "cli"]
    reach_b = ["cli", "mcp", "http"]

    seed(
        registry,
        "old_verb",
        kind="action",
        attributes=action_attributes(
            effects=(first, second), reachability=reach_a, **common
        ),
    )
    seed(
        registry,
        "new_verb",
        kind="action",
        # **The same declaration, written backwards.** Nothing about what either family
        # may do differs; only the order the entries were typed in. `effects` exercises
        # `_effect_identities`, `reachability` exercises `_unordered`, and BOTH have to
        # be order-blind or this pair scores apart.
        attributes=action_attributes(
            effects=(second, first), reachability=reach_b, **common
        ),
    )
    assert isinstance(
        registry.retire("old_verb", "superseded", retired_by="user:sd", successor="new_verb"),
        TypeEntry,
    )

    answer = registry.resolve_type("old_verb", ResolveContext(), tier="haiku")
    assert answer.outcome == "existing" and answer.type is not None
    assert sorted(reach_a) == sorted(reach_b) and reach_a != reach_b, (
        "the fixture must differ ONLY in order, or this id asserts nothing about ordering"
    )
    assert answer.confidence == 1.0, (
        "two identical declarations written in a different order are the SAME "
        "declaration -- ACTIONS.md 1 says 'no ordering', and scoring them apart is row "
        "6d's round-3 defect (it CLOSED A LEGAL OPERATION) repeated at the read"
    )
    assert "identity_stale" not in answer.type.warnings


@pytest.mark.requires_capability("stores_attributes", "indexes_membership")
def test_c3_25_an_UNDECLARED_action_family_is_unknowable_not_agreeing(registry):
    """**Rule 5.3.2-10, Rule U's half.** Kills: deleting `_declaration_agreement`'s guard.

    `ACTIONS.md` §2.2-1 permits a family to register with no declaration. Collapsing one
    of those into a family that declares **human approval only and irreversible** is not
    evidence the two are one thing -- it is **no evidence at all**, and the FIRST kill-row
    trip is what happens when a guard treats those as the same.

    Round 1's mutation lens deleted the `if not mine or not theirs: return (True, None)`
    guard and the suite stayed green.

    **Correction, round 2.** This docstring first said the deleted guard let the pair
    *"fall through to `(False, 1.0)`, so an undeclared family silently became FULLY
    VOUCHED."* **That value was asserted rather than traced.** Computed against this
    fixture, the real fall-through is **`(True, 0.625)`** -- five of the eight keys
    coincidentally agree, because an absent key and a default-valued one compare equal
    on several of them. The mutation IS still caught (0.625 is not the asserted `None`),
    so the kill claim holds; the mechanism behind it did not, and in a row whose whole
    discipline is that such claims are checked, an unchecked one is a finding whatever
    the verdict it supported. Caught by round 2's record lens.
    """
    seed(registry, "old_verb", kind="action", attributes={})
    seed(
        registry,
        "new_verb",
        kind="action",
        attributes=action_attributes(
            approval_mode="human",
            min_auto_tier=None,
            reversibility="irreversible",
            effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
        ),
    )
    assert isinstance(
        registry.retire("old_verb", "superseded", retired_by="user:sd", successor="new_verb"),
        TypeEntry,
    )

    answer = registry.resolve_type("old_verb", ResolveContext(), tier="haiku")
    assert answer.outcome == "existing", "5.10 still promises the old word resolves"
    assert answer.confidence is None, (
        "a family that DECLARED NOTHING is not a family that declared the same thing. "
        "Rule U: unknowable is not equal, and it is not 0.0 either"
    )
    assert answer.type is not None and "identity_stale" in answer.type.warnings


@pytest.mark.requires_capability("indexes_membership")
def test_c3_26_an_unscorable_identity_does_not_clear_a_bar(registry, adapter, make_registry):
    """**Rule 5.3.2-12, Rule U's half.** Kills: `_clears` returning True on `None`.

    A caller that asks for `min_confidence` and gets *we could not score this* has not
    been told the answer clears its bar. §5.3's rule is *"never return the best of a bad
    set as `existing`"*, and an unscored identity is not a good set.

    Round 1's mutation lens flipped `if scored is None: return False` to `return True`
    and the suite stayed green, because every `min_confidence` case used a concretely
    SCORED pair and every unscorable case used no bar. The two halves were each covered
    and their INTERSECTION -- the only place the branch lives -- was not.
    """
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])
    assert isinstance(
        registry.retire(
            "commentable", "superseded", retired_by="user:sd", successor="searchable"
        ),
        TypeEntry,
    )
    seed(registry, "doc", predicates=["searchable"])

    # Joined on a CAPABLE backend, then read through one that cannot compute an extent.
    # That is not exotic: it is one deployment reading another's store, which is
    # `PACKAGE.md` 2.6's production path.
    blind = make_registry(
        DegradedAdapter(adapter, indexes_membership=False), approval_policy="auto"
    )
    unscored = blind.resolve_type("commentable", ResolveContext(), tier="opus")
    # **This ASSERTS where it used to SKIP, and the distinction is the finding.** The
    # first cut read `if unscored.confidence is not None: pytest.skip(...)` -- a skip
    # decided by **the value this id exists to assert**. An ENVIRONMENT skip says *this
    # configuration cannot pose the question* and is legitimate; a RESULT skip says *the
    # answer was not the one I was going to assert* and dresses it as coverage. This
    # backend declines `indexes_membership` by construction, so the question is always
    # posed and no configuration makes skipping honest.
    #
    # Third occurrence of the shape in this project: row 4d found it in `C3-14`, row 6f
    # round 1 found it in `C10-16`, and row 6f then wrote it into this id in the same
    # round it graded the finding. Rule **5.3.2-15** is what it should have pinned.
    assert unscored.confidence is None, (
        f"rule 5.3.2-15: a read that could not compute either extent answers `None` -- "
        f"Rule U at the confidence field, not 0.0 and not a refusal. Got "
        f"{unscored.confidence!r}"
    )
    assert unscored.outcome == "existing", "with NO bar, an unscorable answer still answers"

    barred = blind.resolve_type(
        "commentable", ResolveContext(), tier="opus", min_confidence=0.1
    )
    assert barred.outcome == "none", (
        "the caller asked for 0.1 and the registry cannot say whether the identity "
        "holds at all -- Rule U: 'we could not score this' is not 'this cleared 0.1'"
    )


class _FixedScoreResolver:
    """A resolver that rates an exact alias at a FIXED score below 1.0.

    `PACKAGE.md` 2.6's **production path**: a deployment supplying its own resolver.
    5.3's own `C3-11` rationale is that *"a promise kept only because the shipped scorer
    happens to rate an exact name 1.0 is a promise a deployment supplying its own
    resolver does not get"* -- and this class is that deployment.
    """

    def __init__(self, value: float) -> None:
        self.value = value

    def score(self, candidate, context, known, *, tier):
        out = []
        for record in known:
            words = [getattr(record, "name", "")] + list(getattr(record, "aliases", ()) or ())
            if any(identity_key(w) == identity_key(candidate) for w in words):
                out.append((record.name, self.value))
        return out

    def classify(self, candidate, context, *, tier):
        return None


@pytest.mark.requires_capability("indexes_membership", "stores_aliases", "stores_events")
def test_c3_27_the_confidence_is_the_MIN_of_both_halves(adapter, make_registry):
    """**Rule 5.3.2-14.** The composition is `min`, and BOTH halves are load-bearing.

    **This id replaces one built on a false premise, and the replacement is the finding.**
    Round 1 could not kill a mutation of `_compose` to `agreement` alone, instrumented the
    call, saw the resolver's score was `1.0` every time, and concluded the `min` was
    *unreachable by construction* -- tagging rule 5.3.2-9 `prose-only:`. **A round-2 lens
    disproved it by building a legal custom resolver.** Re-measured across a range, the
    composition is reached for scores **0.9 through 1.0**; the original instrumentation had
    tested ONE score, found no call, and generalised from a single data point.

    So the `min` is observable, and observing it needs the **agreement to exceed the
    score** -- which the round-1 fixtures never arranged, because a two-member extent gives
    `J = 0.5` and every score that reaches the branch is above it. Twenty shared members
    and one latecomer give `J = 20/21`, above a `0.94` resolver, and then the SCORE is the
    weaker half and `min` must take it.
    """
    registry = make_registry(
        adapter, resolver=_FixedScoreResolver(0.94), approval_policy="auto"
    )
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    for i in range(20):
        seed(registry, f"shared{i:02d}", predicates=["commentable", "searchable"])
    merged = registry.merge_types(
        "commentable", "searchable", "same capability", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    seed(registry, "latecomer", predicates=["searchable"])

    left, _, _ = registry._written_extent("default", "commentable", include_retired=True)
    right, _, _ = registry._written_extent("default", "searchable", include_retired=True)
    lset, rset = set(left), set(right)
    agreement = len(lset & rset) / len(lset | rset)
    assert agreement > 0.94, (
        f"the fixture must put the AGREEMENT ABOVE the score or the `min` is invisible "
        f"-- that is exactly why round 1 could not see it. J={agreement}"
    )

    answer = registry.resolve_type("Commentable", ResolveContext(), tier="opus")
    if answer.type is None or answer.type.name != "searchable":
        pytest.skip("this leg does not reach the alias redirect for a variant spelling")
    assert answer.confidence == pytest.approx(0.94), (
        f"5.3.2-14: the resolver's score is the WEAKER half here, so `min` takes it. "
        f"Returning the agreement alone would answer {agreement} and vouch for more than "
        f"this deployment's resolver did. Got {answer.confidence!r}"
    )
    assert answer.confidence < agreement, "and it must be strictly the lower of the two"


@pytest.mark.requires_capability("indexes_membership")
def test_c3_28_an_unknowable_read_answers_None_not_zero(registry, adapter, make_registry):
    """**Rule 5.3.2-15.** The cell where 5.3.2-9's formula has no input.

    A read that could not compute either extent cannot produce a Jaccard, so it produces
    **`None`** -- 5.3's own *"`None` means 'did not score', NOT zero."* Scoring it `0.0`
    would assert the two words share no members, the FIRST trip's operand pointing the
    other way; refusing would ban the door on a legal degraded backend (5.3.2-11).

    **This rule existed only in prose until round 2**, found by a supervisor spec-read
    after four lenses on the implementation missed it: 5.3.2-9 defined the confidence as a
    formula over the extents and said nothing about the state where there are none, so the
    one cell with no input was the one cell with no rule -- and `C3-26`, the id that
    touched it, skipped on the value instead of asserting it.
    """
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])
    assert isinstance(
        registry.retire(
            "commentable", "superseded", retired_by="user:sd", successor="searchable"
        ),
        TypeEntry,
    )
    seed(registry, "doc", predicates=["searchable"])

    scored = registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert scored.confidence is not None and scored.confidence < 1.0, (
        "the capable leg must SCORE this pair, or the contrast below asserts nothing"
    )

    blind = make_registry(
        DegradedAdapter(adapter, indexes_membership=False), approval_policy="auto"
    )
    unknowable = blind.resolve_type("commentable", ResolveContext(), tier="opus")
    assert unknowable.outcome == "existing", "5.10 still promises the old word resolves"
    assert unknowable.confidence is None, (
        f"5.3.2-15: not 0.0, not a number, not a refusal -- {unknowable.confidence!r}"
    )
    assert unknowable.type is not None
    assert "identity_stale" in unknowable.type.warnings

    # **The property 5.3.2-15 states rather than leaves emergent:** ONE store, two
    # readers, two different confidences for one identity claim. This confidence measures
    # what THIS READER could establish, not the identity alone.
    assert scored.confidence != unknowable.confidence


@pytest.mark.requires_capability("stores_attributes", "indexes_membership")
def test_c3_29_a_key_declared_EMPTY_is_not_a_key_never_declared(registry):
    """**Rule 5.3.2-16.** `E`'s FAMILY, found by round 2 in this row's own operand.

    Not statement `E`
    itself -- `E` is a WRITE-time fact treated as true at READ time. This is a comparison defect, and what
    it belongs to is 5.3's own named family: *a confident answer standing in for a fact the system had or
    could not have*.

    `ACTIONS.md` 2.2: *"an empty list is a positive declaration -- this host exposes me on
    no named surface -- not a forgotten field."* The first cut of the action operand
    derived its key set from the union of the two stored dicts and compared
    `mine.get(key)` against `theirs.get(key)`, so a family positively declaring
    `reachability=[]` and one that never declared the key **both flattened to the same
    empty set** and the pair answered a **clean 1.0 with no warning** -- the exact harm
    this row exists to remove, reached through the operand it added to remove it.

    It survived four lenses in round 1 because `action_attributes()` always writes all
    eight keys, so no fixture in the suite could construct the absence at all.
    """
    declared = action_attributes(
        approval_mode="auto",
        min_auto_tier="haiku",
        reversibility="reversible",
        effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
        reachability=["mcp"],
    )
    says_none = dict(declared, reachability=[])   # positively declares NO surface
    never_said = {k: v for k, v in declared.items() if k != "reachability"}
    assert "reachability" in says_none and "reachability" not in never_said

    seed(registry, "old_verb", kind="action", attributes=says_none)
    seed(registry, "new_verb", kind="action", attributes=never_said)

    holds, agreement = registry._identity_agreement(
        "default",
        registry._require("default", "old_verb"),
        registry._require("default", "new_verb"),
    )
    assert holds is True and agreement is not None and agreement < 1.0, (
        f"5.3.2-16: declaring a key EMPTY is not the same as never declaring it, and "
        f"scoring them equal is a clean 1.0 over two families that differ. "
        f"Got holds={holds!r} agreement={agreement!r}"
    )

    # **The other half of 5.3.2-16, and it is what makes the key set FIXED rather than
    # discovered.** A key absent from BOTH sides is a fact the two families share --
    # neither declared it -- so it counts toward agreement out of the full eight. Deriving
    # the denominator from whatever happens to be stored makes the SAME divergence score
    # differently depending on unrelated absent keys, which is a measurement that moves
    # when nothing about the identity moved.
    pair = action_attributes(
        approval_mode="auto",
        min_auto_tier="haiku",
        reversibility="reversible",
        effects=(Effect(op="propose_type", namespace="default", kind="entity"),),
        reachability=["mcp"],
    )
    both_omit = {k: v for k, v in pair.items() if k != "payload_schema"}
    left_side = dict(both_omit, min_auto_tier="haiku")
    right_side = dict(both_omit, min_auto_tier="opus")   # exactly ONE key differs
    seed(registry, "alpha_verb", kind="action", attributes=left_side)
    seed(registry, "beta_verb", kind="action", attributes=right_side)
    _, shared_absent = registry._identity_agreement(
        "default",
        registry._require("default", "alpha_verb"),
        registry._require("default", "beta_verb"),
    )
    assert shared_absent == pytest.approx(7 / 8), (
        f"seven of ACTIONS.md 2.2's EIGHT keys agree -- `payload_schema` is absent from "
        f"both, which is agreement, and only `min_auto_tier` differs. Deriving the key "
        f"set from the stored rows would score this {6 / 7:.4f} over seven keys instead. "
        f"Got {shared_absent!r}"
    )

    out = registry.retire(
        "old_verb", "superseded", retired_by="user:sd", successor="new_verb"
    )
    if isinstance(out, Refusal):
        pytest.skip(f"the write door refuses this pair on this leg: {out.reason}")
    answer = registry.resolve_type("old_verb", ResolveContext(), tier="haiku")
    assert answer.confidence is not None and answer.confidence < 1.0, (
        "and the read must not hand a machine actor a CLEAN 1.0 over it"
    )
    assert answer.type is not None and "identity_stale" in answer.type.warnings
