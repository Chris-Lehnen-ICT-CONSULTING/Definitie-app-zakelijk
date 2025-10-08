# Classification Pre-Processing - Implementation Code Examples

**Supplement to:** ONTOLOGICAL_CLASSIFICATION_PRE_PROCESSING_PATTERN_ANALYSIS.md
**Date:** 2025-10-07
**Pattern:** Pipeline Pattern met Pre-Processing Layer (Optie B)

---

## 1. ServiceAdapter Extension

### 1.1 Core Classification Methods

```python
# src/services/adapters/definition_service_adapter.py

from typing import List, Dict, Tuple, Optional
from services.classification.ontology_classifier import (
    OntologyClassifierService,
    ClassificationResult
)
from services.interfaces import GenerationRequest, DefinitionResponseV2
import logging

logger = logging.getLogger(__name__)


class DefinitionServiceAdapter:
    """
    Facade voor definitie generatie met classificatie pre-processing.

    Implements Pipeline Pattern:
    1. Pre-processing: classify_begrip() (standalone)
    2. Core processing: generate_definition() (requires category)
    3. Convenience: classify_and_generate() (all-in-one)
    """

    def __init__(self, container):
        """Initialize adapter met service dependencies."""
        self.container = container
        self.classifier = container.ontology_classifier()
        self.orchestrator = container.definition_orchestrator_v2()
        logger.info("DefinitionServiceAdapter initialized with pre-processing pipeline")

    # =========================================================================
    # PRE-PROCESSING LAYER: Classification (standalone, reusable)
    # =========================================================================

    def classify_begrip(
        self,
        begrip: str,
        definitie: str = "",
        context: Optional[str] = None,
        voorbeelden: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Pre-processing step: Classificeer begrip naar ontologische categorie.

        Dit is een STANDALONE operation - generatie is NIET vereist.

        Use cases:
        - Preview classificatie VOOR definitie generatie
        - Batch classificatie zonder generatie (corpus analyse)
        - Validatie van bestaande definities
        - Override preview voor gebruiker

        Args:
            begrip: Te classificeren begrip (required)
            definitie: Bestaande definitie (optional, voor context)
            context: Extra context informatie (optional)
            voorbeelden: Voorbeeldzinnen (optional)

        Returns:
            ClassificationResult met:
            - level: TYPE/EXEMPLAAR/PROCES/RESULTAAT/ONBESLIST
            - confidence: 0.0-1.0
            - rationale: Uitleg van classificatie
            - linguistic_cues: Gevonden taalkundige indicatoren
            - validation_warnings: Eventuele waarschuwingen

        Example:
            >>> adapter = container.definition_service_adapter()
            >>> result = adapter.classify_begrip(
            ...     begrip="verificatie",
            ...     definitie="",
            ...     context="identiteitscontrole"
            ... )
            >>> print(f"{result.level} ({result.confidence:.0%})")
            PROCES (85%)
        """
        logger.info(f"[PRE-PROCESSING] Classificatie voor begrip: '{begrip}'")

        try:
            result = self.classifier.classify(
                begrip=begrip,
                definitie=definitie,
                context=context,
                voorbeelden=voorbeelden
            )

            logger.info(
                f"[PRE-PROCESSING] Classificatie resultaat: "
                f"{result.level} (confidence: {result.confidence:.0%})"
            )

            if result.validation_warnings:
                logger.warning(
                    f"[PRE-PROCESSING] Validatie warnings: "
                    f"{len(result.validation_warnings)}"
                )

            return result

        except Exception as e:
            logger.error(f"[PRE-PROCESSING] Classificatie failed: {e}", exc_info=True)
            raise

    def batch_classify_begrippen(
        self,
        items: List[Dict[str, str]]
    ) -> List[ClassificationResult]:
        """
        Batch classificatie voor corpus analyse of bulk operations.

        EFFICIENT: Classificeert 100 begrippen ZONDER definitie generatie.
        Cost: ~$1 voor 100 items (vs $10 via generatie route)

        Args:
            items: List van dictionaries met keys:
                - "begrip": Te classificeren begrip (required)
                - "definitie": Bestaande definitie (optional)
                - "context": Extra context (optional)
                - "voorbeelden": List van voorbeeldzinnen (optional)

        Returns:
            List van ClassificationResult objecten (zelfde volgorde als input)

        Example:
            >>> items = [
            ...     {"begrip": "verificatie", "definitie": ""},
            ...     {"begrip": "validatie", "definitie": ""},
            ...     {"begrip": "sanctie", "definitie": ""}
            ... ]
            >>> results = adapter.batch_classify_begrippen(items)
            >>> for item, result in zip(items, results):
            ...     print(f"{item['begrip']}: {result.level}")
            verificatie: PROCES
            validatie: PROCES
            sanctie: RESULTAAT
        """
        logger.info(f"[BATCH PRE-PROCESSING] Classificatie voor {len(items)} begrippen")

        try:
            results = self.classifier.classify_batch(items)

            # Stats logging
            stats = {}
            for result in results:
                stats[result.level] = stats.get(result.level, 0) + 1

            logger.info(
                f"[BATCH PRE-PROCESSING] Verdeling: "
                + ", ".join(f"{k}={v}" for k, v in stats.items())
            )

            return results

        except Exception as e:
            logger.error(f"[BATCH PRE-PROCESSING] Batch classificatie failed: {e}", exc_info=True)
            raise

    # =========================================================================
    # CORE PROCESSING: Definition Generation (requires category from pre-processing)
    # =========================================================================

    async def generate_definition(
        self,
        request: GenerationRequest
    ) -> DefinitionResponseV2:
        """
        Core processing: Genereer definitie met VERPLICHTE ontologische categorie.

        REQUIRES: request.ontologische_categorie MUST be set via pre-processing!

        Pipeline flow:
        1. [PRE-PROCESSING] classify_begrip() → ClassificationResult
        2. [REQUEST BUILD] Build GenerationRequest(ontologische_categorie=result.level)
        3. [CORE PROCESSING] generate_definition(request) ← YOU ARE HERE

        Args:
            request: GenerationRequest with:
                - begrip: Te definiëren begrip (required)
                - ontologische_categorie: TYPE/EXEMPLAAR/PROCES/RESULTAAT (REQUIRED!)
                - organisatorische_context: Context info (optional)
                - juridische_context: Juridische context (optional)
                - wettelijke_basis: Wettelijke basis (optional)

        Returns:
            DefinitionResponseV2 met:
            - success: True/False
            - definition: Definition object (if success)
            - validation_result: ValidationResult
            - metadata: Generation metadata

        Raises:
            ValueError: Als ontologische_categorie ontbreekt

        Example:
            >>> # STAP 1: Classificeer eerst
            >>> result = adapter.classify_begrip("verificatie", "", "identiteit")
            >>>
            >>> # STAP 2: Build request met categorie
            >>> request = GenerationRequest(
            ...     begrip="verificatie",
            ...     ontologische_categorie=result.level,  # VERPLICHT!
            ...     organisatorische_context=["identiteitscontrole"]
            ... )
            >>>
            >>> # STAP 3: Genereer definitie
            >>> response = await adapter.generate_definition(request)
        """
        # VALIDATION: Category is REQUIRED
        if not request.ontologische_categorie:
            error_msg = (
                "ontologische_categorie is VERPLICHT voor definitie generatie. "
                "Pipeline flow: "
                "1. Call classify_begrip() eerst om categorie te bepalen, "
                "2. Build GenerationRequest met result.level, "
                "3. Call generate_definition(request). "
                "Of gebruik classify_and_generate() voor convenience."
            )
            logger.error(f"[CORE PROCESSING] Validation failed: {error_msg}")
            raise ValueError(error_msg)

        logger.info(
            f"[CORE PROCESSING] Definitie generatie gestart: "
            f"begrip='{request.begrip}', category='{request.ontologische_categorie}'"
        )

        try:
            # Call orchestrator met gecategoriseerde request
            response = await self.orchestrator.create_definition(request)

            logger.info(
                f"[CORE PROCESSING] Definitie generatie {'succeeded' if response.success else 'failed'}"
            )

            return response

        except Exception as e:
            logger.error(f"[CORE PROCESSING] Generatie failed: {e}", exc_info=True)
            raise

    # =========================================================================
    # CONVENIENCE LAYER: All-in-one (auto classify + generate)
    # =========================================================================

    async def classify_and_generate(
        self,
        begrip: str,
        context_dict: Dict[str, Any],
        auto_classify: bool = True,
        override_category: Optional[str] = None
    ) -> Tuple[ClassificationResult, DefinitionResponseV2]:
        """
        Convenience method: Classificeer + genereer in één call.

        Gebruik dit voor:
        - Simpele use cases (1 begrip, geen preview nodig)
        - Scripts/automation
        - Backward compatibility met oude API

        Gebruik NIET voor:
        - Preview + override scenarios (gebruik pipeline: classify → preview → generate)
        - Batch processing (gebruik batch_classify_begrippen)
        - Corpus analyse (gebruik classify_begrip in loop)

        Args:
            begrip: Te definiëren begrip
            context_dict: Context dictionary met keys:
                - "organisatorisch": List[str]
                - "juridisch": List[str]
                - "wettelijk": List[str]
                - "context": str (voor classificatie)
            auto_classify: True = automatisch classificeren, False = gebruik override
            override_category: Handmatige category override (skipt AI classificatie)

        Returns:
            Tuple van (ClassificationResult, DefinitionResponseV2)

        Example (Auto classify):
            >>> result, response = await adapter.classify_and_generate(
            ...     begrip="verificatie",
            ...     context_dict={
            ...         "organisatorisch": ["identiteitscontrole"],
            ...         "juridisch": ["AVG"],
            ...         "context": "identiteitsverificatie"
            ...     }
            ... )
            >>> print(f"Category: {result.level}, Valid: {response.definition.valid}")
            Category: PROCES, Valid: True

        Example (Override):
            >>> result, response = await adapter.classify_and_generate(
            ...     begrip="verificatie",
            ...     context_dict={...},
            ...     auto_classify=False,
            ...     override_category="RESULTAAT"
            ... )
        """
        logger.info(
            f"[CONVENIENCE] classify_and_generate: begrip='{begrip}', "
            f"auto_classify={auto_classify}, override={override_category}"
        )

        # STAP 1: Classificatie (pre-processing)
        if override_category:
            # Mock result voor override scenario
            logger.info(f"[CONVENIENCE] Using manual override: {override_category}")
            classification = ClassificationResult(
                term=begrip,
                definition="",
                level=override_category,
                confidence=1.0,
                rationale="Handmatig overschreven door gebruiker",
                linguistic_cues=[]
            )
        else:
            logger.info(f"[CONVENIENCE] Auto-classifying begrip")
            classification = self.classify_begrip(
                begrip=begrip,
                definitie="",
                context=context_dict.get("context")
            )

        # STAP 2: Build request
        logger.info(f"[CONVENIENCE] Building GenerationRequest with category={classification.level}")
        request = GenerationRequest(
            begrip=begrip,
            ontologische_categorie=classification.level,
            organisatorische_context=context_dict.get("organisatorisch", []),
            juridische_context=context_dict.get("juridisch", []),
            wettelijke_basis=context_dict.get("wettelijk", [])
        )

        # STAP 3: Generate definitie
        logger.info(f"[CONVENIENCE] Calling generate_definition")
        response = await self.generate_definition(request)

        logger.info(
            f"[CONVENIENCE] classify_and_generate completed: "
            f"category={classification.level}, success={response.success}"
        )

        return classification, response
```

---

## 2. UI Integration - 3-Step Flow

### 2.1 DefinitieGeneratieTab (Streamlit)

```python
# src/ui/components/tabs/definitie_generatie_tab.py

import streamlit as st
from typing import Optional
from services.adapters.definition_service_adapter import DefinitionServiceAdapter
from services.classification.ontology_classifier import ClassificationResult
from services.interfaces import GenerationRequest
import logging

logger = logging.getLogger(__name__)


class DefinitieGeneratieTab:
    """
    Tab voor definitie generatie met 3-step pipeline:
    1. Classificeer begrip (pre-processing)
    2. Preview + override (transparency + control)
    3. Genereer definitie (core processing)
    """

    def __init__(self, container):
        self.container = container
        self.adapter = DefinitionServiceAdapter(container)

    def render(self):
        """Render de 3-step pipeline UI."""
        st.header("📝 Definitie Generatie")
        st.markdown("---")

        # =====================================================================
        # INPUT SECTION
        # =====================================================================
        st.subheader("1️⃣ Input")

        col1, col2 = st.columns([2, 1])

        with col1:
            begrip = st.text_input(
                "Begrip *",
                key="begrip_input",
                placeholder="bijv. verificatie, validatie, sanctie"
            )

        with col2:
            # Quick examples dropdown
            example = st.selectbox(
                "Of kies voorbeeld",
                options=["", "verificatie", "validatie", "sanctie", "registratie"],
                key="example_select"
            )
            if example:
                st.session_state.begrip_input = example
                begrip = example

        context = st.text_area(
            "Context (optioneel)",
            key="context_input",
            placeholder="bijv. identiteitscontrole, handhaving, toezicht",
            height=100
        )

        # =====================================================================
        # STAP 1: CLASSIFICATIE (PRE-PROCESSING)
        # =====================================================================
        st.markdown("---")
        st.subheader("2️⃣ Classificatie (Pre-processing)")

        col1, col2 = st.columns([1, 3])

        with col1:
            classify_btn = st.button(
                "🔍 Classificeer",
                key="classify_btn",
                use_container_width=True,
                type="primary"
            )

        with col2:
            st.caption(
                "💡 Tip: Classificatie bepaalt de promptopbouw. "
                "Preview eerst voordat je genereert!"
            )

        if classify_btn:
            if not begrip:
                st.error("⚠️ Begrip is verplicht")
                return

            with st.spinner("🔄 Classificeren..."):
                try:
                    # PRE-PROCESSING: Classify ZONDER definitie generatie
                    result = self.adapter.classify_begrip(
                        begrip=begrip,
                        definitie="",  # Nog geen definitie (pre-processing!)
                        context=context if context else None
                    )

                    # Store in session state
                    st.session_state.classification_result = result
                    st.session_state.override_category = None  # Reset override

                    logger.info(f"Classification succeeded: {result.level}")
                    st.success("✅ Classificatie voltooid!")

                except Exception as e:
                    logger.error(f"Classification failed: {e}", exc_info=True)
                    st.error(f"❌ Classificatie gefaald: {str(e)}")
                    return

        # =====================================================================
        # STAP 2: CLASSIFICATIE PREVIEW & OVERRIDE
        # =====================================================================
        if "classification_result" in st.session_state:
            result: ClassificationResult = st.session_state.classification_result

            st.markdown("---")
            st.subheader("📊 Classificatie Resultaat")

            # METRICS ROW
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Category met emoji
                emoji_map = {
                    "TYPE": "📦",
                    "EXEMPLAAR": "🎯",
                    "PROCES": "⚙️",
                    "RESULTAAT": "✅",
                    "ONBESLIST": "❓"
                }
                st.metric(
                    "Categorie",
                    f"{emoji_map.get(result.level, '?')} {result.level}"
                )

            with col2:
                # Confidence met color coding
                confidence_pct = result.confidence * 100
                confidence_color = (
                    "🟢" if confidence_pct >= 80
                    else "🟡" if confidence_pct >= 60
                    else "🔴"
                )
                st.metric(
                    "Confidence",
                    f"{confidence_color} {confidence_pct:.0f}%"
                )

            with col3:
                # Warnings count
                warning_count = len(result.validation_warnings)
                warning_icon = "⚠️" if warning_count > 0 else "✅"
                st.metric(
                    "Warnings",
                    f"{warning_icon} {warning_count}"
                )

            with col4:
                # Linguistic cues count
                cue_count = len(result.linguistic_cues)
                st.metric(
                    "Cues",
                    f"📝 {cue_count}"
                )

            # RATIONALE EXPANDER
            with st.expander("🔍 Rationale & Details", expanded=True):
                st.write("**Rationale:**")
                st.info(result.rationale)

                if result.linguistic_cues:
                    st.write("**Linguistic Cues:**")
                    for cue in result.linguistic_cues:
                        st.write(f"- {cue}")

                if result.validation_warnings:
                    st.write("**⚠️ Validation Warnings:**")
                    for warning in result.validation_warnings:
                        st.warning(warning)

            # OVERRIDE SECTION
            st.markdown("---")
            st.subheader("✏️ Override (Optioneel)")

            override_col1, override_col2 = st.columns([2, 1])

            with override_col1:
                override_options = [
                    f"✅ Gebruik AI suggestie ({result.level})",
                    "📦 TYPE",
                    "🎯 EXEMPLAAR",
                    "⚙️ PROCES",
                    "✅ RESULTAAT"
                ]

                override_select = st.selectbox(
                    "Kies categorie voor generatie",
                    options=override_options,
                    key="override_select"
                )

                # Parse selected category
                if override_select.startswith("✅ Gebruik"):
                    final_category = result.level
                    st.session_state.override_category = None
                else:
                    # Extract category name (after emoji)
                    final_category = override_select.split(" ", 1)[1]
                    st.session_state.override_category = final_category

            with override_col2:
                if st.session_state.get("override_category"):
                    st.info(f"✓ Override actief:\n{st.session_state.override_category}")
                else:
                    st.success(f"✓ AI suggestie:\n{result.level}")

            # PROMPT PREVIEW (Advanced)
            with st.expander("🔬 Advanced: Prompt Preview"):
                category_for_preview = st.session_state.get("override_category", result.level)
                st.write(f"**Categorie voor prompt:** {category_for_preview}")
                st.write("**Template sectie die gebruikt zal worden:**")

                # Show which prompt template will be used
                template_map = {
                    "PROCES": "Focus op HANDELING en VERLOOP (wie doet wat, hoe verloopt het)",
                    "TYPE": "Focus op CLASSIFICATIE en KENMERKEN (soort, categorie)",
                    "RESULTAAT": "Focus op OORSPRONG en GEVOLG (waar komt het vandaan)",
                    "EXEMPLAAR": "Focus op SPECIFICITEIT (specifiek geval, individueel)"
                }
                st.code(template_map.get(category_for_preview, "Basis template"), language="text")

        # =====================================================================
        # STAP 3: DEFINITIE GENERATIE
        # =====================================================================
        st.markdown("---")
        st.subheader("3️⃣ Definitie Generatie")

        # Check if classification is done
        classification_done = "classification_result" in st.session_state

        if not classification_done:
            st.info("ℹ️ Classificeer eerst het begrip voordat je genereert!")

        generate_col1, generate_col2 = st.columns([1, 3])

        with generate_col1:
            generate_btn = st.button(
                "✨ Genereer Definitie",
                key="generate_btn",
                use_container_width=True,
                type="primary",
                disabled=not classification_done
            )

        with generate_col2:
            if classification_done:
                result = st.session_state.classification_result
                final_cat = st.session_state.get("override_category", result.level)
                st.caption(
                    f"💡 Generatie zal {final_cat} template gebruiken "
                    f"({'override' if st.session_state.get('override_category') else 'AI suggestie'})"
                )

        if generate_btn:
            if not classification_done:
                st.error("⚠️ Classificeer eerst het begrip!")
                return

            with st.spinner("🔄 Genereren..."):
                try:
                    result = st.session_state.classification_result
                    final_category = st.session_state.get("override_category", result.level)

                    # Build request met classificatie
                    request = GenerationRequest(
                        begrip=begrip,
                        ontologische_categorie=final_category,
                        organisatorische_context=[context] if context else []
                    )

                    # CORE PROCESSING: Generate definitie
                    response = await self.adapter.generate_definition(request)

                    if response.success:
                        st.success("✅ Definitie gegenereerd!")

                        # Display definitie
                        st.markdown("---")
                        st.subheader("📄 Gegenereerde Definitie")
                        st.write(response.definition.definitie)

                        # Display validation
                        if response.definition.valid:
                            st.success("✅ Validatie geslaagd")
                        else:
                            st.warning(f"⚠️ Validatie: {len(response.definition.validation_violations)} issues")
                            with st.expander("Validatie details"):
                                for violation in response.definition.validation_violations:
                                    st.write(f"- {violation}")

                        # Store in session state
                        st.session_state.generated_definition = response.definition

                    else:
                        st.error(f"❌ Generatie gefaald: {response.error}")

                except Exception as e:
                    logger.error(f"Generation failed: {e}", exc_info=True)
                    st.error(f"❌ Generatie gefaald: {str(e)}")
```

---

## 3. Batch Processing Script

### 3.1 Corpus Analyse Script

```python
# scripts/batch_classify_corpus.py

"""
Batch classificatie van wetgeving corpus.

Use case: Analyseer 1000 begrippen uit wetgeving zonder definitie generatie.
Cost: ~$10 (vs $100 via generatie route)
Time: ~10 minuten (vs 2 uur)
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime

from utils.container_manager import get_cached_container
from services.adapters.definition_service_adapter import DefinitionServiceAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_wetgeving_corpus() -> List[Dict[str, str]]:
    """
    Load corpus from CSV/JSON file.

    Expected format:
    - begrip: str
    - definitie: str (optional)
    - context: str (optional)
    """
    corpus_path = Path("data/wetgeving_corpus.csv")

    if not corpus_path.exists():
        logger.warning(f"Corpus niet gevonden: {corpus_path}")
        # Generate sample data
        return [
            {"begrip": "verificatie", "definitie": "Het controleren van juistheid", "context": "identiteit"},
            {"begrip": "validatie", "definitie": "Het bevestigen van geldigheid", "context": "documenten"},
            {"begrip": "sanctie", "definitie": "Maatregel na overtreding", "context": "handhaving"},
            # ... etc
        ]

    df = pd.read_csv(corpus_path)
    return df.to_dict('records')


def analyse_verdeling(results: List) -> Dict[str, any]:
    """Analyseer verdeling van categorieën."""
    stats = {
        "TYPE": 0,
        "EXEMPLAAR": 0,
        "PROCES": 0,
        "RESULTAAT": 0,
        "ONBESLIST": 0
    }

    total = len(results)
    confidence_sum = 0.0

    for result in results:
        stats[result.level] += 1
        confidence_sum += result.confidence

    return {
        "verdeling": stats,
        "totaal": total,
        "avg_confidence": confidence_sum / total if total > 0 else 0.0
    }


def export_results(results: List, corpus: List[Dict], output_path: Path):
    """Export classificatie resultaten naar CSV."""
    data = []
    for item, result in zip(corpus, results):
        data.append({
            "begrip": item["begrip"],
            "definitie": item.get("definitie", ""),
            "context": item.get("context", ""),
            "classificatie": result.level,
            "confidence": result.confidence,
            "rationale": result.rationale,
            "warnings": "; ".join(result.validation_warnings) if result.validation_warnings else ""
        })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Resultaten geëxporteerd naar: {output_path}")


def main():
    """Main batch classificatie workflow."""
    logger.info("=" * 80)
    logger.info("BATCH CLASSIFICATIE - Wetgeving Corpus")
    logger.info("=" * 80)

    # Load corpus
    logger.info("Loading corpus...")
    corpus = load_wetgeving_corpus()
    logger.info(f"Corpus loaded: {len(corpus)} begrippen")

    # Initialize adapter
    logger.info("Initializing service adapter...")
    container = get_cached_container()
    adapter = DefinitionServiceAdapter(container)

    # Prepare items for batch classification
    items = [
        {
            "begrip": item["begrip"],
            "definitie": item.get("definitie", ""),
            "context": item.get("context")
        }
        for item in corpus
    ]

    # BATCH CLASSIFY (NO definition generation!)
    logger.info(f"\nClassificeren {len(items)} begrippen...")
    logger.info("Dit gebruikt ALLEEN classificatie (GEEN definitie generatie)")
    logger.info("-" * 80)

    start_time = datetime.now()

    try:
        results = adapter.batch_classify_begrippen(items)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n✅ Classificatie voltooid in {duration:.1f} seconden")

    except Exception as e:
        logger.error(f"❌ Batch classificatie gefaald: {e}", exc_info=True)
        return

    # Analyse verdeling
    logger.info("\n" + "=" * 80)
    logger.info("ANALYSE RESULTATEN")
    logger.info("=" * 80)

    stats = analyse_verdeling(results)

    logger.info(f"\n📊 Verdeling categorieën (totaal: {stats['totaal']}):")
    logger.info("-" * 80)
    for category, count in stats["verdeling"].items():
        pct = (count / stats['totaal']) * 100 if stats['totaal'] > 0 else 0
        bar = "█" * int(pct / 2)  # Visual bar (50 = 100%)
        logger.info(f"{category:12} {count:4d} ({pct:5.1f}%) {bar}")

    logger.info(f"\n📈 Average confidence: {stats['avg_confidence']:.1%}")

    # Export results
    output_path = Path(f"output/classificatie_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    output_path.parent.mkdir(exist_ok=True)
    export_results(results, corpus, output_path)

    logger.info("\n" + "=" * 80)
    logger.info("VOLTOOID")
    logger.info("=" * 80)
    logger.info(f"Resultaten: {output_path}")
    logger.info(f"Duur: {duration:.1f} seconden")
    logger.info(f"Begrippen: {len(results)}")
    logger.info(f"Snelheid: {len(results) / duration:.1f} begrippen/seconde")


if __name__ == "__main__":
    main()
```

**Expected output:**

```
================================================================================
BATCH CLASSIFICATIE - Wetgeving Corpus
================================================================================
Loading corpus...
Corpus loaded: 1000 begrippen
Initializing service adapter...
[PRE-PROCESSING] Batch classificatie voor 1000 begrippen

Classificeren 1000 begrippen...
Dit gebruikt ALLEEN classificatie (GEEN definitie generatie)
--------------------------------------------------------------------------------

✅ Classificatie voltooid in 587.3 seconden

================================================================================
ANALYSE RESULTATEN
================================================================================

📊 Verdeling categorieën (totaal: 1000):
--------------------------------------------------------------------------------
TYPE          450 (45.0%) ██████████████████████
PROCES        280 (28.0%) ██████████████
RESULTAAT     180 (18.0%) █████████
EXEMPLAAR      75 ( 7.5%) ███
ONBESLIST      15 ( 1.5%)

📈 Average confidence: 82.3%

================================================================================
VOLTOOID
================================================================================
Resultaten: output/classificatie_results_20251007_143052.csv
Duur: 587.3 seconden
Begrippen: 1000
Snelheid: 1.7 begrippen/seconde
```

---

## 4. Validation Script

### 4.1 Check Bestaande Definities

```python
# scripts/validate_existing_definitions.py

"""
Valideer ontologische categorieën van bestaande definities.

Use case: Check of 500 bestaande definities in database de juiste categorie hebben.
"""

import logging
from pathlib import Path
from typing import List, Dict
import pandas as pd

from database.repository import DefinitionRepository
from utils.container_manager import get_cached_container
from services.adapters.definition_service_adapter import DefinitionServiceAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_definitions():
    """Valideer alle definities in database."""
    logger.info("=" * 80)
    logger.info("VALIDATIE - Bestaande Definities")
    logger.info("=" * 80)

    # Initialize services
    container = get_cached_container()
    adapter = DefinitionServiceAdapter(container)
    repository = container.definition_repository()

    # Load alle definities
    logger.info("Loading definities from database...")
    definitions = repository.get_all()
    logger.info(f"Gevonden: {len(definitions)} definities")

    # Validate each
    mismatches = []
    correct = 0

    logger.info("\nValideren...")
    for i, definitie in enumerate(definitions, 1):
        if i % 50 == 0:
            logger.info(f"Progress: {i}/{len(definitions)}")

        # Re-classify
        result = adapter.classify_begrip(
            begrip=definitie.begrip,
            definitie=definitie.definitie
        )

        # Compare
        if result.level != definitie.ontologische_categorie:
            mismatches.append({
                "id": definitie.id,
                "begrip": definitie.begrip,
                "stored_category": definitie.ontologische_categorie,
                "ai_category": result.level,
                "confidence": result.confidence,
                "rationale": result.rationale
            })
        else:
            correct += 1

    # Report
    logger.info("\n" + "=" * 80)
    logger.info("RESULTATEN")
    logger.info("=" * 80)
    logger.info(f"\n✅ Correct: {correct}/{len(definitions)} ({correct/len(definitions)*100:.1f}%)")
    logger.info(f"⚠️ Mismatches: {len(mismatches)}/{len(definitions)} ({len(mismatches)/len(definitions)*100:.1f}%)")

    if mismatches:
        logger.info("\n⚠️ MISMATCHES:")
        logger.info("-" * 80)
        for mm in mismatches[:10]:  # Show first 10
            logger.info(
                f"ID {mm['id']:4d} | {mm['begrip']:20s} | "
                f"DB: {mm['stored_category']:10s} → AI: {mm['ai_category']:10s} "
                f"(confidence: {mm['confidence']:.0%})"
            )

        if len(mismatches) > 10:
            logger.info(f"... en {len(mismatches) - 10} meer")

        # Export voor review
        df = pd.DataFrame(mismatches)
        output_path = Path("output/classification_mismatches.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"\nVolledige lijst: {output_path}")

    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    validate_definitions()
```

---

## 5. Tests

### 5.1 ServiceAdapter Tests

```python
# tests/services/adapters/test_definition_service_adapter_classification.py

import pytest
from unittest.mock import Mock, AsyncMock
from services.adapters.definition_service_adapter import DefinitionServiceAdapter
from services.classification.ontology_classifier import ClassificationResult
from services.interfaces import GenerationRequest, DefinitionResponseV2


@pytest.fixture
def mock_container():
    """Mock container met services."""
    container = Mock()

    # Mock classifier
    classifier = Mock()
    container.ontology_classifier.return_value = classifier

    # Mock orchestrator
    orchestrator = Mock()
    container.definition_orchestrator_v2.return_value = orchestrator

    return container


@pytest.fixture
def adapter(mock_container):
    """Create adapter instance."""
    return DefinitionServiceAdapter(mock_container)


class TestClassificationPreProcessing:
    """Test classificatie pre-processing functionality."""

    def test_classify_begrip_success(self, adapter, mock_container):
        """Test standalone classificatie."""
        # Arrange
        classifier = mock_container.ontology_classifier()
        expected_result = ClassificationResult(
            term="verificatie",
            definition="",
            level="PROCES",
            confidence=0.85,
            rationale="Het begrip beschrijft een handeling",
            linguistic_cues=["verificatie", "controleren"]
        )
        classifier.classify.return_value = expected_result

        # Act
        result = adapter.classify_begrip(
            begrip="verificatie",
            definitie="",
            context="identiteitscontrole"
        )

        # Assert
        assert result.level == "PROCES"
        assert result.confidence == 0.85
        classifier.classify.assert_called_once_with(
            begrip="verificatie",
            definitie="",
            context="identiteitscontrole",
            voorbeelden=None
        )

    def test_batch_classify(self, adapter, mock_container):
        """Test batch classificatie."""
        # Arrange
        classifier = mock_container.ontology_classifier()
        items = [
            {"begrip": "verificatie", "definitie": ""},
            {"begrip": "sanctie", "definitie": ""}
        ]
        expected_results = [
            ClassificationResult(term="verificatie", definition="", level="PROCES", confidence=0.85, rationale="", linguistic_cues=[]),
            ClassificationResult(term="sanctie", definition="", level="RESULTAAT", confidence=0.90, rationale="", linguistic_cues=[])
        ]
        classifier.classify_batch.return_value = expected_results

        # Act
        results = adapter.batch_classify_begrippen(items)

        # Assert
        assert len(results) == 2
        assert results[0].level == "PROCES"
        assert results[1].level == "RESULTAAT"

    @pytest.mark.asyncio
    async def test_generate_definition_requires_category(self, adapter):
        """Test dat generate_definition categorie vereist."""
        # Arrange
        request = GenerationRequest(
            begrip="verificatie",
            ontologische_categorie=None  # MISSING!
        )

        # Act & Assert
        with pytest.raises(ValueError, match="ontologische_categorie is VERPLICHT"):
            await adapter.generate_definition(request)

    @pytest.mark.asyncio
    async def test_generate_definition_with_category_success(self, adapter, mock_container):
        """Test generate_definition met valide categorie."""
        # Arrange
        orchestrator = mock_container.definition_orchestrator_v2()
        request = GenerationRequest(
            begrip="verificatie",
            ontologische_categorie="PROCES"  # SET!
        )
        expected_response = DefinitionResponseV2(success=True)
        orchestrator.create_definition = AsyncMock(return_value=expected_response)

        # Act
        response = await adapter.generate_definition(request)

        # Assert
        assert response.success
        orchestrator.create_definition.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_classify_and_generate_auto(self, adapter, mock_container):
        """Test classify_and_generate met auto classificatie."""
        # Arrange
        classifier = mock_container.ontology_classifier()
        orchestrator = mock_container.definition_orchestrator_v2()

        # Mock classificatie
        classification = ClassificationResult(
            term="verificatie",
            definition="",
            level="PROCES",
            confidence=0.85,
            rationale="",
            linguistic_cues=[]
        )
        classifier.classify.return_value = classification

        # Mock generatie
        response = DefinitionResponseV2(success=True)
        orchestrator.create_definition = AsyncMock(return_value=response)

        # Act
        result_class, result_resp = await adapter.classify_and_generate(
            begrip="verificatie",
            context_dict={"context": "identiteit"}
        )

        # Assert
        assert result_class.level == "PROCES"
        assert result_resp.success

    @pytest.mark.asyncio
    async def test_classify_and_generate_override(self, adapter, mock_container):
        """Test classify_and_generate met manual override."""
        # Arrange
        orchestrator = mock_container.definition_orchestrator_v2()
        response = DefinitionResponseV2(success=True)
        orchestrator.create_definition = AsyncMock(return_value=response)

        # Act
        result_class, result_resp = await adapter.classify_and_generate(
            begrip="verificatie",
            context_dict={},
            override_category="RESULTAAT"  # Override AI
        )

        # Assert
        assert result_class.level == "RESULTAAT"  # Override used
        assert result_class.rationale == "Handmatig overschreven door gebruiker"
        assert result_resp.success
```

---

**END OF CODE EXAMPLES**

This document provides complete implementation examples for the recommended Pipeline Pattern (Optie B).
