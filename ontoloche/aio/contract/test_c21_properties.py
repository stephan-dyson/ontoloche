# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c21_properties.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C21 -- property declarations (INTERFACE.md 2.10, ruling R108). Row 8c.

**What a property *is*, never what it holds.** Every id here is a rule of 2.10's table,
and two design tests (UC2, UC3) walked through real calls. Rules 2.10-17 to 2.10-21 are
``reserved:`` for founder questions Q103 to Q106 and are pinned by
``docs/tools/properties_baseline_probe.py --assert``, not here: a contract id is what a
third-party backend certifies, and nobody should certify a behaviour the founder has not
ruled.
"""

from __future__ import annotations
import dataclasses
import pytest
from ontoloche import types as types_module
from ontoloche.actions import PROPOSABLE_KINDS
from ontoloche.properties import (
    BASE_TYPES,
    EntityDeclaration,
    PropertySpec,
    SharedPropertyDeclaration,
    entity_declaration,
    shared_property_declaration,
)
from ontoloche.types import MergeResult, Proposal, Refusal, ResolveContext, TypeEntry
from ontoloche.aio.contract._support import seed
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter


CTX = ResolveContext(source="C21")

LOCATION_CTX = ResolveContext(
    source="NH_HealthCitations_Aug2026.csv#Location",
    sibling_columns=("Provider Address", "City/Town", "State", "ZIP Code"),
    sample_values=("2621 15TH AVE S,GREAT FALLS,MT,59405",),
)

PROCESSING_CTX = ResolveContext(
    source="NH_HealthCitations_Aug2026.csv#Processing Date",
    sample_values=("2026-08-01",) * 12,
    sibling_columns=("Survey Date", "Correction Date"),
)

def _local(name, base="str", **extra):
    return {"name": name, "base_type": base, "description": f"the {name}", **extra}

async def _propose(registry, name, attributes, *, kind="entity", namespace="default"):
    return await registry.propose_type(
        name, f"a {name}, for C21", [], "user:sd",
        kind=kind, namespace=namespace, attributes=attributes,
    )

async def _write(registry, name, attributes, *, kind="entity", namespace="default"):
    """propose + approve; returns the final TypeEntry or the Refusal."""
    out = await _propose(registry, name, attributes, kind=kind, namespace=namespace)
    if isinstance(out, Proposal):
        out = await registry.approve(out.id, "user:sd")
    return out

async def _import(registry, rows, namespace="default"):
    return await registry.import_types(rows, system="c21", namespace=namespace, imported_by="import:c21")

def _prop_warnings(entry):
    """The rule 2.10-10 reference warnings. 2.10-16's not_stored is read on its own."""
    return [w for w in entry.warnings if w.startswith("property_reference_")]

def _not_stored_warnings(entry):
    return sorted(w for w in entry.warnings if w.startswith("property_declaration_not_stored"))

def _refused(out, rule, key=None, slot=None):
    assert isinstance(out, Refusal), out
    assert out.reason == "attributes_schema_violation", out
    assert out.detail.get("rule") == rule, out.detail
    if key is not None:
        assert out.detail.get("key") == key, out.detail
    if slot is not None:
        assert out.detail.get("slot") == slot, out.detail

def _not_stored(caps, keys):
    return {k: "not_stored" for k in keys if not caps.stores_attribute(k)}

async def _entry(registry, kind, attributes, name="probe"):
    """A TypeEntry carrying stored data the doors would refuse, for the pure views."""
    base = await seed(registry, name, kind=kind)
    return dataclasses.replace(base, attributes=attributes)

class _AllCaps:
    @staticmethod
    def stores_attribute(key):
        return True

async def test_c21_01_an_entry_declaring_nothing_and_the_pre_amendment_shape_are_unchanged(registry):
    plain = await seed(registry, "facility")
    assert _prop_warnings(plain) == []
    view = entity_declaration(plain, registry.caps)
    assert view.properties is None and view.primary_key is None and view.title_property is None
    assert view.why_absent == _not_stored(registry.caps, ("properties", "primary_key", "title_property"))

    # The CMS fixture's own shape: primary_key with no properties, names unchecked.
    keyed = await _write(registry, "survey", {"primary_key": ["ccn", "survey_date", "survey_type"]})
    assert isinstance(keyed, TypeEntry), keyed
    assert _prop_warnings(keyed) == []
    if registry.caps.stores_attribute("primary_key"):
        assert entity_declaration(keyed, registry.caps).primary_key == ("ccn", "survey_date", "survey_type")
    else:
        assert entity_declaration(keyed, registry.caps).why_absent["primary_key"] == "not_stored"

    # ...but its shape is checked (2.10-1), and `properties: []` is present.
    _refused(await _write(registry, "citation", {"primary_key": []}), "2.10-1", "primary_key")
    _refused(await _write(registry, "citation", {"primary_key": ["a", "a"]}), "2.10-1", "primary_key")
    _refused(await _write(registry, "citation", {"title_property": ""}), "2.10-1", "title_property")
    _refused(
        await _write(registry, "deficiency_tag", {"properties": [], "primary_key": ["tag_number"]}),
        "2.10-5", "primary_key",
    )
    # JSON null for a reserved key reads as absent.
    nulls = await _write(registry, "tag", {"properties": None, "primary_key": None})
    assert isinstance(nulls, TypeEntry), nulls

async def test_c21_01_tenshen_shaped_entries_gain_no_warning(registry):
    """UC1: Tenshen's vocabulary is relationship types and declares no reserved key."""
    for name in ("blocks", "relates_to", "duplicates"):
        entry = await seed(registry, name, kind="edge")
        assert _prop_warnings(entry) == []

async def test_c21_02_a_breach_is_refused_at_propose_and_declined_at_import_whatever_the_schema_mode(registry):
    bad = {"properties": [{"name": "zip", "base_type": "zipcode", "description": "a zip"}]}
    _refused(await _propose(registry, "facility", bad), "2.10-3", "properties", "zip")

    out = await _import(registry, [
        {"name": "facility", "kind": "entity", "definition": "a nursing home", "attributes": bad},
        {"name": "survey", "kind": "entity", "definition": "an inspection",
         "attributes": {"properties": [_local("ccn")], "primary_key": ["ccn"]}},
    ])
    assert "import_refused:attributes_schema_violation" in out[0].warnings, out[0].warnings
    assert await registry.adapter.get_type("default", "facility", kind="entity") is None
    assert isinstance(out[1], TypeEntry) and not any(w.startswith("import_refused") for w in out[1].warnings)
    assert await registry.adapter.get_type("default", "survey", kind="entity") is not None

@pytest.mark.requires_capability("stores_proposals")
async def test_c21_02_approve_refuses_a_proposal_that_predates_the_rule(registry):
    ok = await _propose(registry, "facility", {"properties": [_local("ccn")]})
    assert isinstance(ok, Proposal), ok
    rec = await registry.adapter.get_proposal(ok.id)
    await registry.adapter.put_proposal(
        dataclasses.replace(rec, attributes={"properties": [{"name": "ccn", "base_type": "nope", "description": "x"}]})
    )
    _refused(await registry.approve(ok.id, "user:sd"), "2.10-3", "properties", "ccn")

async def test_c21_03_the_stored_shape_is_closed_and_a_missing_description_is_refused_at_propose(registry):
    _refused(await _propose(registry, "a", {"properties": [{**_local("x"), "requird": True}]}), "2.10-3", "properties", "x")
    _refused(await _propose(registry, "a", {"properties": [{"base_type": "str", "description": "d"}]}), "2.10-3")
    _refused(await _propose(registry, "a", {"properties": "ccn"}), "2.10-3", "properties")
    _refused(await _propose(registry, "a", {"properties": [{**_local("x"), "required": "yes"}]}), "2.10-3")
    _refused(
        await _propose(registry, "a", {"properties": [{"name": "x", "shared": "x", "base_type": "str"}]}),
        "2.10-3", "properties", "x",
    )
    # A null field reads as absent, so a shared slot with nulled local fields is legal.
    await seed(registry, "x", kind="property", attributes={"base_type": "str"})
    ok = await _write(registry, "b", {"properties": [{"name": "x", "shared": "x", "base_type": None, "description": None}]})
    assert isinstance(ok, TypeEntry), ok
    # Missing, empty and whitespace-only descriptions are one thing (row 8b finding 3).
    for description in (None, "", "   "):
        slot = {"name": "y", "base_type": "str"}
        if description is not None:
            slot["description"] = description
        _refused(await _propose(registry, "c", {"properties": [slot]}), "2.10-3", "properties", "y")

async def test_c21_03_a_blank_description_on_a_shared_slot_is_a_missing_one(registry):
    """Round 1, lens A finding 3: a blank description is missing at every door, so a
    shared slot carrying "" or whitespace carries nothing and is not refused."""
    await seed(registry, "ccn", kind="property", attributes={"base_type": "str"})
    for blank in ("", "   "):
        out = await _write(registry, f"site{len(blank)}", {"properties": [
            {"name": "ccn", "shared": "ccn", "description": blank}]})
        assert isinstance(out, TypeEntry), out
    back = await registry.import_types([{"name": "site9", "definition": "a site", "status": "active",
                                   "attributes": {"properties": [{"name": "ccn", "shared": "ccn", "description": ""}]}}])
    assert not [w for w in back[0].warnings if w.startswith("import_refused")], back[0].warnings

async def test_c21_03_a_missing_description_is_not_a_breach_to_the_view(registry):
    entry = await _entry(registry, "entity", {"properties": [{"name": "y", "base_type": "str", "description": ""}]})
    view = entity_declaration(entry, _AllCaps())
    assert view.properties == (PropertySpec(name="y", base_type="str"),)
    assert view.why_absent == {}

async def test_c21_04_slot_names_are_unique_and_mixed_case(registry):
    ok = await _write(registry, "employee", {"properties": [_local("fullName"), _local("employee_id")]})
    assert isinstance(ok, TypeEntry), ok
    _refused(await _propose(registry, "a", {"properties": [_local("x"), _local("x")]}), "2.10-4", "properties", "x")
    _refused(await _propose(registry, "a", {"properties": [_local("1x")]}), "2.10-4")
    _refused(await _propose(registry, "a", {"properties": [_local("City/Town")]}), "2.10-4")

async def test_c21_05_key_and_title_name_declared_slots_and_a_key_slot_is_required(registry):
    _refused(await _propose(registry, "a", {"properties": [_local("x")], "primary_key": ["y"]}), "2.10-5", "primary_key", "y")
    _refused(await _propose(registry, "a", {"properties": [_local("x")], "title_property": "y"}), "2.10-5", "title_property")
    _refused(
        await _propose(registry, "a", {"properties": [_local("x", required=False)], "primary_key": ["x"]}),
        "2.10-5", "primary_key", "x",
    )
    entry = await _write(registry, "survey", {
        "properties": [_local("ccn"), _local("survey_date", "date"), _local("note", required=False)],
        "primary_key": ["ccn", "survey_date"],
    })
    assert isinstance(entry, TypeEntry), entry
    view = entity_declaration(entry, registry.caps)
    if registry.caps.stores_attribute("properties"):
        required = {p.name: p.required for p in view.properties}
        assert required == {"ccn": True, "survey_date": True, "note": False}

async def test_c21_05_a_duplicate_key_slot_among_declared_slots_is_rule_2_10_5(registry):
    """Round 2, lens A finding 4: with slots declared, distinct key slots are 2.10-5's."""
    _refused(
        await _propose(registry, "a", {"properties": [_local("x")], "primary_key": ["x", "x"]}),
        "2.10-5", "primary_key",
    )
    _refused(await _propose(registry, "a", {"primary_key": ["x", "x"]}), "2.10-1", "primary_key")

async def test_c21_05_an_unhashable_key_beside_slots_is_refused_never_raised(registry):
    """Round 3, lens A finding 1: a list or dict where a key name belongs is rule
    2.10-1's refusal at every door, and one such row never fails an import."""
    slots = [_local("ccn")]
    _refused(await _propose(registry, "a", {"properties": slots, "title_property": ["ccn"]}), "2.10-1", "title_property")
    _refused(await _propose(registry, "a", {"properties": slots, "primary_key": [["ccn"]]}), "2.10-1", "primary_key")
    _refused(await _propose(registry, "a", {"properties": slots, "primary_key": [{}]}), "2.10-1", "primary_key")
    # A properties value that is not a list is not "present" (round 3, lens A finding 2).
    _refused(await _propose(registry, "a", {"properties": "x", "primary_key": ["a", "a"]}), "2.10-1", "primary_key")
    rows = [
        {"name": "good_one", "definition": "fine", "status": "active"},
        {"name": "bad_one", "definition": "bad", "status": "active",
         "attributes": {"properties": slots, "title_property": ["ccn"]}},
    ]
    out = await _import(registry, rows, namespace="c21_05_u")
    assert [e.name for e in out] == ["good_one", "bad_one"]
    assert out[0].warnings == ()
    assert out[1].warnings == ("import_refused:attributes_schema_violation",)
    assert await registry.adapter.get_type("c21_05_u", "bad_one", kind="entity") is None

async def test_c21_05_a_breach_in_stored_data_nulls_the_key_never_the_slots(registry):
    entry = await _entry(registry, "entity", {"properties": [_local("x")], "primary_key": ["y"], "title_property": "z"})
    view = entity_declaration(entry, _AllCaps())
    assert [p.name for p in view.properties] == ["x"]
    assert view.primary_key is None and view.title_property is None
    assert view.why_absent == {"primary_key": "breaches:2.10-5", "title_property": "breaches:2.10-5"}
    with pytest.raises(ValueError):
        entity_declaration(dataclasses.replace(entry, kind="predicate"), _AllCaps())

async def test_c21_06_item_type_with_list_and_opaque_says_what_it_holds(registry):
    _refused(await _propose(registry, "a", {"properties": [_local("x", "list")]}), "2.10-6")
    _refused(await _propose(registry, "a", {"properties": [_local("x", "list", item_type="list")]}), "2.10-6")
    _refused(await _propose(registry, "a", {"properties": [_local("x", "str", item_type="str")]}), "2.10-6")
    _refused(await _propose(registry, "a", {"properties": [_local("x", "opaque")]}), "2.10-6")
    _refused(await _propose(registry, "a", {"properties": [_local("x", "list", item_type="opaque")]}), "2.10-6")
    ok = await _write(registry, "b", {"properties": [
        _local("loc", "opaque", source_type="geopoint"),
        _local("tags", "list", item_type="str"),
    ]})
    assert isinstance(ok, TypeEntry), ok
    assert set(BASE_TYPES) == {"str", "int", "float", "decimal", "bool", "date", "datetime", "list", "dict", "opaque"}

async def test_c21_07_a_value_set_only_on_an_enumerable_type(registry):
    await seed(registry, "flags", kind="value_set")
    _refused(await _propose(registry, "a", {"properties": [_local("x", "bool", value_set="flags")]}), "2.10-7")
    _refused(await _propose(registry, "a", {"properties": [_local("x", "list", item_type="float", value_set="flags")]}), "2.10-7")
    ok = await _write(registry, "b", {"properties": [_local("x", "list", item_type="str", value_set="flags")]})
    assert isinstance(ok, TypeEntry), ok
    assert _prop_warnings(ok) == []

async def test_c21_08_references_are_bare_canonical_words(registry):
    for word in ("fooSpt", "zip__code", "zip_code_", "dot:latitude", "has space"):
        _refused(await _propose(registry, "a", {"properties": [{"name": "x", "shared": word}]}), "2.10-8", "properties", "x")
        _refused(await _propose(registry, "a", {"properties": [_local("x", value_set=word)]}), "2.10-8")

async def test_c21_09_a_property_entry_declares_nothing_or_a_base_type(registry):
    bare = await seed(registry, "latitude", kind="property")
    assert isinstance(bare, TypeEntry)
    typed = await seed(registry, "zip_code", kind="property", attributes={"base_type": "str", "display_name": "ZIP"})
    view = shared_property_declaration(typed, registry.caps)
    if registry.caps.stores_attribute("base_type"):
        assert view.base_type == "str" and view.why_absent == {}
    else:
        assert view.base_type is None and view.why_absent["base_type"] == "not_stored"
    _refused(await _propose(registry, "a", {"display_name": "A"}, kind="property"), "2.10-9")
    _refused(await _propose(registry, "a", {"base_type": "str", "required": True}, kind="property"), "2.10-9", "required")
    # detail.key names the offending key itself on a property entry (round 1, A4).
    _refused(await _propose(registry, "a", {"base_type": "list"}, kind="property"), "2.10-6", "item_type")
    _refused(await _propose(registry, "a", {"base_type": "opaque"}, kind="property"), "2.10-6", "source_type")
    _refused(await _propose(registry, "a", {"base_type": "float", "value_set": "v"}, kind="property"), "2.10-7", "value_set")
    _refused(await _propose(registry, "a", {"base_type": "str", "value_set": "V"}, kind="property"), "2.10-8", "value_set")
    with pytest.raises(ValueError):
        shared_property_declaration(dataclasses.replace(bare, kind="entity"), registry.caps)

async def test_c21_09_a_breach_in_stored_data_nulls_every_reserved_key(registry):
    entry = await _entry(registry, "property", {"base_type": "str", "required": True, "display_name": "Z"}, name="zz")
    view = shared_property_declaration(entry, _AllCaps())
    assert view == SharedPropertyDeclaration(None, None, None, None, None, {"base_type": "breaches:2.10-9"})

async def test_c21_10_a_reference_is_written_and_warned_never_refused(registry):
    out = await _write(registry, "employee", {"properties": [
        {"name": "fullName", "shared": "foo_spt"},
        _local("dept", value_set="departments"),
    ]})
    assert isinstance(out, TypeEntry), out
    assert set(_prop_warnings(out)) == {
        "property_reference_unregistered:fullName:foo_spt",
        "property_reference_unregistered:dept:departments",
    }

    await seed(registry, "foo_spt", kind="property", attributes={"base_type": "str"})
    await seed(registry, "departments", kind="value_set")
    found = await _write(registry, "office", {"properties": [{"name": "name", "shared": "foo_spt"}, _local("d", value_set="departments")]})
    assert _prop_warnings(found) == []

    # A property entry's own value set is labelled `*`.
    star = await _write(registry, "dept_code", {"base_type": "str", "value_set": "nope"}, kind="property")
    assert _prop_warnings(star) == ["property_reference_unregistered:*:nope"]

async def test_c21_10_undeclared_reads_the_view(registry):
    await seed(registry, "bare", kind="property")
    out = await _write(registry, "a", {"properties": [{"name": "x", "shared": "bare"}]})
    if registry.caps.stores_attribute("base_type"):
        assert _prop_warnings(out) == ["property_reference_undeclared:x:bare"]
    else:
        # not stored is 2.10-16's, and saying "undeclared" would be false (Rule U).
        assert _prop_warnings(out) == []

@pytest.mark.requires_capability("stores_proposals")
async def test_c21_10_approve_recomputes_the_warnings(registry):
    pending = await _propose(registry, "a", {"properties": [{"name": "x", "shared": "later"}]})
    assert "property_reference_unregistered:x:later" in pending.warnings
    await seed(registry, "later", kind="property", attributes={"base_type": "int"})
    entry = await registry.approve(pending.id, "user:sd")
    assert isinstance(entry, TypeEntry), entry
    assert _prop_warnings(entry) == []

@pytest.mark.requires_capability("stores_events")
async def test_c21_10_retired_and_redirected(registry):
    await seed(registry, "zip_code", kind="property", attributes={"base_type": "str"})
    await seed(registry, "postal_code", kind="property", attributes={"base_type": "str"})
    await seed(registry, "old_code", kind="property", attributes={"base_type": "str"})
    # force=True: the identity guard is not this test's subject, and a backend that
    # declines indexes_membership refuses it unforced (no_consumer_evidence).
    assert not isinstance(
        await registry.retire("zip_code", "renamed", retired_by="user:sd", successor="postal_code", force=True),
        Refusal,
    )
    assert not isinstance(await registry.retire("old_code", "gone", retired_by="user:sd", force=True), Refusal)
    out = await _write(registry, "a", {"properties": [{"name": "z", "shared": "zip_code"}, {"name": "o", "shared": "old_code"}]})
    assert set(_prop_warnings(out)) == {
        "property_reference_redirected:z:zip_code:postal_code",
        "property_reference_retired:o:old_code",
    }

async def test_c21_10_a_scan_that_cannot_finish_is_unknown_never_absent(adapter, make_registry):
    full = await make_registry(adapter)
    for i in range(6):
        await seed(full, f"p{i}", kind="property", attributes={"base_type": "str"})
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=2))
    out = await _write(capped, "a", {"properties": [{"name": "x", "shared": "missing"}]})
    assert _prop_warnings(out) == ["property_reference_unknown:x:missing"], out.warnings

async def test_c21_11_the_reader_stays_in_its_kind_and_reads_name_or_alias_spellings(registry):
    # An alias held by an entry of ANOTHER kind is not a property (row 8b finding 1).
    await seed(registry, "grid", kind="value_set")
    await registry.import_types(
        [{"name": "severity", "kind": "property", "definition": "a property", "aliases": ["scope_severity_grid"],
          "attributes": {"base_type": "str"}}],
        system="c21", namespace="default", imported_by="import:c21",
    )
    out = await _write(registry, "a", {"properties": [_local("s", value_set="scope_severity_grid")]})
    assert _prop_warnings(out) == ["property_reference_unregistered:s:scope_severity_grid"]
    # A live row whose NAME is another spelling of the word (UC3's `borough_`).
    await seed(registry, "borough_", kind="property", attributes={"base_type": "str"})
    out = await _write(registry, "b", {"properties": [{"name": "b", "shared": "borough"}]})
    assert _prop_warnings(out) == ["property_reference_redirected:b:borough:borough_"]

@pytest.mark.requires_capability("stores_events", "stores_aliases")
async def test_c21_11_a_dead_end_falls_through_to_a_live_alias_holder(registry):
    """Row 8b finding 2: the reader must not say *retired* while resolve_type answers
    the alias holder at 1.0."""
    await seed(registry, "zip_code", kind="property", attributes={"base_type": "str"})
    await seed(registry, "postal_code", kind="property", attributes={"base_type": "str"})
    await registry.retire("zip_code", "renamed", retired_by="user:sd", successor="postal_code", force=True)
    await registry.retire("postal_code", "gone", retired_by="user:sd", force=True)
    await registry.import_types(
        [{"name": "post_code", "kind": "property", "definition": "a post code", "aliases": ["zip_code"],
          "attributes": {"base_type": "str"}}],
        system="c21", namespace="default", imported_by="import:c21",
    )
    out = await _write(registry, "a", {"properties": [{"name": "z", "shared": "zip_code"}]})
    assert _prop_warnings(out) == ["property_reference_redirected:z:zip_code:post_code"]
    res = await registry.resolve_type("zip_code", CTX, kind="property", tier="unspecified")
    assert res.type is not None and res.type.name == "post_code"

@pytest.mark.requires_capability("stores_events")
async def test_c21_11_the_reader_never_crosses_a_namespace(registry):
    await seed(registry, "latitude", kind="property", namespace="dot", attributes={"base_type": "float"})
    out = await _write(registry, "street_tree", {"properties": [{"name": "latitude", "shared": "latitude"}]}, namespace="dpr")
    assert _prop_warnings(out) == ["property_reference_unregistered:latitude:latitude"]

async def test_c21_12_resolve_type_with_kind_property(registry):
    res = await registry.resolve_type("latitude", CTX, kind="property", tier="unspecified")
    assert res.outcome == "proposal" and res.proposal.kind == "property"
    await seed(registry, "latitude", kind="property", attributes={"base_type": "float"})
    res = await registry.resolve_type("latitude", CTX, kind="property", tier="unspecified")
    assert res.outcome == "existing" and res.type.name == "latitude" and res.confidence == 1.0
    # The not_a_type check runs before `kind` is read, so CMS's Location stays one.
    loc = await registry.resolve_type("location", LOCATION_CTX, kind="property", tier="opus")
    assert loc.outcome == "not_a_type" and loc.reason == "redundant_projection", loc

async def test_c21_13_kind_blind_guards_apply_to_properties(registry):
    first = await seed(registry, "zip_code", kind="property", attributes={"base_type": "str"})
    again = await _propose(registry, "zip_code", {"base_type": "str"}, kind="property")
    assert isinstance(again, TypeEntry) and again.name == first.name
    await seed(registry, "zip_pred", kind="predicate")
    # merge_types takes no kind, so the word must be unambiguous: one property, one entity.
    await seed(registry, "zip_entity", kind="entity")
    into_entity = await registry.merge_types("zip_code", "zip_entity", "same", merged_by="user:sd")
    assert isinstance(into_entity, Refusal) and into_entity.reason == "kind_mismatch", into_entity
    into_pred = await registry.merge_types("zip_code", "zip_pred", "same", merged_by="user:sd")
    assert isinstance(into_pred, Refusal) and into_pred.reason == "predicate_merge", into_pred
    await seed(registry, "zip_code", kind="property", namespace="other", attributes={"base_type": "str"})
    across = await registry.merge_types("zip_code", "zip_code", "same", merged_by="user:sd", into_namespace="other")
    assert isinstance(across, Refusal) and across.reason == "cross_namespace_merge", across

async def test_c21_14_a_key_the_backend_cannot_store_is_warned_and_named_not_stored(registry):
    attrs = {"properties": [_local("ccn")], "primary_key": ["ccn"], "title_property": "ccn"}
    out = await _write(registry, "facility", attrs)
    assert isinstance(out, TypeEntry), out
    expected = sorted(
        f"property_declaration_not_stored:{k}" for k in attrs if not registry.caps.stores_attribute(k)
    )
    assert _not_stored_warnings(out) == expected
    stored = await registry.adapter.get_type("default", "facility", kind="entity")
    view = entity_declaration(stored, registry.caps)
    assert view.why_absent == _not_stored(registry.caps, attrs)
    if registry.caps.stores_attribute("primary_key"):
        assert view.primary_key == ("ccn",)

async def test_c21_14_a_degraded_backend_says_what_it_drops(adapter, make_registry):
    reg = await make_registry(AsyncDegradedAdapter(adapter, stores_attributes=False))
    out = await _write(reg, "zip_code", {"base_type": "str"}, kind="property")
    assert "property_declaration_not_stored:base_type" in out.warnings
    view = shared_property_declaration(out, reg.caps)
    assert view.why_absent.get("base_type") == "not_stored"

async def test_c21_14_a_dropped_base_type_is_never_read_as_a_breach(adapter, make_registry):
    """Round 2, lens A finding 1: a display_name whose base_type the backend dropped
    is not_stored, never breaches:2.10-9."""
    reg = await make_registry(AsyncDegradedAdapter(adapter, stores_attributes=False, attribute_projections={"display_name"}))
    out = await _write(reg, "zip_code", {"base_type": "str", "display_name": "Zip"}, kind="property")
    assert "property_declaration_not_stored:base_type" in out.warnings
    stored = await reg.adapter.get_type("default", "zip_code", kind="property")
    view = shared_property_declaration(stored, reg.caps)
    assert view.why_absent.get("base_type") == "not_stored", view.why_absent
    assert not any(v.startswith("breaches:") for v in view.why_absent.values()), view.why_absent

async def test_c21_14_a_reference_the_backend_drops_is_still_warned(adapter, make_registry):
    """Round 2, lens A finding 3: the warning describes what the caller declared, and
    not_stored says apart that it was not kept (rule 2.10-10)."""
    reg = await make_registry(AsyncDegradedAdapter(adapter, stores_attributes=False))
    out = await _write(reg, "employee", {"properties": [
        {"name": "fullName", "shared": "foo_spt"}, _local("dept", value_set="departments"),
    ]})
    assert isinstance(out, TypeEntry), out
    assert "property_declaration_not_stored:properties" in out.warnings
    assert set(_prop_warnings(out)) == {
        "property_reference_unregistered:fullName:foo_spt",
        "property_reference_unregistered:dept:departments",
    }
    star = await _write(reg, "dept_code", {"base_type": "str", "value_set": "nope"}, kind="property")
    assert "property_declaration_not_stored:value_set" in star.warnings
    assert _prop_warnings(star) == ["property_reference_unregistered:*:nope"]

@pytest.mark.requires_capability("indexes_membership")
async def test_c21_15_property_is_a_kind_and_never_a_predicate(registry):
    assert "property" in types_module.KINDS
    assert "property" not in PROPOSABLE_KINDS
    await seed(registry, "geo", kind="predicate")
    member = await seed(registry, "latitude", kind="property", predicates=["geo"], attributes={"base_type": "float"})
    assert "geo" in member.predicates
    refused = await registry.merge_types("latitude", "geo", "same", merged_by="user:sd")
    assert isinstance(refused, Refusal) and refused.reason == "predicate_merge", refused

async def test_c21_16_uc2_cms_twenty_one_columns_through_real_calls(registry):
    caps = registry.caps
    for vs in ("scope_severity_code", "deficiency_corrected_status"):
        assert _prop_warnings(await seed(registry, vs, kind="value_set")) == []
    ccn = await _write(registry, "ccn", {"base_type": "str", "display_name": "CMS Certification Number (CCN)"}, kind="property")
    assert isinstance(ccn, TypeEntry), ccn
    declarations = {
        "facility": {
            "properties": [
                {"name": "ccn", "shared": "ccn"},
                _local("provider_name", display_name="Provider Name"),
                _local("provider_address", display_name="Provider Address"),
                _local("city_town", display_name="City/Town"),
                _local("state", display_name="State"),
                _local("zip_code", display_name="ZIP Code"),
            ],
            "primary_key": ["ccn"],
            "title_property": "provider_name",
        },
        "survey": {
            "properties": [{"name": "ccn", "shared": "ccn"}, _local("survey_date", "date"), _local("survey_type")],
            "primary_key": ["ccn", "survey_date", "survey_type"],
        },
        "deficiency_tag": {
            "properties": [_local("tag_number"), _local("deficiency_prefix"), _local("deficiency_category"),
                           _local("deficiency_description")],
            "primary_key": ["tag_number"],
            "title_property": "deficiency_description",
        },
        "citation": {
            "properties": [
                _local("scope_severity_code", value_set="scope_severity_code"),
                _local("deficiency_corrected", value_set="deficiency_corrected_status"),
                _local("correction_date", "date"),
                _local("inspection_cycle", "int"),
                *[_local(f, "bool") for f in ("standard_deficiency", "complaint_deficiency",
                                             "infection_control_deficiency", "citation_under_idr",
                                             "citation_under_iidr")],
            ],
        },
    }
    slots = 0
    for name, attrs in declarations.items():
        entry = await _write(registry, name, attrs)
        assert isinstance(entry, TypeEntry), (name, entry)
        not_stored = sorted(f"property_declaration_not_stored:{k}" for k in attrs if not caps.stores_attribute(k))
        assert _not_stored_warnings(entry) == not_stored and _prop_warnings(entry) == [], entry.warnings
        view = entity_declaration(await registry.adapter.get_type("default", name, kind="entity"), caps)
        # Every key the backend cannot keep, declared or not: it cannot know which.
        assert view.why_absent == _not_stored(caps, ("properties", "primary_key", "title_property"))
        if view.properties is not None:
            slots += len(view.properties)
    if caps.stores_attribute("properties"):
        assert slots == 22  # 21 columns, `ccn` used twice through one entry
    for column, ctx, reason in (("location", LOCATION_CTX, "redundant_projection"),
                                ("processing_date", PROCESSING_CTX, "export_artefact")):
        res = await registry.resolve_type(column, ctx, tier="opus")
        assert res.outcome == "not_a_type" and res.reason == reason, res

@pytest.mark.requires_capability("stores_events")
async def test_c21_17_uc3_nyc_status_stays_three_things_and_coordinates_are_properties(registry):
    for ns in ("dpr", "oti_311", "dot"):
        await seed(registry, "status", kind="value_set", namespace=ns)
    await seed(registry, "latitude", kind="property", namespace="dot", attributes={"base_type": "float"})
    await seed(registry, "longitude", kind="property", namespace="dot", attributes={"base_type": "float"})
    for ns, entity in (("dpr", "street_tree"), ("oti_311", "service_request"), ("dot", "parking_meter")):
        out = await _write(registry, entity, {"properties": [_local("status", value_set="status")]}, namespace=ns)
        assert _prop_warnings(out) == [], out.warnings
    dot = await _write(registry, "sign", {"properties": [{"name": "latitude", "shared": "latitude"},
                                                    {"name": "longitude", "shared": "longitude"}]}, namespace="dot")
    assert _prop_warnings(dot) == []
    res = await registry.resolve_type("latitude", CTX, kind="property", namespace="dot", tier="unspecified")
    assert res.outcome == "existing" and res.confidence == 1.0
    res = await registry.resolve_type("latitude", CTX, kind="property", namespace="dpr", tier="unspecified")
    assert res.outcome == "proposal" and res.proposal.kind == "property"
    # 8C-RUN.md 0.4 UC3 items 2 and 3 through a write, not only through resolve_type
    # (round 1, lens C finding 1): the reader never crosses a namespace.
    tree = await _write(registry, "tree_pit", {"properties": [{"name": "latitude", "shared": "latitude"}]}, namespace="dpr")
    assert _prop_warnings(tree) == ["property_reference_unregistered:latitude:latitude"], tree.warnings
    await seed(registry, "borough", kind="value_set", namespace="dot")
    pit = await _write(registry, "pit", {"properties": [_local("borough", value_set="borough")]}, namespace="dpr")
    assert _prop_warnings(pit) == ["property_reference_unregistered:borough:borough"], pit.warnings
    merged = await registry.merge_types("status", "status", "same", merged_by="user:sd", namespace="dpr", into_namespace="dot")
    assert isinstance(merged, Refusal) and merged.reason == "cross_namespace_merge", merged
