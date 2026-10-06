#!/usr/bin/env python3
"""Keeps README.md (English) and README.de.md (German) in step.

Checks that both files have the same heading structure (levels in the same
order), that each links to the other, and that every relative link and every
in-page anchor resolves.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {"README.md": "README.de.md", "README.de.md": "README.md"}
LINK = re.compile(r"\]\(([^)\s]+)\)")
failures = []


def headings(text):
    out, fenced = [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,6} ", line):
            level, title = line.split(" ", 1)
            out.append((len(level), title.strip()))
    return out


def slug(title):
    # GitHub: lower case, drop punctuation except hyphens, spaces become hyphens.
    title = re.sub(r"[`*_]", "", title.lower())
    return re.sub(r"[^\w\- ]", "", title).replace(" ", "-")


def fail(msg):
    failures.append(msg)
    print("  FAIL  " + msg)


def main():
    structure = {}
    for name, other in FILES.items():
        text = open(os.path.join(ROOT, name), encoding="utf-8").read()
        heads = headings(text)
        structure[name] = [level for level, _ in heads]
        anchors = {slug(t) for _, t in heads}
        if f"]({other})" not in text.split("\n## ", 1)[0]:
            fail(f"{name}: no language link to {other} above the first section")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, anchor = target.partition("#")
            if path and not os.path.exists(os.path.join(ROOT, path)):
                fail(f"{name}: broken link {target}")
            if not path and anchor and anchor not in anchors:
                fail(f"{name}: unknown anchor #{anchor}")
    a, b = structure["README.md"], structure["README.de.md"]
    if a != b:
        fail(f"heading structure differs: README.md {a} vs README.de.md {b}")
    print(f"README check: {len(a)} headings each, {len(failures)} problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
