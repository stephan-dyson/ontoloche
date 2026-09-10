# R104 — `S5` is a named category, the middle cell's repair direction is UP, and the evidenced repairs are authorised but NOT to row 6h

**Supervisor ruling, 2026-09-09.** Ruling the three items row 6h routed in
[`6H-RUN.md`](../runs/6H-RUN.md) §3, and recording that **the model this supervisor gave the row was wrong
and the row proved it.**

> **CORRECTION, made within the hour and recorded rather than erased.** This ruling was first written,
> committed and pushed saying `S5` spans **five** files. **It spans FOUR** —
> `test_c10_merge_types.py`, `test_c12_foundry_import.py`, `test_c19_actions.py`, `test_c9_retire.py`,
> confirmed by running the row's own `check_skip_census.py --census` and listing the distinct paths behind
> its seven `S5` sites. **The supervisor took the figure from the row's §1.2 prose without counting it**,
> and the row — which had made the same error twice in its own first draft, caught by its round's numbers
> lens — flagged it before the supervisor noticed. **That is the fifth carried attribution in this project
> and the third to come from a document rather than a worker.** The count of *five files* elsewhere in §5
> is a different and correct fact: the row's diff touched five files.

---

## 1. `S5` is a named category. The rule this supervisor wrote would have deleted a correct pattern.

The brief's discriminator said a skip whose guard reads the result under test is **never** legitimate.
**That is false, and the counter-example is not an edge case — the suite invented the exception on purpose,
uses it in seven sites across FOUR files, and documented it in its own words.**

**[Observed — read by the supervisor at `ontoloche/contract/test_c10_merge_types.py:1489-1502`, not accepted
from the row]:**

```python
if not isinstance(refused, Refusal):
    # NOT REACHABLE, never a pass. ... Gated on the CAPABILITY rather than on the
    # outcome, so a store that CAN hold the alias and merged anyway is a finding
    # and not a skip.
    assert degraded.caps.stores_aliases is False, (...)
    pytest.skip("NOT REACHABLE: ...")
```

**The mechanism, stated as a mechanism rather than a judgement:** break the implementation on a *capable*
backend and the assertion fails, so the id **FAILS** and does not skip. That is precisely the repair of
`C3-26`'s defect — *"if the implementation returned `0.0` or `1.0` tomorrow, the id would SKIP, not fail"* —
applied by the suite before this row existed.

**`S5` is therefore legitimate and the gate must not flag it.** It is to be recorded in `6H-RUN.md` as a
**category with a name**, not as a footnote to a refuted model, because the next row that touches this needs
`S5` to be a thing it can look up.

**A gate built on this supervisor's rule would have deleted working coverage in four files.** That sentence
belongs in the record more than any number in it.

## 2. The middle category — reading 1 **and** reading 3. Reading 2 is refused.

`S1` is the largest cell at **49** sites, and `_tombstone_holding` exists three times near-identically with
**only the copy that asserts its fixture held being flagged**.

**The gate is pointing at the right defect in the wrong member of the family.** That is `F1`'s shape
surviving `F1`'s fix: the row stopped the gate *rewarding* de-assertion, but the asymmetry that made the
best-asserted copy the flagged one remains.

- **Reading 1 is adopted:** the two unflagged twins are **under-asserted**. The c4 copy is not
  over-asserted.
- **Reading 3 is adopted as the general answer:** the `S5` proof — an `assert registry.caps.X is False`
  before the skip — is the repair for this whole shape. It converts an unevidenced skip into an evidenced
  one, with precedent in four files.
- **Reading 2 is REFUSED.** Moving `D1`'s `S1`/`S2` line to make the strongest member legal would weaken
  what *legitimate* means in order to make a passing gate — the same trade the gate exists to refuse.

**The repair direction is UP, not down.**

## 3. The row's restraint was correct and is not overridden

Row 6h was **authorised** to repair unambiguously result-under-test sites and **declined on a measurement**:
four of the six flagged sites were **never observed firing on any leg**, and naming a capability for a
refusal never observed is inventing the explanation.

**That is `C19-100`'s defect — it closed a legal operation — which row 6g re-created at three doors two days
ago while trying to honour the ruling against it. Twice in two days is a pattern, not bad luck.**

**The two evidenced repairs are AUTHORISED and are NOT row 6h's to make.**
**`registry.py:3969` is `if force and not self.caps.stores_events:`, which explains
`test_c4_propose_type.py:467`; `registry.py:5317` is `if acknowledge and not self.caps.stores_events:`,
which explains `test_c10_merge_types.py:1337`.** Both return `cannot_record_override` and both are a
`stores_events` fact, so the repair is one line each and well evidenced.

> **CORRECTION, 2026-09-10 03:35. This paragraph cited `3969` for BOTH sites and stamped it *"verified by
> the supervisor"*. It explains ONE.** `test_c10_merge_types.py:1337` calls `merge_types` with
> `acknowledge=` and never passes `force`. Found by row 6i's adversarial round, which named this ruling
> as the **third carrier** of the defect while the record it was correcting had named only two.
>
> **THIS WAS THE WORST OF THE THREE CARRIERS, and not because it is a ruling.** It is the worst because
> it says *verified by the supervisor* next to a claim the supervisor had not verified. **That phrase is
> load-bearing in every record in this project**, and a reader who checks nothing else trusts this line
> **because a supervisor signed it.**
>
> **What the supervisor actually did wrong is not the obvious thing.** The line at `3969` was opened and
> confirmed to say what was quoted. **The quote was verified and never the applicability — whether it
> was the line that site reaches. Running the instrument on the wrong subject is not running the
> instrument.**
>
> **Nothing in the ruling changes.** The capability is the same, the repair is the same, and row 6h's
> restraint is upheld as before.

**They still do not go into this row, and the reason is what this row proved most expensively.** Its
adversarial round found **five BLOCKING, two of them defects in fixes made an hour earlier**, one invisible
from inside while the calibration passed and the number looked plausible. **A change made after the
adversarial round has not been through the adversarial round**, however small and however well evidenced.
*"It is only two lines"* is the exact sentence that precedes it.

They go to a follow-on with its own round, together with the other four once the async leg evidences them,
so the family is repaired as **one coherent change**. The row's worry about a half-repaired family is right,
and the answer is to do **none** of it here rather than all of it here.

## 4. What this ruling does NOT do

- **Kill row stays TWENTY-THREE.** This row is not kill-row shaped, it did not self-classify a trip, and it
  was right not to.
- **The governance register is untouched and still counts ONE. The criterion stays ARMED.**
- **`Q101` and per-key severity stay OPEN and stay the founder's.** Nothing here touches either.
- **§3.3's helper-parameter hole is NOT closed** — a result-conditioned skip inside a helper that takes the
  result as a parameter is invisible to this gate. The row **pre-registered it as known exposure and it
  fired**, which is the pre-registration working rather than a gap in the work. It is the follow-on's first
  item.

## 5. The verification, listed so it can be attacked

Run by the supervisor against row 6h's `7f13800`, not accepted from the row:

- **All FIVE gates exit 0 under the supervisor's own run**: `check_links`, `check_spec_drift`,
  `check_merge_guard`, `check_capability_matrix`, `check_skip_census`.
- **`check_skip_census.py` writes nothing when invoked plain** — tree clean before and after, and the code
  read as well as the behaviour: the only write is `BASELINE_PATH.write_text` at line 1142, inside
  `write_baseline()`, reached only under `if args.write_baseline`. **Checked because it was a fact this
  supervisor had written into its own cron, and a fact you wrote down is not evidence.**
- **The diff is 2448 insertions and ZERO deletions** across five files; **no test file was modified**, which
  matches §3.2 exactly.
- **The pre-registration ordering holds:** `7e24f25` at 21:30:11 touched one file and nothing else;
  `250f9b8` landed ten minutes later.
- `git ls-remote origin refs/heads/main` = `7f13800`.

## 6. The sentence worth carrying out of this

**Twice in one day this supervisor's own instruction was the defect** — the brief's wire-the-gate-in-
immediately clause left the row no legal move against 121 existing sites, and the discriminator would have
destroyed a working pattern in four files. **Both were caught because the brief said the model was a
starting point and not a ruling, and the row took that at its word instead of implementing around it.**

**A brief that cannot be contradicted produces a row that implements the brief's mistakes.**

Recorded by the ontoloche supervisor. Row record: [`6H-RUN.md`](../runs/6H-RUN.md).
Prior: [`R103`](2026-09-09-supervisor-ruling-R103.md).
