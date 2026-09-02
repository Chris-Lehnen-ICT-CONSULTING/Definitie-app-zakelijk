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
from dataclasses import replace
from pathlib import Path

import pytest

import toetsregels.rule_cache as rule_cache_module
from toetsregels.rule_cache import (
    _RECORD_DEFAULTS,
    RuleCache,
    _load_all_rules_cached,
)
from toetsregels.runtime_contract import (
    RuleContractError,
    build_rule_records,
    canonical_rule_id,
    root_contract_policy,
)

pytestmark = [pytest.mark.unit]

REGELS_DIR = Path(rule_cache_module.__file__).parent / "regels"

ALLE_REGEL_JSONS = sorted(REGELS_DIR.glob("*.json"))

# De contractuele ID-set uit de root-SSOT: de enige geldige verwachting.
CONTRACT_IDS = tuple(root_contract_policy().rule_ids)

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
    def test_loader_faalt_op_corrupt_bestand(self, tmp_path):
        # DEF-621 maakte de fail-open zichtbaar: een corrupt regelbestand
        # werd overgeslagen en de loader logde "INCOMPLEET". DEF-606 gaat
        # een stap verder en sluit het gat: er komt geen gedeeltelijke set
        # meer uit, want die draait gewoon door met minder regels en tilt de
        # kwaliteitsscore op zonder dat er iets zichtbaar misgaat.
        (tmp_path / "GOED-01.json").write_text(
            '{"id": "GOED-01", "naam": "ok"}', encoding="utf-8"
        )
        (tmp_path / "KAPOT-01.json").write_text("{niet-json", encoding="utf-8")

        with pytest.raises(RuleContractError, match="KAPOT-01"):
            _load_all_rules_cached.__wrapped__(str(tmp_path))

    def test_stats_tonen_volledige_lading(self):
        cache = RuleCache()
        cache.clear_cache()
        stats = cache.get_stats()
        assert stats["rules_files_on_disk"] == 53
        assert stats["total_rules_cached"] == 53
        assert stats["rules_load_complete"] is True
        assert stats["rules_expected_count"] == len(CONTRACT_IDS)
        assert stats["rules_missing"] == []
        assert stats["rules_unexpected"] == []


class TestVolledigheidIsGeenTelling:
    """DEF-621 commit 4: `rules_load_complete` vergelijkt verzamelingen.

    De oude formule was `len(all_rules) == files_on_disk`. Die telt twee
    grootheden tegen elkaar die samen bewegen, en meldt daardoor volledigheid
    op precies de momenten waarop er iets mis is. Beide tests hieronder falen
    met die oude formule en slagen met de vergelijking tegen de contractuele
    ID-set uit de root-SSOT.

    `RuleCache` is een proces-singleton (`__new__`). Alles wat hier wordt
    gezet, gaat daarom via `monkeypatch`, dat instantie- en klasseattributen
    exact terugzet. Zonder die discipline houdt de singleton na afloop een
    lege of vervalste regelset vast, die later opduikt als een onverklaarbare
    failure in een andere suite.
    """

    @staticmethod
    def _stats_met_geladen_set(
        monkeypatch,
        tmp_path,
        geladen: dict[str, dict],
        op_schijf: list[str] | None = None,
    ) -> dict:
        """Draai de échte `get_stats()` over een opgegeven geladen set.

        Alleen `get_all_rules()` wordt vervangen - de volledigheidslogica
        zelf blijft het onderwerp van de test.

        `op_schijf` bepaalt welke stems er werkelijk in de tijdelijke regelmap
        komen te staan; standaard exact de geladen ID's. Dat is geen decor:
        het legt `rules_files_on_disk` gelijk aan het aantal geladen regels,
        precies de situatie waarin de oude formule
        `len(all_rules) == files_on_disk` volledigheid meldt. Zonder die
        gelijkstelling zou die formule toevallig ook `False` geven en zou de
        test niets onderscheiden. Een afwijkende `op_schijf` modelleert een
        warme cache waarvan de bron inmiddels is veranderd.
        """
        for regel_id in geladen if op_schijf is None else op_schijf:
            (tmp_path / f"{regel_id}.json").write_text("{}", encoding="utf-8")

        cache = RuleCache()
        monkeypatch.setattr(cache, "regels_dir", tmp_path)
        monkeypatch.setattr(RuleCache, "get_all_rules", lambda self: geladen)
        return cache.get_stats()

    def test_lege_set_met_nul_bestanden_is_nooit_compleet(self, tmp_path, monkeypatch):
        """De tautologie in haar zuiverste vorm: 0 == 0 meldde volledigheid.

        Een lege regelmap laadt nul regels; de oude formule vergeleek dat met
        nul bestanden en concludeerde compleet. Er is dan geen enkele
        toetsregel actief, en juist dat mag nooit als gezonde toestand worden
        gerapporteerd.
        """
        stats = self._stats_met_geladen_set(monkeypatch, tmp_path, {})

        assert stats["total_rules_cached"] == 0
        assert stats["rules_files_on_disk"] == 0
        assert stats["rules_load_complete"] is False
        assert stats["rules_expected_count"] == len(CONTRACT_IDS)
        assert sorted(stats["rules_missing"]) == sorted(CONTRACT_IDS)
        assert stats["rules_unexpected"] == []

    def test_zelfde_aantal_met_een_vreemd_id_is_niet_compleet(
        self, tmp_path, monkeypatch
    ):
        """Gelijke cardinaliteit is geen gelijke verzameling.

        Er zijn evenveel regels geladen als het contract noemt, maar het is
        niet dezelfde set: één verwacht ID is vervangen door een onbekend ID.
        Elke vergelijking op aantallen laat dit passeren.
        """
        ontbrekend = CONTRACT_IDS[0]
        vreemd = "ZZZ-99"
        geladen = {rid: {} for rid in CONTRACT_IDS[1:]}
        geladen[vreemd] = {}
        assert len(geladen) == len(CONTRACT_IDS), "opzetfout: cardinaliteit wijkt af"

        stats = self._stats_met_geladen_set(monkeypatch, tmp_path, geladen)

        assert stats["total_rules_cached"] == stats["rules_expected_count"]
        assert stats["rules_files_on_disk"] == stats["total_rules_cached"]
        assert stats["rules_load_complete"] is False
        assert stats["rules_missing"] == [ontbrekend]
        assert stats["rules_unexpected"] == [vreemd]


class TestWarmeCacheMaskeertBronverliesNiet:
    """DEF-621 commit 4: de bronset op schijf telt óók mee.

    `get_all_rules()` levert binnen de TTL een warme cache. Verdwijnt er
    daarna een regelbestand, dan blijft de gecachete set compleet en
    rapporteerde `get_stats()` gewoon `rules_load_complete=True` - terwijl de
    bron het contract niet meer dekt. Een healthcheck bleef daardoor een uur
    lang groen op een regelset die niet meer bestaat.

    De vergelijking loopt daarom over drie verzamelingen: verwacht (root-
    SSOT), geladen (cache) en actueel op schijf (stems). Er wordt geen
    JSON-inhoud gelezen en er wordt niets ge-invalideerd; `get_stats` is een
    diagnosepad en mag geen cache-effecten hebben.
    """

    _stats_met_geladen_set = staticmethod(
        TestVolledigheidIsGeenTelling._stats_met_geladen_set
    )

    def test_verdwenen_bronbestand_bij_warme_cache(self, tmp_path, monkeypatch):
        """De cache is compleet, de bron niet - dat mag niet groen zijn."""
        verdwenen = CONTRACT_IDS[0]
        geladen = {rid: {} for rid in CONTRACT_IDS}
        op_schijf = [rid for rid in CONTRACT_IDS if rid != verdwenen]

        stats = self._stats_met_geladen_set(
            monkeypatch, tmp_path, geladen, op_schijf=op_schijf
        )

        assert stats["total_rules_cached"] == len(CONTRACT_IDS)
        assert stats["rules_files_on_disk"] == len(CONTRACT_IDS) - 1
        assert stats["rules_load_complete"] is False
        # De geladen set dekt het contract nog wél; alleen de bron niet.
        assert stats["rules_missing"] == []
        assert stats["rules_unexpected"] == []
        assert stats["rules_source_missing"] == [verdwenen]
        assert stats["rules_source_unexpected"] == []

    def test_onverwacht_bronbestand_bij_warme_cache(self, tmp_path, monkeypatch):
        """Een extra JSON op schijf hoort net zo zichtbaar te zijn."""
        vreemd = "ZZZ-99"
        geladen = {rid: {} for rid in CONTRACT_IDS}
        op_schijf = [*CONTRACT_IDS, vreemd]

        stats = self._stats_met_geladen_set(
            monkeypatch, tmp_path, geladen, op_schijf=op_schijf
        )

        assert stats["total_rules_cached"] == len(CONTRACT_IDS)
        assert stats["rules_files_on_disk"] == len(CONTRACT_IDS) + 1
        assert stats["rules_load_complete"] is False
        assert stats["rules_missing"] == []
        assert stats["rules_unexpected"] == []
        assert stats["rules_source_missing"] == []
        assert stats["rules_source_unexpected"] == [vreemd]

    def test_canonieke_alias_op_schijf_is_niet_compleet(self, tmp_path, monkeypatch):
        """Twee stems met dezelfde canonieke vorm zijn samen één bestand te veel.

        `ARAI-01.json` en `ARAI_01.json` normaliseren allebei naar `ARAI01`.
        De canonieke bronindex klapt ze samen, dus een zuivere
        verzamelingsvergelijking ziet 53 == 53 en meldt volledigheid - terwijl
        er 54 bestanden staan en niemand weet welke van de twee de geldende
        regel is. Precies de drift die dit project historisch heeft (`VER_01`
        naast `VER-01`, `ARAI01` naast `ARAI-01`). Alleen de cardinaliteit
        ontmaskert dit; de setvergelijking kan het per definitie niet zien.
        """
        alias = CONTRACT_IDS[0].replace("-", "_")
        assert alias != CONTRACT_IDS[0], "opzetfout: contract-ID zonder koppelteken"
        assert canonical_rule_id(alias) == canonical_rule_id(CONTRACT_IDS[0])

        geladen = {rid: {} for rid in CONTRACT_IDS}
        op_schijf = [*CONTRACT_IDS, alias]

        stats = self._stats_met_geladen_set(
            monkeypatch, tmp_path, geladen, op_schijf=op_schijf
        )

        # De drie canonieke verzamelingen zijn hier gelijk; de tellingen niet.
        assert stats["rules_source_missing"] == []
        assert stats["rules_source_unexpected"] == []
        assert stats["rules_expected_count"] == len(CONTRACT_IDS)
        assert stats["rules_files_on_disk"] == len(CONTRACT_IDS) + 1
        assert stats["rules_load_complete"] is False

    def test_canonieke_alias_in_de_cache_is_niet_compleet(self, tmp_path, monkeypatch):
        """Dezelfde botsing, maar dan in de warme cache in plaats van op schijf.

        De bron is hier volledig in orde: 53 bestanden, 53 contract-ID's. De
        cache draagt er één te veel omdat `ARAI_01` naast `ARAI-01` is blijven
        staan. Canoniek klappen die samen, dus alle vier de diff-lijsten zijn
        leeg en beide setvergelijkingen zeggen "gelijk"; alleen de telling van
        de geladen regels ontmaskert het. Zonder deze test zou het schrappen
        van juist die clausule door geen enkele test worden betrapt.
        """
        alias = CONTRACT_IDS[0].replace("-", "_")
        assert alias != CONTRACT_IDS[0], "opzetfout: contract-ID zonder koppelteken"

        geladen = {rid: {} for rid in CONTRACT_IDS}
        geladen[alias] = {}
        op_schijf = list(CONTRACT_IDS)

        stats = self._stats_met_geladen_set(
            monkeypatch, tmp_path, geladen, op_schijf=op_schijf
        )

        assert stats["rules_missing"] == []
        assert stats["rules_unexpected"] == []
        assert stats["rules_source_missing"] == []
        assert stats["rules_source_unexpected"] == []
        assert stats["total_rules_cached"] == len(CONTRACT_IDS) + 1
        assert stats["rules_expected_count"] == len(CONTRACT_IDS)
        assert stats["rules_files_on_disk"] == len(CONTRACT_IDS)
        assert stats["rules_load_complete"] is False


class TestBuildRuleRecordsPolicy:
    """DEF-621: `build_rule_records()` accepteert een expliciete policy.

    Zonder die doorgifte las de functie altijd de met `lru_cache` afgedekte
    `root_contract_policy()`. Een aanroeper die de policy zélf vers uit de
    root-SSOT laadde, kreeg daardoor records die tegen een oudere generatie
    waren gevalideerd: verse ID's, oude recordvereisten.
    """

    def test_expliciete_policy_met_extra_eis_faalt(self, cache_records):
        """Een strengere policy moet de bestaande records afwijzen."""
        strenger = replace(
            root_contract_policy(),
            record_required_fields=(
                *root_contract_policy().record_required_fields,
                "nieuw_verplicht_veld",
            ),
        )
        assert not any("nieuw_verplicht_veld" in r for r in cache_records.values())

        with pytest.raises(RuleContractError, match="nieuw_verplicht_veld"):
            build_rule_records(cache_records, policy=strenger)

    def test_zonder_policy_blijft_het_bestaande_gedrag(self, cache_records):
        """De default blijft de procespolicy; bestaande callers wijzigen niet."""
        records = build_rule_records(cache_records)

        assert set(records) == set(cache_records)
        assert set(records) == set(CONTRACT_IDS)


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
