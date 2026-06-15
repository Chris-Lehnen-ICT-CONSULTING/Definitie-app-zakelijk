"""Import/export en statistieken voor definities."""

import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from database.audit_helpers import AuditHelpers
from database.db_connection import DatabaseConnection
from database.models import DefinitieRecord, DefinitieStatus, SourceType
from domain.ontological_categories import OntologischeCategorie

logger = logging.getLogger(__name__)


class DefinitieImportExportRepository:
    """Import, export en statistieken repository."""

    def __init__(self, db: DatabaseConnection, audit: AuditHelpers):
        self._db = db
        self._audit = audit

    def get_statistics(self) -> dict[str, Any]:
        """Haal database statistieken op."""
        with self._db.get_connection() as conn:
            stats = {}

            cursor = conn.execute("SELECT COUNT(*) FROM definities")
            stats["total_definities"] = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM definities GROUP BY status"
            )
            stats["by_status"] = dict(cursor.fetchall())

            cursor = conn.execute(
                "SELECT categorie, COUNT(*) FROM definities GROUP BY categorie"
            )
            stats["by_category"] = dict(cursor.fetchall())

            cursor = conn.execute("""
                SELECT AVG(validation_score) FROM definities
                WHERE validation_score IS NOT NULL
            """)
            avg_score = cursor.fetchone()[0]
            stats["average_validation_score"] = (
                round(avg_score, 3) if avg_score else None
            )

            return stats

    def export_to_json(
        self,
        file_path: str,
        filters: dict[str, Any] | None = None,
        *,
        search_fn: Callable[..., Any],
    ) -> int:
        """Exporteer definities naar JSON bestand.

        Args:
            file_path: Pad voor export bestand
            filters: Optionele filters (status, categorie, etc.)
            search_fn: Callable voor search_definities (injected vanuit facade)
        """
        filter_categorie: OntologischeCategorie | None = (
            filters.get("categorie") if filters else None
        )
        filter_org_context: str | None = (
            filters.get("organisatorische_context") if filters else None
        )
        filter_status: DefinitieStatus | None = (
            filters.get("status") if filters else None
        )
        records = search_fn(
            categorie=filter_categorie,
            organisatorische_context=filter_org_context,
            status=filter_status,
            limit=None,
        )

        serializable_filters = {}
        if filters:
            for key, value in filters.items():
                if hasattr(value, "value"):
                    serializable_filters[key] = value.value
                else:
                    serializable_filters[key] = value

        export_data = {
            "export_info": {
                "timestamp": datetime.now(UTC).isoformat(),
                "total_count": len(records),
                "filters_applied": serializable_filters,
            },
            "definities": [record.to_dict() for record in records],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        self._audit.log_import_export(
            "export", file_path, len(records), len(records), 0
        )

        logger.info(f"Exported {len(records)} definities to {file_path}")
        return len(records)

    def import_from_json(
        self,
        file_path: str,
        import_by: str | None = None,
        *,
        create_fn: Callable[..., Any],
    ) -> tuple[int, int, list[str]]:
        """Importeer definities uit JSON bestand.

        Args:
            file_path: Pad naar import bestand
            import_by: Wie de import uitvoert
            create_fn: Callable voor create_definitie (injected vanuit facade)
        """
        successful = 0
        failed = 0
        errors = []

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            definities = data.get("definities", [])

            for item in definities:
                try:
                    record = DefinitieRecord(
                        **{
                            k: v
                            for k, v in item.items()
                            if k in DefinitieRecord.__dataclass_fields__
                        }
                    )

                    record.source_type = SourceType.IMPORTED.value
                    record.imported_from = file_path
                    record.created_by = import_by

                    record.id = None
                    record.created_at = None
                    record.updated_at = None

                    create_fn(record)
                    successful += 1

                except Exception as e:
                    failed += 1
                    errors.append(
                        f"Failed to import '{item.get('begrip', 'unknown')}': {e!s}"
                    )

        except Exception as e:
            errors.append(f"Failed to read import file: {e!s}")

        self._audit.log_import_export(
            "import", file_path, successful + failed, successful, failed
        )

        logger.info(f"Import completed: {successful} successful, {failed} failed")
        return successful, failed, errors
