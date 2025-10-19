#!/usr/bin/env python3
"""
Generate a static, browsable dashboard for requirements and epics.

Outputs:
- docs/dashboard/index.html            (requirements overview with epic links)
- docs/dashboard/epics/<EPIC-ID>.html  (simple rendered view of epic content)
- docs/dashboard/assets/style.css      (basic styling)

Notes:
- Parses frontmatter pragmatically (no external YAML dependency). We support common keys
  like id, title, type, priority, status, and epics list.
- Epic content is rendered with a very small Markdown-to-HTML converter (headers, lists, code blocks,
  paragraphs). This is intentionally lightweight to avoid new dependencies.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ_DIR_PRIMARY = ROOT / "docs" / "requirements"
REQ_DIR_FALLBACK = ROOT / "docs" / "backlog" / "requirements"
EPIC_DIR_PRIMARY = ROOT / "docs" / "epics"
EPIC_DIR_FALLBACK = ROOT / "docs" / "backlog" / "epics"
OUT_DIR = ROOT / "docs" / "backlog" / "dashboard"
OUT_EPICS_DIR = OUT_DIR / "epics"
ASSETS_DIR = OUT_DIR / "assets"


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_EPICS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_frontmatter(md: str) -> dict[str, object]:
    """Extracts naive frontmatter block between first two '---' lines and returns raw key→value lines.

    This is a pragmatic parser to avoid YAML dependency. It supports simple key: value pairs and a single-line
    list for 'epics' like: epics: ["EPIC-001", "EPIC-002"].
    """
    lines = md.splitlines()
    fm_start = None
    fm_end = None
    for i, line in enumerate(lines[:200]):  # only scan the first 200 lines for safety
        if line.strip() == "---":
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break
    result: dict[str, object] = {}
    if fm_start is None or fm_end is None:
        return result
    block = lines[fm_start + 1 : fm_end]
    # Track simplistic nested section for 'links'
    current_section: str | None = None
    i = 0
    while i < len(block):
        raw = block[i]
        line = raw.rstrip()
        if not line or line.strip().startswith("#"):
            i += 1
            continue
        # Normalize indentation for key matching
        lstripped = line.lstrip()
        if (line == lstripped) and re.match(r"^[A-Za-z0-9_]+:\s*$", lstripped):
            # section header e.g. 'links:'
            current_section = lstripped.split(":", 1)[0].strip()
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", lstripped)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            # Handle YAML-style lists when value is empty
            list_items: list[str] | None = None
            if val == "":
                j = i + 1
                items: list[str] = []
                while j < len(block):
                    nxt = block[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    if re.match(r"^\s*[-]\s+", nxt):
                        item = (
                            re.sub(r"^\s*[-]\s+", "", nxt).strip().strip('"').strip("'")
                        )
                        items.append(item)
                        j += 1
                        continue
                    # stop at the next key/section at same or lesser indent
                    if re.match(r"^\s*[A-Za-z0-9_]+:\s*", nxt):
                        break
                    break
                if items:
                    list_items = items
                    i = j - 1  # advance to last consumed
            if current_section and key in {"epics", "stories"}:
                # store as section.key (either list or raw)
                if list_items is not None:
                    result[f"{current_section}.{key}_list"] = list_items
                else:
                    result[f"{current_section}.{key}"] = val
            else:
                result[key] = val if list_items is None else list_items
        i += 1
    return result


def parse_epics_from_value(val: str) -> list[str]:
    # Accept formats: ["EPIC-001", "EPIC-002"], ['EPIC-001'], or simple string EPIC-001
    if not val:
        return []
    # If bracketed list
    if val.startswith("[") and val.endswith("]"):
        return re.findall(r"EPIC-\w+", val)
    # Fallback: try to find single epic id
    return re.findall(r"EPIC-[A-Za-z0-9]+", val)


def collect_requirements() -> list[dict[str, object]]:
    reqs: list[dict[str, object]] = []
    sources = []
    if REQ_DIR_PRIMARY.exists():
        sources.extend(sorted(REQ_DIR_PRIMARY.glob("REQ-*.md")))
    if REQ_DIR_FALLBACK.exists():
        sources.extend(sorted(REQ_DIR_FALLBACK.glob("REQ-*.md")))
    seen = set()
    for path in sources:
        if path in seen:
            continue
        seen.add(path)
        try:
            text = read_file(path)
        except Exception:
            continue
        fm = extract_frontmatter(text)
        rid = (str(fm.get("id") or path.stem)).strip('"')
        title = (str(fm.get("title") or fm.get("titel") or "")).strip('"')
        rtype = (str(fm.get("type") or "")).strip('"')
        priority = (str(fm.get("priority") or fm.get("prioriteit") or "")).strip('"')
        status = (str(fm.get("status") or "")).strip('"')
        # epics can be under links.epics or top-level epics
        epics_list = fm.get("links.epics_list") or fm.get("epics_list")
        if isinstance(epics_list, list):
            epics = [str(x) for x in epics_list]
        else:
            epics_val = str(fm.get("links.epics") or fm.get("epics") or "")
            epics = parse_epics_from_value(epics_val)
        # Skip template placeholder requirement files (e.g., REQ-XXX)
        if rid.upper() == "REQ-XXX" or "<titel>" in title.lower():
            continue
        reqs.append(
            {
                "id": rid,
                "title": title,
                "type": rtype,
                "priority": priority,
                "status": status,
                "epics": epics,
                "path": str(path.relative_to(ROOT)),
            }
        )
    return reqs


def simple_markdown_to_html(md: str) -> str:
    """Very small subset of Markdown → HTML for epic content.
    Supports: #, ##, ### headers; lists; code fences; paragraphs; inline code.
    """
    lines = md.splitlines()
    html_lines: list[str] = []
    in_code = False
    in_ul = False
    for line in lines:
        if line.strip().startswith("```"):
            if not in_code:
                html_lines.append("<pre class=code><code>")
                in_code = True
            else:
                html_lines.append("</code></pre>")
                in_code = False
            continue
        if in_code:
            # escape HTML special chars
            esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(esc)
            continue

        # skip frontmatter blocks
        if line.strip() == "---":
            continue

        # headers
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
            continue
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
            continue
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
            continue

        # lists
        if re.match(r"^\s*[-*]\s+", line):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            item = re.sub(r"^\s*[-*]\s+", "", line).strip()
            html_lines.append(f"<li>{item}</li>")
            continue
        if in_ul:
            html_lines.append("</ul>")
            in_ul = False

        # inline code
        line_proc = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        if line_proc.strip() == "":
            html_lines.append("")
        else:
            html_lines.append(f"<p>{line_proc}</p>")

    if in_ul:
        html_lines.append("</ul>")
    if in_code:
        html_lines.append("</code></pre>")

    return "\n".join(html_lines)


def collect_epics() -> dict[str, dict[str, str]]:
    """Return mapping EPIC-ID → {title, content, path}.
    Accepts epic files even if filename includes a suffix.
    """
    mapping: dict[str, dict[str, str]] = {}
    sources = []
    if EPIC_DIR_PRIMARY.exists():
        sources.extend(sorted(EPIC_DIR_PRIMARY.glob("EPIC-*.md")))
    if EPIC_DIR_FALLBACK.exists():
        sources.extend(sorted(EPIC_DIR_FALLBACK.glob("EPIC-*.md")))
    seen = set()
    for path in sources:
        if path in seen:
            continue
        seen.add(path)
        text = read_file(path)
        fm = extract_frontmatter(text)
        eid = (fm.get("id") or path.stem.split(".")[0]).strip('"')
        title = (fm.get("title") or path.stem).strip('"')
        # strip frontmatter for content rendering
        content = re.sub(r"^---[\s\S]*?---\s*", "", text, count=1)
        mapping[eid] = {
            "title": title,
            "content": content,
            "path": str(path.relative_to(ROOT)),
        }
    return mapping


def write_assets() -> None:
    css = ASSETS_DIR / "style.css"
    css.write_text(
        """
html { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
body { margin: 24px; color: #111; }
h1, h2, h3 { margin: 0.6em 0 0.3em; }
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; }
th { background: #f8fafc; position: sticky; top: 0; }
a { color: #0d6efd; text-decoration: none; }
a:hover { text-decoration: underline; }
.tag { display:inline-block; padding:2px 6px; border-radius: 999px; font-size: 12px; background:#eef2ff; color:#3730a3; }
.muted { color: #6b7280; }
.container { max-width: 1200px; margin: 0 auto; }
.code { background: #0b1022; color: #e2e8f0; padding: 12px; border-radius: 6px; overflow-x: auto; }
.breadcrumbs { font-size: 14px; margin-bottom: 12px; color: #6b7280; }
input[type="search"]{ padding:8px 10px; width: 320px; border:1px solid #e5e7eb; border-radius:6px; }
        """.strip()
    )


def render_index(
    requirements: list[dict[str, object]], epics: dict[str, dict[str, str]]
) -> None:
    # Build rows
    rows = []
    for r in requirements:
        epic_links: list[str] = []
        for eid in r.get("epics", []):
            target = (
                f"epics/{eid}.html"
                if eid in epics
                else (epics.get(eid, {}).get("path") or "#")
            )
            epic_links.append(f'<a href="{target}">{eid}</a>')
        epics_html = (
            ", ".join(epic_links) if epic_links else "<span class=muted>—</span>"
        )
        req_path = str(r["path"])
        if req_path.startswith("docs/"):
            req_path_rel = req_path[len("docs/") :]
        else:
            req_path_rel = req_path
        rows.append(
            f"<tr>"
            f"<td><a href='../../{req_path_rel}'>{r['id']}</a></td>"
            f"<td>{(r.get('title') or '')}</td>"
            f"<td><span class='tag'>{(r.get('type') or '')}</span></td>"
            f"<td>{(r.get('priority') or '')}</td>"
            f"<td>{(r.get('status') or '')}</td>"
            f"<td>{epics_html}</td>"
            f"</tr>"
        )

    html = f"""
<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Requirements Dashboard</title>
  <link rel="stylesheet" href="assets/style.css" />
  <style>
    th.sortable {{ cursor: pointer; user-select: none; }}
    th.sortable::after {{ content: '\\2195'; font-size: 11px; margin-left: 6px; color: #9ca3af; }}
    th.sortable[data-sort=asc]::after {{ content: '\\2191'; color: #111827; }}
    th.sortable[data-sort=desc]::after {{ content: '\\2193'; color: #111827; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Requirements Dashboard</h1>
    <p class="muted">Overzicht van alle requirements en links naar epics en bronbestanden.</p>
    <p><a href="graph.html">↗️ Grafisch overzicht (REQ ↔ EPIC)</a></p>
    <div style="margin: 12px 0 20px">
      <input id="search" type="search" placeholder="Zoek (ID, titel, type, status, epic)" />
    </div>
    <table id="req-table">
      <thead>
        <tr>
          <th class="sortable">ID</th>
          <th class="sortable">Titel</th>
          <th class="sortable">Type</th>
          <th class="sortable">Prioriteit</th>
          <th class="sortable">Status</th>
          <th class="sortable">Epics</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
  <script>
    const input = document.getElementById('search');
    const tbody = document.querySelector('#req-table tbody');
    const thead = document.querySelector('#req-table thead');
    input.addEventListener('input', () => {{
      const q = input.value.toLowerCase();
      for (const tr of tbody.querySelectorAll('tr')) {{
        const text = tr.innerText.toLowerCase();
        tr.style.display = text.includes(q) ? '' : 'none';
      }}
    }});

    // Column sorting (natural compare)
    const natCmp = (a, b) => a.localeCompare(b, undefined, {{numeric: true, sensitivity: 'base'}});
    thead.addEventListener('click', (ev) => {{
      const th = ev.target.closest('th.sortable');
      if (!th) return;
      const ths = Array.from(thead.querySelectorAll('th'));
      const idx = ths.indexOf(th);
      const dir = th.dataset.sort === 'asc' ? 'desc' : 'asc';
      for (const t of thead.querySelectorAll('th.sortable')) t.removeAttribute('data-sort');
      th.setAttribute('data-sort', dir);
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((r1, r2) => {{
        const a = (r1.children[idx]?.innerText || '').trim();
        const b = (r2.children[idx]?.innerText || '').trim();
        const cmp = natCmp(a, b);
        return dir === 'asc' ? cmp : -cmp;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  </script>
</body>
</html>
    """
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")

    # Also write a Markdown fallback (useful on GitHub)
    md_rows = []
    md_rows.append("| ID | Titel | Type | Prioriteit | Status | Epics |")
    md_rows.append("|---|---|---|---|---|---|")
    for r in requirements:
        rid = r["id"]
        title = (r.get("title") or "").replace("|", "\\|")
        rtype = r.get("type") or ""
        prio = r.get("priority") or ""
        status = r.get("status") or ""
        req_link = f"[${rid}](../../{req_path_rel})".replace("$", "")
        epic_links = []
        for eid in r.get("epics", []):
            epic_md = f"[${eid}](../epics/{eid}.md)".replace("$", "")
            epic_links.append(epic_md)
        epics_md = ", ".join(epic_links) if epic_links else "—"
        md_rows.append(
            f"| {req_link} | {title} | {rtype} | {prio} | {status} | {epics_md} |"
        )
    (OUT_DIR / "README.md").write_text("\n".join(md_rows) + "\n", encoding="utf-8")


def render_epic_pages(epics: dict[str, dict[str, str]]) -> None:
    for eid, meta in epics.items():
        title = meta.get("title", eid)
        content_md = meta.get("content", "")
        content_html = simple_markdown_to_html(content_md)
        src_path = meta.get("path", "")
        src_rel = src_path[len("docs/") :] if src_path.startswith("docs/") else src_path
        html = f"""
<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{eid} - {title}</title>
  <link rel="stylesheet" href="../assets/style.css" />
</head>
<body>
  <div class="container">
    <div class="breadcrumbs"><a href="../index.html">Requirements</a> / <span>{eid}</span></div>
    <h1>{eid}: {title}</h1>
    <div>{content_html}</div>
    <p class="muted">Bron: <a href="../../{src_rel}">{src_path}</a></p>
  </div>
</body>
</html>
        """
        (OUT_EPICS_DIR / f"{eid}.html").write_text(html, encoding="utf-8")


def render_collapsible_epic_view(
    requirements: list[dict[str, object]], epics: dict[str, dict[str, str]]
) -> None:
    """Write per-epic collapsible HTML: each epic is a details/summary with its requirements."""
    # Build mapping epic -> list[req]
    by_epic: dict[str, list[dict[str, object]]] = {eid: [] for eid in epics}
    orphans: list[dict[str, object]] = []
    for r in requirements:
        linked = False
        for eid in r.get("epics", []):
            by_epic.setdefault(eid, []).append(r)
            linked = True
        if not linked:
            orphans.append(r)

    # Unique filter values
    statuses = sorted(
        {str(r.get("status") or "").strip() for r in requirements if r.get("status")}
    )
    priorities = sorted(
        {
            str(r.get("priority") or "").strip()
            for r in requirements
            if r.get("priority")
        }
    )

    def render_req_li(r: dict[str, object]) -> str:
        rid = r["id"]
        title = r.get("title") or ""
        rtype = r.get("type") or ""
        prio = r.get("priority") or ""
        status = r.get("status") or ""
        path = r.get("path") or ""
        badges = f"<span class='tag'>{rtype}</span> • <span class='muted'>{prio}</span> • <span class='muted'>{status}</span>"
        # build relative path from docs/backlog/dashboard
        p = str(path)
        p_rel = p[len("docs/") :] if p.startswith("docs/") else p
        return (
            f"<li data-status='{status}' data-priority='{prio}'>"
            f"<a href='../../{p_rel}'>{rid}</a> — {title} <span class='muted'>({badges})</span>"
            f"</li>"
        )

    sections: list[str] = []
    for eid in sorted(by_epic.keys()):
        title = epics.get(eid, {}).get("title", eid)
        reqs = sorted(by_epic.get(eid, []), key=lambda x: str(x.get("id")))
        items = (
            "\n".join(render_req_li(r) for r in reqs)
            or "<li><span class='muted'>Geen gekoppelde requirements</span></li>"
        )
        sections.append(
            f"""
<details open>
  <summary><strong>{eid}</strong> — {title} <span class='muted'>({len(reqs)} REQ)</span></summary>
  <ul>
    {items}
  </ul>
</details>
            """.strip()
        )

    if orphans:
        items = "\n".join(
            render_req_li(r) for r in sorted(orphans, key=lambda x: str(x.get("id")))
        )
        sections.append(
            f"""
<details>
  <summary><strong>UNLINKED</strong> — Requirements zonder epic <span class='muted'>({len(orphans)} REQ)</span></summary>
  <ul>
    {items}
  </ul>
</details>
            """.strip()
        )

    html = f"""
<!doctype html>
<html lang=\"nl\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Per-Epic Overzicht</title>
  <link rel=\"stylesheet\" href=\"assets/style.css\" />
  <style>
    details {{ border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px 12px; margin: 10px 0; background: #fff; }}
    summary {{ cursor: pointer; }}
    .toolbar {{ display:flex; gap:12px; align-items:center; margin: 8px 0 12px; flex-wrap: wrap; }}
    .filters {{ display:flex; gap:16px; align-items:center; flex-wrap: wrap; }}
    .filter-group {{ display:flex; gap:8px; align-items:center; flex-wrap: wrap; }}
    .toolbar button {{ padding: 6px 10px; border:1px solid #e5e7eb; background:#f8fafc; border-radius:6px; cursor:pointer; }}
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"breadcrumbs\"><a href=\"index.html\">Requirements</a> / <span>Per-epic</span></div>
    <h1>Per-Epic Overzicht</h1>
    <p class=\"muted\">Inklapbare blokken per epic met gekoppelde requirements.</p>
    <div class=\"toolbar\">
      <input id=\"filter\" type=\"search\" placeholder=\"Filter op REQ of titel\" />
      <div class=\"filters\">
        <div class=\"filter-group\">
          <span class=\"muted\">Status:</span>
          {''.join(f"<label><input type='checkbox' name='statusFilter' value='{s}' checked> {s}</label>" for s in statuses) or "<span class='muted'>—</span>"}
        </div>
        <div class=\"filter-group\">
          <span class=\"muted\">Prioriteit:</span>
          {''.join(f"<label><input type='checkbox' name='prioFilter' value='{p}' checked> {p}</label>" for p in priorities) or "<span class='muted'>—</span>"}
        </div>
        <label class=\"filter-group\"><input type=\"checkbox\" id=\"expandMatched\" checked> Alleen matches uitklappen</label>
      </div>
      <button id=\"expand\">Alles uitklappen</button>
      <button id=\"collapse\">Alles inklappen</button>
    </div>
    <div id=\"container\">
      {''.join(sections)}
    </div>
  </div>
  <script>
    const filter = document.getElementById('filter');
    const container = document.getElementById('container');
    const expandBtn = document.getElementById('expand');
    const collapseBtn = document.getElementById('collapse');
    const expandMatched = document.getElementById('expandMatched');
    const statusBoxes = Array.from(document.querySelectorAll('input[name=\"statusFilter\"]'));
    const prioBoxes = Array.from(document.querySelectorAll('input[name=\"prioFilter\"]'));
    function applyFilter() {{
      const q = (filter.value || '').toLowerCase();
      const activeStatus = new Set(statusBoxes.filter(b => b.checked).map(b => b.value.toLowerCase()));
      const activePrio = new Set(prioBoxes.filter(b => b.checked).map(b => b.value.toLowerCase()));
      for (const det of container.querySelectorAll('details')) {{
        let visible = false;
        for (const li of det.querySelectorAll('li')) {{
          const txt = li.innerText.toLowerCase();
          const st = (li.getAttribute('data-status') || '').toLowerCase();
          const pr = (li.getAttribute('data-priority') || '').toLowerCase();
          const matchesText = !q || txt.includes(q);
          const matchesStatus = activeStatus.size === 0 || activeStatus.has(st);
          const matchesPrio = activePrio.size === 0 || activePrio.has(pr);
          const show = matchesText && matchesStatus && matchesPrio;
          li.style.display = show ? '' : 'none';
          if (show) visible = true;
        }}
        det.style.display = visible ? '' : 'none';
        if (expandMatched && expandMatched.checked) det.open = visible;
      }}
    }}
    filter.addEventListener('input', applyFilter);
    statusBoxes.forEach(b => b.addEventListener('change', applyFilter));
    prioBoxes.forEach(b => b.addEventListener('change', applyFilter));
    if (expandMatched) expandMatched.addEventListener('change', applyFilter);
    expandBtn.addEventListener('click', () => {{ for (const d of container.querySelectorAll('details')) d.open = true; }});
    collapseBtn.addEventListener('click', () => {{ for (const d of container.querySelectorAll('details')) d.open = false; }});
    applyFilter();
  </script>
</body>
</html>
    """
    (OUT_DIR / "per-epic.html").write_text(html, encoding="utf-8")


def write_graph_artifacts(
    requirements: list[dict[str, object]], epics: dict[str, dict[str, str]]
) -> None:
    """Write data.json and graph.html for a simple bipartite SVG graph (EPICs ⇄ REQs)."""
    # Build data model
    epic_nodes = {
        eid: {"id": eid, "title": meta.get("title", eid)} for eid, meta in epics.items()
    }
    # Also include epics referenced by requirements but missing in files
    for r in requirements:
        for eid in r.get("epics", []):
            if eid not in epic_nodes:
                epic_nodes[eid] = {"id": eid, "title": eid}

    req_nodes = [
        {
            "id": r["id"],
            "title": r.get("title", ""),
            "epics": list(r.get("epics", [])),
            "path": r.get("path", ""),
        }
        for r in requirements
    ]
    data = {
        "epics": list(epic_nodes.values()),
        "requirements": req_nodes,
    }
    # Write data.json and prepare inline JSON
    import json

    data_json = json.dumps(data, ensure_ascii=False)

    (OUT_DIR / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Render graph.html (bipartite layout: epics left, requirements right)
    html = """
<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>REQ ↔ EPIC Graph</title>
  <link rel="stylesheet" href="assets/style.css" />
  <style>
    svg { width: 100%; height: 80vh; border: 1px solid #e5e7eb; background: #fff; }
    .node text { font-size: 12px; }
    .epic circle { fill: #1d4ed8; }
    .req circle { fill: #16a34a; }
    .edge { stroke: #9ca3af; stroke-width: 1; opacity: 0.5; }
    .highlight { stroke: #111827 !important; opacity: 0.9 !important; }
    .hidden { display: none; }
  </style>
  </head>
  <body>
  <div class="container">
    <div class="breadcrumbs"><a href="index.html">Requirements</a> / <span>Graph</span></div>
    <h1>REQ ↔ EPIC Graph</h1>
    <p class="muted">Bipartite weergave: EPICs links, REQs rechts. Zoek en hover om verbindingen te highlighten.</p>
    <div style="margin: 12px 0 16px">
      <input id="search" type="search" placeholder="Zoek op ID of titel (REQ of EPIC)" />
      <label style="margin-left: 12px; font-size: 14px"><input type="checkbox" id="hideOrphans" /> Verberg orphan REQs/EPICs</label>
    </div>
    <svg id="graph"></svg>
  </div>
  <script>
  const DATA = {DATA_JSON};
  const svg = document.getElementById('graph');
  const NS = 'http://www.w3.org/2000/svg';
  const W = svg.clientWidth || svg.parentElement.clientWidth;
  const H = svg.clientHeight || 600;
  const LEFT_X = 180, RIGHT_X = Math.max(W - 220, 700);
  const TOP_PAD = 30, ROW = 28;

  (function(){
    const data = DATA;
    const epics = data.epics.slice().sort((a,b)=> a.id.localeCompare(b.id));
    const reqs = data.requirements.slice().sort((a,b)=> a.id.localeCompare(b.id));

    // Layout
    epics.forEach((e, i) => { e.x = LEFT_X; e.y = TOP_PAD + i*ROW; });
    reqs.forEach((r, i) => { r.x = RIGHT_X; r.y = TOP_PAD + i*ROW; });

    // Index for lookups
    const epicById = Object.fromEntries(epics.map(e => [e.id, e]));

    // Draw helpers
    const make = (name, attrs={}) => { const el = document.createElementNS(NS, name); for (const [k,v] of Object.entries(attrs)) el.setAttribute(k, v); return el; };

    // Draw edges first
    const edges = [];
    reqs.forEach(r => {
      (r.epics || []).forEach(eid => {
        const e = epicById[eid];
        if (!e) return;
        const line = make('line', { x1: e.x, y1: e.y, x2: r.x, y2: r.y, class: 'edge' });
        line.dataset.source = r.id; line.dataset.target = e.id;
        svg.appendChild(line);
        edges.push(line);
      });
    });

    // Draw epic nodes
    epics.forEach(e => {
      const g = make('g', { class: 'node epic' });
      const c = make('circle', { cx: e.x, cy: e.y, r: 6 });
      const t = make('text', { x: e.x + 10, y: e.y + 4 });
      t.textContent = e.id + '  ' + (e.title || '');
      g.appendChild(c); g.appendChild(t); svg.appendChild(g);
      g.addEventListener('mouseenter', () => highlightEpic(e.id, true));
      g.addEventListener('mouseleave', () => highlightEpic(e.id, false));
      g.addEventListener('click', () => { window.location.href = `epics/${e.id}.html`; });
      g.dataset.id = e.id;
    });

    // Draw requirement nodes
    reqs.forEach(r => {
      const g = make('g', { class: 'node req' });
      const c = make('circle', { cx: r.x, cy: r.y, r: 6 });
      const t = make('text', { x: r.x + 10, y: r.y + 4 });
      t.textContent = r.id + '  ' + (r.title || '');
      g.appendChild(c); g.appendChild(t); svg.appendChild(g);
      g.addEventListener('mouseenter', () => highlightReq(r.id, true));
      g.addEventListener('mouseleave', () => highlightReq(r.id, false));
      g.addEventListener('click', () => {
        let p = r.path || '';
        if (p.startsWith('docs/')) p = p.substring(5);
        window.location.href = `../../${p}`;
      });
      g.dataset.id = r.id;
    });

    function highlightEpic(eid, on){
      for (const edge of edges){
        if (edge.dataset.target === eid){ edge.classList.toggle('highlight', on); }
      }
    }
    function highlightReq(rid, on){
      for (const edge of edges){
        if (edge.dataset.source === rid){ edge.classList.toggle('highlight', on); }
      }
    }

    // Search filter
    const search = document.getElementById('search');
    const hideOrphans = document.getElementById('hideOrphans');
    function applyFilter(){
      const q = (search.value || '').toLowerCase();
      const connectedEpic = new Set(edges.map(e => e.dataset.target));
      const connectedReq = new Set(edges.map(e => e.dataset.source));

      // Nodes
      for (const g of svg.querySelectorAll('g.node.epic')){
        const id = g.dataset.id; const label = g.textContent.toLowerCase();
        const matches = label.includes(q);
        const orphan = !connectedEpic.has(id);
        g.classList.toggle('hidden', !(matches || (!q && (!hideOrphans.checked || !orphan))));
      }
      for (const g of svg.querySelectorAll('g.node.req')){
        const id = g.dataset.id; const label = g.textContent.toLowerCase();
        const matches = label.includes(q);
        const orphan = !connectedReq.has(id);
        g.classList.toggle('hidden', !(matches || (!q && (!hideOrphans.checked || !orphan))));
      }
      // Edges obey node visibility
      for (const e of edges){
        const s = e.dataset.source, t = e.dataset.target;
        const sHidden = svg.querySelector(`g.node.req[data-id="${s}"]`).classList.contains('hidden');
        const tHidden = svg.querySelector(`g.node.epic[data-id="${t}"]`).classList.contains('hidden');
        e.classList.toggle('hidden', sHidden || tHidden);
      }
    }
    search.addEventListener('input', applyFilter);
    hideOrphans.addEventListener('change', applyFilter);
    applyFilter();
  })();
  </script>
  </body>
  </html>
    """
    html = html.replace("{DATA_JSON}", data_json)
    (OUT_DIR / "graph.html").write_text(html, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    write_assets()
    requirements = collect_requirements()
    epics = collect_epics()
    render_index(requirements, epics)
    render_epic_pages(epics)
    render_collapsible_epic_view(requirements, epics)
    write_graph_artifacts(requirements, epics)
    print(f"[dashboard] Generated at {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
