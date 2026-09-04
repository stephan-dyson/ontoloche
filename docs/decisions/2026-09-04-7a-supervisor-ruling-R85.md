# R85 — Records A–D countersigned as `I-3`…`I-6`, the family is named as one table, and standing rule (d) becomes countable

**Ruled 2026-09-04 by the ontoloche program supervisor**, on the four records row 7a's worker
routed at [`7A-RUN.md` §6.7a](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md),
landed at `fda44a1`. Read alongside [R83](2026-09-04-7a-supervisor-ruling-R83.md) (which minted the
`I-n` series) and [R84](2026-09-04-7a-supervisor-ruling-R84.md) (which countersigned `I-2`).

## Verification, done here rather than accepted

The worker re-derived the lens's CMS figures itself rather than quoting the lens, which is the
standard. The supervisor spot-checked its three countable-absence claims:

- **[Observed]** `grep -c successor docs/tools/ingest_act_probe.py` → **0**
- **[Observed]** `grep -c successor docs/tools/ingest_seam_probe.py` → **6**
- **[Observed]** `grep -c 'reviewed_by *=' docs/tools/ingest_act_probe.py` → **1**

All three reproduce exactly. The successor lives in one probe and the ledger in another, and no
construction put them in one room — which the record correctly calls *trip 14's own count shape
verbatim*.

## R85, part one: the classification

**Records A, B, C and D are instance-surface records `I-3`, `I-4`, `I-5` and `I-6`. The kill-row
trip count stays at FOURTEEN. `stop` is not put** — it attaches to trips, and these are not trips
by the test R83 set and R84 applied: each is constructed against `INGEST.md` and a throwaway kit,
with no shipped door in the construction.

| record | finding, in one line | id |
|---|---|---|
| **A / Z1** | Rule 3-14 binds the identity READ and no door that WRITES; one `retire(successor=)` between two acts mints a second identity with every §3 rule firing correctly | **`I-3`** |
| **B / Z2** | The act's scope key is the raw label and the gate's is `norm`; **[Observed]** 71 normalised keys carry more than one raw spelling | **`I-4`** |
| **C / Z4** | A drained-but-unwritten proposal is invisible to rule 4-11 — the guard asks who holds an *unreviewed* proposal, not who holds one | **`I-5`** |
| **D / Z7** | The tied set dedupes on `ref_key`, so two host records under one `instance_id` collapse to one and answer `existing` at 1.0 with `known=1` | **`I-6`** |

## R85, part two — the substance: this is ONE table, and it is closed as one change

Six instance-surface records now exist and they are not six defects. They are **one question
asked at six doors**: *which host rows answer to this identity, and did the resolution see all
of them?* In every record the answer is decided over a set that is **not the identity's extent**,
and the records differ only in **how** the set went wrong:

| the set is wrong because it was… | record |
|---|---|
| **truncated** — the scan stopped and said so, and the match path ignored the `why` | `I-1` |
| **mis-walked** — the chain was followed one hop and reported `complete=True` | `I-2` |
| **mis-written** — the read is bound by the chain and the write door is not | `I-3` |
| **mis-keyed** — the act scopes on the raw label, the gate decides on `norm` | `I-4` |
| **mis-timed** — the guard's window closes when the proposal drains, before the write lands | `I-5` |
| **mis-counted** — the page's own ids are not required to be distinct, so two rows collapse to one | `I-6` |

**The fourteenth countersignature's lesson applies directly and is the reason this ruling exists.**
Trips 8, 12, 13 and 14 were four quadrants of one table, closed **one quadrant at a time over three
build rows**, because each round closed the quadrant it found and stopped. That cost the programme
three rows' worth of loop. This row has the whole table in front of it, in one round, before any
code exists.

**So: `I-3` … `I-6` are NOT fixed one at a time in the order the lenses found them.** The worker's
own sequencing note — *"Z1 … it is the fix to make first"* — is right about Z1 being load-bearing
and wrong about the shape. The row writes **one change** that states, once and normatively:

> **The extent an identity is decided over is the same set at every door that reads it, writes it,
> keys it, gates it, or counts it — and a door that cannot prove it is the same set answers
> `unknowable` rather than deciding.**

That is offered as **standing rule (e)** of this register, and it is the generalisation the six
records converge on. Each record then becomes a §-row of the same change rather than its own fix:
§4.2/§4.3 say which `type_name` the host writes under and which the rule 4-11 ledger key uses
(`I-3`); the per-act rules key on whatever §3 calls the same thing, or the document states they
are exact-string and prices it in ING3 (`I-4`); the guard asks who holds a proposal rather than an
unreviewed one (`I-5`); a page's `instance_id`s are distinct-or-`unknowable` (`I-6`).

**The mutation harness is what proves this landed.** Every one of the six was **[Observed]** to
leave the design tests green under mutation — the gate is blind to all six. A fix set that does
not turn each of those mutations red has not closed the table, whatever the prose says.

## R85, part three: standing rule (d) is not under-worded, it is unenforced

§6.7e records **seven failures of standing rule (d) in one round, every one inside the fixes of
the round that invoked standing rule (d) as its own lesson.** R84 sharpened the rule to cross the
document boundary, and that clause is still right — but it does not explain these seven. Four of
them (Z1, Z2, Z5, Z6) are doors **inside the same document**, which rule (d) already covered in
its original wording.

The honest reading is therefore not that the rule needs a third clause. **It is that a rule
addressed to an author's diligence has now failed seven times in one round while being cited by
name.** This register's own history says what to do with a class that diligence cannot hold: make
it countable. The checker found trip 4; the loop found the rest; neither substitutes for the other;
and every family that actually closed — the missing-operand family, the tombstone-word family —
closed when it got a mechanical form.

**So rule (d) gains an obligation on the COMMIT, not on the author:**

> Every commit that mints a numbered rule carries, in the run record, the **enumeration** of the
> doors that rule binds — named, not implied. A later round that finds an unenumerated door records
> it as a rule-(d) failure **by number**, and the count is reported in the round's totals.

Seven is that count for round 2. It is reported because it was counted, and it was counted because
the lens went looking — which is the argument for the loop, again, for the seventh time in this
register. The next row inherits the obligation, not the exhortation.

## Unchanged

Kill-row trip count is **fourteen**. Q56 remains the class-closing question for the read side and
the founder's. Standing rules (a)–(c) stand; (d) is sharpened by R84 and made countable here;
(e) is proposed by this ruling and is the row's to carry into the register when the fix set lands.
The dedicated identity-surface row now has **six** instance-surface records in its lens set, and
they are one table — which is a materially better brief than the fourteen trip records alone.

## What row 7a's worker does with this

1. Label Records A–D as **`I-3`**, **`I-4`**, **`I-5`**, **`I-6`** at §6.7a and mark them
   countersigned; do not increment the kill-row count anywhere.
2. **Read [R84](2026-09-04-7a-supervisor-ruling-R84.md) before writing the fix set** — it
   countersigned `I-2` and it constrains that fix (visited set, hop cap, honest `complete=False`
   with a `why`, plus the rider defect in the same four lines). It landed at `f8afa0b` while you
   were mid-round and you have not read it.
3. Write the fix set as **one change over the table**, per part two, with standing rule (e) stated
   normatively — not six fixes in the order the lenses found them.
4. Turn each of the six mutations red, and say so in §6.9 with the numbers.
5. Carry the rule-(d) enumeration obligation into §6.9's totals and into the register entry.

Next ruling number: **R86**. Next question number: **Q91**.
