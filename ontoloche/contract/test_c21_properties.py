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

from .. import types as types_module
from ..actions import PROPOSABLE_KINDS
from ..properties import (
    BASE_TYPES,
    EntityDeclaration,
    PropertySpec,
    SharedPropertyDeclaration,
    entity_declaration,
    shared_property_declaration,
)
from ..types import MergeResult, Proposal, Refusal, ResolveContext, TypeEntry
from ._support import seed
from .doubles import DegradedAdapter

CTX = ResolveContext(source="C21")
#: C3-08 and C3-09's contexts: the evidence `not_a_type` reads.
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


# ----------------------------------------------------------------------- helpers


def _local(name, base="str", **extra):
    return {"name": name, "base_type": base, "description": f"the {name}", **extra}


def _propose(registry, name, attributes, *, kind="entity", namespace="default"):
    return registry.propose_type(
        name, f"a {name}, for C21", [], "user:sd",
        kind=kind, namespace=namespace, attributes=attributes,
    )


def _write(registry, name, attributes, *, kind="entity", namespace="default"):
    """propose + approve; returns the final TypeEntry or the Refusal."""
    out = _propose(registry, name, attributes, kind=kind, namespace=namespace)
    if isinstance(out, Proposal):
        out = registry.approve(out.id, "user:sd")
    return out


def _import(registry, rows, namespace="default"):
    return registry.import_types(rows, system="c21", namespace=namespace, imported_by="import:c21")


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


def _entry(registry, kind, attributes, name="probe"):
    """A TypeEntry carrying stored data the doors would refuse, for the pure views."""
    base = seed(registry, name, kind=kind)
    return dataclasses.replace(base, attributes=attributes)


class _AllCaps:
    @staticmethod
    def stores_attribute(key):
        return True


# ------------------------------------------------------------------- rule 2.10-1


def test_c21_01_an_entry_declaring_nothing_and_the_pre_amendment_shape_are_unchanged(registry):
    plain = seed(registry, "facility")
    assert _prop_warnings(plain) == []
    view = entity_declaration(plain, registry.caps)
    assert view.properties is None and view.primary_key is None and view.title_property is None
    assert view.why_absent == _not_stored(registry.caps, ("properties", "primary_key", "title_property"))

    # The CMS fixture's own shape: primary_key with no properties, names unchecked.
    keyed = _write(registry, "survey", {"primary_key": ["ccn", "survey_date", "survey_type"]})
    assert isinstance(keyed, TypeEntry), keyed
    assert _prop_warnings(keyed) == []
    if registry.caps.stores_attribute("primary_key"):
        assert entity_declaration(keyed, registry.caps).primary_key == ("ccn", "survey_date", "survey_type")
    else:
        assert entity_declaration(keyed, registry.caps).why_absent["primary_key"] == "not_stored"

    # ...but its shape is checked (2.10-1), and `properties: []` is present.
    _refused(_write(registry, "citation", {"primary_key": []}), "2.10-1", "primary_key")
    _refused(_write(registry, "citation", {"primary_key": ["a", "a"]}), "2.10-1", "primary_key")
    _refused(_write(registry, "citation", {"title_property": ""}), "2.10-1", "title_property")
    _refused(
        _write(registry, "deficiency_tag", {"properties": [], "primary_key": ["tag_number"]}),
        "2.10-5", "primary_key",
    )
    # JSON null for a reserved key reads as absent.
    nulls = _write(registry, "tag", {"properties": None, "primary_key": None})
    assert isinstance(nulls, TypeEntry), nulls


def test_c21_01_tenshen_shaped_entries_gain_no_warning(registry):
    """UC1: Tenshen's vocabulary is relationship types and declares no reserved key."""
    for name in ("blocks", "relates_to", "duplicates"):
        entry = seed(registry, name, kind="edge")
        assert _prop_warnings(entry) == []


# ------------------------------------------------------------------- rule 2.10-2


def test_c21_02_a_breach_is_refused_at_propose_and_declined_at_import_whatever_the_schema_mode(registry):
    bad = {"properties": [{"name": "zip", "base_type": "zipcode", "description": "a zip"}]}
    _refused(_propose(registry, "facility", bad), "2.10-3", "properties", "zip")

    out = _import(registry, [
        {"name": "facility", "kind": "entity", "definition": "a nursing home", "attributes": bad},
        {"name": "survey", "kind": "entity", "definition": "an inspection",
         "attributes": {"properties": [_local("ccn")], "primary_key": ["ccn"]}},
    ])
    assert "import_refused:attributes_schema_violation" in out[0].warnings, out[0].warnings
    assert registry.adapter.get_type("default", "facility", kind="entity") is None
    assert isinstance(out[1], TypeEntry) and not any(w.startswith("import_refused") for w in out[1].warnings)
    assert registry.adapter.get_type("default", "survey", kind="entity") is not None


@pytest.mark.requires_capability("stores_proposals")
def test_c21_02_approve_refuses_a_proposal_that_predates_the_rule(registry):
    ok = _propose(registry, "facility", {"properties": [_local("ccn")]})
    assert isinstance(ok, Proposal), ok
    rec = registry.adapter.get_proposal(ok.id)
    registry.adapter.put_proposal(
        dataclasses.replace(rec, attributes={"properties": [{"name": "ccn", "base_type": "nope", "description": "x"}]})
    )
    _refused(registry.approve(ok.id, "user:sd"), "2.10-3", "properties", "ccn")


# ------------------------------------------------------------------- rule 2.10-3


def test_c21_03_the_stored_shape_is_closed_and_a_missing_description_is_refused_at_propose(registry):
    _refused(_propose(registry, "a", {"properties": [{**_local("x"), "requird": True}]}), "2.10-3", "properties", "x")
    _refused(_propose(registry, "a", {"properties": [{"base_type": "str", "description": "d"}]}), "2.10-3")
    _refused(_propose(registry, "a", {"properties": "ccn"}), "2.10-3", "properties")
    _refused(_propose(registry, "a", {"properties": [{**_local("x"), "required": "yes"}]}), "2.10-3")
    _refused(
        _propose(registry, "a", {"properties": [{"name": "x", "shared": "x", "base_type": "str"}]}),
        "2.10-3", "properties", "x",
    )
    # A null field reads as absent, so a shared slot with nulled local fields is legal.
    seed(registry, "x", kind="property", attributes={"base_type": "str"})
    ok = _write(registry, "b", {"properties": [{"name": "x", "shared": "x", "base_type": None, "description": None}]})
    assert isinstance(ok, TypeEntry), ok
    # Missing, empty and whitespace-only descriptions are one thing (row 8b finding 3).
    for description in (None, "", "   "):
        slot = {"name": "y", "base_type": "str"}
        if description is not None:
            slot["description"] = description
        _refused(_propose(registry, "c", {"properties": [slot]}), "2.10-3", "properties", "y")


def test_c21_03_a_blank_description_on_a_shared_slot_is_a_missing_one(registry):
    """Round 1, lens A finding 3: a blank description is missing at every door, so a
    shared slot carrying "" or whitespace carries nothing and is not refused."""
    seed(registry, "ccn", kind="property", attributes={"base_type": "str"})
    for blank in ("", "   "):
        out = _write(registry, f"site{len(blank)}", {"properties": [
            {"name": "ccn", "shared": "ccn", "description": blank}]})
        assert isinstance(out, TypeEntry), out
    back = registry.import_types([{"name": "site9", "definition": "a site", "status": "active",
                                   "attributes": {"properties": [{"name": "ccn", "shared": "ccn", "description": ""}]}}])
    assert not [w for w in back[0].warnings if w.startswith("import_refused")], back[0].warnings


def test_c21_03_a_missing_description_is_not_a_breach_to_the_view(registry):
    entry = _entry(registry, "entity", {"properties": [{"name": "y", "base_type": "str", "description": ""}]})
    view = entity_declaration(entry, _AllCaps())
    assert view.properties == (PropertySpec(name="y", base_type="str"),)
    assert view.why_absent == {}


# ------------------------------------------------------------------- rule 2.10-4


def test_c21_04_slot_names_are_unique_and_mixed_case(registry):
    ok = _write(registry, "employee", {"properties": [_local("fullName"), _local("employee_id")]})
    assert isinstance(ok, TypeEntry), ok
    _refused(_propose(registry, "a", {"properties": [_local("x"), _local("x")]}), "2.10-4", "properties", "x")
    _refused(_propose(registry, "a", {"properties": [_local("1x")]}), "2.10-4")
    _refused(_propose(registry, "a", {"properties": [_local("City/Town")]}), "2.10-4")


# ------------------------------------------------------------------- rule 2.10-5


def test_c21_05_key_and_title_name_declared_slots_and_a_key_slot_is_required(registry):
    _refused(_propose(registry, "a", {"properties": [_local("x")], "primary_key": ["y"]}), "2.10-5", "primary_key", "y")
    _refused(_propose(registry, "a", {"properties": [_local("x")], "title_property": "y"}), "2.10-5", "title_property")
    _refused(
        _propose(registry, "a", {"properties": [_local("x", required=False)], "primary_key": ["x"]}),
        "2.10-5", "primary_key", "x",
    )
    entry = _write(registry, "survey", {
        "properties": [_local("ccn"), _local("survey_date", "date"), _local("note", required=False)],
        "primary_key": ["ccn", "survey_date"],
    })
    assert isinstance(entry, TypeEntry), entry
    view = entity_declaration(entry, registry.caps)
    if registry.caps.stores_attribute("properties"):
        required = {p.name: p.required for p in view.properties}
        assert required == {"ccn": True, "survey_date": True, "note": False}


def test_c21_05_a_duplicate_key_slot_among_declared_slots_is_rule_2_10_5(registry):
    """Round 2, lens A finding 4: with slots declared, distinct key slots are 2.10-5's."""
    _refused(
        _propose(registry, "a", {"properties": [_local("x")], "primary_key": ["x", "x"]}),
        "2.10-5", "primary_key",
    )
    _refused(_propose(registry, "a", {"primary_key": ["x", "x"]}), "2.10-1", "primary_key")


def test_c21_05_an_unhashable_key_beside_slots_is_refused_never_raised(registry):
    """Round 3, lens A finding 1: a list or dict where a key name belongs is rule
    2.10-1's refusal at every door, and one such row never fails an import."""
    slots = [_local("ccn")]
    _refused(_propose(registry, "a", {"properties": slots, "title_property": ["ccn"]}), "2.10-1", "title_property")
    _refused(_propose(registry, "a", {"properties": slots, "primary_key": [["ccn"]]}), "2.10-1", "primary_key")
    _refused(_propose(registry, "a", {"properties": slots, "primary_key": [{}]}), "2.10-1", "primary_key")
    # A properties value that is not a list is not "present" (round 3, lens A finding 2).
    _refused(_propose(registry, "a", {"properties": "x", "primary_key": ["a", "a"]}), "2.10-1", "primary_key")
    rows = [
        {"name": "good_one", "definition": "fine", "status": "active"},
        {"name": "bad_one", "definition": "bad", "status": "active",
         "attributes": {"properties": slots, "title_property": ["ccn"]}},
    ]
    out = _import(registry, rows, namespace="c21_05_u")
    assert [e.name for e in out] == ["good_one", "bad_one"]
    assert out[0].warnings == ()
    assert out[1].warnings == ("import_refused:attributes_schema_violation",)
    assert registry.adapter.get_type("c21_05_u", "bad_one", kind="entity") is None


def test_c21_05_a_breach_in_stored_data_nulls_the_key_never_the_slots(registry):
    entry = _entry(registry, "entity", {"properties": [_local("x")], "primary_key": ["y"], "title_property": "z"})
    view = entity_declaration(entry, _AllCaps())
    assert [p.name for p in view.properties] == ["x"]
    assert view.primary_key is None and view.title_property is None
    assert view.why_absent == {"primary_key": "breaches:2.10-5", "title_property": "breaches:2.10-5"}
    with pytest.raises(ValueError):
        entity_declaration(dataclasses.replace(entry, kind="predicate"), _AllCaps())


# ------------------------------------------------------------------- rule 2.10-6


def test_c21_06_item_type_with_list_and_opaque_says_what_it_holds(registry):
    _refused(_propose(registry, "a", {"properties": [_local("x", "list")]}), "2.10-6")
    _refused(_propose(registry, "a", {"properties": [_local("x", "list", item_type="list")]}), "2.10-6")
    _refused(_propose(registry, "a", {"properties": [_local("x", "str", item_type="str")]}), "2.10-6")
    _refused(_propose(registry, "a", {"properties": [_local("x", "opaque")]}), "2.10-6")
    _refused(_propose(registry, "a", {"properties": [_local("x", "list", item_type="opaque")]}), "2.10-6")
    ok = _write(registry, "b", {"properties": [
        _local("loc", "opaque", source_type="geopoint"),
        _local("tags", "list", item_type="str"),
    ]})
    assert isinstance(ok, TypeEntry), ok
    assert set(BASE_TYPES) == {"str", "int", "float", "decimal", "bool", "date", "datetime", "list", "dict", "opaque"}


# ------------------------------------------------------------------- rule 2.10-7


def test_c21_07_a_value_set_only_on_an_enumerable_type(registry):
    seed(registry, "flags", kind="value_set")
    _refused(_propose(registry, "a", {"properties": [_local("x", "bool", value_set="flags")]}), "2.10-7")
    _refused(_propose(registry, "a", {"properties": [_local("x", "list", item_type="float", value_set="flags")]}), "2.10-7")
    ok = _write(registry, "b", {"properties": [_local("x", "list", item_type="str", value_set="flags")]})
    assert isinstance(ok, TypeEntry), ok
    assert _prop_warnings(ok) == []


# ------------------------------------------------------------------- rule 2.10-8


def test_c21_08_references_are_bare_canonical_words(registry):
    for word in ("fooSpt", "zip__code", "zip_code_", "dot:latitude", "has space"):
        _refused(_propose(registry, "a", {"properties": [{"name": "x", "shared": word}]}), "2.10-8", "properties", "x")
        _refused(_propose(registry, "a", {"properties": [_local("x", value_set=word)]}), "2.10-8")


# ------------------------------------------------------------------- rule 2.10-9


def test_c21_09_a_property_entry_declares_nothing_or_a_base_type(registry):
    bare = seed(registry, "latitude", kind="property")
    assert isinstance(bare, TypeEntry)
    typed = seed(registry, "zip_code", kind="property", attributes={"base_type": "str", "display_name": "ZIP"})
    view = shared_property_declaration(typed, registry.caps)
    if registry.caps.stores_attribute("base_type"):
        assert view.base_type == "str" and view.why_absent == {}
    else:
        assert view.base_type is None and view.why_absent["base_type"] == "not_stored"
    _refused(_propose(registry, "a", {"display_name": "A"}, kind="property"), "2.10-9")
    _refused(_propose(registry, "a", {"base_type": "str", "required": True}, kind="property"), "2.10-9", "required")
    # detail.key names the offending key itself on a property entry (round 1, A4).
    _refused(_propose(registry, "a", {"base_type": "list"}, kind="property"), "2.10-6", "item_type")
    _refused(_propose(registry, "a", {"base_type": "opaque"}, kind="property"), "2.10-6", "source_type")
    _refused(_propose(registry, "a", {"base_type": "float", "value_set": "v"}, kind="property"), "2.10-7", "value_set")
    _refused(_propose(registry, "a", {"base_type": "str", "value_set": "V"}, kind="property"), "2.10-8", "value_set")
    with pytest.raises(ValueError):
        shared_property_declaration(dataclasses.replace(bare, kind="entity"), registry.caps)


def test_c21_09_a_breach_in_stored_data_nulls_every_reserved_key(registry):
    entry = _entry(registry, "property", {"base_type": "str", "required": True, "display_name": "Z"}, name="zz")
    view = shared_property_declaration(entry, _AllCaps())
    assert view == SharedPropertyDeclaration(None, None, None, None, None, {"base_type": "breaches:2.10-9"})


# ------------------------------------------------------------------ rule 2.10-10


def test_c21_10_a_reference_is_written_and_warned_never_refused(registry):
    out = _write(registry, "employee", {"properties": [
        {"name": "fullName", "shared": "foo_spt"},
        _local("dept", value_set="departments"),
    ]})
    assert isinstance(out, TypeEntry), out
    assert set(_prop_warnings(out)) == {
        "property_reference_unregistered:fullName:foo_spt",
        "property_reference_unregistered:dept:departments",
    }

    seed(registry, "foo_spt", kind="property", attributes={"base_type": "str"})
    seed(registry, "departments", kind="value_set")
    found = _write(registry, "office", {"properties": [{"name": "name", "shared": "foo_spt"}, _local("d", value_set="departments")]})
    assert _prop_warnings(found) == []

    # A property entry's own value set is labelled `*`.
    star = _write(registry, "dept_code", {"base_type": "str", "value_set": "nope"}, kind="property")
    assert _prop_warnings(star) == ["property_reference_unregistered:*:nope"]


def test_c21_10_undeclared_reads_the_view(registry):
    seed(registry, "bare", kind="property")
    out = _write(registry, "a", {"properties": [{"name": "x", "shared": "bare"}]})
    if registry.caps.stores_attribute("base_type"):
        assert _prop_warnings(out) == ["property_reference_undeclared:x:bare"]
    else:
        # not stored is 2.10-16's, and saying "undeclared" would be false (Rule U).
        assert _prop_warnings(out) == []


@pytest.mark.requires_capability("stores_proposals")
def test_c21_10_approve_recomputes_the_warnings(registry):
    pending = _propose(registry, "a", {"properties": [{"name": "x", "shared": "later"}]})
    assert "property_reference_unregistered:x:later" in pending.warnings
    seed(registry, "later", kind="property", attributes={"base_type": "int"})
    entry = registry.approve(pending.id, "user:sd")
    assert isinstance(entry, TypeEntry), entry
    assert _prop_warnings(entry) == []


@pytest.mark.requires_capability("stores_events")
def test_c21_10_retired_and_redirected(registry):
    seed(registry, "zip_code", kind="property", attributes={"base_type": "str"})
    seed(registry, "postal_code", kind="property", attributes={"base_type": "str"})
    seed(registry, "old_code", kind="property", attributes={"base_type": "str"})
    # force=True: the identity guard is not this test's subject, and a backend that
    # declines indexes_membership refuses it unforced (no_consumer_evidence).
    assert not isinstance(
        registry.retire("zip_code", "renamed", retired_by="user:sd", successor="postal_code", force=True),
        Refusal,
    )
    assert not isinstance(registry.retire("old_code", "gone", retired_by="user:sd", force=True), Refusal)
    out = _write(registry, "a", {"properties": [{"name": "z", "shared": "zip_code"}, {"name": "o", "shared": "old_code"}]})
    assert set(_prop_warnings(out)) == {
        "property_reference_redirected:z:zip_code:postal_code",
        "property_reference_retired:o:old_code",
    }


def test_c21_10_a_scan_that_cannot_finish_is_unknown_never_absent(adapter, make_registry):
    full = make_registry(adapter)
    for i in range(6):
        seed(full, f"p{i}", kind="property", attributes={"base_type": "str"})
    capped = make_registry(DegradedAdapter(adapter, page_cap=2))
    out = _write(capped, "a", {"properties": [{"name": "x", "shared": "missing"}]})
    assert _prop_warnings(out) == ["property_reference_unknown:x:missing"], out.warnings


# ------------------------------------------------------------------ rule 2.10-11


def test_c21_11_the_reader_stays_in_its_kind_and_reads_name_or_alias_spellings(registry):
    # An alias held by an entry of ANOTHER kind is not a property (row 8b finding 1).
    seed(registry, "grid", kind="value_set")
    registry.import_types(
        [{"name": "severity", "kind": "property", "definition": "a property", "aliases": ["scope_severity_grid"],
          "attributes": {"base_type": "str"}}],
        system="c21", namespace="default", imported_by="import:c21",
    )
    out = _write(registry, "a", {"properties": [_local("s", value_set="scope_severity_grid")]})
    assert _prop_warnings(out) == ["property_reference_unregistered:s:scope_severity_grid"]
    # A live row whose NAME is another spelling of the word (UC3's `borough_`).
    seed(registry, "borough_", kind="property", attributes={"base_type": "str"})
    out = _write(registry, "b", {"properties": [{"name": "b", "shared": "borough"}]})
    assert _prop_warnings(out) == ["property_reference_redirected:b:borough:borough_"]


@pytest.mark.requires_capability("stores_events", "stores_aliases")
def test_c21_11_a_dead_end_falls_through_to_a_live_alias_holder(registry):
    """Row 8b finding 2: the reader must not say *retired* while resolve_type answers
    the alias holder at 1.0."""
    seed(registry, "zip_code", kind="property", attributes={"base_type": "str"})
    seed(registry, "postal_code", kind="property", attributes={"base_type": "str"})
    registry.retire("zip_code", "renamed", retired_by="user:sd", successor="postal_code", force=True)
    registry.retire("postal_code", "gone", retired_by="user:sd", force=True)
    registry.import_types(
        [{"name": "post_code", "kind": "property", "definition": "a post code", "aliases": ["zip_code"],
          "attributes": {"base_type": "str"}}],
        system="c21", namespace="default", imported_by="import:c21",
    )
    out = _write(registry, "a", {"properties": [{"name": "z", "shared": "zip_code"}]})
    assert _prop_warnings(out) == ["property_reference_redirected:z:zip_code:post_code"]
    res = registry.resolve_type("zip_code", CTX, kind="property", tier="unspecified")
    assert res.type is not None and res.type.name == "post_code"


@pytest.mark.requires_capability("stores_events")
def test_c21_11_the_reader_never_crosses_a_namespace(registry):
    seed(registry, "latitude", kind="property", namespace="dot", attributes={"base_type": "float"})
    out = _write(registry, "street_tree", {"properties": [{"name": "latitude", "shared": "latitude"}]}, namespace="dpr")
    assert _prop_warnings(out) == ["property_reference_unregistered:latitude:latitude"]


# ------------------------------------------------------------------ rule 2.10-12


def test_c21_12_resolve_type_with_kind_property(registry):
    res = registry.resolve_type("latitude", CTX, kind="property", tier="unspecified")
    assert res.outcome == "proposal" and res.proposal.kind == "property"
    seed(registry, "latitude", kind="property", attributes={"base_type": "float"})
    res = registry.resolve_type("latitude", CTX, kind="property", tier="unspecified")
    assert res.outcome == "existing" and res.type.name == "latitude" and res.confidence == 1.0
    # The not_a_type check runs before `kind` is read, so CMS's Location stays one.
    loc = registry.resolve_type("location", LOCATION_CTX, kind="property", tier="opus")
    assert loc.outcome == "not_a_type" and loc.reason == "redundant_projection", loc


# ------------------------------------------------------------------ rule 2.10-15


def test_c21_13_kind_blind_guards_apply_to_properties(registry):
    first = seed(registry, "zip_code", kind="property", attributes={"base_type": "str"})
    again = _propose(registry, "zip_code", {"base_type": "str"}, kind="property")
    assert isinstance(again, TypeEntry) and again.name == first.name
    seed(registry, "zip_pred", kind="predicate")
    # merge_types takes no kind, so the word must be unambiguous: one property, one entity.
    seed(registry, "zip_entity", kind="entity")
    into_entity = registry.merge_types("zip_code", "zip_entity", "same", merged_by="user:sd")
    assert isinstance(into_entity, Refusal) and into_entity.reason == "kind_mismatch", into_entity
    into_pred = registry.merge_types("zip_code", "zip_pred", "same", merged_by="user:sd")
    assert isinstance(into_pred, Refusal) and into_pred.reason == "predicate_merge", into_pred
    seed(registry, "zip_code", kind="property", namespace="other", attributes={"base_type": "str"})
    across = registry.merge_types("zip_code", "zip_code", "same", merged_by="user:sd", into_namespace="other")
    assert isinstance(across, Refusal) and across.reason == "cross_namespace_merge", across


# ------------------------------------------------------------------ rule 2.10-16


def test_c21_14_a_key_the_backend_cannot_store_is_warned_and_named_not_stored(registry):
    attrs = {"properties": [_local("ccn")], "primary_key": ["ccn"], "title_property": "ccn"}
    out = _write(registry, "facility", attrs)
    assert isinstance(out, TypeEntry), out
    expected = sorted(
        f"property_declaration_not_stored:{k}" for k in attrs if not registry.caps.stores_attribute(k)
    )
    assert _not_stored_warnings(out) == expected
    stored = registry.adapter.get_type("default", "facility", kind="entity")
    view = entity_declaration(stored, registry.caps)
    assert view.why_absent == _not_stored(registry.caps, attrs)
    if registry.caps.stores_attribute("primary_key"):
        assert view.primary_key == ("ccn",)


def test_c21_14_a_degraded_backend_says_what_it_drops(adapter, make_registry):
    reg = make_registry(DegradedAdapter(adapter, stores_attributes=False))
    out = _write(reg, "zip_code", {"base_type": "str"}, kind="property")
    assert "property_declaration_not_stored:base_type" in out.warnings
    view = shared_property_declaration(out, reg.caps)
    assert view.why_absent.get("base_type") == "not_stored"


def test_c21_14_a_dropped_base_type_is_never_read_as_a_breach(adapter, make_registry):
    """Round 2, lens A finding 1: a display_name whose base_type the backend dropped
    is not_stored, never breaches:2.10-9."""
    reg = make_registry(DegradedAdapter(adapter, stores_attributes=False, attribute_projections={"display_name"}))
    out = _write(reg, "zip_code", {"base_type": "str", "display_name": "Zip"}, kind="property")
    assert "property_declaration_not_stored:base_type" in out.warnings
    stored = reg.adapter.get_type("default", "zip_code", kind="property")
    view = shared_property_declaration(stored, reg.caps)
    assert view.why_absent.get("base_type") == "not_stored", view.why_absent
    assert not any(v.startswith("breaches:") for v in view.why_absent.values()), view.why_absent


def test_c21_14_a_reference_the_backend_drops_is_still_warned(adapter, make_registry):
    """Round 2, lens A finding 3: the warning describes what the caller declared, and
    not_stored says apart that it was not kept (rule 2.10-10)."""
    reg = make_registry(DegradedAdapter(adapter, stores_attributes=False))
    out = _write(reg, "employee", {"properties": [
        {"name": "fullName", "shared": "foo_spt"}, _local("dept", value_set="departments"),
    ]})
    assert isinstance(out, TypeEntry), out
    assert "property_declaration_not_stored:properties" in out.warnings
    assert set(_prop_warnings(out)) == {
        "property_reference_unregistered:fullName:foo_spt",
        "property_reference_unregistered:dept:departments",
    }
    star = _write(reg, "dept_code", {"base_type": "str", "value_set": "nope"}, kind="property")
    assert "property_declaration_not_stored:value_set" in star.warnings
    assert _prop_warnings(star) == ["property_reference_unregistered:*:nope"]


# ------------------------------------------------------------------ rule 2.10-22


@pytest.mark.requires_capability("indexes_membership")
def test_c21_15_property_is_a_kind_and_never_a_predicate(registry):
    assert "property" in types_module.KINDS
    assert "property" not in PROPOSABLE_KINDS
    seed(registry, "geo", kind="predicate")
    member = seed(registry, "latitude", kind="property", predicates=["geo"], attributes={"base_type": "float"})
    assert "geo" in member.predicates
    refused = registry.merge_types("latitude", "geo", "same", merged_by="user:sd")
    assert isinstance(refused, Refusal) and refused.reason == "predicate_merge", refused


# ------------------------------------------------------------- design tests, row 8c


def test_c21_16_uc2_cms_twenty_one_columns_through_real_calls(registry):
    caps = registry.caps
    for vs in ("scope_severity_code", "deficiency_corrected_status"):
        assert _prop_warnings(seed(registry, vs, kind="value_set")) == []
    ccn = _write(registry, "ccn", {"base_type": "str", "display_name": "CMS Certification Number (CCN)"}, kind="property")
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
        entry = _write(registry, name, attrs)
        assert isinstance(entry, TypeEntry), (name, entry)
        not_stored = sorted(f"property_declaration_not_stored:{k}" for k in attrs if not caps.stores_attribute(k))
        assert _not_stored_warnings(entry) == not_stored and _prop_warnings(entry) == [], entry.warnings
        view = entity_declaration(registry.adapter.get_type("default", name, kind="entity"), caps)
        # Every key the backend cannot keep, declared or not: it cannot know which.
        assert view.why_absent == _not_stored(caps, ("properties", "primary_key", "title_property"))
        if view.properties is not None:
            slots += len(view.properties)
    if caps.stores_attribute("properties"):
        assert slots == 22  # 21 columns, `ccn` used twice through one entry
    for column, ctx, reason in (("location", LOCATION_CTX, "redundant_projection"),
                                ("processing_date", PROCESSING_CTX, "export_artefact")):
        res = registry.resolve_type(column, ctx, tier="opus")
        assert res.outcome == "not_a_type" and res.reason == reason, res


@pytest.mark.requires_capability("stores_events")
def test_c21_17_uc3_nyc_status_stays_three_things_and_coordinates_are_properties(registry):
    for ns in ("dpr", "oti_311", "dot"):
        seed(registry, "status", kind="value_set", namespace=ns)
    seed(registry, "latitude", kind="property", namespace="dot", attributes={"base_type": "float"})
    seed(registry, "longitude", kind="property", namespace="dot", attributes={"base_type": "float"})
    for ns, entity in (("dpr", "street_tree"), ("oti_311", "service_request"), ("dot", "parking_meter")):
        out = _write(registry, entity, {"properties": [_local("status", value_set="status")]}, namespace=ns)
        assert _prop_warnings(out) == [], out.warnings
    dot = _write(registry, "sign", {"properties": [{"name": "latitude", "shared": "latitude"},
                                                    {"name": "longitude", "shared": "longitude"}]}, namespace="dot")
    assert _prop_warnings(dot) == []
    res = registry.resolve_type("latitude", CTX, kind="property", namespace="dot", tier="unspecified")
    assert res.outcome == "existing" and res.confidence == 1.0
    res = registry.resolve_type("latitude", CTX, kind="property", namespace="dpr", tier="unspecified")
    assert res.outcome == "proposal" and res.proposal.kind == "property"
    # 8C-RUN.md 0.4 UC3 items 2 and 3 through a write, not only through resolve_type
    # (round 1, lens C finding 1): the reader never crosses a namespace.
    tree = _write(registry, "tree_pit", {"properties": [{"name": "latitude", "shared": "latitude"}]}, namespace="dpr")
    assert _prop_warnings(tree) == ["property_reference_unregistered:latitude:latitude"], tree.warnings
    seed(registry, "borough", kind="value_set", namespace="dot")
    pit = _write(registry, "pit", {"properties": [_local("borough", value_set="borough")]}, namespace="dpr")
    assert _prop_warnings(pit) == ["property_reference_unregistered:borough:borough"], pit.warnings
    merged = registry.merge_types("status", "status", "same", merged_by="user:sd", namespace="dpr", into_namespace="dot")
    assert isinstance(merged, Refusal) and merged.reason == "cross_namespace_merge", merged
