"""Q1 F3 (DEF-835): gedragsrood zonder broncodewijziging.

Pytest-plugin: zet na collectie alleen de twee nieuwe naamconstanten op de
al geladen, ongewijzigde runnermodule, zodat de gerichte F3-tests het
gedrag van de oude code toetsen in plaats van op een AttributeError te
falen. Gebruik: PYTHONPATH=<map met symlink q1_f3_rood.py> -p q1_f3_rood.
"""

import sys


def pytest_collection_finish(session):
    module = sys.modules["def835_int02_modelproef"]
    module.AFRONDING_OPEN = "-afronding.open"
    module.AFRONDING_VOLTOOID = "-afronding.voltooid"
