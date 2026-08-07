from __future__ import annotations

import base64
import copy
import csv
import hashlib
import importlib.util
import itertools
import json
import os
import subprocess
import unicodedata
from pathlib import Path
from types import ModuleType

import pytest

TOOLS_DIR = Path(__file__).parent
REVIEW_TOOL_PATHS = (
    "docs/reviews/2026-08-07-line-by-line/tools/build_inventory.py",
    "docs/reviews/2026-08-07-line-by-line/tools/test_inventory_tools.py",
    "docs/reviews/2026-08-07-line-by-line/tools/validate_inventory.py",
)
BATCH_INDEX_FIELDS = [
    "batch",
    "status",
    "reviewer",
    "verified_by",
    "manifest_sha256",
    "membership_sha256",
]


def load_tool(name: str) -> ModuleType:
    path = TOOLS_DIR / f"{name}.py"
    assert path.is_file(), f"inventory tool is not implemented: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inventory_tools() -> tuple[ModuleType, ModuleType]:
    if not all(
        (TOOLS_DIR / f"{name}.py").is_file()
        for name in ("build_inventory", "validate_inventory")
    ):
        pytest.skip("inventory tools are not implemented yet")
    return load_tool("build_inventory"), load_tool("validate_inventory")


def test_inventory_tools_are_implemented() -> None:
    missing = [
        f"{name}.py"
        for name in ("build_inventory", "validate_inventory")
        if not (TOOLS_DIR / f"{name}.py").is_file()
    ]
    assert missing == []


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_bytes(repo: Path, *args: str, input_bytes: bytes = b"") -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        check=True,
        capture_output=True,
    )
    return result.stdout.strip()


def commit_raw_tree(repo: Path, raw_paths: list[bytes]) -> str:
    blob = git_bytes(repo, "hash-object", "-w", "--stdin", input_bytes=b"content\n")
    entries = b"".join(
        b"100644 blob " + blob + b"\t" + path + b"\0" for path in sorted(raw_paths)
    )
    tree = git_bytes(repo, "mktree", "-z", input_bytes=entries).decode("ascii")
    return git_bytes(repo, "commit-tree", tree, input_bytes=b"raw paths\n").decode(
        "ascii"
    )


@pytest.fixture
def sample_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")

    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text(
        """def marker(function):
    return function

class Service:
    @property
    def label(self):
        return "service"

    @label.setter
    def label(self, value):
        self._label = value

    @staticmethod
    def normalize(value):
        return value

    @classmethod
    async def create(cls):
        return cls()

    @marker
    async def execute(self):
        def nested():
            return 1
        return nested()

def top_level(value):
    return value

def repeated():
    return 1

def repeated():
    return 2

first = lambda value: value; second = lambda value: value + 1
""",
        encoding="utf-8",
    )
    (repo / "path with spaces.txt").write_text("frozen\n", encoding="utf-8")
    (repo / "duplicate.txt").write_text("frozen\n", encoding="utf-8")
    (repo / "empty.txt").write_bytes(b"")
    (repo / "no-final-lf.txt").write_bytes(b"one")
    (repo / "crlf.txt").write_bytes(b"one\r\ntwo\r\n")
    (repo / "asset.bin").write_bytes(b"review\x00binary")
    (repo / ".gitignore").write_text("ignored-secret.env\n", encoding="utf-8")
    (repo / "link.txt").symlink_to("path with spaces.txt")
    (repo / "large.dat").write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:" + "0" * 64 + "\nsize 123\n",
        encoding="ascii",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "fixture")
    (repo / "visible-untracked.txt").write_text("do not read me\n", encoding="utf-8")
    (repo / "ignored-secret.env").write_text("SECRET=never-read\n", encoding="utf-8")
    return repo, git(repo, "rev-parse", "HEAD")


def rows_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["path"]: row for row in rows}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_review(
    builder: ModuleType,
    repo: Path,
    base_sha: str,
    review_dir: Path,
) -> dict[str, list[dict[str, str]]]:
    inventory = builder.build_inventory(repo, base_sha)
    builder.write_inventory(inventory, review_dir / "scope")
    return inventory


def commit_tooling_snapshot(repo: Path) -> str:
    for path_string in REVIEW_TOOL_PATHS:
        path = repo / path_string
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'"""Fixture for {path.name}."""\n', encoding="utf-8")
    git(repo, "add", *REVIEW_TOOL_PATHS)
    git(repo, "commit", "-qm", "tooling fixture")
    return git(repo, "rev-parse", "HEAD")


def tooling_rows(
    builder: ModuleType, repo: Path, tooling_sha: str
) -> list[dict[str, str]]:
    files = rows_by_path(builder.build_inventory(repo, tooling_sha)["files"])
    return [
        {
            "path": path,
            "tooling_sha": tooling_sha,
            "blob_sha": files[path]["object_id"],
            "physical_lines": files[path]["physical_lines"],
            "status": "verified",
            "reviewer": "reviewer-a",
            "verified_by": "reviewer-b",
            "test_result": "pass",
            "notes": "fixture",
        }
        for path in REVIEW_TOOL_PATHS
    ]


def canonical_membership_sha256(builder: ModuleType, rows: list[dict[str, str]]) -> str:
    normalized = [
        {field: row.get(field, "") for field in builder.BATCH_MEMBERSHIP_FIELDS}
        for row in rows
    ]
    normalized.sort(
        key=lambda row: tuple(row[field] for field in builder.BATCH_MEMBERSHIP_FIELDS)
    )
    payload = json.dumps(
        normalized, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def freeze_untracked_scope(
    builder: ModuleType, repo: Path, base_sha: str
) -> tuple[Path, dict[str, list[dict[str, str]]], str]:
    review_dir = repo / "review-fixture"
    inventory = build_review(builder, repo, base_sha, review_dir)
    frozen_path = review_dir / "scope" / "untracked-inventory.csv"
    git(repo, "add", frozen_path.relative_to(repo).as_posix())
    git(repo, "commit", "-qm", "freeze untracked scope")
    return review_dir, inventory, git(repo, "rev-parse", "HEAD")


def synthetic_inventory(
    builder: ModuleType,
    specs: list[tuple[str, str, int, bool]],
    symbol_starts: dict[str, list[int]] | None = None,
) -> dict[str, list[dict[str, str]]]:
    files: list[dict[str, str]] = []
    lines: list[dict[str, str]] = []
    symbols: list[dict[str, str]] = []
    for number, (path, tier, physical_lines, binary) in enumerate(specs, start=1):
        raw_path = path.encode("utf-8")
        path_b64 = base64.b64encode(raw_path).decode("ascii")
        object_id = f"{number:040x}"
        files.append(
            {
                "path": path,
                "path_b64": path_b64,
                "git_mode": "100644",
                "object_type": "blob",
                "object_id": object_id,
                "file_type": "application/octet-stream" if binary else "text/plain",
                "bytes": str(physical_lines),
                "physical_lines": "" if binary else str(physical_lines),
                "logical_lines": "" if binary else str(physical_lines),
                "scope_tier": tier,
                "status": "blocked" if path.endswith("blocked.py") else "pending",
                "reviewer": "",
                "verified_by": "",
                "reviewed_at": "",
                "finding_ids": "F-001" if path.endswith("blocked.py") else "",
                "notes": "fixture",
            }
        )
        start = "0" if binary or physical_lines == 0 else "1"
        end = "0" if binary or physical_lines == 0 else str(physical_lines)
        lines.append(
            {
                "path": path,
                "path_b64": path_b64,
                "reviewed_object_id": object_id,
                "start_line": start,
                "end_line": end,
                "classification": (
                    "binary_equivalent_review"
                    if binary
                    else "empty_file" if physical_lines == 0 else "pending_line_review"
                ),
                "batch": "",
                "status": files[-1]["status"],
                "reviewer": "",
                "verified_by": "",
                "finding_ids": files[-1]["finding_ids"],
                "notes": "fixture-line",
            }
        )
        for symbol_number, start_line in enumerate(
            (symbol_starts or {}).get(path, []), start=1
        ):
            symbols.append(
                {
                    "symbol_id": f"SYM-{number:04d}-{symbol_number:04d}",
                    "path": path,
                    "path_b64": path_b64,
                    "qualified_name": f"symbol_{symbol_number}",
                    "kind": "function",
                    "start_line": str(start_line),
                    "start_col": "0",
                    "end_line": str(start_line),
                    "end_col": "1",
                    "parent_symbol": "",
                    "decorators": "",
                    "complexity": "1",
                    "status": "pending",
                    "reviewer": "",
                    "verified_by": "",
                    "test_ids": "",
                    "finding_ids": "",
                    "notes": "",
                }
            )
    return {
        "files": files,
        "symbols": symbols,
        "line_coverage": lines,
        "batch_membership": [],
        "batch_index": [],
        "review_infrastructure": [],
        "untracked": [],
        "exclusions": [],
        "findings": [],
    }


def test_writer_creates_every_scope_schema(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo
    scope_dir = tmp_path / "review" / "scope"

    builder.write_inventory(builder.build_inventory(repo, base_sha), scope_dir)

    assert {
        "file-inventory.csv",
        "symbol-inventory.csv",
        "line-coverage.csv",
        "batch-membership.csv",
        "batch-index.csv",
        "review-infrastructure.csv",
        "untracked-inventory.csv",
        "exclusions.csv",
    } <= {path.name for path in scope_dir.iterdir()}


@pytest.mark.parametrize(
    ("field", "replacement", "expected_error"),
    [
        ("tooling_sha", "short", "full commit SHA"),
        ("blob_sha", "0" * 40, "review infrastructure blob drift"),
        ("physical_lines", "999", "review infrastructure line drift"),
    ],
)
def test_validator_checks_review_infrastructure_against_tooling_commit(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    field: str,
    replacement: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    tooling_sha = commit_tooling_snapshot(repo)
    infrastructure = tooling_rows(builder, repo, tooling_sha)
    infrastructure[0][field] = replacement
    write_csv(
        review_dir / "scope" / "review-infrastructure.csv",
        builder.REVIEW_INFRASTRUCTURE_FIELDS,
        infrastructure,
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_validator_rejects_duplicate_review_infrastructure_path(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    tooling_sha = commit_tooling_snapshot(repo)
    rows = tooling_rows(builder, repo, tooling_sha)
    write_csv(
        review_dir / "scope" / "review-infrastructure.csv",
        builder.REVIEW_INFRASTRUCTURE_FIELDS,
        [*rows, dict(rows[0])],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("duplicate review infrastructure path" in error for error in errors)


def test_every_tracked_path_has_exactly_one_file_row(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)

    expected = git(repo, "ls-tree", "-r", "--name-only", base_sha).splitlines()
    actual = [row["path"] for row in inventory["files"]]
    assert sorted(actual) == sorted(expected)
    assert len(actual) == len(set(actual))


def test_abbreviated_review_base_sha_is_rejected(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    with pytest.raises(ValueError, match="full commit SHA"):
        builder.build_inventory(repo, base_sha[:12])


def test_paths_with_spaces_are_preserved(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)

    assert "path with spaces.txt" in rows_by_path(inventory["files"])


def test_raw_git_paths_are_lossless(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "raw-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    raw_paths = [
        b"-leading.txt",
        b"comma,name.txt",
        b'quote"name.txt',
        b"tab\tname.txt",
        b"newline\nname.txt",
        "café.txt".encode(),
        unicodedata.normalize("NFD", "café.txt").encode(),
        b"Case.txt",
        b"case.txt",
        b"invalid-\xff.txt",
    ]
    base_sha = commit_raw_tree(repo, raw_paths)

    inventory = builder.build_inventory(repo, base_sha)

    actual = {base64.b64decode(row["path_b64"]) for row in inventory["files"]}
    assert actual == set(raw_paths)


def test_file_rows_use_the_frozen_blob(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo
    expected_blob = git(repo, "rev-parse", f"{base_sha}:path with spaces.txt")
    (repo / "path with spaces.txt").write_text("working tree drift\n", encoding="utf-8")

    inventory = builder.build_inventory(repo, base_sha)
    row = rows_by_path(inventory["files"])["path with spaces.txt"]

    assert row["object_id"] == expected_blob
    assert row["physical_lines"] == "1"


def test_file_metadata_comes_from_git_objects(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)
    rows = rows_by_path(inventory["files"])

    assert rows["path with spaces.txt"]["git_mode"] == "100644"
    assert rows["path with spaces.txt"]["object_type"] == "blob"
    assert rows["path with spaces.txt"]["bytes"] == "7"
    assert rows["link.txt"]["git_mode"] == "120000"
    assert rows["link.txt"]["bytes"] == str(len(b"path with spaces.txt"))
    assert rows["large.dat"]["file_type"] == "application/vnd.git-lfs.pointer"


def test_duplicate_blobs_keep_separate_file_rows(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    rows = rows_by_path(builder.build_inventory(repo, base_sha)["files"])

    assert (
        rows["duplicate.txt"]["object_id"] == rows["path with spaces.txt"]["object_id"]
    )
    assert rows["duplicate.txt"]["path_b64"] != rows["path with spaces.txt"]["path_b64"]


def test_gitlink_is_recorded_without_content_scan(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "gitlink-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(repo, "add", "seed.txt")
    git(repo, "commit", "-qm", "seed")
    target = git(repo, "rev-parse", "HEAD").encode("ascii")
    tree = git_bytes(
        repo,
        "mktree",
        "-z",
        input_bytes=b"160000 commit " + target + b"\tvendor-module\0",
    ).decode("ascii")
    base_sha = git_bytes(repo, "commit-tree", tree, input_bytes=b"gitlink\n").decode(
        "ascii"
    )

    row = builder.build_inventory(repo, base_sha)["files"][0]

    assert row["git_mode"] == "160000"
    assert row["object_type"] == "commit"
    assert row["object_id"] == target.decode("ascii")
    assert row["bytes"] == ""
    assert row["physical_lines"] == ""
    assert "gitlink_review_required" in row["notes"]


def test_text_line_count_handles_empty_no_lf_crlf(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    rows = rows_by_path(builder.build_inventory(repo, base_sha)["files"])

    assert rows["empty.txt"]["physical_lines"] == "0"
    assert rows["no-final-lf.txt"]["physical_lines"] == "1"
    assert rows["crlf.txt"]["physical_lines"] == "2"


def test_python_inventory_covers_all_function_kinds(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)
    symbols = [row for row in inventory["symbols"] if row["path"] == "src/module.py"]
    by_name_kind = {(row["qualified_name"], row["kind"]): row for row in symbols}

    module = by_name_kind[("src.module", "module")]
    service = by_name_kind[("Service", "class")]
    execute = by_name_kind[("Service.execute", "async_method")]
    assert service["parent_symbol"] == module["symbol_id"]
    assert (
        by_name_kind[("Service.label", "property_getter")]["parent_symbol"]
        == service["symbol_id"]
    )
    assert (
        by_name_kind[("Service.label", "property_setter")]["parent_symbol"]
        == service["symbol_id"]
    )
    assert ("Service.normalize", "staticmethod") in by_name_kind
    assert ("Service.create", "async_classmethod") in by_name_kind
    assert execute["parent_symbol"] == service["symbol_id"]
    nested = by_name_kind[("Service.execute.nested", "nested_function")]
    assert nested["parent_symbol"] == execute["symbol_id"]
    assert ("top_level", "function") in by_name_kind
    assert sum(row["qualified_name"] == "repeated" for row in symbols) == 2
    lambdas = [row for row in symbols if row["kind"] == "lambda"]
    assert len(lambdas) == 2
    assert len({(row["start_line"], row["start_col"]) for row in lambdas}) == 2


def test_decorated_symbol_starts_at_earliest_decorator(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    symbols = builder.build_inventory(repo, base_sha)["symbols"]
    execute = next(row for row in symbols if row["qualified_name"] == "Service.execute")

    assert execute["decorators"] == "marker"
    assert execute["start_line"] == "21"
    assert execute["start_col"] == "4"


def test_python_syntax_error_is_a_blocking_inventory_finding(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "syntax-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    git(repo, "add", "broken.py")
    git(repo, "commit", "-qm", "syntax fixture")
    base_sha = git(repo, "rev-parse", "HEAD")

    inventory = builder.build_inventory(repo, base_sha)
    row = rows_by_path(inventory["files"])["broken.py"]

    assert row["status"] == "blocked"
    assert row["finding_ids"].startswith("INV-SYNTAX-")
    assert "blocking_finding=python_syntax_error" in row["notes"]
    assert inventory["findings"][0]["finding_id"] == row["finding_ids"]


def test_python_encoding_is_detected_from_cookie(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "encoding-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "latin.py").write_bytes(
        b"# coding: latin-1\ndef caf\xe9():\n    return 1\n"
    )
    git(repo, "add", "latin.py")
    git(repo, "commit", "-qm", "encoding fixture")
    base_sha = git(repo, "rev-parse", "HEAD")

    inventory = builder.build_inventory(repo, base_sha)

    assert any(row["qualified_name"] == "café" for row in inventory["symbols"])
    assert inventory["files"][0]["status"] == "pending"


def test_python_encoding_error_is_blocking(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "bad-encoding-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "bad.py").write_bytes(b"# coding: utf-8\ndef caf\xe9():\n    return 1\n")
    git(repo, "add", "bad.py")
    git(repo, "commit", "-qm", "bad encoding fixture")
    base_sha = git(repo, "rev-parse", "HEAD")

    inventory = builder.build_inventory(repo, base_sha)

    assert inventory["files"][0]["status"] == "blocked"
    assert "blocking_finding=python_encoding_error" in inventory["files"][0]["notes"]


def test_binary_file_requires_equivalent_binary_review(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)
    row = rows_by_path(inventory["files"])["asset.bin"]

    assert row["scope_tier"] == "F"
    assert row["physical_lines"] == ""
    assert row["logical_lines"] == ""
    assert "binary_review_required" in row["notes"]
    assert "line_by_line_not_applicable" in row["notes"]


def test_initial_line_coverage_partitions_each_file(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)
    coverage = rows_by_path(inventory["line_coverage"])

    assert coverage["crlf.txt"]["start_line"] == "1"
    assert coverage["crlf.txt"]["end_line"] == "2"
    assert coverage["empty.txt"]["start_line"] == "0"
    assert coverage["empty.txt"]["classification"] == "empty_file"
    assert coverage["asset.bin"]["start_line"] == "0"
    assert coverage["asset.bin"]["classification"] == "binary_equivalent_review"


def test_untracked_inventory_excludes_ignored_files(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)
    untracked = rows_by_path(inventory["untracked"])

    assert "visible-untracked.txt" in untracked
    assert "ignored-secret.env" not in untracked
    row = untracked["visible-untracked.txt"]
    assert {"source_root", "captured_at", "content_sha256"} <= row.keys()
    assert row["notes"] == "content_hashed_not_stored"
    assert row["source_root"] == str(repo.resolve())
    assert row["captured_at"].endswith("Z")
    assert len(row["content_sha256"]) == 64


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("duplicate", "duplicate untracked row"),
        ("missing", "untracked path missing"),
        ("unknown", "unknown untracked row"),
    ],
)
def test_validator_requires_exact_untracked_inventory(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    if mutation == "duplicate":
        inventory["untracked"].append(dict(inventory["untracked"][0]))
    elif mutation == "missing":
        inventory["untracked"].pop()
    else:
        row = dict(inventory["untracked"][0])
        row["path"] = "unknown-untracked.txt"
        row["path_b64"] = base64.b64encode(b"unknown-untracked.txt").decode("ascii")
        inventory["untracked"].append(row)
    write_csv(
        review_dir / "scope" / "untracked-inventory.csv",
        builder.UNTRACKED_FIELDS,
        inventory["untracked"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("duplicate", "duplicate file row"),
        ("missing", "tracked file missing"),
        ("unknown", "unknown file row"),
    ],
)
def test_validator_rejects_invalid_file_coverage(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    rows = inventory["files"]

    if mutation == "duplicate":
        rows.append(dict(rows[0]))
    elif mutation == "missing":
        rows.pop()
    else:
        unknown = dict(rows[0])
        unknown["path"] = "unknown.py"
        unknown["path_b64"] = base64.b64encode(b"unknown.py").decode("ascii")
        rows.append(unknown)
    write_csv(review_dir / "scope" / "file-inventory.csv", builder.FILE_FIELDS, rows)

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_validator_ignores_worktree_drift_outside_frozen_tree(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    (repo / "src" / "module.py").write_text(
        "def changed():\n    return 2\n", encoding="utf-8"
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert not any("drift" in error and "src/module.py" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("git_mode", "100755"),
        ("object_type", "commit"),
        ("object_id", "0" * 40),
        ("bytes", "999"),
        ("physical_lines", "999"),
    ],
)
def test_validator_rejects_inventory_metadata_drift(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    row = next(row for row in inventory["files"] if row["path"] == "src/module.py")
    row[field] = replacement
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(
        f"{field} drift" in error and "src/module.py" in error for error in errors
    )


def test_validator_rejects_missing_python_symbol(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["symbols"].pop()
    write_csv(
        review_dir / "scope" / "symbol-inventory.csv",
        builder.SYMBOL_FIELDS,
        inventory["symbols"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("Python symbol missing" in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("duplicate", "duplicate Python symbol row"),
        ("unknown", "unknown Python symbol"),
        ("range", "symbol start_line drift"),
    ],
)
def test_validator_rejects_invalid_symbol_inventory(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    if mutation == "duplicate":
        inventory["symbols"].append(dict(inventory["symbols"][0]))
    elif mutation == "unknown":
        row = dict(inventory["symbols"][0])
        row["symbol_id"] = "SYM-" + "f" * 24
        inventory["symbols"].append(row)
    else:
        inventory["symbols"][0]["start_line"] = "999"
    write_csv(
        review_dir / "scope" / "symbol-inventory.csv",
        builder.SYMBOL_FIELDS,
        inventory["symbols"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    ("start_line", "end_line", "expected_error"),
    [
        ("2", "2", "line coverage gap"),
        ("1", "3", "line coverage outside file"),
    ],
)
def test_validator_rejects_invalid_line_coverage(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    start_line: str,
    end_line: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    row = next(row for row in inventory["line_coverage"] if row["path"] == "crlf.txt")
    row.update(start_line=start_line, end_line=end_line)
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_validator_rejects_overlapping_line_coverage(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    row = next(row for row in inventory["line_coverage"] if row["path"] == "crlf.txt")
    row.update(start_line="1", end_line="1")
    overlap = dict(row)
    overlap.update(start_line="1", end_line="2")
    inventory["line_coverage"].append(overlap)
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("line coverage overlap" in error for error in errors)


def line_membership(row: dict[str, str], batch: str = "BATCH-001") -> dict[str, str]:
    end_line = row["physical_lines"] or "0"
    return {
        "batch": batch,
        "path": row["path"],
        "path_b64": row["path_b64"],
        "reviewed_object_id": row["object_id"],
        "start_line": "1" if end_line != "0" else "0",
        "end_line": end_line,
        "symbol_id": "",
        "role": "line_owner",
        "reviewer": "",
        "verified_by": "",
    }


def test_validator_rejects_overlapping_batch_ownership(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    memberships = [line_membership(row) for row in inventory["files"]]
    target = next(row for row in memberships if row["path"] == "crlf.txt")
    target["end_line"] = "1"
    overlap = dict(target)
    overlap.update(start_line="1", end_line="2", batch="BATCH-002")
    memberships.append(overlap)
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        memberships,
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("batch ownership overlap" in error for error in errors)


def test_validator_rejects_batch_ownership_gap(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    memberships = [line_membership(row) for row in inventory["files"]]
    target = next(row for row in memberships if row["path"] == "crlf.txt")
    target["start_line"] = "2"
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        memberships,
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(
        "batch ownership gap" in error and "crlf.txt" in error for error in errors
    )


def test_validator_enforces_code_batch_file_limit(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo = tmp_path / "batch-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "src").mkdir()
    for number in range(21):
        (repo / "src" / f"file_{number:02d}.txt").write_text("x\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "batch fixture")
    base_sha = git(repo, "rev-parse", "HEAD")
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    memberships = [line_membership(row) for row in inventory["files"]]
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        memberships,
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("exceeds file limit 20" in error for error in errors)


@pytest.mark.parametrize(
    ("content", "expected_error"),
    [
        ("x\n" * 4001, "exceeds line limit 4000"),
        (
            "".join(
                f"def function_{number}():\n    return {number}\n"
                for number in range(151)
            ),
            "exceeds symbol limit 150",
        ),
    ],
)
def test_validator_enforces_code_batch_size_limits(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
    content: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo = tmp_path / "limit-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "src").mkdir()
    path = repo / "src" / ("many.py" if content.startswith("def ") else "many.txt")
    path.write_text(content, encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "limit fixture")
    base_sha = git(repo, "rev-parse", "HEAD")
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    memberships = [line_membership(inventory["files"][0])]
    memberships.extend(
        {
            "batch": "BATCH-001",
            "path": symbol["path"],
            "path_b64": symbol["path_b64"],
            "reviewed_object_id": inventory["files"][0]["object_id"],
            "start_line": symbol["start_line"],
            "end_line": symbol["end_line"],
            "symbol_id": symbol["symbol_id"],
            "role": "symbol_owner",
            "reviewer": "",
            "verified_by": "",
        }
        for symbol in inventory["symbols"]
    )
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        memberships,
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_validator_rejects_same_second_reviewer(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    row = inventory["files"][0]
    row.update(status="verified", reviewer=" Reviewer-A ", verified_by="reviewer-a")
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("different reviewer" in error for error in errors)


def test_validator_rejects_invalid_headers(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    fields = builder.FILE_FIELDS[:-1]
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        fields,
        [{field: row[field] for field in fields} for row in inventory["files"]],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(
        "invalid header" in error and "file-inventory.csv" in error for error in errors
    )


def test_validator_rejects_invalid_status_enum(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["files"][0]["status"] = "complete"
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("invalid status" in error for error in errors)


def test_validator_requires_exclusion_reason_for_out_of_scope_file(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["files"][0]["status"] = "out_of_scope"
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("out_of_scope file lacks exclusion" in error for error in errors)


@pytest.mark.parametrize(
    ("inventory_key", "filename", "fields", "expected_error"),
    [
        (
            "symbols",
            "symbol-inventory.csv",
            "SYMBOL_FIELDS",
            "out_of_scope symbol lacks exclusion",
        ),
        (
            "line_coverage",
            "line-coverage.csv",
            "LINE_COVERAGE_FIELDS",
            "out_of_scope line coverage lacks exclusion",
        ),
    ],
)
def test_validator_requires_exclusion_for_out_of_scope_child_rows(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    inventory_key: str,
    filename: str,
    fields: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory[inventory_key][0]["status"] = "out_of_scope"
    write_csv(
        review_dir / "scope" / filename,
        getattr(builder, fields),
        inventory[inventory_key],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_verified_file_requires_verified_child_rows(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    source = next(row for row in inventory["files"] if row["path"] == "src/module.py")
    source.update(status="verified", reviewer="reviewer-a", verified_by="reviewer-b")
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("verified file has unverified symbol" in error for error in errors)
    assert any(
        "verified file has unverified line coverage" in error for error in errors
    )


def test_validator_reports_malformed_short_csv_row(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    path = review_dir / "scope" / "file-inventory.csv"
    path.write_text(",".join(builder.FILE_FIELDS) + "\nonly-a-path\n", encoding="utf-8")

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(
        "malformed row" in error and "file-inventory.csv" in error for error in errors
    )


def test_final_validator_rejects_pending_rows(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)

    errors = validator.validate_inventory(
        repo,
        base_sha,
        review_dir,
        require_final=True,
    )

    assert any("file row is not final" in error for error in errors)
    assert any("symbol row is not final" in error for error in errors)


def test_final_validator_rejects_blocked_rows(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    for row in inventory["files"]:
        row.update(status="verified", reviewer="reviewer-a", verified_by="reviewer-b")
    inventory["files"][0]["status"] = "blocked"
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any("blocked file row" in error for error in errors)


def test_validator_rejects_incomplete_finding(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    write_csv(
        review_dir / "findings" / "findings.csv",
        validator.FINDING_FIELDS,
        [
            {
                "finding_id": "DEF-REVIEW-001",
                "priority": "P2",
                "certainty": "proven",
                "review_area": "correctness",
                "title": "Incomplete finding",
                "path": "src/module.py",
                "start_line": "1",
                "end_line": "1",
                "evidence": "",
                "reproduction": "run fixture",
                "recommendation": "supply evidence",
                "status": "reviewed",
                "reviewer": "reviewer-a",
                "verified_by": "",
            }
        ],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("finding missing evidence" in error for error in errors)


def valid_finding() -> dict[str, str]:
    return {
        "finding_id": "DEF-REVIEW-001",
        "priority": "P2",
        "certainty": "proven",
        "review_area": "correctness",
        "title": "A finding",
        "path": "src/module.py",
        "start_line": "1",
        "end_line": "1",
        "evidence": "observable evidence",
        "reproduction": "run fixture",
        "recommendation": "change later",
        "status": "reviewed",
        "reviewer": "reviewer-a",
        "verified_by": "",
    }


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("priority", "P9", "invalid priority"),
        ("certainty", "certain", "invalid certainty"),
        ("path", "missing.py", "unknown path"),
        ("end_line", "9999", "range outside file"),
    ],
)
def test_validator_rejects_invalid_finding_contract(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    field: str,
    value: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    finding = valid_finding()
    finding[field] = value
    write_csv(
        review_dir / "findings" / "findings.csv",
        validator.FINDING_FIELDS,
        [finding],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_validator_requires_bidirectional_finding_references(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["files"][0]["finding_ids"] = "UNKNOWN-FINDING"
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )
    write_csv(
        review_dir / "findings" / "findings.csv",
        validator.FINDING_FIELDS,
        [valid_finding()],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("unknown finding reference" in error for error in errors)
    assert any("finding is not referenced" in error for error in errors)


def test_validator_requires_path_consistent_finding_reference(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    wrong_file = next(
        row for row in inventory["files"] if row["path"] != "src/module.py"
    )
    wrong_file["finding_ids"] = "DEF-REVIEW-001"
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )
    write_csv(
        review_dir / "findings" / "findings.csv",
        validator.FINDING_FIELDS,
        [valid_finding()],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("finding reference path mismatch" in error for error in errors)


def test_final_rejects_unreviewed_out_of_scope_rows(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    for key in ("files", "symbols", "line_coverage"):
        for row in inventory[key]:
            row["status"] = "out_of_scope"
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )
    write_csv(
        review_dir / "scope" / "symbol-inventory.csv",
        builder.SYMBOL_FIELDS,
        inventory["symbols"],
    )
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )
    exclusions = [
        {
            "path": row["path"],
            "path_b64": row["path_b64"],
            "reason": "fixture exclusion",
            "approved_by": "",
            "notes": "",
        }
        for row in inventory["files"]
    ]
    write_csv(
        review_dir / "scope" / "exclusions.csv",
        builder.EXCLUSION_FIELDS,
        exclusions,
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any(
        "out_of_scope row requires independent reviewers" in error for error in errors
    )
    assert any("out_of_scope exclusion requires approval" in error for error in errors)


@pytest.mark.parametrize("classification", ["", "invented"])
def test_final_rejects_invalid_line_classification(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    classification: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["line_coverage"][0]["classification"] = classification
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any("invalid line classification" in error for error in errors)


def test_final_rejects_pending_untracked_row(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any("untracked row is not final" in error for error in errors)


def test_final_rejects_missing_review_infrastructure(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any(
        "review infrastructure missing at finalization" in error for error in errors
    )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("path", "symbol owner path mismatch"),
        ("range", "symbol owner range drift"),
    ],
)
def test_validator_rejects_mismatched_symbol_owner(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    symbol = inventory["symbols"][0]
    membership = {
        "batch": "BATCH-001",
        "path": symbol["path"],
        "path_b64": symbol["path_b64"],
        "reviewed_object_id": next(
            row["object_id"]
            for row in inventory["files"]
            if row["path_b64"] == symbol["path_b64"]
        ),
        "start_line": symbol["start_line"],
        "end_line": symbol["end_line"],
        "symbol_id": symbol["symbol_id"],
        "role": "symbol_owner",
        "reviewer": "reviewer-a",
        "verified_by": "reviewer-b",
    }
    if mutation == "path":
        wrong_file = next(
            row for row in inventory["files"] if row["path_b64"] != symbol["path_b64"]
        )
        membership["path"] = wrong_file["path"]
        membership["path_b64"] = wrong_file["path_b64"]
    else:
        membership["start_line"] = str(int(symbol["start_line"]) + 1)
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        [membership],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_validator_rejects_batch_without_manifest(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    membership = line_membership(inventory["files"][0], batch="BATCH-999")
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        [membership],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("batch manifest missing: BATCH-999" in error for error in errors)


def test_out_of_scope_is_forbidden_for_executable_tier(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    source = next(row for row in inventory["files"] if row["scope_tier"] == "A")
    source.update(
        status="out_of_scope", reviewer="reviewer-a", verified_by="reviewer-b"
    )
    for row in inventory["symbols"] + inventory["line_coverage"]:
        if row["path_b64"] == source["path_b64"]:
            row.update(
                status="out_of_scope", reviewer="reviewer-a", verified_by="reviewer-b"
            )
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )
    write_csv(
        review_dir / "scope" / "symbol-inventory.csv",
        builder.SYMBOL_FIELDS,
        inventory["symbols"],
    )
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )
    write_csv(
        review_dir / "scope" / "exclusions.csv",
        builder.EXCLUSION_FIELDS,
        [
            {
                "path": source["path"],
                "path_b64": source["path_b64"],
                "reason": "not actually excludable",
                "approved_by": "review-lead",
                "notes": "",
            }
        ],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(
        "out_of_scope is not permitted for scope tier A" in error for error in errors
    )


def test_out_of_scope_parent_requires_consistent_children(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    binary = next(row for row in inventory["files"] if row["path"] == "asset.bin")
    binary.update(
        status="out_of_scope", reviewer="reviewer-a", verified_by="reviewer-b"
    )
    write_csv(
        review_dir / "scope" / "file-inventory.csv",
        builder.FILE_FIELDS,
        inventory["files"],
    )
    write_csv(
        review_dir / "scope" / "exclusions.csv",
        builder.EXCLUSION_FIELDS,
        [
            {
                "path": binary["path"],
                "path_b64": binary["path_b64"],
                "reason": "binary fixture",
                "approved_by": "review-lead",
                "notes": "",
            }
        ],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("out_of_scope file has non-excluded child" in error for error in errors)


@pytest.mark.parametrize(
    ("path", "classification", "expected_error"),
    [
        ("asset.bin", "code", "binary line classification mismatch"),
        ("empty.txt", "code", "empty line classification mismatch"),
        ("crlf.txt", "binary_equivalent_review", "text line classification mismatch"),
    ],
)
def test_validator_enforces_file_specific_line_classification(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    path: str,
    classification: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    row = next(row for row in inventory["line_coverage"] if row["path"] == path)
    row["classification"] = classification
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_final_line_batch_requires_matching_membership(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["line_coverage"][0]["batch"] = "BATCH-001"
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any(
        "line coverage batch has no matching ownership" in error for error in errors
    )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("missing", "review infrastructure tool missing"),
        ("extra", "unexpected review infrastructure tool"),
        ("mixed_sha", "review infrastructure must use one TOOLING_SHA"),
        ("failed_test", "review infrastructure test_result must be pass"),
    ],
)
def test_validator_requires_exact_review_tool_snapshot(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)
    tooling_sha = commit_tooling_snapshot(repo)
    rows = tooling_rows(builder, repo, tooling_sha)
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        snapshot = rows_by_path(builder.build_inventory(repo, tooling_sha)["files"])
        source = snapshot["src/module.py"]
        rows.append(
            {
                "path": source["path"],
                "tooling_sha": tooling_sha,
                "blob_sha": source["object_id"],
                "physical_lines": source["physical_lines"],
                "status": "verified",
                "reviewer": "reviewer-a",
                "verified_by": "reviewer-b",
                "test_result": "pass",
                "notes": "extra",
            }
        )
    elif mutation == "mixed_sha":
        rows[0]["tooling_sha"] = base_sha
    else:
        rows[0]["test_result"] = "fail"
    write_csv(
        review_dir / "scope" / "review-infrastructure.csv",
        builder.REVIEW_INFRASTRUCTURE_FIELDS,
        rows,
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


def test_builder_accepts_explicit_untracked_root(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    args = builder._parse_args(
        [
            "--base-sha",
            base_sha,
            "--output-dir",
            "scope",
            "--untracked-root",
            str(repo),
        ]
    )

    assert args.untracked_root == repo


def test_final_untracked_validation_uses_frozen_snapshot(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir, inventory, scope_sha = freeze_untracked_scope(builder, repo, base_sha)
    for row in inventory["untracked"]:
        row.update(status="verified", reviewer="reviewer-a", verified_by="reviewer-b")
    write_csv(
        review_dir / "scope" / "untracked-inventory.csv",
        builder.UNTRACKED_FIELDS,
        inventory["untracked"],
    )
    (repo / "visible-untracked.txt").write_text(
        "changed after freeze\n", encoding="utf-8"
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True, scope_sha=scope_sha
    )

    assert not any(
        error.startswith("untracked ") and "drift" in error for error in errors
    )


def test_final_untracked_row_requires_independent_reviewers(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    inventory["untracked"][0].update(
        status="verified", reviewer=" Reviewer-A ", verified_by="reviewer-a"
    )
    write_csv(
        review_dir / "scope" / "untracked-inventory.csv",
        builder.UNTRACKED_FIELDS,
        inventory["untracked"],
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any(
        "untracked row requires a different reviewer" in error for error in errors
    )


def test_line_and_batch_rows_pin_reviewed_object_id(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)

    assert "reviewed_object_id" in builder.LINE_COVERAGE_FIELDS
    assert "reviewed_object_id" in builder.BATCH_MEMBERSHIP_FIELDS
    line = inventory["line_coverage"][0]
    line["reviewed_object_id"] = "0" * 40
    write_csv(
        review_dir / "scope" / "line-coverage.csv",
        builder.LINE_COVERAGE_FIELDS,
        inventory["line_coverage"],
    )

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any("line reviewed_object_id drift" in error for error in errors)


def test_non_utf8_json_is_a_blocking_text_finding(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "json-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "payload.json").write_bytes(b'{"value":"\xff"}\n')
    git(repo, "add", "payload.json")
    git(repo, "commit", "-qm", "json encoding fixture")
    base_sha = git(repo, "rev-parse", "HEAD")

    inventory = builder.build_inventory(repo, base_sha)
    row = inventory["files"][0]

    assert row["status"] == "blocked"
    assert "blocking_finding=text_encoding_error" in row["notes"]
    assert inventory["findings"][0]["path"] == "payload.json"


def test_scope_tiers_cover_build_and_dependency_files(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "tier-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
    (repo / "requirements-dev.txt").write_text("pytest==9.0.3\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "tier fixture")
    base_sha = git(repo, "rev-parse", "HEAD")

    rows = rows_by_path(builder.build_inventory(repo, base_sha)["files"])

    assert rows["Makefile"]["scope_tier"] == "C"
    assert rows["requirements-dev.txt"]["scope_tier"] == "D"


def test_parent_complexity_excludes_nested_function_branches(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "complexity-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "nested.py").write_text(
        "def outer():\n"
        "    def inner(a, b, c):\n"
        "        if a:\n"
        "            return 1\n"
        "        if b:\n"
        "            return 2\n"
        "        if c:\n"
        "            return 3\n"
        "        return 0\n"
        "    return inner\n",
        encoding="utf-8",
    )
    git(repo, "add", "nested.py")
    git(repo, "commit", "-qm", "complexity fixture")
    base_sha = git(repo, "rev-parse", "HEAD")

    symbols = builder.build_inventory(repo, base_sha)["symbols"]
    outer = next(row for row in symbols if row["qualified_name"] == "outer")
    inner = next(row for row in symbols if row["qualified_name"] == "outer.inner")

    assert outer["complexity"] == "1"
    assert inner["complexity"] == "4"


def test_symlink_has_explicit_equivalent_review_classification(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo

    inventory = builder.build_inventory(repo, base_sha)
    file_row = next(row for row in inventory["files"] if row["path"] == "link.txt")
    line_row = next(
        row for row in inventory["line_coverage"] if row["path"] == "link.txt"
    )

    assert file_row["file_type"] == "inode/symlink"
    assert file_row["scope_tier"] == "F"
    assert "symlink_review_required" in file_row["notes"]
    assert line_row["classification"] == "symlink_equivalent_review"


def test_writer_overwrites_stale_findings_with_header_only_inventory(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    findings_path = review_dir / "findings" / "findings.csv"
    write_csv(findings_path, builder.FINDING_FIELDS, [valid_finding()])

    builder.write_inventory(
        builder.build_inventory(repo, base_sha), review_dir / "scope"
    )

    with findings_path.open("r", encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle)) == []


def test_python_variants_and_shebang_are_symbolized(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
) -> None:
    builder, _ = inventory_tools
    repo = tmp_path / "python-variant-repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Inventory Test")
    git(repo, "config", "user.email", "inventory@example.invalid")
    (repo / "types.pyi").write_text(
        "def typed(value: str) -> str: ...\n", encoding="utf-8"
    )
    (repo / "window.pyw").write_text(
        "def render():\n    return None\n", encoding="utf-8"
    )
    (repo / "python-tool").write_text(
        "#!/usr/bin/env python3\ndef execute():\n    return 1\n", encoding="utf-8"
    )
    (repo / "python-tool").chmod(0o755)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "python variants")
    base_sha = git(repo, "rev-parse", "HEAD")

    symbols = builder.build_inventory(repo, base_sha)["symbols"]

    assert {(row["path"], row["qualified_name"]) for row in symbols} >= {
        ("types.pyi", "typed"),
        ("window.pyw", "render"),
        ("python-tool", "execute"),
    }


def test_untracked_symlinks_and_special_files_are_never_followed(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder, _ = inventory_tools
    repo, base_sha = sample_repo
    source = tmp_path / "untracked-source"
    source.mkdir()
    git(source, "init", "-q")
    git(source, "config", "user.name", "Inventory Test")
    git(source, "config", "user.email", "inventory@example.invalid")
    (source / ".gitignore").write_text("ignored-secret.txt\n", encoding="utf-8")
    git(source, "add", ".gitignore")
    git(source, "commit", "-qm", "untracked source")
    (source / "ignored-secret.txt").write_text("never hash me\n", encoding="utf-8")
    external = tmp_path / "external-target.txt"
    external.write_text("never hash me either\n", encoding="utf-8")
    (source / "innocent-link").symlink_to("ignored-secret.txt")
    (source / "external-link").symlink_to(external)
    os.mkfifo(source / "named-pipe")

    rows = rows_by_path(
        builder.build_inventory(repo, base_sha, untracked_root=source)["untracked"]
    )

    for path in ("innocent-link", "external-link"):
        assert rows[path]["content_sha256"] == "NOT_SCANNED_SYMLINK"
        assert rows[path]["notes"] == "symlink_content_not_read"
    monkeypatch.setattr(builder, "_git", lambda _root, _args: b"named-pipe\0")
    special = rows_by_path(builder._untracked_rows(source))["named-pipe"]
    assert special["content_sha256"] == "NOT_SCANNED_SPECIAL"
    assert special["notes"] == "special_file_content_not_read"


def test_validator_uses_explicit_untracked_root_for_nonfinal_exact_set(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    source = tmp_path / "source-worktree"
    source.mkdir()
    git(source, "init", "-q")
    git(source, "config", "user.name", "Inventory Test")
    git(source, "config", "user.email", "inventory@example.invalid")
    (source / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    git(source, "add", "tracked.txt")
    git(source, "commit", "-qm", "source fixture")
    (source / "source-only.txt").write_text("untracked\n", encoding="utf-8")
    review_dir = tmp_path / "review"
    inventory = builder.build_inventory(repo, base_sha, untracked_root=source)
    builder.write_inventory(inventory, review_dir / "scope")

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, untracked_root=source
    )

    assert not any("untracked path missing" in error for error in errors)
    assert not any("unknown untracked row" in error for error in errors)
    assert not any("untracked source_root drift" in error for error in errors)


def test_validator_cli_accepts_untracked_root_and_scope_sha(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    _, validator = inventory_tools
    repo, base_sha = sample_repo

    args = validator._parse_args(
        [
            "--base-sha",
            base_sha,
            "--review-dir",
            "review",
            "--untracked-root",
            str(repo),
            "--scope-sha",
            base_sha,
        ]
    )

    assert args.untracked_root == repo
    assert args.scope_sha == base_sha


def test_final_requires_a_full_scope_sha(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    build_review(builder, repo, base_sha, review_dir)

    missing = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )
    abbreviated = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True, scope_sha=base_sha[:12]
    )

    assert any("SCOPE_SHA is required" in error for error in missing)
    assert any("SCOPE_SHA must be a full commit SHA" in error for error in abbreviated)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("missing", "frozen untracked path missing"),
        ("fabricated", "unknown frozen untracked row"),
        ("content", "frozen untracked content_sha256 drift"),
    ],
)
def test_final_untracked_rows_match_committed_frozen_scope(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir, inventory, scope_sha = freeze_untracked_scope(builder, repo, base_sha)
    rows = [dict(row) for row in inventory["untracked"]]
    if mutation == "missing":
        rows = []
    elif mutation == "fabricated":
        fabricated = dict(rows[0])
        fabricated["path"] = "fabricated.txt"
        fabricated["path_b64"] = base64.b64encode(b"fabricated.txt").decode("ascii")
        rows.append(fabricated)
    else:
        rows[0]["content_sha256"] = "0" * 64
    write_csv(
        review_dir / "scope" / "untracked-inventory.csv",
        builder.UNTRACKED_FIELDS,
        rows,
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True, scope_sha=scope_sha
    )

    assert any(expected_error in error for error in errors)


def test_final_forbids_untracked_out_of_scope(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir, inventory, scope_sha = freeze_untracked_scope(builder, repo, base_sha)
    inventory["untracked"][0].update(
        status="out_of_scope", reviewer="reviewer-a", verified_by="reviewer-b"
    )
    write_csv(
        review_dir / "scope" / "untracked-inventory.csv",
        builder.UNTRACKED_FIELDS,
        inventory["untracked"],
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True, scope_sha=scope_sha
    )

    assert any("untracked out_of_scope is forbidden" in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("missing", "batch index missing: BATCH-001"),
        ("extra", "unexpected batch index: BATCH-002"),
        ("manifest_hash", "batch manifest_sha256 drift: BATCH-001"),
        ("membership_hash", "batch membership_sha256 drift: BATCH-001"),
        ("heading", "batch manifest heading mismatch: BATCH-001"),
        ("empty", "batch manifest is empty: BATCH-001"),
    ],
)
def test_batch_index_proves_manifest_and_canonical_membership(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    membership = line_membership(inventory["files"][0])
    memberships = [membership]
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        memberships,
    )
    manifest = review_dir / "batches" / "BATCH-001.md"
    manifest.parent.mkdir(parents=True)
    manifest_content = b"# BATCH-001\n\nReview evidence.\n"
    if mutation == "heading":
        manifest_content = b"# Wrong heading\n"
    elif mutation == "empty":
        manifest_content = b""
    manifest.write_bytes(manifest_content)
    index = [
        {
            "batch": "BATCH-001",
            "status": "pending",
            "reviewer": "",
            "verified_by": "",
            "manifest_sha256": hashlib.sha256(manifest_content).hexdigest(),
            "membership_sha256": canonical_membership_sha256(builder, memberships),
        }
    ]
    if mutation == "missing":
        index = []
    elif mutation == "extra":
        extra = dict(index[0], batch="BATCH-002")
        index.append(extra)
    elif mutation == "manifest_hash":
        index[0]["manifest_sha256"] = "0" * 64
    elif mutation == "membership_hash":
        index[0]["membership_sha256"] = "0" * 64
    write_csv(review_dir / "scope" / "batch-index.csv", BATCH_INDEX_FIELDS, index)

    errors = validator.validate_inventory(repo, base_sha, review_dir)

    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    ("status", "reviewer", "verified_by", "expected_error"),
    [
        ("pending", "", "", "batch index row is not final: BATCH-001"),
        (
            "verified",
            " Reviewer-A ",
            "reviewer-a",
            "batch index row requires a different reviewer: BATCH-001",
        ),
    ],
)
def test_final_batch_index_requires_verified_independent_review(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
    tmp_path: Path,
    status: str,
    reviewer: str,
    verified_by: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir = tmp_path / "review"
    inventory = build_review(builder, repo, base_sha, review_dir)
    membership = line_membership(inventory["files"][0])
    write_csv(
        review_dir / "scope" / "batch-membership.csv",
        builder.BATCH_MEMBERSHIP_FIELDS,
        [membership],
    )
    manifest_content = b"# BATCH-001\n"
    manifest = review_dir / "batches" / "BATCH-001.md"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(manifest_content)
    write_csv(
        review_dir / "scope" / "batch-index.csv",
        BATCH_INDEX_FIELDS,
        [
            {
                "batch": "BATCH-001",
                "status": status,
                "reviewer": reviewer,
                "verified_by": verified_by,
                "manifest_sha256": hashlib.sha256(manifest_content).hexdigest(),
                "membership_sha256": canonical_membership_sha256(builder, [membership]),
            }
        ],
    )

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, require_final=True
    )

    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    ("path", "expected_group"),
    [
        ("Makefile", 1),
        ("src/api/routes/definitions.py", 2),
        ("src/domain/entities/definition.py", 3),
        ("src/database/migrations/001.sql.py", 4),
        ("src/services/ai/model_router.py", 5),
        ("src/services/orchestrators/generation.py", 6),
        ("src/services/validation/sanitizer.py", 7),
        ("src/services/web_lookup/rag.py", 8),
        ("src/services/export/cache.py", 9),
        ("src/ui/renderers/result.py", 10),
        ("src/ui/components/definition_generator_tab.py", 11),
        ("src/utils/monitoring.py", 12),
        ("tests/unit/services/test_cache.py", 13),
        ("tests/integration/test_api.py", 14),
        ("scripts/check_quality.sh", 15),
        ("data/wetteksten/wid.txt", 16),
        ("docs/plans/review.md", 17),
        ("assets/logo.png", 18),
    ],
)
def test_review_group_policy_has_eighteen_first_match_groups(
    inventory_tools: tuple[ModuleType, ModuleType], path: str, expected_group: int
) -> None:
    builder, _ = inventory_tools

    assert builder.review_group(path) == expected_group


def test_batch_planner_is_deterministic_and_raw_path_sorted(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    inventory = synthetic_inventory(
        builder,
        [
            ("src/misc/z.py", "A", 1, False),
            ("src/misc/é.py", "A", 1, False),
            ("src/misc/a.py", "A", 1, False),
        ],
    )

    first = builder.plan_batches(
        copy.deepcopy(inventory), base_sha="a" * 40, pilot_paths=()
    )
    second = builder.plan_batches(
        {
            **copy.deepcopy(inventory),
            "files": list(reversed(inventory["files"])),
            "line_coverage": list(reversed(inventory["line_coverage"])),
        },
        base_sha="a" * 40,
        pilot_paths=(),
    )

    assert first == second
    assert [
        row["path"] for row in first["batch_membership"] if row["role"] == "line_owner"
    ] == ["src/misc/a.py", "src/misc/z.py", "src/misc/é.py"]


def test_batch_planner_splits_large_json_into_eleven_ranges(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    inventory = synthetic_inventory(builder, [("runtime/huge.json", "D", 60001, False)])

    plan = builder.plan_batches(inventory, base_sha="a" * 40, pilot_paths=())
    ranges = [
        (int(row["start_line"]), int(row["end_line"])) for row in plan["line_coverage"]
    ]

    assert len(ranges) == 11
    assert ranges[0] == (1, 6000)
    assert ranges[-1] == (60001, 60001)
    assert all(
        previous[1] + 1 == current[0]
        for previous, current in itertools.pairwise(ranges)
    )


@pytest.mark.parametrize(
    ("tier", "count", "expected_batches"),
    [("A", 21, 2), ("D", 31, 2)],
)
def test_batch_planner_enforces_file_caps(
    inventory_tools: tuple[ModuleType, ModuleType],
    tier: str,
    count: int,
    expected_batches: int,
) -> None:
    builder, _ = inventory_tools
    root = "src/security" if tier == "A" else "assets"
    inventory = synthetic_inventory(
        builder,
        [(f"{root}/file-{number:02d}.txt", tier, 1, False) for number in range(count)],
    )

    plan = builder.plan_batches(inventory, base_sha="a" * 40, pilot_paths=())

    assert len(plan["batch_index"]) == expected_batches


def test_batch_planner_splits_one_file_at_symbol_cap(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    starts = list(range(1, 152))
    inventory = synthetic_inventory(
        builder,
        [("src/security/many.py", "A", 151, False)],
        {"src/security/many.py": starts},
    )

    plan = builder.plan_batches(inventory, base_sha="a" * 40, pilot_paths=())

    assert len(plan["batch_index"]) == 2
    assert [
        sum(
            row["role"] == "symbol_owner" and row["batch"] == index["batch"]
            for row in plan["batch_membership"]
        )
        for index in plan["batch_index"]
    ] == [150, 1]


def test_batch_planner_rejects_151_symbols_on_same_line(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    inventory = synthetic_inventory(
        builder,
        [("src/security/same-line.py", "A", 1, False)],
        {"src/security/same-line.py": [1] * 151},
    )

    with pytest.raises(ValueError, match="151 symbols share line 1"):
        builder.plan_batches(inventory, base_sha="a" * 40, pilot_paths=())


def test_batch_planner_preserves_immutable_review_fields_when_splitting(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    inventory = synthetic_inventory(
        builder,
        [
            ("runtime/blocked.py", "D", 7000, False),
            ("runtime/empty.txt", "D", 0, False),
            ("runtime/binary.bin", "F", 0, True),
        ],
    )

    plan = builder.plan_batches(inventory, base_sha="a" * 40, pilot_paths=())
    split = [row for row in plan["line_coverage"] if row["path"].endswith("blocked.py")]
    equivalent = [row for row in plan["line_coverage"] if row["start_line"] == "0"]

    assert len(split) == 2
    assert {
        (row["reviewed_object_id"], row["status"], row["finding_ids"], row["notes"])
        for row in split
    } == {("0" * 39 + "1", "blocked", "F-001", "fixture-line")}
    assert len(equivalent) == 2
    assert all(row["start_line"] == row["end_line"] == "0" for row in equivalent)


def test_rendered_manifest_and_index_pin_membership_hashes(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    plan = builder.plan_batches(
        synthetic_inventory(builder, [("src/security/a.py", "A", 3, False)]),
        base_sha="a" * 40,
        pilot_paths=(),
    )
    index = plan["batch_index"][0]
    manifest = plan["manifests"]["BATCH-001.md"]
    memberships = [
        row for row in plan["batch_membership"] if row["batch"] == "BATCH-001"
    ]

    assert all(
        section.encode() in manifest for section in builder.MANIFEST_REQUIRED_SECTIONS
    )
    assert index["membership_sha256"] == builder.canonical_membership_sha256(
        memberships
    )
    assert f"Membership-SHA256: `{index['membership_sha256']}`".encode() in manifest
    assert index["manifest_sha256"] == hashlib.sha256(manifest).hexdigest()


def test_safe_batch_writer_refuses_stale_manifest_without_partial_write(
    inventory_tools: tuple[ModuleType, ModuleType], tmp_path: Path
) -> None:
    builder, _ = inventory_tools
    review_dir = tmp_path / "review"
    inventory = synthetic_inventory(builder, [("src/security/a.py", "A", 3, False)])
    builder.write_inventory(inventory, review_dir / "scope")
    plan = builder.plan_batches(inventory, base_sha="a" * 40, pilot_paths=())
    builder.write_batch_plan(plan, review_dir, update=False)
    stale = review_dir / "batches" / "BATCH-999.md"
    stale.write_text("stale\n", encoding="utf-8")
    before = (review_dir / "scope" / "batch-index.csv").read_bytes()

    with pytest.raises(ValueError, match="unexpected batch manifest set"):
        builder.write_batch_plan(plan, review_dir, update=True)

    assert (review_dir / "scope" / "batch-index.csv").read_bytes() == before


def test_existing_review_planner_never_regenerates_full_inventory(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder, _ = inventory_tools
    review_dir = tmp_path / "review"
    inventory = synthetic_inventory(builder, [("src/security/a.py", "A", 3, False)])
    builder.write_inventory(inventory, review_dir / "scope")
    monkeypatch.setattr(
        builder,
        "build_inventory",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("regenerated")),
    )

    plan = builder.plan_existing_review(
        review_dir, base_sha="a" * 40, update=False, pilot_paths=()
    )

    assert len(plan["batch_index"]) == 1


def test_current_snapshot_batch_plan_is_the_184_batch_golden(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    builder, _ = inventory_tools
    review_dir = TOOLS_DIR.parents[0]
    inventory = builder.load_planning_inventory(review_dir / "scope")

    plan = builder.plan_batches(
        copy.deepcopy(inventory),
        base_sha="b958ddb139b4754d1644ca4b4f22b1683d8ad108",
    )

    assert len(plan["batch_index"]) == 184
    assert len(plan["line_coverage"]) == 1904
    assert len(plan["batch_membership"]) == 12485
    assert plan["batch_membership"] == inventory["batch_membership"]
    pilot_paths = {
        row["path"]
        for row in plan["batch_membership"]
        if row["batch"] == "BATCH-001" and row["role"] == "line_owner"
    }
    assert pilot_paths == set(builder.PILOT_PATHS)


def test_nonfinal_line_coverage_requires_matching_membership_when_present(
    inventory_tools: tuple[ModuleType, ModuleType],
) -> None:
    _, validator = inventory_tools
    line = {
        "batch": "BATCH-001",
        "path": "a.py",
        "path_b64": base64.b64encode(b"a.py").decode("ascii"),
        "reviewed_object_id": "a" * 40,
        "start_line": "1",
        "end_line": "2",
    }
    wrong_owner = dict(line, start_line="1", end_line="1", role="line_owner")

    errors = validator._validate_line_batch_foreign_keys(
        [line], [wrong_owner], require_final=False
    )

    assert any("no matching ownership" in error for error in errors)


def test_supplied_scope_sha_uses_frozen_untracked_snapshot_nonfinal(
    inventory_tools: tuple[ModuleType, ModuleType],
    sample_repo: tuple[Path, str],
) -> None:
    builder, validator = inventory_tools
    repo, base_sha = sample_repo
    review_dir, _, scope_sha = freeze_untracked_scope(builder, repo, base_sha)
    (repo / "visible-untracked.txt").write_text("live drift\n", encoding="utf-8")

    errors = validator.validate_inventory(
        repo, base_sha, review_dir, scope_sha=scope_sha
    )

    assert not any("untracked content_sha256 drift" in error for error in errors)


def test_batch_lifecycle_requires_index_membership_reviewer_consistency(
    inventory_tools: tuple[ModuleType, ModuleType], tmp_path: Path
) -> None:
    builder, validator = inventory_tools
    membership = {
        "batch": "BATCH-001",
        "path": "a.py",
        "path_b64": base64.b64encode(b"a.py").decode("ascii"),
        "reviewed_object_id": "a" * 40,
        "start_line": "1",
        "end_line": "1",
        "symbol_id": "",
        "role": "line_owner",
        "reviewer": "reviewer-a",
        "verified_by": "reviewer-b",
    }
    content = b"# BATCH-001\n"
    manifest = tmp_path / "batches" / "BATCH-001.md"
    manifest.parent.mkdir()
    manifest.write_bytes(content)
    index = [
        {
            "batch": "BATCH-001",
            "status": "verified",
            "reviewer": "reviewer-x",
            "verified_by": "reviewer-b",
            "manifest_sha256": hashlib.sha256(content).hexdigest(),
            "membership_sha256": builder.canonical_membership_sha256([membership]),
        }
    ]

    errors = validator._validate_batch_index(index, [membership], tmp_path, False)

    assert any(
        "reviewer differs between index and membership" in error for error in errors
    )


def test_multi_batch_file_requires_one_reviewer_pair(
    inventory_tools: tuple[ModuleType, ModuleType], tmp_path: Path
) -> None:
    builder, validator = inventory_tools
    base = {
        "path": "a.py",
        "path_b64": base64.b64encode(b"a.py").decode("ascii"),
        "reviewed_object_id": "a" * 40,
        "symbol_id": "",
        "role": "line_owner",
        "verified_by": "reviewer-b",
    }
    memberships = [
        dict(
            base, batch="BATCH-001", start_line="1", end_line="5", reviewer="reviewer-a"
        ),
        dict(
            base,
            batch="BATCH-002",
            start_line="6",
            end_line="10",
            reviewer="reviewer-x",
        ),
    ]
    indexes = []
    for membership in memberships:
        content = f"# {membership['batch']}\n".encode()
        path = tmp_path / "batches" / f"{membership['batch']}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(content)
        indexes.append(
            {
                "batch": membership["batch"],
                "status": "verified",
                "reviewer": membership["reviewer"],
                "verified_by": "reviewer-b",
                "manifest_sha256": hashlib.sha256(content).hexdigest(),
                "membership_sha256": builder.canonical_membership_sha256([membership]),
            }
        )

    errors = validator._validate_batch_index(indexes, memberships, tmp_path, False)

    assert any(
        "multi-batch file has inconsistent reviewers" in error for error in errors
    )


def test_symbol_owner_batch_must_contain_symbol_start_line(
    inventory_tools: tuple[ModuleType, ModuleType], tmp_path: Path
) -> None:
    builder, validator = inventory_tools
    inventory = synthetic_inventory(
        builder,
        [("src/security/a.py", "A", 10, False)],
        {"src/security/a.py": [6]},
    )
    file_row = inventory["files"][0]
    symbol = inventory["symbols"][0]
    line_one = dict(
        line_membership(file_row, "BATCH-001"), start_line="1", end_line="5"
    )
    line_two = dict(
        line_membership(file_row, "BATCH-002"), start_line="6", end_line="10"
    )
    symbol_owner = {
        **line_one,
        "start_line": symbol["start_line"],
        "end_line": symbol["end_line"],
        "symbol_id": symbol["symbol_id"],
        "role": "symbol_owner",
    }

    errors = validator._validate_batch_membership(
        [line_one, line_two, symbol_owner],
        {file_row["path_b64"]: file_row},
        {symbol["symbol_id"]: symbol},
        False,
        tmp_path,
    )

    assert any("does not contain symbol start line" in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("sections", "batch manifest section missing"),
        ("digest", "batch manifest membership digest mismatch"),
        ("stale", "unexpected batch manifest filename"),
        ("gap", "batch IDs are not contiguous"),
    ],
)
def test_validator_enforces_manifest_and_contiguous_batch_contract(
    inventory_tools: tuple[ModuleType, ModuleType],
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, validator = inventory_tools
    membership = {
        "batch": "BATCH-001",
        "path": "a.py",
        "path_b64": base64.b64encode(b"a.py").decode("ascii"),
        "reviewed_object_id": "a" * 40,
        "start_line": "1",
        "end_line": "1",
        "symbol_id": "",
        "role": "line_owner",
        "reviewer": "",
        "verified_by": "",
    }
    memberships = [membership]
    digest = builder.canonical_membership_sha256(memberships)
    batch_id = "BATCH-002" if mutation == "gap" else "BATCH-001"
    if mutation == "gap":
        membership["batch"] = batch_id
        digest = builder.canonical_membership_sha256(memberships)
    content = f"# {batch_id}\n\n- Membership-SHA256: `{digest}`\n".encode()
    if mutation != "sections":
        content += b"\n## Scope\n\n## Verplichte reviewchecklist\n\n## Bevindingen\n\n## Resultaat\n"
    if mutation == "digest":
        content = content.replace(digest.encode(), b"0" * 64)
    manifest_dir = tmp_path / "batches"
    manifest_dir.mkdir()
    (manifest_dir / f"{batch_id}.md").write_bytes(content)
    if mutation == "stale":
        (manifest_dir / "BATCH-999.md").write_text("stale\n", encoding="utf-8")
    indexes = [
        {
            "batch": batch_id,
            "status": "pending",
            "reviewer": "",
            "verified_by": "",
            "manifest_sha256": hashlib.sha256(content).hexdigest(),
            "membership_sha256": digest,
        }
    ]

    errors = validator._validate_batch_index(indexes, memberships, tmp_path, False)

    assert any(expected_error in error for error in errors)
