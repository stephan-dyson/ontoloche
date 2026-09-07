# R97 — FOUNDER RULING (Q94): governance identity gets its OWN register, not a place in the kill-row count

**Ruled by the founder, 2026-09-07 ~10:3x.** The founder's word, verbatim: **"separate."**
Recorded by the ontoloche program supervisor. This closes **Q94**, minted by
[R91](2026-09-04-6d-supervisor-ruling-R91.md) out of row 6d's **A3**.

## What was asked

*Does the kill criterion extend to GOVERNANCE identity — one word answering with two policies — or is that
a separate register?* Default in force since R91: separate, never folded into the count.

## The reason on the record was wrong, and is corrected here

Every prior ruling justified the default as *"the identity criterion is not met — one word, ONE identity,
TWO policies."* **That does not hold.** In A3, `resolve_type` answers the word with the survivor at 1.0
while `preflight` answers the same word with the **tombstone's** policy. That is *two things answering to
one identity*, which is how this register has read the criterion in its own published documents
([`7A-RUN.md` §202](../runs/7A-RUN.md), [`INGEST.md` §364](../specs/INGEST.md)). By the register's own
working definition A3 is **inside**, and the fourteen-month-old sentence excluding it was doing work it
could not support.

## The reason the ruling stands anyway

The count exists to tell the founder **when to stop**. Ask what each answer does to that job.

- **Folding governance in:** the number becomes 24 and then grows on a wider surface. Nobody can afterwards
  tell whether it rose because the system got worse or because the net got bigger. That is precisely the
  defect this project has documented in its own code — [R93](2026-09-05-6d-supervisor-ruling-R93.md)'s
  *"a widened matcher is a minted rule and its consumers are its doors."* Widening the criterion by
  absorbing a new class does the same thing to the register that a widened matcher does to a guard.
- **A separate register:** two clean signals instead of one muddy one — identity-flattening at **23**,
  governance-collapse at **1**. A register opening at 1 on a finding this severe is a **louder** signal than
  a twenty-fourth tick on a counter already at twenty-three.

## What "separate" does NOT mean

**It does not mean A3 is filed away.** A3 is **BLOCKING** and reached with **ordinary calls on two of three
doors** — `retire(successor=)` and `import_types`, with no `force`, no acknowledgement and **empty
warnings**; the third door, `merge_types`, refuses `definitions_diverge` only **overridably**. A Haiku-tier
machine actor recording `applied` against a verb the surviving family declares **human-approval-only and
irreversible** is an authority breach whatever register it is counted in.

So the ruling opens a real register, not a footnote:
[`docs/decisions/2026-09-07-governance-register.md`](2026-09-07-governance-register.md), **A3 as entry one**.

## Consequence carried into row 6e (the audit)

The audit's brief takes an added question, because this ruling exposed it: **`ROADMAP.md` writes the kill
criterion as *"a capability predicate gets merged as a duplicate"*, and the register has been reading it as
*"two things answering to one identity."* That widening was never ruled — it happened in practice.** If the
project widened its own kill criterion silently, that is the same defect it has recorded twenty-three times
in its code, committed by its register. Row 6e answers it.

## Numbering

Kill-row trip count stays **TWENTY-THREE**. Governance register opens at **ONE**. Next ruling **R98**.
**Q97 is now taken** by the governance register's own stop criterion (below); the R95 across-kinds question
(`alias_collision` across kinds at `import`/`reinstate` under `PACKAGE.md` 4.1) becomes **Q98 if numbered**,
and is still surfaced rather than minted.
