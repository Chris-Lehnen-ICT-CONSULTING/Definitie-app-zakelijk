"""
Test script voor hybrid context functionaliteit.
"""

import logging
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_processing.document_processor import get_document_processor
from hybrid_context.context_fusion import ContextFusion
from hybrid_context.hybrid_context_engine import get_hybrid_context_engine
from hybrid_context.smart_source_selector import SmartSourceSelector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_hybrid_context_workflow():
    """Test de complete hybrid context workflow."""

    print("=== HYBRID CONTEXT WORKFLOW TEST ===")

    # Test parameters
    begrip = "authenticatie"
    org_context = "OM"
    jur_context = "Strafrecht"

    try:
        # Stap 1: Test document processor
        print("\n1. Testing Document Processor...")
        doc_processor = get_document_processor()

        # Test tekst content
        test_content = b"""
        Definitie van Authenticatie

        Authenticatie is het proces waarbij de identiteit van een gebruiker wordt geverifieerd.
        Dit gebeurt door controle van inloggegevens zoals gebruikersnaam en wachtwoord.

        Juridische context:
        Dit proces is essentieel voor compliance met de AVG en Wet op de Identificatieplicht.

        Organisatorische context:
        Binnen de strafrechtketen gebruikt het OM authenticatie voor toegang tot systemen.
        """

        # Process test document
        processed_doc = doc_processor.process_uploaded_file(
            test_content, "test_authenticatie.txt", "text/plain"
        )

        print(f"✅ Document verwerkt: {processed_doc.processing_status}")
        print(f"   - Tekst lengte: {processed_doc.text_length}")
        print(f"   - Keywords: {len(processed_doc.keywords)}")
        print(f"   - Concepten: {len(processed_doc.key_concepts)}")
        print(f"   - Juridische refs: {len(processed_doc.legal_references)}")

        # Stap 2: Test Smart Source Selector
        print("\n2. Testing Smart Source Selector...")
        selector = SmartSourceSelector()

        # Get document context
        doc_context = doc_processor.get_aggregated_context([processed_doc.id])

        # Test source selection
        strategy = selector.select_optimal_sources(
            begrip=begrip,
            organisatorische_context=org_context,
            juridische_context=jur_context,
            document_context=doc_context,
        )

        print(f"✅ Source strategy: {strategy.strategy_name}")
        print(f"   - Priority sources: {strategy.priority_sources}")
        print(f"   - Confidence modifier: {strategy.confidence_modifier}")
        print(f"   - Reasoning: {strategy.reasoning}")

        # Stap 3: Test Context Fusion
        print("\n3. Testing Context Fusion...")
        fusion = ContextFusion()

        # Mock web context
        web_context = {
            "wikipedia": {
                "tekst": "Authenticatie is een beveiligingsproces voor identiteitsverificatie...",
                "bron": "wikipedia",
            },
            "wiktionary": {
                "tekst": "authenticatie: het verifiëren van de identiteit van een gebruiker...",
                "bron": "wiktionary",
            },
        }

        # Test fusion
        fusion_result = fusion.fuse_contexts(
            web_context=web_context, document_context=doc_context, begrip=begrip
        )

        print("✅ Context fusion completed")
        print(f"   - Strategy: {fusion_result['strategy']}")
        print(f"   - Confidence: {fusion_result['confidence_score']:.2f}")
        print(f"   - Quality: {fusion_result['quality_assessment']}")
        print(f"   - Conflicts resolved: {fusion_result['conflicts_resolved']}")

        # Stap 4: Test Hybrid Context Engine
        print("\n4. Testing Hybrid Context Engine...")
        hybrid_engine = get_hybrid_context_engine()

        # Test hybrid context creation
        hybrid_context = hybrid_engine.create_hybrid_context(
            begrip=begrip,
            organisatorische_context=org_context,
            juridische_context=jur_context,
            selected_document_ids=[processed_doc.id],
        )

        print("✅ Hybrid context created")
        print(f"   - Confidence: {hybrid_context.confidence_score:.2f}")
        print(f"   - Quality: {hybrid_context.context_quality}")
        print(f"   - Fusion strategy: {hybrid_context.fusion_strategy}")
        print(f"   - Web sources: {len(hybrid_context.web_sources)}")
        print(f"   - Document sources: {len(hybrid_context.document_sources)}")
        print(f"   - Primary sources: {hybrid_context.primary_sources}")

        # Test context summary
        summary = hybrid_engine.get_context_summary(hybrid_context)
        print(f"   - Enhancement level: {summary['enhancement_level']}")
        print(f"   - Total sources: {summary['total_sources']}")

        print("\n🎉 Alle hybrid context tests succesvol!")
        return True

    except Exception as e:
        print(f"\n❌ Test gefaald: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_hybrid_context_workflow()
    if success:
        print("\n✅ Hybrid context system is operationeel!")
    else:
        print("\n❌ Hybrid context system heeft problemen.")
        sys.exit(1)
