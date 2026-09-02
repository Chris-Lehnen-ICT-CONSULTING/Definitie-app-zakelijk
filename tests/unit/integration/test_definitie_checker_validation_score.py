"""DEF-621: een onbekende validatiescore wordt niet als oordeel opgeslagen.

`ServiceAdapter.to_ui_response` zet bij `validation_unknown` bewust
`final_score = 0.0` als fail-closed compatibiliteitsplaceholder: er is niets
getoetst, dus er is geen score. `DefinitieChecker` schreef die nul echter als
echte `validation_score` in de database, waarna Edit- en Expert-tab hem later
als rood kwaliteitsoordeel tonen - niet te onderscheiden van een definitie die
werkelijk nul haalt.

Er zijn precies twee levende opslagroutes:

1. `DefinitieChecker.generate_with_check` -> `_save_generated_definition_v2`;
2. `DefinitieChecker.update_existing_definition` -> `repository.update_definitie`.

De ingesprongen `generate_with_integrated_service` staat na een `return` en
heeft geen call-sites; die is hier bewust geen onderwerp.

De discriminator komt uitsluitend uit het geneste `validation_details`. De
top-level `final_score` draagt hem niet: daar staat de placeholder zelf.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from database.definitie_repository import DefinitieRecord
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import (
    CheckAction,
    DefinitieChecker,
    DefinitieCheckResult,
)

pytestmark = pytest.mark.unit


def _ui_response(final_score: float, status: str | None) -> dict[str, Any]:
    """De UI-dict zoals `to_ui_response` hem oplevert."""
    details: dict[str, Any] = {
        "overall_score": final_score,
        "is_acceptable": status == "validated",
        "violations": [],
        "passed_rules": [],
    }
    if status is not None:
        details["validation_status"] = status
    if status == "validation_unknown":
        details["unknown_reason"] = "ruleset_incomplete"
        details["validation_readiness"] = {
            "ready": False,
            "expected_total": 53,
            "loaded_total": 7,
        }
    return {
        "success": True,
        "definitie_origineel": "een schriftelijke beslissing",
        "definitie_gecorrigeerd": "een schriftelijke beslissing van een bestuursorgaan",
        "final_score": final_score,
        "validation_details": details,
        "voorbeelden": {},
        "metadata": {},
        "sources": [],
    }


class _StubAdapter:
    """Levert een vaste UI-dict; geen AI-aanroep, geen netwerk."""

    def __init__(self, ui_response: dict[str, Any]) -> None:
        self._ui_response = ui_response

    async def generate_definition(self, *args: Any, **kwargs: Any) -> object:
        return object()

    def to_ui_response(self, response: Any) -> dict[str, Any]:
        return self._ui_response


def _checker(ui_response: dict[str, Any]) -> tuple[DefinitieChecker, MagicMock]:
    repo = MagicMock()
    repo.create_definitie.return_value = 42
    repo.update_definitie.return_value = True
    checker = DefinitieChecker(repository=repo)
    checker._get_integrated_service = lambda: _StubAdapter(ui_response)  # type: ignore[method-assign]
    checker.check_before_generation = lambda *a, **kw: DefinitieCheckResult(  # type: ignore[method-assign]
        action=CheckAction.PROCEED
    )
    return checker, repo


# ------------------------------------------- route 1: generate_with_check


def _genereer(ui_response: dict[str, Any]) -> MagicMock:
    checker, repo = _checker(ui_response)
    checker.generate_with_check(
        begrip="besluit",
        organisatorische_context="Gemeente",
        categorie=OntologischeCategorie.TYPE,
        force_generate=True,
    )
    assert repo.create_definitie.called, "route 1 heeft niets opgeslagen"
    return repo


def test_generatie_slaat_geen_placeholder_op_bij_validation_unknown() -> None:
    """De 0.0 is geen oordeel, dus er hoort niets in de scorekolom te staan."""
    repo = _genereer(_ui_response(0.0, "validation_unknown"))

    record = repo.create_definitie.call_args.args[0]
    assert record.validation_score is None, record.validation_score


def test_generatie_bewaart_de_score_bij_validated() -> None:
    """Het normale pad blijft ongewijzigd."""
    repo = _genereer(_ui_response(0.82, "validated"))

    assert repo.create_definitie.call_args.args[0].validation_score == 0.82


def test_generatie_bewaart_de_score_bij_legacy_zonder_status() -> None:
    """Zonder discriminator geldt onverkort het bestaande gedrag."""
    repo = _genereer(_ui_response(0.82, None))

    assert repo.create_definitie.call_args.args[0].validation_score == 0.82


# --------------------------------------- route 2: update_existing_definition


def _bestaand_record() -> DefinitieRecord:
    return DefinitieRecord(
        id=7,
        begrip="besluit",
        definitie="oude definitie",
        categorie=OntologischeCategorie.TYPE.value,
        organisatorische_context="Gemeente",
        juridische_context="",
        validation_score=0.75,
        version_number=1,
    )


def _update(ui_response: dict[str, Any]) -> MagicMock:
    checker, repo = _checker(ui_response)
    repo.get_definitie.return_value = _bestaand_record()
    checker.update_existing_definition(7, updated_by="tester", regenerate=True)
    assert repo.update_definitie.called, "route 2 heeft niets bijgewerkt"
    return repo


def test_update_wist_de_oude_score_bij_validation_unknown() -> None:
    """Een oude score mag niet blijven staan als hij niet meer is vastgesteld.

    Het record droeg 0.75. Na een regeneratie zonder oordeel is die waarde
    niet langer waar; hem laten staan zou een score tonen die bij een andere
    definitietekst hoort. `None` maakt de onbepaaldheid expliciet.
    """
    repo = _update(_ui_response(0.0, "validation_unknown"))

    updates = repo.update_definitie.call_args.args[1]
    assert "validation_score" in updates, updates
    assert updates["validation_score"] is None, updates


def test_update_bewaart_de_score_bij_validated() -> None:
    repo = _update(_ui_response(0.82, "validated"))

    assert repo.update_definitie.call_args.args[1]["validation_score"] == 0.82


def test_update_bewaart_de_score_bij_legacy_zonder_status() -> None:
    repo = _update(_ui_response(0.82, None))

    assert repo.update_definitie.call_args.args[1]["validation_score"] == 0.82


# ------------------------- route 2 tegen de ECHTE repository (einde-tot-einde)
#
# De mocktests hierboven bewijzen welk payload de checker samenstelt, maar niet
# dat de repository daar iets mee doet. Twee defecten bleven daardoor
# onzichtbaar: de checker gaf `version_number + 1` mee terwijl de repository dat
# veld leest als de verwachte HUIDIGE versie (optimistic lock) en zelf ophoogt,
# en `validation_score` ontbrak in de allowed_fields. Het resultaat was een
# update die stilzwijgend niets deed. Deze tests draaien daarom door de échte
# `DefinitieRepository` op een tijdelijke SQLite-database.


def _echte_repo_met_definitie(tmp_path: Any) -> tuple[Any, int]:
    from database.definitie_repository import DefinitieRepository

    repo = DefinitieRepository(str(tmp_path / "def621_persistence.db"))
    record_id = repo.create_definitie(
        DefinitieRecord(
            begrip="besluit",
            definitie="oude definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="Gemeente",
            juridische_context="",
            validation_score=0.75,
        )
    )
    return repo, record_id


def _update_echt(tmp_path: Any, ui_response: dict[str, Any]) -> tuple[bool, Any]:
    repo, record_id = _echte_repo_met_definitie(tmp_path)
    voor = repo.get_definitie(record_id)
    assert voor.validation_score == 0.75, "opzetfout: startscore ontbreekt"
    assert voor.version_number == 1, voor.version_number

    checker = DefinitieChecker(repository=repo)
    checker._get_integrated_service = lambda: _StubAdapter(ui_response)  # type: ignore[method-assign]

    succes, _ = checker.update_existing_definition(
        record_id, updated_by="tester", regenerate=True
    )
    return succes, repo.get_definitie(record_id)


def test_echte_update_wist_de_score_bij_validation_unknown(tmp_path) -> None:
    """De volledige route moet werkelijk landen in de database."""
    succes, na = _update_echt(tmp_path, _ui_response(0.0, "validation_unknown"))

    assert succes is True
    assert na.definitie == "een schriftelijke beslissing van een bestuursorgaan"
    assert na.validation_score is None, na.validation_score
    assert na.version_number == 2, na.version_number
    assert na.previous_version_id is None, na.previous_version_id


def test_echte_update_bewaart_de_score_bij_validated(tmp_path) -> None:
    succes, na = _update_echt(tmp_path, _ui_response(0.82, "validated"))

    assert succes is True
    assert na.validation_score == 0.82, na.validation_score
    assert na.version_number == 2, na.version_number


def test_echte_update_bewaart_de_score_bij_legacy_zonder_status(tmp_path) -> None:
    succes, na = _update_echt(tmp_path, _ui_response(0.82, None))

    assert succes is True
    assert na.validation_score == 0.82, na.validation_score


def test_echte_update_slaat_null_op_en_niet_de_string_none(tmp_path) -> None:
    """`None` moet als SQL NULL landen, niet als de tekst 'None'.

    Een kolom die de string bevat leest terug als waarheid en zou in de UI
    weer als oordeel opduiken.
    """
    repo, record_id = _echte_repo_met_definitie(tmp_path)
    checker = DefinitieChecker(repository=repo)
    checker._get_integrated_service = lambda: _StubAdapter(  # type: ignore[method-assign]
        _ui_response(0.0, "validation_unknown")
    )
    checker.update_existing_definition(record_id, updated_by="tester", regenerate=True)

    with repo._get_connection() as conn:
        rij = conn.execute(
            "SELECT validation_score FROM definities WHERE id = ?", (record_id,)
        ).fetchone()

    assert rij[0] is None, repr(rij[0])
