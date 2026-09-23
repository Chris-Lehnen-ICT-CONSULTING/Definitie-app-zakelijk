"""DEF-821 correctieronde 1 — twee door de Codex-review gereproduceerde fouten.

1. Een beschadigde gereserveerde meldingskop (zonder dubbele punt, spatie
   vóór de dubbele punt, underscore, opmaak eromheen) of een kale
   meldingspayload zonder kop werd als definitie opgeschoond, getoetst en
   opgeslagen. Nu: veilig ongeldig vóór het definitiepad, nul opslag, geen
   ruwe modeltekst in response of log. Gewone definities waarin dezelfde
   woorden midden in een zin staan, blijven definities.
2. Opeenvolgende verduidelijkingsvragen bij dezelfde invoer verloren eerdere
   antwoorden: prompt 3 droeg alleen het laatste antwoord. Nu: de expliciet
   verzonden antwoorden vormen één invoergebonden keten (met de vraag van
   het model als context) die volledig meegaat zolang de invoer gelijk
   blijft, begrensd is, bij invoerwijziging als geheel vervalt en in de tab
   zichtbaar is.

Echte handler → ServiceAdapter → orchestrator → PromptServiceV2 →
DefinitionRepository op een tijdelijke SQLite; alleen het model is een
script (geen netwerk). Niets hier claimt modelkwaliteit.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from database.definitie_repository import DefinitieRepository
from services.interfaces import AIGenerationResult
from services.modelantwoord import (
    FOUTCODES,
    SOORT_DEFINITIE,
    SOORT_ONGELDIG,
    lees_modelantwoord,
)
from tests.unit.ui.handlers.test_def751_betekenisconflict_handler import FakeSM
from tests.unit.ui.test_def821_ontbrekende_grond_ui import (
    BEGRIP,
    CONTEXT,
    _aantal,
    _genereer,
    _keten,
)
from toetsregels.rule_cache import get_rule_cache
from ui.helpers.betekenisconflict import (
    KEY_AFWIJZING,
    KEY_KETEN,
    KEY_OPEN,
    KEY_VERZONDEN,
    MAX_KETEN_ANTWOORDEN,
    verduidelijking_uit_keten,
    verzend_verduidelijking,
)

pytestmark = [pytest.mark.unit]

PAYLOAD = json.dumps(
    {"ontbrekende_grond": "dagconventie", "vraag": "Werkdagen of kalenderdagen?"}
)
CONFLICTPAYLOAD = json.dumps(
    {
        "vraag": "Activiteit of uitkomst?",
        "lezingen": [
            {"lezing": "a", "bron": "context: Proefdienst", "grond": "x"},
            {"lezing": "b", "bron": "context: Proefdienst", "grond": "y"},
        ],
    }
)


@pytest.fixture(autouse=True)
def _verse_regelcache():
    get_rule_cache().clear_cache()


# ------------------------------------------------ 1. beschadigde meldingskop


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        # De gereproduceerde vorm: kop zonder dubbele punt, payload eronder.
        (f"BETEKENISGROND ONTBREEKT\n{PAYLOAD}", "sentinel_beschadigd"),
        (f"BETEKENISGROND ONTBREEKT {PAYLOAD}", "sentinel_beschadigd"),
        (f"BETEKENISGROND ONTBREEKT : {PAYLOAD}", "sentinel_beschadigd"),
        (f"Betekenisgrond ontbreekt - {PAYLOAD}", "sentinel_beschadigd"),
        (f"BETEKENISGROND_ONTBREEKT: {PAYLOAD}", "sentinel_beschadigd"),
        (f"**BETEKENISGROND ONTBREEKT**\n{PAYLOAD}", "sentinel_beschadigd"),
        (f"## BETEKENISGROND ONTBREEKT\n{PAYLOAD}", "sentinel_beschadigd"),
        ("BETEKENISGROND ONTBREEKT", "sentinel_beschadigd"),
        # Ook de ESS-02-kop.
        (f"VERDUIDELIJKING NODIG\n{CONFLICTPAYLOAD}", "sentinel_beschadigd"),
        (f"Verduidelijking nodig : {CONFLICTPAYLOAD}", "sentinel_beschadigd"),
        # Kale payload zonder kop (met of zonder fence).
        (PAYLOAD, "payload_zonder_sentinel"),
        (f"```json\n{PAYLOAD}\n```", "payload_zonder_sentinel"),
        (CONFLICTPAYLOAD, "payload_zonder_sentinel"),
    ],
)
def test_beschadigde_kop_of_kale_payload_is_ongeldig(raw, code):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_ONGELDIG
    assert antwoord.code == code
    assert antwoord.reden == FOUTCODES[code]
    assert "dagconventie" not in antwoord.reden


@pytest.mark.parametrize(
    "raw",
    [
        "Toelichting die een verduidelijking nodig maakt bij een onduidelijke tekst",
        "Grond waarop een betekenis steunt; zonder die grond ontbreekt de betekenis",
        "Verduidelijking die nodig is om een regel toe te passen",
        "Uitnodiging die de verduidelijking nodigt tot reactie",
        "Partij waarvan de betekenisgrond ontbreekt in het register",
        "Reactie binnen drie werkdagen na de dag van ontvangst",
    ],
)
def test_gewone_definities_met_dezelfde_woorden_blijven_definitie(raw):
    antwoord = lees_modelantwoord(raw)
    assert antwoord.soort == SOORT_DEFINITIE
    assert antwoord.tekst is raw


class ScriptModel:
    """Levert per aanroep het volgende antwoord uit een vaste lijst."""

    def __init__(self, *antwoorden: str) -> None:
        self.antwoorden = list(antwoorden)
        self.prompts: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs) -> AIGenerationResult:
        self.prompts.append(prompt)
        return AIGenerationResult(
            text=self.antwoorden.pop(0),
            model="fake",
            tokens_used=1,
            generation_time=0.0,
        )


def test_keten_beschadigde_kop_wordt_niet_opgeschoond_getoetst_of_opgeslagen(
    tmp_path, monkeypatch, caplog
):
    """Codex-repro: handler + orchestrator + opschoning + tijdelijke SQLite."""
    db_path = str(tmp_path / "beschadigd.db")
    model = ScriptModel(f"BETEKENISGROND ONTBREEKT\n{PAYLOAD}")
    handler, _, validation, cleaning = _keten(db_path, monkeypatch, model)
    sm = FakeSM()
    st = MagicMock()
    with caplog.at_level(logging.DEBUG):
        _genereer(handler, sm, st)

    agent = sm.data["last_generation_result"]["agent_result"]
    assert agent["success"] is False
    assert agent.get("error_type") == "modelantwoord_ongeldig"
    assert sm.data["last_generation_result"]["saved_definition_id"] is None
    assert _aantal(db_path) == 0
    assert not cleaning.clean_text.called
    assert not validation.validate_definition.called
    assert not st.success.called and st.error.called
    assert KEY_OPEN not in sm.data
    # Geen ruwe modeltekst in UI-resultaat of log.
    assert "dagconventie" not in json.dumps(agent, default=str)
    assert "dagconventie" not in caplog.text


# ------------------------------------------ 2. keten van verduidelijkingen


VRAAG_1 = "Tellen de drie dagen als werkdagen of als kalenderdagen?"
VRAAG_2 = "Telt de dag van ontvangst mee?"
ANTWOORD_1 = "Werkdagen"
ANTWOORD_2 = "De ontvangstdag telt niet mee"
DEFINITIE = (
    "Reactie die uiterlijk op de derde werkdag na de dag van ontvangst wordt gegeven"
)


def _melding(grond: str, vraag: str) -> str:
    return "BETEKENISGROND ONTBREEKT: " + json.dumps(
        {"ontbrekende_grond": grond, "vraag": vraag}, ensure_ascii=False
    )


def _contextblok(prompt: str) -> str:
    return prompt.split("<context>", 1)[1].split("</context>", 1)[0]


class KetenModel:
    """Vraagt eerst de dagconventie, dan het startmoment, en definieert pas
    als beide antwoorden als DATA in het contextblok staan."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate_definition(self, prompt: str, **kwargs) -> AIGenerationResult:
        self.prompts.append(prompt)
        blok = _contextblok(prompt)
        if ANTWOORD_1 not in blok:
            tekst = _melding("dagconventie", VRAAG_1)
        elif ANTWOORD_2 not in blok:
            tekst = _melding("startmoment", VRAAG_2)
        else:
            tekst = DEFINITIE
        return AIGenerationResult(
            text=tekst, model="fake", tokens_used=1, generation_time=0.0
        )


def _beantwoord(sm: FakeSM, antwoord: str) -> None:
    assert verzend_verduidelijking(sm, sm.data[KEY_OPEN], antwoord) is None


def test_twee_opeenvolgende_vragen_behouden_beide_antwoorden(tmp_path, monkeypatch):
    db_path = str(tmp_path / "keten.db")
    model = KetenModel()
    handler, *_ = _keten(db_path, monkeypatch, model)
    sm = FakeSM()

    _genereer(handler, sm)  # vraag 1
    assert sm.data[KEY_OPEN]["vraag"] == VRAAG_1
    _beantwoord(sm, ANTWOORD_1)
    _genereer(handler, sm)  # vraag 2, met antwoord 1
    assert sm.data[KEY_OPEN]["vraag"] == VRAAG_2
    assert ANTWOORD_1 in _contextblok(model.prompts[1])
    _beantwoord(sm, ANTWOORD_2)
    st = MagicMock()
    _genereer(handler, sm, st)  # definitie, met beide antwoorden

    derde = _contextblok(model.prompts[2])
    assert ANTWOORD_1 in derde and ANTWOORD_2 in derde
    # Herkenbaar met de vraag van het model als context, niet als bron.
    assert VRAAG_1 in derde and VRAAG_2 in derde
    assert derde.index(ANTWOORD_1) < derde.index(ANTWOORD_2)
    assert '<bron nr="1"' not in model.prompts[2], "antwoorden zijn geen bron"
    assert st.success.called
    # Keten afgesloten na de definitie; opgeslagen met beide antwoorden.
    assert KEY_KETEN not in sm.data and KEY_OPEN not in sm.data
    did = sm.data["last_generation_result"]["saved_definition_id"]
    registratie = (
        DefinitieRepository(db_path).get_definitie(did).get_generatieregistratie()
    )
    assert ANTWOORD_1 in registratie["betekenisverduidelijking"]
    assert ANTWOORD_2 in registratie["betekenisverduidelijking"]
    assert _aantal(db_path) == 1


def test_hergenereren_zonder_nieuw_antwoord_houdt_de_keten(tmp_path, monkeypatch):
    db_path = str(tmp_path / "keten-rerun.db")
    model = KetenModel()
    handler, *_ = _keten(db_path, monkeypatch, model)
    sm = FakeSM()
    _genereer(handler, sm)
    _beantwoord(sm, ANTWOORD_1)
    _genereer(handler, sm)  # vraag 2
    _genereer(handler, sm)  # opnieuw, zonder antwoord op vraag 2
    assert ANTWOORD_1 in _contextblok(model.prompts[2])
    assert sm.data[KEY_OPEN]["vraag"] == VRAAG_2
    assert [a["antwoord"] for a in sm.data[KEY_KETEN]["antwoorden"]] == [ANTWOORD_1]


def test_invoerwijziging_laat_de_hele_keten_vervallen(tmp_path, monkeypatch):
    db_path = str(tmp_path / "keten-wijziging.db")
    model = KetenModel()
    handler, *_ = _keten(db_path, monkeypatch, model)
    sm = FakeSM()
    _genereer(handler, sm)
    _beantwoord(sm, ANTWOORD_1)
    _genereer(handler, sm)  # vraag 2; keten = [antwoord 1]
    _beantwoord(sm, ANTWOORD_2)
    st = MagicMock()
    _genereer(
        handler,
        sm,
        st,
        context={**CONTEXT, "organisatorische_context": ["Andere dienst"]},
    )
    derde = model.prompts[2]
    assert ANTWOORD_1 not in derde and ANTWOORD_2 not in derde
    assert st.info.called
    meldingen = " ".join(str(c) for c in st.info.call_args_list)
    assert "niet toegepast" in meldingen
    assert sm.data[KEY_OPEN]["vraag"] == VRAAG_1
    assert sm.data.get(KEY_KETEN, {}).get("antwoorden", []) == []
    assert _aantal(db_path) == 0


def test_te_lange_keten_wordt_voor_het_model_geweigerd_zonder_verlies(
    tmp_path, monkeypatch
):
    """Budget ná escaping (orchestrator): geen stil afkappen, geen modelaanroep,
    verzonden antwoord en keten blijven staan."""
    db_path = str(tmp_path / "keten-lang.db")
    lang = "werkdag " * 300  # ~2400 tekens
    model = ScriptModel(_melding("a", "Vraag 1?"), _melding("b", "Vraag 2?"))
    handler, *_ = _keten(db_path, monkeypatch, model)
    sm = FakeSM()
    _genereer(handler, sm)
    _beantwoord(sm, lang)
    _genereer(handler, sm)  # keten = [lang]; model vraagt opnieuw
    _beantwoord(sm, lang + "extra")
    verzonden = dict(sm.data[KEY_VERZONDEN])
    keten = json.loads(json.dumps(sm.data[KEY_KETEN]))
    st = MagicMock()
    _genereer(handler, sm, st)

    assert len(model.prompts) == 2, "geen modelaanroep voor de te lange keten"
    assert sm.data[KEY_VERZONDEN] == verzonden
    assert sm.data[KEY_KETEN] == keten
    assert "te lang" in sm.data[KEY_AFWIJZING]
    assert st.error.called


def test_keten_is_begrensd_op_aantal_antwoorden(tmp_path, monkeypatch):
    db_path = str(tmp_path / "keten-max.db")
    meldingen = [_melding("g", f"Vraag {i}?") for i in range(MAX_KETEN_ANTWOORDEN + 1)]
    model = ScriptModel(*meldingen)
    handler, *_ = _keten(db_path, monkeypatch, model)
    sm = FakeSM()
    _genereer(handler, sm)
    for i in range(MAX_KETEN_ANTWOORDEN):
        _beantwoord(sm, f"antwoord {i}")
        _genereer(handler, sm)
    assert len(sm.data[KEY_KETEN]["antwoorden"]) == MAX_KETEN_ANTWOORDEN
    _beantwoord(sm, "nog een antwoord")
    st = MagicMock()
    aanroepen = len(model.prompts)
    _genereer(handler, sm, st)
    assert len(model.prompts) == aanroepen, "boven de grens geen modelaanroep"
    assert str(MAX_KETEN_ANTWOORDEN) in sm.data[KEY_AFWIJZING]
    assert KEY_VERZONDEN in sm.data
    assert st.error.called


async def test_prompt_legt_uit_dat_vragen_context_zijn_en_antwoorden_gelden():
    from services.interfaces import GenerationRequest
    from services.prompts.prompt_service_v2 import PromptServiceV2

    request = GenerationRequest(
        id="def821-cr1",
        begrip=BEGRIP,
        organisatorische_context=["Proefdienst"],
        actor="test",
        betekenisverduidelijking=verduidelijking_uit_keten(
            [{"vraag": VRAAG_1, "antwoord": ANTWOORD_1}]
        ),
    )
    prompt = (await PromptServiceV2().build_generation_prompt(request)).text
    assert "alle antwoorden gelden samen" in prompt
    assert "de vragen zijn alleen context en geen gegeven" in prompt
    # De vraag staat alleen als DATA in het contextblok, niet als bron.
    assert prompt.count(VRAAG_1) == 1 and VRAAG_1 in _contextblok(prompt)


def test_ketentekst_draagt_vraag_en_antwoord_per_stap():
    tekst = verduidelijking_uit_keten(
        [
            {"vraag": VRAAG_1, "antwoord": ANTWOORD_1},
            {"vraag": VRAAG_2, "antwoord": ANTWOORD_2},
        ]
    )
    assert tekst.index(VRAAG_1) < tekst.index(ANTWOORD_1) < tekst.index(VRAAG_2)
    assert tekst.index(VRAAG_2) < tekst.index(ANTWOORD_2)
    assert "(1)" in tekst and "(2)" in tekst
    assert "\n" not in tekst


# ---------------------------------------------------------- tab-weergave


def test_tab_toont_de_keten_die_wordt_meegestuurd_als_platte_tekst():
    from tests.unit.ui.test_def821_ontbrekende_grond_ui import (
        INJECTIE,
        TabSM,
        _args,
        _tab,
        open_verzoek,
        tab_resultaat,
    )
    from ui.components import definition_generator_tab as module

    TabSM.data = {
        KEY_OPEN: open_verzoek(),
        KEY_KETEN: {
            "vingerafdruk": "vf-1",
            "antwoorden": [{"vraag": INJECTIE, "antwoord": ANTWOORD_1}],
        },
    }
    st = MagicMock()
    st.button.return_value = False
    tab = _tab()
    from unittest.mock import patch

    with (
        patch.object(module, "st", st),
        patch.object(module, "SessionStateManager", TabSM),
    ):
        tab._render_generation_results(tab_resultaat())
    platte_tekst = " ".join(_args(st, ("text",)))
    assert ANTWOORD_1 in platte_tekst and INJECTIE in platte_tekst
    opgemaakt = " ".join(_args(st, ("caption", "info", "markdown", "warning")))
    assert "meegestuurd" in opgemaakt
    assert "onerror" not in opgemaakt
