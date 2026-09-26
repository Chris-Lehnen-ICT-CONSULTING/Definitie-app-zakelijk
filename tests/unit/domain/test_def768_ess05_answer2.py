"""DEF-768 — `ess05-answer/2`: genest, citaat-eerst antwoord → `ess05-concept/1`.

Voorstel `logs/def768/ronde11-c10-diagnose-voorstel-v2.md` (goedgekeurd). Het
model schrijft elke claim inline op haar gebruiksplaats: bij material eerst de
citaten, dan de tekst; bij inference eerst de geneste premissen, dan de tekst.
Kern-, genus- en kenmerkcitaten staan inline. De app leidt daar deterministisch
het ongewijzigde concept/1 uit af: ID's toekennen, identieke citaten en claims
samenvoegen, posities alleen bij precies één letterlijke treffer.

Deze tests bewijzen de structurele garantie (geen losse of ongebruikte claim,
geen ID-indirectie, fail-closed) en de versiebinding. Ze bewijzen NIET dat een
claimtekst binnen haar citaten of premissen blijft: dat blijft modelrisico en
ligt bij de verifier.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from domain import modeluitvoer
from domain.ess05 import bewijs

pytestmark = [pytest.mark.unit]

ANTWOORD2 = "ess05-answer/2"
ANTWOORD1 = "ess05-answer/1"

KERN = "transportgang die via baan Neral naar de oorspronkelijke laadplaats terugkeert"
BRON = "Neral en Dovar zijn banen. Een lusafvoer eindigt elders & keert niet terug."
BUUR = "transportgang die elders eindigt"
MATERIAAL = {"definition": KERN, "source:b1": BRON, "neighbour:n1": BUUR}
BUREN = {"n1": BUUR}


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def q(locatie: str, citaat: str) -> dict:
    return {
        "material_id": locatie,
        "material_sha256": _sha(MATERIAAL[locatie]),
        "quote": citaat,
    }


def mat(tekst: str, *citaten: dict) -> dict:
    return {"role": "material", "quotes": list(citaten), "text": tekst}


def inf(tekst: str, *premissen: dict) -> dict:
    return {"role": "inference", "premises": list(premissen), "text": tekst}


def afw(tekst: str) -> dict:
    return {"role": "absence_in_supplied_material", "text": tekst}


NERAL = q("definition", "via baan Neral")
TERUG = q("definition", "naar de oorspronkelijke laadplaats terugkeert")
ELDERS = q("neighbour:n1", "elders eindigt")
KERNCLAIM = mat("De kern noemt de terugkeer naar de laadplaats.", TERUG)
BUURCLAIM = mat("De buur eindigt elders.", ELDERS)


def antwoord(**anders) -> dict:
    basis = {
        "schema_version": ANTWOORD2,
        "genus_quote": q("definition", "transportgang"),
        "core_features": [NERAL, TERUG],
        "reason": [KERNCLAIM],
        "neighbours": [
            {
                "neighbour_id": "n1",
                "distinction": "distinguished",
                "feature_quote": TERUG,
                "reason": [
                    BUURCLAIM,
                    inf("De kern sluit de buur daarom uit.", KERNCLAIM, BUURCLAIM),
                ],
                "missing_feature": None,
                "uncertainty": None,
            }
        ],
        "proposals": [],
        "question": None,
    }
    basis.update(anders)
    return copy.deepcopy(basis)


def leid_af(ruw, schema=ANTWOORD2, materiaal=MATERIAAL, buren=BUREN):
    return bewijs.valideer_antwoord(ruw, materiaal, buren, schema=schema)


def structuurfout(ruw, **kw) -> str:
    concept, fouten = leid_af(ruw, **kw)
    assert concept is None
    assert fouten[0]["reason"] == "structuurfout", fouten
    return fouten[0]["detail"]


class TestVersies:
    def test_actueel_schema_is_answer2_en_answer1_blijft_expliciet(self):
        assert bewijs.ANTWOORDSCHEMA == ANTWOORD2
        assert bewijs.ANTWOORDSCHEMA_1 == ANTWOORD1
        assert bewijs.CONCEPTSCHEMA == "ess05-concept/1"
        assert bewijs.VERIFICATIESCHEMA == "ess05-verification/1"

    def test_standaard_is_answer2(self):
        concept, fouten = bewijs.valideer_antwoord(antwoord(), MATERIAAL, BUREN)
        assert fouten == [] and concept is not None

    def test_answer1_antwoord_wordt_live_geweigerd(self):
        """Een oud (plat) antwoord is onder answer/2 een structuurfout, geen herinterpretatie."""
        concept, _ = leid_af(antwoord())
        oud = concept.als_dict()
        oud["schema_version"] = ANTWOORD1
        oud["evidence"] = [
            {k: e[k] for k in ("id", "material_id", "material_sha256", "quote")}
            for e in oud["evidence"]
        ]
        # Onder de expliciete historische versie is het geldig ...
        historisch, fouten = leid_af(oud, schema=ANTWOORD1)
        assert fouten == [] and historisch.data == concept.data
        # ... maar de actuele binding aanvaardt het niet, ook niet met een
        # vervalst versielabel.
        assert "schema_version moet 'ess05-answer/2' zijn" in structuurfout(oud)
        oud["schema_version"] = ANTWOORD2
        assert "antwoord heeft niet exact de afgesproken velden" in structuurfout(oud)

    def test_answer2_antwoord_onder_answer1_geweigerd(self):
        assert structuurfout(antwoord(), schema=ANTWOORD1)

    def test_onbekende_schemaversie_is_structuurfout(self):
        assert "onbekend antwoordschema" in structuurfout(antwoord(), schema="x/9")
        ander = antwoord(schema_version="ess05-answer/3")
        assert "schema_version moet 'ess05-answer/2' zijn" in structuurfout(ander)


class TestAfleiding:
    def test_concept1_met_ids_in_gebruiksvolgorde_en_exacte_posities(self):
        concept, fouten = leid_af(antwoord())
        assert fouten == []
        data = concept.als_dict()
        assert data["schema_version"] == "ess05-concept/1"
        # Citaten in volgorde van eerste gebruik; identieke citaten één keer.
        assert [(e["id"], e["quote"]) for e in data["evidence"]] == [
            ("E1", "transportgang"),
            ("E2", "via baan Neral"),
            ("E3", "naar de oorspronkelijke laadplaats terugkeert"),
            ("E4", "elders eindigt"),
        ]
        for e in data["evidence"]:
            tekst = MATERIAAL[e["material_id"]]
            assert tekst.count(e["quote"]) == 1
            assert tekst[e["start"] : e["end"]] == e["quote"]
            assert e["material_sha256"] == _sha(tekst)
        assert data["genus_evidence"] == "E1"
        assert data["core_features"] == [
            {"id": "F1", "evidence": "E2"},
            {"id": "F2", "evidence": "E3"},
        ]
        assert data["claims"] == [
            {
                "id": "C1",
                "role": "material",
                "text": KERNCLAIM["text"],
                "evidence": ["E3"],
                "premises": [],
            },
            {
                "id": "C2",
                "role": "material",
                "text": BUURCLAIM["text"],
                "evidence": ["E4"],
                "premises": [],
            },
            {
                "id": "C3",
                "role": "inference",
                "text": "De kern sluit de buur daarom uit.",
                "evidence": [],
                "premises": ["C1", "C2"],
            },
        ]
        assert data["reason_claims"] == ["C1"]
        assert data["neighbours"] == [
            {
                "neighbour_id": "n1",
                "distinction": "distinguished",
                "feature_evidence": "E3",
                "reason_claims": ["C2", "C3"],
                "missing_feature_claim": None,
                "uncertainty_claim": None,
            }
        ]
        # Het afgeleide concept doorstaat zelfstandig de conceptcontrole.
        opnieuw, fouten = bewijs.valideer_concept(data, MATERIAAL, BUREN)
        assert fouten == [] and opnieuw.hash == concept.hash

    def test_deterministisch_en_invoer_ongewijzigd(self):
        ruw = antwoord()
        kopie = copy.deepcopy(ruw)
        a, _ = leid_af(ruw)
        b, _ = leid_af(json.loads(json.dumps(ruw)))
        assert a.hash == b.hash and a.data == b.data
        assert ruw == kopie

    def test_voorstel_vraag_ontbrekend_en_onzeker(self):
        bronclaim = mat("De bron noemt de lusafvoer.", q("source:b1", "Een lusafvoer"))
        ruw = antwoord(
            neighbours=[
                {
                    "neighbour_id": "n1",
                    "distinction": "unclear",
                    "feature_quote": None,
                    "reason": [BUURCLAIM],
                    "missing_feature": None,
                    "uncertainty": afw("Het materiaal zegt niet waar hij begint."),
                }
            ],
            proposals=[
                {
                    "term": "lusafvoer",
                    "source_quote": q("source:b1", "Een lusafvoer"),
                    "reason": [bronclaim],
                }
            ],
            question={"text": "Waar begint de buur?", "claims": [BUURCLAIM]},
        )
        concept, fouten = leid_af(ruw)
        assert fouten == []
        data = concept.als_dict()
        per_tekst = {c["text"]: c["id"] for c in data["claims"]}
        buur = data["neighbours"][0]
        assert (
            buur["uncertainty_claim"]
            == per_tekst["Het materiaal zegt niet waar hij begint."]
        )
        assert data["proposals"] == [
            {
                "id": "P1",
                "term": "lusafvoer",
                "source_evidence": next(
                    e["id"] for e in data["evidence"] if e["quote"] == "Een lusafvoer"
                ),
                "reason_claims": [per_tekst["De bron noemt de lusafvoer."]],
            }
        ]
        # De vraagclaim is dezelfde claim als de buurreden: samengevoegd.
        assert data["question"] == {
            "text": "Waar begint de buur?",
            "claims": [per_tekst[BUURCLAIM["text"]]],
        }

    def test_xml_escape_in_citaat_en_term_teruggezet(self):
        bronclaim = mat(
            "De bron noemt elders en terugkeer.",
            q("source:b1", "elders &amp; keert"),
        )
        ruw = antwoord(
            proposals=[
                {"term": "lus&amp;afvoer", "source_quote": None, "reason": [bronclaim]}
            ]
        )
        concept, fouten = leid_af(ruw)
        assert fouten == []
        citaten = [e["quote"] for e in concept.data["evidence"]]
        assert "elders & keert" in citaten
        assert concept.data["proposals"][0]["term"] == "lus&afvoer"


class TestDedup:
    def test_identieke_claim_op_meerdere_plaatsen_is_een_claim(self):
        concept, _ = leid_af(antwoord())
        teksten = [c["text"] for c in concept.data["claims"]]
        assert teksten.count(KERNCLAIM["text"]) == 1
        assert teksten.count(BUURCLAIM["text"]) == 1
        controles = bewijs.verplichte_controles(concept)
        assert [c for c in controles if c.startswith("claim:")] == [
            "claim:C1",
            "claim:C2",
            "claim:C3",
        ]

    def test_zelfde_tekst_ander_citaat_blijft_twee_claims(self):
        tweede = mat(KERNCLAIM["text"], NERAL)
        ruw = antwoord(reason=[KERNCLAIM, tweede])
        concept, fouten = leid_af(ruw)
        assert fouten == []
        claims = [c for c in concept.data["claims"] if c["text"] == KERNCLAIM["text"]]
        assert [c["evidence"] for c in claims] == [["E3"], ["E2"]]

    def test_zelfde_citaat_andere_rol_of_tekst_blijft_apart(self):
        anders = mat("Een andere uitspraak over de terugkeer.", TERUG)
        concept, fouten = leid_af(antwoord(reason=[KERNCLAIM, anders]))
        assert fouten == []
        assert len(concept.data["claims"]) == 4
        # wel één bewijsplaats voor het gedeelde citaat
        assert [e["quote"] for e in concept.data["evidence"]].count(TERUG["quote"]) == 1

    def test_gevolgtrekking_met_andere_premissen_blijft_apart(self):
        a = inf("Samen volgt X.", KERNCLAIM, BUURCLAIM)
        b = inf("Samen volgt X.", BUURCLAIM, KERNCLAIM)
        concept, fouten = leid_af(antwoord(reason=[a, b]))
        assert fouten == []
        gevolg = [c for c in concept.data["claims"] if c["text"] == "Samen volgt X."]
        assert [c["premises"] for c in gevolg] == [["C1", "C2"], ["C2", "C1"]]

    def test_premisse_die_later_ook_reden_is_blijft_eerder(self):
        gevolg = inf("Dus X.", BUURCLAIM)
        concept, fouten = leid_af(antwoord(reason=[gevolg, BUURCLAIM]))
        assert fouten == []
        ids = {c["text"]: c["id"] for c in concept.data["claims"]}
        assert concept.data["reason_claims"] == [ids["Dus X."], ids[BUURCLAIM["text"]]]
        volgorde = [c["id"] for c in concept.data["claims"]]
        assert volgorde.index(ids[BUURCLAIM["text"]]) < volgorde.index(ids["Dus X."])


class TestFailClosed:
    @pytest.mark.parametrize("ruw", [None, [], "tekst", 3])
    def test_geen_object(self, ruw):
        assert structuurfout(ruw)

    def test_onbekend_veld_bovenaan(self):
        assert "onbekend: ['evidence']" in structuurfout(antwoord(evidence=[]))

    def test_ontbrekend_veld_bovenaan(self):
        ruw = antwoord()
        del ruw["genus_quote"]
        assert "ontbrekend: ['genus_quote']" in structuurfout(ruw)

    @pytest.mark.parametrize(
        "claim",
        [
            {"id": "C1", **KERNCLAIM},
            {**KERNCLAIM, "evidence": ["E1"]},
            {**KERNCLAIM, "premises": []},
            {"role": "material", "quotes": [TERUG]},
            {"role": "inference", "premises": [KERNCLAIM], "text": "t", "extra": 1},
            {"role": "absence_in_supplied_material", "text": "t", "quotes": []},
        ],
    )
    def test_claim_met_onbekende_of_ontbrekende_velden(self, claim):
        assert structuurfout(antwoord(reason=[claim]))

    @pytest.mark.parametrize(
        "citaat",
        [
            {**TERUG, "id": "E1"},
            {**TERUG, "start": 0},
            {"material_id": "definition", "quote": "via baan Neral"},
        ],
    )
    def test_citaat_met_onbekende_of_ontbrekende_velden(self, citaat):
        assert structuurfout(antwoord(reason=[mat("x", citaat)]))

    def test_onbekend_veld_in_buur_voorstel_en_vraag(self):
        ruw = antwoord()
        ruw["neighbours"][0]["reason_claims"] = []
        assert structuurfout(ruw)
        voorstel = {"term": "t", "source_quote": None, "reason": [KERNCLAIM], "id": "P"}
        assert structuurfout(antwoord(proposals=[voorstel]))
        vraag = {"text": "Waarom?", "claims": [], "id": "Q"}
        assert structuurfout(antwoord(question=vraag))

    @pytest.mark.parametrize(
        "bewerk",
        [
            lambda a: a.update(reason=["C1"]),
            lambda a: a["neighbours"][0].update(reason=["C1"]),
            lambda a: a["neighbours"][0].update(missing_feature="C1"),
            lambda a: a["neighbours"][0].update(feature_quote="E3"),
            lambda a: a.update(genus_quote="E1"),
            lambda a: a.update(core_features=["E2"]),
            lambda a: a.update(reason=[inf("t", "C1")]),
            lambda a: a.update(reason=[mat("t", "E1")]),
            lambda a: a.update(question={"text": "Waarom?", "claims": ["C1"]}),
        ],
        ids=[
            "reden-id",
            "buurreden-id",
            "missing-id",
            "feature-id",
            "genus-id",
            "kenmerk-id",
            "premisse-id",
            "citaat-id",
            "vraag-id",
        ],
    )
    def test_id_indirectie_geweigerd(self, bewerk):
        ruw = antwoord()
        bewerk(ruw)
        assert "geen object" in structuurfout(ruw)

    def test_citaat_voor_tekst_is_verplicht(self):
        omgekeerd = {"role": "material", "text": "t", "quotes": [TERUG]}
        detail = structuurfout(antwoord(reason=[omgekeerd]))
        assert "afgesproken volgorde" in detail

    def test_premissen_voor_tekst_is_verplicht(self):
        omgekeerd = {"role": "inference", "text": "t", "premises": [KERNCLAIM]}
        assert "afgesproken volgorde" in structuurfout(antwoord(reason=[omgekeerd]))

    def test_rol_eerst(self):
        omgekeerd = {"quotes": [TERUG], "role": "material", "text": "t"}
        assert "afgesproken volgorde" in structuurfout(antwoord(reason=[omgekeerd]))

    @pytest.mark.parametrize(
        "claim",
        [
            mat("t"),
            inf("t"),
            {"role": "material", "quotes": [TERUG], "text": ""},
            {"role": "material", "quotes": [TERUG], "text": 3},
            {"role": "onbekend", "text": "t"},
            {"role": ["material"], "quotes": [TERUG], "text": "t"},
            {"role": "material", "quotes": TERUG, "text": "t"},
            {"role": "inference", "premises": KERNCLAIM, "text": "t"},
        ],
        ids=[
            "material-zonder-citaat",
            "inference-zonder-premisse",
            "lege-tekst",
            "tekst-geen-string",
            "onbekende-rol",
            "rol-geen-tekst",
            "quotes-geen-lijst",
            "premises-geen-lijst",
        ],
    )
    def test_ongeldige_claim(self, claim):
        assert structuurfout(antwoord(reason=[claim]))

    @pytest.mark.parametrize(
        ("claim", "melding"),
        [
            (mat("t"), "een materiaalclaim heeft een citaat"),
            (inf("t"), "een gevolgtrekking heeft premissen"),
        ],
    )
    def test_lege_onderbouwing_al_in_het_antwoord_geweigerd(self, claim, melding):
        """De answer/2-laag weigert zelf, niet pas de conceptcontrole erna."""
        assert structuurfout(antwoord(reason=[claim])) == f"reason[0]: {melding}"

    @pytest.mark.parametrize(
        "citaat",
        [
            {**TERUG, "quote": ""},
            {**TERUG, "quote": 3},
            {**TERUG, "material_id": ""},
            {**TERUG, "material_sha256": None},
        ],
    )
    def test_ongeldig_citaat(self, citaat):
        assert structuurfout(antwoord(reason=[mat("t", citaat)]))

    def test_dubbel_citaat_binnen_een_claim(self):
        assert "dubbel" in structuurfout(antwoord(reason=[mat("t", TERUG, TERUG)]))

    def test_dubbele_premisse_binnen_een_gevolgtrekking(self):
        assert "dubbel" in structuurfout(
            antwoord(reason=[inf("t", KERNCLAIM, KERNCLAIM)])
        )

    def test_dubbele_claim_binnen_een_lijst(self):
        assert "dubbel" in structuurfout(antwoord(reason=[KERNCLAIM, KERNCLAIM]))

    @pytest.mark.parametrize("veld", ["reason"])
    def test_lege_redenlijst(self, veld):
        assert structuurfout(antwoord(**{veld: []}))

    def test_lege_buur_en_voorstelreden(self):
        ruw = antwoord()
        ruw["neighbours"][0]["reason"] = []
        assert structuurfout(ruw)
        voorstel = {"term": "t", "source_quote": None, "reason": []}
        assert structuurfout(antwoord(proposals=[voorstel]))

    def _keten(self, diepte: int) -> dict:
        claim = KERNCLAIM
        for i in range(diepte - 1):
            claim = inf(f"Stap {i}.", claim)
        return claim

    def test_maximale_nesting_wordt_aanvaard(self):
        diepte = bewijs.MAX_CLAIMDIEPTE
        concept, fouten = leid_af(antwoord(reason=[self._keten(diepte)]))
        # de keten zelf plus de buurclaim en de buurgevolgtrekking
        assert fouten == [] and len(concept.data["claims"]) == diepte + 2

    def test_te_diepe_nesting_is_structuurfout(self):
        diepte = bewijs.MAX_CLAIMDIEPTE + 1
        assert "te diep genest" in structuurfout(antwoord(reason=[self._keten(diepte)]))

    def test_te_diepe_nesting_in_buur_en_vraag(self):
        keten = self._keten(bewijs.MAX_CLAIMDIEPTE + 1)
        ruw = antwoord()
        ruw["neighbours"][0]["uncertainty"] = keten
        assert "neighbours[0].uncertainty" in structuurfout(ruw)
        ruw = antwoord(question={"text": "Waarom?", "claims": [keten]})
        assert "question.claims[0]" in structuurfout(ruw)

    def test_extreem_diepe_nesting_zonder_exception(self):
        """Stopt op de grens, vóór verdere recursie (geen RecursionError)."""
        claim = KERNCLAIM
        for i in range(5000):
            claim = inf(f"S{i}", claim)
        ruw = antwoord()
        ruw["reason"] = [claim]  # zonder deepcopy van de diepe keten
        assert "te diep genest" in structuurfout(ruw)

    def test_regels_van_concept1_gelden_na_afleiding(self):
        ruw = antwoord()
        ruw["neighbours"][0]["feature_quote"] = None
        assert "distinguished vereist een kernfragment" in structuurfout(ruw)
        ruw = antwoord(genus_quote=q("source:b1", "Neral en Dovar"))
        assert "komt niet uit de definitiekern" in structuurfout(ruw)
        ruw = antwoord(neighbours=[])
        assert "elke verzonden buur" in structuurfout(ruw)
        ruw = antwoord()
        ruw["neighbours"][0]["distinction"] = "misschien"
        assert "onbekende distinction" in structuurfout(ruw)
        ruw = antwoord(question={"text": "Twee? Vragen?", "claims": []})
        assert "precies één gerichte vraag" in structuurfout(ruw)


class TestCitaten:
    def _fout(self, citaat) -> list[dict]:
        concept, fouten = leid_af(antwoord(reason=[KERNCLAIM, mat("t", citaat)]))
        assert concept is None
        return fouten

    def test_niet_letterlijk(self):
        (fout,) = self._fout(q("definition", "via de baan Neral"))
        assert (
            fout["reason"] == "citaat staat niet letterlijk in het aangewezen materiaal"
        )

    def test_dubbelzinnig(self):
        (fout,) = self._fout(q("definition", "a"))
        assert fout["reason"].startswith("citaat is dubbelzinnig")

    def test_verkeerde_hash(self):
        (fout,) = self._fout({**NERAL, "material_sha256": "0" * 64})
        assert fout["reason"] == "materiaalhash wijkt af"

    def test_onbekend_materiaal(self):
        (fout,) = self._fout({**NERAL, "material_id": "source:onbekend"})
        assert fout["reason"] == "onbekend materiaal"

    def test_citaat_uit_ander_materiaal(self):
        (fout,) = self._fout({**q("definition", "x"), "quote": "Dovar"})
        assert (
            fout["reason"] == "citaat staat niet letterlijk in het aangewezen materiaal"
        )


class TestBewijsroutes:
    def test_geneste_gevolgtrekking_in_verify4_routes(self):
        from services.validation.ess05_verification_service import bewijsroutes

        concept, _ = leid_af(antwoord())
        routes = {r["claim"]: r for r in bewijsroutes(concept)}
        assert routes["C3"] == {
            "claim": "C3",
            "rol": "inference",
            "uitspraak": "De kern sluit de buur daarom uit.",
            "gesloten_bewijsroute": [
                {"premisse": "C1", "uitspraak": KERNCLAIM["text"]},
                {"premisse": "C2", "uitspraak": BUURCLAIM["text"]},
            ],
        }
        assert routes["C2"]["gesloten_bewijsroute"] == [
            {"bewijs": "E4", "materiaal": "neighbour:n1", "citaat": "elders eindigt"}
        ]


# --- binding en replay ---------------------------------------------------------------


class TestBinding:
    """Replay leidt af met exact de gebonden antwoordversie; live is dat answer/2."""

    BINDINGSVELDEN = {
        "prompt_version",
        "verification_prompt_version",
        "schema_version",
        "verification_schema_version",
        "renderer_version",
        "norm_sha256",
        "provider",
        "model",
        "verification_provider",
        "verification_model",
    }

    def _binding(self, **anders):
        import dataclasses

        from domain.ess05.contract import Ess05Beoordelingsbinding

        basis = Ess05Beoordelingsbinding(
            prompt_version="ess05-assess/fake",
            verification_prompt_version="ess05-verify/fake",
            norm_sha256="n" * 64,
            provider="fake",
            model="m",
            verification_provider="fake",
            verification_model="m",
        )
        return dataclasses.replace(basis, **anders)

    def test_binding_draagt_answer2_zonder_de_documentvorm_te_wijzigen(self):
        from domain.ess05.contract import Ess05Beoordelingsbinding

        binding = self._binding()
        assert binding.answer_schema_version == ANTWOORD2
        assert set(binding.als_dict()) == self.BINDINGSVELDEN
        assert Ess05Beoordelingsbinding.uit_dict(binding.als_dict()) == binding

    def _document(self, binding):
        from tests.fixtures.def768_fakes import bouw_document

        spec = {
            "reason": "Synthetisch.",
            "neighbours": [
                {
                    "neighbour_id": "gebruiker:db19d1185536",
                    "distinction": "distinguished",
                    "distinguishing_feature_quote": "actuele lening",
                    "reason": "Synthetisch buuroordeel.",
                }
            ],
        }
        return bouw_document(
            "lener", LENER, CONTEXT, [], buren=BUURLIJST, spec=spec, binding=binding
        )

    def _afwijzing(self, document, binding):
        from domain.ess05.contract import beoordelingsafwijzing

        return beoordelingsafwijzing(
            document, "lener", LENER, CONTEXT, [], intentie=None, buren=BUURLIJST,
            binding=binding,
        )  # fmt: skip

    def _als_answer1(self, document) -> dict:
        """Hetzelfde concept, als historisch plat answer/1-antwoord gebonden."""
        oud = copy.deepcopy(document)
        antwoord = copy.deepcopy(document["concept"])
        antwoord["schema_version"] = ANTWOORD1
        antwoord["evidence"] = [
            {k: e[k] for k in ("id", "material_id", "material_sha256", "quote")}
            for e in antwoord["evidence"]
        ]
        ruw = json.dumps(antwoord, ensure_ascii=False)
        oud["raw_response"] = ruw
        oud["raw_response_sha256"] = _sha(ruw)
        oud["concept_derivation"].update(
            answer_schema_version=ANTWOORD1, raw_response_sha256=_sha(ruw)
        )
        return oud

    def test_live_document_is_answer2_en_wordt_toegepast(self):
        from domain.modeluitvoer import parse_modeluitvoer

        binding = self._binding()
        document = self._document(binding)
        assert document["concept_derivation"]["answer_schema_version"] == ANTWOORD2
        assert parse_modeluitvoer(document["raw_response"])["schema_version"] == (
            ANTWOORD2
        )
        assert self._afwijzing(document, binding) is None

    def test_answer1_document_alleen_onder_expliciete_historische_versie(self):
        binding = self._binding()
        oud = self._als_answer1(self._document(binding))
        reden = self._afwijzing(oud, binding)
        assert "afleidingsbinding wijkt af (answer_schema_version)" in reden
        historisch = self._binding(answer_schema_version=ANTWOORD1)
        assert self._afwijzing(oud, historisch) is None
        # Onder die historische binding geldt een answer/2-document niet.
        nieuw = self._document(binding)
        assert "answer_schema_version" in self._afwijzing(nieuw, historisch)

    def test_answer1_ruw_met_answer2_label_wordt_niet_toegepast(self):
        binding = self._binding()
        oud = self._als_answer1(self._document(binding))
        oud["concept_derivation"]["answer_schema_version"] = ANTWOORD2
        assert "niet afgeleid uit de bewaarde ruwe respons" in self._afwijzing(
            oud, binding
        )

    def test_diepe_ruwe_respons_wordt_bij_replay_geweigerd(self):
        """A2-01: ook de replay leest via de gedeelde parser; geen exception."""
        binding = self._binding()
        document = copy.deepcopy(self._document(binding))
        ruw = '{"schema_version": "ess05-answer/2", "reason": ' + _diep(10000) + "}"
        document["raw_response"] = ruw
        document["raw_response_sha256"] = _sha(ruw)
        document["concept_derivation"]["raw_response_sha256"] = _sha(ruw)
        assert "niet afgeleid uit de bewaarde ruwe respons" in self._afwijzing(
            document, binding
        )


def _diep(n: int, kern: str = "0") -> str:
    return "[" * n + kern + "]" * n


class TestDiepeRuweJson:
    """A2-01: ruwe JSON die dieper nest dan de parsergrens is geen JSON-object.

    De test met 5000 claimniveaus hierboven gaat uit van een al opgebouwd
    Python-object; deze tests beginnen bij de ruwe tekst, waar `json.loads`
    zelf al een RecursionError kan geven.
    """

    @pytest.mark.parametrize(
        "ruw",
        [
            '{"schema_version":"ess05-answer/2","reason":' + _diep(10000) + "}",
            '{"a": ' * 10000 + "0" + "}" * 10000,
            '```json\n{"reason": ' + _diep(10000) + "}\n```",
        ],
        ids=["lijsten-review-a2-01", "objecten", "codeblok"],
    )
    def test_recursiediepte_is_geen_json_object(self, ruw):
        assert modeluitvoer.parse_modeluitvoer(ruw) is None

    def test_grens_is_exact(self):
        grens = modeluitvoer.MAX_JSON_DIEPTE
        # Het omringende object telt als eerste niveau.
        op_de_grens = '{"a": ' + _diep(grens - 1) + "}"
        erboven = '{"a": ' + _diep(grens) + "}"
        assert modeluitvoer.parse_modeluitvoer(op_de_grens) is not None
        assert modeluitvoer.parse_modeluitvoer(erboven) is None
        # Ook de lengte van een lijst of object telt niet mee, alleen de nesting.
        breed = json.dumps({"a": [[0] * 5000], "b": {str(i): i for i in range(5000)}})
        assert modeluitvoer.parse_modeluitvoer(breed) is not None

    def test_diepste_geldige_antwoord_blijft_onder_de_grens(self):
        """De grens weigert geen afgesproken answer/2; de claimgrens meldt zelf."""

        def keten(diepte):
            claim = KERNCLAIM
            for i in range(diepte - 1):
                claim = inf(f"Stap {i}.", claim)
            return claim

        ruw = antwoord()
        ruw["neighbours"][0]["reason"].append(keten(bewijs.MAX_CLAIMDIEPTE))
        geparsed = modeluitvoer.parse_modeluitvoer(json.dumps(ruw))
        assert geparsed == ruw
        concept, fouten = leid_af(geparsed)
        assert fouten == [] and concept is not None

        ruw["neighbours"][0]["reason"][-1] = keten(bewijs.MAX_CLAIMDIEPTE + 1)
        geparsed = modeluitvoer.parse_modeluitvoer(json.dumps(ruw))
        assert "te diep genest" in structuurfout(geparsed)


CONTEXT = {
    "organisatorische_context": ["Studiefinanciering"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
LENER = "persoon met een actuele lening bij de instelling"
BUURLIJST = [
    {
        "term": "werknemer",
        "definitie": "persoon met een arbeidsovereenkomst met de instelling",
        "herkomst": "gebruiker",
        "bevestigd": True,
    }
]


class TestPromptcontract:
    """Het antwoordsjabloon in de beoordelingsprompt (assess/18), geen gedrag."""

    def test_sjabloon_is_answer2_genest_zonder_ids(self):
        from services.validation.ess05_assessment_service import (
            _ANTWOORDSTRUCTUUR,
            Ess05AssessmentService,
        )

        assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/18"
        assert '"schema_version": "ess05-answer/2"' in _ANTWOORDSTRUCTUUR
        for veld in (
            '"genus_quote"',
            '"core_features"',
            '"feature_quote"',
            '"missing_feature"',
            '"uncertainty"',
            '"source_quote"',
            '"quotes"',
            '"premises"',
        ):
            assert veld in _ANTWOORDSTRUCTUUR, veld
        for oud in (
            '"evidence"',
            '"reason_claims"',
            '"genus_evidence"',
            '"feature_evidence"',
            '"source_evidence"',
            '"missing_feature_claim"',
            '"id"',
        ):
            assert oud not in _ANTWOORDSTRUCTUUR, oud
        # Citaat-eerst: in elk claimsjabloon staan citaten/premissen vóór de tekst.
        assert '{"role": "material", "quotes": [<citaat>], "text"' in _ANTWOORDSTRUCTUUR
        assert (
            '{"role": "inference", "premises": [<claim>], "text"' in _ANTWOORDSTRUCTUUR
        )
        assert f"hoogstens {bewijs.MAX_CLAIMDIEPTE} niveaus" in _ANTWOORDSTRUCTUUR
