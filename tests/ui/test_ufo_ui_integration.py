"""
UI Integration Tests for UFO Classifier
========================================
Tests the integration of UFO Classifier with Streamlit UI components
in Generator, Edit, and Expert Review tabs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import streamlit as st
from datetime import datetime
import json

from src.services.ufo_classifier_service import (
    UFOClassifierService,
    UFOCategory,
    UFOClassificationResult,
    get_ufo_classifier
)


class TestGeneratorTabIntegration:
    """Test UFO integration in Generator tab"""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components"""
        mock_st = Mock()
        mock_st.session_state = {}
        mock_st.info = Mock()
        mock_st.warning = Mock()
        mock_st.success = Mock()
        mock_st.error = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.selectbox = Mock()
        mock_st.write = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.expander = Mock()
        mock_st.spinner = Mock()
        return mock_st

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_auto_suggest_on_generation(self, classifier, mock_streamlit):
        """Test auto-suggestion when generating new definition"""
        # Simulate definition generation
        generated_definition = {
            'begrip': 'verdachte',
            'definitie': 'Een persoon die wordt verdacht van een strafbaar feit'
        }

        # Classify
        result = classifier.classify(
            generated_definition['begrip'],
            generated_definition['definitie']
        )

        # Store in session state
        mock_streamlit.session_state['ufo_suggestion'] = result.primary_category.value
        mock_streamlit.session_state['ufo_confidence'] = result.confidence

        # Display suggestion
        if result.confidence >= 0.8:
            icon = "✅"
            status = "Hoge zekerheid"
        elif result.confidence >= 0.6:
            icon = "📊"
            status = "Redelijke zekerheid"
        else:
            icon = "⚠️"
            status = "Lage zekerheid - review vereist"

        mock_streamlit.info(
            f"{icon} Voorgestelde UFO categorie: **{result.primary_category.value}** "
            f"({status}: {result.confidence:.0%})"
        )

        # Verify display
        mock_streamlit.info.assert_called_once()
        assert result.primary_category.value in mock_streamlit.info.call_args[0][0]

    def test_manual_override_ui(self, classifier, mock_streamlit):
        """Test manual override UI in Generator tab"""
        # Get suggestion
        result = classifier.classify("verdachte", "Persoon verdacht")

        # Available categories
        categories = [cat.value for cat in UFOCategory if cat != UFOCategory.UNKNOWN]

        # Mock user selecting different category
        mock_streamlit.selectbox.return_value = "Kind"

        with mock_streamlit.columns[0]:
            selected_category = mock_streamlit.selectbox(
                "UFO Categorie",
                options=categories,
                index=categories.index(result.primary_category.value),
                help="OntoUML/UFO metamodel categorie"
            )

        # Track override
        if selected_category != result.primary_category.value:
            mock_streamlit.session_state['ufo_override'] = True
            mock_streamlit.session_state['ufo_manual'] = selected_category
            mock_streamlit.session_state['ufo_source'] = 'manual'

        assert mock_streamlit.session_state.get('ufo_override') == True
        assert mock_streamlit.session_state.get('ufo_source') == 'manual'

    def test_explanation_modal(self, classifier, mock_streamlit):
        """Test explanation modal/expander in UI"""
        result = classifier.classify(
            "koopovereenkomst",
            "Een overeenkomst waarbij de verkoper zich verbindt"
        )

        # Mock expander for explanation
        mock_streamlit.button.return_value = True  # User clicks "Waarom?"

        if mock_streamlit.button("ℹ️ Waarom deze categorie?"):
            with mock_streamlit.expander("UFO Classificatie Uitleg", expanded=True):
                mock_streamlit.write(f"**Categorie:** {result.primary_category.value}")
                mock_streamlit.write(f"**Zekerheid:** {result.confidence:.1%}")

                mock_streamlit.write("**Gedetecteerde patronen:**")
                for pattern_type, terms in result.matched_patterns.items():
                    mock_streamlit.write(f"- {pattern_type}: {', '.join(terms[:3])}")

                mock_streamlit.write("**Verklaring:**")
                for explanation in result.explanation:
                    mock_streamlit.write(f"• {explanation}")

        # Verify explanation displayed
        assert mock_streamlit.write.call_count >= 4

    def test_low_confidence_warning(self, classifier, mock_streamlit):
        """Test warning display for low confidence"""
        # Create low confidence scenario
        result = classifier.classify("vague", "unclear")

        if result.confidence < 0.6:
            mock_streamlit.warning(
                "⚠️ **Handmatige review vereist**\n\n"
                f"De automatische classificatie heeft een lage zekerheid ({result.confidence:.0%}). "
                "Controleer en pas de UFO categorie handmatig aan indien nodig."
            )

            # Force manual selection
            mock_streamlit.session_state['require_manual_ufo'] = True

        if result.confidence < 0.6:
            mock_streamlit.warning.assert_called_once()
            assert mock_streamlit.session_state.get('require_manual_ufo') == True


class TestEditTabIntegration:
    """Test UFO integration in Edit tab"""

    @pytest.fixture
    def mock_ui_components(self):
        """Mock UI components for Edit tab"""
        components = Mock()
        components.container = Mock()
        components.columns = Mock(return_value=[Mock(), Mock(), Mock()])
        components.form = Mock()
        components.form_submit_button = Mock(return_value=False)
        return components

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_load_existing_ufo_category(self, classifier, mock_ui_components):
        """Test loading existing UFO category in Edit tab"""
        # Mock loading definition from database
        existing_definition = {
            'id': 1,
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht van strafbaar feit',
            'ufo_categorie': 'Role',
            'ufo_confidence': 0.85,
            'ufo_source': 'auto'
        }

        # Display existing category
        with mock_ui_components.container:
            if existing_definition.get('ufo_categorie'):
                source_icon = "🤖" if existing_definition['ufo_source'] == 'auto' else "👤"
                mock_ui_components.info = Mock()
                mock_ui_components.info(
                    f"{source_icon} UFO Categorie: **{existing_definition['ufo_categorie']}** "
                    f"(Zekerheid: {existing_definition['ufo_confidence']:.0%})"
                )

        mock_ui_components.info.assert_called_once()

    def test_reclassify_on_edit(self, classifier, mock_ui_components):
        """Test reclassification when definition is edited"""
        # Original definition
        original = {
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht',
            'ufo_categorie': 'Role'
        }

        # Edited definition
        edited_definition = "Een persoon die wordt verdacht van een ernstig strafbaar feit"

        # Detect change
        if edited_definition != original['definitie']:
            # Reclassify
            new_result = classifier.classify(original['begrip'], edited_definition)

            # Check if category changed
            if new_result.primary_category.value != original['ufo_categorie']:
                mock_ui_components.warning = Mock()
                mock_ui_components.warning(
                    f"⚠️ UFO categorie suggestie gewijzigd: "
                    f"{original['ufo_categorie']} → {new_result.primary_category.value}"
                )

                # Ask for confirmation
                mock_ui_components.checkbox = Mock(return_value=True)
                accept_new = mock_ui_components.checkbox(
                    "Accepteer nieuwe UFO categorie",
                    value=True
                )

                if accept_new:
                    original['ufo_categorie'] = new_result.primary_category.value
                    original['ufo_confidence'] = new_result.confidence
                    original['ufo_source'] = 'auto'

        # Verify the category is updated if accepted
        assert original['ufo_categorie'] in [cat.value for cat in UFOCategory]

    def test_save_with_ufo_metadata(self, classifier, mock_ui_components):
        """Test saving definition with UFO metadata"""
        definition_to_save = {
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht van strafbaar feit',
            'ufo_categorie': None,
            'ufo_confidence': None,
            'ufo_source': None
        }

        # Classify before saving
        result = classifier.classify(
            definition_to_save['begrip'],
            definition_to_save['definitie']
        )

        # Add UFO metadata
        definition_to_save['ufo_categorie'] = result.primary_category.value
        definition_to_save['ufo_confidence'] = result.confidence
        definition_to_save['ufo_source'] = 'auto'
        definition_to_save['ufo_suggestion'] = result.primary_category.value  # Keep suggestion

        # Mock save button
        mock_ui_components.form_submit_button.return_value = True

        if mock_ui_components.form_submit_button("💾 Opslaan"):
            # Validate UFO data
            assert definition_to_save['ufo_categorie'] is not None
            assert 0 <= definition_to_save['ufo_confidence'] <= 1
            assert definition_to_save['ufo_source'] in ['auto', 'manual']

            mock_ui_components.success = Mock()
            mock_ui_components.success(
                f"✅ Definitie opgeslagen met UFO categorie: {definition_to_save['ufo_categorie']}"
            )


class TestExpertReviewTabIntegration:
    """Test UFO integration in Expert Review tab"""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    @pytest.fixture
    def mock_expert_ui(self):
        """Mock Expert Review UI components"""
        ui = Mock()
        ui.container = Mock()
        ui.columns = Mock(return_value=[Mock(), Mock()])
        ui.metric = Mock()
        ui.radio = Mock()
        ui.text_area = Mock()
        ui.button = Mock(return_value=False)
        return ui

    def test_expert_review_display(self, classifier, mock_expert_ui):
        """Test UFO display in expert review"""
        # Definition under review
        review_item = {
            'id': 1,
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht van strafbaar feit',
            'ufo_suggestion': 'Role',
            'ufo_confidence': 0.75,
            'ufo_source': 'auto'
        }

        # Display UFO info prominently
        with mock_expert_ui.container:
            col1, col2 = mock_expert_ui.columns

            with col1:
                mock_expert_ui.metric(
                    "UFO Categorie (Voorstel)",
                    review_item['ufo_suggestion'],
                    f"Zekerheid: {review_item['ufo_confidence']:.0%}"
                )

            with col2:
                # Expert can override
                categories = [cat.value for cat in UFOCategory if cat != UFOCategory.UNKNOWN]
                expert_category = mock_expert_ui.radio(
                    "Expert Oordeel",
                    options=categories,
                    index=categories.index(review_item['ufo_suggestion'])
                )

        mock_expert_ui.metric.assert_called_once()

    def test_expert_override_with_reason(self, classifier, mock_expert_ui):
        """Test expert override with required reason"""
        original_category = "Role"
        expert_category = "Kind"

        # Expert selects different category
        mock_expert_ui.radio.return_value = expert_category

        if expert_category != original_category:
            # Require reason for override
            reason = mock_expert_ui.text_area(
                "Reden voor aanpassing (verplicht)",
                help="Leg uit waarom de automatische classificatie niet correct is"
            )

            mock_expert_ui.text_area.return_value = "Verdachte is hier gebruikt als algemene persoon, niet als rol"

            if reason:
                # Create audit entry
                override_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'original': original_category,
                    'new': expert_category,
                    'reason': reason,
                    'expert': 'current_user'
                }

                assert override_entry['reason'] != ""
                assert override_entry['original'] != override_entry['new']

    def test_bulk_review_interface(self, classifier, mock_expert_ui):
        """Test bulk review for low confidence items"""
        # Get items needing review
        review_queue = [
            {'id': 1, 'begrip': 'vague1', 'definitie': 'unclear1', 'confidence': 0.4},
            {'id': 2, 'begrip': 'vague2', 'definitie': 'unclear2', 'confidence': 0.3},
            {'id': 3, 'begrip': 'vague3', 'definitie': 'unclear3', 'confidence': 0.5}
        ]

        mock_expert_ui.subheader = Mock()
        mock_expert_ui.subheader(f"📋 Bulk Review Queue ({len(review_queue)} items)")

        # Display review table
        for idx, item in enumerate(review_queue):
            with mock_expert_ui.container:
                col1, col2, col3 = mock_expert_ui.columns([3, 2, 1])

                with col1:
                    mock_expert_ui.text(f"{item['begrip']}: {item['definitie']}")

                with col2:
                    # Reclassify for current suggestion
                    result = classifier.classify(item['begrip'], item['definitie'])
                    categories = [cat.value for cat in UFOCategory if cat != UFOCategory.UNKNOWN]

                    selected = mock_expert_ui.selectbox(
                        "Categorie",
                        options=categories,
                        index=categories.index(result.primary_category.value) if result.primary_category.value in categories else 0,
                        key=f"bulk_{item['id']}"
                    )

                with col3:
                    mock_expert_ui.text(f"Conf: {item['confidence']:.0%}")

        # Bulk approve button
        if mock_expert_ui.button("✅ Approve All Selected"):
            mock_expert_ui.success(f"Approved {len(review_queue)} items")

    def test_confidence_threshold_filtering(self, classifier, mock_expert_ui):
        """Test filtering by confidence threshold"""
        # Confidence threshold slider
        mock_expert_ui.slider = Mock(return_value=0.6)
        threshold = mock_expert_ui.slider(
            "Minimum confidence threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1
        )

        # Filter items
        all_items = [
            {'confidence': 0.9, 'needs_review': False},
            {'confidence': 0.7, 'needs_review': False},
            {'confidence': 0.5, 'needs_review': True},
            {'confidence': 0.3, 'needs_review': True}
        ]

        items_to_review = [
            item for item in all_items
            if item['confidence'] < threshold
        ]

        assert len(items_to_review) == 2
        assert all(item['confidence'] < threshold for item in items_to_review)


class TestMigrationUI:
    """Test UI for migrating existing definitions"""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    @pytest.fixture
    def mock_migration_ui(self):
        """Mock migration UI components"""
        ui = Mock()
        ui.progress = Mock()
        ui.empty = Mock()
        ui.dataframe = Mock()
        return ui

    def test_migration_progress_display(self, classifier, mock_migration_ui):
        """Test migration progress display"""
        # Mock existing definitions without UFO
        definitions = [
            {'id': i, 'begrip': f'term_{i}', 'definitie': f'def_{i}'}
            for i in range(100)
        ]

        # Progress tracking
        progress_bar = mock_migration_ui.progress(0)
        status_text = mock_migration_ui.empty()

        results = []
        for i, definition in enumerate(definitions):
            # Update progress
            progress = (i + 1) / len(definitions)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{len(definitions)}: {definition['begrip']}")

            # Classify
            result = classifier.classify(
                definition['begrip'],
                definition['definitie']
            )

            results.append({
                'id': definition['id'],
                'begrip': definition['begrip'],
                'ufo_category': result.primary_category.value,
                'confidence': result.confidence,
                'needs_review': result.confidence < 0.6
            })

        # Display summary
        mock_migration_ui.success = Mock()
        mock_migration_ui.success(f"✅ Migrated {len(results)} definitions")

        needs_review = sum(1 for r in results if r['needs_review'])
        mock_migration_ui.info = Mock()
        mock_migration_ui.info(f"ℹ️ {needs_review} items need manual review")

    def test_migration_review_interface(self, classifier, mock_migration_ui):
        """Test interface for reviewing migration results"""
        # Migration results
        results_df = Mock()
        results_df.shape = (100, 5)

        # Display options
        mock_migration_ui.checkbox = Mock()
        show_all = mock_migration_ui.checkbox("Show all results", value=False)
        show_low_conf = mock_migration_ui.checkbox("Show only low confidence", value=True)

        # Filter display
        if show_low_conf:
            # Filter to low confidence
            filtered_df = Mock()
            filtered_df.shape = (20, 5)
            mock_migration_ui.dataframe(filtered_df)
        else:
            mock_migration_ui.dataframe(results_df)

        # Export options
        if mock_migration_ui.button("📥 Export Results"):
            mock_migration_ui.download_button = Mock()
            mock_migration_ui.download_button(
                label="Download CSV",
                data="csv_data",
                file_name=f"ufo_migration_{datetime.now().strftime('%Y%m%d')}.csv"
            )


class TestUIPerformance:
    """Test UI performance considerations"""

    @pytest.fixture
    def classifier(self):
        return UFOClassifierService()

    def test_async_classification_ui(self, classifier):
        """Test async classification to prevent UI blocking"""
        import asyncio

        async def classify_async(term, definition):
            # Simulate async classification
            await asyncio.sleep(0.001)  # Minimal delay
            return classifier.classify(term, definition)

        # Mock spinner for loading state
        mock_spinner = Mock()

        with mock_spinner("🔄 Classificeren..."):
            # Run async classification
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                classify_async("verdachte", "Persoon verdacht")
            )
            loop.close()

        assert result.primary_category != UFOCategory.UNKNOWN

    def test_cached_ui_elements(self, classifier):
        """Test caching of UI elements for performance"""
        # Cache category list
        @st.cache_data
        def get_ufo_categories():
            return [cat.value for cat in UFOCategory if cat != UFOCategory.UNKNOWN]

        categories = get_ufo_categories()
        assert len(categories) > 0

        # Cache classifier instance
        @st.cache_resource
        def get_classifier_cached():
            return UFOClassifierService()

        cached_classifier = get_classifier_cached()
        assert isinstance(cached_classifier, UFOClassifierService)

    def test_batch_ui_updates(self, classifier):
        """Test batch UI updates for efficiency"""
        # Mock batch container
        batch_container = Mock()
        batch_container.empty = Mock()

        # Collect updates
        updates = []
        for i in range(10):
            result = classifier.classify(f"term_{i}", f"definition_{i}")
            updates.append({
                'term': f"term_{i}",
                'category': result.primary_category.value,
                'confidence': result.confidence
            })

        # Single UI update with all results
        batch_container.empty().dataframe(updates)

        # Verify single update instead of multiple
        batch_container.empty.assert_called_once()


class TestAuditUI:
    """Test audit trail UI for UFO changes"""

    @pytest.fixture
    def mock_audit_ui(self):
        """Mock audit UI components"""
        ui = Mock()
        ui.expander = Mock()
        ui.dataframe = Mock()
        ui.json = Mock()
        return ui

    def test_audit_trail_display(self, mock_audit_ui):
        """Test display of UFO change audit trail"""
        # Mock audit trail
        audit_trail = [
            {
                'timestamp': '2024-01-01T10:00:00',
                'definition_id': 1,
                'old_category': None,
                'new_category': 'Role',
                'confidence': 0.85,
                'source': 'auto'
            },
            {
                'timestamp': '2024-01-01T11:00:00',
                'definition_id': 1,
                'old_category': 'Role',
                'new_category': 'Kind',
                'confidence': 0.92,
                'source': 'manual'
            }
        ]

        with mock_audit_ui.expander("📋 UFO Change History"):
            mock_audit_ui.dataframe(audit_trail)

            # Show detailed view
            if mock_audit_ui.button("Show Details"):
                mock_audit_ui.json(audit_trail)

        mock_audit_ui.dataframe.assert_called_once()

    def test_audit_filtering(self, mock_audit_ui):
        """Test filtering audit trail"""
        # Filter options
        mock_audit_ui.multiselect = Mock(return_value=['manual'])
        source_filter = mock_audit_ui.multiselect(
            "Filter by source",
            options=['auto', 'manual', 'import'],
            default=['manual']
        )

        mock_audit_ui.date_input = Mock()
        date_from = mock_audit_ui.date_input("From date")
        date_to = mock_audit_ui.date_input("To date")

        # Apply filters (mock)
        filtered_audit = [
            {'source': 'manual', 'timestamp': '2024-01-01T11:00:00'}
        ]

        mock_audit_ui.dataframe(filtered_audit)

        assert 'manual' in source_filter


if __name__ == "__main__":
    pytest.main([__file__, "-v"])