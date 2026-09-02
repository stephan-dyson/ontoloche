"""C4 -- ``propose_type`` (14). Mechanism 1: no review.

The call that makes an addition a *request* rather than a fact. It refuses exactly two
things and warns about everything else -- refusing a near-duplicate is how you flatten a
capability predicate.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from .._resolve import same_word
from ..policy import NamespacePolicy
from ..types import CREATED_BY, Citation, Evidence, Proposal, Refusal, ResolveContext, TypeEntry
from ._support import DOC_EVIDENCE_URL, seed
from .doubles import DegradedAdapter

DATA_EVIDENCE = Evidence(
    kind="data",
    summary="14,627 distinct CCNs over 419,479 rows; CCN->name is 1:1",
    locator="NH_HealthCitations_Aug2026.csv",
)


def test_c4_01_an_empty_definition_is_refused(registry):
    with pytest.raises(ValueError):
        registry.propose_type("facility", "", [DATA_EVIDENCE], "user:sd")
    with pytest.raises(ValueError):
        registry.propose_type("facility", "   ", [DATA_EVIDENCE], "user:sd")


@pytest.mark.requires_capability("stores_proposals")
def test_c4_02_an_ai_proposer_without_a_tier_is_refused(registry):
    with pytest.raises(ValueError):
        registry.propose_type("facility", "a nursing home", [], "ai:proposer")
    ok = registry.propose_type("facility", "a nursing home", [], "ai:proposer", tier="opus")
    assert isinstance(ok, Proposal) and ok.tier == "opus"


def test_c4_03_a_name_already_taken_returns_the_existing_entry(registry):
    original = seed(registry, "facility", definition="a Medicare-certified nursing home")
    answer = registry.propose_type(
        "facility", "some other idea of what a facility is", [DATA_EVIDENCE], "user:pm"
    )
    assert isinstance(answer, TypeEntry), "not an error; the proposer's question is answered"
    assert answer.definition == original.definition
    assert answer.status == "active"


@pytest.mark.requires_capability("stores_proposals")
def test_c4_04_a_near_duplicate_warns_and_does_not_refuse(registry):
    """The kill-row protection: refusing here is how a locally-correct new predicate
    gets folded into an existing one instead of being created."""
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    proposal = registry.propose_type(
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


@pytest.mark.requires_capability("stores_proposals")
def test_c4_05_no_evidence_warns_and_the_proposal_is_still_created(registry):
    proposal = registry.propose_type("facility", "a nursing home", [], "user:sd")
    assert isinstance(proposal, Proposal)
    assert "no_evidence" in proposal.warnings, "an honest empty beats a fabricated citation"
    assert proposal.evidence == ()


@pytest.mark.resolver_dependent
def test_c4_06_a_domain_semantic_without_an_external_doc_is_unverified(registry):
    asserting = registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L. Higher letters are LESS serious.",
        [DATA_EVIDENCE],
        "ai:proposer",
        kind="value_set",
        tier="haiku",
    )
    assert "unverified_semantics" in asserting.warnings
    assert "no_evidence" not in asserting.warnings, "there IS evidence; it is just not a citation"

    cited = registry.propose_type(
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


def test_c4_07_auto_approval_is_legible_never_blank(adapter, make_registry):
    registry = make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    entry = registry.propose_type("blocks", "this work item blocks that one", [], "ai:classifier", tier="haiku")
    assert isinstance(entry, TypeEntry)
    assert entry.status == "active"
    assert entry.provenance.approved_by == "auto:classifier"
    assert entry.provenance.approved_by is not None, (
        "a blank field invites a reader to assume a human signed off"
    )


@pytest.mark.requires_capability("indexes_membership")
def test_c4_08_a_retired_name_is_not_silently_reusable(registry, adapter):
    # `capture` is seeded because `retire` now refuses a successor that names no entry
    # (`successor_unregistered`, row 4d round 1). The subject is untouched.
    seed(registry, "capture", definition="the word that replaced it")
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    answer = registry.propose_type("watch", "something else entirely", [DATA_EVIDENCE], "user:pm")
    assert isinstance(answer, TypeEntry)
    assert answer.status == "retired"
    assert "name_previously_retired" in answer.warnings
    assert adapter.get_type("default", "watch").status == "retired", "and no new entry"


@pytest.mark.parametrize(
    "name",
    ["Facility", "1facility", "facility-name", "facility name", "", "f" * 65, "_facility"],
)
def test_c4_09_the_name_rule_is_enforced_identically_on_every_backend(registry, name):
    with pytest.raises(ValueError):
        registry.propose_type(name, "a definition", [DATA_EVIDENCE], "user:sd")


def test_c4_10_created_by_derived_is_reachable_and_distinct(registry):
    """**Ruling R17, row 3e -- the fourth `created_by`, and the first change to that
    vocabulary since it was taken from Tenshen's `work_link_types`.**

    `derived` means *produced by a deterministic rule, with no human and no model in the
    loop*. Two unrelated fixtures reached for the same missing value and that is why
    this one of EDGES.md 14's vocabulary questions was taken:

    * beacon's `EntityMention.match` carries exactly this three-way distinction and its
      first value is literally `deterministic`;
    * UC3's BBL join relates a tree to a service request by a rule over a shared key,
      and before R17 it had to claim `created_by="user"` -- a person deciding something
      no person touched -- or hide the truth in a `created_by_actor` convention that
      nothing validates.

    The other three still land where they landed. `import:` stays `seed` **on purpose**:
    an import is a vocabulary arriving already decided (INTERFACE.md 2.5), where
    `derived` is a decision a rule made just now, and collapsing them loses which of the
    two happened.
    """
    cases = {
        "derived:socrata_bbl_join": "derived",
        "ai:classifier": "ai",
        "seed": "seed",
        "user:sd": "user",
    }
    for actor, expected in cases.items():
        entry = seed(
            registry,
            f"thing_from_{expected}",
            definition=f"a type whose origin is {expected}",
            proposed_by=actor,
            tier="opus" if actor.startswith("ai:") else None,
        )
        assert entry.created_by == expected, f"{actor!r} -> {entry.created_by!r}"

    assert set(CREATED_BY) == {"seed", "ai", "user", "derived"}


@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
def test_c4_11_declaring_a_predicate_whose_identity_moved_is_warned(adapter, make_registry):
    """**Ruling R55, row 4d — the write door says which identity a declaration landed in.**

    `propose_type` never validated its `predicates` list against anything. A type
    declaring a predicate that had been **absorbed** — merged away, retired with a live
    successor, or held as somebody else's alias — was legal, **silent**, and
    indistinguishable at the door from a type declaring the survivor.

    Ruling **R54**, one commit earlier, makes such a declaration *visible*: the
    survivor's extent holds it and `predicates(of=…)` counts it. This makes it
    **announced**, at the door, to the caller who can still act on it. Same fact, the
    other end of the same seam, and it is cheap.

    **It is a warning and never a refusal**, and that is §5.4's own rule rather than a
    concession: this call refuses two things and warns about everything else, *because
    refusing a near-duplicate is how you flatten a capability predicate*. Declaring a
    predicate under a word that still resolves is **correct** behaviour — §5.10 promises
    the old word still resolves — so the proposal is created, the declaration stands, and
    the registry says which identity it landed in.

    Both halves are asserted, and the negative is the one a careless fix breaks: a
    declaration of a live, unmerged predicate carries **nothing**.
    """
    registry = make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable", "untouched"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])

    merged = registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert hasattr(merged, "aliases_added"), merged

    moved = registry.propose_type(
        "memo",
        "a short internal note",
        [Evidence(kind="data", summary="a sample")],
        "user:sd",
        predicates=["commentable"],
    )
    assert "declared_predicate_merged:commentable:searchable" in moved.warnings, (
        "`commentable` is not an identity of its own any more; the declarer is writing "
        "into `searchable` and had no way to know"
    )
    assert moved.predicates == ("commentable",), (
        "the declaration STANDS -- 5.10 promises the old word still resolves, and "
        "refusing a declaration is how you flatten a capability predicate (5.4)"
    )

    # **The negative.** A live, unmerged predicate carries nothing: a signal that never
    # turns off is noise, which is row 4c's own `predicate_requires_review` lesson.
    plain = registry.propose_type(
        "card",
        "a card",
        [Evidence(kind="data", summary="a sample")],
        "user:sd",
        predicates=["untouched"],
    )
    assert not [w for w in plain.warnings if w.startswith("declared_predicate_merged")]

    # ...and so does a predicate that names no row at all. A dangling declaration is a
    # fact rather than an error, and nothing about it has MOVED.
    dangling = registry.propose_type(
        "leaflet",
        "a leaflet",
        [Evidence(kind="data", summary="a sample")],
        "user:sd",
        predicates=["nobody_registered_this"],
    )
    assert not [
        w for w in dangling.warnings if w.startswith("declared_predicate_merged")
    ]


@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_proposals")
def test_c4_12_a_word_is_re_checked_at_the_write_and_a_partial_look_says_so(
    adapter, make_registry
):
    """**Two halves of one guard, both found by row 4d's first adversarial round.**

    **(a) The word was free when the proposal was made and may not be when it is
    written.** `propose_type` asks `_alias_holder`; `_write_approved` writes the row —
    sometimes days later — and re-checked nothing. **Ruling R40 forces every
    `kind="predicate"` down that two-step path**, so the guard was structurally
    unavailable for the one kind the kill row is about, and R40's own human-review window
    is exactly the window in which the check goes stale.

    **(b) A look that did not finish has not said the word is free.** The collision scan
    read `_active_page` and discarded the sentence saying the backend had capped the
    query, so a truncated look read as *"free"*. **Rule U's third operand — *partial is
    not equal*, the FIFTH trip — missing from a guard the SIXTH trip's own commit
    shipped.**

    **And (b) is a WARNING rather than a refusal, which is the finding inside the
    finding.** The first fix refused, and `C3-13` — whose whole subject is a backend that
    caps an unlimited query — went red: refusing there does not *narrow* the guard, it
    **bans `propose_type` on every paging backend**, at exactly the scale UC3 describes.
    `C10-09`'s lesson, one call along. So the fact is reported rather than suppressed,
    which is §5.4's own rule.
    """
    registry = make_registry(adapter)  # manual review: there IS a window
    seed(registry, "searchable", kind="predicate", definition="a capability")
    seed(registry, "aaa_note", predicates=["searchable"])

    pending = registry.propose_type(
        "commentable", "a capability", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(pending, Proposal), (
        "R40: a predicate proposal is PENDING, whatever the policy says"
    )

    # ...and now, while it waits for a human, the word is spoken for.
    registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentable"], "status": "active"}],
        namespace="default", kind="predicate",
    )

    approved = registry.approve(pending.id, "user:sd")
    assert isinstance(approved, Refusal), (
        "approving now would leave two live entries holding one word -- 5.9b, and the "
        "guard `propose_type` ran is a guard about a world that has moved"
    )
    assert approved.reason == "alias_collision"
    assert approved.detail["overridable"] is False

    # --- (b) the partial look ------------------------------------------------
    for i in range(8):
        seed(registry, f"filler_{i}", definition="a filler")
    capped = make_registry(DegradedAdapter(adapter, page_cap=3))
    out = capped.propose_type(
        "another_word", "a capability", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert not isinstance(out, Refusal), (
        "refusing here does not narrow the guard, it BANS the call on every paging "
        "backend -- C10-09's lesson, and C3-13's own subject"
    )
    assert any(w.startswith("alias_check_incomplete:") for w in out.warnings), (
        "the scan read a page the backend had already said was partial; reporting that "
        "is Rule U, and swallowing it is how a truncated look reads as `free`"
    )


@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
def test_c4_13_two_legal_names_that_are_one_word_cannot_both_go_live(adapter, make_registry):
    """**Mechanism 4 with no alias, no merge and no retirement.** Row 4d, round 2.

    `NAME_RE` is `^[a-z][a-z0-9_]{0,63}$`, so `commentable` and `commentable_`, and
    `bike_lane` and `bike__lane`, are all legal **names** that `identity_key` maps to one
    word — and the shipped resolver therefore scores each pair at **1.0**. Round 1
    published that key and re-keyed the alias guards; `_alias_holder` still compared the
    incoming word only against other rows' **aliases**, never against their **names**,
    and skipped a *different* same-kind row as *"that's me"* because its self-test was
    keyed too.

    So two ordinary `propose_type` + `approve` calls created two ACTIVE predicates over
    extents `merge_types` refuses to unify non-overridably, and `resolve_type` answered
    one of them at 1.0. **UC3 is dozens of agencies normalising their own column
    headers**: `"Borough"` → `borough` and `"Borough:"` → `borough_` is the ordinary
    case.

    All three write doors are asserted, and so is the narrowing that a careless fix
    breaks: `PACKAGE.md` §4.1 **blesses** one word under two kinds, and that must stay
    legal.
    """
    registry = make_registry(adapter, approval_policy="auto")
    seed(registry, "commentable", kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable"])

    refused = registry.propose_type(
        "commentable_", "a capability", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(refused, Refusal), (
        "`commentable_` and `commentable` are one word to the resolver, which scores the "
        "pair 1.0 -- two live rows under it is mechanism 4 itself"
    )
    assert refused.reason == "alias_collision"
    assert refused.detail["overridable"] is False
    assert refused.detail["held_by"] == "commentable"

    seed(registry, "bike_lane", kind="predicate", definition="a capability")
    again = registry.import_types(
        [{"name": "bike__lane", "kind": "predicate", "definition": "a capability",
          "status": "active"}],
        namespace="default", kind="predicate",
    )[0]
    assert "import_refused:alias_collision" in again.warnings, (
        f"`bike__lane` and `bike_lane` are one word; the sibling write door must give "
        f"the same answer to the same act: {again.warnings}"
    )

    # **The narrowing.** PACKAGE.md 4.1 blesses one word under two kinds, and C0-11 pins
    # that `get_type` raises there -- so the guard is per-KIND and must stay so.
    both_kinds = registry.propose_type(
        "commentable", "a different thing entirely",
        [Evidence(kind="data", summary="a sample")], "user:sd", kind="entity",
    )
    assert not isinstance(both_kinds, Refusal), (
        "one word under two KINDS is blessed by PACKAGE.md 4.1; refusing it would make "
        "this row reject vocabularies the specification permits"
    )


@pytest.mark.requires_capability("stores_aliases", "indexes_membership")
def test_c4_14_a_word_the_key_cannot_read_is_not_the_same_word(adapter, make_registry):
    """**The identity function was manufacturing mechanism 4.** Row 4d, round 3.

    `identity_key` collapses every run of non-`[a-z0-9]`, so **every word with no ASCII
    alphanumerics maps to the empty string** — and `difflib` rates two empty strings a
    perfect **1.0**. That failed in both directions at once:

    * a **false 1.0** — an alias ``状态`` ("status") made `resolve_type("类型")` ("type"),
      a *different* word, answer that entry at the confidence §5.3 calls a guarantee,
      over a pair `merge_types` refuses non-overridably;
    * a **false refusal** — the second agency's legitimate ``类型`` was then declined
      `alias_collision`, the registry insisting two unrelated Chinese words are one.

    UC3's catalogue is multi-agency and its labels are not all Latin; UC2's CMS export
    has punctuation-only and blank headers. **An empty key is not a word**, and never
    equal to anything — Rule U on the identity of the NAME: *we cannot say what word this
    is* is not *it is the same word*.
    """
    registry = make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable"])
    seed(registry, "doc", predicates=["searchable"])

    held = registry.import_types(
        [{"name": "commentable", "kind": "predicate", "definition": "a capability",
          "aliases": ["\u72b6\u6001"], "status": "active"}],
        namespace="default", kind="predicate",
    )[0]
    assert "\u72b6\u6001" in (held.aliases or ()), held.warnings

    # (a) no false 1.0: a DIFFERENT word does not answer that entry.
    other = registry.resolve_type("\u7c7b\u578b", ResolveContext(), tier="opus")
    assert not (other.type is not None and other.confidence == 1.0), (
        f"'\u7c7b\u578b' is not '\u72b6\u6001'; two words the key cannot read are not "
        f"one word: {other.outcome} {other.type.name if other.type else None}"
    )

    # (b) no false refusal: the second agency's own label is accepted.
    second = registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["\u7c7b\u578b"], "status": "active"}],
        namespace="default", kind="predicate",
    )[0]
    assert not any(w.startswith("import_refused:") for w in second.warnings), (
        f"refusing this insists two unrelated words are one -- mechanism 4 manufactured "
        f"by the function that exists to prevent it: {second.warnings}"
    )

    # ...and a word the key CAN read still matches across spellings.
    assert same_word("B\u00fcrgeramt", "b\u00fcrgeramt")
    assert not same_word("---", "!!!")


def _tombstone_holding(registry, word="zzz_moved"):
    """A RETIRED predicate that still answers to ``word``, and nothing named ``word``.

    The kill row's FOURTEENTH trip's fixture: four ordinary, permitted calls, the last
    of which is a retirement with **no successor**. §5.8 keeps the tombstone's words.
    """
    seed(registry, "alpha", kind="predicate", definition="a capability")
    seed(registry, "aaa_note", predicates=["alpha"])
    written = registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": [word],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or word not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")
    assert word in (gone.aliases or ()), (
        "INTERFACE.md 5.8 -- a tombstone keeps its words by design", gone.aliases
    )
    return gone


@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
def test_c4_15_a_word_a_tombstone_answers_to_is_not_free_at_propose_type(
    adapter, make_registry
):
    """THE KILL ROW'S FOURTEENTH TRIP, at the first mint door.

    Row 6c, round 3 — standing rule (c) applied where the register had been applying it
    to `name` alone. §5.8 keeps a tombstone's words **by design**, so a retired row's
    `name` and its `aliases` are both an **unconsumed permission**. The EIGHTH trip
    closed the retired half of the NAME door (`_word_rows`, `C10-19`); the retired half
    of the ALIAS door was asked by nothing, because `_alias_holder` and `_alias_clash`
    both read active rows only — by design, since `alias_collision` is about two LIVE
    entries.

    **[Observed, five ordinary calls, no merge, no `force` on the mint, no
    acknowledgement, with `check_merge_guard.py` exiting 0]** the tombstone's alias was
    minted as a brand-new row's name **with no warning at all** — and the store then
    refused **both** `merge_types` (`predicate_merge`) and `reinstate`
    (`alias_collision`) NON-OVERRIDABLY. **The registry itself says the state is one
    call from two active rows on one word, with the tombstone permanently
    un-reinstatable** — which is the governance act ruling **R11** created `reinstate`
    to provide. The guard was at the wrong end: it blocked the row that wants its word
    back, not the call that took it.

    **Provenance by BISECT** (standing rule (a)): live at `ddf2f5e` and at `664d3a5^`,
    so it **predates row 6c entirely**; R75 did not introduce it but **widened its blast
    radius** from one tombstone to every successor in a retirement chain.
    """
    registry = make_registry(adapter)
    tombstone = _tombstone_holding(registry)

    # CONTROL -- the tombstone's own NAME has been answered this way since trip 8.
    control = registry.propose_type(
        "alpha", "a second alpha", [DATA_EVIDENCE], "user:sd", kind="predicate"
    )
    assert isinstance(control, TypeEntry) and "name_previously_retired" in control.warnings

    out = registry.propose_type(
        "zzz_moved", "a brand new thing", [DATA_EVIDENCE], "user:sd", kind="predicate"
    )
    assert isinstance(out, TypeEntry), (
        "the caller is owed the holder at the door they knocked on, not a proposal", out
    )
    assert out.name == tombstone.name, out.name
    assert f"word_previously_retired:{tombstone.name}" in out.warnings, out.warnings
    assert not [
        t for t in registry.list_types("predicate", include_retired=True).types
        if t.name == "zzz_moved"
    ], "nothing is written"

    # ...and the whole point: the tombstone can still be brought back.
    back = registry.reinstate("alpha", "we were wrong", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry), (
        "R11's governance act must still be available", back
    )
