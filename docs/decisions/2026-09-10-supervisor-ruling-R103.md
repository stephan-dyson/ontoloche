# R103 — `A3` is CLOSED. The governance stop criterion stands down. The ACTIONS surface reopens.

**Supervisor ruling, 2026-09-10.** Closing the governance register's only entry, on evidence the supervisor
measured rather than accepted.

**Row 6g routed this rather than taking it**, on the reasoning that *"closing an entry is the same class of
act as opening one"* — the register's own standing rule 2. Its `6G-RUN.md` §8.3 states the pass condition
met and stops. **Nothing in that document reads as closing A3**, and the one sentence that did was fixed
first, at this supervisor's instruction, before any of the write-half evidence was measured.

---

## 1. What the criterion actually requires, and why it is no longer met

The criterion, armed by founder ruling [R100](2026-09-09-founder-ruling-R100.md):

> **An actor performs, or records as performed, a governed action that the surviving declaration reserves
> to a different authority — and no door refuses or warns.**

**The harm is an actor RECORDING. It is not the collapse.** That distinction decides this ruling, so it is
stated before the evidence rather than discovered inside it.

**[Observed — the supervisor's own run of `docs/tools/readside_a3_probe.py` against `aa77588`, in-memory
SQLite, no `force`, no acknowledgements]:**

| walk | shape | result at the landed state |
|---|---|---|
| **1** | both declare, row 6d's four keys **contradict** | `retire(successor=)` **REFUSED** `action_declarations_diverge`, `overridable=False` |
| **2** | the absorbed family declares **nothing** | collapse passes the retire door — **but** `resolve_type` answers `confidence=None` + `identity_stale`, `preflight` refuses the Haiku actor, and `record_invocation('old_verb','applied')` **REFUSES**. The survivor's ledger is never written to under a false authority because **the actor cannot record at all.** |
| **3** | four keys **agree**, families differ on **`preconditions`** — uncompared until `R102` | `retire(successor=)` **REFUSED** `action_declarations_diverge`, `overridable=False` |

**Walk 3 was the route by which A3 still fired**, and it is closed at the write door.

**So on every walk reachable by ordinary calls, at least one door refuses or warns.** The criterion's final
clause — *and no door refuses or warns* — **is not satisfied anywhere.** The criterion does not fire.

## 2. The both-halves test, and the correction that makes this defensible

[R100](2026-09-09-founder-ruling-R100.md) §4: *"A3 closes when both halves land."* Both have:

- **The read half**, row 6f under [R99](2026-09-09-founder-ruling-R99.md): `resolve_type` no longer hands a
  machine actor a clean 1.0 on a collapsed pair.
- **The write half**, row 6g under [R102](2026-09-09-founder-ruling-R102.md): the comparator sees all eight
  declared keys, so the collapse itself refuses.

**And one thing had to be corrected first, or this closure would rest on a false premise.** Row 6g's brief —
written by this supervisor — asserted *"a harm blocked by an accident is not blocked"*, on the strength of
row 6f's single probe walk showing **one** refusal on walk 2. **Row 6g measured three**, and only one of
them (`attributes_schema_violation`, by design as a rule and by accident as a governance defence) is the
accidental one. The other two — `preflight`'s approval check and `R99`'s read-side staleness — are
**deliberate governance defences**.

**That correction is load-bearing here.** Had walk 2's harm been blocked by a single accident, closing A3
would have been resting on luck. It is blocked by two deliberate defences and one accident, so it is not.

## 3. What this ruling does NOT do

- **The criterion stays ARMED.** The founder armed it and nothing here disarms it. **Armed and firing are
  different states**; it is armed and no longer firing, and it will fire again on the next entry that meets
  it.
- **The register's count stays at ONE.** Closing an entry does not remove it. The register counts **harms
  ever reached**, and A3 was reached.
- **The kill-row count stays TWENTY-THREE.** A build row is not a trip and a closure is not a trip.
  **`stop` remains RESOLVED by R99 and no sixteenth decline is recorded.**
- **`Q101` stays open and stays the founder's** — whether a per-key absence is agreement or a contradiction.
  A3 closing does not answer it, and `C3-21`'s fixture still pins it.
- **Per-key severity stays open and stays the founder's**, untouched in either direction as `R102` §4
  requires.
- **Defect B stays as row 6b left it.** The declare-nothing branch is unchanged; walk 2's collapse still
  passes the retire door. **It is closed as a HARM, not as a mechanism**, and that is exactly what this
  register counts.

## 4. Consequent — the ACTIONS surface reopens

**The stop in force since 2026-09-09 is lifted.** ACTIONS-surface rows may launch again.

The next queued row is the **skip census**
(`C:\Users\steph\.claude\fleet-supervisor\briefs\2026-09-09-oo-skip-census-followon.md`), and it is not
ACTIONS-surface work at all — it was never blocked by this stop, only sequenced behind row 6g.

## 5. The verification, listed so it can be attacked

Everything below was run by the supervisor against `aa77588`, not accepted from the row:

- `git ls-remote origin refs/heads/main` = `HEAD` = `aa775884df6f258e31ce46e53beed923adc12d1b`
- `21b2e86`, `7bf5442`, `aa77588` all ancestors of `origin/main`
- **four gates, all exit 0**: `check_links`, `check_spec_drift`, `check_merge_guard`,
  `check_capability_matrix`
- `6G-RUN.md` indexed in `docs/README.md`; working tree clean; beacon pin `802ddf02` still an ancestor
- the A3 probe re-run, table in §1 above
- the landed record swept for overstatement: **no sixteenth decline, nothing reading as closing A3** — the
  only match being row 6g's own table describing the sentence it fixed

Row 6g's suites, its numbers rather than the supervisor's: **sync 942 / 316 / 0**, **async 979 / 316 / 0**,
`postgres` + `sqlite` + `sqlite_minimal` **all three CONFORMANT on both legs**, coverage blocks captured
whole.

## 6. The sentence worth carrying out of this

Row 6g committed a census before its comparator, found three defects in its own instrument, demonstrated
its central prediction against two wrong implementations, verified its gate cells against a pristine
comparator, and checked five restraint claims — **and its adversarial round still found two BLOCKINGs that
closed a legal operation, non-overridably, at three doors.**

**Self-verification did not substitute for a fresh adversary.** Without the round this supervisor ruled,
that would have shipped, and this closure would have lifted a governance stop over the precise defect
`R102` §3 named.

Recorded by the ontoloche supervisor. Register: [`2026-09-07-governance-register.md`](2026-09-07-governance-register.md).
Row records: [`6F-RUN.md`](../runs/6F-RUN.md), [`6G-RUN.md`](../runs/6G-RUN.md).
