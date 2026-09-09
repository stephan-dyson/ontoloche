# The GOVERNANCE register — one word, two policies

**Opened 2026-09-07 by founder ruling [R97](2026-09-07-founder-ruling-R97.md)** (Q94, the founder's word:
*"separate"*). This register is **not** the kill row and its entries are **never** folded into the kill-row
count, which stays at **TWENTY-THREE**. It exists because the two failures are different in kind and
folding them would make one number that cannot be read:

| Register | The harm it counts |
|---|---|
| **Kill row** ([`2026-08-29-3c-rulings-R6-R12.md`](2026-08-29-3c-rulings-R6-R12.md)) | **Meaning destroyed by flattening.** Two distinct things end up answering to one identity. |
| **Governance** (this file) | **Authority granted that the declaration withholds.** One identity, correctly one, carries two contradictory governance answers — and the weaker one gets used. |

## Its stop criterion — **ARMED 2026-09-09 by founder ruling [R100](2026-09-09-founder-ruling-R100.md)**. Q97 is closed.

Written in the same spirit as `ROADMAP.md`'s kill criterion — now, while it is cheap to be honest, and
before the register has entries that would tempt it to be written favourably:

> **An actor performs, or records as performed, a governed action that the surviving declaration reserves
> to a different authority — and no door refuses or warns.**
>
> Reading if it fires: *the registry is granting authority it was told to withhold.* **Stop** — a curation
> layer that cannot hold the line on who may act is worse than no curation layer, because the record it
> produces reads as authorised.

**Q97 was the founder's, and on 2026-09-09 he ruled `arm`.** The criterion above is adopted **as written** —
`amend` was offered and not taken. It is **LIVE**.

> ### ⛔ THE CRITERION IS FIRED. Entry 1 (A3) meets it.
>
> This was disclosed before the word was given: the decision page said *"the criterion goes live and entry 1
> (A3) fires it immediately, because A3 is exactly that shape."* He armed it anyway, which makes the halt
> **deliberate** rather than an accident of drafting. See [R100](2026-09-09-founder-ruling-R100.md) for the
> clause-by-clause match and for what the firing does and does not halt.
>
> **In force:** no further ACTIONS-surface row launches until A3's doors refuse or warn; A3's fix is the
> gating work on that surface; and because the criterion's stated harm is that *the produced record reads as
> authorised*, any `applied` already written through this path is suspect and must be established rather
> than assumed absent.
>
> **Not halted:** the project, and the read-side row opened by [R99](2026-09-09-founder-ruling-R99.md) — a
> different surface, and one whose ruling removes A3's delivery step. Firing adds **no entry**: this register
> still counts **ONE**, and standing rule 1 keeps it out of the kill-row count, which stays at **TWENTY-THREE**.

*(Numbering note: Q97 was previously earmarked-if-numbered for R95's across-kinds question
(`alias_collision` across kinds at `import`/`reinstate` under `PACKAGE.md` §4.1). That question is still
**surfaced, not minted**, and becomes **Q98 if numbered**.)*

---

## Entry 1 — A3: two action families' governance collapses, and a machine actor acts on the weaker half

**Found** by row 6d round 1's actions lens; countersigned **not a kill-row trip** by
[R91](2026-09-04-6d-supervisor-ruling-R91.md), which minted Q94 out of it. Full record:
[`6D-RUN.md` §6.2](../runs/6D-RUN.md) (finding A3, line ~452).

**The defect.** Two action families with **contradictory governance declarations** are collapsed with no
refusal and no warning. Afterwards `resolve_type` answers the dead word with the survivor at **1.0**, while
`preflight` answers the same word with the **tombstone's** policy — and a **Haiku-tier machine actor records
`applied` against a verb the surviving family declares human-approval-only and irreversible.**

**Reachability — the worker's own re-run with `force` removed and ALL acknowledgements removed
[Observed], which NARROWED the lens's claim and the narrowing is kept:**

| door | ordinary-calls result |
|---|---|
| `retire(successor=)` | **`('RETIRED','retired',[])`** — no `force`, no acknowledgement |
| `import_types` | **`('new_verb',['old_verb'],[])`** — **warnings EMPTY**, no `force`, no acknowledgement |
| `merge_types` | `('REFUSED','definitions_diverge', overridable=True)` — **not** silent, but **acknowledgeable past** |

**So it stands on TWO of three doors with ordinary calls, not three.** The merge door's defect is weaker and
different: an *overridable* `definitions_diverge` is the only thing between a caller and a collapse that
`preflight` treats as **non-overridable** at invocation time.

**Severity: BLOCKING, and as of 2026-09-09 it FIRES THIS REGISTER'S ARMED STOP CRITERION** (R100). Separate
register does **not** mean deferred, and does not mean fixed either — it is **open and unfixed**, and the
surface is now halted on it rather than merely labelled. **[R99](2026-09-09-founder-ruling-R99.md) removes
its DELIVERY** — `resolve_type` may now refuse or answer below 1.0 instead of handing the machine actor a
confident survivor — **but does not close it**: the two write doors above still neither refuse nor warn on
ordinary calls. **A3 closes when both halves land.** Contract ids `C19-97`, `C19-98`, `C19-99` were added by row 6d for the
declaration operand §5.10's refusal #2 never had, with `C19-99` pinning only the case where the four
governance keys are byte-identical.

**Class.** The ninth kill-row trip's class at the ACTIONS surface, and the **mis-governed cell (`I-7`) in
shipped code for the first time**.

**Why it is not a kill-row trip.** Recorded honestly, because the reason first given was wrong: the
justification on file was *"the identity criterion is not met — one word, ONE identity, TWO policies,"* and
**that does not hold** — `resolve_type` and `preflight` answering one word differently *is* two things
answering to one identity, which is how the register reads the criterion in its own published documents.
R97 rules it separate for a different and better reason: a count that grows on a widening definition stops
being a signal. See R97 for the full argument.

---

## Standing rules for this register

1. **Entries are never folded into the kill-row count**, and the kill-row count is never quoted as
   including them.
2. **A construction reaching this harm is routed to the supervisor and never self-classified** — the same
   rule the kill row runs under.
3. **An entry states its reachability with `force` and acknowledgements REMOVED**, door by door. A finding
   that needs `force` is recorded with that fact in the same table, not in a footnote.
4. **The reason an entry is or is not in this register is stated with its evidence**, and a reason later
   found wrong is corrected in place with the correction visible — as Entry 1's is.
