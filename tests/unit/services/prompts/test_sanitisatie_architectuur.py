"""DEF-591: bewaak dat prompt-modules user-content niet ongesaniteerd renderen.

Het `VeiligeTekst`-type laat mypy de ontwikkelaar corrigeren die een rauwe `str`
aan `datablok()` geeft. Maar drie gaten blijven open, en die dekt deze test:

1. Een module die user-content in de prompt zet **zonder** `datablok()` te
   gebruiken — dan is er geen typecheck om te falen. Dit is exact hoe het rijke
   contextpad in DEF-590 lekte: `_format_sources_with_confidence` rendeerde
   `source.content` rauw, buiten elk datablok.
2. Een `cast(VeiligeTekst, ...)` — mypy laat dat geruisloos door.
3. Een `# type: ignore` op de sanitisatie-grens.

De test is een net, geen bewijs: hij werkt op bestandsniveau en mist alias-imports.
Dat is bewust — een grof net dat een hele klasse fouten vangt is meer waard dan
geen net. Precedent: `tests/unit/test_forbidden_symbols.py`.
"""

import pathlib
import re

import pytest

pytestmark = pytest.mark.unit

_MODULES_DIR = (
    pathlib.Path(__file__).resolve().parents[4]
    / "src"
    / "services"
    / "prompts"
    / "modules"
)

#: Aanroepen die user-content (documenttekst) de prompt in trekken.
#:
#: Bewust NIET `.content` kaal: `ModuleOutput.content` is onze eigen sectietekst.
#: Bewust NIET `context.begrip`: dat veld is via het `VeiligeTekst`-type gedekt
#: (`datablok(TAG_BEGRIP, ...)` weigert een rauwe `str`), en `expertise_module`
#: leest het legitiem om de woordsoort te bepalen zonder het te renderen.
#: Wat overblijft is het patroon dat in DEF-590 daadwerkelijk lekte: een module
#: die `sources` of de samengevoegde contexttekst aanraakt.
_USER_CONTENT_BRONNEN = (
    "get_all_context_text",
    ".sources",
)

#: Bewijs dat de module de content door de sanitizer haalt.
_SANITISATIE_MARKERS = ("sanitize_prompt_regel", "sanitize_prompt_blok")

#: Manieren om het `VeiligeTekst`-contract stil te breken.
_BYPASS_PATRONEN = (
    re.compile(r"cast\(\s*VeiligeTekst"),
    re.compile(r"VeiligeTekst\("),  # alleen de sanitizer mag dit
)


def _python_modules() -> list[pathlib.Path]:
    return [p for p in _MODULES_DIR.glob("*.py") if p.name != "__init__.py"]


def test_modules_directory_bestaat_nog():
    """Vangnet: een mapverplaatsing mag deze guard niet stil uitschakelen."""
    assert _MODULES_DIR.is_dir(), f"pad klopt niet meer: {_MODULES_DIR}"
    assert len(_python_modules()) > 5, "verdacht weinig modules gevonden"


def test_module_die_user_content_rendert_sanitiseert_ook():
    """Wie `.content` of `begrip` aanraakt, moet de sanitizer aanroepen.

    Zo faalt een nieuwe prompt-module die vergeet te hardenen, in plaats van
    stilletjes een injectiekanaal te openen.
    """
    overtreders = []
    for pad in _python_modules():
        tekst = pad.read_text(encoding="utf-8")
        gebruikt_user_content = any(bron in tekst for bron in _USER_CONTENT_BRONNEN)
        if not gebruikt_user_content:
            continue
        if not any(marker in tekst for marker in _SANITISATIE_MARKERS):
            gevonden = [b for b in _USER_CONTENT_BRONNEN if b in tekst]
            overtreders.append(f"  {pad.name}: gebruikt {gevonden} zonder sanitizer")

    if overtreders:
        pytest.fail(
            "Prompt-modules renderen user-content zonder sanitisatie (DEF-590/591):\n"
            + "\n".join(overtreders)
            + "\n\nHaal de waarde door sanitize_prompt_regel/_blok en omhul hem "
            "met datablok()."
        )


def test_niemand_omzeilt_het_veiligetekst_contract():
    """`cast` en handmatige `VeiligeTekst(...)` breken het contract geruisloos.

    Alleen `sanitization.py` zelf mag `VeiligeTekst(...)` aanroepen — dat is de
    uitgang van de sanitizer, oftewel het keuringsstempel.
    """
    overtreders = []
    for pad in _python_modules():
        tekst = pad.read_text(encoding="utf-8")
        for patroon in _BYPASS_PATRONEN:
            if patroon.search(tekst):
                overtreders.append(f"  {pad.name}: {patroon.pattern}")

    if overtreders:
        pytest.fail(
            "Bypass van het VeiligeTekst-contract gevonden:\n"
            + "\n".join(overtreders)
            + "\n\nAlleen sanitization.py mag VeiligeTekst(...) construeren. "
            "Join rauwe tekst eerst, sanitiseer als laatste stap."
        )
