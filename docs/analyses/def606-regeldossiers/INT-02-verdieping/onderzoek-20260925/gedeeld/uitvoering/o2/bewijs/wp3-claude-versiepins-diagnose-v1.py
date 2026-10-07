"""Diagnose buiten de repo: kopie van de pin-tests met alleen de pins aangepast."""
from pathlib import Path
WT = Path("/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2")
UIT = Path("/tmp/wp3_pinprobe2")
wijz = {
 "tests/unit/validation/test_def771_int02_o1.py": [
   ('ROOT = Path(__file__).resolve().parents[3]', f'ROOT = Path("{WT}")'),
   ('assert CONTRACT_VERSION == "2.2.0"', 'assert CONTRACT_VERSION == "2.3.0"'),
   ('        (ne["rule_results"], "INT-02", "signals", []),\n        (ne["rule_results"], "INT-02", "assessment", None),\n', ''),
 ],
 "tests/unit/validation/test_validation_readiness.py": [
   ('Path(__file__).resolve().parents[3]', f'Path("{WT}")'),
   ('assert CONTRACT_VERSION == "2.2.0"', 'assert CONTRACT_VERSION == "2.3.0"'),
 ],
 "tests/unit/services/orchestrators/test_def772_int03_wrappers.py": [('== "2.2.0"', '== "2.3.0"')],
 "tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py": [('== "2.2.0"', '== "2.3.0"')],
 "tests/unit/services/orchestrators/test_def766_ess03_wrappers.py": [('== "2.2.0"', '== "2.3.0"')],
}
for rel, paren in wijz.items():
    tekst = (WT / rel).read_text("utf-8")
    for oud, nieuw in paren:
        n = tekst.count(oud); assert n >= 1, (rel, oud)
        tekst = tekst.replace(oud, nieuw)
        print(rel, "vervangen x", n)
    (UIT / ("test_probe_" + Path(rel).name.removeprefix("test_"))).write_text(tekst, "utf-8")
