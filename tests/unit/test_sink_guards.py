"""Structurele guard-dekking: elke sink is bewust wél of niet beveiligd.

## Waarom deze test bestaat

Drie keer op één dag (DEF-578, DEF-590, DEF-593) is dezelfde fout gemaakt: een
guard werd toegevoegd op de plek waar de bug gevonden was, terwijl dezelfde
gevaarlijke operatie elders óók werd aangeroepen. De fix was compleet, de test
niet — je kon de guard uit twee van de drie schrijfpaden halen en de suite bleef
groen.

Een test die over *invoer* parametriseert vangt dat nooit. Deze test
parametriseert over de **sinks**: elke functie die naar een gevaarlijke bestemming
schrijft, moet ofwel de guard aanroepen, ofwel expliciet met reden op de
waiver-lijst staan.

**Fail-closed.** Een nieuwe exportfunctie die niemand hier registreert, laat deze
test falen. Dat is het punt: de auteur wordt gedwongen te beslissen of zijn sink
een guard nodig heeft, in plaats van dat de vraag stilzwijgend overgeslagen wordt.

## Een nieuwe sink toevoegen

Voeg een `SinkRegel` toe. Zet een functie alleen op `waivers` met een reden die
uitlegt waaróm het formaat ongevoelig is — niet omdat het lastig is.

De test is een net, geen bewijs: hij werkt op naam-niveau in de AST en ziet niet
of de guard op de juiste waarde wordt toegepast. Combineer hem dus met een
sabotage-run per call-site (haal de guard weg, eis dat er iets rood wordt).
"""

import ast
import pathlib
from dataclasses import dataclass, field

import pytest

pytestmark = pytest.mark.unit

_REPO = pathlib.Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SinkRegel:
    """Eén bestand, één klasse van gevaarlijke bestemmingen, één guard."""

    bestand: str
    #: Functies waarvan de naam hiermee begint worden getoetst.
    functie_prefix: str
    #: De guard die zo'n functie moet aanroepen.
    guard: str
    #: Waarom deze sink een guard nodig heeft.
    reden: str
    #: Functienaam → reden waarom die géén guard hoeft.
    waivers: dict[str, str] = field(default_factory=dict)


SINK_REGELS = [
    SinkRegel(
        bestand="src/services/export_service.py",
        functie_prefix="_export_",
        guard="_veilige_rij",
        reden=(
            "DEF-593: Excel/LibreOffice/Sheets lezen een celwaarde die met "
            "= + - @ tab of CR begint als formule. Elke functie die cellen "
            "wegschrijft moet `_veilige_rij` gebruiken."
        ),
        waivers={
            "_export_to_json": "JSON heeft geen formulesemantiek; json.dump escapet zelf.",
            "_export_multiple_to_json": "Idem — JSON wordt niet als spreadsheet geopend.",
            "_export_to_txt": "Platte tekst, geen cellen, geen formule-evaluatie.",
            "_export_multiple_to_txt": "Idem.",
            "_export_sort_key": "Sorteersleutel; schrijft niets weg.",
        },
    ),
]


def _aangeroepen_namen(node: ast.FunctionDef) -> set[str]:
    """Alle functienamen die binnen deze functie worden aangeroepen."""
    namen: set[str] = set()
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        if isinstance(func, ast.Attribute):
            namen.add(func.attr)
        elif isinstance(func, ast.Name):
            namen.add(func.id)
    return namen


def _sink_functies(regel: SinkRegel) -> list[ast.FunctionDef]:
    bron = (_REPO / regel.bestand).read_text(encoding="utf-8")
    boom = ast.parse(bron)
    return [
        n
        for n in ast.walk(boom)
        if isinstance(n, ast.FunctionDef) and n.name.startswith(regel.functie_prefix)
    ]


@pytest.mark.parametrize("regel", SINK_REGELS, ids=lambda r: r.bestand)
def test_registry_is_niet_stale(regel):
    """Vangnet: een hernoemde functie of verplaatst bestand mag de guard niet stil uitschakelen."""
    assert (_REPO / regel.bestand).is_file(), f"bestand weg: {regel.bestand}"
    functies = _sink_functies(regel)
    assert functies, f"geen functies met prefix {regel.functie_prefix!r} gevonden"

    bekende = {f.name for f in functies}
    verdwenen = set(regel.waivers) - bekende
    assert not verdwenen, (
        f"waiver verwijst naar niet-bestaande functies: {sorted(verdwenen)}. "
        "Opruimen, anders dekt de waiver stilletjes niets."
    )


@pytest.mark.parametrize("regel", SINK_REGELS, ids=lambda r: r.bestand)
def test_elke_sink_heeft_een_guard_of_een_waiver(regel):
    """Fail-closed: een nieuwe exportfunctie dwingt een expliciete keuze af."""
    ongedekt = []
    for functie in _sink_functies(regel):
        if functie.name in regel.waivers:
            continue
        if regel.guard in _aangeroepen_namen(functie):
            continue
        ongedekt.append(functie.name)

    if ongedekt:
        pytest.fail(
            f"Sinks zonder guard in {regel.bestand}:\n"
            + "\n".join(f"  {naam}" for naam in sorted(ongedekt))
            + f"\n\n{regel.reden}\n\n"
            f"Roep `{regel.guard}` aan, of zet de functie op de waiver-lijst in "
            f"{__file__} met een reden waarom het formaat ongevoelig is."
        )


@pytest.mark.parametrize("regel", SINK_REGELS, ids=lambda r: r.bestand)
def test_gegarandeerde_sinks_zijn_daadwerkelijk_gedekt(regel):
    """Minstens één functie moet de guard gebruiken, anders is de regel zinloos."""
    gedekt = [
        f.name
        for f in _sink_functies(regel)
        if regel.guard in _aangeroepen_namen(f) and f.name not in regel.waivers
    ]
    assert gedekt, (
        f"geen enkele functie in {regel.bestand} roept {regel.guard} aan — "
        "is de guard hernoemd of verwijderd?"
    )
