# conftest.py
import sys
import os

# voeg <project-root>/src toe aan de module-zoekroute
ROOT = os.path.dirname(__file__)
SRC  = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)