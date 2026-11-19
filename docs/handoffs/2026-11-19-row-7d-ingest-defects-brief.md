# Row 7d brief — the ingestion defect row (ING15 first)

**Drafted and opened 2026-11-19 by the supervisor, after row 7c landed not clean (`8283983..a9d3cb0`, [`7C-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7C-RUN.md)) and merged into `main`.** The founder said on 2026-11-18 "you don't need my permission to move to the next item on the roadmap".

---

## 0. Why this row is next

**Every other roadmap item is gated on something this repo cannot supply.**

- Phase 3's exit criterion is that "the staff doing manual uploads lose the hour a day". That needs a real outside user running ingestion.
- Phase 2B (roadmap #5) is the beacon program's call, in beacon.
- Phase 4 opens "only after Phase 3 works for a real outside user" ([`ROADMAP.md`](https://github.com/stephan-dyson/ontoloche/blob/main/ROADMAP.md)).

**What is left in this repo is defects already found and recorded, and one of them is a MAJOR now on `main`:**

- **ING15 (MAJOR, row 7c §2.8 finding 1).** Rule 4-10's similar-candidate step reuses a candidate this act landed `pending`. Over the CMS triple, `WESTON` is folded into `EAST`'s identity at 0.944, which is below `match_at`, so no reviewer sees it. That is the pollution machine the project exists to prevent, and it ships today.

So this row fixes ING15 first, then the smaller recorded defects on the same surface. A defect that the fix touches stops being a "later row" item.

## 1. What the row delivers

1. **ING15 fixed**, red first. The fix must leave a candidate this act landed `pending` unable to absorb a label the gate answered `proposal` for. 7c §2.8 names the untried option ("reuse only a candidate the act itself proposed"). Treat it as a starting point, not as settled. Re-measure the Q92 split on the 3,346-row `erm2-nwe9` slice and state the cost (7c: 1,029 proposed, 2,310 reused, 7 pending).
2. **ING15's two MINORs** (7c §2.8 findings 2 and 3): the `reused` why text for a `pending` candidate, and a test plus a mutation for `_similar_candidate`'s `CandidateRef` filter, constructed under a `propose_below` where it is reachable.
3. **Row 7b's three recorded build-lens minors** (7B-RUN §2.6): the `decode` substring match in `_fetch_instance_rows`, the `Fraction` overflow in `_non_finite`, and the recursive operand walk. Each one fails closed today, so fix it only where the fix is small and safe. Otherwise record why it is left.
4. **Row 7c's recorded MINORs that are not refusal questions.** Refusal questions stay with DECISIONS-OPEN items 32 to 34 and are not decided here.
5. **Async mirror regenerated** with `tools/unasync.py`, never by hand.

## 2. Out of scope

- The non-default answers to items 19 to 22, 25 and 28 to 34 (the founder's).
- Q92's design change (`row_attributes` read at resolution). ING15's fix is narrower than that.
- D14 (retire-then-alias) and B5-1 (row 8c). They sit on the type surface, not the ingestion one, and they get their own row.
- New features.

## 3. Design tests, expected outcomes in §0 before any run

- **The CMS triple** (`EAST`, `WEST`, `WESTON`, 7c §2.8): after the fix, `WESTON` lands as its own proposal or in `review`, never `reused` onto a pending candidate.
- **The Q92 slice:** the split is re-measured, and Q92's 60% floor still holds or the run says by how much it misses.
- **Kill row:** pre-register which doors the fix touches (rule 4-10's key, rule 4-11's pending check, rule 4-13's per-act memory) and predict before any lens runs where the ING15 shape recurs.

## 4. How the row runs

- §0 of `docs/runs/7D-RUN.md` is pre-registered and committed first.
- Failing tests committed before the code that turns them green, as row 7c did.
- Every touched id seen red by mutation (`docs/tools/ingest_mutation_sweep.py`).
- All five gates exit 0.
- The adversarial loop runs to row 6j's stopping rule with a pre-registered cap. **Cap: three rounds plus a confirming round.** The row is narrow.
- A finding that would make the code refuse or hold something is routed to `docs/DECISIONS-OPEN.md` and the default in force is built.
