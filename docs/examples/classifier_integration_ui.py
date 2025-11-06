"""
VOORBEELD: Ontological Classifier Integratie in UI

Dit bestand toont hoe de standalone OntologicalClassifier
VOOR definitie generatie wordt aangeroepen vanuit de UI.

FLOW:
    1. UI verzamelt begrip + contexten
    2. Roep classifier.classify() aan
    3. Toon result aan gebruiker (optioneel)
    4. Zet result.to_string_level() in GenerationRequest
    5. Genereer definitie (gebruikt categorie in prompt)
"""

import streamlit as st
from services.classification import ClassificationResult, OntologicalClassifier
from services.orchestrators.definition_orchestrator_v2 import GenerationRequest
from ui.session_state import SessionStateManager


def render_classification_step(
    classifier: OntologicalClassifier,
    begrip: str,
    org_context: str | None,
    jur_context: str | None,
) -> ClassificationResult:
    """
    Stap 1: Classificeer begrip VOOR definitie generatie

    Args:
        classifier: OntologicalClassifier instance (via DI)
        begrip: Te classificeren begrip
        org_context: Organisatorische context
        jur_context: Juridische context

    Returns:
        ClassificationResult met niveau + rationale
    """
    st.markdown("### 🔬 Ontologische Classificatie")

    with st.spinner(f"Classificeer '{begrip}' in U/F/O niveau..."):
        result = classifier.classify(
            begrip=begrip,
            organisatorische_context=org_context,
            juridische_context=jur_context,
        )

    # Toon result aan gebruiker
    _display_classification_result(result)

    # Cache in session state voor later gebruik
    SessionStateManager.set_value("last_classification", result)

    return result


def _display_classification_result(result: ClassificationResult):
    """Toon classificatie resultaat in UI"""

    # Header met niveau
    level_emoji = {
        "U": "🔷",  # Universeel
        "F": "🔶",  # Functioneel
        "O": "🟠",  # Operationeel
    }

    emoji = level_emoji.get(result.level.value, "⚪")
    st.success(
        f"{emoji} **Niveau: {result.level.value}** (Confidence: {result.confidence:.1%})"
    )

    # Confidence indicator
    confidence_color = {"high": "green", "medium": "orange", "low": "red"}
    color = confidence_color[result.confidence_level.value]

    st.markdown(
        f"**Betrouwbaarheid:** <span style='color: {color}'>{result.confidence_level.value.upper()}</span>",
        unsafe_allow_html=True,
    )

    # Rationale (uitleg waarom dit niveau)
    with st.expander("📖 Waarom dit niveau?"):
        st.write(result.rationale)

        # Toon alle scores
        st.markdown("**Alle niveau scores:**")
        for level, score in result.scores.items():
            bar_length = int(score * 100)
            st.markdown(f"- **{level}**: {score:.2%} {'█' * (bar_length // 5)}")


async def handle_generate_definition_with_classification(
    container,  # ServiceContainer instance
    begrip: str,
    org_context: str | None,
    jur_context: str | None,
    wettelijke_context: str | None,
    voorbeelden: list[str],
):
    """
    Complete flow: Classificatie + Definitie Generatie

    Dit is hoe de UI de hele flow aanroept:
        1. Classificeer begrip
        2. Toon classificatie aan gebruiker
        3. Gebruik classificatie in definitie generatie

    Args:
        container: ServiceContainer (voor DI)
        begrip: Te definiëren begrip
        org_context: Organisatorische context
        jur_context: Juridische context
        wettelijke_context: Wettelijke context
        voorbeelden: Voorbeeld zinnen
    """

    # ===== STAP 1: CLASSIFICATIE (VOOR GENERATIE) =====

    st.markdown("---")
    st.markdown("## 🎯 Stap 1: Ontologische Classificatie")

    # Haal classifier uit DI container
    classifier = container.ontological_classifier()

    # Classificeer begrip
    classification = render_classification_step(
        classifier=classifier,
        begrip=begrip,
        org_context=org_context,
        jur_context=jur_context,
    )

    # Check betrouwbaarheid
    if not classification.is_reliable:
        st.warning(
            "⚠️ Classificatie heeft lage betrouwbaarheid. "
            "Overweeg om meer context toe te voegen voor betere resultaten."
        )

        # Optioneel: laat gebruiker handmatig kiezen
        manual_override = st.checkbox("Handmatig niveau selecteren?")
        if manual_override:
            level_choice = st.radio(
                "Selecteer niveau:",
                options=["U", "F", "O"],
                index=["U", "F", "O"].index(classification.level.value),
            )
            classification.level.value = level_choice

    # ===== STAP 2: DEFINITIE GENERATIE (GEBRUIKT CLASSIFICATIE) =====

    st.markdown("---")
    st.markdown("## 📝 Stap 2: Definitie Generatie")

    st.info(
        f"💡 Definitie wordt gegenereerd met **{classification.level.value}** niveau prompt template"
    )

    # Bouw GenerationRequest met geclassificeerd niveau
    request = GenerationRequest(
        begrip=begrip,
        ontologische_categorie=classification.to_string_level(),  # ← HIER!
        organisatorische_context=org_context or "",
        juridische_context=jur_context or "",
        wettelijke_context=wettelijke_context or "",
        voorbeelden=voorbeelden or [],
        document_context=None,  # Optioneel
    )

    # Haal orchestrator uit DI container
    orchestrator = container.orchestrator()

    # Genereer definitie
    with st.spinner("Genereer definitie met AI..."):
        try:
            response = await orchestrator.create_definition(request)

            # Toon resultaat
            if response.success:
                st.success("✅ Definitie succesvol gegenereerd!")

                st.markdown("### 📄 Gegenereerde Definitie")
                st.write(response.definition_text)

                # Toon validatie resultaten
                if response.validation_results:
                    _display_validation_results(response.validation_results)

                # Sla op in session state
                SessionStateManager.set_value("last_generation_result", response)
                SessionStateManager.set_value(
                    "generated_definition", response.definition_text
                )

            else:
                st.error(f"❌ Generatie gefaald: {response.error}")

        except Exception as e:
            st.error(f"❌ Fout tijdens generatie: {e}")
            raise


def _display_validation_results(validation_results: dict):
    """Toon validatie resultaten"""
    st.markdown("### ✅ Validatie Resultaten")

    total_rules = validation_results.get("total_rules", 0)
    passed_rules = validation_results.get("passed_rules", 0)

    if passed_rules == total_rules:
        st.success(f"✅ Alle {total_rules} validatieregels geslaagd!")
    else:
        failed = total_rules - passed_rules
        st.warning(f"⚠️ {failed}/{total_rules} regels gefaald")

    # Toon details in expander
    with st.expander("📋 Validatie Details"):
        for result in validation_results.get("results", []):
            status = "✅" if result.get("passed") else "❌"
            st.markdown(
                f"{status} **{result.get('rule_name')}**: {result.get('message')}"
            )


# ===== SIMPLIFIED UI INTEGRATION =====


def simplified_ui_integration_example():
    """
    Vereenvoudigd voorbeeld: Minimale integratie in bestaande UI

    Dit laat zien hoe je met minimale wijzigingen de classifier
    toevoegt aan bestaande definitie generatie flow.
    """

    # Haal container uit session state (bestaand)
    container = SessionStateManager.get_value("service_container")

    # Verzamel inputs (bestaand)
    begrip = st.text_input("Begrip")
    org_context = st.text_area("Organisatorische Context")
    jur_context = st.text_area("Juridische Context")

    if st.button("Genereer Definitie"):
        # NIEUW: Classificeer EERST
        classifier = container.ontological_classifier()
        classification = classifier.classify(begrip, org_context, jur_context)

        st.info(
            f"Geclassificeerd als: **{classification.level.value}** (confidence: {classification.confidence:.1%})"
        )

        # BESTAAND: Genereer definitie (met classificatie)
        GenerationRequest(
            begrip=begrip,
            ontologische_categorie=classification.to_string_level(),  # ← Enige wijziging
            organisatorische_context=org_context,
            juridische_context=jur_context,
            # ... rest van inputs
        )

        # Rest van bestaande generatie code...
        container.orchestrator()
        # await orchestrator.create_definition(request)


# ===== BATCH PROCESSING EXAMPLE =====


def batch_classification_example():
    """
    Voorbeeld: Batch classificatie van bestaande definities

    Nuttig voor:
        - Validatie van bestaande database
        - Migratie naar nieuwe classificatie systeem
        - Analyse van juridische corpus
    """

    st.markdown("## 📊 Batch Classificatie")

    # Upload CSV met begrippen
    uploaded_file = st.file_uploader("Upload begrippen CSV", type=["csv"])

    if uploaded_file and st.button("Classificeer Batch"):
        import pandas as pd

        # Lees begrippen
        df = pd.read_csv(uploaded_file)
        begrippen = df["begrip"].tolist()

        # Haal classifier
        container = SessionStateManager.get_value("service_container")
        classifier = container.ontological_classifier()

        # Classificeer in batch
        with st.spinner(f"Classificeer {len(begrippen)} begrippen..."):
            results = classifier.classify_batch(begrippen)

        # Toon resultaten
        st.success(f"✅ {len(results)} begrippen geclassificeerd!")

        # Maak resultaat tabel
        result_data = []
        for begrip, result in results.items():
            result_data.append(
                {
                    "Begrip": begrip,
                    "Niveau": result.level.value,
                    "Confidence": f"{result.confidence:.1%}",
                    "Betrouwbaarheid": result.confidence_level.value.upper(),
                }
            )

        result_df = pd.DataFrame(result_data)

        # Toon tabel
        st.dataframe(result_df)

        # Download optie
        csv = result_df.to_csv(index=False)
        st.download_button(
            "📥 Download Resultaten",
            data=csv,
            file_name="classificatie_resultaten.csv",
            mime="text/csv",
        )
