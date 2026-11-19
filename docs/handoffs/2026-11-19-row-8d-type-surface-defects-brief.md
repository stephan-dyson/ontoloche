# Row 8d brief — the type-surface defects (D14 and B5-1)

**Drafted and opened 2026-11-19 by the supervisor, after row 7d landed and merged into `main`.** The founder said on 2026-11-18 "you don't need my permission to move to the next item on the roadmap". This is the last recorded in-repo defect work: every roadmap item after it is gated outside this repo (Phase 3's exit needs a real outside user, Phase 2B is beacon's, Phase 4 waits on Phase 3).

---

## 0. The two defects

- **D14 (MAJOR, recorded by row 8b, [`8B-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8B-RUN.md) §2.5 finding 1, still unrouted per [DECISIONS-OPEN item 23](https://github.com/stephan-dyson/ontoloche/blob/main/docs/DECISIONS-OPEN.md)).** An alias write over a tombstone that has a successor gives one word two live claimants, for every kind, with no warning, and the tombstone can no longer be reinstated (`reinstate` refuses `successor_active`). The probe reproduces it as line D14 (`docs/tools/properties_baseline_probe.py`). Rule 2.10-17 and `INTERFACE.md` §12 record it.
- **B5-1 and B5-2 (recorded by row 8c, [`8C-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8C-RUN.md) round 5).** In `import_foundry`, an **absent** shared property type (or interface) whose apiName converts to the same word as a different one the document defines binds the slot (or predicate) to that other row with no warning. R110 compares planned items only. The dry run says `not_in_document` and the real run resolves. The plan holds the evidence (the apiNames differ), so it can be reported.

## 1. What the row delivers

1. **D14 first, red first.** A failing contract test reproducing two live claimants for one word after an alias write over a tombstone with a successor, on all three backends and every kind.
2. **D14's fix splits by what it does:**
   - A **warning** that tells the caller the word now has two live claimants is the row's call.
   - **Refusing** the alias write, or **changing which claimant** a reader resolves to, decides what the registry refuses or holds. That goes to the founder as a new `docs/DECISIONS-OPEN.md` item with options and a recommendation. The row builds today's behaviour as the default in force, pinned by a test, plus the warning, and keeps going.
3. **B5-1 and B5-2:** the import reports the case (warning on the plan and the result), and the dry run and the real run agree. If the right answer is to refuse the bind, that is a refusal question and is routed the same way.
4. **Row 8c's other round-5 MINORs** (A5-1 to A5-3, C5-1 to C5-7) only where a fix is small, safe and reaches no refusal question. Otherwise record why each is left.
5. **Async mirror regenerated** with `tools/unasync.py`, never by hand.

## 2. Out of scope

- Non-default answers to DECISIONS-OPEN items 19 to 22, 25 and 28 to 34 (the founder's).
- The ingestion surface (rows 7b to 7d) and ING16.
- New features.

## 3. Design tests, expected outcomes in §0 before any run

- **D14 probe line** flips from "two live claimants, no warning" to "warned", and the default-in-force behaviour is pinned.
- **B5-1** on the employee fixture's dangling `fooSpt` plus a hand-added `FooSpt`: the plan and the result both report it, and dry and real runs agree.
- **The five Foundry fixtures and UC1 to UC3:** every landing byte-identical to row 8c's except where a new warning is added.
- **Kill row:** pre-register which doors the fix touches (the alias write, `reinstate`, the reader's successor walk, R110's comparison) and predict where the D14 shape recurs before any lens runs.

## 4. How the row runs

- §0 of `docs/runs/8D-RUN.md` is pre-registered and committed first.
- Failing tests committed before the code that turns them green.
- Every touched contract id seen red by mutation.
- All five gates exit 0.
- Adversarial loop to row 6j's stopping rule. **Cap: three rounds plus a confirming round.**
- A finding that would make the code refuse or hold something is routed to `docs/DECISIONS-OPEN.md` and the default in force is built.
