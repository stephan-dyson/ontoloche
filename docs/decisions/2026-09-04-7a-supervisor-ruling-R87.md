# R87 — `I-8` confirmed (mis-directed); a normative citation binds you to ALL of it; and the loop has become PREDICTIVE

**Ruled 2026-09-04 by the ontoloche program supervisor**, on the eighth cell nominated at
[`7A-RUN.md` §6.13a](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md),
landed at `18a5629`. Follows [R83](2026-09-04-7a-supervisor-ruling-R83.md),
[R84](2026-09-04-7a-supervisor-ruling-R84.md), [R85](2026-09-04-7a-supervisor-ruling-R85.md) and
[R86](2026-09-04-7a-supervisor-ruling-R86.md).

## Verification, done here rather than accepted

Three claims, all reproduce:

- **[Observed]** `ontoloche/registry.py` at ~5380, the docstring §3.4a declares itself written from:
  *"The closure is walked in **both** directions and they are different questions … **backward** — a
  walk from `owner` must find the edges written against `assignee`, which is the direction
  `merge_types` actually produces and the one a caller reaches after doing the right thing. **Aliases
  are consulted too** …"*
- **[Observed]** in `docs/specs/INGEST.md`: `backward` → **0** hits, `alias` → **0** hits
  (case-insensitive), `predecessor` → **5**, all of them rule 3-15's *negative* use.
- **[Observed]** in `docs/tools/ingest_probe_kit.py`: `alias` → **0** hits.

So the document cites a shipped function as normative, implements its **three termination rules**,
and implements **one of its three relations**.

## R87, part one: `I-8` is confirmed

**`I-8` — mis-directed: the closure is walked forward only.** The eighth cell of the table. Kill-row
trip count stays at **FOURTEEN**; `stop` is not put, because `stop` attaches to trips.

**It is genuinely a cell and not a construction inside `I-2`,** and the lens's reasoning is adopted
with one addition. The seven existing cells describe doors **disagreeing** with one another or a door
**unable to prove**. Here the read, the key and the write **all agree** — consistently, at every door
— on a set that is a strict **subset** of the identity. `I-2` is about **depth** (one hop, reported
`complete=True`); this is about **direction**. Those are different axes and collapsing them would
hide the second the way trips 8/12/13/14 hid each other.

**The addition, and it matters for the founder's stop question:** this is the **ordinary**
post-retirement path, not an exotic one. The survivor is the name every new caller uses after a
retirement. And its outcome is the worst shape the series has produced — every earlier cell ended in
ambiguity or a duplicate *proposal*; this one ends in **`mode='auto'`, a second row written for one
identity with no human in the loop.**

## R87, part two: a normative citation binds you to ALL of it

**This is R84's second clause failing inside the very section written to satisfy it**, and that is
the ruling's substance.

R84 said: *where a shipped caller already implements the rule, the specification cites that
implementation as its normative reference rather than restating the ruling the implementation was
derived from.* §3.4a **did exactly that** — it names `_identity_closure`, calls the citation *"a rule
rather than a courtesy"* — and then took three of the function's termination rules and one of its
three relations.

So citing is not enough, and R84's clause gets its own sharpening:

> **A citation of a shipped implementation as normative binds the citing document to ALL of it. The
> citation must enumerate, by name and in the same change, what it ADOPTS and what it DECLINES — and
> a partial adoption is recorded as a contortion, not left as prose.**

This is standing rule (d) in its third form, and R85's diagnosis applies again without amendment: a
rule addressed to an author's diligence keeps failing. So the **countable** obligation R85 minted
covers this too — the enumeration a minting commit owes now includes *what a citation takes and what
it leaves.*

## R87, part three: the loop has become PREDICTIVE, and this is new information for `stop`

Round 3's predictions were **pre-registered at `4f3b2eb` before any lens returned.** Prediction **P3**
said the next defect would live in **rule 3-19** — *"the newest rule, the only one that made a set
bigger, and its cost is recorded as ING11 and explicitly unmeasured"* — and **P3 is confirmed**: rule
3-19 widened the extent along the axis that was **already covered** and left the axis the shipped
code exists to cover.

**That is a different kind of fact from anything in the fourteen trip records.** The register's
recurring worry, stated honestly by this row's own §6.9c, is that the findings did **not** shrink
(11 BLOCKING in round 1, 19 in round 2). Non-shrinking findings say the loop is still productive.
**A confirmed pre-registered prediction says the loop is now predictive** — the row named where its
next defect would be, in writing, before looking, and was right.

A process that can do that is not the same object as one that keeps being surprised, and the `stop`
question should be put to the founder with that stated plainly beside the non-shrink. **This
countersignature does not put `stop`** — no trip has occurred — but it records the fact the founder
will want when he next rules on it.

## What this requires of the fix set

1. **Rule 3-19 gains the backward relation and the alias relation, or §3.4a's citation states which
   it declines and why** — by name, in the same change, per part two. Silence is no longer available:
   `backward` and `alias` are currently zero in both the spec and the kit.
2. **Each adopted relation gets its own mutation.** A single mutation over "the closure" would leave
   the fix unfalsifiable in the direction it just added, which is §6.10e-i's harness lesson one
   artefact along.
3. **`mode='auto'` is named in the record as the outcome**, because a cell that writes without a human
   is not the same severity as one that proposes.

## Unchanged

Kill-row trip count is **fourteen**. Q56 remains the class-closing question for the read side and the
founder's. Standing rules (a)–(c) stand; (d) is sharpened by R84, made countable by R85, and extended
here; (e) stands in R86's seven-cell wording and now spans **eight** cells. The dedicated
identity-surface row's lens set is **eight cells**.

## What row 7a's worker does with this

1. Record `I-8` at §6.13a as **countersigned**, with the `mode='auto'` severity note.
2. Carry part two into the register and into §3.4a's citation.
3. Apply the fix per "What this requires", with per-relation mutations.
4. State the prediction-confirmation result in §6.14's convergence note **beside** the non-shrink, not
   instead of it. Both are true and the founder gets both.
5. Do not increment the kill-row count anywhere.

Next ruling number: **R88**. Next question number: **Q91**.
