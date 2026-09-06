"""Rode Fase-A-contracten voor kwaliteitsbewijs (DEF-626 / DEF-627 / DEF-630).

Drie *positieve* contractverwachtingen die de huidige code aantoonbaar niet
waarmaakt. Ze staan bewust in een eigen map met ``pytest.mark.red_phase`` en
``pytest.mark.future``: geen `unit`, `integration`, `acceptance` of `smoke`,
zodat een rood toekomstcontract nooit stilzwijgend een huidige hoofdgate wordt.

`future` is de expliciete dispositie, niet een filter op rood zijn: deze drie
nodes draaien in het optionele `future`-profiel van
``scripts/testing/run_profile.py`` en horen daar aantoonbaar rood te zijn.

* eigenaars: DEF-626 (snapshotvelden), DEF-627 (oude score na edit) en
  DEF-630 (verplichte gate/bypass) — elk bij zijn eigen issue geregistreerd;
* trigger: vrijgave van het bijbehorende Fase-A-herstel bij dat issue;
* herbeoordeling: 2026-10-06 (zie ook onderaan deze docstring).

Uitgangspunten die voor alle drie gelden:

* Er wordt **geen** Fase-A-productgedrag geïmplementeerd; deze module wijzigt
  geen productiecode, schema, gate of migratie.
* Er staat **geen** `skip`, `xfail` of `pytest.raises` om het ontbrekende
  productgedrag groen te maken, en er staat geen assertie die het huidige
  defect als gewenst gedrag vastlegt.
* Setup en de werkelijke actie moeten aantoonbaar *slagen* voordat de gewenste
  contractassertie faalt. Een collectiefout, `AttributeError`, ontbrekende rol
  of setupfout is uitdrukkelijk **geen** bewijs voor deze contracten.
* Er wordt uitsluitend geasserteerd op de huidige, bestaande representatie
  (`DefinitieRecord.validation_score` / `validation_date` /
  `validation_issues`); er wordt geen nieuwe snapshot-API verzonnen.
* Elke proef draait op een nieuwe tijdelijke synthetische database uit de
  bestaande bevroren fixture (`tests/integration/functionality/conftest.py`).
  Geen gebruikersdata, geen SQL naar een bestaand bestand, geen netwerk.
* Zelf verkregen resources (SQLite-verbindingen) worden vanaf het moment van
  verkrijgen in een `finally` gesloten.

Vervaldatum voor herbeoordeling: **2026-10-06** (alle drie). Dat verval is een
reminder voor een expliciete beoordeling door de eigenaar — het is nadrukkelijk
géén automatisch skip-, xfail- of verwijderbesluit.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from domain.ontological_categories import OntologischeCategorie
from tests.integration.functionality.conftest import (
    # Fixture-import: pytest lost `bevroren_omgeving` op uit deze modulenaamruimte.
    bevroren_omgeving,
)

pytestmark = [pytest.mark.red_phase, pytest.mark.future]

_PROJECTWORTEL = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------
# Vaste synthetische invoer
# --------------------------------------------------------------------------

BEGRIP = "vervoersverbod"
CATEGORIE = OntologischeCategorie.PROCES.value
ORGANISATORISCH = "Openbaar Ministerie"
JURIDISCH = "strafprocesrecht"
WETTELIJK = "Wetboek van Strafvordering artikel 509"
CONTEXT: dict[str, list[str]] = {
    "organisatorisch": [ORGANISATORISCH],
    "juridisch": [JURIDISCH],
    "wettelijk": [WETTELIJK],
}

#: Score van een eerdere run. Hoog genoeg om elke drempel in
#: `config/approval_gate.yaml` te passeren (hard_min 0.75), zodat het contract
#: niet per ongeluk door een drempelwaarde wordt gered.
OUDE_SCORE = 0.95

OUDE_TEKST = (
    "Handeling waarbij een bevoegde instantie een persoon verbiedt zich met "
    "een vervoermiddel te verplaatsen."
)
NIEUWE_TEKST = (
    "Bevoegdheid van het Openbaar Ministerie om een verdachte tijdelijk het "
    "gebruik van elk motorrijtuig te ontzeggen, conform het Wetboek van "
    "Strafvordering."
)

REDACTEUR = "synthetische-redacteur"
VASTSTELLER = "synthetische-vaststeller"
WIJZIGINGSREDEN = "synthetische Fase-A-proef: tekst volledig herschreven"
VASTSTELNOTITIE = "synthetische vaststelling zonder actueel validatiesnapshot"


# --------------------------------------------------------------------------
# Hulpmiddelen
# --------------------------------------------------------------------------


def _verse_rij(db_path: Path, definitie_id: int) -> dict[str, Any] | None:
    """Lees de rij via een **nieuwe** SQLite-verbinding en sluit die altijd.

    Bewust buiten elke repository om: een positief serviceantwoord bewijst nog
    geen duurzame rij. De verbinding is vanaf het openen eigendom van deze
    helper, dus `close()` staat in `finally`.
    """
    verbinding = sqlite3.connect(str(db_path))
    try:
        verbinding.row_factory = sqlite3.Row
        rij = verbinding.execute(
            "SELECT * FROM definities WHERE id = ?", (definitie_id,)
        ).fetchone()
        return dict(rij) if rij is not None else None
    finally:
        verbinding.close()


def _spiegel_gatepolicy(werkmap: Path) -> None:
    """Spiegel `config/approval_gate.yaml` naar de tijdelijke werkmap.

    `GatePolicyService` opent dat pad CWD-relatief. Zonder deze spiegeling zou
    de gate stil op ingebouwde defaults draaien en zou de waarneming over de
    poortuitkomst een andere policy beschrijven dan de applicatie gebruikt. De
    inhoud wordt niet aangepast; het bestand in de repository blijft ongemoeid.
    """
    bron = _PROJECTWORTEL / "config" / "approval_gate.yaml"
    assert bron.is_file(), f"setup: gate-policy ontbreekt in de repository: {bron}"
    doel = werkmap / "config" / "approval_gate.yaml"
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_bytes(bron.read_bytes())


@contextmanager
def _edit_service(db_path: Path, validation_service: Any) -> Iterator[Any]:
    """Echte `DefinitionEditService` op een tijdelijk db-pad, met opruiming.

    `DefinitieRepository.__init__` opent via `init_database()` een thread-local
    verbinding; die is vanaf dat moment van ons. De `finally` sluit haar ook
    wanneer de body afbreekt op een rode assertie.
    """
    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import DefinitionEditService

    repository: Any = None
    try:
        repository = DefinitionEditRepository(str(db_path))
        yield DefinitionEditService(
            repository=repository, validation_service=validation_service
        )
    finally:
        if repository is not None:
            toestand = getattr(repository.legacy_repo._db._thread_local, "state", None)
            if toestand is not None:
                toestand.close()


def _snapshotvelden(record: Any) -> dict[str, Any]:
    """De snapshotvelden die de huidige representatie werkelijk kent.

    Uitsluitend bestaande velden van `DefinitieRecord`, zodat een falend
    contract nooit op een `AttributeError` van een verzonnen API leunt.
    """
    return {
        "validation_score": record.validation_score,
        "validation_date": record.validation_date,
        "validation_issues": record.validation_issues,
        "version_number": record.version_number,
        "status": record.status,
    }


def _maak_synthetisch_record(
    repository: Any, *, tekst: str, status: str, score: float
) -> int:
    """Maak één synthetisch record via de **bestaande** repository-route.

    Geen directe SQL: `DefinitionRepository.save()` leest de score uit
    `metadata["validation_score"]` en de status uit `metadata["status"]` — dat
    is de huidige, echte schrijfweg voor deze velden.
    """
    from services.interfaces import Definition

    definitie = Definition(
        begrip=BEGRIP,
        definitie=tekst,
        categorie=CATEGORIE,
        organisatorische_context=[ORGANISATORISCH],
        juridische_context=[JURIDISCH],
        wettelijke_basis=[WETTELIJK],
        metadata={"validation_score": score, "status": status},
    )
    definitie_id = repository.save(definitie)
    assert isinstance(
        definitie_id, int
    ), f"setup: repository gaf geen numeriek id terug: {definitie_id!r}"
    return definitie_id


# --------------------------------------------------------------------------
# DEF-626 — het validatiesnapshot overleeft de opslaggrens niet
# --------------------------------------------------------------------------


async def test_def626_validatiesnapshot_overleeft_de_opslaggrens(
    bevroren_omgeving,  # noqa: F811
) -> None:
    """Het gemeten validatiebewijs hoort de opslaggrens te overleven.

    Contract (positief): na een generatie waarin werkelijk is gevalideerd,
    draagt de opgeslagen rij hetzelfde bewijs — de gemeten score, het moment
    van validatie en de gemeten overtredingen — en beschrijft dat bewijs
    dezelfde versie als de rij zelf.

    Werkelijke actie die eerst moet slagen: `ServiceAdapter.generate_definition`
    over de actieve `DefinitionOrchestratorV2` met de echte
    `ModularValidationService` (53 regels, `validation_status="validated"`,
    niet-lege dekking) en opslag via de echte repository.

    Eigenaar: **DEF-626** (Backlog) — de opslaggrens tussen
    `DefinitionOrchestratorV2` en `DefinitionRepository`. Aanleiding om te
    hernemen: DEF-626. Vervaldatum herbeoordeling: **2026-10-06** (reminder
    voor expliciete beoordeling, geen automatisch skipbesluit).
    """
    from services.service_factory import ServiceAdapter

    omgeving = bevroren_omgeving

    # --- werkelijke actie: generatie met echte validatie ------------------
    adapter = ServiceAdapter(omgeving.container)
    respons = await adapter.generate_definition(
        begrip=BEGRIP, context_dict=CONTEXT, categorie=CATEGORIE
    )
    assert (
        respons.success is True
    ), f"setup: generatie mislukte ({getattr(respons, 'error', None)})"
    assert respons.definition is not None, "setup: generatie leverde geen definitie"
    definitie_id = respons.definition.id
    assert isinstance(
        definitie_id, int
    ), f"setup: geen numeriek id toegekend: {definitie_id!r}"

    # --- de validated-run is echt en gemeten ------------------------------
    validatie = respons.validation_result
    assert isinstance(
        validatie, dict
    ), f"setup: geen validatieresultaat maar {type(validatie).__name__}"
    assert (
        validatie["validation_status"] == "validated"
    ), f"setup: validatiestatus is {validatie['validation_status']!r}"
    systeem = validatie["system"]
    assert systeem["degraded_mode"] is False, "setup: validatie draaide degraded"
    assert (
        systeem["rules_loaded"] == 53
    ), f"setup: {systeem['rules_loaded']} regels geladen i.p.v. 53"
    dekking = validatie["evaluation_coverage"]
    assert (
        dekking["evaluated"] > 0
    ), f"setup: er is niets geëvalueerd, dekking: {dekking}"
    gemeten_score = validatie["overall_score"]
    assert isinstance(
        gemeten_score, (int, float)
    ), f"setup: score is geen getal maar {gemeten_score!r}"
    gemeten_overtredingen = sorted(
        overtreding["code"] for overtreding in validatie["violations"]
    )
    assert gemeten_overtredingen, "setup: geen enkele overtreding gemeten"

    # --- teruglezen via de echte repository -------------------------------
    repository = omgeving.container.repository()
    record = repository.get_definitie(definitie_id)
    assert record is not None, "setup: repository vindt de zojuist opgeslagen rij niet"
    assert (
        record.definitie == respons.definition.definitie
    ), f"setup: opgeslagen tekst wijkt af van de gegenereerde: {record.definitie!r}"

    waargenomen = _snapshotvelden(record)
    bewijs = (
        f"gemeten in de run: score={gemeten_score}, dekking={dekking}, "
        f"overtredingen={gemeten_overtredingen}; "
        f"waargenomen bestaande snapshotvelden op de rij: {waargenomen}"
    )

    # --- contract: het bewijs overleeft de opslaggrens --------------------
    assert record.validation_score == gemeten_score, (
        "DEF-626: de gemeten validatiescore overleeft de opslaggrens niet — "
        f"{bewijs}"
    )
    assert record.validation_date is not None, (
        "DEF-626: er is geen validatiemoment opgeslagen, dus het bewijs is niet "
        f"aan een tijdstip te binden — {bewijs}"
    )
    assert (
        sorted(
            overtreding["code"] for overtreding in record.get_validation_issues_list()
        )
        == gemeten_overtredingen
    ), f"DEF-626: de gemeten overtredingen staan niet op de rij — {bewijs}"

    # Hetzelfde bewijs, gelezen langs de tweede echte repositoryroute, hoort
    # dezelfde versie te beschrijven als de rij die het bewijs draagt.
    domeinobject = repository.get(definitie_id)
    assert domeinobject is not None, "DEF-626: tweede repositoryroute vindt niets"
    assert domeinobject.metadata["validation_score"] == gemeten_score, (
        "DEF-626: de tweede leesroute ziet een andere score: "
        f"{domeinobject.metadata['validation_score']!r}"
    )
    assert domeinobject.metadata["version_number"] == record.version_number, (
        "DEF-626: bewijs en rij beschrijven niet dezelfde versie: "
        f"{domeinobject.metadata['version_number']!r} vs {record.version_number!r}"
    )


# --------------------------------------------------------------------------
# DEF-627 — de oude score blijft na een bewerking als bewijs staan
# --------------------------------------------------------------------------


def test_def627_oude_score_geldt_niet_als_bewijs_voor_nieuwe_tekst(
    bevroren_omgeving,  # noqa: F811
) -> None:
    """Na een tekstbewerking beschrijft de opgeslagen score de nieuwe tekst.

    Contract (positief): zodra de tekst via de echte `DefinitionEditService`
    verandert, is de score op de rij ofwel het resultaat van een hervalidatie
    van diezelfde bewerking, ofwel expliciet ongeldig gemaakt (leeg). De score
    van de vorige tekst mag niet ongewijzigd als actueel bewijs blijven staan.

    Werkelijke actie die eerst moet slagen: een synthetisch record met score
    0.95 via de bestaande repository, daarna een echte bewerking die de tekst
    én het versienummer aantoonbaar verandert.

    Deze proef ontwerpt geen backfill en wijzigt geen productie-invalidatie.

    Eigenaar: **DEF-627** (Backlog) — `DefinitionEditService.save_definition`
    en het updatepad van `DefinitionRepository`. Aanleiding om te hernemen:
    DEF-627. Vervaldatum herbeoordeling: **2026-10-06** (reminder voor
    expliciete beoordeling, geen automatisch skipbesluit).
    """
    omgeving = bevroren_omgeving
    repository = omgeving.container.repository()

    # --- synthetisch uitgangsrecord met een oude score --------------------
    definitie_id = _maak_synthetisch_record(
        repository, tekst=OUDE_TEKST, status="draft", score=OUDE_SCORE
    )
    voor = repository.get_definitie(definitie_id)
    assert voor is not None, "setup: het synthetische record is niet teruggelezen"
    assert (
        voor.validation_score == OUDE_SCORE
    ), f"setup: oorspronkelijke score is {voor.validation_score!r} i.p.v. {OUDE_SCORE}"
    assert (
        voor.definitie == OUDE_TEKST
    ), f"setup: oorspronkelijke tekst wijkt af: {voor.definitie!r}"
    oorspronkelijk = _snapshotvelden(voor)

    # --- werkelijke bewerking via de echte editservice --------------------
    with _edit_service(
        omgeving.db_path, omgeving.container.validation_orchestrator()
    ) as edit_service:
        sessie = edit_service.start_edit_session(definitie_id, user=REDACTEUR)
        assert (
            sessie["success"] is True
        ), f"setup: bewerksessie mislukte ({sessie.get('error')})"
        bewaard = edit_service.save_definition(
            definitie_id,
            {"definitie": NIEUWE_TEKST},
            user=REDACTEUR,
            reason=WIJZIGINGSREDEN,
        )
        assert (
            bewaard["success"] is True
        ), f"setup: opslaan van de bewerking mislukte ({bewaard.get('error')})"
        hervalidatie = bewaard["validation"]

    # --- de bewerking is echt: tekst én versie zijn veranderd -------------
    na = repository.get_definitie(definitie_id)
    assert na is not None, "setup: de bewerkte rij is niet teruggelezen"
    assert (
        na.definitie == NIEUWE_TEKST
    ), f"setup: de tekst is niet gewijzigd: {na.definitie!r}"
    assert na.version_number > voor.version_number, (
        "setup: het versienummer is niet opgehoogd "
        f"({voor.version_number} → {na.version_number})"
    )

    bewijs = (
        f"oorspronkelijk: {oorspronkelijk}; na bewerking: {_snapshotvelden(na)}; "
        f"hervalidatieresultaat van save_definition: {hervalidatie!r}"
    )

    # --- contract: de score beschrijft de actuele tekst -------------------
    if hervalidatie is None:
        # Geen hervalidatie uitgevoerd → het oude bewijs hoort expliciet
        # ongeldig te zijn gemaakt in plaats van ongewijzigd te blijven staan.
        assert na.validation_score is None, (
            "DEF-627: zonder hervalidatie blijft de score van de vorige tekst "
            f"als actueel bewijs staan — {bewijs}"
        )
    else:
        assert na.validation_score == hervalidatie.get("score"), (
            "DEF-627: de opgeslagen score komt niet uit de hervalidatie van "
            f"deze bewerking — {bewijs}"
        )


# --------------------------------------------------------------------------
# DEF-630 — vaststellen zonder actueel snapshot wordt niet geweigerd
# --------------------------------------------------------------------------


def test_def630_vaststellen_zonder_actueel_snapshot_wordt_geweigerd(
    bevroren_omgeving,  # noqa: F811
) -> None:
    """Een losse score zonder actueel snapshot mag geen vaststelling opleveren.

    Contract (positief): `DefinitionWorkflowService.update_status` weigert de
    overgang naar `established` zolang er geen actueel validatiesnapshot bij de
    huidige tekst hoort, en laat de oorspronkelijke status staan.

    Dit is **één** concrete bypassrepro op één route. Het is geen claim dat
    alle export- of statusroutes al zijn afgedekt.

    Zorgvuldig gescheiden van setupfouten: de overgang `review → established`
    is volgens de echte `WorkflowService` een geldige, actuele transitie
    (hieronder geasserteerd via `get_allowed_transitions`), en `update_status`
    kent geen rolparameter. Een ontbrekende rol kan de weigering hier dus niet
    verklaren; alleen de kwaliteitsgate kan dat.

    Eigenaar: **DEF-630** (Backlog) — `DefinitionWorkflowService.update_status`,
    dat rechtstreeks naar `repository.change_status` delegeert en de gate
    overslaat. Aanleiding om te hernemen: DEF-630. Vervaldatum herbeoordeling:
    **2026-10-06** (reminder voor expliciete beoordeling, geen automatisch
    skipbesluit).
    """
    omgeving = bevroren_omgeving
    _spiegel_gatepolicy(omgeving.werkmap)
    repository = omgeving.container.repository()

    # --- synthetisch record: hoge score, géén actueel snapshot ------------
    definitie_id = _maak_synthetisch_record(
        repository, tekst=OUDE_TEKST, status="review", score=OUDE_SCORE
    )
    voor = _verse_rij(omgeving.db_path, definitie_id)
    assert voor is not None, "setup: het synthetische record is niet teruggelezen"
    assert (
        voor["status"] == "review"
    ), f"setup: beginstatus is {voor['status']!r} i.p.v. 'review'"
    assert (
        voor["validation_score"] == OUDE_SCORE
    ), f"setup: score is {voor['validation_score']!r} i.p.v. {OUDE_SCORE}"
    assert voor["validation_date"] is None, (
        "setup: er staat wél een validatiemoment op de rij, dan is dit geen "
        f"proef zonder actueel snapshot: {voor['validation_date']!r}"
    )
    assert voor["validation_issues"] is None, (
        "setup: er staan wél opgeslagen issues, dan is dit geen proef zonder "
        f"actueel snapshot: {voor['validation_issues']!r}"
    )

    # --- de transitie zelf is geldig en actueel ---------------------------
    workflow = omgeving.container.definition_workflow_service()
    toegestaan = workflow.get_allowed_transitions(definitie_id)
    assert "established" in toegestaan, (
        "setup: 'established' is geen actueel toegestane overgang vanuit "
        f"'review' — gemeten: {toegestaan}"
    )
    poort = workflow.preview_gate(definitie_id)

    # --- werkelijke actie: vaststellen via de bestaande route -------------
    resultaat = workflow.update_status(
        definitie_id, "established", user=VASTSTELLER, notes=VASTSTELNOTITIE
    )
    na = _verse_rij(omgeving.db_path, definitie_id)
    assert na is not None, "setup: de rij is na de statuspoging niet teruggelezen"

    bewijs = (
        f"score={voor['validation_score']} zonder validation_date/"
        f"validation_issues; gate-uitkomst preview_gate={poort}; "
        f"update_status gaf {resultaat!r}; status vóór={voor['status']!r}, "
        f"na={na['status']!r}, approved_by={na['approved_by']!r}"
    )

    # --- contract: weigering plus behoud van de oorspronkelijke status ----
    assert resultaat is False, (
        "DEF-630: vaststellen wordt niet geweigerd terwijl er geen actueel "
        f"validatiesnapshot bij de tekst hoort — {bewijs}"
    )
    assert (
        na["status"] == voor["status"]
    ), f"DEF-630: de oorspronkelijke status is niet behouden — {bewijs}"
    assert (
        na["approved_by"] is None
    ), f"DEF-630: er is toch een vaststeller vastgelegd — {bewijs}"
