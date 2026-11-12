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
from ontoloche.types import Evidence, MergeResult, Refusal, ResolveContext, TypeEntry  # noqa: E402

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
