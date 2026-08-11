# BATCH-099 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 11/11 blobs, 3848/3848 fysieke regels en 100/100 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De import-v9-unitset gaf 22/22 groen; Ruff en Black waren schoon op 36 Pythonbestanden en bash -n op zeven shellbestanden.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B099-001 — P2 — AI review tools fail open when checks are unavailable or malformed

**Bewijs:** Missing executables are only warned about and never make all_passed false; the wrapper also resolves the project root to scripts. The companion reviewers similarly return no issues for missing tools or malformed Ruff output.

**Reproductie:** Mock every subprocess call to raise FileNotFoundError: both reviewers return true with an empty issue list. Return malformed Ruff JSON to EnhancedCodeReviewer and it returns an empty category map.

**Aanbevolen oplossing:** Treat missing tools, nonzero infrastructure results and parse failures as explicit review failures; resolve and validate the repository root before running checks.

### B099-002 — P2 — Dashboard Make target points to a missing script and the real generator uses the wrong root

**Bewijs:** The target invokes scripts/generate_requirements_dashboard.py, while the only file is under scripts/docs. That script uses parents[1], making scripts rather than the repository its root.

**Reproductie:** Resolve the Make target against the base tree: the path is absent. Inspect the real generator root and observe all docs/output paths are rooted below scripts.

**Aanbevolen oplossing:** Use the canonical script path, derive the repository with parents[2], and add a smoke test requiring nonempty input and expected output locations.

### B099-003 — P2 — Documentation compliance audit scans an empty scripts directory and exits successfully

**Bewijs:** project_root is the scripts directory, so docs_dir becomes scripts/docs. The immutable tree has zero Markdown files there versus 707 under repository docs, yet main writes a report and returns zero.

**Reproductie:** Count Markdown blobs below scripts/docs and docs, then follow main over the empty iterator; it reports zero checked files and success.

**Aanbevolen oplossing:** Resolve the repository root correctly, require a nonzero expected inventory and return nonzero for empty scope or compliance failures.

### B099-004 — P2 — Requirements frontmatter normalizer destroys nested YAML and lists

**Bewijs:** The line-based parser only retains scalar key-value pairs and the renderer cannot preserve nested mappings. Nested links.epics, links.requirements and lists became empty top-level scalars in the isolated repro.

**Reproductie:** Parse and render frontmatter containing links with nested epics and requirements lists; the resulting YAML loses the nesting and values.

**Aanbevolen oplossing:** Use a real YAML round trip with schema validation and regression fixtures for nested maps, lists, comments and quoting.

### B099-005 — P2 — Documentation link fixer writes workstation-absolute paths for sibling targets

**Bewijs:** rel_from uses Path.relative_to, which only works for descendants; on failure it serializes the absolute target path. Canonical requirement and epic targets are commonly siblings of the source directory.

**Reproductie:** Call rel_from for /repo/docs/backlog/requirements/REQ-001.md from /repo/docs/other; it returns the full /repo path.

**Aanbevolen oplossing:** Use os.path.relpath or equivalent URI-relative logic and test links across sibling documentation directories.

### B099-006 — P2 — Requirements dashboard emits unescaped Markdown and metadata into HTML and script

**Bewijs:** Headers, paragraphs and list items are inserted without HTML escaping; requirement and epic metadata are also interpolated into HTML and inline JSON without script-safe escaping. Current Make/root failures block the normal flow but the sink is executable when called directly.

**Reproductie:** Render a title containing an img onerror attribute and Markdown containing a script tag in a temporary output directory; both strings remain raw in generated HTML.

**Aanbevolen oplossing:** Escape all text and attributes, use a vetted Markdown sanitizer and embed JSON with script-closing sequences safely escaped under a restrictive CSP.

### B099-007 — P3 — Markdown dashboard fallback links every requirement to the last source path

**Bewijs:** req_path_rel is calculated in the preceding HTML loop and reused unchanged for every Markdown row.

**Reproductie:** Render two requirements backed by a.md and b.md; both fallback rows link to b.md.

**Aanbevolen oplossing:** Calculate the relative requirement path inside the Markdown row loop and add a multi-row link regression test.

### B099-008 — P2 — Source-tree generator can replace architecture documentation with an empty tree

**Bewijs:** main resolves repo_root to scripts and therefore searches scripts/src; build_tree silently returns only the src root label when that directory is missing, then inject overwrites the marked section.

**Reproductie:** Run build_tree against a missing temporary directory; it returns only 'src/'. Follow main path resolution from the immutable script location.

**Aanbevolen oplossing:** Resolve the actual repository root and abort before writing when the source directory is absent or the generated inventory is empty.

### B099-009 — P3 — Generated dashboard interactions lack keyboard semantics, labels and responsive containment

**Bewijs:** Sortable table headers react only to delegated click events and expose no button semantics or keyboard handler; the search input relies on placeholder text. Fixed-width controls and wide tables have no responsive overflow strategy; SVG nodes are also click-only later in the file.

**Reproductie:** Inspect the generated markup and handlers: there are no labels, tabindex, roles or key handlers for sorting and graph navigation. Browser and screen-reader execution were not performed.

**Aanbevolen oplossing:** Use labelled inputs and real buttons or keyboard-enabled headers with ARIA sort state, make graph nodes focusable with names, and add responsive table/SVG containment tests.

## Niet getest

- Geen destructive scripts op echte documentatie, geen live GitHub/Linear/Wikipedia/AI-tools of credentials, en geen browser/screenreader/spreadsheet-executie.
