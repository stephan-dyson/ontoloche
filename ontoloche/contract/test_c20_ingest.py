"""C20 -- the mapping layer, read side (INGEST.md 1, 2, 3, 5, 6 and 7). Row 7b.

**Every id is one numbered rule of INGEST.md's tables.** Section 4 (the propose-at-ingest
contract, `C20-27`..`C20-34`, `C20-69`..`C20-72`, `C20-81`) is row 7c's, and its ids stay
planned: `check_spec_drift.py` fails the day one of them is claimed here without the
section moving to the implemented set.

**The host owns the rows** (ruling R78). Every test that needs instances makes the suite
the host through `_support.host_instances`: a table created on the store's own
connection and bound with `HostInstanceTable`, which the adapter only ever reads.

**Finding 1 (E22) is why eight of these are shaped the way they are.** Row 7a's round 2
obliged its fixes to ship checks that go red for `C20-01`, `C20-04`, `C20-05`, `C20-08`,
`C20-18`, `C20-25`, `C20-58` and `C20-63` (rule 2-12), and none was run. Each of the
eight below names the mutation that turns it red, and
`docs/tools/ingest_mutation_sweep.py` applies every one of them and requires the red.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

from ..adapter import CandidatePage, CandidateQuery, Capabilities, InstanceRecord, StorageAdapter
from ..ingest import (
    CONDITION_COMBINATORS,
    CONDITION_OPERATORS,
    CONDITION_TERMS,
    INSTANCE_CHAIN_CAP,
    INSTANCE_CONDITION_KEY,
    INSTANCE_OUTCOMES,
    MATCH_POLICY_KEY,
    CandidateRef,
    InstanceContext,
    InstanceLookup,
    InstanceResolution,
    condition_from_mapping,
    condition_problem,
    evaluate,
    match_policy_problem,
    norm,
    similar,
)
from ..registry import Registry
from ..types import Consumer, Refusal, ResolveContext, TypeEntry
from ._support import host_instances, seed, snapshot
from .doubles import DegradedAdapter

NEEDS_ATTRIBUTES = pytest.mark.requires_capability("stores_attributes")
#: A retired type is SCAFFOLDING in the closure tests: `retire` with a successor asks
#: for consumer evidence (`indexes_membership`), and a backend that declines it is
#: conformant (PACKAGE.md 3.2), so the test does not run there rather than forcing past
#: the guard it is not about.
NEEDS_RETIRE = pytest.mark.requires_capability("stores_attributes", "indexes_membership")
#: `merge_types` writes a recorded override (`stores_events`), the same way.
NEEDS_MERGE = pytest.mark.requires_capability(
    "stores_attributes", "indexes_membership", "stores_events"
)

CTX = InstanceContext(label_source="NH_HealthCitations_Aug2026.csv#Provider Name", act_id="c20")
POLICY = {"match_at": 0.97, "propose_below": 0.80, "ambiguity_margin": 0.02,
          "why": "C20: the kit's thresholds, from the 14,627-row CMS file"}
AL_ONLY = {"op": "in", "attribute": "state", "value": ["AL"],
           "why": "this deployment serves Alabama facilities only"}

#: Five real CMS facilities (NH_HealthCitations_Aug2026.csv), host ids their CCNs.
FACILITIES = (
    ("015009", "BURNS NURSING HOME, INC.", "AL"),
    ("015010", "COOSA VALLEY HEALTHCARE CENTER", "AL"),
    ("015012", "HIGHLANDS HEALTH AND REHAB", "AL"),
    ("055001", "WILLOWBROOKE CT SKILLED CARE CENTER", "CA"),
    ("065001", "MESA VISTA CARE", "CO"),
)
EXACT = "Burns Nursing Home Inc"      # 1.0 against 015009
BAND = "Burns Nursing Home"           # 0.9 against 015009: between 0.80 and 0.97
NOTHING = "zzzz qqqq unrelated"       # below 0.27 against all five


def _rows(facilities=FACILITIES, **extra):
    return [{"host_id": i, "label": label, "state": state, **extra}
            for i, label, state in facilities]


def _governed(policy=POLICY, condition=None):
    attributes = {}
    if policy is not None:
        attributes[MATCH_POLICY_KEY] = policy
    if condition is not None:
        attributes[INSTANCE_CONDITION_KEY] = condition
    return attributes or None


def _world(adapter, make_registry, rows=None, *, name="facility", namespace="default",
           policy=POLICY, condition=None, **bind):
    host_instances(adapter, _rows() if rows is None else rows, type_name=name,
                   namespace=namespace, **bind)
    registry = make_registry(adapter)
    seed(registry, name, namespace=namespace, attributes=_governed(policy, condition))
    return registry


def _resolve(registry, candidate, *, type_name="facility", tier="small", **kwargs):
    return registry.resolve_instance(candidate, CTX, type_name=type_name, tier=tier, **kwargs)


def _successor_world(adapter, make_registry, *, old_rows, new_rows, old_governed=None,
                     new_governed=None, type_column_rows=None, old="facility",
                     new="ltc_facility"):
    """`old` retired toward `new`, each bound to its own host table (or to one table
    with a type column, for the migration window rule 2-17 is about)."""
    if type_column_rows is not None:
        for name in (old, new):
            host_instances(adapter, type_column_rows, type_name=name, type_column="kind_name")
    else:
        host_instances(adapter, old_rows, type_name=old)
        host_instances(adapter, new_rows, type_name=new)
    registry = make_registry(adapter)
    seed(registry, old, attributes=old_governed or _governed())
    seed(registry, new, attributes=new_governed or _governed())
    retired = registry.retire(old, "CMS renamed the class", retired_by="user:sd",
                              successor=new)
    assert isinstance(retired, TypeEntry), retired
    return registry


def _rewrite(adapter, name, **changes):
    """Write a type row the public calls refuse to construct (a dangling successor, a
    cycle, a successor name carrying ':'). A host with write access to the store can."""
    rec = adapter.get_type("default", name, kind="entity")
    adapter.put_type(dataclasses.replace(rec, **changes))


def _all_pages(adapter, q):
    pages = []
    while True:
        page = adapter.find_instance_candidates(q)
        pages.append(page)
        if page.next_after is None:
            return pages
        q = dataclasses.replace(q, after=page.next_after)


def _q(**kw):
    return CandidateQuery(namespace="default", kind="entity", type_name="facility", **kw)


# ============================================================ section 1 -- the seam


@NEEDS_ATTRIBUTES
def test_c20_01_the_project_stores_no_instance_and_mints_no_id(adapter, make_registry):
    """Rule 1-1. **Finding 1's check:** red when ``record_ref`` mints its own id."""
    registry = _world(adapter, make_registry)
    before = snapshot(adapter)
    found = _resolve(registry, EXACT)
    proposed = _resolve(registry, NOTHING)
    lookup = registry.get_instance_checked("facility", "015009")

    assert found.outcome == "existing"
    assert found.ref.id == "015009" and found.candidates[0].ref.id == "015009"
    assert lookup.ref.id == "015009" and lookup.record.instance_id == "015009"
    assert proposed.outcome == "proposal"
    assert proposed.ref is None
    assert "id" not in {f.name for f in dataclasses.fields(CandidateRef)}
    assert snapshot(adapter) == before, "resolving instances wrote to the store"


def test_c20_02_instance_resolution_is_a_new_call_not_resolve_type(registry):
    """Rule 1-2 (R77)."""
    params = set(inspect.signature(Registry.resolve_type).parameters)
    assert not params & {"host_filter", "instance_id", "type_name"}
    assert Registry.resolve_instance is not Registry.resolve_type
    answer = registry.resolve_type(EXACT, ResolveContext(source="C20-02"), tier="small")
    assert not isinstance(answer, InstanceResolution)


def test_c20_03_no_instance_source_refuses_every_call_never_an_empty_set(registry):
    """Rule 1-3. No table is bound, so the reference backends declare the flag False."""
    assert registry.caps.resolves_instances is False
    for answer in (_resolve(registry, EXACT),
                   registry.get_instance_checked("facility", "015009")):
        assert isinstance(answer, Refusal), answer
        assert answer.reason == "instance_source_absent"
        assert answer.detail["problem"] == "capability" and answer.detail["why"]


# ============================================================ section 2 -- retrieval


def test_c20_04_the_protocol_adds_exactly_two_primitives_both_reads(adapter):
    """Rule 2-1. **Finding 1's check:** red when the protocol grows a write primitive."""
    instance_methods = sorted(n for n in dir(StorageAdapter) if "instance" in n)
    assert instance_methods == ["find_instance_candidates", "get_instance"]
    writes = [n for n in dir(StorageAdapter)
              if "instance" in n and n.split("_", 1)[0] in {"put", "delete", "write", "add",
                                                           "update", "upsert", "remove"}]
    assert writes == []
    host_instances(adapter, _rows(), type_name="facility")
    before = [r.instance_id for p in _all_pages(adapter, _q()) for r in p.records]
    adapter.get_instance("default", "entity", "facility", "015009")
    after = [r.instance_id for p in _all_pages(adapter, _q()) for r in p.records]
    assert before == after and len(after) == 5


def test_c20_05_get_instance_returns_none_for_absent_never_a_manufactured_record(
    adapter, make_registry
):
    """Rule 2-2. **Finding 1's check:** red when primitive 22 manufactures a record for
    an id its table does not hold -- on every leg, and through the registry's door."""
    host_instances(adapter, _rows(), type_name="facility")
    assert adapter.get_instance("default", "entity", "facility", "999999") is None
    present = adapter.get_instance("default", "entity", "facility", "015009")
    assert isinstance(present, InstanceRecord)
    assert present.instance_id == "015009" and present.label == "BURNS NURSING HOME, INC."
    registry = make_registry(adapter)
    seed(registry, "facility")
    absent = registry.get_instance_checked("facility", "999999")
    assert isinstance(absent, InstanceLookup), absent
    assert absent.record is None and absent.ref is None and absent.why


def test_c20_06_candidate_pages_follow_r58s_one_rule(adapter):
    """Rule 2-3."""
    host_instances(adapter, _rows(), type_name="facility", page_size=2)
    pages = _all_pages(adapter, _q())
    assert [len(p.records) for p in pages] == [2, 2, 1]
    for page in pages:
        assert page.known == len(page.records)
    # The shipped TypePage convention (PACKAGE.md 3.3): a page with more behind it is
    # complete=False WITH a cursor; the last page is complete=True with none. A
    # truncated read is the third state, complete=False with NO cursor (rule 2-4).
    assert [(p.complete, p.next_after is None) for p in pages] == [
        (False, False), (False, False), (True, True)]
    ids = [r.instance_id for p in pages for r in p.records]
    assert sorted(ids) == sorted(f[0] for f in FACILITIES) and len(set(ids)) == 5


def test_c20_07_a_truncated_read_is_distinguishable_by_the_report_alone(adapter):
    """Rule 2-4."""
    host_instances(adapter, _rows(), type_name="facility", page_size=2, scan_cap=3)
    pages = _all_pages(adapter, _q())
    last = pages[-1]
    assert sum(len(p.records) for p in pages) == 3
    assert last.complete is False and last.next_after is None and last.why_incomplete


@NEEDS_ATTRIBUTES
def test_c20_08_a_backend_that_cannot_count_says_none_never_zero(adapter, make_registry):
    """Rule 2-5. **Finding 1's check:** a double that says ``known=0`` over a non-empty
    page, and one that says ``None``, must both leave the registry unable to answer.
    Red when the registry stops reading ``known``."""
    host_instances(adapter, _rows(), type_name="facility")
    page = adapter.find_instance_candidates(_q())
    assert page.known == len(page.records) == 5

    # Round 1: the "none" case here was never seeded with a policy, so it answered
    # unknowable for the missing declaration, not for the count. The two `known=None`
    # cases (finished, and not) are the `_r1` tests below; "over" is too.
    for known in ("zero",):
        degraded = DegradedAdapter(adapter, instance_known=known)
        registry = make_registry(degraded)
        seed(registry, "facility", attributes=_governed())
        answer = _resolve(registry, EXACT)
        assert answer.outcome == "unknowable", (known, answer)
        assert answer.complete is False and answer.why_incomplete
        assert answer.confidence is None


def test_c20_09_the_adapter_scores_nothing(adapter):
    """Rule 2-6. `C0-04`'s source inspection, extended to primitives 22 and 23."""
    assert not {"score", "confidence"} & {f.name for f in dataclasses.fields(InstanceRecord)}
    assert not {"score", "confidence"} & {f.name for f in dataclasses.fields(CandidatePage)}
    for name in ("get_instance", "find_instance_candidates"):
        try:
            # The BOUND method, not `type(adapter)`'s: a forwarding proxy (the matrix's
            # `WithoutAttributeStore`) has no such class attribute, and the code that
            # answers is the backend's behind it.
            source = inspect.getsource(getattr(adapter, name))
        except (OSError, TypeError):  # pragma: no cover - a compiled third-party backend
            continue
        for word in ("difflib", "SequenceMatcher", "similar(", "norm(", ".ratio("):
            assert word not in source, f"{name} mentions {word!r}"


def test_c20_10_an_undeclared_host_filter_key_is_reported_never_ignored(adapter):
    """Rule 2-7, on the backend and on a double that declines a key the backend honours."""
    host_instances(adapter, _rows(), type_name="facility", filter_columns=("state",))
    page = adapter.find_instance_candidates(_q(host_filter={"county": "Jefferson"}))
    assert page.complete is False and page.next_after is None
    assert "county" in page.why_incomplete

    declining = DegradedAdapter(adapter, instance_filters=())
    assert declining.capabilities().instance_filters == frozenset()
    page = declining.find_instance_candidates(_q(host_filter={"state": "AL"}))
    assert page.complete is False and "state" in page.why_incomplete


def test_c20_11_label_may_order_a_page_and_never_omits_a_record(adapter):
    """Rule 2-8."""
    host_instances(adapter, _rows(), type_name="facility", page_size=2)
    for label in (None, NOTHING, EXACT):
        ids = {r.instance_id for p in _all_pages(adapter, _q(label=label)) for r in p.records}
        assert ids == {f[0] for f in FACILITIES}, label


def test_c20_12_resolves_instances_defaults_false_and_refuses_when_it_is(registry):
    """Rule 2-9."""
    field = next(f for f in dataclasses.fields(Capabilities) if f.name == "resolves_instances")
    assert field.default is False
    assert registry.caps.resolves_instances is False
    assert registry.caps.reason("resolves_instances")
    answer = _resolve(registry, NOTHING, host_filter={"state": "AL"})
    assert isinstance(answer, Refusal) and answer.reason == "instance_source_absent"


def test_c20_13_a_declared_host_filter_key_is_honoured_faithfully(adapter):
    """Rule 2-10."""
    host_instances(adapter, _rows(), type_name="facility", filter_columns=("state",))
    assert "state" in adapter.capabilities().instance_filters
    pages = _all_pages(adapter, _q(host_filter={"state": "AL"}))
    records = [r for p in pages for r in p.records]
    assert {r.attributes["state"] for r in records} == {"AL"} and len(records) == 3
    assert pages[-1].complete is True


@NEEDS_ATTRIBUTES
def test_c20_14_an_identity_read_exhausts_the_cursor(adapter, make_registry):
    """Rule 2-11. One row per page: the match is on the LAST page."""
    registry = _world(adapter, make_registry, page_size=1)
    answer = _resolve(registry, "Mesa Vista Care")
    assert answer.outcome == "existing" and answer.ref.id == "065001"
    assert answer.scanned == 5


@NEEDS_ATTRIBUTES
def test_c20_63_host_filter_is_a_mapping_of_declared_keys(adapter, make_registry):
    """Rule 2-12. **Finding 1's check:** red when a free-form expression is accepted."""
    registry = _world(adapter, make_registry, filter_columns=("state",))
    for expression in ("state = 'AL'", ("state", "AL"), ["state", "AL"]):
        with pytest.raises(TypeError, match="2-12"):
            _resolve(registry, EXACT, host_filter=expression)
    assert _resolve(registry, EXACT, host_filter={"state": "AL"}).outcome == "existing"


@NEEDS_ATTRIBUTES
def test_c20_64_a_narrowed_proposal_says_so(adapter, make_registry):
    """Rule 2-13."""
    registry = _world(adapter, make_registry, filter_columns=("state",))
    narrowed = _resolve(registry, NOTHING, host_filter={"state": "AL"})
    assert narrowed.outcome == "proposal" and narrowed.complete is True
    assert "instance_narrowed_proposal:state" in narrowed.warnings
    whole = _resolve(registry, NOTHING)
    assert whole.outcome == "proposal"
    assert not [w for w in whole.warnings if w.startswith("instance_narrowed_proposal")]


@NEEDS_ATTRIBUTES
def test_c20_65_an_unfaithful_record_is_refused_citing_the_flat_form(adapter, make_registry):
    """Rule 2-14."""
    host_instances(adapter, _rows(), type_name="facility")
    unfaithful = DegradedAdapter(adapter, instance_rename="facility#ward")
    registry = make_registry(unfaithful)
    seed(registry, "facility", attributes=_governed())
    for answer in (_resolve(registry, EXACT),
                   registry.get_instance_checked("facility", "015009")):
        assert isinstance(answer, Refusal), answer
        assert answer.reason == "instance_source_absent"
        assert answer.detail["problem"] == "unfaithful_reference"


@NEEDS_ATTRIBUTES
def test_c20_66_primitive_22_is_judged_by_the_entrys_predicate(adapter, make_registry):
    """Rule 2-15: a row the predicate fails is None with a why, and one it cannot
    decide is a refusal, never a silent pass."""
    county = {"op": "eq", "attribute": "county", "value": "Jefferson",
              "why": "a column this host does not carry"}
    host_instances(adapter, _rows(), type_name="facility")
    host_instances(adapter, _rows(), type_name="home")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed(condition=AL_ONLY))
    seed(registry, "home", attributes=_governed(condition=county))

    kept = registry.get_instance_checked("facility", "015009")
    assert kept.record is not None and kept.why == ""
    assert kept.ref.id == "015009" and kept.governed_by == "default:facility"
    excluded = registry.get_instance_checked("facility", "055001")
    assert excluded.record is None and excluded.ref is None and "predicate" in excluded.why
    refused = registry.get_instance_checked("home", "015009")
    assert isinstance(refused, Refusal), refused
    assert refused.reason == "instance_source_absent"
    assert refused.detail["problem"] == "predicate_undecidable"

    # A predicate written past validation (a host with write access to the store, or a
    # row from before the validator) is one the registry cannot decide. It refuses, the
    # way resolve_instance answers unknowable, never hands the row out as if no
    # predicate were declared. Round 0 security review: this branch failed open.
    rec = adapter.get_type("default", "facility", kind="entity")
    broken = {"op": "eq", "attribute": "state"}  # no value, no why
    adapter.put_type(dataclasses.replace(
        rec, attributes={**rec.attributes, INSTANCE_CONDITION_KEY: broken}))
    malformed = registry.get_instance_checked("facility", "015009")
    assert isinstance(malformed, Refusal), malformed
    assert malformed.reason == "instance_source_absent"
    assert malformed.detail["problem"] == "predicate_undecidable"
    assert _resolve(registry, EXACT).outcome == "unknowable"


@NEEDS_RETIRE
def test_ingest_finding_2_one_id_answers_alike_under_both_names(adapter, make_registry):
    """INGEST.md 8.1a finding 2 (E2). Not an id of its own: the construction that
    found it, kept beside rule 2-15.

    The kit called primitive 22 once, under the declared name, and judged the row with
    the declared entry's predicate. So after `facility` was retired toward
    `ltc_facility` and the host migrated its rows, one identity was ABSENT under its old
    name and present under its new one, while `resolve_instance` answered for both."""
    both = _governed(condition=AL_ONLY)
    registry = _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows(),
                                old_governed=both, new_governed=both)
    for instance_id, present in (("015009", True), ("055001", False), ("999999", False)):
        answers = [registry.get_instance_checked(name, instance_id)
                   for name in ("facility", "ltc_facility")]
        for answer in answers:
            assert isinstance(answer, InstanceLookup), answer
            assert answer.governed_by == "default:ltc_facility"
            assert (answer.record is not None) is present, (instance_id, answer)
        assert answers[0].ref == answers[1].ref
        assert answers[0].record == answers[1].record
    assert registry.get_instance_checked("facility", "015009").warnings[:1] == (
        "instance_type_succeeded:ltc_facility",)


@NEEDS_ATTRIBUTES
def test_c20_75_duplicate_ids_under_one_name_make_the_extent_uncountable(
    adapter, make_registry
):
    """Rule 2-16."""
    rows = _rows() + [{"host_id": "015010", "label": "COOSA VALLEY HEALTH", "state": "AL"}]
    registry = _world(adapter, make_registry, rows)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "2-16" in answer.why_incomplete
    assert "015010" in answer.why_incomplete


@NEEDS_RETIRE
def test_c20_89_one_row_under_two_member_names_is_one_candidate(adapter, make_registry):
    """Rule 2-17 (round 3's K2): mid-migration, one facility under both names."""
    rows = ([dict(r, kind_name="facility") for r in _rows()]
            + [dict(_rows()[0], kind_name="ltc_facility")])
    registry = _successor_world(adapter, make_registry, old_rows=None, new_rows=None,
                                type_column_rows=rows)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "existing", answer
    assert answer.known == 1 and answer.ref.id == "015009"
    assert answer.ref.type.name == "ltc_facility"


# ============================================================ section 3 -- resolve_instance


def test_c20_15_the_outcome_vocabulary_is_closed_at_five():
    """Rule 3-1."""
    assert INSTANCE_OUTCOMES == (
        "existing", "ambiguous", "proposal", "not_an_instance", "unknowable")


def test_c20_16_resolve_instance_is_a_distinct_call():
    """Rule 3-2."""
    params = inspect.signature(Registry.resolve_instance).parameters
    assert set(params) - {"self"} == {
        "candidate", "context", "type_name", "namespace", "tier", "host_filter"}
    assert "InstanceContext" in str(params["context"].annotation)
    assert "host_filter" not in inspect.signature(Registry.resolve_type).parameters


@NEEDS_ATTRIBUTES
def test_c20_17_ambiguous_is_decided_over_the_set_before_existing(adapter, make_registry):
    """Rule 3-3: at-or-above `match_at`, AND within `ambiguity_margin` of the top."""
    rows = _rows() + [{"host_id": "015099", "label": "BURNS NURSING HOMES INC", "state": "AL"}]
    wide = {**POLICY, "match_at": 0.99, "ambiguity_margin": 0.03}
    registry = _world(adapter, make_registry, rows, policy=wide)
    tied = _resolve(registry, EXACT)                 # 1.0 and 0.9778, margin 0.03
    assert tied.outcome == "ambiguous"
    assert {c.ref.id for c in tied.candidates} == {"015009", "015099"}

    host_instances(adapter, rows, type_name="home")
    narrow = make_registry(adapter)
    seed(narrow, "home", attributes=_governed({**wide, "ambiguity_margin": 0.01}))
    assert _resolve(narrow, EXACT, type_name="home").outcome == "existing"


@NEEDS_ATTRIBUTES
def test_c20_18_ambiguous_carries_no_ref_and_every_tied_candidate(adapter, make_registry):
    """Rule 3-4. **Finding 1's check:** red when `ambiguous` keeps a ref or drops a tie."""
    rows = _rows() + [{"host_id": "015098", "label": "BURNS NURSING HOME INC", "state": "AL"},
                      {"host_id": "015097", "label": "Burns Nursing Home, Inc", "state": "AL"}]
    registry = _world(adapter, make_registry, rows)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "ambiguous"
    assert answer.ref is None
    assert sorted(c.ref.id for c in answer.candidates) == ["015009", "015097", "015098"]
    assert answer.known == 3
    assert answer.candidate is not None and answer.candidate.resolution == "ambiguous"


@NEEDS_ATTRIBUTES
def test_c20_19_an_unfinished_read_is_unknowable_whatever_it_found(adapter, make_registry):
    """Rule 3-5: the exact match is on the first page and the read was cut off."""
    registry = _world(adapter, make_registry, page_size=1, scan_cap=2)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.ref is None
    assert answer.complete is False and "cap" in answer.why_incomplete


@NEEDS_ATTRIBUTES
def test_c20_20_no_incomplete_result_carries_a_decided_outcome(adapter, make_registry):
    """Rule 3-6, over every incomplete path this suite can construct."""
    host_instances(adapter, _rows(), type_name="facility", scan_cap=2, page_size=1)
    host_instances(adapter, _rows(), type_name="home")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    seed(registry, "home", attributes=_governed())
    _rewrite(adapter, "home", status="retired", successor="ghost")
    answers = [_resolve(registry, label, type_name=t)
               for t in ("facility", "home") for label in (EXACT, BAND, NOTHING)]
    assert any(a.complete is False for a in answers)
    for a in answers:
        if a.complete is False:
            assert a.outcome in {"unknowable", "not_an_instance"}, a


@NEEDS_ATTRIBUTES
def test_c20_21_proposal_requires_every_page_complete(adapter, make_registry):
    """Rule 3-7: nothing matches on the pages read, and the read was cut off."""
    registry = _world(adapter, make_registry, page_size=1, scan_cap=3)
    answer = _resolve(registry, NOTHING)
    assert answer.outcome == "unknowable"
    complete = _world(adapter, make_registry, name="home")
    assert _resolve(complete, NOTHING, type_name="home").outcome == "proposal"


@NEEDS_ATTRIBUTES
def test_c20_22_not_an_instance_reads_no_host_table(adapter, make_registry):
    """Rule 3-8."""
    host_instances(adapter, _rows(), type_name="facility")
    counted = DegradedAdapter(adapter)
    registry = make_registry(counted)
    seed(registry, "facility", attributes=_governed())
    for word in ("Provider Name", "facility", "  NURSING HOME "):
        answer = _resolve(registry, word)
        assert answer.outcome == "not_an_instance", word
        assert answer.scanned == 0 and answer.ref is None
    assert counted.instance_reads == 0
    assert _resolve(registry, EXACT).outcome == "existing" and counted.instance_reads > 0


@NEEDS_ATTRIBUTES
def test_c20_23_confidence_none_means_did_not_score(adapter, make_registry):
    """Rule 3-9."""
    registry = _world(adapter, make_registry, page_size=1, scan_cap=1)
    assert _resolve(registry, EXACT).confidence is None
    scored = _world(adapter, make_registry, name="home")
    answer = _resolve(scored, EXACT, type_name="home")
    assert isinstance(answer.confidence, float) and answer.confidence == 1.0
    assert _resolve(scored, "Provider Name", type_name="home").confidence is None


def test_c20_24_the_call_takes_no_threshold_and_no_predicate(registry):
    """Rule 3-10."""
    params = set(inspect.signature(Registry.resolve_instance).parameters)
    assert not params & {"min_confidence", "predicate", "match_at", "condition"}
    for kwarg in ("min_confidence", "predicate"):
        with pytest.raises(TypeError):
            registry.resolve_instance(EXACT, CTX, type_name="facility", tier="small",
                                      **{kwarg: 0.5})


@NEEDS_ATTRIBUTES
def test_c20_25_tier_is_required_and_echoed(adapter, make_registry):
    """Rule 3-11. **Finding 1's check:** red when the tier is not the caller's."""
    registry = _world(adapter, make_registry)
    for tier in ("small", "large", "human"):
        assert _resolve(registry, EXACT, tier=tier).tier == tier
        assert _resolve(registry, "Provider Name", tier=tier).tier == tier
    with pytest.raises(TypeError):
        registry.resolve_instance(EXACT, CTX, type_name="facility")
    with pytest.raises(TypeError, match="3-11"):
        _resolve(registry, EXACT, tier="")


@NEEDS_ATTRIBUTES
def test_c20_26_an_undecidable_predicate_is_unknowable_not_narrower(adapter, make_registry):
    """Rule 3-12."""
    county = {"op": "eq", "attribute": "county", "value": "Jefferson",
              "why": "a column the host does not carry"}
    registry = _world(adapter, make_registry, condition=county)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.ref is None
    assert "undecidable" in answer.reason


@NEEDS_ATTRIBUTES
def test_c20_67_a_read_of_zero_rows_is_unknowable(adapter, make_registry):
    """Rule 3-13."""
    registry = _world(adapter, make_registry, rows=[])
    answer = _resolve(registry, NOTHING)
    assert answer.outcome == "unknowable" and answer.scanned == 0
    assert answer.why_incomplete == "scanned=0"


@NEEDS_RETIRE
def test_c20_68_the_read_follows_the_whole_successor_chain(adapter, make_registry):
    """Rule 3-14: two hops, each reported."""
    for name in ("facility", "ltc_facility", "ltc_home"):
        host_instances(adapter, _rows() if name == "ltc_home" else [], type_name=name)
    registry = make_registry(adapter)
    for name in ("facility", "ltc_facility", "ltc_home"):
        seed(registry, name, attributes=_governed())
    for old, new in (("facility", "ltc_facility"), ("ltc_facility", "ltc_home")):
        retired = registry.retire(old, "renamed", retired_by="user:sd", successor=new)
        assert isinstance(retired, TypeEntry), retired
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "existing" and answer.ref.type.name == "ltc_home"
    assert [w for w in answer.warnings if w.startswith("instance_type_succeeded")] == [
        "instance_type_succeeded:ltc_facility", "instance_type_succeeded:ltc_home"]
    assert answer.governed_by == "default:ltc_home"


@NEEDS_ATTRIBUTES
def test_c20_76_a_dangling_successor_stops_and_never_falls_back(adapter, make_registry):
    """Rule 3-15."""
    registry = _world(adapter, make_registry)
    _rewrite(adapter, "facility", status="retired", successor="ghost")
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False
    assert "ghost" in answer.why_incomplete and "3-15" in answer.why_incomplete
    assert answer.scanned == 0 and answer.confidence is None


@NEEDS_ATTRIBUTES
def test_c20_77_the_walk_carries_a_hop_cap(adapter, make_registry):
    """Rule 3-16."""
    names = [f"t{i:02d}" for i in range(INSTANCE_CHAIN_CAP + 2)]
    host_instances(adapter, _rows(), type_name=names[0])
    registry = make_registry(adapter)
    for name in names:
        seed(registry, name, attributes=_governed())
    for here, nxt in zip(names, names[1:]):
        _rewrite(adapter, here, status="retired", successor=nxt)
    answer = _resolve(registry, EXACT, type_name=names[0])
    assert answer.outcome == "unknowable" and "3-16" in answer.why_incomplete


@NEEDS_ATTRIBUTES
def test_c20_78_a_cycle_is_incomplete_and_the_walk_survives_it(adapter, make_registry):
    """Rule 3-17."""
    host_instances(adapter, _rows(), type_name="facility")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    seed(registry, "home", attributes=_governed())
    _rewrite(adapter, "facility", status="retired", successor="home")
    _rewrite(adapter, "home", status="retired", successor="facility")
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "3-17" in answer.why_incomplete


@NEEDS_RETIRE
def test_c20_79_changed_governed_facts_across_the_closure_are_unknowable(
    adapter, make_registry
):
    """Rule 3-18: both facts differ, and the why names both."""
    registry = _successor_world(
        adapter, make_registry, old_rows=_rows(), new_rows=_rows(),
        new_governed=_governed({**POLICY, "match_at": 0.9}, AL_ONLY))
    for name in ("facility", "ltc_facility"):
        answer = _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "unknowable", (name, answer)
        assert "MatchPolicy" in answer.why_incomplete
        assert "tenancy predicate" in answer.why_incomplete


@NEEDS_RETIRE
def test_c20_80_the_extent_is_the_whole_closure_forward(adapter, make_registry):
    """Rule 3-19: a row still written under the retired name is found from it."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    new = _rows()[1:]
    registry = _successor_world(adapter, make_registry, old_rows=old, new_rows=new)
    answer = _resolve(registry, EXACT, type_name="facility")
    assert answer.outcome == "existing" and answer.ref.id == "015009"
    assert answer.scanned == 5


@NEEDS_RETIRE
def test_c20_86_the_closure_walks_backward_too(adapter, make_registry):
    """Rule 3-20: the SURVIVOR finds the row written under the retired name."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    registry = _successor_world(adapter, make_registry, old_rows=old, new_rows=_rows()[1:])
    answer = _resolve(registry, EXACT, type_name="ltc_facility")
    assert answer.outcome == "existing" and answer.ref.id == "015009"
    assert answer.scanned == 5
    lookup = registry.get_instance_checked("ltc_facility", "015009")
    assert lookup.record is not None and lookup.record.type_name == "facility"


@NEEDS_MERGE
@pytest.mark.requires_capability("stores_aliases")
def test_c20_87_aliases_are_members_of_the_closure(adapter, make_registry):
    """Rule 3-21: `merge_types` writes a successor AND an alias; both are read."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    host_instances(adapter, old, type_name="facility")
    host_instances(adapter, _rows()[1:], type_name="ltc_facility")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    seed(registry, "ltc_facility", attributes=_governed())
    merged = registry.merge_types("facility", "ltc_facility", "one class",
                                  merged_by="user:sd", acknowledge=("definitions_diverge", "no_consumer_evidence"))
    assert not isinstance(merged, Refusal), merged
    assert "facility" in adapter.get_type("default", "ltc_facility", kind="entity").aliases
    answer = _resolve(registry, EXACT, type_name="ltc_facility")
    assert answer.outcome == "existing" and answer.ref.id == "015009"


@NEEDS_ATTRIBUTES
def test_c20_88_a_successor_name_carrying_a_separator_stops_the_walk(adapter, make_registry):
    """Rule 3-22 (round 3's K8)."""
    registry = _world(adapter, make_registry)
    for bad in ("ward:north", "ward#north"):
        _rewrite(adapter, "facility", status="retired", successor=bad)
        answer = _resolve(registry, EXACT)
        assert answer.outcome == "unknowable" and "3-22" in answer.why_incomplete, bad


# ============================================================ section 5 -- the gate


@NEEDS_ATTRIBUTES
def test_c20_35_the_policy_is_declared_on_the_entry_and_rides_approval(registry):
    """Rule 5-1."""
    proposal = registry.propose_type("facility", "a nursing facility", [], "user:sd",
                                     kind="entity", attributes=_governed())
    entry = proposal if isinstance(proposal, TypeEntry) else registry.approve(
        proposal.id, "user:sd")
    assert entry.attributes[MATCH_POLICY_KEY] == POLICY
    params = set(inspect.signature(Registry.resolve_instance).parameters)
    assert not params & {"match_at", "propose_below", "ambiguity_margin", "policy"}


def _refused_declaration(registry, attributes, *, name="facility", kind="entity"):
    answer = registry.propose_type(name, f"a {name}", [], "user:sd", kind=kind,
                                   attributes=attributes)
    assert isinstance(answer, Refusal), answer
    assert answer.reason == "attributes_schema_violation"
    return answer


def test_c20_36_propose_below_above_match_at_is_refused(registry):
    """Rule 5-2."""
    assert match_policy_problem({**POLICY, "propose_below": 0.99})
    _refused_declaration(registry, {MATCH_POLICY_KEY: {**POLICY, "propose_below": 0.99}})
    assert match_policy_problem({**POLICY, "propose_below": 0.97}) is None


def test_c20_37_the_policy_why_is_required(registry):
    """Rule 5-3."""
    for why in (None, "", "   "):
        bad = {k: v for k, v in POLICY.items() if k != "why"}
        if why is not None:
            bad["why"] = why
        assert match_policy_problem(bad), why
        _refused_declaration(registry, {MATCH_POLICY_KEY: bad})


@NEEDS_ATTRIBUTES
def test_c20_38_the_gate_mints_no_verdict_vocabulary(adapter, make_registry):
    """Rule 5-4."""
    registry = _world(adapter, make_registry)
    outcomes = {_resolve(registry, c).outcome
                for c in (EXACT, BAND, NOTHING, "Provider Name", "Highlands Health Rehab")}
    assert outcomes == {"existing", "ambiguous", "proposal", "not_an_instance"}
    assert outcomes <= set(INSTANCE_OUTCOMES)


@NEEDS_ATTRIBUTES
def test_c20_39_unscored_and_unfinished_are_unknowable_at_the_gate(adapter, make_registry):
    """Rule 5-5."""
    unscored = _world(adapter, make_registry, policy=None)
    answer = _resolve(unscored, EXACT)
    assert answer.outcome == "unknowable" and answer.confidence is None
    assert "MatchPolicy" in answer.why_incomplete
    cut = _world(adapter, make_registry, name="home", page_size=1, scan_cap=2)
    assert _resolve(cut, EXACT, type_name="home").outcome == "unknowable"


@NEEDS_ATTRIBUTES
def test_c20_40_entries_may_differ_and_callers_may_not(adapter, make_registry):
    """Rule 5-6."""
    host_instances(adapter, _rows(), type_name="facility")
    host_instances(adapter, _rows(), type_name="home")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    seed(registry, "home", attributes=_governed(
        {"match_at": 0.85, "propose_below": 0.5, "ambiguity_margin": 0.01, "why": "loose"}))
    assert _resolve(registry, BAND).outcome == "ambiguous"
    assert _resolve(registry, BAND, type_name="home").outcome == "existing"
    with pytest.raises(TypeError):
        registry.resolve_instance(BAND, CTX, type_name="facility", tier="small",
                                  match_policy=POLICY)


@NEEDS_ATTRIBUTES
def test_c20_41_the_policy_in_force_is_recorded(adapter, make_registry):
    """Rule 5-7. Its carrier is rule 5-11's `governed_by` until row 7c's invocation."""
    registry = _world(adapter, make_registry)
    answer = _resolve(registry, EXACT)
    assert answer.governed_by == "default:facility"
    ns, name = answer.governed_by.split(":")
    entry = adapter.get_type(ns, name, kind="entity")
    assert entry.attributes[MATCH_POLICY_KEY] == POLICY


@NEEDS_ATTRIBUTES
def test_c20_73_existing_requires_exactly_one_in_the_tied_set(adapter, make_registry):
    """Rule 5-8."""
    registry = _world(adapter, make_registry)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "existing"
    assert answer.known == 1 and len(answer.candidates) == 1


@NEEDS_ATTRIBUTES
def test_c20_74_a_top_candidate_in_the_band_is_ambiguous(adapter, make_registry):
    """Rule 5-9: 0.9, between propose_below 0.80 and match_at 0.97."""
    registry = _world(adapter, make_registry)
    answer = _resolve(registry, BAND)
    assert answer.outcome == "ambiguous" and answer.ref is None
    assert 0.80 <= answer.confidence < 0.97


@NEEDS_RETIRE
def test_c20_82_a_successor_does_not_inherit_the_match_policy(adapter, make_registry):
    """Rule 5-10."""
    registry = _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed({**POLICY, "match_at": 0.9}))
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "MatchPolicy" in answer.why_incomplete
    assert "tenancy predicate" not in answer.why_incomplete


@NEEDS_RETIRE
def test_c20_85_governed_by_names_the_entry_that_judged(adapter, make_registry):
    """Rule 5-11."""
    plain = _world(adapter, make_registry, name="home")
    assert _resolve(plain, EXACT, type_name="home").governed_by == "default:home"
    moved = _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows())
    for name in ("facility", "ltc_facility"):
        assert _resolve(moved, EXACT, type_name=name).governed_by == "default:ltc_facility"
    assert moved.get_instance_checked("facility", "015009").governed_by == \
        "default:ltc_facility"


@NEEDS_ATTRIBUTES
def test_c20_90_the_tied_set_has_a_floor(adapter, make_registry):
    """Rule 5-12 (round 3's K7): a margin wide enough to reach every row, and only the
    candidates at or above `propose_below` may tie."""
    wide = {**POLICY, "ambiguity_margin": 0.99}
    registry = _world(adapter, make_registry, policy=wide)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "existing" and answer.known == 1


# ============================================================ section 6 -- Condition


def _cond(op, attribute="state", value="AL", **kw):
    return {"op": op, "attribute": attribute, "value": value, "why": "C20", **kw}


def test_c20_42_the_condition_vocabulary_is_closed_at_twelve(registry):
    """Rule 6-1."""
    assert len(CONDITION_TERMS) == 12
    assert condition_problem(_cond("startswith"))
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("startswith")})


def test_c20_43_a_condition_reads_one_records_values():
    """Rule 6-2: `evaluate` is given the condition and one record's attributes, and
    nothing else to call."""
    assert list(inspect.signature(evaluate).parameters) == ["cond", "attributes"]
    assert evaluate(condition_from_mapping(_cond("eq")), {"state": "AL"}).holds is True


def test_c20_44_evaluation_is_three_valued():
    """Rule 6-3."""
    eq = condition_from_mapping(_cond("eq"))
    assert evaluate(eq, {"state": "AL"}).holds is True
    assert evaluate(eq, {"state": "CA"}).holds is False
    unknown = evaluate(eq, {})
    assert unknown.holds is None and unknown.why


def test_c20_45_an_unreadable_attribute_is_unknowable_not_false():
    """Rule 6-4."""
    for op, value in (("eq", "AL"), ("ne", "AL"), ("not_in", ["AL"])):
        verdict = evaluate(condition_from_mapping(_cond(op, value=value)), {"city": "Mobile"})
        assert verdict.holds is None and verdict.unreadable == ("state",), op


def test_c20_46_null_makes_comparisons_unknowable_and_is_null_a_fact():
    """Rule 6-5."""
    record = {"state": None}
    for op, value in (("eq", "AL"), ("ne", "AL"), ("lt", "M"), ("in", ["AL"])):
        assert evaluate(condition_from_mapping(_cond(op, value=value)), record).holds is None
    assert evaluate(condition_from_mapping(_cond("is_null", value=None)), record).holds is True
    assert evaluate(
        condition_from_mapping(_cond("is_not_null", value=None)), record).holds is False


def test_c20_47_comparisons_refuse_a_null_operand(registry):
    """Rule 6-6."""
    for op in ("eq", "ne", "lt", "lte", "gt", "gte"):
        assert condition_problem(_cond(op, value=None)), op
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("eq", value=None)})


def test_c20_48_in_and_not_in_take_a_sequence(registry):
    """Rule 6-7."""
    for op in ("in", "not_in"):
        assert condition_problem(_cond(op, value="AL")), op
        assert condition_problem(_cond(op, value=["AL", "CA"])) is None
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("in", value="AL")})


def _combinator(op, terms, **kw):
    return {"op": op, "terms": terms, "why": "C20", **kw}


def test_c20_49_a_combinator_needs_terms(registry):
    """Rule 6-8."""
    for op in CONDITION_COMBINATORS:
        assert condition_problem(_combinator(op, [])), op
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _combinator("all_of", [])})


def test_c20_50_a_combinator_carries_no_attribute_or_value(registry):
    """Rule 6-9."""
    term = _cond("eq")
    for extra in ({"attribute": "state"}, {"value": "AL"}):
        assert condition_problem(_combinator("any_of", [term], **extra)), extra
    _refused_declaration(
        registry, {INSTANCE_CONDITION_KEY: _combinator("any_of", [term], value="AL")})


def test_c20_51_an_operator_carries_no_terms(registry):
    """Rule 6-10."""
    assert condition_problem(_cond("eq", terms=[_cond("eq")]))
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("eq", terms=[_cond("eq")])})


def test_c20_52_the_condition_why_is_required(registry):
    """Rule 6-11."""
    for why in ("", "   "):
        assert condition_problem({**_cond("eq"), "why": why}), why
    bare = {k: v for k, v in _cond("eq").items() if k != "why"}
    assert condition_problem(bare)
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: bare})


def test_c20_53_all_of_and_any_of_are_kleene():
    """Rule 6-12."""
    t, f, u = _cond("eq", value="AL"), _cond("eq", value="CA"), _cond("eq", attribute="county")
    record = {"state": "AL"}

    def run(op, *terms):
        return evaluate(condition_from_mapping(_combinator(op, list(terms))), record).holds

    assert run("all_of", t, t) is True
    assert run("all_of", t, f, u) is False
    assert run("all_of", t, u) is None
    assert run("any_of", f, f) is False
    assert run("any_of", f, t, u) is True
    assert run("any_of", f, u) is None


def test_c20_54_there_is_no_not_and_no_matches(registry):
    """Rule 6-13."""
    assert "not" not in CONDITION_TERMS and "matches" not in CONDITION_TERMS
    assert set(CONDITION_OPERATORS) | set(CONDITION_COMBINATORS) == set(CONDITION_TERMS)
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("matches", value="^A")})
    _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _combinator("not", [_cond("eq")])})


@NEEDS_ATTRIBUTES
def test_c20_55_the_condition_rides_approval_and_is_never_a_parameter(registry):
    """Rule 6-14."""
    entry = seed(registry, "facility", attributes=_governed(condition=AL_ONLY))
    assert entry.attributes[INSTANCE_CONDITION_KEY] == AL_ONLY
    with pytest.raises(TypeError):
        registry.resolve_instance(EXACT, CTX, type_name="facility", tier="small",
                                  predicate=AL_ONLY)


@NEEDS_ATTRIBUTES
def test_c20_56_the_registry_evaluates_the_condition_over_every_record(
    adapter, make_registry
):
    """Rule 6-15: no host_filter at all, and the CO row is still excluded."""
    registry = _world(adapter, make_registry, condition=AL_ONLY)
    answer = _resolve(registry, "Mesa Vista Care")
    assert answer.outcome == "proposal"
    assert all(c.discriminators["state"] == "AL" for c in answer.candidates)
    assert registry.get_instance_checked("facility", "065001").record is None


@NEEDS_ATTRIBUTES
def test_c20_57_an_undecided_candidate_is_never_silently_dropped(adapter, make_registry):
    """Rule 6-16: one row's state is NULL."""
    rows = _rows() + [{"host_id": "015077", "label": "SOMEWHERE ELSE", "state": None}]
    registry = _world(adapter, make_registry, rows, condition=AL_ONLY)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "undecidable" in answer.reason


def test_c20_58_the_candidate_primitive_takes_no_tenant(adapter):
    """Rule 6-17 (R24, R59). **Finding 1's check:** red when a tenant field appears."""
    assert [f.name for f in dataclasses.fields(CandidateQuery)] == [
        "namespace", "kind", "type_name", "label", "host_filter", "limit", "after"]
    for name in ("get_instance", "find_instance_candidates"):
        # The protocol's, and the bound method of the backend that answers (a forwarding
        # proxy has no class attribute of its own, C20-09's reason).
        for method in (getattr(StorageAdapter, name), getattr(adapter, name)):
            params = set(inspect.signature(method).parameters)
            assert not {p for p in params if "tenant" in p}, (method, name)
    assert set(inspect.signature(StorageAdapter.find_instance_candidates).parameters) == {
        "self", "q"}


@NEEDS_RETIRE
def test_c20_83_a_successor_does_not_inherit_the_predicate(adapter, make_registry):
    """Rule 6-18."""
    registry = _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed(condition=AL_ONLY))
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "tenancy predicate" in answer.why_incomplete
    assert "MatchPolicy" not in answer.why_incomplete


# ============================================================ section 7 -- the host


@NEEDS_ATTRIBUTES
def test_c20_59_blast_radius_is_reported_incomplete_never_safe(adapter, make_registry):
    """Rule 7-1 (Q87's default: warn)."""
    registry = _world(adapter, make_registry)
    assert "consumers_unregistered" in _resolve(registry, EXACT).warnings
    registered = registry.register_consumer(Consumer(id="billing", gate="facility"))
    assert not isinstance(registered, Refusal), registered
    assert "consumers_unregistered" not in _resolve(registry, EXACT).warnings


def test_c20_60_no_consumer_registration_mechanism_is_added():
    """Rule 7-2."""
    public = {n for n in dir(Registry) if not n.startswith("_")}
    assert {n for n in public if "instance" in n} == {"resolve_instance", "get_instance_checked"}
    assert not {n for n in public if "consumer" in n and "instance" in n}


def test_c20_61_the_entity_vocabulary_is_registered_through_the_shipped_calls(registry):
    """Rule 7-3. A governed fact belongs on a kind="entity" entry and nowhere else."""
    public = {n for n in dir(Registry) if not n.startswith("_")}
    assert not {n for n in public if "entity" in n}
    _refused_declaration(registry, {MATCH_POLICY_KEY: POLICY}, name="admitted", kind="event")


@NEEDS_ATTRIBUTES
def test_c20_62_no_tenancy_predicate_is_unfiltered_and_says_so(adapter, make_registry):
    """Rule 7-4."""
    open_ = _world(adapter, make_registry)
    answer = _resolve(open_, "Mesa Vista Care")
    assert answer.outcome == "existing" and "no_tenancy_predicate" in answer.warnings
    closed = _world(adapter, make_registry, name="home", condition=AL_ONLY)
    assert "no_tenancy_predicate" not in _resolve(closed, EXACT, type_name="home").warnings


@NEEDS_RETIRE
def test_c20_84_a_successor_declares_its_own_governed_facts(adapter, make_registry):
    """Rule 7-5: a successor declaring neither fact answers unknowable; declaring the
    same facts answers."""
    host_instances(adapter, [], type_name="facility")
    host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    seed(registry, "ltc_facility")
    registry.retire("facility", "renamed", retired_by="user:sd", successor="ltc_facility")
    assert _resolve(registry, EXACT).outcome == "unknowable"

    same = _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows(),
                            old="home", new="ltc_home")
    assert _resolve(same, EXACT, type_name="home").outcome == "existing"


# ============================================================ round 1 of the loop
#
# 7B-RUN.md 2.1. Each test below is a construction a round-1 lens ran against 6891fbb,
# kept so the shape it found cannot come back. The id is the rule the shape breaks.


@NEEDS_RETIRE
def test_c20_79_r1_a_reworded_why_on_identical_facts_is_not_a_change(adapter, make_registry):
    """Rule 3-18 under E10 (INGEST.md 5.3): "different" is the three thresholds and the
    predicate's TERMS, never the prose. Round 1 found the raw mappings compared, so a
    reworded `why` stopped the loop, and an `in` list in another order did too."""
    reworded = {**POLICY, "why": "same numbers, reworded by the other team"}
    same_terms = {"op": "in", "attribute": "state", "value": ["AL", "GA"],
                  "why": "one deployment, two states"}
    other_order = {"op": "in", "attribute": "state", "value": ["GA", "AL"],
                   "why": "reworded, and the states listed the other way round"}
    registry = _successor_world(
        adapter, make_registry, old_rows=_rows(), new_rows=[],
        old_governed=_governed(condition=same_terms),
        new_governed=_governed(policy=reworded, condition=other_order))
    for name in ("facility", "ltc_facility"):
        answer = _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "existing", (name, answer)
        lookup = registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup


@NEEDS_RETIRE
def test_c20_79_r1_a_changed_threshold_is_still_a_change(adapter, make_registry):
    """The control for the test above: one threshold moved is a different MatchPolicy."""
    moved = {**POLICY, "match_at": 0.98}
    registry = _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed(policy=moved))
    answer = _resolve(registry, EXACT, type_name="ltc_facility")
    assert answer.outcome == "unknowable" and "MatchPolicy" in answer.why_incomplete


@NEEDS_RETIRE
def test_c20_89_r1_the_two_doors_judge_the_same_copy(adapter, make_registry):
    """Rule 2-17, standing rule (e). Mid-migration the host holds 055001 under both
    names and the copies DIFFER: the stale `facility` row says CA, the migrated
    `ltc_facility` row says CO. Round 1 found resolve_instance judging both copies by
    the predicate first and collapsing after, so the stale CA copy decided `existing`
    while get_instance_checked, which collapses first, excluded the row. One identity
    must be one copy, the effective name's, at both doors."""
    ca_only = {"op": "eq", "attribute": "state", "value": "CA",
               "why": "this deployment serves California only"}
    stale = {"host_id": "055001", "label": "WILLOWBROOKE CT SKILLED CARE CENTER",
             "state": "CA", "kind_name": "facility"}
    moved = dict(stale, state="CO", kind_name="ltc_facility")
    registry = _successor_world(
        adapter, make_registry, old_rows=None, new_rows=None,
        type_column_rows=[stale, moved],
        old_governed=_governed(condition=ca_only), new_governed=_governed(condition=ca_only))
    for name in ("facility", "ltc_facility"):
        answer = _resolve(registry, "Willowbrooke Ct Skilled Care Center", type_name=name)
        assert answer.outcome != "existing", (name, answer)
        assert all(c.ref.type.name == "ltc_facility" for c in answer.candidates), answer
        lookup = registry.get_instance_checked(name, "055001")
        assert isinstance(lookup, InstanceLookup) and lookup.record is None, lookup


@NEEDS_RETIRE
def test_c20_89_r1_the_kept_copy_is_the_effective_names(adapter, make_registry):
    """Rule 2-17's other half, at primitive 22's door: with both copies present the
    lookup returns the effective name's copy, never the first one found."""
    stale = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL",
             "kind_name": "facility"}
    moved = dict(stale, label="BURNS NURSING HOME", kind_name="ltc_facility")
    registry = _successor_world(adapter, make_registry, old_rows=None, new_rows=None,
                                type_column_rows=[stale, moved])
    for name in ("facility", "ltc_facility"):
        lookup = registry.get_instance_checked(name, "015009")
        assert lookup.record.type_name == "ltc_facility", (name, lookup)
        assert lookup.record.label == "BURNS NURSING HOME"
        assert lookup.ref.type.name == "ltc_facility"


@NEEDS_RETIRE
def test_c20_66_r1_an_unreadable_member_refuses_never_hands_out(adapter, make_registry):
    """Rule 2-15, `I-1` at primitive 22's door (round 1, door lens T1). The host binds
    only the successor's table, so the lookup under the retired name cannot be made:
    the row found under the other is a decision over a partial extent."""
    host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    seed(registry, "ltc_facility", attributes=_governed())
    retired = registry.retire("facility", "CMS renamed the class", retired_by="user:sd",
                              successor="ltc_facility")
    assert isinstance(retired, TypeEntry), retired
    for name in ("facility", "ltc_facility"):
        lookup = registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, Refusal), (name, lookup)
        assert lookup.detail["problem"] == "lookup_incomplete"
        assert _resolve(registry, EXACT, type_name=name).outcome == "unknowable"


def test_c20_66_r1_a_repeated_id_refuses_never_reads_absent(adapter, make_registry):
    """Rule 2-15 with rule 2-16 (door lens T2): a citations-shaped host carries CCN
    015009 on two rows. The lookup refuses; an id present twice is never `absent`."""
    rows = _rows() + [dict(_rows()[0], label="BURNS NURSING HOME INC (2023 survey)")]
    host_instances(adapter, rows, type_name="facility")
    registry = make_registry(adapter)
    seed(registry, "facility")
    lookup = registry.get_instance_checked("facility", "015009")
    assert isinstance(lookup, Refusal), lookup
    assert lookup.detail["problem"] == "lookup_incomplete"


def test_c20_05_r1_a_type_column_binding_never_manufactures(adapter, make_registry):
    """Rule 2-2 on the type-column path (door lens T5): one host table, rows typed by a
    column. An id held only as a `facility` is absent as a `hospital`."""
    rows = [dict(r, kind_name="facility") for r in _rows()] + [
        {"host_id": "019999", "label": "A HOSPITAL", "state": "AL", "kind_name": "hospital"}]
    for name in ("facility", "hospital"):
        host_instances(adapter, rows, type_name=name, type_column="kind_name")
    assert adapter.get_instance("default", "entity", "hospital", "015009") is None
    assert adapter.get_instance("default", "entity", "hospital", "019999").label == "A HOSPITAL"
    registry = make_registry(adapter)
    seed(registry, "hospital")
    absent = registry.get_instance_checked("hospital", "015009")
    assert isinstance(absent, InstanceLookup) and absent.record is None, absent


@NEEDS_ATTRIBUTES
def test_c20_18_r1_every_tied_candidate_however_many(adapter, make_registry):
    """Rule 3-4 (door lens C): the suite's widest tie was three, so a set capped at five
    survived. MILLER'S MERRY MANOR is twelve CCNs; here are eight."""
    rows = [{"host_id": f"01{n:04d}", "label": "MILLER'S MERRY MANOR", "state": "AL"}
            for n in range(8)]
    registry = _world(adapter, make_registry, rows)
    answer = _resolve(registry, "MILLER'S MERRY MANOR")
    assert answer.outcome == "ambiguous" and answer.ref is None
    assert answer.known == 8 and len(answer.candidates) == 8


@NEEDS_ATTRIBUTES
def test_c20_17_r1_the_margin_is_inclusive_at_its_edge(adapter, make_registry):
    """Rules 3-3 and 5-8 (build lens 5): 0.98 and 0.96 are within a 0.02 margin, and
    `0.98 - 0.96` is 0.020000000000000018 in floating point. Two candidates, one set."""
    rows = [{"host_id": "000001", "label": "a" * 49 + "b", "state": "AL"},   # 0.98
            {"host_id": "000002", "label": "a" * 48 + "bb", "state": "AL"}]  # 0.96
    registry = _world(adapter, make_registry, rows)
    answer = _resolve(registry, "a" * 50)
    assert answer.outcome == "ambiguous", answer
    assert answer.known == 2


@NEEDS_ATTRIBUTES
def test_c20_74_r1_the_threshold_is_tested_before_rounding(adapter, make_registry):
    """Rule 5-9 (build lens 7): 226/233 = 0.96996 is below `match_at` 0.97 and rounds
    to 0.97 at four places. The band decides on the score, not on its display."""
    rows = [{"host_id": "000001", "label": "a" * 113 + "bbbb", "state": "AL"}]
    registry = _world(adapter, make_registry, rows)
    answer = _resolve(registry, "a" * 116)
    assert answer.outcome == "ambiguous", answer


@NEEDS_ATTRIBUTES
def test_c20_14_r1_a_repeating_cursor_ends_the_read_never_loops(adapter, make_registry):
    """Rule 2-11 (build lens 4): a backend handing back the same cursor forever."""

    class Stuck:
        """Forwards everything; hands back the same cursor on every page."""

        def __init__(self, inner):
            self.inner = inner
            self.calls = 0

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def find_instance_candidates(self, q):
            self.calls += 1
            if self.calls > 50:
                raise AssertionError("the registry kept paging a cursor it had seen")
            page = self.inner.find_instance_candidates(dataclasses.replace(q, after=None))
            return dataclasses.replace(page, records=page.records[:1], known=1,
                                       complete=False, next_after="stuck")

    host_instances(adapter, _rows(), type_name="facility")
    registry = make_registry(Stuck(adapter))
    seed(registry, "facility", attributes=_governed())
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer


@NEEDS_ATTRIBUTES
def test_c20_08_r1_an_over_count_is_as_uncountable_as_an_under_count(adapter, make_registry):
    """Rule 2-5 (door lens D): `known` as the host's total on a page that holds fewer.
    Read as an extent it would be a decision over part of the rows (`I-1`)."""
    host_instances(adapter, _rows(), type_name="facility")
    registry = make_registry(DegradedAdapter(adapter, instance_known="over"))
    seed(registry, "facility", attributes=_governed())
    answer = _resolve(registry, "Mesa Vista Care")
    assert answer.outcome == "unknowable" and answer.complete is False, answer


@NEEDS_ATTRIBUTES
def test_c20_08_r1_a_finished_read_that_cannot_count_is_counted_here(adapter, make_registry):
    """Rule 2-5 with 3.4's third absorber, which is `known=None` AND `complete=False`
    together (build lens 3). A backend that finished but cannot count hands over every
    record, and the registry counts them."""
    host_instances(adapter, _rows(), type_name="facility")
    finished = make_registry(DegradedAdapter(adapter, instance_known="none"))
    seed(finished, "facility", attributes=_governed())
    answer = _resolve(finished, EXACT)
    assert answer.outcome == "existing" and answer.known == 1, answer


@NEEDS_ATTRIBUTES
def test_c20_08_r1_an_unfinished_read_that_cannot_count_is_unknowable(adapter, make_registry):
    """The absorber itself: `known=None` and `complete=False` together."""
    host_instances(adapter, _rows(), type_name="facility", page_size=2)
    registry = make_registry(DegradedAdapter(adapter, instance_known="none",
                                             instance_page_cap=2))
    seed(registry, "facility", attributes=_governed())
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer


def test_c20_01_r1_the_snapshot_sees_every_registry_table(adapter, make_registry):
    """Rule 1-1 (door lens E): the seam check's snapshot read five tables and could not
    see an attribute observation, an edge or an invocation written on the side."""
    from . import _support

    source = inspect.getsource(_support.snapshot)
    for read in ("find_edges", "find_invocations", "read_attr_observed"):
        assert read in source, f"snapshot does not read {read}"


def test_c20_04_r1_no_protocol_method_but_the_two_takes_or_returns_an_instance(adapter):
    """Rule 2-1 (door lens G): a write primitive need not have "instance" in its name."""
    for name in dir(StorageAdapter):
        if name.startswith("_") or name in ("get_instance", "find_instance_candidates"):
            continue
        member = getattr(StorageAdapter, name)
        if not callable(member):
            continue
        hints = str(inspect.signature(member))
        assert "InstanceRecord" not in hints and "CandidatePage" not in hints, name


def test_c20_58_r1_primitive_22_takes_exactly_its_four(adapter):
    """Rule 6-17 (door lens I): a tenancy parameter by another name is still one."""
    assert list(inspect.signature(StorageAdapter.get_instance).parameters) == [
        "self", "namespace", "kind", "type_name", "instance_id"]


@NEEDS_ATTRIBUTES
def test_c20_25_r1_tier_none_is_refused(adapter, make_registry):
    """Rule 3-11 (door lens L)."""
    registry = _world(adapter, make_registry)
    with pytest.raises(TypeError):
        registry.resolve_instance(EXACT, CTX, type_name="facility", tier=None)


@NEEDS_ATTRIBUTES
def test_c20_63_r1_a_class_word_does_not_skip_the_host_filter_check(adapter, make_registry):
    """Rule 2-12 (door lens J): the mapping check runs before `not_an_instance`."""
    registry = _world(adapter, make_registry)
    with pytest.raises(TypeError):
        _resolve(registry, "Provider Name", host_filter="state=AL")


@NEEDS_ATTRIBUTES
def test_c20_62_r1_not_an_instance_carries_the_namespace_warnings(adapter, make_registry):
    """Rules 7-1 and 7-4 (build lens, read-only): every resolution carries them, the
    one that reads nothing included."""
    registry = _world(adapter, make_registry)
    answer = _resolve(registry, "Provider Name")
    assert answer.outcome == "not_an_instance"
    assert "no_tenancy_predicate" in answer.warnings
    assert "consumers_unregistered" in answer.warnings


# ============================================================ round 2 of the loop
#
# 7B-RUN.md 2.2. As round 1: each test is a construction a round-2 lens ran against
# a27a4df, kept so the shape cannot come back.


@NEEDS_ATTRIBUTES
def test_c20_05_r2_an_integer_host_id_reads_back_at_both_doors(adapter, make_registry):
    """Rule 2-2 with standing rule (e) (round 2, build lens M1): the host's id column
    holds integers. Primitive 23 mints ref `#42`; primitive 22 asked for "42" must find
    that row, never call it absent."""
    rows = [{"host_id": 42, "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    host_instances(adapter, rows, type_name="facility", id_type="NUMBER")
    registry = make_registry(adapter)
    seed(registry, "facility", attributes=_governed())
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "existing" and answer.ref.id == "42", answer
    assert adapter.get_instance("default", "entity", "facility", "42") is not None
    lookup = registry.get_instance_checked("facility", "42")
    assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup
    assert lookup.ref == answer.ref


def _chain_world(adapter, make_registry, rows):
    """a -> b -> c on one host table typed by a column, every entry governed alike."""
    for name in ("a", "b", "c"):
        host_instances(adapter, rows, type_name=name, type_column="kind_name")
    registry = make_registry(adapter)
    for name in ("a", "b", "c"):
        seed(registry, name, attributes=_governed())
    for old, new in (("a", "b"), ("b", "c")):
        retired = registry.retire(old, "renamed", retired_by="user:sd", successor=new)
        assert isinstance(retired, TypeEntry), retired
    return registry


@NEEDS_RETIRE
def test_c20_89_r2_the_ref_never_depends_on_the_declared_name(adapter, make_registry):
    """Rule 2-17, "resolved under the name the closure resolves to" (round 2, build
    lens M2). 015009 is held under `a` and `b`, identically, and not under `c`. Round 2
    found `a#015009` from one caller and `b#015009` from another."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    rows = [dict(burns, kind_name="a"), dict(burns, kind_name="b"),
            {"host_id": "015010", "label": "COOSA VALLEY HEALTHCARE CENTER", "state": "AL",
             "kind_name": "c"}]
    registry = _chain_world(adapter, make_registry, rows)
    refs = set()
    for name in ("a", "b", "c"):
        answer = _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "existing", (name, answer)
        refs.add(answer.ref)
        lookup = registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup
        refs.add(lookup.ref)
    assert {r.type.name for r in refs} == {"c"}, refs


@NEEDS_RETIRE
def test_c20_89_r2_disagreeing_copies_none_current_decide_nothing(adapter, make_registry):
    """Rule 2-17's build-side branch (round 2, door lens): two copies that differ, none
    under the effective name. No copy is current, so neither door chooses one."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    rows = [dict(burns, kind_name="a"), dict(burns, kind_name="b", state="CA")]
    registry = _chain_world(adapter, make_registry, rows)
    answer = _resolve(registry, EXACT, type_name="c")
    assert answer.outcome == "unknowable" and "2-17" in answer.why_incomplete, answer
    door = registry.get_instance_checked("c", "015009")
    assert isinstance(door, Refusal) and door.detail["problem"] == "lookup_incomplete", door


@NEEDS_RETIRE
def test_c20_79_r2_a_margin_only_change_is_a_change(adapter, make_registry):
    """Rules 3-18 and 5-10 (round 2, door lens 1): the THREE thresholds, the margin one."""
    registry = _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed({**POLICY, "ambiguity_margin": 0.5}))
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "MatchPolicy" in answer.why_incomplete


@NEEDS_RETIRE
def test_c20_79_r2_one_value_by_equality_is_not_a_change(adapter, make_registry):
    """E10 under the equality `evaluate` uses (round 2, build lens 2): `not_in [1]` and
    `not_in [1.0]` exclude the same rows, so they are one predicate."""
    old = {"op": "not_in", "attribute": "state", "value": [1], "why": "w"}
    new = {"op": "not_in", "attribute": "state", "value": [1.0], "why": "w"}
    registry = _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                old_governed=_governed(condition=old),
                                new_governed=_governed(condition=new))
    assert _resolve(registry, EXACT).outcome == "existing"


@NEEDS_ATTRIBUTES
def test_c20_73_r2_exactly_at_match_at_is_existing(adapter, make_registry):
    """Rule 5-8, "at or above" (round 2, door lens 2)."""
    s = similar(norm(BAND), norm("BURNS NURSING HOME, INC."))
    registry = _world(adapter, make_registry, policy={**POLICY, "match_at": s})
    answer = _resolve(registry, BAND)
    assert answer.outcome == "existing", (s, answer)


@NEEDS_ATTRIBUTES
def test_c20_73_r2_a_hair_below_match_at_is_not_existing(adapter, make_registry):
    """The other side of the same edge (round 2, build lens 1): no tolerance on a
    threshold. Round 1's epsilon made 0.9 count as at 0.9 + 5e-10."""
    s = similar(norm(BAND), norm("BURNS NURSING HOME, INC."))
    registry = _world(adapter, make_registry, policy={**POLICY, "match_at": s + 5e-10})
    assert _resolve(registry, BAND).outcome == "ambiguous"


@NEEDS_ATTRIBUTES
def test_c20_17_r2_a_second_candidate_exactly_at_match_at_ties(adapter, make_registry):
    """Rule 3-3 (round 2, door lens 3): at `match_at` and outside the margin, still tied."""
    rows = _rows() + [{"host_id": "999", "label": "Burns Nursing Home", "state": "AL"}]
    s2 = similar(norm(EXACT), norm("Burns Nursing Home"))
    registry = _world(adapter, make_registry, rows, policy={**POLICY, "match_at": s2})
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "ambiguous", (s2, answer)


@NEEDS_ATTRIBUTES
def test_c20_74_r2_a_top_exactly_at_propose_below_is_ambiguous(adapter, make_registry):
    """Rule 5-9 (round 2, door lens 4)."""
    s = similar(norm(BAND), norm("BURNS NURSING HOME, INC."))
    registry = _world(adapter, make_registry, policy={**POLICY, "propose_below": s})
    answer = _resolve(registry, BAND)
    assert answer.outcome == "ambiguous", (s, answer)


@NEEDS_ATTRIBUTES
def test_c20_90_r2_the_floor_is_inclusive(adapter, make_registry):
    """Rule 5-12 (round 2, door lens 5): a second candidate exactly at `propose_below`,
    inside the margin, is in the tied set."""
    rows = _rows() + [{"host_id": "999", "label": "Burns Nursing Home Incs", "state": "AL"}]
    s2 = similar(norm(EXACT), norm("Burns Nursing Home Incs"))
    pol = {**POLICY, "match_at": 1.0, "propose_below": s2, "ambiguity_margin": 0.05}
    registry = _world(adapter, make_registry, rows, policy=pol)
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "ambiguous", (s2, answer)


def test_c20_42_r2_a_nested_term_outside_the_vocabulary_is_refused(adapter):
    """Rule 6-1, recursively (round 2, door lens 6)."""
    bad = {"op": "all_of", "why": "w",
           "terms": [{"op": "startswith", "attribute": "state", "value": "A", "why": "w"}]}
    assert condition_problem(bad)


def test_c20_45_r2_is_null_over_an_unreadable_attribute_is_unknowable(adapter):
    """Rule 6-4 (round 2, door lens 7): absent is not null."""
    c = condition_from_mapping({"op": "is_null", "attribute": "zip", "why": "w"})
    assert evaluate(c, {"state": "AL"}).holds is None
    c = condition_from_mapping({"op": "is_not_null", "attribute": "zip", "why": "w"})
    assert evaluate(c, {"state": "AL"}).holds is None


@NEEDS_ATTRIBUTES
def test_c20_66_r2_primitive_22_refuses_a_dangling_closure(adapter, make_registry):
    """Rules 2-15 and 3-15 at primitive 22's door (round 2, door lens 8)."""
    registry = _world(adapter, make_registry)
    _rewrite(adapter, "facility", status="retired", successor="ghost")
    answer = registry.get_instance_checked("facility", "015009")
    assert isinstance(answer, Refusal), answer
    assert answer.detail["problem"] == "closure_incomplete"


@NEEDS_RETIRE
def test_c20_66_r2_primitive_22_refuses_changed_governed_facts(adapter, make_registry):
    """Rule 3-18 at primitive 22's door (round 2, door lens 9)."""
    registry = _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows(),
                                new_governed=_governed(condition=AL_ONLY))
    answer = registry.get_instance_checked("facility", "015009")
    assert isinstance(answer, Refusal), answer
    assert answer.detail["problem"] == "governed_facts_changed"


@NEEDS_ATTRIBUTES
def test_c20_64_r2_the_host_filter_reaches_primitive_23(adapter, make_registry):
    """Rule 2-13 (round 2, door lens): the narrowing happens, not only its warning."""
    rows = _rows() + [{"host_id": "999", "label": "BURNS NURSING HOME, INC", "state": "CA"}]
    registry = _world(adapter, make_registry, rows, filter_columns=("state",))
    assert _resolve(registry, EXACT).outcome == "ambiguous"
    narrowed = _resolve(registry, EXACT, host_filter={"state": "AL"})
    assert narrowed.outcome == "existing", narrowed
    assert narrowed.scanned == len([r for r in rows if r["state"] == "AL"])


@NEEDS_ATTRIBUTES
def test_c20_23_r2_a_scored_answer_carries_its_score(adapter, make_registry):
    """Rule 3-9 (round 2, door lens): `None` means did not score, so an answer that
    scored carries the top score."""
    registry = _world(adapter, make_registry)
    for label, outcome in ((BAND, "ambiguous"), (NOTHING, "proposal")):
        answer = _resolve(registry, label)
        assert answer.outcome == outcome, (label, answer)
        assert answer.confidence is not None, answer
        if answer.candidates:
            assert answer.confidence == answer.candidates[0].score


def test_c20_11_r2_the_hosts_page_size_caps_a_larger_limit(adapter):
    """Rule 2-11 with the binding's ceiling (round 2, door lens): a page never holds
    more than the host serves, whatever `limit` asks for."""
    host_instances(adapter, _rows(), type_name="facility", page_size=2)
    page = adapter.find_instance_candidates(CandidateQuery(
        namespace="default", kind="entity", type_name="facility", label=EXACT, limit=10))
    assert len(page.records) == 2 and page.next_after is not None, page


@NEEDS_ATTRIBUTES
def test_c20_14_r2_a_cursor_that_never_repeats_still_ends(adapter, make_registry):
    """Rule 2-11 (round 2, build lens 3): empty pages, a fresh cursor every time."""

    class Endless:
        def __init__(self, inner):
            self.inner = inner
            self.calls = 0

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def find_instance_candidates(self, q):
            self.calls += 1
            if self.calls > 200:
                raise AssertionError("the registry kept paging past its page cap")
            return CandidatePage(records=(), known=0, complete=False,
                                 next_after=f"c{self.calls}", why_incomplete="")

    host_instances(adapter, _rows(), type_name="facility")
    registry = make_registry(Endless(adapter))
    registry.INSTANCE_READ_PAGES_MAX = 50
    seed(registry, "facility", attributes=_governed())
    answer = _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer
