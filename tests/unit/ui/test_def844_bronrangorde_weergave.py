"""DEF-844: de bronweergave toont ook oudere opgeslagen records in rangorde.

Records van vóór DEF-844 staan opgeslagen als web → RAG. Beide secties
("Gebruikte Bronnen" en "Bronbasis") geven de bronnen in brontype-rangorde aan
de lijstweergave door. Streamlit is in de unit-suite procesbreed gemockt; hier
wordt alleen de doorgegeven volgorde waargenomen.
"""

import pytest

from ui.components.sources_renderer import SourcesRenderer

pytestmark = pytest.mark.unit

WIKIPEDIA = {
    "provider": "wikipedia",
    "title": "Wikipedia",
    "url": "https://nl.wikipedia.org/wiki/Verdachte",
    "score": 1.0,
    "used_in_prompt": True,
}
RAG_141 = {
    "provider": "rag",
    "bron_type": "wetgeving",
    "title": "Wetboek van Strafvordering",
    "artikel_lid": "1.4.1",
    "snippet": "Artikel 1.4.1 ...",
    "score": 0.47,
    "used_in_prompt": True,
}
RAG_27 = {**RAG_141, "artikel_lid": "27", "snippet": "Artikel 27 ...", "score": 0.46}
OUDE_VOLGORDE = [WIKIPEDIA, RAG_141, RAG_27]


@pytest.fixture
def waargenomen(monkeypatch):
    gezien: list[list[str]] = []

    def _vang(self, sources, bijlage=None):
        gezien.append([s.get("artikel_lid") or s["title"] for s in sources])

    monkeypatch.setattr(SourcesRenderer, "_render_sources_list", _vang)
    return gezien


def test_gebruikte_bronnen_toont_wetsartikelen_boven_wikipedia(waargenomen):
    SourcesRenderer().render_sources_section(
        generation_result={}, agent_result={"sources": list(OUDE_VOLGORDE)}
    )
    assert waargenomen == [["1.4.1", "27", "Wikipedia"]]


def test_bronbasis_toont_dezelfde_rangorde(waargenomen):
    SourcesRenderer().render_bronbasis_section(
        sources=list(OUDE_VOLGORDE), assessment=None
    )
    assert waargenomen == [["1.4.1", "27", "Wikipedia"]]
