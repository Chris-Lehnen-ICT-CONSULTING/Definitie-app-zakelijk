"""DEF-770 effectproeven: gedeelde bronbinding voor de T24- en G24-helpers.

Een variant is uitsluitend een exacte `git archive --format=tar` van één
commit. Dit bestand:

- leest de commit-ID uit de pax-header van het archief (`git archive` schrijft
  hem daar; dezelfde bron als `git get-tar-commit-id`);
- pakt het archief uit in een verse, nog niet bestaande map, met de
  `data`-filter van `tarfile` (geen absolute paden, geen `..`, geen links
  naar buiten) en zonder `data/` of `*.db`/`*.sqlite*` — er gaat geen
  productiedata mee;
- hasht het archief, de uitgepakte sleutelbestanden en ieder invoer- en
  uitvoerbestand (sha256);
- zet de uitgepakte boom vooraan op `sys.path`, installeert de offline-gate
  uit díe boom en controleert dat elke geladen applicatiemodule uit de boom
  komt en niet uit de werkboom of de venv.

Er wordt niets overschreven: elke doelmap of elk doelbestand moet nieuw zijn.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path
from typing import Any

NIET_AANWEZIG = "niet aanwezig"

#: Runplan-t24-g24-v3 §1: bestanden waarvan de inhoud de variant bindt.
SLEUTELBESTANDEN = (
    "src/toetsregels/regels/INT-01.json",
    "src/domain/int01/zinsgrenzen.py",
    "src/domain/int01/opslag.py",
    "src/services/validation/evaluators/sentence_boundary.py",
    "src/services/prompts/modules/json_based_rules_module.py",
    "src/services/prompts/prompt_service_v2.py",
    "src/services/orchestrators/definition_orchestrator_v2.py",
    "src/services/ai/anthropic_client.py",
    "src/services/ai/model_router.py",
    "config/config.yaml",
    "tests/offline_bootstrap.py",
)

_UITGESLOTEN_SUFFIXEN = (".db", ".sqlite", ".sqlite3", ".db-journal", ".db-wal")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_bestand(pad: Path) -> str:
    h = hashlib.sha256()
    with open(pad, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def canoniek_json(obj: Any) -> bytes:
    """Deterministische bytes voor hashing (gesorteerde sleutels, geen spaties)."""
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def commit_uit_tar(tar_pad: Path) -> str:
    with tarfile.open(tar_pad, "r:") as tar:
        commit = tar.pax_headers.get("comment", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SystemExit(
            f"{tar_pad}: geen git-archive met commit-ID in de pax-header "
            f"(gevonden: {commit!r})"
        )
    return commit


def _mag_mee(lid: tarfile.TarInfo) -> bool:
    naam = lid.name
    if naam == "data" or naam.startswith("data/"):
        return False
    return not naam.lower().endswith(_UITGESLOTEN_SUFFIXEN)


def pak_uit(tar_pad: Path, doel: Path) -> dict[str, Any]:
    """Pak het archief uit in `doel` (moet nieuw zijn); geef de uitsluitingen terug."""
    doel.mkdir(parents=False, exist_ok=False)
    overgeslagen: list[str] = []
    with tarfile.open(tar_pad, "r:") as tar:
        leden = []
        for lid in tar.getmembers():
            if _mag_mee(lid):
                leden.append(lid)
            else:
                overgeslagen.append(lid.name)
        tar.extractall(doel, members=leden, filter="data")
    return {
        "uitgepakte_leden": len(leden),
        "overgeslagen_leden": sorted(overgeslagen),
        "uitsluitingsregel": "data/ en *.db/*.sqlite* (geen productiedata)",
    }


def bronbinding(tar_pad: Path, verwachte_commit: str | None) -> dict[str, Any]:
    commit = commit_uit_tar(tar_pad)
    if verwachte_commit and commit != verwachte_commit:
        raise SystemExit(
            f"commit in archief {commit} wijkt af van --verwachte-commit "
            f"{verwachte_commit}"
        )
    return {
        "archief": str(tar_pad),
        "archief_sha256": sha256_bestand(tar_pad),
        "commit": commit,
        "commit_uit": "pax-header 'comment' van git archive",
    }


def sleutelhashes(bron: Path) -> dict[str, str]:
    return {
        rel: sha256_bestand(bron / rel) if (bron / rel).is_file() else NIET_AANWEZIG
        for rel in SLEUTELBESTANDEN
    }


def activeer_bron(bron: Path, sessie: Path) -> Any:
    """Zet de uitgepakte boom op sys.path en installeer díe offline-gate.

    Geeft de module `offline_bootstrap` uit de boom terug. De werkmap (cwd)
    wordt `sessie/werk`, met symlinks naar `src` en `config` van de boom, net
    als proef-na-implementatie-v3; relatieve paden (regels, cache) lezen dus
    uit de boom en schrijven in de sessie.
    """
    for naam in list(sys.modules):
        if naam.partition(".")[0] in ("tests", "src", "services", "config"):
            raise SystemExit(f"module {naam} al geladen vóór activering van de bron")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(bron))
    from tests import offline_bootstrap  # uit de uitgepakte boom

    offline_bootstrap.install(session_root=sessie)
    werk = sessie / "werk"
    werk.mkdir()
    for naam in ("src", "config"):
        (werk / naam).symlink_to(bron / naam, target_is_directory=True)
    (werk / "data").mkdir()
    os.chdir(werk)
    sys.path.insert(0, str(bron / "src"))
    return offline_bootstrap


def herkomstcontrole(bron: Path, modulenamen: tuple[str, ...]) -> dict[str, str]:
    """Pad per module; stopt als een applicatiemodule niet uit de boom komt."""
    wortel = Path(os.path.realpath(bron))
    paden: dict[str, str] = {}
    for naam in modulenamen:
        module = sys.modules.get(naam)
        if module is None or not getattr(module, "__file__", None):
            paden[naam] = NIET_AANWEZIG
            continue
        pad = Path(os.path.realpath(module.__file__))
        if wortel not in pad.parents:
            raise SystemExit(f"module {naam} komt niet uit de bron: {pad}")
        paden[naam] = str(pad.relative_to(wortel))
    return paden


def schrijf_nieuw(pad: Path, obj: Any) -> str:
    """Schrijf JSON exclusief (open 'x'); geef de sha256 van de bytes terug."""
    data = json.dumps(obj, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    with open(pad, "xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return sha256_bytes(data)
