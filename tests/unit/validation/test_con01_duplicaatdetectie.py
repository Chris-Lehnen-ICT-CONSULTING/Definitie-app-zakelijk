"""CON-01 duplicaatdetectie werkt op de échte productiebedrading (DEF-672).

De controle was op twee manieren onbereikbaar:

1. Zij duckte op `_get_all_definitions`, een privémethode die in DEF-176 als
   dode code is verwijderd. De geïnjecteerde `DefinitionRepository` heeft haar
   niet, dus de capability-guard nam élke productie-aanroep en de functie
   returnde stil — waarna CON-01 een gemeten `pass` meldde.
2. Ook mét die methode matchte de vergelijking nooit: de contextvelden van een
   `DefinitieRecord` zijn JSON-strings, en die werden per teken gesplitst
   (`'["DJI"]'` → `['"', '[', ']', 'd', 'i', 'j']`).

Nu is er een expliciete publieke capability op de repository-interface, en de
vergelijking loopt over de gedeelde contextnormalisatie. De databasequery
begrenst eerst op actieve kandidaten voor het begrip; de genormaliseerde
gestructureerde context beslist daarna. Geen `get_all()`, geen volledige
tabelscan, geen schemawijziging, geen datamigratie.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from domain.context.normalisatie import contextsleutel
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition, DuplicateCandidate
from services.null_repository import NullDefinitionRepository
from services.validation.evaluators.context_metadata import (
    DUPLICATE_LOOKUP_METHODE,
    DUPLICATE_STASH_KEY,
)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager
from toetsregels.runtime_contract import ResultStatus

pytestmark = [pytest.mark.unit]

BEGRIP = "besluit"
DEFINITIETEKST = "besluit: een schriftelijke beslissing van een bestuursorgaan"
ORG = ["DJI", "OM"]
JUR = ["strafrecht"]
WET = ["Awb"]


# --------------------------------------------------------------------------
# Fixtures: een echte SQLite-database met een echte DefinitionRepository
# --------------------------------------------------------------------------


@pytest.fixture
def db_pad(tmp_path: Path) -> str:
    """Verse database met het echte schema."""
    pad = tmp_path / "definities.db"
    DefinitieRepository(str(pad))  # initialiseert het schema
    return str(pad)


@pytest.fixture
def repo(db_pad: str) -> DefinitionRepository:
    """De échte productie-repository, niet een stub."""
    return DefinitionRepository(db_path=db_pad)


def _zet_record(
    db_pad: str,
    *,
    begrip: str = BEGRIP,
    organisatorische_context: str,
    juridische_context: str,
    wettelijke_basis: str,
    status: str = "draft",
    categorie: str = "type",
) -> int:
    """Schrijf een record rechtstreeks weg, mét de rúwe opgeslagen vorm.

    Rechtstreeks en niet via `save()`, zodat een test bestaande, níet-canoniek
    opgeslagen data kan nabootsen: ongesorteerd, met hoofdletters en whitespace
    zoals die vóór deze wijziging in de database is beland.
    """
    with sqlite3.connect(db_pad) as conn:
        cursor = conn.execute(
            """
            INSERT INTO definities
                (begrip, definitie, categorie, organisatorische_context,
                 juridische_context, wettelijke_basis, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                begrip,
                DEFINITIETEKST,
                categorie,
                organisatorische_context,
                juridische_context,
                wettelijke_basis,
                status,
            ),
        )
        return int(cursor.lastrowid or 0)


def _zet_canoniek(db_pad: str, **overrides: Any) -> int:
    velden: dict[str, Any] = {
        "organisatorische_context": json.dumps(ORG),
        "juridische_context": json.dumps(JUR),
        "wettelijke_basis": json.dumps(WET),
    }
    velden.update(overrides)
    return _zet_record(db_pad, **velden)


# --------------------------------------------------------------------------
# De capability op de interface
# --------------------------------------------------------------------------


class TestPublickeCapability:
    def test_interface_declareert_de_capability(self):
        from services.interfaces import DefinitionRepositoryInterface

        assert hasattr(DefinitionRepositoryInterface, "find_duplicate_candidates")
        assert (
            "find_duplicate_candidates"
            in DefinitionRepositoryInterface.__abstractmethods__
        ), "de capability moet afgedwongen zijn, niet optioneel"

    def test_echte_repository_implementeert_haar(self, repo):
        assert callable(repo.find_duplicate_candidates)

    def test_null_repository_implementeert_haar(self):
        # Zonder implementatie zou NullDefinitionRepository niet meer
        # instantieerbaar zijn (abstracte methode) en zou elke test die hem
        # gebruikt omvallen.
        assert NullDefinitionRepository().find_duplicate_candidates(BEGRIP) == []

    def test_geen_privemethode_meer_nodig(self, repo):
        # De aanleiding van DEF-672: de guard duckte op een privémethode die de
        # productie-repository niet heeft.
        assert DUPLICATE_LOOKUP_METHODE == "find_duplicate_candidates"
        assert hasattr(repo, DUPLICATE_LOOKUP_METHODE)
        assert not hasattr(repo, "_get_all_definitions")

    def test_evaluator_verwijst_niet_meer_naar_de_privemethode(self):
        bron = Path("src/services/validation/evaluators/context_metadata.py").read_text(
            encoding="utf-8"
        )
        assert (
            "_get_all_definitions" not in bron
        ), "de evaluator verwijst nog naar de verwijderde privémethode"

    def test_capability_gebruikt_geen_volledige_tabelscan(self):
        from database.definitie_duplicates import KANDIDATEN_QUERY

        genormaliseerd = " ".join(KANDIDATEN_QUERY.split()).lower()
        assert "where" in genormaliseerd, KANDIDATEN_QUERY
        assert "begrip" in genormaliseerd, "query begrenst niet op begrip"
        assert "status" in genormaliseerd, "query filtert niet op status"
        assert "limit" in genormaliseerd, "query heeft geen bovengrens"

    def test_repository_roept_get_all_niet_aan(self, repo, monkeypatch):
        def _verboden(*args: Any, **kwargs: Any):
            raise AssertionError("get_all() is een volledige tabelscan (DEF-176)")

        monkeypatch.setattr(type(repo.legacy_repo), "get_all", _verboden)
        assert repo.find_duplicate_candidates(BEGRIP) == []


# --------------------------------------------------------------------------
# De begrensde query en de genormaliseerde vergelijking
# --------------------------------------------------------------------------


class TestKandidatenSelectie:
    def test_vindt_de_kandidaat_voor_dit_begrip(self, repo, db_pad):
        gezet = _zet_canoniek(db_pad)
        kandidaten = repo.find_duplicate_candidates(BEGRIP)
        assert [k.id for k in kandidaten] == [gezet]

    def test_ander_begrip_levert_geen_kandidaat(self, repo, db_pad):
        _zet_canoniek(db_pad, begrip="vergunning")
        assert repo.find_duplicate_candidates(BEGRIP) == []

    def test_begrip_is_hoofdletter_en_whitespace_onafhankelijk(self, repo, db_pad):
        gezet = _zet_canoniek(db_pad, begrip="Besluit")
        kandidaten = repo.find_duplicate_candidates("  besluit ")
        assert [k.id for k in kandidaten] == [gezet]

    def test_alleen_actieve_kandidaten(self, repo, db_pad):
        actief = _zet_canoniek(db_pad, status="draft")
        _zet_canoniek(db_pad, status="archived")
        kandidaten = repo.find_duplicate_candidates(BEGRIP)
        assert [k.id for k in kandidaten] == [
            actief
        ], "een gearchiveerde definitie is geen duplicaat-kandidaat"

    def test_kandidaat_draagt_de_genormaliseerde_sleutels(self, repo, db_pad):
        # Bestaand, niet-canoniek opgeslagen record: ongesorteerd, hoofdletters
        # en whitespace door elkaar. Normalisatie bij het lézen maakt een
        # datamigratie onnodig.
        _zet_record(
            db_pad,
            organisatorische_context=json.dumps(["  om ", "DJI", "dji"]),
            juridische_context=json.dumps(["Strafrecht"]),
            wettelijke_basis=json.dumps(["awb", ""]),
        )
        kandidaat = repo.find_duplicate_candidates(BEGRIP)[0]
        assert kandidaat.organisatorische_context == contextsleutel(ORG)
        assert kandidaat.juridische_context == contextsleutel(JUR)
        assert kandidaat.wettelijke_basis == contextsleutel(WET)

    def test_kandidaat_draagt_id_status_en_categorie(self, repo, db_pad):
        gezet = _zet_canoniek(db_pad, status="review", categorie="proces")
        kandidaat = repo.find_duplicate_candidates(BEGRIP)[0]
        assert isinstance(kandidaat, DuplicateCandidate)
        assert kandidaat.id == gezet
        assert kandidaat.status == "review"
        assert kandidaat.categorie == "proces"

    def test_lege_database_levert_lege_lijst(self, repo):
        assert repo.find_duplicate_candidates(BEGRIP) == []

    @pytest.mark.parametrize("leeg", ["", "   "])
    def test_leeg_begrip_zoekt_niet(self, repo, db_pad, leeg):
        _zet_canoniek(db_pad)
        assert repo.find_duplicate_candidates(leeg) == []


# --------------------------------------------------------------------------
# Canonieke opslag via dezelfde normalisatie
# --------------------------------------------------------------------------


class TestOpslagIsCanoniek:
    def test_save_slaat_context_canoniek_op(self, repo, db_pad):
        definitie_id = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=DEFINITIETEKST,
                organisatorische_context=["  OM ", "DJI", "DJI", ""],
                juridische_context=["strafrecht"],
                wettelijke_basis=["Awb"],
                categorie="type",
            )
        )
        assert definitie_id
        with sqlite3.connect(db_pad) as conn:
            rij = conn.execute(
                "SELECT organisatorische_context FROM definities WHERE id = ?",
                (definitie_id,),
            ).fetchone()
        assert json.loads(rij[0]) == [
            "DJI",
            "OM",
        ], "opslag is niet getrimd, ontdubbeld en gesorteerd"

    def test_opslag_behoudt_de_schrijfwijze(self, repo, db_pad):
        # Casefolden bij opslag zou "DJI" als "dji" in de UI zetten. De
        # herkenning van niet-canonieke data komt van normalisatie bij het
        # lezen, niet van de vorm op disk.
        definitie_id = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=DEFINITIETEKST,
                organisatorische_context=["DJI"],
                juridische_context=["Strafrecht"],
                categorie="type",
            )
        )
        with sqlite3.connect(db_pad) as conn:
            rij = conn.execute(
                "SELECT organisatorische_context, juridische_context "
                "FROM definities WHERE id = ?",
                (definitie_id,),
            ).fetchone()
        assert json.loads(rij[0]) == ["DJI"]
        assert json.loads(rij[1]) == ["Strafrecht"]

    def test_opgeslagen_definitie_bevat_geen_context(self, repo, db_pad):
        repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=DEFINITIETEKST,
                organisatorische_context=ORG,
                juridische_context=JUR,
                wettelijke_basis=WET,
                categorie="type",
            )
        )
        with sqlite3.connect(db_pad) as conn:
            tekst = conn.execute(
                "SELECT definitie FROM definities WHERE begrip = ?", (BEGRIP,)
            ).fetchone()[0]
        for waarde in (*ORG, *JUR, *WET):
            assert (
                waarde not in tekst
            ), f"contextwaarde {waarde!r} is in de definitietekst beland"

    def test_canonieke_opslag_is_vindbaar_als_duplicaat(self, repo):
        repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=DEFINITIETEKST,
                organisatorische_context=["OM", "DJI"],
                juridische_context=JUR,
                wettelijke_basis=WET,
                categorie="type",
            )
        )
        kandidaat = repo.find_duplicate_candidates(BEGRIP)[0]
        assert kandidaat.organisatorische_context == contextsleutel(ORG)


# --------------------------------------------------------------------------
# End-to-end via de validatieservice
# --------------------------------------------------------------------------


def _context(org=ORG, jur=JUR, wet=WET) -> dict[str, Any]:
    return {
        "organisatorische_context": list(org),
        "juridische_context": list(jur),
        "wettelijke_basis": list(wet),
    }


async def _valideer(repo: Any, context: dict[str, Any], begrip: str = BEGRIP) -> dict:
    svc = ModularValidationService(
        get_toetsregel_manager(), None, None, repository=repo
    )
    return await svc.validate_definition(
        begrip=begrip,
        text=DEFINITIETEKST,
        ontologische_categorie=None,
        context=context,
    )


def _duplicaatmeldingen(res: dict) -> list[dict]:
    return [v for v in res.get("violations", []) if v.get("code") == "CON-01"]


class TestDuplicaatsignaalEndToEnd:
    @pytest.mark.asyncio
    async def test_identieke_context_levert_een_duplicaatmelding(self, repo, db_pad):
        gezet = _zet_canoniek(db_pad)
        res = await _valideer(repo, _context())
        meldingen = _duplicaatmeldingen(res)
        assert meldingen, res.get("violations")
        assert meldingen[0]["metadata"]["existing_definition_id"] == gezet

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("naam", "org"),
        [
            ("andere volgorde", ["OM", "DJI"]),
            ("hoofdletters", ["dji", "om"]),
            ("whitespace", ["  DJI ", "\tOM"]),
            ("duplicaten", ["DJI", "DJI", "OM", "om"]),
        ],
    )
    async def test_dezelfde_context_anders_geschreven(self, repo, db_pad, naam, org):
        _zet_canoniek(db_pad)
        res = await _valideer(repo, _context(org=org))
        assert _duplicaatmeldingen(res), f"{naam}: duplicaat niet herkend"

    @pytest.mark.asyncio
    async def test_bestaand_niet_canoniek_record_wordt_herkend(self, repo, db_pad):
        # De data zoals zij vóór deze wijziging in de database beland kan zijn.
        _zet_record(
            db_pad,
            organisatorische_context=json.dumps(["  om ", "DJI", "dji"]),
            juridische_context=json.dumps(["Strafrecht"]),
            wettelijke_basis=json.dumps(["awb"]),
        )
        res = await _valideer(repo, _context())
        assert _duplicaatmeldingen(
            res
        ), "geen datamigratie, dus lezen moet normaliseren"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("veld", "afwijkend"),
        [
            ("organisatorische_context", ["KMAR"]),
            ("juridische_context", ["bestuursrecht"]),
            ("wettelijke_basis", ["Sv"]),
        ],
    )
    async def test_afwijkend_contextveld_is_geen_duplicaat(
        self, repo, db_pad, veld, afwijkend
    ):
        # Alle drie de velden doen mee aan de identiteit; wijkt er één af, dan
        # is het geen duplicaat.
        _zet_canoniek(db_pad)
        context = _context()
        context[veld] = afwijkend
        res = await _valideer(repo, context)
        assert not _duplicaatmeldingen(res), f"{veld} week af maar gold als duplicaat"

    @pytest.mark.asyncio
    async def test_deelverzameling_is_geen_duplicaat(self, repo, db_pad):
        _zet_canoniek(db_pad)
        res = await _valideer(repo, _context(org=["DJI"]))
        assert not _duplicaatmeldingen(res)

    @pytest.mark.asyncio
    async def test_ander_begrip_is_geen_duplicaat(self, repo, db_pad):
        _zet_canoniek(db_pad, begrip="vergunning")
        res = await _valideer(repo, _context())
        assert not _duplicaatmeldingen(res)

    @pytest.mark.asyncio
    async def test_gearchiveerde_definitie_is_geen_duplicaat(self, repo, db_pad):
        _zet_canoniek(db_pad, status="archived")
        res = await _valideer(repo, _context())
        assert not _duplicaatmeldingen(res)

    @pytest.mark.asyncio
    async def test_lege_database_levert_geen_duplicaat(self, repo):
        res = await _valideer(repo, _context())
        assert not _duplicaatmeldingen(res)


class TestBestaandeSemantiekBlijft:
    """Buiten deze slice verandert er niets (afbakening punt 5)."""

    @pytest.mark.asyncio
    async def test_force_duplicate_maakt_de_melding_een_error(self, repo, db_pad):
        _zet_canoniek(db_pad)
        context = _context()
        context["force_duplicate"] = True
        res = await _valideer(repo, context)
        melding = _duplicaatmeldingen(res)[0]
        assert melding["severity"] == "error"
        assert melding["severity_level"] == "high"

    @pytest.mark.asyncio
    async def test_zonder_force_duplicate_blijft_het_een_warning(self, repo, db_pad):
        _zet_canoniek(db_pad)
        melding = _duplicaatmeldingen(await _valideer(repo, _context()))[0]
        assert melding["severity"] == "warning"
        assert melding["severity_level"] == "medium"

    @pytest.mark.asyncio
    async def test_afwijkende_categorie_is_geen_duplicaat(self, repo, db_pad):
        # Bestaande categoriesemantiek: alleen filteren als beide een categorie
        # hebben en die verschillen.
        _zet_canoniek(db_pad, categorie="proces")
        context = _context()
        context["categorie"] = "type"
        res = await _valideer(repo, context)
        assert not _duplicaatmeldingen(res)

    @pytest.mark.asyncio
    async def test_con01_blijft_een_gemeten_regel(self, repo, db_pad):
        # De 36/12/5-classificatie mag niet schuiven: CON-01 blijft pass/fail.
        _zet_canoniek(db_pad)
        res = await _valideer(repo, _context())
        assert res["rule_statuses"]["CON-01"] in (
            ResultStatus.PASS.value,
            ResultStatus.FAIL.value,
        ), res["rule_statuses"]

    @pytest.mark.asyncio
    async def test_geen_context_zoekt_niet(self, repo, db_pad):
        # Bestaand gedrag: zonder enige context is er niets te vergelijken.
        _zet_canoniek(db_pad)
        res = await _valideer(repo, {})
        assert not _duplicaatmeldingen(res)


class TestRepositoryfoutBlijftFailClosed:
    class _Kapot(NullDefinitionRepository):
        def find_duplicate_candidates(self, begrip: str) -> list[DuplicateCandidate]:
            raise RuntimeError("SQLite: database is locked")

    @pytest.mark.asyncio
    async def test_storing_levert_error_en_geen_goedkeuring(self):
        res = await _valideer(self._Kapot(), _context())
        assert res["rule_statuses"]["CON-01"] == ResultStatus.ERROR.value, res[
            "rule_statuses"
        ]
        assert res["evaluation_coverage"]["error"] >= 1, res["evaluation_coverage"]
        assert res["is_acceptable"] is False, (
            f"score {res['overall_score']} haalt de drempel, maar CON-01 kon niet "
            f"worden beoordeeld"
        )

    @pytest.mark.asyncio
    async def test_zonder_repository_blijft_con01_gemeten(self):
        res = await _valideer(None, _context())
        assert res["rule_statuses"]["CON-01"] in (
            ResultStatus.PASS.value,
            ResultStatus.FAIL.value,
        ), res["rule_statuses"]


class TestContextBlijftBuitenDeDefinitietekst:
    """Afbakening punt 1: context is metadata, nooit tekst."""

    @pytest.mark.asyncio
    async def test_evaluator_ziet_de_context_niet_in_de_tekst(self, repo, db_pad):
        _zet_canoniek(db_pad)
        gezien: list[tuple[str, str]] = []

        from services.validation.evaluators.context_metadata import (
            ContextMetadataEvaluator,
        )

        origineel = ContextMetadataEvaluator.evaluate

        def _spion(zelf, record, ctx, deps):
            gezien.append((ctx.raw_text or "", ctx.cleaned_text or ""))
            return origineel(zelf, record, ctx, deps)

        ContextMetadataEvaluator.evaluate = _spion  # type: ignore[method-assign]
        try:
            await _valideer(repo, _context())
        finally:
            ContextMetadataEvaluator.evaluate = origineel  # type: ignore[method-assign]

        assert gezien, "CON-01 is niet geëvalueerd; de test meet niets"
        for raw, cleaned in gezien:
            for waarde in (*ORG, *JUR, *WET):
                assert waarde not in raw, f"{waarde!r} in raw_text"
                assert waarde not in cleaned, f"{waarde!r} in cleaned_text"

    @pytest.mark.asyncio
    async def test_context_staat_in_metadata_en_niet_in_de_tekst(self, repo, db_pad):
        _zet_canoniek(db_pad)
        res = await _valideer(repo, _context())
        # Het duplicaatsignaal reist via de metadata-stash, niet via de tekst.
        melding = _duplicaatmeldingen(res)[0]
        assert melding["metadata"]["existing_definition_id"]
        assert DUPLICATE_STASH_KEY not in DEFINITIETEKST


class TestRecordVormBlijftOngemoeid:
    def test_definitierecord_velden_zijn_niet_van_type_veranderd(self):
        # Geen schemawijziging: de contextvelden blijven JSON-strings op het
        # record. De begrensde query bleek voldoende, dus er is geen
        # onderbouwing voor een schemawijziging nodig.
        annotaties = DefinitieRecord.__annotations__
        # De contextvelden blijven tekstkolommen met JSON erin; het record is
        # niet naar lijsten omgebouwd. De normalisatie zit in het lezen, niet
        # in een nieuw opslagtype.
        assert annotaties["organisatorische_context"] is str
        assert "str" in str(annotaties["juridische_context"])
        assert "list" not in str(annotaties["juridische_context"])

    def test_schema_is_niet_gewijzigd(self, db_pad):
        # De begrensde query bleek voldoende, dus er is geen onderbouwing voor
        # een schemawijziging nodig — en er is er dan ook geen.
        with sqlite3.connect(db_pad) as conn:
            kolommen = {
                rij[1]: rij[2]
                for rij in conn.execute("PRAGMA table_info(definities)").fetchall()
            }
        for veld in (
            "organisatorische_context",
            "juridische_context",
            "wettelijke_basis",
        ):
            assert veld in kolommen, f"kolom {veld} ontbreekt"
            assert kolommen[veld].upper().startswith("TEXT"), kolommen[veld]
