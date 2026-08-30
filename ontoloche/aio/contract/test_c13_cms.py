# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c13_cms.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C13 -- the CMS design test (5). PACKAGE.md 8.

The 0.5 sample, loaded through the adapter, asserted against the pre-registered ground
truth. **The registry stores types, not instances:** the 400 rows do not become 400 rows
in the type store. Eight type rows and eight usage rows is what "the sample loads" means.
"""

from __future__ import annotations
import pytest
from ontoloche.aio.adapter import TypeQuery
from ontoloche.types import Proposal, TypeEntry
from ontoloche.aio.contract._support import FIXTURE, SEVERITY_ORDERING, load_cms_sample, sample_facts


pytestmark = [
    pytest.mark.cms,
    pytest.mark.skipif(
        not FIXTURE.exists(),
        reason=(
            "the 400-row public CMS sample is not present; regenerate it with "
            "python tools/make_sample_state.py --download"
        ),
    ),
]

PREREGISTERED = {
    "facility": 10,
    "survey": 69,
    "citation": 400,
    "deficiency_tag": 92,
}

@pytest.fixture
async def loaded(registry):
    return registry, await load_cms_sample(registry)

async def test_c13_01_the_samples_vocabulary_loads_as_eight_type_rows(loaded, adapter):
    registry, _ = loaded
    page = await adapter.find_types(TypeQuery(include_retired=True))
    # Eight from the sample, plus the one family a version-4 store ships seeded
    # (`default:edge:equivalent_to`, EDGES.md 3.1). The eight is the number this test
    # is about; the ninth is subtracted by name rather than by loosening the count,
    # because "nine or so" is how a count assertion stops catching the 400 case.
    seeded = [r for r in page.records if (r.kind, r.name) == ("edge", "equivalent_to")]
    assert len(seeded) == 1
    records = tuple(r for r in page.records if r not in seeded)
    assert len(records) == 8, (
        "eight type rows, not four hundred -- reading 'the sample loads' as '400 "
        "citations become types' is the T3/T6 failure the ground truth predicted"
    )

    by_kind: dict[str, list[str]] = {}
    for rec in records:
        by_kind.setdefault(rec.kind, []).append(rec.name)
    assert sorted(by_kind["entity"]) == ["citation", "deficiency_tag", "facility", "survey"]
    assert sorted(by_kind["value_set"]) == [
        "deficiency_corrected_status",
        "scope_severity_code",
    ]
    assert sorted(by_kind["edge"]) == ["conducted_at", "issued_during"]

    assert await adapter.find_consumers("default") == [], (
        "nothing in a CSV registers a consumer, and consumers() says so"
    )
    assert (await registry.consumers("facility")).known == 0
    assert (await registry.consumers("facility")).complete is False

@pytest.mark.requires_capability("counts_usage")
async def test_c13_02_usage_counts_match_the_pre_registered_ground_truth(loaded, record_property):
    registry, result = loaded
    facts = result["facts"]

    for name, expected in PREREGISTERED.items():
        assert (await registry.usage(name)).count == expected, f"{name} instance count"

    # 4 of the 6 full-file correction statuses appear in this slice -- T1, [Observed].
    assert (await registry.usage("deficiency_corrected_status")).count == 4

    # The edges follow the grain of the two counts above.
    assert (await registry.usage("issued_during")).count == PREREGISTERED["citation"]
    assert (await registry.usage("conducted_at")).count == PREREGISTERED["survey"]

    # The one [Inferred] number in PACKAGE.md 8.2 is COMPUTED and REPORTED, never
    # asserted against the doc: it was quoted from run D, which is the run that got the
    # ordering backwards, and grading against an unverified quotation is the moved-target
    # failure the pre-registration exists to prevent.
    computed = facts["scope_severity_code"]
    record_property("scope_severity_code_distinct_computed", computed)
    record_property("scope_severity_codes_present", ",".join(facts["severity_codes_present"]))
    assert (await registry.usage("scope_severity_code")).count == computed
    print(
        f"\n[C13-02] scope_severity_code: {computed} distinct codes computed from the "
        f"sample: {', '.join(facts['severity_codes_present'])} "
        f"(PACKAGE.md 8.2 [Inferred] 7 from an unverified quotation of run D)"
    )

@pytest.mark.requires_capability("stores_attributes")
async def test_c13_03_deficiency_corrected_is_six_values_and_none_is_a_yes_no(loaded):
    """T1: the field reads as a boolean from its name and is not one."""
    registry, result = loaded
    entry = [
        t
        for t in (await registry.list_types(include_retired=True, status=None, namespace=None)).types
        if t.name == "deficiency_corrected_status"
    ][0]

    values = entry.attributes["values"]
    assert len(values) == 6

    booleans = {"yes", "no", "y", "n", "true", "false", "0", "1"}
    for value in values:
        assert value.strip().lower() not in booleans, f"{value!r} is a yes/no"

    present = result["facts"]["corrected_status_present"]
    assert len(present) == 4
    assert set(present) <= set(values), "the slice's values are a subset of the six"
    assert entry.kind == "value_set"

@pytest.mark.requires_capability("stores_attributes")
async def test_c13_04_the_severity_scale_carries_an_external_documentation_citation(loaded):
    """0.5 consequence 3: the inversion was caught by reading CMS documentation, not by
    inspecting data. A tool that never consults domain documentation reproduces that
    failure class for every user."""
    registry, _ = loaded
    entry = [
        t
        for t in (await registry.list_types(include_retired=True, status=None, namespace=None)).types
        if t.name == "scope_severity_code"
    ][0]

    assert entry.kind == "value_set"
    assert entry.attributes["ordered"] is True
    assert tuple(entry.attributes["ordering"]) == SEVERITY_ORDERING
    assert entry.attributes["ordering"][-3:] == ["J", "K", "L"], "Immediate Jeopardy is at the top"

    docs = [e for e in entry.provenance.evidence if e.kind == "external_doc"]
    assert docs, "an ordering asserted with no citation is 0.5's worst result"
    citation = docs[0].citation
    assert citation.url.startswith("https://")
    assert citation.title
    assert citation.retrieved_at is not None
    assert "unverified_semantics" not in entry.warnings

@pytest.mark.requires_capability("stores_attributes")
async def test_c13_05_value_set_is_accepted_and_survives_a_round_trip(registry, adapter):
    """`value_set` was added as a kind because the CMS data forced it -- the first
    recorded CMS-vs-Tenshen conflict, resolved in CMS's favour."""
    facts = sample_facts()
    proposal = await registry.propose_type(
        "scope_severity_code",
        "The CMS scope-and-severity grid, A through L, ordered least to most serious.",
        [],
        "user:sd",
        kind="value_set",
        attributes={"ordered": True, "ordering": list(SEVERITY_ORDERING)},
    )
    # A backend with stores_proposals=False auto-approves and hands back the entry
    # directly (PACKAGE.md 7.3 B4). What C13-05 is about is that `value_set` survives
    # a round trip, not which of the two shapes came back.
    if isinstance(proposal, Proposal):
        assert proposal.kind == "value_set"
        entry = await registry.approve(proposal.id, "user:sd")
    else:
        entry = proposal
    assert isinstance(entry, TypeEntry) and entry.kind == "value_set"

    stored = await adapter.get_type("default", "scope_severity_code", kind="value_set")
    assert stored.kind == "value_set"
    assert stored.attributes == {"ordered": True, "ordering": list(SEVERITY_ORDERING)}
    assert facts["scope_severity_code"] == len(
        [c for c in facts["severity_codes_present"] if c in SEVERITY_ORDERING]
    ), "every code present in the sample is inside the declared A-L set"
