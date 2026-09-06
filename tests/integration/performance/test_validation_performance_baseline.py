"""Performance baseline voor ModularValidationService.

DEF-519: deze baseline mat tot nu toe het fail-closed noodpad. Elke test
bouwde de service met ``toetsregel_manager=None``; dan blijft de regelset
leeg, stopt ``validate_definition`` vóór het eerste await op de
readiness-guard en keert een ``validation_unknown``-resultaat terug met
``evaluated=0`` en een leeg ``rule_statuses``. De gemeten latency,
geheugengroei en doorvoer waren dus die van een vroege return, niet van
validatie.

Alle metingen draaien nu op een echte ``ToetsregelManager`` met de
regeldata van deze checkout. Elke gemeten route toont via
``_borg_echte_evaluatie`` aan dat het resultaat ``validated`` is en dat de
regels werkelijk zijn geëvalueerd; keert het noodpad terug, dan valt de
test om in plaats van een timing over niets te rapporteren.

Geen live API en geen productiedata: de manager leest uitsluitend de
JSON-regelbestanden uit de checkout en elke test draait in een verse
tijdelijke werkmap.
"""

from __future__ import annotations

import asyncio
import gc
import importlib
import statistics
import time
from typing import Any

import pytest

from services.validation.modular_validation_service import ModularValidationService
from services.validation.module_adapter import ValidationModuleAdapter
from services.validation.types_internal import EvaluationContext
from toetsregels.manager import ToetsregelManager

pytestmark = [pytest.mark.performance]


@pytest.fixture(autouse=True)
def verse_werkmap(tmp_path, monkeypatch):
    """Draai elke meting in een eigen, verse tijdelijke werkmap.

    De service en de manager werken met absolute paden; deze fixture borgt
    dat geen enkele meting toch op de repo- of gebruikerswerkmap steunt.
    """
    werkmap = tmp_path / "def519-perf-cwd"
    werkmap.mkdir()
    monkeypatch.chdir(werkmap)
    return werkmap


@pytest.fixture(scope="module")
def regelset_ids() -> tuple[str, ...]:
    """De regel-ids die de echte manager uit deze checkout laadt."""
    ids = tuple(sorted(ToetsregelManager().get_all_regels() or {}))
    assert ids, "ToetsregelManager laadde geen regeldata uit de checkout"
    return ids


def _maak_service() -> ModularValidationService:
    """De service zoals de baseline haar hoort te meten.

    Met een echte manager dekt de regelset het contract, komt de guard niet
    in actie en raakt de meting het werkelijke evaluatiepad.
    """
    return ModularValidationService(
        toetsregel_manager=ToetsregelManager(),
        cleaning_service=None,
        config=None,
    )


def _borg_echte_evaluatie(
    resultaat: dict[str, Any], regelset_ids: tuple[str, ...]
) -> dict[str, Any]:
    """Toon aan dat de zojuist gemeten aanroep werkelijk heeft geëvalueerd.

    Elke assertie discrimineert tegen het noodpad: met
    ``toetsregel_manager=None`` is de status ``validation_unknown``, staat
    ``degraded_mode`` op True, is ``rule_statuses`` leeg en meldt de dekking
    nul geëvalueerde regels. Geeft de dekking terug zodat aanroepers de
    feitelijke aantallen kunnen tonen.
    """
    assert resultaat["validation_status"] == "validated", (
        "gemeten route leverde geen geëvalueerd resultaat: "
        f"{resultaat.get('validation_status')} "
        f"({resultaat.get('unknown_reason')})"
    )
    systeem = resultaat["system"]
    assert systeem["degraded_mode"] is False, systeem
    assert systeem["rules_loaded"] == len(regelset_ids), systeem
    assert systeem["rules_expected"] == len(regelset_ids), systeem

    statussen = resultaat["rule_statuses"]
    assert set(statussen) >= set(regelset_ids), sorted(
        set(regelset_ids) - set(statussen)
    )

    dekking = resultaat["evaluation_coverage"]
    assert dekking["total"] == len(statussen), dekking
    assert dekking["evaluated"] == dekking["passed"] + dekking["failed"], dekking
    assert dekking["evaluated"] > 0, dekking
    assert dekking["coverage_ratio"] > 0.0, dekking
    return dekking


# DEF-519 advisory-dispositie voor de V1-vergelijking hieronder. Geen
# waiver-in-stilte: eigenaar, reden, trigger en vervaldatum staan in de
# skipreden zelf, zodat de melding in elk testrapport meekomt.
V1_MODULE = "services.definition_validator"
ADVISORY_V1 = (
    "advisory (DEF-519, eigenaar DEF-519, vervalt 2026-10-06): de V1-vergelijking "
    "meet geen huidig equivalent meer. DefinitionValidator is verwijderd in commit "
    "15bb27bc ('feat: remove legacy DefinitionValidator completely', 2025-09-01, "
    "-357 regels src/services/definition_validator.py); er is geen tweede actieve "
    "validatie-implementatie om V2 tegen af te zetten. Een cijfer produceren zou "
    "een valse benchmark zijn. Trigger om deze node weer te activeren: er komt een "
    "tweede actieve validatieroute in de codebase, of de disposition vervalt op "
    "2026-10-06 en moet opnieuw worden beoordeeld."
)


# advisory (DEF-519): de node is in de skipreden hierboven al als advisory
# vastgelegd — er is geen onafhankelijke V1-validator meer en een module wordt
# niet met zichzelf vergeleken. De bestaande skip blijft ongewijzigd; de marker
# haalt de node alleen uit de verplichte gate. Owner: DEF-519 (advisory).
# Trigger: een onafhankelijke V1-baseline komt beschikbaar.
# Herbeoordeling: 2026-10-06.
@pytest.mark.performance
@pytest.mark.advisory
def test_performance_vs_v1_baseline():
    """De V1-vergelijking heeft geen huidig equivalent meer (DEF-519).

    Deze node blijft bestaan als drager van haar dispositie, maar rapporteert
    bewust geen getal. De eerdere opzet ving elke ``ImportError`` breed af en
    sloeg dan stil over; daardoor was niet te zien of V1 ontbrak of dat de
    import om een andere reden brak. Nu is het ontbreken van V1 een harde
    verwachting: keert er een ``services.definition_validator`` terug, dan
    valt deze test om en moet de vergelijking echt worden herbouwd in plaats
    van stil te blijven overslaan.

    De controle kijkt naar ``exc.name`` en niet naar het enkele feit dat er
    een ``ModuleNotFoundError`` viel. Een aanwezig maar kapot V1-modulepad dat
    zelf op een ontbrekende dependency struikelt, geeft namelijk dezelfde
    exceptieklasse maar een andere ``name``; die situatie hoort hier hard om
    te vallen en niet stil te worden overgeslagen als afwezige V1.
    """
    with pytest.raises(ModuleNotFoundError) as fout:
        importlib.import_module(V1_MODULE)

    ontbrekend = fout.value.name
    naam_melding = (
        f"verwacht dat {V1_MODULE} zelf ontbreekt, maar de import struikelde "
        f"op {ontbrekend!r}; V1 is dan aanwezig maar kapot en mag niet als "
        "afwezig worden gedisponeerd"
    )
    assert ontbrekend == V1_MODULE, naam_melding

    pytest.skip(ADVISORY_V1)


# Vaste synthetische lengteklassen met de bestaande latencylimieten in ms.
# Ongewijzigd overgenomen: de limieten zijn niet verruimd omdat de meting nu
# duurder is geworden.
LATENCY_GEVALLEN = [
    ("small", "x" * 10, 50),
    ("medium", "x" * 100, 100),
    ("large", "x" * 1000, 200),
    ("xlarge", "x" * 5000, 500),
]


@pytest.mark.performance
@pytest.mark.asyncio
async def test_validation_latency_bounds(regelset_ids):
    """Validatielatency blijft binnen de bestaande grenzen (DEF-519).

    Het timinginterval omsluit uitsluitend de ``validate_definition``-aanroep
    en die aanroep evalueert werkelijk: het resultaat van elke gemeten ronde
    wordt ná het stoppen van de klok tegen ``_borg_echte_evaluatie`` gelegd.
    """
    service = _maak_service()

    # Expliciete warmup, buiten elke meting. Vangt eenmalige kosten (imports,
    # eerste fingerprintmeting) op zodat die niet in de percentielen landen.
    await service.validate_definition(
        begrip="warmup",
        text=LATENCY_GEVALLEN[0][1],
        ontologische_categorie=None,
        context=None,
    )

    for name, text, max_ms in LATENCY_GEVALLEN:
        times = []
        resultaten = []

        # Run multiple times for statistical significance
        for _ in range(10):
            start = time.perf_counter()
            resultaat = await service.validate_definition(
                begrip=f"test_{name}",
                text=text,
                ontologische_categorie=None,
                context=None,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
            resultaten.append(resultaat)

        # Elke gemeten ronde moet echte evaluatie hebben omvat; anders is de
        # timing hierboven die van een vroege return.
        for resultaat in resultaten:
            _borg_echte_evaluatie(resultaat, regelset_ids)

        # Check 95th percentile is within bounds
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        p95_melding = (
            f"{name} text: 95th percentile {p95:.1f}ms exceeds limit {max_ms}ms"
        )
        assert p95 <= max_ms, p95_melding

        # Check median is well within bounds
        median = statistics.median(times)
        mediaan_melding = (
            f"{name} text: median {median:.1f}ms too close to limit {max_ms}ms"
        )
        assert median <= max_ms * 0.7, mediaan_melding


# Het budget waarbinnen een blokkerende regel afgekapt zou moeten worden.
# Ongewijzigd de bestaande 2.0s-grens: deze story stelt geen strenger
# timeoutcontract, zij bewijst alleen dat het bestaande contract ontbreekt.
ADAPTER_TIMEOUT_BUDGET_S = 2.0
# De blokkeerduur van de repro-regel. 3.0s ligt reproduceerbaar boven de
# 2.0s-grens en is genoeg om het ontbreken rood te bewijzen; de
# oorspronkelijke 10s zou alleen procesdeadline opeten.
ADAPTER_BLOKKEERDUUR_S = 3.0

# DEF-519 dispositie voor de afgesplitste timeoutrepro hieronder. Eigenaar van
# de TESTdispositie: DEF-519; het inhoudelijke implementatie- of
# intrekkingsbesluit is niet genomen.
#
# Bronfeiten (2026-09-06, read-only broncontrole):
# * ``src/services/validation/module_adapter.py`` (``evaluate``, ``evaluate_sync``)
#   kent geen budget en geen configuratie; een synchrone ``validate`` draait
#   direct door.
# * De enige gevonden directe aanroepers zijn deze performancetest en twee
#   unit-contracttests. Er is geen productiecaller in ``src``.
# * Het actieve validatiepad loopt via ``ModularValidationService._evaluate_rule``,
#   niet via deze adapter.
# * ``timeout_per_rule_ms`` in ``config/toetsregels/toetsregels_config.yaml``
#   wordt door ``src`` niet gelezen; er is geen mechanisme om dit stil te
#   activeren.
#
# Het gaat dus om een historisch nooit gebouwde, niet productiebedrade
# verwachting - niet om een geleverde garantie die is weggevallen. DEF-519
# bouwt daar geen nieuwe thread-/procesarchitectuur voor. De bestaande
# gemengde node is daarom gesplitst: de snelle adapteroverhead blijft
# REQUIRED, de historische timeoutverwachting krijgt een eigen advisory-node
# met exact dezelfde 2.0s-grens, dezelfde 3.0s-fixture, dezelfde
# errored-eis en zonder skip of xfail. De ontbrekende garantie blijft zo
# zichtbaar rood zonder een nieuwe productgarantie als voorwaarde op te
# voeren. Trigger: vrijgegeven productbedrading of timeoutcontract voor deze
# adapter. Herbeoordeling uiterlijk 2026-10-06.
DISPOSITIE_ADAPTER_TIMEOUT = (
    "rode advisory-repro (testdispositie-eigenaar DEF-519, herbeoordeling "
    "uiterlijk 2026-10-06): adaptertimeout is nooit gebouwd en is niet "
    "productiebedraad; trigger is vrijgegeven productbedrading of een "
    "timeoutcontract voor ValidationModuleAdapter"
)


def _adapter_context() -> EvaluationContext:
    """Gedeelde evaluatiecontext voor de twee adapternodes hieronder."""
    return EvaluationContext(
        raw_text="test",
        cleaned_text="test",
        begrip="test",
        locale=None,
        profile=None,
        correlation_id="perf-test",
        tokens=[],
        metadata={},
    )


@pytest.mark.performance
@pytest.mark.asyncio
async def test_rule_evaluation_overhead():
    """Overhead per regel-evaluatie op het actieve adapterpad.

    DEF-519: deze node toetst actief gedrag en blijft daarom REQUIRED. De
    historische timeoutverwachting die hier eerder in dezelfde body zat, staat
    nu apart in ``test_adapter_kapt_blokkerende_regel_af`` - zie
    ``DISPOSITIE_ADAPTER_TIMEOUT`` voor de onderbouwing van die splitsing.
    """
    adapter = ValidationModuleAdapter()

    class FastRule:
        code = "FAST-01"

        def validate(self, context):
            return {"score": 0.8, "violations": []}

    ctx = _adapter_context()

    # Expliciete warmup, telt niet als meting.
    await adapter.evaluate(FastRule(), ctx)

    # Measure fast rule overhead
    fast_times = []
    for _ in range(100):
        start = time.perf_counter()
        resultaat = await adapter.evaluate(FastRule(), ctx)
        elapsed = time.perf_counter() - start
        fast_times.append(elapsed * 1000)
        assert resultaat["rule_code"] == "FAST-01", resultaat
        assert not resultaat.get("errored", False), resultaat

    # Fast rule overhead should be minimal (< 1ms)
    median_overhead = statistics.median(fast_times)
    overhead_melding = f"Rule evaluation overhead {median_overhead:.2f}ms is too high"
    assert median_overhead < 1.0, overhead_melding


# advisory (DEF-519): de afgesplitste, historisch nooit gebouwde
# timeoutverwachting. Bewust GEEN skip en GEEN xfail - de node hoort rood te
# staan zolang de afkapping ontbreekt. De grens, de blokkeerduur en de
# errored-eis zijn ongewijzigd overgenomen; er wordt geen ruimere grens gezet
# en er is geen productcode toegevoegd. Zie DISPOSITIE_ADAPTER_TIMEOUT.
@pytest.mark.performance
@pytest.mark.advisory
@pytest.mark.asyncio
async def test_adapter_kapt_blokkerende_regel_af():
    """Een blokkerende regel hoort binnen 2.0s afgekapt en errored terug te komen.

    De setup slaagt aantoonbaar: de adapter wordt gebouwd en de blokkerende
    regel wordt werkelijk geëvalueerd. Pas daarna valt de assertie om, op
    precies de ontbrekende afkapping - niet op een importfout of een vroege
    return.
    """
    adapter = ValidationModuleAdapter()
    ctx = _adapter_context()

    class BlokkerendeRule:
        code = "INF-01"

        def validate(self, context):
            time.sleep(ADAPTER_BLOKKEERDUUR_S)
            return {"score": 1.0, "violations": []}

    start = time.perf_counter()
    result = await adapter.evaluate(BlokkerendeRule(), ctx)
    elapsed = time.perf_counter() - start

    assert result["rule_code"] == "INF-01", result

    assert elapsed < ADAPTER_TIMEOUT_BUDGET_S, (
        "Timeout protection failed: de adapter liet een regel die "
        f"{ADAPTER_BLOKKEERDUUR_S:.1f}s blokkeert {elapsed:.2f}s doorlopen "
        f"in plaats van af te kappen binnen {ADAPTER_TIMEOUT_BUDGET_S:.1f}s. "
        f"{DISPOSITIE_ADAPTER_TIMEOUT}"
    )
    errored_melding = (
        f"Timed out rule should be marked as errored. {DISPOSITIE_ADAPTER_TIMEOUT}"
    )
    assert result.get("errored", False), errored_melding


CONCURRENCY_TEKST = "Een test definitie voor concurrent validation performance testing."
CONCURRENCY_NIVEAUS = [1, 5, 10, 20]

# DEF-519 dispositie voor de schaalrepro hieronder. Eigenaar: DEF-519
# (testzijde). De oorspronkelijke, niet-gekozen heuristiek luidt
# ``elapsed <= baseline_time * (1 + 0.5 * (n_concurrent - 1) / 10)``: hooguit
# 50% overhead per verdubbeling van de gelijktijdigheid. Er is geen
# productcode die dat waarmaakt en deze story implementeert geen
# schaalgarantie; de verwachting blijft daarom staan als zichtbare rode
# repro in plaats van als xfail of ruimere grens. Trigger voor het
# productbesluit: besluiten of gelijktijdige validatie werkelijk moet
# schalen (dan is dit een productbug) of dat de verwachting formeel
# vervalt. Herbeoordeling uiterlijk 2026-10-06.
DISPOSITIE_CONCURRENCY_SCHAAL = (
    "rode repro (eigenaar DEF-519, herbeoordeling uiterlijk 2026-10-06): "
    "de oorspronkelijke schaalverwachting elapsed <= baseline * "
    "(1 + 0.5 * (n - 1) / 10) heeft geen dekkende productcode; trigger is "
    "een productbesluit over schalen van gelijktijdige validatie"
)


# advisory (DEF-519): zuiver een hardware-/schalingsbudget op het echte
# evaluatiepad. De oorspronkelijke concurrencyformule en grens blijven
# ongewijzigd staan; er wordt geen versnelling geclaimd en niets verzwakt.
# Owner: testdispositie-519, inhoudelijke owner niet vastgesteld.
# Trigger: vrijgegeven performanceherstel. Herbeoordeling: 2026-10-06.
# Let op: `test_rule_evaluation_overhead` krijgt deze marker bewust NIET — die
# node meet uitsluitend het actieve adapterpad en blijft verplicht. De
# ontbrekende timeoutverwachting die daar eerder in dezelfde body zat, staat nu
# als eigen advisory-node in `test_adapter_kapt_blokkerende_regel_af`.
@pytest.mark.performance
@pytest.mark.advisory
@pytest.mark.asyncio
async def test_concurrent_validation_scaling(regelset_ids):
    """De oorspronkelijke schaalverwachting, nu op het echte evaluatiepad.

    DEF-519: deze node stond als timing-gevoelige xfail uitgeschakeld en mat
    bovendien het noodpad, dus zij bewees niets. De verwachting zelf is
    ongewijzigd overgenomen - zowel de formule als de niveaus. Nieuw is
    alleen dat de manager echt is en dat elke gemeten aanroep vóór de
    schaalassertie aantoont dat er werkelijk is geëvalueerd; anders zou een
    uitkomst hier opnieuw over een vroege return gaan.

    Er is geen ruimere vervangende grens gezet en er is geen productcode
    toegevoegd. Zie ``DISPOSITIE_CONCURRENCY_SCHAAL`` voor eigenaar, reden,
    trigger en herbeoordelingsdatum.
    """
    service = _maak_service()

    # Expliciete warmup, buiten elke meting.
    await service.validate_definition(
        begrip="warmup",
        text=CONCURRENCY_TEKST,
        ontologische_categorie=None,
        context=None,
    )

    baseline_time = 0.0
    for n_concurrent in CONCURRENCY_NIVEAUS:
        tasks = [
            service.validate_definition(
                begrip=f"test_{i}",
                text=CONCURRENCY_TEKST,
                ontologische_categorie=None,
                context={"correlation_id": f"perf-{i}"},
            )
            for i in range(n_concurrent)
        ]

        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # Eerst aantonen dat de zojuist gemeten ronde echte evaluatie was;
        # pas daarna heeft de schaaluitspraak betekenis.
        assert len(results) == n_concurrent
        for resultaat in results:
            _borg_echte_evaluatie(resultaat, regelset_ids)

        # First validation to establish baseline
        if n_concurrent == 1:
            baseline_time = elapsed
        else:
            # Should be less than 50% overhead per doubling of concurrency
            expected_max = baseline_time * (1 + 0.5 * (n_concurrent - 1) / 10)
            # Alleen de meldingsprecisie is opgehoogd: op twee decimalen las
            # deze repro als "0.01s exceeds expected 0.00s" en droeg zij geen
            # bruikbaar bewijs. De formule zelf is ongewijzigd.
            schaal_melding = (
                f"Concurrent {n_concurrent}: {elapsed:.4f}s exceeds expected "
                f"{expected_max:.4f}s (baseline {baseline_time:.4f}s). "
                f"{DISPOSITIE_CONCURRENCY_SCHAAL}"
            )
            assert elapsed <= expected_max, schaal_melding


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_validation_isolation(regelset_ids):
    """Gelijktijdige validaties lekken geen state en leveren gelijke dekking.

    DEF-519: dit is de correctheidscontrole die de schaalrepro hierboven niet
    kan geven, bewust als eigen node zodat die repro rood mag blijven zonder
    dit gedrag mee te slepen. Er staat hier geen tijdsgrens: dit toetst wat
    gelijktijdigheid aan de uitkomst doet, niet hoe snel zij is.
    """
    service = _maak_service()

    enkel = await service.validate_definition(
        begrip="referentie",
        text=CONCURRENCY_TEKST,
        ontologische_categorie=None,
        context={"correlation_id": "perf-referentie"},
    )
    referentiedekking = _borg_echte_evaluatie(enkel, regelset_ids)

    for n_concurrent in CONCURRENCY_NIVEAUS:
        results = await asyncio.gather(
            *[
                service.validate_definition(
                    begrip=f"test_{i}",
                    text=CONCURRENCY_TEKST,
                    ontologische_categorie=None,
                    context={"correlation_id": f"perf-{i}"},
                )
                for i in range(n_concurrent)
            ]
        )

        assert len(results) == n_concurrent
        for i, resultaat in enumerate(results):
            dekking = _borg_echte_evaluatie(resultaat, regelset_ids)
            # Geen state-lek tussen gelijktijdige aanroepen: elk resultaat
            # draagt de correlation_id van zijn eigen aanroep.
            assert resultaat["system"]["correlation_id"] == f"perf-{i}", resultaat[
                "system"
            ]
            # Gelijktijdigheid mag de uitkomst niet veranderen.
            assert dekking == referentiedekking, (n_concurrent, i, dekking)


@pytest.mark.performance
def test_memory_usage_stability(regelset_ids):
    """Geheugengebruik blijft stabiel over 100 echte validaties.

    De grens van 1000 nieuwe objecten is ongewijzigd overgenomen. De service
    wordt bewust vóór de nulmeting opgebouwd, zodat de eenmalige snapshot van
    de regelset niet als groei meetelt.
    """
    service = _maak_service()

    # Expliciete warmup, vóór de nulmeting: de eerste aanroep bouwt eenmalige
    # structuren op die anders als lek zouden ogen.
    asyncio.run(
        service.validate_definition(
            begrip="warmup",
            text="Test definitie voor de warmup van de geheugenmeting.",
            ontologische_categorie=None,
            context=None,
        )
    )

    # Force garbage collection
    gc.collect()

    # Measure initial memory (simplified - real profiling would use tracemalloc)
    initial_objects = len(gc.get_objects())

    async def run_validations():
        for i in range(100):
            resultaat = await service.validate_definition(
                begrip=f"test_{i}",
                text=f"Test definitie nummer {i} voor memory leak detection.",
                ontologische_categorie=None,
                context=None,
            )
            # Elke ronde moet echte evaluatie zijn geweest; het resultaat
            # wordt bewust niet vastgehouden, anders meet de groei de
            # testopzet in plaats van de service.
            _borg_echte_evaluatie(resultaat, regelset_ids)

    asyncio.run(run_validations())

    # Force garbage collection
    gc.collect()

    # Check memory didn't grow excessively
    final_objects = len(gc.get_objects())
    object_growth = final_objects - initial_objects

    # Allow some growth but not linear with iterations
    groei_melding = (
        f"Possible memory leak: {object_growth} new objects after 100 validations"
    )
    assert object_growth < 1000, groei_melding


@pytest.mark.performance
@pytest.mark.benchmark
def test_validation_throughput(benchmark, regelset_ids):
    """Benchmark de doorvoer van een volledige validatie.

    De bestaande benchmarkfixture wordt gebruikt; haar werkelijke
    returnwaarde wordt geasserteerd. De eerdere assertie (``overall_score``
    aanwezig) slaagde ook op het noodpad, want dat resultaat draagt datzelfde
    veld als fail-closed placeholder.
    """
    service = _maak_service()

    async def validate_once():
        return await service.validate_definition(
            begrip="benchmark",
            text="Een benchmark definitie om de throughput te meten van de validatie service.",
            ontologische_categorie=None,
            context=None,
        )

    # Run benchmark
    result = benchmark(lambda: asyncio.run(validate_once()))

    # Verify result is valid: het echte resultaat van de gemeten aanroep moet
    # een volledig geëvalueerde validatie zijn.
    assert "overall_score" in result
    _borg_echte_evaluatie(result, regelset_ids)

    # Benchmark stats will be automatically reported by pytest-benchmark
