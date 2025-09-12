"""
Service layer for definition edit interface functionality.

This service orchestrates the edit operations and provides
business logic for the definition edit interface.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from services.definition_edit_repository import DefinitionEditRepository
from services.interfaces import Definition
from services.validation.modular_validation_service import ModularValidationService

logger = logging.getLogger(__name__)


class DefinitionEditService:
    """
    Service for managing definition editing operations.
    
    Provides:
    - Edit orchestration with validation
    - Version management
    - Auto-save functionality
    - Conflict resolution
    """
    
    def __init__(self, 
                 repository: DefinitionEditRepository = None,
                 validation_service: ModularValidationService = None):
        """
        Initialize the edit service.
        
        Args:
            repository: Repository for data access
            validation_service: Service for validation
        """
        self.repository = repository or DefinitionEditRepository()
        self.validation_service = validation_service
        
        # Auto-save configuration
        self.auto_save_interval = 30  # seconds
        self.auto_save_enabled = True
        
        # Cache for performance
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info("DefinitionEditService initialized")
    
    def start_edit_session(self, definitie_id: int, user: str = "system") -> Dict[str, Any]:
        """
        Start een edit sessie voor een definitie.
        
        Args:
            definitie_id: ID van de te bewerken definitie
            user: Gebruiker die edit sessie start
            
        Returns:
            Sessie informatie inclusief definitie en lock status
        """
        try:
            # Get definition
            definition = self.repository.get(definitie_id)
            if not definition:
                return {
                    'success': False,
                    'error': 'Definitie niet gevonden'
                }
            
            # Check for existing auto-save
            auto_save = self.repository.get_latest_auto_save(definitie_id)
            
            # Get version history
            history = self.repository.get_version_history(definitie_id, limit=5)
            
            return {
                'success': True,
                'definition': definition,
                'auto_save': auto_save,
                'history': history,
                'session_id': self._generate_session_id(definitie_id, user),
                'locked': False,  # Implement locking if needed
                'user': user,
                'started_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting edit session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_definition(self, 
                       definitie_id: int,
                       updates: Dict[str, Any],
                       user: str = "system",
                       reason: str = None,
                       validate: bool = True) -> Dict[str, Any]:
        """
        Sla definitie wijzigingen op.
        
        Args:
            definitie_id: ID van de definitie
            updates: Dictionary met updates
            user: Gebruiker die opslaat
            reason: Reden voor wijziging
            validate: Of validatie uitgevoerd moet worden
            
        Returns:
            Result dictionary met success status
        """
        try:
            # Get current definition
            current = self.repository.get(definitie_id)
            if not current:
                return {
                    'success': False,
                    'error': 'Definitie niet gevonden'
                }
            
            # Check version conflict
            if 'version_number' in updates:
                if self.repository.check_version_conflict(
                    definitie_id, updates['version_number']
                ):
                    return {
                        'success': False,
                        'error': 'Versie conflict - definitie is gewijzigd door andere gebruiker',
                        'conflict': True
                    }
            
            # Apply updates
            updated_definition = self._apply_updates(current, updates)
            
            # Validate if requested
            validation_results = None
            if validate and self.validation_service:
                validation_results = self._validate_definition(updated_definition)
                if validation_results and not validation_results.get('valid', True):
                    # Still save but mark validation issues
                    if not updated_definition.metadata:
                        updated_definition.metadata = {}
                    updated_definition.metadata['validation_issues'] = validation_results.get('issues', [])
            
            # Save with history
            saved_id = self.repository.save_with_history(
                updated_definition,
                wijziging_reden=reason,
                gewijzigd_door=user
            )
            
            # Clear cache
            self._clear_cache(definitie_id)
            
            return {
                'success': True,
                'definition_id': saved_id,
                'validation': validation_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error saving definition: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def auto_save(self, definitie_id: int, content: Dict[str, Any]) -> bool:
        """
        Auto-save draft versie.
        
        Args:
            definitie_id: ID van de definitie
            content: Content om op te slaan
            
        Returns:
            True als succesvol
        """
        if not self.auto_save_enabled:
            return False
        
        try:
            # Add timestamp
            content['auto_save_timestamp'] = datetime.now().isoformat()
            
            # Save draft
            return self.repository.auto_save_draft(definitie_id, content)
            
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            return False
    
    def restore_auto_save(self, definitie_id: int) -> Optional[Dict[str, Any]]:
        """
        Herstel auto-save content.
        
        Args:
            definitie_id: ID van de definitie
            
        Returns:
            Auto-save content indien beschikbaar
        """
        try:
            return self.repository.get_latest_auto_save(definitie_id)
        except Exception as e:
            logger.error(f"Error restoring auto-save: {e}")
            return None
    
    def get_version_history(self, definitie_id: int, 
                           limit: int = 20) -> List[Dict[str, Any]]:
        """
        Haal versie geschiedenis op.
        
        Args:
            definitie_id: ID van de definitie
            limit: Maximum aantal versies
            
        Returns:
            Lijst met versie geschiedenis
        """
        try:
            # Check cache
            cache_key = f"history_{definitie_id}_{limit}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                    return cached_data
            
            # Get from repository
            history = self.repository.get_version_history(definitie_id, limit)
            
            # Process history entries
            for entry in history:
                # Add human-readable timestamp
                if 'gewijzigd_op' in entry:
                    entry['gewijzigd_op_readable'] = self._format_timestamp(
                        entry['gewijzigd_op']
                    )
                
                # Add change summary
                entry['summary'] = self._generate_change_summary(entry)
            
            # Cache result
            self._cache[cache_key] = (history, datetime.now())
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting version history: {e}")
            return []
    
    def revert_to_version(self, definitie_id: int, version_id: int, 
                         user: str = "system") -> Dict[str, Any]:
        """
        Revert definitie naar eerdere versie.
        
        Args:
            definitie_id: ID van de definitie
            version_id: ID van de versie om naar te reverten
            user: Gebruiker die revert uitvoert
            
        Returns:
            Result dictionary
        """
        try:
            # Get version from history
            history = self.repository.get_version_history(definitie_id, limit=100)
            
            version_entry = None
            for entry in history:
                if entry.get('id') == version_id:
                    version_entry = entry
                    break
            
            if not version_entry:
                return {
                    'success': False,
                    'error': 'Versie niet gevonden'
                }
            
            # Get current definition
            current = self.repository.get(definitie_id)
            if not current:
                return {
                    'success': False,
                    'error': 'Definitie niet gevonden'
                }
            
            # Apply value from selected version (prefer new value of that entry)
            if version_entry.get('definitie_nieuwe_waarde'):
                current.definitie = version_entry['definitie_nieuwe_waarde']
            elif version_entry.get('definitie_oude_waarde'):
                current.definitie = version_entry['definitie_oude_waarde']
            
            # Apply context if available
            if version_entry.get('context_snapshot'):
                context = version_entry['context_snapshot']
                if isinstance(context, dict):
                    if 'organisatorische_context' in context:
                        current.context = context['organisatorische_context']
                    if 'juridische_context' in context:
                        if not current.metadata:
                            current.metadata = {}
                        current.metadata['juridische_context'] = context['juridische_context']
            
            # Save as new version
            return self.save_definition(
                definitie_id,
                self._definition_to_dict(current),
                user=user,
                reason=f"Reverted naar versie {version_id}"
            )
            
        except Exception as e:
            logger.error(f"Error reverting to version: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_update(self, updates: List[Tuple[int, Dict[str, Any]]],
                    user: str = "system") -> Dict[str, Any]:
        """
        Update meerdere definities tegelijk.
        
        Args:
            updates: Lijst van (definitie_id, update_dict) tuples
            user: Gebruiker die update uitvoert
            
        Returns:
            Result dictionary met successen en fouten
        """
        results = {
            'success': [],
            'failed': [],
            'total': len(updates)
        }
        
        for definitie_id, update_dict in updates:
            try:
                result = self.save_definition(
                    definitie_id,
                    update_dict,
                    user=user,
                    validate=False  # Skip validation for batch
                )
                
                if result['success']:
                    results['success'].append(definitie_id)
                else:
                    results['failed'].append({
                        'id': definitie_id,
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                results['failed'].append({
                    'id': definitie_id,
                    'error': str(e)
                })
        
        return results
    
    def search_and_replace(self, search_term: str, replace_term: str,
                          field: str = 'definitie',
                          filters: Dict[str, Any] = None,
                          user: str = "system") -> Dict[str, Any]:
        """
        Zoek en vervang in meerdere definities.
        
        Args:
            search_term: Te zoeken term
            replace_term: Vervangende term
            field: Veld om in te zoeken (definitie, begrip, etc.)
            filters: Extra filters voor zoeken
            user: Gebruiker die operatie uitvoert
            
        Returns:
            Result dictionary
        """
        try:
            # Search definitions
            definitions = self.repository.search_with_filters(
                search_term=search_term,
                **filters if filters else {}
            )
            
            updates = []
            for definition in definitions:
                # Check if field contains search term
                field_value = getattr(definition, field, None)
                if field_value and search_term in field_value:
                    # Prepare update
                    new_value = field_value.replace(search_term, replace_term)
                    updates.append((
                        definition.id,
                        {field: new_value}
                    ))
            
            # Execute batch update
            if updates:
                return self.batch_update(updates, user=user)
            
            return {
                'success': [],
                'failed': [],
                'total': 0,
                'message': 'Geen definities gevonden om te updaten'
            }
            
        except Exception as e:
            logger.error(f"Error in search and replace: {e}")
            return {
                'success': [],
                'failed': [],
                'error': str(e)
            }
    
    def _apply_updates(self, definition: Definition, 
                      updates: Dict[str, Any]) -> Definition:
        """Apply updates to definition object."""
        # Create copy
        updated = Definition(
            id=definition.id,
            begrip=updates.get('begrip', definition.begrip),
            definitie=updates.get('definitie', definition.definitie),
            toelichting=updates.get('toelichting', definition.toelichting),
            bron=updates.get('bron', definition.bron),
            context=updates.get('context', definition.context),
            categorie=updates.get('categorie', definition.categorie),
            created_at=definition.created_at,
            updated_at=datetime.now(),
            metadata=definition.metadata or {}
        )
        
        # Update metadata fields
        metadata_fields = ['status', 'juridische_context', 'wettelijke_basis',
                          'validation_score', 'version_number']
        for field in metadata_fields:
            if field in updates:
                updated.metadata[field] = updates[field]
        
        return updated
    
    def _validate_definition(self, definition: Definition) -> Dict[str, Any]:
        """Validate definition using injected validation service (sync/async compatible)."""
        if not self.validation_service:
            return None

        try:
            import inspect
            import asyncio

            vs = self.validation_service

            # Prefer validate_text if available (ValidationOrchestratorV2)
            def _run_async(coro):
                import asyncio, threading
                try:
                    return asyncio.run(coro)
                except RuntimeError:
                    # Fallback: run coroutine in a separate thread with its own loop
                    holder = {}
                    err = {}
                    def _runner():
                        try:
                            holder['v'] = asyncio.run(coro)
                        except Exception as e:  # pragma: no cover
                            err['e'] = e
                    t = threading.Thread(target=_runner, daemon=True)
                    t.start(); t.join()
                    if 'e' in err:
                        raise err['e']
                    return holder.get('v')

            if hasattr(vs, 'validate_text'):
                coro = vs.validate_text(
                    begrip=definition.begrip,
                    text=definition.definitie,
                    ontologische_categorie=getattr(definition, 'ontologische_categorie', None) or definition.categorie,
                    context=None,
                )
                results = _run_async(coro) if inspect.isawaitable(coro) else coro
            else:
                # Try generic validate_definition
                maybe = None
                # Try Definition object signature first
                try:
                    maybe = vs.validate_definition(definition)
                except TypeError:
                    # Fallback to parameterized signature
                    maybe = vs.validate_definition(
                        definition.begrip,
                        definition.definitie,
                        definition.context or '',
                        definition.metadata.get('juridische_context', '') if definition.metadata else '',
                        definition.categorie or 'proces',
                    )

                results = None
                if inspect.isawaitable(maybe):
                    results = _run_async(maybe)
                else:
                    results = maybe

            # Normalize result to UI format
            # Case 1: dict schema (ModularValidationService/Orchestrator ensure_schema)
            if isinstance(results, dict):
                violations = results.get('violations', []) or []
                normalized_issues = []
                for v in violations:
                    rule = v.get('rule_id') or v.get('code')
                    message = v.get('description') or v.get('message', '')
                    severity = v.get('severity', 'warning')
                    normalized_issues.append({'rule': rule, 'message': message, 'severity': severity})
                return {
                    'valid': bool(results.get('is_acceptable', False)),
                    'score': float(results.get('overall_score', 0.0) or 0.0),
                    'issues': normalized_issues,
                }

            # Case 2: legacy object with attributes
            if hasattr(results, 'overall_status') or hasattr(results, 'validation_score'):
                issues_attr = getattr(results, 'issues', []) or []
                normalized_issues = []
                for issue in issues_attr:
                    try:
                        normalized_issues.append(
                            {
                                'rule': getattr(issue, 'regel_code', None) or getattr(issue, 'rule', None),
                                'message': getattr(issue, 'message', ''),
                                'severity': getattr(issue, 'severity', 'warning'),
                            }
                        )
                    except Exception:
                        pass
                return {
                    'valid': getattr(results, 'overall_status', '') == 'success',
                    'score': getattr(results, 'validation_score', 0.0) or 0.0,
                    'issues': normalized_issues,
                }

            # Unknown format
            return None

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return None
    
    def _generate_session_id(self, definitie_id: int, user: str) -> str:
        """Generate unique session ID."""
        import hashlib
        timestamp = datetime.now().isoformat()
        data = f"{definitie_id}_{user}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _format_timestamp(self, timestamp) -> str:
        """Format timestamp for display."""
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                return timestamp
        
        if isinstance(timestamp, datetime):
            delta = datetime.now() - timestamp
            if delta.days > 7:
                return timestamp.strftime("%d-%m-%Y %H:%M")
            elif delta.days > 0:
                return f"{delta.days} dagen geleden"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} uur geleden"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minuten geleden"
            else:
                return "Zojuist"
        
        return str(timestamp)
    
    def _generate_change_summary(self, entry: Dict[str, Any]) -> str:
        """Generate human-readable change summary."""
        wijziging_type = entry.get('wijziging_type', '')
        gewijzigd_door = entry.get('gewijzigd_door', 'Onbekend')
        
        summaries = {
            'created': f"Aangemaakt door {gewijzigd_door}",
            'updated': f"Bewerkt door {gewijzigd_door}",
            'status_changed': f"Status gewijzigd door {gewijzigd_door}",
            'approved': f"Goedgekeurd door {gewijzigd_door}",
            'archived': f"Gearchiveerd door {gewijzigd_door}",
            'auto_save': "Auto-save",
        }
        
        return summaries.get(wijziging_type, f"Gewijzigd door {gewijzigd_door}")
    
    def _definition_to_dict(self, definition: Definition) -> Dict[str, Any]:
        """Convert Definition to dictionary."""
        return {
            'begrip': definition.begrip,
            'definitie': definition.definitie,
            'toelichting': definition.toelichting,
            'bron': definition.bron,
            'context': definition.context,
            'categorie': definition.categorie,
            **(definition.metadata if definition.metadata else {})
        }
    
    def _clear_cache(self, definitie_id: int = None) -> None:
        """Clear cache entries."""
        if definitie_id:
            # Clear specific definition cache
            keys_to_remove = [k for k in self._cache.keys() 
                            if str(definitie_id) in k]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear all cache
            self._cache.clear()
