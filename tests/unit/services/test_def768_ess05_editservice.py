"""DEF-768 WP5: de editorroute van ESS-05 op een echte tijdelijke SQLite.

* `bouw_validatiecontext` geeft burenlijst, lege ruimte en de door de
  gebruiker genoemde verwante begrippen van de sessie mee (sessie wint);
* `normaliseer_validatieresultaat` bewaart de ESS-05-beoordeling en de
  actieve burenlijst van de toetsing;
* `save_definition` legt een sessiebeoordeling alleen vast als zij exact aan
  de op te slaan kandidaat en haar burenlijst bindt; anders met reden;
* een expertbesluit (bevestigen/afwijzen) wordt opgeslagen en heropend;
* `herbind_ess05_in_validatieresultaat` speelt een besluit af zonder
  AI-aanroep: een bevestiging of afwijzing maakt de oude beoordeling
  historisch (ADR-003: buurstatus en afgewezen voorstellen zitten in de
  bindingscontext); een nieuwe toetsing met de bevestigde buur voldoet.
* ADR-003: opslaan vereist de volledige ESS-05-binding (ook verifier en
  versies) én een geldige semantische verificatie van het concept.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest

from domain.ess05.expertacties import bevestig_buur, wijs_buur_af
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    bindingsafwijzing_ess05,
    bouw_validatiecontext,
    ess05_actieve_buren_van,
    ess05_uitkomst_van_definition,
    herbind_ess05_in_validatieresultaat,
    normaliseer_validatieresultaat,
)
from services.interfaces import Definition
from tests.fixtures.def768_fakes import BINDING, bouw_ess05_beoordeling

pytestmark = [pytest.mark.unit]

AT = "2026-09-23T12:00:00+00:00"
BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
ORG = ["Synthetische Uitleendienst"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}
REPOSITORYBUUR = {
    "id": "repository:9",
    "term": "klant",
    "definitie": "Persoon die iets afneemt.",
    "herkomst": "repository",
    "bevestigd": False,
}


def _definition(**overrides: Any) -> Definition:
    metadata = {"status": "draft", "created_by": "tester"}
    metadata.update(overrides.pop("metadata", {}))
    velden: dict[str, Any] = {
        "begrip": BEGRIP,
        "definitie": TEKST,
        "categorie": "type",
        "organisatorische_context": list(ORG),
        "juridische_context": [],
        "wettelijke_basis": [],
        "metadata": metadata,
    }
    velden.update(overrides)
    return Definition(**velden)


def _service(tmp_path, **definitie):
    repo = DefinitionEditRepository(str(tmp_path / "ess05-editor.db"))
    did = repo.save(_definition(**definitie))
    return DefinitionEditService(repository=repo, validation_service=None), did


def _updates(service, did, **over):
    huidig = service.repository.get(did)
    updates = {
        "begrip": huidig.begrip,
        "definitie": huidig.definitie,
        "organisatorische_context": list(huidig.organisatorische_context),
        "juridische_context": [],
        "wettelijke_basis": [],
        "categorie": huidig.categorie,
        "status": huidig.metadata.get("status"),
        "version_number": huidig.metadata.get("version_number"),
    }
    updates.update(over)
    return updates


def _intentie_van(service, did):
    from domain.ess03.contract import intentie_uit_context

    huidig = service.repository.get(did)
    return intentie_uit_context(bouw_validatiecontext(huidig, huidig.metadata))


class TestContextEnResultaat:
    def test_sessie_wint_voor_record_en_gebruikersburen_gaan_mee(self):
        record = {"ess05_buren": [{"term": "oud"}], "ess05_lege_ruimte": {"x": 1}}
        sessie = _definition(
            gerelateerde_begrippen=["werknemer"],
            metadata={"ess05_buren": [REPOSITORYBUUR], "ess05_lege_ruimte": {}},
        )
        ctx = bouw_validatiecontext(sessie, record)
        assert ctx["ess05_buren"] == [REPOSITORYBUUR]
        assert ctx["ess05_lege_ruimte"] == {}
        assert ctx["gerelateerde_begrippen"] == ["werknemer"]
        zonder_sessie = bouw_validatiecontext(_definition(), record)
        assert zonder_sessie["ess05_buren"] == [{"term": "oud"}]

    def test_normalisatie_bewaart_beoordeling_en_actieve_buren(self):
        doc = bouw_ess05_beoordeling(BEGRIP, TEKST, CONTEXT, [], buren=[REPOSITORYBUUR])
        genormaliseerd = normaliseer_validatieresultaat(
            {
                "validation_status": "completed",
                "ess05_assessment": doc,
                "ess05_actieve_buren": [REPOSITORYBUUR],
            }
        )
        assert genormaliseerd["ess05_assessment"] == doc
        assert genormaliseerd["ess05_actieve_buren"] == [REPOSITORYBUUR]


class TestOpslaan:
    def test_bindende_sessiebeoordeling_wordt_vastgelegd(self, tmp_path):
        service, did = _service(tmp_path)
        doc = bouw_ess05_beoordeling(
            BEGRIP,
            TEKST,
            CONTEXT,
            [],
            buren=[REPOSITORYBUUR],
            intentie=_intentie_van(service, did),
        )
        result = service.save_definition(
            did,
            _updates(service, did),
            user="tester",
            validate=False,
            ess05_assessment=doc,
            ess05_actieve_buren=[REPOSITORYBUUR],
            ess05_binding=BINDING,
        )
        assert result["success"] is True, result
        assert result["ess05_assessment_persisted"] is True
        assert service.repository.get(did).metadata["ess05_assessment"] == doc

    def test_niet_bindende_sessiebeoordeling_blijft_weg_met_reden(self, tmp_path):
        service, did = _service(tmp_path)
        doc = bouw_ess05_beoordeling(BEGRIP, TEKST, CONTEXT, [], buren=[REPOSITORYBUUR])
        result = service.save_definition(
            did,
            _updates(service, did, definitie="Een andere tekst dan getoetst."),
            user="tester",
            validate=False,
            ess05_assessment=doc,
            ess05_actieve_buren=[REPOSITORYBUUR],
            ess05_binding=BINDING,
        )
        assert result["success"] is True
        assert result["ess05_assessment_persisted"] is False
        assert "kandidaat" in result["ess05_assessment_reason"]
        assert "ess05_assessment" not in service.repository.get(did).metadata

    def test_ander_model_is_geen_actuele_beoordeling(self, tmp_path):
        service, did = _service(tmp_path)
        doc = bouw_ess05_beoordeling(
            BEGRIP,
            TEKST,
            CONTEXT,
            [],
            buren=[REPOSITORYBUUR],
            intentie=_intentie_van(service, did),
        )
        ander = replace(BINDING, model="nieuw-model")
        result = service.save_definition(
            did,
            _updates(service, did),
            validate=False,
            ess05_assessment=doc,
            ess05_actieve_buren=[REPOSITORYBUUR],
            ess05_binding=ander,
        )
        assert result["ess05_assessment_persisted"] is False
        assert "nieuw-model" in result["ess05_assessment_reason"]

    def test_expertbesluit_wordt_opgeslagen_en_heropend(self, tmp_path):
        service, did = _service(tmp_path)
        besluit = wijs_buur_af(
            [],
            [REPOSITORYBUUR],
            "repository:9",
            actor="deskundige",
            at=AT,
            grond="Klant speelt hier geen rol.",
        )
        result = service.save_definition(
            did, _updates(service, did, ess05_buren=besluit), validate=False
        )
        assert result["success"] is True, result
        heropend = service.repository.get(did)
        assert heropend.metadata["ess05_buren"] == besluit
        ctx = bouw_validatiecontext(heropend, heropend.metadata)
        assert ctx["ess05_buren"][0]["afgewezen"] is True


def _doc_voor_kandidaat() -> dict[str, Any]:
    from services.definition_edit_service import ess03_intentie_van_definition

    return bouw_ess05_beoordeling(
        BEGRIP,
        TEKST,
        CONTEXT,
        [],
        buren=[REPOSITORYBUUR],
        intentie=ess03_intentie_van_definition(_definition()),
    )


class TestHerbinding:
    def _resultaat(self, doc) -> dict[str, Any]:
        return {
            "validation_status": "completed",
            "rule_statuses": {"ESS-05": "review_required"},
            "rule_results": {"ESS-05": {"status": "review_required"}},
            "passed_rules": [],
            "violations": [],
            "review_required": [{"rule_id": "ESS-05", "reason": "open"}],
            "evaluation_coverage": {"review_required": 1, "passed": 0},
            "ess05_assessment": doc,
            "ess05_actieve_buren": [REPOSITORYBUUR],
        }

    def test_bevestiging_maakt_de_oude_beoordeling_historisch_zonder_ai_aanroep(
        self,
    ):
        """Gemigreerd (ADR-003, `/1` → `/2`): onder `/1` maakte een bevestiging
        een open beoordeling direct tot 'voldoet'. De buurstatus zit nu in de
        bindingscontext van beide stappen, dus de oude beoordeling wordt
        historisch; de nulcallroute blijft (geen AI-aanroep bij herbinden)."""
        doc = _doc_voor_kandidaat()
        resultaat = self._resultaat(doc)
        voor = deepcopy(resultaat)
        kandidaat = _definition(
            metadata={
                "ess05_buren": bevestig_buur(
                    [], [REPOSITORYBUUR], "repository:9", actor="d", at=AT
                )
            }
        )
        # Zonder besluit: het oorspronkelijke oordeel (open) blijft staan.
        uitkomst = ess05_uitkomst_van_definition(
            _definition(), [REPOSITORYBUUR], BINDING, assessment=doc
        )
        assert uitkomst["status"] == "review_required"
        assert uitkomst["review"]["assessment"]["applied"] is True

        herbonden = herbind_ess05_in_validatieresultaat(
            resultaat, kandidaat, binding=BINDING
        )
        assert resultaat == voor
        assert herbonden["rule_statuses"]["ESS-05"] == "review_required"
        detail = herbonden["rule_results"]["ESS-05"]
        assert detail["review"]["assessment"]["historical"] is True
        assert "buurbevestiging" in detail["review"]["assessment"]["reason"]

    def test_nieuwe_toetsing_met_de_bevestigde_buur_voldoet(self):
        kandidaat = _definition(
            metadata={
                "ess05_buren": bevestig_buur(
                    [], [REPOSITORYBUUR], "repository:9", actor="d", at=AT
                )
            }
        )
        buren, _ = ess05_actieve_buren_van(kandidaat, [REPOSITORYBUUR])
        from services.definition_edit_service import ess03_intentie_van_definition

        doc = bouw_ess05_beoordeling(
            BEGRIP,
            TEKST,
            CONTEXT,
            [],
            buren=[b.als_dict() for b in buren],
            intentie=ess03_intentie_van_definition(kandidaat),
        )
        herbonden = herbind_ess05_in_validatieresultaat(
            self._resultaat(doc), kandidaat, binding=BINDING
        )
        assert herbonden["rule_statuses"]["ESS-05"] == "pass"
        assert "ESS-05" in herbonden["passed_rules"]
        assert herbonden["review_required"] == []
        assert herbonden["evaluation_coverage"] == {"review_required": 0, "passed": 1}

    def test_afwijzing_maakt_de_beoordeling_historisch(self):
        doc = _doc_voor_kandidaat()
        kandidaat = _definition(
            metadata={
                "ess05_buren": wijs_buur_af(
                    [], [REPOSITORYBUUR], "repository:9", actor="d", at=AT, grond="g"
                )
            }
        )
        herbonden = herbind_ess05_in_validatieresultaat(
            self._resultaat(doc), kandidaat, binding=BINDING
        )
        assert herbonden["rule_statuses"]["ESS-05"] == "review_required"
        detail = herbonden["rule_results"]["ESS-05"]
        assert detail["review"]["assessment"]["historical"] is True


class TestVolledigeBindingBijOpslaan:
    """ADR-003: de ESS-05-eigen binding (tien velden) en een geldige
    semantische verificatie zijn voorwaarde voor vastleggen als actueel."""

    def _afwijzing(self, doc, binding=BINDING):
        return bindingsafwijzing_ess05(
            doc, _definition(), [REPOSITORYBUUR], binding=binding
        )

    def test_bindende_beoordeling_heeft_geen_afwijzing(self):
        assert self._afwijzing(_doc_voor_kandidaat()) is None

    @pytest.mark.parametrize(
        ("veld", "waarde"),
        [
            ("verification_model", "ander-verifiermodel"),
            ("verification_provider", "andere-provider"),
            ("verification_prompt_version", "ess05-verify/99"),
            ("schema_version", "ess05-concept/99"),
            ("verification_schema_version", "ess05-verification/99"),
            ("renderer_version", "ess05-render/99"),
        ],
    )
    def test_elk_ess05_bindingsveld_telt(self, veld, waarde):
        reden = self._afwijzing(
            _doc_voor_kandidaat(), replace(BINDING, **{veld: waarde})
        )
        assert reden is not None
        assert veld in reden
        assert waarde in reden

    def test_zonder_verificatie_wordt_niets_vastgelegd(self):
        doc = _doc_voor_kandidaat()
        doc["verification"] = None
        reden = self._afwijzing(doc)
        assert reden is not None
        assert "verificatie" in reden

    def test_afgekeurde_verificatie_wordt_niet_vastgelegd(self):
        doc = _doc_voor_kandidaat()
        doc["verification"]["checks"][0]["outcome"] = "unsupported"
        reden = self._afwijzing(doc)
        assert reden is not None
        assert "verificatie" in reden

    def test_legacy_contractversie_wordt_niet_vastgelegd(self):
        doc = _doc_voor_kandidaat()
        doc["contract_version"] = "ess05/1"
        reden = self._afwijzing(doc)
        assert reden is not None
        assert "ess05/1" in reden

    def test_ander_verifiermodel_wordt_niet_opgeslagen(self, tmp_path):
        service, did = _service(tmp_path)
        doc = bouw_ess05_beoordeling(
            BEGRIP,
            TEKST,
            CONTEXT,
            [],
            buren=[REPOSITORYBUUR],
            intentie=_intentie_van(service, did),
        )
        result = service.save_definition(
            did,
            _updates(service, did),
            validate=False,
            ess05_assessment=doc,
            ess05_actieve_buren=[REPOSITORYBUUR],
            ess05_binding=replace(BINDING, verification_model="ander-verifiermodel"),
        )
        assert result["ess05_assessment_persisted"] is False
        assert "ander-verifiermodel" in result["ess05_assessment_reason"]
        assert "ess05_assessment" not in service.repository.get(did).metadata
