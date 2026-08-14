"""DEF-674 — het validatieresultaat mag zichzelf niet tegenspreken.

Review van PR #397 op `bc9f7a6c` legde vier tegenspraken bloot in het resultaat
dat contractversie 1.1.0 juist als publiek contract vastlegt. Geen ervan maakte
`is_acceptable` onjuist — het risico zit in de secundaire velden die een
consumer óók mag geloven.

**Gemeten op mergecommit `4d7addc2`, vóór deze fix:**

| Situatie | `is_acceptable` | `acceptance_gate.acceptable` |
| --- | --- | --- |
| gevonden duplicaat | **`True`** | `False` |
| repositorystoring (evaluatorfout) | `False` | `False`, maar zonder status of reden |

De eerste rij is de echte tegenspraak, en hij loopt andersom dan de review van
PR #397 meldde: `is_ok = gate_ok or soft_ok`, dus de soft floor (score ≥ 0,60
zonder blocking errors) overrulet een gate die de definitie juist afkeurt. Het
resultaat meldt dan "acceptabel" terwijl zijn eigen gate "niet acceptabel"
zegt.

Bij de repositorystoring blijkt de gate al `False` te staan — niet dankzij de
errorafhandeling, maar toevallig, doordat dezelfde invoer ook drie critical
violations oplevert. De gate draagt daar geen `status` en geen reden die de
evaluatiefout noemt, dus een consumer kan de blokkade niet aan de fout
toeschrijven.

De UI leest bovendien uitsluitend het gate-veld
(`validation_view.py:240-274`) en toont groen "Gates: OK" zodra dat veld
`True` is, ongeacht `is_acceptable`.

Daarnaast reisde het duplicaatsignaal buiten de statusboekhouding om: via
`ctx.metadata[DUPLICATE_STASH_KEY]`, opgepikt in een `try/except` met het
commentaar `(best-effort)`. Een gevonden duplicaat leverde daardoor tegelijk
`rule_statuses["CON-01"] == "pass"` én een violation.

**Eigenaarsbesluit (Chris, 2026-08-14):** duplicaatdetectie hoort contractueel
bij DUP_01, niet bij CON-01. DUP_01 heet "Geen duplicaat definities in
database", declareert `definition_repository` al als vereiste invoer en draagt
`executability: repository`. CON-01 toetst iets anders: of de context niet
letterlijk in de definitietekst staat. CON-01 houdt daarom uitsluitend zijn
patroontoets en blijft `scored`; DUP_01 krijgt de echte evaluator en blijft
`excluded_from_score`, maar een `fail` blokkeert expliciet de acceptatie.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from domain.context.normalisatie import contextsleutel
from services.interfaces import DuplicateCandidate
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import ResultStatus

pytestmark = [pytest.mark.unit]

BEGRIP = "besluit"
TEKST = (
    "type document dat op grond van de wet een publiekrechtelijke "
    "rechtshandeling bevat met uniek zaaknummer"
)
CONTEXT: dict[str, list[str]] = {
    "organisatorische_context": ["DJI"],
    "juridische_context": ["strafrecht"],
    "wettelijke_basis": ["Awb"],
}

# De regels waarvan de evaluatormodules in PR #397 zelf documenteren dat zij hun
# eigen goede voorbeeld afkeuren. Zolang dat defect bestaat mag het record niet
# beweren dat het voorbeeldpaar normatief is.
DEFECTE_VOORBEELDPAREN = ("ESS-05", "VER-01", "VER-03", "SAM-02")


class _KapotteRepository:
    """Aanwezige repository die op de publieke capability stukloopt."""

    def find_duplicate_candidates(self, begrip: str) -> list[Any]:
        raise RuntimeError("SQLite: database is locked")


class _RepositoryMetDuplicaat:
    """Levert precies één kandidaat die op begrip én context matcht."""

    def __init__(self, categorie: str | None = None) -> None:
        self._categorie = categorie

    def find_duplicate_candidates(self, begrip: str) -> list[DuplicateCandidate]:
        return [
            DuplicateCandidate(
                id=42,
                status="established",
                categorie=self._categorie,
                organisatorische_context=contextsleutel(
                    CONTEXT["organisatorische_context"]
                ),
                juridische_context=contextsleutel(CONTEXT["juridische_context"]),
                wettelijke_basis=contextsleutel(CONTEXT["wettelijke_basis"]),
            )
        ]


class _RepositoryZonderDuplicaat:
    def find_duplicate_candidates(self, begrip: str) -> list[DuplicateCandidate]:
        return []


async def _valideer(repository: Any, **extra_context: Any) -> dict[str, Any]:
    svc = ModularValidationService(
        get_toetsregel_manager(), None, None, repository=repository
    )
    return await svc.validate_definition(
        begrip=BEGRIP,
        text=TEKST,
        ontologische_categorie=None,
        context={**CONTEXT, **extra_context},
    )


def _duplicaatviolations(resultaat: dict[str, Any]) -> list[dict[str, Any]]:
    """Violations die over een gevonden duplicaat gaan.

    Filtert op `metadata.existing_definition_id` — het enige veld dat
    uitsluitend een duplicaatbevinding draagt. Een eerdere versie zocht op de
    woorden "duplicaat"/"duplicate" in de melding; die staan er niet in ("Bestaande
    definitie met dezelfde context gevonden"), waardoor het filter altijd leeg
    terugkwam en twee tests slaagden zonder iets te meten.
    """
    gevonden = []
    for v in resultaat.get("violations", []):
        metadata = v.get("metadata")
        if isinstance(metadata, dict) and "existing_definition_id" in metadata:
            gevonden.append(v)
    return gevonden


class TestGateSpreektDeAcceptatieNietTegen:
    """Invariant 1 en 2: één uitkomst, twee velden, nooit tegengesteld."""

    @pytest.mark.asyncio
    async def test_evaluatiefout_blokkeert_beide_velden(self):
        res = await _valideer(_KapotteRepository())

        # Voorwaarde: er is werkelijk een evaluatorfout opgetreden.
        assert res["evaluation_coverage"]["error"] >= 1, res["evaluation_coverage"]
        assert res["is_acceptable"] is False, res["overall_score"]

        gate = res.get("acceptance_gate") or {}
        assert gate, "resultaat draagt geen acceptance_gate om te toetsen"
        assert gate.get("acceptable") is False, (
            "acceptance_gate.acceptable is True terwijl is_acceptable False is — "
            f"twee velden van hetzelfde resultaat spreken elkaar tegen: {gate}"
        )
        # Op 4d7addc2 staat de gate hier toevallig al op False, door drie
        # critical violations op dezelfde invoer. De blokkade moet echter aan
        # de evaluatiefout toe te schrijven zijn, anders kan een consumer haar
        # niet onderscheiden van een gewone kwaliteitsafkeuring.
        gefaald = [str(g) for g in (gate.get("gates_failed") or [])]
        assert any(
            "error" in g.lower() or "fout" in g.lower() for g in gefaald
        ), f"gate noemt de evaluatiefout niet als blokkadegrond: {gefaald}"

    @pytest.mark.asyncio
    async def test_evaluatiefout_levert_een_zichtbare_status_en_reden(self):
        res = await _valideer(_KapotteRepository())
        gate = res.get("acceptance_gate") or {}

        status = str(gate.get("status") or "").lower()
        assert status and status not in {
            "pass",
            "ok",
        }, f"gate-status moet de blokkade tonen, niet {status!r}: {gate}"
        redenen = [str(r) for r in (gate.get("reasons") or [])]
        assert redenen, f"gate blokkeert zonder reden op te geven: {gate}"
        assert any(
            "fout" in r.lower() or "error" in r.lower() for r in redenen
        ), f"geen enkele reden noemt de evaluatiefout: {redenen}"

    @pytest.mark.asyncio
    async def test_de_twee_velden_zijn_altijd_gelijk(self):
        """Geldt voor elke uitkomst, niet alleen voor de errorbron."""
        for repository in (
            _KapotteRepository(),
            _RepositoryMetDuplicaat(),
            _RepositoryZonderDuplicaat(),
        ):
            res = await _valideer(repository)
            gate = res.get("acceptance_gate") or {}
            if not gate or gate.get("acceptable") is None:
                continue
            assert bool(gate["acceptable"]) == bool(res["is_acceptable"]), (
                f"{type(repository).__name__}: gate={gate.get('acceptable')} "
                f"maar is_acceptable={res['is_acceptable']}"
            )


class TestDuplicaatLooptViaDeStatusboekhouding:
    """Invariant 3 en 4: een echte EvaluationOutcome, geen metadata-stash."""

    @pytest.mark.asyncio
    async def test_gevonden_duplicaat_zet_dup01_op_fail(self):
        res = await _valideer(_RepositoryMetDuplicaat())
        assert res["rule_statuses"].get("DUP_01") == ResultStatus.FAIL.value, (
            "DUP_01 is de regel 'Geen duplicaat definities in database' en moet "
            f"bij een gevonden duplicaat falen: {res['rule_statuses'].get('DUP_01')}"
        )

    @pytest.mark.asyncio
    async def test_con01_doet_geen_duplicaatuitspraak_meer(self):
        res = await _valideer(_RepositoryMetDuplicaat())
        codes = {str(v.get("code")) for v in _duplicaatviolations(res)}
        assert "CON-01" not in codes, (
            "de duplicaatuitspraak hoort bij DUP_01, niet bij CON-01; "
            f"gevonden violation-codes: {codes}"
        )

    @pytest.mark.asyncio
    async def test_geen_enkel_signaal_reist_via_metadata(self):
        import services.validation.evaluators.context_metadata as cm

        assert not hasattr(cm, "DUPLICATE_STASH_KEY"), (
            "DUPLICATE_STASH_KEY bestaat nog; een bevinding die buiten "
            "EvaluationOutcome om reist, ontsnapt aan de statusboekhouding"
        )

    @pytest.mark.asyncio
    async def test_duplicaat_blokkeert_de_acceptatie(self):
        res = await _valideer(_RepositoryMetDuplicaat())
        assert res["is_acceptable"] is False, (
            "een gevonden duplicaat moet de acceptatie blokkeren "
            f"(score {res['overall_score']})"
        )
        gate = res.get("acceptance_gate") or {}
        assert gate.get("acceptable") is False, gate

    @pytest.mark.asyncio
    async def test_zonder_duplicaat_blijft_dup01_geslaagd(self):
        """Tegenhanger: de regel mag niet altijd falen."""
        res = await _valideer(_RepositoryZonderDuplicaat())
        assert res["rule_statuses"].get("DUP_01") == ResultStatus.PASS.value, res[
            "rule_statuses"
        ].get("DUP_01")

    @pytest.mark.asyncio
    async def test_geforceerd_duplicaat_behoudt_de_bedoelde_severity(self):
        """De force-escalatie uit DEF-672 blijft bestaan.

        Zonder force is een duplicaat een waarschuwing; mét force is het een
        expliciete, bewust genomen schending en dus zwaarder.
        """
        zacht = await _valideer(_RepositoryMetDuplicaat())
        hard = await _valideer(_RepositoryMetDuplicaat(), force_duplicate=True)

        zachte = _duplicaatviolations(zacht)
        harde = _duplicaatviolations(hard)
        assert zachte, f"geen duplicaatviolation gevonden: {zacht['violations']}"
        assert harde, f"geen duplicaatviolation gevonden: {hard['violations']}"

        assert zachte[0]["severity"] == "warning", zachte[0]
        assert zachte[0]["severity_level"] == "medium", zachte[0]
        assert harde[0]["severity"] == "error", harde[0]
        assert harde[0]["severity_level"] == "high", harde[0]


class TestRepositoryInvoerIsContractueel:
    """Invariant 5 en 6: wie de repository gebruikt, declareert haar ook."""

    def test_elke_repositoryregel_declareert_de_invoer(self):
        from toetsregels.runtime_contract import (
            Executability,
            RequiredInput,
            build_rule_records,
        )

        records = build_rule_records(get_toetsregel_manager().get_all_regels())
        fout = [
            code
            for code, record in records.items()
            if record.executability is Executability.REPOSITORY
            and RequiredInput.DEFINITION_REPOSITORY not in record.required_inputs
        ]
        assert not fout, f"repositoryregels zonder gedeclareerde invoer: {fout}"

    def test_dup01_is_een_repositoryregel(self):
        from toetsregels.runtime_contract import (
            Executability,
            RequiredInput,
            build_rule_records,
        )

        records = build_rule_records(get_toetsregel_manager().get_all_regels())
        dup = records["DUP_01"]
        assert dup.executability is Executability.REPOSITORY, dup.executability
        assert (
            RequiredInput.DEFINITION_REPOSITORY in dup.required_inputs
        ), dup.required_inputs

    def test_con01_gebruikt_de_repository_niet_meer(self):
        from toetsregels.runtime_contract import (
            Executability,
            RequiredInput,
            build_rule_records,
        )

        records = build_rule_records(get_toetsregel_manager().get_all_regels())
        con = records["CON-01"]
        assert con.executability is Executability.DETERMINISTIC, con.executability
        assert (
            RequiredInput.DEFINITION_REPOSITORY not in con.required_inputs
        ), "CON-01 toetst de formulering, niet de database"

    def test_con01_raakt_de_repository_ook_werkelijk_niet_meer_aan(self):
        """Gedragstest naast de contracttest hierboven.

        Het contract kan kloppen terwijl de evaluator de repository tóch
        gebruikt — dat wás precies de situatie op `4d7addc2`. Deze test roept
        de echte CON-01-evaluator aan met een spion en telt de aanroepen.
        """
        from services.validation.evaluators.base import EvaluationDeps
        from services.validation.evaluators.context_metadata import (
            ContextMetadataEvaluator,
        )
        from services.validation.types_internal import EvaluationContext
        from toetsregels.runtime_contract import RequiredInput, build_rule_records

        class _Spion:
            def __init__(self) -> None:
                self.aanroepen = 0

            def find_duplicate_candidates(self, begrip: str) -> list[Any]:
                self.aanroepen += 1
                return []

        class _StubSupport:
            def severity_for(self, rule: dict[str, Any]) -> str:
                return "error"

            def severity_level_for(self, rule: dict[str, Any]) -> str:
                return "high"

            def build_suggestion(
                self, code, rule, text, ctx, *, reason, details=None
            ) -> str:
                return "suggestie"

        spion = _Spion()
        record = build_rule_records(get_toetsregel_manager().get_all_regels())["CON-01"]
        ctx = EvaluationContext(
            raw_text=TEKST,
            cleaned_text=TEKST,
            begrip=BEGRIP,
            metadata=dict(CONTEXT),
        )
        deps = EvaluationDeps(
            support=_StubSupport(),
            available_inputs=frozenset(RequiredInput),
            repository=spion,
            pattern_cache={},
        )

        ContextMetadataEvaluator().evaluate(record, ctx, deps)

        assert spion.aanroepen == 0, (
            "CON-01 bevraagt de repository nog steeds; de duplicaatcontrole "
            "hoort bij DUP_01"
        )

    @pytest.mark.asyncio
    async def test_zonder_repository_volgt_not_evaluated_geen_pass(self):
        res = await _valideer(None)
        assert res["rule_statuses"].get("DUP_01") == (
            ResultStatus.NOT_EVALUATED.value
        ), (
            "zonder repository kan de duplicaatcontrole niet draaien; dat is "
            f"geen geslaagde toets: {res['rule_statuses'].get('DUP_01')}"
        )


class TestVoorbeeldpaarbeleidVolgtDeWerkelijkheid:
    """Invariant 7: geen `normative` op een regel met een bekend defect."""

    @pytest.mark.parametrize("code", DEFECTE_VOORBEELDPAREN)
    def test_defecte_regel_claimt_geen_normatief_voorbeeldpaar(self, code: str):
        from toetsregels.runtime_contract import (
            ExamplePairPolicy,
            build_rule_records,
        )

        record = build_rule_records(get_toetsregel_manager().get_all_regels())[code]
        assert record.example_pair_policy is not ExamplePairPolicy.NORMATIVE, (
            f"{code} keurt zijn eigen goede voorbeeld af, maar het record "
            "presenteert het voorbeeldpaar als normatief"
        )

    @pytest.mark.parametrize("code", DEFECTE_VOORBEELDPAREN)
    def test_afwijking_draagt_een_reden_en_een_issue(self, code: str):
        from toetsregels.runtime_contract import build_rule_records

        record = build_rule_records(get_toetsregel_manager().get_all_regels())[code]
        assert record.example_pair_reason, f"{code} mist example_pair_reason"
        assert record.example_pair_issue, f"{code} mist example_pair_issue"


class TestUIVolgtDePrimaireUitkomst:
    """Invariant 8: nooit groen bij een niet-acceptabel resultaat."""

    @staticmethod
    def _render(resultaat: dict[str, Any]) -> MagicMock:
        from ui.components import validation_view

        with patch.object(validation_view, "st") as mock_st:
            mock_st.columns.return_value = (
                MagicMock(),
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )
            mock_st.button.return_value = False
            validation_view.render_validation_detailed_list(
                resultaat, key_prefix="def674", show_toggle=False
            )
        return mock_st

    def test_geen_groene_gate_bij_onacceptabel_resultaat(self):
        resultaat = {
            "overall_score": 0.81,
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
            "rule_statuses": {},
            "evaluation_coverage": {"error": 1},
            # Het gate-object zoals het vóór deze fix het resultaat verliet.
            "acceptance_gate": {"acceptable": True, "gates_passed": ["score"]},
        }
        mock_st = self._render(resultaat)

        groen = [
            str(c.args[0])
            for c in mock_st.success.call_args_list
            if c.args and "gates" in str(c.args[0]).lower()
        ]
        assert not groen, (
            "UI toont een groene gate terwijl het resultaat niet acceptabel is: "
            f"{groen}"
        )

    def test_wel_groen_bij_acceptabel_resultaat(self):
        """Tegenhanger: de melding mag niet altijd wegvallen."""
        resultaat = {
            "overall_score": 0.90,
            "is_acceptable": True,
            "violations": [],
            "passed_rules": [],
            "rule_statuses": {},
            "evaluation_coverage": {"error": 0},
            "acceptance_gate": {"acceptable": True, "gates_passed": ["score"]},
        }
        mock_st = self._render(resultaat)

        groen = [
            str(c.args[0])
            for c in mock_st.success.call_args_list
            if c.args and "gates" in str(c.args[0]).lower()
        ]
        assert groen, "een acceptabel resultaat hoort de gate wél groen te tonen"
