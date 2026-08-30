# Supervisor handoff — open-ontology, 2026-08-29 21:10 (power-down)

> **Package renamed** `open_ontology` → `ontoloche` at commit <rename-sha> (2026-08-30); the commands and paths quoted below are as recorded at the time.

**From:** the fleet supervisor for PROJECT open-ontology (Fable, session `434d2782-2053-4d5e-b775-819012bbb1a6`, tmux `fleet-supervisor-open-ontology`, pane %20). **To:** the next supervisor of this project. The founder is powering the box down; the tmux server, this session's cron and the worker session all die with it. **Everything below is what does NOT die: the repo, the working tree, the briefs, and the ruling register.**

## 0. First five actions (in order, ~10 minutes)

1. **Do not touch the working tree until you have read §2.** `C:\Users\steph\projects\open-ontology` is `main` at `eed593c` on origin with **13 files dirty on disk = the worker's round-1 fix in progress (+1785/−169), uncommitted.** No `git stash`, no `checkout`, no `reset`. It is the only copy.
2. Claim the role: `FLEET_SUPERVISOR_PROJECT=open-ontology py C:/Users/steph/projects/mission-control-fleet/tools/fleet_supervisor/role.py status` → it will read `stale`; claim with `role.py claim --session-id "$CLAUDE_CODE_SESSION_ID" --tmux-session fleet-supervisor-open-ontology --interval 15`. Your own session must be tmux-hosted under that name (`~/.claude/skills/launch-claude-session/SKILL.md`).
3. Resume the worker **in its own transcript** rather than relaunching: `tmux new-session -d -s oo-4c-edge-semantics -c /mnt/c/Users/steph/projects/open-ontology "/home/steph/.local/bin/claude-pane --model opus --resume 0881d827-cb7b-4bc6-bc27-7658527ce804"` (verify the wrapper passes `--resume` through; if it does not, run `claude.exe --resume 0881d827-cb7b-4bc6-bc27-7658527ce804 --model opus` inside the pane). Its context was 572k when it died; if resume fails or it is incoherent, launch FRESH on the same brief (§3) with the pointer *"read the brief at `C:\Users\steph\.claude\fleet-supervisor\briefs\2026-08-29-oo-4c-edge-semantics.md`; items 1–10 are on origin/main through `eed593c`; the dirty working tree is round 1's fix in progress — inspect it with `git diff --stat`, finish it, commit it as '4c round 1', then continue the loop from `docs/runs/4C-RUN.md`."*
4. Recreate the cycle cron (15 min, `4,19,34,49 * * * *`) with the prompt in §6 — it is the exact text this session was running, facts current as of this handoff.
5. Read the founder the state in one line: *"4c is 10 of 12 items on main; round 1 of its loop found 22 issues incl. a fifth kill-row route (paging); the fix was mid-flight when the box went down and sits uncommitted on disk; resumed."*

## 1. Where the project is

| row | state |
|---|---|
| #1–#3, 3b, reorg, 3c, 3d, #4, 3e, 4b, #6 | **DONE** — see [`STATUS.md`](../../STATUS.md), [`ROADMAP.md`](../../ROADMAP.md) |
| **4c edge semantics** (build, Opus) | **IN FLIGHT** — items 1–10 of 12 on `origin/main` (`07e7384` R34 · `cbbebbb` R37 · `c0b4176` R38 · `c40fddd` R39 · `34ce5df` R33 · `3fdbbe7` R40 · `8e641e6` checker + 4th trip · `7c61148` constraint 8 · `eed593c` [`4C-RUN.md`](../runs/4C-RUN.md) with Q49–Q55). Item 11 (adversarial loop, cap 3) is in **round 1**: 22 findings (8 blocking / 7 major / 7 minor), the biggest a **FIFTH kill-row route** — the identity guards read predicate extents through a paging adapter primitive and never followed the cursor, so two extents that differ past page one compare equal (repro: worker scratchpad `rev_killrow.py`, `DegradedAdapter(page_cap=2)`). Fix + checker gaining a *partial/paged* extent state + C17-37/44/45 extensions = the dirty tree. Item 12 (landing) not started. |
| #5 Phase 2B (beacon) | not ours; 21.1 landed as Draft `6e87d61a`, **founder approval pending** |
| #7 Phase 3 | not started; must decide paging (R25), tenancy (R24/Q38), value-level + ledger conditions (R41) first |

**Suite floor:** 196 ids, sync 606 passed (as of #6); 4c has added ids on top — never accept a landing below the floor.

## 2. The dirty working tree (do not lose it)

`git status --short` at 21:08 showed 13 modified files: `docs/specs/EDGES.md`, `INTERFACE.md`, `PACKAGE.md`, `docs/tools/check_merge_guard.py`, `open_ontology/registry.py` + `aio/registry.py`, `contract/test_c10_merge_types.py`, `test_c12_foundry_import.py`, `test_c17_edges.py` (+ aio twins), `test_manifest.py`. **It is the worker's round-1 fix.** Only the worker (resumed or fresh) commits it; the supervisor never commits worker files (shared tree, commit-by-path rule). If a fresh worker is told to inspect and finish it, that is the intended path.

## 3. Sessions, briefs, ids

- Worker: tmux `oo-4c-edge-semantics`, was pane `%54`, claude session **`0881d827-cb7b-4bc6-bc27-7658527ce804`** (wakeclaude map `C:\Users\steph\.claude\wakeclaude\session-map\0881d827-...`). Brief: `C:\Users\steph\.claude\fleet-supervisor\briefs\2026-08-29-oo-4c-edge-semantics.md` (12 items; loop cap 3; landing = index row, STATUS, ROADMAP row 4c, 6-line summary).
- Model tiering: judgment = `claude-fable-5`, design + build = Opus, mechanical = Sonnet/Haiku. Pin at launch; never `/model`.
- Pacing: one worker at a time. Usage limits are not a constraint.
- Previous briefs and relay seeds: `C:\Users\steph\.claude\fleet-supervisor\briefs\` (all 2026-08-28/29).

## 4. Rulings and open decisions

- Register **R1–R47** in [`docs/decisions/`](../decisions/) — index at [`docs/README.md`](../README.md). **Next Q is Q56** (4C-RUN has Q49–Q55; the loop may add more). Never reuse an R number. Design/sequencing Qs: rule them yourself under the founder's make-assumptions directive. Product-level: flag with a default.
- **Pre-ruled for 4c's landing (not yet written; write as `2026-08-29-4c-rulings-R48-R5x.md`):** Q49 keep `endpoint_type_merged`'s name; Q51 chain cap stays a constant; Q52 no identity closure on `resolve_type` scoring in v0; Q53 `edge_payload` stays out of the kind vocabulary (say so in PACKAGE §5.2); Q54 `IDENTITY_FIELDS` declared, residual stated; Q55 guard extraction → the ACTIONS build row. **Q50 founder-visible** (may a `stores_proposals=False` backend hold a predicate at all, given R40) — default yes-with-warning, revisit on 2B evidence.
- **Founder-flagged, awaiting his word, defaults in force:** kill row `stop` option (default: continue); Q39 evidence-not-enforcement (default no enforcement); Q48 VISION §7 first deliverable (his doc); Q47 keep ACTIONS §10 (default keep); Q38 R24 tenancy survives actions (default keep, decided with 2B); beacon 21.1 approval (his). Recorded in [`2026-08-29-6-rulings-R40-R47.md`](../decisions/2026-08-29-6-rulings-R40-R47.md).

## 5. The kill row — read before judging the fifth trip

"A capability predicate gets merged as a duplicate" has tripped **in test** four times on main (`0e89037` unknowable extents · `fcb05b3` empty extents · `05b8e04` `retire(successor=)` · `8e641e6` `import_types` aliases, found by the checker itself) and a **fifth** in 4c's round 1 (paging, uncommitted). Full record with supervisor judgments and countersignature: [`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md) (bottom sections). Diagnosis in full form: *one guard written for one call, over a fact more than one call can change, reached through more than one field — and now read through a primitive that pages.* `namespace` and `cross_namespace_merge` have held every time. Standing recommendation: continue; the checker (`docs/tools/check_merge_guard.py`, Parts A callers / B states) is the mechanical gate and must gain the paged state in the round-1 commit. **If the founder says `stop`: stop launching and report.** Record the fifth trip in the same decisions file when the commit lands (the worker may draft it; countersign, do not rewrite).

## 6. Cycle-cron prompt (recreate verbatim, update the facts line as things land)

See the previous session's transcript for the full text (`C:\Users\steph\.claude\projects\C--Users-steph-projects-open-ontology\434d2782-2053-4d5e-b775-819012bbb1a6.jsonl`, last `CronCreate` call, job `59e36fac`). The operative sections: PARTITION · RELAY DISCIPLINE · STANDING RULINGS · PROJECT FACTS · WHEN 4c LANDS · ENVIRONMENT NOTES. **When 4c lands:** (a) close pipeline (fresh capture, one sentinel kill, verify gone); (b) STATUS.md 4c done, commit by path, push; (c) RELAY to the general supervisor (`fleet-supervisor-role`, seed file `briefs\2026-08-29-relay-4c-landed-for-beacon.md` + one-line pointer on an idle prompt) that **R38 is live with `via_successor` and slice 1 may build**, with module paths (`open_ontology/registry.py` `neighbors`/`amend_edge`, `edges.py`, `backends/*`, `contract/test_c17_*`) and numbers; (d) founder report with GitHub links; (e) next row by judgment: **write the Phase 3 decisions (paging R25 — the fifth trip is new evidence that paging is a correctness question, not a Phase 3 nicety —, tenancy R24/Q38, conditions R41) yourself** if 4B-RUN/4C-RUN/EDGES suffice, else brief Opus; the ACTIONS build row "6b" (58 planned `C19` ids, `check_spec_drift.py` pointed at ACTIONS.md) is the other candidate.

## 7. Environment gotchas that cost time today

- Mail DOWN (no `~/.claude/fleet-mail-creds.json`) → push-only.
- `wsl.exe -d Ubuntu-26.04 -- bash -lc '...'` single-quoted; **no `$(...)` inside** (bash EOF error, 17:56); `$vars`/`-F` → a `.sh` in the scratchpad via `MSYS_NO_PATHCONV=1`.
- Never batch a pane-state check with a send. Pointer via `send-keys -l`, verify, `Enter` separately.
- Pane ids are reused: several wakeclaude map files contain `%54`; the **newest** is the live one; always confirm `tmux list-panes -a` vs map content.
- `rm` takes a literal absolute path. Scripts with Windows paths → Write tool. Anchors in ROADMAP/STATUS move when a worker lands a row — grep first. Run `date` before stating times.
- Founder output: `C:\Users\steph\.claude\rules\adhd-output.md`; `[cycle NN]` line first; GitHub URLs `https://github.com/stephan-dyson/open-ontology/blob/main/<path>`; index row for every new doc; STATUS.md at every landing/launch. Standing constraint 0: **no employer data, ever.**
