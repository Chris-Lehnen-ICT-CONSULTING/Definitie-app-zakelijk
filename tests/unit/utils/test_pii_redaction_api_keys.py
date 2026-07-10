"""De PII-filter moet álle gangbare API-key-formaten redigeren (DEF-583).

De regel was `sk-[A-Za-z0-9]{16,}`: die eist 16+ alfanumerieke tekens direct ná
`sk-`. De moderne formaten breken dat meteen af met een streepje:

    sk-proj-...      (OpenAI project-key)   -> "proj" is 4 tekens, dan "-"
    sk-ant-api03-... (Anthropic)            -> "ant" is 3 tekens, dan "-"

Beide glipten dus ongeredigeerd door. Anthropic is de default provider van deze
app, dus dat was de sleutel die in productie in een traceback kon belanden.

**Testkeys isoleren regel 1.** De sleutels hieronder bevatten bewust géén
alfanumerieke reeks van 32+ tekens: anders vangt de base64-regel ze óók, en dan
slaagt de test ook op de ongefixte code — die bewijst dan niets. Geverifieerd:
elk van deze sleutels wordt uitsluitend door de `sk-`-regel gevangen.

Alle keys zijn verzonnen testwaarden.
"""

import pytest

pytestmark = pytest.mark.unit

from utils.logging_filters import REDACTED, _redact_text

# Geen 32+ alfanumerieke run -> alleen regel 1 kan ze vangen.
_OUDE_OPENAI_KEY = "sk-Fk3nQ7pR2sT8vW1xY5zA0bC4dE"
_PROJECT_OPENAI_KEY = "sk-proj-Fk3nQ7pR2sT8vW1xY5zA_bC4dE6fG8hJ-kL2mN4pQrS6tU8vW"
_ANTHROPIC_KEY = "sk-ant-api03-Fk3nQ7pR2sT8vW1xY5zA_bC4dE6fG8hJ-kL2mN4pQrS6tU8vW"

_ALLE_KEYS = [
    ("oud openai", _OUDE_OPENAI_KEY),
    ("openai project", _PROJECT_OPENAI_KEY),
    ("anthropic", _ANTHROPIC_KEY),
]


@pytest.mark.parametrize(("naam", "sleutel"), _ALLE_KEYS)
def test_api_keys_worden_volledig_geredigeerd(naam, sleutel):
    """Volledig, niet gedeeltelijk.

    Voorheen leverde `_mask_token` `sk***vW8t`: prefix plus de laatste vier
    tekens van het secret. Een assertie `sleutel not in resultaat` slaagt dan
    óók bij een lek van 32 tekens sleutelmateriaal.
    """
    resultaat = _redact_text(sleutel)
    assert resultaat == REDACTED, f"{naam}-key niet volledig geredigeerd"


@pytest.mark.parametrize(("naam", "sleutel"), _ALLE_KEYS)
def test_geen_staart_van_de_sleutel_lekt(naam, sleutel):
    """Regressie-guard op het maskeringsniveau.

    Zonder deze assertie zou een verruiming van de maskering (bv. de laatste 32
    tekens tonen) door geen enkele test betrapt worden.
    """
    resultaat = _redact_text(sleutel)
    assert sleutel[-8:] not in resultaat


@pytest.mark.parametrize(("naam", "sleutel"), _ALLE_KEYS)
def test_api_keys_in_een_logregel(naam, sleutel):
    regel = f"AI-call mislukt met sleutel {sleutel} (provider={naam})"
    resultaat = _redact_text(regel)
    assert sleutel not in resultaat
    # De rest van de regel blijft leesbaar.
    assert "AI-call mislukt met sleutel" in resultaat
    assert f"(provider={naam})" in resultaat


def test_meerdere_keys_in_een_regel():
    regel = f"oud={_OUDE_OPENAI_KEY} nieuw={_ANTHROPIC_KEY}"
    resultaat = _redact_text(regel)
    assert _OUDE_OPENAI_KEY not in resultaat
    assert _ANTHROPIC_KEY not in resultaat
    assert resultaat.count(REDACTED) == 2


@pytest.mark.parametrize("achtervoegsel", [".", ",", ")", '"', "'", ""])
def test_key_direct_gevolgd_door_leesteken(achtervoegsel):
    regel = f"sleutel: {_ANTHROPIC_KEY}{achtervoegsel}"
    assert _ANTHROPIC_KEY not in _redact_text(regel)


def test_traceback_met_anthropic_key():
    """Bewust ZONDER `api-key:`-prefix.

    Met die prefix grijpt de `api[_-]?key`-regel in en zou de test ook op de
    ongefixte code slagen — hij zou dan regel 4 meten, niet regel 1.
    """
    traceback = (
        'File "src/services/ai/anthropic_client.py", line 42\n'
        f"    AuthenticationError: sleutel ongeldig ({_ANTHROPIC_KEY})\n"
    )
    resultaat = _redact_text(traceback)
    assert _ANTHROPIC_KEY not in resultaat
    assert REDACTED in resultaat
    assert "anthropic_client.py" in resultaat


# --- Over-redactie: de fout die DEF-580 voor de base64-regel repareerde -------


@pytest.mark.parametrize(
    "onschuldig",
    [
        # `sk` als achtervoegsel van een gewoon woord.
        "risk-assessment_module-v2 geladen",
        "Toetsregel risk-based_controle_matrix faalt",
        "file /app/data/asterisk-config_backup-2026.json",
        "task-sk-verwerking_batch-01 gestart",
        # Een branchnaam die met sk- begint maar geen sleutel is.
        "branch feature/sk-583-api-key-redactie",
        # Te kort om een sleutel te zijn.
        "formulier sk-8 invullen",
        "sk-korte",
        "de afkorting sk- betekent niets",
    ],
)
def test_onschuldige_tekst_blijft_intact(onschuldig):
    """Over-redactie maakt logs onleesbaar en schaadt debugging.

    De eerste vier gevallen hebben `sk` als staart van een woord (`risk`,
    `asterisk`, `task`); de vijfde is een echte branchnaam uit dit project. Alle
    vijf werden geredigeerd door een tussenversie van deze fix.
    """
    assert _redact_text(onschuldig) == onschuldig


def test_paden_blijven_intact():
    """Regressie-guard op DEF-580: geen enkele regel mag paden opeten."""
    pad = "/Users/chris/Projecten/Definitie-app/data/definities.db"
    assert _redact_text(pad) == pad


def test_andere_secret_regels_blijven_werken():
    """De hex-, base64- en api_key=-regels draaien onafhankelijk van regel 1."""
    hex_token = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    base64_blob = "dGhpc2lzYXNlY3JldHRva2VuMTIzNDU2Nzg5MA"
    assert hex_token not in _redact_text(hex_token)
    assert base64_blob not in _redact_text(base64_blob)
    assert REDACTED in _redact_text("api_key=geheimewaarde12345678")
    assert "user@example.com" not in _redact_text("mail: user@example.com")


# --- De bron: config-objecten mogen hun sleutel niet tonen -------------------


def test_apiconfig_toont_de_sleutel_niet_in_repr():
    """DEF-583: `logger.debug("%s", config)` lekte de key volledig.

    De PII-filter bewerkt `record.args` maar laat niet-string objecten met rust;
    de formatter roept `str(config)` pas ná de filter aan. `field(repr=False)`
    dicht dat bij de bron, ongeacht het kanaal (logging, st.error, print).
    """
    from config.config_manager import APIConfig

    config = APIConfig(
        openai_api_key=_OUDE_OPENAI_KEY,
        anthropic_api_key=_ANTHROPIC_KEY,
    )
    weergave = repr(config)
    assert _OUDE_OPENAI_KEY not in weergave
    assert _ANTHROPIC_KEY not in weergave
    assert str(config) == weergave
    # De niet-gevoelige velden blijven zichtbaar voor debugging.
    assert "ai_provider" in weergave


def test_config_als_log_argument_lekt_de_sleutel_niet():
    """End-to-end via het echte filter-pad, met een object als %s-argument."""
    import io
    import logging

    from config.config_manager import APIConfig
    from utils.logging_filters import PIIRedactingFilter

    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.addFilter(PIIRedactingFilter())
    logger = logging.getLogger("test.def583.config")
    logger.handlers = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    config = APIConfig(anthropic_api_key=_ANTHROPIC_KEY)
    logger.debug("actieve config: %s", config)

    uitvoer = buffer.getvalue()
    assert uitvoer, "er is niets gelogd"
    assert _ANTHROPIC_KEY not in uitvoer
