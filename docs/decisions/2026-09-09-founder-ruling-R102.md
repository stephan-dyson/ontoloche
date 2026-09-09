# R102 — Q99 is ruled `all eight`. Everything an action family declares is part of its identity.

**Founder ruling, 2026-09-09. His word: `all eight`.**

Question, minted 2026-09-09 out of row 6f's measurement:

> **Q99** — `ACTIONS.md` §2.2 makes an action family declare **eight** things. `_GOVERNANCE_KEYS` compares
> **four**. Which of the eight are **governance**?

**Ruled: `all eight`.** Every key an action family declares is part of the identity two families must share
before the registry lets them collapse into one.

---

## 1. What it fixes

`_GOVERNANCE_KEYS` compares `approval_mode`, `min_auto_tier`, `reversibility`, `effects`. It never compares
**`inputs`, `preconditions`, `reachability`, `payload_schema`**.

**[Observed, supervisor's own run of `docs/tools/readside_a3_probe.py`]** two families agreeing on the four
and differing on `preconditions` collapse through `retire(successor=)` with **no refusal, no `force`, no
acknowledgement**; a Haiku-tier actor then records `applied`; and the survivor's ledger reads **`n=0`** —
the record filed under the dead word. **That is the route by which entry `A3` still fires this project's
governance stop criterion**, and `all eight` is the ruling that closes it at the write door.

**The comparator could not see the contradiction it exists to catch.** After this ruling it can.

## 2. It dissolves the asymmetry the founder was warned about

Q99's item told him that row 6f's **read** side already scores on all eight, so a narrow ruling would leave
the two sides deliberately asymmetric — the write doors permitting a join the read still flags below 1.0.

**`all eight` removes that.** Both sides now stand on the same definition of what an action family's
identity is:

| side | what it does with the eight keys |
|---|---|
| **read** (`_declaration_agreement`, rule `5.3.2-16`, shipped by row 6f) | scores agreement, never refuses; a key present on one side and absent on the other does **not** agree |
| **write** (`_action_declarations_diverge`, row 6g) | refuses the collapse when they contradict |

*"May these be joined?"* and *"do these still denote one thing?"* remain different questions. They now take
the same evidence.

## 3. What it costs, and the failure mode this project has already been burned by

**`all eight` is the most refusing option.** Collapses that succeed today will refuse tomorrow. That is the
point, and it is what the founder chose.

**But there is a specific, recorded way to get this wrong, and row 6g must not repeat it.** Row 6d's own A3
fix compared `effects` with `!=`. Three of the four keys it compared are scalars, where `!=` is right.
`effects` is a **list** — so two families whose governance was **identical** and whose effects were merely
**written in a different order** were refused `action_declarations_diverge`, **non-overridably, at all
three doors, under every acknowledgement and under `force=True`**. In the registry's own words it
**CLOSED A LEGAL OPERATION**, and it was the most urgent thing left on that surface.

**Expanding from four keys to eight adds three more list-valued keys** — `inputs`, `preconditions`,
`reachability` — and so triples the surface of that exact defect.

**Row 6f already solved this on the read side and the write side must match it.** `registry.py` carries
`_UNORDERED_DECLARED_KEYS = ("effects", "inputs", "preconditions", "reachability")`, with the reason
written above it: §2.5 and §3.3 make `effects` a set, §1's non-goals say *"no ordering"* for the rest, and
*"a read that scored those two apart would repeat it one call along."*

**Row 6g compares those four as SETS, not with `!=`.** If it does not, it re-creates row 6d's defect at the
door where it is non-overridable.

## 4. What this ruling does NOT decide

- **Whether the refusal is overridable.** Today `action_declarations_diverge` is non-overridable. Whether a
  contradiction on `payload_schema` deserves the same severity as one on `approval_mode` is **not ruled**,
  and row 6g must raise it rather than assume it.
- **Whether absence equals divergence.** The declare-nothing hole — `if not mine or not theirs: return
  None` — is a **separate, argued** choice and remains defect B of row 6g's brief. `all eight` says which
  keys are compared **when both sides declare**, not what to do when one does not.
- **How many currently-legal collapses this refuses.** That is a measurement row 6g owes, not an
  assumption. If the number is large, that is evidence worth bringing back, not a reason to narrow the set
  quietly.

## 5. Consequent

- **Row 6g opens.** Its brief's gate (b) is satisfied; both gates are now clear.
- The governance register's `Q99` is marked ruled.
- **`A3` still does not close until row 6g lands.** The stop criterion stays fired and the ACTIONS surface
  stays stopped for everything except row 6g itself.
- Kill-row count stays **TWENTY-THREE**. Governance register stays at **ONE**. A ruling is not a trip.

Recorded by the ontoloche supervisor. Question's origin: [the governance register](2026-09-07-governance-register.md).
Row 6f's read-side half: [`6F-RUN.md`](../runs/6F-RUN.md). Same-day rulings: [R99](2026-09-09-founder-ruling-R99.md),
[R100](2026-09-09-founder-ruling-R100.md), [R101](2026-09-09-founder-ruling-R101.md).
