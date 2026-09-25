"""DEF-768 R8 — migratie van zes R7-antwoorden (/1) naar conceptoordelen (/2).

Voorstel §3 met de leidende rootcorrecties: elke oorspronkelijke tekst blijft
letterlijk (geen claim wordt verbeterd of gesplitst), ID's zijn neutraal,
offsets en hashes berekent de code, en goede en foute items volgen exact
dezelfde regels. De oorspronkelijke R7-bestanden blijven ongewijzigd; de
migratie is fail-closed (bronhashes, gevalhash, structuur).

Bewijst alleen de migratiemechaniek. Of de migratie de bedoelde fout trouw
draagt, is aan de trouwreview (controlelijst).
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

from domain.ess05.bewijs import verplichte_controles
from domain.ess05.contract import Buur, valideer_concept

try:  # de migratie bestaat pas na de GREEN-stap; RED faalt per test
    import migreer_r7_naar_v2 as mig
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mig = None

R7_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R7"
r7_nodig = pytest.mark.skipif(
    not (R7_MAP / "onafhankelijke-eindset-v1.json").is_file(),
    reason="git-ignored R7-bronbestanden ontbreken",
)

KERN = "sluitbericht dat de vrijgavecode voor een sluiting bevat"
BUUR = Buur(
    id="gebruiker:aaaaaaaaaaaa",
    term="draaihaak",
    definitie="werktuig dat een sluiting door mechanische verdraaiing opent",
    herkomst="gebruiker",
    bevestigd=True,
)
MATERIAAL = {
    "definition": KERN,
    "source:b1": "Berichten en werktuigen zijn verschillende objectsoorten.",
    f"neighbour:{BUUR.id}": BUUR.definitie,
}


def _oordeel(**anders):
    oordeel = {
        "lacks_differentia": False,
        "reason": "De kern noemt naast het bovenbegrip 'sluitbericht' een kenmerk.",
        "neighbours": [
            {
                "neighbour_id": BUUR.id,
                "distinction": "distinguished",
                "distinguishing_feature_quote": "de vrijgavecode voor een sluiting bevat",
                "missing_feature": None,
                "reason": "Een draaihaak bevat geen vrijgavecode.",
                "uncertainty": None,
            }
        ],
        "proposed_neighbours": [],
        "question": None,
    }
    oordeel.update(anders)
    return oordeel


def _buur(**anders):
    return {**_oordeel()["neighbours"][0], **anders}


def _migreer(oordeel):
    return mig.migreer(oordeel, MATERIAAL, (BUUR,))


class TestRegels:
    def test_geldig_concept_met_neutrale_ids(self):
        concept = _migreer(_oordeel())
        gevalideerd, fouten = valideer_concept(concept, MATERIAAL, (BUUR,))
        assert fouten == [] and gevalideerd is not None
        ids = [e["id"] for e in concept["evidence"]]
        assert ids == [f"E{i}" for i in range(1, len(ids) + 1)]
        assert [c["id"] for c in concept["claims"]] == ["C1", "C2"]
        assert [k["id"] for k in concept["core_features"]] == ["F1"]

    def test_teksten_letterlijk_en_ongesplitst(self):
        oordeel = _oordeel()
        concept = _migreer(oordeel)
        teksten = [c["text"] for c in concept["claims"]]
        assert teksten == [oordeel["reason"], oordeel["neighbours"][0]["reason"]]
        assert all(c["role"] == "material" for c in concept["claims"])
        assert all(c["premises"] == [] for c in concept["claims"])

    def test_volledig_materiaal_als_bewijs_met_berekende_offsets_en_hash(self):
        concept = _migreer(_oordeel())
        volledig = concept["evidence"][: len(MATERIAAL)]
        for item, (plaats, tekst) in zip(volledig, MATERIAAL.items(), strict=True):
            assert (item["material_id"], item["start"], item["end"]) == (
                plaats,
                0,
                len(tekst),
            )
            assert item["quote"] == tekst
            assert item["material_sha256"] == hashlib.sha256(tekst.encode()).hexdigest()
        for claim in concept["claims"]:
            assert claim["evidence"] == [e["id"] for e in volledig]

    def test_bovenbegrip_kenmerk_en_citaat_uit_de_kern(self):
        concept = _migreer(_oordeel())
        per_id = {e["id"]: e for e in concept["evidence"]}
        assert per_id[concept["genus_evidence"]]["quote"] == "sluitbericht"
        kenmerk = per_id[concept["core_features"][0]["evidence"]]
        assert kenmerk["quote"] == "dat de vrijgavecode voor een sluiting bevat"
        citaat = per_id[concept["neighbours"][0]["feature_evidence"]]
        assert citaat["quote"] == "de vrijgavecode voor een sluiting bevat"
        assert {e["material_id"] for e in (kenmerk, citaat)} == {"definition"}

    def test_zelfde_plaats_wordt_niet_verdubbeld(self):
        oordeel = _oordeel(neighbours=[_buur(distinguishing_feature_quote=KERN)])
        concept = _migreer(oordeel)
        plaatsen = [
            (e["material_id"], e["start"], e["end"]) for e in concept["evidence"]
        ]
        assert len(plaatsen) == len(set(plaatsen))
        assert concept["neighbours"][0]["feature_evidence"] == "E1"

    def test_not_distinguished_draagt_ontbrekend_kenmerk_als_claim(self):
        oordeel = _oordeel(
            neighbours=[
                _buur(
                    distinction="not_distinguished",
                    distinguishing_feature_quote=None,
                    missing_feature="het mechanische kenmerk",
                )
            ]
        )
        concept = _migreer(oordeel)
        buur = concept["neighbours"][0]
        assert buur["feature_evidence"] is None
        claims = {c["id"]: c["text"] for c in concept["claims"]}
        assert claims[buur["missing_feature_claim"]] == "het mechanische kenmerk"
        assert [c["id"] for c in concept["claims"]] == ["C1", "C2", "C3"]

    def test_zonder_kenmerk_lege_kernlijst(self):
        oordeel = _oordeel(
            lacks_differentia=True,
            neighbours=[
                _buur(
                    distinction="not_distinguished",
                    distinguishing_feature_quote=None,
                    missing_feature="x",
                )
            ],
        )
        concept = _migreer(oordeel)
        assert concept["core_features"] == []
        assert concept["genus_evidence"] is not None  # bovenbegrip één keer in de kern

    def test_vraag_zonder_claims(self):
        concept = _migreer(_oordeel(question="Welke soort is bedoeld?"))
        assert concept["question"] == {"text": "Welke soort is bedoeld?", "claims": []}

    @pytest.mark.parametrize(
        ("oordeel", "melding"),
        [
            (_oordeel(reason="Geen bovenbegrip genoemd."), "bovenbegrip"),
            (
                _oordeel(reason="Naast het bovenbegrip 'haak' een kenmerk."),
                "begint niet",
            ),
            (
                _oordeel(neighbours=[_buur(distinguishing_feature_quote="ontbreekt")]),
                "citaat",
            ),
            (
                _oordeel(proposed_neighbours=[{"term": "x", "reason": "y"}]),
                "voorstel",
            ),
            ({**_oordeel(), "extra": 1}, "velden"),
            (
                _oordeel(neighbours=[_buur(missing_feature="toch ontbrekend")]),
                "distinguished",
            ),
        ],
    )
    def test_fail_closed(self, oordeel, melding):
        with pytest.raises(mig.MigratiefoutError, match=melding):
            _migreer(oordeel)

    def test_goed_en_fout_volgen_dezelfde_regels(self):
        # Eén migratiefunctie, geen soortparameter: het label bestaat alleen
        # in de invoerspecificatie, niet in de migratieregels.
        import inspect

        assert "soort" not in inspect.signature(mig.migreer).parameters

    def test_foutdragende_items_moeten_verplichte_controles_zijn(self):
        concept = _migreer(_oordeel())
        gevalideerd, _ = valideer_concept(concept, MATERIAAL, (BUUR,))
        items = mig.foutdragende_items(
            concept,
            {
                "claims_met": ["bevat geen vrijgavecode"],
                "items": [f"neighbour:{BUUR.id}"],
            },
        )
        assert items == ["claim:C2", f"neighbour:{BUUR.id}"]
        assert set(items) <= set(verplichte_controles(gevalideerd))
        with pytest.raises(mig.MigratiefoutError, match="precies één"):
            mig.foutdragende_items(concept, {"claims_met": ["zzz"], "items": []})
        with pytest.raises(mig.MigratiefoutError, match="geen verplicht"):
            mig.foutdragende_items(concept, {"claims_met": [], "items": ["feature:F9"]})


class TestBronnen:
    def test_zes_vastgelegde_bronantwoorden(self):
        assert [b["id"] for b in mig.BRONNEN] == [
            "V-N1",
            "V-N2",
            "V-N3",
            "V-P1",
            "V-P2",
            "V-P3",
        ]
        assert [b["soort"] for b in mig.BRONNEN] == ["fout"] * 3 + ["goed"] * 3
        assert all(b["foutdragend"] for b in mig.BRONNEN if b["soort"] == "fout")
        assert not any(b["foutdragend"] for b in mig.BRONNEN if b["soort"] == "goed")

    @r7_nodig
    def test_echte_migratie_valideert_en_bindt(self):
        invoer = mig.maak_verificatie_invoer(R7_MAP)
        assert invoer["schema"] == mig.INVOERSCHEMA
        assert [i["id"] for i in invoer["items"]] == [b["id"] for b in mig.BRONNEN]
        for item in invoer["items"]:
            materiaal, buren, _ = mig.verificatiemateriaal(item["geval"])
            concept, fouten = valideer_concept(item["concept"], materiaal, buren)
            assert fouten == [], item["id"]
            assert item["concept_hash"] == concept.hash
            assert item["verplichte_controles"] == list(verplichte_controles(concept))
            assert set(item["foutdragende_items"]) <= set(item["verplichte_controles"])
            ruw = json.loads(item["bron"]["ruw_antwoord"])
            teksten = {c["text"] for c in item["concept"]["claims"]}
            assert ruw["reason"] in teksten
            for buur in ruw["neighbours"]:
                assert buur["reason"] in teksten
        per_id = {i["id"]: i for i in invoer["items"]}
        assert per_id["V-N2"]["foutdragende_items"] == ["core_features", "feature:F1"]

    @r7_nodig
    def test_bronhash_afwijking_geweigerd(self, tmp_path):
        kopie = tmp_path / "r7"
        for bron in mig.BRONNEN:
            doel = kopie / bron["callrecord"]
            doel.parent.mkdir(parents=True, exist_ok=True)
            doel.write_bytes((R7_MAP / bron["callrecord"]).read_bytes())
        eindset = json.loads((R7_MAP / mig.R7_EINDSET).read_text(encoding="utf-8"))
        (kopie / mig.R7_EINDSET).write_text(json.dumps(eindset), encoding="utf-8")
        with pytest.raises(mig.MigratiefoutError, match="eindset"):
            mig.maak_verificatie_invoer(kopie)

    @r7_nodig
    def test_origineel_ongewijzigd_en_controlelijst(self, tmp_path):
        voor = {
            b["callrecord"]: (R7_MAP / b["callrecord"]).read_bytes()
            for b in mig.BRONNEN
        }
        doel, lijst = tmp_path / "invoer.json", tmp_path / "lijst.md"
        assert mig.main(["--doel", str(doel), "--controlelijst", str(lijst)]) == 0
        for pad, inhoud in voor.items():
            assert (R7_MAP / pad).read_bytes() == inhoud
        tekst = lijst.read_text(encoding="utf-8")
        for bron in mig.BRONNEN:
            assert bron["id"] in tekst
        assert "trouwreview" in tekst.lower()
        with pytest.raises(FileExistsError):
            mig.main(["--doel", str(doel), "--controlelijst", str(tmp_path / "x.md")])

    @r7_nodig
    def test_controlelijst_toont_de_vraag_en_volgt_de_bestaande_invoer(self, tmp_path):
        doel = tmp_path / "invoer.json"
        assert (
            mig.main(["--doel", str(doel), "--controlelijst", str(tmp_path / "a.md")])
            == 0
        )
        invoer = doel.read_bytes()
        lijst = tmp_path / "b.md"
        assert mig.main(["--doel", str(doel), "--controlelijst", str(lijst),
                         "--alleen-controlelijst"]) == 0  # fmt: skip
        assert doel.read_bytes() == invoer
        tekst = lijst.read_text(encoding="utf-8")
        for item in json.loads(invoer)["items"]:
            vraag = item["concept"]["question"]
            if vraag is not None:
                assert vraag["text"] in tekst, item["id"]
        with pytest.raises(FileNotFoundError):
            mig.main(["--doel", str(tmp_path / "geen.json"), "--controlelijst",
                      str(tmp_path / "c.md"), "--alleen-controlelijst"])  # fmt: skip

    @r7_nodig
    def test_migratie_is_deterministisch(self):
        a = mig.maak_verificatie_invoer(R7_MAP)
        b = mig.maak_verificatie_invoer(R7_MAP)
        assert a == b
        assert copy.deepcopy(a) == a
