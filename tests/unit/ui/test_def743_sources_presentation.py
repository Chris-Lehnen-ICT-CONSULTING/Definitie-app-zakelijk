"""Bronpresentatie zonder gezagsoordeel; links en volledige passage zichtbaar (DEF-743).

Rendert de echte ``SourcesRenderer`` met de échte Streamlit ``AppTest`` op
synthetische bronrecords in het V2-dictformaat dat de renderer ontvangt
(``agent_result["sources"]``). De pytest-conftest vervangt ``streamlit``
procesbreed door een mock, dus dit bestand start zichzelf als subprocess-driver
(``python <dit bestand> --driver <uitvoer.json>``) achter de offline-gate en
leest de waarnemingen terug.

Bewezen presentatie op AANGELEVERDE gegevens:

* provider/route (legacy ``is_authoritative``) levert geen gezagsoordeel op,
  alleen een neutrale herkomstvermelding;
* de score heet zoekinformatie ("Zoekscore"); een echte numerieke nul wordt
  niet door ``confidence`` overschreven; documenten tonen hun selectiewijze
  en citatie, geen score;
* de RAG-route toont haar aanwezige link zoals elke andere bron;
* een passage langer dan 500 tekens blijft verkort in het fragment en is
  volledig raadpleegbaar in een aparte expander.

Grens: dit zegt niets over transport (pakket A), AI-beoordeling of
persistentie. Er wordt geen externe bron geopend; de URL's zijn synthetisch.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]

REPO = Path(__file__).resolve().parents[3]

LANGE_PASSAGE = " ".join(
    f"Zin {n} van de aangeleverde passage beschrijft de archiefkaart nader."
    for n in range(1, 13)
)
assert len(LANGE_PASSAGE) > 500  # De grens van het verkorte fragment.

OVERHEID_URL = "https://wetten.overheid.nl/synthetisch/awb#3:2"
RAG_URL = "https://example.invalid/register/2"
CITATIE_RAG = "Bestuursrecht · Synthetisch testregister · 2"

OVERHEID = {
    "provider": "overheid",
    "source_label": "Overheid.nl",
    "title": "Artikel 3:2 Algemene wet bestuursrecht",
    "url": OVERHEID_URL,
    "snippet": "Bij de voorbereiding van een besluit vergaart het bestuursorgaan kennis.",
    "score": 0.0,  # Echte nul uit de zoekroute.
    "confidence": 0.9,  # Mag de nul niet overschrijven.
    "used_in_prompt": True,
    "retrieved_at": "2026-09-15T10:00:00Z",
    "is_authoritative": True,  # Legacy: uit de provider afgeleid, geen oordeel.
}
RAG = {
    "provider": "rag",
    "title": "Synthetisch testregister",
    "url": RAG_URL,
    "snippet": LANGE_PASSAGE,
    "score": 0.91,
    "used_in_prompt": True,
    "source_label": "RAG: Synthetisch testregister",
    "is_authoritative": False,
    "legal": {"citation_text": CITATIE_RAG},
}
KORT_DOCUMENT = {
    "provider": "documents",
    "title": "awb32.txt",
    "filename": "awb32.txt",
    "doc_id": "awb32",
    "citation_label": "volledig document",
    "selection_basis": "selected_short_document",
    "snippet": "Kort geselecteerd document zonder termtreffer.",
    "score": 0.0,
    "used_in_prompt": True,
    "source_label": "Geüpload document",
}
TERMTREFFER = {
    "provider": "documents",
    "title": "register.txt",
    "filename": "register.txt",
    "doc_id": "upload-01",
    "citation_label": "p. 2",
    "selection_basis": "term_match",
    "snippet": "Een archiefkaart beschrijft één verzameling documenten.",
    "score": 1.0,
    "used_in_prompt": True,
    "source_label": "Geüpload document",
}
LEGACY_UPLOAD = {
    "provider": "documents",
    "title": "los.txt",
    "doc_id": None,
    "snippet": "Alleen.",
    "score": 1.0,
    "used_in_prompt": False,
    "source_label": "Geüpload document",
}
BRONNEN = [OVERHEID, RAG, KORT_DOCUMENT, TERMTREFFER, LEGACY_UPLOAD]


# ------------------------------------------------------------------ driver


def _app(sources: list[dict]) -> None:
    """Testapp voor ``AppTest.from_function``: alleen de echte renderer."""
    import streamlit as st

    from ui.components.sources_renderer import SourcesRenderer

    st.markdown("## Bronnen (DEF-743)")
    SourcesRenderer().render_sources_section({}, {"sources": sources})


def _blok(exp) -> dict:
    return {
        "label": exp.label,
        "markdown": [str(m.value) for m in exp.markdown],
        "caption": [str(c.value) for c in exp.caption],
        "success": [str(s.value) for s in exp.success],
        "info": [str(i.value) for i in exp.info],
        "text": [str(t.value) for t in exp.text],
    }


def _driver(uit_pad: str) -> None:
    for pad in (str(REPO), str(REPO / "src")):
        if pad not in sys.path:
            sys.path.insert(0, pad)
    from tests import offline_bootstrap

    offline_bootstrap.install()
    from streamlit.testing.v1 import AppTest

    invoer = deepcopy(BRONNEN)
    at = AppTest.from_function(_app, kwargs={"sources": invoer}, default_timeout=120)
    at.run()
    waarnemingen = {
        "gate_actief": offline_bootstrap.gate_is_actief(),
        "exceptions": [str(e.value) for e in at.exception],
        "invoer_ongewijzigd": invoer == BRONNEN,
        "expanders": [_blok(e) for e in at.expander],
        "success": [str(s.value) for s in at.success],
        "alle_tekst": "\n".join(
            str(getattr(el, "value", el))
            for verzameling in (
                at.markdown,
                at.caption,
                at.success,
                at.info,
                at.warning,
                at.error,
                at.text,
            )
            for el in verzameling
        ),
    }
    Path(uit_pad).write_text(
        json.dumps(waarnemingen, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------------ pytest


@pytest.fixture(scope="module")
def waarnemingen(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def743-apptest") / "waarnemingen.json"
    proces = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--driver", str(uit)],
        cwd=str(REPO),
        # Bewust de bestaande omgeving (zie DEF-622): de offline-gate en
        # dummykeys komen uit de bootstrap, niet van hier.
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-6000:]
    return json.loads(uit.read_text(encoding="utf-8"))


def _bron(waarnemingen: dict, nummer: int) -> dict:
    """De expander van bron ``nummer`` (1-gebaseerd, zoals in de kop)."""
    kandidaten = [
        e for e in waarnemingen["expanders"] if e["label"].startswith(f"{nummer}. ")
    ]
    assert len(kandidaten) == 1, [e["label"] for e in waarnemingen["expanders"]]
    return kandidaten[0]


def _passages(waarnemingen: dict) -> list[dict]:
    return [e for e in waarnemingen["expanders"] if "Volledige passage" in e["label"]]


def _regels(blok: dict, prefix: str) -> list[str]:
    return [m for m in blok["markdown"] if m.startswith(prefix)]


def test_driver_draait_achter_de_offline_gate_zonder_fouten(waarnemingen):
    assert waarnemingen["gate_actief"] is True
    assert waarnemingen["exceptions"] == []
    assert waarnemingen["invoer_ongewijzigd"] is True
    assert [b["label"][:3] for b in (_bron(waarnemingen, n) for n in range(1, 6))] == [
        "1. ",
        "2. ",
        "3. ",
        "4. ",
        "5. ",
    ]


def test_overheidsbron_krijgt_neutrale_herkomst_en_geen_gezagsoordeel(waarnemingen):
    """provider=overheid + is_authoritative=True: geen 'Autoritatief'-badge."""
    bron = _bron(waarnemingen, 1)
    assert bron["success"] == []
    assert "Herkomst: Overheid.nl" in bron["caption"]
    tekst = waarnemingen["alle_tekst"].lower()
    assert "autoritatief" not in tekst
    assert waarnemingen["success"] == []
    # Bestaand gedrag blijft: prompt-markering en bronlink.
    assert "→ In prompt" in bron["info"]
    assert f"[🔗 Open bron]({OVERHEID_URL})" in bron["markdown"]


def test_webbron_toont_zoekscore_en_respecteert_echte_nul(waarnemingen):
    bron = _bron(waarnemingen, 1)
    assert "**Zoekscore**: 0.00" in bron["markdown"]
    assert _regels(bron, "**Score**") == []
    assert "0.90" not in "\n".join(bron["markdown"])  # confidence overschrijft niet.
    assert any("geen beoordeling van de bron" in c for c in bron["caption"])


def test_rag_bron_toont_zoekscore_met_kleur_link_en_citatie(waarnemingen):
    bron = _bron(waarnemingen, 2)
    assert bron["label"].endswith("🟢")  # Bestaande kleurfunctie blijft.
    assert "Herkomst: RAG: Synthetisch testregister" in bron["caption"]
    assert "**Zoekscore**: 🟢 0.91" in bron["markdown"]
    assert _regels(bron, "**Relevantie**") == []
    assert _regels(bron, "**Score**") == []
    assert any("geen beoordeling van de bron" in c for c in bron["caption"])
    assert f"**Juridische verwijzing**: {CITATIE_RAG}" in bron["markdown"]
    assert f"[🔗 Open bron]({RAG_URL})" in bron["markdown"]
    assert bron["success"] == []


def test_lange_passage_blijft_verkort_en_is_volledig_raadpleegbaar(waarnemingen):
    bron = _bron(waarnemingen, 2)
    assert f"**Fragment**: {LANGE_PASSAGE[:500]}..." in bron["markdown"]
    passages = _passages(waarnemingen)
    assert len(passages) == 1, [e["label"] for e in waarnemingen["expanders"]]
    (passage,) = passages
    assert "bron 2" in passage["label"]
    assert f"{len(LANGE_PASSAGE)} tekens" in passage["label"]
    assert passage["text"] == [LANGE_PASSAGE]  # Exact wat is aangeleverd.
    assert passage["markdown"] == []


def test_upload_toont_selectiewijze_en_citatie_zonder_score(waarnemingen):
    kort = _bron(waarnemingen, 3)
    assert "**Document**: awb32.txt · Locatie: volledig document" in kort["markdown"]
    assert "**Selectie**: Geselecteerd kort document" in kort["markdown"]
    assert "Herkomst: Geüpload document" in kort["caption"]
    assert _regels(kort, "**Score**") == []
    assert _regels(kort, "**Zoekscore**") == []
    assert "0.00" not in "\n".join(kort["markdown"])

    treffer = _bron(waarnemingen, 4)
    assert "**Document**: register.txt · Locatie: p. 2" in treffer["markdown"]
    assert "**Selectie**: Letterlijke termtreffer" in treffer["markdown"]
    assert _regels(treffer, "**Score**") == []
    assert _regels(treffer, "**Zoekscore**") == []
    assert "1.00" not in "\n".join(treffer["markdown"])


def test_legacy_upload_zonder_selectiewijze_krijgt_geen_verzonnen_oordeel(
    waarnemingen,
):
    legacy = _bron(waarnemingen, 5)
    assert "**Document**: los.txt" in legacy["markdown"]
    assert _regels(legacy, "**Selectie**") == []
    assert _regels(legacy, "**Score**") == []
    assert _regels(legacy, "**Zoekscore**") == []
    assert "**Fragment**: Alleen." in legacy["markdown"]
    assert legacy["info"] == []  # used_in_prompt=False: geen prompt-markering.
    assert not any("Open bron" in m for m in legacy["markdown"])  # Geen URL.


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
    else:  # pragma: no cover - alleen als driver bedoeld
        raise SystemExit("gebruik: --driver <uitvoer.json>")
