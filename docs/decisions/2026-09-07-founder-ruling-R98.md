# R98 — FOUNDER RULING (Q95): `C12-09`'s narrowing is KEPT; the residual's second half is routed to row 6e as an unverified construction

**Ruled by the founder, 2026-09-07 ~10:4x.** The founder's words, verbatim: **"go with your recommendation
on 3."** The supervisor's recommendation was **keep**, plus a fourth option none of the three on offer
covered. Recorded by the ontoloche program supervisor. This closes **Q95**, raised by row 6d's change 1
(`9a4e140`) and folded into the founder item with Q94.

## What was asked

Cells 3 and 4 of ruling [R91](2026-09-04-6d-supervisor-ruling-R91.md)'s 2×2×2 — *a tombstone whose own
**NAME** is a word `merge_types` or `retire(successor=)` is about to move onto a live row* — were
**declined** by change 1 rather than closed, because closing them with the rule that closes cells 5–8 would
**reverse a narrowing `C12-09` pins on purpose.** `PACKAGE.md` §6.2's row for `C12-09` reads, verbatim:

> *"**and an imported alias between two identical non-empty extents is still written** — the half a careless
> fix deletes. §5.10 refusal #2 permits that collapse (`C10-09` narrowed the guard rather than closing the
> operation), so a fix that refused every predicate alias would pass a suite asserting only refusals while
> removing a legal write."*

That last clause is Q95 written in advance, by the row that pinned the id.

## Ruled: KEEP (option 1 of the three)

`C12-09` stands untouched. The rule binds **aliases only**. Two reasons, both evidential:

1. **The marginal harm is unproven.** Round 3's kill-row lens drove the transfer doors and **could not build
   a harm the blessed `C12-09` write does not already produce one door earlier** (`6D-RUN.md` §6, ~line
   1695). The decline stands on the evidence available, not on convenience.
2. **Option 2 is the mistake this project had just finished making.** `C10-09`, `C12-09`, `C12-15` and
   `C16-07` all exist because *a fix that closes a legal operation is worse than the defect it closes* — and
   round 3's own `effects`-order false refusal **closed a legal operation for two rounds**. Overturning
   `C12-09` would repeat that deliberately, one ruling along. Option 3 (the three-call succession path) is
   not taken either: it is a real API-shape change and it should not be decided while row 6e is auditing
   whether this whole class of fix is the right approach at all.

**The residual is REAL and stays on the record**, unchanged from how change 1 stated it: a tombstone whose
own name is moved onto a live row by `merge_types` or `retire(successor=)` is left **un-reinstatable**, and
the gate records the gap rather than hiding it — `check_merge_guard.py` axis 11 drives the six closed cells
and **not** cells 3 and 4, and `_retired_holder`'s docstring states the cut.

## The part that is NOT ruled, and is routed rather than adopted

All three options on offer treat the residual as one thing. **It is two:** (a) the row is left
un-reinstatable, and (b) **no door says so.** Every option costs either a legal write or an API shape
because each tries to fix (a).

**Nobody proposed fixing (b) alone** — *warn on the write when a tombstone answers to the word*, disclosing
the un-reinstatable state at the moment it is created instead of leaving it to be discovered. It removes no
legal write, needs no three-call path, and `warnings` is already the mechanism for exactly this (39 values;
`Refusal.warnings` landed at `4f8db52`).

**This is the supervisor's own construction, not the run's, and it is NOT adopted here.** It has not been
verified constructible at both transfer doors, and the standing rule is that a construction is routed and
checked, never self-classified — a rule that binds the supervisor exactly as it binds a worker. It goes to
**row 6e** to **verify or kill**, with its falsifier stated: *if a warning at that write cannot be emitted
without also refusing a `C12-09`-blessed write, the idea is dead and the residual stays silent.*

Row 6e writes no product code, so it does not implement this even if it verifies. It returns a verdict.

## Numbering

Kill-row count stays **TWENTY-THREE**; governance register stays at **ONE**. **Q95 CLOSED.** Next ruling
**R99**. Open with the founder: **Q97** (the governance register's drafted, unarmed stop criterion) and the
`oo-pg` residue `r3lens_de7fdace`. R95's across-kinds question is still surfaced, **Q98 if numbered**.
