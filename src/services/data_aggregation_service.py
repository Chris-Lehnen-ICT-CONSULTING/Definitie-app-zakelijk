"""
Data Aggregation Service.

Centralized service voor het verzamelen en aggregeren van data voor export en andere doeleinden.
Dit elimineert de directe afhankelijkheid van services op UI session state.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from database.definitie_repository import DefinitieRecord, DefinitieRepository

logger = logging.getLogger(__name__)


@dataclass
class CategoryChangeState:
    """State container voor category change regeneration preview."""
    
    # Category change info
    old_category: str
    new_category: str
    begrip: str
    current_definition: str
    
    # Impact analysis
    impact_analysis: list[str] = field(default_factory=list)
    
    # UI state
    show_regeneration_preview: bool = False
    saved_record_id: Optional[int] = None
    
    # Workflow data
    requires_regeneration: bool = True
    success_message: str = ""


@dataclass
class DefinitieExportData:
    """Data container voor definitie export."""
    
    # Core definitie data
    begrip: str
    definitie_origineel: str
    definitie_gecorrigeerd: str
    definitie_aangepast: Optional[str] = None
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Context informatie
    context_dict: dict[str, list[str]] = field(default_factory=dict)
    
    # Toetsing en beoordeling
    toetsresultaten: dict[str, Any] = field(default_factory=dict)
    beoordeling: list[str] = field(default_factory=list)
    beoordeling_gen: list[str] = field(default_factory=list)
    
    # Voorbeelden en uitleg
    voorbeeld_zinnen: list[str] = field(default_factory=list)
    praktijkvoorbeelden: list[str] = field(default_factory=list)
    tegenvoorbeelden: list[str] = field(default_factory=list)
    toelichting: str = ""
    
    # Taalkundige informatie
    synoniemen: str = ""
    antoniemen: str = ""
    voorkeursterm: str = ""
    
    # Bronnen en validatie
    bronnen: list[str] = field(default_factory=list)
    bronnen_gebruikt: str = ""
    
    # Expert review
    expert_review: str = ""
    
    # Technische metadata
    marker: Optional[str] = None
    prompt_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DataAggregationService:
    """
    Service voor het aggregeren van data uit verschillende bronnen.
    
    Deze service haalt data op uit:
    - Database (DefinitieRepository)
    - Business services (WorkflowService, CategoryService, etc.)
    - Domain models
    
    Zonder directe afhankelijkheid van UI session state.
    """
    
    def __init__(self, repository: DefinitieRepository):
        """Initialiseer data aggregation service."""
        self.repository = repository
        logger.info("DataAggregationService geïnitialiseerd")
    
    def aggregate_definitie_for_export(
        self,
        definitie_id: Optional[int] = None,
        definitie_record: Optional[DefinitieRecord] = None,
        additional_data: Optional[dict[str, Any]] = None
    ) -> DefinitieExportData:
        """
        Aggregeer alle data voor een definitie export.
        
        Args:
            definitie_id: ID van definitie om te exporteren
            definitie_record: Bestaande definitie record (optioneel)
            additional_data: Extra data om toe te voegen
            
        Returns:
            DefinitieExportData object met alle benodigde data
        """
        # Haal definitie record op indien nodig
        if definitie_record is None and definitie_id is not None:
            definitie_record = self.repository.get_definitie(definitie_id)
            if not definitie_record:
                raise ValueError(f"Definitie met ID {definitie_id} niet gevonden")
        
        # Basis export data
        export_data = DefinitieExportData(
            begrip=definitie_record.begrip if definitie_record else "",
            definitie_origineel=definitie_record.definitie if definitie_record else "",
            definitie_gecorrigeerd=definitie_record.definitie if definitie_record else "",
        )
        
        # Vul metadata
        if definitie_record:
            export_data.metadata = {
                "id": definitie_record.id,
                "status": definitie_record.status,
                "versie": definitie_record.versie,
                "categorie": definitie_record.categorie,
                "domein": definitie_record.domein,
                "datum_voorstel": definitie_record.created_at,
                "voorsteller": definitie_record.created_by or "Systeem",
            }
            
            # Context uit definitie record
            if definitie_record.context:
                export_data.context_dict = definitie_record.context
            
            # Timestamps
            export_data.created_at = definitie_record.created_at
            export_data.updated_at = definitie_record.updated_at
        
        # Merge met additional data indien aanwezig
        if additional_data:
            self._merge_additional_data(export_data, additional_data)
        
        logger.debug(f"Geaggregeerde export data voor begrip '{export_data.begrip}'")
        return export_data
    
    def _merge_additional_data(
        self,
        export_data: DefinitieExportData,
        additional_data: dict[str, Any]
    ) -> None:
        """Merge additionele data in export data object."""
        # Direct mappings
        direct_fields = [
            "definitie_aangepast", "toelichting", "synoniemen", 
            "antoniemen", "voorkeursterm", "bronnen_gebruikt",
            "expert_review", "marker", "prompt_text"
        ]
        
        for field in direct_fields:
            if field in additional_data:
                setattr(export_data, field, additional_data[field])
        
        # List fields
        list_fields = [
            "voorbeeld_zinnen", "praktijkvoorbeelden", 
            "tegenvoorbeelden", "bronnen", "beoordeling", "beoordeling_gen"
        ]
        
        for field in list_fields:
            if field in additional_data:
                value = additional_data[field]
                if isinstance(value, list):
                    setattr(export_data, field, value)
        
        # Dict fields
        if "toetsresultaten" in additional_data:
            export_data.toetsresultaten = additional_data["toetsresultaten"]
        
        if "context_dict" in additional_data:
            export_data.context_dict.update(additional_data["context_dict"])
        
        if "metadata" in additional_data:
            export_data.metadata.update(additional_data["metadata"])
        
        # Ketenpartners (special handling)
        if "ketenpartners" in additional_data:
            export_data.metadata["ketenpartners"] = additional_data["ketenpartners"]
    
    def prepare_export_dict(self, export_data: DefinitieExportData) -> dict[str, Any]:
        """
        Bereid export data voor in dictionary formaat voor legacy export functies.
        
        Args:
            export_data: DefinitieExportData object
            
        Returns:
            Dictionary compatible met legacy export functies
        """
        return {
            "begrip": export_data.begrip,
            "definitie_origineel": export_data.definitie_origineel,
            "definitie_gecorrigeerd": export_data.definitie_gecorrigeerd,
            "definitie_aangepast": export_data.definitie_aangepast,
            "metadata": export_data.metadata,
            "context_dict": export_data.context_dict,
            "toetsresultaten": export_data.toetsresultaten,
            "beoordeling": export_data.beoordeling,
            "beoordeling_gen": export_data.beoordeling_gen,
            "voorbeeld_zinnen": export_data.voorbeeld_zinnen,
            "praktijkvoorbeelden": export_data.praktijkvoorbeelden,
            "tegenvoorbeelden": export_data.tegenvoorbeelden,
            "toelichting": export_data.toelichting,
            "synoniemen": export_data.synoniemen,
            "antoniemen": export_data.antoniemen,
            "voorkeursterm": export_data.voorkeursterm,
            "bronnen": export_data.bronnen,
            "bronnen_gebruikt": export_data.bronnen_gebruikt,
            "expert_review": export_data.expert_review,
            "marker": export_data.marker,
            "prompt_text": export_data.prompt_text,
        }
    
    def aggregate_from_generation_result(
        self,
        generation_result: dict[str, Any],
        context_dict: Optional[dict[str, list[str]]] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> DefinitieExportData:
        """
        Aggregeer data vanuit een generatie resultaat.
        
        Args:
            generation_result: Resultaat van definitie generatie
            context_dict: Context informatie
            metadata: Extra metadata
            
        Returns:
            DefinitieExportData object
        """
        export_data = DefinitieExportData(
            begrip=generation_result.get("begrip", ""),
            definitie_origineel=generation_result.get("definitie", ""),
            definitie_gecorrigeerd=generation_result.get("definitie_gecorrigeerd", 
                                                       generation_result.get("definitie", "")),
        )
        
        # Vul vanuit generation result
        if "voorbeeld_zinnen" in generation_result:
            export_data.voorbeeld_zinnen = generation_result["voorbeeld_zinnen"]
        
        if "praktijkvoorbeelden" in generation_result:
            export_data.praktijkvoorbeelden = generation_result["praktijkvoorbeelden"]
        
        if "tegenvoorbeelden" in generation_result:
            export_data.tegenvoorbeelden = generation_result["tegenvoorbeelden"]
        
        if "toelichting" in generation_result:
            export_data.toelichting = generation_result["toelichting"]
        
        if "synoniemen" in generation_result:
            export_data.synoniemen = generation_result["synoniemen"]
        
        if "antoniemen" in generation_result:
            export_data.antoniemen = generation_result["antoniemen"]
        
        if "bronnen" in generation_result:
            export_data.bronnen = generation_result["bronnen"]
        
        if "toetsresultaten" in generation_result:
            export_data.toetsresultaten = generation_result["toetsresultaten"]
        
        if "marker" in generation_result:
            export_data.marker = generation_result["marker"]
        
        # Context en metadata
        if context_dict:
            export_data.context_dict = context_dict
        
        if metadata:
            export_data.metadata = metadata
        
        # Timestamps
        export_data.created_at = datetime.now()
        
        return export_data
    
    def create_category_change_state(
        self,
        old_category: str,
        new_category: str,
        begrip: str,
        current_definition: str,
        impact_analysis: list[str],
        saved_record_id: Optional[int] = None,
        success_message: str = ""
    ) -> CategoryChangeState:
        """
        Creëer category change state voor UI rendering.
        
        Args:
            old_category: Oude categorie
            new_category: Nieuwe categorie  
            begrip: Het begrip
            current_definition: Huidige definitie
            impact_analysis: Impact analyse van de wijziging
            saved_record_id: ID van opgeslagen record (optioneel)
            success_message: Success bericht
            
        Returns:
            CategoryChangeState object voor UI
        """
        return CategoryChangeState(
            old_category=old_category,
            new_category=new_category,
            begrip=begrip,
            current_definition=current_definition,
            impact_analysis=impact_analysis,
            show_regeneration_preview=True,
            saved_record_id=saved_record_id,
            success_message=success_message
        )