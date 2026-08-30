"""Do INTERFACE.md and PACKAGE.md still describe the code? -- run them and find out.

Six consecutive adversarial review rounds on `docs/specs/INTERFACE.md` each found at
least one defect of **the same family**: a printed data shape or signature that had
drifted from the reference implementation.

    round 1  `Resolution` and `predicates()` were missing Rule K's fields
    round 2  `register_consumer` was declared `-> Consumer`; it returns `| Refusal`
    round 3  `propose_type`'s third outcome was undocumented
    round 4  `PredicateEntry.extent_size` was typed `int`; the code says `int | None`
    round 5  `MergeResult` had no printed shape at all
    round 6  `merge_types` was missing `into_namespace`; `TypeEntry` was missing two fields

Every one was found by a human-shaped reader comparing two files by eye, and every one
had survived earlier readers doing the same thing. That is a job for a script.

**What this checks, and what it deliberately does not.** It compares the *names* of
fields in the spec's fenced ``Shape:`` blocks against the dataclass in ``types.py``, and
the *parameter names* of the spec's ``def`` blocks against the method on ``Registry``.
It does **not** compare types or defaults: the spec writes ``list[str]`` where the code
writes ``tuple[str, ...]`` on purpose, because the spec describes a contract and the
implementation chose immutability (deviation D-12's neighbourhood). Names are where the
drift that mattered actually happened -- a missing field is invisible to a reader, a
different container is not.

A shape the spec prints that the code does not have, or a field the code returns that
the spec never mentions, is a finding either way: the first misleads an implementer, the
second is a surface nobody agreed to.

**PACKAGE.md is checked the same way, added by row 3d (beacon finding U4).** That
finding was one more of the same family: 3.3's printed ``TypeRecord`` had lost
``retire_reason``, ``retired_by``, ``retired_at`` and ``successor`` -- four fields the
landed dataclass has and the document a third-party adapter author reads does not. The
fifteen INTERFACE shapes were mechanically checked and the ten PACKAGE ones were not,
so the drift moved into the half of the specification nobody was checking. The
difference from INTERFACE.md is only in shape: PACKAGE prints real ``@dataclass``
blocks rather than ``Name:`` sketches, so the parser reads a ``class X:`` header. Names
only, again -- the spec writes what a field *is called*, and a container type that
differs on purpose is not drift.

Run: ``python docs/tools/check_spec_drift.py`` -- exit 0 clean, 1 with a report.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "specs" / "INTERFACE.md"
PACKAGE = ROOT / "docs" / "specs" / "PACKAGE.md"
EDGES = ROOT / "docs" / "specs" / "EDGES.md"
ACTIONS = ROOT / "docs" / "specs" / "ACTIONS.md"
sys.path.insert(0, str(ROOT))

from open_ontology import actions as actions_module  # noqa: E402
from open_ontology import adapter as adapter_module  # noqa: E402
from open_ontology import edges as edges_module  # noqa: E402
from open_ontology import attributes as attributes_module  # noqa: E402
from open_ontology.contract import harness as harness_module  # noqa: E402
from open_ontology import registry as registry_module  # noqa: E402
from open_ontology import types as types_module  # noqa: E402

#: Shapes the spec prints as ``Name:`` inside a fenced block, and their dataclass.
#: A shape is listed here only when the spec means it to be the whole record.
SHAPES = {
    "Provenance": "Provenance",
    "Evidence": "Evidence",
    "Citation": "Citation",
    "Consumer": "Consumer",
    "ConsumerReport": "ConsumerReport",
    "PredicateEntry": "PredicateEntry",
    "PredicateListing": "PredicateListing",
    "ResolveContext": "ResolveContext",
    "Resolution": "Resolution",
    "Proposal": "Proposal",
    "Refusal": "Refusal",
    "Rejection": "Rejection",
    "MergeResult": "MergeResult",
    "TypeListing": "TypeListing",
    "UsageReport": "UsageReport",
}

#: Calls the spec prints as ``def name(...)``, and the Registry method they describe.
CALLS = (
    "consumers",
    "predicates",
    "resolve_type",
    "propose_type",
    "approve",
    "reject",
    "list_types",
    "usage",
    "provenance",
    "retire",
    "reinstate",
    "merge_types",
    "register_consumer",
    "record_use",
)

#: `EDGES.md`'s four printed CALL signatures, against `Registry`. **Row 4c, and the gap
#: is the same one deviation D-4b-2 recorded for a primitive:** `INTERFACE.md`'s fourteen
#: calls have been held against the code since row 3c and `PACKAGE.md`'s eighteen
#: primitives since row 4b's third adversarial round, and `EDGES.md` printed its calls
#: with nothing checking them at all -- in the one document whose surface is not in
#: `INTERFACE.md` §5. Row 4c adds a fourth (`amend_edge`, ruling R37) and changes a
#: third's report shape (`neighbors`, ruling R38), which is exactly when an unchecked
#: printed signature drifts.
EDGE_CALLS = (
    "add_edge",
    "retract_edge",
    "amend_edge",
    "neighbors",
)

#: Fields the spec deliberately declines to print, with the reason. Empty is the goal;
#: an entry here is a decision on the record, not a way to silence the check.
SPEC_OMITS: dict[str, set[str]] = {}

#: PACKAGE.md prints these as real ``@dataclass`` blocks, and they are meant to BE the
#: whole record -- a third-party adapter author builds from them. ``{printed name:
#: (module, attribute)}``. Row 3d, beacon finding U4.
PACKAGE_SHAPES = {
    "Capabilities": (adapter_module, "Capabilities"),
    "TypeRecord": (adapter_module, "TypeRecord"),
    "ProposalRecord": (adapter_module, "ProposalRecord"),
    "ConsumerRecord": (adapter_module, "ConsumerRecord"),
    "UsageRecord": (adapter_module, "UsageRecord"),
    "EventRecord": (adapter_module, "EventRecord"),
    "TypeQuery": (adapter_module, "TypeQuery"),
    "TypePage": (adapter_module, "TypePage"),
    "ProposalQuery": (adapter_module, "ProposalQuery"),
    # Row 4b, EDGES.md 7.1 -- the three shapes a third-party EDGE backend builds from.
    # Listed the day they landed, for beacon finding U4's reason: the drift moves into
    # the half nobody is checking, so there is no half nobody is checking.
    "EdgeRecord": (adapter_module, "EdgeRecord"),
    "EdgeQuery": (adapter_module, "EdgeQuery"),
    "EdgePage": (adapter_module, "EdgePage"),
    # Row 6b, ACTIONS.md 9 -- the two shapes a third-party INVOCATION backend builds
    # from. Listed the day they landed, for beacon finding U4's reason: the drift moves
    # into the half nobody is checking, so there is no half nobody is checking.
    "InvocationRecord": (adapter_module, "InvocationRecord"),
    "InvocationPage": (adapter_module, "InvocationPage"),
    "FieldSpec": (attributes_module, "FieldSpec"),
    "AttributeSchema": (attributes_module, "AttributeSchema"),
    # 6.4 prints the two harness shapes a third-party author builds. They were
    # described only in a module 2.2 calls private until row 3d's third adversarial
    # round; printing them here means they cannot drift from the dataclasses either.
    "BorrowedHarness": (harness_module, "BorrowedHarness"),
    "SchemaHarness": (harness_module, "SchemaHarness"),
}

#: Same rule as SPEC_OMITS, for PACKAGE.md. An entry is a decision on the record.
PACKAGE_OMITS: dict[str, set[str]] = {}

#: EDGES.md prints its shapes as ``Name:`` sketches, exactly as INTERFACE.md does.
#: **Added by row 4b's second adversarial round, and the reason is a defect it found.**
#:
#: EDGES.md 5.1 printed an ``EdgeProvenance`` with no ``model_tier`` and argued at
#: length that the field was *"deliberately absent"* -- while ruling **R20** had granted
#: it before that row started, the code carried it, `C17-02` round-tripped it, and the
#: same document's 14 table printed *"model_tier: yes"* five hundred lines below. The
#: document contradicted the code, the ruling, and itself, in three places at once.
#:
#: INTERFACE.md's printed shapes have been held against `types.py` since row 3c and
#: PACKAGE.md's against `adapter.py` since row 3d, each after the same class of defect.
#: **EDGES.md 5.1 was the last printed shape in this repository that nothing checked,
#: and it is the one that drifted** -- which is the third time this project has watched
#: drift migrate into whichever half is not gated. There is no fourth half.
EDGES_SHAPES = {
    "TypeRef": "TypeRef",
    "InstanceRef": "InstanceRef",
    "Edge": "Edge",
    "EdgeProvenance": "EdgeProvenance",
    "NeighborReport": "NeighborReport",
    "NeighborEdge": "NeighborEdge",
}

#: Same rule as the other two omit maps. An entry is a decision on the record.
EDGES_OMITS: dict[str, set[str]] = {}

#: `ACTIONS.md`'s printed shapes, against `open_ontology/actions.py`. **Row 6b, and
#: nothing held them for three adversarial rounds -- which is why they drifted in every
#: one of the three.**
#:
#: §14 measured the cost of that precisely: round 1 found five drifts between the
#: document and its own probe kit -- `Precondition.namespace`, `Invocation.compensates`,
#: `InvocationProvenance.evidence` and two call signatures -- *inside the section that
#: argues field names were kept ugly BECAUSE that is the drift this checker was written
#: to catch*. All five were fixed, and **round 3 found five more of the same kind plus
#: three whole fields missing** -- `Invocation.declared_policy`,
#: `Invocation.family_version`, `Preflight.family_version` and `record_invocation`'s
#: `judged` parameter, which are the ENTIRETY of round 2's gate-to-record fix, present
#: in rules 3-7 and 3-8 and in the probe and absent from every printed block. *A
#: mechanism specified only in its own rule table is a mechanism the build row cannot
#: build.*
#:
#: §14's own conclusion is the instruction this dict carries out: extend the checker to
#: this file **in the same change that lands the code**, which is now.
ACTIONS_SHAPES = {
    "EdgeRef": (actions_module, "EdgeRef"),
    "InputSpec": (actions_module, "InputSpec"),
    "Precondition": (actions_module, "Precondition"),
    "Effect": (actions_module, "Effect"),
    "Invocation": (actions_module, "Invocation"),
    "InvocationProvenance": (actions_module, "InvocationProvenance"),
    "PreconditionResult": (actions_module, "PreconditionResult"),
    "Preflight": (actions_module, "Preflight"),
    "InvocationReport": (actions_module, "InvocationReport"),
    "ProjectionReport": (actions_module, "ProjectionReport"),
}

#: ACTIONS.md 9 prints its two ADAPTER shapes as real ``@dataclass`` blocks, the way
#: PACKAGE.md 3.3 does, so they are read with that parser rather than the ``Name:`` one.
#:
#: **They are checked here AS WELL AS against PACKAGE.md 3.3, and the duplication is
#: deliberate.** Two documents print the same record; a shape held against only one of
#: them is a shape that can drift in the other -- which is exactly how EDGES.md 5.1's
#: `model_tier` went missing for a row while PACKAGE.md and the code agreed with each
#: other, and a third document asserting a change nobody made is invisible to a two-way
#: diff.
ACTIONS_CLASS_SHAPES = {
    "InvocationRecord": (adapter_module, "InvocationRecord"),
    "InvocationPage": (adapter_module, "InvocationPage"),
}

#: Same rule as the other three omit maps. An entry is a decision on the record.
ACTIONS_OMITS: dict[str, set[str]] = {}

#: `ACTIONS.md`'s four printed CALL signatures, against `Registry`. **Row 6b, and the
#: gap is the one EDGE_CALLS closed one row earlier**: `INTERFACE.md`'s fourteen calls
#: have been held against the code since row 3c, `PACKAGE.md`'s primitives since row 4b,
#: `EDGES.md`'s calls since row 4c -- and this document printed four with nothing
#: checking them at all. Round 3 measured what that costs: `record_invocation`'s
#: `judged` parameter, the whole of round 2's gate-to-record fix, was in a rule table
#: and in the probe kit and in **no printed block**, and 6.4 and 10.3 printed two
#: different `projection` signatures two hundred lines apart.
ACTION_CALLS = (
    "preflight",
    "record_invocation",
    "invocations",
    "projection",
)

#: ACTIONS.md's CLOSED VOCABULARIES, held against `actions.py`'s tuples -- contents, not
#: counts, because this document states them as printed alternatives rather than as
#: number words.
#:
#: ``{tuple name: (the printed shape, the field whose alternatives carry it)}``. Each is
#: read out of the shape block the document already prints, so the vocabulary has ONE
#: home in the specification and one in the code, and the gate holds them together. Row
#: #6 reached ROADMAP.md's kill row twice through a vocabulary rule the document and the
#: implementation disagreed about, so this is not bookkeeping.
ACTION_VOCABULARIES = {
    "EFFECT_OPS": ("Effect", "op"),
    "PRECONDITION_KINDS": ("Precondition", "kind"),
    "OUTCOMES": ("Invocation", "outcome"),
    "GATE_VERDICTS": ("Invocation", "gate_verdict"),
    "REVERSIBILITY": ("Preflight", "reversibility"),
    "APPROVAL_MODES": ("Preflight", "approval_mode"),
    "EVALUATORS": ("PreconditionResult", "evaluated_by"),
    "REF_SHAPES": ("InputSpec", "ref"),
}

_FENCE = re.compile(r"```(?:python)?\n(.*?)```", re.S)
_CLASS = re.compile(r"^class ([A-Z]\w*)[:(]", re.M)
_FIELD = re.compile(r"^\s{4}([a-z_][a-z0-9_]*)\s*:", re.M)
_TABLE_FIELD = re.compile(r"^\|\s*`([a-z_][a-z0-9_]*)`\s*\|", re.M)


def spec_blocks(text: str) -> list[str]:
    return [m.group(1) for m in _FENCE.finditer(text)]


def shape_fields(blocks: list[str], name: str) -> set[str] | None:
    """The field names the spec prints for ``name:``, or None if it prints none."""
    for block in blocks:
        for chunk in re.split(r"\n(?=\S)", block):
            if chunk.lstrip().startswith(f"{name}:"):
                return set(_FIELD.findall(chunk))
    return None


def package_shape_fields(blocks: list[str], name: str) -> set[str] | None:
    """The field names PACKAGE.md prints for ``class <name>:``, or None if it prints none.

    PACKAGE prints executable-looking ``@dataclass`` blocks, so the header is
    ``class Name:`` and the body is four-space-indented ``field: type`` lines, often with
    a trailing comment. A method definition ends the record -- ``Capabilities`` prints
    none, but a future shape might.
    """
    for block in blocks:
        for m in _CLASS.finditer(block):
            if m.group(1) != name:
                continue
            body = block[m.end() :]
            end = re.search(r"^(?:@|class |\S)", body, re.M)
            if end:
                body = body[: end.start()]
            body = re.split(r"^    def ", body, maxsplit=1, flags=re.M)[0]
            # PACKAGE.md packs some records: `namespace: str; kind: str; name: str`.
            # Reading only the first field of such a line invents five findings that are
            # not drift, which is how a checker teaches people to ignore it.
            return {
                name
                for line in body.splitlines()
                for name in _FIELD.findall(
                    "\n".join("    " + part.strip() for part in line.split(";"))
                )
            }
    return None


def call_params(blocks: list[str], name: str) -> set[str] | None:
    for block in blocks:
        m = re.search(rf"def {re.escape(name)}\((.*?)\)\s*->", block, re.S)
        if m:
            body = re.sub(r"#[^\n]*", "", m.group(1))
            found = set()
            for part in re.split(r",(?![^\[\]]*\])", body):
                part = part.strip()
                if not part or part == "*":
                    continue
                found.add(part.split(":")[0].split("=")[0].strip().lstrip("*"))
            return found - {""}
    return None


# ---------------------------------------------------------------------------
# Closed vocabularies -- added by row #4's adversarial round 2.
#
# This checker diffed field NAMES and parameter NAMES and never enum CONTENTS,
# so INTERFACE.md 5.12's enumerated list and ``types.REFUSAL_REASONS`` could
# disagree and the gate would stay green. They did: row #4 added three values to
# both and left ``Refusal``'s own docstring and error message saying "fifteen".
# A reviewer found that by reading two files side by side, which is precisely
# what this file exists to make unnecessary.


#: Number words this checker can read out of prose. Both closed vocabularies state
#: their size in words, and a number the code does not derive is exactly the half that
#: goes stale -- three times so far in this repository.
_WORDS = {
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, "twenty-four": 24,
    "twenty-five": 25, "twenty-six": 26, "twenty-seven": 27, "twenty-eight": 28,
    "twenty-nine": 29, "thirty": 30,
}


def _check_closed_vocabularies(spec_text: str) -> list[str]:
    """INTERFACE.md 5.12's enumerated values must equal ``types.REFUSAL_REASONS``."""
    problems: list[str] = []
    m = re.search(
        r"takes exactly these \*\*([\w-]+)\*\* values.*?:\n\n(.+?)\n",
        spec_text,
        re.S,
    )
    if m is None:
        return ["INTERFACE 5.12: could not find the enumerated Refusal.reason list"]
    printed = set(re.findall(r"`([a-z_]+)`", m.group(2)))
    actual = set(types_module.REFUSAL_REASONS)
    for name in sorted(printed - actual):
        problems.append(
            f"INTERFACE 5.12: {name!r} is enumerated in the document and absent "
            f"from types.REFUSAL_REASONS"
        )
    for name in sorted(actual - printed):
        problems.append(
            f"INTERFACE 5.12: {name!r} is in types.REFUSAL_REASONS and is not "
            f"enumerated in the document -- ruling R3 requires both in one change"
        )
    # The count word in the prose has to match too: a number a reader trusts and
    # the code does not derive is exactly the half that went stale.
    words = _WORDS
    _unused = {
        # Hyphenated from here on. Row 3e: the vocabulary reached twenty-one and this
        # check silently stopped working -- ``\w+`` does not cross a hyphen, so the
        # whole 5.12 block failed to parse and the checker reported "could not find the
        # enumerated list" instead of a wrong number. A checker that degrades into a
        # different error the moment the thing it checks grows has a shelf life, so the
        # words run to thirty and the pattern crosses a hyphen.
        "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, "twenty-four": 24,
        "twenty-five": 25, "twenty-six": 26, "twenty-seven": 27, "twenty-eight": 28,
        "twenty-nine": 29, "thirty": 30,
    }
    said = words.get(m.group(1).lower())
    if said is not None and said != len(actual):
        problems.append(
            f"INTERFACE 5.12 says {m.group(1)!r} values; types.REFUSAL_REASONS "
            f"has {len(actual)}"
        )
    return problems


def _check_warning_vocabulary(spec_text: str) -> list[str]:
    """INTERFACE.md 5.4's table must equal ``types.WARNING_VALUES``.

    Added by row 3e's third adversarial round. 5.4 said "eighteen values" over a table
    that omitted ``gate_unregistered`` -- a value ruling R8 added in row 3d, that v0
    code emits, that ``C11-05`` tests, and that **the table's own last row named**.
    Nothing checked it, because this file held only 5.12's vocabulary. The two closed
    vocabularies are now held the same way, contents and count.

    Values carrying a ``:<detail>`` suffix are compared by their prefix, which is the
    part the vocabulary closes over.
    """
    problems = []
    m = re.search(r"`warnings` vocabulary, complete \u2014 ([\w-]+) values", spec_text)
    if m is None:
        return ["INTERFACE 5.4: could not find the warnings vocabulary heading"]
    block = spec_text[m.end():]
    cut = re.search(r"\n\s*---", block)
    if cut is not None:
        block = block[: cut.start()]
    printed = set(re.findall(r"^\| `([a-z_]+)[:`]", block, re.M))
    actual = set(types_module.WARNING_VALUES)
    for name in sorted(printed - actual):
        problems.append(
            f"INTERFACE 5.4: {name!r} is in the table and absent from "
            f"types.WARNING_VALUES"
        )
    for name in sorted(actual - printed):
        problems.append(
            f"INTERFACE 5.4: {name!r} is in types.WARNING_VALUES and absent from the "
            f"table -- a closed vocabulary nothing derives is one that quietly opens"
        )
    said = _WORDS.get(m.group(1).lower())
    if said is not None and said != len(actual):
        problems.append(
            f"INTERFACE 5.4 says {m.group(1)!r} values; types.WARNING_VALUES has "
            f"{len(actual)}"
        )
    return problems



# ---------------------------------------------------------------------------
# Ruling R31 / ROADMAP standing constraint 8 -- spec rules become executable.
#
# **The measurement that produced the ruling.** Thirteen of row 3e's twenty-one new
# contract ids existed only to pin claims the specifications already made; that row's
# third adversarial round found four false prose sentences no gate could see; and across
# three rows, not one finding of substance came from reading a diff.
#
# **The rule.** Every numbered rule in a spec section ships with either (a) a contract
# id that exercises it, or (b) an explicit `prose-only` tag with a reason -- and this
# checker fails on a rule with neither. It applies from row 4b's landing onward, and 4b
# maps `EDGES.md` §2.4.1, §4.3 and §4.4 first, since it is the row implementing them.
#
# **The mapping lives in the SPEC, not here.** Each of the three sections carries a
# table whose last column names the ids; this reads those tables and holds them against
# the suite. A dict in this file would be a third artefact to keep in step with two
# others, which is the shape of drift the checker exists to catch -- and a reader of
# §4.3 would have to open a Python file to learn which id holds a row.
#
# What it does NOT do, stated rather than implied: it cannot tell that a rule was added
# to a section's PROSE and never added to that section's table. It compares the table to
# the suite, which is two of the three sides. The third side is what the adversarial
# loop is for, and `EDGES.md` §17.5 is honest about what that is worth.

#: `INTERFACE.md` sections that must carry an R31 rule table. **Added by row 4d**, which
#: is the first row to change rules in this document since ruling R31 landed -- standing
#: constraint 8 binds every spec, and until this row the gate only read `EDGES.md`.
#:
#: **They are SUBSECTIONS, and that is the honest choice rather than a dodge.** R31's
#: mechanism requires a section's rule numbers to run 1..N with no gap, so a table under
#: `### 5.3` would be claiming to enumerate every rule in `resolve_type` -- a document
#: this row did not write and has no standing to renumber. A subsection per change
#: enumerates exactly the rules that changed, with no gap and no false claim of coverage.
#: **The residual, stated rather than implied:** the rest of §5.2, §5.3, §5.4 and §5.6
#: remains outside the gate. Bringing a whole section under it is a row's worth of work
#: and belongs to the row that next changes that section wholesale.
R31_INTERFACE_SECTIONS = {
    # Ruling R54 -- `predicates`' extent and `of=` filter resolve the identity.
    "5.2.1": "#### 5.2.1",
    # The Q56 default -- `resolve_type` re-verifies a predicate identity at the read.
    "5.3.2": "#### 5.3.2",
    # Ruling R55 -- the write door names the identity a declaration landed in.
    "5.4.1": "#### 5.4.1",
    # Ruling R54 again, at `list_types`' `predicate=` filter.
    "5.6.1": "#### 5.6.1",
}

#: `EDGES.md` sections that must carry an R31 rule table, and the heading that opens
#: each. Adding a section here is how a later row brings its own rules under the gate.
R31_SECTIONS = {
    "2.4.1": "#### 2.4.1",
    # Row 4c, ruling R34: `payload_schema` stopped being inert, so its rules come under
    # the gate in the change that gave them behaviour rather than a row later.
    "2.5": "### 2.5",
    # Row 4c, ruling R37: `edge_amended` was narrated with a worked example and written
    # by nothing. The amend path lands with its rules under the gate.
    "5.2": "### 5.2",
    "4.3": "### 4.3",
    "4.4": "### 4.4",
}

#: `ACTIONS.md` sections that must carry an R31 rule table. **Row 6b, and §14 says in
#: those words why this dict did not exist a row earlier:**
#:
#: > These ids are PLANNED and nothing claims them yet... `check_spec_drift.py`'s
#: > `R31_SECTIONS` currently lists three `EDGES.md` sections, and its
#: > `_check_rule_coverage` fails a rule whose named id *"no test in the suite claims"*.
#: > **Pointing it at this document today would fail fifty-eight times.** So `ACTIONS.md`
#: > is deliberately not added in this change -- the extension lands in the build row, in
#: > the same change that lands the tests, which is the only order in which the gate is
#: > ever telling the truth. Stated because the alternative failure is worse than the
#: > obvious one: **a checker wired up early gets silenced, and a silenced checker is how
#: > `gate_unregistered` went eighteen-said-nineteen-meant for a row.**
#:
#: All eight, not a subset: the eight tables were RELOCATED by that row's round 1 so that
#: `_section` -- which reads from a heading to the next heading of any level -- can reach
#: them, and thirty of forty-seven rules were unreachable before it did. That work is why
#: this dict can name whole sections rather than the subsections `R31_INTERFACE_SECTIONS`
#: had to settle for.
R31_ACTIONS_SECTIONS = {
    "2.2": "### 2.2",
    "2.4": "### 2.4",
    "2.5": "### 2.5",
    "3": "## 3. Invocations",
    "5.2": "### 5.2",
    "6": "## 6. The calls",
    "8": "## 8. Capability flags",
    "10": "## 10. The tool-slot ceiling",
}

_R31_ROW = re.compile(r"^\| (\d[\d.]*-\d+) \|(.*)\|\s*$", re.M)
_CONTRACT_ID = re.compile(r"`(C\d+-\d+)`")


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    body = text[start + len(heading) :]
    end = re.search(r"^#{2,4} ", body, re.M)
    return body if end is None else body[: end.start()]


def _check_rule_coverage(implemented: set[str]) -> list[str]:
    """Every numbered rule in the R31 sections has an id or a tagged reason."""
    problems: list[str] = []
    for document, path, sections in (
        ("EDGES", EDGES, R31_SECTIONS),
        ("INTERFACE", SPEC, R31_INTERFACE_SECTIONS),
        ("ACTIONS", ACTIONS, R31_ACTIONS_SECTIONS),
    ):
        if not path.exists():  # pragma: no cover - an installed wheel has no docs/
            continue
        problems.extend(
            _check_one_document(path.read_text(encoding="utf-8"), document, sections, implemented)
        )
    return problems


def _check_one_document(
    text: str, document: str, sections: dict[str, str], implemented: set[str]
) -> list[str]:
    problems: list[str] = []
    for label, heading in sections.items():
        body = _section(text, heading)
        if not body:
            problems.append(f"{document} {label}: the section heading {heading!r} is not there")
            continue
        rows = [
            (number, cells)
            for number, cells in _R31_ROW.findall(body)
            if number.startswith(f"{label}-")
        ]
        if not rows:
            problems.append(
                f"{document} {label}: no rule table (ruling R31 / standing constraint 8 -- "
                f"every numbered rule ships with a contract id or a `prose-only:` tag)"
            )
            continue
        seen: list[int] = []
        for number, cells in rows:
            seen.append(int(number.rsplit("-", 1)[1]))
            exercised = cells.rsplit("|", 1)[-1].strip()
            ids = _CONTRACT_ID.findall(exercised)
            if ids:
                for cid in ids:
                    if cid not in implemented:
                        problems.append(
                            f"{document} {number}: names {cid}, and no test in the suite "
                            f"claims that id"
                        )
                continue
            if exercised.startswith("`prose-only:`") or exercised.startswith("prose-only:"):
                reason = exercised.split("prose-only:", 1)[1].strip(" `")
                if len(reason) < 20:
                    problems.append(
                        f"{document} {number}: tagged `prose-only:` with no reason -- R31 "
                        f"requires the reason, because a tag without one is the "
                        f"silencing mechanism the ruling exists to prevent"
                    )
                continue
            problems.append(
                f"{document} {number}: neither a contract id nor a `prose-only:` tag "
                f"(ruling R31 / standing constraint 8). Its `exercised by` cell reads "
                f"{exercised[:60]!r}"
            )
        expected = list(range(1, len(seen) + 1))
        if seen != expected:
            problems.append(
                f"{document} {label}: the rule numbers are {seen}, not {expected} -- a gap "
                f"is a rule somebody deleted from the table and left in the prose"
            )
    return problems


# ---------------------------------------------------------------------------
# PACKAGE.md 3.4's printed PRIMITIVE signatures, against the Protocol.
#
# Added by row 4b's third adversarial round, and the defect that produced it is the
# reason this whole file exists, arriving in the one half of PACKAGE.md nothing reached.
#
# Row 4b added `edge_id` to primitive 15 and its own deviation D-4b-2 said the signature
# had been "amended in the same change". **It had not been.** The Protocol took the
# argument, the registry passed it, and 3.4's printed block still showed the old
# signature -- so a third-party author implementing `read_events` literally from the
# document (which 3.1 calls the whole point: *"conformance must be checkable by people
# who did not write this package"*) got a `TypeError` on the first `edge_provenance`
# call. Two adversarial rounds read past it, because this checker diffed `Registry`
# facade signatures and printed dataclasses and never the eighteen primitive blocks.
#
# Names only, and defaults only where the document prints them -- the same rule the rest
# of this file follows. A primitive the document does not print at all is a finding too:
# 3.4 is what an adapter author builds from.
_PRIMITIVE = re.compile(r"^\*\*\d+\. `(\w+)\((.*?)\)( -> .*?)?`\*\*", re.M)


def _params(text: str) -> set[str]:
    found = set()
    for part in re.split(r",(?![^\[\]]*\])", text):
        part = part.strip()
        if not part or part == "*":
            continue
        found.add(part.split(":")[0].split("=")[0].strip().lstrip("*"))
    return found - {""}


def _check_primitive_signatures(package_text: str) -> list[str]:
    """Every primitive PACKAGE.md 3.4 prints takes what the Protocol takes."""
    problems: list[str] = []
    printed = {name: _params(args) for name, args in
               ((m.group(1), m.group(2)) for m in _PRIMITIVE.finditer(package_text))}
    protocol = adapter_module.StorageAdapter
    import inspect

    expected = {n for n in vars(protocol) if not n.startswith("_")}
    for name in sorted(expected - set(printed)):
        problems.append(
            f"PACKAGE 3.4: the protocol has primitive {name!r} and 3.4 prints no "
            f"signature for it -- an adapter author has nothing to build from"
        )
    for name in sorted(set(printed) - expected):
        problems.append(
            f"PACKAGE 3.4: prints a primitive {name!r} the protocol does not have"
        )
    for name in sorted(set(printed) & expected):
        actual = set(inspect.signature(getattr(protocol, name)).parameters) - {"self"}
        for missing in sorted(actual - printed[name]):
            problems.append(
                f"PACKAGE 3.4 {name}(): the protocol takes {missing!r} and the printed "
                f"signature does not -- a backend built from the document is wrong"
            )
        for extra in sorted(printed[name] - actual):
            problems.append(
                f"PACKAGE 3.4 {name}(): the document prints {extra!r}; the protocol "
                f"does not take it"
            )
    return problems


_SHAPE_FIELD_LINES = re.compile(r"^\s{4}(\w+)\s*:(.*(?:\n\s{8,}#.*)*)", re.M)


def _printed_alternatives(blocks: list[str], shape: str, field_name: str) -> set[str] | None:
    """The quoted alternatives ACTIONS.md prints for one field of one shape.

    The document writes a closed vocabulary as ``kind: "a" | "b" | "c"``, sometimes
    continued on an indented comment line, which is exactly how a reader learns it. This
    reads that back so the reader's source and the code's tuple cannot disagree.
    """
    for block in blocks:
        for chunk in re.split(r"\n(?=\S)", block):
            if not chunk.lstrip().startswith(f"{shape}:"):
                continue
            for name, rest in _SHAPE_FIELD_LINES.findall(chunk):
                if name != field_name:
                    continue
                found = set(re.findall(r'"([a-z_]+)"', rest))
                return found or None
    return None


def _check_action_vocabularies(blocks: list[str], actions_text: str) -> list[str]:
    """Every closed vocabulary ACTIONS.md prints equals the tuple `actions.py` holds."""
    problems: list[str] = []
    for tuple_name, (shape, field_name) in ACTION_VOCABULARIES.items():
        actual = set(getattr(actions_module, tuple_name))
        printed = _printed_alternatives(blocks, shape, field_name)
        if printed is None:
            problems.append(
                f"ACTIONS {shape}.{field_name}: the document prints no closed "
                f"vocabulary there and actions.{tuple_name} holds {sorted(actual)}"
            )
            continue
        for name in sorted(printed - actual):
            problems.append(
                f"ACTIONS {shape}.{field_name}: {name!r} is printed and absent from "
                f"actions.{tuple_name}"
            )
        for name in sorted(actual - printed):
            problems.append(
                f"ACTIONS {shape}.{field_name}: {name!r} is in actions.{tuple_name} and "
                f"is not printed -- a closed vocabulary nothing derives is one that "
                f"quietly opens (ruling R3)"
            )

    # The six governance calls, which 2.5 prints as a middot-separated line rather than
    # as a field. They are the rule the kill row runs through -- *an action that can
    # `merge_types` is ROADMAP.md's kill row wearing a verb* -- so the line and the tuple
    # are held together like any other closed vocabulary.
    m = re.search(
        r"\*\*The six calls that may NOT be an effect.*?\*\*\n\n(.+?)\n", actions_text, re.S
    )
    if m is None:
        problems.append("ACTIONS 2.5: could not find the six governance calls")
    else:
        printed = set(re.findall(r"`([a-z_]+)`", m.group(1)))
        actual = set(actions_module.GOVERNANCE_CALLS)
        for name in sorted(printed ^ actual):
            problems.append(
                f"ACTIONS 2.5: {name!r} is in one of the document's six governance calls "
                f"and actions.GOVERNANCE_CALLS and not the other"
            )

    # Rule 2.5-8's ALLOWLIST, printed in the `Effect` block's own comment. Round 2
    # reached the kill row by OMITTING `kind` from a blocklist, so the allowlist's
    # membership is the thing to hold.
    m = re.search(r"ALLOWLIST:\s*([a-z_ |]+)", actions_text)
    if m is None:
        problems.append("ACTIONS 2.5: could not find the `propose_type` effect allowlist")
    else:
        printed = {part.strip() for part in m.group(1).split("|") if part.strip()}
        actual = set(actions_module.PROPOSABLE_KINDS)
        for name in sorted(printed ^ actual):
            problems.append(
                f"ACTIONS 2.5-8: {name!r} is in the printed allowlist or in "
                f"actions.PROPOSABLE_KINDS and not the other"
            )
    return problems


def _check_printed_primitives(text: str, names: tuple[str, ...], label: str) -> list[str]:
    """Every primitive a document prints as a bare ``def`` takes what the Protocol takes."""
    import inspect

    problems: list[str] = []
    protocol = adapter_module.StorageAdapter
    blocks = spec_blocks(text)
    for name in names:
        printed = call_params(blocks, name)
        if printed is None:
            problems.append(
                f"{label}: prints no signature for primitive {name!r} -- an adapter "
                f"author has nothing to build from"
            )
            continue
        printed -= {"self"}
        method = getattr(protocol, name, None)
        if method is None:
            problems.append(f"{label}: prints a primitive {name!r} the protocol lacks")
            continue
        actual = set(inspect.signature(method).parameters) - {"self"}
        for missing in sorted(actual - printed):
            problems.append(
                f"{label} {name}(): the protocol takes {missing!r} and the printed "
                f"signature does not -- a backend built from the document is wrong"
            )
        for extra in sorted(printed - actual):
            problems.append(
                f"{label} {name}(): the document prints {extra!r}; the protocol does not "
                f"take it"
            )
    return problems


def main() -> int:
    text = SPEC.read_text(encoding="utf-8")
    blocks = spec_blocks(text)
    problems: list[str] = []

    # --- TypeEntry is a table, not a fenced block (2.1).
    table = set(_TABLE_FIELD.findall(text))
    actual = set(types_module.TypeEntry.__dataclass_fields__)
    missing = sorted(actual - table - SPEC_OMITS.get("TypeEntry", set()))
    if missing:
        problems.append(
            f"TypeEntry: the code returns {missing} and 2.1's field table never lists "
            f"them -- an implementer building from the table alone gets the wrong type"
        )

    for spec_name, cls_name in SHAPES.items():
        cls = getattr(types_module, cls_name, None)
        if cls is None or not hasattr(cls, "__dataclass_fields__"):
            problems.append(f"{spec_name}: types.py has no dataclass {cls_name}")
            continue
        printed = shape_fields(blocks, spec_name)
        if printed is None:
            problems.append(
                f"{spec_name}: the spec names it in a signature but never prints its "
                f"shape -- 13's exit criterion says every call has one"
            )
            continue
        actual = set(cls.__dataclass_fields__)
        allowed = SPEC_OMITS.get(spec_name, set())
        for field in sorted(actual - printed - allowed):
            problems.append(f"{spec_name}.{field}: returned by the code, absent from the spec")
        for field in sorted(printed - actual):
            problems.append(f"{spec_name}.{field}: printed by the spec, absent from the code")

    for call in CALLS:
        method = getattr(registry_module.Registry, call, None)
        if method is None:
            problems.append(f"{call}(): the spec declares it; Registry has no such method")
            continue
        import inspect

        actual = set(inspect.signature(method).parameters) - {"self"}
        printed = call_params(blocks, call)
        if printed is None:
            problems.append(f"{call}(): no signature printed in the spec")
            continue
        for name in sorted(actual - printed):
            problems.append(
                f"{call}(): the implementation takes {name!r} and the spec's signature "
                f"does not -- a reader implementing from the spec cannot reach it"
            )
        for name in sorted(printed - actual):
            problems.append(f"{call}(): the spec declares {name!r}; the code does not take it")

    # --- PACKAGE.md's printed dataclasses. Row 3d, beacon finding U4.
    package_blocks = spec_blocks(PACKAGE.read_text(encoding="utf-8"))
    for printed, (module, attribute) in PACKAGE_SHAPES.items():
        cls = getattr(module, attribute, None)
        if cls is None or not hasattr(cls, "__dataclass_fields__"):
            problems.append(f"PACKAGE {printed}: {module.__name__} has no dataclass {attribute}")
            continue
        fields = package_shape_fields(package_blocks, printed)
        if fields is None:
            problems.append(
                f"PACKAGE {printed}: listed as a printed shape and PACKAGE.md prints no "
                f"`class {printed}:` block -- an adapter author has nothing to build from"
            )
            continue
        actual = set(cls.__dataclass_fields__)
        allowed = PACKAGE_OMITS.get(printed, set())
        for name in sorted(actual - fields - allowed):
            problems.append(
                f"PACKAGE {printed}.{name}: the code has it, PACKAGE.md's printed shape "
                f"does not -- a third-party adapter built from the document is wrong"
            )
        for name in sorted(fields - actual):
            problems.append(
                f"PACKAGE {printed}.{name}: printed by PACKAGE.md, absent from the code"
            )

    # --- EDGES.md's printed shapes, against open_ontology/edges.py. Row 4b, round 2.
    if EDGES.exists():
        edges_blocks = spec_blocks(EDGES.read_text(encoding="utf-8"))
        # --- and its printed CALL signatures, against `Registry`. Row 4c.
        for call in EDGE_CALLS:
            method = getattr(registry_module.Registry, call, None)
            if method is None:
                problems.append(
                    f"EDGES {call}(): the spec declares it; Registry has no such method"
                )
                continue
            import inspect

            actual = set(inspect.signature(method).parameters) - {"self"}
            printed = call_params(edges_blocks, call)
            if printed is None:
                problems.append(f"EDGES {call}(): no signature printed in the spec")
                continue
            for name in sorted(actual - printed):
                problems.append(
                    f"EDGES {call}(): the implementation takes {name!r} and the spec's "
                    f"signature does not -- a reader implementing from the spec cannot "
                    f"reach it"
                )
            for name in sorted(printed - actual):
                problems.append(
                    f"EDGES {call}(): the spec declares {name!r}; the code does not take it"
                )
        for printed, attribute in EDGES_SHAPES.items():
            cls = getattr(edges_module, attribute, None)
            if cls is None or not hasattr(cls, "__dataclass_fields__"):
                problems.append(f"EDGES {printed}: open_ontology.edges has no dataclass {attribute}")
                continue
            fields = shape_fields(edges_blocks, printed)
            if fields is None:
                problems.append(
                    f"EDGES {printed}: listed as a printed shape and EDGES.md prints no "
                    f"`{printed}:` block -- a reader has nothing to build from"
                )
                continue
            actual = set(cls.__dataclass_fields__)
            allowed = EDGES_OMITS.get(printed, set())
            for name in sorted(actual - fields - allowed):
                problems.append(
                    f"EDGES {printed}.{name}: the code has it and EDGES.md's printed shape "
                    f"does not -- which is exactly how `model_tier` went missing for a row"
                )
            for name in sorted(fields - actual):
                problems.append(
                    f"EDGES {printed}.{name}: printed by EDGES.md, absent from the code"
                )

    # --- ACTIONS.md's printed shapes and closed vocabularies. Row 6b.
    if ACTIONS.exists():
        actions_text = ACTIONS.read_text(encoding="utf-8")
        actions_blocks = spec_blocks(actions_text)
        for call in ACTION_CALLS:
            method = getattr(registry_module.Registry, call, None)
            if method is None:
                problems.append(
                    f"ACTIONS {call}(): the spec declares it; Registry has no such method"
                )
                continue
            import inspect

            actual = set(inspect.signature(method).parameters) - {"self"}
            printed_params = call_params(actions_blocks, call)
            if printed_params is None:
                problems.append(f"ACTIONS {call}(): no signature printed in the spec")
                continue
            for name in sorted(actual - printed_params):
                problems.append(
                    f"ACTIONS {call}(): the implementation takes {name!r} and the spec's "
                    f"signature does not -- a reader implementing from the spec cannot "
                    f"reach it"
                )
            for name in sorted(printed_params - actual):
                problems.append(
                    f"ACTIONS {call}(): the spec declares {name!r}; the code does not "
                    f"take it"
                )
        for printed, (module, attribute) in ACTIONS_SHAPES.items():
            cls = getattr(module, attribute, None)
            if cls is None or not hasattr(cls, "__dataclass_fields__"):
                problems.append(
                    f"ACTIONS {printed}: {module.__name__} has no dataclass {attribute}"
                )
                continue
            fields = shape_fields(actions_blocks, printed)
            if fields is None:
                problems.append(
                    f"ACTIONS {printed}: listed as a printed shape and ACTIONS.md prints "
                    f"no `{printed}:` block -- a reader has nothing to build from"
                )
                continue
            actual = set(cls.__dataclass_fields__)
            allowed = ACTIONS_OMITS.get(printed, set())
            for name in sorted(actual - fields - allowed):
                problems.append(
                    f"ACTIONS {printed}.{name}: the code has it and ACTIONS.md's printed "
                    f"shape does not -- which is exactly how the whole of round 2's "
                    f"gate-to-record fix went missing from every printed block"
                )
            for name in sorted(fields - actual):
                problems.append(
                    f"ACTIONS {printed}.{name}: printed by ACTIONS.md, absent from the code"
                )
        for printed, (module, attribute) in ACTIONS_CLASS_SHAPES.items():
            cls = getattr(module, attribute)
            fields = package_shape_fields(actions_blocks, printed)
            if fields is None:
                problems.append(
                    f"ACTIONS {printed}: listed as a printed shape and ACTIONS.md prints "
                    f"no `class {printed}:` block -- an adapter author has nothing to "
                    f"build from"
                )
                continue
            actual = set(cls.__dataclass_fields__)
            for name in sorted(actual - fields):
                problems.append(
                    f"ACTIONS {printed}.{name}: the code has it and ACTIONS.md 9's "
                    f"printed shape does not"
                )
            for name in sorted(fields - actual):
                problems.append(
                    f"ACTIONS {printed}.{name}: printed by ACTIONS.md 9, absent from the "
                    f"code"
                )
        problems.extend(_check_action_vocabularies(actions_blocks, actions_text))
        # ACTIONS.md 9's three printed PRIMITIVE signatures, against the Protocol.
        # **Row 6b's first adversarial round found three drifts here and this checker
        # reported the document clean**, because the shape half reads dataclasses and the
        # call half reads `Registry` -- and 9's primitives are neither. PACKAGE.md 3.4's
        # twenty-one are held by `_check_primitive_signatures`; these three are the same
        # objects printed a second time in a second document, and a shape held against
        # only one of the documents that print it is a shape that can drift in the other.
        problems.extend(
            _check_printed_primitives(
                actions_text, ("put_invocation", "get_invocation", "find_invocations"),
                "ACTIONS 9",
            )
        )

    problems.extend(_check_primitive_signatures(PACKAGE.read_text(encoding="utf-8")))
    problems.extend(_check_closed_vocabularies(SPEC.read_text(encoding="utf-8")))
    problems.extend(_check_warning_vocabulary(SPEC.read_text(encoding="utf-8")))

    # Ruling R31, row 4b. The suite is the authority on which ids exist, so it is
    # read rather than listed: a rule table naming an id nobody wrote is exactly the
    # drift this constraint is for, pointing the other way.
    from open_ontology.contract.test_manifest import implemented_ids

    problems.extend(_check_rule_coverage(set(implemented_ids())))

    if problems:
        print("the specifications have drifted from the implementation:\n")
        for p in problems:
            print(f"  - {p}")
        print(
            f"\n{len(problems)} problem(s). Every one of these was, at least once, found "
            "by a human reading two files side by side. Fix the spec, or record the "
            "divergence in SPEC_OMITS with a reason."
        )
        return 1

    print(
        f"{SPEC.relative_to(ROOT)}: every printed shape and signature matches the "
        f"implementation ({len(SHAPES)} shapes, {len(CALLS)} calls).\n"
        f"{PACKAGE.relative_to(ROOT)}: every printed dataclass matches the "
        f"implementation ({len(PACKAGE_SHAPES)} shapes).\n"
        f"INTERFACE.md 5.12: the closed Refusal.reason vocabulary matches "
        f"types.REFUSAL_REASONS ({len(types_module.REFUSAL_REASONS)} values), "
        f"contents and count.\n"
        f"INTERFACE.md 5.4: the closed warnings vocabulary matches "
        f"types.WARNING_VALUES ({len(types_module.WARNING_VALUES)} values).\n"
        f"docs/specs/PACKAGE.md 3.4: every printed primitive signature matches "
        f"StorageAdapter.\n"
        f"docs/specs/EDGES.md: every printed shape and call signature matches the "
        f"implementation ({len(EDGES_SHAPES)} shapes, {len(EDGE_CALLS)} calls).\n"
        f"docs/specs/ACTIONS.md: every printed shape matches open_ontology/actions.py "
        f"({len(ACTIONS_SHAPES) + len(ACTIONS_CLASS_SHAPES)} shapes), every printed call "
        f"signature matches Registry "
        f"({len(ACTION_CALLS)} calls), and every closed vocabulary it prints matches the "
        f"tuple that holds it ({len(ACTION_VOCABULARIES) + 2}).\n"
        f"EDGES.md: every numbered rule in "
        f"{', '.join(sorted(R31_SECTIONS))} carries a contract id or a tagged "
        f"reason (ruling R31, standing constraint 8).\n"
        f"ACTIONS.md: every numbered rule in "
        f"{', '.join(sorted(R31_ACTIONS_SECTIONS))} carries a contract id or a tagged "
        f"reason -- 58 planned ids, 4 prose-only tags, and the gate reads this document "
        f"for the first time in the change that lands them.\n"
        f"INTERFACE.md: every numbered rule in "
        f"{', '.join(sorted(R31_INTERFACE_SECTIONS))} does too -- row 4d is the first "
        f"row to change rules in this document since R31 landed, and constraint 8 binds "
        f"every spec rather than one."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
