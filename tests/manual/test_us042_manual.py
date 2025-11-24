#!/usr/bin/env python3
"""
Manual test script for US-042: Anders... option fix.

Run this with:
    streamlit run tests/manual/test_us042_manual.py

This will start a Streamlit app where you can manually test
the Anders... option with various inputs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import streamlit as st

from ui.components.context_selector import ContextSelector


def main():
    st.set_page_config(
        page_title="US-042 Anders Option Test", page_icon="🧪", layout="wide"
    )

    st.title("🧪 US-042: Anders... Option Test")
    st.markdown("---")

    st.markdown(
        """
    ### Test Instructions

    1. Select "Anders..." from any dropdown
    2. Enter custom text in the input field that appears
    3. Try various edge cases:
       - Empty input
       - Special characters: & ' " ( ) € §
       - Very long text (>200 characters)
       - XSS attempts: `<script>alert('test')</script>`
       - SQL injection: `'; DROP TABLE users; --`
       - Unicode: 🇳🇱 • § € ™

    The component should:
    - ✅ Never crash
    - ✅ Sanitize dangerous input
    - ✅ Accept valid Dutch legal text
    - ✅ Show warnings for invalid input
    - ✅ Limit input to 200 characters
    """
    )

    st.markdown("---")

    # Test the component
    selector = ContextSelector()

    with st.container():
        st.header("📋 Context Selector Component")

        # Render the component
        result = selector.render()

        # Show the results
        st.markdown("---")
        st.header("📊 Results")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Raw Output")
            st.json(result)

        with col2:
            st.subheader("Formatted Output")

            if result.get("organisatorische_context"):
                st.markdown("**Organisatorische Context:**")
                for item in result["organisatorische_context"]:
                    st.write(f"- {item}")

            if result.get("juridische_context"):
                st.markdown("**Juridische Context:**")
                for item in result["juridische_context"]:
                    st.write(f"- {item}")

            if result.get("wettelijke_basis"):
                st.markdown("**Wettelijke Basis:**")
                for item in result["wettelijke_basis"]:
                    st.write(f"- {item}")

    # Test cases section
    st.markdown("---")
    st.header("🧪 Edge Case Test Results")

    test_cases = [
        ("Empty string", ""),
        ("Whitespace only", "   \t\n   "),
        ("Normal text", "Ministerie van Justitie"),
        ("Special chars", "Justitie & Veiligheid"),
        ("Quotes", "Richtlijn 'test' en \"andere\""),
        ("Parentheses", "Wet (EU) 2016/680"),
        ("Long text", "A" * 250),
        ("XSS attempt", "<script>alert('XSS')</script>"),
        ("SQL injection", "'; DROP TABLE users; --"),
        ("Unicode", "Test • § € ™ 🇳🇱"),
        ("Control chars", "Test\x00\x01\x1f\x7f"),
    ]

    with st.expander("View Test Case Results", expanded=False):
        for name, test_input in test_cases:
            col1, col2, col3 = st.columns([2, 3, 3])

            with col1:
                st.write(f"**{name}:**")

            with col2:
                st.code(repr(test_input)[:50])

            with col3:
                try:
                    result = selector._sanitize_custom_input(test_input)
                    if result:
                        st.success(f"✅ {repr(result)[:50]}")
                    else:
                        st.info("🚫 Rejected (None)")
                except Exception as e:
                    st.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
