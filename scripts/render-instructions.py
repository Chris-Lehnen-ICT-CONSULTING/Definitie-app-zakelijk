#!/usr/bin/env python3
"""Render an explicit instruction publication or check existing bytes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.instruction_publication import load_publications, read_regular_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--publication", required=True)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    try:
        publications = load_publications(args.manifest)
        expected = publications[args.publication].encode("utf-8")
        if args.check is not None:
            if read_regular_bytes(args.check) != expected:
                print(
                    "Afwijkende instructiepublicatie: bron en bestand verschillen.",
                    file=sys.stderr,
                )
                return 1
            return 0
        sys.stdout.buffer.write(expected)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Ongeldige instructiebron: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
