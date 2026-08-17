"""DEF-676: elke `bestand.py::node`-verwijzing moet een bestaande node aanwijzen.

Code en tests wijzen elkaar geregeld aan met pytest-notatie —
``pad/naar/test_iets.py::TestKlasse``, ``…::test_functie`` of
``…::TestKlasse::test_methode`` — om te zeggen: *dit hoort daar*. Dat gebeurt
in twee gedaanten:

- als **dekkingsclaim** ("het bewijs voor dit gedrag staat daar");
- als **draai-instructie** ("draai dit commando om X te zien").

Beide zijn verifieerbare beweringen over deze repository. Wijst zo'n
verwijzing naar een bestand of node die hier niet bestaat, dan is zij onwaar:
de dekkingsclaim suggereert dekking die er niet is, en het commando levert
niets op wanneer iemand het kopieert.

Werking: scan elk Python-bestand onder ``src/`` en ``tests/``, zoek
verwijzingen met een expliciete node, los het bestand op en controleer via de
AST dat de node bestaat — op moduleniveau, en bij een derde segment binnen de
body van de genoemde klasse.

**Wat deze guard niet bewijst.** Hij toetst dát de node bestaat, niet dát de
claim eromheen klopt. Een docstring die zegt "gedekt door X::Y" terwijl X::Y
bestaat maar iets heel anders toetst, blijft ongezien. Dat is een reële
restcategorie: hij is in deze PR ook daadwerkelijk voorgekomen. De semantische
kant hoort bij het resterende DEF-676-werk en bij DEF-623.

Verdere scope-grenzen, bewust:

- **Alleen ``.py`` onder ``src/`` en ``tests/``.** Plandocumenten met
  ``Create: tests/.../test_x.py`` zijn toekomstgerichte instructies, geen
  bewering over het heden. Verwijzingen in ``docs/``, ``README.md`` of
  workflows vallen daarmee ook buiten schot.
- **Alleen bestandsnamen met prefix ``test_``.** Een verwijzing naar
  ``src/services/foo.py::Klasse`` wordt niet gecontroleerd.
- **Alleen verwijzingen mét ``::``.** Een kaal pad zonder node valt erbuiten.
- **Alleen fysiek aaneengesloten tekst.** De guard zoekt ``test_*.py::node``
  letterlijk in de bronbestanden. Staat een verwijzing verdeeld over meerdere
  tokens of regels — bijvoorbeeld door impliciete Python-literalconcatenatie,
  ``("…test_x.py" "::TestY")`` — dan ziet hij hem niet.

  Een eerdere versie probeerde die vorm alsnog te vangen door quote-paren weg
  te knippen. Dat modelleert de Python-grammatica niet: het plakte ook losse
  literalen aaneen en verzon zo nodenamen die nergens bestaan, waardoor
  correcte code werd afgekeurd. Zo'n vals-positief is schadelijker dan een
  gemist geval, want deze guard draait bij elke unit-testrun. De reconstructie
  is daarom teruggetrokken; **deze guard pretendeert niet de Python-grammatica
  te reconstrueren.** Het opvangen van gesplitste verwijzingen — bijvoorbeeld
  via ``tokenize`` — blijft onderdeel van DEF-676.
- **Dit bestand zelf wordt overgeslagen**, zodat de synthetische voorbeelden
  in de guardtests hieronder geen overtreding heten.

Twee eigenschappen die de guard eerlijk houden:

- **Fail-closed op de scanwortel.** Ontbreekt ``src/`` of ``tests/``, dan is
  dat zelf een bevinding. Zonder die regel zou een verkeerd afgeleide wortel
  een lege scan opleveren en zou de hoofdtest vacuüm groen worden.
- **Een verkorte bestandsnaam moet uniek zijn.** Nul treffers is ontbrekend,
  meerdere treffers is ambigu — nooit stil de eerste kiezen.

De guard is cwd-onafhankelijk: de repositorywortel komt uit ``__file__``.
"""

import ast
import re
from pathlib import Path, PurePosixPath

import pytest

pytestmark = [pytest.mark.unit]

# tests/unit/validation/<dit bestand> → drie niveaus omhoog is de repowortel.
REPOWORTEL = Path(__file__).resolve().parents[3]
DIT_BESTAND = Path(__file__).resolve()

BRONMAPPEN = ("src", "tests")

# Herkent volledig pad en verkorte naam, met klasse- of functienode en een
# optioneel methodesegment:
#   tests/unit/validation/test_rule_contract.py::TestOordeelregels
#   test_rule_contract.py::test_iets
#   tests/…/test_x.py::TestKlasse::test_methode
VERWIJZING = re.compile(
    r"(?P<pad>(?:[\w./-]+/)?(?P<bestand>test_\w+\.py))"
    r"::(?P<node>[A-Za-z_]\w*)"
    r"(?:::(?P<methode>[A-Za-z_]\w*))?"
)

ONTBREEKT = "ontbreekt"
AMBIGU = "ambigu"
GEVONDEN = "gevonden"
BUITEN = "buiten"


def _bestanden_per_bronmap(wortel: Path = REPOWORTEL) -> dict[str, list[Path]]:
    """Per bestaande bronmap de te scannen bestanden, recursief.

    `rglob` is hier wezenlijk: het gros van de repository ligt genest, dus een
    niet-recursieve variant zou vrijwel alles overslaan en de hoofdguard stil
    laten slagen. Zie `test_scanwortel_omvat_geneste_ankerbestanden`.
    """
    per_map: dict[str, list[Path]] = {}
    for mapnaam in BRONMAPPEN:
        map_ = wortel / mapnaam
        if not map_.is_dir():
            continue
        per_map[mapnaam] = [
            pad for pad in sorted(map_.rglob("*.py")) if pad.resolve() != DIT_BESTAND
        ]
    return per_map


def _te_scannen_bestanden(wortel: Path = REPOWORTEL) -> list[Path]:
    per_map = _bestanden_per_bronmap(wortel)
    return [pad for mapnaam in BRONMAPPEN for pad in per_map.get(mapnaam, [])]


def _binnen_testwortel(kandidaat: Path, testwortel: Path) -> bool:
    """Ligt `kandidaat` na volledige resolutie binnen de testwortel?

    Bewust ná `resolve()`: `is_file()` alleen zegt niets over wáár het bestand
    staat, en een symlink onder `tests/` kan naar buiten wijzen.
    """
    try:
        return kandidaat.resolve().is_relative_to(testwortel)
    except OSError:
        return False


def _resolveer(
    padtekst: str, bestandsnaam: str, wortel: Path
) -> tuple[str, list[Path]]:
    """Los een verwijzing op tot (status, treffers).

    Padvalidatie gaat vóór bestaan: een absoluut pad of een `..`-segment wordt
    afgewezen zonder ook maar naar de schijf te kijken, en iedere kandidaat die
    na resolutie buiten `<wortel>/tests/` ligt eveneens. Anders zou een
    verwijzing naar een bestand buiten de repository stilzwijgend geldig heten
    — en zou het oordeel bovendien afhangen van wat er toevallig op die machine
    staat.
    """
    testwortel = (wortel / "tests").resolve()
    stukken = PurePosixPath(padtekst)

    if stukken.is_absolute() or ".." in stukken.parts:
        return BUITEN, []

    if "/" in padtekst:
        kandidaat = wortel / padtekst
        if not kandidaat.is_file():
            return ONTBREEKT, []
        if not _binnen_testwortel(kandidaat, testwortel):
            return BUITEN, [kandidaat]
        return GEVONDEN, [kandidaat]

    binnen: list[Path] = []
    buiten: list[Path] = []
    for pad in sorted((wortel / "tests").rglob(bestandsnaam)):
        (binnen if _binnen_testwortel(pad, testwortel) else buiten).append(pad)

    # Eén ontsnappende kandidaat besmet de hele verkorte naam. Zou hij hier
    # stil worden weggefilterd, dan kon een intern bestand ten onrechte als
    # uniek gelden en hing de uitkomst af van wat er buiten de repository
    # staat. Beter luid weigeren en om een volledig pad vragen.
    if buiten:
        return BUITEN, buiten
    if not binnen:
        return ONTBREEKT, []
    if len(binnen) > 1:
        return AMBIGU, binnen
    return GEVONDEN, binnen


def _moduleknopen(pad: Path) -> dict[str, set[str]] | None:
    """Module-level nodes → hun directe methodenamen; None bij een leesfout.

    Alleen ``boom.body``: een methode of geneste functie is geen zelfstandige
    node op moduleniveau, dus ``ast.walk`` zou te veel goedkeuren.
    """
    try:
        boom = ast.parse(pad.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None

    functies = (ast.FunctionDef, ast.AsyncFunctionDef)
    knopen: dict[str, set[str]] = {}
    for knoop in boom.body:
        if isinstance(knoop, ast.ClassDef):
            knopen[knoop.name] = {
                kind.name for kind in knoop.body if isinstance(kind, functies)
            }
        elif isinstance(knoop, functies):
            knopen[knoop.name] = set()
    return knopen


def _relatief(pad: Path, wortel: Path) -> str:
    try:
        return str(pad.relative_to(wortel))
    except ValueError:
        return str(pad)


def _controleer_tekst(
    tekst: str, herkomst: str, wortel: Path = REPOWORTEL
) -> list[str]:
    """Geef per onjuiste verwijzing in `tekst` een leesbare bevinding."""
    if "::" not in tekst:
        return []

    bevindingen: list[str] = []

    for treffer in VERWIJZING.finditer(tekst):
        padtekst = treffer.group("pad")
        node = treffer.group("node")
        methode = treffer.group("methode")
        regelnr = tekst.count("\n", 0, treffer.start())
        plek = f"{herkomst}:{regelnr + 1}"
        verwijzing = f"{padtekst}::{node}" + (f"::{methode}" if methode else "")

        status, treffers = _resolveer(padtekst, treffer.group("bestand"), wortel)

        if status == ONTBREEKT:
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing}, maar dat testbestand bestaat niet"
            )
            continue

        if status == BUITEN:
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing}, maar dat pad wijst buiten "
                f"de testwortel. Absolute paden, '..'-segmenten en symlinks die "
                f"buiten tests/ eindigen worden niet geaccepteerd"
            )
            continue

        if status == AMBIGU:
            namen = ", ".join(_relatief(p, wortel) for p in treffers)
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing} met een verkorte naam die "
                f"meerdere bestanden aanwijst: {namen}"
            )
            continue

        doel = treffers[0]
        knopen = _moduleknopen(doel)
        if knopen is None:
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing}, maar "
                f"{_relatief(doel, wortel)} is niet te lezen of te parsen"
            )
            continue

        if node not in knopen:
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing}, maar {node} bestaat niet "
                f"op moduleniveau in {_relatief(doel, wortel)}"
            )
            continue

        if methode is not None and methode not in knopen[node]:
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing}, maar {methode} bestaat niet "
                f"in {node} in {_relatief(doel, wortel)}"
            )
    return bevindingen


def _alle_bevindingen(wortel: Path = REPOWORTEL) -> list[str]:
    """Scan de hele repository. Fail-closed: een lege scan is zelf een bevinding.

    Per bronmap wordt zowel het bestaan als een niet-lege opbrengst geëist. Dat
    tweede is de rem op een versmalde scan: levert een bronmap plotseling nul
    bestanden op, dan is dat een bevinding in plaats van een stille pass.
    """
    per_map = _bestanden_per_bronmap(wortel)
    struikelblokken: list[str] = []
    for mapnaam in BRONMAPPEN:
        if mapnaam not in per_map:
            struikelblokken.append(
                f"scanwortel {wortel} mist {mapnaam}/ — de guard kan zo niets "
                f"bewijzen en faalt daarom expliciet in plaats van leeg te slagen"
            )
        elif not per_map[mapnaam]:
            struikelblokken.append(
                f"scanwortel {wortel}: {mapnaam}/ levert nul te scannen "
                f"Python-bestanden op — de scan is leeg en bewijst dus niets"
            )
    if struikelblokken:
        return struikelblokken

    bevindingen: list[str] = []
    for pad in _te_scannen_bestanden(wortel):
        try:
            tekst = pad.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as fout:
            bevindingen.append(
                f"{_relatief(pad, wortel)} is niet leesbaar "
                f"({type(fout).__name__}), dus niet te controleren"
            )
            continue
        bevindingen.extend(_controleer_tekst(tekst, _relatief(pad, wortel), wortel))
    return bevindingen


def test_geen_verwijzing_naar_een_niet_bestaande_pytestnode():
    bevindingen = _alle_bevindingen()
    assert not bevindingen, (
        "Verwijzingen naar een pytest-node die niet bestaat — de tekst belooft "
        "iets dat deze repository niet waarmaakt:\n  " + "\n  ".join(bevindingen)
    )


# --- de scanwortel moet de echte repository zijn ------------------------


# Twee geneste ankerbestanden, één per bronmap. Allebei doelwit van de
# verwijzingen die DEF-676 repareerde, dus ze verdwijnen niet stilletjes.
ANKERS = (
    "src/services/validation/evaluators/judgment_review.py",
    "tests/unit/validation/test_rule_runtime_matrix.py",
)


def test_scanwortel_is_de_echte_repository():
    # Bewust literals, niet set(BRONMAPPEN): anders beweegt de verwachting mee
    # met de constante en kan deze test een versmalde scan niet betrappen.
    assert (REPOWORTEL / "src").is_dir(), REPOWORTEL
    assert (REPOWORTEL / "tests").is_dir(), REPOWORTEL
    bestanden = _te_scannen_bestanden()
    assert {pad.relative_to(REPOWORTEL).parts[0] for pad in bestanden} == {
        "src",
        "tests",
    }
    assert DIT_BESTAND not in {pad.resolve() for pad in bestanden}


def test_scanwortel_omvat_geneste_ankerbestanden():
    """Beide ankers liggen diep genest, dus dit dwingt recursieve scanning af.

    Bestaan alléén is niet genoeg: de vorige vorm toetste `is_file()` en zou een
    versmalling van `rglob` naar `glob` hebben overleefd. Nu moet het anker
    daadwerkelijk in de scanset zitten.
    """
    gescand = {pad.resolve() for pad in _te_scannen_bestanden()}
    for anker in ANKERS:
        pad = REPOWORTEL / anker
        assert pad.is_file(), f"anker {anker} bestaat niet meer — werk ANKERS bij"
        assert pad.parent != REPOWORTEL, f"anker {anker} moet genest liggen"
        assert pad.resolve() in gescand, (
            f"anker {anker} wordt niet gescand — daalt de scan nog wel af in "
            f"submappen? Zonder recursie mist de guard vrijwel de hele repository"
        )


def test_ontbrekende_bronmap_faalt_expliciet(tmp_path):
    (tmp_path / "src" / "diep").mkdir(parents=True)  # tests/ ontbreekt bewust
    (tmp_path / "src" / "diep" / "iets.py").write_text("x = 1\n", encoding="utf-8")
    bevindingen = _alle_bevindingen(tmp_path)
    assert len(bevindingen) == 1, bevindingen
    assert "mist tests/" in bevindingen[0]


def test_lege_bronmap_faalt_expliciet(tmp_path):
    """Een bestaande maar leeg gescande bronmap mag niet stil doorgaan.

    Dit is de rem op een versmalde scan: levert `tests/` plotseling nul
    bestanden op, dan is dat zelf de bevinding.
    """
    (tmp_path / "src" / "diep").mkdir(parents=True)
    (tmp_path / "src" / "diep" / "iets.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()  # bestaat, maar zonder Python-bestanden
    bevindingen = _alle_bevindingen(tmp_path)
    assert len(bevindingen) == 1, bevindingen
    assert "tests/ levert nul te scannen" in bevindingen[0]


def test_lege_wortel_slaagt_niet_vacuum(tmp_path):
    bevindingen = _alle_bevindingen(tmp_path)
    assert len(bevindingen) == 2, bevindingen
    assert any("mist src/" in b for b in bevindingen), bevindingen
    assert any("mist tests/" in b for b in bevindingen), bevindingen


# --- de aggregatielaag moet zelf kunnen falen ---------------------------


def _mini_repo(tmp_path: Path) -> Path:
    """Minirepo waarin élk bestand genest ligt.

    De nesting is opzettelijk: lag er ook maar één overtreding op het eerste
    niveau, dan zou een versmalling van `rglob` naar `glob` onopgemerkt blijven.
    Nu levert die versmalling nul bestanden per bronmap op en slaan de
    fail-closed-controle en de aggregatietest allebei aan.
    """
    (tmp_path / "src" / "diep" / "genest").mkdir(parents=True)
    (tmp_path / "tests" / "diep" / "doel").mkdir(parents=True)
    (tmp_path / "tests" / "diep" / "doel" / "test_doel.py").write_text(
        "class TestBestaat:\n    def test_methode(self): ...\n", encoding="utf-8"
    )
    (tmp_path / "src" / "diep" / "genest" / "module.py").write_text(
        "# zie tests/diep/doel/test_doel.py::TestBestaatNiet\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "diep" / "test_iets.py").write_text(
        "# zie tests/diep/doel/test_doel.py::test_bestaat_niet\n", encoding="utf-8"
    )
    return tmp_path


def test_alle_bevindingen_aggregeert_over_src_en_tests(tmp_path):
    # Beide overtredingen liggen genest, dus deze test bewijst tegelijk dat de
    # scan recursief is: zonder afdaling levert elke bronmap nul bestanden en
    # slaat de fail-closed-controle aan.
    wortel = _mini_repo(tmp_path)
    bevindingen = _alle_bevindingen(wortel)
    assert len(bevindingen) == 2, bevindingen
    assert any(
        b.startswith("src/diep/genest/module.py:") for b in bevindingen
    ), bevindingen
    assert any(
        b.startswith("tests/diep/test_iets.py:") for b in bevindingen
    ), bevindingen


def test_onleesbaar_bestand_levert_een_bevinding(tmp_path):
    wortel = _mini_repo(tmp_path)
    (wortel / "src" / "kapot.py").write_bytes(b"# zie a.py::B \xff\xfe niet-utf8\n")
    bevindingen = _alle_bevindingen(wortel)
    assert any("niet leesbaar" in b for b in bevindingen), bevindingen


# --- de guard zelf moet kunnen falen ------------------------------------


def test_guard_signaleert_een_ontbrekend_bestand(tmp_path):
    wortel = _mini_repo(tmp_path)
    bevindingen = _controleer_tekst(
        "# zie tests/doel/test_ontbreekt.py::TestIets", "synthetisch", wortel
    )
    assert len(bevindingen) == 1, bevindingen
    assert "dat testbestand bestaat niet" in bevindingen[0]


def test_guard_signaleert_een_ontbrekende_klasse(tmp_path):
    wortel = _mini_repo(tmp_path)
    bevindingen = _controleer_tekst(
        "# zie tests/diep/doel/test_doel.py::TestBestaatNiet", "synthetisch", wortel
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_accepteert_een_bestaande_klasse(tmp_path):
    wortel = _mini_repo(tmp_path)
    assert (
        _controleer_tekst(
            "# zie tests/diep/doel/test_doel.py::TestBestaat", "synthetisch", wortel
        )
        == []
    )


def test_guard_accepteert_een_bestaande_methode(tmp_path):
    wortel = _mini_repo(tmp_path)
    assert (
        _controleer_tekst(
            "# zie tests/diep/doel/test_doel.py::TestBestaat::test_methode",
            "synthetisch",
            wortel,
        )
        == []
    )


def test_guard_signaleert_een_ontbrekende_methode(tmp_path):
    wortel = _mini_repo(tmp_path)
    bevindingen = _controleer_tekst(
        "# zie tests/diep/doel/test_doel.py::TestBestaat::test_bestaat_niet",
        "synthetisch",
        wortel,
    )
    assert len(bevindingen) == 1, bevindingen
    assert "test_bestaat_niet bestaat niet in TestBestaat" in bevindingen[0]


def test_guard_keurt_een_methode_niet_goed_als_modulenode(tmp_path):
    # test_methode bestaat wél, maar als methode — niet op moduleniveau.
    wortel = _mini_repo(tmp_path)
    bevindingen = _controleer_tekst(
        "# zie tests/diep/doel/test_doel.py::test_methode", "synthetisch", wortel
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_voegt_losse_stringstatements_niet_samen(tmp_path):
    """Twee losse stringstatements zijn geen impliciete concatenatie.

    De geldige verwijzing staat in het eerste statement; `"nu"` staat daar los
    van. Wie de tekst tussen de quotes wegknipt plakt er `TestBestaatnu` van —
    een node die nergens bestaat — en keurt daarmee correcte code af.
    """
    wortel = _mini_repo(tmp_path)
    tekst = 'x = "tests/diep/doel/test_doel.py::TestBestaat"\n"nu"\n'

    assert _controleer_tekst(tekst, "synthetisch", wortel) == []


def test_guard_meldt_twee_kapotte_verwijzingen_in_een_tekst(tmp_path):
    wortel = _mini_repo(tmp_path)
    tekst = (
        "# zie tests/diep/doel/test_doel.py::TestWegA\n"
        "# en tests/diep/doel/test_doel.py::TestWegB\n"
    )
    bevindingen = _controleer_tekst(tekst, "synthetisch", wortel)
    assert len(bevindingen) == 2, bevindingen
    assert bevindingen[0].startswith("synthetisch:1")
    assert bevindingen[1].startswith("synthetisch:2")


# --- paden mogen de testwortel niet verlaten ---------------------------
#
# Elk extern bestand hieronder bevat een geldige, bestaande node. Wordt zo'n
# verwijzing afgewezen, dan komt dat dus door de padvalidatie en niet doordat
# het bestand of de node toevallig ontbreekt.


def _extern_testbestand(tmp_path: Path, naam: str = "test_extern.py") -> Path:
    buiten = tmp_path / "buiten"
    buiten.mkdir(exist_ok=True)
    doel = buiten / naam
    doel.write_text("class TestExtern:\n    def test_m(self): ...\n", encoding="utf-8")
    return doel


def test_guard_wijst_een_absoluut_pad_buiten_de_wortel_af(tmp_path):
    wortel = _mini_repo(tmp_path / "repo")
    extern = _extern_testbestand(tmp_path)

    bevindingen = _controleer_tekst(
        f"# zie {extern}::TestExtern", "synthetisch", wortel
    )

    assert len(bevindingen) == 1, bevindingen
    assert "buiten" in bevindingen[0], bevindingen[0]
    # Bewijst dat de regex het héle absolute pad pakt en niet pas vanaf het
    # teken na de eerste slash: anders zou hier een relatief pad staan.
    assert str(extern) in bevindingen[0], bevindingen[0]


def test_guard_wijst_een_pad_met_dubbele_punt_buiten_de_wortel_af(tmp_path):
    wortel = _mini_repo(tmp_path / "repo")
    _extern_testbestand(tmp_path)

    bevindingen = _controleer_tekst(
        "# zie ../buiten/test_extern.py::TestExtern", "synthetisch", wortel
    )

    assert len(bevindingen) == 1, bevindingen
    assert "buiten" in bevindingen[0], bevindingen[0]


def test_guard_wijst_een_symlink_naar_buiten_de_wortel_af(tmp_path):
    wortel = _mini_repo(tmp_path / "repo")
    doel = _extern_testbestand(tmp_path, "test_symdoel.py")
    link = wortel / "tests" / "diep" / "test_link.py"
    link.symlink_to(doel)
    assert link.is_file(), "de symlink moet naar een bestaand bestand wijzen"

    bevindingen = _controleer_tekst(
        "# zie test_link.py::TestExtern", "synthetisch", wortel
    )

    assert len(bevindingen) == 1, bevindingen
    assert "buiten" in bevindingen[0], bevindingen[0]


def test_guard_weigert_een_verkorte_naam_met_een_externe_kandidaat(tmp_path):
    """Gemengd geval: dezelfde verkorte naam bestaat intern én extern.

    Beide kandidaten dragen `TestX`, dus de verwijzing zou tegen elk van beide
    kloppen. Juist daarom mag de externe kandidaat niet stil worden
    weggefilterd: dan zou het interne bestand ten onrechte als uniek gelden en
    zou de uitkomst afhangen van wat er buiten de repository staat.
    """
    wortel = _mini_repo(tmp_path / "repo")

    extern = tmp_path / "buiten" / "test_mix.py"
    extern.parent.mkdir(exist_ok=True)
    extern.write_text("class TestX: ...\n", encoding="utf-8")

    intern = wortel / "tests" / "a" / "test_mix.py"
    intern.parent.mkdir(parents=True)
    intern.write_text("class TestX: ...\n", encoding="utf-8")

    link = wortel / "tests" / "b" / "test_mix.py"
    link.parent.mkdir(parents=True)
    link.symlink_to(extern)
    assert link.is_file(), "de symlink moet naar een bestaand bestand wijzen"

    bevindingen = _controleer_tekst("# zie test_mix.py::TestX", "synthetisch", wortel)

    assert len(bevindingen) == 1, bevindingen
    assert "buiten" in bevindingen[0], bevindingen[0]


def test_guard_accepteert_een_verwijzing_binnen_de_testwortel(tmp_path):
    wortel = _mini_repo(tmp_path / "repo")
    _extern_testbestand(tmp_path)

    assert (
        _controleer_tekst(
            "# zie tests/diep/doel/test_doel.py::TestBestaat", "synthetisch", wortel
        )
        == []
    )


def test_guard_meldt_een_ambigue_verkorte_bestandsnaam(tmp_path):
    for tak in ("a", "b"):
        map_ = tmp_path / "tests" / tak
        map_.mkdir(parents=True)
        (map_ / "test_dubbel.py").write_text("class TestIets: ...\n", encoding="utf-8")

    bevindingen = _controleer_tekst(
        "# zie test_dubbel.py::TestIets", "synthetisch", tmp_path
    )
    assert len(bevindingen) == 1, bevindingen
    assert "meerdere bestanden aanwijst" in bevindingen[0]


def test_guard_accepteert_een_unieke_verkorte_bestandsnaam(tmp_path):
    map_ = tmp_path / "tests" / "a"
    map_.mkdir(parents=True)
    (map_ / "test_uniek.py").write_text("def test_iets(): ...\n", encoding="utf-8")

    assert (
        _controleer_tekst("# zie test_uniek.py::test_iets", "synthetisch", tmp_path)
        == []
    )
