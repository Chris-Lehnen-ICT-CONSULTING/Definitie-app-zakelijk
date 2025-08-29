"""
Generate an AS-IS source tree section and inject it into docs/architecture/source-tree.md.

The script looks for markers:
  <!-- AS-IS: BEGIN AUTO-GENERATED -->
  <!-- AS-IS: END AUTO-GENERATED -->
and replaces the content in between with a Markdown code block containing a
compact directory tree for the `src/` folder (depth-limited).
"""

from __future__ import annotations

from pathlib import Path

DOC_PATH = Path("docs/architecture/source-tree.md")
BEGIN_MARK = "<!-- AS-IS: BEGIN AUTO-GENERATED -->"
END_MARK = "<!-- AS-IS: END AUTO-GENERATED -->"


def build_tree(root: Path, max_depth: int = 2) -> str:
    lines: list[str] = []

    def walk(dir_path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(
                [p for p in dir_path.iterdir() if not p.name.startswith(".")],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except FileNotFoundError:
            return
        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir() and depth < max_depth:
                new_prefix = prefix + ("    " if i == len(entries) - 1 else "│   ")
                walk(entry, new_prefix, depth + 1)

    lines.append("src/")
    walk(root, "", 1)
    return "\n".join(lines)


def inject(md_path: Path, content: str) -> None:
    text = md_path.read_text(encoding="utf-8")
    if BEGIN_MARK not in text or END_MARK not in text:
        error_msg = "Markers not found in document."
        raise RuntimeError(error_msg)
    start = text.index(BEGIN_MARK) + len(BEGIN_MARK)
    end = text.index(END_MARK)
    before = text[:start]
    after = text[end:]
    block = f"\n\n```\n{content}\n```\n\n"
    md_path.write_text(before + block + after, encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"
    tree = build_tree(src_root, max_depth=2)
    inject(DOC_PATH, tree)


if __name__ == "__main__":
    main()
