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
from pathlib import Path

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

# Naad tussen twee aangrenzende Python-stringliteralen. Black breekt een lange
# verwijzing zo af; zonder samenvoegen zou de guard juist die gevallen missen.
LITERAALNAAD = re.compile(r"['\"]\s*['\"]")

ONTBREEKT = "ontbreekt"
AMBIGU = "ambigu"
GEVONDEN = "gevonden"


def _te_scannen_bestanden(wortel: Path = REPOWORTEL) -> list[Path]:
    bestanden: list[Path] = []
    for mapnaam in BRONMAPPEN:
        for pad in sorted((wortel / mapnaam).rglob("*.py")):
            if pad.resolve() == DIT_BESTAND:
                continue
            bestanden.append(pad)
    return bestanden


def _samengevoegd(tekst: str) -> tuple[str, list[tuple[int, int]] | None]:
    """Voeg aangrenzende stringliteralen samen.

    Geeft de samengevoegde tekst plus grenzen waarmee een index in die tekst
    terugvertaald kan worden naar de oorspronkelijke tekst.
    """
    naden = list(LITERAALNAAD.finditer(tekst))
    if not naden:
        return tekst, None

    stukken: list[str] = []
    grenzen: list[tuple[int, int]] = []
    vorig = lengte = delta = 0
    for naad in naden:
        stuk = tekst[vorig : naad.start()]
        stukken.append(stuk)
        lengte += len(stuk)
        delta += naad.end() - naad.start()
        grenzen.append((lengte, delta))
        vorig = naad.end()
    stukken.append(tekst[vorig:])
    return "".join(stukken), grenzen


def _oorspronkelijke_index(index: int, grenzen: list[tuple[int, int]] | None) -> int:
    if grenzen is None:
        return index
    delta = 0
    for grens, cumulatief in grenzen:
        if index >= grens:
            delta = cumulatief
        else:
            break
    return index + delta


def _resolveer(
    padtekst: str, bestandsnaam: str, wortel: Path
) -> tuple[str, list[Path]]:
    """Los een verwijzing op tot (status, treffers)."""
    if "/" in padtekst:
        kandidaat = wortel / padtekst
        return (GEVONDEN, [kandidaat]) if kandidaat.is_file() else (ONTBREEKT, [])

    treffers = sorted((wortel / "tests").rglob(bestandsnaam))
    if not treffers:
        return ONTBREEKT, []
    if len(treffers) > 1:
        return AMBIGU, treffers
    return GEVONDEN, treffers


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

    doorzoekbaar, grenzen = _samengevoegd(tekst)
    bevindingen: list[str] = []

    for treffer in VERWIJZING.finditer(doorzoekbaar):
        padtekst = treffer.group("pad")
        node = treffer.group("node")
        methode = treffer.group("methode")
        regelnr = tekst.count("\n", 0, _oorspronkelijke_index(treffer.start(), grenzen))
        plek = f"{herkomst}:{regelnr + 1}"
        verwijzing = f"{padtekst}::{node}" + (f"::{methode}" if methode else "")

        status, treffers = _resolveer(padtekst, treffer.group("bestand"), wortel)

        if status == ONTBREEKT:
            bevindingen.append(
                f"{plek} verwijst naar {verwijzing}, maar dat testbestand bestaat niet"
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
    """Scan de hele repository. Fail-closed: een lege scan is zelf een bevinding."""
    ontbrekend = [m for m in BRONMAPPEN if not (wortel / m).is_dir()]
    if ontbrekend:
        return [
            f"scanwortel {wortel} mist {m}/ — de guard kan zo niets bewijzen "
            f"en faalt daarom expliciet in plaats van leeg te slagen"
            for m in ontbrekend
        ]

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


def test_scanwortel_is_de_echte_repository():
    # Bewust literals, niet set(BRONMAPPEN): anders beweegt de verwachting mee
    # met de constante en kan deze test een versmalde scan niet betrappen.
    assert (REPOWORTEL / "src").is_dir(), REPOWORTEL
    assert (REPOWORTEL / "tests").is_dir(), REPOWORTEL
    assert (
        REPOWORTEL / "src/services/validation/evaluators/judgment_review.py"
    ).is_file()
    assert (REPOWORTEL / "tests/unit/validation/test_rule_runtime_matrix.py").is_file()
    assert {
        pad.relative_to(REPOWORTEL).parts[0] for pad in _te_scannen_bestanden()
    } == {"src", "tests"}
    assert DIT_BESTAND not in {pad.resolve() for pad in _te_scannen_bestanden()}


def test_ontbrekende_bronmap_faalt_expliciet(tmp_path):
    (tmp_path / "src").mkdir()  # tests/ ontbreekt bewust
    bevindingen = _alle_bevindingen(tmp_path)
    assert len(bevindingen) == 1, bevindingen
    assert "mist tests/" in bevindingen[0]


def test_lege_wortel_slaagt_niet_vacuum(tmp_path):
    assert _alle_bevindingen(tmp_path), "een lege wortel moet fail-closed zijn"


# --- de aggregatielaag moet zelf kunnen falen ---------------------------


def _mini_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "doel").mkdir(parents=True)
    (tmp_path / "tests" / "doel" / "test_doel.py").write_text(
        "class TestBestaat:\n    def test_methode(self): ...\n", encoding="utf-8"
    )
    (tmp_path / "src" / "module.py").write_text(
        "# zie tests/doel/test_doel.py::TestBestaatNiet\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_iets.py").write_text(
        "# zie tests/doel/test_doel.py::test_bestaat_niet\n", encoding="utf-8"
    )
    return tmp_path


def test_alle_bevindingen_aggregeert_over_src_en_tests(tmp_path):
    wortel = _mini_repo(tmp_path)
    bevindingen = _alle_bevindingen(wortel)
    assert len(bevindingen) == 2, bevindingen
    assert any(b.startswith("src/module.py:") for b in bevindingen), bevindingen
    assert any(b.startswith("tests/test_iets.py:") for b in bevindingen), bevindingen


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
        "# zie tests/doel/test_doel.py::TestBestaatNiet", "synthetisch", wortel
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_accepteert_een_bestaande_klasse(tmp_path):
    wortel = _mini_repo(tmp_path)
    assert (
        _controleer_tekst(
            "# zie tests/doel/test_doel.py::TestBestaat", "synthetisch", wortel
        )
        == []
    )


def test_guard_accepteert_een_bestaande_methode(tmp_path):
    wortel = _mini_repo(tmp_path)
    assert (
        _controleer_tekst(
            "# zie tests/doel/test_doel.py::TestBestaat::test_methode",
            "synthetisch",
            wortel,
        )
        == []
    )


def test_guard_signaleert_een_ontbrekende_methode(tmp_path):
    wortel = _mini_repo(tmp_path)
    bevindingen = _controleer_tekst(
        "# zie tests/doel/test_doel.py::TestBestaat::test_bestaat_niet",
        "synthetisch",
        wortel,
    )
    assert len(bevindingen) == 1, bevindingen
    assert "test_bestaat_niet bestaat niet in TestBestaat" in bevindingen[0]


def test_guard_keurt_een_methode_niet_goed_als_modulenode(tmp_path):
    # test_methode bestaat wél, maar als methode — niet op moduleniveau.
    wortel = _mini_repo(tmp_path)
    bevindingen = _controleer_tekst(
        "# zie tests/doel/test_doel.py::test_methode", "synthetisch", wortel
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_ziet_een_over_stringliteralen_afgebroken_verwijzing(tmp_path):
    wortel = _mini_repo(tmp_path)
    afgebroken = '(\n    "tests/doel/test_doel.py"\n    "::TestBestaatNiet"\n)\n'
    bevindingen = _controleer_tekst(afgebroken, "synthetisch", wortel)
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_meldt_twee_kapotte_verwijzingen_in_een_tekst(tmp_path):
    wortel = _mini_repo(tmp_path)
    tekst = (
        "# zie tests/doel/test_doel.py::TestWegA\n"
        "# en tests/doel/test_doel.py::TestWegB\n"
    )
    bevindingen = _controleer_tekst(tekst, "synthetisch", wortel)
    assert len(bevindingen) == 2, bevindingen
    assert bevindingen[0].startswith("synthetisch:1")
    assert bevindingen[1].startswith("synthetisch:2")


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
