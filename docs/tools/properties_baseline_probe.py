"""Row 8b's baseline probe: what the SHIPPED registry does today at the doors a
``kind="property"`` entry would open (8B-RUN.md §0.4).

Row 8b is a spec row and ships no product code. This probe changes nothing in the
package. It observes the current behaviour that the amendment's open doors (D2, D6,
D7, D9) and contortion 10 are claims about, so those claims rest on output rather than
on reading. Run: ``py docs/tools/properties_baseline_probe.py`` from the repo root.
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


def show(label, value):
    print(f"{label:<48} {value}")


def main() -> int:
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
    seed(reg, "facility", attributes={"primary_key": ["ccn"], "properties": [{"name": "ccn"}]})
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
    e = seed(reg, "facility", attributes={"primary_key": ["ccn"],
                                          "properties": [{"name": "ccn"}],
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
