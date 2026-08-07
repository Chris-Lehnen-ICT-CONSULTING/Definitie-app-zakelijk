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
import tokenize

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
        writer = csv.DictWriter(handle, fieldnames=fields)
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
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--untracked-root", type=pathlib.Path)
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    args = _parse_args(arguments)
    try:
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
