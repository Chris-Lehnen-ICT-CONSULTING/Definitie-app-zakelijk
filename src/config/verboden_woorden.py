import json
import logging
import os
import re
from datetime import datetime

import streamlit as st

# Gebruik standaard logging
logger = logging.getLogger(__name__)


# ✅ Laadt de lijst met verboden woorden, met override-optie vanuit Streamlit UI
def laad_verboden_woorden() -> list[str]:
    """
    Laadt de lijst met verboden woorden volgens deze volgorde:
    1. UI-override vanuit Streamlit sessiestate
    2. Anders: via het verboden_woorden.json bestand
    3. Bij fouten → lege lijst
    """
    try:
        # 1) UI-override: alleen als override_actief én lijst niet leeg
        raw = st.session_state.get("override_verboden_woorden")
        if st.session_state.get("override_actief") and raw:
            # raw bestaat en bevat ten minste één element
            if isinstance(raw, str):
                woorden = [w.strip() for w in raw.split(",") if w.strip()]
            elif isinstance(raw, list):
                woorden = raw
            else:
                woorden = []
            logger.debug("Verboden woorden geladen uit UI-override.")
            return woorden

        # 2) Direct laden uit JSON bestand
        verboden_woorden_path = os.path.join(
            os.path.dirname(__file__), "verboden_woorden.json"
        )
        if os.path.exists(verboden_woorden_path):
            with open(verboden_woorden_path, encoding="utf-8") as f:
                data = json.load(f)
                woorden = data.get("verboden_woorden", [])
                if not isinstance(woorden, list):
                    msg = "Ongeldige structuur: 'verboden_woorden' is geen lijst"
                    raise ValueError(msg)
                logger.debug(
                    f"Verboden woorden geladen uit JSON ({len(woorden)} woorden)."
                )
                return woorden

        # 3) Fallback: lege lijst
        logger.warning("Geen verboden woorden bestand gevonden, gebruik lege lijst")
        return []

    except Exception as e:
        logger.error(f"Kan verboden woorden niet laden: {e}")
        return []


# ✅ Functie: sla aangepaste woordenlijst op
def sla_verboden_woorden_op(woordenlijst: list[str]):
    try:
        verboden_woorden_path = os.path.join(
            os.path.dirname(__file__), "verboden_woorden.json"
        )
        with open(verboden_woorden_path, "w", encoding="utf-8") as f:
            json.dump(
                {"verboden_woorden": woordenlijst}, f, ensure_ascii=False, indent=2
            )
        logger.debug(
            f"Verboden woordenlijst succesvol opgeslagen ({len(woordenlijst)} woorden)"
        )
    except Exception as e:
        logger.error(f"Kan verboden woorden niet opslaan: {e}")


# 💚 Genereert regex-lijst om verboden beginconstructies te herkennen
#    • Matcht óf exact op verboden woord aan begin (zoals 'is', 'de')
#    • Óf op combinatie: 'begrip verwijst naar', 'begrip betekent', etc.
#    • Alle patronen starten met ^ (begin van de string)
#    • Case-insensitief (moet toegepast worden bij re.match via flags)


def genereer_verboden_startregex(begrip: str, verboden_lijst: list[str]) -> list[str]:
    """
    Genereert regex-expressies die verboden beginconstructies herkennen,
    inclusief combinaties zoals 'begrip verwijst naar' of alleen 'is'.

    Parameters:
        begrip (str): Het beleidsbegrip (bijv. 'identiteitsvaststelling')
        verboden_lijst (list[str]): Verboden woorden zoals ['is', 'omvat', 'de', ...]

    Returns:
        list[str]: Regex-patronen die beginfouten detecteren
    """
    begrip_escaped = re.escape(begrip.strip().lower())
    patterns = []

    for woord in verboden_lijst:
        woord_clean = woord.strip().lower()
        if not woord_clean:
            continue  # 💚 Sla lege of whitespace-woorden over

        woord_escaped = re.escape(woord_clean)

        # 💚 Patroon 1: begint exact met het verboden woord (bijv. 'is ...')
        patterns.append(rf"^{woord_escaped}\b")

        # 💚 Patroon 2: begint met 'begrip + verboden woord' (bijv. 'identiteitsvaststelling verwijst naar')
        patterns.append(rf"^{begrip_escaped}\s+{woord_escaped}\b")

    return patterns


# ================================
# 🧪 VOORSTEL 4: Logging individuele woordtests naar JSONL
# ================================

# ✅ Pad naar het logbestand waarin testresultaten worden opgeslagen
PAD_LOG = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "log", "verboden_woord_tests.jsonl")
)


# ✅ Functie: logt individueel testresultaat naar JSONL-logbestand
def log_test_verboden_woord(woord: str, zin: str, komt_voor: bool, regex_match: bool):
    """
    Logt een individuele test van een verboden woord op een zin naar een JSONL-logbestand.
    Inclusief: woord, zin, resultaten en timestamp.
    """
    try:
        os.makedirs(os.path.dirname(PAD_LOG), exist_ok=True)

        logregel = {
            "tijd": datetime.now().isoformat(),
            "woord": woord,
            "zin": zin,
            "komt_voor": komt_voor,
            "regex_match": regex_match,
        }

        with open(PAD_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(logregel, ensure_ascii=False) + "\n")

        logger.info("Individuele woordtest gelogd.")

    except Exception as e:
        logger.error(f"Kon woordtest niet loggen: {e}")
