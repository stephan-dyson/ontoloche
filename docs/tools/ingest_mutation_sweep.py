"""INGEST.md's mutation sweep -- row 7b's answer to finding 1 (E22) and E23.

Row 7a's round 2 obliged its fixes to ship checks that go RED for `C20-01`, `C20-04`,
`C20-05`, `C20-08`, `C20-18`, `C20-25`, `C20-58` and rule 2-12 (`C20-63`), and to state
the survivor count it measured. None was run (7A-RUN.md 6.11, E22), and *"nine of nine
red"* over nine self-selected mutations was a different claim from the survivor count
(E23). So this tool does both, mechanically:

* every mutation is a LITERAL ``(file, old, new)`` edit, and the sweep refuses to run a
  mutation whose ``old`` text does not occur EXACTLY ONCE -- a mutation that silently
  fails to apply is a survivor that was never tested, and it reads as a kill;
* each runs in a FRESH copy of the package under a new temporary folder (nothing is
  deleted, here or anywhere), against the contract test that claims the rule, on the
  sqlite leg;
* the unmutated copy is run first and must be GREEN, or every red below means nothing;
* a mutation is KILLED only when pytest reports a test FAILURE. A collection error or
  an import error is reported as ``broken``, never as a kill, because a mutation that
  stops the module importing proves nothing about the rule.

Run::

    py docs/tools/ingest_mutation_sweep.py            # all of them
    py docs/tools/ingest_mutation_sweep.py --required # finding 1's eight only

Exit 0 only when every REQUIRED mutation is killed and nothing is broken. Survivors
among the others are printed and counted, and the count is the deliverable: they are
recorded in ``docs/runs/7B-RUN.md``, not hidden.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = "ontoloche/registry.py"
ING = "ontoloche/ingest.py"
ADA = "ontoloche/adapter.py"
SQL = "ontoloche/backends/_sql.py"


@dataclass(frozen=True)
class Mutation:
    rule: str          # the INGEST.md rule it removes
    test: str          # the contract test that must go red, by id prefix
    file: str
    old: str
    new: str
    required: bool = False


MUTATIONS = (
    # ---- finding 1's eight (7A-RUN.md 6.9c) ------------------------------------------
    Mutation("1-1 the id is the host's", "c20_01", ING,
             "rec.type_name), rec.instance_id)", "rec.type_name), 'oo-' + rec.instance_id)",
             required=True),
    Mutation("2-1 two primitives, both reads", "c20_04", ADA,
             "    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage: ...\n",
             "    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage: ...\n"
             "    def put_instance(self, rec: InstanceRecord) -> InstanceRecord: ...\n",
             required=True),
    Mutation("2-2 None for absent, never manufactured", "c20_05", SQL,
             "        if not rows:\n            return None\n        if len(rows) > 1:",
             "        if not rows:\n            return InstanceRecord(namespace, kind, type_name, "
             "instance_id, instance_id, {}, None)\n        if len(rows) > 1:",
             required=True),
    Mutation("2-5 known=None or a dishonest 0 is uncountable", "c20_08", REG,
             "                    if uncounted or miscounted:",
             "                    if False:", required=True),
    Mutation("3-4 ambiguous carries no ref", "c20_18", REG,
             '"ambiguous", None, candidate_ref("ambiguous"), tied[0].score,',
             '"ambiguous", tied[0].ref, candidate_ref("ambiguous"), tied[0].score,',
             required=True),
    Mutation("3-4 ambiguous returns every tied candidate", "c20_18", REG,
             '"separates them", tied, True, "", scanned)',
             '"separates them", tied[:1], True, "", scanned)', required=True),
    Mutation("3-11 tier is echoed", "c20_25", REG,
             "warnings=tuple(dict.fromkeys(warnings)), tier=tier,",
             'warnings=tuple(dict.fromkeys(warnings)), tier="small",', required=True),
    Mutation("3-11 tier is required", "c20_25", REG,
             "if not isinstance(tier, str) or not tier:", "if False:", required=True),
    Mutation("6-17 no tenant parameter", "c20_58", ADA,
             "    host_filter: Mapping[str, Any] | None = None\n    limit: int | None = None\n"
             "    after: str | None = None\n",
             "    host_filter: Mapping[str, Any] | None = None\n    limit: int | None = None\n"
             "    after: str | None = None\n    tenant: str | None = None\n", required=True),
    Mutation("2-12 host_filter is a mapping", "c20_63", REG,
             "if host_filter is not None and not isinstance(host_filter, Mapping):",
             "if False:", required=True),
    # ---- finding 2 (E2) --------------------------------------------------------------
    Mutation("2-15 / E2 primitive 22 reads the whole closure", "finding_2", REG,
             'for member in closure["members"]:\n            try:\n'
             "                rec = self.adapter.get_instance(",
             "for member in (type_name,):\n            try:\n"
             "                rec = self.adapter.get_instance(", required=True),
    Mutation("2-15 a malformed predicate refuses, never passes", "c20_66", REG,
             "        problem = condition_problem(condition)\n        if problem is not None:\n"
             "            # A malformed predicate",
             "        problem = condition_problem(condition)\n        if False:\n"
             "            # A malformed predicate", required=True),
    # ---- round 1 of the loop (7B-RUN.md 2.1): each fix, shown red with it removed ----
    Mutation("3-18 / E10 a reworded why is not a change", "c20_79", REG,
             "_policy_terms(mine[0]), _policy_terms(theirs[0])",
             "mine[0], theirs[0]", required=True),
    Mutation("2-17 one copy per identity BEFORE the predicate", "c20_89", REG,
             "one_copy, copies_why = _one_copy_per_identity(records, effective)",
             "one_copy, copies_why = list(records), \"\"", required=True),
    Mutation("2-17 the kept copy is the effective name's", "c20_89", REG,
             "chosen = next((r for r in copies if r.type_name == effective), None)",
             "chosen = None", required=True),
    Mutation("2-11 a repeated cursor ends the read", "c20_14", REG,
             "if page.next_after in seen_cursors:", "if False:", required=True),
    Mutation("3-3 the margin is inclusive at its edge", "c20_17", REG,
             "<= policy.ambiguity_margin + _SCORE_EPS", "<= policy.ambiguity_margin",
             required=True),
    Mutation("5-9 the bands read the unrounded score", "c20_74", REG,
             "raw = [score for score, _ in pairs]",
             "raw = [round(score, 4) for score, _ in pairs]", required=True),
    Mutation("2-5 an over-count is uncountable", "c20_08", REG,
             "page.known is not None and page.known != len(page.records)",
             "page.known is not None and page.known < len(page.records)", required=True),
    Mutation("2-5 a finished uncountable read is counted here", "c20_08", REG,
             "uncounted = page.known is None and not page.complete",
             "uncounted = page.known is None", required=True),
    Mutation("2-15 an unreadable member refuses", "c20_66", REG,
             "            except NotSupported as exc:\n                # `I-1` at primitive 22's",
             "            except NotSupported as exc:\n                continue\n"
             "                # `I-1` at primitive 22's", required=True),
    Mutation("2-2 primitive 22 honours the type column", "c20_05", SQL,
             "        params: list[Any] = [instance_id]\n"
             "        if binding.type_column is not None:",
             "        params: list[Any] = [instance_id]\n"
             "        if False:", required=True),
    Mutation("7-4 not_an_instance carries no_tenancy_predicate", "c20_62", REG,
             '            if self._governed_facts(closure["entry"])[1] is None:\n'
             '                warnings.append("no_tenancy_predicate")\n'
             "            warnings.extend(self._instance_consumers_warning(namespace))\n",
             "", required=True),
    # ---- round 2 of the loop (7B-RUN.md 2.2) ------------------------------------------
    Mutation("2-2 primitive 22 matches the id the read side mints", "c20_05", SQL,
             """where = [f'CAST("{binding.id_column}" AS TEXT) = {ph}']""",
             """where = [f'"{binding.id_column}" = {ph}']""", required=True),
    Mutation("2-17 copies resolve under the effective name", "c20_89", REG,
             "chosen = dataclasses.replace(chosen, type_name=effective)", "pass",
             required=True),
    Mutation("2-17 disagreeing copies, none current, decide nothing", "c20_89", REG,
             "            if len(distinct) > 1:", "            if False:", required=True),
    Mutation("2-11 a cursor that never repeats still ends", "c20_14", REG,
             "if len(seen_cursors) >= self.INSTANCE_READ_PAGES_MAX:", "if False:",
             required=True),
    Mutation("3-18 / 5-10 the margin is one of the three", "c20_79", REG,
             '''for k in ("match_at", "propose_below",
                                                "ambiguity_margin"))''',
             '''for k in ("match_at", "propose_below"))''', required=True),
    Mutation("E10 in-values compare by equality", "c20_79", REG,
             "                value = frozenset(members)",
             "                value = tuple(sorted({repr(m) for m in members}))",
             required=True),
    Mutation("5-8 at match_at is existing", "c20_73", REG,
             "if tied and raw[0] >= policy.match_at:", "if tied and raw[0] > policy.match_at:",
             required=True),
    Mutation("5-8 no tolerance below match_at", "c20_73", REG,
             "if tied and raw[0] >= policy.match_at:",
             "if tied and raw[0] >= policy.match_at - 1e-9:", required=True),
    Mutation("3-3 a candidate at match_at ties", "c20_17", REG,
             "at_or_above = score >= policy.match_at", "at_or_above = score > policy.match_at",
             required=True),
    Mutation("5-9 at propose_below is ambiguous", "c20_74", REG,
             "if scored and raw[0] >= policy.propose_below:",
             "if scored and raw[0] > policy.propose_below:", required=True),
    Mutation("5-12 the floor is inclusive", "c20_90", REG,
             "score >= policy.propose_below)                   # rule 5-12 floor",
             "score > policy.propose_below)                   # rule 5-12 floor",
             required=True),
    Mutation("6-1 a nested term is checked", "c20_42", ING,
             "            problem = condition_problem(term, _path=f\"{_path}.terms[{i}]\")\n"
             "            if problem:\n                return problem",
             "            pass", required=True),
    Mutation("6-4 absent is not null", "c20_45", ING,
             '''    attribute = cond.attribute or ""
    if attribute not in attributes:''',
             '''    attribute = cond.attribute or ""
    if cond.op in ("is_null", "is_not_null"):
        missing = attributes.get(attribute) is None
        return ConditionResult(missing if cond.op == "is_null" else not missing, "")
    if attribute not in attributes:''', required=True),
    Mutation("2-15 / 3-15 primitive 22 refuses a dangling closure", "c20_66", REG,
             '''        if not closure["complete"]:
            return refuse("closure_incomplete", closure["why"])''',
             "        pass", required=True),
    Mutation("3-18 primitive 22 refuses changed governed facts", "c20_66", REG,
             '''        if changed:
            return refuse("governed_facts_changed", changed)''',
             "        pass", required=True),
    Mutation("2-13 the host filter reaches primitive 23", "c20_64", REG,
             "host_filter=dict(host_filter) if host_filter else None,",
             "host_filter=None,", required=True),
    Mutation("7-1 not_an_instance carries consumers_unregistered", "c20_62", REG,
             '''            warnings.extend(self._instance_consumers_warning(namespace))
            return answer(''',
             "            return answer(", required=True),
    # ---- round 3 of the loop (7B-RUN.md 2.3) ------------------------------------------
    Mutation("2-2 the id is minted by the database's cast", "c20_05", SQL,
             """cols = [f'CAST("{binding.id_column}" AS TEXT)',""",
             """cols = [f'"{binding.id_column}"',""", required=True),
    Mutation("3-21 an alias moves the effective name", "c20_89", REG,
             "                nxt = holders[0]\n", "                break\n", required=True),
    Mutation("3-21 a hand-written alias is a member", "c20_87", REG,
             "            if m.name not in names:",
             "            if m.name not in names and getattr(self.adapter.get_type("
             "namespace, m.name, kind=\"entity\"), \"successor\", None):",
             required=True),
    Mutation("6-6 a non-finite operand is refused", "c20_47", ING,
             "    if _non_finite(value):\n",
             "    if False:\n", required=True),
    Mutation("7-5 / 6-18 primitive 22 refuses a bare successor", "c20_84", REG,
             '''            rec = self.adapter.get_type(namespace, member, kind="entity")
            if rec is None:
                continue
            theirs = self._governed_facts(rec)''',
             '''            rec = self.adapter.get_type(namespace, member, kind="entity")
            if rec is None or self._governed_facts(rec) == (None, None):
                continue
            theirs = self._governed_facts(rec)''', required=True),
    Mutation("6-5 not_in over null is unknowable", "c20_46", ING,
             "    if got is None:", "    if got is None and cond.op != \"not_in\":",
             required=True),
    Mutation("6-15 a host filter never replaces the predicate", "c20_56", REG,
             '''        if condition is None:
            warnings.append("no_tenancy_predicate")
            survivors = list(one_copy)''',
             '''        if condition is None or host_filter:
            warnings.append("no_tenancy_predicate")
            survivors = list(one_copy)''', required=True),
    Mutation("6-3 an undecidable combinator says why", "c20_44", ING,
             "        if holds is None:", "        if False:", required=True),
    Mutation("3-9 nothing scored is None", "c20_23", REG,
             "scored[0].score if scored else None", "scored[0].score if scored else 0.0",
             required=True),
    Mutation("6-10 is_null takes no terms", "c20_51", ING,
             "    if terms not in (None, (), []):",
             "    if terms not in (None, (), []) and op not in (\"is_null\", \"is_not_null\"):",
             required=True),
    # ---- round 4 of the loop (7B-RUN.md 2.4) and the 31-id ruling -------------------
    Mutation('2-2 a row with no id is never a ref', 'c20_05_r4', SQL,
             '        if any(r[0] is None for r in page_rows):',
             '        if False:', required=True),
    Mutation('3-21 only an entity holds the alias', 'c20_89_r4', REG,
             'if o.kind == "entity" and o.name != word',
             'if o.name != word', required=True),
    Mutation('3-21 two holders decide nothing', 'c20_89_r4', REG,
             '                if len(holders) > 1:',
             '                if False:', required=True),
    Mutation('3-21 a same_word name is not an alias', 'c20_89_r4', REG,
             'and any(same_word(a, word) for a in (o.aliases or ()))',
             'and (same_word(o.name, word) or any(same_word(a, word) for a in (o.aliases or ())))', required=True),
    Mutation('6-6 a non-finite number anywhere', 'c20_47_r4', ING,
             '        return any(_non_finite(v) for v in value.values())',
             '        return False', required=True),
    Mutation('3-20 an unfinished backward walk is unknowable', 'c20_86_r4', REG,
             '        if not complete:\n            return stop(why or',
             '        if False:\n            return stop(why or', required=True),
    Mutation('2-17 copies differing only in label', 'c20_89_r4', REG,
             '            distinct = {(r.label, repr(sorted((r.attributes or {}).items(), key=repr)))',
             '            distinct = {(repr(sorted((r.attributes or {}).items(), key=repr)))', required=True),
    Mutation('I-1 primitive 23 raising is unknowable', 'c20_19_r4', REG,
             '                    except NotSupported as exc:\n                        complete, why_incomplete = False, (',
             '                    except NotSupported as exc:\n                        continue\n                        complete, why_incomplete = False, (', required=True),
    Mutation('E10 not_in order is no change', 'c20_79_r4', REG,
             'condition.get("op") in ("in", "not_in") and isinstance(',
             'condition.get("op") in ("in",) and isinstance(', required=True),
    Mutation('E10 combinator term order is no change', 'c20_79_r4', REG,
             '            value = frozenset(_condition_terms(t) for t in value)',
             '            value = tuple(_condition_terms(t) for t in value)', required=True),
    Mutation('5-2 a stored malformed policy is unknowable', 'c20_36_r4', REG,
             '            elif match_policy_problem(policy_raw) is not None:',
             '            elif False:', required=True),
    Mutation('6-3 ne', 'c20_43_r4', ING,
             'ConditionResult(got != cond.value, "")',
             'ConditionResult(True, "")', required=True),
    Mutation('6-3 not_in', 'c20_43_r4', ING,
             'ConditionResult(got not in tuple(cond.value), "")',
             'ConditionResult(True, "")', required=True),
    Mutation('6-3 lt', 'c20_43_r4', ING,
             'bool(got < cond.value)',
             'bool(got <= cond.value)', required=True),
    Mutation('6-3 lte', 'c20_43_r4', ING,
             'bool(got <= cond.value)',
             'bool(got < cond.value)', required=True),
    Mutation('6-3 gt', 'c20_43_r4', ING,
             'bool(got > cond.value)',
             'bool(got >= cond.value)', required=True),
    Mutation('6-3 gte', 'c20_43_r4', ING,
             'bool(got >= cond.value)',
             'bool(got > cond.value)', required=True),
    Mutation('C20-02 resolve_type takes no host_filter', 'c20_02', REG,
             '        min_confidence: float = 0.0,\n        search_namespaces: Sequence[str] | None = None,',
             '        min_confidence: float = 0.0,\n        host_filter: Any = None,\n        search_namespaces: Sequence[str] | None = None,', required=True),
    Mutation('2-4 every page says how many it holds', 'c20_06', SQL,
             '            known=len(records),\n            complete=not more,\n            why_incomplete=None,',
             '            known=None,\n            complete=not more,\n            why_incomplete=None,', required=True),
    Mutation('2-5 the adapter scores nothing', 'c20_09', SQL,
             '"""INGEST.md 2, primitive 22. ``None`` for absent',
             '"""INGEST.md 2, primitive 22 (no norm() here). ``None`` for absent', required=True),
    Mutation('2-8 a label never omits a record', 'c20_11', SQL,
             '        records = tuple(self._instance_record(binding, r) for r in page_rows)\n',
             '        records = tuple(self._instance_record(binding, r) for r in page_rows if q.label is None or (r[1] or "")[:1] == q.label[:1])\n', required=True),
    Mutation('2-9 resolves_instances defaults False', 'c20_12', ADA,
             'resolves_instances: bool = False',
             'resolves_instances: bool = True', required=True),
    Mutation('2-7 a declared filter key is applied', 'c20_13', SQL,
             '            where.append(f\'"{key}" = {ph}\')\n            params.append(q.host_filter[key])',
             '            pass', required=True),
    Mutation('3-1 five outcomes', 'c20_15', ING,
             'INSTANCE_OUTCOMES = ("existing", "ambiguous", "proposal", "not_an_instance", "unknowable")',
             'INSTANCE_OUTCOMES = ("existing", "ambiguous", "proposal", "not_an_instance", "unknowable", "rejected")', required=True),
    Mutation("3-1 resolve_instance's signature", 'c20_16', REG,
             '        host_filter: Mapping[str, Any] | None = None,\n    ) -> InstanceResolution | Refusal:',
             '        host_filter: Mapping[str, Any] | None = None,\n        explain: bool = False,\n    ) -> InstanceResolution | Refusal:', required=True),
    Mutation('I-1 an incomplete answer decides nothing', 'c20_20', REG,
             '            return answer("unknowable", None, None, None, reason, scored[:5], False,',
             '            return answer("proposal", None, None, None, reason, scored[:5], False,', required=True),
    Mutation('I-2 proposal needs every page', 'c20_21', REG,
             '        if not complete:                                             # `I-1`, `I-2`',
             '        if False:', required=True),
    Mutation('3-11 the call takes no threshold', 'c20_24', REG,
             '        host_filter: Mapping[str, Any] | None = None,\n    ) -> InstanceResolution | Refusal:',
             '        host_filter: Mapping[str, Any] | None = None,\n        min_confidence: float = 0.0,\n    ) -> InstanceResolution | Refusal:', required=True),
    Mutation('6-16 undecidable is unknowable', 'c20_26', REG,
             '        if undecided:                                                # rule 6-16',
             '        if False:', required=True),
    Mutation('5-1 the policy is never a parameter', 'c20_35', REG,
             '        host_filter: Mapping[str, Any] | None = None,\n    ) -> InstanceResolution | Refusal:',
             '        host_filter: Mapping[str, Any] | None = None,\n        policy: Any = None,\n    ) -> InstanceResolution | Refusal:', required=True),
    Mutation('5-3 the policy why is required', 'c20_37', ING,
             '    if not isinstance(why, str) or not why.strip():\n        return f"{MATCH_POLICY_KEY}.why',
             '    if False:\n        return f"{MATCH_POLICY_KEY}.why', required=True),
    Mutation('5-5 the gate mints no vocabulary', 'c20_38', REG,
             '                "not_an_instance", None, None, None,\n                f"{candidate!r} names a class',
             '                "rejected", None, None, None,\n                f"{candidate!r} names a class', required=True),
    Mutation('5-6 unscored names the MatchPolicy', 'c20_39', REG,
             'f"{governed_by} declares no MatchPolicy, so nothing',
             'f"{governed_by} declares no policy, so nothing', required=True),
    Mutation('5-7 callers may not pass a policy', 'c20_40', REG,
             '        host_filter: Mapping[str, Any] | None = None,\n    ) -> InstanceResolution | Refusal:',
             '        host_filter: Mapping[str, Any] | None = None,\n        match_policy: Any = None,\n    ) -> InstanceResolution | Refusal:', required=True),
    Mutation('5-11 the policy in force is recorded', 'c20_41', REG,
             '        governed_by = f"{namespace}:{effective}"\n        warnings.extend(',
             '        governed_by = f"{namespace}/{effective}"\n        warnings.extend(', required=True),
    Mutation('6-2 a condition reads one record', 'c20_43', ING,
             'def evaluate(cond: Condition, attributes: Mapping[str, Any]) -> ConditionResult:',
             'def evaluate(cond: Condition, attributes: Mapping[str, Any], strict: bool = False) -> ConditionResult:', required=True),
    Mutation('6-7 in / not_in take a sequence', 'c20_48', ING,
             '        if not isinstance(value, (list, tuple)):\n            return f"{_path}: {op} takes a sequence',
             '        if False:\n            return f"{_path}: {op} takes a sequence', required=True),
    Mutation('6-8 a combinator needs terms', 'c20_49', ING,
             '        if not isinstance(terms, (list, tuple)) or not terms:',
             '        if not isinstance(terms, (list, tuple)):', required=True),
    Mutation('6-9 a combinator carries no attribute', 'c20_50', ING,
             '        if attribute is not None or value is not None:\n            return f"{_path}: {op} takes terms',
             '        if False:\n            return f"{_path}: {op} takes terms', required=True),
    Mutation('6-11 the condition why is required', 'c20_52', ING,
             '    if not isinstance(why, str) or not why.strip():\n        return f"{_path}.why is required',
             '    if not isinstance(why, str):\n        return f"{_path}.why is required', required=True),
    Mutation('6-12 no not', 'c20_54', ING,
             'CONDITION_COMBINATORS = ("all_of", "any_of")',
             'CONDITION_COMBINATORS = ("all_of", "any_of", "not")', required=True),
    Mutation('6-13 the condition is never a parameter', 'c20_55', REG,
             '        host_filter: Mapping[str, Any] | None = None,\n    ) -> InstanceResolution | Refusal:',
             '        host_filter: Mapping[str, Any] | None = None,\n        predicate: Any = None,\n    ) -> InstanceResolution | Refusal:', required=True),
    Mutation('7-2 no consumer registration is added', 'c20_60', REG,
             '    def get_instance_checked(\n',
             '    def register_instance_consumer(self, namespace: str) -> None:\n        return None\n\n    def get_instance_checked(\n', required=True),
    Mutation('7-3 no entity-only call is added', 'c20_61', REG,
             '    def get_instance_checked(\n',
             '    def resolve_entity(self, candidate: str) -> None:\n        return None\n\n    def get_instance_checked(\n', required=True),
    Mutation('3-16 the hop cap', 'c20_77', REG,
             '            if len(hops) >= INSTANCE_CHAIN_CAP:',
             '            if False:', required=True),
    Mutation('5-10 no inherited MatchPolicy', 'c20_82', REG,
             '                    ("MatchPolicy", _policy_terms(mine[0]), _policy_terms(theirs[0])),',
             '                    ("MatchPolicy", 0, 0),', required=True),
    Mutation('6-18 no inherited predicate', 'c20_83', REG,
             '                    ("tenancy predicate", _condition_terms(mine[1]),\n                     _condition_terms(theirs[1])),',
             '                    ("tenancy predicate", 0, 0),', required=True),
    Mutation('3-20 the closure walks backward', 'c20_86', REG,
             '            if m.name not in names:',
             '            if m.name not in names and False:', required=True),
    Mutation('Q108 default: a tombstone is served', 'c20_80_r4', REG,
             '                if not holders or self.adapter.get_type(\n',
             '                if not holders:\n                    return stop("retired with no successor")\n                if self.adapter.get_type(\n', required=True),
    # ---- the rest of the read side ---------------------------------------------------
    Mutation("1-3 the capability refuses first", "c20_03", REG,
             "        if self.caps.resolves_instances:\n            return None",
             "        if True:\n            return None"),
    Mutation("2-4 a capped read is truncated", "c20_07", SQL,
             "capped = bool(self._fetchall(probe, params))", "capped = False"),
    Mutation("2-7 an undeclared key is reported", "c20_10", SQL,
             "undeclared.append(str(key))", "pass"),
    Mutation("2-11 the read exhausts the cursor", "c20_14", REG,
             "                    after = page.next_after", "                    break"),
    Mutation("2-13 a narrowed proposal says so", "c20_64", REG,
             "        if host_filter:\n            warnings.append(",
             "        if False:\n            warnings.append("),
    Mutation("2-14 the flat-form guard", "c20_65", REG,
             "            problem = flat_form_problem(record_ref(rec).type)\n            if problem:\n"
             "                return Refusal(",
             "            problem = None\n            if problem:\n                return Refusal("),
    Mutation("2-16 duplicate ids are uncountable", "c20_75", REG,
             "        if dup_why:", "        if False:"),
    Mutation("2-17 one row under two names is one", "c20_89", REG,
             "groups.setdefault((rec.namespace, rec.kind, rec.instance_id), []).append(rec)",
             "groups.setdefault((rec.namespace, rec.kind, rec.type_name, rec.instance_id),"
             " []).append(rec)"),
    Mutation("3-3 the margin ties", "c20_17", REG,
             "near_top = (top - score) <= policy.ambiguity_margin + _SCORE_EPS and (",
             "near_top = False and ("),
    Mutation("3-5 an unfinished read is unknowable", "c20_19", REG,
             "        if not complete:                                             # `I-1`",
             "        if False:                                             # `I-1`"),
    Mutation("3-8 not_an_instance", "c20_22", ING,
             "    return not key or key in _CLASS_WORDS", "    return False"),
    Mutation("3-13 zero rows is unknowable", "c20_67", REG,
             "        if scanned == 0:", "        if False:"),
    Mutation("3-14 every hop is reported", "c20_68", REG,
             'warnings.extend(f"instance_type_succeeded:{h}" for h in closure["hops"])\n\n'
             "        def answer(",
             "warnings.extend(())\n\n        def answer("),
    Mutation("3-15 a dangling successor stops", "c20_76", REG,
             "            if nxt_entry is None:", "            if False:"),
    Mutation("3-17 a cycle stops", "c20_78", REG,
             "            if nxt in seen:", "            if False:"),
    Mutation("3-18 governed facts compared across the closure", "c20_79", REG,
             "            if changed:\n                return (",
             "            if False:\n                return ("),
    Mutation("3-19 the extent is the whole closure", "c20_80", REG,
             'for read_type in closure["members"]:', "for read_type in (effective,):"),
    Mutation("3-22 a separator stops the walk", "c20_88", REG,
             'if ":" in nxt or "#" in nxt:', "if False:"),
    Mutation("5-2 propose_below <= match_at", "c20_36", ING,
             'if float(declared["propose_below"]) > float(declared["match_at"]):',
             "if False:"),
    Mutation("5-9 the band is ambiguous", "c20_74", REG,
             "if scored and raw[0] >= policy.propose_below:",
             "if False:"),
    Mutation("5-11 governed_by is the effective entry", "c20_85", REG,
             'governed_by = f"{namespace}:{effective}"',
             'governed_by = f"{namespace}:{type_name}"'),
    Mutation("5-12 the tied set has a floor", "c20_90", REG,
             "score >= policy.propose_below)                   # rule 5-12 floor",
             "True)                   # rule 5-12 floor"),
    Mutation("6-12 all_of is Kleene", "c20_53", ING,
             'holds = False if False in vals else (None if None in vals else True)',
             'holds = False if False in vals else True'),
    Mutation("6-16 an undecided candidate is never dropped", "c20_57", REG,
             "                elif verdict.holds is None:\n                    undecided.append",
             "                elif False:\n                    undecided.append"),
    Mutation("7-1 an unregistered blast radius warns", "c20_59", REG,
             'return [] if found else ["consumers_unregistered"]', "return []"),
    Mutation("7-4 no predicate says so", "c20_62", REG,
             '        if condition is None:\n            warnings.append("no_tenancy_predicate")\n'
             "            survivors = list(one_copy)",
             "        if condition is None:\n            survivors = list(one_copy)"),
)


def _copy() -> Path:
    where = Path(tempfile.mkdtemp(prefix="oo_ingest_mut_"))
    shutil.copytree(ROOT / "ontoloche", where / "ontoloche",
                    ignore=shutil.ignore_patterns("__pycache__", "aio"))
    for name in ("pyproject.toml",):
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, where / name)
    return where


def _run(where: Path, test: str) -> tuple[str, str]:
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "ontoloche/contract/test_c20_ingest.py", "-q",
         "-p", "no:cacheprovider", "-k", f"({test}) and not minimal and not postgres"],
        cwd=where, capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(where),
             "OO_POSTGRES_DSN": ""},
    )
    out = done.stdout + done.stderr
    # pytest's last line is the verdict: "1 failed, 2 passed in 0.3s", "1 error in ...".
    lines = [line for line in out.strip().splitlines() if " in " in line and "passed"
             in line or "failed" in line or "error" in line or "deselected" in line]
    tail = lines[-1] if lines else ""
    if done.returncode == 0 and "passed" in tail:
        return "survived", out
    if "error" in tail or done.returncode not in (0, 1):
        return "broken", out
    if "failed" in tail:
        return "killed", out
    return "broken", out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--required", action="store_true")
    args = parser.parse_args()
    chosen = [m for m in MUTATIONS if m.required or not args.required]

    base = _copy()
    verdict, out = _run(base, "c20 or finding_2")
    if verdict != "survived":
        print("the UNMUTATED copy is not green, so no red below would mean anything:\n")
        print(out[-3000:])
        return 2
    print(f"baseline green in {base}")

    results = []
    for m in chosen:
        source = (ROOT / m.file).read_text(encoding="utf-8")
        count = source.count(m.old)
        if count != 1:
            results.append((m, f"not applied: old text occurs {count} times"))
            continue
        where = _copy()
        target = where / m.file
        target.write_text(source.replace(m.old, m.new), encoding="utf-8")
        verdict, out = _run(where, m.test)
        results.append((m, verdict))
        if verdict == "broken":
            print(out[-1500:])

    width = max(len(m.rule) for m, _ in results)
    for m, verdict in results:
        flag = "REQUIRED" if m.required else "        "
        print(f"  {flag}  {m.rule:<{width}}  {m.test:<10}  {verdict}")
    survivors = [m for m, v in results if v == "survived"]
    bad = [(m, v) for m, v in results if v not in ("killed", "survived")]
    required_alive = [m for m in survivors if m.required]
    print(f"\n{len(results)} mutations: "
          f"{sum(v == 'killed' for _, v in results)} killed, {len(survivors)} survived, "
          f"{len(bad)} not applied or broken. Required survivors: {len(required_alive)}.")
    return 1 if (required_alive or bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
