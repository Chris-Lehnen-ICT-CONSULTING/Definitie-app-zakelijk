"""Safe serialization using JSON + HMAC-SHA256 integrity verification.

Replaces pickle for cache and resilience state persistence (DEF-387).
Prevents Remote Code Execution via tampered cache files.
"""

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SEPARATOR = b"\n---HMAC---\n"
_KEY_FILE = Path("cache/.hmac_key")


def _get_hmac_key() -> bytes:
    """Get or create HMAC signing key."""
    key = os.environ.get("CACHE_HMAC_KEY")
    if key:
        return key.encode()

    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()

    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_key = os.urandom(32)
    fd = os.open(str(_KEY_FILE), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, new_key)
    finally:
        os.close(fd)
    logger.info("Generated new HMAC key for cache integrity")
    return new_key


def _default_serializer(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return {"__datetime__": obj.isoformat()}
    msg = f"Object of type {type(obj).__name__} is not JSON serializable"
    raise TypeError(msg)


def _object_hook(obj: dict) -> Any:
    """JSON deserializer for custom objects."""
    if "__datetime__" in obj:
        return datetime.fromisoformat(obj["__datetime__"])
    return obj


def safe_save(data: Any, filepath: Path) -> None:
    """Serialize data to JSON and sign with HMAC-SHA256.

    Uses atomic write (temp file + rename) to prevent corruption.
    """
    filepath = Path(filepath)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")

    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        json_bytes = json.dumps(data, default=_default_serializer).encode()
        signature = hmac.new(_get_hmac_key(), json_bytes, hashlib.sha256).digest()
        payload = json_bytes + _SEPARATOR + signature

        with open(temp_file, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file, filepath)
    except OSError as e:
        logger.error("Failed to save %s: %s", filepath, e)
        try:
            temp_file.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def safe_load(filepath: Path) -> Any:
    """Load and verify HMAC-signed JSON data.

    Raises ValueError if the file has been tampered with.
    Raises FileNotFoundError if the file doesn't exist.
    """
    filepath = Path(filepath)
    with open(filepath, "rb") as f:
        content = f.read()

    if _SEPARATOR not in content:
        msg = f"Invalid format (no HMAC signature): {filepath}"
        raise ValueError(msg)

    json_bytes, signature = content.rsplit(_SEPARATOR, 1)
    expected = hmac.new(_get_hmac_key(), json_bytes, hashlib.sha256).digest()

    if not hmac.compare_digest(signature, expected):
        msg = f"HMAC verification failed — file may be tampered: {filepath}"
        raise ValueError(msg)

    return json.loads(json_bytes, object_hook=_object_hook)
