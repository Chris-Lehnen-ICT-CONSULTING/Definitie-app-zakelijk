#!/usr/bin/env python3
"""Bronintegriteitspoort voor de quarantaine (DEF-666).

Standaard-library, read-only. Deze gate leest en hasht; zij importeert, parseert
of draait nooit een geïnspecteerd bronbestand. Zij doet ook geen
bereikbaarheidsanalyse: dat het blokkeren zelf klopt en werkt, bewijzen de
onafhankelijke suites `scripts/ci/test_quarantine_guard_check.py` en
`tests/unit/scripts/test_backup_restore_def666.py`.

Wat zij wél doet: het gereviewde manifest en de gereviewde geblokkeerde bytes
aan elkaar binden. `MANIFEST_ANCHOR` is één SHA256 over het volledige geparste
manifest — versie, alle metadata, de huidige geblokkeerde hashes én de
historische hashes. Wie een bron wijzigt en de bijbehorende hash in het manifest
netjes bijwerkt, komt er dus nog steeds niet doorheen: bestand en manifest
kloppen dan onderling, maar het manifest wijkt af van het anker. Dat anker
veranderen vergt een aparte, gereviewde issue die bron, manifest en checker in
dezelfde wijziging aanpast.

Er is bewust geen root-, scope- of waivervlag, en geen omgevingsvariabele. De
repository-root ligt vast; `check(root)` bestaat uitsluitend zodat tests een
eigen kopie kunnen doorgeven. De verwachte policy wordt nooit uit het gelezen
manifest herleid.

Exitcodes: 0 = schoon, 1 = blokkerende bevinding(en), 2 = verkeerd gebruik.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

MANIFEST_REL = "scripts/ci/quarantine_manifest.json"

#: Onafhankelijk gemeten SHA256 over de canonieke vorm van het hele geparste
#: manifest (sort_keys, compacte scheidingstekens, ensure_ascii=False, UTF-8).
MANIFEST_ANCHOR = "58aaf8094bf0b57defdce53776da2a2f08b841dd86191e210c58fef1a7de456b"

EXPECTED_VERSION = 2
EXPECTED_ENTRY_COUNT = 49
GUARD_KINDS = frozenset({"python_module", "shell", "make", "backup_actions"})

#: Geregistreerde actieve configuratie. Bewust een eindige, vaste verzameling:
#: geen brede zoektocht door de repository.
CONFIG_FILES = ("Makefile", ".pre-commit-config.yaml")
WORKFLOW_DIR = ".github/workflows"
WORKFLOW_SUFFIXES = (".yml", ".yaml")

HEX = frozenset("0123456789abcdef")
MAX_PROBLEMS = 200


#: Sentinel voor "manifest kon niet geladen worden". Bewust niet None: `null` is
#: een geldige JSON-waarde, en die verwarring maakte de poort eerder stil groen.
_LOAD_FAILED = object()


class _DuplicateKeyError(ValueError):
    """Twee gelijke sleutels in één JSON-object."""


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Weiger dubbele sleutels, ook als het resultaat identiek zou zijn.

    Een parser neemt normaal stilzwijgend de laatste waarde; dan zou een tweede
    sleutel de inhoud kunnen verbergen zonder dat het anker verschuift.
    """
    seen: set[str] = set()
    for key, _value in pairs:
        if key in seen:
            raise _DuplicateKeyError(key)
        seen.add(key)
    return dict(pairs)


def _canonical(manifest: object) -> bytes:
    return json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def _path_problem(rel: object) -> str | None:
    """Alleen genormaliseerde, relatieve POSIX-paden binnen de root."""
    if not isinstance(rel, str) or not rel:
        return "pad ontbreekt of is geen tekst"
    if "\\" in rel:
        return "pad bevat een backslash"
    if rel.startswith("/"):
        return "pad is absoluut"
    if any(deel in ("", ".", "..") for deel in rel.split("/")):
        return "pad is niet genormaliseerd"
    return None


def _symlink_component(root: Path, rel: str) -> str | None:
    """Eerste symlink in het pad onder `root`, of None.

    De root zelf blijft buiten beschouwing: die mag een alias zijn (op macOS
    zijn `/tmp` en `/var` dat), en dat is geen bevinding.
    """
    huidig = root
    for deel in rel.split("/"):
        huidig = huidig / deel
        if huidig.is_symlink():
            return huidig.relative_to(root).as_posix()
    return None


def _read_bytes(root: Path, rel: str) -> tuple[bytes | None, str | None]:
    doel = root / rel
    if not doel.exists():
        return None, "ontbreekt"
    if not doel.is_file():
        return None, "is geen regulier bestand"
    try:
        return doel.read_bytes(), None
    except OSError as exc:
        return None, f"leesfout ({exc.strerror or exc.__class__.__name__})"


def _load_manifest(root: Path) -> tuple[object, list[str]]:
    """Geef de geparste waarde terug, of `_LOAD_FAILED` met een reden.

    Een geslaagde parse van `null` levert `None` op; dat is een geldige waarde
    en géén laadfout. Alleen `_LOAD_FAILED` betekent dat er niets te toetsen is.
    """
    link = _symlink_component(root, MANIFEST_REL)
    if link is not None:
        return _LOAD_FAILED, [f"{MANIFEST_REL}: symlink in pad ({link})"]
    rauw, leesfout = _read_bytes(root, MANIFEST_REL)
    if rauw is None:
        return _LOAD_FAILED, [f"{MANIFEST_REL}: {leesfout}"]
    try:
        tekst = rauw.decode("utf-8")
    except UnicodeDecodeError:
        return _LOAD_FAILED, [f"{MANIFEST_REL}: geen geldige UTF-8"]
    try:
        manifest = json.loads(tekst, object_pairs_hook=_no_duplicate_keys)
    except _DuplicateKeyError as exc:
        return _LOAD_FAILED, [f"{MANIFEST_REL}: dubbele JSON-sleutel {exc.args[0]!r}"]
    except ValueError as exc:
        return _LOAD_FAILED, [f"{MANIFEST_REL}: onleesbare JSON ({exc})"]
    return manifest, []


def _check_structure(manifest: object) -> tuple[list[str], list[dict]]:
    """Minimale vormcontrole; onbekende sleutels vangt het anker al af."""
    if not isinstance(manifest, dict):
        return [f"{MANIFEST_REL}: geen JSON-object"], []

    problemen: list[str] = []
    if manifest.get("version") != EXPECTED_VERSION:
        problemen.append(f"{MANIFEST_REL}: version is niet {EXPECTED_VERSION}")

    posten = manifest.get("entries")
    if not isinstance(posten, list):
        problemen.append(f"{MANIFEST_REL}: entries ontbreekt of is geen lijst")
        return problemen, []
    if len(posten) != EXPECTED_ENTRY_COUNT:
        problemen.append(
            f"{MANIFEST_REL}: {len(posten)} posten in plaats van "
            f"{EXPECTED_ENTRY_COUNT}"
        )

    bruikbaar: list[dict] = []
    gezien: set[str] = set()
    for index, post in enumerate(posten):
        if not isinstance(post, dict):
            problemen.append(f"{MANIFEST_REL}: post {index} is geen object")
            continue
        rel = post.get("path")
        padfout = _path_problem(rel)
        if padfout is not None:
            problemen.append(f"{MANIFEST_REL}: post {index}: {padfout}")
            continue
        if rel in gezien:
            problemen.append(f"{rel}: komt meer dan eens voor in het manifest")
            continue
        gezien.add(rel)
        maat = post.get("size_bytes")
        if post.get("guard_kind") not in GUARD_KINDS:
            problemen.append(f"{rel}: onbekende guard_kind")
        elif not _is_sha256(post.get("sha256")):
            problemen.append(f"{rel}: sha256 is geen 64-cijferige kleine-letter-hex")
        elif not isinstance(maat, int) or isinstance(maat, bool) or maat < 0:
            problemen.append(f"{rel}: size_bytes is geen geheel getal >= 0")
        else:
            bruikbaar.append(post)
    return problemen, bruikbaar


def _check_sources(root: Path, posten: list[dict]) -> list[str]:
    problemen: list[str] = []
    for post in posten:
        rel = post["path"]
        link = _symlink_component(root, rel)
        if link is not None:
            problemen.append(f"{rel}: symlink in pad ({link})")
            continue
        rauw, leesfout = _read_bytes(root, rel)
        if rauw is None:
            problemen.append(f"{rel}: {leesfout}")
            continue
        if len(rauw) != post["size_bytes"]:
            problemen.append(
                f"{rel}: {len(rauw)} bytes in plaats van de verankerde "
                f"{post['size_bytes']}"
            )
            continue
        gemeten = hashlib.sha256(rauw).hexdigest()
        if gemeten != post["sha256"]:
            problemen.append(f"{rel}: sha256 {gemeten} wijkt af van het anker")
    return problemen


def _reference_forms(rel: str) -> tuple[str, ...]:
    """Begrensde, letterlijke vormen: het pad en, voor Python, de gepunte module."""
    if rel.endswith(".py"):
        return (rel, rel[: -len(".py")].replace("/", "."))
    return (rel,)


def _config_relatives(root: Path) -> tuple[list[str], list[str]]:
    """De vaste configuratiebestanden plus elk direct workflowbestand."""
    problemen: list[str] = []
    relatief = list(CONFIG_FILES)

    link = _symlink_component(root, WORKFLOW_DIR)
    if link is not None:
        problemen.append(f"{WORKFLOW_DIR}: symlink in pad ({link})")
        return problemen, relatief
    map_ = root / WORKFLOW_DIR
    if not map_.is_dir():
        problemen.append(f"{WORKFLOW_DIR}: ontbreekt of is geen map")
        return problemen, relatief
    try:
        kinderen = sorted(map_.iterdir())
    except OSError as exc:
        problemen.append(
            f"{WORKFLOW_DIR}: leesfout ({exc.strerror or exc.__class__.__name__})"
        )
        return problemen, relatief
    relatief += [
        f"{WORKFLOW_DIR}/{kind.name}"
        for kind in kinderen
        if kind.suffix in WORKFLOW_SUFFIXES
    ]
    return problemen, relatief


def _check_configs(root: Path, posten: list[dict]) -> list[str]:
    """Weiger elke letterlijke verwijzing naar de inventaris in actieve config.

    Bewust conservatief: de goedgekeurde configuratie roept geen enkel
    inventarispad aan, ook geen veilige backupactie. De handmatige API en CLI
    van `scripts/backup_restore.py` blijven gewoon beschikbaar, en historische
    testimports buiten deze bestanden blijven geldig. Dynamisch berekende namen
    worden hiermee niet uitgesloten; de bronblokkades zijn de primaire
    bescherming.
    """
    problemen, relatief = _config_relatives(root)
    vormen = [
        (post["path"], vorm)
        for post in posten
        for vorm in _reference_forms(post["path"])
    ]

    for rel in relatief:
        link = _symlink_component(root, rel)
        if link is not None:
            problemen.append(f"{rel}: symlink in pad ({link})")
            continue
        rauw, leesfout = _read_bytes(root, rel)
        if rauw is None:
            problemen.append(f"{rel}: {leesfout}")
            continue
        try:
            tekst = rauw.decode("utf-8")
        except UnicodeDecodeError:
            problemen.append(f"{rel}: geen geldige UTF-8")
            continue
        gemeld: set[str] = set()
        for pad, vorm in vormen:
            if pad not in gemeld and vorm in tekst:
                problemen.append(f"{rel}: verwijst naar het geblokkeerde {pad}")
                gemeld.add(pad)
    return problemen


def _collect(root: Path) -> list[str]:
    manifest, problemen = _load_manifest(root)
    if manifest is _LOAD_FAILED:
        # Een laadfout draagt altijd een reden; een lege lijst zou hier "schoon"
        # betekenen en dat mag nooit.
        return problemen or [f"{MANIFEST_REL}: kon niet geladen worden"]

    # Elke geparste waarde gaat door het anker, ook `null`, een lijst of een
    # getal. Dit is de policygrens: wijkt het anker af, dan is dit niet de
    # gereviewde inventaris en wordt er geen enkel bron- of configuratiebestand
    # meer aangeraakt. Niet-goedgekeurde paden mogen nooit sturen wat we lezen.
    gemeten = hashlib.sha256(_canonical(manifest)).hexdigest()
    if gemeten != MANIFEST_ANCHOR:
        return [
            f"{MANIFEST_REL}: wijkt af van het gereviewde anker (gemeten {gemeten})"
        ]

    vormfouten, posten = _check_structure(manifest)
    problemen += vormfouten
    problemen += _check_sources(root, posten)
    problemen += _check_configs(root, posten)
    return problemen


def check(root: Path) -> list[str]:
    """Controleer één repositorykopie. Lege lijst betekent schoon.

    Faalt nooit met een onafgevangen fout: een onverwachte uitzondering wordt
    zelf een blokkerende bevinding, zodat er nooit stil groen ontstaat.
    """
    try:
        problemen = _collect(root)
    except Exception as exc:
        # Breed en bewust: elke onvoorziene fout wordt een bevinding. Stil groen
        # blijven zou hier het hele doel van de poort ondermijnen.
        return [
            f"onverwachte fout tijdens de controle: {exc.__class__.__name__}: {exc}"
        ]
    if len(problemen) > MAX_PROBLEMS:
        overig = len(problemen) - MAX_PROBLEMS
        return [*problemen[:MAX_PROBLEMS], f"... nog {overig} meldingen weggelaten"]
    return problemen


def main(argv: list[str]) -> int:
    if argv:
        rapport = {
            "status": "usage",
            "errors": [
                (
                    "quarantine_guard_check.py accepteert geen argumenten: de "
                    "repository-root ligt vast en er is geen scope- of waivervlag."
                )
            ],
        }
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
        return 2

    problemen = check(REPO_ROOT)
    rapport = {
        "status": "clean" if not problemen else "blocked",
        "root": str(REPO_ROOT),
        "entries": EXPECTED_ENTRY_COUNT,
        "errors": problemen,
    }
    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    return 0 if not problemen else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
