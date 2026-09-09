# R99 — Q56 is ruled `read`. The identity claim is verified where it is MADE.

**Founder ruling, 2026-09-09. His word: `read`.**

Question, verbatim from the register ([`2026-08-30-4c-rulings-R48-R57.md`](2026-08-30-4c-rulings-R48-R57.md)):

> **Q56** — should an identity claim be verified where it is MADE (`resolve_type`'s 1.0), or only where it is WRITTEN? *FLAGGED TO THE FOUNDER — not ruled. This is the sixth trip's root cause and the only question that closes a class.*

**Ruled: `read`.** The claim is verified where it is made.

---

## 1. What this ruling actually decides, which is narrower than it sounds

The cheap half of Q56 **already shipped**, in row 4d on 2026-08-30 under the Q56 *default*: `resolve_type` re-reads both predicate extents on an alias or successor hit and carries `identity_stale` when they no longer agree. What it could not do was act on what it found. The default's own words:

> **Confidence stays 1.0 — the expensive half is the founder's.**

So `read` does not introduce read-time verification. It **authorises the resolver to answer on what the verification found.** That is the expensive half, and the register named exactly why it was never the supervisor's to take, in `INTERFACE.md` §5.3's own text:

> "Refusing to answer, or answering below 1.0, **would change the guarantee this section makes**, and deciding what this registry declines to serve is not an implementation call. It is Q56, it is the founder's, and it is open."

It is now ruled. `resolve_type` may answer **below 1.0**, and may **refuse**, when the identity claim it is about to make does not re-establish at the read.

## 2. What it does to the kill row

Row 6e's audit ([`6E-RUN.md`](../runs/6E-RUN.md)) found `I=5 · R=17 · D=1` against a falsifier fixed at **eight** before a single trip was read. The one `D` is statement **`E`**:

> the registry treats a fact checked at WRITE time as true at READ time, at `resolve_type`'s §5.3 guarantee of 1.0

`E` is the mechanism that **delivers the harm in twenty-one of the twenty-three trips**. Every other family is a story about a guard, and a failed guard is only a trip when something then answers at 1.0.

**`read` removes `E`.** Not mitigates it — removes the step that turns a failed guard into a confident wrong answer.

### `stop` is RESOLVED, and it is not a sixteenth decline

The fifteenth put of `stop` has stood unanswered since 2026-09-05, held open deliberately by [R96](2026-09-07-founder-ruling-R96.md) pending this audit. It is now **answered, by removing its subject.**

This must not be recorded as a sixteenth decline, and it is not one. A decline says *the criterion tripped and we are continuing anyway*. What happened is different: the criterion's one design defect was identified, put to the founder as the question it had always been, and **ruled in the direction that eliminates it**. The kill row does not fire because the thing it would have fired on is being taken out.

The distinction is the whole point of having kept `stop` open rather than declining it again. A register that logs a decline here would be recording the opposite of what occurred.

**Kill-row count stays TWENTY-THREE.** A ruling is not a trip.

## 3. What it costs, stated because it was the founder's to spend

1. **A shipped guarantee changes.** `INTERFACE.md` §5.3 currently promises `confidence: 1.0` on an `existing` outcome. After this ruling it does not, unconditionally. Every caller that reads 1.0 as "safe to act" gets a new answer shape, and Beacon slice 1 is the caller that matters — it was told (relay of 2026-08-30) that it *"can trust a 1.0 redirect, or is told not to"*. This ruling is the second branch.
2. **Reads get more expensive.** One extent re-read per alias hit on predicates, already paid by the 4d default; refusing or scoring adds the decision, not the read.
3. **`Refusal.reason` is a closed vocabulary** (§5.12). If refusal is the chosen answer for some cases, this ruling mints at least one new value, with its §5.4 row in the same commit, under R3.

## 4. What this ruling does NOT decide, and must not be read as deciding

`read` fixes the **principle**: verification happens where the claim is made, and the resolver may act on it. It does not fix the **policy**. These are row work, and the row must answer them with evidence rather than assume them from this ruling:

- **Refuse, or answer below 1.0, or both by case?** Both are authorised. Which applies where is not ruled.
- **What confidence does a stale-but-answerable redirect carry?** Not ruled. It must not be invented to a round number without a reason on the record.
- **Does this reach beyond predicates?** The 4d default is predicates-only. Trips 12 and 13 proved that warning **structurally blind to transferred words**, which is a gap in the cheap half, not something `read` closes by itself.
- **What does a refusing `resolve_type` do to `preflight`, `list_types(predicate=)` and `_extent`?** R54 already made those resolve the identity. Their behaviour when the identity does not re-establish is unspecified.

## 4b. All four sub-questions are ANSWERED IN SPEC, landed 2026-09-09 at `f388cd1`

Row 6f amended `INTERFACE.md` §5.3 **before touching the resolver** — verified by the supervisor: the spec
commit is the only commit against `INTERFACE.md` in this row, and `ontoloche/registry.py` has **no** commit
in the row at all. The answers:

| §4 sub-question | The row's answer, in `§5.3.2` |
|---|---|
| Refuse, or answer below 1.0, or both? | **Score. NEVER refuse.** `5.3.2-11` — *"this call does NOT refuse on its own account, and R99's authorisation to refuse is deliberately unused."* |
| What confidence does a stale redirect carry? | **`min(resolver_score, J)`**, `J` the **Jaccard agreement of the two written extents** (`5.3.2-9`). Derived from quantities the call already reads, never a round number chosen for roundness. |
| Does this reach past predicates? | **Yes.** `5.3.2-10` — `kind="action"` is verified too, **by its own operand**: an action family has no extent, so its identity claim stands on its governance declaration. One principle, two operands, no invented third. |
| What is Beacon slice 1 told? | It never receives a refusal it did not ask for. `5.3.2-12` makes **`min_confidence` govern this path**, which **[Observed, row 6f] it did not** — the redirect returned before the check was reached, so a caller passing `min_confidence=2.0` still got `existing` at `1.0`. A consumer that wants to decline on a weakened identity now declines with **its own bar**. |

### The refusal you authorised is not being used, and that is a result, not a shortfall

**This was PRE-REGISTERED before the resolver was opened** — §0 of `6F-RUN.md` at `b257f3b`, line 129,
committed as the first and only change to that file: *"…the answer to sub-question 1 is 'answer below 1.0,
never refuse', and **R99's authorisation to refuse goes unused by this row**."* The row fixed that outcome
as a falsifier **that would cost it the interesting answer**, and then reported it.

**Verified by the supervisor** rather than accepted: the sentence is in the pre-registration commit, whose
ordering is provable, not in a later one.

**So §3's cost estimate was too high, in the founder's favour.** §3 warned that *"callers who rely on 1.0
meaning 1.0 get a new answer shape"* and that a refusal path might mint a new closed-vocabulary value. No
value is minted; no caller is refused. The change is **strictly less disruptive than this ruling
advertised** — the registry stops vouching where it cannot vouch, and hands the caller the measurement
instead of a door in the face.

**What is NOT yet done.** The spec is landed; the resolver is uncommitted working-tree changes, and the
row's adversarial rounds have not run. Nothing above is a claim about shipped behaviour.

## 5. It converges with the governance register's entry A3, and that is load-bearing

A3 ([the governance register](2026-09-07-governance-register.md), entry 1) is BLOCKING and open. Its harm is delivered like this:

> `resolve_type` answers the dead word with the survivor at **1.0**, while `preflight` answers the same word with the **tombstone's** policy — and a Haiku-tier machine actor records `applied` against a verb the surviving family declares human-approval-only and irreversible.

**That delivery step is `E`.** [R97](2026-09-07-founder-ruling-R97.md) already recorded the same observation from the other side, when it corrected its own reason for filing A3 separately: *"`resolve_type` answering a word with the survivor at 1.0 while `preflight` answers it with the tombstone's policy **is** two things answering to one identity."*

So `read` removes **A3's delivery**. It does **not** close A3, and no one should read it that way. A3 also stands on two write doors with ordinary calls — `retire(successor=)` returning `('RETIRED','retired',[])` with no refusal, and `import_types` returning **warnings EMPTY** — and this ruling touches neither. A3 stays **open and unfixed** until the write doors refuse or warn.

What it does mean is that the read-side work this ruling opens and the read-side half of A3's fix **are the same work**, and sequencing them as two rows would build the same thing twice.

## 6. Consequent

- Q56 moves from *flagged, unruled* to **RULED** in the register, with the default it displaces named.
- The kill row's `stop` is marked **resolved by R99**, explicitly not declined.
- A row opens for the read-side change. It is spec-first: `INTERFACE.md` §5.3's guarantee is amended before the resolver changes, because the guarantee is the thing being ruled on.
- The row carries §4's open sub-questions as its own, and is not permitted to settle them by assertion.

Recorded by the ontoloche supervisor. Source for the audit's numbers: [`6E-RUN.md`](../runs/6E-RUN.md). Prior rulings this day: [R100](2026-09-09-founder-ruling-R100.md), [R101](2026-09-09-founder-ruling-R101.md).
