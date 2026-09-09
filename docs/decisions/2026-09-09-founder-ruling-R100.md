# R100 — Q97 is ruled `arm`. The governance register's stop criterion is live, and entry 1 fires it.

**Founder ruling, 2026-09-09. His word: `arm`.**

The criterion, as drafted on 2026-09-07 and now **ARMED unchanged**:

> **An actor performs, or records as performed, a governed action that the surviving declaration reserves to a different authority — and no door refuses or warns.**
>
> Reading if it fires: *the registry is granting authority it was told to withhold.* **Stop** — a curation layer that cannot hold the line on who may act is worse than no curation layer, because the record it produces reads as authorised.

---

## 1. It fired on arming, and that was disclosed before the word was given

The decision page stated the consequence plainly and ahead of the ruling:

> **`arm`** — the criterion goes live and **entry 1 (A3) fires it immediately**, because A3 is exactly that shape. That is the honest consequence and you should know it before saying the word.

He armed it anyway. **This is a deliberate choice to make the halt real, not an accident of drafting**, and the record says so because a criterion that fires the day it is armed invites exactly the opposite reading later.

## 2. Why A3 satisfies the criterion, clause by clause

| Criterion clause | A3's [Observed] fact |
|---|---|
| *an actor performs, or records as performed* | a **Haiku-tier machine actor records `applied`** |
| *a governed action that the surviving declaration reserves to a different authority* | against a verb the surviving family declares **human-approval-only and irreversible** |
| *and no door refuses or warns* | `retire(successor=)` → `('RETIRED','retired',[])`, no `force`, no acknowledgement; `import_types` → `('new_verb',['old_verb'],[])`, **warnings EMPTY** |

All three clauses are met on **ordinary calls with `force` and every acknowledgement removed** — the register's standing rule 3 — on two of the three doors. The third, `merge_types`, refuses with an *overridable* `definitions_diverge`, which is weaker and is recorded as weaker rather than counted as a fourth clause.

**The criterion fires. It is not a close call and it is not being read generously.**

## 2b. CORRECTION, same day — two rows of the table above do not reproduce at `HEAD`

**The ruling stands. The evidence I gave for it was partly stale, and that is mine.**

Row 6f measured A3 at `HEAD` and **routed the discrepancy to the supervisor rather than classifying it**.
The supervisor then **re-ran the probe itself** rather than adopting the report
(`docs/tools/readside_a3_probe.py`, in-memory SQLite, no `force`, no acknowledgements, changes nothing):

| clause row above | what actually happens at `HEAD` |
|---|---|
| `retire(successor=)` → `('RETIRED','retired',[])` | **`REFUSED action_declarations_diverge`, `overridable=False`.** Does **not** reproduce. |
| `import_types` → **warnings EMPTY** | The alias is **not written**; warnings carry `near_duplicate` and `import_refused:alias_collision`. Does **not** reproduce. |
| the machine actor records `applied` with nothing refusing | **Reproduces** — but by a different route than the table claims. |

**Why.** Commit `304967a` — *"A3 CLOSED … the DECLARATION operand §5.10's refusal #2 never had for an
action family — at all THREE collapse doors"* — landed **2026-09-05**. The governance register was opened
**2026-09-07** and recorded row 6d's **round-1** observation **in the present tense**. I wrote §2's clause
table on **2026-09-09** by reading that entry, and **I did not re-run it**. A citation that was accurate
when taken is not accurate when carried, and I carried this one into a founder ruling.

**The criterion still fires, on evidence that does reproduce.** Two action families whose four *compared*
governance keys **agree** and whose **`preconditions` differ** collapse with no refusal, no `force` and no
acknowledgement; `resolve_type` then answers the dead word `existing` / survivor / **`confidence=1.0`**; a
Haiku-tier actor records `applied`; and the survivor's ledger reads **`n=0`**, the record filed under the
dead word. Every clause of §2 is met. **`arm` produced the correct outcome.**

**Why the founder is being TOLD and not RE-ASKED.** The conclusion he ruled on — *does A3 fire this
criterion* — is unchanged, and re-putting a question whose answer has not moved would waste the one thing
this project asks of him. But he ruled on a stated reachability, part of which was stale, and this project's
own discipline is that a reason later found wrong is **corrected in place with the correction visible**
(the governance register's standing rule 4, and [R97](2026-09-07-founder-ruling-R97.md)'s own precedent of
correcting its reason rather than editing it away). So the correction is on his page as an FYI, not as a
new decision.

**What this changed underneath the ruling.** A3's *mechanism* is no longer the one §2 tabulates. The doors
**do** refuse on contradictory declarations. The harm now arrives because **`_GOVERNANCE_KEYS`
(`registry.py:8104`) compares FOUR keys while `ACTIONS.md` §2.2 declares EIGHT** — `inputs`,
`preconditions`, `reachability` and `payload_schema` are never compared, so the comparator cannot see the
contradiction it exists to catch. Deciding which of the eight are *governance* decides what the registry
refuses, which is the founder's, and is minted as **`Q99`**.

**The register's count stays at ONE.** This is one harm reached by a second route, not a second harm.
Minting `A4` would be the *"count that grows on a widening definition"* failure R97 ruled against.

## 3. What the firing means, operationally

The criterion's own reading is the instruction: **stop**, on the governance surface, because *the record it produces reads as authorised*.

Concretely, and no wider than the criterion warrants:

1. **No further ACTIONS-surface row launches** until A3's doors refuse or warn. A3 has been BLOCKING and open since 2026-09-07; the difference is that it is now a **halt**, not a severity label.
2. **A3's fix becomes the gating work on that surface**, ahead of anything else queued there.
3. **The harm is a record problem, not only a behaviour problem.** The criterion says the danger is that the produced record *reads as authorised*. Any `applied` already written through this path is suspect, and the row must establish whether such records exist in the fixtures rather than assume they do not.

**What it does NOT mean.** It does not halt the project. It does not halt the read-side row that [R99](2026-09-09-founder-ruling-R99.md) opens — a different surface, and one whose ruling removes A3's delivery step. It is not a kill-row trip: standing rule 1 of the register is that entries are **never** folded into the kill-row count, which stays at **TWENTY-THREE**. A governance stop and a kill-row `stop` are different criteria on different registers, and this document is not evidence for the other one.

## 4. The interaction with R99, stated because it changes the work

R99 rules Q56 `read`, which authorises `resolve_type` to answer below 1.0 or refuse when an identity claim does not re-establish at the read. A3's harm is delivered by `resolve_type` answering the dead word with the survivor **at 1.0** while `preflight` answers it with the tombstone's policy.

So **R99 removes A3's delivery step, and R100 halts the surface until A3's write doors are also fixed.** The two rulings meet on one entry from opposite ends. Neither closes A3 alone:

- Without the write-door fix, a governed collapse still happens silently, and a caller that never touches the resolver still gets an unauthorised record.
- Without the read-side fix, the collapse still delivers a confident wrong answer to anything that resolves the word.

**A3 closes when both halves land.** Until then it stays open, and the criterion stays fired.

## 5. Register bookkeeping

- The criterion moves from **drafted, not armed** to **ARMED by R100**, text unchanged. An amendment was offered (`amend`) and not taken.
- Entry 1 (A3) is annotated **FIRES THE CRITERION**, with the clause table above.
- The governance register's count stays at **ONE**. Firing does not add an entry, and this ruling does not.
- Q97 is closed. The numbering note stands: R95's across-kinds question (`alias_collision` across kinds at `import`/`reinstate` under `PACKAGE.md` §4.1) remains **surfaced, not minted**, and becomes **Q98 if numbered**.

Recorded by the ontoloche supervisor. Register: [`2026-09-07-governance-register.md`](2026-09-07-governance-register.md). Entry 1's full record: [`6D-RUN.md` §6.2](../runs/6D-RUN.md), finding A3. Same-day rulings: [R99](2026-09-09-founder-ruling-R99.md), [R101](2026-09-09-founder-ruling-R101.md).
