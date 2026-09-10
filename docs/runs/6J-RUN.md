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

**Answer 2 — the cheap local option is argued AFTER the fix, not now**, because until the fix exists its
size is an estimate and afterwards it is a measurement. It is not a blocker and it is not carried as one.
**Discharged in §3.4.**

> **`J16`, CORRECTED IN PLACE.** This sentence originally called it *"the item 3 cheap local option"* while
> §0.9, the brief and answers-1 all call the same thing **item 2**. Both designators trace: `6I-RUN.md` §7's
> own numbered list has *"**2.** The item 3 extension, scoped in §1"*, because §7's item 2 IS row 6i's §1
> scoping of the brief's item 3. **The row used both three pages apart and never said they were the same
> thing.** Everything in this record now says **item 2**, matching the brief.

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

> **`J12` — THE LINE-NUMBER CONVENTION, stated because this table does not share it with the rest of
> the record.** Every line above is the **capability-assertion** line, which is where the `grep` that
> found it hit. The census, §1.5, §2.1 and §2.3 all cite the **`pytest.skip(`** line, three or four
> lines below — 478 against 481, 1516 against 1520, and so on for all eleven — and §1.2 cites a
> **guard** line. Nothing here is false and none of it was consistent. **In a record that stops in
> §2.2 to write a citation note about `3969` against `3970`, this one was owed the same sentence, and
> two lenses said so.**

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
   `F12` experiment 1. **[`J17` — row 6i's measurement, `6I-RUN.md` §6.5, not this row's:** it
   classified `S5` there. §0 is a reading section and this originally said *"it currently
   classifies `S5`"*, which claims a live property of an instrument nothing had yet been run
   against.**]**
2. **Part 2, must refuse:** the `d3f9a79` site patched with the brief's authorised one-liner verbatim. This
   is `F12` experiment 2 — **`S2 -> S5` in `6I-RUN.md` §6.5's own run, again not this row's** — and it
   is the case that makes the hole about the brief rather than about the future.
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
`_establishes_not_that_type` forced to `False`. **[Observed — both censuses in one process, the
classifier loaded from its path by `importlib`, keyed by `(file, func, line)` and NOT by `ident`;
see `J19`]**

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
memory beside the working one — and classifying each case with both. **[Observed — each case string
through `classify_source()` on both modules, compared category by category]**

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

**Every one of the nine was an UNGATED promotion, and every one is now gated.**

> **`J11`, CORRECTED IN PLACE.** This read: *"The remaining five are the accept direction — the narrowed
> repair, `reason !=`, the `startswith` prefix, the legitimate exemption, and an inverse guard with no proof
> — and all five classify the same in both, which is what an accept case is for."* **The fifth is a REFUSE
> case.** *"An inverse guard with NO capability proof is still FLAGGED"* expects `S2`, and the old classifier
> already got it right. **Four accept cases and one refuse case the old classifier already refused** — found
> by two lenses independently.

> **`J11.1`, and it is not a wording fix: two of those four "accept" cases were accepted for the WRONG
> REASON, and round 1 proved it.** The `reason !=` case passes only because of a second assertion the first
> cut never read, and the `startswith` case would have passed with the negation removed and the `startswith`
> on an unrelated object. **Both are re-pinned in §3**, one of them by moving a live site out of `S5`.

**All 31 calibration cases pass, the 17 that pre-date this row included.** `--selftest` re-executes the
whole set on every gate invocation, so this is a re-execution anyone can run rather than a claim.

### §1.7 — THE CONTRADICTION FROM §0.7 IS NOW MEASURED, AND IT STANDS

**`J10`, CORRECTED IN PLACE: this sentence cited the wrong document.** It read *"The brief's §4 repeats, in
bold…"*. **[Observed — `grep -n "cell counts must move"` over the briefs directory]** the sentence is at
line 61 of **`2026-09-10-oo-6j-supervisor-answers-2.md`**, in that file's §4. The follow-on brief's §4 is
*"Not to be routed anywhere it does not belong"* and says nothing about the census. **This record's own
header separates "the brief" from the answers files, and §1.2 uses the separation correctly — so this is the
`R104` citation-defect class, committed against the brief that names it.** Only the second half of the
quoted clause is bold in the source, so *"in bold"* over the whole quote overstated it too.

**ANSWERS-2's §4 repeats that *"the census must be re-run and **the cell counts must move.**"*** The
census was re-run. **The cell counts did not move, and §0.5 predicted that before the fix existed.**

**`F12` is a REGRESSION-DETECTION hole and `6I-RUN.md` §6.5 says so in those words.** Today's baseline was
correct for today's tree. **A moved cell would have meant row 6i landed a defective repair — the brief's own
STOP condition — so the two halves of the instruction cannot both be satisfied by a healthy tree.**

**The demonstration is §1.6: nine cases the old instrument got wrong.** That is stronger evidence than a
moved cell, because a moved cell would have to be explained away first.

**This is raised as a shape, not bent to fit.** If the supervisor wants a moved cell it can only come from
repairing something the fix now flags — and the fix flags nothing new on this tree.

#### §1.7.1 — RESOLVED: the rule is WITHDRAWN, and the unchanged tree is a FINDING rather than an absence

**The supervisor withdrew it and verified the fact underneath it independently.**
**[Observed — the supervisor's own run of `--census` at `9b00bcc`, tree byte-identical before and after]**
the six cells came back `60 / 47 / 4 / 1 / 16 / 11`, identical to row 6i's post-repair census, and
`check_skip_census` exited 0.

- **WITHDRAWN:** *"the census cell counts must move."*
- **REPLACED BY:** the fix must be demonstrated to change behaviour **on inputs that exercise it** — cases
  the old checker got wrong and the new one gets right, re-executable by anyone. That is §1.6.

**The supervisor named its own error class, and it is one worth carrying: a rule that specifies an
OBSERVATION instead of the PROPERTY it actually wants.** *"The counts must move"* is a proxy for *"the fix
does something"*, and **a proxy that can conflict with another rule is a defect in the rule, not in the
tree.** Its satisfaction condition was a defect — either row 6i had landed a bad repair, or the suite's own
long-standing pattern was wrong.

**AND THE RESULT IS STRONGER THAN A MOVED CELL WOULD HAVE BEEN, which is the part not to soften into "no
change".** **All ELEVEN `S5` sites survive the full three-part axis** — row 6i's four repairs and the
suite's seven pre-existing ones, every one carrying a narrowed guard or the legitimate inverse shape, the
correct flag in the falsifying sense, and a defeasible assertion.

**A moved cell would have told us one site was wrong. An unmoved census under a strictly stronger checker
tells us all eleven were right for reasons the old checker never checked.** The old gate validated one part
of three and got the right answer anyway. **It now gets the right answer for the right reason, and the
difference is invisible in the counts and enormous in what it will catch tomorrow.**

---

## §2 — THE THREE LIVE SITES

### §2.0 — `P3`, ONE INTEGER: **3**, committed before the census that scores it

**The repairs are written and the mirror is regenerated. The census has NOT been run since.** This
sub-section is committed **before the census that scores it**, so `git log` carries the order.

> **`J13`, CORRECTED IN PLACE. This originally read *"committed alone … exactly as §0 was", and it was
> not.*** **[Observed — `git show --stat`]** `265aafc` touched **one** file. `43d0dac` touched **seven** —
> this record plus all six repaired test files. **The prose was alone in the commit; the commit was not
> alone.** The word "alone" is load-bearing in §0 precisely because it is provable there, and borrowing it
> here spent that credit on something that does not have it. The commit message itself was more careful and
> said only "before the census is run".

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

### §2.1 — The three sites, RE-LOCATED rather than trusted to a line number

The brief's line numbers predate row 6i's own edits and the supervisor had already been caught citing a
stale one, so all three were found by **test name** and then read at the point of use:

| site | test | the line as it stood |
|---|---|---|
| `ontoloche/contract/test_c3_resolve_type.py:695` | `test_c3_17_a_tombstone_elsewhere_is_found_by_the_words_it_answers_to` | `pytest.skip(f"this backend cannot retire the holder ({gone.reason})")` |
| `ontoloche/contract/test_c12_foundry_import.py:1317` | `test_c12_26_the_import_name_door_holds_the_byte_identical_tombstone` | the same line |
| `ontoloche/contract/test_c10_merge_types.py:1281` | `test_c10_23_the_escape_is_evaluated_over_the_whole_holder_set` | the same line, inside the per-order loop |

**All three numbers turned out to be current.** They are recorded as verified rather than as assumed,
because the check is cheap and the alternative is the defect the brief names.

**Five other sites carry the identical message and NONE of them was touched** — `test_c10_merge_types.py:1135`,
`test_c12_foundry_import.py:1080` and three in `test_c5_approve_reject.py`.

> **`J8`, CORRECTED IN PLACE. This originally read *"Two of those are item 4's baselined sites and the rest
> are item 5's unaudited population."* It is ONE, not two.** **[Observed — `docs/tools/skip_census_baseline.json`
> against the census]** the baseline's four are `test_c10_22`, `test_c12_21`, `test_c12_24` and `test_c3_27`,
> and only **`test_c12_21`** (`test_c12_foundry_import.py:1080`) is among the five. The baselined `c10` site
> is `test_c10_22` at line 1206, not `test_c10_21` at 1135. **So: one baselined, four in item 5's unaudited
> population.**

> **`J14`, CORRECTED IN PLACE. The justification that stood here was the standard §2.2 rejects one paragraph
> later.** It read: *"none of the five fires on any leg, which is the same reason item 4's four stay put."*
> **§2.2 claims of the three repaired sites "no possible victim, on any backend, not merely no observed
> one" — and then the five were excused on observed-only grounds.** A lens put the two sentences side by
> side.
>
> **And the five are not one population.** **[Observed — the `@pytest.mark.requires_capability` decorators]**
> `test_c12_21` and `test_c5_13` both declare `stores_events`, so the whole test is skipped on any backend
> lacking it and **their bare skip is structurally DEAD — provably unreachable, on any backend.**
> `test_c10_21` declares only `indexes_membership`, and `test_c5_14` and `test_c5_15` declare nothing. **On a
> backend that is legal under `PACKAGE.md` §3.2 — `indexes_membership=True`, `stores_proposals=True`,
> `stores_events=False` — those three reach the retire and hit the bare skip. They are LATENT, not dead.**
>
> **They stay anyway, and the honest reason is scope, not safety:** they are §7 item 5's population and the
> brief says *"do not repair them silently"*. **[Observed — `grep -c "cannot retire the holder"` over all
> three `-rs` logs returns `0` on each]** none of the five fires on today's matrix, which is a fact about
> today's backends and **not** the argument §2.2 makes. **Recorded as three latent sites this row is not
> authorised to touch, rather than as five sites that do not matter.**

### §2.2 — THE SAFETY IS PROVABLE BY CONSTRUCTION, and this row re-derived it rather than inheriting it

`6I-RUN.md` §3.3 made this argument for its own three `retire` sites. **These three are the same door, so
the argument transfers — but a transferred argument is exactly the thing this row's terms say to
re-measure.** Re-extracted from `ontoloche/registry.py` by walking every `return Refusal(...)` in `retire`
with its enclosing guard chain. **[Observed — `retire` spans `registry.py:3414-4186` and holds twelve]**

| refusals | gated behind | reachable at these three sites? |
|---|---|---|
| 9 of 12 | `successor is not None` | **no** — none of the three passes a `successor` |
| `live_consumers` (`3982`) | `report.gates_on and (not force)` | **no** — all three pass `force=True` |
| `no_consumer_evidence` (`4010`) | `not report.gates_on and ... and (not force)` | **no** — same |
| **`cannot_record_override` (`3970`)** | `force and (not self.caps.stores_events)` | **THE ONLY ONE LEFT** |

**So the fall-through this repair adds has no possible victim, on any backend, not merely no observed
one.** A refusal the capability does not explain cannot occur at these three calls, and if one ever could,
`assert not isinstance(gone, Refusal)` is what would say so.

> **`J15` — AND THAT MAKES THE FALL-THROUGH UNREACHABLE BY THIS ROW'S OWN PROOF.** If
> `cannot_record_override` is the only refusal these three calls can reach, and the branch above
> consumes it, then `assert not isinstance(gone, Refusal)` **cannot fire today.** A lens named it and
> the naming is right: the register elsewhere treats a guard that can never fire as a defect class, so
> calling this one a guard borrows a word it has not earned. **It is a NET against a future
> `registry.py` change** — the day someone adds a thirteenth refusal reachable under `force=True` with
> no successor, this line is what turns a silent skip into a failure. **Recorded as a net, at the cost
> of the stronger-sounding word.**

**A citation note, since `R104`'s `3969` has already been corrected once for pointing at the wrong door:**
`3969` is the **guard** `if force and not self.caps.stores_events` and `3970` is the `return Refusal(...)`
it gates. The comments this row adds cite `3969`, the guard, which is the line that explains the refusal.

### §2.3 — `P3` PREDICTED **3**, ALL `S1` -> `S5`. MEASURED **3**, ALL `S1` -> `S5`. HIT.

```
                       before   after
S0-ENVIRONMENT            60      60
S1-SETUP-RESULT           47      44
S2-RESULT-UNDER-TEST       4       4
S3-UNCONDITIONAL           1       1
S4-UNDECIDABLE            16      16
S5-PROVEN-ENVIRONMENTAL   11      14      total 139, unchanged
```

The three that moved are the three that were repaired, at their new lines —
`test_c3_resolve_type.py:708`, `test_c12_foundry_import.py:1330`,
`test_c10_merge_types.py:1297` — each with the guard
`isinstance(gone, Refusal) and gone.reason == 'cannot_record_override'` and each promoted by a proof the
fixed checker validated on all three parts. **`S0`, `S2`, `S3` and `S4` did not move, and the baseline did
not need to: these three were never in it**, which is what `S1` rather than `S2` meant.

**This is the ORDINARY kind of movement the supervisor named** — sites flagged, then repaired, under a gate
that now reads the guard. It is not the movement the withdrawn rule asked for in §1.7, and the two are
different things.

### §2.4 — The suite at the final state

| leg | floor (row 6i's final) | this row | delta |
|---|---|---|---|
| sync, SQLite only | 528 / 731 / 0 | **528 passed, 731 skipped, 0 failed** (299.20s) | **0** |
| sync, three backends | 943 / 316 / 0 | **943 passed, 316 skipped, 0 failed** (651.59s) | **0** |
| async, three backends | 979 / 316 / 0 | **979 passed, 316 skipped, 0 failed** (365.99s) | **0** |

**Run one at a time, never in parallel**, by `6I-RUN.md` §0.7's own commands. **Zero drift on every cell.**

**The skip count NOT moving is the check, not the absence of one.** The narrowing makes a refusal that is
not `cannot_record_override` FAIL where it used to skip. **If any id at these three sites had been skipping
on some other reason, it would now be a FAILURE, and there are none.** That is the construction proof of
§2.2 confirmed on live code, on three legs, rather than argued.

### §2.5 — THE REPAIR IS EXERCISED, WHICH IS WHY IT WAS WORTH MAKING

**All three sites fire, on all three legs, one id each.** **[Observed — the `-rs` blocks]**

```
test_c3_resolve_type.py:708      1 id   ... before there is a tombstone for the other namespace to find
test_c12_foundry_import.py:1330  1 id   ... before there is a byte-identical tombstone for the name door to hold
test_c10_merge_types.py:1297     1 id   ... before there is a tombstone for the escape to be evaluated against
```

**And the old message is gone from every log**: `grep -c "cannot retire the holder"` returns `0` on all
three.

> **`J7`, CORRECTED IN PLACE. This paragraph originally read: *"Nine `NOT REACHABLE: stores_events=False
> refuses the forced retire` firings per leg now, where six of the nine belong to row 6i's repairs and
> three are this row's."* BOTH HALVES ARE WRONG.**
>
> **The number is SIX, not nine.** The `9` came from `grep -c`, which counts the five `SKIPPED` lines **and**
> four lines of the conformance summary block — **the same events, in two report blocks, counted twice.**
> **[Observed — `grep "^SKIPPED" leg2_sync3.log | grep "refuses the forced retire"`]** the `SKIPPED` entries
> are `c10:1297` (1 id), `c12:1128` (2 ids), `c12:1330` (1 id), `c3:708` (1 id), `c4:481` (1 id) = **6 ids**.
>
> **The split is THREE and THREE, not six and three.** This row's three fire one id each. Row 6i's
> contribution under this message is `c12:1128`'s 2 plus `c4:481`'s 1 = **3** — and `6I-RUN.md` §4.1 records
> exactly that, `2 / 1 / 0`. Row 6i's fourth repair, `test_c10_merge_types.py:1374`, fires under a
> **different** message ("refuses the acknowledgement"), and its `test_c9_retire.py` copy fires on no leg.
>
> **THE SHAPE IS THE POINT: `6 + 3 = 9`, so the wrong split summed correctly.** `6I-RUN.md` §6.6 names that
> as the error that survives review, this record quotes that warning two sections earlier, and then commits
> it. **Found by two independent lenses; one of them also checked it against `6I-RUN.md` §4.1's landed table
> and found this row contradicting a record it had itself cited.**

**Corrected: SIX firings per leg — three row 6i's (`c12:1128` at 2 ids, `c4:481` at 1) and three this row's
(`c3:708`, `c12:1330`, `c10:1297`, one id each).**

**This is the difference between these three and item 4's four.** These were observed firing before the
brief was written and are observed firing after the repair. Item 4's four have been unobserved on three
legs across two rows, and **naming a capability for a refusal never seen fire is `C19-100` closing a legal
operation** — so they stay.

### §2.6 — The mirror, verified the reliable way

```
git diff --stat 16becf6 -- ontoloche/contract      ->  3 files, 66 insertions(+), 6 deletions(-)
git diff --stat 16becf6 -- ontoloche/aio/contract  ->  3 files, 66 insertions(+), 6 deletions(-)
```

`tools/unasync.py` was run **once, as a generator**, and reported `wrote 3 of 25 files`. **It was never run
to verify anything.** The verification is two independent things:

1. **The normalised diff.** Each file's sync diff and aio diff are **byte-identical after normalising away
   `async def` and `await`** — checked per file, all three identical.
2. **`test_generated_matches_source.py` RAN on the async leg**, which loads `unasync.py` and regenerates
   the whole tree in memory to compare. **It is absent from that leg's `-rs` skip block**, which is how
   this row knows it ran rather than skipped — the test skips itself from an installed wheel where `tools/`
   is not shipped, and a skipped anti-drift check reads exactly like a passing one in a totals line.

### §2.7 — The five gates

| gate | result |
|---|---|
| `check_links.py` | **exit 0** |
| `check_spec_drift.py` | **exit 0** |
| `check_merge_guard.py` | **exit 0** |
| `check_capability_matrix.py` | **exit 0**, run to completion with the Postgres DSN |
| `check_skip_census.py` | **exit 0** — 4 result-conditioned skips, baseline 4, the ratchet holds |

**The set stays FIVE.** The checker fix repaired an existing gate rather than adding one, which is the
supervisor's answer 1, and this row proposed no separate executable.

**This is this row's run. The supervisor runs them again before closing the row, and that run is the one
that counts** — "landed" means verified on `origin` by `git ls-remote`, never a row's own word for it.

**THE VERIFICATION BOUNDARY, stated before landing rather than after.** The five gates are re-executed by
the supervisor. **The suite legs — 528 / 943 / 979 — are THIS ROW'S numbers and are labelled as this row's**,
the same as rows 6g, 6h and 6i; the supervisor does not re-run them. The `-rs` logs match every figure cited
from them here, and their **authenticity rests on trust rather than on re-execution**, because reviewers are
barred from running the suites.

---

## §3 — THE ADVERSARIAL ROUND

### §3.0 — THE ROUND'S OWN DEFECT CLASS, FIRST, BECAUSE IT IS THE FINDING ABOUT THE INSTRUMENT

**NO LENS FOUND `J19`.** Four fresh lenses, one of them briefed on nothing but the classifier, and the
hole that lets an ordinary commit walk past the ratchet was found **here** — because a measurement script
written in this row keyed a dict by `Site.ident` and silently lost 46 of 139 sites. **The instrument error
was this row's. Chasing it is what exposed the gate's.**

**And the lens briefed on the classifier fell into the same hole and did not notice.** Lens A ran a
cell-by-cell census comparison to confirm this row's "0 sites moved" and reported
`S0 47 / S1 18 / S2 4 / S3 1 / S4 9 / S5 14` — **93 sites, against a tree of 139** — as though it were the
whole census. Its conclusion was correct. **Its measurement was not, and nothing in its own report would
have told it.**

> **A LENS THAT REACHES THE RIGHT ANSWER FROM AN INCOMPLETE MEASUREMENT IS NOT A PASSING LENS.** It is
> `F14`'s shape moved up one layer: a true statement standing on evidence that does not carry it. **The
> adversarial round is this project's strongest instrument and it has just been shown to carry the same
> defect class it exists to catch.**

**This row hit the identical trap twice more while measuring the answers-5 conditions, and both are worth
the sentence.** A classifier loaded from the scratchpad resolves `REPO_ROOT` to the scratchpad's
grandparent, so its `SCAN_DIRS` do not exist and `census()` returns **zero sites in silence**; and
reassigning `SCAN_DIRS` afterwards does nothing, because `census(directories=SCAN_DIRS)` binds its default
at definition time. **Both failures return a clean, plausible, empty answer.** That is how lens A got 93
and how this row got 0 — and it is why every measurement in §3.4 and §3.6 passes its directories
explicitly and keys on `(file, func, line)`.

### §3.1 — Round 1, and the ratio is the interesting number

**Four fresh lenses, one artefact, four separate briefs: the classifier, the numbers, the repair, the
record.** Verdicts: **three `NOT YET`, one `SHIP IT`.** Eighteen consolidated findings, `J1`-`J18`.

| | MAJOR | MINOR |
|---|---|---|
| **the CLASSIFIER — code** | **6** (`J1`-`J6`) | 0 |
| the RECORD — prose and numbers | 3 (`J7`-`J9`) | 9 (`J10`-`J18`) |

**THAT SPLIT IS THE RESULT, not the total.** `6I-RUN.md` §6.6 records fifteen findings across four rounds
and thirteen lens-passes, and **NOT ONE WAS A CODE DEFECT** — every one was a claim in a record that outran
its evidence. **This round found six defects in the CODE, in a single pass, and every one of them was in
the fix written to close the last row's routed finding.** The first round in three rows to break that
pattern.

**Every finding was reproduced HERE before being accepted.** A lens's report is a hypothesis; eleven
exploit sources were fed to the live `classify_source()` and the categories pasted into the working notes
before a line was changed. **One lens's follow-up was WRONG and is recorded as wrong:** it reported that
the three `-rs` logs no longer existed on disk and that §2.5 therefore rested on nothing checkable. **They
exist, at the paths another lens had just run commands against.** The finding underneath it (`J7`) is real
and stands; the escalation was false and did not go in.

### §3.2 — The six classifier MAJORs. Every one of them is `F12`'s own shape.

**[Observed — each exploit through `classify_source()` on the classifier at `9b00bcc`, then again after the
rebuild]**

| | the shape that defeated it | at `9b00bcc` | rebuilt |
|---|---|---|---|
| **`J1`** | `if not isinstance(gone, Refusal): … else: <proof>; skip()` | `S5` | **`S2`** |
| **`J2`** | `not isinstance(gone, Success)`, and `not isinstance(gone, str)` | `S5` | **`S2`** |
| **`J3`** | `isinstance(gone, Refusal) and not adapter.dsn.startswith("postgres://")` | `S5` | **`S2`** |
| **`J4`** | `reason != "x"`, `reason not in (…)`, `"key" in detail`, `reason != ""` | `S5` | **`S2`** |
| **`J5`** | `(caps.f and False) is False`, `(caps.f and gone.ok) is False`, `explains(caps, gone) is False` | `S5` | **`S2`** |
| **`J6`** | the `S2` refusal text says "CANNOT FAIL" of `caps.f == 0`, which does fail | — | **corrected** |

**`J1` IS THE SHARPEST AND IT IS EXACTLY WHAT THIS ROW EXISTS TO PREVENT.** `_guard_chain` recorded which
tests enclose a skip and **threw away whether the skip was reached through the `if` or the `else`.** So the
exemption earned by `not isinstance(gone, Refusal)` was handed to the else-branch — **the one branch where
the value IS a refusal and its reason DOES exist.** The `why` then printed *"establishes the value is NOT a
refusal, so there is no reason to compare"* about that branch. **That is `F12` verbatim, inside the fix for
`F12`, complete with a false `why` — which is `F15` — in a row that closed both.**

**`J2` is the same class one level down.** The exemption checked that the call was `isinstance` and never
looked at the TYPE. Negating the SUCCESS type names the refusal family exactly.

**`J4` did more than admit exploits: it accepted a LIVE SITE FOR THE WRONG REASON.** `test_c10_25`'s guard
is `out.reason != "alias_collision"`, a complement that names nothing. The site is genuinely correct — but
because of `assert out.reason == "predicate_merge"` sitting above the skip, **which the first cut never
read.** The rebuild reads it: a naming may come from the guard **or** from an assertion in the skip's own
branch, and that is how the site is actually safe.

**`J5` is `F15` surviving in a spelling the walk did not visit.** `_falsifying` asked whether a capability
appeared *anywhere inside* the compared side, so `(registry.caps.stores_events and False) is False` —
constantly true — passed. **The commit that introduced it said the pin was "on the property rather than on
the wording" and it was on neither.** The rebuild requires the compared side to **be** a capability read.

**`J6` is `F15` pointed the other way.** Three expressions that DO fail on a capable backend were refused
with a sentence that was false of the expression it had just quoted. Refusing them is fail-closed and
right; **printing a false reason is the defect this row was opened to remove.** The text now says what the
gate READS, which is a claim about the gate rather than about the expression.

### §3.3 — `J19`: THE SITE IDENT IS NOT AN IDENTITY, AND THE RATCHET CAN BE DEFEATED

**Not one of round 1's eighteen. No lens found it.** It surfaced because a measurement script written HERE
keyed a dict by `Site.ident` and silently lost 46 of 139 sites — **the instrument error was this row's, and
chasing it is what exposed the gate's.**

**[Observed — a synthetic source through `classify_source`, then the gate's own `new` computation]**

```
A. baselined: ONE result-conditioned skip
    S2  line 6   ident t.py::test_one_flagged#0

B. a commit ADDS a second one to the SAME function
    S2  line 6   ident t.py::test_one_flagged#0   guard: isinstance(gone, Refusal)
    S2  line 10  ident t.py::test_one_flagged#0   guard: isinstance(out, Refusal)

    the gate's own `new` computation -> []
    reported: 0        actually present: 2
```

**`Site.ident` is `file::func#ordinal`, and ordinals are assigned per *(function, GUARD TEXT)*.** Two skips
in one function with different guards both carry `#0`, so
`new = [i for i in found if i not in set(declared)]` absorbs the second. **The ratchet does not turn.**

**On the live tree: 139 sites collapse to 93 distinct idents, 36 idents carry more than one site, and FOUR
non-`S2` sites already share an ident with a baselined `S2` site** — `test_c10_22`, `test_c12_21`, and two
in `test_c12_24`. **One guard-edit at any of those four and a new result-conditioned skip is invisible.**

**PROVENANCE, AND IT IS THE STREAK AGAIN.** The per-guard ordinal is **row 6h's own adversarial-round fix**,
and the code says so in its own comment: a plain per-function counter renumbered a flagged site whenever an
ordinary skip was added above it, and *"a gate that fails for unrelated reasons is a gate somebody
weakens"*. **That remedy traded a false failure for an identity that is not an identity.** It is the fourth
consecutive row in which an adversarial round's own fix carried the next defect, and **the second time into
this instrument** — `F12` was the first.

> **NAME THE PATTERN, because four rows of instances have not produced one and the supervisor asked for
> it: A FIX THAT REMOVES A SYMPTOM BY WEAKENING THE THING THAT DETECTS IT.**
>
> The per-function ordinal produced false failures. The remedy made the ordinal per-guard, which stopped
> the false failures **by making two different sites indistinguishable to the detector**. `F12` is the
> same shape: `_capability_proof` was tightened twice by a lens, and neither tightening was *look at the
> guard*, so the check kept its name and lost its reach. **Both fixes were correct about the symptom and
> both narrowed what the instrument could see.**
>
> **The test that would have caught both: after a fix, can the instrument still distinguish the cases it
> could distinguish before?** Neither row asked it. This row asks it of its own fix in §3.6.

**AND IT IS WORSE THAN `F12` IN ONE RESPECT, WHICH IS WHY IT IS NOT BEING QUIETLY ROUTED.** `F12` needed
someone to strip a clause from a working repair. **This needs nothing but an ordinary contributor adding an
ordinary skip to one of four named functions.**

**NOT FIXED IN THIS ROW WITHOUT A RULING, and the reasoning is in
`2026-09-10-oo-6j-questions.md` `Q2`.** The fix puts the guard into the ident, which **rewrites every entry
in the baseline file** — a wholesale baseline change landing in the same commit as a classifier change, which
makes the two impossible to review apart. That is the narrower version of exactly why row 6i routed `F12`.

**A LENS'S OWN NUMBER FELL INTO THIS HOLE AND THE LENS DID NOT NOTICE.** Lens A reported a cell-by-cell
census comparison as `S0 47 / S1 18 / S2 4 / S3 1 / S4 9 / S5 14` — **a 93-site tree** — and drew a correct
conclusion from a partial measurement. **The conclusion happened to hold. The measurement did not, and
nothing in the lens's own report would have told it.** That is recorded because a reviewer's number is not
more trustworthy than a row's, and this record cites none of it.

### §3.4 — §7 ITEM 2 IS DISCHARGED, AND THE CHEAP LOCAL OPTION IS NOT CHEAP

**The debt: answers-1 §2 — *"When the fix is in and the census re-run, tell me what the local option
actually costs and I will rule."*** The fix is in and the census re-run. **`J9` is that this record reached
§2.7 without coming back to it**, and a promise made to the supervisor and left open is the prior row's
`F5`/`F6` shape.

**[Observed — the option simulated by making a helper's parameters their own observation roots, then
re-censusing with a `(file, func, line)` key rather than the colliding `ident`]** **EIGHT sites move, and
three go the wrong way:**

| movement | count | what it is |
|---|---|---|
| `_skip_if_cannot_record` `S4` -> `S5` | 1 | the intended win, and it does work |
| four `conftest.py` sites `S4` -> `S1` | 4 | harmless reclassification |
| **three `_tombstone_holding` copies `S1` -> `S2`** | **3** | **NEW flagged sites, on row 6i's own repairs** |

**The three helpers guard on `word`, a parameter, and assert `word in (gone.aliases or ())`.** Make the
parameter an observation root and the guard reads an observation the assertions reach, which is `S2` by
definition. **So the cheap local option buys one promotion and costs three new baseline entries at the
three sites row 6i repaired last night.**

**Recommendation: it stays its own row**, which is `6I-RUN.md` §1's own verdict and `R104`'s scoping.
**This is the measured argument the supervisor asked for rather than the conclusion he was offered before.**

### §3.5 — What is open, and where it is written down

**Two items are with the supervisor in
`C:\Users\steph\.claude\fleet-supervisor\briefs\2026-09-10-oo-6j-questions.md`**, each with the options,
this row's recommendation, and what it blocks:

- **`Q1`** — `test_c12_27` reclassifies `S5` -> `S2` under the corrected axis, so the ratchet baseline must
  go from **4 to 5**. Recommendation: raise it, and leave the site alone. **GRANTED.**
- **`Q2`** — `J19`, above. Recommendation: route it, with the live-exploitability caveat named rather than
  buried. **ROUTED, with one condition on an interim.**

**Both rulings are in `2026-09-10-oo-6j-supervisor-answers-5.md` and both were decided on the evidence
rather than around it, which is what the file was for.** The supervisor verified before ruling that
`git diff` across row 6i's range touches `test_c12_27` **zero** times, so his STOP condition correctly did
not fire, and that the arithmetic reconciles with his own cycle-70 run: `S5` **11**, this row's three
repairs take it to **14**, this reclassification takes it to **13**.

### §3.5.1 — `Q1` GRANTED, and the principle it turns on

> **A RATCHET BASELINE RECORDS WHAT THE INSTRUMENT CAN PROVE, NOT WHAT THE AUTHOR BELIEVES.**

**The supervisor's sentence, and it is why the baseline rose rather than the rule bending.** `test_c12_27`
is semantically sound: a backend that CAN hold aliases and declined the row anyway fails
`assert registry.caps.stores_aliases is False` rather than skipping. **What the gate cannot do is know that
`"import_refused:"` is evidence of a refusal — that is domain knowledge no AST carries, and a gate that
pretended otherwise would be asserting something it has not established.**

**Option 3 — widening the exemption to admit a complemented predicate — was refused for the decisive
reason:** `not gone.reason.startswith("cannot_")` has the identical shape and admits a whole family.
**Taking it would have traded a false negative for exactly the false positive this row exists to close.**

**RAISING A BASELINE IS NORMALLY THE MOVE THAT NEEDS A RULING BECAUSE IT IS HOW A GATE GETS QUIETLY
WEAKENED. THIS ONE ROSE BECAUSE THE GATE GOT STRICTER**, which is the opposite fact, and the record says so
in those terms so that a later reader counting five flagged sites does not read five defects.

**THE RECORDING REQUIREMENT, and it took a second pass to actually meet.** The ruling required the fifth
entry's `why` to say *which kind* it is, legibly in the baseline file and without reading this record. The
first write did not: the rebuilt `_capability_proof` reported the narrowing failure and stopped, so all
five entries read alike. **The refusal text now names the kind in both directions.** **[Observed —
`docs/tools/skip_census_baseline.json` at `count: 5`]**

| entry | kind |
|---|---|
| `test_c10_22`, `test_c12_21`, `test_c12_24`, `test_c3_27` | *no assertion in the skip's own branch reads a capability at all, so there is no proof here to check* |
| **`test_c12_27`** | ***the block DOES assert `registry.caps.stores_aliases is False`, which fails on a backend holding the capability — so the proof may well be sound and THIS GATE CANNOT VERIFY IT. A limit of the instrument, not an established defect in the suite*** |

### §3.5.2 — The extension is its own row. A RULING now, not an inclination.

`answers-4` §3 said the supervisor was inclined and told this row not to treat it as a decision. **§3.4's
measurement settled it:** eight sites move and **three go the wrong way, as new flagged entries at the three
sites row 6i had just repaired.** **One promotion bought at the price of three new baseline entries on
freshly-repaired code is a bad trade, and it is now a measured one rather than an argued one.** Recorded
with the table, not the conclusion.

### §3.6 — `Q2` ROUTED, AND THE INTERIM ITS CONDITION ALLOWED

**`J19` goes to its own row with the demonstration in §3.3, the way row 6i routed `F12` here.** The
supervisor took this row's third reason as decisive: **a second structural change to the same instrument,
in the same row, after a round that found six MAJORs in the first one, is how the streak continues rather
than ends.**

**But the caveat was not left unmitigated, and the mitigation was specified as a PROPERTY rather than as an
observation — the supervisor's own lesson from the rule he withdrew this morning.** Option 3 was permitted
**if and only if** this row could measure that it (1) touches no classification and (2) needs no change to
`skip_census_baseline.json`'s schema or contents, deriving per-function counts from the existing `sites`
list rather than storing them.

**BOTH CONDITIONS MEASURED AND MET.**

**Condition 1.** **[Observed — the classifier at `ace7081` and the classifier now, both censusing the same
two directories passed explicitly, keyed by `(file, func, line)`]** 139 sites before, 139 after, **sites
whose category changed: 0. Sites whose `why` text changed: 0.** The change lives entirely inside
`run_gate`, which neither `census()` nor `classify_source()` calls.

**Condition 2.** **[Observed — the interim run against a baseline object with the `why` key stripped]** it
reads `site` and nothing else, and returns the same answer. **The `why` field is `Q1`'s recording
requirement and the interim neither needs it nor notices it.**

**WHAT THE INTERIM IS.** `found` and `declared` are lists with one element per flagged site, so comparing
them as **multisets** instead of sets catches an addition whose ident collides:

```
baselined: 1 entry     now flagged: 2 sites
  set test  (before): reports 0  -> []
  multiset  (after):  reports 1  -> ['t.py::test_one_flagged#0']
```

**ITS LIMIT, MEASURED RATHER THAN ASSERTED, because a mitigation whose edges are not stated is how the next
row inherits a false sense of cover.** **[Observed — one flagged site removed from a function and a
different one added]** the counts hold and **the swap is INVISIBLE**. Only a real identity closes that,
which is why the routing stands rather than being quietly cancelled by the interim.

**And the interim answers §3.3's own test — *after a fix, can the instrument still distinguish the cases it
could distinguish before?*** It can distinguish strictly more: every case the set test caught, plus the
colliding addition. **It distinguishes strictly fewer than nothing it previously could.** That is the
question neither row 6h's fix nor `F12`'s asked of itself.

**A standing change to how this row talks to the supervisor, and it is his ruling:** questions go in a
**file** from now on, not only into the pane. **[Observed — his `tmux capture-pane -p -S -`]** the pane
holds **nineteen** non-blank lines, so a question not acted on within one supervision cycle is
unrecoverable. **He sends prose by file for the same reason and had not noticed the return channel carried
the same defect.**
