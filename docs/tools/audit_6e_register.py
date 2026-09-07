#!/usr/bin/env python3
"""Read-only derivations for row 6e (the register audit).

Writes nothing and touches no store. Every number 6E-RUN.md publishes about the
kill-row register is produced here, by this file, and the invoking command is
printed beside the number in the document (6E-RUN.md section 0.7).

Usage:
    py docs/tools/audit_6e_register.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REGISTER = Path("docs/decisions/2026-08-29-3c-rulings-R6-R12.md")

# Headings that open a kill-row trip section, and how many counted trips each covers.
TRIP_HEADING = re.compile(r"^## The kill-row trip — (.+)$")

def sections(text: str) -> list[tuple[str, str]]:
    """Split the register into (heading, body) pairs for the trip sections only."""
    out: list[tuple[str, str]] = []
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = TRIP_HEADING.match(line)
        if m:
            if current is not None:
                out.append((current, "\n".join(buf)))
            current = m.group(1)
            buf = []
        elif current is not None:
            if line.startswith("## ") or line.startswith("### "):
                out.append((current, "\n".join(buf)))
                current = None
                buf = []
            else:
                buf.append(line)
    if current is not None:
        out.append((current, "\n".join(buf)))
    return out


def main() -> int:
    if not REGISTER.exists():
        print(f"not found: {REGISTER} (run from the repo root)", file=sys.stderr)
        return 2
    text = REGISTER.read_text(encoding="utf-8")
    secs = sections(text)

    print("=" * 72)
    print("D1  trip sections found")
    print("=" * 72)
    for head, _ in secs:
        print(f"  - {head[:96]}")
    print(f"  TOTAL SECTIONS: {len(secs)}")

    # D2 -- the harm mechanism. A trip section states the kill-row harm when it
    # records resolve_type answering at confidence 1.0.
    print()
    print("=" * 72)
    print("D2  sections whose recorded harm is resolve_type answering at 1.0")
    print("=" * 72)
    # NOTE: this test is deliberately NOT line-based. The row-6d sections of the
    # register are hard-wrapped at ~100 columns, so `resolve_type` and the `1.0`
    # it answers with routinely land on different lines; a line-based test
    # reports 14 and is wrong. Search the section body across newlines.
    harm = re.compile(r"resolve_type.{0,240}1\.0|1\.0.{0,240}resolve_type", re.S)
    with_10 = []
    without = []
    for head, body in secs:
        (with_10 if harm.search(body) else without).append(head)
    for h in with_10:
        print(f"  1.0  {h[:88]}")
    for h in without:
        print(f"  --   {h[:88]}")
    print(f"  SECTIONS WITH resolve_type-at-1.0 HARM: {len(with_10)} of {len(secs)}")

    # D2b -- the wider test: a 1.0 answer on the word, however the section words
    # it. The three sections D2 misses are trips 1-2 (the harm is the merge
    # itself, before any resolver claim was in the record) and trips 20-22,
    # which state the 1.0 without naming the call.
    any10 = [h for h, b in secs if "1.0" in b]
    print(f"  SECTIONS RECORDING A 1.0 ANSWER AT ALL: {len(any10)} of {len(secs)}")
    print(f"  SECTIONS WITH NO 1.0 AT ALL: {[h[:60] for h, b in secs if '1.0' not in b]}")

    # D3 -- who the register credits with the one-call diagnosis, and where it
    # actually first appears.
    print()
    print("=" * 72)
    print("D3  the one-call diagnosis: first appearance vs later attribution")
    print("=" * 72)
    sentence = re.compile(r"guard written for (?:ONE|one) CALL|guard written for one call", re.I)
    credit = re.compile(r"(?:SIXTH|sixth) trip's (?:diagnosis|own shape)")
    first_lines = [i + 1 for i, ln in enumerate(text.splitlines()) if sentence.search(ln)]
    credit_lines = [i + 1 for i, ln in enumerate(text.splitlines()) if credit.search(ln)]
    print(f"  sentence appears at lines: {first_lines}")
    print(f"  FIRST APPEARANCE: line {first_lines[0] if first_lines else 'n/a'}")
    print(f"  credited to 'the sixth trip' at lines: {credit_lines}")
    print(f"  ATTRIBUTIONS TO THE SIXTH TRIP: {len(credit_lines)}")

    # D4 -- the refrain, and the criterion's two readings.
    print()
    print("=" * 72)
    print("D4  refrain and criterion wording")
    print("=" * 72)
    refrain = len(re.findall(r"design is \*?\*?still\*?\*? not what tripped", text))
    print(f"  'the design is still not what tripped' occurrences: {refrain}")
    for phrase in (
        "capability predicate gets merged as a duplicate",
        "two things answering to one identity",
        "answering to one identity",
        "two ACTIVE rows answering to one word",
        "two live entries holding one word",
    ):
        print(f"  {len(re.findall(re.escape(phrase), text)):>3}  {phrase!r}")

    # D5 -- Q56, the class-closing question that was never ruled.
    print()
    print("=" * 72)
    print("D5  Q56 -- the read-side class-closing question")
    print("=" * 72)
    q56 = [i + 1 for i, ln in enumerate(text.splitlines()) if "Q56" in ln]
    closing = len(re.findall(r"class-closing question[^.]*Q56|Q56[^.]*class-closing", text))
    print(f"  Q56 mentioned on lines: {q56}")
    print(f"  Q56 mentions: {len(q56)}")
    print(f"  named as the class-closing question: {closing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
