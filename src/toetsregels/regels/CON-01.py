"""
Toetsregel CON-01: Contextspecifieke formulering zonder expliciete benoeming

Deze toetsregel controleert of de definitie géén expliciete verwijzing bevat naar de opgegeven context(en).
Gemigreerd van legacy core.py
"""

import logging
import re
from typing import Any

try:
    # Repository kan ontbreken in sommige tooling-contexten; soft import
    from database.definitie_repository import DefinitieRepository
except Exception:  # pragma: no cover
    DefinitieRepository = None  # type: ignore

logger = logging.getLogger(__name__)


class CON01Validator:
    """Validator voor CON-01: Contextspecifieke formulering zonder expliciete benoeming."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit CON-01.json
        """
        self.config = config
        # Normaliseer naar weergave met koppelteken
        self.id = str(config.get("id", "CON-01")).replace("_", "-")
        self.naam = config.get(
            "naam", "Contextspecifieke formulering zonder expliciete benoeming"
        )
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
        self.prioriteit = config.get("prioriteit", "hoog")

        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens CON-01 regel.

        Deze regel controleert of de definitie geen expliciete verwijzing bevat
        naar de opgegeven context(en). De context moet impliciet doorklinken
        zonder letterlijke benoeming.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        definitie_lc = definitie.lower()
        # Ondersteun zowel legacy 'contexten' als V2 velden op top-niveau
        contexten: dict[str, Any] = {}
        if context:
            if isinstance(context.get("contexten"), dict):
                contexten = context.get("contexten") or {}
            else:
                contexten = {
                    "organisatorische_context": context.get("organisatorische_context")
                    or [],
                    "juridische_context": context.get("juridische_context") or [],
                    "wettelijke_basis": context.get("wettelijke_basis") or [],
                }

        # 0️⃣ Extra check: er mag niet meer dan 1 definitie bestaan met exact zelfde begrip + context (synoniemen tellen niet mee)
        try:
            if DefinitieRepository and begrip:
                repo = DefinitieRepository()

                def _as_str_one(val: Any) -> str:
                    if isinstance(val, list):
                        return str(val[0]) if val else ""
                    return str(val or "")

                org = _as_str_one(contexten.get("organisatorische_context", []))
                jur = _as_str_one(contexten.get("juridische_context", []))
                wet = contexten.get("wettelijke_basis", [])
                wet_list = wet if isinstance(wet, list) else []

                if org or jur or wet_list:
                    cnt = repo.count_exact_by_context(
                        begrip=begrip,
                        organisatorische_context=org,
                        juridische_context=jur,
                        wettelijke_basis=wet_list,
                    )
                    if cnt > 1:
                        return (
                            False,
                            f"❌ {self.id}: er bestaan meerdere definities voor dit begrip met dezelfde context (aantal: {cnt}). Consolidatie of hergebruik aanbevolen.",
                            0.0,
                        )
        except Exception:  # Soft-fail: laat overige checks doorlopen
            pass

        # 1️⃣ Dynamisch: user-gegeven contexten
        expliciete_hits = []
        for _label, waardelijst in contexten.items():
            if not waardelijst:
                continue
            for w in waardelijst:
                w = w.lower().strip()
                # Check varianten van context woorden
                varianten = {w, w + "e", w + "en", w.rstrip("e")}
                for var in varianten:
                    if var and var in definitie_lc:
                        expliciete_hits.append(var)

        if expliciete_hits:
            gevonden = ", ".join(sorted(set(expliciete_hits)))
            return (
                False,
                f"❌ {self.id}: opgegeven context letterlijk in definitie herkend ('{gevonden}')",
                0.0,
            )

        # 2️⃣ Herken bredere contexttermen via patronen
        contextuele_term_hits = set()
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            contextuele_term_hits.update(match.lower() for match in matches)

        # 3️⃣ Vergelijk met voorbeeldzinnen
        goede_match = any(vb.lower() in definitie_lc for vb in self.goede_voorbeelden)
        foute_match = any(vb.lower() in definitie_lc for vb in self.foute_voorbeelden)

        if contextuele_term_hits:
            if foute_match:
                return (
                    False,
                    f"❌ {self.id}: bredere contexttermen herkend ({', '.join(sorted(contextuele_term_hits))}), en lijkt op fout voorbeeld",
                    0.0,
                )
            return (
                False,
                f"🟡 {self.id}: bredere contexttaal herkend ({', '.join(sorted(contextuele_term_hits))}), formulering mogelijk vaag",
                0.5,
            )

        if foute_match:
            return False, f"❌ {self.id}: definitie bevat expliciet fout voorbeeld", 0.0

        if goede_match:
            return True, f"✔️ {self.id}: definitie komt overeen met goed voorbeeld", 1.0

        # 5️⃣ Fallback - niets herkend
        return True, f"✔️ {self.id}: geen expliciete contextverwijzing aangetroffen", 0.9

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append(
            "Formuleer de definitie contextneutraal zonder expliciete verwijzingen"
        )
        hints.append(
            "Vermijd termen zoals: 'binnen de context van', 'juridisch', 'beleidsmatig'"
        )
        hints.append("Vermijd organisatienamen zoals: DJI, OM, KMAR")
        hints.append("Laat de context impliciet doorklinken in de formulering")

        if self.goede_voorbeelden:
            hints.append(f"Goed voorbeeld: {self.goede_voorbeelden[0]}")

        return hints


def create_validator(config_path: str | None = None) -> CON01Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        CON01Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "CON-01.json")

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return CON01Validator(config)
