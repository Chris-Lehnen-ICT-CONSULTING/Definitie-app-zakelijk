"""
JSON Validator Loader - Laadt individuele validators uit JSON/Python paren.

Deze module laadt validators dynamisch uit de config/toetsregels/regels directory
waar elke toetsregel bestaat uit een JSON configuratie en bijbehorende Python implementatie.
"""

import importlib.util
import json
import logging
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

logger = logging.getLogger(__name__)


def _is_safe_regel_id(regel_id: Any) -> bool:
    """
    Controleer of een regel ID één bestandsnaamcomponent is.

    Weigert lege waarden, '.', '..', NUL-bytes en beide padseparators. Absolute
    paden en traversal bevatten altijd een separator of zijn '..', en vallen
    daarmee onder dezelfde weigering, zodat een ID nooit buiten de aangewezen
    directory kan wijzen.
    """
    if not isinstance(regel_id, str) or not regel_id:
        return False
    # Expliciet: Path('..').name is '..', dus een naam-check vangt dit niet af
    if regel_id in (".", ".."):
        return False
    return not ("\x00" in regel_id or "/" in regel_id or "\\" in regel_id)


def _resolve_within_root(root: Path, path: Path) -> Path | None:
    """
    Controleer of ``path`` binnen ``root`` blijft en geef het laadpad terug.

    De controle gebeurt op de volledig geresolveerde vormen van root en pad,
    maar teruggegeven wordt het OORSPRONKELIJKE ``path`` -- niet de
    geresolveerde variant. Daardoor blijven ``module.__file__`` en op
    ``__file__`` gebaseerde companionbestanden op de gekozen (alias)locatie
    staan, precies zoals vóór deze padcheck.

    Symlinks binnen de root blijven toegestaan; symlinks die naar buiten wijzen,
    ontbrekende bestanden en padfouten (loops, ongeldige namen) leveren None op.
    Dit borgt uitsluitend confinement binnen het aangewezen pad; er wordt geen
    bescherming geclaimd tegen gelijktijdige vijandige mutatie van het
    bestandssysteem, zoals een symlinkswap na de controle.
    """
    try:
        # Snelpad voor het normale geval: ``path`` is ``root`` plus precies één
        # naamcomponent en dat component is zelf geen symlink. Het bestand ligt
        # dan hoe dan ook direct onder ``root`` -- er is geen enkele symlink die
        # het daarbuiten kan brengen -- dus de twee volledige resolves voegen
        # niets toe. Er wordt niets onthouden: elke aanroep doet een verse lstat,
        # zodat latere map- of symlinkwijzigingen meteen meetellen. Symlinks,
        # ontbrekende paden en alles wat niet exact één component onder de root
        # ligt, volgen hieronder de volledige route.
        if (
            path.parent == root
            and path.name not in (".", "..")
            and not stat.S_ISLNK(os.lstat(path).st_mode)
        ):
            return path

        resolved_root = root.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
        resolved_path.relative_to(resolved_root)
    except (OSError, ValueError, RuntimeError):
        return None
    return path


class JSONValidatorLoader:
    """
    Loader voor individuele JSON/Python validator paren.

    Deze loader ondersteunt de flexibele architectuur waar elke
    toetsregel zijn eigen JSON en Python bestand heeft.
    """

    def __init__(self, regels_dir: str | None = None):
        """
        Initialiseer de validator loader.

        Args:
            regels_dir: Directory met JSON/Python validator paren
        """
        if regels_dir is None:
            # Default naar de standaard locatie (regels/ subdir van toetsregels/)
            self.regels_dir = Path(__file__).parent / "regels"
        else:
            self.regels_dir = Path(regels_dir)

        self._validators_cache: dict[str, Any] = {}
        self._json_cache: dict[str, dict[str, Any]] = {}

        logger.info(
            f"JSONValidatorLoader geïnitialiseerd met directory: {self.regels_dir}"
        )

    def load_validator(self, regel_id: str) -> Any | None:
        """
        Laad een specifieke validator.

        Args:
            regel_id: ID van de regel (bijv. 'CON-01')

        Returns:
            Validator instantie of None
        """
        # Weiger onveilige IDs vóór cachelookup, bestandstoegang en import
        if not _is_safe_regel_id(regel_id):
            logger.warning(f"Ongeldig regel ID geweigerd: {regel_id!r}")
            return None

        # Check cache
        if regel_id in self._validators_cache:
            return self._validators_cache[regel_id]

        # Laad JSON config
        json_config = self.load_json_config(regel_id)
        if not json_config:
            logger.warning(f"Geen JSON configuratie gevonden voor {regel_id}")
            return None

        # Bepaal mogelijke Python bestandsnamen
        # Primair: CON-01 -> CON_01.py
        candidates = [regel_id.replace("-", "_") + ".py"]
        # Alternatief (ARAI-01 → ARAI01.py, ARAI-02SUB1 → ARAI02SUB1.py)
        candidates.append(regel_id.replace("-", "") + ".py")

        # Lexicale sibling van regels_dir: bewust vóór resolving bepaald, zodat
        # een regels_dir-symlink de keuze van validators/ niet verlegt.
        validators_dir = self.regels_dir.parent / "validators"
        py_path = None
        for name in candidates:
            path = _resolve_within_root(validators_dir, validators_dir / name)
            if path is not None:
                py_path = path
                break

        if py_path is None:
            logger.warning(
                f"Geen Python implementatie gevonden voor {regel_id} (geprobeerd: {', '.join(candidates)})"
            )
            return None

        try:
            # Dynamisch laden van Python module
            spec = importlib.util.spec_from_file_location(
                f"toetsregel_{regel_id}", py_path
            )
            if spec is None or spec.loader is None:
                logger.error(f"Kon geen module spec laden voor {py_path}")
                return None
            module: ModuleType = importlib.util.module_from_spec(spec)
            sys.modules[f"toetsregel_{regel_id}"] = module
            spec.loader.exec_module(module)

            # Zoek validator class (conventie: {ID}Validator)
            class_name = f"{regel_id.replace('-', '')}Validator"
            validator_class = getattr(module, class_name, None)

            if validator_class is None:
                logger.error(f"Geen {class_name} gevonden in {py_path}")
                return None

            # Instantieer validator met JSON config
            validator = validator_class(json_config)

            # Cache voor hergebruik
            self._validators_cache[regel_id] = validator

            logger.debug(f"Validator {regel_id} succesvol geladen")
            return validator

        except Exception as e:
            logger.error(f"Fout bij laden validator {regel_id}: {e}")
            return None

    def load_json_config(self, regel_id: str) -> dict[str, Any] | None:
        """
        Laad JSON configuratie voor een regel.

        Args:
            regel_id: ID van de regel

        Returns:
            JSON configuratie als dict of None
        """
        # Weiger onveilige IDs vóór cachelookup en bestandstoegang
        if not _is_safe_regel_id(regel_id):
            logger.warning(f"Ongeldig regel ID geweigerd: {regel_id!r}")
            return None

        if regel_id in self._json_cache:
            return cast(dict[str, Any], self._json_cache[regel_id])

        json_path = _resolve_within_root(
            self.regels_dir, self.regels_dir / f"{regel_id}.json"
        )

        if json_path is None:
            return None

        try:
            with open(json_path, encoding="utf-8") as f:
                config = json.load(f)

            # Voeg ID toe aan config voor consistentie
            config["id"] = regel_id

            # Cache config
            self._json_cache[regel_id] = config

            return cast(dict[str, Any], config)

        except Exception as e:
            logger.error(f"Fout bij laden JSON voor {regel_id}: {e}")
            return None

    def get_all_regel_ids(self) -> list[str]:
        """
        Haal alle beschikbare regel IDs op.

        Returns:
            Lijst met regel IDs
        """
        regel_ids = []

        # Zoek alle JSON bestanden
        for json_file in self.regels_dir.glob("*.json"):
            if json_file.stem != "__init__":
                regel_ids.append(json_file.stem)

        return sorted(regel_ids)

    def validate_definitie(
        self,
        definitie: str,
        begrip: str,
        regel_ids: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Valideer een definitie met de opgegeven regels.

        Args:
            definitie: Te valideren definitie
            begrip: Term die gedefinieerd wordt
            regel_ids: Lijst met regel IDs om te gebruiken (None = alle)
            context: Extra context informatie

        Returns:
            Lijst met validatie resultaten als strings
        """
        if regel_ids is None:
            regel_ids = self.get_all_regel_ids()

        results = []
        passed = 0
        failed = 0

        for regel_id in regel_ids:
            validator = self.load_validator(regel_id)

            if validator is None:
                results.append(f"⏭️ {regel_id}: Validator niet gevonden")
                continue

            try:
                # Roep validate aan (oude interface)
                success, message, score = validator.validate(definitie, begrip, context)

                # Format resultaat
                if success:
                    results.append(f"✅ {regel_id}: {message}")
                    passed += 1
                else:
                    results.append(f"❌ {regel_id}: {message}")
                    failed += 1

            except Exception as e:
                results.append(f"⚠️ {regel_id}: Fout tijdens validatie - {e!s}")
                logger.error(f"Validatie fout voor {regel_id}: {e}")

        # Voeg samenvatting toe aan begin
        total = len(regel_ids)
        if total > 0:
            score_percentage = (passed / total) * 100
            summary = f"📊 **Toetsing Samenvatting**: {passed}/{total} regels geslaagd ({score_percentage:.1f}%)"
            if failed > 0:
                summary += f" | ❌ {failed} gefaald"
            results.insert(0, summary)

        return results


# Globale loader instantie
json_validator_loader = JSONValidatorLoader()
