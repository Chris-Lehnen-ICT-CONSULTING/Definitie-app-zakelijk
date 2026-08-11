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
        return " ".join([str(herhaal["token"])] * int(herhaal["n"]))
    return case.get("tekst", "")


@pytest.fixture(
    scope="module", params=["toetsregel_manager", "cached_manager (productiepad)"]
)
def svc(request) -> ModularValidationService:
    # De matrix draait over BEIDE regelbronnen: de volledige
    # ToetsregelManager (unit-testpad) én de CachedToetsregelManager →
    # RuleCache-keten (productiepad). De DEF-606-bug zat precies in de
    # divergentie tussen die twee; laat RuleCache opnieuw een veld
    # vallen, dan wordt deze matrix rood op het productiepad.
    if request.param.startswith("cached_manager"):
        from toetsregels.cached_manager import get_cached_toetsregel_manager
        from toetsregels.rule_cache import get_rule_cache

        get_rule_cache().clear_cache()  # geen stale FileCache-entries
        manager = get_cached_toetsregel_manager()
    else:
        manager = get_toetsregel_manager()
    return ModularValidationService(manager, None, None)


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
        # Dispositie-koppeling (ALG-375): elke niet-automatische status en
        # elk gedocumenteerd defect (overtriggerend) vereist een tracker-ID
        # zodat een defect niet stil kan blijven staan.
        if status != AUTOMATISCH or entry.get("overtriggerend"):
            import re as _re

            issue = str(entry.get("issue", ""))
            assert _re.fullmatch(r"DEF-\d+", issue), (
                f"{rule_id}: 'issue: DEF-nnn' verplicht bij status {status!r} "
                f"of overtriggerend-vlag (gevonden: {issue!r})"
            )

    def test_evaluator_leesset_is_deel_van_runtime_contract(self):
        # EVALUATOR_GELEZEN_VELDEN is declaratief (grep-inventaris van
        # rule.get-calls). Leesregressies op velden mét cases worden al
        # door de reachability-cases gevangen; deze assert bewaakt alleen
        # de consistentie met het cache-contract. Waargenomen leesset:
        # DEF-621 (hardening).
        assert set(RUNTIME_VELDEN) >= EVALUATOR_GELEZEN_VELDEN

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
            hint = (
                f" (gedocumenteerd defect: {entry['issue']} — is het defect "
                f"gefixt? Werk dan deze fixture-entry bij)"
                if entry.get("issue")
                else ""
            )
            assert vios, f"{rule_id}: grenscase zou moeten falen maar passeert{hint}"
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
    # Het bewezen contract van dit moment. Dit is GEEN vrije aanname
    # (vgl. de afgewezen "37/10/3"-telling): elke case hierachter is door
    # de reachability-tests afgedwongen. Verschuift een regel van
    # categorie, dan hoort deze verdeling bewust mee te veranderen.
    VERWACHTE_VERDELING = {
        "automatisch": 50,
        "bewust_niet_scorend": 1,
        "defect_inert": 1,
        "niet_automatisch_toetsbaar": 1,
    }

    def test_telling_sluit_op_53(self):
        telling: dict[str, int] = {}
        for entry in MATRIX.values():
            telling[entry["scoringstatus"]] = telling.get(entry["scoringstatus"], 0) + 1
        assert (
            sum(telling.values()) == len(RULE_IDS_OP_DISK) == 53
        ), f"telling {telling} sluit niet op de 53 regels op disk"
        assert telling == self.VERWACHTE_VERDELING, (
            f"categorieverdeling verschoven: {dict(sorted(telling.items()))} "
            f"!= {self.VERWACHTE_VERDELING} — bewuste wijziging? Werk dan "
            f"ook fixture en verwachting bij"
        )


class _StubManager:
    """Minimale manager voor synthetische regels (waarde-doorwerking)."""

    def __init__(self, regels: dict):
        self._regels = regels

    def get_all_regels(self) -> dict:
        return self._regels


def _svc_met(regels: dict) -> ModularValidationService:
    return ModularValidationService(_StubManager(regels), None, None)


async def _syn_violations(regels: dict, begrip: str, tekst: str) -> list[dict]:
    svc = _svc_met(regels)
    res = await svc.validate_definition(
        begrip=begrip, text=tekst, ontologische_categorie=None, context={}
    )
    return [
        v for v in res.get("violations", []) if v.get("code", "").startswith("SYN-")
    ]


class TestVeldDoorwerking:
    """Bewijst dat de evaluator de WAARDE van elk baselineveld gebruikt.

    De roundtrip-test toont alleen dat velden de cache overleven; deze
    mutatietests (grens +-1, vlag aan/uit) tonen dat de uitkomst met de
    waarde meebeweegt (review PR #396, test-agent).
    """

    TEKST = "definitie van precies zeven woorden lang hier"
    _CHARS = len(TEKST)  # zelf-kalibrerend: geen handgetelde lengtes
    _WORDS = len(TEKST.split())

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("veld", "faalwaarde", "slaagwaarde"),
        [
            ("min_chars", _CHARS + 1, _CHARS),
            ("max_chars", _CHARS - 1, _CHARS),
            ("min_words", _WORDS + 1, _WORDS),
            ("max_words", _WORDS - 1, _WORDS),
        ],
    )
    async def test_numerieke_grens_werkt_door(self, veld, faalwaarde, slaagwaarde):
        faal = await _syn_violations({"SYN-01": {veld: faalwaarde}}, "x", self.TEKST)
        slaag = await _syn_violations({"SYN-01": {veld: slaagwaarde}}, "x", self.TEKST)
        assert (
            faal
        ), f"{veld}={faalwaarde} zou moeten falen op {self._WORDS}w/{self._CHARS}t"
        assert not slaag, (
            f"{veld}={slaagwaarde} zou moeten passeren op "
            f"{self._WORDS}w/{self._CHARS}t"
        )

    @pytest.mark.asyncio
    async def test_circular_definition_vlag_werkt_door(self):
        tekst = "een sanctie is een opgelegde straf"
        aan = await _syn_violations(
            {"SYN-01": {"circular_definition": True}}, "sanctie", tekst
        )
        uit = await _syn_violations(
            {"SYN-01": {"circular_definition": False}}, "sanctie", tekst
        )
        assert aan and not uit

    @pytest.mark.asyncio
    async def test_forbidden_phrase_werkt_door(self):
        met = await _syn_violations(
            {"SYN-01": {"forbidden_phrases": ["verboden frase"]}},
            "x",
            "tekst met een verboden frase erin",
        )
        zonder = await _syn_violations(
            {"SYN-01": {"forbidden_phrases": ["komt niet voor"]}},
            "x",
            "tekst met een verboden frase erin",
        )
        assert met and not zonder


class TestWaargenomenLeesset:
    def test_evaluator_leest_alle_gedeclareerde_velden(self):
        # Review PR #396 (arch + tests): EVALUATOR_GELEZEN_VELDEN was
        # louter declaratief; als de evaluator een veld niet meer leest,
        # bleef de stil-genegeerd-check ten onrechte streng lijken. Hier
        # observeren we de echte reads via een recording-dict over de 53
        # regels heen: elk gedeclareerd veld moet daadwerkelijk gelezen
        # worden.
        import asyncio
        import json

        gelezen: set[str] = set()

        class _RecordingDict(dict):
            def get(self, sleutel, default=None):
                gelezen.add(sleutel)
                return super().get(sleutel, default)

            def __getitem__(self, sleutel):
                gelezen.add(sleutel)
                return super().__getitem__(sleutel)

            def __contains__(self, sleutel):
                gelezen.add(sleutel)
                return super().__contains__(sleutel)

        regels = {
            p.stem: _RecordingDict(json.loads(p.read_text(encoding="utf-8")))
            for p in REGELS_DIR.glob("*.json")
        }
        svc = _svc_met(regels)
        asyncio.run(
            svc.validate_definition(
                begrip="besluiten",
                text="de tekst, die effectief en niet zonder context is",
                ontologische_categorie=None,
                context={},
            )
        )
        niet_gelezen = EVALUATOR_GELEZEN_VELDEN - gelezen
        assert not niet_gelezen, (
            f"gedeclareerde evaluator-velden zonder waargenomen read: "
            f"{sorted(niet_gelezen)} — EVALUATOR_GELEZEN_VELDEN loopt "
            f"achter op de evaluator"
        )
