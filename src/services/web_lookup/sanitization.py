"""
Sanitization utilities for Web Lookup snippets (Epic 3).
"""

from __future__ import annotations

import html
import re

TAG_RE = re.compile(r"<\/?(script|style|iframe|object|embed|form)[^>]*>", re.IGNORECASE)
PROTOCOL_RE = re.compile(r"(?i)\b(?:javascript|vbscript|data):")
WS_RE = re.compile(r"\s+")

# DEF-743: bronnen zijn DATA; de sanitizer mag inhoudelijke vergelijkingen
# (`0 < waarde < 10`, `leeftijd > 18`, `a<b en c>d`, `x<y en z>w`) en
# placeholders (`<waarde>`) niet als markup wegvegen. Het oude `<[^>]+>` deed
# dat wel. Daarom een conservatieve, parserloze herkenning: een `<…>`-token
# wordt alléén gestript als het aantoonbaar markup is —
#   * commentaar/doctype/PI: `<!-- … -->`, `<!…>`, `<?…>`;
#   * sluit-tag `</naam>` (elke naam; `</…>` is nooit een vergelijking);
#   * open-/zelfsluitende tag van een BEKEND HTML-element, kaal (`<b>`, `<br/>`)
#     of met uitsluitend geldige attributen (`naam=waarde` of een bekend
#     booleaans/`data-`/`aria-`-attribuut);
#   * een onbekende naam alléén met echte toegewezen attributen (`<bron nr="9">`).
# Alles wat daar niet aan voldoet (`<b en c>`, `<y en z>`, `<waarde>`) blijft
# letterlijke tekst en wordt aan het eind geëscapet — geen structurele
# injectie mogelijk, geen betekenisverlies. Gevaarlijke elementen (TAG_RE) en
# protocollen (PROTOCOL_RE) blijven onvoorwaardelijk geblokkeerd.
_TAG_CANDIDATE_RE = re.compile(
    r"<!--.*?-->|<[!?][^<>]*>|<(/?)([A-Za-z][\w:.-]*)([^<>]*)>",
    re.DOTALL,
)
_ATTR_RE = re.compile(
    r"""\s*([A-Za-z_:][-\w:.]*)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s"'=<>`]+))?""",
)
KNOWN_HTML_ELEMENTS: frozenset[str] = frozenset(
    [
        "a",
        "abbr",
        "acronym",
        "address",
        "area",
        "article",
        "aside",
        "audio",
        "b",
        "base",
        "bdi",
        "bdo",
        "big",
        "blockquote",
        "body",
        "br",
        "button",
        "canvas",
        "caption",
        "center",
        "cite",
        "code",
        "col",
        "colgroup",
        "data",
        "datalist",
        "dd",
        "del",
        "details",
        "dfn",
        "dialog",
        "dir",
        "div",
        "dl",
        "dt",
        "em",
        "embed",
        "fieldset",
        "figcaption",
        "figure",
        "font",
        "footer",
        "form",
        "frame",
        "frameset",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "head",
        "header",
        "hgroup",
        "hr",
        "html",
        "i",
        "iframe",
        "img",
        "input",
        "ins",
        "kbd",
        "label",
        "legend",
        "li",
        "link",
        "main",
        "map",
        "mark",
        "marquee",
        "menu",
        "meta",
        "meter",
        "nav",
        "nobr",
        "noframes",
        "noscript",
        "object",
        "ol",
        "optgroup",
        "option",
        "output",
        "p",
        "param",
        "picture",
        "pre",
        "progress",
        "q",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "script",
        "section",
        "select",
        "slot",
        "small",
        "source",
        "span",
        "strike",
        "strong",
        "style",
        "sub",
        "summary",
        "sup",
        "svg",
        "table",
        "tbody",
        "td",
        "template",
        "textarea",
        "tfoot",
        "th",
        "thead",
        "time",
        "title",
        "tr",
        "track",
        "tt",
        "u",
        "ul",
        "var",
        "video",
        "wbr",
    ]
)
KNOWN_BOOLEAN_ATTRIBUTES: frozenset[str] = frozenset(
    [
        "allowfullscreen",
        "async",
        "autofocus",
        "autoplay",
        "checked",
        "compact",
        "controls",
        "default",
        "defer",
        "disabled",
        "formnovalidate",
        "hidden",
        "inert",
        "ismap",
        "itemscope",
        "loop",
        "multiple",
        "muted",
        "nomodule",
        "noresize",
        "noshade",
        "novalidate",
        "nowrap",
        "open",
        "playsinline",
        "readonly",
        "required",
        "reversed",
        "scoped",
        "seamless",
        "selected",
        "truespeed",
    ]
)


def _attributes_are_markup(body: str, *, known_element: bool) -> bool:
    """True als `body` uitsluitend uit geldige HTML-attributen bestaat.

    Bij een onbekende elementnaam telt alleen een reeks toegewezen attributen
    (`naam=waarde`); een kaal woord na een onbekende naam is dan geen bewijs
    van markup.
    """
    pos = 0
    assigned_only = True
    while pos < len(body):
        match = _ATTR_RE.match(body, pos)
        if match is None or match.end() == pos:
            return False
        name, value = match.group(1), match.group(2)
        if value is None:
            lname = name.lower()
            if not (
                lname in KNOWN_BOOLEAN_ATTRIBUTES
                or lname.startswith(("data-", "aria-"))
            ):
                return False
            assigned_only = False
        pos = match.end()
    return known_element or assigned_only


def _is_markup(match: re.Match[str]) -> bool:
    """Beslis of een `<…>`-kandidaat aantoonbaar markup is (zie module-comment)."""
    name = match.group(2)
    if name is None:  # commentaar, doctype, processing instruction
        return True
    closing = match.group(1) == "/"
    body = match.group(3).strip()
    if closing:
        return body == ""
    if body.endswith("/"):
        body = body[:-1].strip()
    known = name.lower() in KNOWN_HTML_ELEMENTS
    if not body:
        return known
    return _attributes_are_markup(body, known_element=known)


def _strip_markup(text: str) -> str:
    """Vervang aantoonbare markup door een spatie; laat de rest letterlijk staan."""
    return _TAG_CANDIDATE_RE.sub(lambda m: " " if _is_markup(m) else m.group(0), text)


def sanitize_snippet(text: str, max_length: int = 500) -> str:
    """Sanitize provider snippets according to epic policy.

    - Strip dangerous tags (script, style, iframe, object, embed, form)
    - Remove aantoonbare HTML-markup (zie `_is_markup`); vergelijkingen,
      placeholders en andere twijfelgevallen blijven letterlijke tekst
    - Block dangerous protocols (javascript:, data:, vbscript:)
    - Collapse whitespace and truncate to max_length
    - HTML-escape entities to be safe in text UIs
    """
    if not text:
        return ""

    # Remove dangerous tags completely
    cleaned = TAG_RE.sub("", text)
    # Remove genuine HTML markup but keep inner text (DEF-743)
    cleaned = _strip_markup(cleaned)
    # Block protocols in any residual text
    cleaned = PROTOCOL_RE.sub("", cleaned)
    # Normalize whitespace
    cleaned = WS_RE.sub(" ", cleaned).strip()
    # Truncate
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    # Escape entities for UI safety
    return html.escape(cleaned, quote=False)
