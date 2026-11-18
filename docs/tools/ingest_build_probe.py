"""Row 7b's design tests, through the SHIPPED registry -- 7B-RUN.md 0.4 and 0.5.

Row 7a's probes ran against a throwaway kit (``ingest_probe_kit.py``). These run the
same questions through ``Registry.resolve_instance`` and ``get_instance_checked`` over
a HOST-OWNED table on the reference SQLite backend, and hold every prediction 7B-RUN 0.4
made before the code existed:

* **UC2 CMS** on the full health-citations export, one host row per CCN;
* **"I already know 38 of these"**, the 7a gate batch, live from NYC ``erm2-nwe9``,
  under both host shapes INGEST.md 5.2 prints;
* **UC3** the CA + CO tenancy fixture, the retire case under Q91's default, and a
  truncated live scan;
* **Paging**: a 7-row host page against the unpaged control, and R58's three states;
* **F1** (the seam: no instance row in the registry's tables), **F2** (the build and
  the kit agree on every UC2 configuration and every gate-batch group), and **Q93**, rule
  3-19's read cost, measured.

Run::

    py docs/tools/ingest_build_probe.py            # print every result
    py docs/tools/ingest_build_probe.py --assert   # exit 1 on any failed check
    py docs/tools/ingest_build_probe.py --offline  # skip the live NYC fetches

The CMS file is read from ``$OO_CMS_CSV`` or the machine's temp folder
(``NH_HealthCitations_Aug2026.csv``), and downloaded there once if absent.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import ssl
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ontoloche.adapter import CandidateQuery  # noqa: E402
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.contract._support import FIXTURE, host_instances, seed  # noqa: E402
from ontoloche.ingest import (  # noqa: E402
    INSTANCE_CONDITION_KEY,
    INSTANCE_OUTCOMES,
    MATCH_POLICY_KEY,
    InstanceContext,
)
from ontoloche.registry import Registry  # noqa: E402
from ontoloche.types import Refusal  # noqa: E402

import ingest_probe_kit as kit  # noqa: E402

CMS_URL = ("https://data.cms.gov/provider-data/sites/default/files/resources/"
           "NH_HealthCitations_Oct2026.csv")
CMS_CACHE = Path(os.environ.get("OO_CMS_CSV") or
                 Path(tempfile.gettempdir()) / "NH_HealthCitations_Aug2026.csv")
NYC = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
NYC_NARROWING = {"agency": "NYPD", "complaint_type": "Illegal Fireworks",
                 "incident_zip": "11214"}

CMS_POLICY = {"match_at": 0.97, "propose_below": 0.80, "ambiguity_margin": 0.02,
              "why": "the kit's figures, from the CMS file"}
NYC_POLICY = {"match_at": 0.97, "propose_below": 0.80, "ambiguity_margin": 0.03,
              "why": "an address matching a held instance to 0.97 is that instance; below "
                     "0.80 it is a different one; the band between is a human's call"}
CTX = InstanceContext(label_source="NH_HealthCitations#Provider Name", act_id="7b-probe")

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    print(f"  [{'ok' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))


def _context() -> ssl.SSLContext:
    """**[Observed] 7B-RUN 0.1 item 4:** this machine's default trust store rejects
    data.cityofnewyork.us and an explicit certifi context accepts it."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover
        return ssl.create_default_context()


def fresh() -> SQLiteAdapter:
    adapter = SQLiteAdapter(":memory:")
    adapter.migrate()
    return adapter


def registry_over(adapter, name, namespace, policy, *, condition=None, rows=None, **bind):
    if rows is not None:
        host_instances(adapter, rows, type_name=name, namespace=namespace, **bind)
    reg = Registry(adapter)
    attributes = {MATCH_POLICY_KEY: policy}
    if condition is not None:
        attributes[INSTANCE_CONDITION_KEY] = condition
    seed(reg, name, namespace=namespace, attributes=attributes)
    return reg


def resolve(reg, label, name="facility", namespace="cms", tier="small", **kw):
    return reg.resolve_instance(label, CTX, type_name=name, namespace=namespace, tier=tier,
                                **kw)


# ------------------------------------------------------------------------------ data
def cms_facilities() -> dict[str, tuple[str, str]]:
    if not CMS_CACHE.exists():  # pragma: no cover - network
        print(f"  downloading {CMS_URL} -> {CMS_CACHE}")
        with urllib.request.urlopen(CMS_URL, context=_context(), timeout=600) as fh:
            CMS_CACHE.write_bytes(fh.read())
    out: dict[str, tuple[str, str]] = {}
    with CMS_CACHE.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["CMS Certification Number (CCN)"],
                           (row["Provider Name"], row["State"]))
    return out


def rows_of(facilities, exclude=()):
    return [{"host_id": ccn, "label": name, "state": state}
            for ccn, (name, state) in sorted(facilities.items()) if ccn not in exclude]


def kit_answer(facilities, label, *, exclude=(), scan_cap=None):
    host = kit.HostTable([kit.InstanceRecord("cms", "entity", "facility", ccn, name,
                                             {"state": state})
                          for ccn, (name, state) in facilities.items() if ccn not in exclude],
                         scan_cap=scan_cap)
    vocab = kit.Vocabulary()
    vocab.declare("cms", "facility", kit.EntryDeclaration(policy=kit.MatchPolicy(
        match_at=0.97, propose_below=0.80, ambiguity_margin=0.02, why="kit")))
    return kit.resolve_instance(label, kit.InstanceContext(act_id="7b"), host=host,
                                vocab=vocab, namespace="cms", type_name="facility",
                                tier="small")


def registry_state(adapter) -> dict[str, str]:
    """Every registry table's CONTENT, digested: an UPDATE shows, not only an INSERT.
    Round 1 (fidelity lens 2): F1 compared row counts on one adapter of four."""
    import hashlib

    out = {}
    for (table,) in adapter._fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'oo_%'"):
        rows = sorted(repr(r) for r in adapter._fetchall(f'SELECT * FROM "{table}"'))
        out[table] = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
    return out


class CallCounter:
    """Counts primitive 23 calls on one adapter (Q93, round 1 fidelity lens 1)."""

    def __init__(self, adapter) -> None:
        self.calls = 0
        inner = adapter.find_instance_candidates

        def counted(q):
            self.calls += 1
            return inner(q)

        adapter.find_instance_candidates = counted


# ------------------------------------------------------------------------------- UC2
def uc2(facilities) -> None:
    print(f"\nUC2 CMS -- {len(facilities)} host rows, one per CCN, from {CMS_CACHE.name}")
    ids = sorted(facilities)
    adapter = fresh()
    reg = registry_over(adapter, "facility", "cms", CMS_POLICY, rows=rows_of(facilities))
    states: list[tuple[str, object, dict[str, str]]] = [
        ("full", adapter, registry_state(adapter))]

    burns = resolve(reg, "BURNS NURSING HOME, INC.")
    check("BURNS NURSING HOME, INC. is existing at 1.0, ref #015009, known=1",
          burns.outcome == "existing" and burns.ref.id == "015009"
          and burns.confidence == 1.0 and burns.known == 1 and burns.complete,
          f"{burns.outcome} {burns.ref} {burns.confidence} known={burns.known}")
    miller = resolve(reg, "MILLER'S MERRY MANOR")
    millers = sorted(c for c, (n, _) in facilities.items() if n == "MILLER'S MERRY MANOR")
    check("MILLER'S MERRY MANOR is ambiguous, ref None, all twelve returned",
          miller.outcome == "ambiguous" and miller.ref is None and miller.known == 12
          and sorted(c.ref.id for c in miller.candidates) == millers,
          f"{miller.outcome} known={miller.known} of {len(millers)}")
    provider = resolve(reg, "Provider Name")
    check("'Provider Name' is not_an_instance with scanned=0",
          provider.outcome == "not_an_instance" and provider.scanned == 0)

    held = fresh()
    held_reg = registry_over(held, "facility", "cms", CMS_POLICY,
                             rows=rows_of(facilities, exclude={"745040"}))
    states.append(("745040 held out", held, registry_state(held)))
    sarah = resolve(held_reg, "THE SARAH ROBERTS FRENCH HOME")
    check("THE SARAH ROBERTS FRENCH HOME with 745040 held out is a proposal over "
          f"{len(ids) - 1} rows",
          sarah.outcome == "proposal" and sarah.scanned == len(ids) - 1,
          f"{sarah.outcome} scanned={sarah.scanned} top={sarah.confidence}")

    tuskegee = "Tuskegee Airmen Texas State Veterans Home"
    pos = ids.index("745057")
    capped = fresh()
    capped_reg = registry_over(capped, "facility", "cms", CMS_POLICY,
                               rows=rows_of(facilities), scan_cap=pos)
    states.append(("capped short of 745057", capped, registry_state(capped)))
    cut = resolve(capped_reg, tuskegee)
    control = resolve(reg, tuskegee)
    check("Tuskegee with a scan cap one row short of 745057 is unknowable, never proposal",
          cut.outcome == "unknowable", f"{cut.outcome}: {cut.why_incomplete[:70]}")
    check("and the uncapped control is existing at 1.0",
          control.outcome == "existing" and control.confidence == 1.0
          and control.ref.id == "745057", f"{control.outcome} {control.confidence}")

    first = ids.index(millers[0])
    m_cap = fresh()
    m_reg = registry_over(m_cap, "facility", "cms", CMS_POLICY, rows=rows_of(facilities),
                          scan_cap=first + 1)
    states.append(("capped past the first Miller", m_cap, registry_state(m_cap)))
    m_cut = resolve(m_reg, "MILLER'S MERRY MANOR")
    check("MILLER'S MERRY MANOR capped one row past its first is unknowable, never "
          "existing (I-1)", m_cut.outcome == "unknowable", m_cut.outcome)

    outcomes = {burns.outcome, miller.outcome, provider.outcome, sarah.outcome, cut.outcome}
    check("all five outcomes are reached on real CMS labels",
          outcomes == set(INSTANCE_OUTCOMES), str(sorted(outcomes)))

    changed = [label for label, ad, before in states if registry_state(ad) != before]
    foreign = [t for _, ad, _ in states for (t,) in ad._fetchall(
        "SELECT name FROM sqlite_master WHERE type='table'")
        if not t.startswith(("oo_", "host_", "sqlite_"))]
    check("F1: on all four stores, every registry table's content is unchanged by the "
          "resolutions made over it, and no table but the registry's and the host's exists",
          not changed and not foreign, f"changed={changed} foreign={foreign}")

    kit_pairs = [
        ("BURNS NURSING HOME, INC.", burns, kit_answer(facilities, "BURNS NURSING HOME, INC.")),
        ("MILLER'S MERRY MANOR", miller, kit_answer(facilities, "MILLER'S MERRY MANOR")),
        ("Provider Name", provider, kit_answer(facilities, "Provider Name")),
        ("THE SARAH ROBERTS FRENCH HOME", sarah,
         kit_answer(facilities, "THE SARAH ROBERTS FRENCH HOME", exclude={"745040"})),
        (tuskegee, control, kit_answer(facilities, tuskegee)),
        (f"{tuskegee} (capped)", cut, kit_answer(facilities, tuskegee, scan_cap=pos)),
        ("MILLER'S MERRY MANOR (capped)", m_cut,
         kit_answer(facilities, "MILLER'S MERRY MANOR", scan_cap=first + 1)),
    ]
    disagree = [(label, b.outcome, k.outcome) for label, b, k in kit_pairs
                if b.outcome != k.outcome or b.known != k.known]
    check(f"F2: the build and the kit agree on all {len(kit_pairs)} UC2 configurations "
          "(five labels, the two capped ones included; outcome and known)",
          not disagree, str(disagree))

    # --- Q93: rule 3-19's read cost --------------------------------------------------
    print("\nQ93 -- rule 3-19's read cost, measured")
    one_calls = CallCounter(adapter)
    t0 = time.perf_counter()
    one = resolve(reg, "BURNS NURSING HOME, INC.")
    single_ms = (time.perf_counter() - t0) * 1000
    split = fresh()
    half = len(ids) // 2
    old_rows = rows_of({k: facilities[k] for k in ids[:half]})
    new_rows = rows_of({k: facilities[k] for k in ids[half:]})
    host_instances(split, old_rows, type_name="facility", namespace="cms")
    host_instances(split, new_rows, type_name="ltc_facility", namespace="cms")
    sreg = Registry(split)
    seed(sreg, "facility", namespace="cms", attributes={MATCH_POLICY_KEY: CMS_POLICY})
    seed(sreg, "ltc_facility", namespace="cms", attributes={MATCH_POLICY_KEY: CMS_POLICY})
    sreg.retire("facility", "renamed", retired_by="user:sd", namespace="cms",
                successor="ltc_facility")
    resolve(sreg, "BURNS NURSING HOME, INC.")          # warm, as the one-member read was
    two_calls = CallCounter(split)
    t0 = time.perf_counter()
    two = resolve(sreg, "BURNS NURSING HOME, INC.")
    closure_ms = (time.perf_counter() - t0) * 1000
    print(f"  one-member closure, one table: scanned={one.scanned}, "
          f"{one_calls.calls} primitive 23 calls, {single_ms:.0f} ms (one warm run)")
    print(f"  two-member closure (rows split {half}/{len(ids) - half}): "
          f"scanned={two.scanned}, {two_calls.calls} primitive 23 calls, "
          f"{closure_ms:.0f} ms (one warm run), outcome {two.outcome}")
    check("Q93: the two-member closure reads the same number of rows as the one-member "
          "read over the same rows, and finds the same answer",
          two.scanned == one.scanned and two.outcome == one.outcome == "existing",
          f"{two.scanned} vs {one.scanned}")


# ------------------------------------------------------------------------------- UC3
def uc3(facilities) -> None:
    ca_co = {c: v for c, v in facilities.items() if v[1] in ("CA", "CO")}
    names_by_state: dict[str, set[str]] = {}
    for _, (name, state) in ca_co.items():
        names_by_state.setdefault(name, set()).add(state)
    shared = sorted(n for n, s in names_by_state.items() if s == {"CA", "CO"})
    print(f"\nUC3 -- {len(ca_co)} CA + CO rows "
          f"({sum(v[1] == 'CA' for v in ca_co.values())} + "
          f"{sum(v[1] == 'CO' for v in ca_co.values())}), {len(shared)} names both share")
    check("the fixture is still 1,373 rows", len(ca_co) == 1373, str(len(ca_co)))
    ca_only = {"op": "eq", "attribute": "state", "value": "CA",
               "why": "this deployment serves California only"}
    adapter = fresh()
    reg = registry_over(adapter, "facility", "cms", CMS_POLICY, condition=ca_only,
                        rows=rows_of(ca_co))
    leaked, scanned = 0, set()
    for name in shared:
        r = resolve(reg, name)
        scanned.add(r.scanned)
        leaked += sum(1 for c in r.candidates if c.discriminators.get("state") == "CO")
        if r.ref is not None and ca_co[r.ref.id][1] == "CO":
            leaked += 1
    check("UC3.1 no CO row is a candidate on any shared label, and each read considered "
          "all 1,373", leaked == 0 and scanned == {1373}, f"leaked={leaked} scanned={scanned}")
    check("UC3.1 primitive 23 takes no tenant argument",
          "tenant" not in CandidateQuery.__dataclass_fields__)

    host_instances(adapter, [], type_name="ltc_facility", namespace="cms")
    reg2 = Registry(adapter)
    seed(reg2, "ltc_facility", namespace="cms", attributes={
        MATCH_POLICY_KEY: CMS_POLICY,
        INSTANCE_CONDITION_KEY: {"op": "in", "attribute": "state", "value": ["CA", "CO"],
                                 "why": "the successor serves both"}})
    reg2.retire("facility", "renamed", retired_by="user:sd", namespace="cms",
                successor="ltc_facility")
    tally = Counter()
    leaked = 0
    for ccn, (name, _) in sorted(ca_co.items()):
        r = resolve(reg2, name)
        tally[r.outcome] += 1
        if r.outcome == "unknowable" and "tenancy predicate" not in r.why_incomplete:
            tally["unnamed"] += 1
        leaked += sum(1 for c in r.candidates if c.discriminators.get("state") == "CO")
    check("UC3.2 retire under Q91's default: every label unknowable naming the changed "
          "fact, 0 CO refs", tally == Counter({"unknowable": len(ca_co)}) and leaked == 0,
          str(dict(tally)))


# --------------------------------------------------------------------------- NYC gate
def soda(params: dict) -> list[dict]:
    where = " AND ".join(f"{k}='{v}'" for k, v in sorted(NYC_NARROWING.items()))
    url = f"{NYC}?{urllib.parse.urlencode({**params, '$where': where})}"
    with urllib.request.urlopen(url, context=_context(), timeout=300) as fh:
        return json.load(fh)


def nyc_gate() -> None:
    print("\nGATE -- \"I already know 38 of these\", live from erm2-nwe9")
    raw = soda({"$limit": 400, "$order": "unique_key",
                "$select": "unique_key,incident_address,complaint_type,incident_zip"})
    rows = [r for r in raw if r.get("incident_address")]
    seen: dict[str, dict] = {}
    for r in rows:
        seen.setdefault(r["incident_address"].strip().upper(), r)
    distinct = sorted(seen.values(), key=lambda r: r["unique_key"])
    known, banded, novel = distinct[:38], distinct[38:62], distinct[62:]
    batch = [("known", r["incident_address"].strip().upper()) for r in known]
    batch += [("banded", kit_abbreviate(r["incident_address"].strip())) for r in banded]
    batch += [("novel", f"{r['incident_address'].strip().upper()} REAR ANNEX "
                        f"{r['unique_key'][-4:]}") for r in novel[:38]]
    print(f"  {len(raw)} rows, {len(distinct)} distinct addresses, batch of {len(batch)}")

    def host_rows(source):
        return [{"host_id": r["unique_key"], "label": r["incident_address"].strip().upper(),
                 "state": r.get("incident_zip")} for r in source]

    def run(source, **bind):
        adapter = fresh()
        reg = registry_over(adapter, "service_request", "nyc", NYC_POLICY,
                            rows=host_rows(source), **bind)
        tally: dict[str, Counter] = {}
        for kind, label in batch:
            r = resolve(reg, label, name="service_request", namespace="nyc", tier="sonnet")
            tally.setdefault(kind, Counter())[r.outcome] += 1
        return tally

    known_banded = {r["incident_address"].strip().upper() for r in known + banded}
    dedup = run(known + banded)
    real = run([r for r in rows if r["incident_address"].strip().upper() in known_banded])
    for label, t in (("one instance per address", dedup), ("the host's actual rows", real)):
        print(f"  {label}: " + ", ".join(f"{k} {dict(sorted(v.items()))}" for k, v in t.items()))
    check("the deduplicated host gives the kit's known {'existing': 38}",
          dedup.get("known") == Counter({"existing": 38}), str(dict(dedup.get("known", {}))))
    check("banded {'ambiguous': 23, 'existing': 1}",
          dedup.get("banded") == Counter({"ambiguous": 23, "existing": 1}),
          str(dict(dedup.get("banded", {}))))
    check("novel {'proposal': 38}", dedup.get("novel") == Counter({"proposal": 38}),
          str(dict(dedup.get("novel", {}))))
    check("the un-deduplicated host's known group is {'ambiguous': 13, 'existing': 25}",
          real.get("known") == Counter({"ambiguous": 13, "existing": 25}),
          str(dict(real.get("known", {}))))

    vocab = kit.Vocabulary()
    vocab.declare("nyc", "service_request", kit.EntryDeclaration(policy=kit.MatchPolicy(
        match_at=0.97, propose_below=0.80, ambiguity_margin=0.03, why="kit")))
    kit_host = kit.HostTable([kit.InstanceRecord(
        "nyc", "entity", "service_request", r["unique_key"],
        r["incident_address"].strip().upper(), {"zip": r.get("incident_zip")})
        for r in known + banded])
    kit_tally: dict[str, Counter] = {}
    for kind, label in batch:
        k = kit.resolve_instance(label, kit.InstanceContext(act_id="7b"), host=kit_host,
                                 vocab=vocab, namespace="nyc", type_name="service_request",
                                 tier="sonnet")
        kit_tally.setdefault(kind, Counter())[k.outcome] += 1
    check("F2: the build and the kit agree on every gate-batch group", kit_tally == dedup,
          str({k: dict(v) for k, v in kit_tally.items()}))

    capped = run(known + banded, scan_cap=5)
    proposals = sum(t.get("proposal", 0) for t in capped.values())
    check("UC3.3 a truncated live scan answers unknowable, never proposal", proposals == 0,
          str({k: dict(v) for k, v in capped.items()}))


def kit_abbreviate(text: str) -> str:
    out = text.upper()
    for pat, rep in (
        (r"\bSTREET\b", "ST"), (r"\bAVENUE\b", "AVE"), (r"\bROAD\b", "RD"),
        (r"\bPLACE\b", "PL"), (r"\bBOULEVARD\b", "BLVD"), (r"\bEAST\b", "E"),
        (r"\bWEST\b", "W"), (r"\bNORTH\b", "N"), (r"\bSOUTH\b", "S"),
        (r"\bPARKWAY\b", "PKWY"), (r"\bDRIVE\b", "DR"), (r"\bCOURT\b", "CT"),
    ):
        out = re.sub(pat, rep, out)
    return out


# ----------------------------------------------------------------------------- paging
def _fixture_ccns() -> int:
    with FIXTURE.open(encoding="utf-8", newline="") as fh:
        return len({r["CMS Certification Number (CCN)"] for r in csv.DictReader(fh)})


def paging(all_facilities) -> None:
    # 7B-RUN 0.4 named the 400-row contract sample. **[Observed]** it is 400 CITATION
    # rows over 10 CCNs, so a host table of it is 10 rows and no page cap bites. The
    # paging host is the first 400 CCNs of the full file instead (7B-RUN 1, departure).
    facilities = {c: all_facilities[c] for c in sorted(all_facilities)[:400]}
    print(f"\nPAGING -- the first {len(facilities)} CCNs of the CMS file "
          f"({FIXTURE.name} has {_fixture_ccns()} CCNs, too few to page)")
    labels = sorted({n for n, _ in facilities.values()})
    labels += [n.title()[:-2] for n in labels] + ["Provider Name", "zzzz qqqq unrelated"]
    paged = registry_over(fresh(), "facility", "cms", CMS_POLICY,
                          rows=rows_of(facilities), page_size=7)
    whole = registry_over(fresh(), "facility", "cms", CMS_POLICY, rows=rows_of(facilities))
    diffs = []
    for label in labels:
        a, b = resolve(paged, label), resolve(whole, label)
        if ((a.outcome, a.known, a.confidence, a.ref,
             sorted(str(c.ref) for c in a.candidates))
                != (b.outcome, b.known, b.confidence, b.ref,
                    sorted(str(c.ref) for c in b.candidates))):
            diffs.append(label)
    check(f"a 7-row host page answers every one of {len(labels)} labels as the unpaged "
          "control does (R58: a guard never reads a page)", not diffs, str(diffs[:3]))

    adapter = fresh()
    host_instances(adapter, rows_of(facilities), type_name="facility", namespace="cms",
                   page_size=7, scan_cap=20)
    q = CandidateQuery(namespace="cms", kind="entity", type_name="facility")
    states = []
    while True:
        page = adapter.find_instance_candidates(q)
        states.append((page.complete, page.next_after is not None))
        if page.next_after is None:
            break
        q = CandidateQuery(namespace="cms", kind="entity", type_name="facility",
                           after=page.next_after)
    adapter2 = fresh()
    host_instances(adapter2, rows_of(facilities), type_name="facility", namespace="cms")
    last = adapter2.find_instance_candidates(
        CandidateQuery(namespace="cms", kind="entity", type_name="facility"))
    states.append((last.complete, last.next_after is not None))
    check("all three of R58's page states are produced and told apart by the report",
          {(True, False), (False, True), (False, False)} <= set(states), str(set(states)))

    capped = registry_over(fresh(), "facility", "cms", CMS_POLICY,
                           rows=rows_of(facilities), page_size=7, scan_cap=20)
    bad = [label for label in labels
           if (r := resolve(capped, label)).complete is False
           and r.outcome not in ("unknowable", "not_an_instance")]
    check("rule 3-6: no complete=False result carries a decided outcome, over every label",
          not bad, str(bad[:3]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assert", dest="strict", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    facilities = cms_facilities()
    uc2(facilities)
    uc3(facilities)
    paging(facilities)
    if not args.offline:
        nyc_gate()
    failed = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    return 1 if (args.strict and failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
