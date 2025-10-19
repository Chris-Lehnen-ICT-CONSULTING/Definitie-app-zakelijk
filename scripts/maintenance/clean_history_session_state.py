#!/usr/bin/env python3
"""Clean History Tab related session state keys"""

import sys

import streamlit as st


def clean_history_session_state():
    """Remove history-related keys from session state"""
    history_keys = [
        "history_date_range",
        "history_start_date",
        "history_end_date",
        "history_status_filter",
        "history_context_filter",
        "history_search",
        "history_filters",
        "history_page",
        "history_selected",
        "history_sort",
    ]

    removed = []
    for key in history_keys:
        if key in st.session_state:
            del st.session_state[key]
            removed.append(key)

    if removed:
        print(f"Removed {len(removed)} history-related session state keys:")
        for key in removed:
            print(f"  - {key}")
    else:
        print("No history-related session state keys found")

    return removed


if __name__ == "__main__":
    # This can be run standalone or imported
    if "streamlit" in sys.modules:
        clean_history_session_state()
    else:
        print("Note: This script should be run within a Streamlit context")
        print(
            "Add to your main.py: from scripts.clean_history_session_state import clean_history_session_state"
        )
