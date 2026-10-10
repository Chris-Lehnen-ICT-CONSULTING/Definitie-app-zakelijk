"""DEF-835 — alleen-lezende diagnosescan; géén vervanging van de staged-gate.

Exporteert de gestagede inhoud (`git show :pad`) van alle bestanden in de index
die van HEAD verschillen, plus de opgegeven werkboombestanden, naar een verse
tijdelijke map op dezelfde relatieve paden. Scant die map met de gepinde
gitleaks onder (a) de HEAD-config en (b) de huidige werkboomconfig, via
`secret_scan.scan_directory`. Bij een niet-schone uitkomst wordt per bestand
opnieuw gescand en alleen pad plus aantal getoond — nooit Match of Secret.

De index wordt uitsluitend gelezen (`git diff --cached --name-only`, `git show`).

Gebruik (vanuit de werkroot):
    .venv/bin/python <dit bestand> <gitleaks> <werkboompad> [<werkboompad> ...]
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

WERKROOT = Path.cwd()
sys.path.insert(0, str(WERKROOT / "scripts" / "ci"))

import secret_scan  # noqa: E402


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=str(WERKROOT), capture_output=True, check=True
    ).stdout


def _schrijf(basis: Path, relpad: str, inhoud: bytes) -> None:
    doel = basis / relpad
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_bytes(inhoud)


def _regel(label: str, resultaat) -> str:
    return (
        f"{label}: status={resultaat.status.value} code={resultaat.code.value} "
        f"findings={resultaat.finding_count} bytes={resultaat.scanned_bytes} "
        f"exit={resultaat.exit_code}"
    )


def main(argv: list[str]) -> int:
    binary, werkboompaden = argv[0], argv[1:]
    gestaged = _git("diff", "--cached", "--name-only", "-z").decode().split("\0")
    gestaged = [pad for pad in gestaged if pad]
    basis = Path(tempfile.mkdtemp(prefix="def835-diagnose-"))
    bron = basis / "bron"
    for relpad in gestaged:
        _schrijf(bron, relpad, _git("show", f":{relpad}"))
    for relpad in werkboompaden:
        _schrijf(bron, relpad, (WERKROOT / relpad).read_bytes())
    head_config = basis / "head-gitleaks.toml"
    head_config.write_bytes(_git("show", "HEAD:.gitleaks.toml"))
    configs = {"head-config": head_config, "werkboom-config": WERKROOT / ".gitleaks.toml"}

    sys.stdout.write(
        f"gestaged={len(gestaged)} werkboombestanden={len(werkboompaden)}\n"
    )
    for label, config in configs.items():
        resultaat = secret_scan.scan_directory(binary, bron, config, 120)
        sys.stdout.write(_regel(label, resultaat) + "\n")
        if resultaat.status is secret_scan.ScanStatus.CLEAN:
            continue
        for relpad in [*gestaged, *werkboompaden]:
            los = basis / f"los-{label}" / relpad.replace("/", "__")
            _schrijf(los, relpad, (bron / relpad).read_bytes())
            deel = secret_scan.scan_directory(binary, los, config, 60)
            if deel.status is not secret_scan.ScanStatus.CLEAN:
                sys.stdout.write(
                    f"  {label} {relpad}: status={deel.status.value} "
                    f"findings={deel.finding_count}\n"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
