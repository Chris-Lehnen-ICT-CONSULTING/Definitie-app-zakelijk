import re

# ✅ Herken meerdere juridische verwijzingsvormen met aparte regexpatronen
_REGEX_PATRONEN = [
    {
        "id": "klassiek_format",
        "pattern": re.compile(
            r'(?P<wet>Wetboek van [A-Z][a-z]+)(?:,\s*boek\s*(?P<boek>[0-9]+))?,?\s*artikel\s*(?P<artikel>[0-9a-zA-Z]+)(?:\s*lid\s*(?P<lid>[0-9]+))?',
            re.IGNORECASE
        )
    },
    {
        "id": "verkort_format_bw_sv",
        "pattern": re.compile(
            r'art\.?\s*(?P<artikel>[0-9]+:[0-9a-zA-Z]+)\s+(?P<wet>BW|Sv|Sr|Rv|RvS)',
            re.IGNORECASE
        )
    },
    {
        "id": "normale_artikel_wet",
        "pattern": re.compile(
            r'artikel\s+(?P<artikel>[0-9]+[a-zA-Z]?)\s+van\s+de\s+(?P<wet>[A-Z][a-zA-Z\s]+)',
            re.IGNORECASE
        )
    },
    {
        "id": "artikel_lid_onder_wet",
        "pattern": re.compile(
            r'artikel\s+(?P<artikel>[0-9]+[a-zA-Z]?)\s+lid\s+(?P<lid>[0-9]+)\s+(onder\s+(?P<sub>[a-z]))?\s+van\s+de\s+(?P<wet>[A-Z][a-zA-Z\s]+)',
            re.IGNORECASE
        )
    },
]


# ==========================
# Logging van juridische verwijzingen (optioneel)
# ==========================
import os
import json
from datetime import datetime

def zoek_wetsartikelstructuur(
    tekst: str,
    log_jsonl: bool = False,
    bron: str = "",
    begrip: str = ""
) -> list[dict]:
    """
    ✅ Detecteert juridische verwijzingen naar wetsartikelen in diverse vormen.
    ✅ Retourneert lijst van dicts met sleutels: wet, artikel, lid, boek, sub, herkend_via.
    ✅ Indien log_jsonl=True, logt elke match in log/wetsverwijzingen_log.jsonl.
    """
    resultaten = []
    for blok in _REGEX_PATRONEN:
        patroon = blok["pattern"]
        for match in patroon.finditer(tekst):
            resultaat = {
                "herkend_via": blok["id"],
                "wet": match.groupdict().get("wet"),
                "boek": match.groupdict().get("boek"),
                "artikel": match.groupdict().get("artikel"),
                "lid": match.groupdict().get("lid"),
                "sub": match.groupdict().get("sub"),
            }
            resultaat_clean = {k: v for k, v in resultaat.items() if v}
            resultaten.append(resultaat_clean)

            if log_jsonl:
                contextregels = tekst[max(0, match.start()-60):match.end()+60]
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "bron": bron,
                    "begrip": begrip,
                    "herkend_via": blok["id"],
                    "match": resultaat_clean,
                    "tekstfragment": match.group(0),
                    "contextregels": contextregels.strip()
                }
                os.makedirs("log", exist_ok=True)
                with open("log/wetsverwijzingen_log.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    return resultaten