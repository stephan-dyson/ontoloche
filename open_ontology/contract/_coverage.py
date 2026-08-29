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
        #: Ids whose test blew up in SETUP or TEARDOWN rather than in the call. pytest
        #: reports those as `when="setup", outcome="failed"`, which matched neither of
        #: this class's two branches, so the id **vanished** -- not exercised, not
        #: skipped, not failed -- and the leg still printed CONFORMANT. Reproduced by an
        #: adversarial reviewer (row 3d, second round) against the real class, and it is
        #: the exact failure mode the report exists to catch: a defect in the backend
        #: under test, in its __init__ or a fixture, disappearing from the count.
        self.errored: dict[str, set[str]] = defaultdict(set)
        #: ``leg -> {contract id: reason}``
        self.skipped: dict[str, dict[str, str]] = defaultdict(dict)
        #: Ids whose test takes no ``adapter`` fixture, so they run ONCE for the whole
        #: session rather than per leg -- C0-04 inspects source text and C14-07 asks
        #: what the package ships. Counted separately, and counted: without this line
        #: the per-leg arithmetic silently comes up two short of 6.2's enumeration,
        #: which is the shape of hole the report exists to close.
        self.backend_independent: set[str] = set()
        #: ``leg -> Capabilities``, recorded by the adapter fixture. Row 3d, second
        #: adversarial round: a declaration nobody can check must not read as checked.
        self.declared: dict[str, object] = {}

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
        if report.outcome == "failed" and report.when in ("setup", "teardown"):
            # An error, not a skip and not a pass. Counted, named, and fatal to the
            # verdict -- never silently dropped.
            if cid:
                self.errored[leg].add(cid)
            return
        if report.outcome == "skipped" and report.when in ("setup", "call"):
            if cid:
                self.skipped[leg].setdefault(cid, _reason_of(report))

    def declare(self, leg: str, caps) -> None:
        """Record what a leg's adapter DECLARED, so the report can say what was checked.

        **Why, and it is a reproduced defect** *(row 3d, second adversarial round)*. An
        adversarial reviewer built an adapter that declares
        ``transaction_scope="savepoint"`` -- *I never commit, the host owns the
        transaction* -- and then committed at depth 0 anyway, which is the literal U1
        regression this row exists to fix. It ran the suite to **`130 passed`, verdict
        CONFORMANT**, because the only test that checks the claim (`C0-12`) needs a host
        connection the suite cannot conjure and skipped.

        Two things came out of that. `C0-12` is now generic -- a third-party author
        supplies a ``BorrowedHarness`` and it runs against their adapter. And when
        nobody supplies one, **the verdict says the declaration was not verified**,
        rather than printing a clean CONFORMANT over a claim taken on trust.
        """
        self.declared[leg] = caps

    #: ``(attribute, predicate, contract id, what to do about it)``. A declaration in
    #: this table is only worth the word "conformant" if its id actually ran.
    CHECKED_DECLARATIONS = (
        (
            "transaction_scope",
            lambda v: v == "savepoint",
            "C0-12",
            'transaction_scope="savepoint" (this adapter says it never commits) -- '
            "supply a BorrowedHarness via run_contract_suite(borrowed_factory=...) "
            "or --borrowed to have it checked",
        ),
        (
            "owns_schema",
            lambda v: v is False,
            "C0-09",
            "owns_schema=False (this adapter says migrate() issues no DDL) -- verified "
            "only for the reference backends, which build the host schema themselves",
        ),
    )

    def unverified(self, leg: str) -> list[str]:
        caps = self.declared.get(leg)
        if caps is None:
            return []
        out = []
        for attribute, holds, cid, advice in self.CHECKED_DECLARATIONS:
            value = getattr(caps, attribute, None)
            if holds(value) and cid not in self.exercised[leg]:
                out.append(f"{cid} did not run here: {advice}")
        return out

    def legs_seen(self) -> list[str]:
        seen = set(self.exercised) | set(self.skipped) | set(self.errored)
        return [leg for leg in self.legs if leg in seen]

    def universe(self) -> set[str]:
        """Every contract id this run touched on any leg.

        The closure check below is against what the run actually collected rather than
        against 6.2's enumeration, so a deliberately filtered run (`-k`) still closes.
        A leg that is short of the universe is short of something the other legs saw.
        """
        ids: set[str] = set(self.backend_independent)
        for leg in self.legs:
            ids |= self.exercised[leg] | set(self.skipped[leg]) | self.errored[leg]
        return ids

    def unaccounted(self, leg: str) -> set[str]:
        seen = self.exercised[leg] | set(self.skipped[leg]) | self.errored[leg]
        return self.universe() - seen - self.backend_independent

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
            unverified = self.unverified(leg)
            unaccounted = self.unaccounted(leg)
            if self.failed[leg] or self.errored[leg] or unaccounted:
                verdict = "NOT CONFORMANT"
            elif unverified:
                verdict = "CONFORMANT, DECLARATIONS UNVERIFIED"
            else:
                verdict = "CONFORMANT"
            listed = " (listed)" if missing else ""
            out.append(
                f"    {leg:<{width}}  {verdict}: {len(done)} ids exercised, "
                f"{len(missing)} not exercisable on this backend{listed}"
            )
            if self.failed[leg]:
                out.append(
                    f"    {'':<{width}}  failed here: {', '.join(sorted(self.failed[leg]))}"
                )
            if self.errored[leg]:
                out.extend(
                    _wrap(
                        "ERRORED in setup or teardown here (the test never ran): "
                        + ", ".join(sorted(self.errored[leg])),
                        f"    {'':<{width}}  ",
                    )
                )
            if unaccounted:
                out.extend(
                    _wrap(
                        "INCOMPLETE COVERAGE -- these ids ran on another leg and are "
                        "neither exercised, skipped nor errored here, so this run cannot "
                        "say what happened to them: " + ", ".join(sorted(unaccounted)),
                        f"    {'':<{width}}  ",
                    )
                )
            pad = f"    {'':<{width}}    "
            for line in unverified:
                out.extend(_wrap("NOT VERIFIED -- " + line, f"    {'':<{width}}  "))
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
