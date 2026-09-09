# Ontoloche — decisions open to the founder

**As of 2026-09-09.** Scope: the `ontoloche` project only. Ordered by what your answer unblocks, not by age. **Item numbers are stable across days** — a ruled item keeps its number and moves to section E rather than being deleted.

> This file is the GitHub-readable mirror of the founder decision page, so it can be read from a phone or any machine without the local HTML. The local page is `C:\Users\steph\.claude\fleet-supervisor\decisions\2026-09-09-ontoloche-decisions.html`; where the two disagree, this file is the one that was checked most recently.

**1 open · 7 ruled · 3 FYI**

**2026-09-09: you ruled all three open items in one pass, including the oldest and largest question in the project.** Q56 is closed after ten days and twenty-three kill-row trips; the governance stop criterion is armed and has fired; and the namespace item turned out to name something that does not exist. Details in section E.

One new item is below, and it exists because ruling item 4 uncovered it rather than because anything went wrong.

---

## A. Decide when you want to — 1 item

### 10 · `oo-pg` is carrying 625 leftover schemas. Drop them, or leave them?

*Low stakes. Raised by your item-4 ruling, not blocking anything.*

**TL;DR.** Your `drop it` on item 4 authorised deleting one namespace attributed to row 6d. That namespace **does not exist** (see item 4 in section E). What *does* exist is **625 `oo_*` schemas** on the `oo-pg` container, left by every three-leg suite run this project has made. **I did not touch them**, because they are a different and much larger object than the one you ruled on, and reading your word as covering them would be taking a destructive action you did not sanction.

**The facts.** 625 as of today, up from **476** on 2026-09-05 and **193** during row 6c. The container has `RestartCount=0` and a persistent volume, so they accumulate indefinitely. They **slow the postgres leg** of the three-leg suite; they have never failed it.

- **`drop them`** — I confirm each is a suite artefact and nothing else's, report the list length, then remove. The postgres leg gets faster. Nothing in the repo depends on them.
- **`leave them`** — they keep accumulating. The cost is suite time, and it grows.

**Ask: `drop them` or `leave them`.** Default in force: **leave** (the project's no-deletion default).

---

## Context — all of these resolve on GitHub

- [ROADMAP.md](https://github.com/stephan-dyson/ontoloche/blob/main/ROADMAP.md) — the kill criterion in its own words, and the kill-row register with all twenty-three trips
- [6E-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6E-RUN.md) — the audit's full record
- [6D-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
- [INTERFACE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md) — §5.3 is the guarantee Q56 is about
- [PACKAGE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/PACKAGE.md) — C12-09 lives in §6.2
- [STATUS.md](https://github.com/stephan-dyson/ontoloche/blob/main/STATUS.md) — the project status page
- The [governance register](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-governance-register.md) — its stop criterion is now ARMED and FIRED
- Rulings 2026-09-09: [R99](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R99.md) · [R100](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R100.md) · [R101](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R101.md)
- Rulings 2026-09-07: [R96](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R96.md) · [R97](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R97.md) · [R98](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R98.md)

---

## E. Ruled — 7 items

### 9 · Q56 — verify the identity claim where it is MADE → **RULED: `read`** *(2026-09-09)*

Recorded as [R99](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R99.md). **The oldest open question in the project, closed after ten days and twenty-three kill-row trips.**

**What it decides.** The *cheap half* of Q56 already shipped in row 4d on 2026-08-30: `resolve_type` re-reads both predicate extents on an alias or successor hit and carries `identity_stale` when they disagree — but **confidence stayed 1.0**, because acting on what it found was yours. `read` takes the **expensive half**: `resolve_type` may now answer **below 1.0** and may **refuse**. That changes `INTERFACE.md` §5.3's shipped guarantee, which is exactly why it was never the supervisor's.

**What it does to the kill row.** It removes statement **`E`** — *the registry treats a fact checked at WRITE time as true at READ time* — which row 6e's audit found is the mechanism **delivering the harm in twenty-one of the twenty-three trips**. So the criterion **does not fire**, and **the fifteenth `stop` is RESOLVED, explicitly not declined a sixteenth time**: a decline says *the criterion tripped and we are continuing anyway*, and that is not what happened. Its subject is being removed. **Count stays TWENTY-THREE** — a ruling is not a trip.

**What it does not decide.** Refuse-versus-score, what confidence a stale redirect carries, and whether any of this reaches past predicates are all still open. They belong to the row this ruling opens, which is spec-first: §5.3's guarantee is amended before the resolver changes.

### 6 · Q97 — the governance register's stop criterion → **RULED: `arm`** *(2026-09-09)*

Recorded as [R100](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R100.md). **The criterion is LIVE and entry 1 (A3) fired it immediately** — which was disclosed on this page before you gave the word, so the halt is deliberate rather than an accident of drafting.

**Why A3 meets it.** A Haiku-tier machine actor *records `applied`* against a verb the surviving family declares *human-approval-only and irreversible*, and **no door refuses or warns**: `retire(successor=)` returns `('RETIRED','retired',[])` and `import_types` returns **warnings EMPTY**, both on ordinary calls with `force` and every acknowledgement removed.

**In force now.** No further ACTIONS-surface row launches until A3's write doors refuse or warn; A3's fix is the gating work on that surface; and because the criterion's stated harm is that *the produced record reads as authorised*, any `applied` already written through this path is **suspect until established otherwise** rather than assumed absent.

**Not halted:** the project, and the read-side row R99 opens. Firing adds **no entry** — the governance register still counts **ONE**, and it is never folded into the kill-row count.

### The two rulings meet on A3, from opposite ends

This is the part worth knowing, because it changes what gets built. A3's harm is delivered by `resolve_type` answering the dead word with the survivor **at 1.0** while `preflight` answers it with the tombstone's policy. **That delivery step is `E`.** So **R99 removes A3's delivery** and **R100 halts the surface until A3's write doors are fixed**. Neither closes A3 alone, and **A3 closes only when both halves land**. It is still open and unfixed. The practical consequence: the read-side work R99 opens and the read-side half of A3's fix are **the same work**, and sequencing them as two rows would build the same thing twice.

### 4 · The row 6d namespace → **RULED: `drop it`** — and there was nothing to drop *(2026-09-09)*

Recorded as [R101](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R101.md). **Nothing was deleted.**

This page promised that on `drop it` I would *"confirm the namespace is the row's and nothing else's, and report before removing."* The confirmation found that **`r3lens_de7fdace` does not exist** — not in `open_ontology`, not in `postgres`. This is not lost state: the container has **`RestartCount=0`** and a persistent volume dating to 2026-08-28, and 625 other schemas from the same era are still there.

**The name has no source in the row's own record.** It appears nowhere in `6D-RUN.md`. Its only occurrences anywhere are in the supervisor documents that carried the item forward. **So this item spent four days on your page naming an object that was never observed.** The page did disclose it was unverified, which is why this is a hygiene failure rather than a false claim — but verifying it was one command, and it should have happened when the item was written, not when you ruled on it. The standing correction is recorded in the supervisor's handoff.

The real residue is 625 `oo_*` schemas, which is **item 10** above rather than something folded into a word you gave about something else.

---

## E2. Resolved 2026-09-07 — 4 items (history)

### 5 · `git push` — fixed, and fixed durably

**RESOLVED.** The day's seven commits are on `origin/main`, after being stuck at `655f515` all day behind a 403.

**The unblock:** you re-authenticated as `stephan-dyson`, which made it the active gh account, and the push went through unchanged.

**The durable fix, which matters more:** the key is now registered on that account, `~/.ssh/config` has a `Host github-stephan` block pinned to `id_ed25519` with `IdentitiesOnly yes`, and this repo's remote is `git@github-stephan:stephan-dyson/ontoloche.git`. **SSH never consults gh**, so pushing here no longer depends on which account is active — switch back to `stove-bison` freely.

**Verified, not assumed:** `ssh -T git@github-stephan` → *"Hi stephan-dyson!"*; `fetch` exit 0; `push --dry-run` → *Everything up-to-date*. The beacon pin `802ddf02` was re-checked *at* the landing and is still an ancestor; the whole day's diff is docs-only.

**For the second account,** which was your actual question: generate a second key, register it on `stove-bison`, add a second `Host` block with its own `IdentityFile` and `IdentitiesOnly yes`, and point that repo's remote at the new alias. Without `IdentitiesOnly`, ssh offers every key and GitHub authenticates you as whichever it accepts first.

**One error of mine on the record:** while writing this item's queue entry I wrapped a gh command in backticks inside a double-quoted shell argument, which *executed* it and launched a stray device-login flow. It failed closed and changed nothing (auth state, push and repo all re-verified afterwards), but the hazard is now written into the supervisor's standing notes.

### 1 · Row 6d landed — what opens next → **RULED: `audit`**

Recorded as [R96](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R96.md). Row 6e ran and is now closed.

It wrote **no product code**. Its one question: *are the twenty-three kill-row trips twenty-three implementation defects, or ONE design defect found twenty-three times?* Each had been ruled *"implementation defect, not design"* by the supervisor who found it, one at a time, and the series had never been read as a series.

**The part of this ruling that matters most:** `stop` is **held open, not declined a sixteenth time**. The fifteenth put stands unanswered pending the audit; the register must not record a decline that did not happen. And the audit was required to be able to return an answer that costs the project — if it found one design defect, `stop` fires and the merge-centred shape goes back on the table. It found one.

### 2 · Q94 — governance identity → **RULED: `separate`**

Recorded as [R97](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R97.md); the governance register is open with **A3 as entry one**.

**The reason previously on file was wrong, and is corrected in the record rather than edited over.** *"The identity criterion is not met"* does not hold: `resolve_type` answering a word with the survivor at 1.0 while `preflight` answers it with the tombstone's policy **is** two things answering to one identity. The ruling stands for a better reason — a count that grows on a widening definition stops being a signal, which is the project's own *"a widened matcher is a minted rule"* turned on its own register.

**Separate does not mean filed away:** A3 is BLOCKING, reachable with ordinary calls on two of three doors, and open.

### 3 · Q95 — `C12-09`'s narrowing → **RULED: keep**

Recorded as [R98](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R98.md). `C12-09` is **kept**; the rule binds aliases only.

Two evidential reasons: round 3's lens drove the transfer doors and **could not build a harm the blessed write does not already produce one door earlier**; and overturning would deliberately repeat the mistake round 3 had just made — its own false refusal **closed a legal operation for two rounds**. The residual stays on the record, and the gate records the gap rather than hiding it.

**The warn-only idea is routed, not adopted.** It is my construction, unverified, and it went to row 6e to *verify or kill* with its falsifier stated, under the same never-self-classify rule that binds a worker. Killing it is a live outcome.

---

## F. FYI — no action needed

### 11 · `Q50` is still open, still yours, and is parked on purpose — surfaced so it cannot repeat Q56

*No action. Listed because the failure it could repeat just cost this project ten days.*

**The question.** May a `stores_proposals=False` backend hold a `kind="predicate"` entry at all? Like Q56, it decides **what the registry declines to serve**, which is why it is yours and not the supervisor's.

**Default in force, and it is safe:** yes, written with warning `predicate_requires_review` — row 4c's behaviour, pinned by `C10-10`. The alternative, `Refusal(reason="proposals_not_stored")`, would mean beacon's own shape (`PACKAGE.md` §7.4) **cannot carry a capability predicate**. The kill row's danger is a predicate going live *and then being merged*, and **the merge is guarded on every backend regardless of this answer**.

**Why it is not in section A.** Its own register entry says it is *"revisited with beacon 2B's evidence"*, and that evidence does not exist yet. Asking you to rule now would be asking you to rule without the thing the question says it needs.

**Why it is on this page anyway.** Q56 also had a safe default in force, and that is exactly what let it sit flagged and unruled for ten days while twenty-three kill-row trips accumulated on it. A default in force is not a reason a question stops being visible. **It moves to section A the moment beacon 2B produces its evidence**, and the supervisor is watching for that rather than waiting to be asked.

Register entry: [`2026-08-30-4c-rulings-R48-R57.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-08-30-4c-rulings-R48-R57.md).

**This is the complete list.** A sweep on 2026-09-09 found exactly one question flagged to you and unruled across every document in the repository, and it is this one.

### 7 · Where the project stands

`main` = `origin/main`, **everything pushed**, working tree clean, `check_links` green and `check_spec_drift` exit 0.

**Corrected 2026-09-09:** `STATUS.md` had been naming `08cc48a` as the day's landing commit with two commits landed after it, and the first fix for that went stale the moment it was pushed, because a document that pins the current head is wrong on its own write. It now states the fact and names no head. This page carries no head either, for the same reason.

**No session is running** in this project; row 6e was closed after its record landed and was indexed in `docs/README.md`.

**Kill-row count stays TWENTY-THREE.** Governance register opens at **ONE**. Next ruling **R99**.

### 8 · Beacon is not at risk

The 2026-09-07 and 2026-09-09 commits touch `docs/` only — no storage contract — so beacon's pin `802ddf02` is unaffected, and it was re-verified as an ancestor at each landing.
