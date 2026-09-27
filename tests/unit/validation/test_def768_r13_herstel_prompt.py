"""DEF-768 R13-herstel — assess/19: answer/3-structuur en appstatus zonder buren.

De prompt beschrijft dezelfde plaatsgebonden routedekking die de code
afdwingt (`bewijs._dekkingsfout`), zodat het model een geldig answer/3 kan
geven. De toetsinstructie (norm) blijft ongewijzigd. Zonder buren staat de
appstatus als gegeven in de invoer: geen deskundige leegbevestiging; de app
bepaalt de open status, het model onderbouwt dat niet (R13-H5, C3).
"""

from __future__ import annotations

import hashlib

import pytest

from domain.ess05 import bewijs
from domain.ess05.contract import normaliseer_buren
from services.validation import ess05_assessment_service as svc

pytestmark = [pytest.mark.unit]

NORM = {"uitleg": "u", "toelichting": "t", "toetsvraag": "v", "geldigheid": "g"}
CONTEXT = {"organisatorische_context": ["Servicedesk ICT-middelen"]}
#: sha256 van de toetsinstructie van assess/18 (gemeten op BASE 5b2f83bc):
#: de norm verandert niet.
TOETSINSTRUCTIE_SHA256_18 = (
    "da9fff7fd83f6276060b3a7d0fd8f72b5dc3c1b3306c23bb28e535d63422a171"
)


def _prompt(buren=()):
    return svc.bouw_beoordelingsprompt(
        "uitleen",
        "tijdelijk en kosteloos ter beschikking stellen",
        CONTEXT,
        (),
        buren=normaliseer_buren(list(buren)),
        intentie=None,
        norm=NORM,
    )


def test_versies():
    assert svc.Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/19"
    assert bewijs.ANTWOORDSCHEMA == "ess05-answer/3"


def test_toetsinstructie_ongewijzigd():
    """De toetsinstructie is byte-gelijk aan die van assess/18."""
    huidig = hashlib.sha256(svc._TOETSINSTRUCTIE.encode("utf-8")).hexdigest()
    assert huidig == TOETSINSTRUCTIE_SHA256_18


def test_structuur_noemt_de_plaatsgebonden_routedekking():
    system, _ = _prompt()
    assert f'"schema_version": "{bewijs.ANTWOORDSCHEMA}"' in system
    assert "reason van het geheel" in system
    assert "missing_feature" in system and "citaat uit definition" in system
    assert "de app weigert" in system.lower()


def test_zonder_buren_appstatus_als_gegeven():
    _, user = _prompt()
    assert "geen deskundige bevestiging" in user
    assert "appstatus" in user.lower()


def test_verifierinvoer_zonder_appstatus_verify4_bytegelijk():
    """De verifier krijgt dezelfde invoerregels als onder assess/18 (verify/4)."""
    regels = svc._invoerregels(
        "uitleen", "tijdelijk", CONTEXT, (), buren=(), intentie=None
    )
    assert not any("appstatus" in r.lower() for r in regels)
    assert svc._APPSTATUS_GEEN_BUREN in _prompt()[1]


def test_met_buren_geen_appstatuszin():
    buur = {
        "term": "verhuur",
        "definitie": "tegen betaling",
        "herkomst": "gebruiker",
        "bevestigd": True,
    }
    _, user = _prompt([buur])
    assert "appstatus" not in user.lower()
