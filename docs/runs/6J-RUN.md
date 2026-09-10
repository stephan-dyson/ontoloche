# 6J-RUN — THE FIFTH GATE'S REGRESSION-DETECTION HOLE, CLOSED AS AN AXIS

**Row 6j, under the brief `2026-09-10-oo-gate-hole-followon.md` and the answers file
`2026-09-10-oo-6j-supervisor-answers-1.md` that carried the GO.**

**The specification is [`6I-RUN.md`](6I-RUN.md) §7**, which the brief points at and deliberately does not
restate. The brief adds sequencing, authorisation and terms, and says so in its own words.

Floor commit: **`16becf6`**, which is where `origin/main` is held while this row works.

---

## §0 — PRE-REGISTRATION

**Committed ALONE, before any measurement.** No census has been run in this row, no suite leg has been run,
no gate has been invoked, and `git log` is the proof of the order. Everything below is derived by **READING
source** — `docs/tools/check_skip_census.py`, the eleven live `S5` sites, and the landed records — which is
the only thing that has happened so far.

### §0.1 — The order is the supervisor's, and both open questions came back answered

**§1 of the brief is a RULING and this row does not vary it:** fix the gate, re-run the census, then repair
the three live sites. Not reversed and not interleaved, because the gate is the instrument that certifies a
repair and today it will certify a wrong one.

**Answer 1 — the checker fix is NOT a sixth gate.** `check_skip_census.py` is already in the standing set,
so repairing it is a fix to an existing gate. The set stays **FIVE**. It becomes a sixth only if this row
ends up proposing a genuinely separate executable, and **the supervisor is told before such a thing is
built, not after.** This row does not expect to need one and §0.2 is written to avoid it.

**Answer 2 — the item 3 cheap local option is argued AFTER the fix, not now**, because until the fix exists
its size is an estimate and afterwards it is a measurement. It is not a blocker and it is not carried as
one.

### §0.2 — THE AXIS, MADE DECIDABLE, and the principle that resolves every ambiguity in it

§7's three parts are the specification. What follows is the rule this row intends to implement for each,
stated **before** the classifier is touched, so the implementation can be checked against it rather than
described by it.

| part | §7's question | what the checker will require |
|---|---|---|
| **what is asserted** | is it the capability that explains **this** refusal? | the proof asserts a capability flag against an **explicit boolean constant** or under an explicit negation, in the **falsifying** sense — the sense in which a backend that DOES have the capability fails the assertion. A bare truthy read, and an `is True` proof, are refused. |
| **when it is reached** | does the guard narrow to the reason that capability explains? | the guard chain over the guarded observation must carry a **discriminator**: a comparison against a literal constant, or a constant-bearing predicate such as `startswith("...")`. A positive type-or-truthiness test alone is **not** a narrowing. §0.4 is the one exemption and its argument. |
| **whether it can fail** | is the assertion's own expression defeatable? | the proof's expression must not be **vacuous** — no operand that makes it constantly true regardless of the capability, which is `assert True or X` and everything of its shape. |

**THE PRINCIPLE THAT RESOLVES THE REST, pre-registered because it is what a later reader will want to argue
with:** `S5-PROVEN-ENVIRONMENTAL` is the **UNGATED** cell and `S2-RESULT-UNDER-TEST` is the gated one.
**Every ambiguity the axis cannot decide resolves toward `S2`.** A checker that is unsure whether a proof is
real must not grant the promotion. Failing toward the gated cell costs a conversation; failing toward the
ungated cell is `F12`.

**AND THE `why` TEXT IS PART OF THE FIX, not a caption on it.** `F15` is the reason: the gate today quotes
the vacuous assertion verbatim and then states a consequence that is false of the very expression it just
quoted, so **it prints the disproof and draws the opposite conclusion from it.** The corrected text will say
**which of the three parts it actually verified** and will make no claim about what would fail that the
checked expression does not support.

### §0.3 — THE LIVE `S5` POPULATION, derived by reading rather than by running the census

**Every `S5` site must carry a capability assertion**, because `_capability_proof`
(`docs/tools/check_skip_census.py:516`) grants the category on nothing else. So the population is
enumerable from source. **[Read — `grep` for `assert ... caps|capabilities` over the scanned files, then
each hit's branch opened by hand]** there are **TWELVE** such assertions sitting in a skip's own branch, and
**eleven** of them classify `S5`:

| # | site (sync tree, at `16becf6`) | guard | proof | narrowed by |
|---|---|---|---|---|
| 1 | `test_c4_propose_type.py:478` `_tombstone_holding` | `isinstance(gone, Refusal) and gone.reason == "cannot_record_override"` | `stores_events is False` | constant |
| 2 | `test_c9_retire.py:1748` `_tombstone_holding` | same | same | constant |
| 3 | `test_c12_foundry_import.py:1125` `_tombstone_holding` | same | same | constant |
| 4 | `test_c10_merge_types.py:1348` `test_c10_24` | `isinstance(merged, Refusal) and merged.reason == "cannot_record_override"` | `stores_events is False` | constant |
| 5 | `test_c19_actions.py:4705` `test_c19_100` | `isinstance(out, Refusal) and out.reason == "cannot_record_override"` | `stores_events is False` | constant |
| 6 | `test_c19_actions.py:4746` `test_c19_101` | same | same | constant |
| 7 | `test_c9_retire.py:1888` `test_c9_37` | `back.reason == "cannot_record_override"` | `stores_events is False` | constant |
| 8 | `test_c9_retire.py:1931` `test_c9_38` | `isinstance(back, Refusal) and back.reason == "cannot_record_override"` | `stores_events is False` | constant |
| 9 | `test_c10_merge_types.py:1417` `test_c10_25` | `out.reason != "alias_collision"` | `indexes_membership is False`, **and a second assertion `out.reason == "predicate_merge"`** | constant, both senses |
| 10 | `test_c12_foundry_import.py:1379` `test_c12_27` | `not any(w.startswith("import_refused:") for w in warnings)` | `stores_aliases is False` | constant, under a negation |
| 11 | `test_c10_merge_types.py:1516` `test_c10_27` | `not isinstance(refused, Refusal)` | `stores_aliases is False` | **NOTHING — the one site with no constant anywhere in its guard** |

**The twelfth is `test_c19_actions.py:4905`, `_skip_if_cannot_record`, and it is `S4-UNDECIDABLE` for a
different reason** — its `out` is a helper's parameter, never assigned in the function, so it never reaches
the observation branch of the classifier at all. That is §7 item 2's site, and the calibration set already
pins the shape as `UNDECIDABLE` (`LENS B2`).

**The cross-check that says this reading is right rather than plausible: 11 is exactly the landed `S5`
cell.** `6I-RUN.md` §3.4 records `S5-PROVEN-ENVIRONMENTAL` at **7 -> 11**. **Its limit, stated rather than
glossed:** the enumeration is a `grep` for a source shape followed by reading, not an AST pass, so a proof
written in a form the pattern does not match would be missed. **The census run after the fix is what settles
it, and if the `S5` population it prints is not these eleven, this section was wrong.**

**All eleven assert the falsifying sense — `is False` — so part 1 of the axis moves nothing here.** None is
vacuous, so part 3 moves nothing here either. **The whole of this row's exposure on the live tree is part 2,
and inside part 2 it is one site.**

### §0.4 — THE ONE EXEMPTION, and it is where this row expects to contradict the brief

**Site 11's guard is `not isinstance(refused, Refusal)` and it carries no constant.** A rule reading
*"require a reason comparison"* literally would drop it from `S5` to `S2`.

**THIS ROW WILL EXEMPT IT, and the argument is that the rule cannot be satisfied there rather than that the
site is close enough.**

**`refused.reason` DOES NOT EXIST on that branch.** The branch is the one where the call did **not** refuse.
There is no reason to compare against, and a rule that demands one is demanding an attribute reference that
would raise. **A requirement no correct site can meet is not a requirement, it is a defect in the checker.**

**And the hazard genuinely is absent, which is the part that matters more than the syntax.** `F12`'s defect
is that a **positive** `isinstance(x, Refusal)` admits a FAMILY — `retire` has twelve `return Refusal(...)`
statements, of which the capability explains one — and the assertion then fires on eleven cases it does not
cover. **The negation admits no family**: it names the complement of that class, and there is nothing inside
it to narrow among.

**So the implemented rule is: a positive type-or-truthiness test over the observation requires a
discriminator; a NEGATED one does not.** Site 10 is the useful control — it is also a negation, and it
carries a constant anyway, so it passes under either reading and cannot tell the two apart. **Site 11 is the
only site in the suite that can**, which is what makes `P2` worth measuring rather than asserting.

### §0.5 — `P1`, ONE INTEGER: **0**

**`P1` predicts that ZERO sites change category in the live census as a result of the checker fix.**

Derived from §0.3: ten of the eleven `S5` sites narrow on a constant, the eleventh is exempted by §0.4, all
eleven assert the falsifying sense, and none is vacuous. Nothing in `S0`, `S1`, `S2`, `S3` or `S4` can move,
because the fix only ever **removes** a promotion and the only promotion in the classifier is into `S5`.

**Falsifier:** any site printing a different category after the fix than the landed census recorded for it.
**If the site that moves is one of row 6i's four landed repairs — sites 1, 2, 3 or 4 above — this row STOPS
and brings it to the supervisor**, per §1 of the brief, before doing anything else with it.

**`P1` is the prediction most likely to be wrong**, and it is recorded at its own length rather than hedged,
because the derivation behind it is a `grep` and eleven hand-reads.

### §0.6 — `P2`, ONE INTEGER: **1**

**`P2` predicts that exactly ONE of the eleven live `S5` sites has its verdict decided by §0.4's negation
exemption** — that is, exactly one classifies `S5` with the exemption in and `S2` with it out.

**This is measured by running the fixed classifier twice over the live tree, once with the exemption
disabled**, which is a source-reading experiment over strings and touches no file — the brief's own
technique. **The prediction names `test_c10_merge_types.py:1516`, `test_c10_27`, as that site.**

**Falsifier:** any count other than 1, or a count of 1 at a different site. **A miss here means the exemption
is doing more work than the argument for it covers**, and the supervisor gets the shape before this row
proceeds to the repairs.

### §0.7 — WHAT REPLACES *"the cell counts will move"*, and this is a contradiction of the brief

**The brief's §1 says: *"Then re-run the census. The cell counts will move and that is the point — a fix that
changes no classification has not been demonstrated to do anything."*** The ORDERING in §1 is a ruling and
this row follows it exactly. **The sentence about the counts is a prediction about the outcome, and §0.5
predicts the opposite.**

**The reason is `F12`'s own precise shape, which `6I-RUN.md` §6.5 states in these words: it is a
REGRESSION-DETECTION hole, not a current-state error.** Today's baseline is correct for today's tree. **A
live cell moving would mean row 6i landed a defective repair** — which the brief's own stop-rule treats as
an alarm to be escalated, not as the demonstration that the fix works. **The two halves of §1 pull against
each other and this row is saying so before measuring rather than after.**

**So the demonstration is the CALIBRATION SET, not the census.** The fix is shown to do something by cases
the OLD classifier gets wrong and the NEW one gets right, pinned so the breakage cannot come back. **That is
a re-execution anyone can run — `--selftest` — and it is stronger evidence than a moved cell, because a
moved cell would have to be explained away first.**

**If the census does move, `P1` missed and the miss is the result**, recorded at the same length as a hit.

### §0.8 — The calibration cases the axis requires, derived from the axis and not from three remembered names

§7's instruction is explicit: *"Derive the calibration set from the axis, not from the three names. A set
built from three remembered cases will not catch the fourth case nobody has thought of."* So the set is
built **one case per part per direction** — the shape that must be refused, and the shape that must still be
accepted — with the accept cases drawn from the live population so the set cannot drift from the suite:

1. **Part 2, must refuse:** a repaired site with **only** the `and x.reason == "..."` clause removed. This is
   `F12` experiment 1, and it currently classifies `S5`.
2. **Part 2, must refuse:** the `d3f9a79` site patched with the brief's authorised one-liner verbatim. This
   is `F12` experiment 2, `S2 -> S5` today, and it is the case that makes the hole about the brief rather
   than about the future.
3. **Part 2, must accept:** the negation shape of §0.4, which must stay `S5`.
4. **Part 1, must refuse:** `assert registry.caps.stores_events is True` — `F4`'s inverted sense.
5. **Part 1, must refuse:** a bare truthy capability read as the whole proof.
6. **Part 3, must refuse:** `assert True or registry.caps.stores_events` — `F15` verbatim.
7. **Part 3, must refuse:** the same vacuity in a form that is not the literal `True or`, so the pin is on
   the property and not on the spelling.
8. **The `why` text**, checked against parts 1, 2 and 3 rather than trusted, because `F15` established that
   it can be false independently of the verdict.

**Every case is a string handed to `classify_source()`. None of them touches the tree.**

### §0.9 — What this row will not do, and it is the brief's list rather than this row's preference

- **§7 item 4's four baselined sites stay.** Unobserved on three legs. Naming a capability for a refusal
  never seen fire is `C19-100` closing a legal operation.
- **§7 item 5's twenty occurrences are not repaired.** If they are audited the audit is published whole; a
  quietly half-audited population is worse than an unaudited one.
- **§7 item 6 is DISCHARGED in `16becf6` and is not re-landed.**
- **§7 item 2 is not decided now.** §0.1 answer 2.
- **The kill row stays TWENTY-THREE. The governance register stays at ONE.** `Q101` and per-key severity are
  the founder's and are open. Nothing in this row is routed near either.

### §0.10 — The commands this row will run, named before they are run

```
py docs/tools/check_skip_census.py --selftest
py docs/tools/check_skip_census.py --census
py docs/tools/check_skip_census.py            # the gate, plain invocation, which does not write
```

**`--write-baseline` writes and the plain invocation does not.** §0.5 predicts the baseline does not need to
move; if it does, that is a `P1` miss and it is reported before anything is written.

**The five gates are run at the end, and the supervisor runs them again before closing the row.** Suite legs
are run once the step-3 repairs touch test files, which they will. **Never `git add -A`. `rm` takes a literal
absolute path. The supervisor is told before this row pushes.**

---

## §1 — THE CHECKER FIX, AND BOTH INTEGERS HIT

**Applied to `docs/tools/check_skip_census.py` only. 434 insertions, 18 deletions, one file.** No test file
was opened in this step and no repair was made — that is step 3, and the brief's §1 ruling is why.

### §1.1 — What the fix is: THREE PARTS, TWO PREDICATES, one shape rule each

**Parts 1 and 3 collapsed into ONE recursive predicate, and that is a finding rather than a tidying.**
`_falsifying(expr)` asks *does this expression FAIL on a backend that HAS the capability*, and that is the
question both parts ask. `assert caps.f is True` cannot fail on a capable backend (`F4`); neither can
`assert True or caps.f` (`F15`). **The same walk refuses both, and it refuses the rewordings nobody has
written yet** — `or` is falsifying only when BOTH operands are, because one non-falsifying operand carries
the whole expression. That is why the last calibration case below, which is `F15` not spelled `True or`,
needed no new code.

**Part 2 is `_guard_narrows`**, and it is the part `_capability_proof` never had: the guard is now read. A
guard narrows either by **naming a specific outcome** — a string literal in a comparison over the
observation, or a `startswith` / `endswith` prefix — or by **establishing the value is not of the refused
type at all**, which is §0.4's exemption.

**Two deliberate refusals inside part 2, both fail-closed and both pinned:**

- **A NUMERIC constant does not buy a narrowing.** `len(x.warnings) > 0` is a threshold, not a reason, and
  admitting it would sell the exemption for a `0`.
- **An ENUM-valued reason is refused too.** That is a conversation rather than a silent promotion, which is
  the direction §0.2's principle points.

### §1.2 — THE EXEMPTION IS A SHAPE RULE, and it is calibrated in BOTH DIRECTIONS

**The supervisor's answers-2 §2 is a ruling and this is what it required.** A named-site exemption
hard-codes today's tree into the instrument and stops applying the moment anyone renames the test, so the
rule is expressed as what it actually is: **`not isinstance(x, T)` over an observation — the value is not a
`T`, so `T`'s discriminating fields are not there to compare.**

**And the ruling's sharper half: an exemption is a NEW WAY THROUGH THE GATE.** *"Invert your guard and the
reason requirement disappears"* must not become true by accident. **So all three directions are written
down on purpose** — an inverse guard **with** a capability proof stays `S5`, an inverse guard **without**
one is still flagged, and an inverse guard with a **vacuous** proof is still flagged, because `F15` applies
inside the exemption too.

**A fourth case fixes the exemption's boundary, and it is the one that keeps the rule honest: `not x.ok` is
NOT exempt.** A negated truthiness test admits a family exactly as a positive one does, and `x.reason` is
right there to compare against — **the requirement CAN be met, so it is not waived.** The exemption is for
the type test alone, because the type test is what makes the reason attribute unavailable.

**One logical site, two files.** The same guard is at `ontoloche/aio/contract/test_c10_merge_types.py:1491`,
and **[Observed — the file's first three lines]** that file carries the `GENERATED FILE -- do not edit`
banner, so the census skips it and counts the site **once**. Nobody should count it twice.

### §1.3 — The `why` text, which was part of the fix and not a caption on it

**Before**, on a site whose proof was `assert True or registry.caps.stores_events`:

```
why: guard reads gone -- the result under test -- but the block asserts
     `True or registry.caps.stores_events` BEFORE it skips, so a capable
     backend that behaved wrongly would FAIL here rather than skip
```

**It quoted the disproof and drew the opposite conclusion from it.** After, every `S5` line says what was
checked and what was not:

```
why: guard reads gone -- the result under test -- but it narrows on a literal
     outcome, and the block asserts `registry.caps.stores_events is False`
     before it skips, an expression that FAILS on a backend holding the
     capability. CHECKED: the narrowing, the falsifying sense, and that the
     assertion is defeatable. NOT CHECKED, because no AST can know it: that
     this capability is the one that explains this outcome
```

**The last clause is the one that matters.** The semantic link — that `stores_events=False` is what produces
`cannot_record_override` — is not decidable from an AST, and the gate now says so instead of implying it
proved it.

**And an `S2` line now says WHY the promotion was refused**, which the old text never did. All four
baselined sites carry one: two are refused by part 2, and two because no assertion in the skip's own branch
reads a capability at all.

### §1.4 — `P1` PREDICTED **0**. THE CENSUS MOVED **0**. HIT.

```
S0-ENVIRONMENT             60        S3-UNCONDITIONAL            1
S1-SETUP-RESULT            47        S4-UNDECIDABLE             16
S2-RESULT-UNDER-TEST        4        S5-PROVEN-ENVIRONMENTAL    11
```

**Every cell is identical to the landed census**, and the `S5` population is the eleven sites §0.3 named,
with the guards §0.3 recorded. **None of row 6i's four landed repairs reclassified, so the brief's STOP
condition did not fire.** The gate exits **0** on the plain invocation, the baseline stays at **4**, and
nothing was written.

**§0.3's derivation was a `grep` and eleven hand-reads and it was right** — worth saying because §0.5 named
it as the prediction most likely to be wrong.

### §1.5 — `P2` PREDICTED **1**, AND NAMED THE SITE. MEASURED **1**, AT THAT SITE. HIT.

Measured by censusing the live tree twice with the same fixed classifier, the second time with
`_establishes_not_that_type` forced to `False`. **[Observed]**

```
ontoloche/contract/test_c10_merge_types.py::test_c10_27_...#0
    with the exemption: S5-PROVEN-ENVIRONMENTAL
    without it:         S2-RESULT-UNDER-TEST
```

**Exactly one site, and it is `test_c10_27` as §0.6 named it.** So the exemption is doing precisely the work
the argument for it covers and no more. Site 10 — `test_c12_27`, also an inverse guard — is unmoved by it,
because its `startswith` prefix narrows on a constant anyway and it never needed the exemption.

### §1.6 — WHAT THE FIX ACTUALLY DOES, since §0.7 said the census would not show it

**NINE of the fourteen new calibration cases are classified WRONG by the classifier at `16becf6` and right
by this one.** Measured by loading both modules — `git show 16becf6:docs/tools/check_skip_census.py` into
memory beside the working one — and classifying each case with both. **[Observed]**

| the case | at `16becf6` | now |
|---|---|---|
| `F12` experiment 1 — a repair with ONLY the reason clause removed | `S5` | **`S2`** |
| `F12` experiment 2 — the supervisor's authorised one-liner, verbatim | `S5` | **`S2`** |
| a numeric constant bought a narrowing | `S5` | **`S2`** |
| the exemption abused with a vacuous proof | `S5` | **`S2`** |
| the exemption's boundary, `not x.ok` | `S5` | **`S2`** |
| `F4` — the inverted sense, `is True` | `S5` | **`S2`** |
| `F4` — a bare truthy capability read | `S5` | **`S2`** |
| `F15` — `assert True or X` verbatim | `S5` | **`S2`** |
| `F15` — the same vacuity, not spelled `True or` | `S5` | **`S2`** |

**Every one of the nine was an UNGATED promotion, and every one is now gated.** The remaining five are the
accept direction — the narrowed repair, `reason !=`, the `startswith` prefix, the legitimate exemption, and
an inverse guard with no proof — and all five classify the same in both, which is what an accept case is
for.

**All 31 calibration cases pass, the 17 that pre-date this row included.** `--selftest` re-executes the
whole set on every gate invocation, so this is a re-execution anyone can run rather than a claim.

### §1.7 — THE CONTRADICTION FROM §0.7 IS NOW MEASURED, AND IT STANDS

**The brief's §4 repeats, in bold, that *"the census must be re-run and the cell counts must move."*** The
census was re-run. **The cell counts did not move, and §0.5 predicted that before the fix existed.**

**`F12` is a REGRESSION-DETECTION hole and `6I-RUN.md` §6.5 says so in those words.** Today's baseline was
correct for today's tree. **A moved cell would have meant row 6i landed a defective repair — the brief's own
STOP condition — so the two halves of the instruction cannot both be satisfied by a healthy tree.**

**The demonstration is §1.6: nine cases the old instrument got wrong.** That is stronger evidence than a
moved cell, because a moved cell would have to be explained away first.

**This is raised as a shape, not bent to fit.** If the supervisor wants a moved cell it can only come from
repairing something the fix now flags — and the fix flags nothing new on this tree.

---

## §2 — THE THREE LIVE SITES

### §2.0 — `P3`, ONE INTEGER: **3**, committed before the census that scores it

**The repairs are written and the mirror is regenerated. The census has NOT been run since.** This
sub-section is committed alone so `git log` carries the order, exactly as §0 was.

**`P3` predicts that THREE sites change category, all of them `S1-SETUP-RESULT` -> `S5-PROVEN-ENVIRONMENTAL`,
leaving `S1` at 44 and `S5` at 14 with the 139 total unchanged.**

Derived by reading, not run: each of the three guards reads `gone`, an observation, and **before the repair
no assertion in any of the three functions reached it** — which is what put them in `S1` rather than in the
gated `S2` cell, and is why they were never baselined. The repair adds `assert not isinstance(gone,
Refusal)`, which reaches `gone` for the first time, so each site crosses into the observation-shared branch
and is then promoted by a proof the fixed checker validates on all three parts.

**Falsifier:** any count other than 3, any site landing anywhere but `S5`, or any movement in `S0`, `S2`,
`S3` or `S4`. **A site landing in `S2` would mean the repair produced exactly the shape it was made to
remove**, and it would be reported before anything else.
