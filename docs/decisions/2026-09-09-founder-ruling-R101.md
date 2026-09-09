# R101 — `drop it` was ruled, and there was nothing under that name to drop

**Founder ruling, 2026-09-09. His word: `drop it`.**

The item, as it stood on the decision page:

> Row 6d's actions lens created `r3lens_de7fdace` on the `oo-pg` container and it was left in place under the project's no-deletion rule. Deleting anything is your call. Nothing is blocked by it.
>
> **Ask:** `drop it` or `leave it`. On `drop it` I confirm the namespace is the row's and nothing else's, and report before removing.

**The ruling is `drop it`. The confirmation step found no such namespace, so nothing was deleted.** This document records the finding rather than reporting a deletion that did not happen.

---

## 1. What was checked, before anything was removed

`oo-pg`, both databases, every schema:

```
$ docker exec oo-pg psql -U postgres -tAc \
    "select datname from pg_database where datistemplate=false;"
postgres
open_ontology

$ docker exec oo-pg psql -U postgres -d <each> -tAc "select nspname from pg_namespace;" \
    | grep -i "r3lens\|de7fdace"
(no match in either database)

$ docker exec oo-pg psql -U postgres -d open_ontology -tAc \
    "select split_part(nspname,'_',1), count(*) from pg_namespace
     where nspname not like 'pg_%' and nspname <> 'information_schema' group by 1;"
oo|625
public|1
```

**`r3lens_de7fdace` does not exist**, and this is not a story about lost state: the container was created `2026-08-28T23:39:27Z`, has **`RestartCount=0`**, and holds a **persistent volume** at `/var/lib/postgresql/data`. It has been running with the same store since before row 6d ran. Anything row 6d actually left behind would still be there — the 625 `oo_*` schemas prove the store persists.

## 2. The name has no source in the row's own record

`grep -rn "r3lens\|de7fdace" docs/runs/6D-RUN.md` returns **nothing**. The only occurrences anywhere in the repository are in supervisor documents that carried the item forward: [R96](2026-09-07-founder-ruling-R96.md), [R98](2026-09-07-founder-ruling-R98.md), and the decision page itself.

**So the item asked the founder to rule on a specific named object that the row that supposedly created it never recorded.** The name entered a supervisor summary, was carried across four days and three decision pages, and was never checked against the container until the ruling authorised the check.

The decision page did disclose that it was unverified — *"I can read the namespace list on your word rather than guessing at it"* — which is the only reason this is a hygiene failure rather than a false statement of fact. It is still a hygiene failure. An item that survives four days on a page whose stated purpose is to be hygienic and evidence-linked should have been verified when it was written, not when it was ruled.

## 3. The real residue is different, larger, and NOT what was authorised

`oo-pg` holds **625 `oo_*` schemas** — up from 476 recorded on 2026-09-05 and 193 in row 6c. These are the genuine leftovers, they accumulate across every three-leg suite run, and they slow the postgres leg without failing it.

**They are not row 6d's, and they were not what `drop it` authorised.** The founder ruled on one named namespace attributed to one row. Reading that word as permission to drop 625 schemas belonging to every run this project has made would be a destructive action he did not sanction, on the strength of a word he gave about something else. Under the standing rule that a deletion names a literal target, and under the project's own no-deletion default, **nothing is dropped.**

The 625 are re-raised as their own item, with a default in force, so the decision is his on the facts as they actually are.

## 4. Consequent

- Item 4 is **CLOSED**: ruled `drop it`, nothing existed under that name, nothing deleted.
- A new item goes to the decision page for the 625 `oo_*` schemas, carrying the counts, what they cost, and a default of **leave**.
- Standing correction for this supervisor, recorded in the handoff: **an item does not go on the founder's page naming a specific object until that object has been observed.** A disclosure that a fact is unverified is not a substitute for verifying it, when verifying it is one command.

Recorded by the ontoloche supervisor. Same-day rulings: [R99](2026-09-09-founder-ruling-R99.md), [R100](2026-09-09-founder-ruling-R100.md).
