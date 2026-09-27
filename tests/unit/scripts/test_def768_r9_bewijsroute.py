"""DEF-768 R9-bewijsherstel — echte R720-regressie: ongestaafde deelzin in een gevolgtrekking.

Echte R9-call (26-09, ontwikkeling R720; fixture
`tests/fixtures/ess05/r9_r720_callrecord_uittreksel_v1.json`, uit callrecord
sha256 8995634a…): automatisch geaccepteerd, maar de onafhankelijke auteur gaf
NO-GO. Claim C5 (inference, premissen C1 en C4) stelt mede dat "het gedeelde
eindpunt op de oorspronkelijke laadplaats niets afgrenst"; C1 en C4 dragen
niet dat dwarsterugloop op de oorspronkelijke laadplaats eindigt. Dat staat
wel in de bron, maar niet in de opgegeven bewijsroute. De verifier keurde C5
volledig goed ("Volgt uit C1 en C4").

Oorzaak: de verifierinstructie (`ess05-verify/2`) toetste een claim tegen
"het materiaal" en weigerde alleen een onjuiste deelzin; de antwoordinstructie
(`ess05-assess/15`) eiste niet dat elke deelzin door de eigen bewijsplaatsen of
premissen gedragen wordt. Herstel: `ess05-assess/16` en `ess05-verify/3`.

Deze tests draaien de echte runnerketen offline op het echte R720-geval en
het echte modelantwoord, met een verifierstub. Ze bewijzen de keten (een
`unsupported` op de ongestaafde deelzin blokkeert, zonder herstel of retry;
een correcte premissenketen blijft vrijgegeven; het oude document blijft
historisch) en dat de nieuwe regel in beide prompts staat. Ze bewijzen NIET
dat een echt model de regel volgt: dat vraagt een nieuwe betaalde proef.
De sluiting van R9 zelf toetst `test_def768_r9_proef.py`.

Sinds `ess05-answer/2` (assess/18) weigert de live keten het echte, platte
answer/1-antwoord (`test_def768_answer2_fixtures.py`). De ketentests voeren
daarom de synthetische answer/2-transformatie van precies dit antwoord
(`answer2_uit_r9_r720_v1.json`, geen modeluitvoer); het afgeleide concept is
het historische modulo bewijs-ID's, met dezelfde claims C1–C5. Het historische
document zelf speelt alleen af onder zijn oude binding met expliciet answer/1.
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import pytest

from domain.ess05.contract import valideer_antwoord
from services.ai.base_client import ChatResponse
from tests.fixtures.def768_fakes import (
    als_answer3,
    is_verificatievraag,
    verificatie_voor,
)
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _FakeProvider
from tests.unit.scripts.test_def768_r8_proef import _omgeving8
from tests.unit.scripts.test_def768_r9_proef import _keten9, _opslag9, _soort

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import migreer_r7_naar_v2 as mig
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

FIXTURE = json.loads(
    (ROOT / "tests/fixtures/ess05/r9_r720_callrecord_uittreksel_v1.json").read_text(
        encoding="utf-8"
    )
)
#: Het historische conceptoordeel waarvan de verifier elk item goedkeurde.
HISTORISCH_CONCEPT = "9faab46592a6aeab83589b18f689e456ab2e96c0fa7b3750e06054844e5f46cf"
#: Synthetisch getransformeerd (answer/2), geen modeluitvoer.
A2 = json.loads(
    (ROOT / "tests/fixtures/ess05/answer2_uit_r9_r720_v1.json").read_text(
        encoding="utf-8"
    )
)
#: Sinds answer/3 (R13-herstel) de synthetische answer/3-weergave van precies dit
#: antwoord (`als_answer3`): schema actueel, een top-level bronclaim verhuisd
#: naar de reden van de eerste buur; claim- en bewijs-ID's gelijk.
ANTWOORD2 = als_answer3(A2["raw_response"])


def _afgeleid_concept() -> str:
    """Hash van het concept dat de app uit ANTWOORD2 afleidt (eigen afleiding)."""
    materiaal, buren, _ = mig.verificatiemateriaal(FIXTURE["geval"])
    concept, fouten = valideer_antwoord(json.loads(ANTWOORD2), materiaal, buren)
    assert concept is not None, fouten
    return concept.hash


AFGELEID_CONCEPT = _afgeleid_concept()
_CONCEPTBLOK = re.compile(
    r'<conceptoordeel candidate_hash="([0-9a-f]{64})">\n(.*?)\n</conceptoordeel>', re.S
)


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _historische_checks(**anders: str) -> list[dict]:
    """De echte verifierchecks, met per item een andere uitkomst."""
    checks = json.loads(FIXTURE["verification_raw_response"])["checks"]
    return [
        {**c, "outcome": anders[c["item"]]} if c["item"] in anders else c
        for c in checks
    ]


class _EchteR720(_FakeProvider):
    """Stap 1: het (echte of aangepaste) R720-antwoord; stap 2: een verifierstub."""

    def __init__(self, antwoord: str, verifier) -> None:
        super().__init__()
        self.antwoord, self.verifier = antwoord, verifier
        self.stappen: list[str] = []
        self.systemen: list[str] = []

    async def chat_completion(self, messages, model, **kwargs):
        system = next(m.content for m in messages if m.role == "system")
        user = "\n".join(m.content for m in messages if m.role != "system")
        stap = "verificatie" if is_verificatievraag(user) else "beoordeling"
        self.stappen.append(stap)
        self.systemen.append(system)
        if stap == "beoordeling":
            tekst = self.antwoord
        else:
            kandidaat, blok = _CONCEPTBLOK.search(user).groups()
            tekst = json.dumps(
                self.verifier(kandidaat, json.loads(html.unescape(blok)))
            )
        self.aanroepen.append({"model": model, **kwargs})
        return ChatResponse(text=tekst, tokens_used=10, model=model)


def _historisch_oordeel(kandidaat, _concept, **anders):
    return {
        "schema_version": "ess05-verification/1",
        "candidate_hash": kandidaat,
        "checks": _historische_checks(**anders),
    }


def _draai(tmp_path: Path, provider: _EchteR720):
    """De echte T-keten, offline, op het echte R720-geval (R9-kopie, eigen tmp-opslag)."""
    pad = tmp_path / "r720.json"
    pad.write_text(json.dumps({"gevallen": [FIXTURE["geval"]]}), encoding="utf-8")
    omg = _omgeving8(provider)
    proef = dataclasses.replace(
        runner.PROEVEN["R9"],
        t_ontwikkelinvoer_sha256=hashlib.sha256(pad.read_bytes()).hexdigest(),
        contract=runner.contractidentiteit(omg),
    )
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase="ontwikkeling",
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag9(tmp_path),
            proef=proef,
            voorganger_opslag=_keten9(tmp_path),
            nieuw_grootboek=True,
        )
    )


def _callrecord(tmp_path: Path) -> dict:
    (pad,) = (tmp_path / "uit").glob("ontwikkeling-*/calls/*.json")
    return json.loads(pad.read_text(encoding="utf-8"))


def _aangepast(bewerk) -> str:
    """Het answer/2-antwoord, met een gerichte bewerking van een inline claim."""
    antwoord = json.loads(ANTWOORD2)
    bewerk(antwoord)
    return json.dumps(antwoord, ensure_ascii=False)


def _c5(antwoord: dict) -> dict:
    """C5 staat inline als tweede reden bij de tweede buur (dwarsterugloop)."""
    c5 = antwoord["neighbours"][1]["reason"][1]
    assert c5["role"] == "inference" and "gedeelde eindpunt" in c5["text"]
    return c5


class TestEchteFixture:
    def test_ongewijzigd_uit_het_callrecord(self):
        assert _sha(FIXTURE["raw_response"]) == FIXTURE["raw_response_sha256"]
        assert _sha(FIXTURE["verification_raw_response"]) == (
            FIXTURE["verification_raw_response_sha256"]
        )
        assert pi.sha_json(FIXTURE["geval"]) == FIXTURE["geval_sha256"]
        doc = FIXTURE["beoordelingsdocument"]
        assert doc["raw_response"] == FIXTURE["raw_response"]
        assert doc["verification_input"]["candidate_hash"] == HISTORISCH_CONCEPT
        assert (doc["prompt_version"], doc["verification_prompt_version"]) == (
            "ess05-assess/15",
            "ess05-verify/2",
        )

    def test_c5_draagt_een_deelzin_die_c1_en_c4_niet_dragen(self):
        concept = FIXTURE["beoordelingsdocument"]["concept"]
        claims = {c["id"]: c for c in concept["claims"]}
        c5 = claims["C5"]
        assert (c5["role"], c5["premises"]) == ("inference", ["C1", "C4"])
        assert "gedeelde eindpunt" in c5["text"]
        # Het eindpunt van dwarsterugloop staat in geen premisse en in geen
        # van hun bewijsplaatsen; wel elders in het materiaal (bron, buur).
        bewijs = {e["id"]: e["quote"] for e in concept["evidence"]}
        route = [claims["C1"]["text"], claims["C4"]["text"]] + [
            bewijs[e] for c in ("C1", "C4") for e in claims[c]["evidence"]
        ]
        assert not any(
            "dwarsterugloop" in t.lower() and "laadplaats" in t for t in route
        )
        checks = {c["item"]: c for c in _historische_checks()}
        assert checks["claim:C5"]["outcome"] == "supported"


class TestKeten:
    def test_historisch_volledig_oordeel_geeft_c5_vrij(self, tmp_path):
        """Reproductie van het defect: de keten vertrouwt het verifieroordeel;
        bij volledig supported gaat de ongestaafde deelzin mee (zoals in R9)."""
        provider = _EchteR720(ANTWOORD2, _historisch_oordeel)
        uitkomst = _draai(tmp_path, provider)
        (resultaat,) = uitkomst["resultaten"]
        assert resultaat["geaccepteerd"] is True
        record = _callrecord(tmp_path)
        assert record["beoordelingsdocument"]["verification_input"][
            "candidate_hash"
        ] == (AFGELEID_CONCEPT)

    def test_ongestaafde_deelzin_blokkeert_zonder_herstel_of_retry(self, tmp_path):
        """Wat `ess05-verify/3` vraagt: een ware maar in deze bewijsroute
        ongestaafde deelzin is unsupported; dan geen vrijgave, geen reparatie
        van het antwoord en geen tweede poging."""

        def verifier(kandidaat, concept):
            return _historisch_oordeel(
                kandidaat, concept, **{"claim:C5": "unsupported"}
            )

        provider = _EchteR720(ANTWOORD2, verifier)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _draai(tmp_path, provider)
        assert provider.stappen == ["beoordeling", "verificatie"]  # geen retry
        doc = _callrecord(tmp_path)["beoordelingsdocument"]
        assert doc["status"] == "error"
        assert doc["error"]["type"] == "semantic_verification_failed"
        assert doc["judgment"] is None
        # Geen stil herstel: exact de ruwe respons en het afgeleide concept.
        assert doc["raw_response"] == ANTWOORD2
        assert doc["verification_input"]["candidate_hash"] == AFGELEID_CONCEPT
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is False
        assert len(_soort(tmp_path, "reservering")) == 2

    def test_correcte_premissenketen_blijft_vrijgegeven(self, tmp_path):
        """Het gedeelde eindpunt met een eigen materiaalclaim als premisse."""

        eindpunt = (
            "Dwarsterugloop eindigt volgens de beschrijving op de "
            "oorspronkelijke laadplaats."
        )

        def bewerk(antwoord):
            c5 = _c5(antwoord)
            buurcitaat = c5["premises"][1]["quotes"][0]
            assert buurcitaat["material_id"] == "neighbour:model:19a4c2e48748"
            c5["premises"].append({
                "role": "material",
                "quotes": [{**buurcitaat,
                            "quote": "op de oorspronkelijke laadplaats eindigt"}],
                "text": eindpunt,
            })  # fmt: skip

        provider = _EchteR720(
            _aangepast(bewerk), lambda k, c: verificatie_voor(c, candidate_hash=k)
        )
        (resultaat,) = _draai(tmp_path, provider)["resultaten"]
        assert resultaat["geaccepteerd"] is True
        concept = _callrecord(tmp_path)["beoordelingsdocument"]["concept"]
        teksten = {c["id"]: c["text"] for c in concept["claims"]}
        gevolg = next(c for c in concept["claims"] if "gedeelde eindpunt" in c["text"])
        # De nieuwe premisse krijgt vóór de gevolgtrekking haar eigen ID.
        assert gevolg["premises"][:2] == ["C1", "C4"]
        assert teksten[gevolg["premises"][2]] == eindpunt

    def test_claim_zonder_overbodige_bijzin_blijft_vrijgegeven(self, tmp_path):
        def bewerk(antwoord):
            c5 = _c5(antwoord)
            c5["text"] = c5["text"].split(";")[0] + "."

        provider = _EchteR720(
            _aangepast(bewerk), lambda k, c: verificatie_voor(c, candidate_hash=k)
        )
        (resultaat,) = _draai(tmp_path, provider)["resultaten"]
        assert resultaat["geaccepteerd"] is True

    def test_beide_prompts_dragen_de_bewijsrouteregel(self, tmp_path):
        """Positieve promptgrens (geen gedragsbewijs): de verifier krijgt de
        premissenregel, de toetser de draag-, splits- of weglaatregel."""
        provider = _EchteR720(ANTWOORD2, _historisch_oordeel)
        _draai(tmp_path, provider)
        beoordeling, verificatie = provider.systemen
        assert "vul geen ontbrekende premisse aan" in verificatie
        assert "ook niet als de deelzin volgens het materiaal waar is" in verificatie
        assert "ongestaafde deelzin maakt de claim unsupported" in verificatie
        assert "splits de claim of laat de deelzin weg" in beoordeling
        doc = _callrecord(tmp_path)["beoordelingsdocument"]
        # Huidige code (answer/2); de R9-regels hierboven blijven erin.
        assert (doc["prompt_version"], doc["verification_prompt_version"]) == (
            "ess05-assess/19",
            "ess05-verify/4",
        )


class TestBewijsrouteVerify4:
    """Het ongewijzigde R9-concept onder `ess05-verify/4` (invoerstructuur, geen
    gedragsbewijs): de gesloten route van C5 bevat exact C1 en C4, en geen
    element van die route draagt het eindpunt van dwarsterugloop."""

    def test_route_van_c5_is_exact_haar_premissen_zonder_het_eindpunt(self):
        from domain.ess05.bewijs import Ess05Concept
        from services.validation.ess05_verification_service import (
            bouw_verificatieprompt,
        )

        concept = FIXTURE["beoordelingsdocument"]["concept"]
        _, gebruiker = bouw_verificatieprompt(
            "<materiaal/>", Ess05Concept(concept), norm={}, toetsinstructie="T."
        )
        (blok,) = re.findall(r"<bewijsroutes>\n(.*?)\n</bewijsroutes>", gebruiker, re.S)
        routes = {r["claim"]: r for r in json.loads(html.unescape(blok))}
        teksten = {c["id"]: c["text"] for c in concept["claims"]}
        c5 = routes["C5"]
        assert (c5["rol"], c5["uitspraak"]) == ("inference", teksten["C5"])
        assert c5["gesloten_bewijsroute"] == [
            {"premisse": p, "uitspraak": teksten[p]} for p in ("C1", "C4")
        ]
        assert not any(
            "dwarsterugloop" in s["uitspraak"].lower()
            and "laadplaats" in s["uitspraak"]
            for s in c5["gesloten_bewijsroute"]
        )


def _onderscheid(uitkomst) -> dict:
    (deel,) = [d for d in uitkomst.als_dict()["parts"] if d["id"] == "distinction"]
    return deel


class TestHistorischeBinding:
    def _replay(self, binding):
        from domain.ess05.contract import beoordeel_onderscheid
        from services.validation.ess05_assessment_service import laad_ess05_norm

        geval = copy.deepcopy(FIXTURE["geval"])
        projectie = pi.modelprojectie(geval)
        prompt = pi.bouw_t_prompt(projectie, laad_ess05_norm())
        return beoordeel_onderscheid(
            projectie["begrip"],
            projectie["tekst"],
            projectie.get("context") or {},
            prompt.bronnen_ruw,
            buren=prompt.buren_ruw,
            intentie=pi.intentie(projectie),
            uitgesloten_termen=projectie.get("uitgesloten_termen") or (),
            assessment=FIXTURE["beoordelingsdocument"],
            binding=binding,
        )

    def _binding(self, **anders):
        omg = _omgeving8(_FakeProvider())
        return dataclasses.replace(omg.dienst.binding(), **anders)

    def test_oude_vrijgave_geldt_alleen_onder_de_oude_binding(self):
        """Onder /15 + /2 met expliciet answer/1 speelt het historische,
        geverifieerde oordeel af; onder de huidige binding is het historisch en
        geen actueel oordeel."""
        oud = self._replay(self._binding(prompt_version="ess05-assess/15",
                                         verification_prompt_version="ess05-verify/2",
                                         answer_schema_version="ess05-answer/1"))  # fmt: skip
        deel = _onderscheid(oud)
        assert oud.status == FIXTURE["geval"]["verwacht"] == "review_required"
        assert "semantisch geverifieerd" in deel["reason"]
        # Zonder de expliciete historische antwoordversie geldt het niet.
        zonder = self._replay(self._binding(prompt_version="ess05-assess/15",
                                            verification_prompt_version="ess05-verify/2"))  # fmt: skip
        assert "afleidingsbinding wijkt af (answer_schema_version)" in (
            _onderscheid(zonder)["reason"]
        )
        huidig = self._replay(self._binding())
        deel = _onderscheid(huidig)
        assert "historisch en geldt niet als actueel oordeel" in deel["reason"]
        assert "'ess05-assess/19'" in deel["reason"]
        assert "semantisch geverifieerd" not in deel["reason"]
