"""Tests voor RAG constants (DEF-365, DEF-379)."""

from services.rag.constants import (
    BRON_TYPES,
    COLLECTION_TYPE_MAP,
    COLLECTION_TYPE_TO_BRON_TYPE,
    COLLECTION_TYPES,
    RECHTSGEBIEDEN,
    CollectionType,
)


class TestCollectionTypes:
    def test_all_unique_keys(self):
        """Alle collection type keys zijn uniek."""
        keys = [ct.key for ct in COLLECTION_TYPES]
        assert len(keys) == len(set(keys))

    def test_map_matches_tuple(self):
        """COLLECTION_TYPE_MAP bevat exact dezelfde items als COLLECTION_TYPES."""
        assert len(COLLECTION_TYPE_MAP) == len(COLLECTION_TYPES)
        for ct in COLLECTION_TYPES:
            assert ct.key in COLLECTION_TYPE_MAP
            assert COLLECTION_TYPE_MAP[ct.key] == ct

    def test_vrij_type_exists(self):
        """Default type 'vrij' moet bestaan."""
        assert "vrij" in COLLECTION_TYPE_MAP

    def test_namedtuple_fields(self):
        """CollectionType heeft key, label, icon velden."""
        ct = COLLECTION_TYPES[0]
        assert isinstance(ct, CollectionType)
        assert ct.key
        assert ct.label
        assert ct.icon


class TestCollectionTypeToBronType:
    """DEF-379: COLLECTION_TYPE_TO_BRON_TYPE mapping."""

    def test_alle_collection_types_aanwezig(self):
        """Elke collection type key heeft een entry in de mapping."""
        for ct in COLLECTION_TYPES:
            assert ct.key in COLLECTION_TYPE_TO_BRON_TYPE

    def test_wetgeving_mapped_naar_wetgeving(self):
        """Collection type 'wetgeving' → bron_type 'wetgeving'."""
        assert COLLECTION_TYPE_TO_BRON_TYPE["wetgeving"] == "wetgeving"

    def test_overige_types_zijn_none(self):
        """Collection types zonder directe bron_type → None."""
        for key in ("kamerstukken", "beleid", "keten", "vrij"):
            assert COLLECTION_TYPE_TO_BRON_TYPE[key] is None

    def test_bron_types_zijn_geldig(self):
        """Alle non-None waarden in de mapping zijn geldige BRON_TYPES."""
        for bron_type in COLLECTION_TYPE_TO_BRON_TYPE.values():
            if bron_type is not None:
                assert bron_type in BRON_TYPES


class TestRechtsgebieden:
    def test_not_empty(self):
        assert len(RECHTSGEBIEDEN) > 0

    def test_keys_are_snake_case(self):
        for key in RECHTSGEBIEDEN:
            assert isinstance(key, str)
            assert key == key.lower()
            assert " " not in key

    def test_labels_are_titlecase(self):
        for label in RECHTSGEBIEDEN.values():
            assert isinstance(label, str)
            assert label[0].isupper()
