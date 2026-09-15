"""CON-01 — gemotiveerde expertkeuze 'Dit is geen contextvermelding' (DEF-622 R1).

Een gewoon woord dat samenvalt met een contextwaarde (`om` bij context `OM`)
is — case-insensitief, bewust zonder acroniem- of hoofdletterheuristiek — een
signaal dat een mens beoordeelt. Tot nu toe kon de expert zo'n signaal alleen
sluiten door het woord als 'inhoudelijk noodzakelijke naam' te bestempelen:
een onjuiste claim. Het contract krijgt een vierde beoordelingsuitkomst voor
een treffer (geen vierde regelstatus): *geen contextvermelding*, met reden en
actor, gebonden aan vingerafdruk en strikte versie. Dan is de treffer
*Voldoet* zonder naamclaim. Onbeoordeeld blijft het signaal open; een échte
registratievermelding elders blijft leidend (beslissing per treffer).

Ook de aanleiding/helptekst hoort een gewoon woord niet als bewezen naam te
presenteren en de derde keuze te benoemen.

Bewijsgrens: dit is de CON-01-uitkomst; de algemene vaststelgate (DEF-630)
en de generieke overridegaten blijven buiten deze proef.
"""

from __future__ import annotations

from typing import Any

import pytest

from domain.context.contract import (
    FUNCTIE_REGISTRATIE,
    STATUS_FAIL,
    STATUS_OPEN,
    STATUS_PASS,
    beoordeel_context,
)
from services.null_repository import NullDefinitionRepository
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

# De opgeslagen functiecode, bewust als literal (niet de contractconstante):
# zo toetst de proef de persistente waarde die in records en readback staat.
FUNCTIE_GEEN_CONTEXT = "not_context"

BEGRIP = "toezicht"
OM_ZIN = (
    "Handeling die door een toezichthouder wordt verricht om naleving vast te stellen."
)
CONTEXT: dict[str, Any] = {"organisatorische_context": ["OM"]}
REDEN = "'om' is hier het voegwoord, geen verwijzing naar het Openbaar Ministerie."
ACTOR = "synthetische-expert"
VERSIE = 3


def _open(tekst: str = OM_ZIN, contexten: dict[str, Any] | None = None):
    uitkomst = beoordeel_context(BEGRIP, tekst, contexten or CONTEXT)
    treffers = [p for p in uitkomst.parts if p.evidence]
    return uitkomst, treffers


def _review(
    fingerprint: str,
    beslissingen: dict[str, dict[str, str]],
    *,
    actor: str = ACTOR,
    versie: Any = VERSIE,
) -> dict[str, Any]:
    return {
        "fingerprint": fingerprint,
        "actor": actor,
        "version_number": versie,
        "decisions": beslissingen,
    }


def _geen_context(treffer_id: str, reden: str = REDEN) -> dict[str, dict[str, str]]:
    return {treffer_id: {"function": FUNCTIE_GEEN_CONTEXT, "reason": reden}}


def test_open_signaal_presenteert_gewoon_woord_niet_als_bewezen_naam():
    uitkomst, treffers = _open()

    assert uitkomst.status == STATUS_OPEN
    (om,) = treffers
    assert om.evidence == "om" and om.context_value == "OM"
    # Aanleiding: een treffer, geen bewezen naam.
    assert "de naam '" not in om.reason.lower(), om.reason
    # Vervolgstap: de derde keuze is zichtbaar naast registratie/noodzakelijk.
    assert "geen contextvermelding" in om.action.lower(), om.action


def test_gemotiveerde_keuze_geen_contextvermelding_geeft_pass_zonder_naamclaim():
    uitkomst, (om,) = _open()

    beoordeeld = beoordeel_context(
        BEGRIP,
        OM_ZIN,
        CONTEXT,
        review=_review(uitkomst.fingerprint, _geen_context(om.id)),
        definitie_versie=VERSIE,
    )

    assert beoordeeld.status == STATUS_PASS
    assert beoordeeld.review is not None and beoordeeld.review["applied"] is True
    assert beoordeeld.review["actor"] == ACTOR
    deel = next(p for p in beoordeeld.parts if p.evidence)
    assert deel.status == STATUS_PASS
    assert REDEN in deel.reason
    # Geen onjuiste naamclaim: dit is geen 'noodzakelijke naam'.
    assert "noodzakelijk" not in deel.reason.lower(), deel.reason
    assert beoordeeld.als_dict()["score"] is None


@pytest.mark.parametrize(
    "variant",
    ["zonder-reden", "zonder-actor", "andere-tekst", "andere-context", "andere-versie"],
)
def test_keuze_bindt_aan_reden_actor_vingerafdruk_en_strikte_versie(variant):
    """Zonder reden of actor telt de keuze niet; bij gewijzigde tekst, context
    of versie geldt zij niet meer: het signaal staat opnieuw open."""
    uitkomst, (om,) = _open()
    tekst, contexten = OM_ZIN, CONTEXT
    review = _review(uitkomst.fingerprint, _geen_context(om.id))
    if variant == "zonder-reden":
        review = _review(uitkomst.fingerprint, _geen_context(om.id, reden="  "))
    elif variant == "zonder-actor":
        review = _review(uitkomst.fingerprint, _geen_context(om.id), actor="")
    elif variant == "andere-tekst":
        tekst = OM_ZIN[:-1] + " binnen het OM."
    elif variant == "andere-context":
        contexten = {"organisatorische_context": ["OM", "DJI"]}
    elif variant == "andere-versie":
        review = _review(uitkomst.fingerprint, _geen_context(om.id), versie=2)

    beoordeeld = beoordeel_context(
        BEGRIP, tekst, contexten, review=review, definitie_versie=VERSIE
    )

    assert beoordeeld.status == STATUS_OPEN, variant
    assert beoordeeld.review is not None and beoordeeld.review["applied"] is False
    assert all(p.status == STATUS_OPEN for p in beoordeeld.parts if p.evidence)


def test_beslissing_per_treffer_registratievermelding_elders_blijft_leidend():
    tekst = "Handeling die door Stichting Zilver wordt verricht om naleving vast te stellen."
    contexten = {"organisatorische_context": ["OM", "Stichting Zilver"]}
    uitkomst, treffers = _open(tekst, contexten)
    om = next(p for p in treffers if p.evidence == "om")
    zilver = next(p for p in treffers if p.evidence == "Stichting Zilver")

    # Alleen 'om' beoordeeld: die treffer sluit, de naam blijft open.
    deels = beoordeel_context(
        BEGRIP,
        tekst,
        contexten,
        review=_review(uitkomst.fingerprint, _geen_context(om.id)),
        definitie_versie=VERSIE,
    )
    assert deels.status == STATUS_OPEN
    assert {p.id: p.status for p in deels.parts if p.evidence} == {
        om.id: STATUS_PASS,
        zilver.id: STATUS_OPEN,
    }

    # Beide beoordeeld: de registratievermelding is en blijft 'Voldoet niet'.
    beslissingen = {
        **_geen_context(om.id),
        zilver.id: {
            "function": FUNCTIE_REGISTRATIE,
            "reason": "Noemt alleen de registrerende organisatie.",
        },
    }
    volledig = beoordeel_context(
        BEGRIP,
        tekst,
        contexten,
        review=_review(uitkomst.fingerprint, beslissingen),
        definitie_versie=VERSIE,
    )
    assert volledig.status == STATUS_FAIL
    assert {p.id: p.status for p in volledig.parts if p.evidence} == {
        om.id: STATUS_PASS,
        zilver.id: STATUS_FAIL,
    }


@pytest.mark.asyncio
async def test_via_echte_validator_pass_zonder_cijfer():
    """Op de productiegrens (echte regelset): de vastgelegde keuze maakt
    CON-01 'Voldoet' zonder cijfer en zonder violation."""
    validator = ModularValidationService(
        toetsregel_manager=get_toetsregel_manager(),
        repository=NullDefinitionRepository(),
    )
    context: dict[str, Any] = {**CONTEXT, "definition_version": VERSIE}
    eerste = await validator.validate_definition(
        begrip=BEGRIP, text=OM_ZIN, context=context
    )
    assert eerste["rule_statuses"]["CON-01"] == "review_required"
    open_detail = eerste["rule_results"]["CON-01"]
    om = next(p for p in open_detail["parts"] if p.get("evidence") == "om")
    context["context_review"] = _review(
        open_detail["fingerprint"], _geen_context(om["id"])
    )

    resultaat = await validator.validate_definition(
        begrip=BEGRIP, text=OM_ZIN, context=context
    )

    assert resultaat["rule_statuses"]["CON-01"] == "pass"
    detail = resultaat["rule_results"]["CON-01"]
    assert detail["score"] is None
    assert detail["review"]["applied"] is True
    assert not any(v.get("code") == "CON-01" for v in resultaat["violations"])
    assert resultaat["overall_score"] is None
