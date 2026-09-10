#!/usr/bin/env python3
"""Check configured instruction outputs and optionally their Git tracking."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

from lib.instruction_publication import (
    _fields,
    _references,
    _unique_object,
    load_publications,
    read_regular_bytes,
)


def repository_file(root: Path, relative: str) -> Path:
    """Keep configured reads in the repository without following path symlinks."""
    path = PurePosixPath(relative)
    if (
        path.is_absolute()
        or str(path) != relative
        or any(part in (".", "..") for part in path.parts)
    ):
        raise ValueError(f"Ongeldig repositorypad: {relative!r}")
    target = root
    for part in path.parts:
        target /= part
        if target.is_symlink():
            raise ValueError(f"Symlink in repositorypad: {relative!r}")
    return target


def load_outputs(root: Path):
    """Validate the complete mapping before inspecting any configured output."""
    config = json.loads(
        read_regular_bytes(repository_file(root, "instructions/outputs.json")),
        object_pairs_hook=_unique_object,
    )
    _fields(config, {"version", "files"}, "outputconfiguratie")
    if type(config["version"]) is not int or config["version"] != 1:
        raise ValueError("Onbekende outputconfiguratieversie")
    outputs = config["files"]
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError("Bestandslijst moet een niet-lege mapping zijn")
    publications = load_publications(
        repository_file(root, "instructions/manifest.json")
    )
    targets = {}
    for relative, selected in outputs.items():
        targets[relative] = (repository_file(root, relative), selected)
        _references(selected, publications, relative)
    return publications, targets


def untracked_files(root: Path, outputs) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "-z"],
        capture_output=True,
        check=True,
        timeout=10,
    )
    tracked = set(result.stdout.decode("utf-8").split("\0"))
    required = set(outputs) | {
        "instructions/outputs.json",
        "instructions/manifest.json",
        "scripts/check-instruction-publications.py",
        "scripts/render-instructions.py",
        "scripts/lib/instruction_publication.py",
    }
    required.update(
        path.relative_to(root).as_posix()
        for path in (root / "instructions/blocks").iterdir()
    )
    return required - tracked


def check(root: Path, require_tracked: bool) -> int:
    publications, targets = load_outputs(root)
    failed = False
    checks = 0
    for relative, (target, selected) in targets.items():
        try:
            actual = read_regular_bytes(target)
        except FileNotFoundError:
            print(f"Ontbreekt: {relative}")
            failed = True
            continue
        for publication in selected:
            checks += 1
            if actual != publications[publication].encode("utf-8"):
                print(f"Afwijkende publicatie: {relative} ({publication})")
                failed = True
    if require_tracked:
        for relative in sorted(untracked_files(root, targets)):
            print(f"Niet getrackt: {relative}")
            failed = True
    if failed:
        return 1
    print(
        f"Instructiepublicaties geldig: {len(targets)} bestanden, {checks} publicatiecontroles"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--require-tracked", action="store_true")
    args = parser.parse_args(argv)
    try:
        return check(args.root.resolve(), args.require_tracked)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"Ongeldige instructiepublicatie: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
