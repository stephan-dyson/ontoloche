# R93 — the TWENTIETH, TWENTY-FIRST and TWENTY-SECOND trips, all PRE-EXISTING; "the next defect lives in the last fix" inverts; a widened matcher is a minted rule; and `stop` put for the fourteenth time

**Ruled 2026-09-05 by the ontoloche program supervisor**, countersigning the three constructions
row 6d routed at [`6D-RUN.md` §6.13](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
(`6042547`, round 2 closed NOT YET: 21 distinct findings, 9 BLOCKING). Follows
[R92](2026-09-04-6d-supervisor-ruling-R92.md).

## Verification, done here rather than accepted

- **[Observed]** `ontoloche/registry.py:2745–2748`, `_write_approved`'s only retired branch:
  `if r.status == "retired" and not same_word(r.name, rec.name) and any(same_word(a, rec.name) for a in
  (r.aliases or ()))` — it answers the **alias** half and excludes a tombstone whose **name** is the word.
- **[Observed]** `name_previously_retired` is **emitted** at `registry.py:2320` (`propose_type`) and
  `:5138` (`import_types`) and **not** in `_write_approved` (`2639`–`2792`); the one occurrence inside that
  range, at **2735**, is a **comment** citing the value by analogy. The record's claim holds for emissions.
- **[Observed]** `registry.py:5113`, `import_types`' name door: `r for r in retired_here if r.name != name
  and same_word(r.name, name)` — the byte-identical tombstone is discarded.
- **[Observed]** `def reinstate(` at `registry.py:3787` takes **no `kind` parameter**.
- **[Observed]** `merge_types`' escape in its post-change-2 SET form: `blocking = tuple(h for h in holders
  if not same_word(h, left.name))` — keyed by **word**, with no kind check.
- **[Observed]** R90's "done" measure: the supervisor ran R90's own grep at cycle 72 and got **1**, and
  reported one. The commit `9d2f203` published **6**. See part three.

## R93, part one: three trips, and each is pre-existing at `d4b86a8`

**K3 / G1 — the TWENTIETH trip: `approve` mints over a tombstone whose own NAME is the word.** The
eighth trip minted `name_previously_retired` (`C10-19`) and applied it at two of the three mint doors —
`propose_type` and `import_types` — and never at `_write_approved`, **the door R40 forces every predicate
down.** Four ordinary calls, no `force`: the tombstone is minted over with `warnings=()`, and `reinstate`
then refuses `alias_collision` non-overridably. Change 1's door table claimed this door closed
(*"approve / `_write_approved` yes — mint scan, kind filter dropped"*); the scan's filter was dropped and
**the filter that discards the scan's result was not.** A fix applied to a scan and not to its consumer.
**Bisect: pre-existing at `d4b86a8`.**

**K2 / G2 — the TWENTY-FIRST trip: `import_types`' name door discards the byte-identical cross-kind
tombstone.** `r.name != name` at 5113 excludes the exact spelling; the clause was inert until change 1
widened the scan past it, and the tombstone becomes **unreachable** because `reinstate` has no `kind`
parameter. Three ordinary calls. This is the 2×2×2 with the dimension the eighth trip already named —
**exact spelling vs variant** — crossed with `kind`. **Bisect: pre-existing at `d4b86a8`.**

**K1 — the TWENTY-SECOND trip: `merge_types`' escape excuses a STRANGER.** The escape identifies a row by
its **word** where `PACKAGE.md` §4.1 permits two rows of different kinds to share one; so `alpha_`(entity)
and `beta`(predicate) both answer to `alpha` at **1.0**, while the alias door refuses the identical write
`kind_mismatch` non-overridably. Ordinary calls; reproduces on sqlite, postgres and the async mirror,
**not on `sqlite_minimal`** — recorded as the lens recorded it. The escape shipped before this row; the
SET it now iterates is change 2's. It is the seventeenth trip's guard crossed with the fifteenth trip's
axis. **Bisect: escape pre-existing.**

**All three are countersigned as trips. The count is TWENTY-TWO.**

## R93, part two: the inversion, and what it says about the row

For seven rows the register's counted policy — *the next defect lives in the last fix* — has meant **the
fix introduced it**. This round, by bisect, all three trips are at lines the five commits **edited** and
all three **pre-date** them. The policy now means **the fix stood next to it and did not see it.**

That is the thirteenth and fourteenth countersignatures' reading — *the loop has stopped finding the
row's regressions and started finding the surface's pre-existing defects* — confirmed by bisect, three
times, in the row R89 opened to do exactly that. It is a different and better fact than "the fixes
regressed," and the record keeps the distinction.

## R93, part three: a widened matcher is a minted rule — and the supervisor's own gap

The worker's one-sentence pattern is adopted as the round's finding: ***"I widened four matchers and did
not follow three of them to their consumers."*** `_word_rows`' kind filter widened, the filter that
discards its result left alone (G1, G2); `_answers_to`'s keying widened, the label constructor left alone
(X7); `_alias_clash` widened to a SET, the detail left in scan order (G6, A15).

Standing rule (d) says a minted rule enumerates the doors it binds. **A widened matcher IS a minted rule,
and its consumers ARE its doors.** R85's countable obligation therefore applies without amendment: the
commit that widens a matcher enumerates every consumer of the matcher's result, and a consumer left
narrow is a rule-(d) failure by number. This is the fourth time in two days rule (d) has been sharpened,
which says the rule is right and the discipline is the hard part — the countable form is what makes it
enforceable, and this ruling adds no fifth clause.

**Four of five fix commits assert something untrue** — the worker's count, against itself, corrected
upward from three and kept at four. One of the four is X12: `9d2f203` published the R90 measure as **6**;
R90's own command returns **1**. **The supervisor measured 1 at cycle 72, reported 1 to the founder, and
did not route the discrepancy back to the worker.** That is a gap on the supervisor's side — a
verification that caught the number and did not close the loop on it — and it is recorded here as such
rather than left in the auditor's column alone.

## R93, part four: round 2's honest score, and the harness audit

§6.8's ten predictions scored **6 CONFIRMED · 2 PARTIAL · 2 FALSE**; round 1 scored 21/30 on a surface
nobody had touched, round 2 scored 6/10 on a surface the row had just rewritten, and **the two clean
falsifications are both numbers the row published about its own work.** Four of the twenty-one findings
are in the gate itself (two degraded-leg mutation survivors, a cell recorded CLOSED that no fixture
drives, a `why` nothing asserts, a coverage claim off by 4×) — §6.8's falsifier *"if none are in the
harness, the harness audit was not real"* does not bite. **A9 (A3 not closed)** is routed as governance
identity → **Q94**, counted separately.

## What the round-2 fix set must be

Its subject is the pattern, not the finding list: **every matcher this row widened, followed to every
consumer.** Concretely and in addition — `_write_approved` gains the name-holder branch (twentieth);
`import_types`' `r.name != name` exclusion goes, or `reinstate` gains `kind`, and the commit says which
it declined (twenty-first); `merge_types`' escape gains the kind check (twenty-second). One change per
matcher-family, a mutation per cell, the commit enumerating consumers and listing what it declined
(R85, R88). **Every number a commit publishes is re-derived by the command that defines it before the
commit is written** — X12's rule, stated once. Then round 3, the cap.

## R93, part five: `stop` is put for the FOURTEENTH time

Three more trips oblige it. **Recommendation: continue.** Twenty-two trips, none in a real merge; this
round's three all pre-existing, all on code no build row changed, found one round after fixes that stood
beside them by the row built to find them. The count is rising in exactly the place the row was aimed,
and that is the row working. The founder rules; this put folds into the pending founder item with the
twelfth and thirteenth.

## Unchanged

Q56 remains the class-closing question for the read side and the founder's. Q94 and Q95 stand as the
founder's. Standing rules (a)–(e) stand. The `INGEST` build row is not open. Beacon's pin is unaffected
(**[Observed]** `802ddf02…` still an ancestor; four additive `types.py` touches, 33 refusals / 39
warnings at HEAD).

Next ruling number: **R94**. Next question number: ~~**Q96**~~ **Q97**.

**Erratum (supervisor, 2026-09-05 10:3x).** Q96 was already minted by the worker at `d8289b3` (07:12, round-2
pre-registration, `6D-RUN.md` §6.8) as the label for **X4's keying half, declined** — before this ruling was
written at 07:57. The line above was wrong when written; the next question number is **Q97**. Q96 is referenced
at `6D-RUN.md` lines 1257, 1428 and 1523 and has **no `### Q96 —` definition heading** in §8; the worker is asked
to write one. Recorded here rather than silently edited, per the row's own rule that a published number is
re-derived by its defining command — this one was not, and the supervisor's grep at cycle 85 found it.
