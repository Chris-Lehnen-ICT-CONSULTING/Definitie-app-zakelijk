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

import toetsregels.rule_cache as rule_cache_module
from toetsregels.rule_cache import (
    _RECORD_DEFAULTS,
    RuleCache,
    _load_all_rules_cached,
)

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(rule_cache_module.__file__).parent / "regels"

ALLE_REGEL_JSONS = sorted(REGELS_DIR.glob("*.json"))

# Velden die _evaluate_json_rule (modular_validation_service) leest —
# het uitvoerbare deel van het regelcontract. BEWUST een golden copy
# naast de productie-constante (importeren en ertegen toetsen zou een
# tautologie zijn); wijzigen vereist een bewuste update aan beide kanten.
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

# Defaults die het cache-record garandeert: het productiecontract zelf
# (import), zodat een verdwijnende default-sleutel hier direct faalt.
GEGARANDEERDE_DEFAULTS = dict(_RECORD_DEFAULTS)

# Runtime-velden die (nu) in geen enkele regel-JSON voorkomen; de
# dekkingstest bewaakt dat deze verzameling niet stil groeit door
# hernoemde of verwijderde velden in de bronbestanden.
VELDEN_ZONDER_VOORKOMEN = {"required_patterns"}


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
            raw = json.loads(
                (REGELS_DIR / f"{regel_id}.json").read_text(encoding="utf-8")
            )
            for veld, default in GEGARANDEERDE_DEFAULTS.items():
                assert veld in record, (
                    f"{regel_id}: gegarandeerde sleutel '{veld}' ontbreekt "
                    f"(default was {default!r})"
                )
                if veld not in raw:
                    # Niet alleen aanwezigheid: de default-wáárde is deel
                    # van het contract (een geflipte default is normatief).
                    assert record[veld] == default, (
                        f"{regel_id}: default van '{veld}' gewijzigd: "
                        f"{record[veld]!r} != {default!r}"
                    )
            assert record.get("id"), f"{regel_id}: id ontbreekt of leeg"
            # Bekende ID-drift (DEF-606): JSON-ids wijken af van de
            # bestandsnaam in scheidingstekens (VER_01 vs VER-01, ARAI01
            # vs ARAI-01). Zonder scheidingstekens moeten ze overeenkomen;
            # uniformering van de ID-vormen is DEF-606-scope.
            import re as _re

            genorm_id = _re.sub(r"[-_]", "", str(record["id"])).upper()
            genorm_key = _re.sub(r"[-_]", "", regel_id).upper()
            assert genorm_id == genorm_key, (
                f"{regel_id}: record-id {record['id']!r} wijst naar een "
                f"andere regel dan de cache-sleutel"
            )

    def test_runtime_velden_komen_ergens_voor(self, cache_records):
        # Vangt drift: een hernoemd/verwijderd runtime-veld in de bron-
        # JSONs zou test_runtime_velden_expliciet stil tot no-op maken.
        zonder_voorkomen = set()
        for veld in RUNTIME_VELDEN:
            if not any(
                veld in json.loads(p.read_text(encoding="utf-8"))
                for p in ALLE_REGEL_JSONS
            ):
                zonder_voorkomen.add(veld)
        assert zonder_voorkomen == VELDEN_ZONDER_VOORKOMEN, (
            f"runtime-velden zonder enig voorkomen gewijzigd: "
            f"{sorted(zonder_voorkomen)} != {sorted(VELDEN_ZONDER_VOORKOMEN)}"
        )

    def test_records_delen_geen_default_containers(self, cache_records):
        # Regressie op gedeelde mutable defaults: records zonder eigen
        # herkenbaar_patronen mogen niet hetzelfde list-object delen —
        # één .append() zou anders naar alle 53 regels lekken.
        sam05 = cache_records["SAM-05"]["herkenbaar_patronen"]
        concirc = cache_records["CON-CIRC-001"]["herkenbaar_patronen"]
        assert sam05 is not concirc, "records delen één default-list"
        assert (
            sam05 is not _RECORD_DEFAULTS["herkenbaar_patronen"]
        ), "record deelt de list uit de module-constante"


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

    def test_volledige_roundtrip_via_publiek_pad(self):
        # Dezelfde 53x-roundtrip maar dan door de echte cacheketen
        # (get_all_rules incl. FileCache-serialisatie), zodat veldverlies
        # in de cachelaag zelf ook gedekt is — niet alleen de loader.
        cache = RuleCache()
        cache.clear_cache()
        records = cache.get_all_rules()
        assert len(records) == 53
        for json_path in ALLE_REGEL_JSONS:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            record = records[json_path.stem]
            verloren = {
                veld
                for veld, waarde in raw.items()
                if veld not in record or record[veld] != waarde
            }
            assert (
                not verloren
            ), f"{json_path.stem}: publiek pad verliest velden: {sorted(verloren)}"


class TestDegradedState:
    def test_loader_meldt_incompleet_bij_corrupt_bestand(self, tmp_path, caplog):
        # Fail-open zichtbaar maken (DEF-621): een corrupt regelbestand
        # verdwijnt niet meer stil - de loader logt de incomplete set met
        # de ontbrekende rule-IDs.
        (tmp_path / "GOED-01.json").write_text(
            '{"id": "GOED-01", "naam": "ok"}', encoding="utf-8"
        )
        (tmp_path / "KAPOT-01.json").write_text("{niet-json", encoding="utf-8")
        import logging

        with caplog.at_level(logging.ERROR):
            records = _load_all_rules_cached.__wrapped__(str(tmp_path))
        assert set(records) == {"GOED-01"}
        assert any(
            "INCOMPLEET" in r.message and "KAPOT-01" in r.message
            for r in caplog.records
        ), "loader meldt de incomplete regelset niet"

    def test_stats_tonen_volledige_lading(self):
        cache = RuleCache()
        cache.clear_cache()
        stats = cache.get_stats()
        assert stats["rules_files_on_disk"] == 53
        assert stats["total_rules_cached"] == 53
        assert stats["rules_load_complete"] is True


class TestPatroonBudget:
    def test_alle_patronen_binnen_tijdsbudget(self):
        # ReDoS-vangnet (security-review PR #396): elk patroon uit elke
        # regel-JSON moet op pathologische input binnen het budget blijven.
        # Catastrophic backtracking (geneste kwantoren) valt hier direct
        # door de mand in CI.
        import re
        import time

        pathologisch = [
            "a" * 5000,
            ("woord " * 1500).strip(),
            "A" * 3000 + "!",
            ("simpel en complex " * 300).strip(),
        ]
        patroon_velden = (
            "herkenbaar_patronen",
            "herkenbaar_patronen_type",
            "herkenbaar_patronen_particulier",
            "herkenbaar_patronen_proces",
            "herkenbaar_patronen_resultaat",
            "redundancy_patterns",
            "required_patterns",
        )
        budget_s = 0.1
        # Geen uitzonderingen: de kwadratische VER-03-patronen zijn in
        # DEF-621 uit de bron verwijderd. Elk nieuw patroon moet binnen
        # het budget blijven.
        overschrijdingen = []
        for json_path in ALLE_REGEL_JSONS:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
            for veld in patroon_velden:
                for pat in raw.get(veld) or []:
                    try:
                        compiled = re.compile(pat, re.IGNORECASE)
                    except re.error:
                        continue  # kapot patroon is een ander defect
                    for tekst in pathologisch:
                        start = time.perf_counter()
                        compiled.search(tekst)
                        duur = time.perf_counter() - start
                        if duur > budget_s:
                            overschrijdingen.append(
                                (json_path.stem, veld, pat, round(duur, 3))
                            )
        assert not overschrijdingen, (
            f"patronen boven het {budget_s * 1000:.0f}ms-budget "
            f"(ReDoS-risico): {overschrijdingen}"
        )
