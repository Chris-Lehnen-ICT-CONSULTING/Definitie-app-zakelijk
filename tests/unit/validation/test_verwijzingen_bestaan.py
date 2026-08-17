"""DEF-676: elke `bestand.py::node`-verwijzing moet een bestaande node aanwijzen.

Code en tests wijzen elkaar geregeld aan met pytest-notatie —
``pad/naar/test_iets.py::TestKlasse`` of ``…::test_functie`` — om te zeggen:
*dit hoort daar*. Dat gebeurt in twee gedaanten:

- als **dekkingsclaim** ("het bewijs voor dit gedrag staat daar");
- als **draai-instructie** ("draai dit commando om X te zien").

Beide zijn verifieerbare beweringen over deze repository. Wijst zo'n
verwijzing naar een bestand of node die hier niet bestaat, dan is zij onwaar:
de dekkingsclaim suggereert dekking die er niet is, en het commando levert
niets op wanneer iemand het kopieert.

Deze guard maakt daar één uitvoerbare invariant van. Aanleiding was een
geparkeerd testbestand waar drie plekken in ``main`` naar bleven verwijzen;
de eerste run legde daarnaast drie draai-instructies met een verouderd
padprefix bloot.

Werking: scan elk Python-bestand onder ``src/`` en ``tests/``, zoek
verwijzingen met een expliciete node, los het bestand op en controleer via de
AST dat de node op **moduleniveau** bestaat.

Ontwerpkeuzes:

- **Alleen moduleniveau.** Een methode in een klasse of een geneste functie is
  geen zelfstandige pytest-node op de plek waar de verwijzing hem zet, dus
  ``ast.walk`` zou te veel goedkeuren. We lezen alleen ``module.body``.
- **Een verkorte bestandsnaam moet uniek zijn.** Nul treffers is ontbrekend,
  meerdere treffers is ambigu — dan kiezen we niet stil de eerste, want dan
  zou een verwijzing "geldig" heten op grond van een bestand dat de auteur
  misschien niet bedoelde.
- **Plandocumenten blijven buiten scope**: alleen ``.py`` wordt gescand, dus
  ``Create: tests/.../test_x.py`` in een plan is een toekomstgerichte
  instructie en geen bewering over het heden.
- **Dit bestand zelf wordt overgeslagen**, zodat de synthetische voorbeelden
  in de guardtests hieronder geen overtreding heten.

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

# Herkent het volledige pad én de verkorte variant, met klasse- of functienode:
#   tests/unit/validation/test_rule_contract.py::TestOordeelregels
#   test_rule_contract.py::test_iets
VERWIJZING = re.compile(
    r"(?P<pad>(?:[\w./-]+/)?(?P<bestand>test_\w+\.py))::(?P<node>[A-Za-z_]\w*)"
)

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


def _resolveer(
    padtekst: str, bestandsnaam: str, wortel: Path
) -> tuple[str, list[Path]]:
    """Los een verwijzing op tot (status, treffers).

    Een volledig pad wordt exact gecontroleerd. Een kale bestandsnaam slaagt
    alleen als er precies één bestand met die naam onder ``tests/`` staat.
    """
    if "/" in padtekst:
        kandidaat = wortel / padtekst
        return (GEVONDEN, [kandidaat]) if kandidaat.is_file() else (ONTBREEKT, [])

    treffers = sorted((wortel / "tests").rglob(bestandsnaam))
    if not treffers:
        return ONTBREEKT, []
    if len(treffers) > 1:
        return AMBIGU, treffers
    return GEVONDEN, treffers


def _modulenodes(pad: Path) -> set[str] | None:
    """Namen van klassen en functies op moduleniveau, of None bij parsefout."""
    try:
        boom = ast.parse(pad.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None
    soorten = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return {knoop.name for knoop in boom.body if isinstance(knoop, soorten)}


def _relatief(pad: Path, wortel: Path) -> str:
    try:
        return str(pad.relative_to(wortel))
    except ValueError:
        return str(pad)


def _controleer_tekst(
    tekst: str, herkomst: str, wortel: Path = REPOWORTEL
) -> list[str]:
    """Geef per onjuiste verwijzing in `tekst` een leesbare bevinding."""
    bevindingen: list[str] = []
    for regelnr, regel in enumerate(tekst.splitlines(), start=1):
        for treffer in VERWIJZING.finditer(regel):
            padtekst = treffer.group("pad")
            node = treffer.group("node")
            plek = f"{herkomst}:{regelnr}"
            verwijzing = f"{padtekst}::{node}"

            status, treffers = _resolveer(padtekst, treffer.group("bestand"), wortel)

            if status == ONTBREEKT:
                bevindingen.append(
                    f"{plek} verwijst naar {verwijzing}, maar dat testbestand "
                    f"bestaat niet"
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
            nodes = _modulenodes(doel)
            if nodes is None:
                bevindingen.append(
                    f"{plek} verwijst naar {verwijzing}, maar "
                    f"{_relatief(doel, wortel)} is niet te lezen of te parsen"
                )
                continue

            if node not in nodes:
                bevindingen.append(
                    f"{plek} verwijst naar {verwijzing}, maar {node} bestaat niet "
                    f"op moduleniveau in {_relatief(doel, wortel)}"
                )
    return bevindingen


def _alle_bevindingen(wortel: Path = REPOWORTEL) -> list[str]:
    bevindingen: list[str] = []
    for pad in _te_scannen_bestanden(wortel):
        bevindingen.extend(
            _controleer_tekst(
                pad.read_text(encoding="utf-8"), _relatief(pad, wortel), wortel
            )
        )
    return bevindingen


def test_geen_verwijzing_naar_een_niet_bestaande_pytestnode():
    bevindingen = _alle_bevindingen()
    assert not bevindingen, (
        "Verwijzingen naar een pytest-node die niet bestaat — de tekst belooft "
        "iets dat deze repository niet waarmaakt:\n  " + "\n  ".join(bevindingen)
    )


# --- de guard zelf moet kunnen falen ------------------------------------


def test_guard_signaleert_een_ontbrekend_bestand():
    bevindingen = _controleer_tekst(
        "# zie tests/unit/validation/test_bestaat_niet.py::TestIets", "synthetisch"
    )
    assert len(bevindingen) == 1, bevindingen
    assert "dat testbestand bestaat niet" in bevindingen[0]


def test_guard_signaleert_een_ontbrekende_klasse():
    bevindingen = _controleer_tekst(
        "# zie tests/unit/validation/test_rule_runtime_matrix.py::TestBestaatNiet",
        "synthetisch",
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_signaleert_een_ontbrekende_functie():
    bevindingen = _controleer_tekst(
        "# zie tests/unit/validation/test_rule_runtime_matrix.py::test_bestaat_niet",
        "synthetisch",
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_accepteert_een_bestaande_klasse():
    bevindingen = _controleer_tekst(
        "# zie tests/unit/validation/test_rule_runtime_matrix.py"
        "::TestAfgeleideTelling",
        "synthetisch",
    )
    assert bevindingen == []


def test_guard_accepteert_een_bestaande_functie():
    bevindingen = _controleer_tekst(
        "# zie tests/unit/services/prompts/test_json_based_rules_consolidation.py"
        "::test_visual_inspection_helper",
        "synthetisch",
    )
    assert bevindingen == []


def test_guard_keurt_een_methode_niet_goed_als_modulenode():
    # TestAfgeleideTelling bestaat wél, haar methode is géén module-level node.
    bevindingen = _controleer_tekst(
        "# zie tests/unit/validation/test_rule_runtime_matrix.py::test_telling_sluit_op_53",
        "synthetisch",
    )
    assert len(bevindingen) == 1, bevindingen
    assert "bestaat niet op moduleniveau" in bevindingen[0]


def test_guard_meldt_een_ambigue_verkorte_bestandsnaam(tmp_path):
    for tak in ("a", "b"):
        map_ = tmp_path / "tests" / tak
        map_.mkdir(parents=True)
        (map_ / "test_dubbel.py").write_text("class TestIets: ...\n", encoding="utf-8")

    bevindingen = _controleer_tekst(
        "# zie test_dubbel.py::TestIets", "synthetisch", wortel=tmp_path
    )
    assert len(bevindingen) == 1, bevindingen
    assert "meerdere bestanden aanwijst" in bevindingen[0]


def test_guard_accepteert_een_unieke_verkorte_bestandsnaam(tmp_path):
    map_ = tmp_path / "tests" / "a"
    map_.mkdir(parents=True)
    (map_ / "test_uniek.py").write_text("def test_iets(): ...\n", encoding="utf-8")

    bevindingen = _controleer_tekst(
        "# zie test_uniek.py::test_iets", "synthetisch", wortel=tmp_path
    )
    assert bevindingen == []


def test_guard_scant_zowel_src_als_tests_en_niet_zichzelf():
    bestanden = _te_scannen_bestanden()
    assert {pad.relative_to(REPOWORTEL).parts[0] for pad in bestanden} == set(
        BRONMAPPEN
    )
    assert DIT_BESTAND not in {pad.resolve() for pad in bestanden}
