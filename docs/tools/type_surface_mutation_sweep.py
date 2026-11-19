"""Row 8d's mutation sweep: every contract id this row touched, seen red by mutation.

The engine is row 7b's (`ingest_mutation_sweep.py`): each mutation is a literal
``(file, old, new)`` edit that must occur exactly once, applied to a fresh copy of the
package in a new temporary folder (nothing is deleted), and run against the contract
test that claims it on the sqlite leg. The unmutated copy must be green first. A
mutation is killed only by a test FAILURE; an import or collection error is ``broken``.

Run::

    py docs/tools/type_surface_mutation_sweep.py [--only <substring>] [--list]

Exit 0 only when every mutation is killed and nothing is broken.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_mutation_sweep import ROOT, Mutation, _copy, _run  # noqa: E402

REG = "ontoloche/registry.py"
C12 = "ontoloche/contract/test_c12_foundry_import.py"

MUTATIONS = (
    # ---- D14 (C12-78, C12-79) ----------------------------------------------------
    Mutation("D14 the import door warns", "c12_78_an_alias", REG,
             "if status != \"retired\" and self.caps.stores_aliases",
             "if False", suite=C12),
    Mutation("D14 a retired row is not warned at import", "c12_79", REG,
             "if status != \"retired\" and self.caps.stores_aliases",
             "if self.caps.stores_aliases", suite=C12),
    Mutation("D14 a backend keeping no aliases is not warned", "c12_78_an_alias_the", REG,
             "if status != \"retired\" and self.caps.stores_aliases",
             "if status != \"retired\"", suite=C12),
    Mutation("D14 the reinstate door warns", "c12_79", REG,
             "        alias_warnings.extend(\n"
             "            self._succeeded_alias_warnings(namespace, rec.kind, rec.name, dormant)\n"
             "        )",
             "        pass", suite=C12),
    Mutation("D14 the successor itself is one claimant", "c12_78_one", REG,
             "            if claimant is not None and claimant != name:",
             "            if claimant is not None:", suite=C12),
    # Not here, on purpose: dropping the `successor` test on the tombstone is an
    # EQUIVALENT mutant (the walk stops at once when there is no successor), so no test
    # can kill it. 8D-RUN.md §1 records it.
    Mutation("D14 the walk follows the chain", "c12_78_a_chain", REG,
             "                if live.status != \"retired\":\n                    claimant = live.name\n                    break",
             "                claimant = live.name\n                break", suite=C12),
    Mutation("D14 a dead end is one claimant", "c12_78_a_chain", REG,
             "                if live.status != \"retired\":\n                    claimant = live.name\n                    break",
             "                if live.status != \"retired\" or not live.successor:\n"
             "                    claimant = live.name\n                    break", suite=C12),
    # ---- B5 (C12-80) --------------------------------------------------------------
    Mutation("B5 the twin is looked up", "c12_80", REG,
             "                    if twin is not None and twin.api_name != api:",
             "                    if False:", suite=C12),
    Mutation("B5 a held twin binds nothing", "c12_80_a_held", REG,
             "                        if twin.reason is None:\n                            bound.append(",
             "                        if True:\n                            bound.append(", suite=C12),
    Mutation("B5 the dry run reports it", "c12_80_a_reference", REG,
             "                    FoundryItem(p.kind, p.api_name, p.name, \"would_write\",\n"
             "                                warnings=bound_warnings,",
             "                    FoundryItem(p.kind, p.api_name, p.name, \"would_write\",", suite=C12),
    Mutation("B5 the real run reports it", "c12_80_a_reference", REG,
             "warnings=tuple(entry.warnings) + bound_warnings, detail=p.detail,",
             "warnings=tuple(entry.warnings), detail=p.detail,", suite=C12),
    Mutation("B5 bound_by_conversion is in the detail", "c12_80_a_reference", REG,
             "            if bound:\n                p.detail[\"bound_by_conversion\"] = bound",
             "            if False:\n                p.detail[\"bound_by_conversion\"] = bound", suite=C12),
    # ---- C5-4 (C12-81) ------------------------------------------------------------
    Mutation("C5-4 an unresolved word is listed once", "c12_81", REG,
             "                    dict(pairs) for pairs in dict.fromkeys(tuple(u.items()) for u in unresolved)",
             "                    dict(pairs) for pairs in [tuple(u.items()) for u in unresolved]",
             suite=C12),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    chosen = [m for m in MUTATIONS
              if not args.only or any(o in m.rule or o in m.test for o in args.only)]
    bad = 0
    for m in chosen:
        count = (ROOT / m.file).read_text(encoding="utf-8").count(m.old)
        bad += count != 1
        if args.list:
            print(f"  {count}  {m.test:<22}  {m.rule}")
    if args.list or bad:
        print(f"\n{len(chosen)} mutations, {bad} whose old text does not occur once")
        return 1 if bad else 0
    base = _copy()
    verdict, out = _run(base, " or ".join(sorted({m.test for m in chosen})), C12)
    if verdict != "survived":
        print("the UNMUTATED copy is not green:\n" + out[-3000:])
        return 2
    print(f"baseline green in {base}")
    results = []
    for m in chosen:
        source = (ROOT / m.file).read_text(encoding="utf-8")
        where = _copy()
        (where / m.file).write_text(source.replace(m.old, m.new), encoding="utf-8")
        verdict, out = _run(where, m.test, m.suite)
        results.append((m, verdict))
        if verdict == "broken":
            print(out[-1500:])
    width = max(len(m.rule) for m, _ in results)
    for m, verdict in results:
        print(f"  {m.rule:<{width}}  {m.test:<22}  {verdict}")
    killed = sum(v == "killed" for _, v in results)
    print(f"\n{len(results)} mutations: {killed} killed, {len(results) - killed} not killed")
    return 0 if killed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
