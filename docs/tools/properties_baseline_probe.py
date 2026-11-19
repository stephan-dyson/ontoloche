"""Row 8b's baseline probe: what the SHIPPED registry does today at the doors a
``kind="property"`` entry would open (8B-RUN.md §0.4).

Row 8b is a spec row and ships no product code. This probe changes nothing in the
package. It observes the current behaviour that the amendment's open doors (D2, D6,
D7, D9) and contortion 10 are claims about, so those claims rest on output rather than
on reading. Run: ``py docs/tools/properties_baseline_probe.py`` from the repo root.

Row 8c built 2.10 and kept rules 2.10-17 to 2.10-21 as today's behaviour, because they
are reserved for founder questions Q103 to Q106 (8C-RUN.md §0.2 item 8). Those rules are
pinned here rather than by a contract id, since a contract id is what a third-party
backend certifies. ``--assert`` exits 1 when any line in ``RESERVED`` prints a value other
than the one recorded, so a change to reserved behaviour fails loudly instead of quietly.
Row 8c also made the D7 and D9 seeds legal declarations: the old seeds named a slot with
no ``base_type``, which rule 2.10-3 now refuses, so D7 had stopped measuring 2.10-20.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ontoloche import Registry  # noqa: E402
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.backends.sqlite_minimal import MinimalSQLiteAdapter  # noqa: E402
from ontoloche.types import Consumer, Evidence, MergeResult, Refusal, ResolveContext, TypeEntry  # noqa: E402

EVIDENCE = [Evidence(kind="human", summary="seeded by row 8b's baseline probe")]


def seed(reg, name, *, kind="entity", attributes=None, ns="default"):
    out = reg.propose_type(
        name, f"{name}, seeded by row 8b's baseline probe", EVIDENCE, "user:sd",
        kind=kind, namespace=ns, attributes=attributes,
    )
    if isinstance(out, (TypeEntry, Refusal)):
        return out
    return reg.approve(out.id, "user:sd")


#: The reserved-rule lines and the value each prints today (row 8c). The rule each pins
#: is the comment. Every other line is printed for the record and is not asserted.
RESERVED = {
    # 2.10-17: collapsing two differing properties or value sets.
    "D2 merge, no acknowledgement": "definitions_diverge",
    "D2 merge, acknowledged": "MergeResult",
    "D2 retire(successor=), no acknowledgement": "retired",
    "D12 alias import over a retired property, warnings": "()",
    "D12 postal_code now": "{'base_type': 'int'}",
    "D13 retire a referenced value set": "retired",
    "D13 warnings": "()",
    # D14 (row 8d): warned, and the default in force pinned (DECISIONS-OPEN item 35).
    "D14 alias import over a tombstone with successor": "('alias_word_succeeded:zip_code:postal_code',)",
    "D14 live alias holders of zip_code": "['post_code']",
    "D14 reinstate zip_code": "successor_active",
    # 2.10-18: collapsing two entities whose declarations contradict.
    "D11 retire(survey, successor=citation)": "retired",
    "D11 warnings": "()",
    "D12 alias import over a retired entity, warnings": "()",
    # 2.10-19: retiring a property a slot still names; the predicate-member exception.
    "D6 retire a used shared property": "retired",
    "D6 warnings": "()",
    "D10 retire a property a consumer gates on": "live_consumers",
    # 2.10-20: an import replaces an active entry's whole attributes.
    "D7 active entity attributes after re-import": "{'properties': []}",
    "D7b property attributes after re-import": "{'base_type': 'int'}",
    "D7b warnings": "()",
    # 2.10-21: an undescribed local slot at import is written, no warning; a shared
    # property entry with no definition is held by R109.
    "Q106 import an undescribed local slot": "written",
    "Q106 warnings": "()",
    "Q106 import a property entry with no definition": "import_refused:definition_missing",
}

SEEN: dict[str, str] = {}


def show(label, value):
    SEEN[label] = str(value)
    print(f"{label:<48} {value}")


def main(argv: list[str] | None = None) -> int:
    check = "--assert" in (sys.argv[1:] if argv is None else argv)
    # Contortion 10: latitude, asked with no kind and with kind="property".
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "street_tree", ns="dot")
    ctx = ResolveContext(
        definition_hint="WGS84 latitude of the asset", sample_values=[40.71],
        source="693u-uax6#latitude", sibling_columns=["longitude", "location"],
        proposed_by="user:sd",
    )
    for kind in (None, "property"):
        r = reg.resolve_type("latitude", ctx, kind=kind, namespace="dot", tier="opus")
        pk = r.proposal.kind if r.proposal else None
        show(f"C10 resolve_type(latitude, kind={kind!r})", f"outcome={r.outcome} proposal.kind={pk}")

    # D7: does import_types rewrite an ACTIVE entity's attributes?
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "facility", attributes={"primary_key": ["ccn"], "properties": [
        {"name": "ccn", "base_type": "str", "description": "the CMS certification number"}]})
    reg.import_types([{"name": "facility", "definition": "facility, re-imported",
                       "status": "active", "attributes": {"properties": []}}])
    after = reg.list_types().types
    attrs = next(t.attributes for t in after if t.name == "facility")
    show("D7 active entity attributes after re-import", attrs)

    # D9: what survives on sqlite_minimal, UC1's declared shape.
    import tempfile
    store = str(Path(tempfile.mkdtemp(prefix="oo8b-")) / "host.db")
    MinimalSQLiteAdapter.create_host_schema(store)
    reg = Registry(MinimalSQLiteAdapter(store))
    e = seed(reg, "facility", attributes={"primary_key": ["ccn"], "properties": [
        {"name": "ccn", "base_type": "str", "description": "the CMS certification number"},
        {"name": "provider_name", "base_type": "str", "description": "the provider's name"}],
        "title_property": "provider_name"})
    show("D9 sqlite_minimal attributes after write", getattr(e, "attributes", e))
    show("D9 sqlite_minimal warnings", getattr(e, "warnings", None))

    # D2: two kind="property" entries with different base types, merged.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "zip_code", kind="property", attributes={"base_type": "str"})
    seed(reg, "postal_code", kind="property", attributes={"base_type": "int"})
    out = reg.merge_types("zip_code", "postal_code", "duplicate", merged_by="user:sd")
    show("D2 merge, no acknowledgement", getattr(out, "reason", type(out).__name__))
    out = reg.merge_types("zip_code", "postal_code", "duplicate", merged_by="user:sd",
                          acknowledge=["no_consumer_evidence", "definitions_diverge"])
    show("D2 merge, acknowledged", type(out).__name__ if isinstance(out, MergeResult)
         else out.reason)

    # D6: retiring a kind="property" entry an active entity names.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "latitude", kind="property", attributes={"base_type": "float"})
    seed(reg, "street_tree", attributes={"properties": [{"name": "latitude",
                                                         "shared": "latitude"}]})
    out = reg.retire("latitude", "no longer wanted", retired_by="user:sd")
    show("D6 retire a used shared property", getattr(out, "status", None) or out.reason)
    show("D6 warnings", getattr(out, "warnings", None))

    # D2 at the second collapsing door: retire(successor=), no acknowledgement.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "zip_code", kind="property", attributes={"base_type": "str"})
    seed(reg, "postal_code", kind="property", attributes={"base_type": "int"})
    out = reg.retire("zip_code", "duplicate", retired_by="user:sd", successor="postal_code")
    show("D2 retire(successor=), no acknowledgement", getattr(out, "status", None) or out.reason)

    # D11: two ENTITIES whose declarations contradict, collapsed by retire(successor=).
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "survey", attributes={"primary_key": ["ccn", "survey_date", "survey_type"]})
    seed(reg, "citation")
    out = reg.retire("survey", "duplicate", retired_by="user:sd", successor="citation")
    show("D11 retire(survey, successor=citation)", getattr(out, "status", None) or out.reason)
    show("D11 warnings", getattr(out, "warnings", None))

    # D7b: re-importing an ACTIVE kind="property" entry with a different base type.
    reg = Registry(SQLiteAdapter(":memory:"))
    reg.import_types([{"name": "foo_spt", "definition": "a foo", "status": "active",
                       "attributes": {"base_type": "str"}}], kind="property")
    back = reg.import_types([{"name": "foo_spt", "definition": "a foo", "status": "active",
                              "attributes": {"base_type": "int"}}], kind="property")
    stored = next(t.attributes for t in reg.list_types(kind="property").types)
    show("D7b property attributes after re-import", stored)
    show("D7b warnings", back[0].warnings if back else None)

    # D10: a property carrying a predicate that a consumer gates on.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "searchable", kind="predicate")
    out = reg.propose_type("latitude", "latitude, seeded by row 8b's baseline probe", EVIDENCE,
                           "user:sd", kind="property", predicates=["searchable"],
                           attributes={"base_type": "float"})
    if not isinstance(out, (TypeEntry, Refusal)):
        reg.approve(out.id, "user:sd")
    from datetime import datetime, timezone
    reg.register_consumer(Consumer(id="search.index", gate="searchable", on_unknown="drop",
                                   owner=None, registered_at=datetime.now(timezone.utc),
                                   locator=None))
    out = reg.retire("latitude", "no longer wanted", retired_by="user:sd")
    show("D10 retire a property a consumer gates on", getattr(out, "status", None) or out.reason)

    # D12: the import alias write as a third collapsing door, after a plain retire.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "zip_code", kind="property", attributes={"base_type": "str"})
    reg.retire("zip_code", "duplicate", retired_by="user:sd")
    back = reg.import_types([{"name": "postal_code", "definition": "a postal code",
                              "status": "active", "aliases": ["zip_code"],
                              "attributes": {"base_type": "int"}}], kind="property")
    show("D12 alias import over a retired property, warnings", back[0].warnings if back else None)
    stored = {t.name: t.attributes for t in reg.list_types(kind="property").types}
    show("D12 postal_code now", stored.get("postal_code"))
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "survey", attributes={"primary_key": ["ccn", "survey_date", "survey_type"]})
    seed(reg, "citation")
    reg.retire("survey", "duplicate", retired_by="user:sd")
    back = reg.import_types([{"name": "citation", "definition": "a citation", "status": "active",
                              "aliases": ["survey"], "attributes": {"grain": "one per row"}}])
    show("D12 alias import over a retired entity, warnings", back[0].warnings if back else None)

    # D13: a value set a slot references, collapsed by retire(successor=).
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "deficiency_corrected_status", kind="value_set")
    seed(reg, "scope_severity_code", kind="value_set")
    seed(reg, "citation", attributes={"properties": [{
        "name": "correction_status", "base_type": "str", "description": "corrected or not",
        "value_set": "deficiency_corrected_status"}]})
    out = reg.retire("deficiency_corrected_status", "duplicate", retired_by="user:sd",
                     successor="scope_severity_code")
    show("D13 retire a referenced value set", getattr(out, "status", None) or out.reason)
    show("D13 warnings", getattr(out, "warnings", None))

    # D1 and D4, which §1 scored without a run: proposing a retired property's name, which
    # mints nothing and hands back the tombstone (the way back is reinstate),
    # and reading a retired property through resolve_type after a typed collapse.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "zip_code", kind="property", attributes={"base_type": "str"})
    seed(reg, "postal_code", kind="property", attributes={"base_type": "int"})
    reg.retire("zip_code", "duplicate", retired_by="user:sd", successor="postal_code")
    r = reg.resolve_type("zip_code", ctx, kind="property", tier="opus")
    show("D4 resolve retired zip_code (str) -> ", f"{r.outcome} {getattr(r.type, 'name', None)} "
         f"{r.confidence} {getattr(r.type, 'attributes', None)}")
    out = reg.propose_type("zip_code", "a zip code again", EVIDENCE, "user:sd", kind="property",
                           attributes={"base_type": "str"})
    show("D1 propose a retired property's name", f"{getattr(out, 'status', None)} {getattr(out, 'warnings', None)}")

    # D14 (round 4): the import alias write over a tombstone that HAS a successor. Older
    # than row 8b, and the same for every kind: the word ends with two live claimants.
    reg = Registry(SQLiteAdapter(":memory:"))
    seed(reg, "zip_code", kind="property", attributes={"base_type": "str"})
    seed(reg, "postal_code", kind="property", attributes={"base_type": "str"})
    reg.retire("zip_code", "duplicate", retired_by="user:sd", successor="postal_code")
    back = reg.import_types([{"name": "post_code", "definition": "a post code",
                              "status": "active", "aliases": ["zip_code"],
                              "attributes": {"base_type": "int"}}], kind="property")
    show("D14 alias import over a tombstone with successor", back[0].warnings if back else None)
    holders = [t.name for t in reg.list_types(kind="property").types if "zip_code" in (t.aliases or ())]
    show("D14 live alias holders of zip_code", holders)
    out = reg.reinstate("zip_code", "bring it back", reinstated_by="user:sd")
    show("D14 reinstate zip_code", getattr(out, "reason", None) or getattr(out, "status", None))

    # 2.10-21 (Q106), row 8c: what import_types does with a missing description.
    reg = Registry(SQLiteAdapter(":memory:"))
    back = reg.import_types([{"name": "employee", "definition": "an employee", "status": "active",
                              "attributes": {"properties": [{"name": "badge", "base_type": "str"}]}}])
    show("Q106 import an undescribed local slot",
         "written" if back and back[0].kind == "entity" and back[0].name == "employee" else back)
    show("Q106 warnings", tuple(w for w in (back[0].warnings if back else ()) if "description" in w
                                or w.startswith("property_")))
    back = reg.import_types([{"name": "badge_code", "definition": "", "status": "active",
                              "attributes": {"base_type": "str"}}], kind="property")
    reasons = [w for w in (back[0].warnings if back else ()) if w.startswith("import_refused:")]
    show("Q106 import a property entry with no definition", reasons[0] if reasons else back)

    if not check:
        return 0
    drift = {k: (v, SEEN.get(k)) for k, v in RESERVED.items() if SEEN.get(k) != v}
    if drift:
        print()
        print("RESERVED BEHAVIOUR MOVED (rules 2.10-17 to 2.10-21, Q103 to Q106):")
        for label, (want, got) in drift.items():
            print(f"  {label}: recorded {want!r}, now {got!r}")
        return 1
    print()
    print(f"--assert: all {len(RESERVED)} reserved-rule lines print their recorded values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
