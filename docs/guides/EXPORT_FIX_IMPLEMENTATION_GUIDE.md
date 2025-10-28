# Export Fix Implementation Guide

**Quick Reference for Developer Implementing the Export Data Limitation Fix**

**Related Analysis:** `docs/reports/EXPORT_DATA_LIMITATION_ANALYSIS.md`
**Architecture Diagram:** `docs/diagrams/export-architecture-problem.md`
**Estimated Time:** 7.5 hours
**Priority:** HIGH (User-facing data loss)

---

## Pre-Implementation Checklist

- [ ] Read full analysis: `EXPORT_DATA_LIMITATION_ANALYSIS.md`
- [ ] Review current exports in `exports/` directory
- [ ] Check for downstream systems parsing export files
- [ ] Create backup branch: `git checkout -b feature/comprehensive-export`
- [ ] Run existing tests: `pytest tests/services/test_export_service.py`
- [ ] Document current export file structure

---

## Implementation Steps

### Step 1: Add to_export_dict() Method (1 hour)

**File:** `src/database/definitie_repository.py`

**Location:** Add after `to_dict()` method (around line 140)

```python
def to_export_dict(self, mode: str = 'full') -> dict[str, Any]:
    """
    Convert to export dictionary with configurable field coverage.

    Args:
        mode: Export mode
            - 'full': All 28 user-facing fields (default)
            - 'legacy': 8 fields for backward compatibility
            - 'minimal': 5 core fields only

    Returns:
        Dictionary with fields based on mode
    """
    # Core fields (always included)
    core = {
        'begrip': self.begrip,
        'definitie': self.definitie,
        'categorie': self.categorie,
        'organisatorische_context': self.organisatorische_context,
        'status': self.status,
    }

    if mode == 'minimal':
        return core

    # Legacy 8-field mode
    if mode == 'legacy':
        return {
            **core,
            'validation_score': self.validation_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    # Full mode (28 fields)
    return {
        **core,
        # Context fields
        'juridische_context': self.juridische_context,
        'wettelijke_basis': self.wettelijke_basis,

        # Business logic
        'ufo_categorie': self.ufo_categorie,
        'toelichting_proces': self.toelichting_proces,

        # Versioning
        'version_number': self.version_number,
        'previous_version_id': self.previous_version_id,

        # Validation
        'validation_score': self.validation_score,
        'validation_date': self.validation_date.isoformat() if self.validation_date else None,
        'validation_issues': self.validation_issues,

        # Source tracking
        'source_type': self.source_type,
        'source_reference': self.source_reference,
        'imported_from': self.imported_from,

        # Terminology
        'voorkeursterm': self.voorkeursterm,

        # User attribution
        'created_by': self.created_by,
        'updated_by': self.updated_by,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'updated_at': self.updated_at.isoformat() if self.updated_at else None,

        # Approval workflow
        'approved_by': self.approved_by,
        'approved_at': self.approved_at.isoformat() if self.approved_at else None,
        'approval_notes': self.approval_notes,

        # Legacy fields
        'datum_voorstel': self.datum_voorstel.isoformat() if self.datum_voorstel else None,
        'ketenpartners': self.ketenpartners,

        # Internal fields EXCLUDED:
        # - last_exported_at (internal tracking)
        # - export_destinations (internal tracking)
        # - voorkeursterm_is_begrip (deprecated)
    }
```

**Test:** `tests/database/test_definitie_repository.py`

```python
def test_to_export_dict_full():
    """Test full export includes all 28 user-facing fields."""
    record = DefinitieRecord(
        begrip="test",
        definitie="test definitie",
        categorie="ENT",
        organisatorische_context="DJI",
        juridische_context="strafrecht",
        wettelijke_basis='["Wbp"]',
        voorkeursterm="test term",
    )

    export = record.to_export_dict(mode='full')

    # Should have 28 fields
    assert len(export) == 28

    # Check critical fields
    assert export['begrip'] == "test"
    assert export['juridische_context'] == "strafrecht"
    assert export['voorkeursterm'] == "test term"

    # Should NOT include internal fields
    assert 'last_exported_at' not in export
    assert 'export_destinations' not in export

def test_to_export_dict_legacy():
    """Test legacy mode maintains backward compatibility."""
    record = DefinitieRecord(begrip="test", definitie="def", categorie="ENT")
    export = record.to_export_dict(mode='legacy')

    # Should have exactly 8 fields
    assert len(export) == 8
    assert set(export.keys()) == {
        'begrip', 'definitie', 'categorie', 'organisatorische_context',
        'status', 'validation_score', 'created_at', 'updated_at'
    }
```

---

### Step 2: Add Bulk Export to ExportService (2 hours)

**File:** `src/services/export_service.py`

**Location:** Add after `export_definitie()` method (around line 175)

```python
def export_definitions_bulk(
    self,
    definitions: list[DefinitieRecord],
    format: ExportFormat = ExportFormat.TXT,
    filename_prefix: str = "definities_export",
) -> str:
    """
    Export multiple definitions to a single file.

    Args:
        definitions: List of definitions to export
        format: Export format
        filename_prefix: Prefix for generated filename

    Returns:
        Path to exported file

    Raises:
        ValueError: If definitions list is empty
        NotImplementedError: If format is not supported
    """
    if not definitions:
        raise ValueError("No definitions provided for export")

    logger.info(f"Bulk export: {len(definitions)} definitions to {format.value}")

    if format == ExportFormat.TXT:
        return self._export_bulk_to_txt(definitions, filename_prefix)
    if format == ExportFormat.JSON:
        return self._export_bulk_to_json(definitions, filename_prefix)
    if format == ExportFormat.CSV:
        return self._export_bulk_to_csv(definitions, filename_prefix)

    msg = f"Bulk export format {format} not implemented"
    raise NotImplementedError(msg)

def _export_bulk_to_txt(
    self,
    definitions: list[DefinitieRecord],
    filename_prefix: str,
) -> str:
    """Export multiple definitions to TXT format."""
    tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    bestandsnaam = f"{filename_prefix}_{tijdstempel}.txt"
    pad = self.export_dir / bestandsnaam

    lines = [
        "=" * 80,
        f"DEFINITIE EXPORT - {len(definitions)} definities",
        f"Geëxporteerd op: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
        "",
    ]

    for idx, definitie in enumerate(definitions, 1):
        # Convert to export dict
        export_dict = definitie.to_export_dict(mode='full')

        lines.extend([
            f"\n{'=' * 80}",
            f"DEFINITIE {idx}/{len(definitions)}",
            f"{'=' * 80}",
            "",
            f"📘 Begrip: {export_dict['begrip']}",
            f"📝 Definitie: {export_dict['definitie']}",
            "",
            f"🏷️  Categorie: {export_dict['categorie']}",
            f"🏛️  UFO Categorie: {export_dict.get('ufo_categorie', 'n/a')}",
            f"📊 Status: {export_dict['status']}",
            "",
            "📍 Context:",
            f"  • Organisatorisch: {export_dict['organisatorische_context']}",
            f"  • Juridisch: {export_dict.get('juridische_context', 'n/a')}",
            f"  • Wettelijke basis: {export_dict.get('wettelijke_basis', 'n/a')}",
            "",
            f"🏷️  Voorkeursterm: {export_dict.get('voorkeursterm', 'n/a')}",
            f"💡 Toelichting: {export_dict.get('toelichting_proces', 'n/a')}",
            "",
            "✅ Validatie:",
            f"  • Score: {export_dict.get('validation_score', 'n/a')}",
            f"  • Datum: {export_dict.get('validation_date', 'n/a')}",
            f"  • Issues: {export_dict.get('validation_issues', 'geen')}",
            "",
            "📄 Bron:",
            f"  • Type: {export_dict.get('source_type', 'n/a')}",
            f"  • Referentie: {export_dict.get('source_reference', 'n/a')}",
            f"  • Geïmporteerd van: {export_dict.get('imported_from', 'n/a')}",
            "",
            "👤 Goedkeuring:",
            f"  • Goedgekeurd door: {export_dict.get('approved_by', 'n/a')}",
            f"  • Datum: {export_dict.get('approved_at', 'n/a')}",
            f"  • Notities: {export_dict.get('approval_notes', 'n/a')}",
            "",
            "📅 Metadata:",
            f"  • Aangemaakt: {export_dict.get('created_at', 'n/a')} door {export_dict.get('created_by', 'n/a')}",
            f"  • Gewijzigd: {export_dict.get('updated_at', 'n/a')} door {export_dict.get('updated_by', 'n/a')}",
            f"  • Versie: {export_dict.get('version_number', 'n/a')}",
            "",
        ])

    # Write to file
    with open(pad, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Bulk TXT export completed: {pad}")
    return str(pad)

def _export_bulk_to_csv(
    self,
    definitions: list[DefinitieRecord],
    filename_prefix: str,
) -> str:
    """Export multiple definitions to CSV format."""
    import csv

    tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    bestandsnaam = f"{filename_prefix}_{tijdstempel}.csv"
    pad = self.export_dir / bestandsnaam

    # Get all field names from first record (all should have same fields)
    if definitions:
        fieldnames = list(definitions[0].to_export_dict(mode='full').keys())
    else:
        fieldnames = []

    with open(pad, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for definitie in definitions:
            writer.writerow(definitie.to_export_dict(mode='full'))

    logger.info(f"Bulk CSV export completed: {pad} ({len(definitions)} records)")
    return str(pad)

def _export_bulk_to_json(
    self,
    definitions: list[DefinitieRecord],
    filename_prefix: str,
) -> str:
    """Export multiple definitions to JSON format."""
    tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    bestandsnaam = f"{filename_prefix}_{tijdstempel}.json"
    pad = self.export_dir / bestandsnaam

    json_data = {
        'export_info': {
            'export_timestamp': datetime.now(UTC).isoformat(),
            'export_version': '2.0',
            'format': 'json',
            'count': len(definitions),
        },
        'definitions': [d.to_export_dict(mode='full') for d in definitions],
    }

    with open(pad, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Bulk JSON export completed: {pad}")
    return str(pad)
```

**Test:** `tests/services/test_export_service.py`

```python
def test_export_definitions_bulk_txt(tmp_path):
    """Test bulk TXT export with multiple definitions."""
    repository = DefinitieRepository(db_path=":memory:")
    service = ExportService(repository, export_dir=str(tmp_path))

    # Create test definitions
    definitions = [
        DefinitieRecord(begrip=f"test_{i}", definitie=f"def {i}", categorie="ENT")
        for i in range(3)
    ]

    # Export
    path = service.export_definitions_bulk(definitions, format=ExportFormat.TXT)

    # Verify
    assert Path(path).exists()
    content = Path(path).read_text(encoding='utf-8')
    assert "DEFINITIE 1/3" in content
    assert "DEFINITIE 3/3" in content
    assert "test_0" in content
    assert "test_2" in content

def test_export_field_coverage():
    """Ensure bulk export includes all 28 user-facing fields."""
    record = DefinitieRecord(
        begrip="test",
        definitie="test",
        categorie="ENT",
        juridische_context="strafrecht",
        voorkeursterm="preferred",
    )

    export = record.to_export_dict(mode='full')

    # Critical fields must be present
    critical_fields = [
        'begrip', 'definitie', 'categorie',
        'juridische_context', 'wettelijke_basis',
        'voorkeursterm', 'ufo_categorie',
        'approved_by', 'approved_at',
        'validation_issues',
    ]

    for field in critical_fields:
        assert field in export, f"Missing critical field: {field}"
```

---

### Step 3: Refactor FormatExporter (2 hours)

**File:** `src/ui/components/tabs/import_export_beheer/format_exporter.py`

**Changes:**

1. **Add ExportService dependency:**

```python
from services.export_service import ExportService, ExportFormat

class FormatExporter:
    def __init__(self, repository: DefinitieRepository):
        self.repository = repository
        self.export_service = ExportService(repository)  # NEW
```

2. **Replace _generate_export() method:**

```python
def _generate_export(self, format: str, status_filter: str, limit: int):
    """Generate export using ExportService."""
    with st.spinner("Export genereren..."):
        try:
            # Get definitions
            if status_filter == "Alle":
                definitions = self.repository.get_all()
            else:
                definitions = self.repository.get_by_status(status_filter)

            # Apply limit
            if limit > 0:
                definitions = definitions[:limit]

            if not definitions:
                st.warning("Geen definities gevonden voor export")
                return

            # Use ExportService for bulk export
            export_format = ExportFormat(format.lower())
            path = self.export_service.export_definitions_bulk(
                definitions=definitions,
                format=export_format,
                filename_prefix="definities_export"
            )

            # Show success and download button
            with open(path, 'rb') as f:
                file_data = f.read()

            filename = Path(path).name
            mime_type = self._get_mime_type(format)

            st.download_button(
                label=f"📥 Download {format} ({len(definitions)} definities)",
                data=file_data,
                file_name=filename,
                mime=mime_type,
            )

            st.success(f"✅ Export gegenereerd: {len(definitions)} definities")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            st.error(f"Fout bij genereren export: {e!s}")

def _get_mime_type(self, format: str) -> str:
    """Get MIME type for format."""
    mime_types = {
        'CSV': 'text/csv',
        'TXT': 'text/plain',
        'JSON': 'application/json',
        'Excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return mime_types.get(format, 'text/plain')
```

3. **Remove obsolete methods:**

```python
# DELETE these methods (no longer needed):
# - _definitions_to_dataframe()
# - _generate_txt_export()
```

**Test:** Manual UI test after implementation

---

### Step 4: Add Field Coverage Test (1 hour)

**File:** `tests/services/test_export_field_coverage.py` (NEW)

```python
"""
Test suite for export field coverage.

Ensures that exports include all user-facing fields from DefinitieRecord.
"""

import pytest
from database.definitie_repository import DefinitieRecord


def test_export_dict_covers_all_user_fields():
    """Verify to_export_dict() includes all 28 user-facing fields."""
    record = DefinitieRecord(begrip="test", definitie="test", categorie="ENT")
    export = record.to_export_dict(mode='full')

    # Should have 28 fields (31 total - 3 internal)
    assert len(export) == 28, f"Expected 28 fields, got {len(export)}"

    # Define all expected fields
    expected_fields = {
        # Core (5)
        'begrip', 'definitie', 'categorie', 'organisatorische_context', 'status',
        # Context (2)
        'juridische_context', 'wettelijke_basis',
        # Business logic (2)
        'ufo_categorie', 'toelichting_proces',
        # Versioning (2)
        'version_number', 'previous_version_id',
        # Validation (3)
        'validation_score', 'validation_date', 'validation_issues',
        # Source tracking (3)
        'source_type', 'source_reference', 'imported_from',
        # Terminology (1)
        'voorkeursterm',
        # User attribution (4)
        'created_by', 'updated_by', 'created_at', 'updated_at',
        # Approval (3)
        'approved_by', 'approved_at', 'approval_notes',
        # Legacy (2)
        'datum_voorstel', 'ketenpartners',
    }

    assert set(export.keys()) == expected_fields

    # Should NOT include internal fields
    internal_fields = {'last_exported_at', 'export_destinations', 'voorkeursterm_is_begrip'}
    assert not any(f in export for f in internal_fields)


def test_critical_fields_not_null_when_set():
    """Ensure critical fields are included when they have values."""
    record = DefinitieRecord(
        begrip="test",
        definitie="test definitie",
        categorie="ENT",
        juridische_context="strafrecht",
        wettelijke_basis='["Wbp", "AVG"]',
        voorkeursterm="preferred term",
        approved_by="admin",
    )

    export = record.to_export_dict(mode='full')

    # Critical fields should preserve values
    assert export['juridische_context'] == "strafrecht"
    assert export['wettelijke_basis'] == '["Wbp", "AVG"]'
    assert export['voorkeursterm'] == "preferred term"
    assert export['approved_by'] == "admin"


def test_legacy_mode_backward_compatible():
    """Verify legacy mode maintains 8-field backward compatibility."""
    record = DefinitieRecord(begrip="test", definitie="test", categorie="ENT")
    export = record.to_export_dict(mode='legacy')

    assert len(export) == 8
    assert set(export.keys()) == {
        'begrip', 'definitie', 'categorie', 'organisatorische_context',
        'status', 'validation_score', 'created_at', 'updated_at'
    }
```

**Run test:**
```bash
pytest tests/services/test_export_field_coverage.py -v
```

---

### Step 5: Update Documentation (1 hour)

**File 1:** `docs/architectuur/export-architecture.md` (NEW)

```markdown
# Export Architecture

## Overview
All export functionality flows through `ExportService` to ensure consistent field coverage.

## Components
- **ExportService**: Core export logic
- **DefinitieRecord.to_export_dict()**: Field mapping
- **FormatExporter**: UI wrapper (delegates to ExportService)
- **UIComponentsAdapter**: Single-definition exports

## Field Coverage
Exports include 28 out of 31 DefinitieRecord fields:
- 31 total database fields
- 28 user-facing fields (exported)
- 3 internal fields (excluded)

See `test_export_field_coverage.py` for field list.
```

**File 2:** Update `CLAUDE.md`

Add to "Development Richtlijnen" section:

```markdown
### Export Architectuur

- **Centrale export:** Alle export via `ExportService` (Single Responsibility)
- **Field coverage:** 28/31 velden (exclusief internal tracking)
- **Formaten:** TXT, JSON, CSV (allen via `DefinitieRecord.to_export_dict()`)
- **Test validatie:** `test_export_field_coverage.py` voorkomt field regressie
- **Bulk vs single:** Beide paden gebruiken `ExportService`

**BELANGRIJK:** Nieuwe velden in `DefinitieRecord` MOETEN toegevoegd worden aan `to_export_dict()` én `test_export_field_coverage.py`
```

---

### Step 6: Manual Testing (30 min)

**Test Checklist:**

1. **UI Bulk Export Test:**
   - [ ] Open Import/Export tab
   - [ ] Export 10 definitions to TXT
   - [ ] Verify file contains 28 fields per definition
   - [ ] Check for juridische_context, voorkeursterm, approved_by

2. **Single Definition Export Test:**
   - [ ] Generate a definition in Generator tab
   - [ ] Click export button
   - [ ] Verify same field coverage as bulk export

3. **Format Comparison:**
   - [ ] Export same definitions to TXT, CSV, JSON
   - [ ] Verify all formats have identical field coverage
   - [ ] Check CSV has 28 columns

4. **Backward Compatibility:**
   - [ ] If needed, test legacy mode: `to_export_dict(mode='legacy')`
   - [ ] Verify produces 8-field output

5. **Performance Test:**
   - [ ] Export 100+ definitions
   - [ ] Check file size (~3x larger than before)
   - [ ] Verify performance is acceptable (< 5 seconds)

---

## Rollback Plan

**If issues arise during implementation:**

1. **Keep old code temporarily:**
   ```python
   # In format_exporter.py
   USE_NEW_EXPORT = os.getenv("USE_NEW_EXPORT", "true") == "true"

   if USE_NEW_EXPORT:
       path = self.export_service.export_definitions_bulk(...)
   else:
       # Old code path (fallback)
       df = self._definitions_to_dataframe(definitions)
       ...
   ```

2. **Set environment variable to rollback:**
   ```bash
   export USE_NEW_EXPORT=false
   streamlit run src/main.py
   ```

3. **Fix issues, then re-enable:**
   ```bash
   export USE_NEW_EXPORT=true
   ```

---

## Success Criteria

### Quantitative
- ✅ Export includes 28/31 fields (90% coverage)
- ✅ Tests pass: `test_export_field_coverage.py`
- ✅ No performance degradation (< 5s for 100 records)
- ✅ File size increase acceptable (~3x)

### Qualitative
- ✅ User complaint resolved
- ✅ Single export codebase (no duplication)
- ✅ Documented field mapping
- ✅ Automated regression prevention

---

## Post-Implementation Tasks

1. **Monitor first week:**
   - Watch for user feedback
   - Check export file sizes
   - Monitor performance metrics

2. **Document lessons learned:**
   - Update `docs/refactor-log.md`
   - Add to team knowledge base

3. **Remove feature flag (after 1 week):**
   - If no issues, delete `USE_NEW_EXPORT` rollback code
   - Clean up old methods

4. **Consider future enhancements:**
   - Export profiles (minimal, standard, full)
   - Excel formatting (bold headers, frozen panes)
   - Export scheduling/automation

---

## File Reference Summary

**Modified Files:**
- `src/database/definitie_repository.py` - Add `to_export_dict()`
- `src/services/export_service.py` - Add bulk export methods
- `src/ui/components/tabs/import_export_beheer/format_exporter.py` - Refactor to use service

**New Files:**
- `tests/services/test_export_field_coverage.py` - Field coverage tests
- `docs/architectuur/export-architecture.md` - Architecture documentation

**Updated Documentation:**
- `CLAUDE.md` - Add export architecture section
- `docs/refactor-log.md` - Document this refactoring

---

## Questions During Implementation?

**Check these resources:**
1. Full analysis: `docs/reports/EXPORT_DATA_LIMITATION_ANALYSIS.md`
2. Architecture diagram: `docs/diagrams/export-architecture-problem.md`
3. Existing tests: `tests/services/test_export_service.py`
4. Field list: `src/database/schema.sql` lines 9-82

**Still stuck?** Review the "Root Cause Summary" section in the analysis document.
