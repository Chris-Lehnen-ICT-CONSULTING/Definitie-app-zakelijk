"""De PII-filter moet álle gangbare API-key-formaten redigeren (DEF-583).

De regel was `sk-[A-Za-z0-9]{16,}`: die eist 16+ alfanumerieke tekens direct ná
`sk-`. De moderne formaten breken dat meteen af met een streepje:

    sk-proj-...      (OpenAI project-key)   -> "proj" is 4 tekens, dan "-"
    sk-ant-api03-... (Anthropic)            -> "ant" is 3 tekens, dan "-"

Beide glipten dus ongeredigeerd door. Anthropic is de default provider van deze
app, dus dat was de sleutel die in productie in een traceback kon belanden.

Alle keys hieronder zijn verzonnen testwaarden.
"""

import pytest

pytestmark = pytest.mark.unit

from utils.logging_filters import REDACTED, _redact_text

# Verzonnen sleutels in de drie formaten die in het wild voorkomen.
_OUDE_OPENAI_KEY = "sk-A1b2C3d4E5f6G7h8IJKLmnopQRSTuvwx"
_PROJECT_OPENAI_KEY = (
    "sk-proj-abcdEFGH1234ijklMNOP5678qrstUVWX_yz90-AB"
    "cdefGHIJ1234klmnOPQR5678stuvWXYZ"
)
_ANTHROPIC_KEY = "sk-ant-api03-abcdEFGH1234ijklMNOP5678qrstUVWX_yz90-AA"


@pytest.mark.parametrize(
    ("naam", "sleutel"),
    [
        ("oud openai", _OUDE_OPENAI_KEY),
        ("openai project", _PROJECT_OPENAI_KEY),
        ("anthropic", _ANTHROPIC_KEY),
    ],
)
def test_api_keys_worden_geredigeerd(naam, sleutel):
    resultaat = _redact_text(sleutel)
    assert sleutel not in resultaat, f"{naam}-key ongeredigeerd in de log"


@pytest.mark.parametrize(
    ("naam", "sleutel"),
    [
        ("openai project", _PROJECT_OPENAI_KEY),
        ("anthropic", _ANTHROPIC_KEY),
    ],
)
def test_api_keys_in_een_logregel_worden_geredigeerd(naam, sleutel):
    regel = f"AI-call mislukt met key {sleutel} (provider={naam})"
    resultaat = _redact_text(regel)
    assert sleutel not in resultaat
    # De rest van de regel blijft leesbaar.
    assert "AI-call mislukt met key" in resultaat
    assert f"(provider={naam})" in resultaat


def test_traceback_met_anthropic_key_wordt_geredigeerd():
    traceback = (
        'File "src/services/ai/anthropic_client.py", line 42\n'
        f"    AuthenticationError: invalid x-api-key: {_ANTHROPIC_KEY}\n"
    )
    resultaat = _redact_text(traceback)
    assert _ANTHROPIC_KEY not in resultaat
    assert REDACTED in resultaat or "***" in resultaat


@pytest.mark.parametrize(
    "onschuldig",
    [
        "formulier sk-8 invullen",
        "sk-korte",  # te kort om een key te zijn
        "de afkorting sk- betekent niets",
    ],
)
def test_onschuldige_tekst_met_sk_blijft_intact(onschuldig):
    """Over-redactie maakt logs onleesbaar (zie DEF-580); de prefix alleen is
    geen reden om te maskeren."""
    assert _redact_text(onschuldig) == onschuldig
