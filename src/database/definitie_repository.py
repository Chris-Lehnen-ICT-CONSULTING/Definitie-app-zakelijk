"""
DefinitieRepository - Database laag voor definitie management systeem.
Biedt CRUD operaties, duplicate detection, en import/export functionaliteit.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import hashlib
from enum import Enum

from generation.definitie_generator import OntologischeCategorie

logger = logging.getLogger(__name__)


class DefinitieStatus(Enum):
    """Status van een definitie in het systeem."""
    DRAFT = "draft"
    REVIEW = "review"  
    ESTABLISHED = "established"
    ARCHIVED = "archived"


class SourceType(Enum):
    """Type van de bron waaruit definitie komt."""
    GENERATED = "generated"
    IMPORTED = "imported"
    MANUAL = "manual"


@dataclass
class DefinitieRecord:
    """Representatie van een definitie record in de database."""
    id: Optional[int] = None
    begrip: str = ""
    definitie: str = ""
    categorie: str = ""
    organisatorische_context: str = ""
    juridische_context: Optional[str] = ""
    
    # Status en versioning
    status: str = DefinitieStatus.DRAFT.value
    version_number: int = 1
    previous_version_id: Optional[int] = None
    
    # Validation
    validation_score: Optional[float] = None
    validation_date: Optional[datetime] = None
    validation_issues: Optional[str] = None  # JSON string
    
    # Source tracking
    source_type: str = SourceType.GENERATED.value
    source_reference: Optional[str] = None
    imported_from: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    
    # Export
    last_exported_at: Optional[datetime] = None
    export_destinations: Optional[str] = None  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary voor JSON serialization."""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result
    
    def get_validation_issues_list(self) -> List[Dict[str, Any]]:
        """Haal validation issues op als list."""
        if not self.validation_issues:
            return []
        try:
            return json.loads(self.validation_issues)
        except json.JSONDecodeError:
            return []
    
    def set_validation_issues(self, issues: List[Dict[str, Any]]):
        """Set validation issues als JSON string."""
        self.validation_issues = json.dumps(issues, ensure_ascii=False)
    
    def get_export_destinations_list(self) -> List[str]:
        """Haal export destinations op als list."""
        if not self.export_destinations:
            return []
        try:
            return json.loads(self.export_destinations)
        except json.JSONDecodeError:
            return []
    
    def add_export_destination(self, destination: str):
        """Voeg export destination toe."""
        destinations = self.get_export_destinations_list()
        if destination not in destinations:
            destinations.append(destination)
            self.export_destinations = json.dumps(destinations)


@dataclass
class DuplicateMatch:
    """Representatie van een mogelijk duplicaat."""
    definitie_record: DefinitieRecord
    match_score: float
    match_reasons: List[str]


class DefinitieRepository:
    """Repository voor definitie management met volledige CRUD operaties."""
    
    def __init__(self, db_path: str = "definities.db"):
        """
        Initialiseer repository met database connectie.
        
        Args:
            db_path: Pad naar SQLite database bestand
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialiseer database met schema."""
        # Zorg dat database directory bestaat
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Laad schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    # Execute schema in parts (SQLite doesn't like some multi-statement syntax)
                    statements = self._split_sql_statements(schema_sql)
                    for statement in statements:
                        if statement.strip():
                            try:
                                conn.execute(statement)
                            except sqlite3.Error as e:
                                # Skip errors for existing tables/triggers
                                if "already exists" not in str(e):
                                    logger.warning(f"Schema execution warning: {e}")
                conn.commit()
        else:
            logger.warning(f"Schema file not found at {schema_path}")
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL bestand in individuele statements."""
        # Simple split on semicolon - could be improved for complex cases
        statements = []
        current_statement = ""
        
        for line in sql.split('\n'):
            line = line.strip()
            if line.startswith('--') or not line:
                continue
            
            current_statement += line + '\n'
            
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        return statements
    
    def _get_connection(self) -> sqlite3.Connection:
        """Haal database connectie op met Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enables column access by name
        return conn
    
    def create_definitie(self, record: DefinitieRecord) -> int:
        """
        Maak nieuwe definitie aan.
        
        Args:
            record: DefinitieRecord object
            
        Returns:
            ID van nieuw aangemaakte record
        """
        with self._get_connection() as conn:
            # Check voor duplicates
            duplicates = self.find_duplicates(
                record.begrip, 
                record.organisatorische_context,
                record.juridische_context or ""
            )
            
            if duplicates and any(d.definitie_record.status != DefinitieStatus.ARCHIVED.value for d in duplicates):
                raise ValueError(f"Definitie voor '{record.begrip}' bestaat al in deze context")
            
            # Set timestamps
            now = datetime.now()
            record.created_at = now
            record.updated_at = now
            
            # Insert record
            cursor = conn.execute("""
                INSERT INTO definities (
                    begrip, definitie, categorie, organisatorische_context, juridische_context,
                    status, version_number, previous_version_id,
                    validation_score, validation_date, validation_issues,
                    source_type, source_reference, imported_from,
                    created_at, updated_at, created_by, updated_by,
                    approved_by, approved_at, approval_notes,
                    last_exported_at, export_destinations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.begrip, record.definitie, record.categorie,
                record.organisatorische_context, record.juridische_context,
                record.status, record.version_number, record.previous_version_id,
                record.validation_score, record.validation_date, record.validation_issues,
                record.source_type, record.source_reference, record.imported_from,
                record.created_at, record.updated_at, record.created_by, record.updated_by,
                record.approved_by, record.approved_at, record.approval_notes,
                record.last_exported_at, record.export_destinations
            ))
            
            record_id = cursor.lastrowid
            
            # Log creation
            self._log_geschiedenis(record_id, "created", record.created_by, 
                                 f"Nieuwe definitie aangemaakt voor '{record.begrip}'")
            
            logger.info(f"Created definitie {record_id} voor '{record.begrip}'")
            return record_id
    
    def get_definitie(self, definitie_id: int) -> Optional[DefinitieRecord]:
        """
        Haal definitie op op basis van ID.
        
        Args:
            definitie_id: Database ID
            
        Returns:
            DefinitieRecord of None als niet gevonden
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM definities WHERE id = ?", 
                (definitie_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_record(row)
            return None
    
    def find_definitie(
        self, 
        begrip: str, 
        organisatorische_context: str,
        juridische_context: str = "",
        status: Optional[DefinitieStatus] = None
    ) -> Optional[DefinitieRecord]:
        """
        Zoek definitie op basis van begrip en context.
        
        Args:
            begrip: Het begrip
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            status: Optionele status filter
            
        Returns:
            DefinitieRecord of None
        """
        with self._get_connection() as conn:
            query = """
                SELECT * FROM definities 
                WHERE begrip = ? AND organisatorische_context = ? 
                AND (juridische_context = ? OR (juridische_context IS NULL AND ? = ''))
            """
            params = [begrip, organisatorische_context, juridische_context, juridische_context]
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY version_number DESC LIMIT 1"
            
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                return self._row_to_record(row)
            return None
    
    def find_duplicates(
        self, 
        begrip: str, 
        organisatorische_context: str,
        juridische_context: str = ""
    ) -> List[DuplicateMatch]:
        """
        Zoek mogelijke duplicaten voor een begrip.
        
        Args:
            begrip: Het begrip om te checken
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            
        Returns:
            List van DuplicateMatch objecten
        """
        matches = []
        
        with self._get_connection() as conn:
            # Exact match
            cursor = conn.execute("""
                SELECT * FROM definities 
                WHERE begrip = ? AND organisatorische_context = ?
                AND (juridische_context = ? OR (juridische_context IS NULL AND ? = ''))
                AND status != 'archived'
            """, (begrip, organisatorische_context, juridische_context, juridische_context))
            
            for row in cursor.fetchall():
                record = self._row_to_record(row)
                matches.append(DuplicateMatch(
                    definitie_record=record,
                    match_score=1.0,
                    match_reasons=["Exact match: begrip + context"]
                ))
            
            # Fuzzy match op begrip (alleen als geen exact match)
            if not matches:
                cursor = conn.execute("""
                    SELECT * FROM definities 
                    WHERE begrip LIKE ? AND organisatorische_context = ?
                    AND status != 'archived'
                """, (f"%{begrip}%", organisatorische_context))
                
                for row in cursor.fetchall():
                    record = self._row_to_record(row)
                    similarity = self._calculate_similarity(begrip, record.begrip)
                    if similarity > 0.7:  # 70% similarity threshold
                        matches.append(DuplicateMatch(
                            definitie_record=record,
                            match_score=similarity,
                            match_reasons=[f"Fuzzy match: '{begrip}' ≈ '{record.begrip}'"]
                        ))
        
        return sorted(matches, key=lambda x: x.match_score, reverse=True)
    
    def update_definitie(self, definitie_id: int, updates: Dict[str, Any], updated_by: str = None) -> bool:
        """
        Update bestaande definitie.
        
        Args:
            definitie_id: Database ID
            updates: Dictionary met velden om te updaten
            updated_by: Wie de update uitvoert
            
        Returns:
            True als succesvol geupdate
        """
        with self._get_connection() as conn:
            # Haal huidige record op
            current = self.get_definitie(definitie_id)
            if not current:
                return False
            
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if hasattr(current, field):
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            # Add metadata
            set_clauses.append("updated_at = ?")
            params.append(datetime.now())
            
            if updated_by:
                set_clauses.append("updated_by = ?")
                params.append(updated_by)
            
            params.append(definitie_id)
            
            # Execute update
            query = f"UPDATE definities SET {', '.join(set_clauses)} WHERE id = ?"
            conn.execute(query, params)
            
            # Log update
            self._log_geschiedenis(definitie_id, "updated", updated_by, 
                                 f"Definitie geupdate: {list(updates.keys())}")
            
            logger.info(f"Updated definitie {definitie_id}")
            return True
    
    def change_status(self, definitie_id: int, new_status: DefinitieStatus, 
                     changed_by: str = None, notes: str = None) -> bool:
        """
        Wijzig status van definitie.
        
        Args:
            definitie_id: Database ID
            new_status: Nieuwe status
            changed_by: Wie de wijziging uitvoert
            notes: Optionele notities
            
        Returns:
            True als succesvol gewijzigd
        """
        updates = {"status": new_status.value}
        
        if new_status == DefinitieStatus.ESTABLISHED and changed_by:
            updates.update({
                "approved_by": changed_by,
                "approved_at": datetime.now(),
                "approval_notes": notes
            })
        
        success = self.update_definitie(definitie_id, updates, changed_by)
        
        if success:
            self._log_geschiedenis(definitie_id, "status_changed", changed_by,
                                 f"Status gewijzigd naar {new_status.value}")
        
        return success
    
    def search_definities(
        self, 
        query: str = None,
        categorie: OntologischeCategorie = None,
        organisatorische_context: str = None,
        status: DefinitieStatus = None,
        limit: int = 100
    ) -> List[DefinitieRecord]:
        """
        Zoek definities met verschillende filters.
        
        Args:
            query: Zoekterm (zoekt in begrip en definitie)
            categorie: Filter op categorie
            organisatorische_context: Filter op organisatie
            status: Filter op status
            limit: Maximum aantal resultaten
            
        Returns:
            List van DefinitieRecord objecten
        """
        with self._get_connection() as conn:
            where_clauses = []
            params = []
            
            if query:
                where_clauses.append("(begrip LIKE ? OR definitie LIKE ?)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term])
            
            if categorie:
                where_clauses.append("categorie = ?")
                params.append(categorie.value)
            
            if organisatorische_context:
                where_clauses.append("organisatorische_context = ?")
                params.append(organisatorische_context)
            
            if status:
                where_clauses.append("status = ?")
                params.append(status.value)
            
            base_query = "SELECT * FROM definities"
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            base_query += " ORDER BY begrip, created_at DESC"
            
            if limit:
                base_query += f" LIMIT {limit}"
            
            cursor = conn.execute(base_query, params)
            return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Haal database statistieken op."""
        with self._get_connection() as conn:
            stats = {}
            
            # Total counts
            cursor = conn.execute("SELECT COUNT(*) FROM definities")
            stats['total_definities'] = cursor.fetchone()[0]
            
            # Counts by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM definities GROUP BY status
            """)
            stats['by_status'] = dict(cursor.fetchall())
            
            # Counts by category
            cursor = conn.execute("""
                SELECT categorie, COUNT(*) FROM definities GROUP BY categorie
            """)
            stats['by_category'] = dict(cursor.fetchall())
            
            # Average validation score
            cursor = conn.execute("""
                SELECT AVG(validation_score) FROM definities 
                WHERE validation_score IS NOT NULL
            """)
            avg_score = cursor.fetchone()[0]
            stats['average_validation_score'] = round(avg_score, 3) if avg_score else None
            
            return stats
    
    def export_to_json(self, file_path: str, filters: Dict[str, Any] = None) -> int:
        """
        Exporteer definities naar JSON bestand.
        
        Args:
            file_path: Pad voor export bestand
            filters: Optionele filters (status, categorie, etc.)
            
        Returns:
            Aantal geëxporteerde definities
        """
        # Apply filters to get records
        records = self.search_definities(
            categorie=filters.get('categorie') if filters else None,
            organisatorische_context=filters.get('organisatorische_context') if filters else None,
            status=filters.get('status') if filters else None,
            limit=None  # No limit for export
        )
        
        # Convert filters to serializable format
        serializable_filters = {}
        if filters:
            for key, value in filters.items():
                if hasattr(value, 'value'):  # Enum
                    serializable_filters[key] = value.value
                else:
                    serializable_filters[key] = value
        
        # Convert to dict format
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'total_count': len(records),
                'filters_applied': serializable_filters
            },
            'definities': [record.to_dict() for record in records]
        }
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # Log export
        self._log_import_export('export', file_path, len(records), len(records), 0)
        
        logger.info(f"Exported {len(records)} definities to {file_path}")
        return len(records)
    
    def import_from_json(self, file_path: str, import_by: str = None) -> Tuple[int, int, List[str]]:
        """
        Importeer definities uit JSON bestand.
        
        Args:
            file_path: Pad naar import bestand
            import_by: Wie de import uitvoert
            
        Returns:
            Tuple van (succesvol, gefaald, error_messages)
        """
        successful = 0
        failed = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            definities = data.get('definities', [])
            
            for item in definities:
                try:
                    # Create record from dict
                    record = DefinitieRecord(**{
                        k: v for k, v in item.items() 
                        if k in DefinitieRecord.__dataclass_fields__
                    })
                    
                    # Set import metadata
                    record.source_type = SourceType.IMPORTED.value
                    record.imported_from = file_path
                    record.created_by = import_by
                    
                    # Clear ID and timestamps for new record
                    record.id = None
                    record.created_at = None
                    record.updated_at = None
                    
                    self.create_definitie(record)
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to import '{item.get('begrip', 'unknown')}': {str(e)}")
        
        except Exception as e:
            errors.append(f"Failed to read import file: {str(e)}")
        
        # Log import
        self._log_import_export('import', file_path, successful + failed, successful, failed)
        
        logger.info(f"Import completed: {successful} successful, {failed} failed")
        return successful, failed, errors
    
    def _row_to_record(self, row: sqlite3.Row) -> DefinitieRecord:
        """Converteer database row naar DefinitieRecord."""
        return DefinitieRecord(
            id=row['id'],
            begrip=row['begrip'],
            definitie=row['definitie'],
            categorie=row['categorie'],
            organisatorische_context=row['organisatorische_context'],
            juridische_context=row['juridische_context'],
            status=row['status'],
            version_number=row['version_number'],
            previous_version_id=row['previous_version_id'],
            validation_score=row['validation_score'],
            validation_date=datetime.fromisoformat(row['validation_date']) if row['validation_date'] else None,
            validation_issues=row['validation_issues'],
            source_type=row['source_type'],
            source_reference=row['source_reference'],
            imported_from=row['imported_from'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            created_by=row['created_by'],
            updated_by=row['updated_by'],
            approved_by=row['approved_by'],
            approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
            approval_notes=row['approval_notes'],
            last_exported_at=datetime.fromisoformat(row['last_exported_at']) if row['last_exported_at'] else None,
            export_destinations=row['export_destinations']
        )
    
    def _log_geschiedenis(self, definitie_id: int, wijziging_type: str, 
                         gewijzigd_door: str = None, reden: str = None):
        """Log wijziging in geschiedenis tabel."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO definitie_geschiedenis 
                (definitie_id, wijziging_type, wijziging_reden, gewijzigd_door)
                VALUES (?, ?, ?, ?)
            """, (definitie_id, wijziging_type, reden, gewijzigd_door))
    
    def _log_import_export(self, operatie_type: str, bestand_pad: str, 
                          verwerkt: int, succesvol: int, gefaald: int):
        """Log import/export operatie."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO import_export_logs 
                (operatie_type, bron_bestemming, aantal_verwerkt, aantal_succesvol, 
                 aantal_gefaald, bestand_pad, status, voltooid_op)
                VALUES (?, ?, ?, ?, ?, ?, 'completed', ?)
            """, (operatie_type, bestand_pad, verwerkt, succesvol, gefaald, 
                  bestand_pad, datetime.now()))
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Bereken similarity score tussen twee strings."""
        # Simple similarity based on common characters
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        if str1_lower == str2_lower:
            return 1.0
        
        # Jaccard similarity
        set1 = set(str1_lower.split())
        set2 = set(str2_lower.split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0


# Convenience functions
def get_definitie_repository(db_path: str = None) -> DefinitieRepository:
    """Haal gedeelde repository instance op."""
    if not db_path:
        # Default database in project directory
        project_root = Path(__file__).parent.parent.parent
        db_path = str(project_root / "data" / "definities.db")
    
    return DefinitieRepository(db_path)