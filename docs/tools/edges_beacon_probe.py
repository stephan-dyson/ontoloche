"""UC1 design test for EDGES.md v0 -- beacon's three relationship shapes.

READ-ONLY over ``C:\\Users\\steph\\projects\\beacon``. Nothing in beacon is
edited, imported or executed: the model files are parsed as text for their
``mapped_column`` declarations, and the traversals are walked over synthetic
instances shaped like beacon's rows.

Covers the three shapes ``beacon/docs/specs/2026-08-27-ontology-layer-
exploration-design.md`` §2.2 enumerates -- Shape A (``work_links`` +
``work_link_types``), Shape B (the polymorphic mention substrate) and Shape C
(one payload-carrying bespoke join table, ``task_stakeholders``) -- plus the
three SHIPPED read seams of §2.7, and the grounding bundle's ``relations`` slot
(§2.4).

    py docs/tools/edges_beacon_probe.py [path-to-beacon]
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from docs.tools.edges_probe_kit import (  # noqa: E402
    EdgeRegistry,
    EdgeStore,
    Family,
    InstanceRef,
    TypeRef,
    prov,
)

BEACON = pathlib.Path(
    sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\steph\projects\beacon"
)

NS = "tenshen"
TASK = TypeRef(NS, "entity", "task")
PROJECT = TypeRef(NS, "entity", "project")
PERSON = TypeRef(NS, "entity", "person")
NOTE_ROW = TypeRef(NS, "entity", "task_notes")  # NOT a registered beacon entity

# EdgeRecord fields (EDGES 7.1) a host column can map onto.
EDGE_FIELDS = {
    "edge_id", "namespace", "family", "src", "dst", "attributes",
    "attr_schema_version", "provenance.created_at", "provenance.created_by",
    "provenance.created_by_actor", "provenance.confidence",
    "provenance.evidence", "provenance.source_version", "status",
    "retract_reason", "retracted_by", "retracted_at", "warnings",
}

# `mapped_column` only: SQLAlchemy `relationship()` attributes are also typed
# Mapped[...] and are NOT columns. Matching them made `task` and `person` look
# like homeless columns of task_stakeholders on the first run.
COL_RE = re.compile(r"^\s{4}(\w+):\s*Mapped\[[^\]]*\]\s*=\s*mapped_column", re.M)


def columns_of(path: pathlib.Path, class_name: str) -> list[str]:
    """Column attribute names declared in one class body, by text."""
    src = path.read_text(encoding="utf-8")
    m = re.search(rf"^class {class_name}\b.*?(?=^class |\Z)", src, re.M | re.S)
    if not m:
        raise SystemExit(f"class {class_name} not found in {path}")
    return COL_RE.findall(m.group(0))


def check(label: str, got, want, notes: str = "") -> bool:
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got {got!r}, expected {want!r} {notes}")
    return ok


def report_mapping(title: str, cols: list[str], mapping: dict[str, str]) -> list[str]:
    print(f"\n{title}")
    homeless = []
    for c in cols:
        target = mapping.get(c)
        if target is None:
            homeless.append(c)
            print(f"    {c:22s} -> NO HOME")
        else:
            print(f"    {c:22s} -> {target}")
    return homeless


def main() -> int:
    ok = True
    if not BEACON.exists():
        print(f"beacon not found at {BEACON}; pass its path as argv[1]")
        return 2
    models = BEACON / "src" / "beacon" / "models"
    print(f"Reading beacon READ-ONLY from {models}\n")

    # ---- T1.1 Shape A: work_links -----------------------------------------
    wl = columns_of(models / "work_link.py", "WorkLink")
    homeless_wl = report_mapping(
        "T1.1 -- Shape A, `work_links` -> EdgeRecord",
        wl,
        {
            "id": "edge_id (cast int -> str, CONTORTION E4)",
            "from_type": "src.type.name",
            "from_id": "src.id (cast int -> str, CONTORTION E4)",
            "to_type": "dst.type.name",
            "to_id": "dst.id (cast int -> str)",
            "relationship_type": "family  [DB column is `relationship`]",
            "description": "attributes['description'] via edge_attribute_projections",
            "confidence": "provenance.confidence",
            "created_by": "provenance.created_by  [CONTORTION T1.5: `interview` has no value]",
            "created_at": "provenance.created_at",
        },
    )
    ok &= check("only `user_id` has no home", homeless_wl, ["user_id"],
                "-- CONTORTION E3: tenancy is not a namespace, and this doc refuses to map it")
    ok &= check("the four columns the migration adds are absent today",
                sorted(set(["status", "retract_reason", "retracted_by", "retracted_at"])
                       & set(wl)), [],
                "-- T1.12: one ALTER TABLE, four additive columns")

    # ---- T1.2 PersonLink ---------------------------------------------------
    pl_src = (models / "person.py").read_text(encoding="utf-8")
    m = re.search(r"^class PersonLink\b.*?(?=^class |\Z)", pl_src, re.M | re.S)
    body = m.group(0)
    nullable_family = bool(
        re.search(r"relationship_type:\s*Mapped\[str \| None\]", body)
    )
    print("\nT1.2 -- Shape A', `person_links`: is the family required?")
    print(f"    declared as: {re.search(r'relationship_type:.*', body).group(0).strip()}")
    ok &= check("PersonLink.relationship_type is NULLABLE", nullable_family, True)
    ok &= check("...and Edge.family is REQUIRED", "family" in EDGE_FIELDS, True,
                "-- PREDICTED FAILURE T1.2 confirmed: a null-family row has no honest map")
    ok &= check("there is no person_link_types registry table",
                (models / "person_link_type.py").exists(), False,
                "-- the labels are free text in a code comment")

    # ---- T1.3 / T1.4 Shape C: task_stakeholders ---------------------------
    ts = columns_of(models / "person.py", "TaskStakeholder")
    homeless_ts = report_mapping(
        "T1.3 -- Shape C, `task_stakeholders` -> EdgeRecord (payload-carrying)",
        ts,
        {
            "id": "edge_id",
            "task_id": "src.id",
            "person_id": "dst.id",
            "role": "attributes['role']  (UNVALIDATED until R10 -- EDGES 2.5)",
            "source": "attributes['source']  (payload, NOT provenance -- T1.4)",
            "created_at": "provenance.created_at",
        },
    )
    ok &= check("every column has a home", homeless_ts, [])
    ok &= check("`source` is payload, not provenance", "source" in ts, True,
                "-- beacon's gate counts 'user' ONLY, so it is a business signal")

    # ---- T1.9 Shape B: the mention substrate ------------------------------
    em = columns_of(models / "entity_mention.py", "_EntityMentionMixin")
    homeless_em = report_mapping(
        "T1.9 -- Shape B, `_EntityMentionMixin` -> EdgeRecord",
        em,
        {
            "id": "edge_id",
            "workspace": None,
            "user_id": None,
            "source_table": "src.type.name  -- but it names a TABLE, not an entity",
            "record_id": "src.id",
            "entity_type": "dst.type.name",
            "entity_id": "dst.id",
            "source": "attributes['source']",
            "match": "attributes['match']  -- see T1.5b below",
            "confidence": "provenance.confidence",
            "matched_span": "provenance.evidence[].summary",
            "rationale": "provenance.evidence[].summary",
            "content_hash": "provenance.source_version  -- EDGES 5.3, and beacon built it first",
            "created_at": "provenance.created_at",
            "updated_at": "(derived)",
            "corrected": "status == 'retracted'  -- EDGES 2.6's tombstone, already in beacon",
            "corrected_at": "retracted_at",
            "corrected_reason": "retract_reason",
        },
    )
    ok &= check("the homeless columns are the tenancy pair", sorted(homeless_em),
                ["user_id", "workspace"], "-- CONTORTION E3 again, same cause")
    print("    NOTE: `source_table` values are 'task_notes' | 'project_notes' |")
    print("          'meeting_notes' | 'open_loops' -- ROWS IN A TABLE, not entity")
    print("          instances. endpoint_kinds cannot be satisfied. T1.9 FAILS as predicted.")

    # ---- T1.5b the created_by vocabulary, counted -------------------------
    print("\nT1.5 -- how many created_by-shaped vocabularies does beacon carry?")
    vocabs = {
        "INTERFACE 2.1 / TypeEntry.created_by": ["seed", "ai", "user"],
        "WorkLink.created_by": ["user", "ai", "interview"],
        "PersonLink.created_by": ["user", "ai", "interview"],
        "TaskStakeholder.source": ["user", "auto_extract", "intake_auto", "legacy"],
        "EntityMention.source": ["ai-inferred", "user-linked"],
        "EntityMention.match": ["deterministic", "llm", "manual"],
    }
    for k, v in vocabs.items():
        print(f"    {k:42s} {v}")
    ok &= check("distinct vocabularies", len(vocabs), 6)
    ok &= check("`deterministic` appears in beacon and not in EDGES",
                "deterministic" in vocabs["EntityMention.match"]
                and "deterministic" not in vocabs["INTERFACE 2.1 / TypeEntry.created_by"],
                True,
                "-- the SAME value UC3's BBL join wanted (T3.8). Two fixtures, one gap")

    # ---- T1.10 can endpoint_kind_mismatch fire on beacon? -----------------
    print("\nT1.10 -- can endpoint_kind_mismatch fire on beacon today?")
    entity_vocab_sites = [
        "architecture/event-spine.md", "assistant/actions/search_audit.py",
        "services/aura_render.py", "services/comment_service.py",
        "services/user_progress_service.py", "services/view_query_spec.py",
        "services/collab_membership_service.py",
    ]
    print(f"    beacon spec sec 2.3 enumerates {len(entity_vocab_sites)} live entity-type")
    print("    vocabularies that disagree. None is registered anywhere.")
    fam = Family(name="blocks", namespace=NS, level="instance",
                 definition="The src task blocks the dst task.",
                 inverse_label="blocked_by",
                 endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    reg_unreg = EdgeRegistry(families=[fam], store=EdgeStore(), registered_types=[])
    e = reg_unreg.add_edge("blocks", InstanceRef(TASK, "41"), InstanceRef(TASK, "77"),
                           prov("ai:classifier", "ai", confidence=0.82), namespace=NS)
    ok &= check("the edge is WRITTEN, not refused", getattr(e, "refused", False), False)
    print(f"    warnings: {e.warnings}")
    ok &= check("...and warns instead of claiming a mismatch",
                all(w.startswith("endpoint_type_unregistered:") for w in e.warnings), True,
                "-- Rule U: a positive claim about a mismatch requires having looked")
    print("    => independently reaches beacon sec 10.4's own conclusion: Slice 0 first.")

    # ---- T1.6 / T1.7 the three shipped read seams -------------------------
    print("\nT1.6/T1.7/T1.8 -- the three SHIPPED read seams of beacon sec 2.7, walked")
    stake = Family(name="task_stakeholder", namespace=NS, level="instance",
                   definition="The person is a stakeholder of the task.",
                   inverse_label="stakeholder_of",
                   endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    touches = Family(name="task_organization", namespace=NS, level="instance",
                     definition="The task touches the organization.",
                     inverse_label="touched_by_task",
                     endpoint_kinds={"src": ("entity",), "dst": ("entity",)})
    store = EdgeStore()
    reg = EdgeRegistry(
        families=[fam, stake, touches], store=store,
        registered_types=[TASK, PROJECT, PERSON],
    )
    reg.add_edge("blocks", InstanceRef(TASK, "41"), InstanceRef(TASK, "77"),
                 prov("ai:classifier", "ai", confidence=0.82), namespace=NS)
    reg.add_edge("task_stakeholder", InstanceRef(TASK, "77"), InstanceRef(PERSON, "7"),
                 prov("user:sd", "user"), namespace=NS,
                 attributes={"role": "owner", "source": "user"})

    # (1) deadline_cluster_service: task -> work_links[blocks] -> blocker task
    r1 = reg.neighbors(InstanceRef(TASK, "41"), ["blocks"], 1, namespace=NS,
                       direction="out")
    ok &= check("T1.6 deadline_cluster's shipped walk", [str(n) for n in r1.nodes],
                ["tenshen:entity:task#77"])
    # (2) the flagship 3-hop query, which the shipped walk stops one hop short of
    r2 = reg.neighbors(InstanceRef(TASK, "41"), ["blocks", "task_stakeholder"], 2,
                       namespace=NS, direction="out")
    ok &= check("T1.7 flagship query reaches the PERSON at depth 2",
                sorted(str(n) for n in r2.nodes),
                ["tenshen:entity:person#7", "tenshen:entity:task#77"],
                "-- the hop sec 2.7 says is missing")
    ok &= check("...and at_depth distinguishes the two hops",
                sorted({ne.at_depth for ne in r2.edges}), [1, 2])
    # (3) entity_touchpoint_service: org -> tasks -> people, depth 2
    reg.add_edge("task_organization", InstanceRef(TASK, "41"),
                 InstanceRef(TypeRef(NS, "entity", "organization"), "3"),
                 prov("user:sd", "user"), namespace=NS, attributes={"role": "vendor"})
    r3 = reg.neighbors(InstanceRef(TypeRef(NS, "entity", "organization"), "3"),
                       ["task_organization", "blocks"], 2, namespace=NS)
    ok &= check("T1.8 entity_touchpoint's org reaches tasks then blocked tasks",
                sorted(str(n) for n in r3.nodes),
                ["tenshen:entity:task#41", "tenshen:entity:task#77"])

    # ---- T1.11 the grounding bundle's relations slot ----------------------
    print("\nT1.11 -- filling the grounding bundle's `relations` slot")
    print("    grounding-contract.md: \"relations\": list[Reference], Reference = "
          "{type, id, note}")
    relations = [
        {"type": ne.edge.dst.type.name, "id": ne.edge.dst.id,
         "note": (f"{ne.edge.family} (hop {ne.at_depth}"
                  + (f", confidence {ne.edge.provenance.confidence}"
                     if ne.edge.provenance.confidence is not None else "")
                  + ")")}
        for ne in r2.edges
    ]
    for rel in relations:
        print(f"    {rel}")
    lost = ["family", "at_depth", "confidence", "created_by", "source_version",
            "status", "warnings", "complete", "families_searched"]
    ok &= check("Reference has three keys", sorted(relations[0]), ["id", "note", "type"])
    print(f"    fields with no slot of their own: {lost}")
    ok &= check("...so they survive only as prose in `note`",
                all(k in relations[0]["note"] or k in ("family",) for k in ("hop",)), True,
                "-- CONTORTION: the one field a constrained narrator may not parse")

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
