# R111 — Q107 (item 23): `fold into the build row`

**Ruled 2026-11-17 by the founder** (reply: *"fold"*), after the supervisor laid out the three options and recommended this one.

## What was asked

`Q107` (item 23 in [`DECISIONS-OPEN.md`](../DECISIONS-OPEN.md)) asked what happens to row 8b's 14 open round-5 findings: a separate fix pass, fold them into the build row, or leave §2.10 as landed. It decides no refusal. The refusals in §2.10 are rules 2.10-17 to 2.10-21, which are `Q103` to `Q106` and stay open.

## The ruling

**`fold into the build row`.** Row 8c's first task is the 14 findings in [`8B-RUN.md`](../runs/8B-RUN.md) §2.5 (5 MAJOR, 9 MINOR). Each fix to §2.10 is made in row 8c and reviewed by that row's adversarial loop together with the code that implements it.

## Why this option

- **No unreviewed text lands in the spec.** That was the reason item 23 gave for bringing the question at all, and this option keeps it: every fix passes a fresh adversary, now with code to test the wording against.
- **`fix pass` costs a whole spec row** before the build can start, and its reviewers would read the reference reader (rule 2.10-11) without code to test it against. Three of the five MAJORs are in that reader.
- **`leave` would make a build row guess** at wording that already has a known defect and a proposed fix, which is the failure the loop exists to prevent.

## What this does not decide

- `Q103` to `Q106` (items 19 to 22) and item 25 stay open and stay the founder's. Row 8c builds rules 2.10-17 to 2.10-21 as today's behaviour, measured and pinned, per its brief §0 item 3.
- The unrouted retire-then-alias defect (probe line D14) stays out of scope for row 8c, per its brief §2.
