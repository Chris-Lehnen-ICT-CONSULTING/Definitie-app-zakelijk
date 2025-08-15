"""
Prompt Debug Section voor het tonen van gebruikte prompts.

Dit component toont de exacte prompts die naar GPT zijn gestuurd
voor analyse en debugging doeleinden.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PromptDebugSection:
    """Component voor het tonen en analyseren van AI prompts."""

    @staticmethod
    def render(
        generation_result: Optional[Any] = None,
        voorbeelden_prompts: Optional[Dict[str, str]] = None,
    ):
        """
        Render de prompt debug sectie.

        Args:
            generation_result: GenerationResult object met prompt_template
            voorbeelden_prompts: Dictionary met prompts per voorbeeld type
        """
        with st.expander("🔍 Debug: Gebruikte Prompts", expanded=False):
            st.markdown("### Prompts verzonden naar GPT")
            st.caption(
                "Deze sectie toont de exacte prompts die naar de AI zijn gestuurd voor analyse doeleinden."
            )

            # Definitie generatie prompt
            if generation_result and hasattr(generation_result, "prompt_template"):
                st.markdown("#### 📝 Definitie Generatie Prompt")

                # Toon prompt in code block voor makkelijk kopiëren
                st.code(generation_result.prompt_template, language="text")

                # Download knop
                st.download_button(
                    label="⬇️ Download Definitie Prompt",
                    data=generation_result.prompt_template,
                    file_name="definitie_prompt.txt",
                    mime="text/plain",
                    key="download_def_prompt",
                )

                # Toon metadata
                if hasattr(generation_result, "context") and generation_result.context:
                    st.markdown("##### 📊 Context Metadata")
                    context_dict = {
                        "begrip": generation_result.context.begrip,
                        "organisatorische_context": generation_result.context.organisatorische_context,
                        "juridische_context": generation_result.context.juridische_context,
                        "categorie": (
                            generation_result.context.categorie.value
                            if generation_result.context.categorie
                            else None
                        ),
                    }
                    st.json(context_dict)

            # Voorbeelden prompts
            if voorbeelden_prompts:
                st.markdown("#### 🎯 Voorbeelden Generatie Prompts")

                tabs = st.tabs(list(voorbeelden_prompts.keys()))

                for i, (example_type, prompt) in enumerate(voorbeelden_prompts.items()):
                    with tabs[i]:
                        st.code(prompt, language="text")

                        # Download knop per type
                        st.download_button(
                            label=f"⬇️ Download {example_type} Prompt",
                            data=prompt,
                            file_name=f"{example_type}_prompt.txt",
                            mime="text/plain",
                            key=f"download_{example_type}_prompt",
                        )

            # Prompt statistieken
            st.markdown("#### 📈 Prompt Statistieken")
            col1, col2, col3 = st.columns(3)

            with col1:
                if generation_result and hasattr(generation_result, "prompt_template"):
                    st.metric(
                        "Definitie Prompt Lengte",
                        f"{len(generation_result.prompt_template)} chars",
                    )

            with col2:
                if voorbeelden_prompts:
                    avg_length = sum(
                        len(p) for p in voorbeelden_prompts.values()
                    ) / len(voorbeelden_prompts)
                    st.metric("Gem. Voorbeeld Prompt", f"{int(avg_length)} chars")

            with col3:
                total_prompts = 1 if generation_result else 0
                total_prompts += len(voorbeelden_prompts) if voorbeelden_prompts else 0
                st.metric("Totaal Prompts", total_prompts)

            # Test prompt functionaliteit
            st.markdown("#### 🧪 Test Prompt")
            st.caption(
                "Kopieer een prompt hierboven en test met verschillende parameters."
            )

            test_prompt = st.text_area(
                "Test Prompt",
                height=200,
                placeholder="Plak hier een prompt om te testen...",
                key="test_prompt_input",
            )

            col1, col2 = st.columns(2)
            with col1:
                test_model = st.selectbox(
                    "Model", ["gpt-4", "gpt-3.5-turbo"], key="test_model"
                )

            with col2:
                test_temp = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.01,
                    step=0.01,
                    key="test_temp",
                )

            if st.button("🚀 Test Prompt", key="test_prompt_button"):
                if test_prompt:
                    st.info("Test functionaliteit wordt binnenkort toegevoegd...")
                else:
                    st.warning("Voer eerst een prompt in om te testen.")


def capture_voorbeelden_prompts(
    begrip: str, definitie: str, context_dict: Dict[str, List[str]]
) -> Dict[str, str]:
    """
    Capture alle prompts die gebruikt worden voor voorbeelden generatie.

    Args:
        begrip: Het begrip
        definitie: De definitie
        context_dict: Context dictionary

    Returns:
        Dictionary met prompts per voorbeeld type
    """
    from voorbeelden.unified_voorbeelden import (
        UnifiedExamplesGenerator,
        ExampleRequest,
        ExampleType,
    )

    generator = UnifiedExamplesGenerator()
    prompts = {}

    # Capture prompts voor elk type
    for example_type in ExampleType:
        request = ExampleRequest(
            begrip=begrip,
            definitie=definitie,
            context_dict=context_dict,
            example_type=example_type,
        )

        # Build prompt zonder het daadwerkelijk uit te voeren
        prompt = generator._build_prompt(request)
        prompts[example_type.value] = prompt

    return prompts
