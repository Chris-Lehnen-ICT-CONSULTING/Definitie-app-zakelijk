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

## Drie netten, drie assen (review 14 juli op a4e233be)

De herschrijving van 10 juli maakte de sink-scanner scherp (per functie) maar
versmalde stilletjes de dekking: van álle modules naar één bestand, en de
bypass-scan op `cast(VeiligeTekst, ...)` verdween zonder vervanging. Daarom nu:

1. **Sink-net** (suffix `_context_section`, één module): scherp, faalt met
   functienaam.
2. **Bron-net** (alle modules, naamsonafhankelijk): elke functie die
   `get_all_context_text` of `.sources` aanraakt moet een sanitizer aanroepen.
   Vangt de nieuwe module of de afwijkend genoemde sink die het sink-net mist.
3. **Bypass-net** (alle modules): niemand construeert `VeiligeTekst(...)` of
   `cast(VeiligeTekst, ...)` buiten `sanitization.py` — dat is het
   keuringsstempel van de sanitizer.

Bekende beperking (bewuste waiver, review 14 juli): de scanners zijn
presence-based. Een guard-aanroep waarvan het resultaat wordt weggegooid, of
een aanroep in dead code, telt als gedekt. Voor de bestaande sinks vangen de
gedragstests in `test_definitie_prompt_hardening.py` dat scenario; wie een
nieuwe sink toevoegt, hoort daar ook een gedragstest bij te schrijven.
"""

import ast
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

_MODULE = _MODULES_DIR / "context_awareness_module.py"

_FUNCTIE_KNOPEN = (ast.FunctionDef, ast.AsyncFunctionDef)

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


def _aangeroepen_namen(functie: ast.AST) -> set[str]:
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
        if not isinstance(knoop, _FUNCTIE_KNOPEN):
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
        if isinstance(n, _FUNCTIE_KNOPEN) and n.name.endswith(_SINK_SUFFIX)
    ]


# --- Het bron-net: naamsonafhankelijk, over alle modules -----------------------

#: Aanroep resp. attribuut die user-content (documenttekst) de functie in trekken.
#: Bewust NIET `.content` kaal (ModuleOutput.content is onze eigen sectietekst)
#: en NIET `context.begrip` (gedekt door het VeiligeTekst-type op `datablok`).
_BRON_AANROEP = "get_all_context_text"
_BRON_ATTRIBUUT = "sources"

#: Aanroepen die gelden als bewijs van sanitisatie.
_SANITIZERS = frozenset({_GUARD, "sanitize_prompt_blok", "sanitize_prompt_regel"})

#: functienaam → reden waarom die user-content mag aanraken zonder sanitizer.
_BRON_WAIVERS = {
    "execute": (
        "Leest alleen `len(sources)` voor metadata; rendert geen bron-content."
    ),
    "_calculate_context_score": (
        "Middelt confidence-getallen over de bronnen; rendert geen bron-content."
    ),
}


def _raakt_user_content(functie: ast.AST) -> bool:
    for knoop in ast.walk(functie):
        if isinstance(knoop, ast.Attribute) and knoop.attr == _BRON_ATTRIBUUT:
            return True
        if isinstance(knoop, ast.Call):
            naam = (
                knoop.func.attr
                if isinstance(knoop.func, ast.Attribute)
                else getattr(knoop.func, "id", None)
            )
            if naam == _BRON_AANROEP:
                return True
    return False


def _functies_die_user_content_lekken(bron: str) -> list[str]:
    """Functies die bron-content aanraken zonder sanitizer en zonder waiver."""
    lekkend = []
    for knoop in ast.walk(ast.parse(bron)):
        if not isinstance(knoop, _FUNCTIE_KNOPEN):
            continue
        if knoop.name in _BRON_WAIVERS:
            continue
        if not _raakt_user_content(knoop):
            continue
        if not _SANITIZERS & _aangeroepen_namen(knoop):
            lekkend.append(knoop.name)
    return lekkend


#: Manieren om het VeiligeTekst-contract stil te breken; alleen `sanitization.py`
#: mag `VeiligeTekst(...)` aanroepen — dat is de uitgang van de sanitizer.
_BYPASS_PATRONEN = (
    re.compile(r"cast\(\s*VeiligeTekst"),
    re.compile(r"VeiligeTekst\("),
)


def _python_modules() -> list[pathlib.Path]:
    return [p for p in _MODULES_DIR.glob("*.py") if p.name != "__init__.py"]


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


# --- Het bron-net: alle modules, naamsonafhankelijk ---------------------------


def test_modules_directory_bestaat_nog():
    """Vangnet: een mapverplaatsing mag het bron- en bypass-net niet stil uitschakelen."""
    assert _MODULES_DIR.is_dir(), f"pad klopt niet meer: {_MODULES_DIR}"
    assert len(_python_modules()) > 5, "verdacht weinig modules gevonden"


def test_geen_module_lekt_user_content_zonder_sanitizer():
    """Wie `get_all_context_text` of `.sources` aanraakt, sanitiseert — in élke module.

    Het sink-net hierboven kent alleen `context_awareness_module.py` en de
    `_context_section`-naamconventie; dit net is naamsonafhankelijk en vangt de
    nieuwe module of afwijkend genoemde functie die daar doorheen glipt.
    """
    overtreders = []
    for pad in _python_modules():
        for naam in _functies_die_user_content_lekken(pad.read_text(encoding="utf-8")):
            overtreders.append(f"  {pad.name}: {naam}")

    if overtreders:
        pytest.fail(
            "Functies die bron-content aanraken zonder sanitizer (DEF-590/591):\n"
            + "\n".join(sorted(overtreders))
            + "\n\nHaal de waarde door sanitize_prompt_regel/_blok of "
            f"{_GUARD}, of zet de functie met reden in _BRON_WAIVERS in {__file__}."
        )


def test_bron_waivers_wijzen_naar_bestaande_functies():
    """Fail-closed op de waiver-as: een dode waiver dekt stilletjes niets."""
    alle_functies = set()
    for pad in _python_modules():
        alle_functies.update(
            n.name
            for n in ast.walk(ast.parse(pad.read_text(encoding="utf-8")))
            if isinstance(n, _FUNCTIE_KNOPEN)
        )
    verdwenen = set(_BRON_WAIVERS) - alle_functies
    assert (
        not verdwenen
    ), f"_BRON_WAIVERS verwijst naar niet-bestaande functies: {sorted(verdwenen)}"


def test_bron_net_ziet_een_lek_ook_in_een_async_functie():
    """Zelftest: naamsonafhankelijk én async — de twee gaten van het sink-net."""
    lek = """
class NieuweModule:
    async def render_documenten(self, context) -> str:
        return "\\n".join(s.content for s in context.enriched_context.sources)
"""
    assert _functies_die_user_content_lekken(lek) == ["render_documenten"]


def test_bron_net_keurt_een_gesaniteerde_functie_goed():
    veilig = """
class M:
    def render_documenten(self, context) -> str:
        return sanitize_prompt_blok(
            context.enriched_context.get_all_context_text(), 20000
        )
"""
    assert _functies_die_user_content_lekken(veilig) == []


# --- Het bypass-net: het keuringsstempel blijft bij de sanitizer ---------------


def test_niemand_omzeilt_het_veiligetekst_contract():
    """`cast(VeiligeTekst, ...)` en handmatige `VeiligeTekst(...)` breken het
    contract geruisloos: mypy zwijgt en de runtime-guard in `datablok` vangt
    alleen angle-brackets. Alleen `sanitization.py` mag het stempel zetten.
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


def test_bypass_patronen_matchen_de_bypass():
    """Zelftest: de regexes herkennen beide bypass-vormen daadwerkelijk."""
    assert any(p.search("x = cast(VeiligeTekst, raw)") for p in _BYPASS_PATRONEN)
    assert any(p.search("x = VeiligeTekst(raw)") for p in _BYPASS_PATRONEN)
    assert not any(
        p.search("def f(x: VeiligeTekst) -> str: ...") for p in _BYPASS_PATRONEN
    ), "een type-annotatie is legitiem gebruik en mag niet matchen"
