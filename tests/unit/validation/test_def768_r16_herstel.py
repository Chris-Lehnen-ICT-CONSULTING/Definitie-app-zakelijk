"""DEF-768 — R16-herstel (`ess05-bewijsregels/4`): regressie op de bewaarde R16-antwoorden.

Grondslag: logs/def768/bewijsregels-r16-uitvoerreview-result-v1.md. Twee strikt
gescheiden soorten invoer:

- **Historisch, ongewijzigd**: de ruwe interpretaties uit de R16-callrecords
  (reports/, git-ignored; sha256-gepind). Onder v4/v5 blijven zij ongeldig, nu al in
  de geldigheidsfase (één aanroep, geen controle). De vastgelegde v3-uitslagen
  zelf veranderen niet.
- **Synthetisch gecorrigeerd**: dezelfde ruwe interpretaties waarin alleen elk
  broncitaat is vervangen door de benoemde, unieke passage van zijn eigen
  onderwerp ('Uitleen: …' / 'Verhuur: …'). Toestand, context, kern en
  buurcitaten blijven van het model. Dit is geen modeluitvoer.

De controles zijn gestubd (vaste of semantisch gestubde uitkomst): dit bewijst
de deterministische keten en wat de controle te zien krijgt, geen modelgedrag.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from domain.ess05 import bewijsregels as br
from domain.ess05.lokale_controle import OMVANG_VOLLEDIG
from services.validation import ess05_bewijsregel_service as bs
from tests.unit.domain import test_def768_bewijsregels as dt
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT
from tests.unit.validation.test_def768_bewijsregel_service import _beoordeel, _SpyAI

pytestmark = [pytest.mark.unit]

RUN = (
    ROOT / "reports" / "DEF-768-AI-20260928-R16" / "bewijsregels-20260928T103927398796Z"
)
RECORDS = {
    "A": ("001-bewijsregels-A.json",
          "eeb5faf59f35d959e3a0d4b991ea7a26636fd54512e533e35581b7e46e9952db"),
    "B": ("002-bewijsregels-B.json",
          "0991876ae1283261d410157bc31b3a747446478460ef48b0da724b16c357ced4"),
    "C": ("003-bewijsregels-C.json",
          "5613099372ae1bd158e65a1f1a0a9f6fde074bf94dd1e5af52cd2837c2564b0a"),
}  # fmt: skip
records_nodig = pytest.mark.skipif(
    not all((RUN / "calls" / naam).is_file() for naam, _ in RECORDS.values()),
    reason="git-ignored R16-callrecords ontbreken",
)

BRON_ID = "source:doc:testwerkinstructie-apparatuuruitgifte"
BUUR_ID = "gebruiker:0ddba46dcf07"
BUUR_MAT = f"neighbour:{BUUR_ID}"
INLEIDING = (
    "Lokale testwerkinstructie van de Servicedesk ICT-middelen, alleen voor deze "
    "beoordelingstest. "
)
CONTEXT = "organisatorische_context: Servicedesk ICT-middelen"
#: De materiaalhashes uit reports/.../bewijsregel-invoer-v1.json (A = B; C eigen).
MATERIAAL_SHA256 = {
    "A": {
        "definition": "61c911d84edb152d216fe4e59276388d599749c2fa65f6bc1d47e484056d7bf8",
        "context": "31ee14875b445404834ff425a72528a059a74ad886a1a836cc49ba91d2428541",
        BRON_ID: "34e4a72fbe45b066a80891bb0d445f6c0e21c843003ad1c4636a17a1d3857eb6",
        BUUR_MAT: "d7d7622a15425771dfc6d6376fbd6b94eec0e68358cd14104a073f80c21496eb",
    },
    "C": {
        "definition": "61c911d84edb152d216fe4e59276388d599749c2fa65f6bc1d47e484056d7bf8",
        "context": "31ee14875b445404834ff425a72528a059a74ad886a1a836cc49ba91d2428541",
        BRON_ID: "e73046ee5374bf41cab467034453575837236a9b6095df787cea93169686332a",
        BUUR_MAT: "3206e9a4ee388139975fa8302b3031f3a7ee886859b4a1b88f4e65c9adb92da6",
    },
}
UITLEEN = (
    "Uitleen: de servicedesk stelt apparatuur tijdelijk en kosteloos ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug."
)
VERHUUR = {
    "A": (
        "Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking aan een "
        "medewerker; de medewerker geeft de apparatuur daarna terug."
    ),
    "C": (
        "Verhuur: de servicedesk stelt apparatuur permanent ter beschikking aan een "
        "medewerker."
    ),
}


def _materiaal(naam: str) -> dict[str, str]:
    c = naam == "C"
    return {
        "definition": dt.DEFINITIE,
        "context": CONTEXT,
        BRON_ID: INLEIDING + (dt.BRON_C if c else dt.BRON_A),
        BUUR_MAT: dt.BUUR_C if c else dt.BUUR_A,
    }


def _invoer(naam: str) -> br.Vergelijkingsinvoer:
    return br.Vergelijkingsinvoer(
        term="uitleen",
        materiaal=_materiaal(naam),
        buren=((BUUR_ID, "verhuur"),),
        onvolledig=frozenset({BRON_ID} if naam == "B" else ()),
    )


def _historisch(naam: str) -> dict:
    """De ongewijzigde ruwe R16-interpretatie, na sha256-controle van het record."""
    bestand, sha = RECORDS[naam]
    data = (RUN / "calls" / bestand).read_bytes()
    assert hashlib.sha256(data).hexdigest() == sha
    return json.loads(data)["interpretatie"]["ruw"]


def _gecorrigeerd(naam: str) -> dict:
    """SYNTHETISCH: alleen elk broncitaat → de benoemde passage van zijn onderwerp.

    v6: plus schema /3, omdat de tests de citaten daarna met `naar_eenheden`
    naar eenheden omzetten (het historische record zelf blijft schema /2).
    """
    ruw = copy.deepcopy(_historisch(naam))
    ruw["schema_version"] = br.INTERPRETATIESCHEMA
    passage = {"doel": UITLEEN, BUUR_ID: VERHUUR["C" if naam == "C" else "A"]}
    for a in ruw["antwoorden"]:
        for c in a["citaten"]:
            if c["material_id"] == BRON_ID:
                c["citaat"] = passage[a["onderwerp"]]
    return ruw


def _aspect(uitkomst, kenmerk):
    return next(a for a in uitkomst.buren[0].aspecten if a.kenmerk == kenmerk)


class TestMateriaal:
    @pytest.mark.parametrize("naam", ["A", "C"])
    def test_reconstructie_is_het_echte_r16_materiaal(self, naam):
        assert {
            m: hashlib.sha256(t.encode("utf-8")).hexdigest()
            for m, t in _materiaal(naam).items()
        } == MATERIAAL_SHA256[naam]


@records_nodig
class TestHistorischOngewijzigd:
    """De echte R16-antwoorden blijven ongeldig; nu vóór elke controle."""

    @pytest.mark.parametrize("naam", ["A", "B", "C"])
    def test_historisch_antwoord_is_error_na_een_aanroep(self, naam):
        # v6: het historische antwoord (schema /2) is onder schema /3 een
        # schemafout; nog steeds één aanroep en geen enkele controle.
        ai = _SpyAI(_historisch(naam))
        resultaat = _beoordeel(ai, _invoer(naam))
        assert (resultaat.uitkomst, resultaat.fout.soort) == ("error", "schemafout")
        assert len(ai.aanroepen) == 1 and resultaat.controles == ()

    # v6: test_c_losse_teruggaafzin_zonder_uitleen_is_onderwerpfout vervalt; een
    # eenheid zonder begripsnaam gaat door naar de controle, gedekt door
    # test_def768_bewijseenheden.py::TestOnderwerp::
    # test_eenheid_zonder_begripsnaam_gaat_door_naar_de_controle.


@records_nodig
class TestSynthetischGecorrigeerd:
    """SYNTHETISCH gecorrigeerde binding; controles gestubd op supported."""

    def test_a_open_na_vier_aanroepen(self):
        ai = _SpyAI(dt.naar_eenheden(_gecorrigeerd("A"), _invoer("A")))
        resultaat = _beoordeel(ai, _invoer("A"))
        assert (resultaat.uitkomst, resultaat.fout) == ("review_required", None)
        assert len(ai.aanroepen) == 4
        assert (_aspect(resultaat.regels, "kosten").aspect,
                _aspect(resultaat.regels, "kosten").reden) == ("onbeslist", "onbekend")  # fmt: skip

    # v6: test_a_herhaald_kort_citaat_blijft_citaatfout vervalt; eenheden zijn
    # uniek door nummering, gedekt door test_def768_bewijseenheden.py::
    # TestEenheden::test_herhaalde_tekst_in_twee_zinnen_is_niet_dubbelzinnig.

    def test_verhuurteruggave_is_geen_uitleenbewijs(self):
        ruw = _gecorrigeerd("A")
        k4 = next(a for a in ruw["antwoorden"]
                  if (a["kenmerk_id"], a["onderwerp"]) == ("K4", "doel"))  # fmt: skip
        k4["citaten"] = [{"material_id": BRON_ID, "citaat": VERHUUR["A"]}]
        fout = br.bepaal(dt.naar_eenheden(ruw, _invoer("A")), _invoer("A")).fout
        assert fout.soort == "onderwerpfout" and "verhuur" in fout.melding

    def test_b_blijft_dekking_ontbreekt_nadat_de_binding_klopt(self):
        ai = _SpyAI(dt.naar_eenheden(_gecorrigeerd("B"), _invoer("B")))
        resultaat = _beoordeel(ai, _invoer("B"))
        assert (resultaat.uitkomst, resultaat.fout.soort) == (
            "error",
            "dekking_ontbreekt",
        )
        assert len(ai.aanroepen) == 1

    def test_c_pass_en_onbekende_teruggave_blijft_onbekend(self):
        ai = _SpyAI(dt.naar_eenheden(_gecorrigeerd("C"), _invoer("C")))
        resultaat = _beoordeel(ai, _invoer("C"))
        assert resultaat.uitkomst == "pass" and len(ai.aanroepen) == 4
        teruggave = _aspect(resultaat.regels, "teruggave")
        assert (teruggave.aspect, teruggave.reden) == ("onbeslist", "onbekend")

    def test_c_doelpakket_draagt_volledige_lokale_bron_en_context(self):
        invoer = _invoer("C")
        interpretatie = br.valideer_interpretatie(
            dt.naar_eenheden(_gecorrigeerd("C"), invoer), invoer
        )
        eenheden = {e.naam: e for e in br.controle_eenheden(interpretatie, invoer)}
        doel = eenheden["doel"].pakket.inhoud
        volledig = {
            c["citaat"] for c in doel["citaten"] if c["omvang"] == OMVANG_VOLLEDIG
        }
        assert {invoer.materiaal[BRON_ID], CONTEXT} <= volledig
        assert "alleen voor deze beoordelingstest" in invoer.materiaal[BRON_ID]
        assert "voor elk geval" not in doel["uitspraak"]
        assert "voor uitleen geldt teruggave" in doel["uitspraak"]


class TestBepalingTegenoverVoorval:
    """Wat de doelcontrole krijgt bij een bepaling, een voorval of een voorwaarde.

    De controle is hier SEMANTISCH GESTUBD (weigert een voorval of voorwaardelijke
    afspraak in het volledige materiaal); dat het echte model zo oordeelt, is
    niet bewezen. Deterministisch bewezen: het pakket bevat de volledige passage
    plus de eis 'bepaling, geen enkel voorval en geen voorwaardelijke afspraak',
    en een weigering stopt de beoordeling vóór de regels.
    """

    BEPALING = dt.BRON_A
    VOORVAL = (
        "Uitleen: gisteren stelde de servicedesk een laptop tijdelijk en kosteloos ter "
        "beschikking aan een medewerker; de medewerker gaf de laptop daarna terug. "
        "Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking aan een "
        "medewerker; de medewerker geeft de apparatuur daarna terug."
    )
    VOORWAARDE = (
        "Uitleen: bij storing stelt de servicedesk apparatuur tijdelijk en kosteloos ter "
        "beschikking aan een medewerker; de medewerker geeft de apparatuur daarna "
        "terug. Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking aan "
        "een medewerker; de medewerker geeft de apparatuur daarna terug."
    )

    @staticmethod
    def _ruw(bron: str) -> dict:
        passage = bron.split(" Verhuur:", 1)[0]
        ruw = copy.deepcopy(dt._interpretatie_a())
        for a in ruw["antwoorden"]:
            if a["onderwerp"] == "doel":
                a["citaten"] = [{"material_id": dt.BRON, "citaat": passage}]
        return ruw

    @staticmethod
    def _stub(pakketten: list[str]):
        def controle(_naam: str) -> str:
            # Volgorde kern, doel, buur: de doelcontrole is de derde aanroep.
            tekst = pakketten[-1]
            doel = len(pakketten) == 3
            if doel and ("gisteren" in tekst or "bij storing" in tekst):
                return "unsupported"
            return "supported"

        return controle

    @pytest.mark.parametrize(
        ("bron", "uitkomst"),
        [("BEPALING", "review_required"), ("VOORVAL", "error"),
         ("VOORWAARDE", "error")],
    )  # fmt: skip
    def test_doelcontrole_krijgt_passage_en_bepalingseis(self, bron, uitkomst):
        tekst = getattr(self, bron)
        pakketten: list[str] = []
        ai = _SpyAI(
            dt.naar_eenheden(self._ruw(tekst), dt._invoer(tekst)),
            controle=self._stub(pakketten),
        )
        origineel = ai.generate_definition

        async def spy(**kwargs):
            pakketten.append(kwargs["prompt"])
            return await origineel(**kwargs)

        ai.generate_definition = spy
        resultaat = _beoordeel(ai, dt._invoer(tekst))
        assert resultaat.uitkomst == uitkomst
        doel = pakketten[2]
        assert tekst in doel  # volledige bron, niet alleen het fragment
        assert "geen enkel voorval en geen voorwaardelijke afspraak" in doel
        assert "elk geval" not in doel.split("Volgens de citaten:", 1)[-1]
        if uitkomst == "error":
            assert resultaat.fout.soort == "semantische_controle_mislukt"
            assert len(pakketten) == 3


class TestInterpretatieprompt:
    def test_promptversie_en_regelversie_opgehoogd(self):
        identiteit = bs.Ess05BewijsregelService.contractidentiteit()
        assert identiteit["interpretation_prompt_version"] == (
            "ess05-interpretatie-prompt/5"
        )
        assert identiteit["bewijsregel_version"] == "ess05-bewijsregels/7"
        assert identiteit["interpretation_schema_version"] == "ess05-interpretatie/3"
        assert identiteit["render_version"] == "ess05-bewijsregels-render/2"

    def test_prompt_vraagt_eenheden_en_bepaling(self):
        # v6 (prompt /4): bewijs via eenheden in plaats van een benoemde, unieke
        # passage; de dubbelzinnige zin 'precies één keer' is weg (R17).
        prompt = bs.interpretatiesysteemprompt()
        assert "precies één keer" not in prompt
        assert "genummerde eenheden [U1], [U2]" in prompt
        assert "bepaling" in prompt
        assert "een enkel voorval of een voorwaardelijke afspraak is geen bepaling" in (
            prompt
        )
        assert "(het kenmerk geldt voor elk geval van dat onderwerp)" not in prompt
        # R16-H-01: geen verbod op een tweede begripsnaam; v6: negatief anker.
        assert "zonder de naam van een ander begrip" not in prompt
        assert "een eenheid die alleen een ander begrip noemt is geen bewijs" in prompt
