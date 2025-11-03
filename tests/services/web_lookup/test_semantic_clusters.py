"""
Tests for semantic clusters functionality in JuridischeSynoniemlService.

Semantic clusters groeperen gerelateerde (maar NIET synonieme) juridische begrippen
voor cascade fallback, related suggestions, en context expansion.

Test coverage:
- Cluster loading from YAML
- get_related_terms() - lookup related cluster terms
- get_cluster_name() - lookup cluster membership
- expand_with_related() - combine synonyms + related terms
- Cluster validation (duplicates, cross-contamination)
- Backward compatibility (clusters zijn optioneel)
"""

import tempfile
from pathlib import Path

import pytest

from src.services.web_lookup.synonym_service import JuridischeSynoniemlService


class TestClusterLoading:
    """Test cluster loading from YAML."""

    def test_load_clusters_from_yaml(self):
        """Test dat clusters correct worden geladen uit YAML."""
        # Create temp YAML with clusters
        yaml_content = """
# Hoofdtermen met synoniemen
hoger_beroep:
  - appel
  - appelprocedure

cassatie:
  - hogere voorziening
  - cassatieberoep

# Clusters (gerelateerde begrippen)
_clusters:
  rechtsmiddelen:
    - rechtsmiddel
    - hoger_beroep
    - cassatie
    - verzet
  straffen:
    - gevangenisstraf
    - taakstraf
    - geldboete
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)

            # Check clusters loaded
            assert len(service.clusters) == 2
            assert "rechtsmiddelen" in service.clusters
            assert "straffen" in service.clusters

            # Check cluster contents (normalized)
            assert "rechtsmiddel" in service.clusters["rechtsmiddelen"]
            assert "hoger beroep" in service.clusters["rechtsmiddelen"]
            assert "cassatie" in service.clusters["rechtsmiddelen"]
            assert "verzet" in service.clusters["rechtsmiddelen"]

            assert "gevangenisstraf" in service.clusters["straffen"]
            assert "taakstraf" in service.clusters["straffen"]
            assert "geldboete" in service.clusters["straffen"]

            # Check reverse index
            assert service.term_to_cluster["hoger beroep"] == "rechtsmiddelen"
            assert service.term_to_cluster["cassatie"] == "rechtsmiddelen"
            assert service.term_to_cluster["gevangenisstraf"] == "straffen"

        finally:
            Path(temp_path).unlink()

    def test_empty_clusters_section(self):
        """Test dat lege _clusters sectie gracefully wordt afgehandeld."""
        yaml_content = """
hoger_beroep:
  - appel

_clusters: {}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)

            # Empty clusters is valid
            assert len(service.clusters) == 0
            assert len(service.term_to_cluster) == 0

        finally:
            Path(temp_path).unlink()

    def test_no_clusters_section_backward_compatible(self):
        """Test backward compatibility: geen _clusters sectie is valid."""
        yaml_content = """
hoger_beroep:
  - appel
  - appelprocedure

cassatie:
  - hogere voorziening
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)

            # No clusters is valid (backward compatible)
            assert len(service.clusters) == 0
            assert len(service.term_to_cluster) == 0

            # Synoniemen still work
            assert len(service.synoniemen) == 2

        finally:
            Path(temp_path).unlink()

    def test_invalid_clusters_type(self):
        """Test dat invalid _clusters type (niet dict) wordt afgehandeld."""
        yaml_content = """
hoger_beroep:
  - appel

_clusters:
  - invalid_list_format
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)

            # Invalid type should be skipped (warning logged)
            assert len(service.clusters) == 0

        finally:
            Path(temp_path).unlink()


class TestGetRelatedTerms:
    """Test get_related_terms() method."""

    @pytest.fixture()
    def service_with_clusters(self):
        """Service met clusters voor tests."""
        yaml_content = """
hoger_beroep:
  - appel

cassatie:
  - hogere voorziening

_clusters:
  rechtsmiddelen:
    - rechtsmiddel
    - hoger_beroep
    - cassatie
    - verzet
    - herziening
  straffen:
    - gevangenisstraf
    - taakstraf
    - geldboete
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        service = JuridischeSynoniemlService(config_path=temp_path)
        yield service

        Path(temp_path).unlink()

    def test_get_related_terms_basic(self, service_with_clusters):
        """Test basis get_related_terms() functionaliteit."""
        related = service_with_clusters.get_related_terms("hoger_beroep")

        # Should return other terms in same cluster (exclusief zichzelf)
        assert "cassatie" in related
        assert "rechtsmiddel" in related
        assert "verzet" in related
        assert "herziening" in related

        # Should NOT include the term itself
        assert "hoger beroep" not in related

        # Should have 4 related terms (5 in cluster - 1 self)
        assert len(related) == 4

    def test_get_related_terms_normalization(self, service_with_clusters):
        """Test dat normalization werkt (underscores → spaces)."""
        # Query with underscore
        related_underscore = service_with_clusters.get_related_terms("hoger_beroep")

        # Query with space
        related_space = service_with_clusters.get_related_terms("hoger beroep")

        # Should be identical (normalization)
        assert related_underscore == related_space

    def test_get_related_terms_not_in_cluster(self, service_with_clusters):
        """Test get_related_terms() voor term niet in cluster."""
        related = service_with_clusters.get_related_terms("onbekende_term")

        # Should return empty list
        assert related == []

    def test_get_related_terms_different_cluster(self, service_with_clusters):
        """Test dat related terms alleen uit zelfde cluster komen."""
        related = service_with_clusters.get_related_terms("gevangenisstraf")

        # Should only include terms from 'straffen' cluster
        assert "taakstraf" in related
        assert "geldboete" in related

        # Should NOT include terms from other clusters
        assert "hoger beroep" not in related
        assert "cassatie" not in related


class TestGetClusterName:
    """Test get_cluster_name() method."""

    @pytest.fixture()
    def service_with_clusters(self):
        """Service met clusters voor tests."""
        yaml_content = """
_clusters:
  rechtsmiddelen:
    - rechtsmiddel
    - hoger_beroep
    - cassatie
  straffen:
    - gevangenisstraf
    - taakstraf
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        service = JuridischeSynoniemlService(config_path=temp_path)
        yield service

        Path(temp_path).unlink()

    def test_get_cluster_name_basic(self, service_with_clusters):
        """Test basis get_cluster_name() functionaliteit."""
        assert (
            service_with_clusters.get_cluster_name("hoger_beroep") == "rechtsmiddelen"
        )
        assert service_with_clusters.get_cluster_name("cassatie") == "rechtsmiddelen"
        assert service_with_clusters.get_cluster_name("gevangenisstraf") == "straffen"
        assert service_with_clusters.get_cluster_name("taakstraf") == "straffen"

    def test_get_cluster_name_normalization(self, service_with_clusters):
        """Test dat normalization werkt."""
        # Both should return same cluster
        assert (
            service_with_clusters.get_cluster_name("hoger_beroep") == "rechtsmiddelen"
        )
        assert (
            service_with_clusters.get_cluster_name("hoger beroep") == "rechtsmiddelen"
        )

    def test_get_cluster_name_not_in_cluster(self, service_with_clusters):
        """Test get_cluster_name() voor term niet in cluster."""
        assert service_with_clusters.get_cluster_name("onbekende_term") is None


class TestExpandWithRelated:
    """Test expand_with_related() method."""

    @pytest.fixture()
    def service_full(self):
        """Service met zowel synoniemen als clusters."""
        yaml_content = """
# Synoniemen
hoger_beroep:
  - appel
  - appelprocedure
  - beroepsinstantie

cassatie:
  - hogere voorziening
  - cassatieberoep

# Clusters (gerelateerde begrippen, NIET synoniemen)
_clusters:
  rechtsmiddelen:
    - rechtsmiddel
    - hoger_beroep
    - cassatie
    - verzet
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        service = JuridischeSynoniemlService(config_path=temp_path)
        yield service

        Path(temp_path).unlink()

    def test_expand_with_related_basic(self, service_full):
        """Test basis expand_with_related() functionaliteit."""
        expanded = service_full.expand_with_related(
            "hoger beroep", max_synonyms=2, max_related=2
        )

        # Should include:
        # 1. Original term
        assert "hoger beroep" in expanded

        # 2. Top synonyms (max 2)
        assert "appel" in expanded
        assert "appelprocedure" in expanded

        # 3. Related cluster terms (max 2, exclude original)
        # Related terms are: rechtsmiddel, cassatie, verzet (hoger_beroep excluded)
        cluster_terms_in_expanded = [
            t for t in expanded if t in ["rechtsmiddel", "cassatie", "verzet"]
        ]
        assert len(cluster_terms_in_expanded) <= 2

        # Total should be: 1 original + 2 synonyms + 2 related = 5
        assert len(expanded) <= 5

    def test_expand_with_related_no_synonyms(self, service_full):
        """Test expand_with_related() voor term zonder synoniemen."""
        expanded = service_full.expand_with_related(
            "rechtsmiddel", max_synonyms=3, max_related=2
        )

        # Should include original
        assert "rechtsmiddel" in expanded

        # No synonyms voor rechtsmiddel, so should only add related terms
        # Related: hoger_beroep, cassatie, verzet
        assert len(expanded) <= 3  # 1 original + 2 related

    def test_expand_with_related_no_cluster(self):
        """Test expand_with_related() voor term niet in cluster."""
        yaml_content = """
hoger_beroep:
  - appel
  - appelprocedure

# No clusters
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)
            expanded = service.expand_with_related(
                "hoger beroep", max_synonyms=2, max_related=2
            )

            # Should only include original + synonyms (no related terms)
            assert "hoger beroep" in expanded
            assert "appel" in expanded
            assert "appelprocedure" in expanded

            # Max 3 (1 original + 2 synonyms)
            assert len(expanded) <= 3

        finally:
            Path(temp_path).unlink()

    def test_expand_with_related_limits(self, service_full):
        """Test dat max_synonyms en max_related limits worden gerespecteerd."""
        # Max 1 synonym, max 1 related
        expanded = service_full.expand_with_related(
            "hoger beroep", max_synonyms=1, max_related=1
        )

        # Should have at most: 1 original + 1 synonym + 1 related = 3
        assert len(expanded) <= 3

        # Original always included
        assert "hoger beroep" in expanded

    def test_expand_with_related_no_duplicate_terms(self, service_full):
        """Test dat termen niet dubbel voorkomen (synonym + related)."""
        expanded = service_full.expand_with_related(
            "hoger beroep", max_synonyms=10, max_related=10
        )

        # Check for duplicates
        assert len(expanded) == len(set(expanded)), "Expanded list has duplicates"


class TestClusterValidation:
    """Test cluster validation (duplicate membership, cross-contamination)."""

    def test_duplicate_term_in_cluster_warns(self):
        """Test dat duplicate term binnen cluster wordt gedetecteerd."""
        yaml_content = """
_clusters:
  rechtsmiddelen:
    - hoger_beroep
    - cassatie
    - hoger_beroep  # Duplicate!
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Should load, but skip duplicate (logged as warning)
            service = JuridischeSynoniemlService(config_path=temp_path)

            # Should only have 2 unique terms
            assert len(service.clusters["rechtsmiddelen"]) == 2

        finally:
            Path(temp_path).unlink()

    def test_term_in_multiple_clusters_warns(self):
        """Test dat term in meerdere clusters wordt gedetecteerd (eerste wint)."""
        yaml_content = """
_clusters:
  rechtsmiddelen:
    - hoger_beroep
    - cassatie
  procedureel:
    - dagvaarding
    - hoger_beroep  # Cross-contamination!
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Should load, but keep first occurrence (logged as warning)
            service = JuridischeSynoniemlService(config_path=temp_path)

            # hoger_beroep should be in first cluster only
            assert service.term_to_cluster["hoger beroep"] == "rechtsmiddelen"

            # procedureel should only have 1 term
            assert len(service.clusters["procedureel"]) == 1
            assert "dagvaarding" in service.clusters["procedureel"]
            assert "hoger beroep" not in service.clusters["procedureel"]

        finally:
            Path(temp_path).unlink()


class TestClusterStatistics:
    """Test cluster statistics in get_stats()."""

    def test_stats_include_clusters(self):
        """Test dat get_stats() cluster informatie bevat."""
        yaml_content = """
hoger_beroep:
  - appel

_clusters:
  rechtsmiddelen:
    - hoger_beroep
    - cassatie
  straffen:
    - gevangenisstraf
    - taakstraf
    - geldboete
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)
            stats = service.get_stats()

            # Check cluster stats
            assert "clusters" in stats
            assert "termen_in_clusters" in stats

            assert stats["clusters"] == 2  # 2 clusters
            assert stats["termen_in_clusters"] == 5  # 5 total terms

        finally:
            Path(temp_path).unlink()

    def test_stats_no_clusters(self):
        """Test get_stats() zonder clusters (backward compatibility)."""
        yaml_content = """
hoger_beroep:
  - appel
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            service = JuridischeSynoniemlService(config_path=temp_path)
            stats = service.get_stats()

            # Should still have cluster keys, but with 0 values
            assert stats["clusters"] == 0
            assert stats["termen_in_clusters"] == 0

        finally:
            Path(temp_path).unlink()


class TestRealWorldClusters:
    """Test met echte juridische clusters uit juridische_synoniemen.yaml."""

    @pytest.fixture()
    def real_service(self):
        """Service met echte config (if available)."""
        # Try to load real config
        config_path = (
            Path(__file__).parent.parent.parent.parent
            / "config"
            / "juridische_synoniemen.yaml"
        )
        if config_path.exists():
            return JuridischeSynoniemlService(config_path=str(config_path))
        pytest.skip("Real config file not found")

    def test_rechtsmiddelen_cluster_exists(self, real_service):
        """Test dat rechtsmiddelen cluster bestaat in echte config."""
        assert "rechtsmiddelen" in real_service.clusters

        # Check expected terms
        rechtsmiddelen = real_service.clusters["rechtsmiddelen"]
        assert "hoger beroep" in rechtsmiddelen
        assert "cassatie" in rechtsmiddelen
        assert "rechtsmiddel" in rechtsmiddelen

    def test_related_terms_rechtsmiddelen(self, real_service):
        """Test get_related_terms() voor rechtsmiddelen cluster."""
        related = real_service.get_related_terms("hoger beroep")

        # Should include other rechtsmiddelen
        assert "cassatie" in related
        assert "rechtsmiddel" in related

        # Should NOT include synonyms (synoniemen zijn apart)
        # "appel" is a synonym, not a related term
        assert "appel" not in related

    def test_expand_with_related_rechtsmiddelen(self, real_service):
        """Test expand_with_related() voor hoger beroep."""
        expanded = real_service.expand_with_related(
            "hoger beroep", max_synonyms=2, max_related=2
        )

        # Should include original
        assert "hoger beroep" in expanded

        # Should include synonyms (appel, etc.)
        synonyms = real_service.get_synoniemen("hoger beroep")
        if synonyms:
            # At least one synonym should be in expanded
            assert any(s in expanded for s in synonyms[:2])

        # Should include related cluster terms (cassatie, rechtsmiddel, etc.)
        related = real_service.get_related_terms("hoger beroep")
        if related:
            # At least one related term should be in expanded
            assert any(r in expanded for r in related[:2])
