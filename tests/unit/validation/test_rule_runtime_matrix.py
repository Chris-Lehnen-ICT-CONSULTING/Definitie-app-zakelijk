"""DEF-503/DEF-606 Task 2: 53× evaluator-/reachabilitymatrix.

Per rule-ID bewijst deze runner tegen het échte validatiepad
(`validate_definition`) dat de geclassificeerde runtime-uitkomst klopt:

- ``automated``: de negatieve case MOET een violation voor die regel
  opleveren, de positieve case NIET, en de grenscase precies wat de fixture
  zegt. Een regel die "automated" claimt maar nooit kan falen
  (inert/default-pass) laat de runner falen.
- ``review_required`` / ``not_evaluated``: de adversariële probe MOET géén
  violation geven — dat documenteert de uitkomst; gaat de regel tóch af,
  dan is de classificatie verouderd en faalt de runner eveneens.

De classificatie komt sinds DEF-624 uit het gevalideerde ``runtime_contract``
in het regelrecord zelf, niet meer uit deze fixture: die was een tweede
waarheid naast het record. De fixture draagt alleen nog de cases.

Verder faalt de runner bij: een rule-ID op disk zonder fixture-entry (en
andersom), een fixture-entry die zijn eigen classificatie meebrengt, en een
gedeclareerd veld dat de evaluator stil negeert (bv. ``vereist_param``)
terwijl het record zich automatisch noemt. De aantallen per categorie worden
uit de records afgeleid en door de asserties bewezen — nergens hardcoded.
"""

import json
from pathlib import Path

import pytest
import yaml

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from toetsregels.rule_cache import RUNTIME_VELDEN
from toetsregels.runtime_contract import (
    AutomationStatus,
    Executability,
    build_rule_records,
)

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


def _laad_fixture() -> dict[str, dict]:
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and data, "runtime_cases.yaml is leeg"
    return data


MATRIX = _laad_fixture()
RULE_IDS_OP_DISK = sorted(p.stem for p in REGELS_DIR.glob("*.json"))

# DEF-624: de classificatie stond in deze fixture en was daarmee een tweede
# waarheid naast de regelrecords. Zij komt nu uit het gevalideerde contract;
# de fixture houdt alleen nog de cases.
RECORDS = build_rule_records(
    {
        pad.stem: json.loads(pad.read_text(encoding="utf-8"))
        for pad in REGELS_DIR.glob("*.json")
    }
)


def _is_automatisch(rule_id: str) -> bool:
    return RECORDS[rule_id].automation_status is AutomationStatus.AUTOMATED


def _vereist_repository(rule_id: str) -> bool:
    """Kan deze regel alleen met de begrippenverzameling worden beoordeeld?

    Deze matrix draait bewust zonder repository (`_beschikbare_invoer`), zodat
    hij het tekstpad meet. Een regel met `executability: repository` kan daar
    per contract geen `pass`/`fail` opleveren maar uitsluitend
    `not_evaluated` — dat is de uitkomst die DEF-624 voorschrijft voor
    ontbrekende vereiste invoer, en nadrukkelijk géén `pass`.
    """
    return RECORDS[rule_id].executability is Executability.REPOSITORY


AUTOMATISCHE_IDS = sorted(r for r in RULE_IDS_OP_DISK if _is_automatisch(r))
# Automatische regels die de matrix werkelijk kan meten: alles wat geen
# repository nodig heeft. De repository-regels worden hieronder apart getoetst
# (`TestRepositoryregelsZonderRepository`); hun gedrág mét repository staat in
# `test_con01_duplicaatdetectie.py` en `test_contractconsistentie_def674.py`.
AUTOMATISCH_TEKSTPAD_IDS = sorted(
    r for r in AUTOMATISCHE_IDS if not _vereist_repository(r)
)
AUTOMATISCH_REPOSITORY_IDS = sorted(
    r for r in AUTOMATISCHE_IDS if _vereist_repository(r)
)
NIET_AUTOMATISCHE_IDS = sorted(r for r in RULE_IDS_OP_DISK if not _is_automatisch(r))


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


async def _resultaat_voor(svc, case: dict) -> dict:
    return await svc.validate_definition(
        begrip=case.get("begrip", "begrip"),
        text=_tekst_van(case),
        ontologische_categorie=case.get("categorie"),
        context={},
    )


def _violations_uit(res: dict, rule_id: str) -> list[dict]:
    return [
        v
        for v in res.get("violations", [])
        if str(v.get("code", "")).upper() == rule_id.upper()
    ]


async def _violations_voor(svc, rule_id: str, case: dict) -> list[dict]:
    return _violations_uit(await _resultaat_voor(svc, case), rule_id)


def _beschikbare_invoer(case: dict) -> set[str]:
    """Welke gedeclareerde invoer heeft de probe daadwerkelijk?

    Spiegelt `ModularValidationService._available_inputs` voor de argumenten
    die deze runner meegeeft: tekst en begrip altijd, categorie alleen als de
    case er een noemt, en géén repository of contextlijsten. Bewust hier
    uitgeschreven en niet uit de service geleend — dat laatste zou de
    verwachting met de implementatie mee laten bewegen.
    """
    beschikbaar = {"definition_text"}
    if str(case.get("begrip", "begrip")).strip():
        beschikbaar.add("term")
    if case.get("categorie"):
        beschikbaar.add("ontological_category")
    return beschikbaar


def _verwachte_runtimestatus(rule_id: str, case: dict) -> str:
    """De status die het contract voor deze probe voorschrijft.

    Ontbreekt vereiste invoer, dan is `not_evaluated` het contractuele
    antwoord; anders moet de runtime exact de gedeclareerde
    automatiseringsstatus opleveren.
    """
    record = RECORDS[rule_id]
    beschikbaar = _beschikbare_invoer(case)
    if any(vereist.value not in beschikbaar for vereist in record.required_inputs):
        return "not_evaluated"
    return record.automation_status.value


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
        status = RECORDS[rule_id].automation_status
        if _is_automatisch(rule_id) and not _vereist_repository(rule_id):
            for verplicht in ("positief", "negatief", "grens"):
                assert verplicht in entry, f"{rule_id}: case '{verplicht}' ontbreekt"
        else:
            # Ook een automatische regel die de repository vereist draagt een
            # probe: deze matrix meet het tekstpad, en daar hoort zij
            # `not_evaluated` op te leveren (DEF-674).
            assert "probe" in entry, f"{rule_id}: adversariële probe ontbreekt"
            assert entry.get("reden"), f"{rule_id}: reden verplicht bij {status.value}"
        # Dispositie-koppeling (ALG-375): elke niet-automatische status en
        # elk gedocumenteerd defect (overtriggerend) vereist een tracker-ID
        # zodat een defect niet stil kan blijven staan.
        if not _is_automatisch(rule_id) or entry.get("overtriggerend"):
            import re as _re

            issue = str(entry.get("issue", ""))
            assert _re.fullmatch(r"DEF-\d+", issue), (
                f"{rule_id}: 'issue: DEF-nnn' verplicht bij status "
                f"{status.value!r} of overtriggerend-vlag (gevonden: {issue!r})"
            )

    def test_fixture_dupliceert_de_classificatie_niet(self):
        # De classificatie hoort in het RuleRecord, niet in twee bronnen.
        gedupliceerd = sorted(
            rule_id
            for rule_id, entry in MATRIX.items()
            if {"evaluator", "scoringstatus"} & set(entry)
        )
        assert not gedupliceerd, (
            f"fixture-entries met een eigen classificatie naast het "
            f"regelrecord: {gedupliceerd}"
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
        if stil and _is_automatisch(rule_id):
            pytest.fail(
                f"{rule_id}: veld(en) {stil} worden door geen evaluator-tak "
                f"gelezen (stil genegeerd) terwijl de regel automatisch "
                f"heet — implementeer de tak of herclassificeer het record"
            )


class TestReachability:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rule_id",
        AUTOMATISCH_TEKSTPAD_IDS,
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
        AUTOMATISCH_TEKSTPAD_IDS,
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
        AUTOMATISCH_TEKSTPAD_IDS,
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
        NIET_AUTOMATISCHE_IDS,
        ids=str,
    )
    async def test_niet_scorende_regel_is_echt_onbereikbaar(self, svc, rule_id):
        """De probe moet de werkelijke status raken, niet alleen violations.

        DEF-670 (review PR #397, bevinding 8): deze test asserteerde alleen
        `not vios`. Voor de niet-automatische regels kan die assertie
        structureel niet falen — `judgment_review` en de uitgestelde
        strategieën leveren nooit een violation, wat de invoer ook is. De test
        bevestigde dus de classificatie in plaats van haar te toetsen.

        Daarom kijkt hij nu naar `rule_statuses`: staat een als
        `review_required` geclassificeerde regel opeens op `pass` of `fail`,
        dan draait er wél een automatische beoordeling en is de classificatie
        verouderd. De verwachting komt uit het regelrecord (root-SSOT), niet
        uit een tweede tabel in de fixture.
        """
        entry = MATRIX[rule_id]
        res = await _resultaat_voor(svc, entry["probe"])
        vios = _violations_uit(res, rule_id)
        assert not vios, (
            f"{rule_id}: contract zegt "
            f"{RECORDS[rule_id].automation_status.value!r} maar "
            f"de probe triggert wél een violation — herclassificeer naar "
            f"automatisch: {[v.get('message') for v in vios]}"
        )

        status = res["rule_statuses"].get(rule_id)
        assert status is not None, f"{rule_id}: geen rule_status in het resultaat"
        assert status not in ("pass", "fail"), (
            f"{rule_id}: contract zegt "
            f"{RECORDS[rule_id].automation_status.value!r} maar de runtime "
            f"levert {status!r} — er draait dus tóch een automatische "
            f"beoordeling; herclassificeer het record"
        )
        assert status == _verwachte_runtimestatus(rule_id, entry["probe"]), (
            f"{rule_id}: runtime levert {status!r}, contract schrijft "
            f"{_verwachte_runtimestatus(rule_id, entry['probe'])!r} voor"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rule_id", AUTOMATISCH_TEKSTPAD_IDS, ids=str)
    async def test_automatische_regel_levert_een_gemeten_status(self, svc, rule_id):
        """De keerzijde: een automatische regel moet écht meten.

        Zonder deze test kon een als `automated` geclassificeerde regel
        stilzwijgend `not_evaluated` of `error` opleveren en toch groen
        blijven, zolang de negatieve case ergens een violation opleverde.
        """
        entry = MATRIX[rule_id]
        res = await _resultaat_voor(svc, entry["positief"])
        status = res["rule_statuses"].get(rule_id)
        assert status in ("pass", "fail"), (
            f"{rule_id}: heet automatisch maar levert {status!r} op de "
            f"positieve case — die regel wordt niet werkelijk beoordeeld"
        )


class TestRepositoryregelsZonderRepository:
    """Automatische regels die de begrippenverzameling nodig hebben (DEF-674).

    Deze matrix meet het tekstpad en geeft geen repository mee. Een regel met
    `executability: repository` levert daar per contract `not_evaluated` op —
    nooit `pass`, want dan zou een niet-uitgevoerde controle als geslaagd
    tellen, precies de default-pass die DEF-624 sluit.

    Het gedrag mét repository staat in `test_con01_duplicaatdetectie.py` en
    `test_contractconsistentie_def674.py`, waar een echte SQLite-repository
    wordt gebruikt.
    """

    @pytest.mark.parametrize("rule_id", AUTOMATISCH_REPOSITORY_IDS, ids=str)
    @pytest.mark.asyncio
    async def test_zonder_repository_niet_evaluated(self, svc, rule_id):
        entry = MATRIX[rule_id]
        res = await _resultaat_voor(svc, entry["probe"])
        status = res["rule_statuses"].get(rule_id)
        assert status == "not_evaluated", (
            f"{rule_id} vereist de repository; zonder die invoer is "
            f"{status!r} niet het contractuele antwoord"
        )

    @pytest.mark.parametrize("rule_id", AUTOMATISCH_REPOSITORY_IDS, ids=str)
    @pytest.mark.asyncio
    async def test_zonder_repository_geen_violation(self, svc, rule_id):
        entry = MATRIX[rule_id]
        vios = await _violations_voor(svc, rule_id, entry["probe"])
        assert not vios, (
            f"{rule_id} kon niet worden beoordeeld maar levert tóch een "
            f"violation: {vios}"
        )

    def test_er_is_ten_minste_een_repositoryregel(self):
        # Zonder deze assertie zou de klasse hierboven leeg kunnen draaien en
        # daarmee stilzwijgend niets bewijzen.
        assert AUTOMATISCH_REPOSITORY_IDS == ["DUP_01"], (
            "de uitsluiting van het tekstpad is vastgepind op DUP_01. Schuift "
            "een andere regel naar `executability: repository`, dan verdwijnt "
            "zij stil uit vier gedragstests en houdt alleen de zwakkere "
            f"not_evaluated-toets over: {AUTOMATISCH_REPOSITORY_IDS}"
        )


class TestAfgeleideTelling:
    # Het bewezen contract van dit moment. Dit is GEEN vrije aanname
    # (vgl. de afgewezen 37/10/3-telling): elke case hierachter is door de
    # reachability-tests afgedwongen. De verdeling komt uit de regelrecords;
    # verschuift een regel van klasse, dan hoort deze verwachting bewust mee
    # te veranderen.
    VERWACHTE_VERDELING = {
        # DEF-674: DUP_01 ging van `not_evaluated` (uitgestelde evaluator) naar
        # `automated`. De duplicaatcontrole draaide al — maar in CON-01, waar
        # zij contractueel niet hoort. Zij heeft nu haar eigen evaluator op de
        # regel die "Bestaat deze definitie nog niet in de database?" toetst.
        "automated": 37,
        "review_required": 12,
        "not_evaluated": 4,
    }

    def test_telling_sluit_op_53(self):
        telling: dict[str, int] = {}
        for record in RECORDS.values():
            sleutel = record.automation_status.value
            telling[sleutel] = telling.get(sleutel, 0) + 1
        assert (
            sum(telling.values()) == len(RULE_IDS_OP_DISK) == 53
        ), f"telling {telling} sluit niet op de 53 regels op disk"
        assert telling == self.VERWACHTE_VERDELING, (
            f"klasseverdeling verschoven: {dict(sorted(telling.items()))} "
            f"!= {self.VERWACHTE_VERDELING} — bewuste wijziging? Werk dan "
            f"ook de regelrecords en deze verwachting bij"
        )

    def test_alleen_automatische_regels_wegen_mee_in_de_score(self):
        # DEF-624: een regel die niet automatisch wordt beoordeeld mag de
        # kwaliteitsscore niet raken, anders wordt dekking als kwaliteit
        # gepresenteerd.
        fout = sorted(
            record.rule_id
            for record in RECORDS.values()
            if record.counts_toward_score
            and record.automation_status is not AutomationStatus.AUTOMATED
        )
        assert not fout, f"niet-automatische regels met scorepolicy scored: {fout}"


# DEF-606: ook een synthetische regel heeft een gevalideerd contract nodig;
# zonder dat is er geen aanwijsbare evaluator en weigert de service te laden.
SYNTHETISCH_CONTRACT = {
    "evaluator": "generic",
    "required_inputs": ["definition_text", "term"],
    "executability": "deterministic",
    "automation_status": "automated",
    "score_policy": "scored",
}

# De verplichte recordvelden komen uit de root-SSOT; een synthetische regel
# moet daar net zo goed aan voldoen. `prioriteit: midden` houdt gewicht en
# severity gelijk aan wat een veldloos record eerder kreeg.
SYNTHETISCHE_RECORDVELDEN = {
    "naam": "Synthetische testregel",
    "uitleg": "Alleen voor waarde-doorwerkingstests.",
    "prioriteit": "midden",
}


def _met_contract(regels: dict) -> dict:
    """Vul een contract aan waar het ontbreekt; laat echte records intact.

    Records die al een contract dragen worden ongemoeid teruggegeven — ook
    hun type, zodat een observerende mapping (TestWaargenomenLeesset) niet
    stilletjes in een gewone dict verandert en de reads verloren gaan.
    """
    return {
        rule_id: (
            data
            if data.get("runtime_contract")
            else {
                "id": rule_id,
                **SYNTHETISCHE_RECORDVELDEN,
                "runtime_contract": {**SYNTHETISCH_CONTRACT},
                **data,
            }
        )
        for rule_id, data in regels.items()
    }


class _StubManager:
    """Minimale manager voor synthetische regels (waarde-doorwerking)."""

    def __init__(self, regels: dict):
        self._regels = regels

    def get_all_regels(self) -> dict:
        return self._regels


def _svc_met(regels: dict) -> ModularValidationService:
    return ModularValidationService(_StubManager(_met_contract(regels)), None, None)


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


class TestVerwachteTelling:
    def test_expected_count_uit_contract(self):
        # DEF-621: de service leidde zijn verwachte regeltelling niet
        # meer uit een hardcoded 45 af maar uit de bestanden op disk.
        svc = ModularValidationService(get_toetsregel_manager(), None, None)
        assert svc._rules_expected_count == len(RULE_IDS_OP_DISK) == 53
