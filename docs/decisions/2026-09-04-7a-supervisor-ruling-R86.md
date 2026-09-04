# R86 — the nine constructions are SIX cells plus one new one; a record is a cell, not a construction; standing rule (e) gains the governed facts

**Ruled 2026-09-04 by the ontoloche program supervisor**, on the numbering
[`7A-RUN.md` §6.9b](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md)
routed to the supervisor: *"§6.5a and §6.6a carry `I-2`…`I-6` as proposed labels only; the final
`I-n` assignment, and whether any of the nine is something other than an instance-surface record,
is ruled rather than assumed."* Read after [R83](2026-09-04-7a-supervisor-ruling-R83.md),
[R84](2026-09-04-7a-supervisor-ruling-R84.md) and [R85](2026-09-04-7a-supervisor-ruling-R85.md).

## First, a correction to R85 rather than a claim of foresight

R85 built its one-table framing on **six** records. §6.9b lists **nine** constructions. The table
is **extended** by this ruling; it did not already cover them, and this ruling says so rather than
reading the extra three back into R85 as though they had been anticipated.

## R86, part one: a record is a CELL, not a construction

The four constructions R85 did not number — B1, B2, B5 and D3 — do **not** become `I-7`…`I-10`.

**A record in this series is a cell of the table.** Numbering each construction separately is
precisely the error the fourteenth countersignature diagnosed: trips 8, 12, 13 and 14 were counted
as four separate things for three build rows before anyone saw they were four quadrants of one
table, and that mis-seeing is what cost the programme three rounds. Having just named the table,
this register does not go back to counting doors.

**The worker's own mapping is adopted for three of the four**, and it is a real result that it
needed no new cell for them:

| construction | cell it falls in |
|---|---|
| **B1** — rule 4-10 has no type scope, so a `task` reuses a `project`'s `CandidateRef` | **mis-keyed**, `I-4`, on the *type* half of the key rather than the label half |
| **B2** — rule 4-11 asks a door with no `label` filter that returns the oldest 100 | **mis-timed** (`I-5`) **and truncated** (`I-1`) at once — an identity read that reads one page and decides |
| **B5** — rule 4-10's memory is written only on the `proposed` branch | **mis-written**, `I-3` |

## R86, part two: D3 does not fit, and the table gains a seventh cell

**The worker's mapping of D3 to `I-2` (*"mis-walked at the governed-fact half"*) is rejected.**
Verified against D3's own construction at §6.8b: the chain walk **succeeds** and the extent is
**right**. Nothing about *which rows are in the set* goes wrong. What changes is **which rules the
set is judged by** — the successor's `MatchPolicy` and the successor's `Condition` are swapped in
under a caller who named the predecessor.

That is a different axis, and the evidence is that it produces a failure the other six cannot:

- **[Observed]**, design test 3's CA+CO fixture: control → `existing #555338 CA`, *"CO rows visible
  to this CALIFORNIA caller: 0"*; after one `retire(successor='ltc_facility')` →
  `ambiguous known=2`, *"CO rows visible to this CALIFORNIA caller: 1"* — **R59's stated reversal
  condition, reached by retiring a type rather than by omitting a keyword.**
- **[Observed]**, the policy half over the same data: **73 of 1,373 real CMS labels resolve
  differently once `facility` is retired.**
- **§5.1's rule 5-6 is defeated in its own terms** — *two entries may declare different policies;
  two callers may not* — because here **one caller gets both policies.**

So the table gains a **seventh cell, `I-7` — mis-governed: the set is right and the facts that
govern the decision belong to another entry.**

**Aggravating, and verified here rather than accepted:** rule 5-7 (`C20-41`) has no carrier.
**[Observed]** `InstanceResolution`'s printed shape in `INGEST.md` contains **zero** occurrences of
`policy`, and the shipped carrier at `ontoloche/actions.py:689–693` declares `approval_mode`,
`min_auto_tier` and `reversibility` — **not** the three match thresholds. A rule about which policy
governed an answer cannot be checked when the answer cannot say which policy governed it.

## R86, part three: standing rule (e) is amended before it is ever recorded

R85 proposed standing rule (e) over six cells and its wording is about the *set* alone. The seventh
cell is outside that wording, so the rule is amended now rather than shipped and patched:

> **The extent an identity is decided over, AND the facts that govern the decision, are the same at
> every door that reads it, writes it, keys it, gates it or counts it — and a door that cannot
> prove both answers `unknowable` rather than deciding.**

## What this requires of the fix set

`I-7` is **not** closed by the extent fixes, and the row must not let it ride out on them.

1. **§5, §6 and §7 must say whether a successor inherits its predecessor's `MatchPolicy` and
   `Condition`.** The document's own §7.2 makes the successor's entry *someone else's to declare*,
   which points hard at **no inheritance** — the walk stops, or answers `unknowable`, when the
   governed facts differ across a hop. **That decision is the row's to take and record; it is not
   the supervisor's to design.** Take it, state it as a numbered rule, and construct against it.
2. **Rule 5-7 gains a carrier in the same change**, or the row records that it has none and prices
   that in §10. An uncarryable rule is unfalsifiable, which is the indictment axis seven earned.
3. **§4.4 names three amendments and does not name this one.** If closing `I-7` asks a fourth thing
   of `ACTIONS.md`, it is named there with the other three and routed through **Q91**.
4. **If the honest answer changes what the registry declines to serve** — as Q56 does on the read
   side — it stops being the row's and becomes the founder's. Raise it as **Q91** with the shipped
   behaviour as the default, in the shape Q56 was raised in.

## Unchanged

Kill-row trip count is **fourteen** across all nine constructions; **[Observed]** re-verified by the
supervisor this cycle — `resolve_instance` occurs **0** times in `ontoloche/` and row 7a has touched
**0** product files. `stop` is not put by any of them. Q56 remains the class-closing question for
the read side and the founder's. The dedicated identity-surface row's lens set is **seven cells over
nine constructions**, which is a materially better brief than either the fourteen trip records alone
or a list of nine doors.

## What row 7a's worker does with this

1. Record the final numbering at §6.9b: **`I-1`…`I-6` stand as countersigned**; B1, B2 and B5 are
   **constructions within** `I-4`, `I-5`+`I-1`, and `I-3` respectively, not new records; **D3 is
   `I-7`, a new cell — mis-governed.**
2. Correct §6.9b's own mapping line for D3, which assigned it to `I-2`.
3. State standing rule (e) in the amended seven-cell form, not R85's six-cell form.
4. Extend the fix set per "What this requires" above; turn the `I-7` mutation red like the other six.
5. Do not increment the kill-row count anywhere.

Next ruling number: **R87**. Next question number: **Q91**.
