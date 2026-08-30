# Run record — the ontoloche rename (2026-08-30)

**What:** the project is renamed **ontoloche** ("on-tuh-LOH-chee" — the *-che* after Apache), by founder ruling 2026-08-30 13:5x, verbatim *"44 name ontoloche"*. Repo `open-ontology` → `ontoloche`; distribution `open-ontology` → `ontoloche`; import `open_ontology` → `ontoloche`. Availability at ruling time: PyPI `ontoloche` 404 (free); GitHub repo-name search, 0 repositories.

**How:** one `git mv` (history preserved) plus a mechanical text rewrite of 75 files, applied by a script validated in a throwaway worktree before it touched this tree. The async tree was **regenerated** by `tools/unasync.py`, not hand-edited — the regeneration wrote 0 of 25 files, i.e. the mechanical rename matched the generator's own output byte for byte, and `tools/unasync.py --check` reports all 25 current. Historical run, finding and decision records were **not rewritten**: each that mentioned the old import name carries a one-line note under its title instead (7 files), because a record that quotes a command is a record, not documentation.

**Conformance, on this tree after the rename (2026-08-30 15:49 local, three legs — sqlite, sqlite_minimal, Postgres via `oo-pg`):**

| suite | result |
|---|---|
| `py -m pytest ontoloche/contract -q -p no:randomly` | **747 passed, 238 skipped** (21:40) |
| `py -m pytest ontoloche/aio/contract -q -p no:randomly` | **785 passed, 238 skipped** (6:50) |

Both above row 6b round 2's floor. The suite state is mid-row-6b (round 2 landed, round 3 pending); the rename deliberately interleaved at a clean-tree point between rounds, and row 6b resumes on the new paths.

**What a reader of an old link should know:** GitHub redirects `github.com/stephan-dyson/open-ontology` to `github.com/stephan-dyson/ontoloche` after the repo rename; in-repo GitHub URLs in historical records were left as written and resolve through that redirect. The commit that fills the rename SHA into the historical notes is the immediate child of the rename commit.
