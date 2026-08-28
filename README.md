# open-ontology *(working name)*

An open ontology and pipeline layer — typed entities, typed relationships, and
governed actions that AI agents can safely call.

**Status: pre-code, specs in progress.** Phase 0 discovery is closed and Phase 1's interface contract is written. No implementation yet.

## Start here

- [`ROADMAP.md`](ROADMAP.md) — the sequenced plan. Priority: top, behind CASA/compliance only. Phase 0 is discovery with no code and no spec, because the interface shape depends on WHICH pollution mechanism it must prevent.
- [`VISION.md`](VISION.md) — the thesis, what was observed, what is assumed, and
  the open questions. Claims are tagged **[Observed] / [Inferred] / [Assumed]**;
  §9 lists what is explicitly *not* validated.
- [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md) — **the concrete test of the whole idea.** A
  non-technical analyst goes from a spreadsheet to a sent action in five steps, without a
  developer at any point. Read this to argue with the product; read the two above to argue
  with the strategy.
- [`docs/INTERFACE.md`](docs/INTERFACE.md) — **the Phase 1 deliverable: the type-registry
  contract, `v0` and unstable.** Twelve calls built around a proposal→approval loop, with
  `consumers(type)` — *"if I add this, what will silently ignore it?"* — first-class. Includes
  the Tenshen and CMS design tests, and the conflicts both produced.
- [`docs/0.3-prior-art.md`](docs/0.3-prior-art.md) — what the two visible prior interfaces
  actually look like, read on 2026-08-28. Verdict: no interface worth matching call-for-call;
  Foundry's status vocabulary worth matching field-for-field.
- [`docs/FINDINGS-0.1-tenshen-archaeology.md`](docs/FINDINGS-0.1-tenshen-archaeology.md) —
  the first piece of real evidence. Seven entity vocabularies in one codebase, traced to
  their origin commits. It changed the interface: **most "duplicate" types are not
  duplicates**, and the failure that actually shipped a bug was a type being *silently
  ignored*, not a type being duplicated.

## The one-paragraph version

Palantir Foundry already ships a governed ontology layer. In the field, it rots —
too many entities, too many editors, no curation discipline — and real work routes
around it into spreadsheets. Every open-source alternative currently visible is
cloning Foundry's *structure*, which is the part that already exists and already
failed. **The product is not an ontology layer. It is an ontology layer that
resists rot**, where the AI proposes and curates the vocabulary and humans approve.

## Why this repo is private

It is a first draft built on one day of first-hand observation. It is not ready to
be read as a claim about the world, and the open questions in §11 need answering
before any of it hardens.
