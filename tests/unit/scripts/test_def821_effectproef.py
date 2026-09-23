"""Regressietests voor scripts/testing/def821_effectproef.py (DEF-821).

De harness is bewijsvoering: strikt casusschema (JSON/JSONL), hard budget
(≤ 32 aanroepen, vóór elke aanroep geweigerd), geen secrets op schijf, de
verwachting nooit in de prompt, en een echte basisversie (``git archive``
van ``BASIS_REF``) naast de werkboom. Geen modelaanroepen hier: de
eind-tot-eindtest draait uitsluitend de offline modus (prompts bouwen, keten
stopt vóór het model).
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

from services.ai.base_client import ChatMessage, ChatResponse

pytestmark = [pytest.mark.unit]

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts" / "testing"))

import def821_effectproef as proef

ONTWIKKELCASUSSEN = REPO / "scripts" / "testing" / "def821_ontwikkelcasussen.json"
G2_BEGIN = "Beschrijf begripsbepalende kenmerken die in de bedoelde context"


def _casus(**extra) -> dict:
    return {"id": "C1", "begrip": "x", "verwachting": "v", **extra}


# ------------------------------------------------------------------ schema


def test_json_lijst_object_en_jsonl_worden_gelezen(tmp_path):
    lijst = tmp_path / "a.json"
    lijst.write_text(json.dumps([_casus()]), encoding="utf-8")
    obj = tmp_path / "b.json"
    obj.write_text(json.dumps({"casussen": [_casus(id="C2")]}), encoding="utf-8")
    jsonl = tmp_path / "c.jsonl"
    jsonl.write_text(
        json.dumps(_casus(id="C3")) + "\n\n" + json.dumps(_casus(id="C4")) + "\n",
        encoding="utf-8",
    )
    assert [c.id for c in proef.lees_casussen(lijst)] == ["C1"]
    assert [c.id for c in proef.lees_casussen(obj)] == ["C2"]
    assert [c.id for c in proef.lees_casussen(jsonl)] == ["C3", "C4"]


def test_volledige_casus_wordt_genormaliseerd():
    casus = proef.casus_uit_dict(
        _casus(
            organisatorische_context=[" Proefdienst "],
            juridische_context=["bestuursrecht"],
            wettelijke_basis=["Awb"],
            ontologische_categorie="proces",
            documenten=[{"doc_id": "d", "snippet": "s", "filename": "f.txt"}],
            betekenisverduidelijking="werkdagen",
            verwachte_uitkomst="ontbrekende_grond",
            herkomst="h",
        )
    )
    assert casus.organisatorische_context == ("Proefdienst",)
    assert casus.documenten == ({"doc_id": "d", "snippet": "s", "filename": "f.txt"},)
    assert casus.verwachte_uitkomst == "ontbrekende_grond"


@pytest.mark.parametrize(
    "fout",
    [
        {"id": "C 1"},
        {"id": ""},
        {"onbekend": 1},
        {"verwachting": " "},
        {"begrip": None},
        {"ontologische_categorie": "soort"},
        {"verwachte_uitkomst": "goed"},
        {"organisatorische_context": "DJI"},
        {"organisatorische_context": [""]},
        {"documenten": [{"doc_id": "d"}]},
        {"documenten": [{"doc_id": "d", "snippet": "s", "url": "http://x"}]},
        {"betekenisverduidelijking": ""},
    ],
)
def test_ongeldige_casus_wordt_geweigerd(fout):
    with pytest.raises(proef.CasusFoutError):
        proef.casus_uit_dict(_casus(**fout))


def test_dubbele_id_en_lege_lijst_worden_geweigerd(tmp_path):
    pad = tmp_path / "x.json"
    pad.write_text(json.dumps([_casus(), _casus()]), encoding="utf-8")
    with pytest.raises(proef.CasusFoutError):
        proef.lees_casussen(pad)
    pad.write_text("[]", encoding="utf-8")
    with pytest.raises(proef.CasusFoutError):
        proef.lees_casussen(pad)


def test_ontwikkelcasussen_d1_tot_d6_zijn_geldig_en_bevroren():
    casussen = proef.lees_casussen(ONTWIKKELCASUSSEN)
    assert [c.id for c in casussen] == ["D1", "D2", "D3", "D4", "D5", "D6"]
    verwacht = {c.id: c.verwachte_uitkomst for c in casussen}
    assert verwacht == {
        "D1": "definitie",
        "D2": "definitie",
        "D3": "ontbrekende_grond",
        "D4": "ontbrekende_grond",
        "D5": "definitie",
        "D6": "definitie",
    }
    # Betekenisgrond is expliciet (documentpassage), geen netwerkbron.
    assert all(len(c.documenten) == 1 for c in casussen)


# ------------------------------------------------------------------ budget


def test_budget_acht_casussen_twee_versies_twee_herhalingen_is_precies_32():
    assert proef.controleer_budget(8, 2, 32) == 32


@pytest.mark.parametrize(("casussen", "max_calls"), [(9, 32), (6, 20), (5, 19)])
def test_budget_boven_de_grens_wordt_vooraf_geweigerd(casussen, max_calls):
    with pytest.raises(SystemExit):
        proef.controleer_budget(casussen, 2, max_calls)


def test_max_calls_kan_de_harde_grens_niet_verhogen():
    with pytest.raises(SystemExit):
        proef.controleer_budget(9, 2, 1000)


class _FakeClient:
    provider_name = "fake"

    def __init__(self) -> None:
        self.aanroepen = 0

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None
    ):
        self.aanroepen += 1
        return ChatResponse(text="antwoord", model=model, tokens_used=1)

    async def close(self) -> None:
        return None


def test_proxy_weigert_boven_budget_zonder_de_echte_client_te_raken():
    echt = _FakeClient()
    client = proef.RegistrerendeClient(echt, budget=1)
    berichten = [ChatMessage(role="user", content="prompt")]

    async def _twee() -> None:
        await client.chat_completion(berichten, model="m", temperature=0.1)
        with pytest.raises(proef.LiveBudgetOverschredenError):
            await client.chat_completion(berichten, model="m", temperature=0.1)

    asyncio.run(_twee())
    assert echt.aanroepen == 1
    assert len(client.aanroepen) == 1
    aanroep = client.aanroepen[0]
    assert aanroep.respons_tekst == "antwoord"
    assert aanroep.temperature == 0.1 and aanroep.model_gevraagd == "m"


# ------------------------------------------------------------------ secrets


def test_scrubber_verwijdert_patronen_en_exacte_sleutel(tmp_path, caplog):
    scrub = proef.Scrubber()
    scrub.registreer("geheim-zonder-patroon-123")
    tekst = "a sk-ant-api03-abcdefghijklmnop b geheim-zonder-patroon-123 c"
    uit = scrub(tekst)
    assert "sk-ant" not in uit and "geheim-zonder" not in uit
    assert uit.count("[REDACTED]") == 2

    proef.SCRUB.registreer("nog-een-geheim-456")
    pad = tmp_path / "x.json"
    proef.schrijf_json(pad, {"k": "nog-een-geheim-456 sk-abcdefghijklmnop"})
    assert "geheim" not in pad.read_text(encoding="utf-8")
    record = logging.LogRecord(
        "x", logging.INFO, "p", 1, "key=%s", ("nog-een-geheim-456",), None
    )
    proef._ScrubFilter().filter(record)
    assert "geheim" not in record.getMessage()


# ------------------------------------------------------------ offline e2e


def _basis_beschikbaar() -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(REPO), "cat-file", "-e", f"{proef.BASIS_REF}^{{commit}}"],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


@pytest.mark.slow
@pytest.mark.skipif(not _basis_beschikbaar(), reason="basiscommit niet in deze clone")
def test_offline_proef_bouwt_beide_volledige_appprompts_zonder_modelaanroep(tmp_path):
    casussen = tmp_path / "casussen.jsonl"
    casussen.write_text(
        json.dumps(
            {
                "id": "T1",
                "begrip": "tijdige reactie",
                "organisatorische_context": ["Proefdienst"],
                "documenten": [
                    {
                        "doc_id": "t1",
                        "snippet": "Reactie binnen drie dagen na ontvangst.",
                    }
                ],
                "verwachting": "VERWACHTING-MAG-NIET-IN-DE-PROMPT",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    uit = tmp_path / "proef"
    assert proef.main(["--cases", str(casussen), "--out", str(uit)]) == 0

    manifest = json.loads((uit / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["modus"] == "offline"
    assert "live" not in manifest
    assert manifest["versies"]["basis"]["commit"] == proef.BASIS_REF
    assert manifest["modelinfo_verschillen"] == []
    assert manifest["modelinfo"]["basis"]["ai_service_cache"] is False
    basis = (uit / "prompts/basis/prompts/T1.prompt.txt").read_text(encoding="utf-8")
    nieuw = (uit / "prompts/nieuw/prompts/T1.prompt.txt").read_text(encoding="utf-8")
    # Echte volledige appprompts: basis zonder, nieuw met de DEF-821-wijziging.
    for prompt in (basis, nieuw):
        assert "### 🎯 FINALE INSTRUCTIES:" in prompt
        assert "Reactie binnen drie dagen na ontvangst." in prompt
        assert "VERWACHTING-MAG-NIET-IN-DE-PROMPT" not in prompt
    assert "Gebruik objectief toetsbare elementen" in basis
    assert G2_BEGIN not in basis and "BETEKENISGROND ONTBREEKT:" not in basis
    assert G2_BEGIN in nieuw and "BETEKENISGROND ONTBREEKT:" in nieuw
    # De basisbron is een echte git-archive-kopie, geen werkboom.
    assert (
        not (uit / "bron/basis/src/services/modelantwoord.py")
        .read_text(encoding="utf-8")
        .count("ONTBREKENDE_GROND_SENTINEL")
    )


def test_bestaande_uitvoermap_wordt_niet_overschreven(tmp_path):
    casussen = tmp_path / "c.json"
    casussen.write_text(json.dumps([_casus()]), encoding="utf-8")
    uit = tmp_path / "bestaat"
    uit.mkdir()
    with pytest.raises(SystemExit):
        proef.main(["--cases", str(casussen), "--out", str(uit)])
