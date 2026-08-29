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
