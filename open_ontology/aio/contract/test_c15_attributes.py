# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c15_attributes.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C15 -- the ``attributes`` mechanism (13). PACKAGE.md 5.

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

def _schema(
    mode: str,
    version: int = 1,
    fields=None,
    additional: str = "allow",
    name: str | None = None,
):
    return AttributeSchema(
        namespace="default",
        kind="value_set",
        version=version,
        fields=fields if fields is not None else dict(SEVERITY_FIELDS),
        additional=additional,
        mode=mode,
        registered_by="deployment",
        name=name,
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
@pytest.mark.requires_capability("stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_02_the_census_records_every_key_written_in_off_mode(registry):
    """Ruling R2: package-local, outside the conformance definition. It does not solve
    the escape hatch; it makes the escape hatch enumerable.

    The two markers were added by row 3d, when the natively-degraded third leg ran this
    for the first time. Its subject is a census of **arbitrary** keys, which needs
    ``stores_attributes`` as scaffolding: on a backend that stores none, the only keys
    ever written are its projections (PACKAGE.md 5.7), and the honest census there is
    *those keys, `complete=False`, with a why*. That behaviour has its own subject,
    ``C15-09``; asserting it here would make one test mean two things.
    """
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

@pytest.mark.nonbinding
@pytest.mark.requires_attribute_store
async def test_c15_09_a_projected_key_is_censused_and_the_census_says_it_is_partial(
    adapter, make_registry
):
    """**Beacon finding U3's census consequence, and it is a Rule U question.**

    PACKAGE.md 5.7: a backend with `stores_attributes=False` may still own some keys as
    typed columns, and those keys **are written**. `attribute_census` used to refuse
    outright on `stores_attributes=False` and return `entries=()` -- which on such a
    backend is a *confident wrong answer*: it says nothing was ever written when
    something was, in the one call whose whole job is making the escape hatch
    enumerable (§5.5).

    The honest answer is both halves at once: the projected keys **are** listed, and
    `complete` is `False` with a `why_incomplete` naming which keys the count covers.
    Same move as `ConsumerReport.complete=False`.
    """
    caps = await adapter.capabilities()
    if caps.stores_attributes:
        pytest.skip(
            "PACKAGE.md 5.7 -- this backend stores arbitrary attributes, so a census "
            "restricted to its projections has no subject here. C15-02 is the full case."
        )
    if not caps.attribute_projections:
        pytest.skip(
            "PACKAGE.md 5.7 -- this backend declines attributes AND declares no "
            "projected columns, so there is no key it stores. C15-08 is that case."
        )
    projected = sorted(caps.attribute_projections)[0]
    registry = await make_registry(adapter)

    await seed(
        registry,
        "scope_severity_code",
        kind="value_set",
        definition="the CMS scope and severity code",
        attributes={projected: ["ccn"], "ordering": ["A", "B", "C"]},
    )

    census = await registry.attribute_census()
    keys = {e.key: e for e in census.entries}
    assert projected in keys, (
        "the projected key WAS written, to a column this backend owns -- a census that "
        "omits it reports an unknown where the backend has a fact"
    )
    assert "ordering" not in keys, "and a key it never stored is not invented into one"
    assert census.complete is False, "the census covers the projections and nothing else"
    assert census.why_incomplete and projected in census.why_incomplete, (
        "and it names which keys it counted, in the backend's own words plus the list"
    )

@pytest.mark.requires_capability("stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_10_a_name_level_schema_shadows_the_per_kind_one(registry):
    """**Ruling R10, row 3e -- `C15-07`'s two horns, both gone, on CMS's own data.**

    `C15-07` pinned the limitation in this mechanism's flagship justification: a schema
    keyed `(namespace, kind, version)` is **one schema per kind**, and CMS has two
    `kind="value_set"` entries with different shapes. Requiring `ordering` refuses
    `deficiency_corrected_status` for lacking an order it has no business having;
    making `ordering` optional lets `scope_severity_code` be created claiming an order
    and declaring none -- the CMS severity scale back inside somebody's transform,
    unversioned, which is the pollution PACKAGE.md 5.1 justifies the whole mechanism on.

    R10 adds the third option `C15-07` said did not exist: `(namespace, kind, name)`
    schemas that **shadow** the per-kind one. This test drives both CMS value sets
    through it and asserts the shadowing is a replacement, not a merge -- a merge of two
    field maps produces a third schema nobody wrote and nobody versioned.
    """
    unordered = {"values": ["Past Non-Compliance", "No revisit needed"]}

    # The per-kind schema is the strict one: a value_set must declare its ordering.
    await registry.register_attribute_schema(_schema("enforce"))

    # The ordered set obeys it. This is 5.1's whole argument, and it still works.
    ordered_ok = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L, where J, K and L are Immediate Jeopardy.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": True, "ordering": list("ABCDEFGHIJKL")},
    )
    assert not isinstance(ordered_ok, Refusal)

    # ...and the unordered one is still refused BY THE PER-KIND SCHEMA -- horn 1, which
    # is the state of the world this ruling starts from.
    refused = await registry.propose_type(
        "deficiency_corrected_status",
        "The six status strings CMS uses for whether a deficiency was corrected.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": False, **unordered},
    )
    assert isinstance(refused, Refusal) and refused.reason == "attributes_schema_violation"
    assert refused.detail["schema_name"] is None, "the PER-KIND schema refused it"

    # R10: one schema for that one name. `ordering` is not in it at all, so it cannot
    # be required and cannot be silently accepted-as-absent by the other schema either.
    await registry.register_attribute_schema(
        _schema(
            "enforce",
            name="deficiency_corrected_status",
            fields={
                "ordered": FieldSpec(
                    type="bool",
                    description="whether the values of this set have a meaningful order",
                ),
                "values": FieldSpec(
                    type="list", item_type="str", required=True,
                    description="the status strings, which have no order to declare",
                ),
            },
        )
    )

    now_fine = await registry.propose_type(
        "deficiency_corrected_status",
        "The six status strings CMS uses for whether a deficiency was corrected.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": False, **unordered},
    )
    assert not isinstance(now_fine, Refusal), (
        "the name-level schema shadows the per-kind one: the unordered set is judged "
        "by its own schema, which never asked for an ordering"
    )

    # Shadowing, not merging: the per-kind schema's REQUIRED `ordering` field does not
    # come along. If it merged, the write above would still be refused.
    entry = (
        now_fine
        if isinstance(now_fine, TypeEntry)
        else await registry.approve(now_fine.id, "user:sd")
    )
    assert entry.attributes["ordered"] is False
    assert "ordering" not in entry.attributes

    # And the name-level schema is strict about its OWN fields -- it is a schema, not
    # an exemption. `values` is required there.
    missing = await registry.propose_type(
        "deficiency_corrected_status_v2",
        "A second unordered status set, to prove the override is not an escape hatch.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": False},
    )
    assert isinstance(missing, Refusal), "the per-kind schema still governs every other name"
    assert missing.detail["schema_name"] is None

@pytest.mark.requires_capability("stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_11_the_per_kind_schema_still_governs_every_name_without_an_override(registry):
    """**R10's other half: an override overrides ONE name, and nothing else.**

    The failure mode a name-level key invites is that registering one override quietly
    relaxes the kind -- a deployment writes one exception and stops noticing that the
    general rule is still the general rule. Asserted here on a third `value_set` that
    has no override of its own: it is judged by the per-kind schema exactly as before
    R10, and the refusal names which schema refused it so the two can be told apart.
    """
    await registry.register_attribute_schema(_schema("enforce"))
    await registry.register_attribute_schema(
        _schema(
            "enforce",
            name="deficiency_corrected_status",
            fields={
                "values": FieldSpec(
                    type="list", item_type="str", required=True,
                    description="the status strings, which have no order to declare",
                )
            },
        )
    )

    third = await registry.propose_type(
        "survey_type_code",
        "The kind of survey a citation was written during.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"ordered": False},          # no `ordering`, and no override for it
    )
    assert isinstance(third, Refusal), "a name with no override falls back to the kind"
    assert third.reason == "attributes_schema_violation"
    assert third.detail["schema_name"] is None
    assert "ordering" in str(third.detail)

@pytest.mark.requires_capability("stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_12_an_override_may_not_weaken_the_kind_and_the_census_says_so(registry):
    """**Both halves of R10 that the first cut got wrong.** Row 3e, first adversarial
    round, both reproduced on the CMS fixture this mechanism is justified on.

    *Half one -- the enforcement floor.* PACKAGE.md 5.2b rule 3 says *"an override is a
    schema, not an exemption"*. The first cut shadowed `mode` and `additional` along
    with `fields`, so a name-level schema with `fields={}`, `additional="allow"`,
    `mode="off"` turned a strictly enforced kind **completely off for one name**, with
    no warning and nothing in the census to show it. In UC3 that is one agency's
    one-line, unreviewed opt-out of a rule dozens publish under. The fields are replaced;
    the strictness is a **floor**, applied at validation time rather than at
    registration -- a floor enforced when a schema is registered is bypassed by
    registering the weak override first, and a rule whose ordering you can pick is not a
    rule.

    *Half two -- `declared` is tri-state.* A census row is `(kind, key)` over every type
    of that kind, so after R10 a key can be declared by a name-level schema for one name
    and by nothing for the rest. `True` would claim it for types the override never
    covered; `False` is a confident negative about a key that is **required** somewhere
    -- Rule U, on the call whose whole job is making the escape hatch enumerable. So the
    third state exists and `declared_why` names the schemas it depends on.
    """
    strict = AttributeSchema(
        namespace="default", kind="value_set", version=1, mode="enforce",
        additional="forbid", registered_by="deployment",
        fields={
            "ordered": FieldSpec(type="bool", description="whether the set has an order"),
            "ordering": FieldSpec(
                type="list", item_type="str", required=True,
                description="the values least-serious first",
            ),
        },
    )
    await registry.register_attribute_schema(strict)

    # An override that tries to switch the kind's governance off for one name.
    await registry.register_attribute_schema(
        AttributeSchema(
            namespace="default", kind="value_set", version=1, mode="off",
            additional="allow", fields={}, registered_by="deployment",
            name="deficiency_corrected_status",
        )
    )
    escaped = await registry.propose_type(
        "deficiency_corrected_status",
        "The six status strings CMS uses for whether a deficiency was corrected.",
        [], "ai:proposer", kind="value_set", tier="opus",
        attributes={"an_entire_nested_world": {"a": {"b": 2}}, "junk": 1},
    )
    assert isinstance(escaped, Refusal), (
        "an override replaces the FIELDS and may not weaken the STRICTNESS"
    )
    assert escaped.reason == "attributes_schema_violation"
    assert escaped.detail["schema_name"] == "deficiency_corrected_status"

    # A real override -- its own fields, and the kind's strictness -- works.
    await registry.register_attribute_schema(
        AttributeSchema(
            namespace="default", kind="value_set", version=2, mode="enforce",
            additional="forbid", registered_by="deployment",
            name="deficiency_corrected_status",
            fields={
                "ordered": FieldSpec(type="bool", description="whether it has an order"),
                "values": FieldSpec(
                    type="list", item_type="str", required=True,
                    description="the status strings, which have no order to declare",
                ),
            },
        )
    )
    ok = await seed(
        registry, "deficiency_corrected_status", kind="value_set",
        definition="The six status strings CMS uses.",
        attributes={"ordered": False, "values": ["Past Non-Compliance", "No revisit needed"]},
    )
    assert ok.status == "active"
    await seed(
        registry, "scope_severity_code", kind="value_set",
        definition="Ordered severity scale A-L, where J, K and L are Immediate Jeopardy.",
        attributes={"ordered": True, "ordering": list("ABCDEFGHIJKL")},
    )

    census = {e.key: e for e in (await registry.attribute_census()).entries}
    assert census["ordered"].declared is True, (
        "both schemas declare it, so it is declared for every name of this kind"
    )
    assert census["values"].declared is None, (
        "Rule U: declared for one name of this kind and for no other, so the answer "
        "depends on which type -- neither True nor False is honest"
    )
    assert "deficiency_corrected_status" in (census["values"].declared_why or "")

    # **And the same in the other direction**, which the first cut got wrong: the
    # per-kind schema declares `ordering` and the override REMOVES it (shadowing is
    # replacement, §5.2b rule 1). A flat `True` there is the same confident positive
    # the tri-state exists to prevent -- and [Observed, row 3e second adversarial
    # round] the registry refused a write of `ordering` on the overridden name with
    # "not declared in the schema" while the census said it was declared for all.
    assert census["ordering"].declared is None
    assert "deficiency_corrected_status" in (census["ordering"].declared_why or "")

    # §5.2b's sentinel guard, which had no test: the empty string is the STORE's way of
    # saying "per-kind", so a caller passing it would silently replace the schema for
    # the whole kind.
    with pytest.raises(ValueError):
        AttributeSchema(namespace="default", kind="value_set", version=1, fields={}, name="")

@pytest.mark.nonbinding
@pytest.mark.requires_capability("stores_attributes")
@pytest.mark.requires_attribute_store
async def test_c15_13_a_plain_string_attribute_survives_the_census_on_every_leg(registry):
    """The most ordinary attribute value there is, through the audit call. Row 4c.

    **[Observed, on `main` before row 4c]** one type written with
    ``attributes={"note": "a plain string"}`` made ``attribute_census()`` raise
    ``json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`` on the
    **Postgres leg and only there** -- the reference *deployment* backend. Every
    ``*_json`` column in that schema is ``jsonb``, so psycopg decodes it before the
    dialect sees it, and the dialect re-parsed anything arriving as a ``str``: which is
    exactly a jsonb column holding a JSON string.

    Nothing caught it for three rows. No test wrote a string-valued attribute and then
    censused it; the census is nonbinding under ruling **R2**, so it is outside the
    conformance verdict and had no cross-leg assertion of its own; and the sqlite legs
    store text and parse it correctly, so the two-leg agreement everything else relies
    on had one leg that never disagreed. It was found by wiring ruling R34's
    edge-payload census onto the same call.

    This is the assertion that would have caught it: a string, an int, a list and a
    dict, written as attributes and read back through the census, on every leg.
    """
    await seed(
        registry,
        "thing",
        attributes={
            "note": "a plain string",
            "count": 3,
            "tags": ["a", "b"],
            "nested": {"k": "v"},
        },
    )
    census = await registry.attribute_census()
    examples = {entry.key: entry.example for entry in census.entries}
    assert examples["note"] == "a plain string", (
        "a jsonb column holding a JSON string is a string, not a document to re-parse"
    )
    assert examples["count"] == 3
    assert examples["tags"] == ["a", "b"]
    assert examples["nested"] == {"k": "v"}
