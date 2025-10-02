"""Tests voor de insert helper van DefinitieRepository."""

from datetime import UTC, datetime, timezone

from database.definitie_repository import DefinitieRecord, DefinitieRepository


def _make_record() -> DefinitieRecord:
    record = DefinitieRecord()
    record.begrip = "Test"
    record.definitie = "Een testdefinitie"
    record.categorie = "type"
    record.organisatorische_context = "[]"
    record.juridische_context = "[]"
    record.wettelijke_basis = "[]"
    record.ufo_categorie = "Kind"
    record.toelichting_proces = "Proces toelichting"
    record.status = "draft"
    record.version_number = 1
    record.previous_version_id = None
    record.validation_score = 0.9
    record.validation_date = datetime.now(UTC)
    record.validation_issues = None
    record.source_type = "generated"
    record.source_reference = "bron"
    record.imported_from = "import"
    record.created_at = datetime.now(UTC)
    record.updated_at = datetime.now(UTC)
    record.created_by = "tester"
    record.updated_by = "tester"
    record.approved_by = "approver"
    record.approved_at = datetime.now(UTC)
    record.approval_notes = "notes"
    record.last_exported_at = None
    record.export_destinations = "[]"
    record.datum_voorstel = datetime.now(UTC)
    record.ketenpartners = "[]"
    return record


def test_build_insert_columns_without_legacy():
    record = _make_record()
    columns, values = DefinitieRepository._build_insert_columns(
        record, record.wettelijke_basis or "[]", include_legacy=False
    )

    expected_columns = [
        "begrip",
        "definitie",
        "categorie",
        "organisatorische_context",
        "juridische_context",
        "wettelijke_basis",
        "ufo_categorie",
        "toelichting_proces",
        "status",
        "version_number",
        "previous_version_id",
        "validation_score",
        "validation_date",
        "validation_issues",
        "source_type",
        "source_reference",
        "imported_from",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "approved_by",
        "approved_at",
        "approval_notes",
        "last_exported_at",
        "export_destinations",
    ]

    assert columns == expected_columns
    assert len(columns) == len(values)
    assert values[0] == record.begrip
    assert values[expected_columns.index("wettelijke_basis")] == record.wettelijke_basis


def test_build_insert_columns_with_legacy():
    record = _make_record()
    columns, values = DefinitieRepository._build_insert_columns(
        record, record.wettelijke_basis or "[]", include_legacy=True
    )

    assert columns[-2:] == ["datum_voorstel", "ketenpartners"]
    assert values[-2:] == [record.datum_voorstel, record.ketenpartners]
    assert len(columns) == len(values)
