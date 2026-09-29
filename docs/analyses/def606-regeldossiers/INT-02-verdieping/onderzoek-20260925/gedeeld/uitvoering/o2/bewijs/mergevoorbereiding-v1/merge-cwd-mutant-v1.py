"""DEF-835 mergecorrectie: in-memory cwd-mutanten van de runner (bron ongewijzigd).

Pytest-plugin: na collectie wordt de al geladen runnermodule opnieuw
uitgevoerd met één tekstmutatie in `_proefomgeving`, in haar eigen
namespace. Gebruik: MERGE_CWD_MUTANT=<naam> PYTHONPATH=<map met symlink
merge_cwd_mutant.py> pytest ... -p merge_cwd_mutant.
"""

import os
import sys
from pathlib import Path

ANKER = "            os.chdir(vorige)"
MUTANTEN = {
    # Naïeve variant die de oude test (cwd == ROOT) goedkeurde.
    "herstel_naar_repo": "            os.chdir(REPO)",
    # Geen herstel: cwd blijft in de (verwijderde) tijdelijke map.
    "geen_herstel": "            pass",
}


def pytest_collection_finish(session):
    naam = os.environ["MERGE_CWD_MUTANT"]
    module = sys.modules["def835_int02_modelproef"]
    bron = Path(module.__file__).read_text("utf-8")
    assert bron.count(ANKER) == 1, "anker niet uniek"
    code = compile(bron.replace(ANKER, MUTANTEN[naam]), module.__file__, "exec")
    exec(code, module.__dict__)
