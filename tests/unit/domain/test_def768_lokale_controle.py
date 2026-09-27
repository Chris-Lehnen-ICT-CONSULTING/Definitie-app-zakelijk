"""DEF-768 fase A — lokale controle: één uitspraak met uitsluitend haar eigen route.

Het controlepakket (`inhoud`) is exact wat een lokaal verificatieverzoek mag
bevatten: de uitspraak, haar rol en haar citaten (material) of directe
premissen (inference). Materiaal-ID's, materiaalhashes, posities, claim-ID's en
de concepthash staan uitsluitend in de binding, buiten de modelpayload.
Synthetisch materiaal; bewijst gegevensisolatie en fail-closed toetsing, geen
semantische juistheid.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from domain.ess05 import bewijs, lokale_controle as lc

pytestmark = [pytest.mark.unit]

DEFINITIE = "tijdelijk ter beschikking stellen van een voorwerp aan een persoon"
BRON = (
    "Regel A: het voorwerp wordt tijdelijk en kosteloos uitgegeven. "
    "Regel B: een ander voorwerp blijft in de kast."
)
MATERIAAL = {
    "definition": DEFINITIE,
    "context": "organisatorische_context: Afdeling Middelen",
    "source:doc:regels": BRON,
    "neighbour:gebruiker:abc": "tegen betaling ter beschikking stellen",
}
BUURTERMEN = {"gebruiker:abc": "huur"}


def _ref(materiaal_id: str, citaat: str, materiaal=MATERIAAL) -> lc.Citaatverwijzing:
    start = materiaal[materiaal_id].index(citaat)
    return lc.Citaatverwijzing(materiaal_id, start, start + len(citaat))


def _materiaalpakket(materiaal=MATERIAAL, uitspraak="De kern noemt tijdelijkheid."):
    return lc.bouw_materiaalpakket(
        uitspraak,
        [_ref("definition", "tijdelijk", materiaal), _ref("source:doc:regels", "kosteloos", materiaal)],
        materiaal,
        buurtermen=BUURTERMEN,
    )  # fmt: skip


def _payload(pakket: lc.Lokaalpakket) -> str:
    return json.dumps(dict(pakket.inhoud), ensure_ascii=False)


class TestMateriaalpakket:
    def test_alleen_uitspraak_rol_en_eigen_citaten(self):
        pakket = _materiaalpakket()
        assert set(pakket.inhoud) == {"schema_version", "rol", "uitspraak", "citaten"}
        assert pakket.inhoud["schema_version"] == lc.PAKKETSCHEMA
        assert pakket.rol == bewijs.ROL_MATERIAAL
        assert [set(c) for c in pakket.inhoud["citaten"]] == [
            {"id", "herkomst", "omvang", "citaat"}
        ] * 2
        assert [c["citaat"] for c in pakket.inhoud["citaten"]] == [
            "tijdelijk",
            "kosteloos",
        ]
        assert [c["id"] for c in pakket.inhoud["citaten"]] == ["B1", "B2"]

    def test_geen_ongeciteerde_tekst_en_geen_binding_in_de_payload(self):
        pakket = _materiaalpakket()
        payload = _payload(pakket)
        for verboden in (DEFINITIE, BRON, "Regel B", MATERIAAL["context"],
                         MATERIAAL["neighbour:gebruiker:abc"], "material_sha256",
                         bewijs._sha256(DEFINITIE), "source:doc:regels", '"start"'):  # fmt: skip
            assert verboden not in payload, verboden

    def test_binding_buiten_de_payload_draagt_materiaal_en_posities(self):
        pakket = _materiaalpakket()
        kern, bron = pakket.binding["citaten"]
        assert kern == {
            "material_id": "definition",
            "material_sha256": bewijs._sha256(DEFINITIE),
            "start": 0,
            "end": len("tijdelijk"),
        }
        assert bron["material_id"] == "source:doc:regels"
        assert pakket.binding["pakket_hash"] == pakket.hash

    def test_omvang_fragment_of_volledige_tekst(self):
        pakket = lc.bouw_materiaalpakket(
            "De kern noemt geen kosten.",
            [lc.Citaatverwijzing("definition", 0, len(DEFINITIE)),
             _ref("source:doc:regels", "kosteloos")],
            MATERIAAL,
        )  # fmt: skip
        assert [c["omvang"] for c in pakket.inhoud["citaten"]] == [
            lc.OMVANG_VOLLEDIG,
            lc.OMVANG_FRAGMENT,
        ]

    def test_herkomstlabels_generiek(self):
        pakket = lc.bouw_materiaalpakket(
            "x",
            [_ref("definition", "tijdelijk"), _ref("context", "Afdeling"),
             _ref("source:doc:regels", "Regel A"),
             _ref("neighbour:gebruiker:abc", "tegen betaling")],
            MATERIAAL,
            buurtermen=BUURTERMEN,
        )  # fmt: skip
        assert [c["herkomst"] for c in pakket.inhoud["citaten"]] == [
            "definitie",
            "context",
            "bron doc:regels",
            "beschrijving verwant begrip 'huur'",
        ]

    def test_metamorf_ongeciteerde_tekst_wijzigt_niets_route_wel(self):
        basis = _materiaalpakket()
        # Zelfde citaten, andere tekst buiten de route (ook in het geciteerde materiaal).
        anders = {**MATERIAAL, "source:doc:regels": BRON.replace("kast", "la"),
                  "context": "organisatorische_context: Andere afdeling"}  # fmt: skip
        zelfde = _materiaalpakket(anders)
        assert zelfde.inhoud == basis.inhoud and zelfde.hash == basis.hash
        assert (
            zelfde.binding != basis.binding
        )  # de materiaalhash bindt, buiten de payload
        # Een ander citaat of een andere uitspraak verandert het pakket.
        breder = lc.bouw_materiaalpakket(
            "De kern noemt tijdelijkheid.",
            [_ref("definition", "tijdelijk ter"), _ref("source:doc:regels", "kosteloos")],
            MATERIAAL,
        )  # fmt: skip
        assert breder.hash != basis.hash
        assert _materiaalpakket(uitspraak="Iets anders.").hash != basis.hash

    @pytest.mark.parametrize(
        ("citaten", "melding"),
        [
            ([], "citaat"),
            ([lc.Citaatverwijzing("source:doc:onbekend", 0, 3)], "onbekend materiaal"),
            ([lc.Citaatverwijzing("definition", 5, 5)], "bereik"),
            ([lc.Citaatverwijzing("definition", 0, len(DEFINITIE) + 1)], "bereik"),
            ([lc.Citaatverwijzing("definition", -1, 3)], "bereik"),
        ],
    )
    def test_ongeldige_route_geweigerd(self, citaten, melding):
        with pytest.raises(lc.PakketfoutError, match=melding):
            lc.bouw_materiaalpakket("x", citaten, MATERIAAL)

    def test_lege_uitspraak_geweigerd(self):
        with pytest.raises(lc.PakketfoutError, match="uitspraak"):
            lc.bouw_materiaalpakket("  ", [_ref("definition", "tijdelijk")], MATERIAAL)


class TestGevolgtrekkingspakket:
    def test_alleen_uitspraak_en_directe_premissen(self):
        pakket = lc.bouw_gevolgtrekkingspakket("Dus Z.", ["X geldt.", "Y geldt."])
        assert dict(pakket.inhoud) == {
            "schema_version": lc.PAKKETSCHEMA,
            "rol": bewijs.ROL_GEVOLGTREKKING,
            "uitspraak": "Dus Z.",
            "premissen": [
                {"id": "P1", "uitspraak": "X geldt."},
                {"id": "P2", "uitspraak": "Y geldt."},
            ],
        }

    def test_premissevolgorde_en_tekst_binden_het_pakket(self):
        a = lc.bouw_gevolgtrekkingspakket("Dus Z.", ["X geldt.", "Y geldt."])
        assert (
            lc.bouw_gevolgtrekkingspakket("Dus Z.", ["Y geldt.", "X geldt."]).hash
            != a.hash
        )
        assert lc.bouw_gevolgtrekkingspakket("Dus Z.", ["X geldt."]).hash != a.hash

    @pytest.mark.parametrize("premissen", [[], ["X.", " "]])
    def test_lege_premissen_geweigerd(self, premissen):
        with pytest.raises(lc.PakketfoutError, match="premisse"):
            lc.bouw_gevolgtrekkingspakket("Dus Z.", premissen)


# --- uit een echt concept (R13-H2, ongewijzigde modeluitvoer; historisch answer/2) --------

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ess05"
R13 = {
    g["id"]: g
    for g in json.loads(
        (FIXTURE / "r13_herkenbare_antwoorden_v1.json").read_text(encoding="utf-8")
    )["gevallen"]
}


def _r13_concept(gid: str):
    geval = R13[gid]
    concept, fouten = bewijs.valideer_antwoord(
        json.loads(geval["raw_response"]),
        geval["materiaal"],
        geval["buren"],
        schema=bewijs.ANTWOORDSCHEMA_2,
    )
    assert concept is not None, fouten
    return concept, geval["materiaal"]


def _claim(concept, rol: str) -> dict:
    return next(c for c in concept.data["claims"] if c["role"] == rol)


class TestUitConcept:
    def test_materiaalclaim_exact_haar_eigen_citaten(self):
        concept, materiaal = _r13_concept("H2")
        claim = _claim(concept, bewijs.ROL_MATERIAAL)
        pakket = lc.pakket_uit_concept(concept, claim["id"], materiaal)
        bewijsplaatsen = {e["id"]: e for e in concept.data["evidence"]}
        assert pakket.inhoud["uitspraak"] == claim["text"]
        assert [c["citaat"] for c in pakket.inhoud["citaten"]] == [
            bewijsplaatsen[e]["quote"] for e in claim["evidence"]
        ]
        assert pakket.binding["claim"] == claim["id"]
        assert pakket.binding["concept_hash"] == concept.hash

    def test_gevolgtrekking_exact_haar_directe_premissen(self):
        concept, materiaal = _r13_concept("H2")
        claim = _claim(concept, bewijs.ROL_GEVOLGTREKKING)
        teksten = {c["id"]: c["text"] for c in concept.data["claims"]}
        pakket = lc.pakket_uit_concept(concept, claim["id"], materiaal)
        assert [p["uitspraak"] for p in pakket.inhoud["premissen"]] == [
            teksten[p] for p in claim["premises"]
        ]
        assert pakket.binding["premissen"] == claim["premises"]

    def test_andere_claims_concepthash_en_claimids_niet_in_de_payload(self):
        concept, materiaal = _r13_concept("H2")
        for claim in concept.data["claims"]:
            pakket = lc.pakket_uit_concept(concept, claim["id"], materiaal)
            payload = _payload(pakket)
            eigen = {claim["text"]} | {
                c["text"]
                for c in concept.data["claims"]
                if c["id"] in claim["premises"]
            }
            for ander in concept.data["claims"]:
                if ander["text"] not in eigen and ander["text"] not in claim["text"]:
                    assert ander["text"] not in payload, (claim["id"], ander["id"])
            assert concept.hash not in payload
            assert f'"{claim["id"]}"' not in payload

    def test_afwezigheidsclaim_valt_buiten_fase_a(self):
        concept, materiaal = _r13_concept("H2")
        data = copy.deepcopy(concept.als_dict())
        claim = _claim(bewijs.Ess05Concept(data), bewijs.ROL_MATERIAAL)
        claim["role"] = bewijs.ROL_AFWEZIGHEID
        with pytest.raises(lc.PakketfoutError, match="afwezigheid"):
            lc.pakket_uit_concept(bewijs.Ess05Concept(data), claim["id"], materiaal)

    def test_ander_materiaal_dan_de_binding_geweigerd(self):
        concept, materiaal = _r13_concept("H2")
        claim = _claim(concept, bewijs.ROL_MATERIAAL)
        gewijzigd = {k: v + " (gewijzigd)" for k, v in materiaal.items()}
        with pytest.raises(lc.PakketfoutError, match="materiaalhash"):
            lc.pakket_uit_concept(concept, claim["id"], gewijzigd)

    def test_onbekende_claim_geweigerd(self):
        concept, materiaal = _r13_concept("H2")
        with pytest.raises(lc.PakketfoutError, match="onbekende claim"):
            lc.pakket_uit_concept(concept, "C999", materiaal)


# --- toetsing van het lokale antwoord -----------------------------------------------------


def _antwoord(pakket, **anders) -> dict:
    ruw = {
        "schema_version": lc.LOKAAL_VERIFICATIESCHEMA,
        "packet_hash": pakket.hash,
        "checks": [
            {"item": lc.CONTROLE_ITEM, "outcome": "supported", "finding": "B1 draagt."}
        ],
    }
    ruw.update(anders)
    return ruw


class TestToetsing:
    @pytest.mark.parametrize("uitkomst", bewijs.UITKOMSTEN)
    def test_uitkomst_onveranderd_doorgegeven(self, uitkomst):
        pakket = _materiaalpakket()
        ruw = _antwoord(pakket)
        ruw["checks"][0]["outcome"] = uitkomst
        resultaat = lc.toets_lokale_verificatie(ruw, pakket)
        assert (resultaat.uitkomst, resultaat.soort) == (uitkomst, None)
        assert resultaat.bevinding == "B1 draagt."

    def test_verwisseld_pakket_is_hashfout(self):
        pakket, ander = _materiaalpakket(), _materiaalpakket(uitspraak="Iets anders.")
        resultaat = lc.toets_lokale_verificatie(_antwoord(ander), pakket)
        assert (resultaat.uitkomst, resultaat.soort) == (None, "packet_hash_mismatch")

    @pytest.mark.parametrize(
        "checks",
        [
            [],
            [{"item": lc.CONTROLE_ITEM, "outcome": "supported", "finding": "a"}] * 2,
            [{"item": lc.CONTROLE_ITEM, "outcome": "supported", "finding": "a"},
             {"item": "completeness", "outcome": "supported", "finding": "b"}],
            [{"item": "claim:C1", "outcome": "supported", "finding": "a"}],
            [{"item": lc.CONTROLE_ITEM, "outcome": "waar", "finding": "a"}],
            [{"item": lc.CONTROLE_ITEM, "outcome": "supported", "finding": " "}],
            [{"item": lc.CONTROLE_ITEM, "outcome": "supported"}],
        ],
        ids=["leeg", "dubbel", "extra", "ander-item", "onbekende-uitkomst",
             "lege-bevinding", "veld-ontbreekt"],
    )  # fmt: skip
    def test_dekking_en_vorm_fail_closed(self, checks):
        pakket = _materiaalpakket()
        resultaat = lc.toets_lokale_verificatie(
            _antwoord(pakket, checks=checks), pakket
        )
        assert (resultaat.uitkomst, resultaat.soort) == (None, "malformed_response")

    @pytest.mark.parametrize(
        "ruw",
        [
            "geen object",
            {"schema_version": "ess05-verification/1"},
            {"schema_version": "ess05-local-verification/0", "packet_hash": "x",
             "checks": []},
        ],
    )  # fmt: skip
    def test_schema_fail_closed(self, ruw):
        resultaat = lc.toets_lokale_verificatie(ruw, _materiaalpakket())
        assert (resultaat.uitkomst, resultaat.soort) == (None, "malformed_response")

    def test_extra_veld_fail_closed(self):
        pakket = _materiaalpakket()
        ruw = _antwoord(pakket, candidate_hash="x")
        assert lc.toets_lokale_verificatie(ruw, pakket).soort == "malformed_response"
