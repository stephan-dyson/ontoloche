# R91 — the FIFTEENTH and SIXTEENTH trips, both PREDICTED before the lens ran; two constructions that are not trips; and `stop` put for the twelfth time

**Ruled 2026-09-04 by the ontoloche program supervisor**, countersigning the four constructions row 6d
routed at [`6D-RUN.md` §6.2 and §6.3](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
(`aa6d2e5`, `3126023`). Follows [R89](2026-09-04-founder-ruling-R89.md) and
[R90](2026-09-04-6d-supervisor-ruling-R90.md).

## Verification, done here rather than accepted

Every countable claim the two records rest on was re-run by the supervisor:

- **[Observed]** `ontoloche/registry.py:4216` — `if "predicate" in (here.kind, there.kind):` — the
  deliberate skip A3 describes.
- **[Observed]** `_word_rows` is called at `registry.py` **2176**, **2658** and **4769** — the three mint
  doors A1 names. **[Observed]** `def _alias_clash` is at **7432**.
- **[Observed]** in `docs/tools/check_merge_guard.py`: `kind="action"` **0**, `preflight` **0**,
  `record_invocation` **0**, `approval_mode` **0**, `reversibility` **0**, `ActionFamily` **0**. In
  `ontoloche/contract/test_c19_actions.py`: `successor=` **0**, `reinstate(` **0**.
- **[Observed]** `py docs/tools/check_merge_guard.py` → **exit 0** at HEAD with all four findings live.

One note on the code-reading rather than the behaviour: the record says `_alias_clash` *"filters by no
kind at all"*; the supervisor's count of `kind` in 7432–7470 is **3**, which neither confirms nor refutes
that sentence. The **behavioural** evidence — `reinstate` refusing `alias_collision` after a cross-kind
mint, re-run by the worker with ordinary calls on both legs and in both directions — is what the ruling
rests on, and it stands.

## R91, part one: A1 is the FIFTEENTH trip and F4 is the SIXTEENTH

**The kill-row criterion is identity:** a state reached by ordinary calls at shipped doors in which two
rows answer to one word. Both of these reach it.

**A1 — the fifteenth trip: a retired family's word is free at every mint door ONE KIND ALONG.** A word a
retired `kind="action"` family still holds as an alias is minted as a `kind="predicate"` row's **name**
with no refusal and no warning; `resolve_type` then answers the new row at 1.0 while the tombstone still
holds the word; `reinstate` refuses `alias_collision` non-overridably. Five ordinary calls, no `force`, no
acknowledgement, **both directions, both legs**, and F1 shows it is **not action-specific** —
`predicate` tombstone → `entity` mint reaches the same state at all three doors. The same-kind controls
answer `word_previously_retired` and reinstate cleanly, which is what proves this is a defect and not the
design. **Fix is a mutation survivor in both directions** (F1: widening the scan to all kinds leaves the
gate at exit 0). Countable gate reason: `kind="action"` **0** — every axis-10 fixture is one kind on both
sides.

**F4 — the sixteenth trip: the same word arriving as an incoming ALIAS is free at three doors.** The
trip-14 fix closed the word arriving as a **name**. Arriving as an **alias** it passes
`_alias_identity_breach` at `registry.py:7023` — `_word_rows(namespace, alias)` with `match_aliases`
defaulted to `False`, **the exact operand whose absence IS the fourteenth trip**, its `why` discarded in
the same line. Reached at `import_types`' alias write, `retire(successor=)`'s R75 transfer, and
`merge_types`' word move. `resolve_type` answers the new row at 1.0 while the tombstone holds the word;
`reinstate` refuses with **`path_back=None`** — worse than the door it descends from. **Fix is a
one-line mutation survivor** (`match_aliases=True` closes all three doors and the shadow gate still exits
0). Countable gate reason: axis 10's door list is literally `("propose_type", "import_types", "approve")`
— three mint doors, zero alias-write doors, zero transfer doors.

**Both are countersigned as trips. The count is SIXTEEN.**

## R91, part two: they are two cells of ONE table, and the table is named

Trip 14 closed one cell: **(retired word × arrives as NAME × same kind × mint door)**. R85 and R86 ruled
that this register names tables rather than counting doors, so it does:

| dimension | trip 14 closed | fifteenth opens | sixteenth opens |
|---|---|---|---|
| **how the word arrives** | as a name | as a name | **as an alias** |
| **the holder's kind** | same kind | **a different kind** | same kind |
| **the door** | mint | mint | **write / transfer** |

That is a **2×2×2 with eight cells**, of which the fourteenth trip's fix and axis 10 drove **exactly
one**. The two trips are counted separately because each is a distinct construction reaching the harm —
the register's standard since trip 1 — **and they are closed in ONE change**, with one mutation per cell
so no cell is left as a survivor. The fix commit enumerates all eight cells and says which it closes and
which it declines (R85, R88).

## R91, part three: both trips were PREDICTED, and that is the fact the founder is owed

**§0.3 predicted both before any lens or probe existed** — checkable at `d4b86a8`:

- **T14** predicted *"the open cell is (aliases × retired × a different kind), and the three guards give
  three different answers to* does any row answer to this word?" **That is A1, by cell.**
- **T11** predicted the F4 call site **by name and by line** — `_alias_identity_breach`, `registry.py:7023`.
  **That is F4, by address.**

Every one of the previous fourteen trips was found by a lens that surprised the row. **These two were
named in writing, then constructed.** And no build row shipped code through either door between the
prediction and the finding — which is what R89 opened this row to make possible, and what R88 said the
loop had never demonstrated. **This is the first prevention in the register's history, and it is
recorded as such.**

## R91, part four: A3 and F5 are NOT trips

**A3 — not a trip; the ninth trip's class at the ACTIONS surface; BLOCKING; and it raises Q94.** Two
action families with contradictory governance declarations collapse through `retire(successor=)` and
`import_types` with no refusal — the worker's re-run with `force` and acknowledgements removed narrowed
the lens's "three doors" to **two**, and the narrowing is kept. `resolve_type('old_verb')` answers
`new_verb` at 1.0; `preflight('old_verb')` answers **auto / reversible**; `preflight('new_verb')`
answers **human / irreversible**; a Haiku-tier actor records `applied` against the dead word and the
survivor's ledger is empty. **One word, one identity, two governance answers.** The identity criterion
is not met — the word resolves to one row — so this is not a kill-row trip. It is the ninth trip's
sentence at a surface never asked (*a guard that cannot read a fact must compute it if computable*; the
declarations are stored attributes and refusal #2 is skipped at 4216 with nothing put in its place), and
it is **the mis-governed cell (`I-7`) reached in SHIPPED code for the first time**. Countable gate
reason: the gate cannot construct an action family at all (six zeros above). **Q94, for the founder:**
*does the kill criterion extend to governance identity — one word answering with two policies — or is
that a separate register?* The supervisor's default until ruled: **separate**, recorded beside the trips,
never folded into their count.

**F5 — not a trip; the tenth trip's class and trip 4's shape; BLOCKING.** `_alias_holder`'s exact
self-skip (`registry.py:2624`) was written for a caller whose row exists; at `_write_approved` the row
does not exist yet, so the skip fires on a **stranger**, the refusal is unreachable for the exact
spelling, and `approve` **raises `AlreadyExists`** out of a specified governance call whose contract is a
`TypeEntry` or a `Refusal`. **[Observed, worker-verified]** `AlreadyExists` appears nowhere in
`INTERFACE.md`. The guard works on the variant and crashes on the ordinary case. **No second row is
written** — case C's second `approve` raises rather than writes — so the store does not end holding two
rows for one word: **fail-closed by accident.** Not a trip. The async mirror is `[Inferred]` only, as the
lens honestly recorded.

## R91, part five: `stop` is put for the TWELFTH time

Two trips in one round oblige the put. **Recommendation: continue, and the reason is the opposite of
every previous put.** Fourteen times the counterweight was *"the design is still not what tripped."*
This time the counterweight is that **the row said where both trips would be before it looked, and no
code shipped through those doors in between.** R88 told the founder the loop had demonstrated finding
and not preventing; **it has now demonstrated preventing, twice, within one round of being given the
configuration to do it.** That is R89's decision working. The founder rules.

## What row 6d's worker does with this

1. Record the fifteenth and sixteenth trips at §6.2 A1 and §6.3 F4 as **countersigned**, in the
   fourteen records' shape, with this ruling as the countersignature; update every count that reads
   fourteen to **sixteen** (`6D-RUN.md`, `STATUS.md`, the register).
2. Record A3 and F5 as **not trips**, with the classes above; carry Q94.
3. Fill §0.7 for **T14** and **T11** as **CONFIRMED — by construction, before any fix**, and for every
   other T/N/S row the three lenses reached, with unreached rows marked *not reached*.
4. When the round closes: **ONE change over the 2×2×2**, one mutation per cell, the commit enumerating
   all eight cells and listing what it declined. A3's fix is a **separate** change — it is a different
   table.
5. Do not touch the count yourself; it is sixteen because this ruling says so.

## Unchanged

Q56 remains the class-closing question for the read side and the founder's. Standing rules (a)–(e) stand.
The `INGEST` build row is not open. Beacon's pin is unaffected — **[Observed]** no product file has
changed since R89; the fix set will be the first to touch `ontoloche/registry.py`, and the supervisor
re-checks the pin when it lands.

Next ruling number: **R92**. Next question number: **Q95** (Q94 is minted here).
