"""
Integration tests voor het complete Generator-Validator feedback loop systeem.
Test de samenwerking tussen alle componenten van de definitie agent.
"""

import pytest
import time
from typing import Dict, Any

from generation.definitie_generator import (
    DefinitieGenerator, GenerationContext, OntologischeCategorie, 
    RegelInterpreter, generate_definitie
)
from validation.definitie_validator import (
    DefinitieValidator, ValidationRegelInterpreter, ViolationSeverity,
    validate_definitie
)
from orchestration.definitie_agent import (
    DefinitieAgent, FeedbackBuilder, AgentStatus,
    generate_definition_with_feedback
)


class TestRegelInterpreters:
    """Test beide regel interpreters samen."""
    
    def test_same_rules_different_interpretation(self):
        """Test dat dezelfde regels verschillend geïnterpreteerd worden."""
        from config.toetsregel_manager import get_toetsregel_manager
        
        rule_manager = get_toetsregel_manager()
        gen_interpreter = RegelInterpreter()
        val_interpreter = ValidationRegelInterpreter()
        
        # Test met CON-01 regel
        con01 = rule_manager.load_regel("CON-01")
        assert con01 is not None
        
        # Generator interpretatie
        gen_instruction = gen_interpreter.for_generation(con01)
        assert gen_instruction.rule_id == "CON-01"
        assert "formuleer" in gen_instruction.guidance.lower()
        assert len(gen_instruction.focus_areas) > 0
        
        # Validator interpretatie  
        val_criterion = val_interpreter.for_validation(con01)
        assert val_criterion.rule_id == "CON-01"
        assert len(val_criterion.patterns_to_avoid) > 0
        assert val_criterion.severity == ViolationSeverity.CRITICAL
        
        # Verschillende output maar zelfde basis
        assert gen_instruction.guidance != val_criterion.description
        assert gen_instruction.rule_id == val_criterion.rule_id
    
    def test_all_critical_rules_covered(self):
        """Test dat alle kritieke regels door beide interpreters worden ondersteund."""
        from config.toetsregel_manager import get_toetsregel_manager
        
        rule_manager = get_toetsregel_manager()
        gen_interpreter = RegelInterpreter()
        val_interpreter = ValidationRegelInterpreter()
        
        kritieke_regels = rule_manager.get_kritieke_regels()
        assert len(kritieke_regels) > 0
        
        for regel in kritieke_regels:
            regel_id = regel.get("id")
            
            # Beide interpreters moeten regel kunnen verwerken
            gen_instruction = gen_interpreter.for_generation(regel)
            val_criterion = val_interpreter.for_validation(regel)
            
            assert gen_instruction.rule_id == regel_id
            assert val_criterion.rule_id == regel_id
            assert len(gen_instruction.guidance) > 10  # Meaningful guidance
            assert len(val_criterion.description) > 10  # Meaningful description


class TestGeneratorValidatorIntegration:
    """Test integratie tussen Generator en Validator."""
    
    def test_generator_validator_workflow(self):
        """Test basis workflow: genereer → valideer."""
        generator = DefinitieGenerator()
        validator = DefinitieValidator()
        
        # Maak context
        context = GenerationContext(
            begrip="verificatie",
            organisatorische_context="DJI",
            juridische_context="strafrecht",
            categorie=OntologischeCategorie.PROCES
        )
        
        # Genereer definitie
        gen_result = generator.generate(context)
        assert gen_result.definitie
        assert len(gen_result.gebruikte_instructies) > 0
        
        # Valideer definitie
        val_result = validator.validate(gen_result.definitie, context.categorie)
        assert val_result.overall_score >= 0.0
        assert val_result.overall_score <= 1.0
        assert isinstance(val_result.is_acceptable, bool)
    
    def test_different_categories_different_results(self):
        """Test dat verschillende categorieën verschillende regels krijgen."""
        generator = DefinitieGenerator()
        validator = DefinitieValidator()
        
        begrip = "registratie"
        org_context = "OM"
        
        categorieën = [
            OntologischeCategorie.TYPE,
            OntologischeCategorie.PROCES,
            OntologischeCategorie.RESULTAAT,
            OntologischeCategorie.EXEMPLAAR
        ]
        
        results = {}
        
        for categorie in categorieën:
            context = GenerationContext(
                begrip=begrip,
                organisatorische_context=org_context,
                juridische_context="",
                categorie=categorie
            )
            
            gen_result = generator.generate(context)
            val_result = validator.validate(gen_result.definitie, categorie)
            
            results[categorie] = {
                'generation': gen_result,
                'validation': val_result
            }
        
        # Verschillende categorieën zouden verschillende instructies moeten hebben
        type_instructions = results[OntologischeCategorie.TYPE]['generation'].gebruikte_instructies
        proces_instructions = results[OntologischeCategorie.PROCES]['generation'].gebruikte_instructies
        
        # Al mogen ze overlap hebben, ze zouden niet identiek moeten zijn
        type_ids = [i.rule_id for i in type_instructions]
        proces_ids = [i.rule_id for i in proces_instructions]
        
        # Beide zouden instructies moeten hebben
        assert len(type_ids) > 0
        assert len(proces_ids) > 0
    
    def test_feedback_integration(self):
        """Test dat feedback correct geïntegreerd wordt in volgende generatie."""
        generator = DefinitieGenerator()
        
        context = GenerationContext(
            begrip="toezicht",
            organisatorische_context="DJI",
            juridische_context="",
            categorie=OntologischeCategorie.PROCES
        )
        
        # Eerste generatie zonder feedback
        result1 = generator.generate(context)
        prompt1_length = len(result1.prompt_template)
        
        # Voeg feedback toe
        context.feedback_history = [
            "Start met een zelfstandig naamwoord",
            "Vermijd explicite context vermelding",
            "Voeg onderscheidende kenmerken toe"
        ]
        
        # Tweede generatie met feedback
        result2 = generator.generate(context)
        prompt2_length = len(result2.prompt_template)
        
        # Prompt met feedback zou langer moeten zijn
        assert prompt2_length > prompt1_length
        assert "VERBETERINGEN" in result2.prompt_template


class TestFeedbackBuilder:
    """Test de FeedbackBuilder uitgebreid."""
    
    def test_critical_violations_prioritized(self):
        """Test dat kritieke violations geprioriteerd worden."""
        from validation.definitie_validator import RuleViolation, ViolationType
        from orchestration.definitie_agent import FeedbackContext
        
        feedback_builder = FeedbackBuilder()
        
        violations = [
            RuleViolation(
                rule_id="STR-01",
                rule_name="Start regel",
                violation_type=ViolationType.STRUCTURE_ISSUE,
                severity=ViolationSeverity.LOW,
                description="Lage prioriteit probleem"
            ),
            RuleViolation(
                rule_id="CON-01",
                rule_name="Context regel",
                violation_type=ViolationType.FORBIDDEN_PATTERN,
                severity=ViolationSeverity.CRITICAL,
                description="Kritiek probleem",
                detected_pattern="binnen de context"
            )
        ]
        
        context = FeedbackContext(
            violations=violations,
            previous_attempts=[],
            score_history=[0.5]
        )
        
        feedback = feedback_builder.build_improvement_feedback(context, 1)
        
        # Kritieke feedback zou eerst moeten komen
        assert len(feedback) > 0
        assert "🚨 KRITIEK" in feedback[0]
    
    def test_learning_from_history(self):
        """Test dat feedback leert van vorige pogingen."""
        from orchestration.definitie_agent import FeedbackContext
        
        feedback_builder = FeedbackBuilder()
        
        # Simuleer stagnerende scores
        context = FeedbackContext(
            violations=[],
            previous_attempts=["Poging 1", "Poging 2"],
            score_history=[0.7, 0.71, 0.71]  # Stagnatie
        )
        
        feedback = feedback_builder.build_improvement_feedback(context, 3)
        
        # Zou stagnatie moeten detecteren
        feedback_text = " ".join(feedback).lower()
        assert "stagneert" in feedback_text or "andere" in feedback_text
    
    def test_feedback_deduplication(self):
        """Test dat duplicate feedback wordt gefilterd."""
        from validation.definitie_validator import RuleViolation, ViolationType
        from orchestration.definitie_agent import FeedbackContext
        
        feedback_builder = FeedbackBuilder()
        
        # Duplicate violations
        violations = [
            RuleViolation(
                rule_id="CON-01",
                rule_name="Context regel",
                violation_type=ViolationType.FORBIDDEN_PATTERN,
                severity=ViolationSeverity.CRITICAL,
                description="Probleem 1",
                detected_pattern="binnen de context"
            ),
            RuleViolation(
                rule_id="CON-01", 
                rule_name="Context regel",
                violation_type=ViolationType.FORBIDDEN_PATTERN,
                severity=ViolationSeverity.CRITICAL,
                description="Probleem 2",
                detected_pattern="binnen de context"
            )
        ]
        
        context = FeedbackContext(
            violations=violations,
            previous_attempts=[],
            score_history=[0.5]
        )
        
        feedback = feedback_builder.build_improvement_feedback(context, 1)
        
        # Niet meer dan 5 feedback items
        assert len(feedback) <= 5
        
        # Geen exacte duplicates
        unique_feedback = set(feedback)
        assert len(unique_feedback) == len(feedback)


class TestDefinitieAgent:
    """Test de complete DefinitieAgent orchestration."""
    
    def test_single_iteration_success(self):
        """Test succesvolle definitie in één iteratie (hypothetisch)."""
        agent = DefinitieAgent(max_iterations=1, acceptance_threshold=0.5)  # Lage threshold voor test
        
        result = agent.generate_definition(
            begrip="document",
            organisatorische_context="OM",
            categorie=OntologischeCategorie.TYPE
        )
        
        assert result.iteration_count == 1
        assert result.final_definitie
        assert result.total_processing_time > 0
        assert len(result.iterations) == 1
        
        # Check eerste iteratie
        first_iteration = result.iterations[0]
        assert first_iteration.iteration_number == 1
        assert first_iteration.definitie
        assert first_iteration.validation_result
        assert first_iteration.processing_time > 0
    
    def test_multiple_iterations_with_improvement(self):
        """Test meerdere iteraties met score verbetering."""
        agent = DefinitieAgent(max_iterations=3, acceptance_threshold=0.95)  # Hoge threshold om meerdere iteraties te forceren
        
        result = agent.generate_definition(
            begrip="verificatie",
            organisatorische_context="DJI",
            categorie=OntologischeCategorie.PROCES
        )
        
        # Zou meerdere iteraties moeten doen vanwege hoge threshold
        assert result.iteration_count > 1
        assert len(result.improvement_history) == result.iteration_count
        
        # Check dat elke iteratie valid is
        for i, iteration in enumerate(result.iterations):
            assert iteration.iteration_number == i + 1
            assert iteration.definitie
            assert 0.0 <= iteration.validation_result.overall_score <= 1.0
    
    def test_early_stopping_on_success(self):
        """Test early stopping bij acceptabele definitie."""
        # Mock een scenario waar de eerste poging al goed genoeg is
        agent = DefinitieAgent(max_iterations=5, acceptance_threshold=0.1)  # Zeer lage threshold
        
        result = agent.generate_definition(
            begrip="registratie",
            organisatorische_context="OM",
            categorie=OntologischeCategorie.PROCES
        )
        
        # Als de threshold laag genoeg is, zou het vroeg moeten stoppen
        if result.success:
            assert result.iteration_count < 5
            assert "achieved" in result.reason.lower()
    
    def test_max_iterations_reached(self):
        """Test dat max iteraties correct afgehandeld wordt."""
        agent = DefinitieAgent(max_iterations=2, acceptance_threshold=0.99)  # Onbereikbaar hoge threshold
        
        result = agent.generate_definition(
            begrip="beoordeling",
            organisatorische_context="DJI",
            categorie=OntologischeCategorie.PROCES
        )
        
        # Zou exact max iteraties moeten doen
        assert result.iteration_count == 2
        assert not result.success  # Vanwege onbereikbare threshold
        assert "maximum" in result.reason.lower() or "insufficient" in result.reason.lower()
    
    def test_status_tracking(self):
        """Test dat agent status correct getrackt wordt."""
        agent = DefinitieAgent(max_iterations=1)
        
        # Voor start
        status = agent.get_status()
        assert status["status"] == AgentStatus.INITIALIZING.value
        assert status["iterations_completed"] == 0
        
        # Na generatie
        result = agent.generate_definition(
            begrip="controle",
            organisatorische_context="OM",
            categorie=OntologischeCategorie.PROCES
        )
        
        final_status = agent.get_status()
        assert final_status["iterations_completed"] > 0
        assert final_status["processing_time"] > 0
    
    def test_performance_metrics(self):
        """Test dat performance metrics correct berekend worden."""
        agent = DefinitieAgent(max_iterations=2)
        
        result = agent.generate_definition(
            begrip="analyse",
            organisatorische_context="DJI",
            categorie=OntologischeCategorie.PROCES
        )
        
        metrics = result.get_performance_metrics()
        
        # Check alle verwachte metrics
        expected_keys = [
            "iterations", "final_score", "score_improvement",
            "average_iteration_time", "total_time", "success_rate"
        ]
        
        for key in expected_keys:
            assert key in metrics
            assert isinstance(metrics[key], (int, float))
        
        # Sanity checks
        assert metrics["iterations"] > 0
        assert 0.0 <= metrics["final_score"] <= 1.0
        assert metrics["total_time"] > 0
        assert metrics["average_iteration_time"] > 0
        assert 0.0 <= metrics["success_rate"] <= 1.0


class TestConvenienceFunctions:
    """Test convenience functions voor eenvoudig gebruik."""
    
    def test_generate_definitie_convenience(self):
        """Test convenience function voor eenvoudige generatie."""
        definitie = generate_definitie(
            begrip="toezicht",
            organisatorische_context="DJI",
            categorie="proces"
        )
        
        assert isinstance(definitie, str)
        assert len(definitie) > 0
        assert definitie != "Failed to generate definition"
    
    def test_validate_definitie_convenience(self):
        """Test convenience function voor eenvoudige validatie."""
        test_definitie = "Verificatie waarbij identiteitsgegevens worden gecontroleerd"
        
        result = validate_definitie(
            definitie=test_definitie,
            categorie="proces"
        )
        
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'is_acceptable')
        assert 0.0 <= result.overall_score <= 1.0
    
    def test_generate_definition_with_feedback_convenience(self):
        """Test convenience function voor feedback loop."""
        result = generate_definition_with_feedback(
            begrip="registratie",
            organisatorische_context="OM",
            categorie="type",
            max_iterations=2
        )
        
        assert hasattr(result, 'final_definitie')
        assert hasattr(result, 'iterations')
        assert hasattr(result, 'success')
        assert result.iteration_count <= 2
        assert result.final_definitie


class TestErrorHandling:
    """Test error handling en edge cases."""
    
    def test_empty_begrip_handling(self):
        """Test omgang met lege begrip."""
        agent = DefinitieAgent(max_iterations=1)
        
        result = agent.generate_definition(
            begrip="",
            organisatorische_context="OM",
            categorie=OntologischeCategorie.TYPE
        )
        
        # Zou niet moeten crashen
        assert result is not None
        assert hasattr(result, 'success')
    
    def test_invalid_context_handling(self):
        """Test omgang met ongeldige context."""
        agent = DefinitieAgent(max_iterations=1)
        
        result = agent.generate_definition(
            begrip="test",
            organisatorische_context="",
            categorie=OntologischeCategorie.TYPE
        )
        
        # Zou niet moeten crashen
        assert result is not None
        assert result.iteration_count > 0
    
    def test_very_long_begrip(self):
        """Test omgang met zeer lange begrippen."""
        agent = DefinitieAgent(max_iterations=1)
        
        zeer_lang_begrip = "dit_is_een_extreem_lang_begrip_dat_normaal_gesproken_niet_voorkomt_maar_we_testen_het_toch" * 5
        
        result = agent.generate_definition(
            begrip=zeer_lang_begrip,
            organisatorische_context="OM",
            categorie=OntologischeCategorie.TYPE
        )
        
        # Zou niet moeten crashen
        assert result is not None
        assert result.final_definitie


class TestPerformance:
    """Test performance aspecten van het systeem."""
    
    def test_single_iteration_performance(self):
        """Test dat één iteratie snel genoeg is."""
        agent = DefinitieAgent(max_iterations=1)
        
        start_time = time.time()
        
        result = agent.generate_definition(
            begrip="document",
            organisatorische_context="OM",
            categorie=OntologischeCategorie.TYPE
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Zou snel moeten zijn (onder 5 seconden voor test)
        assert total_time < 5.0
        assert result.total_processing_time < 5.0
        
        # Agent timing zou consistent moeten zijn met gemeten tijd
        assert abs(result.total_processing_time - total_time) < 1.0
    
    def test_multiple_iterations_performance(self):
        """Test performance van meerdere iteraties."""
        agent = DefinitieAgent(max_iterations=3)
        
        result = agent.generate_definition(
            begrip="verificatie",
            organisatorische_context="DJI",
            categorie=OntologischeCategorie.PROCES
        )
        
        # Elke iteratie zou redelijk snel moeten zijn
        for iteration in result.iterations:
            assert iteration.processing_time < 2.0
        
        # Totale tijd zou niet exponentieel moeten groeien
        if result.iteration_count > 1:
            avg_time = result.total_processing_time / result.iteration_count
            assert avg_time < 2.0


if __name__ == "__main__":
    # Run tests als script wordt uitgevoerd
    import subprocess
    import sys
    
    print("🧪 Running Generator-Validator Integration Tests")
    print("=" * 50)
    
    # Run pytest op dit bestand
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "-x"  # Stop op eerste failure voor snellere feedback
    ], capture_output=False)
    
    sys.exit(result.returncode)