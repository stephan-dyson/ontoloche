"""Walks every ``.md`` file in the repo and checks that relative markdown
links resolve to a file on disk. Bare-path backtick references are out of
scope -- only ``[text](path)`` links are extracted.

Usage: ``python docs/tools/check_links.py`` from anywhere; exits non-zero
and lists every unresolved link if any are found.
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target)) or target.startswith("mailto:")


def main() -> int:
    broken: list[tuple[Path, str]] = []
    for md_file in REPO_ROOT.rglob("*.md"):
        if ".venv" in md_file.parts or ".git" in md_file.parts:
            continue
        text = md_file.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or is_external(target) or target.startswith("#"):
                continue
            path_part = target.split("#", 1)[0]
            path_part = urllib.parse.unquote(path_part)
            if not path_part:
                continue
            resolved = (md_file.parent / path_part).resolve()
            if not resolved.exists():
                broken.append((md_file.relative_to(REPO_ROOT), target))

    if broken:
        print(f"{len(broken)} broken relative link(s):")
        for source, target in broken:
            print(f"  {source}: {target}")
        return 1

    print("All relative markdown links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
