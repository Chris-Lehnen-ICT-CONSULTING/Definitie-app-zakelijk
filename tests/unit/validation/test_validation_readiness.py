"""DEF-621: readiness is verzamelingsgelijkheid, geen telling.

De huidige volledigheidsbepaling telt: `rule_cache.py:400` vergelijkt
`len(all_rules)` met het aantal bestanden op schijf. Die vergelijking is
tautologisch zodra bestanden ontbreken — bij nul bestanden geldt `0 == 0` en
meldt de cache volledigheid.

Deze suite legt de vervangende semantiek vast: readiness is waar dan en
slechts dan als de geladen regel-ID-verzameling gelijk is aan de contractuele
ID-set uit de root-SSOT, en die set niet leeg is. De beslissende case is
`52 gevonden, één verkeerd ID`: het aantal klopt, de verzameling niet. Een
telling laat die door; een verzamelingsvergelijking niet.

Daarnaast: de fingerprint moet zowel de regelbestanden als de contract-SSOT
dekken, en het schema moet een `validation_unknown` met een echte score
afwijzen.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from services.validation.interfaces import (
    CONTRACT_VERSION,
    UNKNOWN_REASON_RULESET_INCOMPLETE,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)
from services.validation.readiness import bepaal_readiness, bereken_fingerprint

pytestmark = [pytest.mark.unit]


CONTRACT_IDS: tuple[str, ...] = tuple(f"REG-{n:02d}" for n in range(1, 54))

SCHEMA_PAD = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "architectuur"
    / "contracts"
    / "schemas"
    / "validation_result.schema.json"
)


# ---------------------------------------------------------------- readiness


@pytest.mark.parametrize(
    ("naam", "geladen", "verwacht_ready", "verwacht_missing", "verwacht_unexpected"),
    [
        ("volledig 53/53", CONTRACT_IDS, True, 0, 0),
        ("52 van 53", CONTRACT_IDS[:-1], False, 1, 0),
        # De beslissende case: het AANTAL klopt (52), de VERZAMELING niet.
        (
            "52 gevonden met een verkeerd ID",
            CONTRACT_IDS[:-2] + ("REG-99",),
            False,
            2,
            1,
        ),
        ("fallback 7 van 53", CONTRACT_IDS[:7], False, 46, 0),
        ("superset 54", CONTRACT_IDS + ("REG-99",), False, 0, 1),
    ],
)
def test_readiness_vergelijkt_verzamelingen_niet_aantallen(
    naam: str,
    geladen: tuple[str, ...],
    verwacht_ready: bool,
    verwacht_missing: int,
    verwacht_unexpected: int,
) -> None:
    r = bepaal_readiness(CONTRACT_IDS, geladen)

    assert r.ready is verwacht_ready, naam
    assert len(r.missing_rule_ids) == verwacht_missing, (naam, r.missing_rule_ids)
    assert len(r.unexpected_rule_ids) == verwacht_unexpected, (
        naam,
        r.unexpected_rule_ids,
    )
    assert (r.reason is None) is verwacht_ready, naam
    if not verwacht_ready:
        assert r.reason == UNKNOWN_REASON_RULESET_INCOMPLETE, naam


def test_lege_contractset_is_nooit_compleet() -> None:
    """0/0 mag niet als compleet gelden — de huidige tautologie.

    `len(all_rules) == files_on_disk` levert bij nul bestanden `0 == 0` en
    dus "compleet". Een lege verwachte set betekent dat het contract niet
    gelezen kon worden; dat is per definitie niet ready.
    """
    assert bepaal_readiness((), ()).ready is False
    assert bepaal_readiness((), ()).reason == UNKNOWN_REASON_RULESET_INCOMPLETE


def test_readiness_normaliseert_schrijfwijzen() -> None:
    """`CON-01` (bestandsnaam) en `CON_01` (veld `id`) zijn hetzelfde ID.

    Zonder normalisatie zou een complete set als incompleet gelden, puur
    door de historische schrijfwijzen.
    """
    assert bepaal_readiness(("CON-01", "ARAI-02SUB1"), ("CON_01", "ARAI02SUB1")).ready


# -------------------------------------------------------------- fingerprint


@pytest.fixture
def bronnen(tmp_path: Path) -> tuple[Path, Path]:
    """Twee fingerprintbronnen: één regelbestand en de contract-SSOT."""
    regel = tmp_path / "REG-01.json"
    regel.write_text(json.dumps({"id": "REG_01"}), encoding="utf-8")
    ssot = tmp_path / "toetsregels_config.yaml"
    ssot.write_text("contract:\n  rule_ids: []\n", encoding="utf-8")
    return regel, ssot


def test_fingerprint_is_stabiel_zonder_wijziging(bronnen: tuple[Path, Path]) -> None:
    assert bereken_fingerprint(bronnen) == bereken_fingerprint(bronnen)


@pytest.mark.parametrize("index", [0, 1], ids=["regelbestand", "contract_ssot"])
def test_fingerprint_wijzigt_bij_elke_bron(
    bronnen: tuple[Path, Path], index: int
) -> None:
    """Beide bronnen tellen mee: regelbestanden én de contract-SSOT.

    Een fingerprint over alleen de regelmap zou een beschadigde of herstelde
    root-SSOT missen, terwijl juist die de verwachte ID-set bepaalt.
    """
    voor = bereken_fingerprint(bronnen)
    bronnen[index].write_text("gewijzigd", encoding="utf-8")
    assert bereken_fingerprint(bronnen) != voor


def test_fingerprint_wijzigt_bij_verdwenen_en_hersteld_bestand(
    bronnen: tuple[Path, Path],
) -> None:
    """Beide overgangen zijn zichtbaar: weg én terug."""
    origineel = bereken_fingerprint(bronnen)
    inhoud = bronnen[0].read_bytes()

    bronnen[0].unlink()
    incompleet = bereken_fingerprint(bronnen)
    assert incompleet != origineel

    bronnen[0].write_bytes(inhoud)
    assert bereken_fingerprint(bronnen) != incompleet


# ------------------------------------------------------------------ schema


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PAD.read_text(encoding="utf-8"))


def _basisresultaat(**overrides: Any) -> dict[str, Any]:
    resultaat: dict[str, Any] = {
        "version": CONTRACT_VERSION,
        "overall_score": 0.0,
        "is_acceptable": False,
        "violations": [],
        "passed_rules": [],
        "detailed_scores": {},
        "system": {"correlation_id": "3f8c1a2e-0000-4000-8000-000000000000"},
    }
    resultaat.update(overrides)
    return resultaat


def test_contractversie_is_verhoogd_naar_1_2_0() -> None:
    assert CONTRACT_VERSION == "1.2.0"
    assert _schema()["properties"]["validation_status"]["enum"] == [
        VALIDATION_STATUS_VALIDATED,
        VALIDATION_STATUS_UNKNOWN,
    ]


def test_unknown_resultaat_is_schemageldig() -> None:
    resultaat = _basisresultaat(
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
        validation_readiness={
            "ready": False,
            "expected_total": 53,
            "loaded_total": 52,
            "missing_rule_ids": ["REG-53"],
            "unexpected_rule_ids": [],
        },
    )
    Draft202012Validator(_schema()).validate(resultaat)


def test_unknown_met_echte_score_is_schema_ongeldig() -> None:
    """De placeholders zijn conditioneel afgedwongen, niet alleen beschreven.

    `overall_score` en `is_acceptable` blijven aanwezig voor compatibiliteit,
    maar bij `validation_unknown` zijn het uitsluitend fail-closed
    placeholders. Een score van 0,7 naast die status is een tegenspraak en
    moet het schema afwijzen — anders is de semantiek slechts proza.
    """
    resultaat = _basisresultaat(
        overall_score=0.7,
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
        validation_readiness={
            "ready": False,
            "expected_total": 53,
            "loaded_total": 52,
            "missing_rule_ids": ["REG-53"],
            "unexpected_rule_ids": [],
        },
    )
    with pytest.raises(ValidationError, match="0"):
        Draft202012Validator(_schema()).validate(resultaat)


def test_unknown_zonder_reden_is_schema_ongeldig() -> None:
    resultaat = _basisresultaat(validation_status=VALIDATION_STATUS_UNKNOWN)
    with pytest.raises(ValidationError, match="unknown_reason"):
        Draft202012Validator(_schema()).validate(resultaat)


def test_validated_resultaat_met_score_blijft_geldig() -> None:
    """De conditionele constraint mag het normale pad niet raken."""
    resultaat = _basisresultaat(
        overall_score=0.82,
        is_acceptable=True,
        validation_status=VALIDATION_STATUS_VALIDATED,
    )
    Draft202012Validator(_schema()).validate(resultaat)


def test_incompleet_readinessobject_is_schema_ongeldig() -> None:
    """Zodra `validation_readiness` aanwezig is, moet het volledig zijn.

    Een half ingevuld readinessobject — bijvoorbeeld zonder
    `missing_rule_ids` — geeft dezelfde onduidelijkheid als de telling die
    deze uitbreiding juist vervangt: de consumer weet dan wél dat er iets
    mist, maar niet wat. Alle vijf velden zijn daarom verplicht.
    """
    resultaat = _basisresultaat(
        validation_status=VALIDATION_STATUS_UNKNOWN,
        unknown_reason=UNKNOWN_REASON_RULESET_INCOMPLETE,
        validation_readiness={
            "ready": False,
            "expected_total": 53,
            "loaded_total": 52,
        },
    )
    with pytest.raises(ValidationError, match="missing_rule_ids"):
        Draft202012Validator(_schema()).validate(resultaat)


def test_schemaomschrijving_noemt_contractversie_1_2_0() -> None:
    """De omschrijving mag niet op 1.1.0 blijven staan terwijl de versie 1.2.0 is.

    Een schema dat zichzelf verkeerd nummert is precies zo misleidend als een
    resultaat dat zichzelf verkeerd nummert.
    """
    assert "1.2.0" in _schema()["description"]
