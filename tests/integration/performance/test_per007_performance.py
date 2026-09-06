"""
PER-007 Performance Benchmark Tests
These tests run after GREEN phase to ensure performance requirements are met.

DEF-519 — alle acht node-intenties en álle oorspronkelijke grenzen zijn
behouden; alleen de fixtures en het gemeten contract zijn actueel gemaakt:

* `GenerationRequest` vereist `id`, `HybridContextManager` vereist een
  `ContextConfig` (zeven nodes faalden hierop met `TypeError`);
* `PromptServiceV2._convert_request_to_context` bestaat niet meer; de actuele
  equivalent van de promptfase is `build_generation_prompt` — die wordt echt
  gemeten, zonder mockprompt;
* elke gemeten contextcall wordt op zijn werkelijke resultaat gecontroleerd
  (drie exacte lijsten, deduplicatie én volgorde), buiten het meetinterval, zodat
  een lege of noop-implementatie niet "snel dus groen" wordt;
* de stille `except ImportError: pass` / `pytest.skip` rond de nooit gebouwde
  ContextFormatter is vervangen door een positieve prerequisite met exact pad.

Advisory voor de niet-geleverde architectuur (ContextFormatter, ASTRA-validatie,
Anders-filtering): owner testdispositie DEF-519; inhoudelijk eigenaar nog niet
bepaald; trigger = vrijgegeven expliciet herstelbesluit; herbeoordeling
2026-10-06. Er wordt niets van die architectuur gebouwd en geen enkele grens
versoepeld; de metingen claimen geen werking die niet plaatsvindt.
"""

import concurrent.futures
import logging
import time
import tracemalloc
from pathlib import Path

import pytest

from services.definition_generator_config import ContextConfig
from services.definition_generator_context import EnrichedContext, HybridContextManager
from services.interfaces import GenerationRequest
from services.prompts.prompt_service_v2 import PromptServiceV2

pytestmark = [pytest.mark.performance]

# `advisory`-dispositie (DEF-519) op vijf van de tien nodes, per node en niet op
# bestandsniveau. `performance` als zodanig is géén grond voor uitsluiting: de
# vijf nodes zonder marker — waaronder `test_context_processing_under_100ms` en
# `test_deduplication_performance` met hun echte timinggrenzen — blijven
# onverkort in de verplichte gate.
# Reden: PER007-performance-intenties waarvan het herstel niet is vrijgegeven.
# Alle oorspronkelijke workloads en grenzen blijven ongewijzigd staan; er wordt
# geen versnelling, geen budget en geen concurrencywinst geclaimd.
# Owner: testdispositie-519, inhoudelijke owner niet vastgesteld.
# Trigger: vrijgegeven herstel van de PER007-budgetten.
# Herbeoordeling: 2026-10-06.
# Uitzondering: `test_astra_validation_performance` is een ASTRA-intentie met
# eigen owner DEF-468 en eigen trigger.

PROJECTWORTEL = Path(__file__).resolve().parents[3]
FORMATTER_PAD = PROJECTWORTEL / "src" / "services" / "ui" / "formatters.py"
FORMATTER_ONTBREEKT = (
    f"ContextFormatter ontbreekt: {FORMATTER_PAD} — nooit gebouwd; "
    "advisory DEF-519 (testdispositie), herbeoordeling 2026-10-06"
)


def _maak_manager() -> HybridContextManager:
    """Echte contextmanager met de actuele, verplichte configuratie."""

    return HybridContextManager(ContextConfig())


def meet_geheugen(
    manager: HybridContextManager,
    request: GenerationRequest,
    iteraties: int,
    verwacht: dict[str, list[str]],
) -> tuple[float, int]:
    """Meet het geheugenverschil over `iteraties` contextcalls.

    Respecteert een reeds lopende tracemalloc-sessie: er wordt alleen zelf
    gestart en gestopt wanneer wij hem hebben aangezet — ook wanneer de
    contextcall een fout gooit. Per iteratie wordt het resultaat gecontroleerd
    zonder het te bewaren; accumulatie zou de meting zelf veranderen.
    """
    zelf_gestart = not tracemalloc.is_tracing()
    if zelf_gestart:
        tracemalloc.start()
    try:
        snapshot1 = tracemalloc.take_snapshot()

        correct = 0
        for _ in range(iteraties):
            result = manager._build_base_context(request)
            if all(result[sleutel] == waarde for sleutel, waarde in verwacht.items()):
                correct += 1
            # Result should be garbage collected
            del result

        snapshot2 = tracemalloc.take_snapshot()
    finally:
        if zelf_gestart:
            tracemalloc.stop()

    stats = snapshot2.compare_to(snapshot1, "lineno")
    total_memory = sum(stat.size_diff for stat in stats)
    return total_memory / 1024 / 1024, correct


class TestPerformance:
    """Performance benchmarks - run after GREEN phase implementation"""

    @pytest.mark.benchmark
    @pytest.mark.performance
    def test_context_processing_under_100ms(self):
        """Context processing must complete in < 100ms"""
        request = GenerationRequest(
            id="perf-context",
            begrip="test",
            organisatorische_context=["OM", "DJI", "Rechtspraak", "CJIB", "KMAR"],
            juridische_context=["Strafrecht", "Bestuursrecht", "Burgerlijk recht"],
            wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv", "AWB", "BW", "WvSr"],
        )

        manager = _maak_manager()

        times = []
        resultaten = []
        iterations = 100

        for _ in range(iterations):
            start = time.perf_counter()
            result = manager._build_base_context(request)
            end = time.perf_counter()
            # Correctheid wordt ná de meting getoetst; alleen verzamelen hier.
            times.append(end - start)
            resultaten.append(result)

        avg_time = sum(times) / len(times) * 1000  # Convert to ms
        max_time = max(times) * 1000

        assert avg_time < 100, f"Average time {avg_time:.2f}ms exceeds 100ms limit"
        assert max_time < 200, f"Max time {max_time:.2f}ms exceeds 200ms limit"

        # Elke gemeten call moet het volledige, geordende resultaat hebben
        # opgeleverd — een lege of noop-implementatie is niet "snel dus goed".
        assert len(resultaten) == iterations
        for result in resultaten:
            assert result["organisatorisch"] == [
                "OM",
                "DJI",
                "Rechtspraak",
                "CJIB",
                "KMAR",
            ]
            assert result["juridisch"] == [
                "Strafrecht",
                "Bestuursrecht",
                "Burgerlijk recht",
            ]
            assert result["wettelijk"] == [
                "Art. 27 Sv",
                "Art. 67 Sv",
                "AWB",
                "BW",
                "WvSr",
            ]

    @pytest.mark.benchmark
    @pytest.mark.performance
    def test_deduplication_performance(self):
        """Deduplication must be efficient even with large lists"""
        base_orgs = ["OM", "DJI", "Rechtspraak", "CJIB"]
        large_list = base_orgs * 50  # 200 items with lots of duplicates

        request = GenerationRequest(
            id="perf-dedup", begrip="test", organisatorische_context=large_list
        )

        manager = _maak_manager()

        times = []
        resultaten = []
        for _ in range(50):
            start = time.perf_counter()
            result = manager._build_base_context(request)
            end = time.perf_counter()
            times.append(end - start)
            resultaten.append(result)

        avg_time = sum(times) / len(times) * 1000  # ms
        assert avg_time < 50, f"Deduplication took {avg_time:.2f}ms, exceeds 50ms limit"

        # Deduplicatie én volgorde bij élke gemeten call.
        assert len(resultaten) == 50
        for result in resultaten:
            assert (
                result["organisatorisch"] == base_orgs
            ), f"Deduplication failed. Got {result['organisatorisch']}"

    @pytest.mark.benchmark
    @pytest.mark.performance
    @pytest.mark.advisory
    def test_ui_formatting_performance(self):
        """UI preview generation must be fast"""
        context = EnrichedContext(
            base_context={
                "organisatorisch": ["OM", "DJI", "Rechtspraak", "CJIB", "KMAR"],
                "juridisch": ["Strafrecht", "Bestuursrecht", "Burgerlijk recht"],
                "wettelijk": ["Art. 27 Sv", "Art. 67 Sv", "AWB", "BW", "WvSr"],
                "domein": ["Justice", "Security"],
                "technisch": [],
                "historisch": [],
            },
            sources=[],
            expanded_terms={
                "OM": "Openbaar Ministerie",
                "DJI": "Dienst Justitiële Inrichtingen",
            },
            confidence_scores={"organisatorisch": 1.0, "juridisch": 0.95},
            metadata={"timestamp": "2025-09-04"},
        )

        # Positieve prerequisite in plaats van een skip: een ontbrekende
        # formatter is zichtbaar, een kapotte dependency wordt niet verborgen.
        assert FORMATTER_PAD.is_file(), FORMATTER_ONTBREEKT

        from services.ui.formatters import ContextFormatter

        formatter = ContextFormatter()

        times = []
        for _ in range(1000):
            start = time.perf_counter()
            result = formatter.format_ui_preview(context)
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times) * 1000  # ms
        assert avg_time < 1, f"UI formatting took {avg_time:.2f}ms, exceeds 1ms limit"

        assert "📋 Org:" in result or "Org:" in result
        assert "⚖️ Juridisch:" in result or "Juridisch:" in result

    @pytest.mark.benchmark
    @pytest.mark.performance
    @pytest.mark.advisory  # eigen owner DEF-468: ASTRA-intentie niet geleverd
    def test_astra_validation_performance(self):
        """ASTRA validation must be fast"""
        verwachte_organisaties = [
            "OM",
            "DJI",
            "InvalidOrg",
            "CustomOrg",
            "Rechtspraak",
            "FakeOrg",
            "CJIB",
            "KMAR",
            "AnotherCustom",
            "NP",
        ]
        request = GenerationRequest(
            id="perf-astra",
            begrip="test",
            organisatorische_context=list(verwachte_organisaties),
        )

        manager = _maak_manager()

        log_records: list[logging.LogRecord] = []
        handler = logging.Handler()
        handler.emit = lambda record: log_records.append(record)
        logger = logging.getLogger("services.definition_generator_context")
        vorig_niveau = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        try:
            times = []
            resultaten = []
            for _ in range(100):
                start = time.perf_counter()
                # Validation happens during processing
                result = manager._build_base_context(request)
                end = time.perf_counter()
                times.append(end - start)
                resultaten.append(result)

            # Gedrag vóór budget. Exacte lijst, niet alleen een lengte:
            # niets geblokkeerd, niets herordend, niets stil toegevoegd.
            assert len(resultaten) == 100
            for result in resultaten:
                gevonden = result["organisatorisch"]
                assert gevonden == verwachte_organisaties, gevonden

            # De meting mag geen ASTRA-werking claimen die niet plaatsvindt:
            # zonder waarschuwing over de onbekende organisaties is er geen
            # validatie gemeten (advisory DEF-519).
            waarschuwingen = [
                r.getMessage() for r in log_records if r.levelname == "WARNING"
            ]
            assert waarschuwingen, (
                "geen ASTRA-validatie waarneembaar tijdens de gemeten call "
                "(geen waarschuwing over InvalidOrg/FakeOrg)"
            )

            avg_time = sum(times) / len(times) * 1000  # ms
            assert (
                avg_time < 10
            ), f"ASTRA validation took {avg_time:.2f}ms, exceeds 10ms limit"
        finally:
            logger.removeHandler(handler)
            logger.setLevel(vorig_niveau)

    @pytest.mark.benchmark
    @pytest.mark.performance
    @pytest.mark.advisory
    @pytest.mark.asyncio
    async def test_end_to_end_flow_performance(self):
        """Complete context flow must be under 200ms"""
        request = GenerationRequest(
            id="perf-e2e",
            begrip="verdachte",
            organisatorische_context=["OM", "DJI", "Anders...", "CustomOrg"],
            juridische_context=["Strafrecht", "Anders...", "CustomJur"],
            wettelijke_basis=["Art. 27 Sv", "Art. 67 Sv", "Anders...", "CustomWet"],
        )

        # De UI-formatfase hoort binnen élke gemeten flow te draaien. Zolang de
        # formatter er niet is, is de complete-flowgrens niet bewezen: daarom
        # staat deze prerequisite VÓÓR de meting en niet erachter. Een leeg
        # formatterbestand helpt niet — de import en de resultaatcontrole
        # hieronder moeten ook slagen.
        assert FORMATTER_PAD.is_file(), FORMATTER_ONTBREEKT

        from services.ui.formatters import ContextFormatter

        times = []
        promptresultaten = []
        ui_previews = []
        for _ in range(50):
            start = time.perf_counter()

            # Step 1: Process context
            manager = _maak_manager()
            base_context = manager._build_base_context(request)

            # Step 2: Create enriched context
            enriched = EnrichedContext(
                base_context=base_context,
                sources=[],
                expanded_terms={},
                confidence_scores={},
                metadata={},
            )

            # Step 3: Format for UI — binnen het gemeten interval.
            ui_preview = ContextFormatter().format_ui_preview(enriched)

            # Step 4: Format for prompt — actuele equivalent van de verwijderde
            # `_convert_request_to_context`; de échte route, geen mockprompt.
            prompt_service = PromptServiceV2()
            promptresultaat = await prompt_service.build_generation_prompt(request)

            end = time.perf_counter()
            times.append(end - start)
            promptresultaten.append(promptresultaat)
            ui_previews.append(ui_preview)

        # Gedrag vóór budget: elke gemeten flow leverde een echte UI-string en
        # een prompt met de werkelijke invoer erin.
        assert len(ui_previews) == 50
        for ui_preview in ui_previews:
            assert "Org:" in ui_preview or "📋" in ui_preview
        for promptresultaat in promptresultaten:
            assert promptresultaat.text
            assert promptresultaat.token_count > 0
            assert request.begrip in promptresultaat.text
            assert "OM" in promptresultaat.text
            assert "Strafrecht" in promptresultaat.text

        avg_time = sum(times) / len(times) * 1000  # ms
        max_time = max(times) * 1000

        assert avg_time < 200, f"E2E flow took {avg_time:.2f}ms average, exceeds 200ms"
        assert max_time < 400, f"E2E flow took {max_time:.2f}ms max, exceeds 400ms"

    @pytest.mark.benchmark
    @pytest.mark.performance
    @pytest.mark.advisory
    def test_anders_processing_overhead(self):
        """Anders option processing should add minimal overhead"""
        request_normal = GenerationRequest(
            id="perf-anders-normaal",
            begrip="test",
            organisatorische_context=["OM", "DJI", "Rechtspraak"],
        )

        request_anders = GenerationRequest(
            id="perf-anders",
            begrip="test",
            organisatorische_context=[
                "OM",
                "Anders...",
                "CustomOrg",
                "DJI",
                "Anders...",
                "Custom2",
            ],
        )

        manager = _maak_manager()

        times_normal = []
        times_anders = []
        normale_resultaten = []
        anders_resultaten = []

        for _ in range(100):
            start = time.perf_counter()
            resultaat_normaal = manager._build_base_context(request_normal)
            end = time.perf_counter()
            times_normal.append(end - start)
            normale_resultaten.append(resultaat_normaal)

            start = time.perf_counter()
            resultaat_anders = manager._build_base_context(request_anders)
            end = time.perf_counter()
            times_anders.append(end - start)
            anders_resultaten.append(resultaat_anders)

        # Gedrag vóór budget. De baseline wordt niet weggegooid: beide kanten
        # moeten hun exacte, geordende lijst hebben opgeleverd, anders vergelijkt
        # de overheadmeting twee niet-vergelijkbare bewerkingen.
        assert len(normale_resultaten) == 100
        assert len(anders_resultaten) == 100
        for resultaat in normale_resultaten:
            assert resultaat["organisatorisch"] == ["OM", "DJI", "Rechtspraak"]
        for resultaat in anders_resultaten:
            gevonden = resultaat["organisatorisch"]
            assert "CustomOrg" in gevonden, gevonden
            assert "Custom2" in gevonden, gevonden
            # De meting mag geen Anders-verwerking claimen die niet plaatsvindt.
            assert resultaat["organisatorisch"] == [
                "OM",
                "CustomOrg",
                "DJI",
                "Custom2",
            ], "Anders... niet verwerkt; er is dus geen Anders-verwerking gemeten"

        avg_normal = sum(times_normal) / len(times_normal)
        avg_anders = sum(times_anders) / len(times_anders)
        overhead_percent = ((avg_anders - avg_normal) / avg_normal) * 100

        assert (
            overhead_percent < 20
        ), f"Anders processing adds {overhead_percent:.1f}% overhead, exceeds 20% limit"

    @pytest.mark.benchmark
    @pytest.mark.performance
    def test_memory_efficiency(self):
        """Context processing should be memory efficient"""
        request = GenerationRequest(
            id="perf-memory",
            begrip="test",
            organisatorische_context=["OM", "DJI", "Rechtspraak"] * 10,
            juridische_context=["Strafrecht", "Bestuursrecht"] * 10,
            wettelijke_basis=["Art. 27 Sv", "AWB"] * 10,
        )

        manager = _maak_manager()
        verwacht = {
            "organisatorisch": ["OM", "DJI", "Rechtspraak"],
            "juridisch": ["Strafrecht", "Bestuursrecht"],
            "wettelijk": ["Art. 27 Sv", "AWB"],
        }

        memory_mb, correcte_iteraties = meet_geheugen(manager, request, 1000, verwacht)

        # Gedrag vóór budget: élke van de 1000 iteraties leverde de exacte
        # lijsten op. Er wordt niets bewaard — accumulatie zou juist de
        # geheugenmeting veranderen; alleen een teller gaat mee.
        assert correcte_iteraties == 1000

        assert memory_mb < 10, f"Memory usage {memory_mb:.2f}MB exceeds 10MB limit"

    @pytest.mark.performance
    @pytest.mark.parametrize("vooraf_actief", [False, True])
    def test_memory_tracemalloc_hersteld_op_foutpad(self, vooraf_actief):
        """`meet_geheugen` laat de tracemalloc-toestand achter zoals hij was.

        Draait de echte meetroutine met een gecontroleerde contextfout, zowel
        met als zonder een reeds lopende tracemalloc-sessie. Er wordt geen
        globale stop/reset buiten het eigen bereik gedaan.
        """

        class _FoutieveManager(HybridContextManager):
            def _build_base_context(self, request):
                raise RuntimeError("gecontroleerde contextfout")

        request = GenerationRequest(id="perf-memory-foutpad", begrip="test")

        wij_startten = vooraf_actief and not tracemalloc.is_tracing()
        if wij_startten:
            tracemalloc.start()
        try:
            toestand_vooraf = tracemalloc.is_tracing()
            # Expliciete, echt toetsbare preconditie: de uitgangssituatie moet
            # zijn wat deze parameter beschrijft. Draaide er al een sessie bij
            # vooraf_actief=False, dan is dit geval ongeschikt en faalt het
            # hier eerlijk; die bestaande sessie wordt bewust niet gestopt.
            assert toestand_vooraf is vooraf_actief, (
                f"ongeschikte uitgangssituatie: tracemalloc.is_tracing()="
                f"{toestand_vooraf}, verwacht {vooraf_actief}; een reeds lopende "
                "sessie blijft ongemoeid"
            )

            with pytest.raises(RuntimeError, match="gecontroleerde contextfout"):
                meet_geheugen(_FoutieveManager(ContextConfig()), request, 5, {})

            assert tracemalloc.is_tracing() is toestand_vooraf
        finally:
            if wij_startten:
                tracemalloc.stop()

    @pytest.mark.benchmark
    @pytest.mark.performance
    @pytest.mark.advisory
    def test_concurrent_processing_performance(self):
        """Context processing should handle concurrent requests efficiently"""
        requests = [
            GenerationRequest(
                id=f"perf-concurrent-{i}",
                begrip=f"test_{i}",
                organisatorische_context=["OM", "DJI", f"Org{i}"],
                juridische_context=["Strafrecht", f"Domain{i}"],
                wettelijke_basis=["Art. 27 Sv", f"Law{i}"],
            )
            for i in range(10)
        ]

        manager = _maak_manager()

        def process_request(req):
            start = time.perf_counter()
            result = manager._build_base_context(req)
            end = time.perf_counter()
            return req.id, end - start, result

        start_time = time.perf_counter()

        # De timeouts hieronder begrenzen het *wachten* op resultaten. Zij
        # begrenzen de afsluiting van de executor NIET: `with` roept
        # shutdown(wait=True) aan en wacht op reeds gestarte futures, en een
        # cancel() raakt alleen nog niet gestarte werk. Het uiteindelijke
        # vangnet is de procesdeadline van de canonieke runner; hier wordt geen
        # eigen executor-framework gebouwd.
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_request, req) for req in requests]
            try:
                results = [
                    f.result(timeout=30)
                    for f in concurrent.futures.as_completed(futures, timeout=60)
                ]
            finally:
                for f in futures:
                    f.cancel()

        total_time = time.perf_counter() - start_time

        # Gedrag vóór timing: elk verzoek kreeg zijn eigen, exacte context.
        # Deze assertions moeten uitgevoerd worden, ook als de timingformule
        # daarna faalt.
        assert len(results) == len(requests)
        per_id = {req_id: result for req_id, _duur, result in results}
        assert set(per_id) == {req.id for req in requests}
        for req in requests:
            index = req.id.rsplit("-", 1)[1]
            result = per_id[req.id]
            assert result["organisatorisch"] == ["OM", "DJI", f"Org{index}"]
            assert result["juridisch"] == ["Strafrecht", f"Domain{index}"]
            assert result["wettelijk"] == ["Art. 27 Sv", f"Law{index}"]

        individual_times = [duur for _req_id, duur, _result in results]
        avg_individual = sum(individual_times) / len(individual_times) * 1000
        total_time_ms = total_time * 1000

        # Each request should still be fast
        assert (
            avg_individual < 50
        ), f"Individual processing too slow: {avg_individual:.2f}ms average"

        # Total time should be less than sum of individual times (parallelism benefit)
        sequential_estimate = sum(individual_times) * 1000
        assert (
            total_time_ms < sequential_estimate * 0.5
        ), f"Concurrent processing too slow: {total_time_ms:.2f}ms"
