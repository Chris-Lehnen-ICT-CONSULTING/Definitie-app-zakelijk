#!/usr/bin/env python3
"""DEF-563: review-inventaris van timingkandidaten, geen wall-clock-bewijs.

Alleen AST; importeert/executeert nooit tests. Nieuwe, gewijzigde en verdwenen
kandidaten vragen expliciete baseline-review. Geen automatische --update.
Exit 0: inventaris gelijk; 1: review nodig; 2: scope/config/parsefout.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

TIMING = re.compile(
    r"duration|elapsed|verstreken|throughput|latency|per_sec|"
    r"(?:^|_)(?:time|seconds|p95|p99)(?:_|$)",
    re.I,
)
CLOCKS = {"time.time", "time.perf_counter", "time.monotonic", "time.process_time"}
SCOPES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
STATUSES = {"unreviewed", "retain-risk", "deterministic", "contract", "non-timing"}
DEFAULT_BASELINE = "docs/testing/def563-timing-baseline.json"


def local_nodes(scope):
    """Nested functions/classes worden afzonderlijk geïnventariseerd."""
    for child in ast.iter_child_nodes(scope):
        if not isinstance(child, SCOPES):
            yield child
            yield from local_nodes(child)


def scopes(node, prefix=""):
    yield prefix or "<module>", node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPES):
            name = f"{prefix}::{child.name}" if prefix else child.name
            yield from scopes(child, name)
        else:
            # Ondersteunt functies onder if/try zonder de ouder opnieuw te tellen.
            yield from nested_scopes(child, prefix)


def nested_scopes(node, prefix):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPES):
            name = f"{prefix}::{child.name}" if prefix else child.name
            yield from scopes(child, name)
        else:
            yield from nested_scopes(child, prefix)


def clock_aliases(tree):
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module == "time":
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"time.{alias.name}"
    return aliases


def time_related(expr, derived, aliases):
    for node in ast.walk(expr):
        if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)):
            if ast.unparse(node) in derived:
                return True
            if isinstance(node, ast.Name):
                name = node.id
            elif isinstance(node, ast.Attribute):
                name = node.attr
            else:
                name = node.slice.value if isinstance(node.slice, ast.Constant) else ""
            if isinstance(name, str) and TIMING.search(name):
                return True
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            first, dot, rest = name.partition(".")
            if aliases.get(first, first) + dot + rest in CLOCKS:
                return True
    return False


def comparisons(scope, aliases):
    nodes = list(local_nodes(scope))
    derived = set()
    # Kleine, conservatieve toekenningsoverdracht; geen interprocedurele analyse.
    assignments = [n for n in nodes if isinstance(n, (ast.Assign, ast.AnnAssign))]
    for _ in range(len(assignments) + 1):
        previous = len(derived)
        for node in assignments:
            if node.value is not None and time_related(node.value, derived, aliases):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                derived.update(ast.unparse(target) for target in targets)
        if len(derived) == previous:
            break
    return [
        ast.unparse(compare)
        for node in nodes
        if isinstance(node, ast.Assert)
        for compare in ast.walk(node.test)
        if isinstance(compare, ast.Compare)
        and any(
            isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in compare.ops
        )
        and time_related(compare, derived, aliases)
    ]


def inventory(root):
    tests = root / "tests"
    if not tests.is_dir() or tests.is_symlink():
        raise ValueError("tests-scope ontbreekt of is een symlink")
    files = []
    for directory, dirs, names in os.walk(tests, followlinks=False, onerror=raise_io):
        for name in dirs + names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError("symlink in tests-scope")
        files.extend(Path(directory) / name for name in names if name.endswith(".py"))
    if not files:
        raise ValueError("lege Python-testscope")
    entries = {}
    for path in sorted(files):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(ast.dump(tree).encode()).hexdigest()
        aliases = clock_aliases(tree)
        for scope, node in scopes(tree):
            found = comparisons(node, aliases)
            if found:
                key = f"{path.relative_to(root).as_posix()}::{scope}"
                if key in entries:
                    raise ValueError("dubbele kandidaatidentiteit")
                entries[key] = {"source_sha256": digest, "comparisons": found}
    return {"schema": 1, "files_scanned": len(files), "entries": entries}


def raise_io(error):
    raise error


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("dubbele JSON-sleutel")
        result[key] = value
    return result


def read_baseline(path):
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("ongeldig baselineschema")
    if not re.fullmatch(r"[a-f0-9]{40}", str(data.get("source_commit", ""))):
        raise ValueError("baseline mist broncommit")
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("baseline mist entries")
    for key, entry in entries.items():
        if (
            not key.startswith("tests/")
            or "::" not in key
            or not isinstance(entry, dict)
        ):
            raise ValueError("ongeldige baseline-entry")
        if not isinstance(entry.get("status"), str) or entry["status"] not in STATUSES:
            raise ValueError("ongeldige dispositie")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise ValueError("dispositie mist reden")
        if not re.fullmatch(r"[a-f0-9]{64}", str(entry.get("source_sha256", ""))):
            raise ValueError("ongeldige bronhash")
        values = entry.get("comparisons")
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(v, str) and v for v in values)
        ):
            raise ValueError("ongeldige vergelijkingen")
    return entries


def check(current, baseline):
    changes = []
    for key in sorted(current.keys() | baseline.keys()):
        if key not in baseline:
            changes.append(("nieuw", key))
        elif key not in current:
            changes.append(("verdwenen", key))
        elif any(
            current[key][field] != baseline[key][field]
            for field in ("source_sha256", "comparisons")
        ):
            changes.append(("gewijzigd", key))
    for kind, key in changes:
        print(f"timing-inventaris: {kind}: {key}")
    print(
        f"timing-inventaris: {len(current)} locaties; {len(changes)} te beoordelen wijzigingen"
    )
    return int(bool(changes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", type=Path, nargs="?", default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--inventory", action="store_true", help="alleen JSON; schrijft geen baseline"
    )
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        result = inventory(root)
        if args.inventory:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        baseline = read_baseline(args.baseline or root / DEFAULT_BASELINE)
        return check(result["entries"], baseline)
    except (OSError, ValueError, SyntaxError, RecursionError) as error:
        # Geen broninhoud of rauwe parserfout in CI-uitvoer.
        print(
            f"timing-inventaris: ongeldige invoer ({type(error).__name__})",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
