"""De PII-filter mag filesystem-paden niet als base64-token redigeren (DEF-580).

`_redact_text` had `/` in de base64-charset, waardoor elk pad van 32+ tekens
werd geredigeerd:

    /Users/chrislehnen/Projecten/Definitie-app/data/definities.db
    → /[REDACTED]-app/data/definities.db

Dat maakt DB-paden, importpaden en tracebacks onleesbaar. Deze tests borgen
zowel dat paden intact blijven als dat echte secrets nog gevangen worden — de
fix mag de filter niet verzwakken voor de gevallen die ertoe doen.
"""

import pytest

pytestmark = pytest.mark.unit

from utils.logging_filters import REDACTED, _redact_text


@pytest.mark.parametrize(
    "pad",
    [
        "/Users/chrislehnen/Projecten/Definitie-app/data/definities.db",
        # Met cijfers erin: optie A (cijfer-lookahead) zou hier nog falen.
        "/Users/chris2/Projecten/Definitie-app/data/definities.db",
        "/opt/hostedtoolcache/Python/3.13.14/x64/lib/python3.13/site-packages",
        "src/services/prompts/synonym_research_prompt.py:42 in build_prompt",
    ],
)
def test_paden_blijven_intact(pad):
    assert _redact_text(pad) == pad, "pad werd geredigeerd als base64-token"


@pytest.mark.parametrize(
    "geheim",
    [
        # Kale base64-blob zonder slashes — het geval dat de regel moet vangen.
        "dGhpcyBpcyBhIHNlY3JldCB0b2tlbiAxMjM0NTY3ODkw",
        # Lange alfanumerieke sleutel.
        "AKIAIOSFODNN7EXAMPLEwJalrXUtnFEMIKSEVENbPxRfiCY",
    ],
)
def test_base64_achtige_secrets_worden_nog_geredigeerd(geheim):
    assert geheim not in _redact_text(geheim)
    assert REDACTED in _redact_text(geheim)


def test_andere_secret_regels_blijven_werken():
    """De sk-, hex- en api_key=-regels draaien onafhankelijk van de base64-regel."""
    sk = "sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890"
    hex_token = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    assert sk not in _redact_text(sk)
    assert hex_token not in _redact_text(hex_token)
    assert REDACTED in _redact_text("api_key=geheimewaarde12345678")
    assert "user@example.com" not in _redact_text("mail: user@example.com")


def test_pad_met_ingebedde_secret_redigeert_alleen_het_secret():
    regel = "laden uit /Users/chris/Projecten/app/.env: sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890"
    resultaat = _redact_text(regel)
    assert "/Users/chris/Projecten/app/.env" in resultaat
    assert "sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890" not in resultaat
