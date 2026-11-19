# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c20_ingest.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

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
import decimal
import inspect
import pytest
from ontoloche.aio.adapter import CandidatePage, CandidateQuery, Capabilities, InstanceRecord, AsyncStorageAdapter
from ontoloche.ingest import (
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
    match_policy_from_mapping,
    match_policy_problem,
    norm,
    similar,
)
from ontoloche.aio.registry import AsyncRegistry
from ontoloche.types import Consumer, Refusal, ResolveContext, TypeEntry
from ontoloche.aio.contract._support import host_instances, seed, snapshot
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter
from ontoloche.actions import Effect, InputSpec, parse_ref, ref_key  # noqa: E402
from ontoloche.edges import InstanceRef, TypeRef  # noqa: E402
from ontoloche.aio.contract._support import action_family  # noqa: E402


NEEDS_ATTRIBUTES = pytest.mark.requires_capability("stores_attributes")

NEEDS_RETIRE = pytest.mark.requires_capability("stores_attributes", "indexes_membership")

NEEDS_ALIASES = pytest.mark.requires_capability(
    "stores_attributes", "indexes_membership", "stores_aliases"
)

NEEDS_MERGE = pytest.mark.requires_capability(
    "stores_attributes", "indexes_membership", "stores_events"
)

CTX = InstanceContext(label_source="NH_HealthCitations_Aug2026.csv#Provider Name", act_id="c20")

POLICY = {"match_at": 0.97, "propose_below": 0.80, "ambiguity_margin": 0.02,
          "why": "C20: the kit's thresholds, from the 14,627-row CMS file"}

AL_ONLY = {"op": "in", "attribute": "state", "value": ["AL"],
           "why": "this deployment serves Alabama facilities only"}

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

async def _world(adapter, make_registry, rows=None, *, name="facility", namespace="default",
           policy=POLICY, condition=None, **bind):
    await host_instances(adapter, _rows() if rows is None else rows, type_name=name,
                   namespace=namespace, **bind)
    registry = await make_registry(adapter)
    await seed(registry, name, namespace=namespace, attributes=_governed(policy, condition))
    return registry

async def _resolve(registry, candidate, *, type_name="facility", tier="small", **kwargs):
    return await registry.resolve_instance(candidate, CTX, type_name=type_name, tier=tier, **kwargs)

async def _successor_world(adapter, make_registry, *, old_rows, new_rows, old_governed=None,
                     new_governed=None, type_column_rows=None, old="facility",
                     new="ltc_facility"):
    """`old` retired toward `new`, each bound to its own host table (or to one table
    with a type column, for the migration window rule 2-17 is about)."""
    if type_column_rows is not None:
        for name in (old, new):
            await host_instances(adapter, type_column_rows, type_name=name, type_column="kind_name")
    else:
        await host_instances(adapter, old_rows, type_name=old)
        await host_instances(adapter, new_rows, type_name=new)
    registry = await make_registry(adapter)
    await seed(registry, old, attributes=_governed() if old_governed is None else old_governed)
    await seed(registry, new, attributes=_governed() if new_governed is None else new_governed)
    retired = await registry.retire(old, "CMS renamed the class", retired_by="user:sd",
                              successor=new)
    assert isinstance(retired, TypeEntry), retired
    return registry

async def _rewrite(adapter, name, **changes):
    """Write a type row the public calls refuse to construct (a dangling successor, a
    cycle, a successor name carrying ':'). A host with write access to the store can."""
    rec = await adapter.get_type("default", name, kind="entity")
    await adapter.put_type(dataclasses.replace(rec, **changes))

async def _all_pages(adapter, q):
    pages = []
    while True:
        page = await adapter.find_instance_candidates(q)
        pages.append(page)
        if page.next_after is None:
            return pages
        q = dataclasses.replace(q, after=page.next_after)

def _q(**kw):
    return CandidateQuery(namespace="default", kind="entity", type_name="facility", **kw)

@NEEDS_ATTRIBUTES
async def test_c20_01_the_project_stores_no_instance_and_mints_no_id(adapter, make_registry):
    """Rule 1-1. **Finding 1's check:** red when ``record_ref`` mints its own id."""
    registry = await _world(adapter, make_registry)
    before = await snapshot(adapter)
    found = await _resolve(registry, EXACT)
    proposed = await _resolve(registry, NOTHING)
    lookup = await registry.get_instance_checked("facility", "015009")

    assert found.outcome == "existing"
    assert found.ref.id == "015009" and found.candidates[0].ref.id == "015009"
    assert lookup.ref.id == "015009" and lookup.record.instance_id == "015009"
    assert proposed.outcome == "proposal"
    assert proposed.ref is None
    assert "id" not in {f.name for f in dataclasses.fields(CandidateRef)}
    assert await snapshot(adapter) == before, "resolving instances wrote to the store"

async def test_c20_02_instance_resolution_is_a_new_call_not_resolve_type(registry):
    """Rule 1-2 (R77)."""
    params = set(inspect.signature(AsyncRegistry.resolve_type).parameters)
    assert not params & {"host_filter", "instance_id", "type_name"}
    assert AsyncRegistry.resolve_instance is not AsyncRegistry.resolve_type
    answer = await registry.resolve_type(EXACT, ResolveContext(source="C20-02"), tier="small")
    assert not isinstance(answer, InstanceResolution)

async def test_c20_03_no_instance_source_refuses_every_call_never_an_empty_set(registry):
    """Rule 1-3. No table is bound, so the reference backends declare the flag False."""
    assert registry.caps.resolves_instances is False
    for answer in (await _resolve(registry, EXACT),
                   await registry.get_instance_checked("facility", "015009")):
        assert isinstance(answer, Refusal), answer
        assert answer.reason == "instance_source_absent"
        assert answer.detail["problem"] == "capability" and answer.detail["why"]

async def test_c20_04_the_protocol_adds_exactly_two_primitives_both_reads(adapter):
    """Rule 2-1. **Finding 1's check:** red when the protocol grows a write primitive."""
    instance_methods = sorted(n for n in dir(AsyncStorageAdapter) if "instance" in n)
    assert instance_methods == ["find_instance_candidates", "get_instance"]
    writes = [n for n in dir(AsyncStorageAdapter)
              if "instance" in n and n.split("_", 1)[0] in {"put", "delete", "write", "add",
                                                           "update", "upsert", "remove"}]
    assert writes == []
    await host_instances(adapter, _rows(), type_name="facility")
    before = [r.instance_id for p in await _all_pages(adapter, _q()) for r in p.records]
    await adapter.get_instance("default", "entity", "facility", "015009")
    after = [r.instance_id for p in await _all_pages(adapter, _q()) for r in p.records]
    assert before == after and len(after) == 5

async def test_c20_05_get_instance_returns_none_for_absent_never_a_manufactured_record(
    adapter, make_registry
):
    """Rule 2-2. **Finding 1's check:** red when primitive 22 manufactures a record for
    an id its table does not hold -- on every leg, and through the registry's door."""
    await host_instances(adapter, _rows(), type_name="facility")
    assert await adapter.get_instance("default", "entity", "facility", "999999") is None
    present = await adapter.get_instance("default", "entity", "facility", "015009")
    assert isinstance(present, InstanceRecord)
    assert present.instance_id == "015009" and present.label == "BURNS NURSING HOME, INC."
    registry = await make_registry(adapter)
    await seed(registry, "facility")
    absent = await registry.get_instance_checked("facility", "999999")
    assert isinstance(absent, InstanceLookup), absent
    assert absent.record is None and absent.ref is None and absent.why

async def test_c20_06_candidate_pages_follow_r58s_one_rule(adapter):
    """Rule 2-3."""
    await host_instances(adapter, _rows(), type_name="facility", page_size=2)
    pages = await _all_pages(adapter, _q())
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

async def test_c20_07_a_truncated_read_is_distinguishable_by_the_report_alone(adapter):
    """Rule 2-4."""
    await host_instances(adapter, _rows(), type_name="facility", page_size=2, scan_cap=3)
    pages = await _all_pages(adapter, _q())
    last = pages[-1]
    assert sum(len(p.records) for p in pages) == 3
    assert last.complete is False and last.next_after is None and last.why_incomplete

@NEEDS_ATTRIBUTES
async def test_c20_08_a_backend_that_cannot_count_says_none_never_zero(adapter, make_registry):
    """Rule 2-5. **Finding 1's check:** a double that says ``known=0`` over a non-empty
    page, and one that says ``None``, must both leave the registry unable to answer.
    Red when the registry stops reading ``known``."""
    await host_instances(adapter, _rows(), type_name="facility")
    page = await adapter.find_instance_candidates(_q())
    assert page.known == len(page.records) == 5

    # Round 1: the "none" case here was never seeded with a policy, so it answered
    # unknowable for the missing declaration, not for the count. The two `known=None`
    # cases (finished, and not) are the `_r1` tests below; "over" is too.
    for known in ("zero",):
        degraded = AsyncDegradedAdapter(adapter, instance_known=known)
        registry = await make_registry(degraded)
        await seed(registry, "facility", attributes=_governed())
        answer = await _resolve(registry, EXACT)
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

async def test_c20_10_an_undeclared_host_filter_key_is_reported_never_ignored(adapter):
    """Rule 2-7, on the backend and on a double that declines a key the backend honours."""
    await host_instances(adapter, _rows(), type_name="facility", filter_columns=("state",))
    page = await adapter.find_instance_candidates(_q(host_filter={"county": "Jefferson"}))
    assert page.complete is False and page.next_after is None
    assert "county" in page.why_incomplete

    declining = AsyncDegradedAdapter(adapter, instance_filters=())
    assert (await declining.capabilities()).instance_filters == frozenset()
    page = await declining.find_instance_candidates(_q(host_filter={"state": "AL"}))
    assert page.complete is False and "state" in page.why_incomplete

async def test_c20_11_label_may_order_a_page_and_never_omits_a_record(adapter):
    """Rule 2-8."""
    await host_instances(adapter, _rows(), type_name="facility", page_size=2)
    for label in (None, NOTHING, EXACT):
        ids = {r.instance_id for p in await _all_pages(adapter, _q(label=label)) for r in p.records}
        assert ids == {f[0] for f in FACILITIES}, label

async def test_c20_12_resolves_instances_defaults_false_and_refuses_when_it_is(registry):
    """Rule 2-9."""
    field = next(f for f in dataclasses.fields(Capabilities) if f.name == "resolves_instances")
    assert field.default is False
    assert registry.caps.resolves_instances is False
    assert registry.caps.reason("resolves_instances")
    answer = await _resolve(registry, NOTHING, host_filter={"state": "AL"})
    assert isinstance(answer, Refusal) and answer.reason == "instance_source_absent"

async def test_c20_13_a_declared_host_filter_key_is_honoured_faithfully(adapter):
    """Rule 2-10."""
    await host_instances(adapter, _rows(), type_name="facility", filter_columns=("state",))
    assert "state" in (await adapter.capabilities()).instance_filters
    pages = await _all_pages(adapter, _q(host_filter={"state": "AL"}))
    records = [r for p in pages for r in p.records]
    assert {r.attributes["state"] for r in records} == {"AL"} and len(records) == 3
    assert pages[-1].complete is True

@NEEDS_ATTRIBUTES
async def test_c20_14_an_identity_read_exhausts_the_cursor(adapter, make_registry):
    """Rule 2-11. One row per page: the match is on the LAST page."""
    registry = await _world(adapter, make_registry, page_size=1)
    answer = await _resolve(registry, "Mesa Vista Care")
    assert answer.outcome == "existing" and answer.ref.id == "065001"
    assert answer.scanned == 5

@NEEDS_ATTRIBUTES
async def test_c20_63_host_filter_is_a_mapping_of_declared_keys(adapter, make_registry):
    """Rule 2-12. **Finding 1's check:** red when a free-form expression is accepted."""
    registry = await _world(adapter, make_registry, filter_columns=("state",))
    for expression in ("state = 'AL'", ("state", "AL"), ["state", "AL"]):
        with pytest.raises(TypeError, match="2-12"):
            await _resolve(registry, EXACT, host_filter=expression)
    assert (await _resolve(registry, EXACT, host_filter={"state": "AL"})).outcome == "existing"

@NEEDS_ATTRIBUTES
async def test_c20_64_a_narrowed_proposal_says_so(adapter, make_registry):
    """Rule 2-13."""
    registry = await _world(adapter, make_registry, filter_columns=("state",))
    narrowed = await _resolve(registry, NOTHING, host_filter={"state": "AL"})
    assert narrowed.outcome == "proposal" and narrowed.complete is True
    assert "instance_narrowed_proposal:state" in narrowed.warnings
    whole = await _resolve(registry, NOTHING)
    assert whole.outcome == "proposal"
    assert not [w for w in whole.warnings if w.startswith("instance_narrowed_proposal")]

@NEEDS_ATTRIBUTES
async def test_c20_65_an_unfaithful_record_is_refused_citing_the_flat_form(adapter, make_registry):
    """Rule 2-14."""
    await host_instances(adapter, _rows(), type_name="facility")
    unfaithful = AsyncDegradedAdapter(adapter, instance_rename="facility#ward")
    registry = await make_registry(unfaithful)
    await seed(registry, "facility", attributes=_governed())
    for answer in (await _resolve(registry, EXACT),
                   await registry.get_instance_checked("facility", "015009")):
        assert isinstance(answer, Refusal), answer
        assert answer.reason == "instance_source_absent"
        assert answer.detail["problem"] == "unfaithful_reference"

@NEEDS_ATTRIBUTES
async def test_c20_66_primitive_22_is_judged_by_the_entrys_predicate(adapter, make_registry):
    """Rule 2-15: a row the predicate fails is None with a why, and one it cannot
    decide is a refusal, never a silent pass."""
    county = {"op": "eq", "attribute": "county", "value": "Jefferson",
              "why": "a column this host does not carry"}
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="home")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed(condition=AL_ONLY))
    await seed(registry, "home", attributes=_governed(condition=county))

    kept = await registry.get_instance_checked("facility", "015009")
    assert kept.record is not None and kept.why == ""
    assert kept.ref.id == "015009" and kept.governed_by == "default:facility"
    excluded = await registry.get_instance_checked("facility", "055001")
    assert excluded.record is None and excluded.ref is None and "predicate" in excluded.why
    refused = await registry.get_instance_checked("home", "015009")
    assert isinstance(refused, Refusal), refused
    assert refused.reason == "instance_source_absent"
    assert refused.detail["problem"] == "predicate_undecidable"

    # A predicate written past validation (a host with write access to the store, or a
    # row from before the validator) is one the registry cannot decide. It refuses, the
    # way resolve_instance answers unknowable, never hands the row out as if no
    # predicate were declared. Round 0 security review: this branch failed open.
    rec = await adapter.get_type("default", "facility", kind="entity")
    broken = {"op": "eq", "attribute": "state"}  # no value, no why
    await adapter.put_type(dataclasses.replace(
        rec, attributes={**rec.attributes, INSTANCE_CONDITION_KEY: broken}))
    malformed = await registry.get_instance_checked("facility", "015009")
    assert isinstance(malformed, Refusal), malformed
    assert malformed.reason == "instance_source_absent"
    assert malformed.detail["problem"] == "predicate_undecidable"
    assert (await _resolve(registry, EXACT)).outcome == "unknowable"

@NEEDS_RETIRE
async def test_ingest_finding_2_one_id_answers_alike_under_both_names(adapter, make_registry):
    """INGEST.md 8.1a finding 2 (E2). Not an id of its own: the construction that
    found it, kept beside rule 2-15.

    The kit called primitive 22 once, under the declared name, and judged the row with
    the declared entry's predicate. So after `facility` was retired toward
    `ltc_facility` and the host migrated its rows, one identity was ABSENT under its old
    name and present under its new one, while `resolve_instance` answered for both."""
    both = _governed(condition=AL_ONLY)
    registry = await _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows(),
                                old_governed=both, new_governed=both)
    for instance_id, present in (("015009", True), ("055001", False), ("999999", False)):
        answers = [await registry.get_instance_checked(name, instance_id)
                   for name in ("facility", "ltc_facility")]
        for answer in answers:
            assert isinstance(answer, InstanceLookup), answer
            assert answer.governed_by == "default:ltc_facility"
            assert (answer.record is not None) is present, (instance_id, answer)
        assert answers[0].ref == answers[1].ref
        assert answers[0].record == answers[1].record
    assert (await registry.get_instance_checked("facility", "015009")).warnings[:1] == (
        "instance_type_succeeded:ltc_facility",)

@NEEDS_ATTRIBUTES
async def test_c20_75_duplicate_ids_under_one_name_make_the_extent_uncountable(
    adapter, make_registry
):
    """Rule 2-16."""
    rows = _rows() + [{"host_id": "015010", "label": "COOSA VALLEY HEALTH", "state": "AL"}]
    registry = await _world(adapter, make_registry, rows)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "2-16" in answer.why_incomplete
    assert "015010" in answer.why_incomplete

@NEEDS_RETIRE
async def test_c20_89_one_row_under_two_member_names_is_one_candidate(adapter, make_registry):
    """Rule 2-17 (round 3's K2): mid-migration, one facility under both names."""
    rows = ([dict(r, kind_name="facility") for r in _rows()]
            + [dict(_rows()[0], kind_name="ltc_facility")])
    registry = await _successor_world(adapter, make_registry, old_rows=None, new_rows=None,
                                type_column_rows=rows)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "existing", answer
    assert answer.known == 1 and answer.ref.id == "015009"
    assert answer.ref.type.name == "ltc_facility"

def test_c20_15_the_outcome_vocabulary_is_closed_at_five():
    """Rule 3-1."""
    assert INSTANCE_OUTCOMES == (
        "existing", "ambiguous", "proposal", "not_an_instance", "unknowable")

def test_c20_16_resolve_instance_is_a_distinct_call():
    """Rule 3-2."""
    params = inspect.signature(AsyncRegistry.resolve_instance).parameters
    assert set(params) - {"self"} == {
        "candidate", "context", "type_name", "namespace", "tier", "host_filter"}
    assert "InstanceContext" in str(params["context"].annotation)
    assert "host_filter" not in inspect.signature(AsyncRegistry.resolve_type).parameters

@NEEDS_ATTRIBUTES
async def test_c20_17_ambiguous_is_decided_over_the_set_before_existing(adapter, make_registry):
    """Rule 3-3: at-or-above `match_at`, AND within `ambiguity_margin` of the top."""
    rows = _rows() + [{"host_id": "015099", "label": "BURNS NURSING HOMES INC", "state": "AL"}]
    wide = {**POLICY, "match_at": 0.99, "ambiguity_margin": 0.03}
    registry = await _world(adapter, make_registry, rows, policy=wide)
    tied = await _resolve(registry, EXACT)                 # 1.0 and 0.9778, margin 0.03
    assert tied.outcome == "ambiguous"
    assert {c.ref.id for c in tied.candidates} == {"015009", "015099"}

    await host_instances(adapter, rows, type_name="home")
    narrow = await make_registry(adapter)
    await seed(narrow, "home", attributes=_governed({**wide, "ambiguity_margin": 0.01}))
    assert (await _resolve(narrow, EXACT, type_name="home")).outcome == "existing"

@NEEDS_ATTRIBUTES
async def test_c20_18_ambiguous_carries_no_ref_and_every_tied_candidate(adapter, make_registry):
    """Rule 3-4. **Finding 1's check:** red when `ambiguous` keeps a ref or drops a tie."""
    rows = _rows() + [{"host_id": "015098", "label": "BURNS NURSING HOME INC", "state": "AL"},
                      {"host_id": "015097", "label": "Burns Nursing Home, Inc", "state": "AL"}]
    registry = await _world(adapter, make_registry, rows)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "ambiguous"
    assert answer.ref is None
    assert sorted(c.ref.id for c in answer.candidates) == ["015009", "015097", "015098"]
    assert answer.known == 3
    assert answer.candidate is not None and answer.candidate.resolution == "ambiguous"

@NEEDS_ATTRIBUTES
async def test_c20_19_an_unfinished_read_is_unknowable_whatever_it_found(adapter, make_registry):
    """Rule 3-5: the exact match is on the first page and the read was cut off."""
    registry = await _world(adapter, make_registry, page_size=1, scan_cap=2)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.ref is None
    assert answer.complete is False and "cap" in answer.why_incomplete

@NEEDS_ATTRIBUTES
async def test_c20_20_no_incomplete_result_carries_a_decided_outcome(adapter, make_registry):
    """Rule 3-6, over every incomplete path this suite can construct."""
    await host_instances(adapter, _rows(), type_name="facility", scan_cap=2, page_size=1)
    await host_instances(adapter, _rows(), type_name="home")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "home", attributes=_governed())
    await _rewrite(adapter, "home", status="retired", successor="ghost")
    answers = [await _resolve(registry, label, type_name=t)
               for t in ("facility", "home") for label in (EXACT, BAND, NOTHING)]
    assert any(a.complete is False for a in answers)
    for a in answers:
        if a.complete is False:
            assert a.outcome in {"unknowable", "not_an_instance"}, a

@NEEDS_ATTRIBUTES
async def test_c20_21_proposal_requires_every_page_complete(adapter, make_registry):
    """Rule 3-7: nothing matches on the pages read, and the read was cut off."""
    registry = await _world(adapter, make_registry, page_size=1, scan_cap=3)
    answer = await _resolve(registry, NOTHING)
    assert answer.outcome == "unknowable"
    complete = await _world(adapter, make_registry, name="home")
    assert (await _resolve(complete, NOTHING, type_name="home")).outcome == "proposal"

@NEEDS_ATTRIBUTES
async def test_c20_22_not_an_instance_reads_no_host_table(adapter, make_registry):
    """Rule 3-8."""
    await host_instances(adapter, _rows(), type_name="facility")
    counted = AsyncDegradedAdapter(adapter)
    registry = await make_registry(counted)
    await seed(registry, "facility", attributes=_governed())
    for word in ("Provider Name", "facility", "  NURSING HOME "):
        answer = await _resolve(registry, word)
        assert answer.outcome == "not_an_instance", word
        assert answer.scanned == 0 and answer.ref is None
    assert counted.instance_reads == 0
    assert (await _resolve(registry, EXACT)).outcome == "existing" and counted.instance_reads > 0

@NEEDS_ATTRIBUTES
async def test_c20_23_confidence_none_means_did_not_score(adapter, make_registry):
    """Rule 3-9."""
    registry = await _world(adapter, make_registry, page_size=1, scan_cap=1)
    assert (await _resolve(registry, EXACT)).confidence is None
    scored = await _world(adapter, make_registry, name="home")
    answer = await _resolve(scored, EXACT, type_name="home")
    assert isinstance(answer.confidence, float) and answer.confidence == 1.0
    assert (await _resolve(scored, "Provider Name", type_name="home")).confidence is None

async def test_c20_24_the_call_takes_no_threshold_and_no_predicate(registry):
    """Rule 3-10."""
    params = set(inspect.signature(AsyncRegistry.resolve_instance).parameters)
    assert not params & {"min_confidence", "predicate", "match_at", "condition"}
    for kwarg in ("min_confidence", "predicate"):
        with pytest.raises(TypeError):
            await registry.resolve_instance(EXACT, CTX, type_name="facility", tier="small",
                                      **{kwarg: 0.5})

@NEEDS_ATTRIBUTES
async def test_c20_25_tier_is_required_and_echoed(adapter, make_registry):
    """Rule 3-11. **Finding 1's check:** red when the tier is not the caller's."""
    registry = await _world(adapter, make_registry)
    for tier in ("small", "large", "human"):
        assert (await _resolve(registry, EXACT, tier=tier)).tier == tier
        assert (await _resolve(registry, "Provider Name", tier=tier)).tier == tier
    with pytest.raises(TypeError):
        await registry.resolve_instance(EXACT, CTX, type_name="facility")
    with pytest.raises(TypeError, match="3-11"):
        await _resolve(registry, EXACT, tier="")

@NEEDS_ATTRIBUTES
async def test_c20_26_an_undecidable_predicate_is_unknowable_not_narrower(adapter, make_registry):
    """Rule 3-12."""
    county = {"op": "eq", "attribute": "county", "value": "Jefferson",
              "why": "a column the host does not carry"}
    registry = await _world(adapter, make_registry, condition=county)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.ref is None
    assert "undecidable" in answer.reason

@NEEDS_ATTRIBUTES
async def test_c20_67_a_read_of_zero_rows_is_unknowable(adapter, make_registry):
    """Rule 3-13."""
    registry = await _world(adapter, make_registry, rows=[])
    answer = await _resolve(registry, NOTHING)
    assert answer.outcome == "unknowable" and answer.scanned == 0
    assert answer.why_incomplete == "scanned=0"

@NEEDS_RETIRE
async def test_c20_68_the_read_follows_the_whole_successor_chain(adapter, make_registry):
    """Rule 3-14: two hops, each reported."""
    for name in ("facility", "ltc_facility", "ltc_home"):
        await host_instances(adapter, _rows() if name == "ltc_home" else [], type_name=name)
    registry = await make_registry(adapter)
    for name in ("facility", "ltc_facility", "ltc_home"):
        await seed(registry, name, attributes=_governed())
    for old, new in (("facility", "ltc_facility"), ("ltc_facility", "ltc_home")):
        retired = await registry.retire(old, "renamed", retired_by="user:sd", successor=new)
        assert isinstance(retired, TypeEntry), retired
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "existing" and answer.ref.type.name == "ltc_home"
    assert [w for w in answer.warnings if w.startswith("instance_type_succeeded")] == [
        "instance_type_succeeded:ltc_facility", "instance_type_succeeded:ltc_home"]
    assert answer.governed_by == "default:ltc_home"

@NEEDS_ATTRIBUTES
async def test_c20_76_a_dangling_successor_stops_and_never_falls_back(adapter, make_registry):
    """Rule 3-15."""
    registry = await _world(adapter, make_registry)
    await _rewrite(adapter, "facility", status="retired", successor="ghost")
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False
    assert "ghost" in answer.why_incomplete and "3-15" in answer.why_incomplete
    assert answer.scanned == 0 and answer.confidence is None

@NEEDS_ATTRIBUTES
async def test_c20_77_the_walk_carries_a_hop_cap(adapter, make_registry):
    """Rule 3-16."""
    names = [f"t{i:02d}" for i in range(INSTANCE_CHAIN_CAP + 2)]
    await host_instances(adapter, _rows(), type_name=names[0])
    registry = await make_registry(adapter)
    for name in names:
        await seed(registry, name, attributes=_governed())
    for here, nxt in zip(names, names[1:]):
        await _rewrite(adapter, here, status="retired", successor=nxt)
    answer = await _resolve(registry, EXACT, type_name=names[0])
    assert answer.outcome == "unknowable" and "3-16" in answer.why_incomplete

@NEEDS_ATTRIBUTES
async def test_c20_78_a_cycle_is_incomplete_and_the_walk_survives_it(adapter, make_registry):
    """Rule 3-17."""
    await host_instances(adapter, _rows(), type_name="facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "home", attributes=_governed())
    await _rewrite(adapter, "facility", status="retired", successor="home")
    await _rewrite(adapter, "home", status="retired", successor="facility")
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "3-17" in answer.why_incomplete

@NEEDS_RETIRE
async def test_c20_79_changed_governed_facts_across_the_closure_are_unknowable(
    adapter, make_registry
):
    """Rule 3-18: both facts differ, and the why names both."""
    registry = await _successor_world(
        adapter, make_registry, old_rows=_rows(), new_rows=_rows(),
        new_governed=_governed({**POLICY, "match_at": 0.9}, AL_ONLY))
    for name in ("facility", "ltc_facility"):
        answer = await _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "unknowable", (name, answer)
        assert "MatchPolicy" in answer.why_incomplete
        assert "tenancy predicate" in answer.why_incomplete

@NEEDS_RETIRE
async def test_c20_80_the_extent_is_the_whole_closure_forward(adapter, make_registry):
    """Rule 3-19: a row still written under the retired name is found from it."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    new = _rows()[1:]
    registry = await _successor_world(adapter, make_registry, old_rows=old, new_rows=new)
    answer = await _resolve(registry, EXACT, type_name="facility")
    assert answer.outcome == "existing" and answer.ref.id == "015009"
    assert answer.scanned == 5

@NEEDS_RETIRE
async def test_c20_86_the_closure_walks_backward_too(adapter, make_registry):
    """Rule 3-20: the SURVIVOR finds the row written under the retired name."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    registry = await _successor_world(adapter, make_registry, old_rows=old, new_rows=_rows()[1:])
    answer = await _resolve(registry, EXACT, type_name="ltc_facility")
    assert answer.outcome == "existing" and answer.ref.id == "015009"
    assert answer.scanned == 5
    lookup = await registry.get_instance_checked("ltc_facility", "015009")
    assert lookup.record is not None and lookup.record.type_name == "facility"

@NEEDS_MERGE
@pytest.mark.requires_capability("stores_aliases")
async def test_c20_87_aliases_are_members_of_the_closure(adapter, make_registry):
    """Rule 3-21: `merge_types` writes a successor AND an alias; both are read."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    await host_instances(adapter, old, type_name="facility")
    await host_instances(adapter, _rows()[1:], type_name="ltc_facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    merged = await registry.merge_types("facility", "ltc_facility", "one class",
                                  merged_by="user:sd", acknowledge=("definitions_diverge", "no_consumer_evidence"))
    assert not isinstance(merged, Refusal), merged
    assert "facility" in (await adapter.get_type("default", "ltc_facility", kind="entity")).aliases
    answer = await _resolve(registry, EXACT, type_name="ltc_facility")
    assert answer.outcome == "existing" and answer.ref.id == "015009"

@NEEDS_ATTRIBUTES
async def test_c20_88_a_successor_name_carrying_a_separator_stops_the_walk(adapter, make_registry):
    """Rule 3-22 (round 3's K8)."""
    registry = await _world(adapter, make_registry)
    for bad in ("ward:north", "ward#north"):
        await _rewrite(adapter, "facility", status="retired", successor=bad)
        answer = await _resolve(registry, EXACT)
        assert answer.outcome == "unknowable" and "3-22" in answer.why_incomplete, bad

@NEEDS_ATTRIBUTES
async def test_c20_35_the_policy_is_declared_on_the_entry_and_rides_approval(registry):
    """Rule 5-1."""
    proposal = await registry.propose_type("facility", "a nursing facility", [], "user:sd",
                                     kind="entity", attributes=_governed())
    entry = proposal if isinstance(proposal, TypeEntry) else await registry.approve(
        proposal.id, "user:sd")
    assert entry.attributes[MATCH_POLICY_KEY] == POLICY
    params = set(inspect.signature(AsyncRegistry.resolve_instance).parameters)
    assert not params & {"match_at", "propose_below", "ambiguity_margin", "policy"}

async def _refused_declaration(registry, attributes, *, name="facility", kind="entity"):
    answer = await registry.propose_type(name, f"a {name}", [], "user:sd", kind=kind,
                                   attributes=attributes)
    assert isinstance(answer, Refusal), answer
    assert answer.reason == "attributes_schema_violation"
    return answer

async def test_c20_36_propose_below_above_match_at_is_refused(registry):
    """Rule 5-2."""
    assert match_policy_problem({**POLICY, "propose_below": 0.99})
    await _refused_declaration(registry, {MATCH_POLICY_KEY: {**POLICY, "propose_below": 0.99}})
    assert match_policy_problem({**POLICY, "propose_below": 0.97}) is None

async def test_c20_37_the_policy_why_is_required(registry):
    """Rule 5-3."""
    for why in (None, "", "   "):
        bad = {k: v for k, v in POLICY.items() if k != "why"}
        if why is not None:
            bad["why"] = why
        assert match_policy_problem(bad), why
        await _refused_declaration(registry, {MATCH_POLICY_KEY: bad})

@NEEDS_ATTRIBUTES
async def test_c20_38_the_gate_mints_no_verdict_vocabulary(adapter, make_registry):
    """Rule 5-4."""
    registry = await _world(adapter, make_registry)
    outcomes = {(await _resolve(registry, c)).outcome
                for c in (EXACT, BAND, NOTHING, "Provider Name", "Highlands Health Rehab")}
    assert outcomes == {"existing", "ambiguous", "proposal", "not_an_instance"}
    assert outcomes <= set(INSTANCE_OUTCOMES)

@NEEDS_ATTRIBUTES
async def test_c20_39_unscored_and_unfinished_are_unknowable_at_the_gate(adapter, make_registry):
    """Rule 5-5."""
    unscored = await _world(adapter, make_registry, policy=None)
    answer = await _resolve(unscored, EXACT)
    assert answer.outcome == "unknowable" and answer.confidence is None
    assert "MatchPolicy" in answer.why_incomplete
    cut = await _world(adapter, make_registry, name="home", page_size=1, scan_cap=2)
    assert (await _resolve(cut, EXACT, type_name="home")).outcome == "unknowable"

@NEEDS_ATTRIBUTES
async def test_c20_40_entries_may_differ_and_callers_may_not(adapter, make_registry):
    """Rule 5-6."""
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="home")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "home", attributes=_governed(
        {"match_at": 0.85, "propose_below": 0.5, "ambiguity_margin": 0.01, "why": "loose"}))
    assert (await _resolve(registry, BAND)).outcome == "ambiguous"
    assert (await _resolve(registry, BAND, type_name="home")).outcome == "existing"
    with pytest.raises(TypeError):
        await registry.resolve_instance(BAND, CTX, type_name="facility", tier="small",
                                  match_policy=POLICY)

@NEEDS_ATTRIBUTES
async def test_c20_41_the_policy_in_force_is_recorded(adapter, make_registry):
    """Rule 5-7. Its carrier is rule 5-11's `governed_by` until row 7c's invocation."""
    registry = await _world(adapter, make_registry)
    answer = await _resolve(registry, EXACT)
    assert answer.governed_by == "default:facility"
    ns, name = answer.governed_by.split(":")
    entry = await adapter.get_type(ns, name, kind="entity")
    assert entry.attributes[MATCH_POLICY_KEY] == POLICY
    if not registry.caps.stores_invocations:
        return
    # The invocation half (row 7c, amendment A5): the thresholds that governed travel
    # onto the record WITH the entry that governed them, copied, so the reviewer of a
    # proposal can say which entry's numbers produced it (`I-7`).
    await _ingest_family(registry)
    rec = await registry.record_invocation(
        "propose_facility", {"instance": (await _resolve(registry, NOTHING)).candidate},
        actor="ai:ingest", outcome="applied",
        match_policy=match_policy_from_mapping(POLICY), governed_by=answer.governed_by,
    )
    assert not isinstance(rec, Refusal), rec
    assert rec.declared_policy["match_policy"] == {
        "governed_by": "default:facility", "match_at": 0.97, "propose_below": 0.80,
        "ambiguity_margin": 0.02,
    }, rec.declared_policy

@NEEDS_ATTRIBUTES
async def test_c20_73_existing_requires_exactly_one_in_the_tied_set(adapter, make_registry):
    """Rule 5-8."""
    registry = await _world(adapter, make_registry)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "existing"
    assert answer.known == 1 and len(answer.candidates) == 1

@NEEDS_ATTRIBUTES
async def test_c20_74_a_top_candidate_in_the_band_is_ambiguous(adapter, make_registry):
    """Rule 5-9: 0.9, between propose_below 0.80 and match_at 0.97."""
    registry = await _world(adapter, make_registry)
    answer = await _resolve(registry, BAND)
    assert answer.outcome == "ambiguous" and answer.ref is None
    assert 0.80 <= answer.confidence < 0.97

@NEEDS_RETIRE
async def test_c20_82_a_successor_does_not_inherit_the_match_policy(adapter, make_registry):
    """Rule 5-10."""
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed({**POLICY, "match_at": 0.9}))
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "MatchPolicy" in answer.why_incomplete
    assert "tenancy predicate" not in answer.why_incomplete

@NEEDS_RETIRE
async def test_c20_85_governed_by_names_the_entry_that_judged(adapter, make_registry):
    """Rule 5-11."""
    plain = await _world(adapter, make_registry, name="home")
    assert (await _resolve(plain, EXACT, type_name="home")).governed_by == "default:home"
    moved = await _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows())
    for name in ("facility", "ltc_facility"):
        assert (await _resolve(moved, EXACT, type_name=name)).governed_by == "default:ltc_facility"
    assert (await moved.get_instance_checked("facility", "015009")).governed_by == \
        "default:ltc_facility"

@NEEDS_ATTRIBUTES
async def test_c20_90_the_tied_set_has_a_floor(adapter, make_registry):
    """Rule 5-12 (round 3's K7): a margin wide enough to reach every row, and only the
    candidates at or above `propose_below` may tie."""
    wide = {**POLICY, "ambiguity_margin": 0.99}
    registry = await _world(adapter, make_registry, policy=wide)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "existing" and answer.known == 1

def _cond(op, attribute="state", value="AL", **kw):
    return {"op": op, "attribute": attribute, "value": value, "why": "C20", **kw}

async def test_c20_42_the_condition_vocabulary_is_closed_at_twelve(registry):
    """Rule 6-1."""
    assert len(CONDITION_TERMS) == 12
    assert condition_problem(_cond("startswith"))
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("startswith")})

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

async def test_c20_47_comparisons_refuse_a_null_operand(registry):
    """Rule 6-6."""
    for op in ("eq", "ne", "lt", "lte", "gt", "gte"):
        assert condition_problem(_cond(op, value=None)), op
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("eq", value=None)})

async def test_c20_48_in_and_not_in_take_a_sequence(registry):
    """Rule 6-7."""
    for op in ("in", "not_in"):
        assert condition_problem(_cond(op, value="AL")), op
        assert condition_problem(_cond(op, value=["AL", "CA"])) is None
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("in", value="AL")})

def _combinator(op, terms, **kw):
    return {"op": op, "terms": terms, "why": "C20", **kw}

async def test_c20_49_a_combinator_needs_terms(registry):
    """Rule 6-8."""
    for op in CONDITION_COMBINATORS:
        assert condition_problem(_combinator(op, [])), op
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _combinator("all_of", [])})

async def test_c20_50_a_combinator_carries_no_attribute_or_value(registry):
    """Rule 6-9."""
    term = _cond("eq")
    for extra in ({"attribute": "state"}, {"value": "AL"}):
        assert condition_problem(_combinator("any_of", [term], **extra)), extra
    await _refused_declaration(
        registry, {INSTANCE_CONDITION_KEY: _combinator("any_of", [term], value="AL")})

async def test_c20_51_an_operator_carries_no_terms(registry):
    """Rule 6-10."""
    assert condition_problem(_cond("eq", terms=[_cond("eq")]))
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("eq", terms=[_cond("eq")])})

async def test_c20_52_the_condition_why_is_required(registry):
    """Rule 6-11."""
    for why in ("", "   "):
        assert condition_problem({**_cond("eq"), "why": why}), why
    bare = {k: v for k, v in _cond("eq").items() if k != "why"}
    assert condition_problem(bare)
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: bare})

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

async def test_c20_54_there_is_no_not_and_no_matches(registry):
    """Rule 6-13."""
    assert "not" not in CONDITION_TERMS and "matches" not in CONDITION_TERMS
    assert set(CONDITION_OPERATORS) | set(CONDITION_COMBINATORS) == set(CONDITION_TERMS)
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _cond("matches", value="^A")})
    await _refused_declaration(registry, {INSTANCE_CONDITION_KEY: _combinator("not", [_cond("eq")])})

@NEEDS_ATTRIBUTES
async def test_c20_55_the_condition_rides_approval_and_is_never_a_parameter(registry):
    """Rule 6-14."""
    entry = await seed(registry, "facility", attributes=_governed(condition=AL_ONLY))
    assert entry.attributes[INSTANCE_CONDITION_KEY] == AL_ONLY
    with pytest.raises(TypeError):
        await registry.resolve_instance(EXACT, CTX, type_name="facility", tier="small",
                                  predicate=AL_ONLY)

@NEEDS_ATTRIBUTES
async def test_c20_56_the_registry_evaluates_the_condition_over_every_record(
    adapter, make_registry
):
    """Rule 6-15: no host_filter at all, and the CO row is still excluded."""
    registry = await _world(adapter, make_registry, condition=AL_ONLY)
    answer = await _resolve(registry, "Mesa Vista Care")
    assert answer.outcome == "proposal"
    assert all(c.discriminators["state"] == "AL" for c in answer.candidates)
    assert (await registry.get_instance_checked("facility", "065001")).record is None

@NEEDS_ATTRIBUTES
async def test_c20_57_an_undecided_candidate_is_never_silently_dropped(adapter, make_registry):
    """Rule 6-16: one row's state is NULL."""
    rows = _rows() + [{"host_id": "015077", "label": "SOMEWHERE ELSE", "state": None}]
    registry = await _world(adapter, make_registry, rows, condition=AL_ONLY)
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "undecidable" in answer.reason

def test_c20_58_the_candidate_primitive_takes_no_tenant(adapter):
    """Rule 6-17 (R24, R59). **Finding 1's check:** red when a tenant field appears."""
    assert [f.name for f in dataclasses.fields(CandidateQuery)] == [
        "namespace", "kind", "type_name", "label", "host_filter", "limit", "after"]
    for name in ("get_instance", "find_instance_candidates"):
        # The protocol's, and the bound method of the backend that answers (a forwarding
        # proxy has no class attribute of its own, C20-09's reason).
        for method in (getattr(AsyncStorageAdapter, name), getattr(adapter, name)):
            params = set(inspect.signature(method).parameters)
            assert not {p for p in params if "tenant" in p}, (method, name)
    assert set(inspect.signature(AsyncStorageAdapter.find_instance_candidates).parameters) == {
        "self", "q"}

@NEEDS_RETIRE
async def test_c20_83_a_successor_does_not_inherit_the_predicate(adapter, make_registry):
    """Rule 6-18."""
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed(condition=AL_ONLY))
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "tenancy predicate" in answer.why_incomplete
    assert "MatchPolicy" not in answer.why_incomplete

@NEEDS_ATTRIBUTES
async def test_c20_59_blast_radius_is_reported_incomplete_never_safe(adapter, make_registry):
    """Rule 7-1 (Q87's default: warn)."""
    registry = await _world(adapter, make_registry)
    assert "consumers_unregistered" in (await _resolve(registry, EXACT)).warnings
    registered = await registry.register_consumer(Consumer(id="billing", gate="facility"))
    assert not isinstance(registered, Refusal), registered
    assert "consumers_unregistered" not in (await _resolve(registry, EXACT)).warnings

def test_c20_60_no_consumer_registration_mechanism_is_added():
    """Rule 7-2."""
    public = {n for n in dir(AsyncRegistry) if not n.startswith("_")}
    assert {n for n in public if "instance" in n} == {"resolve_instance", "get_instance_checked"}
    assert not {n for n in public if "consumer" in n and "instance" in n}

async def test_c20_61_the_entity_vocabulary_is_registered_through_the_shipped_calls(registry):
    """Rule 7-3. A governed fact belongs on a kind="entity" entry and nowhere else."""
    public = {n for n in dir(AsyncRegistry) if not n.startswith("_")}
    assert not {n for n in public if "entity" in n}
    await _refused_declaration(registry, {MATCH_POLICY_KEY: POLICY}, name="admitted", kind="event")

@NEEDS_ATTRIBUTES
async def test_c20_62_no_tenancy_predicate_is_unfiltered_and_says_so(adapter, make_registry):
    """Rule 7-4."""
    open_ = await _world(adapter, make_registry)
    answer = await _resolve(open_, "Mesa Vista Care")
    assert answer.outcome == "existing" and "no_tenancy_predicate" in answer.warnings
    closed = await _world(adapter, make_registry, name="home", condition=AL_ONLY)
    assert "no_tenancy_predicate" not in (await _resolve(closed, EXACT, type_name="home")).warnings

@NEEDS_RETIRE
async def test_c20_84_a_successor_declares_its_own_governed_facts(adapter, make_registry):
    """Rule 7-5: a successor declaring neither fact answers unknowable; declaring the
    same facts answers."""
    await host_instances(adapter, [], type_name="facility")
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility")
    await registry.retire("facility", "renamed", retired_by="user:sd", successor="ltc_facility")
    assert (await _resolve(registry, EXACT)).outcome == "unknowable"

    same = await _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows(),
                            old="home", new="ltc_home")
    assert (await _resolve(same, EXACT, type_name="home")).outcome == "existing"

@NEEDS_RETIRE
async def test_c20_79_r1_a_reworded_why_on_identical_facts_is_not_a_change(adapter, make_registry):
    """Rule 3-18 under E10 (INGEST.md 5.3): "different" is the three thresholds and the
    predicate's TERMS, never the prose. Round 1 found the raw mappings compared, so a
    reworded `why` stopped the loop, and an `in` list in another order did too."""
    reworded = {**POLICY, "why": "same numbers, reworded by the other team"}
    same_terms = {"op": "in", "attribute": "state", "value": ["AL", "GA"],
                  "why": "one deployment, two states"}
    other_order = {"op": "in", "attribute": "state", "value": ["GA", "AL"],
                   "why": "reworded, and the states listed the other way round"}
    registry = await _successor_world(
        adapter, make_registry, old_rows=_rows(), new_rows=[],
        old_governed=_governed(condition=same_terms),
        new_governed=_governed(policy=reworded, condition=other_order))
    for name in ("facility", "ltc_facility"):
        answer = await _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "existing", (name, answer)
        lookup = await registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup

@NEEDS_RETIRE
async def test_c20_79_r1_a_changed_threshold_is_still_a_change(adapter, make_registry):
    """The control for the test above: one threshold moved is a different MatchPolicy."""
    moved = {**POLICY, "match_at": 0.98}
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed(policy=moved))
    answer = await _resolve(registry, EXACT, type_name="ltc_facility")
    assert answer.outcome == "unknowable" and "MatchPolicy" in answer.why_incomplete

@NEEDS_RETIRE
async def test_c20_89_r1_the_two_doors_judge_the_same_copy(adapter, make_registry):
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
    registry = await _successor_world(
        adapter, make_registry, old_rows=None, new_rows=None,
        type_column_rows=[stale, moved],
        old_governed=_governed(condition=ca_only), new_governed=_governed(condition=ca_only))
    for name in ("facility", "ltc_facility"):
        answer = await _resolve(registry, "Willowbrooke Ct Skilled Care Center", type_name=name)
        assert answer.outcome != "existing", (name, answer)
        assert all(c.ref.type.name == "ltc_facility" for c in answer.candidates), answer
        lookup = await registry.get_instance_checked(name, "055001")
        assert isinstance(lookup, InstanceLookup) and lookup.record is None, lookup

@NEEDS_RETIRE
async def test_c20_89_r1_the_kept_copy_is_the_effective_names(adapter, make_registry):
    """Rule 2-17's other half, at primitive 22's door: with both copies present the
    lookup returns the effective name's copy, never the first one found."""
    stale = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL",
             "kind_name": "facility"}
    moved = dict(stale, label="BURNS NURSING HOME", kind_name="ltc_facility")
    registry = await _successor_world(adapter, make_registry, old_rows=None, new_rows=None,
                                type_column_rows=[stale, moved])
    for name in ("facility", "ltc_facility"):
        lookup = await registry.get_instance_checked(name, "015009")
        assert lookup.record.type_name == "ltc_facility", (name, lookup)
        assert lookup.record.label == "BURNS NURSING HOME"
        assert lookup.ref.type.name == "ltc_facility"

@NEEDS_RETIRE
async def test_c20_66_r1_an_unreadable_member_refuses_never_hands_out(adapter, make_registry):
    """Rule 2-15, `I-1` at primitive 22's door (round 1, door lens T1). The host binds
    only the successor's table, so the lookup under the retired name cannot be made:
    the row found under the other is a decision over a partial extent."""
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    retired = await registry.retire("facility", "CMS renamed the class", retired_by="user:sd",
                              successor="ltc_facility")
    assert isinstance(retired, TypeEntry), retired
    for name in ("facility", "ltc_facility"):
        lookup = await registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, Refusal), (name, lookup)
        assert lookup.detail["problem"] == "lookup_incomplete"
        assert (await _resolve(registry, EXACT, type_name=name)).outcome == "unknowable"

async def test_c20_66_r1_a_repeated_id_refuses_never_reads_absent(adapter, make_registry):
    """Rule 2-15 with rule 2-16 (door lens T2): a citations-shaped host carries CCN
    015009 on two rows. The lookup refuses; an id present twice is never `absent`."""
    rows = _rows() + [dict(_rows()[0], label="BURNS NURSING HOME INC (2023 survey)")]
    await host_instances(adapter, rows, type_name="facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility")
    lookup = await registry.get_instance_checked("facility", "015009")
    assert isinstance(lookup, Refusal), lookup
    assert lookup.detail["problem"] == "lookup_incomplete"

async def test_c20_05_r1_a_type_column_binding_never_manufactures(adapter, make_registry):
    """Rule 2-2 on the type-column path (door lens T5): one host table, rows typed by a
    column. An id held only as a `facility` is absent as a `hospital`."""
    rows = [dict(r, kind_name="facility") for r in _rows()] + [
        {"host_id": "019999", "label": "A HOSPITAL", "state": "AL", "kind_name": "hospital"}]
    for name in ("facility", "hospital"):
        await host_instances(adapter, rows, type_name=name, type_column="kind_name")
    assert await adapter.get_instance("default", "entity", "hospital", "015009") is None
    assert (await adapter.get_instance("default", "entity", "hospital", "019999")).label == "A HOSPITAL"
    registry = await make_registry(adapter)
    await seed(registry, "hospital")
    absent = await registry.get_instance_checked("hospital", "015009")
    assert isinstance(absent, InstanceLookup) and absent.record is None, absent

@NEEDS_ATTRIBUTES
async def test_c20_18_r1_every_tied_candidate_however_many(adapter, make_registry):
    """Rule 3-4 (door lens C): the suite's widest tie was three, so a set capped at five
    survived. MILLER'S MERRY MANOR is twelve CCNs; here are eight."""
    rows = [{"host_id": f"01{n:04d}", "label": "MILLER'S MERRY MANOR", "state": "AL"}
            for n in range(8)]
    registry = await _world(adapter, make_registry, rows)
    answer = await _resolve(registry, "MILLER'S MERRY MANOR")
    assert answer.outcome == "ambiguous" and answer.ref is None
    assert answer.known == 8 and len(answer.candidates) == 8

@NEEDS_ATTRIBUTES
async def test_c20_17_r1_the_margin_is_inclusive_at_its_edge(adapter, make_registry):
    """Rules 3-3 and 5-8 (build lens 5): 0.98 and 0.96 are within a 0.02 margin, and
    `0.98 - 0.96` is 0.020000000000000018 in floating point. Two candidates, one set."""
    rows = [{"host_id": "000001", "label": "a" * 49 + "b", "state": "AL"},   # 0.98
            {"host_id": "000002", "label": "a" * 48 + "bb", "state": "AL"}]  # 0.96
    registry = await _world(adapter, make_registry, rows)
    answer = await _resolve(registry, "a" * 50)
    assert answer.outcome == "ambiguous", answer
    assert answer.known == 2

@NEEDS_ATTRIBUTES
async def test_c20_74_r1_the_threshold_is_tested_before_rounding(adapter, make_registry):
    """Rule 5-9 (build lens 7): 226/233 = 0.96996 is below `match_at` 0.97 and rounds
    to 0.97 at four places. The band decides on the score, not on its display."""
    rows = [{"host_id": "000001", "label": "a" * 113 + "bbbb", "state": "AL"}]
    registry = await _world(adapter, make_registry, rows)
    answer = await _resolve(registry, "a" * 116)
    assert answer.outcome == "ambiguous", answer

@NEEDS_ATTRIBUTES
async def test_c20_14_r1_a_repeating_cursor_ends_the_read_never_loops(adapter, make_registry):
    """Rule 2-11 (build lens 4): a backend handing back the same cursor forever."""

    class Stuck:
        """Forwards everything; hands back the same cursor on every page."""

        def __init__(self, inner):
            self.inner = inner
            self.calls = 0

        def __getattr__(self, name):
            return getattr(self.inner, name)

        async def find_instance_candidates(self, q):
            self.calls += 1
            if self.calls > 50:
                raise AssertionError("the registry kept paging a cursor it had seen")
            page = await self.inner.find_instance_candidates(dataclasses.replace(q, after=None))
            return dataclasses.replace(page, records=page.records[:1], known=1,
                                       complete=False, next_after="stuck")

    await host_instances(adapter, _rows(), type_name="facility")
    registry = await make_registry(Stuck(adapter))
    await seed(registry, "facility", attributes=_governed())
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer

@NEEDS_ATTRIBUTES
async def test_c20_08_r1_an_over_count_is_as_uncountable_as_an_under_count(adapter, make_registry):
    """Rule 2-5 (door lens D): `known` as the host's total on a page that holds fewer.
    Read as an extent it would be a decision over part of the rows (`I-1`)."""
    await host_instances(adapter, _rows(), type_name="facility")
    registry = await make_registry(AsyncDegradedAdapter(adapter, instance_known="over"))
    await seed(registry, "facility", attributes=_governed())
    answer = await _resolve(registry, "Mesa Vista Care")
    assert answer.outcome == "unknowable" and answer.complete is False, answer

@NEEDS_ATTRIBUTES
async def test_c20_08_r1_a_finished_read_that_cannot_count_is_counted_here(adapter, make_registry):
    """Rule 2-5 with 3.4's third absorber, which is `known=None` AND `complete=False`
    together (build lens 3). A backend that finished but cannot count hands over every
    record, and the registry counts them."""
    await host_instances(adapter, _rows(), type_name="facility")
    finished = await make_registry(AsyncDegradedAdapter(adapter, instance_known="none"))
    await seed(finished, "facility", attributes=_governed())
    answer = await _resolve(finished, EXACT)
    assert answer.outcome == "existing" and answer.known == 1, answer

@NEEDS_ATTRIBUTES
async def test_c20_08_r1_an_unfinished_read_that_cannot_count_is_unknowable(adapter, make_registry):
    """The absorber itself: `known=None` and `complete=False` together."""
    await host_instances(adapter, _rows(), type_name="facility", page_size=2)
    registry = await make_registry(AsyncDegradedAdapter(adapter, instance_known="none",
                                             instance_page_cap=2))
    await seed(registry, "facility", attributes=_governed())
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer

def test_c20_01_r1_the_snapshot_sees_every_registry_table(adapter, make_registry):
    """Rule 1-1 (door lens E): the seam check's snapshot read five tables and could not
    see an attribute observation, an edge or an invocation written on the side."""
    from ontoloche.contract import _support

    source = inspect.getsource(_support.snapshot)
    for read in ("find_edges", "find_invocations", "read_attr_observed"):
        assert read in source, f"snapshot does not read {read}"

def test_c20_04_r1_no_protocol_method_but_the_two_takes_or_returns_an_instance(adapter):
    """Rule 2-1 (door lens G): a write primitive need not have "instance" in its name."""
    for name in dir(AsyncStorageAdapter):
        if name.startswith("_") or name in ("get_instance", "find_instance_candidates"):
            continue
        member = getattr(AsyncStorageAdapter, name)
        if not callable(member):
            continue
        hints = str(inspect.signature(member))
        assert "InstanceRecord" not in hints and "CandidatePage" not in hints, name

def test_c20_58_r1_primitive_22_takes_exactly_its_four(adapter):
    """Rule 6-17 (door lens I): a tenancy parameter by another name is still one."""
    assert list(inspect.signature(AsyncStorageAdapter.get_instance).parameters) == [
        "self", "namespace", "kind", "type_name", "instance_id"]

@NEEDS_ATTRIBUTES
async def test_c20_25_r1_tier_none_is_refused(adapter, make_registry):
    """Rule 3-11 (door lens L)."""
    registry = await _world(adapter, make_registry)
    with pytest.raises(TypeError):
        await registry.resolve_instance(EXACT, CTX, type_name="facility", tier=None)

@NEEDS_ATTRIBUTES
async def test_c20_63_r1_a_class_word_does_not_skip_the_host_filter_check(adapter, make_registry):
    """Rule 2-12 (door lens J): the mapping check runs before `not_an_instance`."""
    registry = await _world(adapter, make_registry)
    with pytest.raises(TypeError):
        await _resolve(registry, "Provider Name", host_filter="state=AL")

@NEEDS_ATTRIBUTES
async def test_c20_62_r1_not_an_instance_carries_the_namespace_warnings(adapter, make_registry):
    """Rules 7-1 and 7-4 (build lens, read-only): every resolution carries them, the
    one that reads nothing included."""
    registry = await _world(adapter, make_registry)
    answer = await _resolve(registry, "Provider Name")
    assert answer.outcome == "not_an_instance"
    assert "no_tenancy_predicate" in answer.warnings
    assert "consumers_unregistered" in answer.warnings

@NEEDS_ATTRIBUTES
async def test_c20_05_r2_an_integer_host_id_reads_back_at_both_doors(adapter, make_registry):
    """Rule 2-2 with standing rule (e) (round 2, build lens M1): the host's id column
    holds integers. Primitive 23 mints ref `#42`; primitive 22 asked for "42" must find
    that row, never call it absent."""
    rows = [{"host_id": 42, "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    await host_instances(adapter, rows, type_name="facility", id_type="INTEGER")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "existing" and answer.ref.id == "42", answer
    assert await adapter.get_instance("default", "entity", "facility", "42") is not None
    lookup = await registry.get_instance_checked("facility", "42")
    assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup
    assert lookup.ref == answer.ref

async def _chain_world(adapter, make_registry, rows):
    """a -> b -> c on one host table typed by a column, every entry governed alike."""
    for name in ("a", "b", "c"):
        await host_instances(adapter, rows, type_name=name, type_column="kind_name")
    registry = await make_registry(adapter)
    for name in ("a", "b", "c"):
        await seed(registry, name, attributes=_governed())
    for old, new in (("a", "b"), ("b", "c")):
        retired = await registry.retire(old, "renamed", retired_by="user:sd", successor=new)
        assert isinstance(retired, TypeEntry), retired
    return registry

@NEEDS_RETIRE
async def test_c20_89_r2_the_ref_never_depends_on_the_declared_name(adapter, make_registry):
    """Rule 2-17, "resolved under the name the closure resolves to" (round 2, build
    lens M2). 015009 is held under `a` and `b`, identically, and not under `c`. Round 2
    found `a#015009` from one caller and `b#015009` from another."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    rows = [dict(burns, kind_name="a"), dict(burns, kind_name="b"),
            {"host_id": "015010", "label": "COOSA VALLEY HEALTHCARE CENTER", "state": "AL",
             "kind_name": "c"}]
    registry = await _chain_world(adapter, make_registry, rows)
    refs = set()
    for name in ("a", "b", "c"):
        answer = await _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "existing", (name, answer)
        refs.add(answer.ref)
        lookup = await registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup
        refs.add(lookup.ref)
    assert {r.type.name for r in refs} == {"c"}, refs

@NEEDS_RETIRE
async def test_c20_89_r2_disagreeing_copies_none_current_decide_nothing(adapter, make_registry):
    """Rule 2-17's build-side branch (round 2, door lens): two copies that differ, none
    under the effective name. No copy is current, so neither door chooses one."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    rows = [dict(burns, kind_name="a"), dict(burns, kind_name="b", state="CA")]
    registry = await _chain_world(adapter, make_registry, rows)
    answer = await _resolve(registry, EXACT, type_name="c")
    assert answer.outcome == "unknowable" and "2-17" in answer.why_incomplete, answer
    door = await registry.get_instance_checked("c", "015009")
    assert isinstance(door, Refusal) and door.detail["problem"] == "lookup_incomplete", door

@NEEDS_RETIRE
async def test_c20_79_r2_a_margin_only_change_is_a_change(adapter, make_registry):
    """Rules 3-18 and 5-10 (round 2, door lens 1): the THREE thresholds, the margin one."""
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                new_governed=_governed({**POLICY, "ambiguity_margin": 0.5}))
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "MatchPolicy" in answer.why_incomplete

@NEEDS_RETIRE
async def test_c20_79_r2_one_value_by_equality_is_not_a_change(adapter, make_registry):
    """E10 under the equality `evaluate` uses (round 2, build lens 2): `not_in [1]` and
    `not_in [1.0]` exclude the same rows, so they are one predicate."""
    old = {"op": "not_in", "attribute": "state", "value": [1], "why": "w"}
    new = {"op": "not_in", "attribute": "state", "value": [1.0], "why": "w"}
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                old_governed=_governed(condition=old),
                                new_governed=_governed(condition=new))
    assert (await _resolve(registry, EXACT)).outcome == "existing"

@NEEDS_ATTRIBUTES
async def test_c20_73_r2_exactly_at_match_at_is_existing(adapter, make_registry):
    """Rule 5-8, "at or above" (round 2, door lens 2)."""
    s = similar(norm(BAND), norm("BURNS NURSING HOME, INC."))
    registry = await _world(adapter, make_registry, policy={**POLICY, "match_at": s})
    answer = await _resolve(registry, BAND)
    assert answer.outcome == "existing", (s, answer)

@NEEDS_ATTRIBUTES
async def test_c20_73_r2_a_hair_below_match_at_is_not_existing(adapter, make_registry):
    """The other side of the same edge (round 2, build lens 1): no tolerance on a
    threshold. Round 1's epsilon made 0.9 count as at 0.9 + 5e-10."""
    s = similar(norm(BAND), norm("BURNS NURSING HOME, INC."))
    registry = await _world(adapter, make_registry, policy={**POLICY, "match_at": s + 5e-10})
    assert (await _resolve(registry, BAND)).outcome == "ambiguous"

@NEEDS_ATTRIBUTES
async def test_c20_17_r2_a_second_candidate_exactly_at_match_at_ties(adapter, make_registry):
    """Rule 3-3 (round 2, door lens 3): at `match_at` and outside the margin, still tied."""
    rows = _rows() + [{"host_id": "999", "label": "Burns Nursing Home", "state": "AL"}]
    s2 = similar(norm(EXACT), norm("Burns Nursing Home"))
    registry = await _world(adapter, make_registry, rows, policy={**POLICY, "match_at": s2})
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "ambiguous", (s2, answer)

@NEEDS_ATTRIBUTES
async def test_c20_74_r2_a_top_exactly_at_propose_below_is_ambiguous(adapter, make_registry):
    """Rule 5-9 (round 2, door lens 4)."""
    s = similar(norm(BAND), norm("BURNS NURSING HOME, INC."))
    registry = await _world(adapter, make_registry, policy={**POLICY, "propose_below": s})
    answer = await _resolve(registry, BAND)
    assert answer.outcome == "ambiguous", (s, answer)

@NEEDS_ATTRIBUTES
async def test_c20_90_r2_the_floor_is_inclusive(adapter, make_registry):
    """Rule 5-12 (round 2, door lens 5): a second candidate exactly at `propose_below`,
    inside the margin, is in the tied set."""
    rows = _rows() + [{"host_id": "999", "label": "Burns Nursing Home Incs", "state": "AL"}]
    s2 = similar(norm(EXACT), norm("Burns Nursing Home Incs"))
    pol = {**POLICY, "match_at": 1.0, "propose_below": s2, "ambiguity_margin": 0.05}
    registry = await _world(adapter, make_registry, rows, policy=pol)
    answer = await _resolve(registry, EXACT)
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
async def test_c20_66_r2_primitive_22_refuses_a_dangling_closure(adapter, make_registry):
    """Rules 2-15 and 3-15 at primitive 22's door (round 2, door lens 8)."""
    registry = await _world(adapter, make_registry)
    await _rewrite(adapter, "facility", status="retired", successor="ghost")
    answer = await registry.get_instance_checked("facility", "015009")
    assert isinstance(answer, Refusal), answer
    assert answer.detail["problem"] == "closure_incomplete"

@NEEDS_RETIRE
async def test_c20_66_r2_primitive_22_refuses_changed_governed_facts(adapter, make_registry):
    """Rule 3-18 at primitive 22's door (round 2, door lens 9)."""
    registry = await _successor_world(adapter, make_registry, old_rows=[], new_rows=_rows(),
                                new_governed=_governed(condition=AL_ONLY))
    answer = await registry.get_instance_checked("facility", "015009")
    assert isinstance(answer, Refusal), answer
    assert answer.detail["problem"] == "governed_facts_changed"

@NEEDS_ATTRIBUTES
async def test_c20_64_r2_the_host_filter_reaches_primitive_23(adapter, make_registry):
    """Rule 2-13 (round 2, door lens): the narrowing happens, not only its warning."""
    rows = _rows() + [{"host_id": "999", "label": "BURNS NURSING HOME, INC", "state": "CA"}]
    registry = await _world(adapter, make_registry, rows, filter_columns=("state",))
    assert (await _resolve(registry, EXACT)).outcome == "ambiguous"
    narrowed = await _resolve(registry, EXACT, host_filter={"state": "AL"})
    assert narrowed.outcome == "existing", narrowed
    assert narrowed.scanned == len([r for r in rows if r["state"] == "AL"])

@NEEDS_ATTRIBUTES
async def test_c20_23_r2_a_scored_answer_carries_its_score(adapter, make_registry):
    """Rule 3-9 (round 2, door lens): `None` means did not score, so an answer that
    scored carries the top score."""
    registry = await _world(adapter, make_registry)
    for label, outcome in ((BAND, "ambiguous"), (NOTHING, "proposal")):
        answer = await _resolve(registry, label)
        assert answer.outcome == outcome, (label, answer)
        assert answer.confidence is not None, answer
        if answer.candidates:
            assert answer.confidence == answer.candidates[0].score

async def test_c20_11_r2_the_hosts_page_size_caps_a_larger_limit(adapter):
    """Rule 2-11 with the binding's ceiling (round 2, door lens): a page never holds
    more than the host serves, whatever `limit` asks for."""
    await host_instances(adapter, _rows(), type_name="facility", page_size=2)
    page = await adapter.find_instance_candidates(CandidateQuery(
        namespace="default", kind="entity", type_name="facility", label=EXACT, limit=10))
    assert len(page.records) == 2 and page.next_after is not None, page

@NEEDS_ATTRIBUTES
async def test_c20_14_r2_a_cursor_that_never_repeats_still_ends(adapter, make_registry):
    """Rule 2-11 (round 2, build lens 3): empty pages, a fresh cursor every time."""

    class Endless:
        def __init__(self, inner):
            self.inner = inner
            self.calls = 0

        def __getattr__(self, name):
            return getattr(self.inner, name)

        async def find_instance_candidates(self, q):
            self.calls += 1
            if self.calls > 200:
                raise AssertionError("the registry kept paging past its page cap")
            return CandidatePage(records=(), known=0, complete=False,
                                 next_after=f"c{self.calls}", why_incomplete="")

    await host_instances(adapter, _rows(), type_name="facility")
    registry = await make_registry(Endless(adapter))
    registry.INSTANCE_READ_PAGES_MAX = 50
    await seed(registry, "facility", attributes=_governed())
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer

async def _round_trips(registry, label):
    """The ref one door mints reads back at the other (standing rule (e))."""
    answer = await _resolve(registry, label)
    assert answer.outcome == "existing", (label, answer)
    lookup = await registry.get_instance_checked("facility", answer.ref.id)
    assert isinstance(lookup, InstanceLookup) and lookup.record is not None, (answer, lookup)
    assert lookup.ref == answer.ref, (answer.ref, lookup.ref)
    return answer

@NEEDS_ATTRIBUTES
async def test_c20_05_r3_a_real_or_bytes_host_id_reads_back_at_both_doors(adapter, make_registry):
    """Rule 2-2 with standing rule (e) (round 3, build lens M1): round 2 fixed the
    integer and left the id minted by Python's `str()` while primitive 22 compared the
    database's text. A REAL `1e20` was `#1e+20` at one door and absent at the other; a
    bytes id was `#b'015009'`. The id is now minted by the database, once."""
    rows = [{"host_id": 1e20, "label": "BURNS NURSING HOME, INC.", "state": "AL"},
            {"host_id": 1e-7, "label": "COOSA VALLEY HEALTHCARE CENTER", "state": "AL"},
            {"host_id": b"015012", "label": "MESA VISTA CARE", "state": "AL"}]
    target = getattr(adapter, "inner", adapter)
    if getattr(getattr(target, "d", None), "name", "") != "sqlite":
        rows = rows[:2]          # bytes have no column here that also holds numbers
    await host_instances(adapter, rows, type_name="facility", id_type="NUMBER")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    for row in rows:
        answer = await _round_trips(registry, row["label"])
        assert not answer.ref.id.startswith("b'"), answer.ref

@NEEDS_ATTRIBUTES
async def test_c20_16_r3_two_ids_one_text_are_one_id_at_both_doors(adapter, make_registry):
    """Rule 2-16 with standing rule (e): two stored ids the database renders as one text
    are, to both doors, one id on two rows. Neither door hands out either of them."""
    rows = [{"host_id": 0.1 + 0.2, "label": "BURNS NURSING HOME, INC.", "state": "AL"},
            {"host_id": 0.3, "label": "BURNS NURSING HOME INC", "state": "AL"}]
    await host_instances(adapter, rows, type_name="facility", id_type="NUMBER")
    probe = await adapter.find_instance_candidates(CandidateQuery(
        namespace="default", kind="entity", type_name="facility", label=EXACT))
    ids = [r.instance_id for r in probe.records]
    if len(set(ids)) == 2:
        pytest.skip(f"this database renders the two ids apart ({ids}): no collision")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    assert (await _resolve(registry, EXACT)).outcome == "unknowable"
    lookup = await registry.get_instance_checked("facility", ids[0])
    assert isinstance(lookup, Refusal) and lookup.detail["problem"] == "lookup_incomplete"

async def _alias_world(adapter, make_registry):
    """`legacy_home` retired with no successor, then claimed as an alias by `facility`
    through `import_types`, with public calls only (round 3, door lens 1)."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    await host_instances(adapter, [burns], type_name="legacy_home")
    await host_instances(adapter, [burns, {"host_id": "015010", "label": "COOSA VALLEY",
                                     "state": "AL"}], type_name="facility")
    registry = await make_registry(adapter)
    await seed(registry, "legacy_home", attributes=_governed())
    await seed(registry, "facility", attributes=_governed())
    retired = await registry.retire("legacy_home", "dropped", retired_by="user:sd")
    assert isinstance(retired, TypeEntry), retired
    await registry.import_types([{"name": "facility", "kind": "entity", "definition": "a facility",
                            "aliases": ["legacy_home"], "status": "active",
                            "attributes": _governed()}], kind="entity")
    return registry

@NEEDS_ALIASES
async def test_c20_89_r3_an_alias_moves_the_effective_name(adapter, make_registry):
    """Rules 2-17, 3-21 and 5-11 (round 3, door lens 1): `resolve_type` answers
    `facility` for `legacy_home`; the instance doors answered `legacy_home#015009`,
    `governed_by default:legacy_home`, and proposed under the tombstone."""
    registry = await _alias_world(adapter, make_registry)
    seen = set()
    for name in ("facility", "legacy_home"):
        answer = await _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "existing", (name, answer)
        seen.add((answer.ref, answer.governed_by))
        proposal = await _resolve(registry, NOTHING, type_name=name)
        assert proposal.outcome == "proposal" and proposal.candidate.type.name == "facility"
        lookup = await registry.get_instance_checked(name, "015009")
        assert isinstance(lookup, InstanceLookup) and lookup.ref.type.name == "facility"
    assert seen == {(answer.ref, "default:facility")}, seen
    assert answer.ref.type.name == "facility"

@NEEDS_ALIASES
async def test_c20_87_r3_a_hand_written_alias_is_read(adapter, make_registry):
    """Rule 3-21's own reason (round 3, door lens 6): "a hand-written alias is one the
    successor scan would miss". `merge_types` writes both; `import_types` writes only
    the alias, so the closure must read the alias holder's table AND the alias's."""
    registry = await _alias_world(adapter, make_registry)
    answer = await _resolve(registry, EXACT, type_name="facility")
    assert answer.scanned == 3, answer

@NEEDS_RETIRE
async def test_c20_84_r3_primitive_22_refuses_a_bare_successor(adapter, make_registry):
    """Rules 7-5 and 6-18 at primitive 22's door (round 3, door lens 2): a successor
    declaring NO governed facts is a change from a predecessor that declared them."""
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                old_governed=_governed(condition=AL_ONLY), new_governed={})
    lookup = await registry.get_instance_checked("facility", "055001")
    assert isinstance(lookup, Refusal), lookup
    assert lookup.detail["problem"] == "governed_facts_changed"

def test_c20_46_r3_not_in_over_null_is_unknowable(adapter):
    """Rule 6-5 (round 3, door lens 3): `not_in` too."""
    c = condition_from_mapping({"op": "not_in", "attribute": "state", "value": ["CA"],
                                "why": "w"})
    assert evaluate(c, {"state": None}).holds is None

@NEEDS_ATTRIBUTES
async def test_c20_56_r3_a_host_filter_never_replaces_the_predicate(adapter, make_registry):
    """Rule 6-15 (round 3, door lens 4): narrowing the host's read is an optimisation;
    the entry's predicate is still evaluated over what came back."""
    registry = await _world(adapter, make_registry, condition=AL_ONLY, filter_columns=("state",))
    answer = await _resolve(registry, "Willowbrooke Ct Skilled Care Center",
                      host_filter={"state": "CA"})
    assert answer.outcome != "existing", answer

def test_c20_44_r3_an_undecidable_combinator_says_why(adapter):
    """Rule 6-3 (round 3, door lens 5): `unknowable` carries its sentence."""
    t = {"op": "eq", "attribute": "state", "value": "AL", "why": "w"}
    u = {"op": "eq", "attribute": "zip", "value": "35004", "why": "w"}
    f = {"op": "eq", "attribute": "state", "value": "CA", "why": "w"}
    for op, terms in (("all_of", [t, u]), ("any_of", [f, u])):
        c = condition_from_mapping({"op": op, "terms": terms, "why": "w"})
        result = evaluate(c, {"state": "AL"})
        assert result.holds is None and result.why.strip(), (op, result)

@NEEDS_ATTRIBUTES
async def test_c20_23_r3_a_proposal_that_scored_nothing_carries_none(adapter, make_registry):
    """Rule 3-9 (round 3, door lens minor): the predicate excludes every row, nothing
    is scored, and `None` is the only honest confidence."""
    nowhere = {"op": "eq", "attribute": "state", "value": "ZZ", "why": "no such state"}
    registry = await _world(adapter, make_registry, condition=nowhere)
    answer = await _resolve(registry, EXACT)
    assert answer.confidence is None, answer

def test_c20_51_r3_is_null_takes_no_terms(adapter):
    """Rule 6-10 (round 3, door lens minor)."""
    assert condition_problem({"op": "is_null", "attribute": "state", "why": "w",
                              "terms": [{"op": "eq", "attribute": "state", "value": "AL",
                                         "why": "w"}]})

def test_c20_47_r3_a_non_finite_operand_is_refused(adapter):
    """Round 3, build lens minor 2: NaN equals nothing, itself included, so rule 3-18
    could never find a predicate equal to its own copy."""
    for value in (float("nan"), float("inf"), [float("nan")]):
        op = "in" if isinstance(value, list) else "eq"
        assert condition_problem({"op": op, "attribute": "x", "value": value, "why": "w"})

@NEEDS_RETIRE
async def test_c20_79_r3_a_why_inside_an_operand_is_an_operand(adapter, make_registry):
    """E10 (round 2's minor, round 3's fidelity lens): `why` is a Condition's prose, and a
    key named "why" inside a mapping operand is part of the value."""
    old = {"op": "ne", "attribute": "state", "value": {"why": "x", "k": 1}, "why": "w"}
    new = {"op": "ne", "attribute": "state", "value": {"why": "y", "k": 1}, "why": "w"}
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                old_governed=_governed(condition=old),
                                new_governed=_governed(condition=new))
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and "predicate" in answer.why_incomplete, answer

@NEEDS_ATTRIBUTES
async def test_c20_05_r4_a_row_with_no_id_is_never_a_ref(adapter, make_registry):
    """Rule 2-2 with standing rule (e) (round 4, build lens M1): a NULL id was minted as
    `#None`, which primitive 22 read back as absent. The read is incomplete instead:
    the row cannot be referenced and cannot be left out."""
    rows = [{"host_id": None, "label": "BURNS NURSING HOME, INC.", "state": "AL"},
            *_rows()[1:]]
    await host_instances(adapter, rows, type_name="facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    for label in (EXACT, NOTHING):
        answer = await _resolve(registry, label)
        assert answer.outcome == "unknowable" and answer.complete is False, answer
        assert "no id" in answer.why_incomplete, answer
        assert all(c.ref.id != "None" for c in answer.candidates), answer

async def _retired_word_world(adapter, make_registry, holders):
    """`legacy_home` retired with no successor; each of `holders` a live entity with
    its own host table. The aliases are written by the tests that need them."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    for name in ("legacy_home", *holders):
        await host_instances(adapter, [burns], type_name=name)
    registry = await make_registry(adapter)
    for name in ("legacy_home", *holders):
        await seed(registry, name, attributes=_governed())
    retired = await registry.retire("legacy_home", "dropped", retired_by="user:sd")
    assert isinstance(retired, TypeEntry), retired
    return registry

@NEEDS_ALIASES
async def test_c20_89_r4_only_an_entity_alias_moves_the_name(adapter, make_registry):
    """Rule 3-21 (round 4, build lens 2): a PREDICATE holding the word as an alias does
    not move an entity identity to the entity that shares the predicate's name. The
    store is written directly; no public call was found to build it."""
    registry = await _retired_word_world(adapter, make_registry, ["facility"])
    rec = await adapter.get_type("default", "facility", kind="entity")
    await adapter.put_type(dataclasses.replace(rec, kind="predicate", aliases=("legacy_home",)))
    answer = await _resolve(registry, EXACT, type_name="legacy_home")
    assert answer.governed_by == "default:legacy_home", answer

@NEEDS_ALIASES
async def test_c20_89_r4_two_holders_decide_nothing(adapter, make_registry):
    """Rule 3-21 under Rule U (round 4, build lens 3): two live entries hold the retired
    word as an alias. The first by sort order won, and the second's table and governed
    facts were never read."""
    registry = await _retired_word_world(adapter, make_registry, ["facility", "ltc_facility"])
    for name in ("facility", "ltc_facility"):
        await _rewrite(adapter, name, aliases=("legacy_home",))
    answer = await _resolve(registry, EXACT, type_name="legacy_home")
    assert answer.outcome == "unknowable" and "alias" in answer.why_incomplete, answer

@NEEDS_RETIRE
async def test_c20_89_r4_a_same_word_name_is_not_an_alias(adapter, make_registry):
    """Rules 3-20 and 3-21 (round 4, build lens 4): a live `legacy_home_` answers to the
    word by `same_word`, claims no alias, and its own closure never walks back to the
    tombstone. Hopping to it gave one effective entry two extents."""
    registry = await _retired_word_world(adapter, make_registry, [])
    rec = await adapter.get_type("default", "legacy_home", kind="entity")
    await host_instances(adapter, [{"host_id": "015010", "label": "COOSA VALLEY", "state": "AL"}],
                   type_name="legacy_home_")
    await adapter.put_type(dataclasses.replace(rec, name="legacy_home_", status="active",
                                         successor=None, aliases=()))
    old = await _resolve(registry, EXACT, type_name="legacy_home")
    new = await _resolve(registry, EXACT, type_name="legacy_home_")
    assert old.governed_by == "default:legacy_home" and old.scanned == 1, old
    assert new.scanned == 1, new

def test_c20_47_r4_a_non_finite_number_anywhere_is_refused(adapter):
    """Round 4, build lens (clean-attack note): NaN inside a mapping operand, inside a
    nested sequence, and as a `Decimal` was let through. A finite `Decimal` is not."""
    for op, value in (("eq", {"k": float("nan")}), ("in", [[float("nan")]]),
                      ("eq", decimal.Decimal("NaN"))):
        assert condition_problem({"op": op, "attribute": "x", "value": value, "why": "w"})
    assert condition_problem({"op": "eq", "attribute": "x", "value": decimal.Decimal("1.5"),
                              "why": "w"}) is None

@NEEDS_RETIRE
async def test_c20_86_r4_an_unfinished_backward_walk_is_unknowable(adapter, make_registry):
    """Rule 3-20 under Rule U (round 4, door lens 2): the survivor's backward scan
    cannot finish, and the survivor must not decide over the part it saw."""
    old = [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    registry = await _successor_world(adapter, make_registry, old_rows=old, new_rows=_rows()[1:])
    for n in range(4):
        await seed(registry, f"pad{n}", attributes=_governed())
        await seed(registry, f"padnew{n}", attributes=_governed())
        await registry.retire(f"pad{n}", "pad", retired_by="user:sd", successor=f"padnew{n}")
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=1))
    answer = await _resolve(capped, EXACT, type_name="ltc_facility")
    assert answer.outcome == "unknowable", answer

@NEEDS_RETIRE
async def test_c20_89_r4_copies_differing_only_in_label_decide_nothing(adapter, make_registry):
    """Rule 2-17 (round 4, door lens 3): the label is content. With it ignored, the
    copy scored depended on which name the caller declared."""
    burns = {"host_id": "015009", "label": "BURNS NURSING HOME, INC.", "state": "AL"}
    rows = [dict(burns, kind_name="a"), dict(burns, kind_name="b", label="ZZZ OTHER")]
    registry = await _chain_world(adapter, make_registry, rows)
    for name in ("a", "b", "c"):
        answer = await _resolve(registry, EXACT, type_name=name)
        assert answer.outcome == "unknowable" and "2-17" in answer.why_incomplete, answer

@NEEDS_RETIRE
async def test_c20_19_r4_a_member_primitive_23_cannot_read_is_unknowable(adapter, make_registry):
    """Rules 3-5 and 3-19, I-1 (round 4, door lens 5): one member's candidate read
    raises. The double stops after 200 calls so a loop that retries is red, not hung."""
    from ontoloche.errors import NotSupported

    class Raises:
        def __init__(self, inner):
            self.inner, self.calls = inner, 0

        def __getattr__(self, name):
            return getattr(self.inner, name)

        async def find_instance_candidates(self, q):
            if q.type_name == "facility":
                self.calls += 1
                if self.calls > 200:
                    raise AssertionError("the registry kept asking a member it cannot read")
                raise NotSupported("cannot read facility")
            return await self.inner.find_instance_candidates(q)

    registry = await _successor_world(adapter, make_registry, old_rows=_rows()[:1],
                                new_rows=_rows()[1:])
    wrapped = await make_registry(Raises(adapter))
    answer = await _resolve(wrapped, NOTHING, type_name="ltc_facility")
    assert answer.outcome == "unknowable" and answer.complete is False, answer

@NEEDS_RETIRE
@pytest.mark.parametrize("pair", [
    ({"op": "not_in", "attribute": "state", "value": ["CA", "CO"], "why": "w"},
     {"op": "not_in", "attribute": "state", "value": ["CO", "CA"], "why": "w"}),
    ({"op": "any_of", "why": "w", "terms": [
        {"op": "eq", "attribute": "state", "value": "AL", "why": "w"},
        {"op": "eq", "attribute": "state", "value": "GA", "why": "w"}]},
     {"op": "any_of", "why": "w", "terms": [
        {"op": "eq", "attribute": "state", "value": "GA", "why": "w"},
        {"op": "eq", "attribute": "state", "value": "AL", "why": "w"}]}),
])
async def test_c20_79_r4_reordered_terms_are_not_a_change(adapter, make_registry, pair):
    """E10 (round 4, door lens 4): only an `in` list had been reordered. The build reads
    "the terms" as a set for `in`, `not_in` and a combinator's terms."""
    old, new = pair
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=[],
                                old_governed=_governed(condition=old),
                                new_governed=_governed(condition=new))
    assert (await _resolve(registry, EXACT)).outcome == "existing"

@NEEDS_ATTRIBUTES
async def test_c20_36_r4_a_stored_malformed_policy_is_unknowable(adapter, make_registry):
    """Rule 5-2, fail closed (round 4, door lens minor): a policy written past the
    declaration check is not scored against."""
    registry = await _world(adapter, make_registry)
    rec = await adapter.get_type("default", "facility", kind="entity")
    await adapter.put_type(dataclasses.replace(rec, attributes={
        **rec.attributes, MATCH_POLICY_KEY: {**POLICY, "match_at": 7.0}}))
    assert (await _resolve(registry, EXACT)).outcome == "unknowable"

@NEEDS_ATTRIBUTES
@pytest.mark.parametrize("cond,cand,want", [
    ({"op": "not_in", "attribute": "state", "value": ["CA", "CO"], "why": "w"},
     "Willowbrooke Ct Skilled Care Center", "proposal"),
    ({"op": "ne", "attribute": "state", "value": "CA", "why": "w"},
     "Willowbrooke Ct Skilled Care Center", "proposal"),
    ({"op": "lt", "attribute": "state", "value": "CA", "why": "w"},
     "Willowbrooke Ct Skilled Care Center", "proposal"),
    ({"op": "gt", "attribute": "state", "value": "CO", "why": "w"},
     "Mesa Vista Care", "proposal"),
    ({"op": "lte", "attribute": "state", "value": "AL", "why": "w"},
     "Willowbrooke Ct Skilled Care Center", "proposal"),
    ({"op": "lte", "attribute": "state", "value": "AL", "why": "w"}, EXACT, "existing"),
    ({"op": "gte", "attribute": "state", "value": "CA", "why": "w"},
     "Willowbrooke Ct Skilled Care Center", "existing"),
])
async def test_c20_43_r4_each_operator_holds_and_fails_where_it_should(adapter, make_registry,
                                                                  cond, cand, want):
    """Rule 6-3 and §6's operator meanings (round 4, door lens 1): six of the twelve
    operators had never been shown to exclude the row they exclude."""
    registry = await _world(adapter, make_registry, condition=cond)
    answer = await _resolve(registry, cand)
    assert answer.outcome == want, (cond, answer)

@NEEDS_RETIRE
async def test_c20_80_r4_a_tombstone_with_no_successor_is_served_q108(adapter, make_registry):
    """DECISIONS-OPEN item 31, Q108's default in force (the supervisor's ruling on round
    3's departure): a retired entity with no successor and no alias holder is still
    served from its own rows. `existing` under the retired name, a proposal under it,
    and primitive 22 returning the row. If the founder rules `unknowable` or `refuse`,
    this test is the one that changes."""
    registry = await _retired_word_world(adapter, make_registry, [])
    found = await _resolve(registry, EXACT, type_name="legacy_home")
    assert found.outcome == "existing" and found.ref.type.name == "legacy_home", found
    assert found.governed_by == "default:legacy_home", found
    novel = await _resolve(registry, NOTHING, type_name="legacy_home")
    assert novel.outcome == "proposal" and novel.candidate.type.name == "legacy_home"
    lookup = await registry.get_instance_checked("legacy_home", "015009")
    assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup

async def _spelled_alias_world(adapter, make_registry, spelling):
    """`legacy_home` retired with no successor and holding BURNS; `facility` live with
    COOSA, claiming the word as an alias written `spelling`. Public calls only."""
    await host_instances(adapter, [{"host_id": "015009", "label": "BURNS NURSING HOME, INC.",
                              "state": "AL"}], type_name="legacy_home")
    await host_instances(adapter, [{"host_id": "015010", "label": "COOSA VALLEY", "state": "AL"}],
                   type_name="facility")
    registry = await make_registry(adapter)
    await seed(registry, "legacy_home", attributes=_governed())
    await seed(registry, "facility", attributes=_governed())
    retired = await registry.retire("legacy_home", "dropped", retired_by="user:sd")
    assert isinstance(retired, TypeEntry), retired
    await registry.import_types([{"name": "facility", "kind": "entity", "definition": "a facility",
                            "aliases": [spelling], "status": "active",
                            "attributes": _governed()}], kind="entity")
    return registry

@NEEDS_ALIASES
@pytest.mark.parametrize("spelling", ["Legacy Home", "Legacy_Home", "legacy-home"])
async def test_c20_87_r5_an_alias_in_another_spelling_is_read_from_both_names(
        adapter, make_registry, spelling):
    """Rules 3-20 and 3-21, standing rule (e) (round 5, build and door lenses, MAJOR):
    the alias joined the closure from the retired name, matched by `identity_key`, and
    not from the holder, looked up as bytes. From `facility` the read was a strict
    subset, presented as complete, and proposed a duplicate of BURNS."""
    registry = await _spelled_alias_world(adapter, make_registry, spelling)
    old = await _resolve(registry, EXACT, type_name="legacy_home")
    new = await _resolve(registry, EXACT, type_name="facility")
    assert (old.outcome, old.ref, old.scanned) == (new.outcome, new.ref, new.scanned), (old, new)
    assert new.outcome == "existing" and new.scanned == 2, new
    lookup = await registry.get_instance_checked("facility", "015009")
    assert isinstance(lookup, InstanceLookup) and lookup.record is not None, lookup

@NEEDS_ALIASES
async def test_c20_87_r5_an_alias_naming_two_entries_decides_nothing(adapter, make_registry):
    """Rule 3-21 under Rule U (round 5): `Legacy Home` is `legacy_home` and also
    `legacy_home_` by `identity_key`, and choosing one would be deciding."""
    registry = await _spelled_alias_world(adapter, make_registry, "Legacy Home")
    rec = await adapter.get_type("default", "legacy_home", kind="entity")
    await adapter.put_type(dataclasses.replace(rec, name="legacy_home_", successor=None, aliases=()))
    answer = await _resolve(registry, EXACT, type_name="facility")
    assert answer.outcome == "unknowable" and "identity_key" in answer.why_incomplete, answer

@NEEDS_ALIASES
async def test_c20_89_r5_a_capped_alias_look_is_unknowable(adapter, make_registry):
    """Rule U through rule 3-21 (round 5, door lens minor 1): §2.4 called this branch
    near-equivalent to the closure-incomplete check. It is not: with it removed, a
    capped look answered `existing` under the tombstone."""
    registry = await _retired_word_world(adapter, make_registry, ["facility"])
    await _rewrite(adapter, "facility", aliases=("legacy_home",))
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=1))
    assert (await _resolve(capped, EXACT, type_name="legacy_home")).outcome == "unknowable"
    assert isinstance(await capped.get_instance_checked("legacy_home", "015009"), Refusal)

@NEEDS_ATTRIBUTES
async def test_c20_45_r5_an_incomparable_operand_is_unknowable_at_both_doors(adapter, make_registry):
    """Rule 6-4 (round 5, door lens minor 2): `lt 5` over string states raises, and the
    answer is `unknowable`, never `True`, which would hand the row out (R59)."""
    registry = await _world(adapter, make_registry,
                      condition={"op": "lt", "attribute": "state", "value": 5, "why": "w"})
    assert (await _resolve(registry, EXACT)).outcome == "unknowable"
    assert isinstance(await registry.get_instance_checked("facility", "015009"), Refusal)

@NEEDS_ATTRIBUTES
async def test_c20_05_r5_an_id_that_cannot_be_text_is_never_a_crash(adapter, make_registry):
    """Rule 2-2 (round 5, build lens minor 1): a SQLite BLOB id that is not UTF-8. Both
    primitives raised the driver's raw decode error."""
    target = getattr(adapter, "inner", adapter)
    if getattr(getattr(target, "d", None), "name", "") != "sqlite":
        pytest.skip("only SQLite casts a BLOB to TEXT by decoding it")
    rows = [{"host_id": b"\xff\xfe", "label": "BURNS NURSING HOME, INC.", "state": "AL"}]
    await host_instances(adapter, rows, type_name="facility", id_type="NUMBER")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    answer = await _resolve(registry, EXACT)
    assert answer.outcome == "unknowable" and answer.complete is False, answer
    # Primitive 22 filters by id, so the bad row is never rendered: an id no row
    # carries is honestly absent, and nothing crashes.
    lookup = await registry.get_instance_checked("facility", "anything")
    assert not isinstance(lookup, Refusal) and lookup.record is None, lookup

@NEEDS_ATTRIBUTES
async def test_c20_05_r6_a_present_row_that_cannot_be_rendered_is_refused(adapter, make_registry):
    """Rule 2-2 (round 6, door lens MAJOR, a test gap): primitive 22's guard was never
    reached by `C20-05` r5. A row whose id is fine but whose TEXT label holds bytes
    that are not UTF-8 (Latin-1 data in SQLite) must be refused at primitive 22, never
    read as absent (`None` means no such row) and never a raw driver crash."""
    target = getattr(adapter, "inner", adapter)
    if getattr(getattr(target, "d", None), "name", "") != "sqlite":
        pytest.skip("only SQLite stores TEXT that is not UTF-8")
    registry = await _world(adapter, make_registry)
    binding = list(target._instance_tables.values())[0]
    await target._execute(f"UPDATE \"{binding.table}\" SET label = CAST(x'fffe' AS TEXT) "
                    "WHERE host_id = '015009'")
    assert (await _resolve(registry, EXACT)).outcome == "unknowable"
    assert isinstance(await registry.get_instance_checked("facility", "015009"), Refusal)

def test_c20_47_r5_every_non_finite_shape_is_refused(adapter):
    """Round 5, build lens minor 2."""
    loop: list = []
    loop.append(loop)
    for op, value in (("eq", complex("nan")), ("eq", {float("nan"): 1}),
                      ("in", [frozenset({float("inf")})]), ("in", loop),
                      ("eq", {float("nan")})):
        assert condition_problem({"op": op, "attribute": "x", "value": value, "why": "w"})
    for value in (True, 3, 10 ** 400, 2.5, complex(1, 2)):
        assert condition_problem({"op": "eq", "attribute": "x", "value": value,
                                  "why": "w"}) is None

NEEDS_LEDGER = pytest.mark.requires_capability("stores_attributes", "stores_invocations")

_HOST_WRITE = Effect(op="host_state", why="the host writes the facility row (INGEST.md 4.2)")

async def _ingest_family(registry, name="propose_facility", *, mode="auto"):
    out = await action_family(registry, name, approval_mode=mode,
                        inputs=[InputSpec("instance", "candidate")], effects=[_HOST_WRITE])
    assert isinstance(out, TypeEntry), out
    return out

@NEEDS_LEDGER
async def test_c20_69_a_proposed_thing_is_named_by_a_candidate_ref_with_no_id(adapter, make_registry):
    """Rule **4-9**. A `CandidateRef` has no `id` and never acquires one: the host mints
    the identifier, and the moment it does the ledger's reference is an `InstanceRef`
    (amendment A2's `results`, `C20-29`). Through the ledger, the recorded input reads
    back as the candidate and never as an instance."""
    registry = await _world(adapter, make_registry)
    res = await _resolve(registry, NOTHING)
    assert res.outcome == "proposal", res
    cand = res.candidate
    assert isinstance(cand, CandidateRef)
    assert {f.name for f in dataclasses.fields(cand)} == {"type", "label", "resolution", "act_id"}
    assert not hasattr(cand, "id")
    await _ingest_family(registry)
    rec = await registry.record_invocation("propose_facility", {"instance": cand}, actor="ai:ingest",
                                     outcome="applied")
    assert not isinstance(rec, Refusal), rec
    back = parse_ref(rec.inputs["instance"])
    assert back == cand and isinstance(back, CandidateRef), back
    assert "#" not in rec.inputs["instance"].split('"label"')[0], rec.inputs

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_29_the_minted_ref_is_recorded_in_results_under_the_effective_type(
    adapter, make_registry
):
    """Rule **4-3**. The `InstanceRef` the host minted is recorded in `results`
    (amendment A2), never in an effect's `why` and never in `inputs`, and the type it
    is written under is the EFFECTIVE one the resolution reports (`I-3`)."""
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=_rows())
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("a result is an event, and this backend keeps none")
    res = await _resolve(registry, NOTHING, type_name="facility")
    assert res.outcome == "proposal", res
    assert res.candidate.type.name == "ltc_facility", "the EFFECTIVE type, not the declared"
    await _ingest_family(registry)
    rec = await registry.record_invocation("propose_facility", {"instance": res.candidate},
                                     actor="ai:ingest", outcome="applied",
                                     observed_effects=[_HOST_WRITE])
    minted = InstanceRef(res.candidate.type, "995001")
    out = await registry.record_result(rec.invocation_id, {"instance": minted}, actor="host:cms")
    assert not isinstance(out, Refusal), out
    assert out.results == {"instance": minted}
    assert out.results["instance"].type.name == "ltc_facility"
    assert all(ref_key(minted) not in e.why for e in out.observed_effects)
    assert parse_ref(out.inputs["instance"]) == res.candidate
    # Through the act: the candidate it records is under the EFFECTIVE type too.
    act_1 = await _act(registry, "act-29")
    landing = await act_1.land(NOTHING + " two", type_name="facility")
    assert landing.outcome == "proposed", landing
    assert landing.candidate.type.name == "ltc_facility"
    assert parse_ref(landing.invocation.inputs["instance"]).type.name == "ltc_facility"
    assert landing.invocation.results == {}

@NEEDS_LEDGER
async def test_c20_31_an_ambiguous_proposal_is_recorded_in_review_whatever_the_family_says(
    adapter, make_registry
):
    """Rule **4-5**, through the ledger (amendment A3). A proposal made over an
    `ambiguous` resolution carries `instance_ambiguous_at_proposal:<input_name>:<n>` and
    is recorded in `review` mode in an `auto` family, and the next proposal is not."""
    registry = await _world(adapter, make_registry)
    res = await _resolve(registry, BAND)
    assert res.outcome == "ambiguous" and res.complete, res
    await _ingest_family(registry, mode="auto")
    warning = f"instance_ambiguous_at_proposal:instance:{res.known}"
    rec = await registry.record_invocation("propose_facility", {"instance": res.candidate},
                                     actor="ai:ingest", outcome="applied",
                                     approval_mode="review", warnings=(warning,))
    assert not isinstance(rec, Refusal), rec
    assert rec.declared_policy["approval_mode"] == "review"
    assert warning in rec.warnings
    # Through the act, which computes the warning and the mode itself.
    act = await _act(registry, "act-31")
    landing = await act.land(BAND + " ", type_name="facility")
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        # The direct record above holds this identity, and a backend with no invocation
        # events cannot say whether its row was written: rule 4-11 lands that unknowable
        # and records nothing (amendment A4's complete=False).
        assert landing.outcome == "unknowable" and landing.invocation is None, landing
        return
    assert landing.outcome in ("proposed", "pending"), landing
    inv = landing.invocation
    assert inv.declared_policy["approval_mode"] == "review"
    assert inv.declared_policy["approval_mode_declared"] == "auto"
    assert f"instance_ambiguous_at_proposal:instance:{_tied_n(landing.resolution)}" in (
        inv.warnings)
    plain = await act.land(NOTHING, type_name="facility")
    assert plain.invocation.declared_policy["approval_mode"] == "auto"

@NEEDS_LEDGER
async def test_c20_71_the_guard_asks_who_holds_an_unwritten_proposal_not_an_unreviewed_one(
    adapter, make_registry
):
    """Rule **4-11**, through the ledger's A4 read. A proposal whose row has not been
    written holds the identity whether or not it has been reviewed, and once the host
    reports the row (`record_result`) it holds nothing."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    res = await _resolve(registry, NOTHING)
    assert res.outcome == "proposal", res
    await _ingest_family(registry, mode="review")
    first = await registry.record_invocation("propose_facility", {"instance": res.candidate},
                                       actor="ai:ingest", outcome="applied")
    again = await _resolve(registry, NOTHING.upper())
    held = await registry.invocations(unwritten_for=again.candidate)
    assert held.complete and [i.invocation_id for i in held.invocations] == [first.invocation_id]
    await registry.review_invocation(first.invocation_id, reviewed_by="user:sd")
    assert [i.invocation_id
            for i in (await registry.invocations(unwritten_for=again.candidate)).invocations] == [
        first.invocation_id], "draining the queue stood the guard down (I-5)"
    await registry.record_result(first.invocation_id,
                           {"instance": InstanceRef(res.candidate.type, "995001")},
                           actor="host:cms")
    assert (await registry.invocations(unwritten_for=again.candidate)).invocations == ()

    # Through the act: a second act's landing of a held identity is `pending`, carries
    # the holder, and mints no second identity.
    other = "yyyy wwww elsewhere"
    act_2 = await _act(registry, "act-71a")
    holder = await act_2.land(other, type_name="facility")
    assert holder.outcome == "proposed", holder
    act_3 = await _act(registry, "act-71b")
    second = await act_3.land(other.upper(), type_name="facility")
    assert second.outcome == "pending", second
    assert (f"instance_proposal_pending:{holder.invocation.invocation_id}"
            in second.invocation.warnings)
    held = await registry.invocations(unwritten_for=second.candidate)
    assert [i.invocation_id for i in held.invocations] == [holder.invocation.invocation_id], (
        "the pending row is itself a holder: two permissions for one identity")
    await registry.review_invocation(holder.invocation.invocation_id, reviewed_by="user:sd")
    act_4 = await _act(registry, "act-71c")
    third = await act_4.land(other, type_name="facility")
    assert third.outcome == "pending", "draining the queue stood the guard down (I-5)"

def _tied_n(res, policy=POLICY):
    """Rule 4-12's `<n>`: the rows a reviewer chooses among -- at or above `match_at`, or
    at or above `propose_below` within `ambiguity_margin` of the top (rules 3-3, 5-12)."""
    scores = [c.score for c in res.candidates if c.score is not None]
    top = max(scores)
    return sum(1 for s in scores if s >= policy["match_at"] or (
        top - s <= policy["ambiguity_margin"] + 1e-9 and s >= policy["propose_below"]))

async def _act(registry, act_id="act-1", *, family="propose_facility", tier="small", **kw):
    act = await registry.ingest_act(act_id, family=family, actor="ai:ingest", tier=tier, **kw)
    assert not isinstance(act, Refusal), act
    return act

async def _ledger(registry):
    return [i.invocation_id for i in (await registry.invocations(limit=10_000)).invocations]

@NEEDS_LEDGER
async def test_c20_27_a_propose_at_ingest_act_is_an_invocation_and_adds_no_store(
    adapter, make_registry
):
    """Rule **4-1**. The act's proposal is an ordinary invocation of a `kind="action"`
    family, and §4 adds no object with a store and no primitive: the act is memory."""
    from ontoloche.aio.adapter import AsyncStorageAdapter as Adapter
    from ontoloche.ingest import INGEST_LANDINGS, IngestLanding

    assert not [n for n in dir(Adapter) if "ingest" in n.lower() or n.startswith("act")]
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    act_5 = await _act(registry)
    landing = await act_5.land(NOTHING, type_name="facility")
    assert isinstance(landing, IngestLanding) and landing.outcome in INGEST_LANDINGS
    assert landing.outcome == "proposed", landing
    inv = landing.invocation
    assert inv.family == "propose_facility"
    assert await adapter.get_type("default", "propose_facility", kind="action") is not None
    assert parse_ref(inv.inputs["instance"]) == landing.candidate
    assert await _ledger(registry) == [inv.invocation_id]
    # A second act with the same id shares nothing: the memory is the act's, not a store.
    act_6 = await _act(registry)
    again = await act_6.land(NOTHING, type_name="facility")
    # The LEDGER answers across acts, not the memory: `pending` where it can read whether
    # the first row was written, `unknowable` (rule 4-11, A4) where it cannot. Never the
    # act's own `reused`, which would be a store shared across acts.
    events = registry.caps.stores_events and registry.caps.stores_invocation_events
    assert again.outcome == ("pending" if events else "unknowable"), again

@NEEDS_LEDGER
async def test_c20_28_the_host_writes_the_row_and_this_project_performs_no_write(
    adapter, make_registry
):
    """Rule **4-2**. The family must declare `host_state` (the act refuses one that does
    not), and landing a proposal writes no instance row."""
    registry = await _world(adapter, make_registry)
    out = await action_family(registry, "no_host_write", approval_mode="auto",
                        inputs=[InputSpec("instance", "candidate")], effects=[])
    assert isinstance(out, TypeEntry), out
    refused = await registry.ingest_act("a", family="no_host_write", actor="ai:ingest",
                                  tier="small")
    assert isinstance(refused, Refusal) and refused.reason == "attributes_schema_violation"
    out = await action_family(registry, "no_candidate", approval_mode="auto",
                        inputs=[InputSpec("instance", "instance")], effects=[_HOST_WRITE])
    refused = await registry.ingest_act("a", family="no_candidate", actor="ai:ingest", tier="small")
    assert isinstance(refused, Refusal) and refused.reason == "attributes_schema_violation"
    unknown = await registry.ingest_act("a", family="nope", actor="ai:ingest", tier="small")
    assert isinstance(unknown, Refusal) and unknown.reason == "action_family_unknown"

    await _ingest_family(registry)
    act_7 = await _act(registry)
    landing = await act_7.land(NOTHING, type_name="facility")
    assert landing.outcome == "proposed"
    assert landing.invocation.declared_effects == (_HOST_WRITE,)
    after = await _resolve(registry, NOTHING)
    assert after.outcome == "proposal" and after.scanned == len(FACILITIES), (
        "a proposal wrote a host row")

@NEEDS_LEDGER
async def test_c20_30_provenance_is_invocation_provenance_unchanged(adapter, make_registry):
    """Rule **4-4**. Actor, tier, confidence, approver and `source_version` ride the
    invocation's existing provenance, and §4 adds no field to it."""
    import dataclasses

    from ontoloche.actions import InvocationProvenance

    assert [f.name for f in dataclasses.fields(InvocationProvenance)] == [
        "created_at", "created_by_actor", "created_by", "model_tier", "confidence",
        "approved_by", "approved_at", "evidence", "source_version", "history",
        "history_why",
    ]
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    act_8 = await _act(registry, tier="large")
    landing = await act_8.land(
        NOTHING, type_name="facility", confidence=0.4, source_version="cms-2026-08")
    prov = landing.invocation.provenance
    assert prov.created_by_actor == "ai:ingest" and prov.created_by == "ai"
    assert prov.model_tier == "large" and prov.confidence == 0.4
    assert prov.source_version == "cms-2026-08"
    assert prov.approved_by and prov.approved_by.startswith("auto:")

@NEEDS_LEDGER
async def test_c20_33_unknowable_and_not_an_instance_yield_no_proposal(adapter, make_registry):
    """Rule **4-7**. Both outcomes mint nothing, and the second is the classifier
    SUCCEEDING: proposing over it is how a column header becomes a host row."""
    registry = await _world(adapter, make_registry)
    await seed(registry, "unscored")               # no MatchPolicy: nothing can be scored
    await host_instances(adapter, _rows(), type_name="unscored")
    await _ingest_family(registry)
    act = await _act(registry)
    header = await act.land("Provider Name", type_name="facility")
    assert header.outcome == "not_an_instance", header
    blind = await act.land(EXACT, type_name="unscored")
    assert blind.outcome == "unknowable", blind
    for landing in (header, blind):
        assert landing.invocation is None and landing.candidate is None
        assert landing.ref is None and landing.why
    assert await _ledger(registry) == []

@NEEDS_LEDGER
async def test_c20_34_an_ingest_family_may_not_propose_a_predicate(adapter, make_registry):
    """Rule **4-8**. Refused at declaration (`ACTIONS.md` 2.5's allowlist), and the act
    refuses a family carrying one that reached the store past validation."""
    import dataclasses

    registry = await _world(adapter, make_registry)
    from ontoloche.actions import action_attributes

    out = await registry.propose_type(
        "mint_predicate", "an ingest family that would mint predicates", [], "user:sd",
        kind="action",
        attributes=action_attributes(
            reversibility="reversible", approval_mode="auto",
            inputs=[InputSpec("instance", "candidate")],
            effects=[_HOST_WRITE,
                     Effect(op="propose_type", namespace="default", kind="predicate")],
        ),
    )
    assert isinstance(out, Refusal) and out.reason == "effect_not_permitted", out
    await _ingest_family(registry)
    rec = await adapter.get_type("default", "propose_facility", kind="action")
    effects = list(rec.attributes["effects"]) + [
        Effect(op="propose_type", namespace="default", kind="predicate").to_dict()]
    await adapter.put_type(dataclasses.replace(rec, attributes={**rec.attributes, "effects": effects}))
    refused = await registry.ingest_act("a", family="propose_facility", actor="ai:ingest",
                                  tier="small")
    assert isinstance(refused, Refusal) and refused.reason == "attributes_schema_violation"

@NEEDS_LEDGER
async def test_c20_32_ambiguous_proposals_are_enumerable_and_drained_only_by_review(
    adapter, make_registry
):
    """Rule **4-6**. The review-mode proposals rule 4-5 records are in
    `invocations(unreviewed=True)`, and only `review_invocation` takes them out."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("draining is an event, and this backend keeps none")
    await _ingest_family(registry)
    act = await _act(registry)
    ambiguous = (await act.land(BAND, type_name="facility")).invocation
    clean = (await act.land(NOTHING, type_name="facility")).invocation
    queue = {i.invocation_id for i in (await registry.invocations(unreviewed=True)).invocations}
    assert ambiguous.invocation_id in queue and clean.invocation_id not in queue
    await registry.record_result(ambiguous.invocation_id,
                           {"instance": InstanceRef(TypeRef("default", "entity", "facility"),
                                                    "995002")},
                           actor="host:cms")
    queue = {i.invocation_id for i in (await registry.invocations(unreviewed=True)).invocations}
    assert ambiguous.invocation_id in queue, "a RESULT is not a review"
    await registry.review_invocation(ambiguous.invocation_id, reviewed_by="user:sd")
    queue = {i.invocation_id for i in (await registry.invocations(unreviewed=True)).invocations}
    assert ambiguous.invocation_id not in queue

@NEEDS_LEDGER
async def test_c20_72_n_is_counted_over_a_finished_read(adapter, make_registry):
    """Rule **4-12**. `<n>` is the tied set's size over a COMPLETE read -- the rows a
    reviewer chooses among, not the resolution's display list (round 1) -- and an
    unfinished read never reaches the proposal door (rule 3-6): it lands `unknowable`
    and records nothing."""
    # Padding rows nothing like BAND, so the read SCANS more rows than it KNOWS: an `<n>`
    # taken from `scanned`, or from `known` (the five shown), is then a different number.
    padding = [{"host_id": f"pad{i}", "label": f"qqqq unrelated padding {i}", "state": "XX"}
               for i in range(7)]
    registry = await _world(adapter, make_registry, rows=_rows() + padding)
    await _ingest_family(registry)
    act_9 = await _act(registry)
    landing = await act_9.land(BAND, type_name="facility")
    res = landing.resolution
    assert res.outcome == "ambiguous" and res.complete
    assert res.scanned > res.known, (res.scanned, res.known)
    ambiguity = [w for w in landing.invocation.warnings
                 if w.startswith("instance_ambiguous_at_proposal:")]
    assert _tied_n(res) != res.known, "the fixture must separate the tied set from known"
    assert ambiguity == [f"instance_ambiguous_at_proposal:instance:{_tied_n(res)}"], ambiguity

    dup = await make_registry(adapter)
    await host_instances(adapter, _rows() + _rows()[:1], type_name="dupes")
    await seed(dup, "dupes", attributes=_governed())
    act_10 = await _act(dup, "act-dup")
    blind = await act_10.land(BAND, type_name="dupes")
    assert blind.outcome == "unknowable" and blind.invocation is None, blind
    assert not any(w.startswith("instance_ambiguous_at_proposal")
                   for w in (blind.resolution.warnings if blind.resolution else ()))

@NEEDS_LEDGER
async def test_c20_70_within_one_act_an_identity_is_resolved_once_under_the_gates_key(
    adapter, make_registry
):
    """Rule **4-10**. The key is the gate's: the closure of the type and the label under
    the gate's own RELATION (`similar(norm(a), norm(b)) >= match_at`), not the raw label
    (`I-4`) and not the label without its type (B1)."""
    registry = await _world(adapter, make_registry)
    await host_instances(adapter, _rows(), type_name="clinic")
    await seed(registry, "clinic", attributes=_governed())
    await _ingest_family(registry)
    act = await _act(registry)

    first = await act.land(EXACT, type_name="facility")
    assert first.outcome == "existing"
    again = await act.land(EXACT.upper(), type_name="facility")
    assert again.outcome == "reused" and again.ref == first.ref and again.resolution is None

    minted = await act.land(NOTHING, type_name="facility")
    assert minted.outcome == "proposed"
    for variant in (NOTHING.upper(), "  " + NOTHING + "!", "zzzz qqqq unrelatd"):
        reused = await act.land(variant, type_name="facility")
        assert reused.outcome == "reused", (variant, reused)
        assert reused.candidate == minted.candidate and reused.invocation is None

    other_type = await act.land(NOTHING, type_name="clinic")
    assert other_type.outcome == "proposed", "B1: a second type's landing reused the first's"
    assert other_type.candidate.type.name == "clinic"
    assert len(await _ledger(registry)) == 2

@NEEDS_LEDGER
async def test_c20_81_the_per_act_memory_is_written_on_every_branch_that_answers(
    adapter, make_registry
):
    """Rule **4-13** (finding B5). The pending branch binds the act as the minting one
    does, so the same identity landing again in that act is `reused`, not a second
    pending invocation. `existing` binds it too (B7)."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("rule 4-11's read needs invocation events to be complete")
    await _ingest_family(registry)
    act_11 = await _act(registry, "act-a")
    await act_11.land(NOTHING, type_name="facility")
    b = await _act(registry, "act-b")
    pending = await b.land(NOTHING, type_name="facility")
    assert pending.outcome == "pending", pending
    again = await b.land(NOTHING, type_name="facility")
    assert again.outcome == "reused" and again.candidate == pending.candidate
    assert len(await _ledger(registry)) == 2, "the pending branch left the act unbound"

@NEEDS_LEDGER
async def test_c20_71_r1_a_compensating_row_holds_nothing(adapter, make_registry):
    """Rule **4-11** (round 1, lens 1, MAJOR 1). A compensating invocation that carries
    the same candidate undoes the proposal; it does not become a holder, or the identity
    could never be proposed again."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry, mode="review")
    act_a = await _act(registry, "act-r1a")
    first = await act_a.land(NOTHING, type_name="facility")
    assert first.outcome == "proposed", first
    undo = await registry.record_invocation(
        "propose_facility", {"instance": first.candidate}, actor="user:sd",
        outcome="applied", approved_by="user:sd", compensates=first.invocation.invocation_id)
    assert not isinstance(undo, Refusal), undo
    held = await registry.invocations(unwritten_for=first.candidate)
    assert held.complete and [i.invocation_id for i in held.invocations] == [], held
    act_b = await _act(registry, "act-r1b")
    again = await act_b.land(NOTHING, type_name="facility")
    assert again.outcome == "proposed", again

@NEEDS_LEDGER
async def test_c20_71_r1_a_pending_warning_naming_no_holder_exempts_nothing(adapter, make_registry):
    """Rule **4-11** (round 1, lens 2, M1). `instance_proposal_pending:<id>` makes a row
    a non-holder only when `<id>` is a matching applied row of the same identity. A
    proposal recorded directly with a pending warning naming nothing real is a holder."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    res = await _resolve(registry, NOTHING)
    await _ingest_family(registry)
    forged = await registry.record_invocation(
        "propose_facility", {"instance": res.candidate}, actor="ai:ingest", outcome="applied",
        warnings=("instance_proposal_pending:bogus",))
    assert not isinstance(forged, Refusal), forged
    act_c = await _act(registry, "act-r1c")
    landing = await act_c.land(NOTHING, type_name="facility")
    assert landing.outcome == "pending", landing
    assert f"instance_proposal_pending:{forged.invocation_id}" in landing.invocation.warnings

@NEEDS_LEDGER
async def test_c20_71_r1_an_unrelated_broken_closure_does_not_stall_the_namespace(
    adapter, make_registry
):
    """Rule **4-11** (round 1, lens 2, M2). A ledger row for another type whose label is
    nothing like this identity cannot hold it, so its broken closure must not turn every
    A4 read in the namespace `complete=False`."""
    registry = await _world(adapter, make_registry)
    await host_instances(adapter, _rows(), type_name="widget")
    await seed(registry, "widget", attributes=_governed())
    await _ingest_family(registry)
    widget = await _resolve(registry, "qqqq widget nothing alike", type_name="widget")
    assert widget.outcome == "proposal", widget
    out = await registry.record_invocation("propose_facility", {"instance": widget.candidate},
                                     actor="ai:ingest", outcome="applied")
    assert not isinstance(out, Refusal), out
    await _rewrite(adapter, "widget", status="retired", successor="gadget_missing")
    cand = (await _resolve(registry, NOTHING)).candidate
    held = await registry.invocations(unwritten_for=cand)
    assert held.complete, held.why_incomplete
    act_d = await _act(registry, "act-r1d")
    assert (await act_d.land(NOTHING, type_name="facility")).outcome == "proposed"

@NEEDS_LEDGER
async def test_c20_72_r1_n_is_the_tied_set_not_the_display_list(adapter, make_registry):
    """Rule **4-12** with §4.3's K9 (round 1, lens 1, MAJOR 2). On a band ambiguous
    (rule 5-9) the resolution's `candidates` are the five best for display, sub-floor
    rows included; `<n>` is the multiplicity a reviewer chooses among -- the rows at or
    above `propose_below` within `ambiguity_margin` of the top."""
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    act_e = await _act(registry, "act-r1e")
    landing = await act_e.land(BAND, type_name="facility")
    res = landing.resolution
    assert res.outcome == "ambiguous" and res.known > 1, res
    floor = POLICY["propose_below"]
    above = [c for c in res.candidates if c.score is not None and c.score >= floor]
    assert len(above) == 1, [c.score for c in res.candidates]
    ambiguity = [w for w in landing.invocation.warnings
                 if w.startswith("instance_ambiguous_at_proposal:")]
    assert ambiguity == ["instance_ambiguous_at_proposal:instance:1"], ambiguity

@NEEDS_LEDGER
async def test_c20_70_r1_a_foreign_act_id_is_refused_before_the_recall(adapter, make_registry):
    """Rule **4-10**'s memory is the act's (round 1, lens 2, m3): a context naming another
    act is a `ValueError` even when the act already answered for the identity."""
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    act_f = await _act(registry, "act-A")
    await act_f.land(NOTHING, type_name="facility")
    with pytest.raises(ValueError):
        await act_f.land(NOTHING, type_name="facility",
                   context=InstanceContext(act_id="act-B", proposed_by="ai:ingest"))

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_41_r1_the_act_records_the_effective_entrys_policy(adapter, make_registry):
    """`I-7` at the act (round 1, lens 3, M2). Through `land`, the policy recorded is the
    EFFECTIVE entry's, with `governed_by` naming it -- not the declared type. Rule 3-18
    makes a closure whose entries disagree on the numbers `unknowable`, so the numbers
    are equal by construction and `governed_by` is the only thing that can be wrong."""
    registry = await _successor_world(adapter, make_registry, old_rows=_rows(), new_rows=_rows())
    await _ingest_family(registry)
    act_g = await _act(registry, "act-r1g")
    landing = await act_g.land(NOTHING, type_name="facility")
    assert landing.outcome == "proposed", landing
    assert landing.resolution.governed_by == "default:ltc_facility"
    assert landing.invocation.declared_policy["match_policy"] == {
        "governed_by": "default:ltc_facility", "match_at": 0.97, "propose_below": 0.80,
        "ambiguity_margin": 0.02,
    }, landing.invocation.declared_policy
