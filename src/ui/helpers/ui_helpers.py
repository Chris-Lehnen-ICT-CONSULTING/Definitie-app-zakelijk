"""
Unified UI Helper Functions for DefinitieAgent.

This module consolidates common UI patterns to eliminate duplicate code
across all tab components while maintaining exact functionality.
"""

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

import streamlit as st

from ui.cached_services import get_service, initialize_services_once
from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


# === Session State Helpers ===

def ensure_session_value(key: str, default: Any = None) -> Any:
    """
    Get or initialize a session state value with a default.

    Replaces repeated pattern:
        if key not in st.session_state:
            st.session_state[key] = default
        return st.session_state[key]
    """
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def update_session_values(**kwargs) -> None:
    """
    Update multiple session state values at once.

    Replaces repeated pattern:
        st.session_state["key1"] = value1
        st.session_state["key2"] = value2
        ...
    """
    for key, value in kwargs.items():
        st.session_state[key] = value


def clear_session_values(*keys: str) -> None:
    """
    Clear multiple session state values.

    Replaces repeated pattern:
        if "key1" in st.session_state:
            del st.session_state["key1"]
        ...
    """
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


# === Service Access Helpers ===

def get_service_safe(service_name: str) -> Any:
    """
    Get a service with automatic initialization and error handling.

    Replaces repeated pattern:
        initialize_services_once()
        container = st.session_state.get("service_container")
        if not container:
            st.error("Service container not initialized")
            return None
        service = container.get_service(service_name)
    """
    try:
        initialize_services_once()
        return get_service(service_name)
    except Exception as e:
        logger.error(f"Failed to get service {service_name}: {e}")
        return None


def get_orchestrator():
    """Get orchestrator service with error handling."""
    return get_service_safe("orchestrator")


def get_repository():
    """Get repository service with error handling."""
    return get_service_safe("repository")


def get_web_lookup():
    """Get web lookup service with error handling."""
    return get_service_safe("web_lookup")


# === UI Feedback Helpers ===

def show_result(success: bool, message: str, icon: str = None) -> None:
    """
    Display a result message with appropriate styling.

    Replaces repeated pattern:
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
    """
    if success:
        icon = icon or "✅"
        st.success(f"{icon} {message}")
    else:
        icon = icon or "❌"
        st.error(f"{icon} {message}")


def show_metrics(metrics: dict[str, Any], columns: int = 3) -> None:
    """
    Display metrics in a grid layout.

    Replaces repeated pattern:
        cols = st.columns(3)
        for i, (key, value) in enumerate(metrics.items()):
            cols[i % 3].metric(key, value)
    """
    if not metrics:
        return

    cols = st.columns(columns)
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            st.metric(label, value)


# === Progress Indicators ===

@contextmanager
def show_progress(message: str, type: str = "spinner") -> Generator:
    """
    Unified progress indicator context manager.

    Replaces repeated pattern:
        with st.spinner("Loading..."):
            # do work
    """
    if type == "spinner":
        with st.spinner(message):
            yield
    elif type == "status":
        with st.status(message, expanded=True) as status:
            yield status
    else:
        yield


# === Error Handling ===

def safe_operation(
    operation_name: str = "operation",
    show_error: bool = True,
    default_return: Any = None
) -> Callable:
    """
    Decorator for safe operation execution with error handling.

    Replaces repeated pattern:
        try:
            # do operation
        except Exception as e:
            logger.error(f"Error: {e}")
            st.error(f"Error: {e}")
            return None
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T | Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T | Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                if show_error:
                    st.error(f"Fout in {operation_name}: {str(e)}")
                return default_return
        return wrapper
    return decorator


# === Button Handlers ===

def create_action_button(
    label: str,
    action: Callable,
    key: str = None,
    type: str = "secondary",
    confirm: str = None,
    disabled: bool = False,
    **kwargs
) -> Any:
    """
    Create a button with optional confirmation and execute action.

    Replaces repeated pattern:
        if st.button("Label", key="key", type="primary"):
            with st.spinner("Processing..."):
                try:
                    result = action()
                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error: {e}")
    """
    button_clicked = st.button(
        label,
        key=key,
        type=type,
        disabled=disabled,
        **kwargs
    )

    if button_clicked:
        if confirm:
            if not st.checkbox(f"Bevestig: {confirm}", key=f"{key}_confirm"):
                st.warning("Actie geannuleerd - bevestiging vereist")
                return None

        with show_progress(f"{label}..."):
            result = action()
            if result is not None:
                return result

    return None


# === Data Validation ===

def validate_required_fields(
    fields: dict[str, Any],
    field_names: dict[str, str] = None
) -> tuple[bool, list[str]]:
    """
    Validate required fields and return validation status.

    Replaces repeated pattern:
        errors = []
        if not field1:
            errors.append("Field1 is required")
        if not field2:
            errors.append("Field2 is required")
        ...
    """
    errors = []
    field_names = field_names or {}

    for field_key, field_value in fields.items():
        display_name = field_names.get(field_key, field_key)

        if field_value is None or (
            isinstance(field_value, (str, list, dict)) and not field_value
        ):
            errors.append(f"{display_name} is verplicht")

    return len(errors) == 0, errors


def show_validation_errors(errors: list[str]) -> None:
    """Display validation errors in a consistent format."""
    if errors:
        st.error("**Validatie fouten:**")
        for error in errors:
            st.error(f"• {error}")


# === Form Helpers ===

@contextmanager
def create_form(
    key: str,
    clear_on_submit: bool = False
) -> Generator:
    """
    Create a form with automatic state management.

    Replaces repeated pattern:
        with st.form(key):
            # form fields
            if st.form_submit_button():
                # handle submission
    """
    with st.form(key=key, clear_on_submit=clear_on_submit) as form:
        yield form


def create_select_box(
    label: str,
    options: list,
    key: str,
    default_index: int = 0,
    format_func: Callable = None,
    help: str = None
) -> Any:
    """
    Create a selectbox with consistent styling and behavior.

    Replaces varied selectbox patterns across tabs.
    """
    return st.selectbox(
        label,
        options=options,
        index=default_index,
        key=key,
        format_func=format_func or str,
        help=help
    )


# === Expander Helpers ===

@contextmanager
def create_section(
    title: str,
    expanded: bool = False,
    icon: str = None
) -> Generator:
    """
    Create a section with consistent styling.

    Replaces repeated pattern:
        with st.expander("Title", expanded=True):
            # section content
    """
    display_title = f"{icon} {title}" if icon else title
    with st.expander(display_title, expanded=expanded):
        yield


# === Status Display ===

def show_status_badge(
    status: str,
    statuses_map: dict[str, tuple[str, str]] = None
) -> None:
    """
    Display a status badge with color coding.

    Default status map for common cases.
    """
    default_map = {
        "success": ("✅", "green"),
        "error": ("❌", "red"),
        "warning": ("⚠️", "orange"),
        "info": ("ℹ️", "blue"),
        "pending": ("⏳", "gray"),
        "active": ("🟢", "green"),
        "inactive": ("🔴", "red"),
    }

    statuses_map = statuses_map or default_map
    icon, color = statuses_map.get(status.lower(), ("•", "gray"))

    st.markdown(
        f"<span style='color: {color}; font-size: 1.2em;'>{icon} {status}</span>",
        unsafe_allow_html=True
    )


# === Tab Navigation ===

def create_tab_navigation(
    tabs: dict[str, Callable],
    default_tab: str = None
) -> None:
    """
    Create tab navigation with automatic state management.

    Replaces repeated tab creation patterns.
    """
    tab_names = list(tabs.keys())
    default_index = tab_names.index(default_tab) if default_tab else 0

    selected_tab = st.tabs(tab_names)[default_index]

    # Execute the selected tab's render function
    if selected_tab in tabs:
        tabs[selected_tab]()


# === Data Export Helpers ===

def create_download_button(
    data: str | bytes,
    filename: str,
    label: str = "Download",
    mime: str = "text/plain",
    key: str = None
) -> bool:
    """
    Create a download button with consistent styling.

    Replaces varied download button patterns.
    """
    return st.download_button(
        label=f"📥 {label}",
        data=data,
        file_name=filename,
        mime=mime,
        key=key
    )


# === Initialization Helper ===

def initialize_tab(
    tab_name: str,
    required_services: list[str] = None
) -> dict[str, Any]:
    """
    Initialize a tab with required services and session state.

    Returns dict of initialized services or None if initialization fails.
    """
    logger.debug(f"Initializing tab: {tab_name}")

    # Initialize session state
    SessionStateManager.initialize_session_state()

    # Initialize required services
    services = {}
    if required_services:
        for service_name in required_services:
            service = get_service_safe(service_name)
            if service is None:
                st.error(f"Kan {service_name} service niet initialiseren")
                return {}
            services[service_name] = service

    logger.debug(f"Tab {tab_name} initialized with {len(services)} services")
    return services