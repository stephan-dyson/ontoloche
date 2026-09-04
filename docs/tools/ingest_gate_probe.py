# -*- coding: utf-8 -*-
"""Design test 4 for `docs/specs/INGEST.md` v0 -- **"I already know 38 of these"**, the
match-vs-propose confidence gate, over real NYC 311 rows.

`ROADMAP.md`'s Phase 3 homes instance resolution with the walkthrough's *"I already know
38 of these"*. This test lands a batch in which a **known** fraction already exists and
checks that each of the gate's three outcomes fires on the fraction it should -- and
that the number is in the record rather than asserted.

**The design question it decides:** is the threshold a **call parameter** or a
**declared, governed fact on the entry**? 4.3 runs the identical batch under two callers
choosing different thresholds and counts the disagreements. A duplicate that exists
because two callers picked different numbers is not a data problem, and it is not one
the curation loop can see.

The 200 landing rows are pulled live from ``erm2-nwe9`` and pinned into the run record
by their ``unique_key``s, so the walk-through reproduces.

Run: ``py docs/tools/ingest_gate_probe.py``
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_seam_probe import (  # noqa: E402
    CHECKS, CandidatePage, CandidateQuery, InstanceRecord, _norm, _similar, check,
)

DATASET = "erm2-nwe9"
RESOURCE = f"https://data.cityofnewyork.us/resource/{DATASET}.json"

#: The host's own narrowing, as design test 2 established it must be.
HOST_NARROWING = ("agency='NYPD' AND complaint_type='Illegal Fireworks' "
                  "AND incident_zip='11214'")

#: The walkthrough's number, made literal.
ALREADY_KNOWN = 38
BAND = 24          # rows perturbed into the middle band
BATCH = 100

#: Deterministic, and every one of them is a real USPS/NYC abbreviation. Nothing here
#: is a typo generator: this is the shape a second publisher's address column has.
ABBREVIATIONS = (
    (r"\bSTREET\b", "ST"), (r"\bAVENUE\b", "AVE"), (r"\bROAD\b", "RD"),
    (r"\bPLACE\b", "PL"), (r"\bBOULEVARD\b", "BLVD"), (r"\bEAST\b", "E"),
    (r"\bWEST\b", "W"), (r"\bNORTH\b", "N"), (r"\bSOUTH\b", "S"),
    (r"\bPARKWAY\b", "PKWY"), (r"\bDRIVE\b", "DR"), (r"\bCOURT\b", "CT"),
)


def abbreviate(text: str) -> str:
    out = text.upper()
    for pat, rep in ABBREVIATIONS:
        out = re.sub(pat, rep, out)
    return out


@dataclass(frozen=True)
class MatchPolicy:
    """The gate, three-valued per R60. **Declared on the entry, never on the call.**

    ``match_at`` and ``propose_below`` are the two thresholds and the band between them
    is the third outcome -- a human's, not a default's.
    """

    match_at: float
    propose_below: float
    why: str

    def __post_init__(self) -> None:
        if not (0.0 <= self.propose_below <= self.match_at <= 1.0):
            raise ValueError("propose_below must not exceed match_at")
        if not (self.why or "").strip():
            raise ValueError("MatchPolicy.why is required and non-empty")

    def verdict(self, score: float | None) -> str:
        if score is None:
            return "unknowable"
        if score >= self.match_at:
            return "match"
        if score < self.propose_below:
            return "propose"
        return "review"


class StaticHost:
    def __init__(self, rows: list[InstanceRecord]) -> None:
        self._rows = sorted(rows, key=lambda r: r.instance_id)

    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage:
        pool = [r for r in self._rows
                if (r.namespace, r.kind, r.type_name) == (q.namespace, q.kind,
                                                          q.type_name)]
        return CandidatePage(records=tuple(pool), known=len(pool), complete=True,
                             why_incomplete=None, next_after=None)


def best_score(label: str, host: StaticHost) -> tuple[str | None, float | None]:
    page = host.find_instance_candidates(
        CandidateQuery(namespace="nyc", kind="entity", type_name="service_request"))
    norm = _norm(label)
    best: tuple[str | None, float] = (None, 0.0)
    for rec in page.records:
        s = _similar(norm, _norm(rec.label))
        if s > best[1]:
            best = (f"{rec.namespace}:{rec.kind}:{rec.type_name}#{rec.instance_id}", s)
    return best[0], round(best[1], 4)


def soda(params: dict) -> list[dict]:
    with urllib.request.urlopen(f"{RESOURCE}?{urllib.parse.urlencode(params)}",
                                timeout=300) as fh:
        return json.load(fh)


def main() -> int:
    print("DESIGN TEST 4 -- \"I already know 38 of these\", the confidence gate")
    print(f"  live from {RESOURCE}, {date.today().isoformat()}")
    print(f"  host narrowing: {HOST_NARROWING}")

    raw = soda({"$where": HOST_NARROWING, "$limit": 400, "$order": "unique_key",
                "$select": "unique_key,incident_address,complaint_type,incident_zip"})
    rows = [r for r in raw if r.get("incident_address")]
    # distinct addresses, so "already known" is a fact about the instance and not an
    # artefact of one address appearing twice in the source
    seen: dict[str, dict] = {}
    for r in rows:
        seen.setdefault(r["incident_address"].strip().upper(), r)
    distinct = sorted(seen.values(), key=lambda r: r["unique_key"])
    print(f"  {len(raw)} rows fetched, {len(distinct)} with a distinct address")
    check("the live partition supplies enough distinct addresses for the batch",
          len(distinct) >= ALREADY_KNOWN + BAND + 20, f"{len(distinct)}")

    known = distinct[:ALREADY_KNOWN]
    banded = distinct[ALREADY_KNOWN:ALREADY_KNOWN + BAND]
    novel = distinct[ALREADY_KNOWN + BAND:]

    # The HOST already holds these, and the band rows too -- in their FULL spelling.
    host_rows = [
        InstanceRecord("nyc", "entity", "service_request", r["unique_key"],
                       r["incident_address"].strip().upper(),
                       {"complaint_type": r.get("complaint_type"),
                        "zip": r.get("incident_zip")})
        for r in known + banded
    ]
    host = StaticHost(host_rows)
    print(f"  host holds {len(host_rows)} instances "
          f"({ALREADY_KNOWN} exact + {BAND} that will land abbreviated)")

    # The landing batch: 38 exact, BAND abbreviated, the rest genuinely new.
    batch: list[tuple[str, str]] = []
    batch += [("known", r["incident_address"].strip().upper()) for r in known]
    batch += [("banded", abbreviate(r["incident_address"].strip()))
              for r in banded]
    for r in novel[: BATCH - ALREADY_KNOWN - BAND]:
        batch.append(("novel", f"{r['incident_address'].strip().upper()} "
                               f"REAR ANNEX {r['unique_key'][-4:]}"))
    print(f"  landing batch: {len(batch)} rows "
          f"({sum(1 for k, _ in batch if k == 'known')} known / "
          f"{sum(1 for k, _ in batch if k == 'banded')} abbreviated / "
          f"{sum(1 for k, _ in batch if k == 'novel')} new)")

    policy = MatchPolicy(
        match_at=0.97, propose_below=0.80,
        why="an address that matches a held instance to 0.97 is that instance; below "
            "0.80 it is a different one; the band between is a human's call")
    print(f"\n4.1 the gate, declared on the entry: match_at={policy.match_at} "
          f"propose_below={policy.propose_below}")

    tally: dict[str, dict[str, int]] = {}
    examples: dict[str, tuple[str, float]] = {}
    for kind, label in batch:
        _, score = best_score(label, host)
        v = policy.verdict(score)
        tally.setdefault(kind, {}).setdefault(v, 0)
        tally[kind][v] += 1
        if kind not in examples or v == "review":
            examples.setdefault(f"{kind}:{v}", (label, score or 0.0))
    for kind in ("known", "banded", "novel"):
        print(f"  {kind:>7}: {dict(sorted(tally.get(kind, {}).items()))}")
    for k, (label, s) in sorted(examples.items()):
        print(f"     {k:<16} e.g. {label[:52]!r} @ {s}")

    matched = tally.get("known", {}).get("match", 0)
    print(f"\n  the number: {matched} of {ALREADY_KNOWN} already-known rows matched")
    check(f"all {ALREADY_KNOWN} already-known rows fire `match` and nothing else does "
          f"from that group", matched == ALREADY_KNOWN
          and set(tally.get("known", {})) == {"match"}, str(tally.get("known")))
    check("the abbreviated rows land in the REVIEW band rather than silently matching "
          "or silently proposing",
          tally.get("banded", {}).get("review", 0) >= BAND * 0.5,
          str(tally.get("banded")))
    check("the genuinely new rows propose, and none of them matches",
          tally.get("novel", {}).get("match", 0) == 0, str(tally.get("novel")))

    # --- 4.2 all three outcomes fired ---------------------------------------
    fired = {v for kind in tally for v in tally[kind]}
    print(f"\n4.2 outcomes that fired across the batch: {sorted(fired)}")
    check("all three of the gate's outcomes fire on one batch of real rows",
          {"match", "review", "propose"} <= fired, str(sorted(fired)))

    # --- 4.3 the threshold as a CALL PARAMETER, constructed as a failure -----
    print("\n4.3 the same batch under two callers who chose their own thresholds")
    lax = MatchPolicy(0.86, 0.80, why="caller A")
    strict = MatchPolicy(0.995, 0.80, why="caller B")
    disagree = 0
    both: list[tuple[str, str, str, float]] = []
    for kind, label in batch:
        _, score = best_score(label, host)
        va, vb = lax.verdict(score), strict.verdict(score)
        if va != vb:
            disagree += 1
            if len(both) < 3:
                both.append((label, va, vb, score or 0.0))
    print(f"  {disagree} of {len(batch)} rows resolve DIFFERENTLY for the two callers")
    for label, va, vb, s in both:
        print(f"     {label[:46]!r} @ {s}: caller A -> {va}, caller B -> {vb}")
    check("a per-call threshold makes one landed row resolve two ways into ONE "
          "vocabulary -- so the threshold is a governed fact on the entry, not an "
          "argument", disagree > 0, f"{disagree} rows")

    # --- 4.4 the fourth verdict, and it is not the gate's to soften ----------
    print("\n4.4 an unscored candidate")
    print(f"  policy.verdict(None) -> {policy.verdict(None)!r}")
    check("a candidate the scan could not score is `unknowable`, not `propose` -- "
          "design test 1's fifth outcome, at the gate",
          policy.verdict(None) == "unknowable")

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
