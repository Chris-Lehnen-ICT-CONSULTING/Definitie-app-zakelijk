"""Hermetische fixture voor de functionality-integratietests (DEF-519).

De vier modules in deze map laadden zelf `.env` en sloegen zichzelf over zodra
er geen `OPENAI_API_KEY` stond. Onder de offline-gate van `tests/conftest.py`
faalde die dotenv-aanroep tijdens *collectie*, waardoor geen enkele body meer
draaide. Deze fixture vervangt die constructie door één echte, tijdelijke
omgeving:

* een **echte** `ServiceContainer` met een expliciet `db_path` in `tmp_path`
  (de basetemp van pytest is door de offline-gate als eigen root geadopteerd,
  dus SQLite mag daar openen; de repository-database blijft onaangeroerd);
* **één** bevroren grens: `services.ai.create_ai_client` levert een client die
  het `AsyncAIClient`-contract implementeert en `chat_completion` beantwoordt
  uit een deterministisch antwoordboek. Alles daarbinnen — prompt-opbouw,
  parser, rate limiter, resilience, validatie, opslag — is productiecode.

De bevroren antwoorden bewijzen *gedrag*, geen live prestaties: elke duurmeting
in deze suite meet de lokale code, niet de API-latency.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from services.ai.base_client import ChatMessage, ChatResponse

# --------------------------------------------------------------------------
# Antwoordboek
# --------------------------------------------------------------------------

#: Herkenningspunten uit `UnifiedExamplesGenerator._build_prompt`. Volgorde is
#: significant: "tegenvoorbeelden" bevat "voorbeelden", dus specifiek eerst.
_SOORT_MARKERINGEN: tuple[tuple[str, str], ...] = (
    ("synoniemen", "synoniemen of verwante termen"),
    ("antoniemen", "antoniemen of tegengestelde termen"),
    ("toelichting", "toelichting bij het begrip"),
    ("tegenvoorbeelden", "tegenvoorbeelden die niet onder"),
    ("praktijkvoorbeelden", "praktische voorbeelden waarbij"),
    ("voorbeeldzinnen", "korte voorbeeldzinnen waarin"),
)

#: Het gevraagde aantal staat letterlijk in de prompt; het antwoordboek leest
#: het daar uit in plaats van een eigen aantal te verzinnen. Zo meet de test of
#: de productiecode het juiste aantal *vraagt* én het antwoord juist verwerkt.
_AANTAL_PATRONEN: dict[str, str] = {
    "voorbeeldzinnen": r"Geef (\d+) korte voorbeeldzinnen",
    "praktijkvoorbeelden": r"Geef (\d+) praktische voorbeelden",
    "tegenvoorbeelden": r"Geef (\d+) tegenvoorbeelden",
    "synoniemen": r"Geef EXACT (\d+) synoniemen",
    "antoniemen": r"Geef EXACT (\d+) antoniemen",
}

#: Woordprefix per termsoort. Bewust zonder de substrings "synoniem"/"antoniem":
#: `_parse_response` filtert regels die die woorden bevatten weg.
_TERM_PREFIX: dict[str, str] = {"synoniemen": "syn", "antoniemen": "ant"}

#: Zinprefix per zinsoort; de parser eist regels langer dan tien tekens.
_ZIN_PREFIX: dict[str, str] = {
    "voorbeeldzinnen": "Voorbeeldzin",
    "praktijkvoorbeelden": "Praktijkvoorbeeld",
    "tegenvoorbeelden": "Tegenvoorbeeld",
}

TOELICHTING_TEKST = (
    "Bevroren toelichting: dit begrip beschrijft een bevoegdheid die binnen de "
    "opgegeven context wordt toegepast en daar een vaste betekenis heeft."
)

DEFINITIE_TEKST = (
    "Een bevroren proefdefinitie die het begrip beschrijft als een handeling "
    "van een bevoegde instantie binnen het strafprocesrecht."
)


def verwachte_termen(soort: str, aantal: int) -> list[str]:
    """De exacte lijst die de parser uit een geldig antwoord moet halen."""
    prefix = _TERM_PREFIX[soort]
    return [f"{prefix}term{i:02d}" for i in range(1, aantal + 1)]


def verwachte_zinnen(soort: str, aantal: int) -> list[str]:
    """De exacte lijst die de parser uit een geldig zin-antwoord moet halen."""
    prefix = _ZIN_PREFIX[soort]
    return [
        f"{prefix} nummer {i:02d} uit het bevroren antwoordboek"
        for i in range(1, aantal + 1)
    ]


def verwacht_resultaat(soort: str, aantal: int) -> list[str]:
    """Verwachte parseruitkomst voor elke voorbeeldsoort."""
    if soort in _TERM_PREFIX:
        return verwachte_termen(soort, aantal)
    if soort in _ZIN_PREFIX:
        return verwachte_zinnen(soort, aantal)
    if soort == "toelichting":
        return [TOELICHTING_TEKST]
    msg = f"Onbekende voorbeeldsoort: {soort!r}"
    raise ValueError(msg)


def _ontleed_prompt(prompt: str) -> tuple[str | None, int]:
    """Bepaal soort en gevraagd aantal uit de prompt van de productiecode."""
    laag = prompt.lower()
    for soort, markering in _SOORT_MARKERINGEN:
        if markering in laag:
            patroon = _AANTAL_PATRONEN.get(soort)
            if patroon is None:  # toelichting vraagt om één alinea
                return soort, 1
            treffer = re.search(patroon, prompt)
            if treffer is None:
                msg = f"Aantal niet leesbaar uit prompt voor {soort!r}"
                raise AssertionError(msg)
            return soort, int(treffer.group(1))
    return None, 0


def _antwoordtekst(soort: str | None, aantal: int) -> str:
    """Bouw de bevroren antwoordtekst voor een gevraagde soort."""
    if soort is None:
        return DEFINITIE_TEKST
    if soort == "toelichting":
        return TOELICHTING_TEKST
    return "\n".join(verwacht_resultaat(soort, aantal))


# --------------------------------------------------------------------------
# Bevroren providergrens
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Oproep:
    """Eén waargenomen aanroep van de providergrens."""

    soort: str | None
    gevraagd_aantal: int
    model: str
    temperature: float
    max_tokens: int
    prompt: str


class BevrorenAIClient:
    """Deterministische `AsyncAIClient` — de enige bevroren grens.

    `modus` bepaalt de kwaliteit van het antwoord en maakt zo toetsbaar dat de
    assertions in de tests discrimineren:

    ``geldig``   het gevraagde aantal items;
    ``leeg``     een lege respons (de provider levert niets bruikbaars);
    ``tekort``   één item minder dan gevraagd.
    """

    def __init__(self, modus: str = "geldig") -> None:
        self.modus = modus
        self.oproepen: list[Oproep] = []
        self.gesloten = False

    @property
    def provider_name(self) -> str:
        return "bevroren"

    def oproepen_van(self, soort: str | None) -> list[Oproep]:
        return [oproep for oproep in self.oproepen if oproep.soort == soort]

    def wis(self) -> None:
        self.oproepen.clear()

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: float | None = None,
    ) -> ChatResponse:
        prompt = messages[-1].content if messages else ""
        soort, gevraagd = _ontleed_prompt(prompt)
        self.oproepen.append(
            Oproep(
                soort=soort,
                gevraagd_aantal=gevraagd,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                prompt=prompt,
            )
        )

        if self.modus == "leeg":
            tekst = ""
        elif self.modus == "tekort":
            tekst = _antwoordtekst(soort, max(gevraagd - 1, 0)) if soort else ""
        else:
            tekst = _antwoordtekst(soort, gevraagd)

        return ChatResponse(
            text=tekst,
            tokens_used=len(tekst.split()),
            model=model,
            metadata={"bevroren": True, "soort": soort},
        )

    async def close(self) -> None:
        self.gesloten = True


@dataclass
class BevrorenOmgeving:
    """Alles wat een functionality-test nodig heeft, in één greep."""

    container: Any
    client: BevrorenAIClient
    db_path: Path
    werkmap: Path
    _generator: Any = field(default=None, repr=False)

    @property
    def generator(self) -> Any:
        return self._generator

    def wis_cache(self) -> None:
        """Leeg de tijdelijke AIServiceV2-cache van deze test."""
        from utils.cache import _cache

        _cache.clear()
        _cache.metadata = {}

    def zet_modus(self, modus: str) -> None:
        """Schakel de providergrens om, wis oproephistorie én cache.

        Zonder de cachewissing zou een herhaalde prompt het *vorige* (geldige)
        antwoord teruggeven en zou de discriminatiecontrole niets bewijzen.
        """
        self.client.modus = modus
        self.client.wis()
        self.wis_cache()


#: Configuratiebestanden die de productiecode via een **CWD-relatief** pad
#: opent. `DefinitionOrchestratorV2.validation_service` doet dat met
#: ``ValidationConfig.from_yaml("src/config/validation_rules.yaml")``, dus in een
#: eigen werkmap valt de generatie om met FileNotFoundError. De echte inhoud
#: wordt hierheen gespiegeld: zo blijft de validatie de *productieregels*
#: gebruiken en blijft de werkmap toch onafhankelijk van de repository.
_GESPIEGELDE_CONFIGS: tuple[str, ...] = ("src/config/validation_rules.yaml",)

_PROJECTWORTEL = Path(__file__).resolve().parents[3]


def lees_opgeslagen_definitie(
    db_path: Path, definitie_id: int
) -> dict[str, Any] | None:
    """Lees een opgeslagen rij terug via een **nieuwe** SQLite-verbinding.

    Bewust buiten de repository om: een positief responseobject bewijst nog geen
    duurzame rij. Deze route opent het bestand zelf en sluit de verbinding weer.
    """
    verbinding = sqlite3.connect(str(db_path))
    try:
        verbinding.row_factory = sqlite3.Row
        rij = verbinding.execute(
            "SELECT id, begrip, definitie, categorie, status, version_number "
            "FROM definities WHERE id = ?",
            (definitie_id,),
        ).fetchone()
        return dict(rij) if rij is not None else None
    finally:
        verbinding.close()


def _sluit_sqlite_verbindingen(container: Any) -> None:
    """Sluit de SQLite-verbindingen die deze fixture zelf opende.

    `DatabaseConnection` houdt één verbinding per thread in een
    `_ThreadConnectionState`; die klasse heeft daar `close()` voor, en de
    verbinding wordt bewust met ``check_same_thread=False`` geopend zodat een
    andere thread haar mag opruimen. Zonder deze stap blijft de verbinding open
    tot de garbage collector toeslaat — zichtbaar als ResourceWarning.

    Beperking: verbindingen die de sync→async-bridge in *worker*-threads opende
    zitten in de thread-local van die (inmiddels beëindigde) thread en zijn hier
    niet bereikbaar. Zie het rapport bij deze wijziging.
    """
    from database.db_connection import DatabaseConnection

    gezien: set[int] = set()
    for instantie in list(getattr(container, "_instances", {}).values()):
        for houder in (instantie, getattr(instantie, "legacy_repo", None)):
            db = getattr(houder, "_db", None)
            if not isinstance(db, DatabaseConnection) or id(db) in gezien:
                continue
            gezien.add(id(db))
            toestand = getattr(db._thread_local, "state", None)
            if toestand is not None:
                toestand.close()


def _sluit_provider(client: BevrorenAIClient) -> None:
    """Sluit de providergrens via het `AsyncAIClient`-contract (`close()`)."""
    import asyncio

    asyncio.run(client.close())


def _spiegel_relatieve_configs(werkmap: Path) -> None:
    for relatief in _GESPIEGELDE_CONFIGS:
        bron = _PROJECTWORTEL / relatief
        if not bron.is_file():  # pragma: no cover - defensief
            msg = f"Gespiegelde configuratie ontbreekt in de repository: {relatief}"
            raise AssertionError(msg)
        doel = werkmap / relatief
        doel.parent.mkdir(parents=True, exist_ok=True)
        doel.write_bytes(bron.read_bytes())


@pytest.fixture
def bevroren_omgeving(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Echte container + generator achter één bevroren providergrens."""
    import services.ai as ai_pakket
    from services.container import ServiceContainer
    from utils import (
        cache as cache_module,
        container_manager,
        integrated_resilience,
        smart_rate_limiter,
    )
    from utils.performance_monitor import get_performance_monitor
    from voorbeelden import unified_voorbeelden

    werkmap = tmp_path / "werkmap"
    werkmap.mkdir()
    _spiegel_relatieve_configs(werkmap)
    # Onafhankelijke CWD: relatieve schrijfpaden (cache, exports) landen hier en
    # niet in de repository.
    monkeypatch.chdir(werkmap)

    client = BevrorenAIClient()
    monkeypatch.setattr(
        ai_pakket,
        "create_ai_client",
        lambda provider, api_key, timeout=30.0: client,
    )

    db_path = werkmap / "definities.db"
    container = ServiceContainer(
        {
            "db_path": str(db_path),
            "enable_monitoring": False,
            "enable_ontology": False,
        }
    )
    # Vanaf hier bestaan er resources die deze fixture zelf verkreeg (de
    # SQLite-verbindingen van de container en de providerclient). Alles wat
    # volgt staat daarom in try/finally, zodat ook een fout tijdens de
    # resterende setup nog opruimt — en wel vóór monkeypatch zijn patches
    # terugdraait (die finalizer draait later, want hij is een dependency).
    try:
        # Geen enkel codepad mag alsnog de productiecontainer
        # (data/definities.db) optuigen; de echte container hierboven is het
        # antwoord op elke lookup.
        monkeypatch.setattr(
            container_manager, "get_cached_container", lambda: container
        )

        cache_map = werkmap / "cache"
        cache_map.mkdir()
        monkeypatch.setattr(cache_module._cache, "cache_dir", cache_map)
        monkeypatch.setattr(cache_module._cache.config, "cache_dir", cache_map)
        monkeypatch.setattr(
            cache_module._cache, "metadata_file", cache_map / "meta.json"
        )
        monkeypatch.setattr(cache_module._cache, "metadata", {})

        # Loop-gebonden singletons: elke test krijgt verse limiters en een vers
        # resilience-systeem, zodat de uitkomst niet van de testvolgorde afhangt.
        monkeypatch.setattr(smart_rate_limiter, "_smart_limiters", {})
        monkeypatch.setattr(integrated_resilience, "_integrated_system", None)

        monitor = get_performance_monitor()
        monkeypatch.setattr(monitor, "metrics", {})
        monkeypatch.setattr(monitor, "active_timers", {})

        unified_voorbeelden.reset_examples_generator()
        generator = unified_voorbeelden.get_examples_generator()
        # De echte AIServiceV2 van de echte container — dezelfde instantie die
        # de orchestrator gebruikt (DEF-459), nu met de bevroren client erachter.
        generator.ai_service = container.ai_service()

        yield BevrorenOmgeving(
            container=container,
            client=client,
            db_path=db_path,
            werkmap=werkmap,
            _generator=generator,
        )
    finally:
        # Genest, zodat een fout in een eerdere stap de volgende niet overslaat.
        try:
            unified_voorbeelden.reset_examples_generator()
        finally:
            try:
                _sluit_sqlite_verbindingen(container)
            finally:
                _sluit_provider(client)
