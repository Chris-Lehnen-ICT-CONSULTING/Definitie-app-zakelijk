"""
Async definition processing service for DefinitieAgent.
Provides concurrent processing for improved performance and user experience.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass

from utils.exceptions import (
    APIError, ValidationError
)
from utils.async_api import async_gpt_call
from ui.session_state import SessionStateManager
from voorbeelden.async_voorbeelden import async_generate_all_examples, ExampleGenerationResult
from definitie_generator.generator import genereer_definitie
from prompt_builder.prompt_builder import PromptBouwer, PromptConfiguratie
from ai_toetser import toets_definitie
from opschoning.opschoning import opschonen
from logs.application.log_definitie import log_definitie


@dataclass
class AsyncProcessingResult:
    """Result container for async definition processing."""
    success: bool
    processing_time: float
    definitie_origineel: str = ""
    definitie_gecorrigeerd: str = ""
    marker: str = ""
    bronnen_tekst: str = ""
    toetsresultaten: List[str] = None
    examples: Optional[ExampleGenerationResult] = None
    additional_content: Optional[Dict[str, str]] = None
    error_message: str = ""
    cache_hits: int = 0
    total_requests: int = 0


class AsyncDefinitionService:
    """Async service class for definition processing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def async_generate_definition(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> Tuple[str, str, str]:
        """
        Generate definition using async AI calls.
        
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
            # Use existing sync function for now, TODO: make fully async
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
            self.logger.error(f"Async definition generation failed: {str(e)}")
            raise APIError(f"Definitie generatie mislukt: {str(e)}")
    
    async def async_generate_sources(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> str:
        """
        Generate sources information using async AI.
        
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
            
            return await async_gpt_call(
                prompt=prompt_bronnen,
                model="gpt-4",
                max_tokens=1000,
                temperature=0.2,
            )
            
        except Exception as e:
            self.logger.error(f"Async sources generation failed: {str(e)}")
            raise APIError(f"Bronnen generatie mislukt: {str(e)}")
    
    def async_validate_definition(
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
        Validate definition using quality rules (sync for now).
        
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
            self.logger.error(f"Async definition validation failed: {str(e)}")
            raise ValidationError(f"Definitie validatie mislukt: {str(e)}")
    
    async def async_generate_additional_content(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """
        Generate additional content concurrently.
        
        Args:
            begrip: Term
            context_dict: Context information
            
        Returns:
            Dictionary with additional content
            
        Raises:
            APIError: If content generation fails
        """
        try:
            # Create concurrent tasks for additional content
            tasks = {
                'toelichting': self._async_generate_explanation(begrip, context_dict),
                'synoniemen': self._async_generate_synonyms(begrip, context_dict),
                'antoniemen': self._async_generate_antonyms(begrip, context_dict)
            }
            
            # Execute concurrently
            results = {}
            for name, coro in tasks.items():
                try:
                    results[name] = await coro
                except Exception as e:
                    self.logger.error(f"Error generating {name}: {str(e)}")
                    results[name] = f"❌ Error: {str(e)}"
            
            return results
            
        except Exception as e:
            self.logger.error(f"Async additional content generation failed: {str(e)}")
            raise APIError(f"Aanvullende content generatie mislukt: {str(e)}")
    
    async def _async_generate_explanation(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> str:
        """Generate explanation asynchronously."""
        prompt = (
            f"Geef een korte toelichting op de betekenis en toepassing van het begrip '{begrip}', "
            f"zoals het zou kunnen voorkomen in overheidsdocumenten.\n"
            f"Gebruik de contexten hieronder alleen als achtergrond en noem ze niet letterlijk:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context: {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis: {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )
        return await async_gpt_call(prompt, temperature=0.3)
    
    async def _async_generate_synonyms(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> str:
        """Generate synonyms asynchronously."""
        prompt = (
            f"Geef maximaal 5 synoniemen voor het begrip '{begrip}', "
            f"relevant binnen de context van overheidsgebruik.\n"
            f"Gebruik onderstaande contexten als achtergrond. Geef de synoniemen als een lijst, zonder toelichting:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context: {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis: {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )
        return await async_gpt_call(prompt, temperature=0.2, max_tokens=150)
    
    async def _async_generate_antonyms(
        self, 
        begrip: str, 
        context_dict: Dict[str, List[str]]
    ) -> str:
        """Generate antonyms asynchronously."""
        prompt = (
            f"Geef maximaal 5 antoniemen voor het begrip '{begrip}', "
            f"binnen de context van overheidsgebruik.\n"
            f"Gebruik onderstaande contexten alleen als achtergrond. Geef de antoniemen als een lijst, zonder toelichting:\n\n"
            f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
            f"Juridische context: {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
            f"Wettelijke basis: {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
        )
        return await async_gpt_call(prompt, temperature=0.2, max_tokens=150)
    
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
    
    async def async_process_complete_definition(
        self,
        form_data: Dict[str, Any],
        toetsregels: Dict[str, Any],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> AsyncProcessingResult:
        """
        Process complete definition generation workflow asynchronously.
        
        Args:
            form_data: Form data from UI
            toetsregels: Quality rules
            progress_callback: Optional progress callback
            
        Returns:
            AsyncProcessingResult with all results and timing
        """
        start_time = time.time()
        
        try:
            begrip = form_data["begrip"]
            context_dict = form_data["context_dict"]
            
            if not begrip.strip():
                return AsyncProcessingResult(
                    success=False,
                    processing_time=0,
                    error_message="Begrip mag niet leeg zijn"
                )
            
            total_steps = 6
            current_step = 0
            
            # Step 1: Build prompt
            if progress_callback:
                progress_callback("Building prompt...", current_step, total_steps)
            
            prompt_text = self.build_prompt(begrip, context_dict)
            SessionStateManager.set_value("prompt_text", prompt_text)
            current_step += 1
            
            # Step 2: Generate definition
            if progress_callback:
                progress_callback("Generating definition...", current_step, total_steps)
            
            definitie_origineel, definitie_gecorrigeerd, marker = await self.async_generate_definition(
                begrip, context_dict
            )
            
            SessionStateManager.update_definition_results(
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                marker=marker
            )
            current_step += 1
            
            # Step 3: Generate sources concurrently with examples
            if progress_callback:
                progress_callback("Generating sources and examples...", current_step, total_steps)
            
            # Start concurrent tasks
            sources_task = self.async_generate_sources(begrip, context_dict)
            examples_task = async_generate_all_examples(
                begrip=begrip,
                definitie=definitie_origineel,
                context_dict=context_dict,
                progress_callback=lambda msg, completed, total: progress_callback(
                    f"Examples: {msg}", current_step, total_steps
                ) if progress_callback else None
            )
            additional_task = self.async_generate_additional_content(begrip, context_dict)
            
            # Wait for all concurrent tasks
            bronnen_tekst, examples, additional_content = await asyncio.gather(
                sources_task, examples_task, additional_task
            )
            current_step += 1
            
            # Step 4: Validate definition
            if progress_callback:
                progress_callback("Validating definition...", current_step, total_steps)
            
            toetsresultaten = self.async_validate_definition(
                definitie_gecorrigeerd,
                toetsregels,
                begrip=begrip,
                marker=marker,
                voorkeursterm=SessionStateManager.get_value("voorkeursterm"),
                bronnen_gebruikt=bronnen_tekst,
                contexten=context_dict,
                gebruik_logging=form_data.get("gebruik_logging", False)
            )
            current_step += 1
            
            # Step 5: Update session state
            if progress_callback:
                progress_callback("Updating session state...", current_step, total_steps)
            
            SessionStateManager.update_ai_content(
                voorbeeld_zinnen=examples.voorbeeld_zinnen,
                praktijkvoorbeelden=examples.praktijkvoorbeelden,
                tegenvoorbeelden=examples.tegenvoorbeelden,
                toelichting=examples.toelichting,
                synoniemen=examples.synoniemen,
                antoniemen=examples.antoniemen,
                bronnen_gebruikt=bronnen_tekst
            )
            
            SessionStateManager.set_value("beoordeling_gen", toetsresultaten)
            current_step += 1
            
            # Step 6: Log the results
            if progress_callback:
                progress_callback("Logging results...", current_step, total_steps)
            
            self._log_definition_version(
                versietype="AI",
                form_data=form_data,
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                toetsresultaten=toetsresultaten
            )
            current_step += 1
            
            processing_time = time.time() - start_time
            
            if progress_callback:
                progress_callback("Complete!", current_step, total_steps)
            
            self.logger.info(f"Async definition processing completed in {processing_time:.2f}s")
            
            return AsyncProcessingResult(
                success=True,
                processing_time=processing_time,
                definitie_origineel=definitie_origineel,
                definitie_gecorrigeerd=definitie_gecorrigeerd,
                marker=marker,
                bronnen_tekst=bronnen_tekst,
                toetsresultaten=toetsresultaten,
                examples=examples,
                additional_content=additional_content,
                total_requests=examples.total_requests + 3  # +3 for definition, sources, validation
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Async definition processing failed: {str(e)}"
            self.logger.error(error_message)
            
            return AsyncProcessingResult(
                success=False,
                processing_time=processing_time,
                error_message=error_message
            )
    
    async def async_process_modified_definition(
        self,
        form_data: Dict[str, Any],
        toetsregels: Dict[str, Any]
    ) -> AsyncProcessingResult:
        """
        Process modified definition validation asynchronously.
        
        Args:
            form_data: Form data from UI
            toetsregels: Quality rules
            
        Returns:
            AsyncProcessingResult with validation results
        """
        start_time = time.time()
        
        try:
            aangepaste_definitie = SessionStateManager.get_value("aangepaste_definitie")
            
            if not aangepaste_definitie.strip():
                return AsyncProcessingResult(
                    success=False,
                    processing_time=0,
                    error_message="Aangepaste definitie mag niet leeg zijn"
                )
            
            # Validate modified definition
            toetsresultaten = self.async_validate_definition(
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
            
            processing_time = time.time() - start_time
            
            return AsyncProcessingResult(
                success=True,
                processing_time=processing_time,
                toetsresultaten=toetsresultaten,
                total_requests=1  # Only validation
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Async modified definition processing failed: {str(e)}"
            self.logger.error(error_message)
            
            return AsyncProcessingResult(
                success=False,
                processing_time=processing_time,
                error_message=error_message
            )
    
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


# Global async definition service
_async_service: Optional[AsyncDefinitionService] = None


def get_async_definition_service() -> AsyncDefinitionService:
    """Get or create global async definition service."""
    global _async_service
    if _async_service is None:
        _async_service = AsyncDefinitionService()
    return _async_service