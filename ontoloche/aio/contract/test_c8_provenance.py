# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c8_provenance.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C8 -- ``provenance`` (6). Mechanisms 1 and 3.

Who added this, when, on what evidence, and did anybody actually approve it.
"""

from __future__ import annotations
import pytest
from datetime import UTC, datetime, timedelta
from ontoloche.types import Citation, Evidence, TypeEntry
from ontoloche.aio.contract._support import DOC_EVIDENCE_URL, seed


@pytest.mark.requires_capability("stores_proposals")
async def test_c8_01_missing_evidence_is_empty_never_a_reconstructed_narrative(registry):
    proposal = await registry.propose_type("facility", "a nursing home", [], "user:pm")
    await registry.approve(proposal.id, "user:sd")

    provenance = await registry.provenance("facility")
    assert provenance.evidence == ()
    assert provenance.proposed_by == "user:pm"
    assert provenance.approved_by == "user:sd"

@pytest.mark.requires_capability("stores_proposals", "stores_events", "indexes_membership")
async def test_c8_02_history_is_append_only(registry, clock):
    proposal = await registry.propose_type("watch", "a thing a user watches", [], "user:pm")
    await registry.approve(proposal.id, "user:sd")
    before = list((await registry.provenance("watch")).history)
    assert [e.event for e in before] == ["proposed", "approved"]

    clock.advance(timedelta(minutes=5))
    # `capture` is seeded because `retire` now refuses a successor that names no entry
    # (`successor_unregistered`, row 4d round 1). The successor is scaffolding here; the
    # subject is that history is append-only.
    await seed(registry, "capture", definition="the word that replaced it")
    await registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    after = list((await registry.provenance("watch")).history)
    assert [e.event for e in after] == ["proposed", "approved", "retired"]
    assert after[: len(before)] == before, (
        "a correction is a new event, never an edit -- no prior event's bytes changed"
    )

async def test_c8_03_an_auto_approved_entry_says_auto(adapter, make_registry):
    registry = await make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")
    await registry.propose_type("blocks", "this blocks that", [], "ai:classifier", tier="opus")

    provenance = await registry.provenance("blocks")
    assert provenance.approved_by == "auto:classifier"
    assert provenance.approved_by.startswith("auto:")

async def test_c8_04_an_imported_row_says_unknown_imported_never_null(registry):
    await registry.import_types(
        [{"name": "flight", "status": "active", "apiName": "Flight", "rid": "ri.o.1"}]
    )
    provenance = await registry.provenance("flight")
    assert provenance.approved_by == "unknown:imported"
    assert provenance.imported_from == {
        "system": "foundry",
        "apiName": "Flight",
        "rid": "ri.o.1",
    }

@pytest.mark.requires_capability("stores_proposals")
async def test_c8_05_model_tier_is_never_overwritten(registry, clock):
    proposal = await registry.propose_type(
        "scope_severity_code",
        "an ordered severity scale",
        [
            Evidence(
                kind="external_doc",
                summary="CMS scope-and-severity grid runs A to L",
                citation=Citation(
                    url=DOC_EVIDENCE_URL,
                    title="CMS QSO-23-01",
                    retrieved_at=datetime(2026, 8, 28, tzinfo=UTC),
                ),
            )
        ],
        "ai:proposer",
        kind="value_set",
        tier="haiku",
    )
    await registry.approve(
        proposal.id,
        "user:sd",
        definition="an ordered severity scale A-L; J, K and L are Immediate Jeopardy",
        note="corrected the wording",
    )
    assert (await registry.provenance("scope_severity_code")).model_tier == "haiku", (
        "the tier that produced the proposal, not the tier of whoever touched it last -- "
        "this is what answers 'which types were proposed by a cheap model?'"
    )

    clock.advance(timedelta(days=1))
    await registry.retire("scope_severity_code", "replaced", retired_by="user:sd")
    assert (await registry.provenance("scope_severity_code")).model_tier == "haiku"

async def test_c8_06_source_version_is_the_sources_version_and_round_trips(registry):
    """**Ruling R21, row 3e -- INTERFACE.md 10b.5, contortion 12.**

    Every other field of `Provenance` is a fact about **us**: when we created the entry,
    who proposed it, when we approved it, when we fetched a citation. `source_version`
    is the one field that is a fact about the thing the entry was **derived from**, and
    UC3 is why it has to exist: a type proposed from a 2017-10-04 snapshot of a
    "Historical data" dataset is a different claim from one proposed off a feed updated
    yesterday, and none of the ten fields had a home for that. `Citation.retrieved_at`
    is when *we* fetched; `imported_from` is foreign SYSTEM identifiers.

    What forced it now was not that finding alone -- it was collected for v1 with the
    rest -- but that EDGES.md gave `EdgeProvenance` the field first, leaving **two
    shapes for one concept with one of them missing it**, which is the drift
    `check_spec_drift.py` exists to catch, pointing inward.

    Asserted: supplied once by the proposer, readable on the `Proposal` before anything
    is approved, present on the `Provenance` after, and **`None` when nobody supplied
    one** -- never invented and never quietly filled in with our own timestamp.
    """
    supplied = await registry.propose_type(
        "tree_census_record",
        "one row of the street tree census.",
        [],
        "derived:socrata_export",
        source_version="2017-10-04",
    )
    if isinstance(supplied, TypeEntry):        # stores_proposals=False (PACKAGE 7.3 B4)
        entry = supplied
    else:
        assert supplied.source_version == "2017-10-04", (
            "readable before approval -- a value accepted and invisible until approval "
            "is a value the proposer cannot check"
        )
        entry = await registry.approve(supplied.id, "user:sd")
        assert isinstance(entry, TypeEntry)

    assert entry.provenance.source_version == "2017-10-04"
    assert (await registry.provenance("tree_census_record")).source_version == "2017-10-04"

    # ...and it is never invented.
    plain = await seed(registry, "service_request", definition="one 311 service request")
    assert plain.provenance.source_version is None, (
        "Rule U: no source version was supplied, so there is none -- not our own "
        "created_at wearing the source's name"
    )
    assert plain.provenance.created_at is not None, "which is OUR fact, and is set"
