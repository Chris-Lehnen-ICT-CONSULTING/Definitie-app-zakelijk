"""
DefinitieChecker - Integreert duplicate detection met DefinitieAgent.
Voorkomt dubbele generatie door bestaande definities te checken.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from database.definitie_repository import (
    DefinitieRepository, get_definitie_repository, 
    DefinitieRecord, DefinitieStatus, DuplicateMatch, SourceType
)
from generation.definitie_generator import GenerationContext, OntologischeCategorie
from validation.definitie_validator import ValidationResult
from orchestration.definitie_agent import DefinitieAgent, AgentResult

logger = logging.getLogger(__name__)


class CheckAction(Enum):
    """Actie die ondernomen moet worden na duplicate check."""
    PROCEED = "proceed"           # Ga door met generatie
    USE_EXISTING = "use_existing" # Gebruik bestaande definitie
    UPDATE_EXISTING = "update"    # Update bestaande definitie
    USER_CHOICE = "user_choice"   # Laat gebruiker kiezen


@dataclass
class DefinitieCheckResult:
    """Resultaat van duplicate check."""
    action: CheckAction
    existing_definitie: Optional[DefinitieRecord] = None
    duplicates: List[DuplicateMatch] = None
    message: str = ""
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.duplicates is None:
            self.duplicates = []


class DefinitieChecker:
    """
    Integreert duplicate detection met definitie generatie workflow.
    Checkt bestaande definities voordat nieuwe worden gegenereerd.
    """
    
    def __init__(self, repository: DefinitieRepository = None):
        """
        Initialiseer checker met repository.
        
        Args:
            repository: DefinitieRepository instance, gebruikt default als None
        """
        self.repository = repository or get_definitie_repository()
        self.agent = DefinitieAgent()
    
    def check_before_generation(
        self, 
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: OntologischeCategorie = OntologischeCategorie.TYPE
    ) -> DefinitieCheckResult:
        """
        Check voor bestaande definities voordat generatie start.
        
        Args:
            begrip: Het begrip om te checken
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            categorie: Ontologische categorie
            
        Returns:
            DefinitieCheckResult met aanbevolen actie
        """
        logger.info(f"Checking for existing definitions of '{begrip}' in context {organisatorische_context}")
        
        # Zoek exact match
        existing = self.repository.find_definitie(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context
        )
        
        if existing:
            return self._handle_exact_match(existing)
        
        # Zoek duplicates/fuzzy matches
        duplicates = self.repository.find_duplicates(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context
        )
        
        if duplicates:
            return self._handle_duplicates(duplicates)
        
        # Geen duplicates gevonden - ga door met generatie
        return DefinitieCheckResult(
            action=CheckAction.PROCEED,
            message=f"Geen bestaande definitie gevonden voor '{begrip}'. Generatie kan doorgaan.",
            confidence=1.0
        )
    
    def generate_with_check(
        self,
        begrip: str,
        organisatorische_context: str,
        juridische_context: str = "",
        categorie: OntologischeCategorie = OntologischeCategorie.TYPE,
        force_generate: bool = False,
        created_by: str = None
    ) -> Tuple[DefinitieCheckResult, Optional[AgentResult], Optional[DefinitieRecord]]:
        """
        Voer complete workflow uit: check + eventuele generatie + opslag.
        
        Args:
            begrip: Het begrip om te definiëren
            organisatorische_context: Organisatorische context
            juridische_context: Juridische context
            categorie: Ontologische categorie
            force_generate: Forceer nieuwe generatie ondanks duplicates
            created_by: Wie de definitie aanmaakt
            
        Returns:
            Tuple van (check_result, agent_result, saved_record)
        """
        # Stap 1: Check voor duplicates
        check_result = self.check_before_generation(
            begrip, organisatorische_context, juridische_context, categorie
        )
        
        # Stap 2: Bepaal actie
        if not force_generate and check_result.action != CheckAction.PROCEED:
            # Return bestaande definitie zonder nieuwe generatie
            return check_result, None, check_result.existing_definitie
        
        # Stap 3: Genereer nieuwe definitie
        logger.info(f"Generating new definition for '{begrip}'")
        
        agent_result = self.agent.generate_definition(
            begrip=begrip,
            organisatorische_context=organisatorische_context,
            juridische_context=juridische_context,
            categorie=categorie
        )
        
        # Stap 4: Sla definitie op in database
        if agent_result.success:
            saved_record = self._save_generated_definition(
                agent_result, categorie, created_by
            )
            
            return check_result, agent_result, saved_record
        else:
            logger.warning(f"Failed to generate definition for '{begrip}': {agent_result.reason}")
            return check_result, agent_result, None
    
    def update_existing_definition(
        self,
        definitie_id: int,
        updated_by: str = None,
        regenerate: bool = False
    ) -> Tuple[bool, Optional[AgentResult]]:
        """
        Update bestaande definitie, optioneel met regeneratie.
        
        Args:
            definitie_id: ID van definitie om te updaten
            updated_by: Wie de update uitvoert
            regenerate: Of definitie opnieuw gegenereerd moet worden
            
        Returns:
            Tuple van (success, agent_result)
        """
        existing = self.repository.get_definitie(definitie_id)
        if not existing:
            return False, None
        
        if not regenerate:
            # Simple metadata update
            success = self.repository.update_definitie(
                definitie_id, 
                {"updated_by": updated_by}, 
                updated_by
            )
            return success, None
        
        # Regenerate definitie
        categorie = OntologischeCategorie(existing.categorie)
        
        agent_result = self.agent.generate_definition(
            begrip=existing.begrip,
            organisatorische_context=existing.organisatorische_context,
            juridische_context=existing.juridische_context or "",
            categorie=categorie
        )
        
        if agent_result.success:
            # Update with new definition
            updates = {
                "definitie": agent_result.final_definitie,
                "validation_score": agent_result.final_score,
                "version_number": existing.version_number + 1,
                "previous_version_id": definitie_id
            }
            
            success = self.repository.update_definitie(definitie_id, updates, updated_by)
            return success, agent_result
        
        return False, agent_result
    
    def approve_definition(
        self, 
        definitie_id: int, 
        approved_by: str,
        notes: str = None
    ) -> bool:
        """
        Keur definitie goed (zet status op ESTABLISHED).
        
        Args:
            definitie_id: ID van definitie
            approved_by: Wie de definitie goedkeurt
            notes: Optionele goedkeuringsnotities
            
        Returns:
            True als succesvol goedgekeurd
        """
        return self.repository.change_status(
            definitie_id, 
            DefinitieStatus.ESTABLISHED, 
            approved_by, 
            notes
        )
    
    def get_pending_definitions(self) -> List[DefinitieRecord]:
        """Haal definities op die wachten op goedkeuring."""
        return self.repository.search_definities(status=DefinitieStatus.REVIEW)
    
    def get_established_definitions(
        self, 
        organisatorische_context: str = None
    ) -> List[DefinitieRecord]:
        """Haal vastgestelde definities op."""
        return self.repository.search_definities(
            status=DefinitieStatus.ESTABLISHED,
            organisatorische_context=organisatorische_context
        )
    
    def export_established_definitions(
        self, 
        file_path: str,
        organisatorische_context: str = None
    ) -> int:
        """
        Exporteer vastgestelde definities naar bestand.
        
        Args:
            file_path: Pad voor export bestand
            organisatorische_context: Optionele filter op organisatie
            
        Returns:
            Aantal geëxporteerde definities
        """
        filters = {"status": DefinitieStatus.ESTABLISHED}
        if organisatorische_context:
            filters["organisatorische_context"] = organisatorische_context
        
        return self.repository.export_to_json(file_path, filters)
    
    def import_external_definitions(
        self, 
        file_path: str,
        import_by: str = None
    ) -> Tuple[int, int, List[str]]:
        """
        Importeer definities uit extern bestand.
        
        Args:
            file_path: Pad naar import bestand
            import_by: Wie de import uitvoert
            
        Returns:
            Tuple van (succesvol, gefaald, errors)
        """
        return self.repository.import_from_json(file_path, import_by)
    
    def _handle_exact_match(self, existing: DefinitieRecord) -> DefinitieCheckResult:
        """Behandel exact match scenario."""
        if existing.status == DefinitieStatus.ESTABLISHED.value:
            return DefinitieCheckResult(
                action=CheckAction.USE_EXISTING,
                existing_definitie=existing,
                message=f"Vastgestelde definitie bestaat al voor '{existing.begrip}' (ID: {existing.id})",
                confidence=1.0
            )
        elif existing.status == DefinitieStatus.DRAFT.value:
            return DefinitieCheckResult(
                action=CheckAction.UPDATE_EXISTING,
                existing_definitie=existing,
                message=f"Draft definitie bestaat voor '{existing.begrip}' (ID: {existing.id}). Overweeg update.",
                confidence=1.0
            )
        else:
            return DefinitieCheckResult(
                action=CheckAction.USER_CHOICE,
                existing_definitie=existing,
                message=f"Definitie in status '{existing.status}' bestaat voor '{existing.begrip}' (ID: {existing.id})",
                confidence=0.8
            )
    
    def _handle_duplicates(self, duplicates: List[DuplicateMatch]) -> DefinitieCheckResult:
        """Behandel fuzzy duplicates scenario."""
        best_match = duplicates[0]  # Highest score first
        
        if best_match.match_score > 0.9:
            return DefinitieCheckResult(
                action=CheckAction.USER_CHOICE,
                existing_definitie=best_match.definitie_record,
                duplicates=duplicates,
                message=f"Zeer vergelijkbare definitie gevonden: '{best_match.definitie_record.begrip}' (score: {best_match.match_score:.2f})",
                confidence=best_match.match_score
            )
        elif best_match.match_score > 0.7:
            return DefinitieCheckResult(
                action=CheckAction.USER_CHOICE,
                duplicates=duplicates,
                message=f"Mogelijke duplicaten gevonden (beste match: {best_match.match_score:.2f})",
                confidence=best_match.match_score
            )
        else:
            return DefinitieCheckResult(
                action=CheckAction.PROCEED,
                duplicates=duplicates,
                message=f"Zwakke overeenkomsten gevonden, maar generatie kan doorgaan",
                confidence=1.0 - best_match.match_score
            )
    
    def _save_generated_definition(
        self, 
        agent_result: AgentResult, 
        categorie: OntologischeCategorie,
        created_by: str = None
    ) -> DefinitieRecord:
        """Sla gegenereerde definitie op in database."""
        # Extract context from first iteration
        if agent_result.iterations:
            first_iteration = agent_result.iterations[0]
            context = first_iteration.generation_result.context
            
            # Create record
            record = DefinitieRecord(
                begrip=context.begrip,
                definitie=agent_result.final_definitie,
                categorie=categorie.value,
                organisatorische_context=context.organisatorische_context,
                juridische_context=context.juridische_context,
                status=DefinitieStatus.REVIEW.value,  # Start in review
                validation_score=agent_result.final_score,
                source_type=SourceType.GENERATED.value,
                source_reference=f"DefinitieAgent v{agent_result.iteration_count} iterations",
                created_by=created_by or "system"
            )
            
            # Add validation issues if any
            if agent_result.best_iteration and agent_result.best_iteration.validation_result.violations:
                issues = [
                    {
                        "rule_id": v.rule_id,
                        "severity": v.severity.value,
                        "description": v.description
                    }
                    for v in agent_result.best_iteration.validation_result.violations
                ]
                record.set_validation_issues(issues)
            
            # Save to database
            record_id = self.repository.create_definitie(record)
            record.id = record_id
            
            logger.info(f"Saved generated definition {record_id} for '{context.begrip}'")
            return record
        
        raise ValueError("No iterations found in agent result")


# Convenience functions
def check_existing_definition(
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: str = "type"
) -> DefinitieCheckResult:
    """
    Convenience functie voor snelle duplicate check.
    
    Args:
        begrip: Het begrip om te checken
        organisatorische_context: Organisatorische context
        juridische_context: Juridische context
        categorie: Ontologische categorie string
        
    Returns:
        DefinitieCheckResult
    """
    checker = DefinitieChecker()
    cat_enum = OntologischeCategorie(categorie)
    
    return checker.check_before_generation(
        begrip, organisatorische_context, juridische_context, cat_enum
    )


def generate_or_retrieve_definition(
    begrip: str,
    organisatorische_context: str,
    juridische_context: str = "",
    categorie: str = "type",
    force_new: bool = False,
    created_by: str = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Convenience functie voor complete workflow: check + genereer + opslag.
    
    Args:
        begrip: Het begrip
        organisatorische_context: Organisatorische context
        juridische_context: Juridische context
        categorie: Ontologische categorie string
        force_new: Forceer nieuwe generatie
        created_by: Wie de definitie aanmaakt
        
    Returns:
        Tuple van (definitie_text, metadata_dict)
    """
    checker = DefinitieChecker()
    cat_enum = OntologischeCategorie(categorie)
    
    check_result, agent_result, saved_record = checker.generate_with_check(
        begrip, organisatorische_context, juridische_context, 
        cat_enum, force_new, created_by
    )
    
    if saved_record:
        return saved_record.definitie, {
            "id": saved_record.id,
            "status": saved_record.status,
            "validation_score": saved_record.validation_score,
            "source": "generated",
            "check_action": check_result.action.value
        }
    elif check_result.existing_definitie:
        return check_result.existing_definitie.definitie, {
            "id": check_result.existing_definitie.id,
            "status": check_result.existing_definitie.status,
            "validation_score": check_result.existing_definitie.validation_score,
            "source": "existing",
            "check_action": check_result.action.value
        }
    else:
        return "Definitie kon niet worden gegenereerd", {
            "source": "failed",
            "check_action": check_result.action.value,
            "error": agent_result.reason if agent_result else "Unknown error"
        }