"""
Definition processing service for DefinitieAgent.
Handles the complete definition generation and validation workflow.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from utils.exceptions import (
    handle_api_error, handle_validation_error, 
    APIError, ValidationError, safe_execute,
    log_and_display_error
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
from log.log_definitie import log_definitie


class DefinitionService:
    """Service class for definition processing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @handle_api_error
    def generate_definition(self, begrip: str, context_dict: Dict[str, List[str]]) -> Tuple[str, str, str]:
        """
        Generate definition using AI.
        
        Args:
            begrip: Term to define
            context_dict: Context information
            
        Returns:
            Tuple of (original_definition, cleaned_definition, marker)
            
        Raises:
            APIError: If AI generation fails
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
            
            for regel in regels:
                if regel.lower().startswith("ontologische categorie:"):
                    marker = regel.split(":", 1)[1].strip()
                else:
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
        Generate sources information using AI.
        
        Args:
            begrip: Term
            context_dict: Context information
            
        Returns:
            Sources text
            
        Raises:
            APIError: If sources generation fails
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
        Validate definition using quality rules.
        
        Args:
            definitie: Definition text to validate
            toetsregels: Quality rules
            begrip: Original term
            marker: Ontological marker
            voorkeursterm: Preferred term
            bronnen_gebruikt: Sources used
            contexten: Context information
            gebruik_logging: Whether to use detailed logging
            
        Returns:
            List of validation results
            
        Raises:
            ValidationError: If validation fails
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
            self.logger.error(f"Definition validation failed: {str(e)}")
            raise ValidationError(f"Definitie validatie mislukt: {str(e)}")
    
    @handle_api_error
    def generate_examples(self, begrip: str, definitie: str, context_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Generate example sentences and cases.
        
        Args:
            begrip: Term
            definitie: Definition
            context_dict: Context information
            
        Returns:
            Dictionary with different types of examples
            
        Raises:
            APIError: If example generation fails
        """
        try:
            return {
                "voorbeeld_zinnen": safe_execute(
                    lambda: genereer_voorbeeld_zinnen(begrip, definitie, context_dict),
                    default_value=[],
                    error_message="Example sentences generation failed"
                ),
                "praktijkvoorbeelden": safe_execute(
                    lambda: genereer_praktijkvoorbeelden(begrip, definitie, context_dict),
                    default_value=[],
                    error_message="Practice examples generation failed"
                ),
                "tegenvoorbeelden": safe_execute(
                    lambda: genereer_tegenvoorbeelden(begrip, definitie, context_dict),
                    default_value=[],
                    error_message="Counter examples generation failed"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Examples generation failed: {str(e)}")
            raise APIError(f"Voorbeelden generatie mislukt: {str(e)}")
    
    @handle_api_error
    def generate_additional_content(self, begrip: str, context_dict: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Generate additional content like explanations and synonyms.
        
        Args:
            begrip: Term
            context_dict: Context information
            
        Returns:
            Dictionary with additional content
            
        Raises:
            APIError: If content generation fails
        """
        try:
            return {
                "toelichting": safe_execute(
                    lambda: genereer_toelichting(begrip, context_dict),
                    default_value="",
                    error_message="Explanation generation failed"
                ),
                "synoniemen": safe_execute(
                    lambda: genereer_synoniemen(begrip, context_dict),
                    default_value="",
                    error_message="Synonyms generation failed"
                ),
                "antoniemen": safe_execute(
                    lambda: genereer_antoniemen(begrip, context_dict),
                    default_value="",
                    error_message="Antonyms generation failed"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Additional content generation failed: {str(e)}")
            raise APIError(f"Aanvullende content generatie mislukt: {str(e)}")
    
    
    def build_prompt(self, begrip: str, context_dict: Dict[str, List[str]]) -> str:
        """
        Build GPT prompt for definition generation.
        
        Args:
            begrip: Term to define
            context_dict: Context information
            
        Returns:
            Generated prompt text
        """
        try:
            prompt_config = PromptConfiguratie(
                begrip=begrip,
                context_dict=context_dict
            )
            pb = PromptBouwer(prompt_config)
            return pb.bouw_prompt()
            
        except Exception as e:
            self.logger.error(f"Prompt building failed: {str(e)}")
            return ""
    
    def process_complete_definition(
        self,
        form_data: Dict[str, Any],
        toetsregels: Dict[str, Any]
    ) -> bool:
        """
        Process complete definition generation workflow.
        
        Args:
            form_data: Form data from UI
            toetsregels: Quality rules
            
        Returns:
            True if successful, False otherwise
        """
        try:
            begrip = form_data["begrip"]
            context_dict = form_data["context_dict"]
            
            if not begrip.strip():
                return False
            
            # Build prompt
            prompt_text = self.build_prompt(begrip, context_dict)
            SessionStateManager.set_value("prompt_text", prompt_text)
            
            # Generate definition
            definitie_origineel, definitie_gecorrigeerd, marker = self.generate_definition(begrip, context_dict)
            
            # Update session state with results
            SessionStateManager.update_definition_results(
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                marker=marker
            )
            
            # Generate sources
            bronnen_tekst = self.generate_sources(begrip, context_dict)
            
            # Validate definition
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
            
            # Generate examples
            examples = self.generate_examples(begrip, definitie_origineel, context_dict)
            
            # Generate additional content
            additional_content = self.generate_additional_content(begrip, context_dict)
            
            # Update session state with all generated content
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
            
            # Log the AI version
            self._log_definition_version(
                versietype="AI",
                form_data=form_data,
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                toetsresultaten=toetsresultaten
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Complete definition processing failed: {str(e)}")
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