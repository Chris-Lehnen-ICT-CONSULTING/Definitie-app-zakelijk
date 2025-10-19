"""Debug logging for voorbeelden generation flow.

This module provides detailed logging for troubleshooting issues in the
voorbeelden (examples) generation pipeline. Can be enabled/disabled via
DEBUG_EXAMPLES environment variable.
"""

import logging
import os
import uuid
from datetime import UTC, datetime
from functools import wraps

# Check if debug mode is enabled
DEBUG_ENABLED = os.getenv("DEBUG_EXAMPLES", "false").lower() == "true"

# Setup dedicated logger
logger = logging.getLogger("voorbeelden.debug")
if DEBUG_ENABLED:
    logger.setLevel(logging.DEBUG)
    # Add console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - [VOORBEELDEN-DEBUG] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
else:
    logger.setLevel(logging.WARNING)


class VoorbeeldenDebugger:
    """Debug tracker for voorbeelden generation flow."""

    def __init__(self):
        """Initialize debug tracker."""
        self.generation_id = None
        self.enabled = DEBUG_ENABLED

    def start_generation(self, begrip: str, definitie: str) -> str:
        """Start tracking a new generation flow.

        Returns:
            generation_id: Unique ID for this generation flow
        """
        if not self.enabled:
            return ""

        self.generation_id = str(uuid.uuid4())[:8]
        logger.debug(f"[{self.generation_id}] === START GENERATION ===")
        logger.debug(f"[{self.generation_id}] Begrip: {begrip}")
        logger.debug(f"[{self.generation_id}] Definitie length: {len(definitie)} chars")
        logger.debug(
            f"[{self.generation_id}] Timestamp: {datetime.now(UTC).isoformat()}"
        )

        return self.generation_id

    def log_point(self, point: str, generation_id: str, **kwargs):
        """Log a specific point in the flow.

        Args:
            point: Flow point identifier (A, B, C, C2, D)
            generation_id: Generation ID for this flow
            **kwargs: Additional context to log
        """
        if not self.enabled:
            return

        logger.debug(f"[{generation_id}] >>> POINT {point}")

        # Log additional context (without full content, only counts/lengths)
        for key, value in kwargs.items():
            if value is None:
                logger.debug(f"[{generation_id}]   {key}: None")
            elif isinstance(value, list | tuple):
                logger.debug(f"[{generation_id}]   {key}: {len(value)} items")
            elif isinstance(value, dict):
                logger.debug(f"[{generation_id}]   {key}: {len(value)} keys")
            elif isinstance(value, str):
                logger.debug(f"[{generation_id}]   {key}: {len(value)} chars")
            else:
                logger.debug(f"[{generation_id}]   {key}: {value}")

    def log_session_state(self, generation_id: str, point: str):
        """Log relevant session state for debugging.

        Args:
            generation_id: Generation ID for this flow
            point: Flow point identifier
        """
        if not self.enabled:
            return

        logger.debug(f"[{generation_id}] Session State at {point}:")

        # Check for voorbeelden in session state (UI only)
        try:
            st = __import__("streamlit")
        except Exception:
            logger.debug(f"[{generation_id}] Session state unavailable (no UI context)")
            return
        if hasattr(st, "session_state"):
            relevant_keys = [
                "voorbeelden",
                "generated_voorbeelden",
                "cached_voorbeelden",
                "synoniemen",
                "antoniemen",
                "voorbeeldzinnen",
                "praktijkvoorbeelden",
                "tegenvoorbeelden",
                "toelichting",
            ]

            for key in relevant_keys:
                if key in st.session_state:
                    value = st.session_state[key]
                    if isinstance(value, dict):
                        logger.debug(
                            f"[{generation_id}]   st.session_state.{key}: dict with {len(value)} keys"
                        )
                        # Log each key's count
                        for k, v in value.items():
                            if isinstance(v, list | tuple):
                                logger.debug(
                                    f"[{generation_id}]     - {k}: {len(v)} items"
                                )
                            elif isinstance(v, str):
                                logger.debug(
                                    f"[{generation_id}]     - {k}: {len(v)} chars"
                                )
                    elif isinstance(value, list | tuple):
                        logger.debug(
                            f"[{generation_id}]   st.session_state.{key}: {len(value)} items"
                        )
                    elif isinstance(value, str):
                        logger.debug(
                            f"[{generation_id}]   st.session_state.{key}: {len(value)} chars"
                        )
                    else:
                        logger.debug(
                            f"[{generation_id}]   st.session_state.{key}: {type(value).__name__}"
                        )

    def log_cache_interaction(
        self, generation_id: str, cache_key: str, hit: bool, ttl: int | None = None
    ):
        """Log cache interactions.

        Args:
            generation_id: Generation ID for this flow
            cache_key: The cache key being used
            hit: Whether it was a cache hit or miss
            ttl: Time-to-live if relevant
        """
        if not self.enabled:
            return

        status = "HIT" if hit else "MISS"
        logger.debug(f"[{generation_id}] Cache {status}: {cache_key[:50]}...")
        if ttl:
            logger.debug(f"[{generation_id}]   TTL: {ttl} seconds")

    def log_api_call(
        self,
        generation_id: str,
        example_type: str,
        prompt_length: int,
        response_length: int,
        duration_ms: int,
    ):
        """Log API call details.

        Args:
            generation_id: Generation ID for this flow
            example_type: Type of examples being generated
            prompt_length: Length of the prompt sent
            response_length: Length of the response received
            duration_ms: API call duration in milliseconds
        """
        if not self.enabled:
            return

        logger.debug(f"[{generation_id}] API Call for {example_type}:")
        logger.debug(f"[{generation_id}]   Prompt: {prompt_length} chars")
        logger.debug(f"[{generation_id}]   Response: {response_length} chars")
        logger.debug(f"[{generation_id}]   Duration: {duration_ms}ms")

    def log_error(self, generation_id: str, point: str, error: Exception):
        """Log errors in the flow.

        Args:
            generation_id: Generation ID for this flow
            point: Flow point where error occurred
            error: The exception that occurred
        """
        # Always log errors, even if debug is disabled
        logger.error(f"[{generation_id}] ERROR at point {point}: {error}")
        logger.error(f"[{generation_id}]   Type: {type(error).__name__}")

    def end_generation(
        self, generation_id: str, success: bool, results: dict | None = None
    ):
        """End tracking of generation flow.

        Args:
            generation_id: Generation ID for this flow
            success: Whether generation was successful
            results: Final results dictionary
        """
        if not self.enabled:
            return

        status = "SUCCESS" if success else "FAILED"
        logger.debug(f"[{generation_id}] === END GENERATION: {status} ===")

        if results:
            logger.debug(f"[{generation_id}] Results summary:")
            for key, value in results.items():
                if isinstance(value, list | tuple):
                    logger.debug(f"[{generation_id}]   {key}: {len(value)} items")
                elif isinstance(value, str):
                    logger.debug(f"[{generation_id}]   {key}: {len(value)} chars")
                else:
                    logger.debug(f"[{generation_id}]   {key}: {type(value).__name__}")


# Global debugger instance
debugger = VoorbeeldenDebugger()


def debug_flow_point(point: str):
    """Decorator to mark flow points for debugging.

    Args:
        point: Flow point identifier (A, B, C, C2, D)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not DEBUG_ENABLED:
                return func(*args, **kwargs)

            # Try to extract generation_id from kwargs or create new
            generation_id = kwargs.get("generation_id", "")
            if not generation_id and len(args) > 0:
                # Check if first arg has generation_id attribute
                if hasattr(args[0], "generation_id"):
                    generation_id = args[0].generation_id

            if not generation_id:
                generation_id = str(uuid.uuid4())[:8]

            debugger.log_point(point, generation_id, function=func.__name__)

            try:
                result = func(*args, **kwargs)
                debugger.log_point(
                    f"{point}_complete",
                    generation_id,
                    success=True,
                    result_type=type(result).__name__,
                )
                return result
            except Exception as e:
                debugger.log_error(generation_id, point, e)
                raise

        return wrapper

    return decorator


def get_debug_info() -> dict:
    """Get current debug information.

    Returns:
        Dictionary with debug status and current generation ID
    """
    return {
        "enabled": DEBUG_ENABLED,
        "generation_id": debugger.generation_id,
        "env_var": "DEBUG_EXAMPLES",
    }
