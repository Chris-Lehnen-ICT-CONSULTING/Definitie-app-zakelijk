"""DEF-622 (B-03/B-07/B-10): vaststelconflict en verplichte CON-01-beoordeling.

Twee lagen, bewust onderscheiden van de per-recordgarantie van DEF-482
(`test_definition_workflow_atomiciteit.py` bewaakt dat status, metadata en
audit van één record samen committen):

* **Vaststelvoorwaarde CON-01 (B-07)** — in `DefinitionWorkflowService`:
  geen context, een open naamfunctie, een beoordeling die niet meer bij de
  tekst/context hoort, of registratiegebruik blokkeren de vaststelling. Dat
  is niet overrulebaar met een notitie. Het concept blijft opslaan/bewerken.
  De algemene expertbeoordelings-/scoregate blijft DEF-630; hier zijn de
  overige gatecomponenten daarom synthetisch positief (score aanwezig, geen
  kritieke issues).

* **Inter-recordconflict (B-03/B-10)** — maximaal één vastgesteld, leidend
  record per begrip + volledige genormaliseerde context, ongeacht categorie.
  Vervanging is een bewuste keuze en archiveert het eerdere record in
  dezelfde transactie als de nieuwe vaststelling; een auditfout rolt beide
  terug; gelijktijdige pogingen laten nooit twee leidende records over. De
  invariant zit op de persistentiegrens, zodat ook een generieke
  `update_definitie`/`create_definitie` hem niet kan omzeilen.

Alle databases zijn tijdelijk en synthetisch (tmp_path, offline-bootstrap).
"""

from __future__ import annotations

import json
import threading
from typing import Any

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieStatus,
    VaststelconflictError,
)
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.workflow_service import WorkflowService

pytestmark = [pytest.mark.unit]

ORG = '["Stichting Zilver"]'
JUR = '["privaatrecht"]'
WET = '["Regeling Z"]'
ACTOR = "synthetische-expert"


def _service(tmp_path, naam: str = "vaststel.db"):
    repo = DefinitionRepository(str(tmp_path / naam))
    svc = DefinitionWorkflowService(workflow_service=WorkflowService(), repository=repo)
    return svc, repo


def _record(
    *,
    definitie: str = "kwaliteitsmerk voor gecontroleerde producten",
    org: str = ORG,
    jur: str = JUR,
    wet: str = WET,
    categorie: str = "type",
    status: str = DefinitieStatus.REVIEW.value,
    score: float | None = 0.9,
    begrip: str = "keurmerk",
) -> DefinitieRecord:
    # DEF-743: een record zonder bronnen kan alleen worden vastgesteld met een
    # gedocumenteerde deskundige uitzondering "geen passende bron" (CON-02).
    # Die wordt hier als echte, gebonden marker gezaaid (geen versiebump), zodat
    # deze proeven de CON-01-vaststelvoorwaarde blijven isoleren.
    from domain.context.normalisatie import lees_contextwaarden
    from tests.fixtures.def743_fakes import geen_bron_uitzondering_marker

    marker = geen_bron_uitzondering_marker(
        begrip,
        definitie,
        {
            "organisatorische_context": lees_contextwaarden(org),
            "juridische_context": lees_contextwaarden(jur),
            "wettelijke_basis": lees_contextwaarden(wet),
        },
        actor=ACTOR,
    )
    return DefinitieRecord(
        begrip=begrip,
        definitie=definitie,
        categorie=categorie,
        organisatorische_context=org,
        juridische_context=jur,
        wettelijke_basis=wet,
        status=status,
        # Synthetisch positieve overige gatecomponenten (DEF-630 blijft
        # eigenaar van de algemene score-/expertgate).
        validation_score=score,
        validation_issues=json.dumps([marker], ensure_ascii=False),
    )


def _rij(repo: DefinitionRepository, definitie_id: int) -> dict[str, Any]:
    conn = repo.legacy_repo._db.get_connection()
    row = conn.execute(
        "SELECT id, status, version_number, definitie, approved_by FROM definities "
        "WHERE id = ?",
        (definitie_id,),
    ).fetchone()
    return dict(row)


def _vastgestelde(repo: DefinitionRepository) -> list[int]:
    conn = repo.legacy_repo._db.get_connection()
    return [
        r[0]
        for r in conn.execute(
            "SELECT id FROM definities WHERE begrip = 'keurmerk' "
            "AND status = 'established' ORDER BY id"
        )
    ]


def _audit(repo: DefinitionRepository, definitie_id: int) -> list[tuple[str, str]]:
    conn = repo.legacy_repo._db.get_connection()
    return [
        (r[0], r[1] or "")
        for r in conn.execute(
            "SELECT wijziging_type, wijziging_reden FROM definitie_geschiedenis "
            "WHERE definitie_id = ? AND wijziging_reden IS NOT NULL ORDER BY id",
            (definitie_id,),
        )
    ]


def _beoordeling(repo: DefinitionRepository, definitie_id: int, functie: str) -> None:
    """Leg de expertbeoordeling van het (enige) naamsignaal vast."""
    from domain.context.contract import beoordeel_context
    from domain.context.normalisatie import lees_contextwaarden

    record = repo.get_definitie(definitie_id)
    assert record is not None
    contexten = {
        "organisatorische_context": lees_contextwaarden(
            record.organisatorische_context
        ),
        "juridische_context": lees_contextwaarden(record.juridische_context),
        "wettelijke_basis": lees_contextwaarden(record.wettelijke_basis),
    }
    uitkomst = beoordeel_context(record.begrip, record.definitie, contexten)
    naam = next(p for p in uitkomst.parts if p.evidence)
    ok = repo.legacy_repo.set_context_review(
        definitie_id,
        {
            "fingerprint": uitkomst.fingerprint,
            "actor": ACTOR,
            # De beoordeelde recordversie hoort in de payload zelf (V2b);
            # expected_version is alleen de concurrency-guard.
            "version_number": record.version_number,
            "decisions": {
                naam.id: {"function": functie, "reason": "Synthetische motivering."}
            },
        },
        updated_by=ACTOR,
        # De versie die de beoordelaar vóór zich had (optimistic lock, V2a).
        expected_version=record.version_number,
    )
    assert ok


def _geen_bron_uitzondering(repo: DefinitionRepository, definitie_id: int) -> None:
    """Leg de gedocumenteerde uitzondering "geen passende bron" (opnieuw) vast
    via D, gebonden aan de actuele kandidaat (DEF-743). Versie +1."""
    from tests.fixtures.def743_fakes import geen_bron_uitzondering_marker

    record = repo.get_definitie(definitie_id)
    assert record is not None
    marker = geen_bron_uitzondering_marker(
        record.begrip,
        record.get_definitie_tekst(),
        record.get_contextlijsten(),
        actor=ACTOR,
        version_number=record.version_number,
    )
    assert repo.set_source_review(
        definitie_id,
        marker["source_review"],
        updated_by=ACTOR,
        expected_version=record.version_number,
    )


def _reviewversie(repo: DefinitionRepository, definitie_id: int) -> int | None:
    record = repo.get_definitie(definitie_id)
    assert record is not None
    review = record.get_context_review()
    return None if review is None else review.get("version_number")


def _versie(repo: DefinitionRepository, definitie_id: int) -> int:
    return int(_rij(repo, definitie_id)["version_number"])


# ---------------------------------------------------------------- B-07 gate


class TestCon01Vaststelvoorwaarde:
    def test_geen_context_blokkeert_ook_met_override(self, tmp_path):
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(org="[]", jur="[]", wet="[]"))

        uitkomst = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="override poging",
            expected_version=_versie(repo, did),
        )

        assert uitkomst.success is False
        assert uitkomst.gate_status == "blocked"
        assert any("context" in r.lower() for r in uitkomst.gate_reasons or [])
        assert _rij(repo, did)["status"] == DefinitieStatus.REVIEW.value

    def test_open_naamfunctie_blokkeert_maar_concept_blijft_bewerkbaar(self, tmp_path):
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk dat Stichting Zilver verleent")
        )

        uitkomst = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="x",
            expected_version=_versie(repo, did),
        )

        assert uitkomst.success is False
        assert uitkomst.gate_status == "blocked"
        redenen = " ".join(uitkomst.gate_reasons or []).lower()
        assert "nog te beoordelen" in redenen and "stichting zilver" in redenen
        # Het concept blijft: opslaan/bewerken kan gewoon door.
        assert repo.legacy_repo.update_definitie(did, {"toelichting_proces": "later"})
        assert _rij(repo, did)["status"] == DefinitieStatus.REVIEW.value

    def test_noodzakelijke_naam_laat_vaststelling_toe(self, tmp_path):
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk dat Stichting Zilver verleent")
        )
        _beoordeling(repo, did, "necessary")

        uitkomst = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, did),
        )

        assert uitkomst.success is True, uitkomst.error_message
        assert _rij(repo, did)["status"] == DefinitieStatus.ESTABLISHED.value
        # De beoordeling is aan actor en tekst gebonden en blijft leesbaar.
        review = repo.get_definitie(did).get_context_review()
        assert review["actor"] == ACTOR

    def test_registratiegebruik_blokkeert(self, tmp_path):
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk zoals gebruikt binnen Stichting Zilver")
        )
        _beoordeling(repo, did, "registration")

        uitkomst = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="x",
            expected_version=_versie(repo, did),
        )

        assert uitkomst.success is False and uitkomst.gate_status == "blocked"
        assert any("voldoet niet" in r.lower() for r in uitkomst.gate_reasons or [])

    def test_gewijzigde_tekst_maakt_beoordeling_ongeldig(self, tmp_path):
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk dat Stichting Zilver verleent")
        )
        _beoordeling(repo, did, "necessary")
        assert repo.legacy_repo.update_definitie(
            did, {"definitie": "kwaliteitsmerk dat Stichting Zilver verleent aan leden"}
        )

        uitkomst = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="x",
            expected_version=_versie(repo, did),
        )

        assert uitkomst.success is False and uitkomst.gate_status == "blocked"
        assert any(
            "nog te beoordelen" in r.lower() for r in uitkomst.gate_reasons or []
        )
        assert _rij(repo, did)["status"] == DefinitieStatus.REVIEW.value


# ------------------------------------------------------- B-03/B-10 conflict


class TestInterRecordConflict:
    def _leidend_en_kandidaat(self, tmp_path):
        svc, repo = _service(tmp_path)
        leidend = repo.legacy_repo.create_definitie(
            _record(
                definitie="oorspronkelijke definitie",
                status=DefinitieStatus.ESTABLISHED.value,
                categorie="type",
            )
        )
        # Andere categorie, zelfde begrip en volledige context: categorie is
        # géén ontsnapping aan de exclusiviteit (besluit 6).
        kandidaat = repo.legacy_repo.create_definitie(
            _record(definitie="nieuwe definitie", categorie="proces"),
            allow_duplicate=True,
            duplicate_reason="synthetische opvolger",
        )
        return svc, repo, leidend, kandidaat

    def test_tweede_vaststelling_vereist_bewuste_vervanging(self, tmp_path):
        svc, repo, leidend, kandidaat = self._leidend_en_kandidaat(tmp_path)

        uitkomst = svc.approve(
            kandidaat,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, kandidaat),
        )

        assert uitkomst.success is False
        assert uitkomst.gate_status == "conflict"
        assert any(str(leidend) in r for r in uitkomst.gate_reasons or [])
        assert _vastgestelde(repo) == [leidend]
        assert _rij(repo, kandidaat)["status"] == DefinitieStatus.REVIEW.value

    def test_bewuste_vervanging_archiveert_oud_en_stelt_nieuw_vast(self, tmp_path):
        svc, repo, leidend, kandidaat = self._leidend_en_kandidaat(tmp_path)

        uitkomst = svc.approve(
            kandidaat,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, kandidaat),
            vervang_definitie_id=leidend,
        )

        assert uitkomst.success is True, uitkomst.error_message
        assert _vastgestelde(repo) == [kandidaat]
        assert _rij(repo, leidend)["status"] == DefinitieStatus.ARCHIVED.value
        # Reguliere statusaudit blijft behouden, met verwijzing naar de opvolger.
        oud_audit = _audit(repo, leidend)
        assert any(
            soort == "status_changed" and str(kandidaat) in reden
            for soort, reden in oud_audit
        ), oud_audit
        assert any(soort == "status_changed" for soort, _ in _audit(repo, kandidaat))

    def test_vervanging_van_verkeerd_record_wordt_geweigerd(self, tmp_path):
        svc, repo, leidend, kandidaat = self._leidend_en_kandidaat(tmp_path)
        ander = repo.legacy_repo.create_definitie(
            DefinitieRecord(
                begrip="waarmerk",
                definitie="iets anders",
                categorie="type",
                organisatorische_context=ORG,
                status=DefinitieStatus.ESTABLISHED.value,
                validation_score=0.9,
            )
        )

        uitkomst = svc.approve(
            kandidaat,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, kandidaat),
            vervang_definitie_id=ander,
        )

        assert uitkomst.success is False and uitkomst.gate_status == "conflict"
        assert _vastgestelde(repo) == [leidend]
        assert _rij(repo, ander)["status"] == DefinitieStatus.ESTABLISHED.value

    def test_auditfout_rolt_vervanging_en_vaststelling_terug(
        self, tmp_path, monkeypatch
    ):
        svc, repo, leidend, kandidaat = self._leidend_en_kandidaat(tmp_path)
        audit = repo.legacy_repo._crud._audit
        origineel = audit.log_geschiedenis
        teller = {"n": 0}

        def _faalt_na_archivering(*args, **kwargs):
            teller["n"] += 1
            if teller["n"] >= 2:
                raise RuntimeError("synthetische auditstoring")
            return origineel(*args, **kwargs)

        monkeypatch.setattr(audit, "log_geschiedenis", _faalt_na_archivering)

        uitkomst = svc.approve(
            kandidaat,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, kandidaat),
            vervang_definitie_id=leidend,
        )

        assert uitkomst.success is False
        assert teller["n"] >= 2, "de storing is niet bereikt; de test bewijst niets"
        assert _vastgestelde(repo) == [leidend]
        assert _rij(repo, leidend)["status"] == DefinitieStatus.ESTABLISHED.value
        assert _rij(repo, kandidaat)["status"] == DefinitieStatus.REVIEW.value

    def test_gelijktijdige_vaststelpogingen_laten_een_leidend_record_over(
        self, tmp_path, monkeypatch
    ):
        """Twee concurrerende pogingen zonder leidend record: precies één slaagt.

        Overlap wordt afgedwongen met synchronisatie, niet met timing: thread
        A houdt zijn schrijftransactie (na de hercontrole ónder de lock) vast
        tot thread B aantoonbaar aan zijn eigen ``BEGIN IMMEDIATE`` is
        begonnen (trace-callback op B's connectie). B wacht dus werkelijk op
        A's lock, en ziet daarna A's gecommitte vaststelling bij zijn eigen
        hercontrole. Zonder de hercontrole/invariant onder de lock zouden
        beide slagen — dat is wat deze test onderscheidt (B-10).
        """
        from database.definitie_crud import DefinitieCrudRepository

        svc, repo = _service(tmp_path)
        eerste = repo.legacy_repo.create_definitie(
            _record(definitie="eerste kandidaat")
        )
        tweede = repo.legacy_repo.create_definitie(
            _record(definitie="tweede kandidaat", categorie="proces"),
            allow_duplicate=True,
            duplicate_reason="synthetische tweede kandidaat",
        )
        versies = {eerste: _versie(repo, eerste), tweede: _versie(repo, tweede)}
        uitkomsten: dict[str, Any] = {}
        fouten: list[str] = []
        a_in_transactie = threading.Event()
        b_begint = threading.Event()
        origineel = DefinitieCrudRepository.find_leidende_definitie

        def _hercontrole_met_wachttijd(self_crud, *args, **kwargs):
            resultaat = origineel(self_crud, *args, **kwargs)
            conn = self_crud._db.get_connection()
            if threading.current_thread().name == "A" and conn.in_transaction:
                # A zit nu ónder de schrijflock; laat B aantoonbaar wachten.
                a_in_transactie.set()
                if not b_begint.wait(10):
                    fouten.append("thread B begon niet aan BEGIN IMMEDIATE")
            return resultaat

        monkeypatch.setattr(
            DefinitieCrudRepository,
            "find_leidende_definitie",
            _hercontrole_met_wachttijd,
        )

        def _stel_vast(naam: str, definitie_id: int) -> None:
            eigen_svc, eigen_repo = _service(tmp_path)
            conn = eigen_repo.legacy_repo._db.get_connection()

            def traceer(statement: str) -> None:
                if naam == "B" and statement.strip().upper().startswith(
                    "BEGIN IMMEDIATE"
                ):
                    b_begint.set()

            conn.set_trace_callback(traceer)
            try:
                uitkomsten[naam] = eigen_svc.approve(
                    definitie_id,
                    ACTOR,
                    user_role="reviewer",
                    notes="",
                    expected_version=versies[definitie_id],
                )
            finally:
                conn.set_trace_callback(None)

        thread_a = threading.Thread(target=_stel_vast, args=("A", eerste), name="A")
        thread_b = threading.Thread(target=_stel_vast, args=("B", tweede), name="B")
        thread_a.start()
        assert a_in_transactie.wait(10), "A bereikte de hercontrole onder de lock niet"
        thread_b.start()
        thread_a.join(timeout=30)
        thread_b.join(timeout=30)

        assert not fouten, fouten
        assert not thread_a.is_alive() and not thread_b.is_alive()
        assert uitkomsten["A"].success is True, uitkomsten["A"].error_message
        assert uitkomsten["B"].success is False
        assert uitkomsten["B"].gate_status == "conflict", uitkomsten["B"]
        assert _vastgestelde(repo) == [eerste]

    def test_beoordelaar_is_de_handelende_gebruiker(self, tmp_path):
        """V3: de beoordeling draagt de actor die haar opslaat; een afwijkende
        beoordelaar in de payload wordt vóór mutatie geweigerd."""
        from domain.context.contract import beoordeel_context
        from domain.context.normalisatie import lees_contextwaarden

        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk dat Stichting Zilver verleent")
        )
        rec = repo.get_definitie(did)
        uitkomst = beoordeel_context(
            rec.begrip,
            rec.definitie,
            {
                "organisatorische_context": lees_contextwaarden(
                    rec.organisatorische_context
                ),
                "juridische_context": lees_contextwaarden(rec.juridische_context),
                "wettelijke_basis": lees_contextwaarden(rec.wettelijke_basis),
            },
        )
        naam = next(p for p in uitkomst.parts if p.evidence)
        versie_voor = _versie(repo, did)
        beoordeling = {
            "fingerprint": uitkomst.fingerprint,
            "actor": "expert-A",
            "version_number": versie_voor,
            "decisions": {naam.id: {"function": "necessary", "reason": "Uitgever."}},
        }

        with pytest.raises(ValueError, match="beoordelaar"):
            repo.set_context_review(
                did, beoordeling, updated_by="expert-B", expected_version=versie_voor
            )
        with pytest.raises(ValueError, match="handelende gebruiker"):
            repo.set_context_review(
                did, beoordeling, updated_by="", expected_version=versie_voor
            )
        for ongeldig in (True, 7, ["expert-A"]):
            with pytest.raises(ValueError, match="beoordelaar"):
                repo.set_context_review(
                    did,
                    {**beoordeling, "actor": ongeldig},
                    updated_by="expert-A",
                    expected_version=versie_voor,
                )
        # Niets gemuteerd: geen versiebump, geen beoordeling.
        assert _versie(repo, did) == versie_voor
        assert repo.get_definitie(did).get_context_review() is None

        # Consistent (of zonder actor): de handelende gebruiker wordt vastgelegd.
        zonder_actor = {k: v for k, v in beoordeling.items() if k != "actor"}
        assert repo.set_context_review(
            did, zonder_actor, updated_by="expert-A", expected_version=versie_voor
        )
        opgeslagen = repo.get_definitie(did).get_context_review()
        assert opgeslagen["actor"] == "expert-A"
        assert opgeslagen["version_number"] == _versie(repo, did)
        # De vaststeller mag een ander zijn (bestaand contract).
        uitkomst_b = svc.approve(
            did,
            "expert-B",
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, did),
        )
        assert uitkomst_b.success is True, uitkomst_b.error_message


# -------------------------------------------------- persistentiegrens (DB)


class TestPersistentiegrens:
    def test_generieke_statusupdate_kan_geen_tweede_leidend_record_maken(
        self, tmp_path
    ):
        _, repo = _service(tmp_path)
        leidend = repo.legacy_repo.create_definitie(
            _record(status=DefinitieStatus.ESTABLISHED.value)
        )
        concept = repo.legacy_repo.create_definitie(
            _record(definitie="ander", categorie="proces"),
            allow_duplicate=True,
            duplicate_reason="synthetisch",
        )
        with pytest.raises(VaststelconflictError):
            repo.legacy_repo.update_definitie(
                concept, {"status": DefinitieStatus.ESTABLISHED.value}
            )
        assert _vastgestelde(repo) == [leidend]

    def test_contextwijziging_van_vastgesteld_record_kan_niet_botsen(self, tmp_path):
        _, repo = _service(tmp_path)
        leidend = repo.legacy_repo.create_definitie(
            _record(status=DefinitieStatus.ESTABLISHED.value)
        )
        elders = repo.legacy_repo.create_definitie(
            _record(
                definitie="ander",
                org='["Stichting Goud"]',
                status=DefinitieStatus.ESTABLISHED.value,
            )
        )
        # Verplaatsen naar de context van het leidende record: geweigerd.
        with pytest.raises(VaststelconflictError):
            repo.legacy_repo.update_definitie(elders, {"organisatorische_context": ORG})
        # Ook via de schrijfwijze/volgorde-varianten van dezelfde context.
        with pytest.raises(VaststelconflictError):
            repo.legacy_repo.update_definitie(
                elders, {"organisatorische_context": '["stichting zilver"]'}
            )
        assert sorted(_vastgestelde(repo)) == sorted([leidend, elders])
        assert json.loads(_rij_kolom(repo, elders, "organisatorische_context")) == [
            "Stichting Goud"
        ]

    def test_create_met_status_vastgesteld_botst_op_leidend_record(self, tmp_path):
        _, repo = _service(tmp_path)
        leidend = repo.legacy_repo.create_definitie(
            _record(status=DefinitieStatus.ESTABLISHED.value)
        )
        with pytest.raises(VaststelconflictError):
            repo.legacy_repo.create_definitie(
                _record(
                    definitie="import",
                    categorie="proces",
                    status=DefinitieStatus.ESTABLISHED.value,
                ),
                allow_duplicate=True,
                duplicate_reason="synthetische import",
            )
        assert _vastgestelde(repo) == [leidend]

    def test_zelfde_record_opnieuw_opslaan_botst_niet_met_zichzelf(self, tmp_path):
        _, repo = _service(tmp_path)
        leidend = repo.legacy_repo.create_definitie(
            _record(status=DefinitieStatus.ESTABLISHED.value)
        )
        assert repo.legacy_repo.update_definitie(
            leidend, {"organisatorische_context": '["stichting zilver"]'}
        )
        assert _vastgestelde(repo) == [leidend]


class TestReviewbevindingenVaststelling:
    """Onafhankelijke reviewbevindingen E1–E3 op de eerste vaststelcommit."""

    def test_ander_begrip_met_synoniem_en_zelfde_context_is_geen_conflict(
        self, tmp_path
    ):
        """E1: de B-10-exclusiviteit geldt voor hetzelfde begrip; een ander
        begrip dat ons begrip als synoniem voert, is geen leidend record."""
        svc, repo = _service(tmp_path)
        ander = repo.legacy_repo.create_definitie(
            DefinitieRecord(
                begrip="waarmerk",
                definitie="ander begrip, zelfde context",
                categorie="type",
                organisatorische_context=ORG,
                juridische_context=JUR,
                wettelijke_basis=WET,
                status=DefinitieStatus.ESTABLISHED.value,
                validation_score=0.9,
            )
        )
        repo.legacy_repo._db.get_connection().execute(
            "INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, "
            "voorbeeld_tekst, actief) VALUES (?, 'synonyms', 'keurmerk', 1)",
            (ander,),
        )
        # De generatielookup ziet het synoniem wél als duplicaat (bestaande
        # functie); bewust ernaast aanmaken vraagt daar een reden.
        kandidaat = repo.legacy_repo.create_definitie(
            _record(),
            allow_duplicate=True,
            duplicate_reason="synthetisch synoniemgeval",
        )

        uitkomst = svc.approve(
            kandidaat,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, kandidaat),
        )

        assert uitkomst.success is True, uitkomst.error_message
        assert _rij(repo, ander)["status"] == DefinitieStatus.ESTABLISHED.value

    def test_teruggezette_tekst_herleeft_oude_beoordeling_niet(self, tmp_path):
        """E2: de beoordeling is aan de versie gebonden; tekst wijzigen en
        terugzetten levert dezelfde tekst maar een nieuwere versie op."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk dat Stichting Zilver verleent")
        )
        _beoordeling(repo, did, "necessary")
        assert repo.legacy_repo.update_definitie(
            did, {"definitie": "kwaliteitsmerk dat Stichting Zilver verleent (v2)"}
        )
        assert repo.legacy_repo.update_definitie(
            did, {"definitie": "kwaliteitsmerk dat Stichting Zilver verleent"}
        )

        uitkomst = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, did),
        )

        assert uitkomst.success is False and uitkomst.gate_status == "blocked"
        assert any(
            "nog te beoordelen" in r.lower() for r in uitkomst.gate_reasons or []
        )

    @pytest.mark.parametrize(
        "markers",
        [
            # Twee markers, tegenstrijdig: ambigu → geen beoordeling.
            [("necessary", True), ("registration", True)],
            [("registration", True), ("necessary", True)],
            # Eerste geldig, tweede misvormd: fail-closed.
            [("necessary", True), ("necessary", False)],
        ],
    )
    def test_dubbele_of_misvormde_beoordelingsmarkers_tellen_niet(
        self, tmp_path, markers
    ):
        """E3: meerdere of misvormde CON-01-REVIEW-markers zijn geen beoordeling."""
        from database.models import CONTEXT_REVIEW_CODE
        from domain.context.contract import beoordeel_context
        from domain.context.normalisatie import lees_contextwaarden

        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie="kwaliteitsmerk dat Stichting Zilver verleent")
        )
        rec = repo.get_definitie(did)
        uitkomst = beoordeel_context(
            rec.begrip,
            rec.definitie,
            {
                "organisatorische_context": lees_contextwaarden(
                    rec.organisatorische_context
                ),
                "juridische_context": lees_contextwaarden(rec.juridische_context),
                "wettelijke_basis": lees_contextwaarden(rec.wettelijke_basis),
            },
        )
        naam = next(p for p in uitkomst.parts if p.evidence)
        issues = []
        for functie, geldig in markers:
            review: Any = {
                "fingerprint": uitkomst.fingerprint,
                "actor": ACTOR,
                "version_number": rec.version_number + 1,
                "decisions": {naam.id: {"function": functie, "reason": "Synthetisch."}},
            }
            issues.append(
                {
                    "code": CONTEXT_REVIEW_CODE,
                    "rule_id": "CON-01",
                    "severity": "info",
                    "context_review": review if geldig else "misvormd",
                }
            )
        assert repo.legacy_repo.update_definitie(
            did, {"validation_issues": json.dumps(issues, ensure_ascii=False)}
        )

        assert repo.get_definitie(did).get_context_review() is None
        uitkomst_vaststelling = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, did),
        )
        assert uitkomst_vaststelling.success is False
        assert uitkomst_vaststelling.gate_status == "blocked"


def _rij_kolom(repo: DefinitionRepository, definitie_id: int, kolom: str) -> Any:
    conn = repo.legacy_repo._db.get_connection()
    return conn.execute(
        f"SELECT {kolom} FROM definities WHERE id = ?", (definitie_id,)
    ).fetchone()[0]


# -------------------------------------------- deltareview V2a-V2c (e9ecf6c09)


class TestReviewversiebinding:
    """De versiebinding van de beoordeling (deltareview V2a-V2c).

    De beoordeling bindt aan (vingerafdruk, recordversie). Drie lekken zijn
    gedicht: verouderde invoer die opnieuw geldig gestempeld werd (V2a), een
    ontbrekend of ongeldig reviewversienummer dat de controle uitschakelde
    (V2b) en de vaststelling die haar eigen geldige beoordeling door de
    statusversiebump meteen liet vervallen (V2c). Lokale CON-binding en
    readback; geen nieuwe DEF-630-gate-eis.
    """

    NAAMTEKST = "kwaliteitsmerk dat Stichting Zilver verleent"

    def test_verouderde_invoer_wordt_niet_opnieuw_geldig_gestempeld(self, tmp_path):
        """V2a: dezelfde oude beoordeling opnieuw aanbieden na wijzigen en
        terugzetten bindt niet aan de actuele versie; alleen actuele invoer
        op de actuele versie telt."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        _beoordeling(repo, did, "necessary")
        oud = repo.get_definitie(did).get_context_review()
        assert (oud["version_number"], _versie(repo, did)) == (2, 2)
        assert repo.legacy_repo.update_definitie(
            did, {"definitie": self.NAAMTEKST + " (v2)"}
        )
        assert repo.legacy_repo.update_definitie(did, {"definitie": self.NAAMTEKST})
        assert _versie(repo, did) == 4
        assert svc.preview_gate(did)["status"] == "blocked"

        # Oude payload op de actuele versie: verouderde invoer, geweigerd vóór
        # mutatie. Op haar eigen (oude) versie: stale write, niets geschreven.
        with pytest.raises(ValueError, match="versie"):
            repo.set_context_review(did, oud, updated_by=ACTOR, expected_version=4)
        assert (
            repo.set_context_review(did, oud, updated_by=ACTOR, expected_version=2)
            is False
        )
        actueel_payload = {**oud, "version_number": 4}
        for ongeldig in (None, True, "4", 4.0):
            with pytest.raises(ValueError, match="expected_version"):
                repo.set_context_review(
                    did,
                    actueel_payload,
                    updated_by=ACTOR,
                    expected_version=ongeldig,  # type: ignore[arg-type]
                )
        assert _versie(repo, did) == 4
        assert repo.get_definitie(did).get_context_review() == oud
        uitkomst = svc.approve(
            did, ACTOR, user_role="reviewer", notes="", expected_version=4
        )
        assert uitkomst.success is False and uitkomst.gate_status == "blocked"

        # DEF-743: ook de CON-02-uitzondering verviel door de tekstwijziging
        # (versiebinding; herleeft nooit). De deskundige legt haar opnieuw vast
        # vóór de CON-01-beoordeling (die neemt haar mee): versie 5.
        _geen_bron_uitzondering(repo, did)
        assert _versie(repo, did) == 5

        # Actuele invoer op de actuele versie bindt wél.
        _beoordeling(repo, did, "necessary")
        assert (_reviewversie(repo, did), _versie(repo, did)) == (6, 6)
        uitkomst = svc.approve(
            did, ACTOR, user_role="reviewer", notes="", expected_version=6
        )
        assert uitkomst.success is True, uitkomst.error_message

    @pytest.mark.parametrize(
        "versie",
        ["ontbreekt", None, True, [], {}, "invalid", 2.5],
        ids=["ontbreekt", "None", "True", "lijst", "dict", "tekst", "float"],
    )
    def test_ontbrekende_of_ongeldige_reviewversie_blokkeert(self, tmp_path, versie):
        """V2b: via de generieke update een verder geldige marker met een
        ontbrekend/ongeldig versienummer: het record heeft een versie, dus de
        beoordeling telt niet en de vaststelling blijft geblokkeerd."""
        from database.models import CONTEXT_REVIEW_CODE
        from domain.context.contract import beoordeel_context
        from domain.context.normalisatie import lees_contextwaarden

        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        rec = repo.get_definitie(did)
        uitkomst = beoordeel_context(
            rec.begrip,
            rec.definitie,
            {
                "organisatorische_context": lees_contextwaarden(
                    rec.organisatorische_context
                ),
                "juridische_context": lees_contextwaarden(rec.juridische_context),
                "wettelijke_basis": lees_contextwaarden(rec.wettelijke_basis),
            },
        )
        naam = next(p for p in uitkomst.parts if p.evidence)
        review: dict[str, Any] = {
            "fingerprint": uitkomst.fingerprint,
            "actor": ACTOR,
            "decisions": {naam.id: {"function": "necessary", "reason": "Uitgever."}},
        }
        if versie != "ontbreekt":
            review["version_number"] = versie
        marker = {
            "code": CONTEXT_REVIEW_CODE,
            "rule_id": "CON-01",
            "severity": "info",
            "context_review": review,
        }
        assert repo.legacy_repo.update_definitie(
            did, {"validation_issues": json.dumps([marker], ensure_ascii=False)}
        )
        assert repo.get_definitie(did).get_context_review() is not None

        gate = svc.preview_gate(did)
        assert gate["status"] == "blocked"
        assert any("versie" in r for r in gate["reasons"]), gate
        vaststelling = svc.approve(
            did,
            ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=_versie(repo, did),
        )
        assert vaststelling.success is False
        assert vaststelling.gate_status == "blocked"
        assert _rij(repo, did)["status"] == DefinitieStatus.REVIEW.value

    def test_vaststelling_behoudt_de_eigen_geldige_beoordeling(self, tmp_path):
        """V2c: de statusversiebump van de vaststelling neemt de beoordeling
        atomair mee; readback toont een vastgesteld record waarvan de
        CON-01-binding nog klopt (legitieme keten review -> opslaan ->
        vaststellen -> readback)."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        _beoordeling(repo, did, "necessary")
        assert (_reviewversie(repo, did), _versie(repo, did)) == (2, 2)
        assert svc.preview_gate(did)["status"] == "pass"

        uitkomst = svc.approve(
            did, ACTOR, user_role="reviewer", notes="", expected_version=2
        )
        assert uitkomst.success is True, uitkomst.error_message

        rij = _rij(repo, did)
        assert rij["status"] == DefinitieStatus.ESTABLISHED.value
        assert rij["version_number"] == 3
        assert _reviewversie(repo, did) == 3
        assert svc.preview_gate(did)["status"] == "pass"
        # Readback via de servicelaag: dezelfde, nog geldige binding.
        definition = repo.get(did)
        assert definition is not None
        assert definition.metadata["version_number"] == 3
        assert definition.metadata["context_review"]["version_number"] == 3
        # De statusaudit blijft één reguliere regel.
        soorten = [s for s, _ in _audit(repo, did)]
        assert soorten.count("status_changed") == 1

    @pytest.mark.parametrize(
        "update",
        [
            {"validation_score": 0.95},
            {"toelichting_proces": "synthetisch"},
            {"categorie": "proces"},
            {"ufo_categorie": "Kind"},
            {"status": DefinitieStatus.DRAFT.value},
            {"definitie": "kwaliteitsmerk dat Stichting Zilver verleent"},
        ],
        ids=[
            "score",
            "toelichting_proces",
            "categorie",
            "ufo",
            "status_draft",
            "tekst",
        ],
    )
    def test_generieke_update_laat_de_beoordeling_vervallen(self, tmp_path, update):
        """V2c (tweede deltareview): behoud is begrensd tot de toegestane
        atomaire statusactie (vaststelling). Elke generieke recordwijziging —
        ook zonder tekstwijziging — maakt de versiegebonden beoordeling
        ongeldig; er is geen automatische verlengingsregel."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        _beoordeling(repo, did, "necessary")
        assert (_reviewversie(repo, did), _versie(repo, did)) == (2, 2)

        assert repo.legacy_repo.update_definitie(did, dict(update))
        assert (_reviewversie(repo, did), _versie(repo, did)) == (2, 3)
        gate = svc.preview_gate(did)
        assert gate["status"] == "blocked"
        assert any("versie" in r for r in gate["reasons"]), gate

    def test_behoud_geldt_alleen_voor_de_vaststelling(self, tmp_path):
        """Alleen `change_status(..., ESTABLISHED)` — de atomaire vaststel-
        actie — neemt een geldig gebonden beoordeling mee; een generieke
        statuswijziging via dezelfde persistentielaag doet dat niet."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        _beoordeling(repo, did, "necessary")

        # Generieke statusactie naar draft: geen behoud.
        assert repo.legacy_repo.change_status(did, DefinitieStatus.DRAFT, ACTOR)
        assert (_reviewversie(repo, did), _versie(repo, did)) == (2, 3)
        assert svc.preview_gate(did)["status"] == "blocked"

        # Opnieuw beoordelen op de actuele versie en vaststellen: behoud.
        _beoordeling(repo, did, "necessary")
        assert (_reviewversie(repo, did), _versie(repo, did)) == (4, 4)
        assert repo.legacy_repo.change_status(
            did, DefinitieStatus.REVIEW, ACTOR
        )  # generiek: geen behoud
        assert (_reviewversie(repo, did), _versie(repo, did)) == (4, 5)
        _beoordeling(repo, did, "necessary")
        uitkomst = svc.approve(
            did, ACTOR, user_role="reviewer", notes="", expected_version=6
        )
        assert uitkomst.success is True, uitkomst.error_message
        assert (_reviewversie(repo, did), _versie(repo, did)) == (7, 7)

    @pytest.mark.parametrize(
        "payloadversie", [True, 1.0, "1"], ids=["bool", "float", "tekst"]
    )
    def test_payloadversie_met_ongeldig_type_wordt_geweigerd(
        self, tmp_path, payloadversie
    ):
        """V2b (tweede deltareview): numerieke gelijkheid volstaat niet —
        `True`/`1.0` bij expected_version=1 zijn geen geldige versie en
        worden vóór mutatie geweigerd."""
        from domain.context.contract import beoordeel_context

        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        rec = repo.get_definitie(did)
        uitkomst = beoordeel_context(
            rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
        )
        naam = next(p for p in uitkomst.parts if p.evidence)
        payload = {
            "fingerprint": uitkomst.fingerprint,
            "actor": ACTOR,
            "version_number": payloadversie,
            "decisions": {naam.id: {"function": "necessary", "reason": "Uitgever."}},
        }
        with pytest.raises(ValueError, match="versie"):
            repo.set_context_review(did, payload, updated_by=ACTOR, expected_version=1)
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_context_review() is None
        assert svc.preview_gate(did)["status"] == "blocked"

    def test_ongeldig_versietype_wordt_bij_vaststelling_niet_geldig_gestempeld(
        self, tmp_path
    ):
        """V2b: een bewaarde marker met reviewversie `2.0` op recordversie 2
        is geen geldige binding; de vaststelactie op de persistentielaag mag
        haar niet als integer 3 overnemen."""
        from database.models import CONTEXT_REVIEW_CODE
        from domain.context.contract import beoordeel_context

        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        rec = repo.get_definitie(did)
        uitkomst = beoordeel_context(
            rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
        )
        naam = next(p for p in uitkomst.parts if p.evidence)
        marker = {
            "code": CONTEXT_REVIEW_CODE,
            "rule_id": "CON-01",
            "severity": "info",
            "context_review": {
                "fingerprint": uitkomst.fingerprint,
                "actor": ACTOR,
                "version_number": 2.0,
                "decisions": {naam.id: {"function": "necessary", "reason": "Uitg."}},
            },
        }
        # Marker 2.0 komt op recordversie 2 te staan: numeriek "gelijk".
        assert repo.legacy_repo.update_definitie(
            did, {"validation_issues": json.dumps([marker], ensure_ascii=False)}
        )
        assert _versie(repo, did) == 2
        assert svc.preview_gate(did)["status"] == "blocked"

        # Generieke wijziging: de marker mag niet als integer 3 herleven.
        assert repo.legacy_repo.update_definitie(
            did, {"toelichting_proces": "synthetisch"}
        )
        assert _versie(repo, did) == 3
        assert repo.get_definitie(did).get_context_review()["version_number"] == 2.0
        assert svc.preview_gate(did)["status"] == "blocked"

        # Rechtstreeks op de persistentielaag vaststellen (zonder gate), met
        # marker 3.0 op recordversie 3: ook de vaststelactie neemt een
        # verkeerd getypeerde versie niet als integer mee.
        marker["context_review"]["version_number"] = 4.0
        assert repo.legacy_repo.update_definitie(
            did, {"validation_issues": json.dumps([marker], ensure_ascii=False)}
        )
        assert _versie(repo, did) == 4
        assert repo.legacy_repo.change_status(did, DefinitieStatus.ESTABLISHED, ACTOR)
        assert _versie(repo, did) == 5
        assert repo.get_definitie(did).get_context_review()["version_number"] == 4.0
        assert svc.preview_gate(did)["status"] == "blocked"

    # ------------------------------------------ V2b, vierde ronde (mandaat)

    def _payload(self, repo: DefinitionRepository, did: int) -> dict[str, Any]:
        from domain.context.contract import beoordeel_context

        rec = repo.get_definitie(did)
        uitkomst = beoordeel_context(
            rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
        )
        naam = next(p for p in uitkomst.parts if p.evidence)
        return {
            "fingerprint": uitkomst.fingerprint,
            "actor": ACTOR,
            "decisions": {naam.id: {"function": "necessary", "reason": "Uitgever."}},
        }

    @pytest.mark.parametrize("variant", ["ontbreekt", "None"])
    def test_payload_zonder_versienummer_wordt_geweigerd(self, tmp_path, variant):
        """V2b (a): de payload draagt zelf de beoordeelde versie; ontbreekt
        die (of is hij null), dan is dat geen actuele invoer — ook niet met een
        kloppende expected_version, die alleen de concurrency-guard is."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        payload = self._payload(repo, did)
        if variant == "None":
            payload["version_number"] = None

        with pytest.raises(ValueError, match="versienummer"):
            repo.set_context_review(did, payload, updated_by=ACTOR, expected_version=1)
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_context_review() is None
        assert svc.preview_gate(did)["status"] == "blocked"

        # Dezelfde invoer mét de beoordeelde versie bindt wél: opslaan →
        # readback → vaststelling door een ander → readback gebonden.
        assert repo.set_context_review(
            did, {**payload, "version_number": 1}, updated_by=ACTOR, expected_version=1
        )
        assert (_reviewversie(repo, did), _versie(repo, did)) == (2, 2)
        uitkomst = svc.approve(
            did, "expert-B", user_role="reviewer", notes="", expected_version=2
        )
        assert uitkomst.success is True, uitkomst.error_message
        assert (_reviewversie(repo, did), _versie(repo, did)) == (3, 3)
        assert svc.preview_gate(did)["status"] == "pass"

    def test_payloadversie_ongelijk_aan_beoordeelde_versie_wordt_geweigerd(
        self, tmp_path
    ):
        """V2b: payloadversie en expected_version moeten dezelfde beoordeelde
        versie zijn; een afwijkende payloadversie is verouderde invoer."""
        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        assert repo.legacy_repo.update_definitie(did, {"validation_score": 0.95})
        payload = {**self._payload(repo, did), "version_number": 1}
        with pytest.raises(ValueError, match="versie"):
            repo.set_context_review(did, payload, updated_by=ACTOR, expected_version=2)
        assert _versie(repo, did) == 2
        assert repo.get_definitie(did).get_context_review() is None
        assert svc.preview_gate(did)["status"] == "blocked"

    def test_opgeslagen_tekstversie_telt_niet_bij_gate_noch_bij_vaststelling(
        self, tmp_path
    ):
        """V2b (b): één strikte integerconventie voor invoer, gate en carry.
        Een bewaarde marker met tekstversie "2" op recordversie 2 passeert de
        gate niet en wordt bij vaststelling niet als integer meegenomen."""
        from database.models import CONTEXT_REVIEW_CODE

        svc, repo = _service(tmp_path)
        did = repo.legacy_repo.create_definitie(_record(definitie=self.NAAMTEKST))
        marker = {
            "code": CONTEXT_REVIEW_CODE,
            "rule_id": "CON-01",
            "severity": "info",
            "context_review": {**self._payload(repo, did), "version_number": "2"},
        }
        assert repo.legacy_repo.update_definitie(
            did, {"validation_issues": json.dumps([marker], ensure_ascii=False)}
        )
        assert _versie(repo, did) == 2
        assert repo.get_definitie(did).get_context_review()["version_number"] == "2"

        gate = svc.preview_gate(did)
        assert gate["status"] == "blocked"
        assert any("versie" in r for r in gate["reasons"]), gate
        vaststelling = svc.approve(
            did, ACTOR, user_role="reviewer", notes="", expected_version=2
        )
        assert vaststelling.success is False and vaststelling.gate_status == "blocked"

        # Rechtstreeks op de persistentielaag (zonder gate): geen herstempeling.
        assert repo.legacy_repo.change_status(did, DefinitieStatus.ESTABLISHED, ACTOR)
        assert _versie(repo, did) == 3
        assert repo.get_definitie(did).get_context_review()["version_number"] == "2"
        assert svc.preview_gate(did)["status"] == "blocked"
