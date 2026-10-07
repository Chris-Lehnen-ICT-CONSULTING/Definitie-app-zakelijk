"""DEF-844: brontype-rangorde — wettelijke bron vóór Wikipedia.

Scenario uit GAT-hertest 3 (DEF-837): bij "verdachte" stond Wikipedia (score
1.00, webschaal) boven de passende Sv-artikelen (cosine 0.40–0.47). De regel
vergelijkt geen scores van verschillende schalen: eerst brontype, dan kanaal,
dan de eigen score.
"""

from copy import deepcopy

import pytest

from domain.sources.rangorde import (
    RANG_EIGEN,
    RANG_OVERIG_WEB,
    RANG_WETTELIJK,
    UPLOAD_COLLECTIE,
    bronrang,
    is_wetgevingsdocumenttype,
    is_wetgevingsdomein,
    rangschik_bronnen,
    sorteersleutel,
)

pytestmark = pytest.mark.unit

WIKIPEDIA = {
    "provider": "wikipedia",
    "title": "Wikipedia",
    "url": "https://nl.wikipedia.org/wiki/Verdachte",
    "score": 1.0,
}
WIKTIONARY = {
    "provider": "wiktionary",
    "title": "verdachte",
    "url": "https://nl.wiktionary.org/wiki/verdachte",
    "score": 0.9,
}
RECHTSPRAAK = {
    "provider": "rechtspraak.nl",
    "title": "ECLI:NL:HR:2026:1",
    "url": "https://uitspraken.rechtspraak.nl/details?id=ECLI:NL:HR:2026:1",
    "score": 0.95,
}
WETTEN_WEB = {
    "provider": "wetgeving.nl",
    "title": "Wetboek van Strafvordering",
    "url": "https://wetten.overheid.nl/BWBR0001903/2026-07-01#Artikel27",
    "score": 0.6,
}


def _rag(
    artikel: str,
    score: float,
    bron_type: str | None = "wetgeving",
    collectie: str | None = "Wetboek van Strafvordering",
) -> dict:
    bron = {
        "provider": "rag",
        "title": "Wetboek van Strafvordering",
        "artikel_lid": artikel,
        "score": score,
    }
    if bron_type is not None:
        bron["bron_type"] = bron_type
    if collectie is not None:
        bron["collection_name"] = collectie
    return bron


def _web(url: str, document_type: str | None = None, score: float = 0.5) -> dict:
    bron = {"provider": "overheid.nl", "title": url, "url": url, "score": score}
    if document_type is not None:
        bron["document_type"] = document_type
    return bron


def _doc(naam: str, score: float) -> dict:
    return {"provider": "documents", "title": naam, "score": score}


def _labels(bronnen: list[dict]) -> list[str]:
    return [b.get("artikel_lid") or b["title"] for b in bronnen]


def test_gat_scenario_wetsartikel_boven_wikipedia():
    # Volgorde zoals de orchestrator haar vóór DEF-844 leverde: web, dan RAG.
    invoer = [
        WIKIPEDIA,
        _rag("1.4.1", 0.47),
        _rag("27", 0.46),
        _rag("1.4.2", 0.41),
        _rag("27d", 0.41),
        _rag("2.5.4", 0.40),
    ]
    assert _labels(rangschik_bronnen(invoer)) == [
        "1.4.1",
        "27",
        "1.4.2",
        "27d",
        "2.5.4",
        "Wikipedia",
    ]


def test_binnen_type_op_eigen_score_aflopend():
    invoer = [_rag("a", 0.40), _rag("b", 0.47), _rag("c", 0.41)]
    assert _labels(rangschik_bronnen(invoer)) == ["b", "c", "a"]


def test_gelijke_score_behoudt_aangeleverde_volgorde():
    invoer = [_rag("1.4.2", 0.41), _rag("27d", 0.41)]
    assert _labels(rangschik_bronnen(invoer)) == ["1.4.2", "27d"]


def test_webbron_van_wetgevingsdomein_boven_wikipedia():
    invoer = [WIKIPEDIA, WIKTIONARY, WETTEN_WEB]
    assert rangschik_bronnen(invoer)[0] is WETTEN_WEB


def test_rag_wetgeving_voor_web_wetgeving_scores_niet_vergeleken():
    # Web-wetgeving 0.6 > RAG 0.45, maar binnen de groep gaat het kanaal voor.
    invoer = [WETTEN_WEB, _rag("27", 0.45)]
    assert _labels(rangschik_bronnen(invoer)) == ["27", "Wetboek van Strafvordering"]


def test_volledige_groepsvolgorde():
    invoer = [
        WIKIPEDIA,
        _doc("register.txt", 1.0),
        _rag("beleid", 0.9, bron_type="pdf"),
        RECHTSPRAAK,
        WETTEN_WEB,
        _rag("27", 0.45),
    ]
    assert _labels(rangschik_bronnen(invoer)) == [
        "27",  # RAG-wetgeving
        "Wetboek van Strafvordering",  # web-wetgeving
        "register.txt",  # geüpload document (volgorde van vóór DEF-844)
        "beleid",  # overige RAG
        "Wikipedia",  # overige web, op eigen score
        "ECLI:NL:HR:2026:1",
    ]


def test_wettelijke_bron_voor_document_en_document_voor_overige_rag():
    invoer = [
        _doc("register.txt", 1.0),
        _rag("x", 0.9, bron_type="pdf"),
        _rag("27", 0.4),
    ]
    assert _labels(rangschik_bronnen(invoer)) == ["27", "register.txt", "x"]


def test_documenten_behouden_aangeleverde_volgorde():
    invoer = [_doc("a.txt", 0.2), _doc("b.txt", 1.0), _doc("c.txt", 0.5)]
    assert _labels(rangschik_bronnen(invoer)) == ["a.txt", "b.txt", "c.txt"]


def test_zonder_rag_en_wetgeving_blijft_webvolgorde_ongewijzigd():
    # build_provenance levert web al op score aflopend; daar verandert niets.
    invoer = [WIKIPEDIA, RECHTSPRAAK, WIKTIONARY]
    assert rangschik_bronnen(invoer) == [WIKIPEDIA, RECHTSPRAAK, WIKTIONARY]


@pytest.mark.parametrize(
    ("bron", "rang"),
    [
        (_rag("27", 0.4), RANG_WETTELIJK),
        (_rag("27", 0.4, bron_type="WETGEVING"), RANG_WETTELIJK),
        (_rag("x", 0.4, bron_type="pdf"), RANG_EIGEN),
        (_rag("x", 0.4, bron_type=None), RANG_EIGEN),
        (_rag("27", 0.4, collectie=UPLOAD_COLLECTIE), RANG_EIGEN),
        (_doc("a.txt", 1.0), RANG_EIGEN),
        (WETTEN_WEB, RANG_WETTELIJK),
        (WIKIPEDIA, RANG_OVERIG_WEB),
        (RECHTSPRAAK, RANG_OVERIG_WEB),
        ({"provider": "overheid.nl", "url": None, "score": 1.0}, RANG_OVERIG_WEB),
        # BWB-kanaal (sru_service "Wetgeving.nl"): ook zonder http-identifier.
        ({"provider": "wetgeving.nl", "url": "", "score": 0.5}, RANG_WETTELIJK),
        ({"provider": "Wetgeving.nl", "url": None, "score": 0.5}, RANG_WETTELIJK),
    ],
)
def test_bronrang(bron, rang):
    assert bronrang(bron) == rang


@pytest.mark.parametrize(
    ("url", "verwacht"),
    [
        ("https://wetten.overheid.nl/BWBR0001903", True),
        ("https://WETTEN.overheid.nl/x", True),
        ("https://lokaleregelgeving.overheid.nl/CVDR1", True),
        # Gemengde domeinen: host alleen is geen bewijs (zie documenttype).
        ("https://zoek.officielebekendmakingen.nl/stb-2026-1.html", False),
        ("https://www.officielebekendmakingen.nl/x", False),
        ("https://eur-lex.europa.eu/eli/reg/2016/679/oj", False),
        ("https://nl.wikipedia.org/wiki/Verdachte", False),
        ("https://repository.overheid.nl/frbr/x", False),
        ("https://wetten.overheid.nl.example.com/x", False),
        ("https://example.com/?u=https://wetten.overheid.nl", False),
        ("", False),
        (None, False),
        ("http://[::1", False),
    ],
)
def test_is_wetgevingsdomein(url, verwacht):
    assert is_wetgevingsdomein(url) is verwacht


# --- Punt 1 (Codex): uploads tellen nooit als wettelijk ----------------------


@pytest.mark.parametrize(
    "bron",
    [
        # Uploadroute zet "wetgeving" zodra een rechtsgebied is gekozen.
        _rag("27", 0.9, collectie=UPLOAD_COLLECTIE),
        _rag("27", 0.9, bron_type="WETGEVING", collectie=UPLOAD_COLLECTIE),
        # Herkomst onbekend (ouder record): geen bewijs, dus geen voorrang.
        _rag("27", 0.9, collectie=None),
        _rag("27", 0.9, collectie="  "),
    ],
)
def test_wetgevingslabel_zonder_bibliotheekherkomst_is_eigen_bron(bron):
    assert bronrang(bron) == RANG_EIGEN


def test_upload_met_wetgevingslabel_onder_echte_wetgeving():
    upload = _rag("upload", 0.9, collectie=UPLOAD_COLLECTIE)
    bibliotheek = _rag("27", 0.4)
    invoer = [WIKIPEDIA, upload, WETTEN_WEB, bibliotheek]
    assert _labels(rangschik_bronnen(invoer)) == [
        "27",  # bronbibliotheek-wetgeving (RAG)
        "Wetboek van Strafvordering",  # BWB-webbron
        "upload",  # upload: eigen bron, ondanks hogere score en label
        "Wikipedia",
    ]


# --- Punt 2 (Codex): gemengde domeinen alleen met documenttype -----------------


@pytest.mark.parametrize(
    ("bron", "rang"),
    [
        # Officiële bekendmakingen: alleen regelgeving telt.
        (
            _web(
                "https://zoek.officielebekendmakingen.nl/stb-2026-1.html", "Staatsblad"
            ),
            RANG_WETTELIJK,
        ),
        (
            _web("https://zoek.officielebekendmakingen.nl/stb-2026-2.html", "Wet"),
            RANG_WETTELIJK,
        ),
        (
            _web(
                "https://zoek.officielebekendmakingen.nl/kst-36000-1.html", "Kamerstuk"
            ),
            RANG_OVERIG_WEB,
        ),
        (
            _web(
                "https://zoek.officielebekendmakingen.nl/ah-tk-2026-1.html",
                "Kamervragen (Aanhangsel)",
            ),
            RANG_OVERIG_WEB,
        ),
        (
            _web(
                "https://zoek.officielebekendmakingen.nl/kv-tk-2026-1.html",
                "Kamervragen zonder antwoord",
            ),
            RANG_OVERIG_WEB,
        ),
        (
            _web(
                "https://zoek.officielebekendmakingen.nl/h-tk-2026-1.html",
                "Handelingen",
            ),
            RANG_OVERIG_WEB,
        ),
        (
            _web("https://zoek.officielebekendmakingen.nl/stb-2026-3.html"),
            RANG_OVERIG_WEB,
        ),
        (
            _web("https://zoek.officielebekendmakingen.nl/stb-2026-4.html", ""),
            RANG_OVERIG_WEB,
        ),
        # EUR-Lex: verordening/richtlijn wel, arrest niet.
        (
            _web("https://eur-lex.europa.eu/eli/reg/2016/679/oj", "Verordening"),
            RANG_WETTELIJK,
        ),
        (
            _web("https://eur-lex.europa.eu/eli/dir/2016/680/oj", "Directive"),
            RANG_WETTELIJK,
        ),
        (
            _web(
                "https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:62018CJ0311",
                "Arrest",
            ),
            RANG_OVERIG_WEB,
        ),
        (
            _web(
                "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62018CJ0311",
                "Judgment",
            ),
            RANG_OVERIG_WEB,
        ),
        (_web("https://eur-lex.europa.eu/eli/reg/2016/679/oj"), RANG_OVERIG_WEB),
        # Documenttype zonder gemengd domein maakt niets wettelijk.
        (_web("https://nl.wikipedia.org/wiki/Wet", "Wet"), RANG_OVERIG_WEB),
        # Host met uitsluitend regelgeving: wettelijk, ook zonder type.
        (_web("https://wetten.overheid.nl/BWBR0001903"), RANG_WETTELIJK),
        (
            _web("https://lokaleregelgeving.overheid.nl/CVDR1", "Kamerstuk"),
            RANG_WETTELIJK,
        ),
    ],
)
def test_gemengde_domeinen_alleen_wettelijk_met_documenttype(bron, rang):
    assert bronrang(bron) == rang


@pytest.mark.parametrize(
    ("documenttype", "verwacht"),
    [
        ("Wet", True),
        (" wet ", True),
        ("Staatsblad", True),
        ("Kamerstuk", False),
        ("Arrest", False),
        ("", False),
        (None, False),
        (12, False),
    ],
)
def test_is_wetgevingsdocumenttype(documenttype, verwacht):
    assert is_wetgevingsdocumenttype(documenttype) is verwacht


def test_rangschik_bronnen_gebruikt_de_gedeelde_sorteersleutel():
    invoer = [WIKIPEDIA, _doc("a.txt", 0.1), _rag("27", 0.4), WETTEN_WEB]
    assert rangschik_bronnen(invoer) == sorted(invoer, key=sorteersleutel)


def test_muteert_niets_en_levert_dezelfde_objecten():
    invoer = [WIKIPEDIA, _rag("27", 0.46)]
    kopie = deepcopy(invoer)
    uit = rangschik_bronnen(invoer)
    assert invoer == kopie
    assert {id(b) for b in uit} == {id(b) for b in invoer}
    assert uit is not invoer


def test_onleesbare_elementen_achteraan_zonder_crash():
    invoer = ["kapot", WIKIPEDIA, None, _rag("27", 0.46)]
    uit = rangschik_bronnen(invoer)
    assert uit[:2] == [invoer[3], WIKIPEDIA]
    assert uit[2:] == ["kapot", None]


def test_onleesbare_score_telt_als_nul():
    invoer = [_rag("a", "x"), _rag("b", 0.3)]  # type: ignore[arg-type]
    assert _labels(rangschik_bronnen(invoer)) == ["b", "a"]


def test_nan_score_telt_als_nul_en_houdt_de_volgorde_voorspelbaar():
    invoer = [_rag("a", 0.2), _rag("nan", "nan"), _rag("b", 0.4)]  # type: ignore
    assert _labels(rangschik_bronnen(invoer)) == ["b", "a", "nan"]
