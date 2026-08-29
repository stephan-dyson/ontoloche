"""The conformance coverage report -- ruling **R12**, roadmap row 3d.

> **A conformance claim without its coverage line is not a claim.**

Row 3c gave the suite a `CONFORMANCE` summary naming which *backends* ran, because a
run with no Postgres exits `0` having exercised SQLite alone and a skip is easy to miss
beside a wall of passes. R12 says the same thing one level down: a backend that declines
capabilities **cannot exercise every contract id**, and a run that reports only "329
passed" is telling the truth about the assertions and not about the coverage.

So conformance stops asserting *"the whole suite passed"* and starts asserting *"the
whole suite passed; N ids exercised, M not exercisable on this backend, listed"* -- the
same move as `ConsumerReport.complete=False`, and for the same reason: a report that
omits what it could not see promises a completeness it does not have.

**What counts as exercised.** An id is exercised on a leg when a test claiming that id
ran to `passed` or `failed` on that leg. It is *not exercisable* when every test
claiming it was **skipped** there -- and the skip reasons already say why, because the
`requires_capability` fixture and the mid-test guards were written to name the flag and
quote the backend's own `why`. This module aggregates what was already there; it invents
no reasons of its own.

The bookkeeping tests (`test_manifest`, the parity tests) claim no contract id and are
not counted: they are about the suite, not about the backend under test.
"""

from __future__ import annotations

import re
import textwrap
from collections import defaultdict

__all__ = ["Coverage", "contract_id_of"]

#: ``open_ontology/contract/test_c5_approve_reject.py::test_c5_03_x[postgres]`` -> ``C5-03``
_ID = re.compile(r"::test_c(\d+)_(\d+)_")


def contract_id_of(nodeid: str) -> str | None:
    """The contract id a node claims, or None when it claims none."""
    m = _ID.search(nodeid)
    if m is None:
        return None
    return f"C{int(m.group(1))}-{int(m.group(2)):02d}"


def _reason_of(report) -> str:
    """The skip reason, as the test wrote it. Never paraphrased here."""
    longrepr = getattr(report, "longrepr", None)
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        text = str(longrepr[2])
    else:
        text = str(longrepr or "")
    text = text.strip()
    if text.startswith("Skipped: "):
        text = text[len("Skipped: ") :]
    return " ".join(text.split()) or "skipped with no reason given"


class Coverage:
    """Per-leg id coverage, accumulated from pytest reports.

    One instance per run. The sync and async conftests both drive this one class, so the
    two stacks cannot report coverage differently -- which would be its own small version
    of the drift the whole repository is arranged against.
    """

    def __init__(self, legs: tuple[str, ...]):
        self.legs = tuple(legs) + ("external",)
        self.exercised: dict[str, set[str]] = defaultdict(set)
        self.failed: dict[str, set[str]] = defaultdict(set)
        #: ``leg -> {contract id: reason}``
        self.skipped: dict[str, dict[str, str]] = defaultdict(dict)
        #: Ids whose test takes no ``adapter`` fixture, so they run ONCE for the whole
        #: session rather than per leg -- C0-04 inspects source text and C14-07 asks
        #: what the package ships. Counted separately, and counted: without this line
        #: the per-leg arithmetic silently comes up two short of 6.2's enumeration,
        #: which is the shape of hole the report exists to close.
        self.backend_independent: set[str] = set()

    # ------------------------------------------------------------------ collection
    def leg_of(self, nodeid: str) -> str | None:
        """Which leg this node ran on, from the parametrisation brackets.

        Substring matching on ``f"[{leg}]"`` is not enough and the first version of this
        was wrong because of it: ``C4-09`` is parametrised over malformed names as well
        as over backends, so its ids read ``[sqlite-name0]`` and matched no leg at all --
        **three contract ids went missing from every leg's count**, which is precisely
        the class of silent omission this report exists to stop. Found by the report's
        own arithmetic not adding up on its first run.
        """
        start = nodeid.rfind("[")
        if start == -1 or not nodeid.endswith("]"):
            return None
        parts = nodeid[start + 1 : -1].split("-")
        for leg in self.legs:
            if leg in parts:
                return leg
        return None

    def record(self, report) -> None:
        cid = contract_id_of(report.nodeid)
        leg = self.leg_of(report.nodeid)
        if leg is None:
            if cid and report.when == "call" and report.outcome in ("passed", "failed"):
                self.backend_independent.add(cid)
            return
        if report.when == "call" and report.outcome in ("passed", "failed"):
            if cid:
                self.exercised[leg].add(cid)
                if report.outcome == "failed":
                    self.failed[leg].add(cid)
            return
        if report.outcome == "skipped" and report.when in ("setup", "call"):
            if cid:
                self.skipped[leg].setdefault(cid, _reason_of(report))

    def legs_seen(self) -> list[str]:
        seen = set(self.exercised) | set(self.skipped)
        return [leg for leg in self.legs if leg in seen]

    # --------------------------------------------------------------------- report
    def lines(self) -> list[str]:
        """The coverage block, ready to print. Ruling R12's required shape."""
        out: list[str] = []
        legs = self.legs_seen()
        if not legs:
            return out
        out.append("  coverage, per leg (PACKAGE.md 6.4 / ruling R12):")
        width = max(len(leg) for leg in legs)
        for leg in legs:
            done = self.exercised[leg]
            # An id skipped on one test but exercised by another claiming the same id
            # is exercised. C0-08 and C0-12 are hand-written twice for that reason.
            missing = {cid: why for cid, why in self.skipped[leg].items() if cid not in done}
            verdict = "NOT CONFORMANT" if self.failed[leg] else "CONFORMANT"
            listed = " (listed)" if missing else ""
            out.append(
                f"    {leg:<{width}}  {verdict}: {len(done)} ids exercised, "
                f"{len(missing)} not exercisable on this backend{listed}"
            )
            if self.failed[leg]:
                out.append(
                    f"    {'':<{width}}  failed here: {', '.join(sorted(self.failed[leg]))}"
                )
            pad = f"    {'':<{width}}    "
            for reason, ids in sorted(
                _group(missing).items(), key=lambda kv: (-len(kv[1]), kv[0])
            ):
                head, *rest = _wrap(f"{len(ids)}: {reason}", pad)
                out.append(head)
                out.extend(rest)
                out.extend(_wrap(", ".join(sorted(ids)), pad + "   "))
        if self.backend_independent:
            out.append(
                f"    (+{len(self.backend_independent)} backend-independent, run once: "
                f"{', '.join(sorted(self.backend_independent))})"
            )
        out.append(
            "  A conformance claim without its coverage line is not a claim (ruling R12)."
        )
        return out


def _group(missing: dict[str, str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for cid, reason in missing.items():
        grouped[reason].append(cid)
    return grouped


def _wrap(text: str, pad: str, width: int = 96) -> list[str]:
    """Wrapped, never truncated. The interesting half of a `requires_capability` reason
    is the backend's own ``why``, which is at the END of the sentence -- an earlier
    version clipped the line and cut off exactly that."""
    lines = textwrap.wrap(text, width=width) or [""]
    return [pad + lines[0]] + [pad + "  " + line for line in lines[1:]]
