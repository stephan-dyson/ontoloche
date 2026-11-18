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
    match_policy_problem,
)
from ontoloche.aio.registry import AsyncRegistry
from ontoloche.types import Consumer, Refusal, ResolveContext, TypeEntry
from ontoloche.aio.contract._support import host_instances, seed, snapshot
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter


NEEDS_ATTRIBUTES = pytest.mark.requires_capability("stores_attributes")

NEEDS_RETIRE = pytest.mark.requires_capability("stores_attributes", "indexes_membership")

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
    await seed(registry, old, attributes=old_governed or _governed())
    await seed(registry, new, attributes=new_governed or _governed())
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

    for known in ("zero", "none"):
        degraded = AsyncDegradedAdapter(adapter, instance_known=known)
        registry = await make_registry(degraded)
        if known == "zero":
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
