"""DEF-835 besluit 19 — draai de nulmeting en alle mutanten; vat de junit-xml samen.

Gebruik (vanuit deze map): <python> draai_besluit19.py <werkboom>
Schrijft resultaten/besluit19-<naam>.xml en drukt per run de telling af.
Geen netwerk; alles in het geheugen via mutatie_plugin.
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from mutatie_plugin import MUTANTEN

HIER = Path(__file__).resolve().parent
WERKBOOM = Path(sys.argv[1]).resolve()
TESTS = [
    WERKBOOM / "tests/unit/domain/test_def835_int02_bronfuncties.py",
    WERKBOOM / "tests/unit/domain/test_def835_int02_papertest.py",
    WERKBOOM / "tests/unit/validation/test_def835_int02_assessment_service.py",
]
DESELECT = (
    "tests/unit/validation/test_def835_int02_assessment_service.py"
    "::test_dienst_wordt_niet_door_de_container_aangemaakt"
)


def draai(naam: str | None) -> tuple[int, int, list[str]]:
    label = naam or "nulmeting"
    xml = HIER / "resultaten" / f"besluit19-{label}.xml"
    cmd = [sys.executable, "-m", "pytest", "-p", "mutatie_plugin"]
    if naam:
        cmd += ["--def835-mutant", naam]
    cmd += ["-p", "no:cacheprovider", "--tb=no", "-q", f"--rootdir={WERKBOOM}"]
    cmd += ["--deselect", DESELECT, f"--junitxml={xml}", *map(str, TESTS)]
    subprocess.run(cmd, cwd=HIER, capture_output=True, check=False)
    suite = ET.parse(xml).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    totaal = int(suite.get("tests"))
    gefaald = int(suite.get("failures")) + int(suite.get("errors"))
    namen = [
        f"{c.get('name')}"
        for c in suite.iter("testcase")
        if c.find("failure") is not None or c.find("error") is not None
    ]
    return totaal, gefaald, namen


def main() -> None:
    regels = []
    for naam in [None, *MUTANTEN]:
        totaal, gefaald, namen = draai(naam)
        oordeel = (
            ("groen" if gefaald == 0 else "ROOD")
            if naam is None
            else ("gedood" if gefaald else "OVERLEEFT")
        )
        regels.append(f"{naam or 'nulmeting':40} {gefaald:4}/{totaal:<4} {oordeel}")
        if naam and naam.endswith("_b19"):
            regels += [f"    - {n}" for n in namen]
    sys.stdout.write("\n".join(regels) + "\n")


if __name__ == "__main__":
    main()
