# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/_support.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""Shared helpers for the suite. Not part of the package's public surface.

The suite may not import anything private from the package under test (PACKAGE.md 2.2),
so everything here is built out of the public protocol and the public shapes.
"""

from __future__ import annotations
import hashlib
from typing import Any, Callable, Sequence
from open_ontology.aio.adapter import ProposalQuery, TypeQuery
from open_ontology.types import Evidence, TypeEntry
import csv
from datetime import UTC, datetime
from pathlib import Path
from open_ontology.types import Citation, Evidence


EXTERNAL_FACTORY: Callable[[], Any] | None = None

EXTERNAL_RESOLVER: Callable[[], Any] | None = None

FIXTURE_NAME = "cms_sample_400.csv"

async def snapshot(adapter) -> str:
    """A digest of everything the store holds, read through the public primitives only.

    "Byte-identical" is not portable across two backends whose on-disk formats differ by
    design, so the suite compares what the protocol can see. That is the stronger test
    anyway: it catches a write that landed, not merely a file that changed size.
    """
    caps = await adapter.capabilities()
    parts: list[str] = []
    page = await adapter.find_types(TypeQuery(include_retired=True))
    for rec in page.records:
        parts.append(repr(rec))
    if caps.stores_proposals:
        for rec in (await adapter.find_proposals(ProposalQuery())).records:
            parts.append(repr(rec))
    namespaces = sorted({r.namespace for r in page.records} | {"default"})
    for namespace in namespaces:
        for consumer in await adapter.find_consumers(namespace):
            parts.append(repr(consumer))
        if caps.stores_events:
            for event in await adapter.read_events(namespace):
                parts.append(repr(event))
        for rec in page.records:
            if rec.namespace == namespace:
                parts.append(repr(await adapter.get_usage(namespace, rec.kind, rec.name)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()

async def seed(
    registry,
    name: str,
    *,
    kind: str = "entity",
    definition: str | None = None,
    predicates: Sequence[str] = (),
    attributes: dict | None = None,
    evidence: Sequence[Evidence] = (),
    proposed_by: str = "user:sd",
    tier: str | None = None,
    approved_by: str = "user:sd",
    namespace: str = "default",
) -> TypeEntry:
    """propose + approve, for tests whose subject is something else."""
    proposal = await registry.propose_type(
        name,
        definition or f"a {name}, for the purposes of this test",
        list(evidence),
        proposed_by,
        kind=kind,
        namespace=namespace,
        predicates=list(predicates),
        attributes=attributes,
        tier=tier,
    )
    if isinstance(proposal, TypeEntry):
        return proposal
    entry = await registry.approve(proposal.id, approved_by)
    assert isinstance(entry, TypeEntry), entry
    return entry

DOC_EVIDENCE_URL = "https://www.cms.gov/files/document/qso-23-01-nh-revised-2026-01-28.pdf"

csv.field_size_limit(10_000_000)

FIXTURE = Path(__file__).resolve().parents[2] / "contract" / "fixtures" / FIXTURE_NAME

CMS_DATASET_URL = "https://data.cms.gov/provider-data/dataset/r5ix-sfxw"

CMS_QSO_URL = "https://www.cms.gov/files/document/qso-23-01-nh-revised-2026-01-28.pdf"

RETRIEVED = datetime(2026, 8, 28, tzinfo=UTC)

CORRECTED_STATUS_VALUES_FULL_FILE = (
    "Deficient, Provider has date of correction",
    "Past Non-Compliance",
    "Deficient, Provider has plan of correction",
    "Deficient, Provider has no plan of correction",
    "Waiver has been granted",
    "No revisit needed",
)

SEVERITY_ORDERING = tuple("ABCDEFGHIJKL")

def read_sample(path: Path = FIXTURE) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        return header, list(reader)

def sample_facts(path: Path = FIXTURE) -> dict:
    """Everything the C13 assertions are made against, computed from the CSV.

    The four [Observed] counts in PACKAGE.md 8.2 are pre-registered and asserted; the
    severity-code count is [Inferred] there, quoted from the run that got the ordering
    backwards, so it is **computed here and reported** rather than asserted against a
    number taken from an unverified quotation.
    """
    header, rows = read_sample(path)
    at = {name: i for i, name in enumerate(header)}
    ccn = at["CMS Certification Number (CCN)"]

    facilities = {r[ccn] for r in rows}
    surveys = {(r[ccn], r[at["Survey Date"]], r[at["Survey Type"]]) for r in rows}
    tags = {r[at["Deficiency Tag Number"]] for r in rows}
    statuses = {r[at["Deficiency Corrected"]] for r in rows}
    severities = {r[at["Scope Severity Code"]] for r in rows}

    descriptions: dict[str, set[str]] = {}
    for row in rows:
        descriptions.setdefault(row[at["Deficiency Tag Number"]], set()).add(
            row[at["Deficiency Description"]]
        )

    location_rebuilt = sum(
        1
        for r in rows
        if r[at["Location"]].strip()
        == ",".join(
            (r[at["Provider Address"]], r[at["City/Town"]], r[at["State"]], r[at["ZIP Code"]])
        )
    )
    processing_dates = {r[at["Processing Date"]] for r in rows}

    return {
        "rows": len(rows),
        "facility": len(facilities),
        "survey": len(surveys),
        "citation": len(rows),
        "deficiency_tag": len(tags),
        "deficiency_corrected_status": len(statuses),
        "scope_severity_code": len(severities),
        "severity_codes_present": sorted(severities),
        "corrected_status_present": sorted(statuses),
        "tags_with_more_than_one_description": sum(
            1 for v in descriptions.values() if len(v) > 1
        ),
        "location_exactly_rebuilt": location_rebuilt,
        "processing_date_distinct": len(processing_dates),
    }

def _data(summary: str) -> Evidence:
    return Evidence(kind="data", summary=summary, locator=FIXTURE_NAME)

def _cms_doc(summary: str, *, url: str = CMS_DATASET_URL, title: str, quote: str | None = None):
    return Evidence(
        kind="external_doc",
        summary=summary,
        citation=Citation(url=url, title=title, retrieved_at=RETRIEVED, quote=quote),
    )

def cms_vocabulary(facts: dict) -> list[dict]:
    """The eight entries the sample's vocabulary comes to.

    **The registry stores types, not instances.** The 400 sample rows do not become 400
    rows in the type store; what lands is this vocabulary plus the instance counts in
    usage. Reading "the sample loads" as "400 citations become types" is the T3/T6
    failure the ground truth predicted, committed by the harness instead of by a model.
    """
    return [
        {
            "name": "facility",
            "kind": "entity",
            "definition": (
                "A Medicare/Medicaid-certified nursing home, identified by its CMS "
                "Certification Number (CCN). Provider Name is a label, not an identifier: "
                "104 distinct names are shared by more than one CCN in the August 2026 file."
            ),
            "attributes": {"primary_key": ["ccn"]},
            "uses": facts["facility"],
            "evidence": [
                _data(
                    f"{facts['facility']} distinct CCNs across {facts['rows']} sampled rows; "
                    "CCN->name is 1:1 full-file"
                ),
                _cms_doc(
                    "CMS describes the row subject as the nursing home that received the citation.",
                    title="Health Deficiencies -- CMS Provider Data Catalog",
                    quote="including the nursing home that received the citation",
                ),
            ],
        },
        {
            "name": "survey",
            "kind": "entity",
            "definition": (
                "One inspection visit to a facility, keyed by (CCN, Survey Date, Survey "
                "Type). Several citations are issued during one survey."
            ),
            "attributes": {"primary_key": ["ccn", "survey_date", "survey_type"]},
            "uses": facts["survey"],
            "evidence": [
                _data(f"{facts['survey']} distinct (CCN, Survey Date, Survey Type) triples"),
                _cms_doc(
                    "CMS names the inspection date as a distinct level of the data.",
                    title="Health Deficiencies -- CMS Provider Data Catalog",
                    quote="the associated inspection date",
                ),
            ],
        },
        {
            "name": "citation",
            "kind": "entity",
            "definition": (
                "One deficiency cited against a facility during a survey. The file's grain: "
                "one citation per row."
            ),
            "attributes": {"grain": "one per row"},
            "uses": facts["citation"],
            "evidence": [
                _data(f"{facts['rows']} rows, one citation each"),
                _cms_doc(
                    "CMS states the grain explicitly.",
                    title="Health Deficiencies -- CMS Provider Data Catalog",
                    quote="Data are presented as one citation per row.",
                ),
            ],
        },
        {
            "name": "deficiency_tag",
            "kind": "entity",
            "definition": (
                "A regulatory tag (an F-tag) a citation is written under. Deficiency "
                "Description is a lookup on the tag, not per-citation free text: no tag in "
                "the sample carries more than one description."
            ),
            "attributes": {"primary_key": ["tag_number"]},
            "uses": facts["deficiency_tag"],
            "evidence": [
                _data(
                    f"{facts['deficiency_tag']} distinct tags in the sample, "
                    f"{facts['tags_with_more_than_one_description']} with more than one "
                    "description"
                )
            ],
        },
        {
            "name": "deficiency_corrected_status",
            "kind": "value_set",
            "definition": (
                "The status of a citation's correction. Reads as a boolean from its name "
                "and is not one: six status strings full-file, none of them a yes or a no."
            ),
            "attributes": {
                "values": list(CORRECTED_STATUS_VALUES_FULL_FILE),
                "ordered": False,
                "present_in_sample": facts["corrected_status_present"],
            },
            "uses": facts["deficiency_corrected_status"],
            "evidence": [
                _data(
                    f"{facts['deficiency_corrected_status']} distinct values in the sample; "
                    "six full-file, none a yes/no"
                ),
                _cms_doc(
                    "CMS describes the field as the current status of the citation.",
                    title="Health Deficiencies -- CMS Provider Data Catalog",
                    quote="the current status of the citation and the correction date",
                ),
            ],
        },
        {
            "name": "scope_severity_code",
            "kind": "value_set",
            "definition": (
                "The CMS scope-and-severity grid, A through L. It is ORDERED and the order "
                "runs least serious to most serious: J, K and L are Immediate Jeopardy."
            ),
            "attributes": {
                "ordered": True,
                "ordering": list(SEVERITY_ORDERING),
                "present_in_sample": facts["severity_codes_present"],
            },
            "uses": facts["scope_severity_code"],
            "evidence": [
                _data(
                    f"{facts['scope_severity_code']} distinct codes present in the sample: "
                    + ", ".join(facts["severity_codes_present"])
                ),
                _cms_doc(
                    "The CMS scope-and-severity grid runs A (least serious) to L (most "
                    "serious); J, K and L constitute Immediate Jeopardy.",
                    url=CMS_QSO_URL,
                    title="CMS QSO-23-01, revised 2026-01-28",
                    quote="Substandard quality of care and immediate jeopardy: J, K, L",
                ),
            ],
        },
        {
            "name": "issued_during",
            "kind": "edge",
            "definition": "A citation was issued during a survey.",
            "attributes": {"from": "citation", "to": "survey"},
            "uses": facts["citation"],
            "evidence": [_data(f"{facts['citation']} citations, each on exactly one survey")],
        },
        {
            "name": "conducted_at",
            "kind": "edge",
            "definition": "A survey was conducted at a facility.",
            "attributes": {"from": "survey", "to": "facility"},
            "uses": facts["survey"],
            "evidence": [_data(f"{facts['survey']} surveys, each at exactly one facility")],
        },
    ]

async def load_cms_sample(registry, path: Path = FIXTURE) -> dict:
    """Load the sample's vocabulary through the adapter and record its instance counts.

    ``propose_type`` returns a ``TypeEntry`` rather than a ``Proposal`` on a backend
    with ``stores_proposals=False`` -- PACKAGE.md 7.3 B4, which is the Tenshen adapter
    the document's own design test calls conformant. This harness assumed a ``Proposal``
    and crashed with ``AttributeError: 'TypeEntry' object has no attribute 'id'``, so
    **the mandatory C13 group failed a backend §7.4 says conforms** -- the exact
    "legitimate backend fails for a non-storage reason" class §6.1 exists to prevent.
    Corrected by row 3c after an adversarial review round; ``seed()`` above always had
    it right.
    """
    facts = sample_facts(path)
    entries = []
    for spec in cms_vocabulary(facts):
        proposal = await registry.propose_type(
            spec["name"],
            spec["definition"],
            spec["evidence"],
            "ai:proposer",
            kind=spec["kind"],
            attributes=spec["attributes"],
            tier="opus",
        )
        # B4: no proposal table means propose_type IS the decision.
        entry = (
            proposal
            if isinstance(proposal, TypeEntry)
            else await registry.approve(proposal.id, "user:sd")
        )
        for _ in range(spec["uses"]):
            await registry.record_use(spec["name"], by="cms_sample_loader")
        entries.append(entry)
    return {"facts": facts, "entries": entries}
