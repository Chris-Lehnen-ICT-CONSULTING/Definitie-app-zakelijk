"""DEF-503/DEF-606 Task 2: 53× evaluator-/reachabilitymatrix.

Per rule-ID bewijst deze runner tegen het échte validatiepad
(`validate_definition`) dat de geclassificeerde runtime-uitkomst klopt:

- ``automatisch`` (evt. ``gewicht_nul: true``): de negatieve case MOET een
  violation voor die regel opleveren, de positieve case NIET, en de
  grenscase precies wat het fixture zegt. Een regel die "automatisch"
  claimt maar nooit kan falen (inert/default-pass) laat de runner falen.
- ``niet_automatisch_toetsbaar`` / ``bewust_niet_scorend`` /
  ``defect_inert``: de adversariële probe MOET géén violation geven —
  dat documenteert de onbereikbaarheid; gaat de regel tóch af, dan is de
  classificatie verouderd en faalt de runner eveneens.

Verder faalt de runner bij: een rule-ID op disk zonder fixture-entry (en
andersom), een onbekende evaluator, en een gedeclareerd veld dat de
evaluator stil negeert (bv. ``vereist_param``) zonder expliciete
``defect_inert``-classificatie. De aantallen per categorie worden uit de
fixture afgeleid en door de asserties bewezen — nergens hardcoded.
"""

from pathlib import Path

import pytest
import yaml

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from toetsregels.rule_cache import RUNTIME_VELDEN

pytestmark = [pytest.mark.unit]

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "toetsregels"
    / "runtime_cases.yaml"
)
REGELS_DIR = Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"

# Velden die _evaluate_json_rule daadwerkelijk leest (rule.get-inventaris).
# NB: RUNTIME_VELDEN (rule_cache) bevat óók vereist_param — dat veld wordt
# bewaard maar door géén evaluator-tak geconsumeerd; het verschil tussen
# beide sets is precies wat "stil genegeerd" betekent.
EVALUATOR_GELEZEN_VELDEN = frozenset(
    {
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
    }
)

GELDIGE_EVALUATORS = frozenset({"json_generiek", "special_case", "positieve_indicator"})
GELDIGE_STATUSSEN = frozenset(
    {
        "automatisch",
        "niet_automatisch_toetsbaar",
        "bewust_niet_scorend",
        "defect_inert",
    }
)
AUTOMATISCH = "automatisch"


def _laad_fixture() -> dict[str, dict]:
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and data, "runtime_cases.yaml is leeg"
    return data


MATRIX = _laad_fixture()
RULE_IDS_OP_DISK = sorted(p.stem for p in REGELS_DIR.glob("*.json"))


def _tekst_van(case: dict) -> str:
    herhaal = case.get("tekst_herhaal")
    if herhaal:
        return (str(herhaal["token"]) + " ") * int(herhaal["n"])
    return case.get("tekst", "")


@pytest.fixture(scope="module")
def svc() -> ModularValidationService:
    return ModularValidationService(get_toetsregel_manager(), None, None)


async def _violations_voor(svc, rule_id: str, case: dict) -> list[dict]:
    res = await svc.validate_definition(
        begrip=case.get("begrip", "begrip"),
        text=_tekst_van(case),
        ontologische_categorie=case.get("categorie"),
        context={},
    )
    return [
        v
        for v in res.get("violations", [])
        if str(v.get("code", "")).upper() == rule_id.upper()
    ]


class TestMatrixVolledigheid:
    def test_fixture_dekt_alle_rules_op_disk(self):
        ontbreekt = sorted(set(RULE_IDS_OP_DISK) - set(MATRIX))
        assert not ontbreekt, f"rule-IDs zonder fixture-entry: {ontbreekt}"

    def test_fixture_heeft_geen_spookregels(self):
        spook = sorted(set(MATRIX) - set(RULE_IDS_OP_DISK))
        assert not spook, f"fixture-entries zonder JSON-regel: {spook}"

    @pytest.mark.parametrize("rule_id", sorted(MATRIX), ids=str)
    def test_entry_contract(self, rule_id):
        entry = MATRIX[rule_id]
        assert (
            entry.get("evaluator") in GELDIGE_EVALUATORS
        ), f"{rule_id}: onbekende evaluator {entry.get('evaluator')!r}"
        status = entry.get("scoringstatus")
        assert (
            status in GELDIGE_STATUSSEN
        ), f"{rule_id}: onbekende scoringstatus {status!r}"
        if status == AUTOMATISCH:
            for verplicht in ("positief", "negatief", "grens"):
                assert verplicht in entry, f"{rule_id}: case '{verplicht}' ontbreekt"
        else:
            assert "probe" in entry, f"{rule_id}: adversariële probe ontbreekt"
            assert entry.get("reden"), f"{rule_id}: reden verplicht bij {status}"

    @pytest.mark.parametrize("rule_id", sorted(MATRIX), ids=str)
    def test_geen_stil_genegeerde_velden(self, rule_id):
        import json

        entry = MATRIX[rule_id]
        raw = json.loads((REGELS_DIR / f"{rule_id}.json").read_text(encoding="utf-8"))
        # required_fields moeten echt in de JSON staan
        for veld in entry.get("required_fields", []):
            assert veld in raw, f"{rule_id}: required veld '{veld}' staat niet in JSON"
        # Runtime-velden in de JSON die geen enkele evaluator-tak leest
        # mogen alleen bestaan onder een expliciete defect_inert-vlag.
        stil = sorted((set(raw) & set(RUNTIME_VELDEN)) - EVALUATOR_GELEZEN_VELDEN)
        if stil and entry.get("scoringstatus") != "defect_inert":
            pytest.fail(
                f"{rule_id}: veld(en) {stil} worden door geen evaluator-tak "
                f"gelezen (stil genegeerd) — classificeer defect_inert of "
                f"implementeer de tak"
            )


class TestReachability:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rule_id",
        [r for r in sorted(MATRIX) if MATRIX[r]["scoringstatus"] == AUTOMATISCH],
        ids=str,
    )
    async def test_negatieve_case_faalt(self, svc, rule_id):
        entry = MATRIX[rule_id]
        vios = await _violations_voor(svc, rule_id, entry["negatief"])
        assert vios, (
            f"{rule_id}: negatieve case geeft géén violation — regel is "
            f"inert of de case raakt de failure branch niet"
        )
        verwacht = entry["negatief"].get("verwacht_in_melding")
        if verwacht:
            berichten = " | ".join(str(v.get("message", "")) for v in vios)
            assert (
                verwacht.lower() in berichten.lower()
            ), f"{rule_id}: melding bevat niet {verwacht!r}: {berichten}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rule_id",
        [r for r in sorted(MATRIX) if MATRIX[r]["scoringstatus"] == AUTOMATISCH],
        ids=str,
    )
    async def test_positieve_case_passeert(self, svc, rule_id):
        entry = MATRIX[rule_id]
        vios = await _violations_voor(svc, rule_id, entry["positief"])
        assert not vios, (
            f"{rule_id}: positieve case triggert onterecht: "
            f"{[v.get('message') for v in vios]}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rule_id",
        [r for r in sorted(MATRIX) if MATRIX[r]["scoringstatus"] == AUTOMATISCH],
        ids=str,
    )
    async def test_grenscase(self, svc, rule_id):
        entry = MATRIX[rule_id]
        grens = entry["grens"]
        verwacht = grens.get("verwacht", "geen_violation")
        vios = await _violations_voor(svc, rule_id, grens)
        if verwacht == "violation":
            assert vios, f"{rule_id}: grenscase zou moeten falen maar passeert"
        else:
            assert not vios, (
                f"{rule_id}: grenscase zou moeten passeren maar faalt: "
                f"{[v.get('message') for v in vios]}"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rule_id",
        [r for r in sorted(MATRIX) if MATRIX[r]["scoringstatus"] != AUTOMATISCH],
        ids=str,
    )
    async def test_niet_scorende_regel_is_echt_onbereikbaar(self, svc, rule_id):
        entry = MATRIX[rule_id]
        vios = await _violations_voor(svc, rule_id, entry["probe"])
        assert not vios, (
            f"{rule_id}: geclassificeerd als {entry['scoringstatus']!r} maar "
            f"de probe triggert wél een violation — herclassificeer naar "
            f"automatisch: {[v.get('message') for v in vios]}"
        )


class TestAfgeleideTelling:
    def test_telling_sluit_op_53(self):
        telling: dict[str, int] = {}
        for entry in MATRIX.values():
            telling[entry["scoringstatus"]] = telling.get(entry["scoringstatus"], 0) + 1
        totaal = sum(telling.values())
        assert (
            totaal == len(RULE_IDS_OP_DISK) == 53
        ), f"telling {telling} sluit niet op de 53 regels op disk"
        # Zichtbaar bewijs in de testoutput (geen hardcoded verwachting).
        print(f"\nRuntime-matrix telling: {dict(sorted(telling.items()))}")
