import os
import json
from datetime import datetime
import pandas as pd
import logging                                # ✅ voor console‐logging

# ================================
# 🛠️ LOGGER-FACTORY
# ================================
def get_logger(name: str) -> logging.Logger:
    """
    Retourneert een logger met StreamHandler, formatter en level INFO.
    Voorkomt dubbele handlers bij herhaalde aanroep.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "[%(asctime)s] %(name)s %(levelname)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# ================================
# 🧾 CENTRALE LOGGINGFUNCTIE
# ================================
def log_definitie(
    versietype: str,
    begrip: str,
    context: str,
    juridische_context: str,
    wet_basis: str,
    definitie_origineel: str,
    definitie_gecorrigeerd: str,
    definitie_aangepast: str,
    toetsing: list,
    voorbeeld_zinnen: str,
    praktijkvoorbeelden: list[str],
    toelichting: str,
    synoniemen: str,
    antoniemen: str,
    vrije_input: str,
    datum,
    voorsteller: str,
    ketenpartners: list,
    expert_review: str = ""
):
    # ✅ Haal logger op
    logger = get_logger(__name__)
    logger.debug(f"Start log_definitie voor begrip={begrip} (versie={versietype})")

    # 💚 Stap 1: JSON-log (per rij → analyse/hergebruik)
    metadata = {
        "Versietype": versietype,
        "begrip": begrip,
        "context": context,
        "juridische_context": juridische_context,
        "wettelijke_basis": wet_basis,
        "definitie_origineel": definitie_origineel,
        "definitie_gecorrigeerd": definitie_gecorrigeerd,
        "definitie_aangepast": definitie_aangepast,
        "definitie": definitie_aangepast or definitie_gecorrigeerd,
        "toetsing": toetsing,
        "voorbeeld_zinnen": voorbeeld_zinnen,
        "praktijkvoorbeelden": praktijkvoorbeelden,
        "toelichting": toelichting,
        "synoniemen": synoniemen,
        "antoniemen": antoniemen,
        "vrije_input": vrije_input,
        "expert_review": expert_review,
        "datum": str(datum),
        "voorsteller": voorsteller,
        "ketenpartners": ketenpartners,
        "timestamp": datetime.now().isoformat()
    }
    os.makedirs("log", exist_ok=True)
    with open("log/definities_log.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
    logger.info("JSON-log weggeschreven naar log/definities_log.json")

    # 💚 Stap 2: CSV-log (platte tabelstructuur)
    csv_pad = "log/definities_log.csv"
    if os.path.exists(csv_pad):
        df_bestaand = pd.read_csv(csv_pad)
        logger.debug("Bestaande CSV ingeladen")
    else:
        df_bestaand = pd.DataFrame(columns=[
            "Versietype", "Begrip", "Context", "Juridische context",
            "Wettelijke basis", "Definitie", "Definitie_origineel",
            "Definitie_gecorrigeerd", "Voorbeeld_zinnen", "Praktijkvoorbeelden", "Toelichting",
            "Synoniemen", "Antoniemen", "Vrije input", "Expert-review",
            "Datum", "Voorsteller", "Ketenpartners", "Timestamp"
        ] + [f"Regel {i}" for i in range(1, len(toetsing)+1)])
        logger.debug("Nieuwe CSV DataFrame aangemaakt")

    # Bouw de nieuwe rij
    nieuwe_rij = {
        "Versietype": versietype,
        "Begrip": begrip,
        "Context": context,
        "Juridische context": juridische_context,
        "Wettelijke basis": wet_basis,
        "Definitie_origineel": definitie_origineel,
        "Definitie_gecorrigeerd": definitie_gecorrigeerd,
        "Definitie_aangepast": definitie_aangepast,
        "Voorbeeld_zinnen": voorbeeld_zinnen,
        "Praktijkvoorbeelden": "; ".join(praktijkvoorbeelden),
        "Toelichting": toelichting,
        "Synoniemen": synoniemen,
        "Antoniemen": antoniemen,
        "Vrije input": vrije_input,
        "Expert-review": expert_review,
        "Datum": str(datum),
        "Voorsteller": voorsteller,
        "Ketenpartners": ", ".join(ketenpartners),
        "Timestamp": datetime.now().isoformat(),
        **{f"Regel {i+1}": r for i, r in enumerate(toetsing)}
    }

    df_nieuw = pd.concat([df_bestaand, pd.DataFrame([nieuwe_rij])], ignore_index=True)
    df_nieuw.to_csv(csv_pad, index=False, encoding="utf-8")
    logger.info("CSV-log bijgewerkt in log/definities_log.csv")

def parse_toetsing_regels(toetsing_lijst):
    regels_dict = {}
    for i, regel in enumerate(toetsing_lijst, 1):
        regels_dict[f"Regel {i}"] = regel
    return regels_dict
