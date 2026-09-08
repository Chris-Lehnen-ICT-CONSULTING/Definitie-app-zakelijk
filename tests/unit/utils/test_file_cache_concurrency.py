"""Concurrency-regressies voor ``FileCache`` (DEF-732, blocker van DEF-665).

``CacheManager`` heeft een lock, ``FileCache`` niet. Daardoor is
``FileCache.get()`` niet atomair:

    if self._is_expired(cache_key):   # A: waar, want de sleutel ontbreekt
        self._delete_entry(cache_key) # B: verwijdert wat er intussen staat
        return None

Publiceert een andere thread tussen A en B een geldige waarde met ``set()``,
dan gooit B dat bestand én de metadata-entry weg. De waarde is dan stil
verdwenen terwijl de schrijver succes meldde (aangetoond in cache147/cache148).

Dit is een **voldoende** mechanisme voor het waargenomen CI-symptoom: de
20-threads-stresstest die intermitterend rood werd (unit146). Er is hier niet
aangetoond dat het de enige oorzaak van die run was; alleen dat dit verlies
werkelijk optreedt en dat het symptoom ermee overeenkomt.

Opzet van de hoofdproef
-----------------------
De volgorde wordt met echte events afgedwongen, niet met slaapjes:

1. de lezer meldt via een sonde op ``_is_expired`` dat hij een echte miss heeft
   waargenomen, en wacht daarna begrensd;
2. de schrijver wacht op die melding, meldt dat hij aan publiceren begint, en
   roept dan werkelijk ``set()`` aan;
3. de lezer wacht eerst op die aankondiging en daarna begrensd op de voltooide
   publicatie, en loopt pas daarna door naar ``_delete_entry``.

In de huidige, ongesynchroniseerde code rondt de schrijver zijn publicatie af
vóórdat de lezer verder gaat: het publicatie-event komt binnen en de lezer wist
de zojuist gepubliceerde entry. In een atomaire implementatie kan de schrijver
niet tussentijds publiceren; de tweede wachtbeurt loopt dan af op haar timeout,
de lezer rondt zijn ``get()`` af en de schrijver publiceert daarna alsnog. De
assertie kijkt naar de enige uitkomst die in beide tijdlijnen gelijk hoort te
zijn: de gepubliceerde waarde bestaat aan het eind nog.

De timeout is geen correctheidsmiddel maar een leefbaarheidsgrens; de foutieve
tijdlijn wordt door het event afgedwongen. Een afgelopen timeout bewijst op
zichzelf niet dát er een lock wordt gehouden — alleen dat de schrijver niet
publiceerde voordat de lezer verderging. De diagnostiek benoemt dat zo.

Reikwijdte
----------
Deze suite dekt één ``FileCache``-instantie binnen één proces. Gedeelde
cachemappen tussen processen of tussen losse instanties vallen hierbuiten en
worden door een instantielock ook niet afgedekt.

Alle opslag is synthetisch (``tmp_path``) met een expliciete dummy-HMAC-sleutel;
de globale cache van de module en de cache van de gebruiker worden nooit
aangeraakt en er wordt niets opgeruimd.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from utils.cache import CacheConfig, FileCache
from utils.safe_serializer import safe_load

pytestmark = [pytest.mark.unit]

#: Duidelijk synthetisch; geen echte sleutel en nergens anders in gebruik.
DUMMY_HMAC_KEY = "def732-dummy-hmac-key-geen-echt-geheim"

#: Eén totale bovengrens voor een hele threadgroep, niet per thread. Ruim boven
#: het werk, zodat alleen een echte blokkade hem haalt.
WACHT = 10.0

#: Grens voor de sonde in de lezer. In de gerepareerde tijdlijn kan de schrijver
#: niet publiceren zolang de lezer het lock vasthoudt; dan loopt deze af.
SONDE_TIMEOUT = 1.0

SLEUTEL = "def732-gedeelde-sleutel"
WAARDE = {"begrip": "verificatie", "definitie": "controleren", "versie": 3}


@pytest.fixture
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Verse, geïsoleerde cachemap met een expliciete dummy-HMAC-sleutel."""
    monkeypatch.setenv("CACHE_HMAC_KEY", DUMMY_HMAC_KEY)
    return tmp_path / "cache"


def _maak_cache(cache_dir: Path, **opties: Any) -> FileCache:
    return FileCache(CacheConfig(cache_dir=str(cache_dir), **opties))


def _draai(doelen: list[Callable[[], Any]], *, deadline: float = WACHT) -> list[Any]:
    """Draai elk doel in een eigen daemon-thread en verzamel de uitkomsten.

    Eén gedeelde deadline voor de hele groep: bij een regressie die vastloopt
    telt de wachttijd niet per thread op. ``time.monotonic`` dient hier
    uitsluitend als leefbaarheidsgrens, niet als synchronisatiemiddel.

    Bewust daemon-threads: een implementatie die zichzelf vastzet — bijvoorbeeld
    een niet-reentrant lock rond geneste opruiming — laat deze proef falen op de
    deadline in plaats van de hele testrun te laten hangen.
    """
    uitkomsten: list[Any] = [None] * len(doelen)
    fouten: list[Exception] = []

    def loop(index: int, doel: Callable[[], Any]) -> None:
        try:
            uitkomsten[index] = doel()
        except Exception as exc:  # wordt hieronder als testfout gemeld
            fouten.append(exc)

    threads = [
        threading.Thread(target=loop, args=(index, doel), daemon=True)
        for index, doel in enumerate(doelen)
    ]
    for thread in threads:
        thread.start()
    einde = time.monotonic() + deadline
    for thread in threads:
        thread.join(timeout=max(0.0, einde - time.monotonic()))

    vastgelopen = [thread.name for thread in threads if thread.is_alive()]
    assert not vastgelopen, f"threads liepen vast: {vastgelopen}"
    assert not fouten, f"threads gaven een fout: {fouten}"
    return uitkomsten


def _bewaarde_metadata(cache_dir: Path) -> dict:
    """De metadata zoals die werkelijk op schijf staat; moet geldige JSON zijn."""
    tekst = (cache_dir / "metadata.json").read_text(encoding="utf-8")
    return json.loads(tekst)


class TestGelijktijdigePublicatie:
    """Een lezer die een miss ziet, mag geen verse publicatie wegwissen."""

    def test_gepubliceerde_waarde_overleeft_gelijktijdige_lezermiss(
        self, cache_dir: Path, monkeypatch: pytest.MonkeyPatch
    ):
        cache = _maak_cache(cache_dir)
        lezer_zag_miss = threading.Event()
        schrijver_begon = threading.Event()
        schrijver_publiceerde = threading.Event()
        sonde_zag_start: list[bool] = []
        sonde_zag_publicatie: list[bool] = []

        origineel_is_expired = cache._is_expired

        def sonde(cache_key: str) -> bool:
            """Naad in de test: laat de schrijver toe ná de waargenomen miss."""
            verlopen = origineel_is_expired(cache_key)
            if cache_key == SLEUTEL and verlopen and not lezer_zag_miss.is_set():
                lezer_zag_miss.set()
                # Eerst bewijzen dat de schrijver werkelijk aan publiceren
                # begint; pas daarna begrensd wachten op de voltooiing.
                sonde_zag_start.append(schrijver_begon.wait(timeout=WACHT))
                sonde_zag_publicatie.append(
                    schrijver_publiceerde.wait(timeout=SONDE_TIMEOUT)
                )
            return verlopen

        monkeypatch.setattr(cache, "_is_expired", sonde)

        def lezer() -> Any:
            return cache.get(SLEUTEL)

        def schrijver() -> bool:
            assert lezer_zag_miss.wait(timeout=WACHT), "lezer meldde geen miss"
            schrijver_begon.set()
            geslaagd = cache.set(SLEUTEL, WAARDE, ttl=600)
            schrijver_publiceerde.set()
            return geslaagd

        gelezen, geschreven = _draai([lezer, schrijver])

        assert sonde_zag_publicatie, "de sonde is nooit aangeroepen"
        assert sonde_zag_start == [
            True
        ], "de schrijver is niet aan publiceren begonnen vóór de lezer verderging"
        assert geschreven is True, "de schrijver meldde geen geslaagde publicatie"
        assert gelezen is None, "de lezer hoorde een echte miss te zien"

        # Een afgelopen timeout bewijst niet dát er een lock wordt gehouden,
        # alleen dat de publicatie niet vóór de lezer afgerond was.
        tijdlijn = (
            "schrijver publiceerde vóórdat de lezer verderging"
            if sonde_zag_publicatie[0]
            else "schrijver publiceerde niet vóórdat de lezer verderging"
        )
        cache_file = cache_dir / f"{SLEUTEL}.json"
        assert cache_file.is_file(), f"de gepubliceerde entry is weggewist ({tijdlijn})"
        assert safe_load(cache_file) == WAARDE, tijdlijn
        assert SLEUTEL in cache.metadata, tijdlijn
        assert SLEUTEL in _bewaarde_metadata(cache_dir), tijdlijn
        assert (
            cache.get(SLEUTEL) == WAARDE
        ), f"de waarde is na afloop niet meer leesbaar ({tijdlijn})"


class TestOverlappendeSchrijvers:
    """Gelijktijdige publicaties mogen elkaars metadata niet overschrijven."""

    def test_alle_sleutels_blijven_in_metadata_en_op_schijf(self, cache_dir: Path):
        cache = _maak_cache(cache_dir)
        sleutels = [f"def732-sleutel-{nummer:02d}" for nummer in range(12)]

        def schrijf(sleutel: str) -> Callable[[], bool]:
            return lambda: cache.set(sleutel, {"waarde": sleutel}, ttl=600)

        resultaten = _draai([schrijf(sleutel) for sleutel in sleutels])
        assert all(resultaten), resultaten

        for sleutel in sleutels:
            assert sleutel in cache.metadata, sleutel
            assert cache.get(sleutel) == {"waarde": sleutel}, sleutel
            assert safe_load(cache_dir / f"{sleutel}.json") == {"waarde": sleutel}

        # De metadata wordt in haar geheel herschreven; gelijktijdige publicaties
        # mogen daarbij geen entry en geen geldige JSON verliezen.
        bewaard = _bewaarde_metadata(cache_dir)
        assert set(bewaard) == set(sleutels), sorted(bewaard)


class TestGenesteOpruimingBlijftLeefbaar:
    """De reparatie moet reentrant zijn: opruimen gebeurt binnen ``set``/``clear``."""

    def test_eviction_tijdens_set_loopt_niet_vast(self, cache_dir: Path):
        # `set()` roept `_cleanup_old_entries()` aan, die op zijn beurt
        # `_delete_entry()` aanroept — genest binnen dezelfde publieke oproep.
        # Een niet-reentrant lock zou hier blokkeren; dat faalt dan op de join.
        cache = _maak_cache(cache_dir, max_cache_size=3)
        sleutels = [f"def732-evict-{nummer:02d}" for nummer in range(10)]

        def schrijf(sleutel: str) -> Callable[[], bool]:
            return lambda: cache.set(sleutel, {"waarde": sleutel}, ttl=600)

        resultaten = _draai([schrijf(sleutel) for sleutel in sleutels])
        assert all(resultaten), resultaten
        assert len(cache.metadata) <= 3, sorted(cache.metadata)

        for sleutel in cache.metadata:
            assert (cache_dir / f"{sleutel}.json").is_file(), sleutel
            assert cache.get(sleutel) == {"waarde": sleutel}, sleutel

    def test_clear_naast_schrijvers_loopt_niet_vast_en_blijft_consistent(
        self, cache_dir: Path
    ):
        cache = _maak_cache(cache_dir)
        sleutels = [f"def732-clear-{nummer:02d}" for nummer in range(8)]
        for sleutel in sleutels[:4]:
            assert cache.set(sleutel, {"waarde": sleutel}, ttl=600) is True

        def schrijf(sleutel: str) -> Callable[[], bool]:
            return lambda: cache.set(sleutel, {"waarde": sleutel}, ttl=600)

        doelen: list[Callable[[], Any]] = [schrijf(s) for s in sleutels[4:]]
        doelen.append(cache.clear)
        doelen.append(lambda: [cache.get(s) for s in sleutels])
        _draai(doelen)

        # Invariant, ongeacht wie won: elke metadata-entry heeft een bestand en
        # elk gepubliceerd bestand hoort bij een entry.
        for sleutel in cache.metadata:
            assert (cache_dir / f"{sleutel}.json").is_file(), sleutel
        bestanden = {
            pad.stem for pad in cache_dir.glob("*.json") if pad.name != "metadata.json"
        }
        assert bestanden == set(cache.metadata), (
            sorted(bestanden),
            sorted(cache.metadata),
        )
        assert cache.get_stats()["entries"] == len(cache.metadata)
