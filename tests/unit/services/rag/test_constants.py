"""Tests voor RAG constants (DEF-365)."""

from services.rag.constants import (
    COLLECTION_TYPE_MAP,
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
