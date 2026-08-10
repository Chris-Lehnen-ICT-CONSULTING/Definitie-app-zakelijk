"""DEF-603: regressietest organisatiekeuze.

US-442 (okt 2025) verwijderde onbedoeld IND, NFI en de Raad voor de
Kinderbescherming uit de organisatiekeuze: de vervangende selector leest
`ui_cfg.organizational_contexts` en die lijst miste de drie organisaties
uit het (verweesde) `context_options.ORGANIZATIONS`.
"""

from pathlib import Path

import pytest
import yaml

from config.config_manager import UIConfig

pytestmark = [pytest.mark.unit]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_YAML = PROJECT_ROOT / "config" / "config.yaml"

# De drie organisaties die in US-442 uit de keuzelijst verdwenen.
HERSTELDE_ORGANISATIES = ["IND", "NFI", "Raad voor de Kinderbescherming"]


def _yaml_organizational_contexts() -> list[str]:
    data = yaml.safe_load(CONFIG_YAML.read_text(encoding="utf-8"))
    return data["ui"]["organizational_contexts"]


class TestOrganisatiekeuze:
    @pytest.mark.parametrize("organisatie", HERSTELDE_ORGANISATIES)
    def test_dataclass_default_bevat_herstelde_organisaties(self, organisatie):
        assert organisatie in UIConfig().organizational_contexts

    @pytest.mark.parametrize("organisatie", HERSTELDE_ORGANISATIES)
    def test_yaml_overlay_bevat_herstelde_organisaties(self, organisatie):
        # De config.yaml-overlay wint van de dataclass-default; de fix moet
        # dus op beide plekken staan.
        assert organisatie in _yaml_organizational_contexts()

    def test_yaml_en_dataclass_default_zijn_identiek(self):
        # Voorkomt nieuwe drift tussen de twee bronnen — precies het
        # mechanisme waardoor deze regressie kon ontstaan.
        assert _yaml_organizational_contexts() == UIConfig().organizational_contexts

    def test_anders_blijft_laatste_optie(self):
        assert UIConfig().organizational_contexts[-1] == "Anders..."
