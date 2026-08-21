"""Tests voor de root-allowlist-guard (DEF-685).

Borgt dat de guard uit `.claude/rules/project-rules.md` regel 1 machinaal
wordt afgedwongen: een getrackt of gestaged rootbestand dat niet op de
allowlist staat, blokkeert. Untracked bestanden blijven buiten schot, zodat
de guard het openstaande trackingbesluit uit ALG-399 niet forceert.

Elke testcase raakt precies één tak van de guard, zodat een groene suite
niet per ongeluk op een andere regel steunt dan bedoeld.
"""

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_root_allowlist.sh"

# Rootbestanden die volgens de normtekst zijn toegestaan; genoeg om een
# geloofwaardige schone root na te bouwen zonder de echte repo te kopiëren.
_TOEGESTAAN = ("README.md", "CLAUDE.md", "Makefile", "pyproject.toml")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} faalde ({result.returncode}): "
            f"{result.stdout}{result.stderr}"
        )
    return result


def _init_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    # Globale config buitensluiten: commit.gpgsign of een core.hooksPath van de
    # ontwikkelaar mag deze wegwerp-repo niet laten struikelen.
    _git(tmp_path, "config", "commit.gpgsign", "false")
    _git(tmp_path, "config", "core.hooksPath", "/dev/null")
    return tmp_path


def _schrijf(repo: Path, naam: str, inhoud: str = "x\n") -> Path:
    pad = repo / naam
    pad.parent.mkdir(parents=True, exist_ok=True)
    pad.write_text(inhoud)
    return pad


def _stage(repo: Path, *namen: str) -> None:
    for naam in namen:
        _git(repo, "add", "--", naam)


def _commit(repo: Path, *namen: str) -> None:
    _stage(repo, *namen)
    _git(repo, "commit", "-q", "-m", "test")


def _run(repo: Path, *, ci: bool) -> subprocess.CompletedProcess:
    # GITHUB_ACTIONS expliciet zetten: draait de suite zelf in CI, dan zou de
    # pre-commitmodus anders nooit getoetst worden.
    env = dict(os.environ)
    env["GITHUB_ACTIONS"] = "true" if ci else "false"
    return subprocess.run(
        ["bash", str(_SCRIPT), str(repo)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _uitvoer(result: subprocess.CompletedProcess) -> str:
    return result.stdout + result.stderr


# --- schone root -----------------------------------------------------------


def test_schone_root_slaagt_in_ci_modus(tmp_path):
    repo = _init_repo(tmp_path)
    for naam in _TOEGESTAAN:
        _schrijf(repo, naam)
    _commit(repo, *_TOEGESTAAN)

    result = _run(repo, ci=True)

    assert result.returncode == 0, _uitvoer(result)


def test_schone_root_slaagt_in_precommit_modus(tmp_path):
    repo = _init_repo(tmp_path)
    for naam in _TOEGESTAAN:
        _schrijf(repo, naam)
    _stage(repo, *_TOEGESTAAN)

    result = _run(repo, ci=False)

    assert result.returncode == 0, _uitvoer(result)


# --- onbekend rootbestand --------------------------------------------------


def test_tracked_onbekend_rootbestand_faalt_in_ci(tmp_path):
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _schrijf(repo, "syn-result.md")
    _commit(repo, "README.md", "syn-result.md")

    result = _run(repo, ci=True)

    assert result.returncode == 1
    uitvoer = _uitvoer(result)
    assert "syn-result.md" in uitvoer
    # Niet de AGENTS.md-tak: die heeft een eigen melding en zou hier maskeren.
    assert "ALG-399" not in uitvoer


def test_staged_onbekend_rootbestand_faalt_in_precommit(tmp_path):
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")
    _schrijf(repo, "analyse-output.txt")
    _stage(repo, "analyse-output.txt")

    result = _run(repo, ci=False)

    assert result.returncode == 1
    assert "analyse-output.txt" in _uitvoer(result)


def test_ongestaged_onbekend_rootbestand_slaagt_in_precommit(tmp_path):
    # De pre-commitmodus kijkt naar de index, niet naar de werkmap: een
    # onbekend bestand dat nog niet gestaged is, blokkeert de commit niet.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")
    _schrijf(repo, "kladblok.md")

    result = _run(repo, ci=False)

    assert result.returncode == 0, _uitvoer(result)


def test_untracked_onbekend_rootbestand_slaagt_in_ci(tmp_path):
    # Kernafspraak: de guard forceert untracked bestanden niet.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")
    _schrijf(repo, "kladblok.md")

    result = _run(repo, ci=True)

    assert result.returncode == 0, _uitvoer(result)


# --- AGENTS.md -------------------------------------------------------------


def test_tracked_agents_md_faalt_met_verwijzing_naar_alg399(tmp_path):
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _schrijf(repo, "AGENTS.md")
    _commit(repo, "README.md", "AGENTS.md")

    result = _run(repo, ci=True)

    assert result.returncode == 1
    uitvoer = _uitvoer(result)
    assert "AGENTS.md" in uitvoer
    assert "ALG-399" in uitvoer


def test_staged_agents_md_faalt_in_precommit(tmp_path):
    # De footgun uit de review van PR #404: git add -A stageert AGENTS.md.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")
    _schrijf(repo, "AGENTS.md")
    _git(repo, "add", "-A")

    result = _run(repo, ci=False)

    assert result.returncode == 1
    assert "ALG-399" in _uitvoer(result)


def test_untracked_agents_md_slaagt(tmp_path):
    # Zolang ALG-399 niet heeft beslist, is de untracked snapshot legitiem.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")
    _schrijf(repo, "AGENTS.md")

    result = _run(repo, ci=True)

    assert result.returncode == 0, _uitvoer(result)


# --- patronen en scope -----------------------------------------------------


@pytest.mark.parametrize(
    "naam",
    [
        "requirements.txt",
        "requirements.in",
        "requirements-dev.txt",
        "requirements-dev.in",
        ".gitleaks.toml",
        ".gitleaksignore",
        ".gitignore",
        ".pre-commit-config.yaml",
        "CHANGELOG.md",
        "pytest.ini",
        "Makefile",
    ],
)
def test_toegestaan_rootbestand_slaagt(tmp_path, naam):
    repo = _init_repo(tmp_path)
    _schrijf(repo, naam)
    _commit(repo, naam)

    result = _run(repo, ci=True)

    assert result.returncode == 0, _uitvoer(result)


def test_bestand_in_subdirectory_wordt_genegeerd(tmp_path):
    # De regel gaat over de root; docs/ en scripts/ vallen er niet onder.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _schrijf(repo, "docs/analyses/rapport.md")
    _commit(repo, "README.md", "docs/analyses/rapport.md")

    result = _run(repo, ci=True)

    assert result.returncode == 0, _uitvoer(result)


def test_bestandsnaam_met_spatie_wordt_correct_gemeld(tmp_path):
    # git quote-path zou "mijn rapport.md" anders als twee namen opleveren.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _schrijf(repo, "mijn rapport.md")
    _commit(repo, "README.md", "mijn rapport.md")

    result = _run(repo, ci=True)

    assert result.returncode == 1
    assert "mijn rapport.md" in _uitvoer(result)


# --- fail-closed -----------------------------------------------------------


def test_buiten_een_git_repo_faalt_de_guard_gesloten(tmp_path):
    # Zonder werkboom kan de guard niets vaststellen. Groen melden zou hier het
    # gevaarlijkst zijn: de gebruiker denkt dat er gecontroleerd is.
    result = _run(tmp_path, ci=True)

    assert result.returncode == 1
    assert "git-werkboom" in _uitvoer(result)


def test_falende_git_faalt_gesloten(tmp_path, monkeypatch):
    # Bijvoorbeeld "detected dubious ownership" of een kapotte index: git geeft
    # een foutstatus en geen uitvoer. Een lege lijst mag niet als schoon gelden.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")

    nepbin = tmp_path / "nepbin"
    nepbin.mkdir()
    nepgit = nepbin / "git"
    nepgit.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        "  rev-parse) exit 0 ;;\n"
        '  *) echo "fatal: detected dubious ownership" >&2; exit 128 ;;\n'
        "esac\n"
    )
    nepgit.chmod(0o755)

    env = dict(os.environ)
    env["GITHUB_ACTIONS"] = "true"
    env["PATH"] = f"{nepbin}:{env['PATH']}"
    result = subprocess.run(
        ["bash", str(_SCRIPT), str(repo)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "geen bruikbare bestandslijst" in (result.stdout + result.stderr)


def test_staged_onbekend_bestand_zonder_commits_faalt(tmp_path):
    # Derde tak van list_candidates: een repo zonder HEAD valt terug op
    # git ls-files --cached. Zonder deze test is die tak alleen positief gedekt.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "syn-result.md")
    _stage(repo, "syn-result.md")

    result = _run(repo, ci=False)

    assert result.returncode == 1
    assert "syn-result.md" in _uitvoer(result)


# --- meldingen zijn modus-specifiek ----------------------------------------


def test_ci_melding_wijst_op_git_rm_cached(tmp_path):
    # Bij een reeds gecommit bestand helpt unstagen niet; de tip moet kloppen.
    repo = _init_repo(tmp_path)
    _schrijf(repo, "AGENTS.md")
    _commit(repo, "AGENTS.md")

    uitvoer = _uitvoer(_run(repo, ci=True))

    assert "git rm --cached" in uitvoer
    assert "git restore --staged" not in uitvoer


def test_precommit_melding_wijst_op_restore_staged(tmp_path):
    repo = _init_repo(tmp_path)
    _schrijf(repo, "README.md")
    _commit(repo, "README.md")
    _schrijf(repo, "AGENTS.md")
    _stage(repo, "AGENTS.md")

    uitvoer = _uitvoer(_run(repo, ci=False))

    assert "git restore --staged" in uitvoer
    assert "git rm --cached" not in uitvoer


# --- globs sluiten af op de extensie ---------------------------------------


@pytest.mark.parametrize(
    "naam",
    [
        "requirements-analyse-2026.md",
        "requirements.txt.bak",
        ".gitleaks-dump.json",
    ],
)
def test_werkbestand_met_toegestaan_voorvoegsel_faalt(tmp_path, naam):
    # Een kaal requirements* of .gitleaks* zou juist de categorie doorlaten die
    # de regel moet tegenhouden.
    repo = _init_repo(tmp_path)
    _schrijf(repo, naam)
    _commit(repo, naam)

    result = _run(repo, ci=True)

    assert result.returncode == 1
    assert naam in _uitvoer(result)


# --- norm en allowlist mogen niet uiteenlopen ------------------------------


def _regel_een() -> str:
    tekst = (_REPO_ROOT / ".claude" / "rules" / "project-rules.md").read_text(
        encoding="utf-8"
    )
    for regel in tekst.splitlines():
        if regel.startswith("1. **Geen ad-hoc bestanden in project root**"):
            return regel
    raise AssertionError("regel 1 niet gevonden in project-rules.md")


# Norm-token uit regel 1 -> een concreet bestand dat eronder valt.
_NORM_VOORBEELDEN = {
    "README.md": "README.md",
    "CLAUDE.md": "CLAUDE.md",
    "Makefile": "Makefile",
    "CHANGELOG.md": "CHANGELOG.md",
    "requirements*": "requirements.txt",
    "pyproject.toml": "pyproject.toml",
    "pytest.ini": "pytest.ini",
    ".pre-commit-config.yaml": ".pre-commit-config.yaml",
    ".gitignore": ".gitignore",
    ".gitleaks*": ".gitleaks.toml",
}


def test_normtekst_noemt_nog_elk_toegestaan_rootbestand():
    # Kant 1 van de koppeling: haalt iemand een naam uit regel 1, dan faalt dit.
    regel = _regel_een()
    ontbreekt = [token for token in _NORM_VOORBEELDEN if token not in regel]

    assert not ontbreekt, f"regel 1 noemt deze niet meer: {ontbreekt}"


def test_guard_accepteert_alles_wat_de_normtekst_noemt(tmp_path):
    # Kant 2: haalt iemand een naam uit ALLOWED_ROOT_FILES, dan faalt dit.
    repo = _init_repo(tmp_path)
    voorbeelden = sorted(set(_NORM_VOORBEELDEN.values()))
    for naam in voorbeelden:
        _schrijf(repo, naam)
    _commit(repo, *voorbeelden)

    result = _run(repo, ci=True)

    assert result.returncode == 0, _uitvoer(result)


def test_normtekst_verwijst_naar_de_guard():
    # De wederzijdse verwijzing is een acceptatiecriterium van DEF-685.
    assert "check_root_allowlist.sh" in _regel_een()


def test_normtekst_houdt_agents_md_ongetrackt():
    # De AGENTS.md-uitzondering in de guard hangt aan deze zin; verdwijnt zij,
    # dan moet de guard-tak opnieuw worden afgewogen (ALG-399).
    regel = _regel_een()

    assert "AGENTS.md" in regel
    assert "ALG-399" in regel


# --- de echte repo ---------------------------------------------------------


def test_echte_repo_is_schoon():
    # Zonder deze test kan de guard groen zijn op fixtures en toch de CI van
    # iedereen breken.
    result = _run(_REPO_ROOT, ci=True)

    assert result.returncode == 0, _uitvoer(result)
