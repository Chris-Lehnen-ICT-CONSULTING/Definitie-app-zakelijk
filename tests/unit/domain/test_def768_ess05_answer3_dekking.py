"""DEF-768 R13-herstel — `ess05-answer/3`: plaatsgebonden routedekking.

Bevindingen (logs/def768/herkenbare-gevallen-inhoudscontrole-result-v1.md): vrije
claims in de reden van het geheel (H2 C5 vergelijkt met verhuur; H5 C3 concludeert
appstatus uit afwezige buren) en buurclaims waarvan de eigen route één kant van de
vergelijking mist (H2 C13 `missing_feature` zonder kerncitaat; H3 C7 buurconclusie
zonder kerncitaat). De verifier ving dat inconsistent op.

answer/3 = de geneste vorm van answer/2 plus een codegebonden eis per plaats:

- `reason` van het geheel steunt (ook via premissen) alleen op materiaal van de
  kandidaat zelf: definitie, context of bedoelde betekenis;
- per verwant begrip bevat de route van `missing_feature` een kerncitaat én een
  citaat dat het ontbrekende kenmerk draagt (bron, buurbeschrijving of betekenis);
- elke gevolgtrekking direct in de buur-`reason` bevat een kerncitaat én materiaal
  van de buurkant (bron, buurbeschrijving of een afwezigheidsclaim).

Historisch: de echte R13-antwoorden staan ongewijzigd in
`tests/fixtures/ess05/r13_herkenbare_antwoorden_v1.json` en blijven als answer/2
afleidbaar. Varianten hieronder zijn synthetisch en per functie afgeleid; ze
bewijzen de vaste controle, geen modelkwaliteit.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from domain.ess05 import bewijs

pytestmark = [pytest.mark.unit]

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "ess05"
    / "r13_herkenbare_antwoorden_v1.json"
)
GEVALLEN = {
    g["id"]: g for g in json.loads(FIXTURE.read_text(encoding="utf-8"))["gevallen"]
}


def _geval(gid: str) -> tuple[dict, dict, dict]:
    geval = GEVALLEN[gid]
    return json.loads(geval["raw_response"]), geval["materiaal"], geval["buren"]


def _als3(antwoord: dict) -> dict:
    """Synthetisch: hetzelfde antwoord, alleen `schema_version` answer/3."""
    kopie = copy.deepcopy(antwoord)
    kopie["schema_version"] = bewijs.ANTWOORDSCHEMA
    return kopie


def _valideer3(antwoord: dict, materiaal: dict, buren: dict):
    return bewijs.valideer_antwoord(_als3(antwoord), materiaal, buren)


def _structuurfout(uitkomst) -> str:
    concept, fouten = uitkomst
    assert concept is None, "antwoord ten onrechte aanvaard"
    assert fouten[0]["reason"] == "structuurfout", fouten
    return fouten[0]["detail"]


def _kern(antwoord: dict) -> dict:
    """De eerste top-level claim van elk R13-antwoord: een kerncitaat (material)."""
    claim = antwoord["reason"][0]
    assert claim["role"] == "material"
    assert {q["material_id"] for q in claim["quotes"]} == {"definition"}
    return claim


def _citaat(materiaal: dict, locatie: str, tekst: str) -> dict:
    assert materiaal[locatie].count(tekst) == 1
    from hashlib import sha256

    return {
        "material_id": locatie,
        "material_sha256": sha256(materiaal[locatie].encode("utf-8")).hexdigest(),
        "quote": tekst,
    }


# --- versie en historie -----------------------------------------------------------------


class TestVersie:
    def test_actueel_answer3_historisch_answer2_expliciet(self):
        assert bewijs.ANTWOORDSCHEMA == "ess05-answer/3"
        assert bewijs.ANTWOORDSCHEMA_2 == "ess05-answer/2"

    @pytest.mark.parametrize("gid", sorted(GEVALLEN))
    def test_echte_r13_antwoorden_blijven_als_answer2_afleidbaar(self, gid):
        antwoord, materiaal, buren = _geval(gid)
        assert antwoord["schema_version"] == "ess05-answer/2"
        concept, fouten = bewijs.valideer_antwoord(
            antwoord, materiaal, buren, schema=bewijs.ANTWOORDSCHEMA_2
        )
        assert concept is not None, fouten

    def test_answer2_niet_als_actueel_antwoord(self):
        antwoord, materiaal, buren = _geval("H4")
        assert "answer/3" in _structuurfout(
            bewijs.valideer_antwoord(antwoord, materiaal, buren)
        )


# --- de werkelijke defecten, als answer/3 aangeboden ------------------------------------


class TestR13Defecten:
    def test_h2_c5_vergelijking_in_reden_van_het_geheel(self):
        """H2 met alleen kerncitaat + C5 bovenaan (C13 al hersteld): C5 weigert."""
        antwoord, materiaal, buren = _geval("H2")
        c5 = antwoord["reason"][2]
        assert c5["role"] == "inference" and "verhuur" in c5["text"]
        antwoord["neighbours"][0]["missing_feature"] = _h2_missing_hersteld(
            antwoord, materiaal
        )
        antwoord["reason"] = [_kern(antwoord), c5]
        detail = _structuurfout(_valideer3(antwoord, materiaal, buren))
        assert "reason van het geheel" in detail and "source:" in detail

    def test_h2_c13_missing_feature_zonder_kerncitaat(self):
        antwoord, materiaal, buren = _geval("H2")
        antwoord["reason"] = [_kern(antwoord)]
        mf = antwoord["neighbours"][0]["missing_feature"]
        assert {q["material_id"] for q in mf["quotes"]} == {
            "source:doc:testwerkinstructie-apparatuuruitgifte"
        }
        detail = _structuurfout(_valideer3(antwoord, materiaal, buren))
        assert "missing_feature" in detail and "definitie" in detail

    def test_h3_c7_buurconclusie_zonder_kerncitaat(self):
        antwoord, materiaal, buren = _geval("H3")
        # De top-level reden van H3 (kern + context) voldoet al; alleen C7 schendt.
        detail = _structuurfout(_valideer3(antwoord, materiaal, buren))
        assert "gevolgtrekking" in detail and "definitie" in detail

    def test_h5_c3_appstatus_uit_afwezige_buren(self):
        antwoord, materiaal, buren = _geval("H5")
        assert antwoord["reason"][2]["role"] == "inference"
        detail = _structuurfout(_valideer3(antwoord, materiaal, buren))
        assert "reason van het geheel" in detail

    def test_h1_origineel_met_broncitaat_bovenaan_weigert(self):
        """Ook een juiste maar overbodige bronclaim bovenaan past niet in answer/3."""
        antwoord, materiaal, buren = _geval("H1")
        assert "reason van het geheel" in _structuurfout(
            _valideer3(antwoord, materiaal, buren)
        )


# --- synthetisch herstelde antwoorden (afleiding per functie) ---------------------------


def _h2_missing_hersteld(antwoord: dict, materiaal: dict) -> dict:
    """Synthetisch: C13 als gevolgtrekking uit de kernclaim (C3) en het bronkenmerk."""
    kern = antwoord["reason"][2]["premises"][0]  # C3: "De kern noemt geen kenmerk ..."
    bron = {
        "role": "material",
        "quotes": [
            _citaat(
                materiaal,
                "source:doc:testwerkinstructie-apparatuuruitgifte",
                "tijdelijk en kosteloos ter beschikking",
            )
        ],
        "text": "Volgens de bron is uitleen kosteloos.",
    }
    return {
        "role": "inference",
        "premises": [kern, bron],
        "text": "In de kern ontbreekt het door de bron gedragen kenmerk kosteloos.",
    }


class TestHersteld:
    def test_h2_hersteld_geeft_een_concept(self):
        """Afleiding: reden = alleen C1 (kern); missing_feature = kern + bron."""
        antwoord, materiaal, buren = _geval("H2")
        antwoord["neighbours"][0]["missing_feature"] = _h2_missing_hersteld(
            antwoord, materiaal
        )
        antwoord["reason"] = [_kern(antwoord)]
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten
        assert concept.data["neighbours"][0]["distinction"] == "not_distinguished"

    def test_h3_hersteld_met_kernpremisse(self):
        """Afleiding: C7 krijgt de kernclaim (C1) als extra premisse."""
        antwoord, materiaal, buren = _geval("H3")
        c7 = antwoord["neighbours"][0]["reason"][2]
        c7["premises"] = [_kern(antwoord), *c7["premises"]]
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten

    def test_h5_hersteld_alleen_kandidaat_bovenaan(self):
        antwoord, materiaal, buren = _geval("H5")
        antwoord["reason"] = [_kern(antwoord)]
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten

    def test_h4_origineel_voldoet_ongewijzigd(self):
        antwoord, materiaal, buren = _geval("H4")
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten

    def test_h1_zonder_bronclaim_bovenaan_voldoet(self):
        antwoord, materiaal, buren = _geval("H1")
        antwoord["reason"] = [_kern(antwoord)]
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten
        assert concept.data["neighbours"][0]["distinction"] == "distinguished"


# --- tegengevallen die een naïeve patch onderscheiden ------------------------------------


class TestTegengevallen:
    def test_diep_geneste_bronpremisse_bovenaan_weigert(self):
        """Niet alleen de directe claim: ook een premisse van een premisse telt."""
        antwoord, materiaal, buren = _geval("H4")
        kern = _kern(antwoord)
        bron = antwoord["neighbours"][0]["reason"][0]
        assert bron["role"] == "material"
        diep = {"role": "inference", "premises": [kern, bron], "text": "Tussenstap."}
        antwoord["reason"] = [
            kern,
            {"role": "inference", "premises": [kern, diep], "text": "Conclusie."},
        ]
        assert "reason van het geheel" in _structuurfout(
            _valideer3(antwoord, materiaal, buren)
        )

    def test_context_bovenaan_mag(self):
        antwoord, materiaal, buren = _geval("H3")
        c7 = antwoord["neighbours"][0]["reason"][2]
        c7["premises"] = [_kern(antwoord), *c7["premises"]]
        assert antwoord["reason"][1]["quotes"][0]["material_id"] == "context"
        concept, _ = _valideer3(antwoord, materiaal, buren)
        assert concept is not None

    def test_missing_feature_alleen_kern_weigert(self):
        """Een kerncitaat alleen draagt niet het ontbrekende kenmerk."""
        antwoord, materiaal, buren = _geval("H2")
        antwoord["reason"] = [_kern(antwoord)]
        kern = _kern(antwoord)
        antwoord["neighbours"][0]["missing_feature"] = {
            "role": "material",
            "quotes": kern["quotes"],
            "text": "In de kern ontbreekt een kenmerk over betaling.",
        }
        detail = _structuurfout(_valideer3(antwoord, materiaal, buren))
        assert "missing_feature" in detail

    def test_missing_feature_als_materiaalclaim_met_beide_citaten_mag(self):
        antwoord, materiaal, buren = _geval("H2")
        antwoord["reason"] = [_kern(antwoord)]
        kern = _kern(antwoord)
        antwoord["neighbours"][0]["missing_feature"] = {
            "role": "material",
            "quotes": [
                *kern["quotes"],
                _citaat(
                    materiaal,
                    "source:doc:testwerkinstructie-apparatuuruitgifte",
                    "tijdelijk en kosteloos ter beschikking",
                ),
            ],
            "text": "De kern noemt kosteloos niet; de bron draagt het voor uitleen.",
        }
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten

    def test_buurconclusie_uit_kern_en_context_weigert(self):
        """Kern plus kandidaatmateriaal is geen buurkant."""
        antwoord, materiaal, buren = _geval("H3")
        c7 = antwoord["neighbours"][0]["reason"][2]
        c7["premises"] = [_kern(antwoord), antwoord["reason"][1]]
        assert "gevolgtrekking" in _structuurfout(
            _valideer3(antwoord, materiaal, buren)
        )

    def test_buurconclusie_uit_kern_en_afwezigheid_mag(self):
        antwoord, materiaal, buren = _geval("H3")
        c7 = antwoord["neighbours"][0]["reason"][2]
        c7["premises"] = [
            _kern(antwoord),
            {
                "role": "absence_in_supplied_material",
                "text": "Het materiaal legt niet vast of verhuur kosteloos is.",
            },
        ]
        concept, fouten = _valideer3(antwoord, materiaal, buren)
        assert concept is not None, fouten

    def test_materiaalclaim_over_de_buur_in_buurreden_blijft_vrij(self):
        """Alleen gevolgtrekkingen dragen de vergelijking; beschrijvingen niet."""
        antwoord, materiaal, buren = _geval("H3")
        c7 = antwoord["neighbours"][0]["reason"][2]
        c7["premises"] = [_kern(antwoord), *c7["premises"]]
        eerste = antwoord["neighbours"][0]["reason"][0]
        assert eerste["role"] == "material"
        assert {q["material_id"] for q in eerste["quotes"]} == {
            next(iter(buren)) and f"neighbour:{next(iter(buren))}"
        }
        concept, _ = _valideer3(antwoord, materiaal, buren)
        assert concept is not None

    def test_afwezigheid_bovenaan_weigert(self):
        antwoord, materiaal, buren = _geval("H4")
        antwoord["reason"].append(
            {"role": "absence_in_supplied_material", "text": "Er is geen derde rol."}
        )
        assert "reason van het geheel" in _structuurfout(
            _valideer3(antwoord, materiaal, buren)
        )
