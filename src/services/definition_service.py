"""
Definition processing service for DefinitieAgent.
Handles the complete definition generation and validation workflow.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from utils.exceptions import (
    handle_api_error, handle_validation_error, 
    APIError, ValidationError, safe_execute
)
from ui.session_state import SessionStateManager
from definitie_generator.generator import genereer_definitie
from prompt_builder.prompt_builder import stuur_prompt_naar_gpt, PromptBouwer, PromptConfiguratie
from ai_toetser import toets_definitie
from opschoning.opschoning import opschonen
# Use cached versions for better performance
from voorbeelden.cached_voorbeelden import (
    genereer_voorbeeld_zinnen,
    genereer_praktijkvoorbeelden,
    genereer_tegenvoorbeelden,
    genereer_synoniemen,
    genereer_antoniemen,
    genereer_toelichting
)
import sys
import os
# Voeg root directory toe aan Python path voor logs module toegang
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from logs.application.log_definitie import log_definitie  # Logging functie uit root logs directory


class DefinitionService:
    """Service klasse voor definitie verwerkingsoperaties.
    
    Deze service laag beheert de complete workflow voor definitie generatie,
    validatie en aanvullende content generatie.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @handle_api_error
    def generate_definition(self, begrip: str, context_dict: Dict[str, List[str]]) -> Tuple[str, str, str]:
        """
        Genereer definitie met behulp van AI.
        
        Args:
            begrip: Te definiëren begrip
            context_dict: Context informatie voor generatie
            
        Returns:
            Tuple van (originele_definitie, opgeschoonde_definitie, marker)
            
        Raises:
            APIError: Als AI generatie mislukt
        """
        if not begrip.strip():
            raise ValidationError("Begrip mag niet leeg zijn")
        
        try:
            # Generate full GPT response
            raw_response = genereer_definitie(begrip, context_dict)
            
            # Parse metadata marker and pure definition text
            marker = None
            regels = raw_response.splitlines()
            tekstregels = []
            
            # Loop door alle regels en extraheer metadata
            for regel in regels:
                if regel.lower().startswith("ontologische categorie:"):
                    # Extraheer ontologische categorie marker
                    marker = regel.split(":", 1)[1].strip()
                else:
                    # Voeg gewone tekst regels toe aan definitie
                    tekstregels.append(regel)
            
            definitie_origineel = "\n".join(tekstregels).strip()
            
            # Clean the definition
            definitie_gecorrigeerd = opschonen(definitie_origineel, begrip)
            
            return definitie_origineel, definitie_gecorrigeerd, marker or ""
            
        except Exception as e:
            self.logger.error(f"Definition generation failed: {str(e)}")
            raise APIError(f"Definitie generatie mislukt: {str(e)}")
    
    @handle_api_error
    def generate_sources(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """
        Genereer broninformatie met behulp van AI.
        
        Args:
            begrip: Begrip waarvoor bronnen gezocht worden
            context_dict: Context informatie voor bronnen
            
        Returns:
            Bronnen tekst met relevante wetgeving en richtlijnen
            
        Raises:
            APIError: Als bronnen generatie mislukt
        """
        try:
            prompt_bronnen = (
                f"Geef een overzicht van de bronnen of kennis waarop je de volgende definitie hebt gebaseerd. "
                f"Noem expliciet wetten, richtlijnen of veelgebruikte definities indien van toepassing. "
                f"Begrip: '{begrip}'\n"
                f"Organisatorische context: '{', '.join(context_dict.get('organisatorisch', []))}'\n"
                f"Juridische context: '{', '.join(context_dict.get('juridisch', []))}'\n"
                f"Wettelijke basis: '{', '.join(context_dict.get('wettelijk', []))}'"
            )
            
            return stuur_prompt_naar_gpt(
                prompt_bronnen,
                model="gpt-4",
                max_tokens=1000,
                temperatuur=0.2,
            ).strip()
            
        except Exception as e:
            self.logger.error(f"Sources generation failed: {str(e)}")
            raise APIError(f"Bronnen generatie mislukt: {str(e)}")
    
    @handle_validation_error
    def validate_definition(
        self,
        definitie: str,
        toetsregels: Dict[str, Any],
        begrip: str,
        marker: str = "",
        voorkeursterm: str = "",
        bronnen_gebruikt: Optional[str] = None,
        contexten: Optional[Dict[str, List[str]]] = None,
        gebruik_logging: bool = False
    ) -> List[str]:
        """
        Valideer definitie tegen kwaliteitsregels.
        
        Args:
            definitie: Te valideren definitie tekst
            toetsregels: Kwaliteitsregels voor validatie
            begrip: Oorspronkelijk begrip
            marker: Ontologische categorie marker
            voorkeursterm: Voorkeursterm voor het begrip
            bronnen_gebruikt: Gebruikte bronnen
            contexten: Context informatie
            gebruik_logging: Of gedetailleerde logging gebruikt wordt
            
        Returns:
            Lijst met validatie resultaten en feedback
            
        Raises:
            ValidationError: Als validatie mislukt
        """
        try:
            return toets_definitie(
                definitie,
                toetsregels,
                begrip=begrip,
                marker=marker,
                voorkeursterm=voorkeursterm,
                bronnen_gebruikt=bronnen_gebruikt,
                contexten=contexten or {},
                gebruik_logging=gebruik_logging
            )
            
        except Exception as e:
            self.logger.error(f"Definitie validatie mislukt: {str(e)}")
            raise ValidationError(f"Definitie validatie mislukt: {str(e)}")
    
    @handle_api_error
    def generate_examples(self, begrip: str, definitie: str, context_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Genereer voorbeeldzinnen en praktijkcases.
        
        Args:
            begrip: Begrip waarvoor voorbeelden gegenereerd worden
            definitie: Definitie tekst als basis
            context_dict: Context informatie voor voorbeelden
            
        Returns:
            Dictionary met verschillende soorten voorbeelden
            
        Raises:
            APIError: Als voorbeelden generatie mislukt
        """
        try:
            return {
                "voorbeeld_zinnen": safe_execute(
                    lambda: genereer_voorbeeld_zinnen(begrip, definitie, context_dict),
                    default_value=[],
                    error_message="Voorbeeld zinnen generatie mislukt"
                ),
                "praktijkvoorbeelden": safe_execute(
                    lambda: genereer_praktijkvoorbeelden(begrip, definitie, context_dict),
                    default_value=[],
                    error_message="Praktijkvoorbeelden generatie mislukt"
                ),
                "tegenvoorbeelden": safe_execute(
                    lambda: genereer_tegenvoorbeelden(begrip, definitie, context_dict),
                    default_value=[],
                    error_message="Tegenvoorbeelden generatie mislukt"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Voorbeelden generatie mislukt: {str(e)}")
            raise APIError(f"Voorbeelden generatie mislukt: {str(e)}")
    
    @handle_api_error
    def generate_additional_content(self, begrip: str, context_dict: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Genereer aanvullende content zoals toelichting en synoniemen.
        
        Args:
            begrip: Begrip waarvoor aanvullende content gegenereerd wordt
            context_dict: Context informatie voor content generatie
            
        Returns:
            Dictionary met aanvullende content (toelichting, synoniemen, antoniemen)
            
        Raises:
            APIError: Als content generatie mislukt
        """
        try:
            return {
                "toelichting": safe_execute(
                    lambda: genereer_toelichting(begrip, context_dict),
                    default_value="",
                    error_message="Toelichting generatie mislukt"
                ),
                "synoniemen": safe_execute(
                    lambda: genereer_synoniemen(begrip, context_dict),
                    default_value="",
                    error_message="Synoniemen generatie mislukt"
                ),
                "antoniemen": safe_execute(
                    lambda: genereer_antoniemen(begrip, context_dict),
                    default_value="",
                    error_message="Antoniemen generatie mislukt"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Aanvullende content generatie mislukt: {str(e)}")
            raise APIError(f"Aanvullende content generatie mislukt: {str(e)}")
    
    
    def build_prompt(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """
        Bouw GPT prompt voor definitie generatie.
        
        Args:
            begrip: Te definiëren begrip
            context_dict: Context informatie voor prompt opbouw
            
        Returns:
            Gegenereerde prompt tekst voor AI model
        """
        try:
            prompt_config = PromptConfiguratie(
                begrip=begrip,
                context_dict=context_dict
            )
            pb = PromptBouwer(prompt_config)
            return pb.bouw_prompt()
            
        except Exception as e:
            self.logger.error(f"Prompt opbouw mislukt: {str(e)}")
            return ""
    
    def process_complete_definition(
        self,
        form_data: Dict[str, Any],
        toetsregels: Dict[str, Any]
    ) -> bool:
        """
        Verwerk complete definitie generatie workflow.
        
        Deze methode coördineert alle stappen: prompt building, definitie generatie,
        validatie, voorbeelden generatie en logging.
        
        Args:
            form_data: Formuliergegevens uit UI
            toetsregels: Kwaliteitsregels voor validatie
            
        Returns:
            True als succesvol, False bij fouten
        """
        try:
            begrip = form_data["begrip"]
            context_dict = form_data["context_dict"]
            
            if not begrip.strip():
                return False
            
            # Bouw de prompt voor AI generatie
            prompt_text = self.build_prompt(begrip, context_dict)
            SessionStateManager.set_value("prompt_text", prompt_text)
            
            # Genereer definitie met AI
            definitie_origineel, definitie_gecorrigeerd, marker = self.generate_definition(begrip, context_dict)
            
            # Update sessie status met definitie resultaten
            SessionStateManager.update_definition_results(
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                marker=marker
            )
            
            # Genereer bronnenlijst voor traceerbaarheid
            bronnen_tekst = self.generate_sources(begrip, context_dict)
            
            # Valideer definitie tegen kwaliteitsregels
            toetsresultaten = self.validate_definition(
                definitie_gecorrigeerd,
                toetsregels,
                begrip=begrip,
                marker=marker,
                voorkeursterm=SessionStateManager.get_value("voorkeursterm"),
                bronnen_gebruikt=bronnen_tekst,
                contexten=context_dict,
                gebruik_logging=form_data.get("gebruik_logging", False)
            )
            
            # Genereer voorbeelden en use cases
            examples = self.generate_examples(begrip, definitie_origineel, context_dict)
            
            # Genereer aanvullende content (synoniemen, toelichting)
            additional_content = self.generate_additional_content(begrip, context_dict)
            
            # Update sessie status met alle gegenereerde content
            SessionStateManager.update_ai_content(
                voorbeeld_zinnen=examples["voorbeeld_zinnen"],
                praktijkvoorbeelden=examples["praktijkvoorbeelden"],
                tegenvoorbeelden=examples["tegenvoorbeelden"],
                toelichting=additional_content["toelichting"],
                synoniemen=additional_content["synoniemen"],
                antoniemen=additional_content["antoniemen"],
                bronnen_gebruikt=bronnen_tekst
            )
            
            SessionStateManager.set_value("beoordeling_gen", toetsresultaten)
            
            # Log de AI gegenereerde versie voor audit trail
            self._log_definition_version(
                versietype="AI",
                form_data=form_data,
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                toetsresultaten=toetsresultaten
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Complete definitie verwerking mislukt: {str(e)}")
            return False
    
    def process_modified_definition(
        self,
        form_data: Dict[str, Any],
        toetsregels: Dict[str, Any]
    ) -> bool:
        """
        Process modified definition validation.
        
        Args:
            form_data: Form data from UI
            toetsregels: Quality rules
            
        Returns:
            True if successful, False otherwise
        """
        try:
            aangepaste_definitie = SessionStateManager.get_value("aangepaste_definitie")
            
            if not aangepaste_definitie.strip():
                return False
            
            # Validate modified definition
            toetsresultaten = self.validate_definition(
                aangepaste_definitie,
                toetsregels,
                begrip=form_data["begrip"],
                voorkeursterm=SessionStateManager.get_value("voorkeursterm"),
                bronnen_gebruikt=SessionStateManager.get_value("bronnen_gebruikt"),
                contexten=form_data["context_dict"],
                gebruik_logging=form_data.get("gebruik_logging", False)
            )
            
            SessionStateManager.set_value("beoordeling", toetsresultaten)
            
            # Log the modified version
            self._log_definition_version(
                versietype="Aangepast",
                form_data=form_data,
                definitie_origineel=SessionStateManager.get_value("definitie_origineel"),
                definitie_gecorrigeerd=SessionStateManager.get_value("definitie_gecorrigeerd"),
                toetsresultaten=toetsresultaten
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Modified definition processing failed: {str(e)}")
            return False
    
    def _log_definition_version(
        self,
        versietype: str,
        form_data: Dict[str, Any],
        definitie_origineel: str,
        definitie_gecorrigeerd: str,
        toetsresultaten: List[str]
    ):
        """Log definition version to files."""
        try:
            log_definitie(
                versietype=versietype,
                begrip=form_data["begrip"],
                context=form_data["context"],
                juridische_context=form_data["juridische_context"],
                wet_basis=form_data["wet_basis"],
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                definitie_aangepast=SessionStateManager.get_value("aangepaste_definitie"),
                toetsing=toetsresultaten,
                voorbeeld_zinnen=SessionStateManager.get_value("voorbeeld_zinnen"),
                praktijkvoorbeelden=SessionStateManager.get_value("praktijkvoorbeelden"),
                toelichting=SessionStateManager.get_value("toelichting"),
                synoniemen=SessionStateManager.get_value("synoniemen"),
                antoniemen=SessionStateManager.get_value("antoniemen"),
                vrije_input=SessionStateManager.get_value("vrije_input"),
                prompt_text=SessionStateManager.get_value("prompt_text"),
                datum=form_data["datum"],
                voorsteller=form_data["voorsteller"],
                ketenpartners=form_data["ketenpartners"],
                expert_review=SessionStateManager.get_value("expert_review")
            )
            
        except Exception as e:
            self.logger.error(f"Definition logging failed: {str(e)}")