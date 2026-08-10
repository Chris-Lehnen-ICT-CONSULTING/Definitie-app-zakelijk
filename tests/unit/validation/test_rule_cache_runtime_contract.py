"""DEF-606 Task 1: roundtrip-contract JSON → RuleCache runtime-record.

`rule_cache._load_all_rules_cached` zegt "alle velden" te bewaren maar
construeert een whitelist; normatieve uitvoeringsvelden verdwijnen
daardoor vóór evaluatie. Omdat de productie-wiring
(definition_orchestrator_v2 → CachedToetsregelManager → RuleCache) deze
projectie aan ModularValidationService levert, vuren de betrokken
checks in productie stil nooit.

Naamtoewijzing plan → JSON: min_karakters=min_chars,
max_karakters=max_chars, circular_reference=circular_definition,
verboden_frase=forbidden_phrases, vereist_param=vereist_param.
"""

import json
from pathlib import Path

import pytest

from toetsregels.rule_cache import RuleCache, _load_all_rules_cached

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(_load_all_rules_cached.__wrapped__.__code__.co_filename).parent / (
    "regels"
)

ALLE_REGEL_JSONS = sorted(REGELS_DIR.glob("*.json"))

# Velden die _evaluate_json_rule (modular_validation_service) leest —
# het uitvoerbare deel van het regelcontract.
RUNTIME_VELDEN = (
    "aanbeveling",
    "circular_definition",
    "forbidden_phrases",
    "herkenbaar_patronen",
    "max_chars",
    "max_words",
    "min_chars",
    "min_commas",
    "min_words",
    "prioriteit",
    "redundancy_patterns",
    "required_patterns",
    "vereist_param",
)

# Defaults die het cache-record altijd garandeerde (consumers rekenen
# op aanwezigheid van deze sleutels).
GEGARANDEERDE_DEFAULTS = {
    "naam": "",
    "prioriteit": "midden",
    "aanbeveling": "optioneel",
    "herkenbaar_patronen": [],
    "uitleg": "",
    "toetsvraag": "",
    "goede_voorbeelden": [],
    "foute_voorbeelden": [],
}


def _laad_projectie() -> dict[str, dict]:
    # Bewust via __wrapped__: omzeilt de FileCache op disk zodat een
    # stale cache-entry (TTL 1u) de roundtrip-toets niet kan vervuilen.
    return _load_all_rules_cached.__wrapped__(str(REGELS_DIR))


@pytest.fixture(scope="module")
def cache_records() -> dict[str, dict]:
    records = _laad_projectie()
    assert len(records) == 53, "verwacht exact 53 regelrecords"
    return records


class TestRoundtripVerliestNiets:
    @pytest.mark.parametrize("json_path", ALLE_REGEL_JSONS, ids=lambda p: p.stem)
    def test_elk_bronveld_overleeft_de_cache(self, json_path, cache_records):
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        record = cache_records[json_path.stem]
        verloren = {
            veld: waarde
            for veld, waarde in raw.items()
            if veld not in record or record[veld] != waarde
        }
        assert not verloren, (
            f"{json_path.stem}: cache verliest of wijzigt velden: "
            f"{sorted(verloren)}"
        )

    @pytest.mark.parametrize("json_path", ALLE_REGEL_JSONS, ids=lambda p: p.stem)
    def test_runtime_velden_expliciet(self, json_path, cache_records):
        # Gerichte regressie op de uitvoerbare velden (DEF-606
        # acceptatiecriterium: min/max/circulariteit/vereist_param).
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        record = cache_records[json_path.stem]
        for veld in RUNTIME_VELDEN:
            if veld in raw:
                assert record.get(veld) == raw[veld], (
                    f"{json_path.stem}: runtime-veld '{veld}' verliest zijn "
                    f"waarde in de cache"
                )

    def test_defaults_blijven_gegarandeerd(self, cache_records):
        for regel_id, record in cache_records.items():
            for veld, default in GEGARANDEERDE_DEFAULTS.items():
                assert veld in record, (
                    f"{regel_id}: gegarandeerde sleutel '{veld}' ontbreekt "
                    f"(default was {default!r})"
                )
            assert record.get("id"), f"{regel_id}: id ontbreekt of leeg"


class TestPubliekPad:
    def test_get_rule_levert_volledig_record(self):
        # Via het publieke singleton-pad, na expliciete clear zodat de
        # verse projectie geladen wordt (geen stale FileCache-entry).
        cache = RuleCache()
        cache.clear_cache()
        raw = json.loads((REGELS_DIR / "SAM-06.json").read_text(encoding="utf-8"))
        record = cache.get_rule("SAM-06")
        assert record is not None
        assert (
            record.get("vereist_param") == raw["vereist_param"]
        ), "SAM-06: vereist_param overleeft het publieke get_rule-pad niet"
