# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c15_attributes.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C15 -- the ``attributes`` mechanism (6). PACKAGE.md 5.

The default is ``off`` so that an untouched deployment behaves exactly as
INTERFACE.md 2.1 describes. What happens unconditionally is the census, and ruling R2
keeps that package-local and outside the conformance definition.
"""

from __future__ import annotations
import pytest
from open_ontology.attributes import AttributeSchema, FieldSpec
from open_ontology.types import Refusal, TypeEntry
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import WithoutAttributeStore


SEVERITY_FIELDS = {
    "ordered": FieldSpec(
        type="bool",
        description="whether the values of this set have a meaningful order",
    ),
    "ordering": FieldSpec(
        type="list",
        item_type="str",
        required=True,
        description=(
            "the values least-serious first. Required because an ordering that is not "
            "written down is the CMS scope-and-severity scale living in somebody's "
            "transform, which is the field the cheapest tier read backwards."
        ),
    ),
}

def _schema(mode: str, version: int = 1, fields=None, additional: str = "allow"):
    return AttributeSchema(
        namespace="default",
        kind="value_set",
        version=version,
        fields=fields if fields is not None else dict(SEVERITY_FIELDS),
        additional=additional,
        mode=mode,
        registered_by="deployment",
    )

@pytest.mark.requires_capability("stores_attributes")
async def test_c15_01_with_no_schema_attributes_are_opaque_unread_and_unvalidated(registry):
    entry = await seed(
        registry,
        "scope_severity_code",
        kind="value_set",
        definition="the CMS scope and severity code",
        attributes={"anything": {"at": ["all"]}, "ordered": "not even a bool"},
    )
    assert isinstance(entry, TypeEntry)
    assert entry.attributes == {"anything": {"at": ["all"]}, "ordered": "not even a bool"}
    assert not any(w.startswith("attributes_invalid") for w in entry.warnings)
    assert entry.attr_schema_version is None, "written with validation off"

@pytest.mark.nonbinding
async def test_c15_02_the_census_records_every_key_written_in_off_mode(registry):
    """Ruling R2: package-local, outside the conformance definition. It does not solve
    the escape hatch; it makes the escape hatch enumerable."""
    await seed(
        registry,
        "scope_severity_code",
        kind="value_set",
        definition="the CMS scope and severity code",
        attributes={"ordered": True, "ordering": ["A", "B", "C"]},
    )
    await seed(
        registry,
        "deficiency_corrected_status",
        kind="value_set",
        definition="six status strings, none of them a yes/no",
        attributes={"ordered": False, "value_count": 6},
    )

    census = await registry.attribute_census()
    keys = {e.key: e for e in census.entries}
    assert set(keys) == {"ordered", "ordering", "value_count"}
    assert keys["ordered"].n == 2
    assert keys["value_count"].n == 1
    assert keys["ordered"].declared is False, "no schema is registered, so nothing is declared"
    assert keys["ordered"].schema_versions == (None,), (
        "the spread of attr_schema_version across rows carrying this key"
    )
    assert census.complete is True

@pytest.mark.requires_capability("stores_proposals")
@pytest.mark.requires_attribute_store
async def test_c15_03_warn_mode_warns_and_does_not_refuse(registry):
    await registry.register_attribute_schema(_schema("warn"))
    proposal = await registry.propose_type(
        "scope_severity_code",
        "the CMS scope and severity code",
        [],
        "user:sd",
        kind="value_set",
        attributes={"ordered": True},  # `ordering` is required and absent
    )
    assert not isinstance(proposal, Refusal), "warn mode never refuses"
    assert any(w.startswith("attributes_invalid:ordering") for w in proposal.warnings)

    entry = await registry.approve(proposal.id, "user:sd")
    assert isinstance(entry, TypeEntry)
    assert any(w.startswith("attributes_invalid:ordering") for w in entry.warnings), (
        "and the entry is thereafter enumerable"
    )

@pytest.mark.requires_attribute_store
async def test_c15_04_enforce_mode_refuses_with_the_offending_field(registry):
    await registry.register_attribute_schema(_schema("enforce"))
    refusal = await registry.propose_type(
        "scope_severity_code",
        "the CMS scope and severity code",
        [],
        "user:sd",
        kind="value_set",
        attributes={"ordered": True},
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "attributes_schema_violation"
    assert any(v.startswith("ordering:") for v in refusal.detail["violations"])
    assert refusal.detail["schema_version"] == 1

@pytest.mark.requires_capability("stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_05_a_new_required_field_does_not_invalidate_older_rows(registry):
    await registry.register_attribute_schema(
        _schema(
            "enforce",
            version=1,
            fields={
                "ordered": FieldSpec(type="bool", description="whether the values are ordered")
            },
        )
    )
    entry = await seed(
        registry,
        "deficiency_corrected_status",
        kind="value_set",
        definition="six status strings",
        attributes={"ordered": False},
    )
    assert entry.attr_schema_version == 1

    await registry.register_attribute_schema(_schema("enforce", version=2))

    # v1 rows are not rewritten and not retroactively invalidated. They are v1 rows.
    still = [
        t
        for t in (await registry.list_types(include_retired=True, status=None, namespace=None)).types
        if t.name == "deficiency_corrected_status"
    ][0]
    assert still.attributes == {"ordered": False}
    assert still.attr_schema_version == 1
    assert not any(w.startswith("attributes_invalid") for w in still.warnings)

    # But a new write is judged against v2.
    refusal = await registry.propose_type(
        "scope_severity_code",
        "the CMS scope and severity code",
        [],
        "user:sd",
        kind="value_set",
        attributes={"ordered": True},
    )
    assert isinstance(refusal, Refusal) and refusal.reason == "attributes_schema_violation"

@pytest.mark.requires_capability("stores_proposals", "stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_06_the_cms_severity_case_an_ordered_set_with_no_written_ordering(registry):
    """The reason the attribute-schema mechanism exists at all.

    v0 expresses "a value_set claiming an order must declare it" as a *required field*,
    not as a cross-field rule: FieldSpec is per-field on purpose, because a rule
    language here would be a schema language (PACKAGE.md 5.6).
    """
    await registry.register_attribute_schema(_schema("enforce"))

    refusal = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L, where J, K and L are Immediate Jeopardy.",
        [],
        "ai:proposer",
        kind="value_set",
        tier="opus",
        attributes={"ordered": True},
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "attributes_schema_violation"

    accepted = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L, where J, K and L are Immediate Jeopardy.",
        [],
        "ai:proposer",
        kind="value_set",
        tier="opus",
        attributes={
            "ordered": True,
            "ordering": list("ABCDEFGHIJKL"),
        },
    )
    assert not isinstance(accepted, Refusal)
    entry = await registry.approve(accepted.id, "user:sd")
    assert entry.attributes["ordering"][-3:] == ["J", "K", "L"]
    assert entry.attr_schema_version == 1

@pytest.mark.requires_attribute_store
async def test_c15_07_one_schema_per_kind_cannot_serve_two_value_sets_of_one_dataset(registry):
    """**The limitation in the mechanism's own flagship justification, pinned.**

    PACKAGE.md 5.1 justifies this whole section on the CMS scope-and-severity ordering:
    a ``value_set`` claiming an order must be made to declare it. But a schema is keyed
    ``(namespace, kind, version)`` -- **one schema per kind, not per type name** -- and
    the CMS file has *two* ``kind="value_set"`` entries with different shapes:
    ``scope_severity_code`` must be made to declare an ``ordering``, and
    ``deficiency_corrected_status`` (six status strings, no yes/no, no order) has none
    to declare.

    So a deployment gets one of two wrong answers and there is no third:

    * ``ordering`` required -> the unordered set is refused for lacking a field it has
      no business having;
    * ``ordering`` optional -> the ordered set can be created with no ordering, which
      is precisely the pollution 5.1 says the mechanism exists to prevent.

    This test asserts that both horns are real. It is **not** a bug report against a
    backend: every backend behaves this way because the key is in the schema, not in
    the storage. Recorded in PACKAGE.md 5.6 and 11.3; a ruling on whether to key
    schemas per ``(namespace, kind, name)`` is wanted. Added by row 3c after an
    adversarial review round; see docs/findings/3C-VALIDATION.md.
    """
    unordered = {
        "values": ["Deficient, Provider Has Date Of Correction", "Deficient, No Plan Of Correction"],
    }

    # Horn 1 -- `ordering` required. The set that has no order is refused.
    await registry.register_attribute_schema(_schema("enforce"))
    refused = await registry.propose_type(
        "deficiency_corrected_status",
        "The six status strings CMS uses for whether a deficiency was corrected.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": False, **unordered},
    )
    assert isinstance(refused, Refusal), "an unordered value_set refused for lacking an order"
    assert refused.reason == "attributes_schema_violation"
    assert "ordering" in str(refused.detail)

    # Horn 2 -- `ordering` optional. The set that HAS an order may now omit it, and
    # the mechanism's whole reason for existing is gone.
    relaxed = dict(SEVERITY_FIELDS)
    relaxed["ordering"] = FieldSpec(
        type="list", item_type="str", required=False,
        description=relaxed["ordering"].description,
    )
    await registry.register_attribute_schema(_schema("enforce", version=2, fields=relaxed))

    now_allowed = await registry.propose_type(
        "deficiency_corrected_status",
        "The six status strings CMS uses for whether a deficiency was corrected.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": False, **unordered},
    )
    assert not isinstance(now_allowed, Refusal), "horn 2 lets the unordered set through"

    undeclared = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L, where J, K and L are Immediate Jeopardy.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": True},          # claims an order, declares none
    )
    assert not isinstance(undeclared, Refusal), (
        "and it lets the ORDERED set through with no ordering -- which is the CMS "
        "severity scale back inside somebody's transform, unversioned. One schema per "
        "kind cannot hold both CMS value_sets correctly"
    )

@pytest.mark.requires_capability("stores_attributes")
async def test_c15_08_declining_the_attribute_store_leaves_a_backend_conformant(
    adapter, make_registry
):
    """**§5.5 and `2A-RUN.md` D-2 both say so; until row 3c it was false.**

    `AsyncAttributeStore` is optional -- outside the fifteen primitives and outside
    conformance (ruling R2). A backend that does not implement it is *"still fully
    conformant"*, and `attribute_census` *"then reports `complete=False` with a `why`
    rather than an empty census"*. **[Observed] a real backend that declined it crashed
    five C15 tests with `NotSupported`**, because they called
    `register_attribute_schema` with no guard -- and the defect had gone unnoticed
    because `AsyncDegradedAdapter` unconditionally re-declared the four extension methods, so
    the tool built to construct degraded backends could not construct **the one optional
    capability that is a protocol rather than a `Capabilities` flag**.

    Added by an adversarial review round; see docs/findings/3C-VALIDATION.md.
    """
    declining = await make_registry(WithoutAttributeStore(adapter))

    census = await declining.attribute_census()
    assert census.entries == (), "nothing is recorded, because nothing can be"
    assert census.known is None, "None, not 0 -- 0 would claim we counted and found none"
    assert census.complete is False
    assert census.why_incomplete, "and it says why, in the backend's own words"

    # The vocabulary itself is untouched: attributes still round-trip, they are simply
    # never validated and never censused. That is INTERFACE.md 2.1's default behaviour.
    entry = await seed(
        declining,
        "scope_severity_code",
        kind="value_set",
        attributes={"ordered": True, "ordering": list("ABC")},
    )
    assert entry.attributes == {"ordered": True, "ordering": list("ABC")}
