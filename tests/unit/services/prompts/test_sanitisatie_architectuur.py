"""DEF-591: bewaak dat elke contextsectie zijn user-content door de guard haalt.

## Waarom de eerste versie van deze test waardeloos was

Hij checkte per *bestand*: als de string `sanitize_prompt_blok` ergens in het
bestand voorkwam, was het bestand goedgekeurd. Maar de DEF-590-bug zat in één
functie (`_build_rich_context_section` rendeerde `source.content` rauw) terwijl
een ándere functie in datzelfde bestand (`_veilig_datablok`) wél sanitiseerde.
De test zou dus **groen** zijn gebleven op precies de bug die hem motiveerde.
Geverifieerd door de bug te reproduceren.

## Wat deze versie doet

Een sink-registry op **functieniveau**, via de AST:

* `ContextAwarenessModule` levert zijn prompt-tekst uit functies die eindigen op
  `_context_section`. Dat zijn de sinks: alles wat daar terugkomt gaat de prompt
  in.
* Elke sink moet `_veilig_datablok` aanroepen, óf expliciet met reden op de
  waiver-lijst staan.
* **Fail-closed**: een vierde contextsectie die niemand registreert, laat de test
  falen. Dat is het punt — de auteur wordt gedwongen te beslissen.

## Bewezen, niet aangenomen

`test_scanner_ziet_een_overtreding` draait de scanner op een synthetische module
die de DEF-590-bug bevat, en eist dat hij hem markeert. Een guard die nooit rood
is geweest, is geen guard.

Aanvullend, en niet vervangbaar: `test_definitie_prompt_hardening.py` toetst het
gedrag van alle drie de paden. Deze test bewaakt de structuur, die het gedrag.
"""

import ast
import pathlib

import pytest

pytestmark = pytest.mark.unit

_MODULE = (
    pathlib.Path(__file__).resolve().parents[4]
    / "src"
    / "services"
    / "prompts"
    / "modules"
    / "context_awareness_module.py"
)

#: Functies die prompt-tekst teruggeven. Alles wat hier uit komt gaat naar het model.
_SINK_SUFFIX = "_context_section"

#: De helper die sanitiseert én in een datablok omhult.
_GUARD = "_veilig_datablok"

#: Sink → reden waarom die géén guard hoeft.
_WAIVERS = {
    "_build_fallback_context_section": (
        "Geeft een vaste tekst terug zonder user-content; er is niets te saniteren."
    ),
}


def _aangeroepen_namen(functie: ast.FunctionDef) -> set[str]:
    namen: set[str] = set()
    for call in ast.walk(functie):
        if not isinstance(call, ast.Call):
            continue
        if isinstance(call.func, ast.Attribute):
            namen.add(call.func.attr)
        elif isinstance(call.func, ast.Name):
            namen.add(call.func.id)
    return namen


def _ongedekte_sinks(bron: str) -> list[str]:
    """De sinks in `bron` die de guard niet aanroepen en geen waiver hebben.

    Draait op een bronstring, niet op een pad, zodat de negatieve test hem op een
    synthetische module kan loslaten.
    """
    boom = ast.parse(bron)
    ongedekt = []
    for knoop in ast.walk(boom):
        if not isinstance(knoop, ast.FunctionDef):
            continue
        if not knoop.name.endswith(_SINK_SUFFIX):
            continue
        if knoop.name in _WAIVERS:
            continue
        if _GUARD not in _aangeroepen_namen(knoop):
            ongedekt.append(knoop.name)
    return ongedekt


def _sink_namen(bron: str) -> list[str]:
    return [
        n.name
        for n in ast.walk(ast.parse(bron))
        if isinstance(n, ast.FunctionDef) and n.name.endswith(_SINK_SUFFIX)
    ]


# --- De guard bewaakt de echte code ------------------------------------------


def test_module_bestaat_nog():
    """Vangnet: een hernoemd bestand mag deze guard niet stil uitschakelen."""
    assert _MODULE.is_file(), f"pad klopt niet meer: {_MODULE}"


def test_registry_kent_alle_sinks():
    """Fail-closed op de andere as: een waiver mag niet naar een dode functie wijzen."""
    sinks = _sink_namen(_MODULE.read_text(encoding="utf-8"))
    assert len(sinks) >= 3, f"verdacht weinig contextsecties gevonden: {sinks}"

    verdwenen = set(_WAIVERS) - set(sinks)
    assert not verdwenen, (
        f"waiver verwijst naar niet-bestaande functies: {sorted(verdwenen)}. "
        "Opruimen, anders dekt de waiver stilletjes niets."
    )


def test_elke_contextsectie_gaat_door_de_guard():
    ongedekt = _ongedekte_sinks(_MODULE.read_text(encoding="utf-8"))
    if ongedekt:
        pytest.fail(
            "Contextsecties die user-content renderen zonder guard (DEF-590/591):\n"
            + "\n".join(f"  {naam}" for naam in sorted(ongedekt))
            + f"\n\nRoep `{_GUARD}` aan, of zet de functie op de waiver-lijst in "
            f"{__file__} met een reden waarom er niets te saniteren valt."
        )


# --- De guard is bewezen, niet aangenomen ------------------------------------


_DEF_590_BUG = '''
class ContextAwarenessModule:
    def _build_rich_context_section(self, context) -> str:
        """Precies de DEF-590-bug: rendert bronnen rauw, buiten elk datablok."""
        sections = ["UITGEBREIDE CONTEXT:"]
        for source in context.enriched_context.sources:
            sections.append(f"  {source.source_type}: {source.content[:150]}")
        return "\\n".join(sections)

    def _build_moderate_context_section(self, context) -> str:
        """Deze functie sanitiseert wél — en maskeerde de bug in de per-file check."""
        return _veilig_datablok([context.enriched_context.get_all_context_text()])
'''


def test_scanner_ziet_een_overtreding():
    """De echte DEF-590-bug: één sink lekt, een andere in hetzelfde bestand niet.

    De vorige, per-bestand versie van deze test bleef hier groen op.
    """
    ongedekt = _ongedekte_sinks(_DEF_590_BUG)
    assert ongedekt == [
        "_build_rich_context_section"
    ], f"scanner mist de bug die hij moet vangen; gevonden: {ongedekt}"


def test_scanner_keurt_een_gesaniteerde_sectie_goed():
    veilig = """
class M:
    def _build_rich_context_section(self, context) -> str:
        return _veilig_datablok([context.enriched_context.get_all_context_text()])
"""
    assert _ongedekte_sinks(veilig) == []


def test_scanner_respecteert_de_waiver():
    met_waiver = """
class M:
    def _build_fallback_context_section(self) -> str:
        return "Geen specifieke context beschikbaar."
"""
    assert _ongedekte_sinks(met_waiver) == []
