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
) -> DefinitieRecord:
    return DefinitieRecord(
        begrip="keurmerk",
        definitie=definitie,
        categorie=categorie,
        organisatorische_context=org,
        juridische_context=jur,
        wettelijke_basis=wet,
        status=status,
        # Synthetisch positieve overige gatecomponenten (DEF-630 blijft
        # eigenaar van de algemene score-/expertgate).
        validation_score=score,
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
            "decisions": {
                naam.id: {"function": functie, "reason": "Synthetische motivering."}
            },
        },
        updated_by=ACTOR,
    )
    assert ok


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
        self, tmp_path
    ):
        """Twee concurrerende pogingen zonder leidend record: precies één slaagt.

        De invariant wordt binnen `BEGIN IMMEDIATE` hercontroleerd, dus de
        uitkomst is onafhankelijk van de scheduling: wie de lock als tweede
        krijgt, ziet de gecommitte vaststelling van de eerste.
        """
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
        uitkomsten: dict[int, Any] = {}

        def _stel_vast(definitie_id: int) -> None:
            eigen_svc, _ = _service(tmp_path)
            uitkomsten[definitie_id] = eigen_svc.approve(
                definitie_id,
                ACTOR,
                user_role="reviewer",
                notes="",
                expected_version=versies[definitie_id],
            )

        threads = [
            threading.Thread(target=_stel_vast, args=(d,)) for d in (eerste, tweede)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        geslaagd = [d for d, u in uitkomsten.items() if u.success]
        assert len(geslaagd) == 1, {
            d: (u.success, u.error_message) for d, u in uitkomsten.items()
        }
        assert _vastgestelde(repo) == geslaagd
        mislukt = next(u for d, u in uitkomsten.items() if not u.success)
        assert mislukt.gate_status == "conflict", mislukt


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


def _rij_kolom(repo: DefinitionRepository, definitie_id: int, kolom: str) -> Any:
    conn = repo.legacy_repo._db.get_connection()
    return conn.execute(
        f"SELECT {kolom} FROM definities WHERE id = ?", (definitie_id,)
    ).fetchone()[0]
