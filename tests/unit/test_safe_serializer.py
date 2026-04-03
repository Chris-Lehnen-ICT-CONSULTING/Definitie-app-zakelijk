"""Tests for safe_serializer module (DEF-387).

Verifies JSON + HMAC-SHA256 serialization replaces pickle safely.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.safe_serializer import (
    _SEPARATOR,
    _get_hmac_key,
    safe_load,
    safe_save,
)

pytestmark = [pytest.mark.unit]


@pytest.fixture
def tmp_file(tmp_path):
    return tmp_path / "test_data.json"


@pytest.fixture
def hmac_key(tmp_path):
    """Use a fixed HMAC key for reproducible tests."""
    key_file = tmp_path / ".hmac_key"
    key = b"test-key-32-bytes-for-hmac-test!"
    key_file.write_bytes(key)
    with patch("utils.safe_serializer._KEY_FILE", key_file):
        yield key


class TestSafeRoundtrip:
    """Verify data survives save → load cycle."""

    def test_dict_roundtrip(self, tmp_file, hmac_key):
        data = {"key": "value", "number": 42, "nested": {"a": [1, 2, 3]}}
        safe_save(data, tmp_file)
        loaded = safe_load(tmp_file)
        assert loaded == data

    def test_list_roundtrip(self, tmp_file, hmac_key):
        data = ["one", "two", "three"]
        safe_save(data, tmp_file)
        loaded = safe_load(tmp_file)
        assert loaded == data

    def test_datetime_roundtrip(self, tmp_file, hmac_key):
        data = {"timestamp": datetime(2026, 3, 27, 12, 0, 0)}
        safe_save(data, tmp_file)
        loaded = safe_load(tmp_file)
        assert isinstance(loaded["timestamp"], datetime)
        assert loaded["timestamp"].year == 2026

    def test_none_values(self, tmp_file, hmac_key):
        data = {"empty": None, "list": [None, "value"]}
        safe_save(data, tmp_file)
        loaded = safe_load(tmp_file)
        assert loaded == data


class TestHMACIntegrity:
    """Verify HMAC prevents tampering."""

    def test_tampered_data_raises(self, tmp_file, hmac_key):
        safe_save({"secret": "data"}, tmp_file)
        content = tmp_file.read_bytes()
        json_bytes, sig = content.rsplit(_SEPARATOR, 1)
        tampered = json.dumps({"secret": "HACKED"}).encode() + _SEPARATOR + sig
        tmp_file.write_bytes(tampered)
        with pytest.raises(ValueError, match="HMAC verification failed"):
            safe_load(tmp_file)

    def test_tampered_signature_raises(self, tmp_file, hmac_key):
        safe_save({"data": "ok"}, tmp_file)
        content = tmp_file.read_bytes()
        json_bytes, _ = content.rsplit(_SEPARATOR, 1)
        bad_sig = b"\x00" * 32
        tmp_file.write_bytes(json_bytes + _SEPARATOR + bad_sig)
        with pytest.raises(ValueError, match="HMAC verification failed"):
            safe_load(tmp_file)

    def test_missing_signature_raises(self, tmp_file, hmac_key):
        tmp_file.write_bytes(b'{"data": "no signature"}')
        with pytest.raises(ValueError, match="no HMAC signature"):
            safe_load(tmp_file)

    def test_file_not_found_raises(self, tmp_file):
        with pytest.raises(FileNotFoundError):
            safe_load(tmp_file)


class TestAtomicWrite:
    """Verify atomic write behavior."""

    def test_creates_parent_dirs(self, tmp_path, hmac_key):
        deep_file = tmp_path / "a" / "b" / "c" / "data.json"
        safe_save({"nested": True}, deep_file)
        assert deep_file.exists()
        assert safe_load(deep_file) == {"nested": True}

    def test_no_temp_file_left_on_success(self, tmp_file, hmac_key):
        safe_save({"clean": True}, tmp_file)
        temp = tmp_file.with_suffix(tmp_file.suffix + ".tmp")
        assert not temp.exists()


class TestHMACKeyManagement:
    """Verify HMAC key generation and retrieval."""

    def test_env_var_takes_precedence(self, tmp_path):
        with (
            patch.dict(os.environ, {"CACHE_HMAC_KEY": "my-secret-key"}),
            patch("utils.safe_serializer._KEY_FILE", tmp_path / "unused"),
        ):
            key = _get_hmac_key()
            assert key == b"my-secret-key"

    def test_generates_key_if_missing(self, tmp_path):
        key_file = tmp_path / ".hmac_key"
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("utils.safe_serializer._KEY_FILE", key_file),
        ):
            os.environ.pop("CACHE_HMAC_KEY", None)
            key = _get_hmac_key()
            assert len(key) == 32
            assert key_file.exists()
