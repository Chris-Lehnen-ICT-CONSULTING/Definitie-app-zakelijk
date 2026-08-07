#!/usr/bin/env python3
"""Build a lossless review inventory from one immutable Git commit."""

from __future__ import annotations

import argparse
import ast
import base64
import csv
import datetime
import hashlib
import json
import mimetypes
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import tokenize
from collections import Counter

FILE_FIELDS = [
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
    "status",
    "reviewer",
    "verified_by",
    "reviewed_at",
    "finding_ids",
    "notes",
]
SYMBOL_FIELDS = [
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
    "status",
    "reviewer",
    "verified_by",
    "test_ids",
    "finding_ids",
    "notes",
]
LINE_COVERAGE_FIELDS = [
    "path",
    "path_b64",
    "reviewed_object_id",
    "start_line",
    "end_line",
    "classification",
    "batch",
    "status",
    "reviewer",
    "verified_by",
    "finding_ids",
    "notes",
]
BATCH_MEMBERSHIP_FIELDS = [
    "batch",
    "path",
    "path_b64",
    "reviewed_object_id",
    "start_line",
    "end_line",
    "symbol_id",
    "role",
    "reviewer",
    "verified_by",
]
BATCH_INDEX_FIELDS = [
    "batch",
    "status",
    "reviewer",
    "verified_by",
    "manifest_sha256",
    "membership_sha256",
]
REVIEW_INFRASTRUCTURE_FIELDS = [
    "path",
    "tooling_sha",
    "blob_sha",
    "physical_lines",
    "status",
    "reviewer",
    "verified_by",
    "test_result",
    "notes",
]
UNTRACKED_FIELDS = [
    "path",
    "path_b64",
    "source_root",
    "captured_at",
    "content_sha256",
    "file_type",
    "bytes",
    "scope_tier",
    "status",
    "reviewer",
    "verified_by",
    "owner",
    "notes",
]
EXCLUSION_FIELDS = ["path", "path_b64", "reason", "approved_by", "notes"]
FINDING_FIELDS = [
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
    "verified_by",
]

PILOT_PATHS = (
    "src/main.py",
    "src/services/service_factory.py",
    "src/database/db_connection.py",
    "src/ui/components/definition_generator_tab.py",
    "tests/smoke/test_critical_paths.py",
    "tests/unit/database/test_transactie_atomiciteit.py",
    "tests/unit/services/test_service_factory_caching.py",
    "tests/unit/ui/test_definition_generator_tab_generation_details.py",
)
REVIEW_GROUP_TITLES = {
    0: "Pilot: entrypoint, service, database, UI en gekoppelde tests",
    1: "Entrypoints, build, dependencies en configuratie",
    2: "Security en FastAPI",
    3: "Domain, models, ontologie en classificatie",
    4: "Database, repositories, schema en migraties",
    5: "AI-clients, interfaces, container en modelrouter",
    6: "Prompts, orchestrators en generatieflow",
    7: "Validatie, toetsregels, opschoning en sanitization",
    8: "Web lookup, document processing en RAG",
    9: "Workflow, import/export, cache en voorbeelden",
    10: "Streamlit state, helpers, renderers en handlers",
    11: "Generatie-, edit-, expert- en beheer-UI",
    12: "Monitoring, utils, CLI, tools en integrations",
    13: "Unit-tests gekoppeld aan productieonderdelen",
    14: "Integration-, contract-, smoke-, performance- en archived-tests",
    15: "Operationele scripts en shellcode",
    16: "JSON, YAML, SQL, prompts en overige runtime-data",
    17: "Documentatie, plannen en handovers",
    18: "Binaire en overige artefacten",
}
MANIFEST_REQUIRED_SECTIONS = (
    "## Scope",
    "## Verplichte reviewchecklist",
    "## Bevindingen",
    "## Resultaat",
)
MANIFEST_CHECKLIST_ITEMS = (
    "Iedere toegewezen regel rechtstreeks uit het immutable object-ID gelezen.",
    "Ieder toegewezen symbool en iedere functie line-by-line beoordeeld.",
    "Callers, afhankelijkheden, tests en foutpaden gecontroleerd.",
    "Codekwaliteit en architectuur beoordeeld.",
    "Bugs, security en foutafhandeling beoordeeld.",
    "Functionaliteit en relevante tests beoordeeld.",
    "UI/UX, toegankelijkheid en responsive gedrag beoordeeld indien van toepassing.",
    "Findings bevatten prioriteit, bewijs, reproductie en oplossing.",
    "Bewezen, vermoed en niet-getest expliciet onderscheiden.",
    "Onafhankelijke tweede reviewer heeft scope en findings geverifieerd.",
)


def _git(
    repo: pathlib.Path, args: list[str], *, input_bytes: bytes | None = None
) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        check=True,
        capture_output=True,
    )
    return result.stdout


def verify_full_commit_sha(repo: pathlib.Path, base_sha: str) -> str:
    """Return the canonical commit SHA and reject abbreviations or tag names."""
    if not base_sha or base_sha != base_sha.strip():
        raise ValueError("REVIEW_BASE_SHA must be a full commit SHA")
    try:
        resolved = _git(repo, ["rev-parse", "--verify", f"{base_sha}^{{commit}}"])
    except subprocess.CalledProcessError as exc:
        raise ValueError("REVIEW_BASE_SHA must identify an existing commit") from exc
    full_sha = resolved.decode("ascii").strip()
    if base_sha.casefold() != full_sha.casefold() or len(base_sha) != len(full_sha):
        raise ValueError("REVIEW_BASE_SHA must be a full commit SHA")
    return full_sha


def _tree_entries(repo: pathlib.Path, base_sha: str) -> list[dict[str, bytes | str]]:
    output = _git(repo, ["ls-tree", "-r", "-z", "--full-tree", base_sha])
    entries: list[dict[str, bytes | str]] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.split(b" ", 2)
        entries.append(
            {
                "raw_path": raw_path,
                "git_mode": mode.decode("ascii"),
                "object_type": object_type.decode("ascii"),
                "object_id": object_id.decode("ascii"),
            }
        )
    return entries


class _CatFileReader:
    def __init__(self, repo: pathlib.Path) -> None:
        self.repo = repo
        self.process: subprocess.Popen[bytes] | None = None

    def __enter__(self) -> _CatFileReader:
        self.process = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=self.repo,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return self

    def read(self, object_id: str) -> tuple[str, bytes]:
        process = self.process
        if process is None or process.stdin is None or process.stdout is None:
            raise RuntimeError("cat-file reader is not open")
        process.stdin.write(object_id.encode("ascii") + b"\n")
        process.stdin.flush()
        header = process.stdout.readline().rstrip(b"\n")
        fields = header.split(b" ")
        if len(fields) != 3:
            raise ValueError(f"unable to read Git object {object_id}: {header!r}")
        _, object_type, raw_size = fields
        size = int(raw_size)
        content = process.stdout.read(size)
        if len(content) != size or process.stdout.read(1) != b"\n":
            raise ValueError(f"truncated Git object {object_id}")
        return object_type.decode("ascii"), content

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        process = self.process
        if process is None:
            return
        if process.stdin is not None:
            process.stdin.close()
        process.wait(timeout=10)
        if process.returncode and exc_type is None:
            stderr = b"" if process.stderr is None else process.stderr.read()
            raise RuntimeError(
                f"git cat-file failed: {stderr.decode(errors='replace')}"
            )
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def _path_fields(raw_path: bytes) -> tuple[str, str]:
    readable = raw_path.decode("utf-8", errors="backslashreplace")
    encoded = base64.b64encode(raw_path).decode("ascii")
    return readable, encoded


def _detect_python_text(content: bytes) -> tuple[str | None, str | None]:
    lines = iter(content.splitlines(keepends=True))
    try:
        encoding, _ = tokenize.detect_encoding(lines.__next__)
        return content.decode(encoding), None
    except (LookupError, SyntaxError, UnicodeDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _is_python_source(raw_path: bytes, content: bytes) -> bool:
    lowered = raw_path.lower()
    return lowered.endswith((b".py", b".pyi", b".pyw")) or (
        content.startswith(b"#!") and b"python" in content.splitlines()[0].lower()
    )


def _expects_utf8_text(raw_path: bytes) -> bool:
    return pathlib.PurePosixPath(
        raw_path.decode("utf-8", errors="ignore")
    ).suffix.lower() in {
        ".csv",
        ".ini",
        ".json",
        ".md",
        ".rst",
        ".sql",
        ".toml",
        ".tsv",
        ".txt",
        ".yaml",
        ".yml",
    }


def _detect_text(
    raw_path: bytes, content: bytes, *, python_source: bool
) -> tuple[str | None, str | None]:
    if python_source:
        return _detect_python_text(content)
    if b"\0" in content:
        return None, None
    try:
        return content.decode("utf-8"), None
    except UnicodeDecodeError as exc:
        if _expects_utf8_text(raw_path):
            return None, f"{type(exc).__name__}: {exc}"
        return None, None


def _file_type(
    path: str,
    content: bytes | None,
    is_binary: bool,
    *,
    python_source: bool = False,
    git_mode: str = "100644",
) -> str:
    if git_mode == "120000":
        return "inode/symlink"
    if content is not None and content.startswith(
        b"version https://git-lfs.github.com/spec/v1\n"
    ):
        return "application/vnd.git-lfs.pointer"
    guessed, _ = mimetypes.guess_type(path)
    if python_source:
        return "text/x-python"
    if guessed:
        return guessed
    return "application/octet-stream" if is_binary else "text/plain"


def _scope_tier(
    path: str,
    *,
    is_binary: bool,
    is_lfs: bool,
    object_type: str,
    git_mode: str = "100644",
) -> str:
    parts = pathlib.PurePosixPath(path).parts
    suffix = pathlib.PurePosixPath(path).suffix.lower()
    name = pathlib.PurePosixPath(path).name
    if is_binary or is_lfs or object_type != "blob" or git_mode == "120000":
        return "F"
    if parts and parts[0] == "tests":
        return "B"
    if parts and parts[0] == "src":
        return "A"
    if (
        name in {"Makefile", "Dockerfile"}
        or (parts and parts[0] in {"scripts", "migrations", ".github"})
        or suffix
        in {
            ".sh",
            ".sql",
        }
    ):
        return "C"
    if (
        name.startswith("requirements")
        or (parts and parts[0] in {"config", "prompts"})
        or suffix
        in {
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
        }
    ):
        return "D"
    return "E"


def _physical_lines(content: bytes) -> int:
    return len(content.splitlines())


def _logical_python_lines(content: bytes) -> int:
    ignored = {
        tokenize.ENCODING,
        tokenize.ENDMARKER,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.COMMENT,
    }
    logical: set[int] = set()
    reader = iter(content.splitlines(keepends=True)).__next__
    try:
        for token in tokenize.tokenize(reader):
            if token.type not in ignored and token.string.strip():
                logical.add(token.start[0])
    except (IndentationError, SyntaxError, tokenize.TokenError, UnicodeDecodeError):
        return 0
    return len(logical)


def _complexity(node: ast.AST) -> int:
    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.score = 1

        def visit_FunctionDef(self, child: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, child: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, child: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, child: ast.ClassDef) -> None:
            return

        def generic_visit(self, child: ast.AST) -> None:
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp)):
                self.score += 1
            elif isinstance(child, ast.BoolOp):
                self.score += max(0, len(child.values) - 1)
            elif isinstance(child, ast.Try):
                self.score += len(child.handlers) + bool(child.orelse)
            elif isinstance(child, ast.Match):
                self.score += len(child.cases)
            elif isinstance(child, ast.comprehension):
                self.score += 1 + len(child.ifs)
            super().generic_visit(child)

    visitor = ComplexityVisitor()
    if isinstance(node, ast.Lambda):
        children = [node.body]
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        children = node.body
    else:
        children = [node]
    for child in children:
        visitor.visit(child)
    return visitor.score


def _module_name(path: str) -> str:
    pure = pathlib.PurePosixPath(path)
    parts = list(pure.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or "<module>"


def _symbol_id(path_b64: str, name: str, kind: str, line: int, col: int) -> str:
    payload = f"{path_b64}\0{name}\0{kind}\0{line}\0{col}".encode()
    return "SYM-" + hashlib.sha256(payload).hexdigest()[:24]


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, path: str, path_b64: str, physical_lines: int) -> None:
        self.path = path
        self.path_b64 = path_b64
        self.rows: list[dict[str, str]] = []
        module_name = _module_name(path)
        module_id = _symbol_id(path_b64, module_name, "module", 1, 0)
        self.stack: list[tuple[str, str, str]] = [(module_id, module_name, "module")]
        self.rows.append(
            self._row(
                module_id,
                module_name,
                "module",
                1 if physical_lines else 0,
                0,
                physical_lines,
                0,
                "",
                "",
                1,
            )
        )

    def _row(
        self,
        symbol_id: str,
        qualified_name: str,
        kind: str,
        start_line: int,
        start_col: int,
        end_line: int,
        end_col: int,
        parent_symbol: str,
        decorators: str,
        complexity: int,
    ) -> dict[str, str]:
        return {
            "symbol_id": symbol_id,
            "path": self.path,
            "path_b64": self.path_b64,
            "qualified_name": qualified_name,
            "kind": kind,
            "start_line": str(start_line),
            "start_col": str(start_col),
            "end_line": str(end_line),
            "end_col": str(end_col),
            "parent_symbol": parent_symbol,
            "decorators": decorators,
            "complexity": str(complexity),
            "status": "pending",
            "reviewer": "",
            "verified_by": "",
            "test_ids": "",
            "finding_ids": "",
            "notes": "",
        }

    def _qualified(self, name: str) -> str:
        parent_name = self.stack[-1][1]
        if self.stack[-1][2] == "module":
            return name
        return f"{parent_name}.{name}"

    @staticmethod
    def _decorators(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> list[str]:
        return [ast.unparse(decorator) for decorator in node.decorator_list]

    def _function_kind(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        decorators: list[str],
    ) -> str:
        is_async = isinstance(node, ast.AsyncFunctionDef)
        parent_kind = self.stack[-1][2]
        if parent_kind == "class":
            if any(name == "property" for name in decorators):
                return "property_getter"
            if any(name.endswith(".setter") for name in decorators):
                return "property_setter"
            if any(name.endswith(".deleter") for name in decorators):
                return "property_deleter"
            if any(name == "staticmethod" for name in decorators):
                return "async_staticmethod" if is_async else "staticmethod"
            if any(name == "classmethod" for name in decorators):
                return "async_classmethod" if is_async else "classmethod"
            return "async_method" if is_async else "method"
        if parent_kind in {
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
        }:
            return "nested_async_function" if is_async else "nested_function"
        return "async_function" if is_async else "function"

    def _visit_definition(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> None:
        decorators = self._decorators(node)
        if isinstance(node, ast.ClassDef):
            kind = "class"
        else:
            kind = self._function_kind(node, decorators)
        qualified = self._qualified(node.name)
        starts = [(node.lineno, node.col_offset)] + [
            (decorator.lineno, max(0, decorator.col_offset - 1))
            for decorator in node.decorator_list
        ]
        start_line, start_col = min(starts)
        symbol_id = _symbol_id(self.path_b64, qualified, kind, start_line, start_col)
        self.rows.append(
            self._row(
                symbol_id,
                qualified,
                kind,
                start_line,
                start_col,
                node.end_lineno or node.lineno,
                node.end_col_offset or node.col_offset,
                self.stack[-1][0],
                ";".join(decorators),
                _complexity(node),
            )
        )
        self.stack.append((symbol_id, qualified, kind))
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_definition(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_definition(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        name = f"<lambda@{node.lineno}:{node.col_offset}>"
        qualified = self._qualified(name)
        symbol_id = _symbol_id(
            self.path_b64, qualified, "lambda", node.lineno, node.col_offset
        )
        self.rows.append(
            self._row(
                symbol_id,
                qualified,
                "lambda",
                node.lineno,
                node.col_offset,
                node.end_lineno or node.lineno,
                node.end_col_offset or node.col_offset,
                self.stack[-1][0],
                "",
                _complexity(node),
            )
        )
        self.stack.append((symbol_id, qualified, "lambda"))
        self.generic_visit(node)
        self.stack.pop()


def _parse_symbols(
    path: str, path_b64: str, text: str, physical_lines: int
) -> list[dict[str, str]]:
    tree = ast.parse(text, filename=path, type_comments=True)
    visitor = _SymbolVisitor(path, path_b64, physical_lines)
    visitor.visit(tree)
    return visitor.rows


def _blocking_finding(
    path: str,
    category: str,
    message: str,
    line: int,
) -> dict[str, str]:
    digest = hashlib.sha256(
        f"{path}\0{category}\0{line}\0{message}".encode()
    ).hexdigest()[:12]
    prefix = "INV-SYNTAX" if category == "python_syntax_error" else "INV-ENCODING"
    return {
        "finding_id": f"{prefix}-{digest.upper()}",
        "priority": "P1",
        "certainty": "proven",
        "review_area": "inventory",
        "title": f"Blocking {category.replace('_', ' ')}",
        "path": path,
        "start_line": str(line),
        "end_line": str(line),
        "evidence": message,
        "reproduction": "Parse the frozen Git blob with the inventory builder",
        "recommendation": "Resolve or explicitly exclude the invalid source before review",
        "status": "blocked",
        "reviewer": "inventory-tool",
        "verified_by": "",
    }


def _is_sensitive_untracked(path: str) -> bool:
    name = pathlib.PurePosixPath(path).name.casefold()
    return (
        name == ".env"
        or name.startswith(".env.")
        or any(token in name for token in ("credential", "private-key", "secret"))
        or pathlib.PurePosixPath(name).suffix in {".key", ".p12", ".pfx", ".pem"}
    )


def _untracked_rows(
    source_root: pathlib.Path,
    captured_at: str | None = None,
) -> list[dict[str, str]]:
    root = source_root.resolve()
    output = _git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    timestamp = captured_at or datetime.datetime.now(datetime.UTC).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    rows: list[dict[str, str]] = []
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        path, path_b64 = _path_fields(raw_path)
        filesystem_path = root / raw_path.decode(
            sys.getfilesystemencoding(), errors="surrogateescape"
        )
        try:
            path_stat = filesystem_path.lstat()
        except OSError:
            path_stat = None
        size = path_stat.st_size if path_stat is not None else 0
        sensitive = _is_sensitive_untracked(path)
        if path_stat is not None and stat.S_ISLNK(path_stat.st_mode):
            content_sha256 = "NOT_SCANNED_SYMLINK"
            notes = "symlink_content_not_read"
        elif path_stat is not None and not stat.S_ISREG(path_stat.st_mode):
            content_sha256 = "NOT_SCANNED_SPECIAL"
            notes = "special_file_content_not_read"
        elif sensitive:
            content_sha256 = "NOT_SCANNED_SECRET"
            notes = "sensitive_content_not_read"
        else:
            digest = hashlib.sha256()
            descriptor: int | None = None
            try:
                flags = os.O_RDONLY
                for optional_flag in ("O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
                    flags |= getattr(os, optional_flag, 0)
                descriptor = os.open(filesystem_path, flags)
                opened_stat = os.fstat(descriptor)
                if not stat.S_ISREG(opened_stat.st_mode):
                    content_sha256 = "NOT_SCANNED_SPECIAL"
                    notes = "special_file_content_not_read"
                elif path_stat is None or (
                    opened_stat.st_dev,
                    opened_stat.st_ino,
                ) != (path_stat.st_dev, path_stat.st_ino):
                    content_sha256 = "UNREADABLE"
                    notes = "content_changed_during_capture"
                else:
                    size = opened_stat.st_size
                    while chunk := os.read(descriptor, 1024 * 1024):
                        digest.update(chunk)
                    content_sha256 = digest.hexdigest()
                    notes = "content_hashed_not_stored"
            except OSError:
                content_sha256 = "UNREADABLE"
                notes = "content_unreadable"
            finally:
                if descriptor is not None:
                    os.close(descriptor)
        file_type = _file_type(path, None, False)
        rows.append(
            {
                "path": path,
                "path_b64": path_b64,
                "source_root": str(root),
                "captured_at": timestamp,
                "content_sha256": content_sha256,
                "file_type": file_type,
                "bytes": str(size),
                "scope_tier": _scope_tier(
                    path,
                    is_binary=False,
                    is_lfs=False,
                    object_type="blob",
                ),
                "status": "pending",
                "reviewer": "",
                "verified_by": "",
                "owner": "user-owned",
                "notes": notes,
            }
        )
    return rows


def canonical_membership_sha256(rows: list[dict[str, str]]) -> str:
    """Hash a batch's membership rows independent of their CSV ordering."""
    normalized = [
        {field: row.get(field, "") for field in BATCH_MEMBERSHIP_FIELDS} for row in rows
    ]
    normalized.sort(
        key=lambda row: tuple(row[field] for field in BATCH_MEMBERSHIP_FIELDS)
    )
    payload = json.dumps(
        normalized, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def review_group(
    path: str, scope_tier: str | None = None, file_type: str | None = None
) -> int:
    """Return the first matching review group from the eighteen-group policy."""
    lowered = path.casefold()
    suffix = pathlib.PurePosixPath(lowered).suffix
    binary_suffixes = {
        ".7z",
        ".db",
        ".gif",
        ".gz",
        ".ico",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".tar",
        ".webp",
        ".zip",
    }
    if (
        scope_tier == "F"
        or suffix in binary_suffixes
        or (file_type or "").startswith(("image/", "application/pdf"))
    ):
        return 18
    if lowered.startswith(
        (".github/", ".trunk/", "config/", ".claude/rules/", ".prompt-forge/")
    ) or pathlib.PurePosixPath(lowered).name in {
        ".gitleaks.toml",
        ".gitleaksignore",
        ".gitignore",
        ".pre-commit-config.yaml",
        "makefile",
        "pyproject.toml",
        "pytest.ini",
        "requirements-dev.in",
        "requirements-dev.txt",
        "requirements.in",
        "requirements.txt",
    }:
        return 1
    if lowered.startswith("tests/unit/"):
        return 13
    if lowered.startswith("tests/"):
        return 14
    if lowered.startswith("scripts/") or suffix in {".sh", ".bash", ".zsh"}:
        return 15
    if lowered.startswith(("docs/", "project-documentation/")):
        return 17
    if lowered == "src/validation/sanitizer.py":
        return 2
    if lowered.startswith(
        ("src/toetsregels/", "src/services/validation/", "src/validation/")
    ) or any(
        token in lowered
        for token in (
            "cleaning_service",
            "validation_renderer",
            "validation_rules",
            "validation_view",
        )
    ):
        return 7
    if lowered.startswith(("src/api/", "src/security/")) or any(
        token in lowered for token in ("rate_limit", "security_service", "sanitization")
    ):
        return 2
    if lowered.startswith(
        (
            "src/domain/",
            "src/models/",
            "src/ontologie/",
            "src/services/classification/",
            "src/services/ontology/",
        )
    ):
        return 3
    if lowered.startswith(("src/database/", "src/repositories/")) or any(
        token in lowered
        for token in ("repository", "metadata_schema", "/migrations/", "schema.sql")
    ):
        return 4
    if (
        lowered.startswith("src/services/ai/")
        or lowered
        in {
            "src/services/container.py",
            "src/services/interfaces.py",
        }
        or any(token in lowered for token in ("model_router", "ai_client"))
    ):
        return 5
    if lowered.startswith(("prompts/", "src/services/definition_generator")) or any(
        token in lowered
        for token in (
            "generation_handler",
            "orchestrator",
            "prompt_",
            "/prompts/",
            "regeneration",
        )
    ):
        return 6
    if lowered.startswith(
        (
            "src/document_processing/",
            "src/services/rag/",
            "src/services/web_lookup/",
            "data/uploads/documents/",
        )
    ) or any(token in lowered for token in ("modern_web_lookup", "document_upload")):
        return 8
    if (
        lowered == "src/ui/session_state.py"
        or lowered.startswith(
            ("src/ui/helpers/", "src/ui/handlers/", "src/ui/renderers/")
        )
        or any(
            token in lowered
            for token in (
                "category_renderer",
                "context_state_cleaner",
                "duplicate_check_renderer",
                "examples_renderer",
                "sources_renderer",
            )
        )
    ):
        return 10
    if lowered.startswith(("src/export/", "src/voorbeelden/")) or any(
        token in lowered
        for token in (
            "/cache",
            "_cache",
            "definition_import",
            "import_export",
            "workflow",
            "export",
            "voorbeelden",
        )
    ):
        return 9
    if lowered.startswith("src/ui/"):
        return 11
    if lowered.startswith(("src/", "tools/")):
        return 12
    if lowered.startswith(("data/", "runtime/")) or suffix in {
        ".json",
        ".sql",
        ".yaml",
        ".yml",
    }:
        return 16
    if suffix in {".html", ".md", ".rst"}:
        return 17
    return 18


def _raw_path_sort_key(row: dict[str, str]) -> bytes:
    return base64.b64decode(row["path_b64"], validate=True)


def _symbols_for_path(
    symbols: list[dict[str, str]], path_b64: str
) -> list[dict[str, str]]:
    return sorted(
        (row for row in symbols if row["path_b64"] == path_b64),
        key=lambda row: (
            int(row["start_line"]),
            int(row["start_col"]),
            int(row["end_line"]),
            int(row["end_col"]),
            row["symbol_id"],
        ),
    )


def _file_chunks(
    file_row: dict[str, str],
    symbols: list[dict[str, str]],
    line_limit: int,
) -> list[tuple[int, int, list[dict[str, str]]]]:
    physical = int(file_row.get("physical_lines") or 0)
    if physical == 0:
        return [(0, 0, symbols)]
    starts = Counter(int(symbol["start_line"]) for symbol in symbols)
    for line, count in starts.items():
        if count > 150:
            raise ValueError(f"{count} symbols share line {line} in {file_row['path']}")
    chunks: list[tuple[int, int, list[dict[str, str]]]] = []
    start = 1
    while start <= physical:
        end = min(start + line_limit - 1, physical)
        candidates = [
            symbol for symbol in symbols if start <= int(symbol["start_line"]) <= end
        ]
        if len(candidates) > 150:
            count = 0
            split_before: int | None = None
            for line in sorted({int(symbol["start_line"]) for symbol in candidates}):
                line_count = starts[line]
                if count + line_count > 150:
                    split_before = line
                    break
                count += line_count
            if split_before is None or split_before <= start:
                raise ValueError(
                    f"cannot split symbols safely at line {start} in {file_row['path']}"
                )
            end = split_before - 1
            candidates = [
                symbol
                for symbol in symbols
                if start <= int(symbol["start_line"]) <= end
            ]
        chunks.append((start, end, candidates))
        start = end + 1
    return chunks


def _line_template(
    rows: list[dict[str, str]], path_b64: str, start: int, end: int
) -> dict[str, str]:
    candidates = [row for row in rows if row["path_b64"] == path_b64]
    if not candidates:
        raise ValueError(f"line coverage missing for {path_b64}")
    exact = next(
        (
            row
            for row in candidates
            if row["start_line"] == str(start) and row["end_line"] == str(end)
        ),
        None,
    )
    if exact is not None:
        return exact
    return next(
        (
            row
            for row in candidates
            if int(row["start_line"]) <= start <= int(row["end_line"])
        ),
        candidates[0],
    )


def _manifest_path(path: str) -> str:
    escaped = json.dumps(path, ensure_ascii=True)[1:-1]
    return (
        escaped.replace("#", r"\u0023").replace("|", r"\u007c").replace("`", r"\u0060")
    )


def _render_manifest(
    batch: str,
    group: int,
    base_sha: str,
    memberships: list[dict[str, str]],
    index_lifecycle: dict[str, str],
) -> bytes:
    line_owners = [row for row in memberships if row["role"] == "line_owner"]
    symbol_owners = [row for row in memberships if row["role"] == "symbol_owner"]
    digest = canonical_membership_sha256(memberships)
    physical_lines = sum(
        (
            0
            if row["start_line"] == row["end_line"] == "0"
            else int(row["end_line"]) - int(row["start_line"]) + 1
        )
        for row in line_owners
    )
    unique_files = len({row["path_b64"] for row in line_owners})
    final = index_lifecycle.get("status") == "verified"
    checkbox = "x" if final else " "
    lines = [
        f"# {batch}",
        "",
        f"- Status: `{index_lifecycle.get('status', 'pending')}`",
        f"- Reviewgroep: `{group}` — {REVIEW_GROUP_TITLES[group]}",
        f"- Review-base: `{base_sha}`",
        f"- Membership-SHA256: `{digest}`",
        f"- Bestanden: `{unique_files}`",
        f"- Fysieke regels: `{physical_lines}`",
        f"- Python-symbolen: `{len(symbol_owners)}`",
        f"- Reviewer: `{index_lifecycle.get('reviewer', '')}`",
        f"- Onafhankelijke verifier: `{index_lifecycle.get('verified_by', '')}`",
        "",
        "## Scope",
        "",
        "| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |",
        "|---|---|---:|---:|---|",
    ]
    for row in line_owners:
        start, end = int(row["start_line"]), int(row["end_line"])
        symbol_count = sum(
            owner["path_b64"] == row["path_b64"]
            and start <= int(owner["start_line"]) <= end
            for owner in symbol_owners
        )
        lines.append(
            f"| `{_manifest_path(row['path'])}` | `{row['path_b64']}` | "
            f"`{row['start_line']}-{row['end_line']}` | {symbol_count} | "
            f"`{row['reviewed_object_id']}` |"
        )
    lines.extend(["", "## Verplichte reviewchecklist", ""])
    lines.extend(f"- [{checkbox}] {item}" for item in MANIFEST_CHECKLIST_ITEMS)
    lines.extend(
        [
            "",
            "## Bevindingen",
            "",
            "Nog niet geregistreerd.",
            "",
            "## Resultaat",
            "",
            "Geverifieerd." if final else "Nog niet uitgevoerd.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _ownership_fingerprint(rows: list[dict[str, str]]) -> tuple[tuple[str, ...], ...]:
    fields = (
        "path_b64",
        "reviewed_object_id",
        "start_line",
        "end_line",
        "symbol_id",
        "role",
    )
    return tuple(sorted(tuple(row.get(field, "") for field in fields) for row in rows))


def plan_batches(
    inventory: dict[str, object],
    *,
    base_sha: str,
    pilot_paths: tuple[str, ...] | list[str] = PILOT_PATHS,
) -> dict[str, object]:
    """Plan deterministic ownership without rebuilding the frozen inventory."""
    files = [dict(row) for row in inventory["files"]]  # type: ignore[index]
    symbols = [dict(row) for row in inventory["symbols"]]  # type: ignore[index]
    old_lines = [dict(row) for row in inventory["line_coverage"]]  # type: ignore[index]
    old_memberships = [
        dict(row) for row in inventory.get("batch_membership", [])  # type: ignore[union-attr]
    ]
    old_indexes = {
        row["batch"]: dict(row)
        for row in inventory.get("batch_index", [])  # type: ignore[union-attr]
    }
    files_by_path = {row["path"]: row for row in files}
    missing_pilot = sorted(set(pilot_paths) - files_by_path.keys())
    if missing_pilot:
        raise ValueError(f"pilot paths missing: {', '.join(missing_pilot)}")

    chunks: list[dict[str, object]] = []
    pilot_set = set(pilot_paths)
    if pilot_paths:
        for path in sorted(pilot_paths, key=lambda item: item.encode("utf-8")):
            file_row = files_by_path[path]
            path_symbols = _symbols_for_path(symbols, file_row["path_b64"])
            physical = int(file_row.get("physical_lines") or 0)
            chunks.append(
                {
                    "file": file_row,
                    "start": 0 if physical == 0 else 1,
                    "end": physical,
                    "symbols": path_symbols,
                    "group": 0,
                    "code_class": "ABC",
                }
            )

    regular_files = sorted(
        (row for row in files if row["path"] not in pilot_set),
        key=lambda row: (
            review_group(row["path"], row["scope_tier"], row["file_type"]),
            0 if row["scope_tier"] in {"A", "B", "C"} else 1,
            row["scope_tier"],
            _raw_path_sort_key(row),
        ),
    )
    for file_row in regular_files:
        code_class = "ABC" if file_row["scope_tier"] in {"A", "B", "C"} else "DEF"
        group = review_group(
            file_row["path"], file_row["scope_tier"], file_row["file_type"]
        )
        line_limit = 4000 if code_class == "ABC" else 6000
        path_symbols = _symbols_for_path(symbols, file_row["path_b64"])
        for start, end, chunk_symbols in _file_chunks(
            file_row, path_symbols, line_limit
        ):
            chunks.append(
                {
                    "file": file_row,
                    "start": start,
                    "end": end,
                    "symbols": chunk_symbols,
                    "group": group,
                    "code_class": code_class,
                }
            )

    packed: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for chunk in chunks:
        group = int(chunk["group"])
        code_class = str(chunk["code_class"])
        if group == 0:
            if current is None or int(current["group"]) != 0:
                if current is not None:
                    packed.append(current)
                current = {"group": 0, "code_class": "ABC", "chunks": []}
            current["chunks"].append(chunk)  # type: ignore[union-attr]
            continue
        file_limit = 20 if code_class == "ABC" else 30
        line_limit = 4000 if code_class == "ABC" else 6000
        chunk_lines = (
            0
            if chunk["start"] == chunk["end"] == 0
            else int(chunk["end"]) - int(chunk["start"]) + 1
        )
        must_start = (
            current is None
            or int(current["group"]) != group
            or str(current["code_class"]) != code_class
        )
        if not must_start:
            candidate_chunks = [*current["chunks"], chunk]  # type: ignore[index]
            candidate_files = {
                item["file"]["path_b64"] for item in candidate_chunks  # type: ignore[index]
            }
            candidate_lines = sum(
                (
                    0
                    if item["start"] == item["end"] == 0
                    else int(item["end"]) - int(item["start"]) + 1
                )
                for item in candidate_chunks
            )
            candidate_symbols = sum(
                len(item["symbols"]) for item in candidate_chunks  # type: ignore[arg-type]
            )
            must_start = (
                len(candidate_files) > file_limit
                or candidate_lines > line_limit
                or candidate_symbols > 150
            )
        if must_start:
            if current is not None:
                packed.append(current)
            current = {"group": group, "code_class": code_class, "chunks": []}
        current["chunks"].append(chunk)  # type: ignore[union-attr]
        if chunk_lines > line_limit or len(chunk["symbols"]) > 150:  # type: ignore[arg-type]
            raise ValueError(f"unsplittable batch item: {chunk['file']['path']}")  # type: ignore[index]
    if current is not None:
        packed.append(current)

    old_membership_map = {
        (
            row["batch"],
            row["path_b64"],
            row["start_line"],
            row["end_line"],
            row["role"],
            row["symbol_id"],
        ): row
        for row in old_memberships
    }
    new_lines: list[dict[str, str]] = []
    memberships: list[dict[str, str]] = []
    batch_groups: dict[str, int] = {}
    for number, packed_batch in enumerate(packed, start=1):
        batch = f"BATCH-{number:03d}"
        batch_groups[batch] = int(packed_batch["group"])
        for chunk in packed_batch["chunks"]:  # type: ignore[assignment]
            file_row = chunk["file"]
            start, end = int(chunk["start"]), int(chunk["end"])
            template = _line_template(old_lines, file_row["path_b64"], start, end)
            line_row = dict(template)
            line_row.update(
                start_line=str(start),
                end_line=str(end),
                batch=batch,
                reviewed_object_id=file_row["object_id"],
            )
            new_lines.append(line_row)
            line_key = (
                batch,
                file_row["path_b64"],
                str(start),
                str(end),
                "line_owner",
                "",
            )
            old_line_owner = old_membership_map.get(line_key, {})
            memberships.append(
                {
                    "batch": batch,
                    "path": file_row["path"],
                    "path_b64": file_row["path_b64"],
                    "reviewed_object_id": file_row["object_id"],
                    "start_line": str(start),
                    "end_line": str(end),
                    "symbol_id": "",
                    "role": "line_owner",
                    "reviewer": old_line_owner.get("reviewer", ""),
                    "verified_by": old_line_owner.get("verified_by", ""),
                }
            )
            for symbol in chunk["symbols"]:
                symbol_key = (
                    batch,
                    file_row["path_b64"],
                    symbol["start_line"],
                    symbol["end_line"],
                    "symbol_owner",
                    symbol["symbol_id"],
                )
                old_symbol_owner = old_membership_map.get(symbol_key, {})
                memberships.append(
                    {
                        "batch": batch,
                        "path": file_row["path"],
                        "path_b64": file_row["path_b64"],
                        "reviewed_object_id": file_row["object_id"],
                        "start_line": symbol["start_line"],
                        "end_line": symbol["end_line"],
                        "symbol_id": symbol["symbol_id"],
                        "role": "symbol_owner",
                        "reviewer": old_symbol_owner.get("reviewer", ""),
                        "verified_by": old_symbol_owner.get("verified_by", ""),
                    }
                )

    old_by_batch: dict[str, list[dict[str, str]]] = {}
    new_by_batch: dict[str, list[dict[str, str]]] = {}
    for row in old_memberships:
        old_by_batch.setdefault(row["batch"], []).append(row)
    for row in memberships:
        new_by_batch.setdefault(row["batch"], []).append(row)
    stable_batches = {
        batch
        for batch, batch_memberships in new_by_batch.items()
        if batch in old_indexes
        and _ownership_fingerprint(batch_memberships)
        == _ownership_fingerprint(old_by_batch.get(batch, []))
    }
    for row in memberships:
        if row["batch"] not in stable_batches:
            row.update(reviewer="", verified_by="")
    for row in new_lines:
        if row["batch"] not in stable_batches:
            if row.get("status") != "blocked":
                row["status"] = "pending"
            row.update(reviewer="", verified_by="")

    indexes: list[dict[str, str]] = []
    manifests: dict[str, bytes] = {}
    for batch in sorted(batch_groups):
        batch_memberships = [row for row in memberships if row["batch"] == batch]
        lifecycle = (
            old_indexes[batch]
            if batch in stable_batches
            else {"status": "pending", "reviewer": "", "verified_by": ""}
        )
        manifest = _render_manifest(
            batch,
            batch_groups[batch],
            base_sha,
            batch_memberships,
            lifecycle,
        )
        manifests[f"{batch}.md"] = manifest
        indexes.append(
            {
                "batch": batch,
                "status": lifecycle.get("status", "pending"),
                "reviewer": lifecycle.get("reviewer", ""),
                "verified_by": lifecycle.get("verified_by", ""),
                "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
                "membership_sha256": canonical_membership_sha256(batch_memberships),
            }
        )
    return {
        "line_coverage": new_lines,
        "batch_membership": memberships,
        "batch_index": indexes,
        "manifests": manifests,
    }


def _read_inventory_csv(path: pathlib.Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != fields:
            raise ValueError(f"invalid header in {path.name}")
        return [{field: row.get(field) or "" for field in fields} for row in reader]


def load_planning_inventory(scope_dir: pathlib.Path | str) -> dict[str, object]:
    scope = pathlib.Path(scope_dir)
    return {
        "files": _read_inventory_csv(scope / "file-inventory.csv", FILE_FIELDS),
        "symbols": _read_inventory_csv(scope / "symbol-inventory.csv", SYMBOL_FIELDS),
        "line_coverage": _read_inventory_csv(
            scope / "line-coverage.csv", LINE_COVERAGE_FIELDS
        ),
        "batch_membership": _read_inventory_csv(
            scope / "batch-membership.csv", BATCH_MEMBERSHIP_FIELDS
        ),
        "batch_index": _read_inventory_csv(
            scope / "batch-index.csv", BATCH_INDEX_FIELDS
        ),
    }


def write_batch_plan(
    plan: dict[str, object], review_dir: pathlib.Path | str, *, update: bool
) -> None:
    review = pathlib.Path(review_dir)
    manifest_dir = review / "batches"
    expected_names = set(plan["manifests"])  # type: ignore[arg-type]
    existing_names = {path.name for path in manifest_dir.glob("BATCH-*.md")}
    if existing_names and not update:
        raise ValueError("batch manifests already exist; use update mode")
    if existing_names and existing_names != expected_names:
        raise ValueError(
            "unexpected batch manifest set: "
            f"expected {sorted(expected_names)}, got {sorted(existing_names)}"
        )
    stage = pathlib.Path(tempfile.mkdtemp(prefix="batch-plan-"))
    stage_scope = stage / "scope"
    stage_manifests = stage / "batches"
    _write_csv(
        stage_scope / "line-coverage.csv",
        LINE_COVERAGE_FIELDS,
        plan["line_coverage"],  # type: ignore[arg-type]
    )
    _write_csv(
        stage_scope / "batch-membership.csv",
        BATCH_MEMBERSHIP_FIELDS,
        plan["batch_membership"],  # type: ignore[arg-type]
    )
    _write_csv(
        stage_scope / "batch-index.csv",
        BATCH_INDEX_FIELDS,
        plan["batch_index"],  # type: ignore[arg-type]
    )
    stage_manifests.mkdir(parents=True, exist_ok=True)
    for name, content in plan["manifests"].items():  # type: ignore[union-attr]
        (stage_manifests / name).write_bytes(content)
    (review / "scope").mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for name in ("line-coverage.csv", "batch-membership.csv", "batch-index.csv"):
        os.replace(stage_scope / name, review / "scope" / name)
    for name in sorted(expected_names):
        os.replace(stage_manifests / name, manifest_dir / name)


def plan_existing_review(
    review_dir: pathlib.Path | str,
    *,
    base_sha: str,
    update: bool,
    pilot_paths: tuple[str, ...] | list[str] = PILOT_PATHS,
) -> dict[str, object]:
    review = pathlib.Path(review_dir)
    inventory = load_planning_inventory(review / "scope")
    plan = plan_batches(inventory, base_sha=base_sha, pilot_paths=pilot_paths)
    write_batch_plan(plan, review, update=update)
    return plan


def build_inventory(
    repo_root: pathlib.Path | str,
    base_sha: str,
    *,
    untracked_root: pathlib.Path | str | None = None,
    captured_at: str | None = None,
    include_untracked: bool = True,
) -> dict[str, list[dict[str, str]]]:
    repo = pathlib.Path(repo_root).resolve()
    full_sha = verify_full_commit_sha(repo, base_sha)
    entries = _tree_entries(repo, full_sha)
    files: list[dict[str, str]] = []
    symbols: list[dict[str, str]] = []
    line_coverage: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []

    with _CatFileReader(repo) as reader:
        for entry in entries:
            raw_path = entry["raw_path"]
            assert isinstance(raw_path, bytes)
            path, path_b64 = _path_fields(raw_path)
            object_type = str(entry["object_type"])
            object_id = str(entry["object_id"])
            git_mode = str(entry["git_mode"])
            content: bytes | None = None
            if object_type == "blob":
                actual_type, content = reader.read(object_id)
                if actual_type != object_type:
                    raise ValueError(f"Git object type changed for {path}")

            status = "pending"
            finding_ids = ""
            notes: list[str] = []
            text: str | None = None
            encoding_error: str | None = None
            python_source = bool(
                content is not None and _is_python_source(raw_path, content)
            )
            if content is not None:
                text, encoding_error = _detect_text(
                    raw_path,
                    content,
                    python_source=python_source,
                )
            is_binary = content is not None and text is None and encoding_error is None
            is_symlink = git_mode == "120000"
            is_lfs = bool(
                content
                and content.startswith(b"version https://git-lfs.github.com/spec/v1\n")
            )
            physical = ""
            logical = ""
            if content is not None and not is_binary and not is_symlink:
                physical_count = _physical_lines(content)
                physical = str(physical_count)
                if python_source:
                    logical = str(_logical_python_lines(content))
                elif text is not None:
                    logical = str(sum(bool(line.strip()) for line in text.splitlines()))
            else:
                physical_count = 0

            if encoding_error is not None:
                status = "blocked"
                category = (
                    "python_encoding_error" if python_source else "text_encoding_error"
                )
                finding = _blocking_finding(path, category, encoding_error, 1)
                findings.append(finding)
                finding_ids = finding["finding_id"]
                notes.append(f"blocking_finding={category}; {encoding_error}")
            elif python_source and text is not None:
                try:
                    symbols.extend(_parse_symbols(path, path_b64, text, physical_count))
                except SyntaxError as exc:
                    status = "blocked"
                    message = (
                        f"{exc.msg} at line {exc.lineno or 1}, column {exc.offset or 0}"
                    )
                    finding = _blocking_finding(
                        path,
                        "python_syntax_error",
                        message,
                        exc.lineno or 1,
                    )
                    findings.append(finding)
                    finding_ids = finding["finding_id"]
                    notes.append(f"blocking_finding=python_syntax_error; {message}")

            if is_binary:
                notes.extend(["binary_review_required", "line_by_line_not_applicable"])
            if object_type == "commit":
                notes.append("gitlink_review_required")
            if is_symlink:
                notes.append("symlink_review_required")
            if is_lfs:
                notes.append("git_lfs_pointer_review_required")

            file_type = _file_type(
                path,
                content,
                is_binary or object_type != "blob",
                python_source=python_source,
                git_mode=git_mode,
            )
            tier = _scope_tier(
                path,
                is_binary=is_binary,
                is_lfs=is_lfs,
                object_type=object_type,
                git_mode=git_mode,
            )
            file_row = {
                "path": path,
                "path_b64": path_b64,
                "git_mode": git_mode,
                "object_type": object_type,
                "object_id": object_id,
                "file_type": file_type,
                "bytes": str(len(content)) if content is not None else "",
                "physical_lines": physical,
                "logical_lines": logical,
                "scope_tier": tier,
                "status": status,
                "reviewer": "",
                "verified_by": "",
                "reviewed_at": "",
                "finding_ids": finding_ids,
                "notes": "; ".join(notes),
            }
            files.append(file_row)

            if object_type != "blob" or is_binary or is_symlink:
                start_line = end_line = "0"
                if object_type == "commit":
                    classification = "gitlink_equivalent_review"
                elif is_symlink:
                    classification = "symlink_equivalent_review"
                else:
                    classification = "binary_equivalent_review"
            elif physical_count == 0:
                start_line = end_line = "0"
                classification = "empty_file"
            else:
                start_line, end_line = "1", str(physical_count)
                classification = "pending_line_review"
            line_coverage.append(
                {
                    "path": path,
                    "path_b64": path_b64,
                    "reviewed_object_id": object_id,
                    "start_line": start_line,
                    "end_line": end_line,
                    "classification": classification,
                    "batch": "",
                    "status": status,
                    "reviewer": "",
                    "verified_by": "",
                    "finding_ids": finding_ids,
                    "notes": "",
                }
            )

    return {
        "files": files,
        "symbols": symbols,
        "line_coverage": line_coverage,
        "batch_membership": [],
        "batch_index": [],
        "review_infrastructure": [],
        "untracked": (
            _untracked_rows(
                pathlib.Path(untracked_root) if untracked_root is not None else repo,
                captured_at,
            )
            if include_untracked
            else []
        ),
        "exclusions": [],
        "findings": findings,
    }


def _write_csv(
    path: pathlib.Path, fields: list[str], rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_inventory(
    inventory: dict[str, list[dict[str, str]]], output_dir: pathlib.Path | str
) -> None:
    output = pathlib.Path(output_dir)
    outputs = [
        ("file-inventory.csv", FILE_FIELDS, "files"),
        ("symbol-inventory.csv", SYMBOL_FIELDS, "symbols"),
        ("line-coverage.csv", LINE_COVERAGE_FIELDS, "line_coverage"),
        ("batch-membership.csv", BATCH_MEMBERSHIP_FIELDS, "batch_membership"),
        ("batch-index.csv", BATCH_INDEX_FIELDS, "batch_index"),
        (
            "review-infrastructure.csv",
            REVIEW_INFRASTRUCTURE_FIELDS,
            "review_infrastructure",
        ),
        ("untracked-inventory.csv", UNTRACKED_FIELDS, "untracked"),
        ("exclusions.csv", EXCLUSION_FIELDS, "exclusions"),
    ]
    for filename, fields, key in outputs:
        _write_csv(output / filename, fields, inventory[key])
    _write_csv(
        output.parent / "findings" / "findings.csv",
        FINDING_FIELDS,
        inventory["findings"],
    )


def _parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--output-dir", type=pathlib.Path)
    parser.add_argument("--plan-batches", action="store_true")
    parser.add_argument("--review-dir", type=pathlib.Path)
    parser.add_argument("--update-batches", action="store_true")
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--untracked-root", type=pathlib.Path)
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    args = _parse_args(arguments)
    try:
        if args.plan_batches:
            if args.review_dir is None:
                raise ValueError("--review-dir is required with --plan-batches")
            full_sha = verify_full_commit_sha(args.repo_root.resolve(), args.base_sha)
            plan = plan_existing_review(
                args.review_dir,
                base_sha=full_sha,
                update=args.update_batches,
            )
            print(
                f"Planned {len(plan['batch_index'])} batches, "
                f"{len(plan['line_coverage'])} line ranges and "
                f"{len(plan['batch_membership'])} ownership rows."
            )
            return 0
        if args.update_batches:
            raise ValueError("--update-batches requires --plan-batches")
        if args.output_dir is None:
            raise ValueError("--output-dir is required unless --plan-batches is used")
        inventory = build_inventory(
            args.repo_root,
            args.base_sha,
            untracked_root=args.untracked_root,
        )
        write_inventory(inventory, args.output_dir)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"inventory build failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"Inventoried {len(inventory['files'])} files, "
        f"{len(inventory['symbols'])} Python symbols and "
        f"{len(inventory['untracked'])} untracked paths."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
