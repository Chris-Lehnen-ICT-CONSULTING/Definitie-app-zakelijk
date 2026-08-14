"""DEF-606/DEF-624: de rootconfig is echt de root-SSOT, niet alleen proza.

`config/toetsregels/toetsregels_config.yaml` wijst de contractpolicy aan.
Deze suite bewijst dat die aanwijzing bindend is: wijkt de YAML af van de
runtime-enums, dan faalt het laden zichtbaar in plaats van dat er stil een
tweede waarheid ontstaat.

Er wordt bewust met kopieën van de echte config gewerkt. Een test die zijn
eigen minimale YAML verzint zou de drift die hij moet aantonen niet kunnen
vinden — hij zou alleen zijn eigen fixture toetsen.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from toetsregels.runtime_contract import (
    ROOT_CONFIG_PATH,
    AutomationStatus,
    EvaluatorType,
    ExamplePairPolicy,
    Executability,
    RequiredInput,
    ResultStatus,
    RuleContractError,
    ScorePolicy,
    build_rule_record,
    load_root_contract_policy,
    root_contract_policy,
)

pytestmark = [pytest.mark.unit]

RUW = yaml.safe_load(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))


def _schrijf_variant(tmp_path: Path, muteer) -> Path:
    """Schrijf een kopie van de echte rootconfig met één gerichte mutatie."""
    data = copy.deepcopy(RUW)
    muteer(data)
    pad = tmp_path / "toetsregels_config.yaml"
    pad.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return pad


class TestRootPolicyAansluiting:
    @pytest.mark.parametrize(
        ("sleutel", "enum_type"),
        [
            ("evaluators", EvaluatorType),
            ("required_inputs", RequiredInput),
            ("executability", Executability),
            ("automation_status", AutomationStatus),
            ("score_policy", ScorePolicy),
            ("result_status", ResultStatus),
            ("example_pair_policy", ExamplePairPolicy),
        ],
    )
    def test_waardeset_is_identiek_aan_de_enum(self, sleutel, enum_type):
        policy = root_contract_policy()
        assert set(getattr(policy, sleutel)) == {
            lid.value for lid in enum_type
        }, f"'{sleutel}' in de root-SSOT wijkt af van {enum_type.__name__}"

    def test_resultaatstatussen_zijn_volledig(self):
        # Het onderscheid pass/fail/review_required/not_evaluated/error is de
        # kern van DEF-624; een ingekorte set zou default-pass terugbrengen.
        assert set(root_contract_policy().result_status) == {
            "pass",
            "fail",
            "review_required",
            "not_evaluated",
            "error",
        }

    def test_achterhaalde_pythonchecks_zijn_verdwenen(self):
        checks = set((RUW.get("validation") or {}).get("checks") or [])
        assert not checks & {
            "python_class_exists",
            "json_python_consistency",
        }, "de rootconfig eist nog controles op de niet-actieve Pythonlaag"
        assert "runtime_contract" in checks

    def test_json_is_het_enige_actieve_runtimeformaat(self):
        formats = (RUW["loading"])["formats"]
        assert formats["json"]["enabled"] is True
        assert formats["python"]["enabled"] is False
        assert RUW["loading"]["consistency"]["require_both_formats"] is False


class TestDriftFaaltZichtbaar:
    def test_onbekende_evaluator_in_yaml_faalt(self, tmp_path):
        def muteer(data):
            data["runtime_contract"]["evaluators"].append("verzonnen_evaluator")

        with pytest.raises(RuleContractError, match="runtime niet kent"):
            load_root_contract_policy(_schrijf_variant(tmp_path, muteer))

    def test_ontbrekende_evaluator_in_yaml_faalt(self, tmp_path):
        def muteer(data):
            data["runtime_contract"]["evaluators"].remove("judgment_review")

        with pytest.raises(RuleContractError, match="mist waarden"):
            load_root_contract_policy(_schrijf_variant(tmp_path, muteer))

    def test_ingekorte_resultaatstatus_faalt(self, tmp_path):
        def muteer(data):
            data["runtime_contract"]["result_status"] = ["pass", "fail"]

        with pytest.raises(RuleContractError, match="mist waarden"):
            load_root_contract_policy(_schrijf_variant(tmp_path, muteer))

    def test_afwijkende_contractvelden_falen(self, tmp_path):
        def muteer(data):
            data["runtime_contract"]["required_fields"].remove("score_policy")

        with pytest.raises(RuleContractError, match="wijkt af van wat de runtime"):
            load_root_contract_policy(_schrijf_variant(tmp_path, muteer))

    def test_ontbrekende_sectie_faalt(self, tmp_path):
        def muteer(data):
            del data["runtime_contract"]

        with pytest.raises(RuleContractError, match="ontbreekt"):
            load_root_contract_policy(_schrijf_variant(tmp_path, muteer))

    def test_lege_waardeset_faalt(self, tmp_path):
        def muteer(data):
            data["runtime_contract"]["score_policy"] = []

        with pytest.raises(RuleContractError, match="niet-lege lijst"):
            load_root_contract_policy(_schrijf_variant(tmp_path, muteer))

    def test_onleesbare_config_faalt(self, tmp_path):
        with pytest.raises(RuleContractError, match="niet leesbaar"):
            load_root_contract_policy(tmp_path / "bestaat-niet.yaml")


class TestRecordveldenUitDeRootconfig:
    def test_root_config_bepaalt_de_verplichte_recordvelden(self):
        assert set(root_contract_policy().record_required_fields) == {
            "id",
            "naam",
            "uitleg",
            "prioriteit",
            "runtime_contract",
        }

    @pytest.mark.parametrize(
        "veld", ["id", "naam", "uitleg", "prioriteit", "runtime_contract"]
    )
    def test_ontbrekend_recordveld_faalt(self, veld):
        import json

        pad = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "toetsregels"
            / "regels"
            / "CON-02.json"
        )
        data = json.loads(pad.read_text(encoding="utf-8"))
        data.pop(veld)
        with pytest.raises(RuleContractError):
            build_rule_record("CON-02", data)
