"""
Performance test voor US-202 Rule Cache optimalisatie.

Test dat de RuleCache herhaalde regeltoegang uit geheugen bedient in plaats van
de JSON-bestanden opnieuw van schijf te lezen.

Cachelagen, eerlijk benoemd (geen Streamlit):
1. de proces-lokale memo in ``RuleCache._rules_memo`` (TTL 3600s, DEF-496);
2. de ``@cached``-FileCache rond ``_load_all_rules_cached``.

DEF-519 — contractmapping van de twee rode nodes:

* ``test_cache_is_actually_used`` patchte de loader en asserteerde op een
  verzonnen ``TEST-01``, terwijl de singleton-memo de echte regelset al
  vasthield; er werd geen enkele callcount getoetst. De node telt nu de
  werkelijke bestandslezingen van de échte loader op een eigen kopie van de
  volledige regelset, met exacte aantallen en een cachebypass-proef.
* ``test_memory_efficiency`` eiste een whitelist-projectie die DEF-606
  uitdrukkelijk heeft verwijderd (normatieve velden verdwenen daardoor stil uit
  de runtime), en mockte ``json.load``/``open`` terwijl ``lees_regelbestand``
  ``read_text`` + ``json.loads`` gebruikt — de mock kwam nooit aan bod. Vervangen
  door ``test_full_source_record_preserved``: álle bronvelden blijven behouden.
  Er wordt geen geheugenwinst geclaimd; die is hier niet gemeten.
"""

import json
import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.rule_cache import RuleCache, get_rule_cache
from toetsregels.runtime_contract import (
    RuleContractError,
    lees_regelbestand,
    load_root_contract_policy,
)

pytestmark = [pytest.mark.performance]


def _contract_ids() -> set[str]:
    """De contractuele regel-ID-set uit de root-SSOT."""
    return set(load_root_contract_policy().rule_ids)


@contextmanager
def eigen_cachecontext(cache_map: Path):
    """Bind de échte FileCache/CacheConfig aan een eigen map en herstel exact.

    `utils.cache` houdt module-globale toestand (`_cache`, `_cache_config`,
    `_stats`). De `@cached`-decorator leest die globals bij elke aanroep, dus
    een eigen FileCache hier betekent: echte decorator, echte loader, echte
    validatie — alleen op eigen opslag. Een verse, lege map is koud, zodat
    `clear_cache()` (die de gedeelde cache van de gebruiker zou legen) nergens
    nodig is. In `finally` gaan cacheobject, config én statistiek exact terug,
    ook op het foutpad. Dit is de enige cleanupimplementatie in dit bestand.
    """
    from utils import cache as cache_module

    vorige_cache = cache_module._cache
    vorige_config = cache_module._cache_config
    with cache_module._stats_lock:
        vorige_stats = dict(cache_module._stats)

    config = cache_module.CacheConfig(cache_dir=str(cache_map))
    cache_module._cache_config = config
    cache_module._cache = cache_module.FileCache(config)
    with cache_module._stats_lock:
        cache_module._stats.update({"hits": 0, "misses": 0, "evictions": 0})
    try:
        yield cache_module._cache
    finally:
        cache_module._cache = vorige_cache
        cache_module._cache_config = vorige_config
        with cache_module._stats_lock:
            cache_module._stats.clear()
            cache_module._stats.update(vorige_stats)


class TestRuleCachePerformance:
    """Test performance improvements van RuleCache."""

    # ------------------------------------------------------------------
    # Fixtures: gedeelde state isoleren en exact herstellen
    # ------------------------------------------------------------------

    @pytest.fixture
    def verse_rulecache(self):
        """Verse singleton + module-global; herstelt ook bij een assertionfout.

        Zonder deze isolatie bepaalt de testvolgorde de uitkomst: de memo van
        een eerdere test houdt de regelset binnen de TTL vast.
        """
        from toetsregels import rule_cache as rc

        vorige_klasse_instance = RuleCache._instance
        vorige_module_global = rc._rule_cache
        RuleCache._instance = None
        rc._rule_cache = None
        try:
            yield RuleCache()
        finally:
            RuleCache._instance = vorige_klasse_instance
            rc._rule_cache = vorige_module_global

    @pytest.fixture
    def eigen_filecache(self, tmp_path):
        """Eigen, lege FileCache voor deze test; gedeelde state blijft intact."""
        with eigen_cachecontext(tmp_path / "cache-koud-1") as filecache:
            yield filecache

    @pytest.fixture
    def echte_regelset(self, tmp_path):
        """Kopie van de volledige echte regelset in een eigen tmpdir.

        De contractcontrole toetst tegen het ``rule_ids``-manifest in de
        root-SSOT, dus een deelset zou terecht falen: alleen de volledige echte
        set is geldige bron. Er wordt niets in de repo geschreven of verwijderd.
        """
        from toetsregels import rule_cache as rc

        bron = Path(rc.__file__).parent / "regels"
        doel = tmp_path / "regels"
        doel.mkdir()
        for pad in sorted(bron.glob("*.json")):
            shutil.copy2(pad, doel / pad.name)

        assert list(doel.glob("*.json")), f"geen regelbestanden gekopieerd uit {bron}"
        return doel

    @pytest.fixture
    def leestelling(self, monkeypatch):
        """Tel de werkelijke bestandslezingen van de échte loader."""
        from toetsregels import rule_cache as rc

        tellingen = {"lezingen": 0}

        def tellende_lezer(pad: Path):
            tellingen["lezingen"] += 1
            return lees_regelbestand(pad)

        monkeypatch.setattr(rc, "lees_regelbestand", tellende_lezer)
        return tellingen

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def test_rule_cache_singleton(self, verse_rulecache):
        """Test dat RuleCache een singleton is."""
        cache1 = RuleCache()
        cache2 = RuleCache()
        cache3 = get_rule_cache()

        assert cache1 is cache2
        assert cache2 is cache3
        assert cache1 is verse_rulecache

    def test_cached_manager_uses_cache(self, verse_rulecache, eigen_filecache):
        """Test dat CachedToetsregelManager de RuleCache gebruikt.

        `eigen_filecache` is vereist: deze node doet echte decorator-calls en
        zou anders de vooraf bestaande FileCache en statistieken wijzigen.
        """
        manager = CachedToetsregelManager()
        assert manager.cache is verse_rulecache

        start = time.time()
        rules1 = manager.get_all_regels()
        time.time() - start

        start = time.time()
        rules2 = manager.get_all_regels()
        time.time() - start

        # Zelfde object uit de memo, niet slechts gelijke inhoud.
        assert rules1 == rules2
        assert rules1 is rules2

        stats = manager.get_stats()
        assert stats["cache_hits"] >= 2

    def test_cache_is_actually_used(
        self, tmp_path, verse_rulecache, eigen_filecache, echte_regelset, leestelling
    ):
        """Herhaalde calls lezen niet opnieuw van schijf (memo + FileCache)."""
        cache = verse_rulecache
        cache.regels_dir = echte_regelset
        # Koud door constructie: eigen lege cachemap en eigen regelmap. Geen
        # clear_cache(), want die leegt de gedeelde cache van de gebruiker.
        bestanden = len(list(echte_regelset.glob("*.json")))
        eerste = cache.get_all_rules()
        lezingen_na_eerste = leestelling["lezingen"]

        # Echte gegevens: exact de contractuele regelset, geen verzonnen TEST-01.
        assert set(eerste) == _contract_ids()
        assert lezingen_na_eerste == bestanden

        for _ in range(4):
            volgende = cache.get_all_rules()
            assert volgende is eerste
        assert leestelling["lezingen"] == lezingen_na_eerste, "herladen ondanks cache"

        # Cold-load-tegenproef zonder iets te verwijderen: een verse eigen
        # cachecontext plus een verse RuleCache-instantie (lege memo) leest de
        # bestanden werkelijk opnieuw.
        with eigen_cachecontext(tmp_path / "cache-koud-2"):
            RuleCache._instance = None
            koude_cache = RuleCache()
            koude_cache.regels_dir = echte_regelset
            opnieuw = koude_cache.get_all_rules()

        assert leestelling["lezingen"] == 2 * lezingen_na_eerste
        assert set(opnieuw) == _contract_ids()
        assert opnieuw is not eerste

    def test_weight_calculation(self, verse_rulecache):
        """Test dat regel weights correct worden berekend."""
        cache = verse_rulecache

        with patch.object(cache, "get_all_rules") as mock_get_all:
            mock_get_all.return_value = {
                "HIGH-01": {"id": "HIGH-01", "prioriteit": "hoog"},
                "MID-01": {"id": "MID-01", "prioriteit": "midden"},
                "LOW-01": {"id": "LOW-01", "prioriteit": "laag"},
                "CUSTOM-01": {
                    "id": "CUSTOM-01",
                    "prioriteit": "midden",
                    "weight": 0.85,
                },
            }

            weights = cache.get_rule_weights()

            assert weights["HIGH-01"] == 1.0
            assert weights["MID-01"] == 0.7
            assert weights["LOW-01"] == 0.4
            assert weights["CUSTOM-01"] == 0.85  # Custom weight overrides priority
            assert mock_get_all.call_count == 1

    def test_filter_by_priority(self, verse_rulecache):
        """Test filtering regels op prioriteit."""
        cache = verse_rulecache

        with patch.object(cache, "get_all_rules") as mock_get_all:
            mock_get_all.return_value = {
                "HIGH-01": {"id": "HIGH-01", "prioriteit": "hoog"},
                "HIGH-02": {"id": "HIGH-02", "prioriteit": "hoog"},
                "MID-01": {"id": "MID-01", "prioriteit": "midden"},
                "LOW-01": {"id": "LOW-01", "prioriteit": "laag"},
            }

            high_rules = cache.get_rules_by_priority("hoog")
            assert len(high_rules) == 2
            assert all(r["prioriteit"] == "hoog" for r in high_rules)
            assert mock_get_all.call_count == 1

    def test_manager_compatibility(self, verse_rulecache, eigen_filecache):
        """De manager levert echte resultaten via de RuleCache-interface.

        `eigen_filecache` is vereist: deze node doet echte decorator-calls en
        zou anders de vooraf bestaande FileCache en statistieken wijzigen.
        """
        cached_manager = CachedToetsregelManager()

        alle = cached_manager.get_all_regels()
        assert set(alle) == _contract_ids()

        beschikbaar = cached_manager.get_available_regels()
        assert set(beschikbaar) == set(alle)

        verplicht = cached_manager.get_verplichte_regels()
        assert verplicht, "regelset zonder verplichte regels is onaannemelijk"
        assert all(regel["aanbeveling"] == "verplicht" for regel in verplicht)

        kritiek = cached_manager.get_kritieke_regels()
        assert {regel["id"] for regel in verplicht} <= {
            regel["id"] for regel in kritiek
        }

        een_id = sorted(alle)[0]
        regel = cached_manager.load_regel(een_id)
        assert regel is not None
        assert regel["id"] == alle[een_id]["id"]

        stats = cached_manager.get_stats()
        assert stats["total_rules_cached"] == len(alle)
        assert stats["rules_missing"] == []

    def test_full_source_record_preserved(
        self, verse_rulecache, eigen_filecache, echte_regelset, leestelling
    ):
        """Álle bronvelden overleven het laden (DEF-606), niet alleen een whitelist."""
        cache = verse_rulecache
        cache.regels_dir = echte_regelset

        doelbestand = sorted(echte_regelset.glob("*.json"))[0]
        bron = json.loads(doelbestand.read_text(encoding="utf-8"))
        bron["def519_extra_bronveld"] = {"vrij": ["veld", "met", "inhoud"]}
        doelbestand.write_text(
            json.dumps(bron, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        rules = cache.get_all_rules()
        record = rules[doelbestand.stem]

        # Elk bronveld exact behouden — normatief én extra.
        for veld, waarde in bron.items():
            assert veld in record, f"bronveld '{veld}' verdwenen uit het record"
            assert record[veld] == waarde, f"bronveld '{veld}' gewijzigd"
        assert record["def519_extra_bronveld"] == {"vrij": ["veld", "met", "inhoud"]}

        # Defaults vullen uitsluitend ontbrekende optionele sleutels aan.
        from toetsregels.rule_cache import _RECORD_DEFAULTS

        for veld in _RECORD_DEFAULTS:
            assert veld in record
        assert leestelling["lezingen"] > 0, "er is niets werkelijk gelezen"

    def test_broken_source_fails_visibly_without_cache_pollution(
        self, verse_rulecache, eigen_filecache, echte_regelset
    ):
        """Kapotte of ontbrekende bron faalt zichtbaar en cachet niets.

        Geen clear_cache() nodig: het laden faalt vóórdat er iets gecacht is.
        """
        cache = verse_rulecache
        cache.regels_dir = echte_regelset

        doelbestand = sorted(echte_regelset.glob("*.json"))[0]
        origineel = doelbestand.read_text(encoding="utf-8")

        # 1. Ongeldige JSON.
        doelbestand.write_text("{ dit is geen geldige json", encoding="utf-8")
        with pytest.raises(RuleContractError):
            cache.get_all_rules()

        assert cache._rules_memo is None, "kapotte set mag niet in de memo staan"
        # Nog steeds fout: er is niets blijven hangen in de @cached-laag.
        with pytest.raises(RuleContractError):
            cache.get_all_rules()

        # 2. Ontbrekende verplichte bron.
        doelbestand.write_text(origineel, encoding="utf-8")
        verplaatst = doelbestand.with_suffix(".json.buiten-set")
        doelbestand.rename(verplaatst)

        with pytest.raises(RuleContractError) as exc_info:
            cache.get_all_rules()
        assert doelbestand.stem in str(exc_info.value)
        assert cache._rules_memo is None

        # Herstel de eigen bron en toon dat de cache daarna gewoon laadt.
        verplaatst.rename(doelbestand)
        assert set(cache.get_all_rules()) == _contract_ids()

    def test_bestaande_cachestate_blijft_ongemoeid_ook_op_foutpad(
        self, tmp_path, verse_rulecache, echte_regelset
    ):
        """De eigen cachecontext raakt de voorafgaande cachestate niet aan.

        De 'voorafgaande' toestand is hier zelf synthetisch en tijdelijk — er
        wordt geen gebruikerscache aangeraakt of verwijderd. Getoetst wordt dat
        cacheobject, config, statistiek én een eigen cache-entry ongewijzigd
        terugkomen, óók wanneer het werk binnen de scope faalt.
        """
        from utils import cache as cache_module

        def _werk_dat_faalt():
            with eigen_cachecontext(tmp_path / "werk-cache"):
                RuleCache._instance = None
                werkcache = RuleCache()
                werkcache.regels_dir = echte_regelset
                sorted(echte_regelset.glob("*.json"))[0].write_text(
                    "{ kapot", encoding="utf-8"
                )
                werkcache.get_all_rules()

        with eigen_cachecontext(tmp_path / "bestaande-cache") as bestaande:
            bestaande.set("def519-eigen-entry", {"waarde": "blijft"}, ttl=3600)
            with cache_module._stats_lock:
                cache_module._stats.update({"hits": 7, "misses": 3, "evictions": 1})

            cache_identiteit = cache_module._cache
            config_identiteit = cache_module._cache_config
            statistiek = dict(cache_module._stats)
            entrybestanden = sorted(
                p.name for p in (tmp_path / "bestaande-cache").iterdir()
            )

            # Werk in een eigen scope die met een fout eindigt.
            with pytest.raises(RuleContractError):
                _werk_dat_faalt()

            assert cache_module._cache is cache_identiteit
            assert cache_module._cache_config is config_identiteit
            assert dict(cache_module._stats) == statistiek
            assert bestaande.get("def519-eigen-entry") == {"waarde": "blijft"}
            assert (
                sorted(p.name for p in (tmp_path / "bestaande-cache").iterdir())
                == entrybestanden
            )
