"""
Prompt Debug Section voor het tonen van gebruikte prompts.

Dit component toont de exacte prompts die naar GPT zijn gestuurd
voor analyse en debugging doeleinden.
"""

import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class PromptDebugSection:
    """Component voor het tonen en analyseren van AI prompts."""

    @staticmethod
    def render(
        generation_result: Any | None = None,
        voorbeelden_prompts: dict[str, str] | None = None,
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

            # Verzamel alle prompts voor tabs
            all_prompts = {}

            # Voeg definitie generatie prompt toe
            if generation_result and hasattr(generation_result, "prompt_template"):
                all_prompts["📝 Definitie Generatie"] = (
                    generation_result.prompt_template
                )

            # Voeg voorbeelden prompts toe
            if voorbeelden_prompts:
                for example_type, prompt in voorbeelden_prompts.items():
                    # Maak mooiere tab namen
                    tab_name = example_type
                    if example_type == "sentence":
                        tab_name = "📄 Voorbeeldzinnen"
                    elif example_type == "practical":
                        tab_name = "💼 Praktijkvoorbeelden"
                    elif example_type == "counter":
                        tab_name = "❌ Tegenvoorbeelden"
                    elif example_type == "synonyms":
                        tab_name = "🔄 Synoniemen"
                    elif example_type == "antonyms":
                        tab_name = "↔️ Antoniemen"
                    elif example_type == "clarifications":
                        tab_name = "💡 Toelichting"
                    else:
                        tab_name = f"📌 {example_type.title()}"

                    all_prompts[tab_name] = prompt

            # Toon alle prompts in tabs
            if all_prompts:
                tabs = st.tabs(list(all_prompts.keys()))

                for i, (tab_name, prompt) in enumerate(all_prompts.items()):
                    with tabs[i]:
                        # Toon prompt in code block
                        st.code(prompt, language="text")

                        # Prompt statistieken
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Prompt lengte", f"{len(prompt):,} karakters")
                        with col2:
                            st.metric("Geschatte tokens", f"~{len(prompt) // 4:,}")

                        # Download knop
                        file_name = (
                            tab_name.replace(" ", "_")
                            .replace("📝", "")
                            .replace("📄", "")
                            .replace("💼", "")
                            .replace("❌", "")
                            .replace("🔄", "")
                            .replace("↔️", "")
                            .replace("💡", "")
                            .replace("📌", "")
                            .strip()
                        )
                        st.download_button(
                            label=f"⬇️ Download {tab_name} Prompt",
                            data=prompt,
                            file_name=f"{file_name}_prompt.txt",
                            mime="text/plain",
                            key=f"download_{file_name}_prompt",
                        )

                        # Context metadata alleen voor definitie generatie
                        if "Definitie Generatie" in tab_name and generation_result:
                            if (
                                hasattr(generation_result, "context")
                                and generation_result.context
                            ):
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
            else:
                st.info("Geen prompt informatie beschikbaar voor deze generatie.")

            # Algemene prompt statistieken
            if all_prompts:
                st.markdown("#### 📈 Algemene Statistieken")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Totaal Prompts", len(all_prompts))

                with col2:
                    total_chars = sum(len(p) for p in all_prompts.values())
                    st.metric("Totale Lengte", f"{total_chars:,} chars")

                with col3:
                    total_tokens = sum(len(p) // 4 for p in all_prompts.values())
                    st.metric("Geschatte Tokens", f"~{total_tokens:,}")

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
                st.selectbox("Model", ["gpt-4.1", "gpt-4"], key="test_model")

            with col2:
                st.slider(
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
    begrip: str, definitie: str, context_dict: dict[str, list[str]]
) -> dict[str, str]:
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
        ExampleRequest,
        ExampleType,
        UnifiedExamplesGenerator,
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
