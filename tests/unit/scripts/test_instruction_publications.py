"""Tests voor de instructiepublicaties en hun trackingpoort (ALG-399).

De repository publiceert haar instructies uit één bron: `instructions/blocks/`.
`instructions/manifest.json` bepaalt welke publicaties daaruit ontstaan en
`instructions/outputs.json` waar ze terechtkomen. `scripts/render-instructions.py`
genereert, `scripts/check-instruction-publications.py` bewaakt.

Deze tests toetsen vier dingen die anders stil kunnen wegvallen:

1. **Verplichte output** — elk pad uit `outputs.json` bestaat echt.
2. **Drift** — een met de hand gewijzigde publicatie wordt gezien.
3. **Staged/tracked-contract** — `--require-tracked` accepteert de index als
   bron van waarheid, zodat de poort al vóór de commit klopt.
4. **Rootguard-koppeling** — AGENTS.md is tegelijk gepubliceerde output én
   toegestaan rootbestand; die twee mogen niet uiteenlopen.

De volledige keten (alle negen outputs) wordt in een wegwerp-fixture bewezen.
Dat is bewust: `.claude/rules/` is in deze werkmap beschermd, dus daar staan de
drie gegenereerde verwijzingen pas na de handmatige patch. De fixture installeert
niets en laadt geen projectconfiguratie; ze kopieert alleen bestanden.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUCTIES = _REPO_ROOT / "instructions"
_SCRIPTS = _REPO_ROOT / "scripts"

# Beschermde paden: gegenereerd, maar in deze werkmap niet schrijfbaar. Ze
# komen uit het git-apply-voorstel en zijn tot dan de enige verwachte rode tak.
_BESCHERMD = (
    ".claude/rules/patterns.md",
    ".claude/rules/project-rules.md",
    ".claude/rules/streamlit-patterns.md",
)

_PATCHUITLEG = (
    "Dit pad staat onder .claude/rules/ en is in deze werkmap beschermd. "
    "Pas eerst het git-apply-voorstel toe "
    "(/private/tmp/ALG399-definitie-integratie-20260910/)."
)

# Systeem- en gebruikersconfig buitensluiten: gpgsign, hooksPath of een
# init-template van de ontwikkelaar mag de wegwerp-repo niet laten kantelen.
_GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _outputs() -> dict[str, list[str]]:
    config = json.loads((_INSTRUCTIES / "outputs.json").read_text(encoding="utf-8"))
    return config["files"]


def _render(root: Path, publicatie: str) -> bytes:
    """Roep de bestaande renderer aan; die importeert zijn eigen lib uit scripts/."""
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(root / "scripts" / "render-instructions.py"),
            "--manifest",
            str(root / "instructions" / "manifest.json"),
            "--publication",
            publicatie,
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    return result.stdout


def _check(root: Path, *, require_tracked: bool) -> subprocess.CompletedProcess:
    argv = [
        sys.executable,
        "-B",
        "-E",
        "-S",
        str(root / "scripts" / "check-instruction-publications.py"),
        "--root",
        str(root),
    ]
    if require_tracked:
        argv.append("--require-tracked")
    return subprocess.run(
        argv, capture_output=True, text=True, env=_GIT_ENV, check=False
    )


def _git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=_GIT_ENV,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} faalde ({result.returncode}): "
            f"{result.stdout}{result.stderr}"
        )


@pytest.fixture
def keten(tmp_path: Path) -> Path:
    """Complete, getrackte instructieketen in een wegwerp-repo.

    Kopieert bron en gereedschap, rendert alle negen outputs met de bestaande
    renderer en commit ze. Hier zijn ook de drie beschermde paden gewoon
    schrijfbaar, zodat de volledige keten toetsbaar is.
    """
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    shutil.copytree(_INSTRUCTIES, root / "instructions")
    for naam in (
        "render-instructions.py",
        "check-instruction-publications.py",
    ):
        shutil.copy2(_SCRIPTS / naam, root / "scripts" / naam)
    shutil.copytree(_SCRIPTS / "lib", root / "scripts" / "lib")

    for relatief, publicaties in _outputs().items():
        doel = root / relatief
        doel.parent.mkdir(parents=True, exist_ok=True)
        doel.write_bytes(_render(root, publicaties[0]))

    _git(root, "init", "-q", "--template=")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "config", "core.hooksPath", "/dev/null")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "instructiepublicaties")
    return root


# --- 1. verplichte output --------------------------------------------------


@pytest.mark.parametrize("relatief", sorted(_outputs()))
def test_geconfigureerde_output_bestaat_en_klopt(relatief):
    """Elke geconfigureerde publicatie staat er, met exact de gerenderde bytes."""
    doel = _REPO_ROOT / relatief
    uitleg = _PATCHUITLEG if relatief in _BESCHERMD else ""

    assert doel.is_file(), f"ontbrekende publicatie: {relatief}. {uitleg}"
    for publicatie in _outputs()[relatief]:
        assert doel.read_bytes() == _render(
            _REPO_ROOT, publicatie
        ), f"{relatief} wijkt af van publicatie {publicatie}. {uitleg}"


def test_alle_negen_outputs_en_elf_controles_slagen(keten):
    """De keten als geheel: negen bestanden, elf publicatiecontroles."""
    result = _check(keten, require_tracked=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "9 bestanden, 11 publicatiecontroles" in result.stdout


def test_ontbrekende_output_wordt_gemeld(keten):
    doel = keten / "instructions" / "generated" / "cowork-project.md"
    doel.unlink()

    result = _check(keten, require_tracked=False)

    assert result.returncode == 1
    assert "Ontbreekt: instructions/generated/cowork-project.md" in result.stdout


# --- 2. drift --------------------------------------------------------------


def test_handmatige_wijziging_in_output_wordt_gezien(keten):
    """De kern van de poort: publicaties met de hand bijwerken mag niet loont."""
    doel = keten / "AGENTS.md"
    doel.write_bytes(doel.read_bytes() + b"\nextra regel\n")

    result = _check(keten, require_tracked=False)

    assert result.returncode == 1
    assert "Afwijkende publicatie: AGENTS.md" in result.stdout


def test_wijziging_in_het_bronblok_zonder_hergeneratie_wordt_gezien(keten):
    """Andersom: wie de bron aanpast en vergeet te renderen, valt ook door."""
    blok = keten / "instructions" / "blocks" / "definitie.policy.md"
    blok.write_text(
        blok.read_text(encoding="utf-8") + "\nNieuwe regel.\n", encoding="utf-8"
    )

    result = _check(keten, require_tracked=False)

    assert result.returncode == 1
    # Alle publicaties van dit blok lopen mee, niet alleen de eerste.
    assert "Afwijkende publicatie: CLAUDE.md" in result.stdout
    assert "Afwijkende publicatie: AGENTS.md" in result.stdout


# --- 3. staged/tracked-contract --------------------------------------------


def test_ongetrackte_publicatie_faalt_onder_require_tracked(keten):
    """Een schone clone mag geen handgemaakte, ongetrackte instructie nodig hebben."""
    _git(keten, "rm", "-q", "--cached", "AGENTS.md")

    zonder_vlag = _check(keten, require_tracked=False)
    met_vlag = _check(keten, require_tracked=True)

    # Zonder de vlag is dit geen fout: de inhoud klopt nog steeds.
    assert zonder_vlag.returncode == 0, zonder_vlag.stdout + zonder_vlag.stderr
    assert met_vlag.returncode == 1
    assert "Niet getrackt: AGENTS.md" in met_vlag.stdout


def test_ongetrackt_bronblok_faalt_onder_require_tracked(keten):
    """Ook het gereedschap en de bron zelf moeten mee in de clone."""
    _git(keten, "rm", "-q", "--cached", "instructions/blocks/guidelines.policy.md")

    result = _check(keten, require_tracked=True)

    assert result.returncode == 1
    assert "Niet getrackt: instructions/blocks/guidelines.policy.md" in result.stdout


def test_gestagede_publicatie_geldt_als_getrackt(keten):
    """De index is de bron van waarheid, zodat de poort vóór de commit klopt."""
    _git(keten, "rm", "-q", "--cached", "AGENTS.md")
    _git(keten, "add", "--", "AGENTS.md")

    result = _check(keten, require_tracked=True)

    assert result.returncode == 0, result.stdout + result.stderr


# --- 4. rootguard-koppeling ------------------------------------------------


def test_agents_md_is_publicatie_en_toegestaan_rootbestand():
    """De trackingmigratie klopt alleen als beide kanten hem kennen."""
    guard = (_SCRIPTS / "ci" / "check_root_allowlist.sh").read_text(encoding="utf-8")

    assert "AGENTS.md" in _outputs()
    assert '"AGENTS.md"' in guard


def test_elke_root_publicatie_staat_op_de_allowlist():
    """Publiceert het manifest ooit een nieuw rootbestand, dan valt dit om."""
    guard = (_SCRIPTS / "ci" / "check_root_allowlist.sh").read_text(encoding="utf-8")
    in_de_root = [pad for pad in _outputs() if "/" not in pad]
    ontbreekt = [pad for pad in in_de_root if f'"{pad}"' not in guard]

    assert not ontbreekt, f"niet op de allowlist in de guard: {ontbreekt}"


# --- archief: de oorspronkelijke bronnen blijven aanwijsbaar ---------------


def _archiefindex() -> dict:
    return json.loads(
        (_INSTRUCTIES / "source-archives" / "index.json").read_text(encoding="utf-8")
    )


def test_archief_bewaart_alle_zes_oorspronkelijke_bronnen():
    index = _archiefindex()

    assert set(index["files"]) == {
        "CLAUDE.md",
        "AGENTS.md",
        ".claude/rules/patterns.md",
        ".claude/rules/project-rules.md",
        ".claude/rules/streamlit-patterns.md",
        "docs/guidelines/AGENTS.md",
    }


def test_archiefbestanden_zijn_padloos_en_inert():
    """Het archief mag geen .claude/rules-pad nabouwen: het is dode opslag."""
    index = _archiefindex()
    map_ = _INSTRUCTIES / "source-archives" / "files"
    namen = set()

    for relatief, entry in index["files"].items():
        naam = Path(entry["archive"]).name
        assert (
            entry["archive"] == f"instructions/source-archives/files/{naam}"
        ), relatief
        assert naam not in namen, f"botsende archiefnaam: {naam}"
        namen.add(naam)

    assert not [pad for pad in map_.iterdir() if pad.is_dir()]
    assert {pad.name for pad in map_.iterdir()} == namen


def test_archiefinhoud_komt_overeen_met_de_vastgelegde_hash():
    """Bronidentiteit: de hash hoort bij de oorspronkelijke bytes, niet bij het pad."""
    import hashlib

    for relatief, entry in _archiefindex()["files"].items():
        inhoud = (_REPO_ROOT / entry["archive"]).read_bytes()

        assert hashlib.sha256(inhoud).hexdigest() == entry["sha256"], relatief


# --- CI en documentatie ----------------------------------------------------


def _ci_workflow() -> str:
    return (_REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def test_ci_draait_de_trackingpoort_voor_de_dependency_installatie():
    """Vóór installeren: de poort mag geen projectdependencies nodig hebben."""
    workflow = _ci_workflow()
    commando = (
        "python -B -E -S scripts/check-instruction-publications.py --require-tracked"
    )

    assert commando in workflow
    assert workflow.index(commando) < workflow.index("Install dependencies")


def test_ci_behoudt_de_bestaande_gates():
    workflow = _ci_workflow()

    for target in ("make grep-check", "make test-tool-gates", "make test-acceptance"):
        assert target in workflow, target


def test_readme_documenteert_regenereren_en_controleren():
    readme = (_INSTRUCTIES / "README.md").read_text(encoding="utf-8")

    assert "scripts/render-instructions.py" in readme
    assert "--require-tracked" in readme
    assert "source-archives" in readme
