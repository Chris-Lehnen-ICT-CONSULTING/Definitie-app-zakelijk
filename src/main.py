"""
Main application file for DefinitieAgent - Modern tabbed interface.
A Streamlit application for generating and validating legal definitions.

This module serves as the entry point for the DefinitieAgent application,
handling initialization, configuration, and launching the main user interface.
"""

from dotenv import load_dotenv

# Load .env file before any other imports that might need environment variables
load_dotenv()

import logging
import os
import sys
import time
from pathlib import Path

# Add src directory to Python path for proper imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

from ui.session_state import SessionStateManager
from ui.tabbed_interface import TabbedInterface
from utils.exceptions import log_and_display_error

# Setup structured logging if enabled via environment variable
from utils.structured_logging import setup_structured_logging

if os.getenv("STRUCTURED_LOGGING", "false").lower() == "true":
    setup_structured_logging(enable_json=True, log_file="logs/app.json.log")

# Configureer basis logging (fallback als structured logging niet enabled is)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
try:
    # Voeg PII/redactie filter toe aan root logger
    from utils.logging_filters import PIIRedactingFilter

    _root = logging.getLogger()
    if not any(isinstance(f, PIIRedactingFilter) for f in _root.filters):
        _root.addFilter(PIIRedactingFilter())
except Exception:  # Fail-safe: logging mag nooit breken
    pass

# Initialiseer logger - Stel logging in voor deze module
logger = logging.getLogger(__name__)  # Verkrijg logger instantie voor dit bestand

# Configureer Streamlit pagina - Stel basis pagina instellingen in
st.set_page_config(
    page_title="DefinitieAgent",  # Browser tab titel
    page_icon="🧠",  # Browser tab icoon
    layout="wide",  # Gebruik volledige breedte van de pagina
    initial_sidebar_state="expanded",  # Start met uitgevouwen sidebar
)

# Let op: geen .env-bestand laden; vertrouw op systeem-omgeving


@st.cache_resource
def get_tabbed_interface():
    """
    Cached TabbedInterface instance (reused across reruns).

    Returns singleton interface object. This eliminates 200ms overhead per rerun
    by instantiating TabbedInterface only once instead of on every Streamlit rerun.

    IMPORTANT: TabbedInterface must be stateless (no session-specific state stored).
    All session state is passed as parameters to render() methods.

    Returns:
        TabbedInterface: Cached singleton instance

    Performance Impact:
        - Before: 200ms overhead per rerun (6 reruns = 1.2s wasted)
        - After: ~10ms overhead per rerun (cache hit)
        - Savings: 190ms per rerun
    """
    logger.info(
        "🔄 Cold start: TabbedInterface initialization (expected once per session)"
    )
    return TabbedInterface()


def main():
    """Hoofd applicatie functie.

    Deze functie is het startpunt voor de DefinitieAgent applicatie.
    Het initialiseert alle benodigde componenten en start de gebruikersinterface.

    Raises:
        Exception: Alle onverwachte fouten worden gelogd en getoond aan gebruiker
    """
    try:
        # Measure Streamlit initialization overhead only
        init_start = time.perf_counter()
        SessionStateManager.initialize_session_state()
        init_ms = (time.perf_counter() - init_start) * 1000

        # Create interface (CACHED via @st.cache_resource)
        # First call: ~200ms (initialization), Subsequent calls: ~10ms (cache hit)
        interface_start = time.perf_counter()
        interface = get_tabbed_interface()  # OPTIMIZED: Cached singleton
        interface_ms = (time.perf_counter() - interface_start) * 1000

        # Measure UI render overhead only
        # Business logic (definition generation, validation, etc.) happens here
        # but is timed separately within the service layers
        render_start = time.perf_counter()
        interface.render()
        render_ms = (time.perf_counter() - render_start) * 1000

        # Track separate metrics for accurate performance monitoring
        _track_streamlit_metrics(init_ms, interface_ms, render_ms)

    except Exception as e:
        # Log en toon startup fouten - Log en toon opstartfouten
        logger.error(f"Applicatie fout: {e!s}")  # Log fout voor debugging
        st.error(
            log_and_display_error(e, "applicatie opstarten")
        )  # Toon gebruikersvriendelijke fout


def _is_heavy_operation(render_ms: float) -> bool:
    """Detect heavy operations based on render time.

    Heavy operations (definition generation, voorbeelden generation, etc.) involve
    multiple sequential API calls and naturally take 5+ seconds to complete.
    Pure UI reruns (page navigation, state updates) should complete in <200ms.

    This timing-based approach is more reliable than flag-based detection because:
    - Flags are set DURING render (in button handlers), not BEFORE
    - Checking flags before render starts always returns False
    - Timing-based check happens AFTER render completes (has actual data)

    Args:
        render_ms: Render time in milliseconds (measured AFTER render completes)

    Returns:
        True if this appears to be a heavy operation (API calls, business logic)
        False if this is a pure UI rerun (navigation, state updates)

    Examples:
        - 50ms render → False (UI-only rerun)
        - 35,000ms render → True (6 voorbeelden API calls @ 5s each)
        - 4,000ms render → False (below threshold, probably single fast API call)

    History:
        - DEF-111: Replaced flag-based detection to fix false alarm pollution
        - Prior: Used session_state flags (generating_definition, etc.) but they
                 were checked before being set, causing 74,569% "regressions"
    """
    heavy_threshold_ms = 5000  # 5 seconds
    return render_ms > heavy_threshold_ms


def _track_streamlit_metrics(init_ms: float, interface_ms: float, render_ms: float):
    """Track separate Streamlit performance metrics for granular monitoring.

    This function tracks three distinct phases of Streamlit request handling:
    1. Session state initialization (init_ms)
    2. TabbedInterface instantiation (interface_ms) - OPTIMIZED with @st.cache_resource
    3. UI rendering (render_ms)

    Args:
        init_ms: Time spent in SessionStateManager.initialize_session_state()
        interface_ms: Time spent creating TabbedInterface
                      (should be ~10ms after caching)
        render_ms: Time spent rendering UI (includes business logic)

    Performance Targets:
        - init_ms: < 10ms (session state setup)
        - interface_ms: < 20ms after first call (cache hit should be ~10ms)
        - render_ms: < 200ms for UI-only reruns, 5-20s for definition generation

    Regression Detection:
        - interface_ms > 50ms: Possible cache miss or initialization overhead
        - render_ms > 200ms without heavy operation: UI rendering regression
    """
    # Detect first load (cold start) - cache miss is EXPECTED on first request
    is_first_request = SessionStateManager.get_value("_first_request_done") is None
    if is_first_request:
        SessionStateManager.set_value("_first_request_done", True)

    try:
        from monitoring.performance_tracker import get_tracker

        tracker = get_tracker()
        total_ms = init_ms + interface_ms + render_ms

        # Detect if this is a heavy operation by timing (checked AFTER render completes)
        # Heavy operations (definition generation, voorbeelden) take 5+ seconds
        # UI-only reruns complete in <200ms
        # DEF-111: Replaced flag-based detection to fix false alarm pollution
        is_heavy_operation = _is_heavy_operation(render_ms)

        # Track individual metrics
        tracker.track_metric(
            "streamlit_init_ms",
            init_ms,
            metadata={
                "session_id": id(st.session_state),
                "platform": sys.platform,
            },
        )

        tracker.track_metric(
            "streamlit_interface_ms",
            interface_ms,
            metadata={
                "session_id": id(st.session_state),
                "platform": sys.platform,
            },
        )

        tracker.track_metric(
            "streamlit_render_ms",
            render_ms,
            metadata={
                "session_id": id(st.session_state),
                "platform": sys.platform,
                "is_heavy_operation": is_heavy_operation,
            },
        )

        # Track total for backward compatibility
        tracker.track_metric(
            "streamlit_total_request_ms",
            total_ms,
            metadata={
                "session_id": id(st.session_state),
                "platform": sys.platform,
                "is_heavy_operation": is_heavy_operation,
            },
        )

        # Regression checking - only for lightweight operations
        if not is_heavy_operation:
            # Check interface instantiation time (should be fast after caching)
            if interface_ms > 50:
                if is_first_request:
                    # Cold start - expected behavior, log as INFO
                    logger.info(
                        f"Cold start complete: {interface_ms:.1f}ms "
                        f"(first load, cache populated)"
                    )
                else:
                    # Unexpected cache miss - this IS a problem
                    logger.warning(
                        f"TabbedInterface unexpected cache miss: {interface_ms:.1f}ms "
                        f"(expected <20ms). Check @st.cache_resource effectiveness."
                    )

            # Check render time
            alert = tracker.check_regression("streamlit_render_ms", render_ms)
            if alert == "CRITICAL":
                logger.warning(
                    f"CRITICAL render regression: {render_ms:.1f}ms "
                    f"(>20% slechter dan baseline) - investigate UI rendering overhead"
                )
            elif alert == "WARNING":
                logger.warning(
                    f"WARNING render regression: {render_ms:.1f}ms "
                    f"(>10% slechter dan baseline) - check for inefficiencies"
                )
            else:
                logger.debug(
                    f"Request breakdown: init={init_ms:.1f}ms, "
                    f"interface={interface_ms:.1f}ms, render={render_ms:.1f}ms, "
                    f"total={total_ms:.1f}ms"
                )
        else:
            # Log heavy operations separately without regression checking
            logger.info(
                f"Heavy operation completed in {total_ms:.1f}ms "
                f"(init={init_ms:.1f}ms, interface={interface_ms:.1f}ms, "
                f"render={render_ms:.1f}ms)"
            )

    except Exception as e:
        # Performance tracking mag nooit de applicatie breken
        logger.debug(f"Performance tracking fout (non-critical): {e}")


if __name__ == "__main__":
    # Start de applicatie alleen als dit bestand direct wordt uitgevoerd
    main()  # Roep de hoofd functie aan om de applicatie te starten
