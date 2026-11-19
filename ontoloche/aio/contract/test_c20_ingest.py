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
from ontoloche.actions import CARRIED_WARNINGS, Effect, InputSpec, parse_ref, ref_key  # noqa: E402
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
    assert f"instance_ambiguous_at_proposal:instance:{_tied_n(landing.resolution, BAND + ' ')}" in (
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

def _tied_n(res, label, policy=POLICY):
    """Rule 4-12's `<n>`: the rows a reviewer chooses among -- at or above `match_at`, or
    at or above `propose_below` within `ambiguity_margin` of the top (rules 3-3, 5-12),
    on the gate's UNROUNDED scores (the candidates' four places are display only)."""
    scores = [similar(norm(label), norm(c.label)) for c in res.candidates]
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
    assert _tied_n(res, BAND) != res.known, "the fixture must separate the tied set from known"
    assert ambiguity == [f"instance_ambiguous_at_proposal:instance:{_tied_n(res, BAND)}"], ambiguity

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

_EAST = "RENNES HEALTH AND REHAB CENTER EAST"

_WEST = "RENNES HEALTH AND REHAB CENTER WEST"

_WESTON = "RENNES HEALTH AND REHAB CENTER WESTON"

@NEEDS_LEDGER
async def test_c20_71_r2_a_pending_row_is_judged_against_its_own_identity(adapter, make_registry):
    """Rule **4-11**, amendment A4 (round 2, lens 1, M1). A `pending` row names the
    proposal that held ITS identity. Whether it is exempt is judged against its own
    label, not the reader's, or a pending row -- which proposes nothing and is never
    written -- becomes a permanent holder for a third label the gate calls distinct."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry)
    act_e, act_w, act_x = [await _act(registry, f"act-r2{c}") for c in "ewx"]
    east = await act_e.land(_EAST, type_name="facility")
    assert east.outcome == "proposed", east
    west = await act_w.land(_WEST, type_name="facility")
    assert west.outcome == "pending", west
    await registry.record_result(east.invocation.invocation_id,
                           {"instance": InstanceRef(east.candidate.type, "995101")},
                           actor="host:cms")
    weston = await act_x.land(_WESTON, type_name="facility")
    assert weston.outcome == "proposed", weston
    held = await registry.invocations(unwritten_for=weston.candidate)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        weston.invocation.invocation_id], held

@NEEDS_LEDGER
async def test_c20_71_r2_an_empty_incomplete_page_is_not_no_holder(adapter, make_registry):
    """Rule **4-11**, Rule U (round 2, lens 1, m1). An empty page with `complete=False`
    and no cursor is an unfinished read, not a confident empty ledger."""
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    cand = (await _resolve(registry, NOTHING)).candidate

    class _Stalled:
        def __init__(self, inner):
            object.__setattr__(self, "inner", inner)

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def __setattr__(self, name, value):
            setattr(self.inner, name, value)

        async def find_invocations(self, **kwargs):
            page = await self.inner.find_invocations(**kwargs)
            return type(page)(**{**page.__dict__, "records": (), "next_after": None,
                                 "complete": False,
                                 "why_incomplete": "the ledger could not be read"})

    stalled = await make_registry(_Stalled(adapter))
    held = await stalled.invocations(unwritten_for=cand)
    assert not held.complete and "could not be read" in (held.why_incomplete or ""), held

@NEEDS_LEDGER
async def test_c20_71_r2_a_proposal_recorded_in_another_namespace_still_holds(
    adapter, make_registry
):
    """Rule **4-10**'s key is the IDENTITY's namespace (round 2, lens 2, M2). A family in
    `ops` that records a candidate of `default:entity:facility` holds that identity for
    an act in `default`: A4 keys on the candidate's type, not on the ledger row's."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry)
    out = await action_family(registry, "propose_facility", namespace="ops", approval_mode="auto",
                        inputs=[InputSpec("instance", "candidate")], effects=[_HOST_WRITE])
    assert isinstance(out, TypeEntry), out
    cand = (await _resolve(registry, NOTHING)).candidate
    elsewhere = await registry.record_invocation("propose_facility", {"instance": cand},
                                           namespace="ops", actor="ai:ingest",
                                           outcome="applied")
    assert not isinstance(elsewhere, Refusal), elsewhere
    act_n = await _act(registry, "act-r2n")
    landing = await act_n.land(NOTHING, type_name="facility")
    assert landing.outcome == "pending", landing
    assert f"instance_proposal_pending:{elsewhere.invocation_id}" in landing.invocation.warnings

@NEEDS_LEDGER
async def test_c20_71_r2_a_failed_compensation_releases_nothing(adapter, make_registry):
    """Rule **4-11** (round 2, lens 2, M3). An undo that was tried and FAILED undid
    nothing, so the proposal it names still holds the identity."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry, mode="review")
    act_f = await _act(registry, "act-r2f")
    first = await act_f.land(NOTHING, type_name="facility")
    assert first.outcome == "proposed", first
    undo = await registry.record_invocation(
        "propose_facility", {"instance": first.candidate}, actor="user:sd",
        outcome="failed", compensates=first.invocation.invocation_id)
    assert not isinstance(undo, Refusal), undo
    act_g = await _act(registry, "act-r2g")
    again = await act_g.land(NOTHING, type_name="facility")
    assert again.outcome == "pending", again

@NEEDS_LEDGER
async def test_c20_71_r2_an_unfinished_a4_read_lands_unknowable_through_the_act(
    adapter, make_registry
):
    """§0.2 item 10, rule 4-11 with Rule U (round 2, lens 2, coverage). When A4 cannot
    say whether a matching row was written, the act proposes nothing: `unknowable`, and
    no second invocation is recorded."""
    blind = AsyncDegradedAdapter(adapter, stores_invocation_events=False)
    registry = await _world(blind, make_registry)
    if not registry.caps.stores_invocations:
        pytest.skip("this backend keeps no ledger")
    await _ingest_family(registry)
    act_u = await _act(registry, "act-r2u")
    first = await act_u.land(NOTHING, type_name="facility")
    assert first.outcome == "proposed", first
    act_v = await _act(registry, "act-r2v")
    second = await act_v.land(NOTHING, type_name="facility")
    assert second.outcome == "unknowable" and second.invocation is None, second
    assert len(await _ledger(registry)) == 1

@NEEDS_LEDGER
async def test_c20_30_r2_the_resolutions_carried_warnings_ride_onto_the_invocation(
    adapter, make_registry
):
    """Rule **4-4** with A3 (round 2, lens 2, coverage). The resolution's caller-reportable
    warnings travel onto the invocation the act records."""
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    act_w = await _act(registry, "act-r2w")
    landing = await act_w.land(NOTHING, type_name="facility")
    assert landing.outcome == "proposed", landing
    carried = [w for w in landing.resolution.warnings
               if w.split(":", 1)[0] in CARRIED_WARNINGS]
    assert carried, landing.resolution.warnings
    for w in carried:
        assert w in landing.invocation.warnings, (w, landing.invocation.warnings)

@NEEDS_LEDGER
async def test_c20_71_r3_every_candidate_input_of_a_row_is_judged(adapter, make_registry):
    """Rule **4-11**, amendment A4 (round 3, lenses 1 and 2). A row with two candidate
    inputs that both match holds the identity while EITHER is unwritten: a result for
    `a` writes `a`, not `b`. Judging only the first input that matched released `b`."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    out = await action_family(registry, "propose_pair", approval_mode="auto",
                        inputs=[InputSpec("a", "candidate"), InputSpec("b", "candidate")],
                        effects=[_HOST_WRITE])
    assert isinstance(out, TypeEntry), out
    cand = (await _resolve(registry, NOTHING)).candidate
    pair = await registry.record_invocation("propose_pair", {"a": cand, "b": cand},
                                      actor="ai:ingest", outcome="applied")
    assert not isinstance(pair, Refusal), pair
    wrote = await registry.record_result(pair.invocation_id,
                                   {"a": InstanceRef(cand.type, "995201")}, actor="host:cms")
    assert not isinstance(wrote, Refusal), wrote
    held = await registry.invocations(unwritten_for=cand)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        pair.invocation_id], held

@NEEDS_LEDGER
async def test_c20_28_r3_a_family_amended_after_the_act_began_is_judged_at_the_landing(
    adapter, make_registry
):
    """Rule **4-2** (round 3, lens 2, m1; rule 4-8 at the landing is `C20-28` r4). The act checks its family when it
    is created, and a family can be amended after that (`declaration_amended`). A landing
    under a family that no longer says the host writes the row is refused, as a fresh
    `ingest_act` would be, and records nothing."""
    registry = await _world(adapter, make_registry)
    if not registry.caps.stores_invocations:
        pytest.skip("this backend keeps no ledger")
    await _ingest_family(registry)
    act_q = await _act(registry, "act-r3q")
    from ontoloche.actions import action_attributes
    await registry.import_types([{
        "name": "propose_facility", "kind": "action", "definition": "amended",
        "status": "active",
        "attributes": action_attributes(
            reversibility="reversible", approval_mode="auto",
            inputs=[InputSpec("instance", "candidate")],
            effects=[Effect(op="propose_type", kind="entity", namespace="default",
                            why="the host write dropped")])}],
        namespace="default", kind="action")
    fresh = await registry.ingest_act("act-r3r", family="propose_facility", actor="ai:ingest",
                                tier="small")
    assert isinstance(fresh, Refusal) and fresh.reason == "attributes_schema_violation", fresh
    landing = await act_q.land(NOTHING, type_name="facility")
    assert landing.outcome == "refused", landing
    assert landing.refusal is not None
    assert landing.refusal.reason == "attributes_schema_violation", landing
    assert await _ledger(registry) == []

@NEEDS_LEDGER
async def test_c20_27_r3_a_gate_refusal_through_the_act_records_nothing(adapter, make_registry):
    """Rule **4-1** (round 3, lens 2, coverage). The act is an invocation of its family,
    so the gate's verdict binds it: a tier the family does not admit is refused and
    nothing is recorded."""
    registry = await _world(adapter, make_registry)
    out = await action_family(registry, "propose_facility", approval_mode="auto",
                        min_auto_tier="large", inputs=[InputSpec("instance", "candidate")],
                        effects=[_HOST_WRITE])
    assert isinstance(out, TypeEntry), out
    act_s = await _act(registry, "act-r3s", tier="small")
    landing = await act_s.land(NOTHING, type_name="facility")
    assert landing.outcome == "refused" and landing.invocation is None, landing
    assert await _ledger(registry) == []

@NEEDS_LEDGER
async def test_c20_81_r3_existing_binds_and_a_refused_landing_binds_nothing(
    adapter, make_registry
):
    """Rule **4-13** as amended in round 2 (round 3, lens 3, m2). An `existing` landing
    writes the per-act memory, so the act's next landing of that identity is `reused`;
    a `refused` landing recorded nothing and writes none, so it is refused again."""
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    act_t = await _act(registry, "act-r3t")
    first = await act_t.land(EXACT, type_name="facility")
    assert first.outcome == "existing", first
    again = await act_t.land(EXACT, type_name="facility")
    assert again.outcome == "reused" and again.ref == first.ref, again

    out = await action_family(registry, "propose_gated", approval_mode="auto",
                        min_auto_tier="large", inputs=[InputSpec("instance", "candidate")],
                        effects=[_HOST_WRITE])
    assert isinstance(out, TypeEntry), out
    act_u = await _act(registry, "act-r3u", family="propose_gated", tier="small")
    refused = await act_u.land(NOTHING, type_name="facility")
    assert refused.outcome == "refused", refused
    twice = await act_u.land(NOTHING, type_name="facility")
    assert twice.outcome == "refused", twice

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_71_r3_a_pending_row_is_exempt_through_the_closure_after_a_retire(
    adapter, make_registry
):
    """Rule **4-11** with `I-5`'s second form (round 3, lens 2, coverage). A proposal made
    under `facility`, and a pending row made under its successor after a retire, are one
    identity. When the proposal is written the pending row holds nothing, so the next
    landing proposes."""
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act_a, act_b, act_c = [await _act(registry, f"act-r3{c}") for c in "abc"]
    held = await act_a.land(NOTHING, type_name="facility")
    assert held.outcome == "proposed", held
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    pending = await act_b.land(NOTHING, type_name="ltc_facility")
    assert pending.outcome == "pending", pending
    await registry.record_result(held.invocation.invocation_id,
                           {"instance": InstanceRef(held.candidate.type, "995001")},
                           actor="host:cms")
    after = await act_c.land(NOTHING, type_name="ltc_facility")
    assert after.outcome == "proposed", after

@NEEDS_LEDGER
async def test_c20_71_r3_a_broken_target_closure_is_never_no_holder(adapter, make_registry):
    """Rule **4-11**, `I-2` at the direct door (round 3, lens 2, coverage). When the
    candidate's own closure cannot be finished, `invocations(unwritten_for=)` answers
    `complete=False`, never a confident empty."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry)
    act_o = await _act(registry, "act-r3o")
    first = await act_o.land(NOTHING, type_name="facility")
    assert first.outcome == "proposed", first
    await _rewrite(adapter, "facility", status="retired", successor="gone_missing")
    held = await registry.invocations(unwritten_for=first.candidate)
    assert not held.complete, held

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_70_r4_the_recall_follows_a_retire_inside_one_act(adapter, make_registry):
    """Rule **4-10** (round 4, lens 2, m1). The act's memory is keyed under the closure of
    `type_name`, so it holds when the type is retired between two landings of one act:
    `facility` is now `ltc_facility`, and the second landing of the identity the act
    already proposed is `reused`, not a fresh `pending` row."""
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act_t = await _act(registry, "act-r4t")
    first = await act_t.land(NOTHING, type_name="facility")
    assert first.outcome == "proposed", first
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    for type_name in ("facility", "ltc_facility"):
        again = await act_t.land(NOTHING, type_name=type_name)
        assert again.outcome == "reused", (type_name, again.outcome, again.why)
        assert again.candidate == first.candidate, again
    assert len(await _ledger(registry)) == 1

_PAIR_BASE = "kemubcrdlsbqgbcnnchcrnbsdhuusbssmbhbrejn"

@NEEDS_LEDGER
async def test_c20_71_r4_a_pending_row_is_exempt_only_when_each_candidate_is_held(
    adapter, make_registry
):
    """Rule **4-11** (round 4, lens 2, m2). A pending row with two candidates that match
    the reader, only one of them held by the row it names, is a holder for the other.
    At `match_at` 0.97 the reader R matches X and Y and X does not match Y."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry)
    await action_family(registry, "propose_pair", approval_mode="auto",
                  inputs=[InputSpec("a", "candidate"), InputSpec("b", "candidate")],
                  effects=[_HOST_WRITE])
    act_u = await _act(registry, "act-r4u")
    held = await act_u.land(_PAIR_BASE + "qz", type_name="facility")
    assert held.outcome == "proposed", held
    hid = held.invocation.invocation_id
    cx = (await _resolve(registry, _PAIR_BASE + "qz")).candidate
    cy = (await _resolve(registry, "qz" + _PAIR_BASE)).candidate
    pair = await registry.record_invocation("propose_pair", {"a": cx, "b": cy}, actor="ai:x",
                                      outcome="applied",
                                      warnings=(f"instance_proposal_pending:{hid}",))
    assert not isinstance(pair, Refusal), pair
    reader = (await _resolve(registry, _PAIR_BASE)).candidate
    ids = [i.invocation_id for i in (await registry.invocations(unwritten_for=reader)).invocations]
    # Rows recorded in the same instant order on their random ids, so compare as a set.
    assert sorted(ids) == sorted([hid, pair.invocation_id]), ids
    await registry.record_result(hid, {"instance": InstanceRef(cx.type, "995301")}, actor="host:cms")
    act_v = await _act(registry, "act-r4v")
    landing = await act_v.land("qz" + _PAIR_BASE, type_name="facility")
    assert landing.outcome == "pending", landing

@NEEDS_LEDGER
async def test_c20_28_r4_a_family_amended_to_propose_predicates_is_judged_at_the_landing(
    adapter, make_registry
):
    """Rule **4-8** at the landing (round 4, lens 3, m1). The public doors refuse a
    predicate-proposing family (`import_types` says `effect_not_permitted`), so this
    writes one past them, as a host with write access to the store can. The landing is
    refused and records nothing."""
    registry = await _world(adapter, make_registry)
    if not registry.caps.stores_invocations:
        pytest.skip("this backend keeps no ledger")
    await _ingest_family(registry)
    act_w = await _act(registry, "act-r4w")
    from ontoloche.actions import action_attributes
    rec = await adapter.get_type("default", "propose_facility", kind="action")
    await adapter.put_type(dataclasses.replace(rec, attributes=action_attributes(
        reversibility="reversible", approval_mode="auto",
        inputs=[InputSpec("instance", "candidate")],
        effects=[_HOST_WRITE, Effect(op="propose_type", kind="predicate",
                                     namespace="default", why="written past the door")])))
    landing = await act_w.land(NOTHING, type_name="facility")
    assert landing.outcome == "refused", landing
    assert landing.refusal is not None
    assert landing.refusal.reason == "attributes_schema_violation", landing
    assert "4-8" in landing.why, landing.why
    assert await _ledger(registry) == []

@NEEDS_LEDGER
async def test_c20_70_r5_the_recall_never_settles_an_ambiguity_the_gate_would_review(
    adapter, make_registry
):
    """Rule **4-10** with the gate's non-transitive relation (round 5, lens 2, MAJOR).
    At `match_at` 0.97 the label R matches X and Y and X does not match Y. One act lands
    X and Y, both `existing`. The gate calls R `ambiguous`, so the act's landing of R
    must be what a fresh act gives (a review-mode proposal), never a recall of whichever
    of X and Y the act landed first."""
    x, y, r = _PAIR_BASE + "qz", "qz" + _PAIR_BASE, _PAIR_BASE
    rows = [{"host_id": "X1", "label": x, "state": "AL"},
            {"host_id": "Y1", "label": y, "state": "AL"}]
    registry = await _world(adapter, make_registry, rows)
    await _ingest_family(registry)
    act_x = await _act(registry, "act-r5x")
    assert (await act_x.land(x, type_name="facility")).outcome == "existing"
    assert (await act_x.land(y, type_name="facility")).outcome == "existing"
    gate = await _resolve(registry, r)
    assert gate.outcome == "ambiguous", gate
    landing = await act_x.land(r, type_name="facility")
    assert landing.outcome != "reused", (landing.outcome, landing.ref, landing.why)
    assert landing.outcome == "proposed", landing
    assert landing.resolution is not None and landing.resolution.outcome == "ambiguous"
    # ...and a fresh act now finds that proposal as the identity's holder (rule 4-11),
    # where `written` is readable; without it A4's read is unfinished (`unknowable`).
    act_y = await _act(registry, "act-r5y")
    events = registry.caps.stores_events and registry.caps.stores_invocation_events
    assert (await act_y.land(r, type_name="facility")).outcome == (
        "pending" if events else "unknowable")

@NEEDS_LEDGER
async def test_c20_70_r5_two_proposals_the_reader_matches_are_never_recalled_by_order(
    adapter, make_registry
):
    """Rule **4-10** (round 5, lens 2, same root). One act proposes X and Y. R matches
    both, so the act does not hand R either `CandidateRef`: the gate decides, and rule
    4-11 finds the two unwritten proposals."""
    x, y, r = _PAIR_BASE + "qz", "qz" + _PAIR_BASE, _PAIR_BASE
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry)
    act_z = await _act(registry, "act-r5z")
    assert (await act_z.land(x, type_name="facility")).outcome == "proposed"
    assert (await act_z.land(y, type_name="facility")).outcome == "proposed"
    landing = await act_z.land(r, type_name="facility")
    assert landing.outcome == "pending", (landing.outcome, landing.why)

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_70_r5_a_recalled_ref_is_the_one_the_gate_gives_now(adapter, make_registry):
    """Rule **4-10** with rule 2-17 (round 5, lens 2, m2). After `facility` is retired
    toward `ltc_facility`, the gate answers `existing` under the effective type. The
    act's next landing of the same label gives that ref, not the retired member's."""
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act_e = await _act(registry, "act-r5e")
    first = await act_e.land(EXACT, type_name="facility")
    assert first.outcome == "existing" and first.ref.type.name == "facility", first
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    gate = await _resolve(registry, EXACT, type_name="ltc_facility")
    again = await act_e.land(EXACT, type_name="ltc_facility")
    assert again.ref == gate.ref, (again.outcome, again.ref, gate.ref)

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_70_r5_the_recall_defers_to_rule_3_18(adapter, make_registry):
    """Rule **4-10** with rule 3-18 (round 5, lens 1, m1). The successor declares its own
    `MatchPolicy`, so after the retire the gate declines to judge the extent
    (`unknowable`). The act's next landing says the same, and records nothing."""
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed(dict(POLICY, match_at=0.95)))
    await _ingest_family(registry)
    act_g = await _act(registry, "act-r5g")
    first = await act_g.land(NOTHING, type_name="facility")
    assert first.outcome == "proposed", first
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    gate = await _resolve(registry, NOTHING)
    assert gate.outcome == "unknowable", gate
    again = await act_g.land(NOTHING, type_name="facility")
    assert again.outcome == "unknowable", (again.outcome, again.why)
    assert len(await _ledger(registry)) == 1

@NEEDS_LEDGER
async def test_c20_70_r6_one_landed_neighbour_never_settles_an_ambiguity(adapter, make_registry):
    """Rule **4-10** (round 6, lens 2, MAJOR). The act has landed only X (`existing`).
    The gate calls R `ambiguous` over X's and Y's host rows, so the act's landing of R
    is the gate's: a review-mode proposal, never a recall of X's row."""
    x, y, r = _PAIR_BASE + "qz", "qz" + _PAIR_BASE, _PAIR_BASE
    rows = [{"host_id": "X1", "label": x, "state": "AL"},
            {"host_id": "Y1", "label": y, "state": "AL"}]
    registry = await _world(adapter, make_registry, rows)
    await _ingest_family(registry)
    act_k = await _act(registry, "act-r6k")
    assert (await act_k.land(x, type_name="facility")).outcome == "existing"
    assert (await _resolve(registry, r)).outcome == "ambiguous"
    landing = await act_k.land(r, type_name="facility")
    assert landing.outcome == "proposed", (landing.outcome, landing.ref, landing.why)
    assert landing.resolution is not None and landing.resolution.outcome == "ambiguous"

@NEEDS_LEDGER
async def test_c20_70_r6_a_repeat_of_a_label_the_act_answered_is_reused(adapter, make_registry):
    """Rules **4-10** and **4-13** (round 6, lenses 1 and 2, MINOR). Inside the
    non-transitive triple, a repeat of a label this act already answered is `reused`:
    the exact key is resolved once, and no pending row is added per repeat."""
    x, y, r = _PAIR_BASE + "qz", "qz" + _PAIR_BASE, _PAIR_BASE
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await _ingest_family(registry)
    act_m = await _act(registry, "act-r6m")
    first = [await act_m.land(label, type_name="facility") for label in (x, y, r)]
    assert [f.outcome for f in first] == ["proposed", "proposed", "pending"], first
    again = [await act_m.land(label, type_name="facility") for label in (x, r, x, r)]
    assert [a.outcome for a in again] == ["reused"] * 4, [(a.outcome, a.why) for a in again]
    assert again[0].candidate == first[0].candidate and again[1].candidate == first[2].candidate
    assert len(await _ledger(registry)) == 3

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_70_r6_after_a_retire_the_gate_answers_once_and_is_recalled(adapter, make_registry):
    """Rule **4-10** with rule 2-17 (round 6, lens 2, m2). The host row exists only under
    the retired member's name. After the retire the gate is asked once, and its answer
    is recalled from then on."""
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, [], type_name="ltc_facility")   # bound, and empty
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act_n = await _act(registry, "act-r6n")
    assert (await act_n.land(EXACT, type_name="facility")).outcome == "existing"
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    gate = await _resolve(registry, EXACT, type_name="ltc_facility")
    after = [await act_n.land(EXACT, type_name="ltc_facility") for _ in range(3)]
    assert [a.outcome for a in after] == ["existing", "reused", "reused"], after
    assert all(a.ref == gate.ref for a in after), (gate.ref, [a.ref for a in after])

@NEEDS_LEDGER
async def test_c20_70_r6_the_cms_triple_with_one_landed_neighbour(adapter, make_registry):
    """Rule **4-10** over real CMS labels (round 6, lens 3, MAJOR). Host rows E1 (EAST)
    and W2 (WESTON); EAST ~ WEST and WEST ~ WESTON, EAST !~ WESTON. The act lands EAST
    (`existing`), and its landing of WEST is the gate's review-mode proposal, never E1."""
    rows = [{"host_id": "E1", "label": _EAST, "state": "AL"},
            {"host_id": "W2", "label": _WESTON, "state": "AL"}]
    registry = await _world(adapter, make_registry, rows)
    await _ingest_family(registry)
    act_p = await _act(registry, "act-r6p")
    assert (await act_p.land(_EAST, type_name="facility")).outcome == "existing"
    assert (await _resolve(registry, _WEST)).outcome == "ambiguous"
    landing = await act_p.land(_WEST, type_name="facility")
    assert landing.outcome == "proposed", (landing.outcome, landing.ref, landing.why)
    assert landing.resolution is not None and landing.resolution.outcome == "ambiguous"

@NEEDS_LEDGER
async def test_c20_70_r6_a_remembered_proposal_never_hides_a_host_row(adapter, make_registry):
    """Rule **4-10** (round 6, lens 3, same root). The act proposed X; the host holds Y.
    The gate answers R `existing` (Y's row), and so does the act."""
    x, y, r = _PAIR_BASE + "qz", "qz" + _PAIR_BASE, _PAIR_BASE
    registry = await _world(adapter, make_registry, [{"host_id": "Y1", "label": y, "state": "AL"}])
    await _ingest_family(registry)
    act_q = await _act(registry, "act-r6q")
    assert (await act_q.land(x, type_name="facility")).outcome == "proposed"
    gate = await _resolve(registry, r)
    assert gate.outcome == "existing", gate
    landing = await act_q.land(r, type_name="facility")
    assert landing.outcome == "existing" and landing.ref == gate.ref, (
        landing.outcome, landing.ref, landing.why)

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_70_r6_after_a_retire_the_exact_key_is_recalled_before_the_gate(
    adapter, make_registry
):
    """Rule **4-10** (post-cap fix, a pin the sweep asked for). The exact key reads each
    entry's closure NOW. Inside the non-transitive triple the act holds three candidates
    within `match_at` of R, so after a retire only the exact recall of R's own candidate
    gives `reused`: the similar-candidate step sees three and goes on to A4."""
    x, y, r = _PAIR_BASE + "qz", "qz" + _PAIR_BASE, _PAIR_BASE
    await host_instances(adapter, _rows(), type_name="facility")
    await host_instances(adapter, _rows(), type_name="ltc_facility")
    registry = await make_registry(adapter)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("`written` is an event, and this backend keeps none")
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act_w = await _act(registry, "act-r6w")
    first = [await act_w.land(label, type_name="facility") for label in (x, y, r)]
    assert [f.outcome for f in first] == ["proposed", "proposed", "pending"], first
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    again = await act_w.land(r, type_name="ltc_facility")
    assert again.outcome == "reused" and again.candidate == first[2].candidate, (
        again.outcome, again.why)
    assert len(await _ledger(registry)) == 3

@NEEDS_LEDGER
async def test_c20_70_d1_a_pending_candidate_never_absorbs_a_distinct_label(adapter, make_registry):
    """Rule **4-10**, ING15 (row 7c's post-cap review, MAJOR). Act A proposes EAST; act B
    lands WEST `pending` behind A's row; the gate answers WESTON `proposal`. WEST's
    candidate is A's identity, and EAST ~ WESTON is 0.944, below `match_at`, so reusing
    it folds WESTON into EAST with no reviewer. The similar step reuses only a candidate
    the act itself PROPOSED: B proposes WESTON, exactly as a fresh act would."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    act_a, act_b, act_c = [await _act(registry, f"act-d1{c}") for c in "abc"]
    east = await act_a.land(_EAST, type_name="facility")
    assert east.outcome == "proposed", east
    west = await act_b.land(_WEST, type_name="facility")
    assert west.outcome == "pending", west
    assert (await _resolve(registry, _WESTON)).outcome == "proposal"
    weston = await act_b.land(_WESTON, type_name="facility")
    assert weston.outcome == "proposed", (weston.outcome, weston.why)
    assert weston.invocation is not None and not any(
        w.startswith("instance_proposal_pending:") for w in weston.invocation.warnings
    ), weston.invocation.warnings
    held = await registry.invocations(unwritten_for=weston.candidate)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        weston.invocation.invocation_id], held
    fresh = await act_c.land(_WESTON, type_name="facility")
    assert fresh.outcome == "pending", (fresh.outcome, fresh.why)

@NEEDS_LEDGER
async def test_c20_70_d1_a_recalled_pending_label_says_what_holds_it(adapter, make_registry):
    """Rule **4-10** (ING15's minor, 7C-RUN 2.8 finding 2). A repeat of a label this act
    landed `pending` is `reused` (rule 4-13), and its why names the holder's invocation:
    this act proposed nothing for it."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    act_a, act_b = [await _act(registry, f"act-d2{c}") for c in "ab"]
    east = await act_a.land(_EAST, type_name="facility")
    assert east.outcome == "proposed", east
    assert (await act_b.land(_WEST, type_name="facility")).outcome == "pending"
    again = await act_b.land(_WEST, type_name="facility")
    assert again.outcome == "reused", again
    assert east.invocation.invocation_id in again.why, again.why
    assert "pending" in again.why and "proposed" not in again.why, again.why

_HIGH_FLOOR = {"match_at": 0.97, "propose_below": 0.96, "ambiguity_margin": 0.0,
               "why": "C20 row 7d: a floor above 0.944, so the similar step is reachable"}

@NEEDS_LEDGER
async def test_c20_70_d1_a_remembered_host_ref_is_never_a_similar_candidate(
    adapter, make_registry
):
    """Rule **4-10** (ING15's minor, 7C-RUN 2.8 finding 3). The similar step reuses only
    a candidate the act proposed. A remembered `existing` ref within `match_at` must not
    override the gate's `proposal`: the host row is EAST, the act lands WEST (`existing`,
    0.971), and WESTON (0.944 to EAST, 0.972 to WEST) is the gate's proposal."""
    registry = await _world(adapter, make_registry,
                      [{"host_id": "E1", "label": _EAST, "state": "AL"}], policy=_HIGH_FLOOR)
    await _ingest_family(registry)
    act_h = await _act(registry, "act-d3")
    assert (await act_h.land(_WEST, type_name="facility")).outcome == "existing"
    assert (await _resolve(registry, _WESTON)).outcome == "proposal"
    weston = await act_h.land(_WESTON, type_name="facility")
    assert weston.outcome == "proposed", (weston.outcome, weston.why)
    assert weston.ref is None and isinstance(weston.candidate, CandidateRef), weston

async def test_c20_05_d1_a_dropped_table_is_the_drivers_error_whatever_its_name(
    adapter, make_registry
):
    """Rule **2-2** (7B-RUN 2.6, build lens minor 1). Only the driver's own decode
    failure is a row that cannot be rendered. A dropped host table whose NAME contains
    "decode" is the same driver error as any other dropped table, never `NotSupported`
    with a why about an id that cannot be text."""
    from ontoloche.errors import NotSupported

    target = getattr(adapter, "inner", adapter)
    if not hasattr(target, "_instance_tables") or not hasattr(target, "_execute"):
        pytest.skip("only the SQL backends bind a host table this suite can drop")
    await host_instances(adapter, _rows(), type_name="decode_site")
    binding = next(b for b in target._instance_tables.values() if b.type_name == "decode_site")
    assert "decode" in binding.table, binding.table
    await target._execute(f'DROP TABLE "{binding.table}"')
    with pytest.raises(Exception) as caught:
        await target.get_instance("default", "entity", "decode_site", "015009")
    assert not isinstance(caught.value, NotSupported), caught.value

def test_c20_47_d1_a_huge_fraction_is_finite_and_never_a_crash(adapter):
    """Rule **6-6** (7B-RUN 2.6, build lens minor 2). `Fraction(10**400)` is finite.
    `float()` of it overflows, so it is judged as a rational, never converted."""
    from fractions import Fraction

    for value in (Fraction(10 ** 400), Fraction(-(10 ** 400), 3), [Fraction(1, 10 ** 400)]):
        op = "in" if isinstance(value, list) else "eq"
        assert condition_problem({"op": op, "attribute": "x", "value": value,
                                  "why": "w"}) is None, value

def test_c20_47_d1_a_deep_or_shared_operand_is_walked_once(adapter):
    """Rule **6-6** (7B-RUN 2.6, build lens minor 3). The operand walk visits each
    container once: a list nested 5,000 deep is judged without `RecursionError`, and a
    sub-list shared at 20 levels (a million paths) is judged at once. A non-finite
    member at the bottom is still found, and a container holding itself is still
    refused."""
    import time

    deep: list = [1.5]
    for _ in range(5000):
        deep = [deep]
    assert condition_problem({"op": "in", "attribute": "x", "value": [deep],
                              "why": "w"}) is None
    bad: list = [float("nan")]
    for _ in range(5000):
        bad = [bad]
    assert condition_problem({"op": "in", "attribute": "x", "value": [bad], "why": "w"})
    shared: list = [2.5]
    for _ in range(20):
        shared = [shared, shared]
    began = time.perf_counter()
    assert condition_problem({"op": "in", "attribute": "x", "value": shared,
                              "why": "w"}) is None
    assert time.perf_counter() - began < 1.0
    loop: list = [[1.0]]
    loop[0].append(loop)
    assert condition_problem({"op": "in", "attribute": "x", "value": loop, "why": "w"})

@pytest.mark.requires_capability("stores_attributes", "stores_proposals")
async def test_c20_34_d1_the_allowlist_holds_at_approve_and_import_types(adapter, make_registry):
    """Rule **4-8** (7C-RUN 2.1, recorded: `C20-34` covered two of the four doors in a
    test, the probe the rest). A predicate-proposing family written into a pending
    proposal past validation is refused at `approve`, and the same family is refused at
    `import_types`. Neither reaches the type store."""
    from ontoloche.actions import action_attributes

    registry = await _world(adapter, make_registry)
    bad = [_HOST_WRITE, Effect(op="propose_type", namespace="default", kind="predicate")]
    attrs = action_attributes(reversibility="reversible", approval_mode="auto",
                              inputs=[InputSpec("instance", "candidate")], effects=bad)
    clean = action_attributes(reversibility="reversible", approval_mode="auto",
                              inputs=[InputSpec("instance", "candidate")],
                              effects=[_HOST_WRITE])
    pending = await registry.propose_type("mint_b", "clean, amended past validation", [],
                                    "user:sd", kind="action", attributes=clean)
    assert getattr(pending, "id", None) is not None, pending
    rec = await adapter.get_proposal(pending.id)
    await adapter.put_proposal(dataclasses.replace(rec, attributes={
        **rec.attributes, "effects": [e.to_dict() for e in bad]}))
    approved = await registry.approve(pending.id, "user:sd")
    assert isinstance(approved, Refusal) and approved.reason == "effect_not_permitted", approved
    assert (await adapter.get_proposal(pending.id)).status == "pending"
    imported = (await registry.import_types(
        [{"name": "mint_c", "kind": "action", "status": "active",
          "definition": "mints predicates, imported", "attributes": attrs}],
        namespace="default", kind="action"))[0]
    assert "import_refused:effect_not_permitted" in imported.warnings, imported
    for name in ("mint_b", "mint_c"):
        assert await adapter.get_type("default", name, kind="action") is None, name

class _LedgerDouble:
    """Wraps an adapter and rewrites `find_invocations` pages (row 7d, C7 and C10)."""

    def __init__(self, inner, page):
        object.__setattr__(self, "inner", inner)
        object.__setattr__(self, "page", page)
        object.__setattr__(self, "calls", [0])

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def __setattr__(self, name, value):
        setattr(self.inner, name, value)

    async def find_invocations(self, **kwargs):
        self.calls[0] += 1
        if self.calls[0] > 200:
            raise RuntimeError("the ledger read never stopped")
        if kwargs.get("after") == "the-same-cursor":
            # A cursor this double minted is not the backend's: answer for it here.
            first = await self.inner.find_invocations(**{**kwargs, "after": None})
            return self.page(type(first)(**{**first.__dict__, "records": ()}), kwargs)
        return self.page(await self.inner.find_invocations(**kwargs), kwargs)

@NEEDS_LEDGER
async def test_c20_71_d1_a_repeated_cursor_is_an_unfinished_read(adapter, make_registry):
    """Rule **4-11**, Rule U (7C-RUN 2.2 #6 and 2.3 #7, recorded: A4's cursor-repeat
    guard). A ledger whose cursor comes back unchanged would be read forever. A4 stops
    and answers incomplete, never a confident "no holder"."""
    registry = await _world(adapter, make_registry)
    await _ingest_family(registry)
    cand = (await _resolve(registry, NOTHING)).candidate
    def repeat(page, kwargs):
        return type(page)(**{**page.__dict__, "next_after": "the-same-cursor"})

    looping = await make_registry(_LedgerDouble(adapter, repeat))
    held = await looping.invocations(unwritten_for=cand)
    assert not held.complete and "repeated" in (held.why_incomplete or ""), held

@NEEDS_LEDGER
async def test_c20_71_d1_a4_holds_at_exactly_match_at(adapter, make_registry):
    """Rule **4-10**'s key in A4 (7C-RUN 2.2 #6, recorded): `similar >= match_at` holds
    at equality. The policy's `match_at` is set to the two labels' own score."""
    from ontoloche.ingest import norm, similar

    a, b = _EAST, _WEST
    at = similar(norm(a), norm(b))
    policy = {"match_at": at, "propose_below": 0.5, "ambiguity_margin": 0.0,
              "why": "C20 row 7d: match_at is EAST ~ WEST exactly"}
    registry = await _world(adapter, make_registry, policy=policy)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    act_a = await _act(registry, "act-d4a")
    first = await act_a.land(a, type_name="facility")
    assert first.outcome == "proposed", first
    cand_b = (await _resolve(registry, b)).candidate
    held = await registry.invocations(unwritten_for=cand_b)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        first.invocation.invocation_id], held

@NEEDS_LEDGER
async def test_c20_71_d1_a_pending_row_naming_a_failed_row_is_not_exempt(adapter, make_registry):
    """Rule **4-11** (7C-RUN 2.3 #7, recorded: the proposals filter). A pending row is
    exempt only when the row it names is an APPLIED proposal of its candidate. A row
    naming a `failed` invocation holds the identity itself."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    cand = (await _resolve(registry, NOTHING)).candidate
    failed = await registry.record_invocation("propose_facility", {"instance": cand},
                                        actor="ai:ingest", outcome="failed")
    assert not isinstance(failed, Refusal), failed
    named = await registry.record_invocation(
        "propose_facility", {"instance": cand}, actor="ai:ingest", outcome="applied",
        warnings=(f"instance_proposal_pending:{failed.invocation_id}",))
    assert not isinstance(named, Refusal), named
    held = await registry.invocations(unwritten_for=cand)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        named.invocation_id], held

@NEEDS_LEDGER
async def test_c20_71_d1_an_unreadable_compensation_is_an_unfinished_read(adapter, make_registry):
    """Rule **4-11**, Rule U (7C-RUN 2.3 #7, recorded: the `why_not` branch). When the
    read of who compensated a holder cannot finish, A4 does not know whether the undo
    was applied, so it answers incomplete."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    cand = (await _resolve(registry, NOTHING)).candidate
    first = await registry.record_invocation("propose_facility", {"instance": cand},
                                       actor="ai:ingest", outcome="applied")
    undo = await registry.record_invocation("propose_facility", {"instance": cand},
                                      actor="ai:ingest", outcome="failed",
                                      compensates=first.invocation_id)
    assert not isinstance(undo, Refusal), undo

    def stall_compensations(page, kwargs):
        # Only the paged read of who compensated a holder (it passes `after=`), not
        # the one-row `compensated_by` lookup.
        if kwargs.get("compensates") is None or "after" not in kwargs:
            return page
        return type(page)(**{**page.__dict__, "records": (), "next_after": None,
                             "complete": False,
                             "why_incomplete": "the compensations could not be read"})

    stalled = await make_registry(_LedgerDouble(adapter, stall_compensations))
    held = await stalled.invocations(unwritten_for=cand)
    assert not held.complete and "compensations could not be read" in (
        held.why_incomplete or ""), held

@NEEDS_LEDGER
async def test_c20_71_d1_a_result_for_an_unmatched_input_releases_nothing(adapter, make_registry):
    """Rule **4-11**, amendment A2 (7C-RUN 2.3 #7, recorded: `results` loosened to any
    input). A row with two candidate inputs, only `a` matching, is written for the
    identity only by a result for `a`. A result for `b` releases nothing."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    out = await action_family(registry, "propose_pair", approval_mode="auto",
                        inputs=[InputSpec("a", "candidate"), InputSpec("b", "candidate")],
                        effects=[_HOST_WRITE])
    assert isinstance(out, TypeEntry), out
    cand = (await _resolve(registry, NOTHING)).candidate
    other = (await _resolve(registry, _EAST)).candidate
    pair = await registry.record_invocation("propose_pair", {"a": cand, "b": other},
                                      actor="ai:ingest", outcome="applied")
    assert not isinstance(pair, Refusal), pair
    wrote = await registry.record_result(pair.invocation_id,
                                   {"b": InstanceRef(other.type, "995301")}, actor="host:cms")
    assert not isinstance(wrote, Refusal), wrote
    held = await registry.invocations(unwritten_for=cand)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        pair.invocation_id], held

@NEEDS_LEDGER
async def test_c20_71_d1_unwritten_for_takes_only_a_candidate(adapter, make_registry):
    """Amendment A4 (7C-RUN 2.3 #7, recorded: the `CandidateRef` type check). A4 keys
    on a proposed thing. An `InstanceRef` names a written one, and is a `ValueError`."""
    registry = await _world(adapter, make_registry)
    with pytest.raises(ValueError, match="takes a CandidateRef"):
        await registry.invocations(unwritten_for=InstanceRef(TypeRef("default", "entity",
                                                               "facility"), "015009"))

@NEEDS_LEDGER
async def test_c20_71_d1_a4_reads_past_the_first_page(adapter, make_registry):
    """Rule **4-11**, amendment A4 (iii) (7C-RUN 2.1, recorded: no mutation for reading
    only the oldest page). With one row per page, a holder recorded after three
    unrelated rows is found, and the read is complete."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    for label in (_EAST, _WEST, _WESTON):
        cand_x = (await _resolve(registry, label)).candidate
        assert not isinstance(await registry.record_invocation(
            "propose_facility", {"instance": cand_x}, actor="ai:ingest",
            outcome="applied"), Refusal)
    cand = (await _resolve(registry, NOTHING)).candidate
    holder = await registry.record_invocation("propose_facility", {"instance": cand},
                                        actor="ai:ingest", outcome="applied")
    held = await registry.invocations(unwritten_for=cand, limit=1)
    assert held.complete and [i.invocation_id for i in held.invocations] == [
        holder.invocation_id], held

def test_c20_47_d1_a_freed_container_never_hides_a_later_one(adapter):
    """Rule **6-6** (7D-RUN 2.1, round 1 lens 1 #3 and lens 2 #5). The walk remembers a
    finished container by `id()`, so it keeps that container alive: a mapping that builds
    its values fresh on each read frees the first one, and CPython hands its id to the
    next, whose NaN was skipped. And the end-of-members sentinel is the walk's own, so an
    operand carrying the module's container tuple is walked past it."""
    from collections.abc import Mapping

    from ontoloche.ingest import _CONTAINERS, _non_finite

    class Fresh(Mapping):
        def __init__(self, x):
            self.x = x

        def __getitem__(self, key):
            return [self.x]

        def __iter__(self):
            return iter(("k",))

        def __len__(self):
            return 1

    nan = float("nan")
    assert _non_finite([Fresh(nan)])
    for n in range(1, 40):      # CPython hands a freed id on; some n meets it
        assert _non_finite([Fresh(1.0) for _ in range(n)] + [Fresh(nan)]), n
    assert _non_finite([_CONTAINERS, nan])

async def _undo(registry, landing):
    out = await registry.record_invocation(
        "propose_facility", {"instance": landing.candidate}, actor="user:sd",
        outcome="applied", approved_by="user:sd",
        compensates=landing.invocation.invocation_id)
    assert not isinstance(out, Refusal), out

async def _write(registry, landing, row_id):
    out = await registry.record_result(landing.invocation.invocation_id,
                                 {"instance": InstanceRef(landing.candidate.type, row_id)},
                                 actor="host:cms")
    assert not isinstance(out, Refusal), out

@NEEDS_LEDGER
@pytest.mark.parametrize("ends", ["compensated", "written"])
async def test_c20_70_d1_an_own_proposal_that_ended_is_not_reused(adapter, make_registry, ends):
    """Rule **4-10**, ING16 (7D-RUN 2.2, round 2). The act reuses a candidate it proposed
    only while its own row is still unwritten. The act proposes EAST; an applied row then
    undoes EAST's row (`C20-71` r1's shape), or `record_result` writes it with no host
    row (r2's). The act's WEST, within `match_at` of EAST,
    lands as a fresh act's would, proposed and not reused onto the ended candidate, and
    the repeat of EAST then goes to the gate and onto the act's live WEST proposal."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry, mode="review" if ends == "compensated" else "auto")
    act = await _act(registry, "act-i16")
    east = await act.land(_EAST, type_name="facility")
    assert east.outcome == "proposed", east
    (await _undo(registry, east) if ends == "compensated" else await _write(registry, east, "995161"))
    fresh_act = await _act(registry, "act-i16f")
    fresh = await fresh_act.land(_WEST, type_name="facility")
    assert fresh.outcome == "proposed", fresh
    await _undo(registry, fresh) if ends == "compensated" else await _write(registry, fresh, "995162")
    west = await act.land(_WEST, type_name="facility")
    assert west.outcome == "proposed", west
    assert west.candidate != east.candidate
    again = await act.land(_EAST, type_name="facility")   # its memory of EAST ended: the gate,
    assert again.outcome == "reused" and again.candidate == west.candidate, again  # then WEST

@NEEDS_LEDGER
@pytest.mark.parametrize("ends", ["compensated", "written"])
async def test_c20_70_d1_a_pending_label_whose_holder_ended_is_landed_again(adapter, make_registry,
                                                                      ends):
    """Rule **4-10**, ING16 (7D-RUN 2.2, round 2). Act A proposes EAST and act B lands
    WEST `pending` behind it. A's row is then undone or written. B's repeat of WEST lands
    as a fresh act's would, `proposed`, never `reused` behind a holder that holds nothing."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry, mode="review" if ends == "compensated" else "auto")
    act_a = await _act(registry, "act-i16a")
    act_b = await _act(registry, "act-i16b")
    east = await act_a.land(_EAST, type_name="facility")
    west = await act_b.land(_WEST, type_name="facility")
    assert (east.outcome, west.outcome) == ("proposed", "pending"), (east, west)
    (await _undo(registry, east) if ends == "compensated" else await _write(registry, east, "995163"))
    again = await act_b.land(_WEST, type_name="facility")
    assert again.outcome == "proposed", again

@NEEDS_RETIRE
@NEEDS_LEDGER
@pytest.mark.parametrize("banded", [False, True])
async def test_c20_70_d1_a_candidate_remembered_before_a_retire_goes_to_the_gate(
        adapter, make_registry, banded):
    """Rule **4-10** (7D-RUN 2.2, round 2 lens 2 #1). A remembered candidate is reused only
    after the gate, like a remembered host row after its closure changed. The act proposes
    a label under `ltc_facility`; `facility`, whose host table holds the label, is then
    retired toward `ltc_facility`. The act's repeat lands `existing` on that row, as a
    fresh act's does, never `reused` onto a second identity for one host thing. With the
    host row only in the band, the act reuses its own live candidate and a fresh act lands
    `pending` behind it: both mint nothing."""
    label = _PAIR_BASE[:34] + "zzzzzz" if banded else _PAIR_BASE
    await host_instances(adapter, [{"host_id": "H1", "label": label, "state": "AL"}],
                   type_name="facility")
    await host_instances(adapter, _rows()[1:2], type_name="ltc_facility")
    registry = await make_registry(adapter)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act = await _act(registry, "act-i16r")
    first = await act.land(_PAIR_BASE, type_name="ltc_facility")
    assert first.outcome == "proposed", first
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    again = await act.land(_PAIR_BASE, type_name="ltc_facility")
    fresh_act = await _act(registry, "act-i16rf")
    fresh = await fresh_act.land(_PAIR_BASE, type_name="ltc_facility")
    if banded:
        assert (again.outcome, again.candidate) == ("reused", first.candidate), again
        assert fresh.outcome == "pending", fresh
    else:
        assert fresh.outcome == "existing", fresh
        assert (again.outcome, again.ref) == ("existing", fresh.ref), again

def test_c20_47_d1_a_number_that_is_also_a_mapping_is_judged_as_a_number(adapter):
    """Rule **6-6** (7D-RUN 2.2, round 2 lens 2 #3). An operand that is both a number and
    a container is judged as the number first, as the recursive walk did: a NaN float that
    is also an empty mapping is refused."""
    from collections.abc import Mapping

    from ontoloche.ingest import _non_finite

    class FloatMap(float, Mapping):
        def __getitem__(self, key):
            raise KeyError(key)

        def __iter__(self):
            return iter(())

        def __len__(self):
            return 0

    assert _non_finite(FloatMap("nan"))
    assert _non_finite([FloatMap("nan")])

@NEEDS_RETIRE
@NEEDS_LEDGER
async def test_c20_70_d1_a_host_row_remembered_before_the_closure_grew_goes_to_the_gate(
        adapter, make_registry):
    """Rule **4-10** (7D-RUN 2.3, round 3 lens 2 #1). A host row remembered before the
    closure CHANGED goes back to the gate, and the closure changes when its members do,
    not only its effective name. The act lands a label `existing` on an `ltc_facility`
    row; `facility`, whose table holds an exact twin, is then retired toward
    `ltc_facility`. The effective entry is still `ltc_facility`, and the gate now sees two
    rows at 1.0. The act's repeat is the gate's `ambiguous`, as a fresh act's is, never a
    `reused` that hides the tie from every reviewer."""
    label = _EAST
    await host_instances(adapter, [{"host_id": "OLD1", "label": label, "state": "AL"}],
                   type_name="facility")
    await host_instances(adapter, [{"host_id": "NEW1", "label": label, "state": "AL"}],
                   type_name="ltc_facility")
    registry = await make_registry(adapter)
    await seed(registry, "facility", attributes=_governed())
    await seed(registry, "ltc_facility", attributes=_governed())
    await _ingest_family(registry)
    act = await _act(registry, "act-r3a")
    first = await act.land(label, type_name="ltc_facility")
    assert first.outcome == "existing", first
    gone = await registry.retire("facility", "renamed", retired_by="user:sd",
                           successor="ltc_facility")
    assert isinstance(gone, TypeEntry), gone
    again = await act.land(label, type_name="ltc_facility")
    assert again.outcome != "reused", again
    assert again.resolution is not None and again.resolution.outcome == "ambiguous", again

@NEEDS_LEDGER
async def test_c20_70_d1_a_similar_reuse_says_when_its_row_could_not_be_read(adapter, make_registry):
    """Rule **4-10**, ING16 (7D-RUN 2.3, round 3 lens 1 #1). When the read of whether a
    remembered candidate's row still holds it cannot finish, the act's own answer stands
    and the landing says the check could not be made, on the similar step as on the exact
    key. Forced here by a ledger whose read of the act's own row never finishes."""
    registry = await _world(adapter, make_registry)
    if not (registry.caps.stores_events and registry.caps.stores_invocation_events):
        pytest.skip("A4's read needs invocation events, and this backend keeps none")
    await _ingest_family(registry)
    act = await _act(registry, "act-r3b")
    east = await act.land(_EAST, type_name="facility")
    assert east.outcome == "proposed", east

    def unfinished(page, kwargs):
        return type(page)(**{**page.__dict__, "complete": False, "next_after": None,
                             "why_incomplete": "the ledger read did not finish here"})

    act._registry = await make_registry(_LedgerDouble(adapter, unfinished))
    west = await act.land(_WEST, type_name="facility")
    assert west.outcome == "reused" and west.candidate == east.candidate, west
    assert "could not be read" in west.why, west.why
