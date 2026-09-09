# Ontoloche — decisions open to the founder

**As of 2026-09-09.** Scope: the `ontoloche` project only. Ordered by what your answer unblocks, not by age. **Item numbers are stable across days** — item 9 stays item 9 until it is ruled.

> This file is the GitHub-readable mirror of the founder decision page, so it can be read from a phone or any machine without the local HTML. The local page is `C:\Users\steph\.claude\fleet-supervisor\decisions\2026-09-09-ontoloche-decisions.html`; where the two disagree, this file is the one that was checked most recently.

**3 open · 1 is the biggest call in the project · 4 resolved 2026-09-07 · 2 FYI**

Nothing here is decaying. The repo is clean and fully pushed, row 6e is closed, and no session is running. These are decisions waiting on you rather than problems waiting on anyone. **Item 9 (Q56) is the one that matters**; the other two are small and have defaults in force.

---

## A. Decide now — 3 items

### 9 · Q56 — the audit found ONE design defect, and it is a question you were asked at trip 6 and have never ruled

*The biggest call in the project.*

**TL;DR.** Row 6e answered. The twenty-three kill-row trips are **four recurring implementation families (18 of 23), one order-dependence singleton, and ONE design defect** — and that design defect is the mechanism that **delivers the harm in twenty-one of the twenty-three**. It is not a discovery. It is **Q56**, flagged to you as the sixth trip's root cause and **named the class-closing question nine times without a ruling**. Under [ROADMAP.md](https://github.com/stephan-dyson/ontoloche/blob/main/ROADMAP.md)'s criterion, one design defect means `stop` fires. **My recommendation is that you rule Q56 and let that ruling decide whether `stop` fires, not the reverse.**

**Q56, verbatim from the register:**

> "should an identity claim be verified where it is MADE (`resolve_type`'s 1.0), or only where it is WRITTEN? — FLAGGED TO THE FOUNDER, not ruled. This is the sixth trip's root cause and the only question that closes a class."

**What the defect is, in mechanics.** Writes are guarded: is this word free, do these two predicates denote the same set, does a tombstone still hold this name. Reads are not. `resolve_type` answers with **confidence 1.0**, which [INTERFACE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md) §5.3 calls a *guarantee*, and nothing re-establishes at read time the facts that guarantee rests on. So a guard failing at a write does not produce a quiet inconsistency. It produces a registry that *confidently* tells the next caller the wrong thing at 1.0.

**Why it counted as design when four other recurring statements did not.** The audit's bar was *does a local fix remove it?* A comparison, a caller list, a matcher's width and a scan's order each have a line you can change, and all four were classified implementation however often they recurred. This one names *when a guarantee is granted relative to when its fact is checked*. There is no line. Your own shipped spec already says so, at INTERFACE.md §5.3:

> "Refusing to answer, or answering below 1.0, **would change the guarantee this section makes**, and deciding what this registry declines to serve is not an implementation call. It is Q56, it is the founder's, and it is open."

The cheap half shipped (warn when extents disagree); trips 12 and 13 proved that warning **structurally blind to transferred words**. The expensive half was never taken, explicitly because it changes the design.

**Why twenty-three countersignatures missed it.** Every one tested "is this design?" with the same narrow question — *is `namespace` untouched?* — which appears **ten times** in the register, and which **R90 had already found to be two claims, one never tested in six rulings**. `namespace` can be untouched in every trip while the read-side guarantee is what makes each one reach the harm. That is what "individually right, wrong in series" looks like.

#### Your options

| Rule Q56 | What it does | What it costs |
| --- | --- | --- |
| **`read`** | `resolve_type` re-establishes the identity claim when it answers, and may warn below 1.0 or refuse. **This removes the design defect**, and with it the delivery step in twenty-one of the twenty-three trips. `stop` becomes moot: you are fixing the thing it would have fired on. | It **changes a shipped guarantee**, which is why it was always yours. Reads get more expensive (an extent re-read on predicate hits). Callers who rely on 1.0 meaning 1.0 get a new answer shape. |
| **`write`** | Current behaviour becomes **deliberate and permanent**. The registry keeps promising 1.0 on write-time facts. | Then **`stop` genuinely fires**, because you have confirmed the delivery mechanism as design rather than defect. The register should also stop counting its consequences as defects: they are consequences of a ruled choice. |
| **`hold`** | I park row 6e and stop asking. | The question stays open, as it has since trip 6. |

**The trap, stated rather than hidden.** "It's a known issue" is both a fair reason not to panic *and* exactly how a design defect survives twenty-three trips. Nine deferrals of one decision, with twenty-one trips accumulating on it, is either ordinary prioritisation or precisely what a design defect looks like from the inside. I cannot measure which, and neither could the twenty-three countersignatures that each concluded *"implementation, not design."*

**The counterweight, in the audit's own words.** Every trip was caught **in test, none in a real merge**; two of the last five were **predicted in writing before the lens ran**; and this question has been open and visible since trip 6. Its closing sentence:

> "A founder may reasonably read E as a design question already on the table rather than a design defect, and the difference between those two readings is a ruling, not a measurement."

**Evidence.** The audit's full record is [6E-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6E-RUN.md). Its pre-registration (§0) is committed at `9dc994d` and is provably the **first and only** commit touching that file, which is what makes its falsifier binding: it fixed **eight** as the number of recurring/design trips below which its hypothesis dies, and got **eighteen**. I re-ran its load-bearing claims myself rather than countersigning on trust — *"answering to one identity"* occurs **zero** times in the register and **zero** in ROADMAP.md, whose actual criterion text is *"a capability predicate gets merged as a duplicate"*; Q56 is named the class-closing question **nine** times; its re-derivation script contains no write or mutation call.

**Ask: `read` or `write`, but not today unless you already know.** This is the only question in the project that closes a class, and I would rather you took it cold than fast. Say `hold` and I park row 6e and stop asking.

---

### 6 · Q97 — the governance register has a stop criterion. Arm it, or leave it recorded and inert?

*Created by your own ruling.*

**TL;DR.** Your `separate` opened a second register. A register that counts but can never say `stop` is a tally, not a criterion, so I drafted one — deliberately **before** the register has entries that would tempt me to write it favourably. It is **recorded and NOT armed** until you rule.

**Drafted criterion:** "An actor performs, or records as performed, a governed action that the surviving declaration reserves to a different authority, and no door refuses or warns."

**Reading if it fires:** the registry is granting authority it was told to withhold. Stop — a curation layer that cannot hold the line on who may act is worse than none, because the record it produces reads as authorised.

- **`arm`** — the criterion goes live and **entry 1 (A3) fires it immediately**, because A3 is exactly that shape. That is the honest consequence and you should know it before saying the word.
- **`record`** — entries accrue, nothing stops, and you keep the option to arm it later once you see whether the register grows.
- **`amend`** — tell me what it should say instead.

**Ask: `arm`, `record`, or `amend`.** Default in force: **record** (drafted, not armed). Register: [2026-09-07-governance-register.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-governance-register.md).

---

### 4 · Row 6d left a Postgres namespace behind — drop it or leave it?

*Low stakes, carried.*

**TL;DR.** The row's actions lens created `r3lens_de7fdace` on the `oo-pg` container and it was left in place under the project's no-deletion rule. Deleting anything is your call. Nothing is blocked by it.

**Now verifiable.** `oo-pg` is **Up**, so I can read the namespace list on your word rather than guessing at it.

**Ask: `drop it` or `leave it`.** On `drop it` I confirm the namespace is the row's and nothing else's, and report before removing.

---

## Context — all of these resolve on GitHub

- [ROADMAP.md](https://github.com/stephan-dyson/ontoloche/blob/main/ROADMAP.md) — the kill criterion in its own words, and the kill-row register with all twenty-three trips
- [6E-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6E-RUN.md) — the audit's full record
- [6D-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
- [INTERFACE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md) — §5.3 is the guarantee Q56 is about
- [PACKAGE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/PACKAGE.md) — C12-09 lives in §6.2
- [STATUS.md](https://github.com/stephan-dyson/ontoloche/blob/main/STATUS.md) — the project status page
- Rulings: [R96](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R96.md) · [R97](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R97.md) · [R98](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R98.md)

---

## E. Resolved 2026-09-07 — 4 items (history)

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

### 7 · Where the project stands

`main` = `origin/main`, **everything pushed**, working tree clean, `check_links` green and `check_spec_drift` exit 0.

**Corrected 2026-09-09:** `STATUS.md` had been naming `08cc48a` as the day's landing commit with two commits landed after it, and the first fix for that went stale the moment it was pushed, because a document that pins the current head is wrong on its own write. It now states the fact and names no head. This page carries no head either, for the same reason.

**No session is running** in this project; row 6e was closed after its record landed and was indexed in `docs/README.md`.

**Kill-row count stays TWENTY-THREE.** Governance register opens at **ONE**. Next ruling **R99**.

### 8 · Beacon is not at risk

The 2026-09-07 and 2026-09-09 commits touch `docs/` only — no storage contract — so beacon's pin `802ddf02` is unaffected, and it was re-verified as an ancestor at each landing.
