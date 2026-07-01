#!/usr/bin/env python3
"""Strip Hermes read_file line-number prefixes from a source file.

Hermes' read_file tool returns lines prefixed with line numbers like:

    1|import React from 'react'
    2|function App() {

If that output is written back to a JSX/JS/Python/etc. file unchanged, the file
becomes invalid and the dev server / build will crash with a blank white screen
or syntax errors. This script removes those prefixes in-place.

Usage:
    python3 fix-line-number-corruption.py src/App.jsx
"""

import argparse
import re
import sys


def clean(content: str) -> str:
    lines = content.splitlines(keepends=True)
    out = []
    for line in lines:
        # Remove one or more leading "N|" groups, e.g. "1|" or "1|1|"
        cleaned = re.sub(r"^(\d+\|)+", "", line)
        out.append(cleaned)
    return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Strip Hermes read_file line-number prefixes from a file.")
    parser.add_argument("path", help="File to clean in-place")
    args = parser.parse_args()

    path = args.path
    try:
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    cleaned = clean(original)
    if cleaned == original:
        print(f"No line-number prefixes found in {path}; nothing changed.")
        return 0

    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    print(f"Cleaned {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
