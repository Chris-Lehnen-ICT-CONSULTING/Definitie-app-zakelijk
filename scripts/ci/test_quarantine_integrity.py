#!/usr/bin/env python3
"""Contracttests voor de bronintegriteitschecker (DEF-666).

Hermetisch: standaard-library `unittest` + `subprocess`. Geen app-imports, geen
conftest, geen netwerk, geen externe pakketten. Fixtures staan in verse
tijdelijke mappen en worden bewust NIET opgeruimd.

De checker `scripts/ci/quarantine_guard_check.py` bestaat nog niet; deze suite is
daarom RED tot hij er is. Zij toetst het afgesproken contract:

    check(root: Path) -> list[str]      # lege lijst = schoon
    CLI zonder argumenten, vaste repository-root, geen waiver of omgevingsluik

De checker verankert de HELE gereviewde manifestinhoud in één canonieke
SHA256-constante in zijn eigen bron. Daarmee liggen niet alleen de historische
hashes vast, maar ook de huidige geblokkeerde hashes en alle beleidsmetadata.
Wie een bronbestand wijzigt én de bijbehorende hash in het manifest netjes
bijwerkt, komt er dus nog steeds niet doorheen: het anker verschuift niet mee.
Dat is precies wat `test_bytewijziging_met_bijgewerkt_manifest_blijft_geblokkeerd`
bewijst.

Afbakening: dit is een integriteitspoort, geen bereikbaarheidsanalyse. Het
structurele en gedragsmatige bewijs voor de 49 blokkades staat in
`test_quarantine_guard_check.py` en `tests/unit/scripts/test_backup_restore_def666.py`.
Hier wordt geen tweede AST-motor of callgraph gebouwd.

VEILIGHEID: de fixtures kopiëren uitsluitend bytes. Geen enkel gequarantained
doelbestand wordt geïmporteerd of uitgevoerd, ook niet in de gemanipuleerde
varianten. De manipulaties verwijderen niets: zij hernoemen, zodat elke byte als
bewijsmateriaal blijft staan.

Eis aan de implementatie: de checker mag zijn fail-closed gedrag nooit op een
`assert` laten steunen. Een uitdrukkelijk meegegeven `-O` verwijdert die uit de
bytecode; expliciete controles blijven dan wel werken.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "ci" / "quarantine_guard_check.py"

MANIFEST_REL = "scripts/ci/quarantine_manifest.json"
PRECOMMIT_REL = ".pre-commit-config.yaml"
MAKEFILE_REL = "Makefile"

#: Vaste steekproeven uit de inventaris. Bewust benoemd en niet op index, zodat
#: een herordend manifest de bedoeling van een test niet stilzwijgend verschuift.
PY_DOEL = "scripts/archive_data.py"
SHELL_DOEL = "docs/archiveer-simpel.sh"
#: Oudermap van een inventarisbestand; wordt hernoemd voor de ouder-symlinkzaak.
ENKELE_MAP = "scripts/analyse"

#: De frontmatternormalisator: de enige automatische ingang die ooit bestond.
NORMALISATOR_PAD = "scripts/docs/fix_requirements_frontmatter.py"
NORMALISATOR_MODULE = "scripts.docs.fix_requirements_frontmatter"

#: Nieuw workflowbestand, zodat bewezen is dat de scan ook net toegevoegde
#: bestanden in .github/workflows meeneemt en niet alleen de bestaande.
NIEUWE_WORKFLOW = ".github/workflows/new-def666-probe.yml"
NIEUWE_WORKFLOW_INHOUD = (
    "name: DEF-666 probe\n"
    "on: [workflow_dispatch]\n"
    "jobs:\n"
    "  probe:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    f"      - run: python3 {NORMALISATOR_PAD}\n"
)

TIMEOUT = 60


# ---------------------------------------------------------------------------
# Hulpjes
# ---------------------------------------------------------------------------


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan.

    Het pad wordt gecanonicaliseerd: op macOS geeft `mkdtemp` een `/var/...`
    alias terug, en die symlink mag de symlinkcontrole van de checker niet
    onbedoeld laten aanslaan.
    """
    return Path(tempfile.mkdtemp(prefix=f"def666-int-{prefix}-")).resolve()


def _checker():
    """Laad de productiechecker via zijn pad. Ontbreken is verwacht RED."""
    assert CHECKER.is_file(), (
        "scripts/ci/quarantine_guard_check.py bestaat nog niet — dit is de "
        "verwachte RED-toestand tot de checker is geïmplementeerd"
    )
    spec = importlib.util.spec_from_file_location("def666_quarantine_checker", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check(root: Path) -> list[str]:
    return _checker().check(root)


def _inventaris() -> list[str]:
    data = json.loads((REPO_ROOT / MANIFEST_REL).read_text(encoding="utf-8"))
    return [entry["path"] for entry in data["entries"]]


def _configuraties() -> list[str]:
    """Actieve configuratie die de checker meeneemt, zoals nu in de repo staat."""
    relatief = [r for r in (PRECOMMIT_REL, MAKEFILE_REL) if (REPO_ROOT / r).is_file()]
    workflows = REPO_ROOT / ".github" / "workflows"
    if workflows.is_dir():
        relatief += [
            p.relative_to(REPO_ROOT).as_posix()
            for p in sorted(workflows.iterdir())
            if p.is_file() and p.suffix in (".yml", ".yaml")
        ]
    return relatief


def _kopieer(rel: str, root: Path) -> Path:
    doel = root / rel
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_bytes((REPO_ROOT / rel).read_bytes())
    return doel


def _fixture() -> Path:
    """Verse kopie van manifest, de 49 geblokkeerde bronnen en de actieve config.

    Alleen bytes; er wordt niets uitgevoerd en niets geïmporteerd.
    """
    root = _new_dir("kopie")
    for rel in [MANIFEST_REL, *_inventaris(), *_configuraties()]:
        _kopieer(rel, root)
    return root


def _manifest(root: Path) -> dict:
    return json.loads((root / MANIFEST_REL).read_text(encoding="utf-8"))


def _schrijf_manifest(root: Path, data: object) -> None:
    (root / MANIFEST_REL).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _post(data: dict, pad: str) -> dict:
    for entry in data["entries"]:
        if entry["path"] == pad:
            return entry
    raise AssertionError(f"{pad} ontbreekt in het manifest")


def _vervang_door_symlink(doel: Path) -> None:
    """Hernoem het bestand en zet op de oude naam een symlink ernaartoe.

    Er wordt niets verwijderd: de exacte bytes blijven als bewijs staan. Inhoud
    en hash blijven kloppen, zodat alleen de symlinkregel kan aanslaan.
    """
    elders = doel.parent / f"{doel.name}.elders"
    assert not elders.exists(), f"{elders} bestaat al"
    doel.rename(elders)
    doel.symlink_to(elders)


# ---------------------------------------------------------------------------
# Positief
# ---------------------------------------------------------------------------


class TestOngewijzigdeInventaris(unittest.TestCase):
    """Een onaangeroerde kopie van het gereviewde geheel is schoon."""

    def test_ongewijzigde_kopie_van_de_negenenveertig_is_schoon(self):
        assert len(_inventaris()) == 49, "de inventaris moet 49 paden tellen"
        fouten = _check(_fixture())
        assert fouten == [], fouten

    def test_echte_cli_op_de_vaste_repo_root_is_schoon(self):
        """De CLI kent geen root- of waivervlag; hij gebruikt de vaste root.

        Bewust vanuit een andere werkmap gedraaid, zodat een terugval op cwd
        zichtbaar zou worden.
        """
        assert CHECKER.is_file(), "checker ontbreekt nog — verwachte RED"
        proc = subprocess.run(
            [sys.executable, "-I", "-B", str(CHECKER)],
            cwd=_new_dir("elders"),
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Negatief — manifestinhoud
# ---------------------------------------------------------------------------


def _verwijder_post(data: dict) -> None:
    data["entries"].pop()


def _voeg_post_toe(data: dict) -> None:
    extra = dict(data["entries"][0])
    extra["path"] = "scripts/ci/verzonnen_extra.py"
    data["entries"].append(extra)


def _dubbele_post(data: dict) -> None:
    data["entries"].append(dict(_post(data, PY_DOEL)))


def _wijzig_originele_hash(data: dict) -> None:
    _post(data, PY_DOEL)["original_sha256"] = "0" * 64


def _wijzig_guard_kind(data: dict) -> None:
    _post(data, SHELL_DOEL)["guard_kind"] = "python_module"


def _wijzig_huidige_hash(data: dict) -> None:
    _post(data, PY_DOEL)["sha256"] = "1" * 64


class TestManifestManipulatie(unittest.TestCase):
    """Elke inhoudelijke afwijking van het gereviewde manifest blokkeert."""

    def test_gewijzigde_manifestinhoud_blokkeert(self):
        gevallen = (
            ("post verwijderd", _verwijder_post),
            ("post toegevoegd", _voeg_post_toe),
            ("dubbele post", _dubbele_post),
            ("originele hash gewijzigd", _wijzig_originele_hash),
            ("guard_kind gewijzigd", _wijzig_guard_kind),
            ("huidige hash gewijzigd", _wijzig_huidige_hash),
        )
        for naam, muteer in gevallen:
            with self.subTest(naam=naam):
                root = _fixture()
                data = _manifest(root)
                muteer(data)
                _schrijf_manifest(root, data)
                assert _check(root), f"{naam} werd niet geblokkeerd"

    def test_ongeldige_json_blokkeert(self):
        root = _fixture()
        (root / MANIFEST_REL).write_text("{ dit is geen json", encoding="utf-8")
        assert _check(root), "een onleesbaar manifest mag nooit groen zijn"

    def test_geldige_json_met_verkeerde_vorm_blokkeert(self):
        """`null` en andere geldige-maar-verkeerde toplaagwaarden.

        `null` is de gevaarlijkste: een checker die "niets geladen" met "geen
        bevindingen" verwart, wordt daar stil groen van.
        """
        for tekst in ("null", "[]", "false", "0", '"tekst"'):
            with self.subTest(vorm=tekst):
                root = _fixture()
                (root / MANIFEST_REL).write_text(tekst, encoding="utf-8")
                assert _check(root), f"{tekst} als manifest mag nooit groen zijn"

    def test_ankerfout_stopt_voor_de_bron_en_configuratiefase(self):
        """Het anker is de policygrens: daarna wordt niets meer ingelezen.

        Bij een afwijkend anker is de inventaris niet langer de gereviewde
        inventaris. Bronnen of configuratie daarna nog aanraken zou betekenen
        dat niet-goedgekeurde paden het bestandssysteem sturen.
        """
        checker = _checker()
        root = _fixture()
        data = _manifest(root)
        data["owner"] = "niet-gereviewd"
        _schrijf_manifest(root, data)

        with (
            mock.patch.object(
                checker, "_check_structure", return_value=([], [])
            ) as structuur,
            mock.patch.object(checker, "_check_sources", return_value=[]) as bronnen,
            mock.patch.object(checker, "_check_configs", return_value=[]) as configs,
        ):
            fouten = checker.check(root)

        assert fouten, "een afwijkend anker moet blokkeren"
        assert (
            not structuur.called
        ), "de structuurcontrole hoort na de ankergrens te stoppen"
        assert not bronnen.called, "geen bronbestand aanraken na een ankerfout"
        assert not configs.called, "geen configuratie aanraken na een ankerfout"

    def test_dubbele_json_sleutel_blokkeert(self):
        """Een tweede `entries`-sleutel die een parser stil overschrijft.

        De inhoud lijkt daardoor ongewijzigd; alleen de duplicaatregel vangt dit.
        """
        root = _fixture()
        tekst = (root / MANIFEST_REL).read_text(encoding="utf-8")
        assert '"entries"' in tekst, "manifest zonder entries-sleutel"
        gesaboteerd = tekst.replace('"entries"', '"entries": [],\n  "entries"', 1)
        (root / MANIFEST_REL).write_text(gesaboteerd, encoding="utf-8")
        assert _check(root), "een dubbele JSON-sleutel mag nooit groen zijn"


# ---------------------------------------------------------------------------
# Negatief — bronbestanden en padvormen
# ---------------------------------------------------------------------------


class TestBronManipulatie(unittest.TestCase):
    """Gewijzigde, ontbrekende of omgeleide doelbestanden blokkeren."""

    def test_bytewijziging_in_een_doel_blokkeert(self):
        root = _fixture()
        doel = root / PY_DOEL
        doel.write_bytes(doel.read_bytes() + b"\n# ongeautoriseerde toevoeging\n")
        assert _check(root), "een gewijzigd doelbestand mag nooit groen zijn"

    def test_bytewijziging_met_bijgewerkt_manifest_blijft_geblokkeerd(self):
        """De kern van het anker: zelfconsistent maken helpt de aanvaller niet.

        Bestand en manifest kloppen na deze manipulatie onderling, maar het
        manifest wijkt af van de gereviewde constante in de checker.
        """
        root = _fixture()
        doel = root / PY_DOEL
        rauw = doel.read_bytes() + b"\n# ongeautoriseerde toevoeging\n"
        doel.write_bytes(rauw)
        data = _manifest(root)
        post = _post(data, PY_DOEL)
        post["sha256"] = hashlib.sha256(rauw).hexdigest()
        post["size_bytes"] = len(rauw)
        _schrijf_manifest(root, data)
        assert _check(root), "het anker liet een bijgewerkte hash toch passeren"

    def test_ontbrekend_doel_blokkeert(self):
        root = _fixture()
        doel = root / PY_DOEL
        opzij = doel.parent / f"{doel.name}.opzij"
        assert not opzij.exists(), f"{opzij} bestaat al"
        doel.rename(opzij)  # opzij gezet, bewust niet verwijderd
        assert _check(root), "een ontbrekend doelbestand mag nooit groen zijn"

    def test_symlinks_blokkeren(self):
        gevallen = ("doelbestand", "manifest", "configuratie", "oudercomponent")
        for naam in gevallen:
            with self.subTest(naam=naam):
                root = _fixture()
                if naam == "doelbestand":
                    _vervang_door_symlink(root / PY_DOEL)
                elif naam == "manifest":
                    _vervang_door_symlink(root / MANIFEST_REL)
                elif naam == "configuratie":
                    _vervang_door_symlink(root / PRECOMMIT_REL)
                else:
                    ouder = root / ENKELE_MAP
                    echte = root / "echte_map"
                    assert not echte.exists(), f"{echte} bestaat al"
                    ouder.rename(echte)  # hernoemd, niets verwijderd of gekopieerd
                    ouder.symlink_to(echte, target_is_directory=True)
                assert _check(root), f"symlink op {naam} werd niet geblokkeerd"


# ---------------------------------------------------------------------------
# Negatief — heringevoerde automatische ingangen
# ---------------------------------------------------------------------------


class TestAutomatischeIngangen(unittest.TestCase):
    """Een teruggeplaatste aanroep van de normalisator blokkeert."""

    def test_heringevoerde_verwijzing_blokkeert(self):
        gevallen = (
            (
                "letterlijke CLI in pre-commit",
                PRECOMMIT_REL,
                (
                    "      - id: herintroductie\n"
                    f"        entry: python3 {NORMALISATOR_PAD}\n"
                ),
                False,
            ),
            (
                "gepunte module in Makefile",
                MAKEFILE_REL,
                f"\nherintroductie:\n\t@$(PY) -m {NORMALISATOR_MODULE}\n",
                False,
            ),
            (
                "nieuw workflowbestand",
                NIEUWE_WORKFLOW,
                NIEUWE_WORKFLOW_INHOUD,
                True,
            ),
        )
        for naam, rel, toevoeging, nieuw in gevallen:
            with self.subTest(naam=naam):
                root = _fixture()
                doel = root / rel
                if nieuw:
                    assert not doel.exists(), f"{rel} bestond al in de fixture"
                    doel.parent.mkdir(parents=True, exist_ok=True)
                    doel.write_text(toevoeging, encoding="utf-8")
                else:
                    assert doel.is_file(), f"{rel} ontbreekt in de fixture"
                    doel.write_text(
                        doel.read_text(encoding="utf-8") + toevoeging, encoding="utf-8"
                    )
                assert _check(root), f"{naam} werd niet geblokkeerd"


if __name__ == "__main__":
    unittest.main(verbosity=2)
