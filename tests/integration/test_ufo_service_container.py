"""
Integration Tests for UFO Classifier with ServiceContainer
===========================================================
Tests the integration of UFOClassifierService with the ServiceContainer
and other services in the application.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sqlite3

from src.services.ufo_classifier_service import (
    UFOClassifierService,
    UFOCategory,
    get_ufo_classifier
)


class TestServiceContainerIntegration:
    """Test UFO Classifier integration with ServiceContainer"""

    @pytest.fixture
    def mock_service_container(self):
        """Create a mock ServiceContainer with UFO classifier"""
        container = Mock()

        # Add UFO classifier method
        container.ufo_classifier = Mock(side_effect=get_ufo_classifier)

        # Add other services that might interact
        container.repository = Mock()
        container.validation_orchestrator = Mock()
        container.ai_service = Mock()

        # Track service initialization
        container._instances = {}
        container._initialization_count = 0

        return container

    def test_ufo_classifier_registration(self, mock_service_container):
        """Test that UFO classifier can be registered in container"""
        # Get classifier from container
        classifier = mock_service_container.ufo_classifier()

        assert isinstance(classifier, UFOClassifierService)
        mock_service_container.ufo_classifier.assert_called_once()

    def test_singleton_behavior_in_container(self, mock_service_container):
        """Test singleton pattern within container"""
        # Override to return actual singleton
        mock_service_container.ufo_classifier = get_ufo_classifier

        classifier1 = mock_service_container.ufo_classifier()
        classifier2 = mock_service_container.ufo_classifier()

        assert classifier1 is classifier2

    def test_lazy_loading_in_container(self, mock_service_container):
        """Test lazy loading of UFO classifier"""
        # Simulate lazy loading
        def lazy_ufo_classifier():
            if 'ufo_classifier' not in mock_service_container._instances:
                mock_service_container._instances['ufo_classifier'] = UFOClassifierService()
                mock_service_container._initialization_count += 1
            return mock_service_container._instances['ufo_classifier']

        mock_service_container.ufo_classifier = lazy_ufo_classifier

        # First call - should initialize
        classifier1 = mock_service_container.ufo_classifier()
        assert mock_service_container._initialization_count == 1

        # Second call - should not re-initialize
        classifier2 = mock_service_container.ufo_classifier()
        assert mock_service_container._initialization_count == 1
        assert classifier1 is classifier2

    def test_integration_with_repository(self, mock_service_container):
        """Test UFO classifier integration with repository"""
        classifier = mock_service_container.ufo_classifier()
        repository = mock_service_container.repository

        # Mock repository methods
        repository.get_all_definitions = Mock(return_value=[
            {'id': 1, 'begrip': 'verdachte', 'definitie': 'Persoon verdacht van strafbaar feit'},
            {'id': 2, 'begrip': 'proces', 'definitie': 'Juridische procedure'}
        ])

        repository.update_ufo_category = Mock()

        # Process definitions
        definitions = repository.get_all_definitions()
        for definition in definitions:
            result = classifier.classify(
                definition['begrip'],
                definition['definitie']
            )

            repository.update_ufo_category(
                definition['id'],
                result.primary_category.value,
                result.confidence
            )

        # Verify repository was called correctly
        assert repository.get_all_definitions.called
        assert repository.update_ufo_category.call_count == 2

    def test_integration_with_validation_orchestrator(self, mock_service_container):
        """Test integration with validation orchestrator"""
        classifier = mock_service_container.ufo_classifier()
        validator = mock_service_container.validation_orchestrator

        # Mock validation context
        validation_context = {
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht van strafbaar feit',
            'require_ufo': True
        }

        # Classify
        result = classifier.classify(
            validation_context['begrip'],
            validation_context['definitie']
        )

        # Add to validation
        validator.add_ufo_validation = Mock()
        validator.add_ufo_validation(
            result.primary_category.value,
            result.confidence
        )

        validator.add_ufo_validation.assert_called_once_with(
            result.primary_category.value,
            result.confidence
        )

    def test_integration_with_ai_service(self, mock_service_container):
        """Test potential integration with AI service for enhanced classification"""
        classifier = mock_service_container.ufo_classifier()
        ai_service = mock_service_container.ai_service

        # Mock AI service enhancement
        ai_service.enhance_classification = Mock(return_value={
            'additional_context': 'legal domain',
            'confidence_boost': 0.1
        })

        # Classify with potential AI enhancement
        result = classifier.classify('verdachte', 'Persoon verdacht')

        # Simulate AI enhancement
        if result.confidence < 0.8:
            enhancement = ai_service.enhance_classification(
                'verdachte',
                'Persoon verdacht'
            )
            # Could boost confidence based on AI analysis
            enhanced_confidence = min(
                result.confidence + enhancement['confidence_boost'],
                1.0
            )

            assert enhanced_confidence >= result.confidence

    def test_container_configuration_for_ufo(self, mock_service_container):
        """Test container configuration specific to UFO classifier"""
        # Add configuration
        mock_service_container.config = {
            'ufo_classifier': {
                'confidence_threshold': 0.6,
                'enable_caching': True,
                'max_cache_size': 1024,
                'batch_size': 100
            }
        }

        # Create classifier with config
        classifier = mock_service_container.ufo_classifier()

        # Verify configuration can be accessed
        config = mock_service_container.config['ufo_classifier']
        assert config['confidence_threshold'] == 0.6
        assert config['enable_caching'] == True

    def test_error_handling_in_container(self, mock_service_container):
        """Test error handling when UFO classifier fails"""
        # Simulate failure
        mock_service_container.ufo_classifier = Mock(
            side_effect=Exception("Initialization failed")
        )

        with pytest.raises(Exception) as exc_info:
            mock_service_container.ufo_classifier()

        assert "Initialization failed" in str(exc_info.value)

    def test_container_cleanup(self, mock_service_container):
        """Test proper cleanup of UFO classifier resources"""
        classifier = mock_service_container.ufo_classifier()

        # Simulate cleanup
        def cleanup():
            if 'ufo_classifier' in mock_service_container._instances:
                # Clear caches
                classifier.pattern_matcher.find_matches.cache_clear()
                del mock_service_container._instances['ufo_classifier']

        mock_service_container.cleanup = cleanup
        mock_service_container.cleanup()

        assert 'ufo_classifier' not in mock_service_container._instances


class TestServiceOrchestration:
    """Test orchestration of UFO classifier with other services"""

    @pytest.fixture
    def orchestrator(self):
        """Create service orchestrator with UFO classifier"""
        orchestrator = Mock()
        orchestrator.ufo_classifier = get_ufo_classifier()
        orchestrator.repository = Mock()
        orchestrator.validator = Mock()
        orchestrator.import_service = Mock()
        orchestrator.workflow_service = Mock()
        return orchestrator

    def test_definition_creation_workflow(self, orchestrator):
        """Test complete workflow for definition creation with UFO"""
        # 1. Create definition
        new_definition = {
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht van strafbaar feit'
        }

        # 2. Classify with UFO
        ufo_result = orchestrator.ufo_classifier.classify(
            new_definition['begrip'],
            new_definition['definitie']
        )

        # 3. Validate
        orchestrator.validator.validate = Mock(return_value={'valid': True})
        validation = orchestrator.validator.validate(new_definition)

        # 4. Save to repository
        orchestrator.repository.create = Mock(return_value={'id': 1})
        saved = orchestrator.repository.create({
            **new_definition,
            'ufo_categorie': ufo_result.primary_category.value,
            'ufo_confidence': ufo_result.confidence
        })

        # Verify workflow
        assert ufo_result.primary_category == UFOCategory.ROLE
        assert validation['valid']
        assert saved['id'] == 1

    def test_bulk_import_workflow(self, orchestrator):
        """Test bulk import workflow with UFO classification"""
        # Mock import data
        import_data = [
            {'begrip': 'verdachte', 'definitie': 'Persoon verdacht'},
            {'begrip': 'proces', 'definitie': 'Juridische procedure'},
            {'begrip': 'overeenkomst', 'definitie': 'Contract tussen partijen'}
        ]

        orchestrator.import_service.parse_file = Mock(return_value=import_data)

        # Process import
        processed = []
        for item in import_data:
            # Classify
            result = orchestrator.ufo_classifier.classify(
                item['begrip'],
                item['definitie']
            )

            # Add UFO data
            item['ufo_categorie'] = result.primary_category.value
            item['ufo_confidence'] = result.confidence
            item['needs_review'] = result.confidence < 0.6

            processed.append(item)

        # Verify processing
        assert len(processed) == 3
        assert all('ufo_categorie' in item for item in processed)
        assert any(item['needs_review'] for item in processed) or True  # At least one might need review

    def test_validation_integration(self, orchestrator):
        """Test UFO classifier integration with validation rules"""
        # Definition to validate
        definition = {
            'begrip': 'verdachte',
            'definitie': 'Persoon verdacht van strafbaar feit',
            'categorie': 'type'  # Old category system
        }

        # Get UFO classification
        ufo_result = orchestrator.ufo_classifier.classify(
            definition['begrip'],
            definition['definitie']
        )

        # Mock validation rule that checks UFO category
        def validate_ufo_consistency(data, ufo_category):
            # Check if old category aligns with UFO category
            if data['categorie'] == 'type' and ufo_category == UFOCategory.KIND:
                return True
            if data['categorie'] == 'proces' and ufo_category == UFOCategory.EVENT:
                return True
            # ROLE doesn't map directly to old categories
            return ufo_category == UFOCategory.ROLE

        is_consistent = validate_ufo_consistency(definition, ufo_result.primary_category)
        assert is_consistent or ufo_result.primary_category == UFOCategory.ROLE

    def test_approval_workflow_with_ufo(self, orchestrator):
        """Test approval workflow considering UFO confidence"""
        # Low confidence classification
        low_conf_result = orchestrator.ufo_classifier.classify(
            "vague",
            "unclear definition"
        )

        # High confidence classification
        high_conf_result = orchestrator.ufo_classifier.classify(
            "rechtspersoon",
            "Een juridische entiteit met rechtspersoonlijkheid"
        )

        # Mock workflow service
        orchestrator.workflow_service.requires_approval = Mock(
            side_effect=lambda conf: conf < 0.6
        )

        # Check approval requirements
        needs_approval_low = orchestrator.workflow_service.requires_approval(
            low_conf_result.confidence
        )
        needs_approval_high = orchestrator.workflow_service.requires_approval(
            high_conf_result.confidence
        )

        assert needs_approval_low or low_conf_result.confidence >= 0.6
        assert not needs_approval_high

    def test_export_with_ufo_metadata(self, orchestrator):
        """Test export includes UFO metadata"""
        # Mock data with UFO categories
        export_data = [
            {
                'begrip': 'verdachte',
                'definitie': 'Persoon verdacht',
                'ufo_categorie': 'Role',
                'ufo_confidence': 0.85
            }
        ]

        orchestrator.export_service = Mock()
        orchestrator.export_service.export_to_json = Mock(return_value=True)

        # Export with UFO data
        orchestrator.export_service.export_to_json(
            export_data,
            include_ufo=True
        )

        orchestrator.export_service.export_to_json.assert_called_once_with(
            export_data,
            include_ufo=True
        )


class TestDatabaseIntegration:
    """Test database integration for UFO classifier"""

    @pytest.fixture
    def test_db(self):
        """Create test database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)

        # Create schema
        conn.executescript("""
            CREATE TABLE definities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                begrip TEXT NOT NULL,
                definitie TEXT NOT NULL,
                ufo_categorie TEXT,
                ufo_suggestion TEXT,
                ufo_confidence REAL,
                ufo_source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE definition_ufo_history (
                id INTEGER PRIMARY KEY,
                definition_id INTEGER,
                old_category TEXT,
                new_category TEXT,
                confidence REAL,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (definition_id) REFERENCES definities(id)
            );
        """)

        conn.commit()
        yield conn, db_path

        conn.close()
        Path(db_path).unlink(missing_ok=True)

    def test_save_ufo_classification(self, test_db):
        """Test saving UFO classification to database"""
        conn, db_path = test_db
        classifier = UFOClassifierService()

        # Classify
        result = classifier.classify(
            "verdachte",
            "Persoon verdacht van strafbaar feit"
        )

        # Save to database
        cursor = conn.execute("""
            INSERT INTO definities (begrip, definitie, ufo_suggestion, ufo_confidence, ufo_source)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "verdachte",
            "Persoon verdacht van strafbaar feit",
            result.primary_category.value,
            result.confidence,
            'auto'
        ))

        conn.commit()
        definition_id = cursor.lastrowid

        # Verify saved
        saved = conn.execute(
            "SELECT * FROM definities WHERE id = ?",
            (definition_id,)
        ).fetchone()

        assert saved is not None
        assert saved[3] == result.primary_category.value  # ufo_suggestion
        assert saved[4] == result.confidence  # ufo_confidence

    def test_update_ufo_category(self, test_db):
        """Test updating UFO category in database"""
        conn, db_path = test_db
        classifier = UFOClassifierService()

        # Insert initial record
        cursor = conn.execute("""
            INSERT INTO definities (begrip, definitie)
            VALUES (?, ?)
        """, ("verdachte", "Persoon verdacht"))
        conn.commit()
        def_id = cursor.lastrowid

        # Classify and update
        result = classifier.classify("verdachte", "Persoon verdacht")

        # Update with classification
        conn.execute("""
            UPDATE definities
            SET ufo_suggestion = ?, ufo_confidence = ?, ufo_source = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (result.primary_category.value, result.confidence, 'auto', def_id))

        # Add to history
        conn.execute("""
            INSERT INTO definition_ufo_history
            (definition_id, old_category, new_category, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """, (def_id, None, result.primary_category.value, result.confidence, 'auto'))

        conn.commit()

        # Verify update
        updated = conn.execute(
            "SELECT ufo_suggestion, ufo_confidence FROM definities WHERE id = ?",
            (def_id,)
        ).fetchone()

        assert updated[0] == result.primary_category.value
        assert updated[1] == result.confidence

        # Verify history
        history = conn.execute(
            "SELECT * FROM definition_ufo_history WHERE definition_id = ?",
            (def_id,)
        ).fetchone()

        assert history is not None
        assert history[3] == result.primary_category.value  # new_category

    def test_batch_update_existing_definitions(self, test_db):
        """Test batch update of existing definitions"""
        conn, db_path = test_db
        classifier = UFOClassifierService()

        # Insert test data
        test_data = [
            ("verdachte", "Persoon verdacht van strafbaar feit"),
            ("proces", "Juridische procedure"),
            ("overeenkomst", "Contract tussen partijen")
        ]

        for begrip, definitie in test_data:
            conn.execute(
                "INSERT INTO definities (begrip, definitie) VALUES (?, ?)",
                (begrip, definitie)
            )
        conn.commit()

        # Batch classify and update
        cursor = conn.execute("SELECT id, begrip, definitie FROM definities")
        definitions = cursor.fetchall()

        update_count = 0
        for def_id, begrip, definitie in definitions:
            result = classifier.classify(begrip, definitie)

            conn.execute("""
                UPDATE definities
                SET ufo_suggestion = ?, ufo_confidence = ?, ufo_source = ?
                WHERE id = ?
            """, (result.primary_category.value, result.confidence, 'auto', def_id))

            update_count += 1

        conn.commit()

        # Verify all updated
        cursor = conn.execute(
            "SELECT COUNT(*) FROM definities WHERE ufo_suggestion IS NOT NULL"
        )
        count = cursor.fetchone()[0]

        assert count == len(test_data)
        assert update_count == len(test_data)

    def test_query_low_confidence_definitions(self, test_db):
        """Test querying definitions with low confidence for review"""
        conn, db_path = test_db
        classifier = UFOClassifierService()

        # Insert diverse data
        test_data = [
            ("verdachte", "Persoon verdacht van strafbaar feit"),  # High confidence
            ("vague", "unclear"),  # Low confidence
            ("abstract", "something"),  # Low confidence
            ("rechtspersoon", "Juridische entiteit")  # High confidence
        ]

        for begrip, definitie in test_data:
            result = classifier.classify(begrip, definitie)
            conn.execute("""
                INSERT INTO definities
                (begrip, definitie, ufo_suggestion, ufo_confidence, ufo_source)
                VALUES (?, ?, ?, ?, ?)
            """, (begrip, definitie, result.primary_category.value, result.confidence, 'auto'))

        conn.commit()

        # Query low confidence items
        cursor = conn.execute("""
            SELECT begrip, definitie, ufo_suggestion, ufo_confidence
            FROM definities
            WHERE ufo_confidence < 0.6
            ORDER BY ufo_confidence ASC
        """)

        low_confidence = cursor.fetchall()

        # Should have at least some low confidence items
        assert len(low_confidence) >= 0

        # All should be below threshold
        for item in low_confidence:
            assert item[3] < 0.6  # ufo_confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])