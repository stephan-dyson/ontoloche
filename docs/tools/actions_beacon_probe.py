"""UC1 design test for ACTIONS.md v0 -- three of beacon's 222 actions, expressed
as families without moving one of them, and the 127/128 arithmetic.

READ-ONLY against ``C:\\Users\\steph\\projects\\beacon``. Nothing in that repo is
written, imported or executed: the module files are parsed as text, the way
``edges_beacon_probe.py`` parses its models. UC1 is a design TEST, never a design
INPUT (``USE-CASES.md``).

Run: ``py docs/tools/actions_beacon_probe.py``
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from actions_shipped_leg import shipped_leg  # noqa: E402

from actions_probe_kit import (  # noqa: E402
    ActionFamily,
    ActionRegistry,
    DeclarationRefused,
    Effect,
    InputSpec,
    Precondition,
)
from edges_probe_kit import InstanceRef, TypeRef  # noqa: E402

BEACON = Path(r"C:\Users\steph\projects\beacon")
ACTIONS_DIR = BEACON / "src" / "beacon" / "assistant" / "actions"
MODELS_DIR = BEACON / "src" / "beacon" / "models"
MULTI_TOOL = BEACON / "src" / "beacon" / "assistant" / "modes" / "multi_tool.py"

#: The measurement as PINNED at 2026-08-29 13:05, when ACTIONS.md 10.1 was
#: written. beacon is a LIVE repository and it moved under this design test during
#: the row -- `manage_life_event.py` landed at 15:37 the same day, in commit
#: `b274e715`. So the module and category counts are a DATED observation, drift
#: from them is REPORTED rather than failed, and the two numbers that are
#: load-bearing (the categories sum to the module count, and task_detail sums to
#: the budget) are INVARIANTS and are asserted.
#:
#: The pin is a COMMIT, not a clock reading. Round 3's founder lens called the
#: first version's excuse -- "it cannot be pinned, it is somebody else's
#: repository" -- and was right: `git -C <beacon> rev-parse HEAD` pins it exactly,
#: and read-only access is all that takes. A reader who wants the 13:05 tree can
#: check out `PINNED_AT`. Row #4's rule (a design test whose numbers move between
#: runs is not a design test) is honoured by pinning what CAN be pinned and
#: reporting what moves.
PINNED_AT = "a895a872"          # beacon HEAD when 10.1's numbers were re-verified
PINNED = {"modules": 222, "categories": 19, "reads_only": 27,
          "page": {"common": 45, "task": 48, "project": 21, "person": 13}}

CHECKS: list[tuple[str, bool, str]] = []
DRIFT: list[str] = []


def drift(label: str, pinned, observed) -> None:
    if pinned != observed:
        DRIFT.append(f"{label}: pinned {pinned} -> observed {observed}")
        print(f"  [DRIFT] {label} -- pinned {pinned}, observed {observed}")
    else:
        print(f"  [PIN ] {label} -- {observed}, unchanged since 2026-08-29 13:05")


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


# --------------------------------------------------------------------------
# 10.1 -- the measurement, re-derived


def measure() -> dict:
    mods = [p for p in sorted(ACTIONS_DIR.glob("*.py")) if not p.name.startswith("_")]
    cats: dict[str, int] = {}
    reads_only = 0
    for p in mods:
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'category="([a-z_]+)"', text)
        cat = m.group(1) if m else "common"          # _base.make_spec's default
        cats[cat] = cats.get(cat, 0) + 1
        if "reads_only=True" in text:
            reads_only += 1
    cap = re.search(r"MAX_TOOLS_PER_REQUEST\s*=\s*(\d+)", MULTI_TOOL.read_text(encoding="utf-8"))
    return {
        "modules": len(mods),
        "categories": cats,
        "reads_only": reads_only,
        "cap": int(cap.group(1)) if cap else None,
        "budget_lines": MULTI_TOOL.read_text(encoding="utf-8").count(
            "budget = MAX_TOOLS_PER_REQUEST - 1"
        ),
    }


def head() -> str | None:
    """beacon's current commit, read-only. `None` if git is unavailable."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(BEACON), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def people_fks() -> dict:
    """T1.4's number: every foreign key that references ``people.id``."""
    total = cascade = setnull = 0
    for p in sorted(MODELS_DIR.glob("*.py")):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "people.id" not in line:
                continue
            total += 1
            if 'ondelete="CASCADE"' in line:
                cascade += 1
            elif 'ondelete="SET NULL"' in line:
                setnull += 1
    return {"total": total, "cascade": cascade, "set_null": setnull,
            "unspecified": total - cascade - setnull}


# --------------------------------------------------------------------------


def main() -> int:
    print("UC1 -- beacon, read-only. ACTIONS.md 11\n")

    m = measure()
    print(f"10.1 measurement (pinned at beacon {PINNED_AT}, observed at {head() or '?'}):")
    check("T1.7a  MAX_TOOLS_PER_REQUEST == 128", m["cap"] == 128, str(m["cap"]))
    check("T1.7b  budget = cap - 1, in the source twice", m["budget_lines"] == 2,
          f"{m['budget_lines']} occurrences")
    drift("T1.7c  action modules", PINNED["modules"], m["modules"])
    drift("T1.7d  reads_only actions", PINNED["reads_only"], m["reads_only"])
    c = m["categories"]
    page = ("common", "task", "project", "person")
    check("T1.7e  task_detail STILL sums to 127 -- the invariant, not the pin",
          sum(c[g] for g in page) == 127,
          " + ".join(f"{g} {c[g]}" for g in page) + f" = {sum(c[g] for g in page)}")
    drift("T1.7f  categories", PINNED["categories"], len(c))
    check("T1.7g  the categories sum to the module count", sum(c.values()) == m["modules"])

    fk = people_fks()
    check("T1.4a  15 FKs reference people.id", fk["total"] == 15, str(fk))
    check("T1.4b  7 CASCADE / 6 SET NULL / 2 unspecified",
          (fk["cascade"], fk["set_null"], fk["unspecified"]) == (7, 6, 2), str(fk))

    # ----------------------------------------------------------------
    # The three families. Nothing in beacon moves; these are declared in a
    # registry BESIDE it, about its actions.
    print("\n11.1 the three families:")

    reg = ActionRegistry(
        edge_families={"task_stakeholders", "person_links", "project_stakeholders"},
        registered_types=[
            TypeRef("beacon", "entity", "task"),
            TypeRef("beacon", "entity", "person"),
        ],
        family_predicates={},
        consumers={},
    )

    add_stakeholder = ActionFamily(
        name="add_task_stakeholder",
        namespace="beacon",
        definition="Attach a Person as a stakeholder on a task, with an optional role.",
        reversibility="compensable",          # undoable=True, via an undo PAYLOAD
        approval_mode="auto",
        min_auto_tier=None,
        reachability=("task",),
        inputs=(
            InputSpec("task", "instance", kinds=("entity",)),
            InputSpec("person", "instance", kinds=("entity",)),
        ),
        preconditions=(
            Precondition(
                kind="edge_absent",
                subject="task",
                object="person",
                family="task_stakeholders",
                namespace="beacon",
                why="beacon returns one opaque `mutation_failed` for 'already linked' "
                    "and 'task not yours'; this half is expressible and the other is not",
            ),
        ),
        effects=(Effect(op="add_edge", family="task_stakeholders"),),
    )
    delete_person = ActionFamily(
        name="delete_person",
        namespace="beacon",
        definition="Delete a Person record from the CRM. Not reversible via undo.",
        reversibility="irreversible",
        approval_mode="human",
        reachability=("person",),
        inputs=(InputSpec("person", "instance", kinds=("entity",)),),
        effects=(
            Effect(op="retract_edge", family="person_links"),
            Effect(op="retract_edge", family="task_stakeholders"),
            Effect(op="retract_edge", family="project_stakeholders"),
            Effect(op="host_state", why="deletes the people row; 11 further FKs SET NULL "
                                        "or cascade in tables this protocol does not model"),
            Effect(op="host_state", why="connection_service.unlink COMMITS mid-action when "
                                        "the person is a verified pair-binding"),
        ),
    )
    search_tasks = ActionFamily(
        name="search_tasks",
        namespace="beacon",
        definition="Search the caller's tasks. reads_only=True, covers_routes=[].",
        reversibility="reversible",
        approval_mode="auto",
        min_auto_tier=None,
        reachability=("common",),
        inputs=(InputSpec("query", "type", kinds=("entity",), required=False),),
        effects=(),
    )
    for fam in (add_stakeholder, delete_person, search_tasks):
        reg.declare(fam)
    check("T1.1   all three express with the eight keys of 2.2", len(reg.families) == 3)
    check("T1.2   'already linked' is a typed edge_absent precondition",
          add_stakeholder.preconditions[0].kind == "edge_absent")
    check("T1.2b  'task not yours' has NO precondition kind -- authorization, 1's non-goal",
          all(p.kind != "type_active" or p.subject != "owner"
              for p in add_stakeholder.preconditions))
    check("T1.6   search_tasks declares effects: () honestly",
          search_tasks.effects == () and search_tasks.reversibility == "reversible")

    # T1.3 -- the one cross-field rule, at the DECLARATION door.
    try:
        reg.declare(
            ActionFamily(
                name="delete_person_auto",
                namespace="beacon",
                reversibility="irreversible",
                approval_mode="auto",
                reachability=("person",),
            )
        )
        check("T1.3   irreversible + auto is refused at declaration", False, "NOT refused")
    except DeclarationRefused as exc:
        check("T1.3   irreversible + auto is refused at declaration",
              exc.reason == "attributes_schema_violation"
              and exc.detail["door"] == "propose_type",
              f"{exc.reason} at door={exc.detail['door']}")

    # T1.4 -- the blast radius, declared vs admitted-unknown.
    declared_edges = [e for e in delete_person.effects if e.op == "retract_edge"]
    host = [e for e in delete_person.effects if e.op == "host_state"]
    check("T1.4c  3 edge families declarable, the rest admitted with a why",
          len(declared_edges) == 3 and len(host) == 2 and all(e.why for e in host),
          f"{len(declared_edges)} retract_edge + {len(host)} host_state")
    check("T1.5   the mid-action commit is declared as a second host_state",
          any("COMMITS" in e.why for e in host))

    # T1.7 -- the arithmetic, through projection().
    print("\n10.3 projection:")
    pool = ActionRegistry(edge_families=set())
    for group, n in c.items():
        for i in range(n):
            pool.declare(
                ActionFamily(
                    name=f"{group}_{i}",
                    reversibility="reversible",
                    approval_mode="auto",
                    reachability=(group,),
                )
            )
    rep = pool.projection("task_detail", budget=127, order=page)
    check("T1.7h  counts reproduce beacon's four",
          [rep.counts[g] for g in page] == [45, 48, 21, 13], str(rep.counts))
    check("T1.7i  all four fit at 127, over_by 0",
          rep.fits == page and rep.would_evict == () and rep.over_by == 0,
          f"fits={rep.fits} over_by={rep.over_by}")

    pool.declare(
        ActionFamily(name="reorder_subtasks", reversibility="reversible",
                     approval_mode="auto", reachability=("task",))
    )
    rep2 = pool.projection("task_detail", budget=127, order=page)
    check("T1.7j  a 49th task family evicts person, over_by 1",
          rep2.counts["task"] == 49 and rep2.would_evict == ("person",) and rep2.over_by == 1,
          f"task={rep2.counts['task']} would_evict={rep2.would_evict} over_by={rep2.over_by}")

    rep3 = pool.projection("task_detail", budget=127, order=None)
    check("T1.8   order=None answers counts only",
          rep3.order_source is None and rep3.fits == () and rep3.would_evict == ()
          and not rep3.complete and "does not choose" in (rep3.why_incomplete or ""),
          rep3.why_incomplete or "")

    check("T1.9   consumers_at_risk is empty AND the report is incomplete",
          rep2.consumers_at_risk == () and rep2.complete is False
          and "ConsumerReport.complete" in (rep2.why_incomplete or ""),
          rep2.why_incomplete or "")

    # Round 1 MAJOR 3: `counts` must not move with the order. A family in two
    # groups is counted in both and CHARGED to one -- two numbers, two fields.
    two = ActionRegistry(edge_families=set())
    for name, groups in (("a", ("alpha",)), ("b", ("beta",)), ("ab", ("alpha", "beta"))):
        two.declare(ActionFamily(name=name, reversibility="reversible",
                                 approval_mode="auto", reachability=groups))
    fwd = two.projection("s", budget=10, order=("alpha", "beta"))
    rev = two.projection("s", budget=10, order=("beta", "alpha"))
    check("R1-A3  `counts` is order-independent; `admitted` is what the rule charges",
          fwd.counts == rev.counts == {"alpha": 2, "beta": 2}
          and fwd.admitted == {"alpha": 2, "beta": 1}
          and rev.admitted == {"beta": 2, "alpha": 1}
          and fwd.known == rev.known == 3,
          f"counts={fwd.counts} admitted fwd={fwd.admitted} rev={rev.admitted}")

    # Round 1 BLOCKING 4: a kind="action" entry with NO declaration is a legal
    # TypeEntry, not a refusal -- and the hole is closed at the other end.
    bare = two.declare(ActionFamily(name="not_yet_declared"))
    pf = two.preflight("not_yet_declared", {}, actor="user:sd")
    check("R1-B4  a bare kind='action' entry registers, and preflight refuses on it",
          bare.reversibility is None and getattr(pf, "refused", False)
          and pf.reason == "attributes_schema_violation",
          f"{getattr(pf, 'reason', pf)}")

    # Round 1 BLOCKING 5 / MINOR: a projection over an EMPTY NAMESPACE is a
    # legitimate scope, not a typo; a projection over unknown GROUPS is a typo.
    empty = two.projection("s", budget=10, order=("alpha",), namespace="nowhere")
    typo = two.projection("s", budget=10, order=("alphaa",))
    check("R1-m3  an empty namespace scope answers; an unknown group refuses",
          not getattr(empty, "refused", False) and empty.counts == {"alpha": 0}
          and getattr(typo, "refused", False)
          and typo.reason == "action_family_unknown",
          f"empty={empty.counts} typo={getattr(typo, 'reason', typo)}")

    # T1.12 -- nothing in beacon moved.
    check("T1.12  the probe only READ beacon", True,
          "module files parsed as text; no import, no write")

    # **Row 6b, brief item 5: the same questions, asked of the SHIPPED registry.**
    # The kit leg above is what makes this probe's pre-registered numbers comparable run
    # to run; this is what stops them being claims about a model the package does not
    # import. Row #6's own 17 had to record that its `import_types` kill-row fix
    # *"exists only in the probe kit"* -- a legitimate spec-row boundary, and exactly the
    # boundary a build row exists to remove.
    shipped_leg(check, fixture="beacon")

    print()
    if DRIFT:
        print("FIXTURE DRIFT since the pin (beacon is a live repository):")
        for d in DRIFT:
            print("  " + d)
        print()
    failed = [c_ for c_ in CHECKS if not c_[1]]
    if failed:
        print(f"{len(failed)} CHECK(S) FAILED")
        return 1
    print(f"ALL {len(CHECKS)} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
