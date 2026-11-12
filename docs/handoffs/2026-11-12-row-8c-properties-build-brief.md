# Row 8c brief — the properties build row

**Drafted 2026-11-12 by the supervisor, after row 8b landed (`586ba1a..22933f8`, [`runs/8B-RUN.md`](../runs/8B-RUN.md)). The row is not open.** It builds what [`INTERFACE.md` §2.10](../specs/INTERFACE.md) specifies under ruling [R108](../decisions/2026-09-22-founder-ruling-R108.md), and it replaces row 8a's interim `carry` (R105) with the §2.10 mapping.

---

## 0. What has to happen before it opens

1. **The founder answers item 23, `Q107`** ([`DECISIONS-OPEN.md`](../DECISIONS-OPEN.md)). Row 8b stopped at its five-round cap with 5 MAJOR and 9 MINOR findings open in §2.10, three MAJORs in rule 2.10-11's reader. The answer decides this row's shape:
   - `fix pass`: a short spec row lands the 14 fixes first, and this row builds from the reviewed text.
   - `fold into the build row`: this row's first task is the 14 findings in `8B-RUN.md` §2.5, reviewed together with the code.
   - `leave`: this row builds §2.10 as landed and records every gap it meets as a contortion, deciding none of them.
2. **Row 8a has landed and merged into `main`**, because this row changes the importer that 8a writes.
3. **Items 19 to 22 (`Q103` to `Q106`) do NOT have to be answered first.** Rules 2.10-17 to 2.10-21 are the refusals routed to the founder, so this row builds them as **today's behaviour, measured and pinned**, and changes none of them. A ruling that arrives mid-row is built in the same row only if the founder says so.

## 1. What the row delivers

1. **The two views** §2.10 prints (the entity declaration view and the `kind="property"` view, with `why_absent`), built against `Capabilities.stores_attribute` on every backend.
2. **Rules 2.10-1 to 2.10-16, 2.10-22 and 2.10-23 enforced as specified**, each pinned by the `C21` contract id `check_spec_drift.py` already lists as planned. The checker must report those ids as built, not planned, when the row ends.
3. **`resolve_type(..., kind="property")`** per rule 2.10-12. Contortion 10 stays *narrowed*, not closed, and rule 2.10-14's two resolver residuals stay stated.
4. **The importer's property mapping.** `import_foundry` maps Foundry properties and shared property types into §2.10 declarations, using the informative table in §2.10 and rule 2.10-6 for `opaque` types. R105's `carry` is removed for everything that now has a home. Anything with no home is reported in the dry run, never dropped.
5. **Async mirror regenerated** with `tools/unasync.py`, never hand-written.

## 2. Out of scope

- Values. Rule 2.10-13 and R78: no row is ever checked against a declaration.
- Any behaviour change at rules 2.10-17 to 2.10-21 without a founder ruling.
- The unrouted retire-then-alias defect carried in item 23 (probe line D14). It predates row 8b, and it needs its own row or a founder ruling on where it goes.

## 3. Design tests (standing constraint 7), expected outcomes in §0 before any run

- **UC2 CMS:** the 23 columns land as row 8b's §1.14 scored them, through real calls rather than a probe.
- **UC3 NYC:** `latitude` and `longitude` resolve with `kind="property"`, `status` stays three things, and no cross-namespace merge succeeds.
- **UC1 Tenshen:** the row confirms or refutes 8b's finding that option B costs Tenshen nothing, now against code.
- **Foundry:** every property in row 8a's fixtures imports to a declaration, or is in the dry-run report with a reason.

## 4. How the row runs (the project's standing process)

- §0 is pre-registered and committed first, before any code or test.
- Tests red first, in the contract suite, on all three backends. The postgres leg needs `oo-pg` on port 55432.
- All five gates exit 0: `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, `check_skip_census`.
- The adversarial loop runs to row 6j's stopping rule (`6J-RUN.md` §5 item 10), with the cap pre-registered in §0.
- The row pre-registers which kill-row doors the new views and the property mapping open. Row 8b's §0.4 lists the doors `kind="property"` opens.
- Anything that decides what the registry refuses goes to the founder, never into code as a default.
