"""DEF-768 / ADR-003 — gesloten ESS-05-bewijscontract `/2` (`domain.ess05.bewijs`).

Toetst zonder model, netwerk of DB wat vaste code kan bewaken: een gesloten
conceptoordeel (kenmerken, bewijsplaatsen, claims, buren, voorstellen, vraag),
exacte bewijsplaatsen tegen de gebonden materiaaltekst, referentiële
integriteit, de afleiding van `lacks_differentia` uit de kenmerkenlijst en de
volledige, unieke dekking van de semantische verificatie.

Grens (ADR-003): een geslaagde controle hier bewijst geen semantische
juistheid. Een citaat dat bestaat kan een claim alsnog niet dragen; dat is aan
de afzonderlijke verifier, niet aan deze code.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy

import pytest

from domain.ess05.bewijs import (
    CONCEPTSCHEMA,
    RENDERERVERSIE,
    VERIFICATIESCHEMA,
    concepthash,
    toets_verificatie,
    valideer_concept,
    verplichte_controles,
)

pytestmark = [pytest.mark.unit]

KERN = "persoon met een actuele lening bij de instelling"
BUURDEF = "persoon met een arbeidsovereenkomst met de instelling"
BRON = "Een lener is een persoon die geld leent van de instelling."
BUUR = "gebruiker:abc"
MATERIAAL = {
    "definition": KERN,
    "source:s1": BRON,
    f"neighbour:{BUUR}": BUURDEF,
}
BUURDEFINITIES = {BUUR: BUURDEF}


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _ev(id_: str, locatie: str, citaat: str, materiaal=MATERIAAL) -> dict:
    start = materiaal[locatie].index(citaat)
    return {
        "id": id_,
        "material_id": locatie,
        "material_sha256": _sha(materiaal[locatie]),
        "start": start,
        "end": start + len(citaat),
        "quote": citaat,
    }


def _claim(id_, rol, tekst, evidence=(), premises=()):
    return {
        "id": id_,
        "role": rol,
        "text": tekst,
        "evidence": list(evidence),
        "premises": list(premises),
    }


def _buur(distinction="distinguished", feature="E1", reasons=("C3",), missing=None):
    return {
        "neighbour_id": BUUR,
        "distinction": distinction,
        "feature_evidence": feature,
        "reason_claims": list(reasons),
        "missing_feature_claim": missing,
        "uncertainty_claim": None,
    }


def _concept() -> dict:
    """Een geldig concept: kenmerk 'actuele lening' onderscheidt van de buur."""
    return {
        "schema_version": CONCEPTSCHEMA,
        "genus_evidence": "E0",
        "core_features": [{"id": "F1", "evidence": "E1"}],
        "evidence": [
            _ev("E0", "definition", "persoon"),
            _ev("E1", "definition", "actuele lening"),
            _ev("E2", f"neighbour:{BUUR}", "arbeidsovereenkomst"),
        ],
        "claims": [
            _claim("C1", "material", "De kern noemt een actuele lening.", ["E1"]),
            _claim(
                "C2", "material", "De buur berust op een arbeidsovereenkomst.", ["E2"]
            ),
            _claim(
                "C3",
                "inference",
                "Een lening is een ander criterium dan een arbeidsovereenkomst.",
                premises=["C1", "C2"],
            ),
        ],
        "reason_claims": ["C3"],
        "neighbours": [_buur()],
        "proposals": [],
        "question": None,
    }


def _valideer(ruw, materiaal=MATERIAAL, buren=BUURDEFINITIES):
    return valideer_concept(ruw, materiaal, buren)


def _structuurfout(ruw) -> str:
    concept, fouten = _valideer(ruw)
    assert concept is None
    assert fouten and fouten[0]["reason"] == "structuurfout", fouten
    return fouten[0]["detail"]


def _bewijsfout(ruw) -> str:
    concept, fouten = _valideer(ruw)
    assert concept is None
    assert fouten and fouten[0]["reason"] != "structuurfout", fouten
    return fouten[0]["reason"]


def _verificatie(concept, **overschrijf) -> dict:
    uitkomsten = overschrijf.pop("uitkomsten", {})
    return {
        "schema_version": VERIFICATIESCHEMA,
        "candidate_hash": overschrijf.pop("candidate_hash", concept.hash),
        "checks": [
            {
                "item": item,
                "outcome": uitkomsten.get(item, "supported"),
                "finding": f"Gecontroleerd tegen het materiaal: {item}.",
            }
            for item in verplichte_controles(concept)
        ],
    }


# --- gesloten concept ----------------------------------------------------------------


class TestGeslotenConcept:
    def test_geldig_concept_wordt_aanvaard_met_afgeleide_indicator(self):
        concept, fouten = _valideer(_concept())
        assert fouten == []
        assert concept is not None
        assert concept.lacks_differentia is False

    def test_versies_zijn_afzonderlijk_benoemd(self):
        assert CONCEPTSCHEMA == "ess05-concept/1"
        assert VERIFICATIESCHEMA == "ess05-verification/1"
        assert RENDERERVERSIE == "ess05-render/1"

    def test_onbekende_of_ontbrekende_sleutel_is_structuurfout(self):
        extra = _concept() | {"lacks_differentia": False}
        assert "lacks_differentia" in _structuurfout(extra)
        ontbrekend = _concept()
        del ontbrekend["claims"]
        _structuurfout(ontbrekend)

    def test_geneste_extra_sleutel_is_structuurfout(self):
        ruw = _concept()
        ruw["claims"][0]["confidence"] = 0.9
        _structuurfout(ruw)
        ruw = _concept()
        ruw["neighbours"][0]["reason"] = "vrije paragraaf"
        _structuurfout(ruw)

    def test_verkeerde_schemaversie_is_structuurfout(self):
        _structuurfout(_concept() | {"schema_version": "ess05-concept/0"})

    def test_model_levert_geen_eigen_indicator_meer(self):
        ruw = _concept() | {"lacks_differentia": True}
        _structuurfout(ruw)

    def test_positie_als_boolean_of_negatief_is_structuurfout(self):
        ruw = _concept()
        ruw["evidence"][1]["start"] = True
        _structuurfout(ruw)


# --- bewijsplaatsen --------------------------------------------------------------------


class TestBewijsplaatsen:
    def test_niet_bestaand_citaat_wordt_afgewezen(self):
        ruw = _concept()
        ruw["evidence"][1]["quote"] = "tijdelijke lening"
        assert _bewijsfout(ruw) == "citaat wijkt af van de bewijsplaats"

    def test_bestaand_citaat_op_verkeerde_positie_wordt_afgewezen(self):
        ruw = _concept()
        ruw["evidence"][1]["start"] += 1
        ruw["evidence"][1]["end"] += 1
        assert _bewijsfout(ruw) == "citaat wijkt af van de bewijsplaats"

    def test_positie_buiten_bereik_wordt_afgewezen(self):
        ruw = _concept()
        ruw["evidence"][1]["end"] = len(KERN) + 5
        assert _bewijsfout(ruw) == "bewijsplaats buiten bereik"

    def test_onbekend_materiaal_wordt_afgewezen(self):
        ruw = _concept()
        ruw["evidence"][2]["material_id"] = "source:verzonnen"
        assert _bewijsfout(ruw) == "onbekend materiaal"

    def test_afwijkende_materiaalhash_wordt_afgewezen(self):
        ruw = _concept()
        ruw["evidence"][1]["material_sha256"] = "0" * 64
        assert _bewijsfout(ruw) == "materiaalhash wijkt af"

    def test_posities_gelden_voor_de_exacte_gebonden_tekst(self):
        """Geen normalisatie: dubbele spatie in het materiaal telt mee."""
        materiaal = dict(MATERIAAL, definition="persoon met een  actuele lening")
        ruw = _concept()
        ruw["evidence"] = [
            _ev("E0", "definition", "persoon", materiaal),
            _ev("E1", "definition", "actuele lening", materiaal),
            _ev("E2", f"neighbour:{BUUR}", "arbeidsovereenkomst", materiaal),
        ]
        assert _valideer(ruw, materiaal)[0] is not None
        ruw["evidence"][1]["quote"] = "een actuele lening"
        ruw["evidence"][1]["start"] = materiaal["definition"].index("een  actuele")
        ruw["evidence"][1]["end"] = ruw["evidence"][1]["start"] + len(
            "een actuele lening"
        )
        assert _valideer(ruw, materiaal)[0] is None

    def test_kern_gelijk_aan_buurdefinitie_is_nooit_onderscheiden(self):
        materiaal = dict(MATERIAAL, **{f"neighbour:{BUUR}": KERN})
        ruw = _concept()
        ruw["evidence"][2] = _ev("E2", f"neighbour:{BUUR}", "actuele lening", materiaal)
        concept, fouten = _valideer(ruw, materiaal, {BUUR: KERN})
        assert concept is None
        assert fouten[0]["reason"] == "kern gelijk aan de buurdefinitie"


# --- referenties en dekking ------------------------------------------------------------


class TestReferenties:
    def test_dubbele_ids_zijn_structuurfout(self):
        ruw = _concept()
        ruw["claims"][1]["id"] = "C1"
        _structuurfout(ruw)
        ruw = _concept()
        ruw["claims"][0]["id"] = "E1"
        _structuurfout(ruw)

    def test_onbekende_verwijzing_is_structuurfout(self):
        ruw = _concept()
        ruw["claims"][0]["evidence"] = ["E9"]
        _structuurfout(ruw)
        ruw = _concept()
        ruw["reason_claims"] = ["C9"]
        _structuurfout(ruw)

    def test_kernkenmerk_moet_uit_de_definitiekern_komen(self):
        ruw = _concept()
        ruw["core_features"] = [{"id": "F1", "evidence": "E2"}]
        _structuurfout(ruw)

    def test_onderscheidend_fragment_moet_uit_de_kern_komen(self):
        ruw = _concept()
        ruw["neighbours"][0]["feature_evidence"] = "E2"
        _structuurfout(ruw)

    def test_ongebruikte_claim_of_bewijsplaats_is_structuurfout(self):
        ruw = _concept()
        ruw["claims"].append(_claim("C4", "material", "Losse zin.", ["E1"]))
        _structuurfout(ruw)
        ruw = _concept()
        ruw["evidence"].append(_ev("E3", "source:s1", "geld leent"))
        _structuurfout(ruw)

    def test_elke_verzonden_buur_precies_eens(self):
        ruw = _concept()
        ruw["neighbours"] = []
        _structuurfout(ruw)
        ruw = _concept()
        ruw["neighbours"].append(_buur())
        _structuurfout(ruw)

    def test_algemene_reden_is_verplicht(self):
        ruw = _concept()
        ruw["reason_claims"] = []
        ruw["neighbours"][0]["reason_claims"] = ["C3"]
        _structuurfout(ruw)


class TestClaimrollen:
    def test_materiaalclaim_vereist_bewijs(self):
        ruw = _concept()
        ruw["claims"][0]["evidence"] = []
        _structuurfout(ruw)

    def test_gevolgtrekking_vereist_eerdere_premissen(self):
        ruw = _concept()
        ruw["claims"][2]["premises"] = []
        _structuurfout(ruw)
        ruw = _concept()
        ruw["claims"][0] = _claim("C1", "inference", "Kring.", premises=["C3"])
        _structuurfout(ruw)

    def test_afwezigheidsclaim_zonder_verzonnen_citaat_is_geldig(self):
        ruw = _concept()
        ruw["claims"].append(
            _claim(
                "C4",
                "absence_in_supplied_material",
                "Het materiaal zegt niet of een werknemer ook kan lenen.",
            )
        )
        ruw["neighbours"][0]["uncertainty_claim"] = "C4"
        concept, fouten = _valideer(ruw)
        assert fouten == []
        assert concept is not None

    def test_afwezigheidsclaim_met_citaat_is_structuurfout(self):
        ruw = _concept()
        ruw["claims"].append(
            _claim("C4", "absence_in_supplied_material", "Niets.", ["E1"])
        )
        ruw["neighbours"][0]["uncertainty_claim"] = "C4"
        _structuurfout(ruw)

    def test_onbekende_rol_is_structuurfout(self):
        ruw = _concept()
        ruw["claims"][0]["role"] = "quote"
        _structuurfout(ruw)


class TestBuurlabels:
    def test_not_distinguished_vereist_ontbrekend_kenmerk_en_geen_fragment(self):
        ruw = _concept()
        ruw["neighbours"][0] = _buur("not_distinguished", feature=None)
        _structuurfout(ruw)
        ruw["neighbours"][0] = _buur("not_distinguished", feature="E1", missing="C1")
        _structuurfout(ruw)
        ruw["neighbours"][0] = _buur("not_distinguished", feature=None, missing="C1")
        assert _valideer(ruw)[0] is not None

    def test_unclear_heeft_geen_fragment(self):
        ruw = _concept()
        ruw["neighbours"][0] = _buur("unclear", feature="E1")
        _structuurfout(ruw)

    def test_distinguished_vereist_fragment(self):
        ruw = _concept()
        ruw["neighbours"][0] = _buur("distinguished", feature=None)
        _structuurfout(ruw)

    def test_buur_zonder_beschrijving_kan_alleen_unclear(self):
        materiaal = {
            k: v for k, v in MATERIAAL.items() if not k.startswith("neighbour:")
        }
        materiaal[f"neighbour:{BUUR}"] = ""
        ruw = _concept()
        ruw["evidence"] = ruw["evidence"][:2]
        ruw["claims"] = ruw["claims"][:1]
        ruw["reason_claims"] = ["C1"]
        ruw["neighbours"][0] = _buur("distinguished", reasons=("C1",))
        concept, fouten = valideer_concept(ruw, materiaal, {BUUR: None})
        assert concept is None
        assert fouten[0]["reason"] == "structuurfout"
        ruw["neighbours"][0] = _buur("unclear", feature=None, reasons=("C1",))
        assert valideer_concept(ruw, materiaal, {BUUR: None})[0] is not None


class TestAfleidingIndicator:
    def test_lege_kenmerkenlijst_geeft_lacks_differentia(self):
        ruw = _concept()
        ruw["core_features"] = []
        ruw["neighbours"][0] = _buur("not_distinguished", feature=None, missing="C1")
        concept, fouten = _valideer(ruw)
        assert fouten == []
        assert concept.lacks_differentia is True

    def test_lege_kenmerkenlijst_met_onderscheiden_buur_is_tegenstrijdig(self):
        ruw = _concept()
        ruw["core_features"] = []
        _structuurfout(ruw)

    def test_kernkenmerk_is_geen_verplicht_volledige_lijst(self):
        """Eén echt kenmerk volstaat voor `false`; geen opsommingsplicht."""
        concept, _ = _valideer(_concept())
        assert len(concept.data["core_features"]) == 1
        assert concept.lacks_differentia is False


class TestVoorstellenEnVraag:
    def _met_voorstel(self, bron="E3"):
        ruw = _concept()
        ruw["evidence"].append(_ev("E3", "source:s1", "Een lener is een persoon"))
        ruw["claims"].append(
            _claim("C4", "material", "De bron noemt de lener.", ["E3"])
        )
        ruw["proposals"] = [
            {
                "id": "P1",
                "term": "debiteur",
                "source_evidence": bron,
                "reason_claims": ["C4"],
            }
        ]
        return ruw

    def test_voorstel_met_bronbewijs_is_geldig(self):
        assert _valideer(self._met_voorstel())[0] is not None

    def test_bronherkomst_eist_bronmateriaal(self):
        _structuurfout(self._met_voorstel(bron="E1"))

    def test_voorstel_vereist_redenclaims(self):
        ruw = self._met_voorstel(bron=None)
        ruw["proposals"][0]["reason_claims"] = []
        _structuurfout(ruw)

    def test_vraag_is_precies_een_gerichte_vraag(self):
        ruw = _concept()
        ruw["question"] = {"text": "Is dit zo? En dat?", "claims": []}
        _structuurfout(ruw)
        ruw["question"] = {
            "text": "Moet ook de werknemer worden uitgesloten?",
            "claims": ["C2"],
        }
        assert _valideer(ruw)[0] is not None


# --- kandidaat-hash --------------------------------------------------------------------


class TestKandidaathash:
    def test_hash_onafhankelijk_van_sleutelvolgorde(self):
        ruw = _concept()
        omgekeerd = dict(reversed(list(deepcopy(ruw).items())))
        assert concepthash(ruw) == concepthash(omgekeerd)

    def test_hash_verandert_bij_elke_inhoudswijziging(self):
        ruw = _concept()
        anders = deepcopy(ruw)
        anders["claims"][2]["text"] += " Extra."
        assert concepthash(ruw) != concepthash(anders)

    def test_concept_draagt_zijn_hash(self):
        ruw = _concept()
        concept, _ = _valideer(ruw)
        assert concept.hash == concepthash(ruw)


# --- verificatiedekking ----------------------------------------------------------------


class TestVerificatie:
    def _concept(self, ruw=None):
        concept, fouten = _valideer(ruw or _concept())
        assert concept is not None, fouten
        return concept

    def test_verplichte_controles_dekken_alle_zichtbare_onderdelen(self):
        ruw = TestVoorstellenEnVraag()._met_voorstel()
        ruw["question"] = {
            "text": "Moet de werknemer worden uitgesloten?",
            "claims": [],
        }
        items = verplichte_controles(self._concept(ruw))
        assert set(items) == {
            "core_features",
            "feature:F1",
            "claim:C1",
            "claim:C2",
            "claim:C3",
            "claim:C4",
            f"neighbour:{BUUR}",
            "proposal:P1",
            "question",
            "completeness",
        }

    def test_lege_kenmerkenlijst_heeft_eigen_verplichte_controle(self):
        ruw = _concept()
        ruw["core_features"] = []
        ruw["neighbours"][0] = _buur("not_distinguished", feature=None, missing="C1")
        items = verplichte_controles(self._concept(ruw))
        assert "core_features" in items
        assert not any(i.startswith("feature:") for i in items)

    def test_volledig_ondersteund_geeft_vrijgave(self):
        concept = self._concept()
        uitkomst = toets_verificatie(_verificatie(concept), concept)
        assert uitkomst.goedgekeurd is True
        assert uitkomst.soort is None

    def test_een_unsupported_weigert_als_semantische_verificatiefout(self):
        concept = self._concept()
        uitkomst = toets_verificatie(
            _verificatie(concept, uitkomsten={"claim:C3": "unsupported"}), concept
        )
        assert uitkomst.goedgekeurd is False
        assert uitkomst.soort == "semantic_verification_failed"
        assert [b["item"] for b in uitkomst.bevindingen] == ["claim:C3"]

    def test_undetermined_is_geen_vrijgave(self):
        concept = self._concept()
        uitkomst = toets_verificatie(
            _verificatie(concept, uitkomsten={"completeness": "undetermined"}),
            concept,
        )
        assert uitkomst.goedgekeurd is False
        assert uitkomst.soort == "semantic_verification_failed"

    def test_verkeerde_kandidaathash_is_bindingsfout(self):
        concept = self._concept()
        uitkomst = toets_verificatie(
            _verificatie(concept, candidate_hash="0" * 64), concept
        )
        assert uitkomst.goedgekeurd is False
        assert uitkomst.soort == "candidate_hash_mismatch"

    @pytest.mark.parametrize("wijziging", ["ontbreekt", "dubbel", "onbekend"])
    def test_dekking_moet_volledig_en_uniek_zijn(self, wijziging):
        concept = self._concept()
        ruw = _verificatie(concept)
        if wijziging == "ontbreekt":
            ruw["checks"].pop()
        elif wijziging == "dubbel":
            ruw["checks"].append(deepcopy(ruw["checks"][0]))
        else:
            ruw["checks"].append(
                {"item": "claim:C9", "outcome": "supported", "finding": "x"}
            )
        uitkomst = toets_verificatie(ruw, concept)
        assert uitkomst.goedgekeurd is False
        assert uitkomst.soort == "malformed_response"

    def test_losse_goedkeuring_vervangt_geen_controles(self):
        concept = self._concept()
        ruw = _verificatie(concept) | {"approved": True}
        ruw["checks"] = []
        uitkomst = toets_verificatie(ruw, concept)
        assert uitkomst.goedgekeurd is False
        assert uitkomst.soort == "malformed_response"

    def test_bevinding_is_verplicht_en_uitkomst_gesloten(self):
        concept = self._concept()
        ruw = _verificatie(concept)
        ruw["checks"][0]["finding"] = ""
        assert toets_verificatie(ruw, concept).soort == "malformed_response"
        ruw = _verificatie(concept)
        ruw["checks"][0]["outcome"] = "approved"
        assert toets_verificatie(ruw, concept).soort == "malformed_response"

    def test_geen_verificatie_is_geen_vrijgave(self):
        concept = self._concept()
        assert toets_verificatie(None, concept).goedgekeurd is False


# --- vaste weergave --------------------------------------------------------------------


class TestWeergave:
    def test_materiaalclaim_toont_het_gecontroleerde_citaat(self):
        concept, _ = _valideer(_concept())
        tekst = concept.claimtekst(["C1"])
        assert "De kern noemt een actuele lening." in tekst
        assert "“actuele lening”" in tekst

    def test_gevolgtrekking_wordt_niet_als_bronuitspraak_getoond(self):
        concept, _ = _valideer(_concept())
        assert concept.claimtekst(["C3"]).startswith("Gevolgtrekking:")

    def test_afwezigheid_krijgt_geen_verzonnen_citaat(self):
        ruw = _concept()
        ruw["claims"].append(
            _claim(
                "C4",
                "absence_in_supplied_material",
                "Over lenen door werknemers zegt het materiaal niets.",
            )
        )
        ruw["neighbours"][0]["uncertainty_claim"] = "C4"
        concept, _ = _valideer(ruw)
        tekst = concept.claimtekst(["C4"])
        assert tekst.startswith("Niet in het aangeleverde materiaal:")
        assert "“" not in tekst
