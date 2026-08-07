#!/usr/bin/env python3
"""Validate completeness and review state of the frozen inventory."""

from __future__ import annotations

import argparse
import base64
import csv
import datetime
import hashlib
import importlib.util
import io
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
BUILDER_SPEC = importlib.util.spec_from_file_location(
    "review_build_inventory", TOOLS_DIR / "build_inventory.py"
)
if BUILDER_SPEC is None or BUILDER_SPEC.loader is None:
    raise RuntimeError("could not load build_inventory.py")
builder = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(builder)


FINDING_FIELDS = builder.FINDING_FIELDS
STATUSES = {"pending", "in_review", "reviewed", "verified", "blocked", "out_of_scope"}
FINAL_STATUSES = {"verified", "out_of_scope"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
CERTAINTIES = {"proven", "suspected", "not_tested"}
REVIEW_TOOL_PATHS = {
    "docs/reviews/2026-08-07-line-by-line/tools/build_inventory.py",
    "docs/reviews/2026-08-07-line-by-line/tools/test_inventory_tools.py",
    "docs/reviews/2026-08-07-line-by-line/tools/validate_inventory.py",
}
LINE_CLASSIFICATIONS = {
    "binary_equivalent_review",
    "blank",
    "code",
    "comment",
    "configuration",
    "data",
    "documentation",
    "empty_file",
    "generated",
    "gitlink_equivalent_review",
    "pending_line_review",
    "symlink_equivalent_review",
}
SYMBOL_KINDS = {
    "module",
    "class",
    "function",
    "async_function",
    "method",
    "async_method",
    "nested_function",
    "nested_async_function",
    "property_getter",
    "property_setter",
    "property_deleter",
    "staticmethod",
    "async_staticmethod",
    "classmethod",
    "async_classmethod",
    "lambda",
}


def _read_csv(
    path: pathlib.Path,
    expected_fields: list[str],
    errors: list[str],
    *,
    required: bool = True,
) -> list[dict[str, str]]:
    if not path.is_file():
        if required:
            errors.append(f"missing CSV: {path.name}")
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_fields:
            errors.append(
                f"invalid header in {path.name}: expected {expected_fields}, got {reader.fieldnames}"
            )
            return []
        rows: list[dict[str, str]] = []
        for line_number, raw_row in enumerate(reader, start=2):
            if None in raw_row or any(value is None for value in raw_row.values()):
                errors.append(f"malformed row in {path.name} at line {line_number}")
            rows.append({field: raw_row.get(field) or "" for field in expected_fields})
        return rows


def _duplicates(values: list[str]) -> set[str]:
    return {value for value, count in Counter(values).items() if count > 1}


def _reviewer_errors(row: dict[str, str], label: str) -> list[str]:
    if row.get("status") not in {"verified", "out_of_scope"}:
        return []
    reviewer = row.get("reviewer", "").strip()
    verifier = row.get("verified_by", "").strip()
    if not reviewer or not verifier:
        if row.get("status") == "out_of_scope":
            return [f"{label}: out_of_scope row requires independent reviewers"]
        return [f"{label}: verified row requires two reviewers"]
    if reviewer.casefold() == verifier.casefold():
        if row.get("status") == "out_of_scope":
            return [f"{label}: out_of_scope row requires independent reviewers"]
        return [f"{label}: verified row requires a different reviewer"]
    return []


def _status_errors(
    rows: list[dict[str, str]],
    label: str,
    *,
    require_final: bool,
) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        status = row.get("status", "")
        row_label = f"{label} row {index}"
        if status not in STATUSES:
            errors.append(f"{row_label}: invalid status {status!r}")
            continue
        errors.extend(_reviewer_errors(row, row_label))
        if require_final and status == "blocked":
            errors.append(f"blocked {label} row at {row.get('path', row_label)}")
        elif require_final and status not in FINAL_STATUSES:
            errors.append(f"{label} row is not final at {row.get('path', row_label)}")
    return errors


def _decode_path(encoded: str, label: str, errors: list[str]) -> bytes | None:
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        errors.append(f"{label}: invalid path_b64")
        return None


def _split_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.replace(",", ";").split(";") if item.strip()}


def _validate_file_rows(
    rows: list[dict[str, str]],
    expected: list[dict[str, str]],
    require_final: bool,
) -> tuple[list[str], dict[str, dict[str, str]]]:
    errors = _status_errors(rows, "file", require_final=require_final)
    expected_by_id = {row["path_b64"]: row for row in expected}
    actual_ids = [row["path_b64"] for row in rows]
    for path_b64 in sorted(_duplicates(actual_ids)):
        errors.append(f"duplicate file row: {path_b64}")
    actual_by_id = {row["path_b64"]: row for row in rows}
    for path_b64 in sorted(expected_by_id.keys() - actual_by_id.keys()):
        errors.append(f"tracked file missing: {expected_by_id[path_b64]['path']}")
    for path_b64 in sorted(actual_by_id.keys() - expected_by_id.keys()):
        errors.append(
            f"unknown file row: {actual_by_id[path_b64].get('path', path_b64)}"
        )
    immutable_fields = [
        "path",
        "path_b64",
        "git_mode",
        "object_type",
        "object_id",
        "file_type",
        "bytes",
        "physical_lines",
        "logical_lines",
        "scope_tier",
    ]
    for path_b64 in expected_by_id.keys() & actual_by_id.keys():
        actual = actual_by_id[path_b64]
        expected_row = expected_by_id[path_b64]
        _decode_path(path_b64, f"file {actual.get('path', path_b64)}", errors)
        for field in immutable_fields:
            if actual.get(field) != expected_row[field]:
                errors.append(f"{field} drift at {expected_row['path']}")
        if actual.get("scope_tier") not in set("ABCDEF"):
            errors.append(f"invalid scope tier at {expected_row['path']}")
    return errors, actual_by_id


def _validate_symbol_rows(
    rows: list[dict[str, str]],
    expected: list[dict[str, str]],
    file_ids: set[str],
    require_final: bool,
) -> tuple[list[str], dict[str, dict[str, str]]]:
    errors = _status_errors(rows, "symbol", require_final=require_final)
    expected_by_id = {row["symbol_id"]: row for row in expected}
    actual_ids = [row["symbol_id"] for row in rows]
    for symbol_id in sorted(_duplicates(actual_ids)):
        errors.append(f"duplicate Python symbol row: {symbol_id}")
    actual_by_id = {row["symbol_id"]: row for row in rows}
    for symbol_id in sorted(expected_by_id.keys() - actual_by_id.keys()):
        row = expected_by_id[symbol_id]
        errors.append(f"Python symbol missing: {row['path']}::{row['qualified_name']}")
    for symbol_id in sorted(actual_by_id.keys() - expected_by_id.keys()):
        errors.append(f"unknown Python symbol: {symbol_id}")
    immutable_fields = [
        "symbol_id",
        "path",
        "path_b64",
        "qualified_name",
        "kind",
        "start_line",
        "start_col",
        "end_line",
        "end_col",
        "parent_symbol",
        "decorators",
        "complexity",
    ]
    for symbol_id in expected_by_id.keys() & actual_by_id.keys():
        actual = actual_by_id[symbol_id]
        expected_row = expected_by_id[symbol_id]
        for field in immutable_fields:
            if actual.get(field) != expected_row[field]:
                errors.append(f"symbol {field} drift at {symbol_id}")
        if actual.get("kind") not in SYMBOL_KINDS:
            errors.append(f"invalid symbol kind at {symbol_id}")
        if actual.get("path_b64") not in file_ids:
            errors.append(f"symbol has unknown file at {symbol_id}")
        parent = actual.get("parent_symbol", "")
        if parent and parent not in actual_by_id:
            errors.append(f"symbol has unknown parent at {symbol_id}")
    return errors, actual_by_id


def _range_values(
    row: dict[str, str], label: str, errors: list[str]
) -> tuple[int, int] | None:
    try:
        start = int(row.get("start_line", ""))
        end = int(row.get("end_line", ""))
    except ValueError:
        errors.append(f"{label}: non-numeric line range")
        return None
    if start > end:
        errors.append(f"{label}: inverted line range")
        return None
    return start, end


def _partition_errors(
    ranges: list[tuple[int, int]],
    physical_lines: int,
    label: str,
    *,
    outside_message: str,
    gap_message: str,
    overlap_message: str,
) -> list[str]:
    if physical_lines == 0:
        if ranges != [(0, 0)]:
            return [f"{outside_message}: {label}"]
        return []
    errors: list[str] = []
    valid = sorted(ranges)
    cursor = 1
    for start, end in valid:
        if start < 1 or end > physical_lines:
            errors.append(f"{outside_message}: {label}")
            continue
        if start > cursor:
            errors.append(f"{gap_message}: {label} before line {start}")
        elif start < cursor:
            errors.append(f"{overlap_message}: {label} at line {start}")
        cursor = max(cursor, end + 1)
    if cursor <= physical_lines:
        errors.append(f"{gap_message}: {label} after line {cursor - 1}")
    return errors


def _validate_line_coverage(
    rows: list[dict[str, str]],
    files: dict[str, dict[str, str]],
    require_final: bool,
) -> list[str]:
    errors = _status_errors(rows, "line coverage", require_final=require_final)
    grouped: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for index, row in enumerate(rows, start=2):
        path_b64 = row.get("path_b64", "")
        if path_b64 not in files:
            errors.append(f"unknown line coverage path at row {index}")
            continue
        if row.get("path") != files[path_b64]["path"]:
            errors.append(f"line coverage path drift at row {index}")
        file_row = files[path_b64]
        if row.get("reviewed_object_id") != file_row.get("object_id"):
            errors.append(f"line reviewed_object_id drift at {file_row['path']}")
        classification = row.get("classification", "")
        if classification not in LINE_CLASSIFICATIONS:
            errors.append(f"invalid line classification at {file_row['path']}")
        elif file_row.get("object_type") == "commit":
            if classification != "gitlink_equivalent_review":
                errors.append(
                    f"gitlink line classification mismatch at {file_row['path']}"
                )
        elif file_row.get("git_mode") == "120000":
            if classification != "symlink_equivalent_review":
                errors.append(
                    f"symlink line classification mismatch at {file_row['path']}"
                )
        elif file_row.get("physical_lines") == "":
            if classification != "binary_equivalent_review":
                errors.append(
                    f"binary line classification mismatch at {file_row['path']}"
                )
        elif file_row.get("physical_lines") == "0":
            if classification != "empty_file":
                errors.append(
                    f"empty line classification mismatch at {file_row['path']}"
                )
        elif classification in {
            "binary_equivalent_review",
            "empty_file",
            "gitlink_equivalent_review",
            "symlink_equivalent_review",
        }:
            errors.append(f"text line classification mismatch at {file_row['path']}")
        if require_final and classification == "pending_line_review":
            errors.append(
                f"invalid line classification at finalization: {file_row['path']}"
            )
        values = _range_values(row, f"line coverage row {index}", errors)
        if values is not None:
            grouped[path_b64].append(values)
    for path_b64, file_row in files.items():
        physical = int(file_row["physical_lines"] or 0)
        errors.extend(
            _partition_errors(
                grouped.get(path_b64, []),
                physical,
                file_row["path"],
                outside_message="line coverage outside file",
                gap_message="line coverage gap",
                overlap_message="line coverage overlap",
            )
        )
    return errors


def _validate_batch_membership(
    rows: list[dict[str, str]],
    files: dict[str, dict[str, str]],
    symbols: dict[str, dict[str, str]],
    require_final: bool,
    review_dir: pathlib.Path,
) -> list[str]:
    if not rows:
        return ["batch membership missing at finalization"] if require_final else []
    errors: list[str] = []
    line_groups: dict[str, list[tuple[int, int]]] = defaultdict(list)
    symbol_counts: Counter[str] = Counter()
    batch_paths: dict[str, set[str]] = defaultdict(set)
    batch_lines: Counter[str] = Counter()
    batch_symbols: Counter[str] = Counter()
    line_owner_ranges: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    symbol_owners: list[tuple[str, str, str, int]] = []
    for index, row in enumerate(rows, start=2):
        label = f"batch membership row {index}"
        batch = row.get("batch", "")
        path_b64 = row.get("path_b64", "")
        role = row.get("role", "")
        if not re.fullmatch(r"BATCH-\d{3}", batch):
            errors.append(f"{label}: invalid batch ID")
        if path_b64 not in files:
            errors.append(f"{label}: unknown path")
            continue
        if row.get("path") != files[path_b64]["path"]:
            errors.append(f"{label}: path drift")
        if row.get("reviewed_object_id") != files[path_b64].get("object_id"):
            errors.append(f"{label}: reviewed_object_id drift")
        batch_paths[batch].add(path_b64)
        if role == "line_owner":
            values = _range_values(row, label, errors)
            if values is not None:
                line_groups[path_b64].append(values)
                start, end = values
                line_owner_ranges[(batch, path_b64)].append(values)
                batch_lines[batch] += 0 if start == end == 0 else end - start + 1
            if row.get("symbol_id"):
                errors.append(f"{label}: line owner must not name a symbol")
        elif role == "symbol_owner":
            symbol_id = row.get("symbol_id", "")
            if symbol_id not in symbols:
                errors.append(f"{label}: unknown symbol")
            else:
                symbol = symbols[symbol_id]
                if row.get("path_b64") != symbol.get("path_b64"):
                    errors.append(f"symbol owner path mismatch: {symbol_id}")
                if row.get("start_line") != symbol.get("start_line") or row.get(
                    "end_line"
                ) != symbol.get("end_line"):
                    errors.append(f"symbol owner range drift: {symbol_id}")
                symbol_counts[symbol_id] += 1
                batch_symbols[batch] += 1
                try:
                    symbol_start = int(symbol.get("start_line", ""))
                except ValueError:
                    symbol_start = -1
                symbol_owners.append((symbol_id, batch, path_b64, symbol_start))
        else:
            errors.append(f"{label}: invalid role")
        reviewer = row.get("reviewer", "").strip()
        verifier = row.get("verified_by", "").strip()
        if require_final and (not reviewer or not verifier):
            errors.append(f"{label}: missing second reviewer")
        elif reviewer and verifier and reviewer.casefold() == verifier.casefold():
            errors.append(f"{label}: requires a different reviewer")

    for path_b64, file_row in files.items():
        physical = int(file_row["physical_lines"] or 0)
        errors.extend(
            _partition_errors(
                line_groups.get(path_b64, []),
                physical,
                file_row["path"],
                outside_message="batch ownership outside file",
                gap_message="batch ownership gap",
                overlap_message="batch ownership overlap",
            )
        )
    for symbol_id in symbols:
        count = symbol_counts[symbol_id]
        if count == 0:
            errors.append(f"batch symbol ownership gap: {symbol_id}")
        elif count > 1:
            errors.append(f"batch symbol ownership overlap: {symbol_id}")
    for symbol_id, batch, path_b64, symbol_start in symbol_owners:
        if not any(
            start <= symbol_start <= end
            for start, end in line_owner_ranges.get((batch, path_b64), [])
        ):
            errors.append(
                f"symbol owner batch does not contain symbol start line: {symbol_id}"
            )

    for batch, path_ids in batch_paths.items():
        if not (review_dir / "batches" / f"{batch}.md").is_file():
            errors.append(f"batch manifest missing: {batch}")
        code_batch = any(
            files[path_id]["scope_tier"] in {"A", "B", "C"} for path_id in path_ids
        )
        file_limit = 20 if code_batch else 30
        line_limit = 4000 if code_batch else 6000
        if len(path_ids) > file_limit:
            errors.append(f"{batch} exceeds file limit {file_limit}: {len(path_ids)}")
        if batch_lines[batch] > line_limit:
            errors.append(
                f"{batch} exceeds line limit {line_limit}: {batch_lines[batch]}"
            )
        if batch_symbols[batch] > 150:
            errors.append(f"{batch} exceeds symbol limit 150: {batch_symbols[batch]}")
    return errors


def _validate_line_batch_foreign_keys(
    lines: list[dict[str, str]],
    memberships: list[dict[str, str]],
    require_final: bool,
) -> list[str]:
    if not memberships and not require_final:
        return []
    owners = {
        (
            row.get("batch", ""),
            row.get("path_b64", ""),
            row.get("start_line", ""),
            row.get("end_line", ""),
            row.get("reviewed_object_id", ""),
        )
        for row in memberships
        if row.get("role") == "line_owner"
    }
    errors: list[str] = []
    for row in lines:
        key = (
            row.get("batch", ""),
            row.get("path_b64", ""),
            row.get("start_line", ""),
            row.get("end_line", ""),
            row.get("reviewed_object_id", ""),
        )
        if not row.get("batch") or key not in owners:
            errors.append(
                f"line coverage batch has no matching ownership: {row.get('path', '')}"
            )
    return errors


def _manifest_value(content: str, label: str) -> str | None:
    matches = re.findall(
        rf"^- {re.escape(label)}: `([^`\r\n]*)`$", content, re.MULTILINE
    )
    return matches[0] if len(matches) == 1 else None


def _manifest_semantic_errors(
    batch: str,
    index_row: dict[str, str],
    memberships: list[dict[str, str]],
    content: str,
    *,
    require_final: bool,
    base_sha: str | None,
) -> list[str]:
    errors: list[str] = []
    comparisons = (
        ("Status", index_row.get("status", ""), "status"),
        ("Reviewer", index_row.get("reviewer", "").strip(), "reviewer"),
        (
            "Onafhankelijke verifier",
            index_row.get("verified_by", "").strip(),
            "verifier",
        ),
    )
    for label, expected, error_label in comparisons:
        actual = _manifest_value(content, label)
        if actual is None or actual.strip() != expected:
            errors.append(f"manifest {error_label} mismatch: {batch}")
    if base_sha is not None and _manifest_value(content, "Review-base") != base_sha:
        errors.append(f"manifest review-base mismatch: {batch}")

    line_owners = [row for row in memberships if row.get("role") == "line_owner"]
    symbol_owners = [row for row in memberships if row.get("role") == "symbol_owner"]
    expected_counts = (
        ("Bestanden", len({row.get("path_b64", "") for row in line_owners}), "file"),
        (
            "Fysieke regels",
            sum(
                (
                    0
                    if row.get("start_line") == row.get("end_line") == "0"
                    else int(row.get("end_line", "0"))
                    - int(row.get("start_line", "0"))
                    + 1
                )
                for row in line_owners
            ),
            "line",
        ),
        ("Python-symbolen", len(symbol_owners), "symbol"),
    )
    for label, expected, error_label in expected_counts:
        if _manifest_value(content, label) != str(expected):
            errors.append(f"manifest {error_label} count mismatch: {batch}")

    expected_scope: Counter[tuple[str, ...]] = Counter()
    for row in line_owners:
        start, end = int(row["start_line"]), int(row["end_line"])
        symbol_count = sum(
            owner.get("path_b64") == row.get("path_b64")
            and start <= int(owner.get("start_line", "-1")) <= end
            for owner in symbol_owners
        )
        expected_scope[
            (
                builder._manifest_path(row.get("path", "")),
                row.get("path_b64", ""),
                row.get("start_line", ""),
                row.get("end_line", ""),
                str(symbol_count),
                row.get("reviewed_object_id", ""),
            )
        ] += 1
    actual_scope: Counter[tuple[str, ...]] = Counter()
    try:
        scope = content.split("## Scope", 1)[1].split(
            "## Verplichte reviewchecklist", 1
        )[0]
        scope_lines = [line for line in scope.splitlines() if line]
    except IndexError:
        scope_lines = []
    expected_header = [
        "| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |",
        "|---|---|---:|---:|---|",
    ]
    scope_pattern = re.compile(
        r"^\| `([^`]*)` \| `([A-Za-z0-9+/=]+)` \| "
        r"`([0-9]+)-([0-9]+)` \| ([0-9]+) \| `([0-9a-f]+)` \|$"
    )
    scope_valid = scope_lines[:2] == expected_header
    for line in scope_lines[2:]:
        match = scope_pattern.fullmatch(line)
        if match is None:
            scope_valid = False
            continue
        actual_scope[match.groups()] += 1
    if not scope_valid or actual_scope != expected_scope:
        errors.append(f"manifest scope mismatch: {batch}")

    if require_final:
        try:
            checklist = content.split("## Verplichte reviewchecklist", 1)[1].split(
                "## Bevindingen", 1
            )[0]
        except IndexError:
            checklist = ""
        expected_checklist = Counter(
            f"- [x] {item}" for item in builder.MANIFEST_CHECKLIST_ITEMS
        )
        actual_checklist = Counter(
            line for line in checklist.splitlines() if line.startswith("- [")
        )
        if actual_checklist != expected_checklist:
            errors.append(f"manifest final checklist incomplete: {batch}")
        try:
            result = content.split("## Resultaat", 1)[1].strip()
        except IndexError:
            result = ""
        if not result or result == "Nog niet uitgevoerd.":
            errors.append(f"manifest final result incomplete: {batch}")
    return errors


def _validate_batch_index(
    rows: list[dict[str, str]],
    memberships: list[dict[str, str]],
    review_dir: pathlib.Path,
    require_final: bool,
    *,
    base_sha: str | None = None,
) -> list[str]:
    errors: list[str] = []
    actual_ids = [row.get("batch", "") for row in rows]
    for batch in sorted(_duplicates(actual_ids)):
        errors.append(f"duplicate batch index row: {batch}")
    actual = {row.get("batch", ""): row for row in rows}
    expected_ids = {row.get("batch", "") for row in memberships if row.get("batch")}
    for batch in sorted(expected_ids - actual.keys()):
        errors.append(f"batch index missing: {batch}")
    for batch in sorted(actual.keys() - expected_ids):
        errors.append(f"unexpected batch index: {batch}")

    numbered_ids = sorted(expected_ids)
    contiguous_ids = [
        f"BATCH-{number:03d}" for number in range(1, len(expected_ids) + 1)
    ]
    if numbered_ids != contiguous_ids:
        errors.append(
            "batch IDs are not contiguous: "
            f"expected {contiguous_ids}, got {numbered_ids}"
        )

    manifest_dir = review_dir / "batches"
    manifest_names = {path.name for path in manifest_dir.glob("BATCH-*.md")}
    expected_names = {f"{batch}.md" for batch in expected_ids}
    for name in sorted(manifest_names - expected_names):
        errors.append(f"unexpected batch manifest filename: {name}")
    for name in sorted(expected_names - manifest_names):
        errors.append(f"batch manifest missing: {name.removesuffix('.md')}")

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    path_reviewers: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for membership in memberships:
        grouped[membership.get("batch", "")].append(membership)
        path_reviewers[membership.get("path_b64", "")].add(
            (
                membership.get("reviewer", "").strip(),
                membership.get("verified_by", "").strip(),
            )
        )
    for path_b64, reviewer_pairs in path_reviewers.items():
        if len(reviewer_pairs) > 1:
            path = next(
                (
                    row.get("path", path_b64)
                    for row in memberships
                    if row.get("path_b64") == path_b64
                ),
                path_b64,
            )
            errors.append(f"multi-batch file has inconsistent reviewers: {path}")
    for batch in sorted(expected_ids & actual.keys()):
        row = actual[batch]
        status = row.get("status", "")
        if status not in STATUSES:
            errors.append(f"invalid status in batch index row: {batch}")
        if require_final and status != "verified":
            errors.append(f"batch index row is not final: {batch}")
        reviewer = row.get("reviewer", "").strip()
        verifier = row.get("verified_by", "").strip()
        if status == "verified" and (not reviewer or not verifier):
            errors.append(f"batch index row requires two reviewers: {batch}")
        elif reviewer and verifier and reviewer.casefold() == verifier.casefold():
            errors.append(f"batch index row requires a different reviewer: {batch}")
        for membership in grouped[batch]:
            if membership.get("reviewer", "").strip() != reviewer:
                errors.append(f"reviewer differs between index and membership: {batch}")
            if membership.get("verified_by", "").strip() != verifier:
                errors.append(
                    f"verified_by differs between index and membership: {batch}"
                )

        manifest = review_dir / "batches" / f"{batch}.md"
        try:
            content = manifest.read_bytes()
        except OSError:
            continue
        decoded = ""
        if not content:
            errors.append(f"batch manifest is empty: {batch}")
        else:
            try:
                decoded = content.decode("utf-8")
                heading = decoded.splitlines()[0]
            except UnicodeDecodeError:
                heading = ""
            if heading != f"# {batch}":
                errors.append(f"batch manifest heading mismatch: {batch}")
        for section in builder.MANIFEST_REQUIRED_SECTIONS:
            if section not in decoded:
                errors.append(f"batch manifest section missing: {batch}: {section}")
        if row.get("manifest_sha256") != hashlib.sha256(content).hexdigest():
            errors.append(f"batch manifest_sha256 drift: {batch}")
        membership_digest = builder.canonical_membership_sha256(grouped[batch])
        if row.get("membership_sha256") != membership_digest:
            errors.append(f"batch membership_sha256 drift: {batch}")
        manifest_digest = re.search(r"Membership-SHA256: `([0-9a-f]{64})`", decoded)
        if manifest_digest is None or manifest_digest.group(1) != membership_digest:
            errors.append(f"batch manifest membership digest mismatch: {batch}")
        errors.extend(
            _manifest_semantic_errors(
                batch,
                row,
                grouped[batch],
                decoded,
                require_final=require_final,
                base_sha=base_sha,
            )
        )
    return errors


def _validate_untracked_rows(
    rows: list[dict[str, str]],
    expected: list[dict[str, str]],
    *,
    require_final: bool,
    comparison: str | None,
) -> list[str]:
    errors = _status_errors(rows, "untracked", require_final=require_final)
    actual_ids = [row.get("path_b64", "") for row in rows]
    for path_b64 in sorted(_duplicates(actual_ids)):
        errors.append(f"duplicate untracked row: {path_b64}")
    actual = {row.get("path_b64", ""): row for row in rows}
    expected_map = {row["path_b64"]: row for row in expected} if comparison else {}
    if comparison:
        for path_b64 in sorted(expected_map.keys() - actual.keys()):
            prefix = "frozen " if comparison == "frozen" else ""
            errors.append(
                f"{prefix}untracked path missing: {expected_map[path_b64]['path']}"
            )
        for path_b64 in sorted(actual.keys() - expected_map.keys()):
            prefix = "unknown frozen" if comparison == "frozen" else "unknown"
            errors.append(
                f"{prefix} untracked row: {actual[path_b64].get('path', path_b64)}"
            )
    immutable = [
        "path",
        "path_b64",
        "source_root",
        "content_sha256",
        "file_type",
        "bytes",
        "scope_tier",
        "owner",
        "notes",
    ]
    if comparison == "frozen":
        immutable.append("captured_at")
    for path_b64, row in actual.items():
        _decode_path(path_b64, f"untracked {row.get('path', path_b64)}", errors)
        if comparison and path_b64 in expected_map:
            for field in immutable:
                if row.get(field) != expected_map[path_b64][field]:
                    prefix = "frozen " if comparison == "frozen" else ""
                    errors.append(
                        f"{prefix}untracked {field} drift at "
                        f"{expected_map[path_b64]['path']}"
                    )
        status = row.get("status", "")
        if status == "out_of_scope":
            errors.append(
                f"untracked out_of_scope is forbidden: {row.get('path', path_b64)}"
            )
        if status not in STATUSES:
            errors.append(
                f"invalid status in untracked row at {row.get('path', path_b64)}"
            )
        reviewer = row.get("reviewer", "").strip()
        verifier = row.get("verified_by", "").strip()
        if (
            status == "verified"
            and reviewer
            and verifier
            and reviewer.casefold() == verifier.casefold()
        ):
            errors.append(
                f"untracked row requires a different reviewer: {row.get('path', '')}"
            )
        source_root = row.get("source_root", "")
        if not source_root or not pathlib.Path(source_root).is_absolute():
            errors.append(f"untracked source_root is invalid at {row.get('path', '')}")
        captured_at = row.get("captured_at", "")
        try:
            datetime.datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"untracked captured_at is invalid at {row.get('path', '')}")
        digest = row.get("content_sha256", "")
        if digest not in {
            "NOT_SCANNED_SECRET",
            "NOT_SCANNED_SPECIAL",
            "NOT_SCANNED_SYMLINK",
            "UNREADABLE",
        } and not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(
                f"untracked content_sha256 is invalid at {row.get('path', '')}"
            )
    return errors


def _read_frozen_untracked(
    repo: pathlib.Path,
    review: pathlib.Path,
    scope_sha: str,
    errors: list[str],
) -> list[dict[str, str]] | None:
    try:
        full_sha = builder.verify_full_commit_sha(repo, scope_sha)
    except ValueError as exc:
        errors.append(str(exc).replace("REVIEW_BASE_SHA", "SCOPE_SHA"))
        return None
    try:
        relative_review = review.resolve().relative_to(repo).as_posix()
    except ValueError:
        errors.append("review directory must be inside the repository for SCOPE_SHA")
        return None
    git_path = f"{relative_review}/scope/untracked-inventory.csv"
    try:
        raw = builder._git(repo, ["show", f"{full_sha}:{git_path}"])
        text = raw.decode("utf-8")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        errors.append(f"frozen untracked inventory missing or unreadable at {full_sha}")
        return None
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != builder.UNTRACKED_FIELDS:
        errors.append("invalid frozen untracked inventory header")
        return None
    rows: list[dict[str, str]] = []
    for line_number, raw_row in enumerate(reader, start=2):
        if None in raw_row or any(value is None for value in raw_row.values()):
            errors.append(
                f"malformed row in frozen untracked inventory at line {line_number}"
            )
            continue
        rows.append(
            {field: raw_row.get(field) or "" for field in builder.UNTRACKED_FIELDS}
        )
    return rows


def _validate_review_infrastructure(
    repo: pathlib.Path,
    rows: list[dict[str, str]],
    require_final: bool,
) -> list[str]:
    errors = _status_errors(rows, "review infrastructure", require_final=require_final)
    if require_final and not rows:
        errors.append("review infrastructure missing at finalization")
        return errors
    actual_paths = {row.get("path", "") for row in rows}
    for path in sorted(REVIEW_TOOL_PATHS - actual_paths):
        errors.append(f"review infrastructure tool missing: {path}")
    for path in sorted(actual_paths - REVIEW_TOOL_PATHS):
        errors.append(f"unexpected review infrastructure tool: {path}")
    tooling_shas = {row.get("tooling_sha", "") for row in rows}
    if rows and len(tooling_shas) != 1:
        errors.append("review infrastructure must use one TOOLING_SHA")
    for path in sorted(_duplicates([row.get("path", "") for row in rows])):
        errors.append(f"duplicate review infrastructure path: {path}")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("status") != "verified":
            errors.append(
                f"review infrastructure row must be verified: {row.get('path', '')}"
            )
        if row.get("test_result") != "pass":
            errors.append(
                f"review infrastructure test_result must be pass: {row.get('path', '')}"
            )
        grouped[row.get("tooling_sha", "")].append(row)
    for requested_sha, commit_rows in grouped.items():
        try:
            tooling_sha = builder.verify_full_commit_sha(repo, requested_sha)
        except ValueError as exc:
            errors.append(f"review infrastructure requires full commit SHA: {exc}")
            continue
        tree = builder._tree_entries(repo, tooling_sha)
        by_path: dict[str, dict[str, bytes | str]] = {}
        for entry in tree:
            raw_path = entry["raw_path"]
            assert isinstance(raw_path, bytes)
            path, _ = builder._path_fields(raw_path)
            by_path[path] = entry
        with builder._CatFileReader(repo) as reader:
            for row in commit_rows:
                path = row.get("path", "")
                entry = by_path.get(path)
                if entry is None or entry.get("object_type") != "blob":
                    errors.append(
                        f"review infrastructure path missing from tooling commit: {path}"
                    )
                    continue
                object_id = str(entry["object_id"])
                if row.get("blob_sha") != object_id:
                    errors.append(f"review infrastructure blob drift: {path}")
                _, content = reader.read(object_id)
                expected_lines = str(len(content.splitlines()))
                if row.get("physical_lines") != expected_lines:
                    errors.append(f"review infrastructure line drift: {path}")
    return errors


def _validate_verified_file_children(
    files: list[dict[str, str]],
    symbols: list[dict[str, str]],
    lines: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    symbols_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    lines_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in symbols:
        symbols_by_path[row.get("path_b64", "")].append(row)
    for row in lines:
        lines_by_path[row.get("path_b64", "")].append(row)
    for file_row in files:
        if file_row.get("status") != "verified":
            continue
        path_b64 = file_row.get("path_b64", "")
        if any(row.get("status") != "verified" for row in symbols_by_path[path_b64]):
            errors.append(
                f"verified file has unverified symbol: {file_row.get('path', '')}"
            )
        if any(row.get("status") != "verified" for row in lines_by_path[path_b64]):
            errors.append(
                f"verified file has unverified line coverage: {file_row.get('path', '')}"
            )
    return errors


def _validate_exclusions(
    files: list[dict[str, str]],
    symbols: list[dict[str, str]],
    lines: list[dict[str, str]],
    exclusions: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    files_by_path = {row.get("path_b64", ""): row for row in files}
    exclusions_by_path: dict[str, dict[str, str]] = {}
    for path_b64 in _duplicates([row.get("path_b64", "") for row in exclusions]):
        errors.append(f"duplicate exclusion: {path_b64}")
    for row in exclusions:
        path_b64 = row.get("path_b64", "")
        exclusions_by_path[path_b64] = row
        file_row = files_by_path.get(path_b64)
        if file_row is None or row.get("path") != file_row.get("path"):
            errors.append(f"exclusion path/path_b64 mismatch: {row.get('path', '')}")
        if not row.get("reason", "").strip():
            errors.append(
                f"out_of_scope exclusion requires reason: {row.get('path', '')}"
            )
        if not row.get("approved_by", "").strip():
            errors.append(
                f"out_of_scope exclusion requires approval: {row.get('path', '')}"
            )

    children_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in [*symbols, *lines]:
        children_by_path[row.get("path_b64", "")].append(row)
    for file_row in files:
        path_b64 = file_row.get("path_b64", "")
        excluded = file_row.get("status") == "out_of_scope"
        if excluded and file_row.get("scope_tier") != "F":
            errors.append(
                f"out_of_scope is not permitted for scope tier "
                f"{file_row.get('scope_tier', '')}: {file_row.get('path', '')}"
            )
        if excluded and path_b64 not in exclusions_by_path:
            errors.append(
                f"out_of_scope file lacks exclusion: {file_row.get('path', '')}"
            )
        child_statuses = [row.get("status") for row in children_by_path[path_b64]]
        if excluded and any(status != "out_of_scope" for status in child_statuses):
            errors.append(
                f"out_of_scope file has non-excluded child: {file_row.get('path', '')}"
            )
        if not excluded and any(status == "out_of_scope" for status in child_statuses):
            errors.append(
                f"out_of_scope child has non-excluded parent: {file_row.get('path', '')}"
            )
    for label, rows in (("symbol", symbols), ("line coverage", lines)):
        for row in rows:
            if (
                row.get("status") == "out_of_scope"
                and row.get("path_b64") not in exclusions_by_path
            ):
                errors.append(
                    f"out_of_scope {label} lacks exclusion: {row.get('path', '')}"
                )
    return errors


def _validate_findings(
    rows: list[dict[str, str]],
    files: dict[str, dict[str, str]],
    inventory_rows: list[dict[str, str]],
    require_final: bool,
) -> list[str]:
    errors: list[str] = []
    ids = [row.get("finding_id", "") for row in rows]
    for finding_id in _duplicates(ids):
        errors.append(f"duplicate finding ID: {finding_id}")
    findings = {row.get("finding_id", ""): row for row in rows if row.get("finding_id")}
    display_paths: dict[str, list[dict[str, str]]] = defaultdict(list)
    for file_row in files.values():
        display_paths[file_row["path"]].append(file_row)
    mandatory = [
        "finding_id",
        "priority",
        "certainty",
        "review_area",
        "title",
        "path",
        "start_line",
        "end_line",
        "evidence",
        "reproduction",
        "recommendation",
        "status",
        "reviewer",
    ]
    for row in rows:
        finding_id = row.get("finding_id", "<missing>")
        for field in mandatory:
            if not row.get(field, "").strip():
                errors.append(f"finding missing {field}: {finding_id}")
        if row.get("priority") not in PRIORITIES:
            errors.append(f"invalid priority for finding {finding_id}")
        if row.get("certainty") not in CERTAINTIES:
            errors.append(f"invalid certainty for finding {finding_id}")
        if row.get("status") not in STATUSES:
            errors.append(f"invalid finding status for {finding_id}")
        errors.extend(_reviewer_errors(row, f"finding {finding_id}"))
        if require_final and row.get("status") != "verified":
            errors.append(f"finding is not verified: {finding_id}")
        candidates = display_paths.get(row.get("path", ""), [])
        if len(candidates) != 1:
            errors.append(f"finding has unknown path: {finding_id}")
            continue
        values = _range_values(row, f"finding {finding_id}", errors)
        if values is None:
            continue
        start, end = values
        physical = int(candidates[0]["physical_lines"] or 0)
        if physical == 0:
            if (start, end) != (0, 0):
                errors.append(f"finding range outside file: {finding_id}")
        elif start < 1 or end > physical:
            errors.append(f"finding range outside file: {finding_id}")

    references: set[str] = set()
    for inventory_row in inventory_rows:
        row_references = _split_ids(inventory_row.get("finding_ids", ""))
        references.update(row_references)
        for finding_id in row_references & findings.keys():
            if inventory_row.get("path") != findings[finding_id].get("path"):
                errors.append(
                    f"finding reference path mismatch: {finding_id} at "
                    f"{inventory_row.get('path', '')}"
                )
    for reference in sorted(references - findings.keys()):
        errors.append(f"unknown finding reference: {reference}")
    for finding_id in sorted(findings.keys() - references):
        errors.append(f"finding is not referenced by inventory: {finding_id}")
    return errors


def validate_inventory(
    repo_root: pathlib.Path | str,
    base_sha: str,
    review_dir: pathlib.Path | str,
    require_final: bool = False,
    *,
    untracked_root: pathlib.Path | str | None = None,
    scope_sha: str | None = None,
) -> list[str]:
    repo = pathlib.Path(repo_root).resolve()
    review = pathlib.Path(review_dir)
    scope = review / "scope"
    errors: list[str] = []
    expected = builder.build_inventory(
        repo,
        base_sha,
        untracked_root=untracked_root,
        include_untracked=not require_final and scope_sha is None,
    )

    files = _read_csv(scope / "file-inventory.csv", builder.FILE_FIELDS, errors)
    symbols = _read_csv(scope / "symbol-inventory.csv", builder.SYMBOL_FIELDS, errors)
    lines = _read_csv(scope / "line-coverage.csv", builder.LINE_COVERAGE_FIELDS, errors)
    batches = _read_csv(
        scope / "batch-membership.csv", builder.BATCH_MEMBERSHIP_FIELDS, errors
    )
    batch_index = _read_csv(
        scope / "batch-index.csv", builder.BATCH_INDEX_FIELDS, errors
    )
    infrastructure = _read_csv(
        scope / "review-infrastructure.csv",
        builder.REVIEW_INFRASTRUCTURE_FIELDS,
        errors,
    )
    untracked = _read_csv(
        scope / "untracked-inventory.csv", builder.UNTRACKED_FIELDS, errors
    )
    exclusions = _read_csv(scope / "exclusions.csv", builder.EXCLUSION_FIELDS, errors)
    findings = _read_csv(
        review / "findings" / "findings.csv",
        FINDING_FIELDS,
        errors,
        required=False,
    )

    file_errors, file_map = _validate_file_rows(files, expected["files"], require_final)
    errors.extend(file_errors)
    symbol_errors, symbol_map = _validate_symbol_rows(
        symbols,
        expected["symbols"],
        set(file_map),
        require_final,
    )
    errors.extend(symbol_errors)
    errors.extend(_validate_line_coverage(lines, file_map, require_final))
    errors.extend(
        _validate_batch_membership(
            batches,
            file_map,
            symbol_map,
            require_final,
            review,
        )
    )
    errors.extend(_validate_line_batch_foreign_keys(lines, batches, require_final))
    errors.extend(
        _validate_batch_index(
            batch_index,
            batches,
            review,
            require_final,
            base_sha=base_sha,
        )
    )
    comparison: str | None
    if scope_sha is not None:
        expected_untracked: list[dict[str, str]] = []
        comparison = None
        frozen = _read_frozen_untracked(repo, review, scope_sha, errors)
        if frozen is not None:
            expected_untracked = frozen
            comparison = "frozen"
    elif require_final:
        expected_untracked = []
        comparison = None
        errors.append("SCOPE_SHA is required for final validation")
    else:
        expected_untracked = expected["untracked"]
        comparison = "live"
        try:
            review_prefix = (
                review.resolve()
                .relative_to(
                    pathlib.Path(untracked_root).resolve()
                    if untracked_root is not None
                    else repo
                )
                .as_posix()
                .encode("utf-8")
            )
        except ValueError:
            review_prefix = b""
        if review_prefix:
            expected_untracked = [
                row
                for row in expected_untracked
                if not (
                    base64.b64decode(row["path_b64"]) == review_prefix
                    or base64.b64decode(row["path_b64"]).startswith(
                        review_prefix + b"/"
                    )
                )
            ]
    errors.extend(
        _validate_untracked_rows(
            untracked,
            expected_untracked,
            require_final=require_final,
            comparison=comparison,
        )
    )
    errors.extend(_validate_review_infrastructure(repo, infrastructure, require_final))
    errors.extend(_validate_verified_file_children(files, symbols, lines))
    errors.extend(
        _validate_findings(
            findings,
            file_map,
            [*files, *symbols, *lines],
            require_final,
        )
    )

    errors.extend(_validate_exclusions(files, symbols, lines, exclusions))
    return errors


def _parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--review-dir", required=True, type=pathlib.Path)
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--untracked-root", type=pathlib.Path)
    parser.add_argument("--scope-sha")
    parser.add_argument("--require-final", action="store_true")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    args = _parse_args(arguments)
    try:
        errors = validate_inventory(
            args.repo_root,
            args.base_sha,
            args.review_dir,
            require_final=args.require_final,
            untracked_root=args.untracked_root,
            scope_sha=args.scope_sha,
        )
    except (OSError, ValueError) as exc:
        print(f"inventory validation failed: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Inventory validation failed with {len(errors)} error(s).")
        return 1
    print("Inventory validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
