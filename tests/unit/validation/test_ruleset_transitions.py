"""DEF-621: beide regelset-overgangen worden op dezelfde service-instantie gezien.

De regels worden vandaag **eenmalig in `__init__`** geladen; daarna verandert
de interne state nooit meer. Op één instantie wordt dus geen van beide
overgangen opgemerkt — niet compleet→incompleet en niet incompleet→hersteld.
De TTL van een uur (`rule_cache.py:24,98,147`) is daar niet de enige oorzaak
van, maar maakt het herstelgat wel een uur lang zichtbaar.

Deze suite eist detectie via een fingerprint over de regelbestanden én de
contract-SSOT, met de contractuele ID-set als autoriteit. Beide richtingen,
beide echte injectiepaden, binnen een niet-verlopen TTL.

De concurrency-case gebruikt **echte threads**. `asyncio.gather` volstaat niet:
de verversing draait volledig synchroon vóór het eerste `await`, dus
coroutines op één event loop interleaven daar nooit en de race wordt niet
gereproduceerd.
"""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
import yaml

from services.validation.interfaces import (
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager
from toetsregels.runtime_contract import (
    load_root_contract_policy,
    root_contract_policy,
)

pytestmark = [pytest.mark.unit]

# Een recordveld dat geen enkele regel-JSON draagt. Wordt in de
# policytransitietest tijdelijk verplicht gesteld in de root-SSOT.
VELD_NIEUW = "nieuw_verplicht_veld"


ECHTE_REGELS = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
ECHTE_SSOT = (
    Path(__file__).resolve().parents[3]
    / "config"
    / "toetsregels"
    / "toetsregels_config.yaml"
)


@pytest.fixture(scope="module")
def alle_regels() -> dict[str, str]:
    return {
        pad.stem: pad.read_text(encoding="utf-8")
        for pad in sorted(ECHTE_REGELS.glob("*.json"))
    }


@pytest.fixture
def regelmap(tmp_path: Path, alle_regels: dict[str, str]) -> Path:
    """Een volledige kopie van de echte 53 regelbestanden."""
    d = tmp_path / "regels"
    d.mkdir()
    for naam, inhoud in alle_regels.items():
        (d / f"{naam}.json").write_text(inhoud, encoding="utf-8")
    return d


@pytest.fixture(params=["ToetsregelManager", "CachedToetsregelManager"])
def managerfabriek(
    request: pytest.FixtureRequest,
) -> Iterator[Callable[[Path], Any]]:
    """Beide echte injectiepaden, op dezelfde tijdelijke regelmap.

    `RuleCache` is een proces-singleton met een vast `regels_dir`. Die wordt
    hier op de tijdelijke map gezet zodat het productiepad werkelijk wordt
    getest en niet stilzwijgend op de echte regelmap terugvalt.

    De teardown is niet optioneel. Zonder herstel houdt de singleton na afloop
    een tijdelijke - en in deze suite doelbewust incomplete - regelset vast,
    die dan in latere tests opduikt als een onverklaarbare failure. Volgorde
    telt: eerst `regels_dir` terugzetten, daarna pas legen, zodat de memo en
    de decoratorcache niet opnieuw met de tijdelijke set worden gevuld.
    """
    opgeruimd: list[tuple[Any, Path]] = []

    def maak(regels_dir: Path) -> Any:
        if request.param == "ToetsregelManager":
            return ToetsregelManager(base_dir=str(regels_dir.parent))
        manager = CachedToetsregelManager()
        origineel = manager.cache.regels_dir
        manager.cache.regels_dir = regels_dir
        manager.clear_cache()
        opgeruimd.append((manager, origineel))
        return manager

    yield maak

    for manager, origineel in opgeruimd:
        manager.cache.regels_dir = origineel
        manager.clear_cache()


async def _status(service: ModularValidationService) -> str:
    resultaat = await service.validate_definition(
        begrip="besluit",
        text="besluit: een schriftelijke beslissing van een bestuursorgaan",
    )
    return str(resultaat["validation_status"])


# ------------------------------------------------------------- beide wegen


@pytest.mark.asyncio
async def test_compleet_naar_incompleet_op_dezelfde_instantie(
    regelmap: Path, managerfabriek: Callable[[Path], Any]
) -> None:
    """Een verdwenen regelbestand mag geen uur lang onzichtbaar blijven."""
    service = ModularValidationService(toetsregel_manager=managerfabriek(regelmap))
    assert await _status(service) == VALIDATION_STATUS_VALIDATED

    next(iter(sorted(regelmap.glob("*.json")))).unlink()

    assert await _status(service) == VALIDATION_STATUS_UNKNOWN


@pytest.mark.asyncio
async def test_incompleet_naar_hersteld_op_dezelfde_instantie(
    regelmap: Path, managerfabriek: Callable[[Path], Any]
) -> None:
    """Herstel binnen de TTL moet direct zichtbaar zijn — de kern van punt 6."""
    doel = next(iter(sorted(regelmap.glob("*.json"))))
    inhoud = doel.read_text(encoding="utf-8")
    doel.unlink()

    service = ModularValidationService(toetsregel_manager=managerfabriek(regelmap))
    assert await _status(service) == VALIDATION_STATUS_UNKNOWN

    doel.write_text(inhoud, encoding="utf-8")

    assert await _status(service) == VALIDATION_STATUS_VALIDATED


@pytest.mark.asyncio
async def test_beschadigde_contract_ssot_wordt_gezien_en_hersteld(
    regelmap: Path,
    managerfabriek: Callable[[Path], Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """De contract-SSOT hoort óók in de fingerprint.

    Zonder die bron zou een beschadigde of herstelde `toetsregels_config.yaml`
    onopgemerkt blijven, terwijl juist die de verwachte ID-set bepaalt.
    """
    ssot = tmp_path / "toetsregels_config.yaml"
    ssot.write_text(ECHTE_SSOT.read_text(encoding="utf-8"), encoding="utf-8")
    # raising=False: `ROOT_SSOT_PAD` komt pas in commit 3. Zonder deze vlag
    # zou de monkeypatch nu een AttributeError geven en zou de test rood staan
    # om een testopzetfout in plaats van om ontbrekende functionaliteit.
    monkeypatch.setattr(
        "services.validation.modular_validation_service.ROOT_SSOT_PAD",
        ssot,
        raising=False,
    )

    service = ModularValidationService(toetsregel_manager=managerfabriek(regelmap))
    assert await _status(service) == VALIDATION_STATUS_VALIDATED

    origineel = ssot.read_text(encoding="utf-8")
    ssot.write_text("contract: {}\n", encoding="utf-8")
    assert await _status(service) == VALIDATION_STATUS_UNKNOWN

    ssot.write_text(origineel, encoding="utf-8")
    assert await _status(service) == VALIDATION_STATUS_VALIDATED


@pytest.mark.asyncio
async def test_geldige_contractpolicywijziging_wordt_gezien_en_hersteld(
    regelmap: Path,
    managerfabriek: Callable[[Path], Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eén snapshot mag geen twee policygeneraties mengen.

    De verwachte ID-set wordt vers uit `ROOT_SSOT_PAD` gelezen, maar
    `build_rule_records()` haalde de recordvereisten opnieuw uit het met
    `lru_cache` afgedekte `root_contract_policy()`. Een SSOT die geldig
    blijft en exact dezelfde 53 ID's houdt, maar één extra verplicht
    recordveld eist, werd daardoor half gezien: nieuwe ID's, oude
    recordpolicy. De regelset dekt dat contract niet meer en de uitkomst
    hoort `validation_unknown` te zijn.

    De wijziging is bewust *geldig*, niet corrupt. Alleen zo bewijst de test
    dat de policy zelf meeverhuist; bij een kapotte YAML zou het laden toch
    al klappen en zou de menging onzichtbaar blijven.
    """
    # Warm de procescache deterministisch op. Zonder deze aanroep zou de
    # lru_cache pas later gevuld kunnen worden - mogelijk mét de gewijzigde
    # policy - en zou de test de menging niet meer meten.
    gecacht = root_contract_policy()

    ssot = tmp_path / "toetsregels_config.yaml"
    origineel = ECHTE_SSOT.read_text(encoding="utf-8")
    ssot.write_text(origineel, encoding="utf-8")
    monkeypatch.setattr(
        "services.validation.modular_validation_service.ROOT_SSOT_PAD", ssot
    )

    service = ModularValidationService(toetsregel_manager=managerfabriek(regelmap))
    assert await _status(service) == VALIDATION_STATUS_VALIDATED

    ruw = yaml.safe_load(origineel)
    velden = ruw["loading"]["formats"]["json"]["required_fields"]
    assert VELD_NIEUW not in velden, "opzetfout: het veld was al verplicht"
    velden.append(VELD_NIEUW)
    ssot.write_text(
        yaml.safe_dump(ruw, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    # De gewijzigde SSOT is geldig en noemt exact dezelfde ID's ...
    gewijzigd = load_root_contract_policy(ssot)
    assert set(gewijzigd.rule_ids) == set(gecacht.rule_ids)
    assert VELD_NIEUW in gewijzigd.record_required_fields
    assert VELD_NIEUW not in gecacht.record_required_fields
    # ... maar geen enkel regelrecord draagt het nieuwe verplichte veld.
    dragers = [
        pad.name
        for pad in sorted(regelmap.glob("*.json"))
        if VELD_NIEUW in json.loads(pad.read_text(encoding="utf-8"))
    ]
    assert dragers == [], f"opzetfout: records dragen {VELD_NIEUW}: {dragers}"

    assert await _status(service) == VALIDATION_STATUS_UNKNOWN

    ssot.write_text(origineel, encoding="utf-8")
    assert await _status(service) == VALIDATION_STATUS_VALIDATED


@pytest.mark.asyncio
async def test_ongewijzigde_bronnen_herladen_niet(
    regelmap: Path, managerfabriek: Callable[[Path], Any]
) -> None:
    """De fingerprint mag de cachewinst niet weggooien op het happy path."""
    manager = managerfabriek(regelmap)
    service = ModularValidationService(toetsregel_manager=manager)

    tellingen: list[int] = []
    origineel = manager.get_all_regels

    def tellend() -> dict[str, Any]:
        tellingen.append(1)
        return origineel()

    manager.get_all_regels = tellend  # type: ignore[method-assign]

    await _status(service)
    await _status(service)

    assert tellingen == [], "regels herladen zonder dat een bron wijzigde"


# ---------------------------------------------------- echte threadconcurrentie


def test_mislukte_reload_geeft_onder_threads_nooit_een_positief_resultaat(
    regelmap: Path, monkeypatch: pytest.MonkeyPatch, alle_regels: dict[str, str]
) -> None:
    """Geen enkele thread mag een gemengd of positief resultaat krijgen.

    De verversing is synchroon en draait vóór het eerste `await`; met
    `asyncio.gather` op één event loop interleaven de threads daar dus niet
    en zou de race onzichtbaar blijven. Daarom echte threads: een
    `threading.Barrier` laat ze gelijk starten en elke worker draait zijn
    eigen `asyncio.run`.
    """
    aantal = 8
    service = ModularValidationService(
        toetsregel_manager=ToetsregelManager(base_dir=str(regelmap.parent))
    )
    assert asyncio.run(_status(service)) == VALIDATION_STATUS_VALIDATED

    # Wijzig de bron zodat elke thread een verversing triggert, en laat die
    # verversing vervolgens falen.
    (regelmap / "extra.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        ModularValidationService,
        "_bouw_snapshot",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("herlaadpoging faalt")),
    )

    barrier = threading.Barrier(aantal)

    def worker() -> dict[str, Any]:
        barrier.wait(timeout=10)
        return asyncio.run(
            service.validate_definition(
                begrip="besluit",
                text="besluit: een schriftelijke beslissing van een bestuursorgaan",
            )
        )

    with ThreadPoolExecutor(max_workers=aantal) as pool:
        resultaten = [
            f.result(timeout=30) for f in [pool.submit(worker) for _ in range(aantal)]
        ]

    assert len(resultaten) == aantal
    for i, r in enumerate(resultaten):
        assert r["validation_status"] == VALIDATION_STATUS_UNKNOWN, i
        assert r["overall_score"] == 0.0, i
        assert r["is_acceptable"] is False, i
        assert r["passed_rules"] == [], i
        assert "acceptance_gate" not in r, i
