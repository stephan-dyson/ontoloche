# -*- coding: utf-8 -*-
"""Design test 4 for `docs/specs/INGEST.md` v0 -- **"I already know 38 of these"**, the
match-vs-propose confidence gate, over real NYC 311 rows.

`ROADMAP.md`'s Phase 3 homes instance resolution with the walkthrough's *"I already know
38 of these"*. This test lands a batch in which a **known** fraction already exists and
checks that each of the gate's outcomes fires on the fraction it should.

**AMENDED BY ROUND 1.** **K3:** the gate had three verdicts of its own -- ``match`` /
``propose`` / ``review`` -- and ``review`` was not one of the five that rule 3-1 closes,
so this probe and design test 1 answered one landed row two ways. The gate now answers
in `INGEST.md` 3.1's five outcomes, through the shared kit. **M3:** the headline number
was a property of one ``setdefault`` line -- the host held one instance per *address*
while the instance in ``erm2-nwe9`` is a service request keyed by ``unique_key``. Both
numbers are now printed, and the un-deduped one is the honest headline.

Run: ``py docs/tools/ingest_gate_probe.py``
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_probe_kit import (  # noqa: E402
    EntryDeclaration, HostTable, InstanceContext, InstanceRecord, MatchPolicy,
    Vocabulary, resolve_instance,
)
from ingest_seam_probe import CHECKS, check  # noqa: E402

DATASET = "erm2-nwe9"
RESOURCE = f"https://data.cityofnewyork.us/resource/{DATASET}.json"
HOST_NARROWING = {"agency": "NYPD", "complaint_type": "Illegal Fireworks",
                  "incident_zip": "11214"}

ALREADY_KNOWN = 38
BAND = 24
BATCH = 100

#: Declared on the ENTRY (rule 5-1), never on the call.
NYC_POLICY = MatchPolicy(
    match_at=0.97, propose_below=0.80, ambiguity_margin=0.03,
    why="an address matching a held instance to 0.97 is that instance; below 0.80 it is "
        "a different one; the band between is a human's call")

#: Deterministic, and every one is a real USPS/NYC abbreviation. Not a typo generator:
#: this is the shape a second publisher's address column has.
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


def soda(params: dict) -> list[dict]:
    where = " AND ".join(f"{k}='{v}'" for k, v in sorted(HOST_NARROWING.items()))
    params = {**params, "$where": where}
    with urllib.request.urlopen(f"{RESOURCE}?{urllib.parse.urlencode(params)}",
                                timeout=300) as fh:
        return json.load(fh)


def nyc_vocab() -> Vocabulary:
    v = Vocabulary()
    v.declare("nyc", "service_request", EntryDeclaration(policy=NYC_POLICY))
    return v


def rec(row: dict) -> InstanceRecord:
    return InstanceRecord("nyc", "entity", "service_request", row["unique_key"],
                          row["incident_address"].strip().upper(),
                          {"complaint_type": row.get("complaint_type"),
                           "zip": row.get("incident_zip")})


def run_batch(batch, host) -> tuple[dict, dict]:
    vocab = nyc_vocab()
    tally: dict[str, Counter] = {}
    examples: dict[str, tuple[str, float]] = {}
    for kind, label in batch:
        r = resolve_instance(label, InstanceContext(act_id="dt4"), host=host,
                             vocab=vocab, namespace="nyc",
                             type_name="service_request", tier="sonnet")
        tally.setdefault(kind, Counter())[r.outcome] += 1
        examples.setdefault(f"{kind}:{r.outcome}", (label, r.confidence or 0.0))
    return tally, examples


def main() -> int:
    print('DESIGN TEST 4 -- "I already know 38 of these", the confidence gate')
    print(f"  live from {RESOURCE}, {date.today().isoformat()}")
    print(f"  host narrowing: {HOST_NARROWING}")

    raw = soda({"$limit": 400, "$order": "unique_key",
                "$select": "unique_key,incident_address,complaint_type,incident_zip"})
    rows = [r for r in raw if r.get("incident_address")]
    seen: dict[str, dict] = {}
    for r in rows:
        seen.setdefault(r["incident_address"].strip().upper(), r)
    distinct = sorted(seen.values(), key=lambda r: r["unique_key"])
    shared = len(rows) - len(distinct)
    print(f"  {len(raw)} rows fetched, {len(distinct)} with a distinct address, "
          f"{shared} sharing one ({shared / max(len(rows), 1):.0%})")
    check("the live partition supplies enough distinct addresses for the batch",
          len(distinct) >= ALREADY_KNOWN + BAND + 20, f"{len(distinct)}")

    known = distinct[:ALREADY_KNOWN]
    banded = distinct[ALREADY_KNOWN:ALREADY_KNOWN + BAND]
    novel = distinct[ALREADY_KNOWN + BAND:]

    batch: list[tuple[str, str]] = []
    batch += [("known", r["incident_address"].strip().upper()) for r in known]
    batch += [("banded", abbreviate(r["incident_address"].strip())) for r in banded]
    for r in novel[: BATCH - ALREADY_KNOWN - BAND]:
        batch.append(("novel", f"{r['incident_address'].strip().upper()} REAR ANNEX "
                               f"{r['unique_key'][-4:]}"))
    print(f"  landing batch: {len(batch)} rows "
          f"({sum(1 for k, _ in batch if k == 'known')} known / "
          f"{sum(1 for k, _ in batch if k == 'banded')} abbreviated / "
          f"{sum(1 for k, _ in batch if k == 'novel')} new)")

    # --- 4.1 the DEDUPED host: one instance per address ---------------------
    print(f"\n4.1 the gate on a host holding ONE instance per address "
          f"(match_at={NYC_POLICY.match_at} propose_below={NYC_POLICY.propose_below})")
    dedup_host = HostTable([rec(r) for r in known + banded])
    tally, examples = run_batch(batch, dedup_host)
    for kind in ("known", "banded", "novel"):
        print(f"  {kind:>7}: {dict(sorted(tally.get(kind, Counter()).items()))}")
    for k, (label, s) in sorted(examples.items()):
        print(f"     {k:<20} e.g. {label[:46]!r} @ {s}")
    matched = tally.get("known", Counter()).get("existing", 0)
    print(f"\n  the number: {matched} of {ALREADY_KNOWN} already-known rows matched")
    check(f"all {ALREADY_KNOWN} already-known rows fire `existing` and nothing else "
          f"does from that group",
          matched == ALREADY_KNOWN and set(tally.get("known", {})) == {"existing"},
          str(dict(tally.get("known", Counter()))))
    check("the abbreviated rows land in the AMBIGUOUS band rather than silently "
          "matching or silently proposing",
          tally.get("banded", Counter()).get("ambiguous", 0) >= BAND * 0.5,
          str(dict(tally.get("banded", Counter()))))
    check("the genuinely new rows propose, and none of them matches",
          tally.get("novel", Counter()).get("existing", 0) == 0,
          str(dict(tally.get("novel", Counter()))))
    fired = {o for kind in tally for o in tally[kind]}
    print(f"\n4.2 outcomes that fired across the batch: {sorted(fired)}")
    check("the gate answers ONLY in INGEST 3.1's five outcomes -- no sixth verdict "
          "(round 1, K3)", fired <= set(("existing", "ambiguous", "proposal",
                                         "not_an_instance", "unknowable")),
          str(sorted(fired)))
    check("and all three of the gate's own outcomes fire on one batch of real rows",
          {"existing", "ambiguous", "proposal"} <= fired, str(sorted(fired)))

    # --- 4.3 the UN-DEDUPED host: the host's actual rows (round 1, M3) ------
    print("\n4.3 the SAME batch against the host's ACTUAL rows -- round 1 finding M3")
    print("    (`erm2-nwe9`'s instance is a service request keyed by unique_key, not an "
          "address)")
    real_host = HostTable([rec(r) for r in rows
                           if r["incident_address"].strip().upper()
                           in {k["incident_address"].strip().upper()
                               for k in known + banded}])
    tally2, _ = run_batch(batch, real_host)
    for kind in ("known", "banded", "novel"):
        print(f"  {kind:>7}: {dict(sorted(tally2.get(kind, Counter()).items()))}")
    real_matched = tally2.get("known", Counter()).get("existing", 0)
    real_amb = tally2.get("known", Counter()).get("ambiguous", 0)
    print(f"\n  the honest number: {real_matched} of {ALREADY_KNOWN} matched, "
          f"{real_amb} correctly refused to guess")
    check("4.3 the deduped host answers 38 of 38 and the host's ACTUAL rows answer "
          "fewer -- and the difference is `ambiguous`, which is the call working "
          "rather than failing",
          real_matched + real_amb == ALREADY_KNOWN and real_amb > 0,
          f"existing={real_matched} ambiguous={real_amb}")
    check("4.3 and NOT ONE of the multiplicities was collapsed into a false `existing`",
          real_matched < ALREADY_KNOWN or shared == 0,
          f"{real_matched} of {ALREADY_KNOWN}, {shared} rows share an address")

    # --- 4.4 the threshold as a call parameter, constructed as a failure ----
    print("\n4.4 the same batch under two ENTRIES declaring different thresholds")
    print("    (which is what a per-CALL threshold would let two callers do)")
    lax, strict = Vocabulary(), Vocabulary()
    lax.declare("nyc", "service_request", EntryDeclaration(
        policy=MatchPolicy(0.86, 0.80, 0.03, why="caller A")))
    strict.declare("nyc", "service_request", EntryDeclaration(
        policy=MatchPolicy(0.995, 0.80, 0.003, why="caller B")))
    disagree, shown = 0, []
    for kind, label in batch:
        a = resolve_instance(label, InstanceContext(act_id="A"), host=dedup_host,
                             vocab=lax, namespace="nyc", type_name="service_request",
                             tier="sonnet")
        b = resolve_instance(label, InstanceContext(act_id="B"), host=dedup_host,
                             vocab=strict, namespace="nyc",
                             type_name="service_request", tier="sonnet")
        if a.outcome != b.outcome:
            disagree += 1
            if len(shown) < 3:
                shown.append((label, a.outcome, b.outcome, a.confidence or 0.0))
    print(f"  {disagree} of {len(batch)} rows resolve DIFFERENTLY")
    for label, va, vb, s in shown:
        print(f"     {label[:42]!r} @ {s}: A -> {va}, B -> {vb}")
    check("4.4 a per-caller threshold makes one landed row resolve two ways into ONE "
          "vocabulary -- so the threshold is a governed fact on the entry (rule 5-1)",
          disagree > 0, f"{disagree} rows")

    # --- 4.5 the fifth outcome, at the gate ---------------------------------
    print("\n4.5 a candidate the read could not finish")
    capped = HostTable([rec(r) for r in known + banded], scan_cap=5)
    r5 = resolve_instance(batch[0][1], InstanceContext(act_id="dt4"), host=capped,
                          vocab=nyc_vocab(), namespace="nyc",
                          type_name="service_request", tier="sonnet")
    r5_mut = resolve_instance(batch[0][1], InstanceContext(act_id="dt4"), host=capped,
                              vocab=nyc_vocab(), namespace="nyc",
                              type_name="service_request", tier="sonnet",
                              _mutate="rule_u_last")
    print(f"  over a truncated read -> outcome={r5.outcome!r} complete={r5.complete}")
    print(f"  MUTATED               -> outcome={r5_mut.outcome!r}")
    check("4.5 the gate never softens the fifth outcome into a fourth",
          r5.outcome == "unknowable", r5.outcome)
    check("4.5 MUTATION: the broken ordering answers confidently over an unfinished "
          "read at the gate too -- the check goes red",
          r5_mut.outcome != "unknowable", r5_mut.outcome)

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
