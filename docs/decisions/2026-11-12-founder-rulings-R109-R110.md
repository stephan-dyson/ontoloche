# R109–R110 — the founder's answers to two questions row 8a raised before code

**Founder rulings, 2026-11-12.** Given in session, in answer to two questions row 8a put to him before §0 of [`runs/8A-RUN.md`](../runs/8A-RUN.md) was written. Both decide what the registry refuses, so the kickoff sent them to him rather than into code as a default.

**Numbering is provisional.** Row 8b runs in parallel on `main` and may mint its own rulings. If it takes R109 or R110 first, the supervisor renumbers these at merge. The content does not change.

---

## R109 — a Foundry type with no description: `hold + override map`

**The question.** The row 8a brief (§1 item 3.4) says an empty description *"imports as `proposed` with a warning, never as `active` with a placeholder definition."* In this registry `proposed` is a **proposal record**, not a status a stored type can have, and a proposal also needs a non-empty definition. **[Observed]** `propose_type` raises `ValueError("definition is required and must be non-empty")` (`ontoloche/registry.py:2596`), and the sqlite schema carries `CHECK (length(definition) > 0)` on `oo_type` (`ontoloche/backends/migrations/sqlite/0001_init.sql:21`). So the brief's literal instruction has no landing place. The options put to him:

1. **Hold + override map.** Nothing is written. The row comes back shaped as it would have looked, marked `proposed`, carrying `import_refused:definition_missing`. The caller can pass `definitions={apiName: text}` and import again. No placeholder text lands anywhere.
2. **Real proposal with a placeholder.** File a proposal carrying placeholder text for a human to review, falling back to holding on a backend with no proposal table.
3. **Discuss.**

**His answer: option 1, `hold + override map`.**

**What this means for the code.** `import_types` writes no row whose definition is missing or blank, and never writes `"imported from <system>"` as a definition again. `import_foundry` takes `definitions=` keyed by Foundry `apiName`.

## R110 — two Foundry apiNames that convert to one name: `hold both + names map`

**The question.** The brief's §5 question 1. Converting a Foundry `apiName` to `^[a-z][a-z0-9_]{0,63}$` can map two different apiNames onto one name (`NursingHome` and `nursing_home` both become `nursing_home`). **[Observed]** `import_types` overwrites a standing row of the same kind and name (`registry.py:5628` reads `standing`, and `put_type` replaces it), so without a rule the second row silently replaces the first in one call. The options put to him:

1. **Hold both + names map.** Neither row is written. Both come back with `import_refused:name_collision_after_conversion` and the colliding apiNames. The caller passes `names={apiName: name}` to resolve it and imports again.
2. **Suffix the later one** (`_2`, `_3`) with a warning.
3. **Discuss.**

**His answer: option 1, `hold both + names map`.**

**What this means for the code.** The collision check runs over the converted names of one kind inside one import, before anything is handed to `import_types`. A caller-supplied name goes through the same check, so the map cannot create a collision of its own.

---

**Kill row and governance register:** unchanged. A ruling is not a trip.
