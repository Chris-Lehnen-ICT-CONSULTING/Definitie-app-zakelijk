#!/usr/bin/env python3
"""Test rate limiter in Streamlit UI context."""

import pytest
import streamlit as st
import asyncio
import time
import sys
sys.path.insert(0, 'src')

# Configureer pagina
# Skip this UI test when running under pytest without full Streamlit API
if not hasattr(st, "set_page_config"):
    pytest.skip(
        "Streamlit mocked without set_page_config; skipping UI rate limiter UI test",
        allow_module_level=True,
    )

st.set_page_config(
    page_title="Rate Limiter Test",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Rate Limiter Test - Endpoint-Specific")
st.markdown("Test om te verifiëren dat endpoint-specifieke rate limiting werkt")

# Test opties
col1, col2 = st.columns(2)
with col1:
    test_type = st.selectbox(
        "Test Type",
        ["Quick Test (3 requests)", "Stress Test (10 requests)", "Parallel Endpoints"]
    )
with col2:
    endpoint = st.selectbox(
        "Endpoint",
        ["examples_generation_sentence", "examples_generation_practical", "definition_generation"]
    )

if st.button("🚀 Start Test"):
    from utils.integrated_resilience import get_integrated_system, with_full_resilience
    from utils.smart_rate_limiter import RequestPriority

    async def run_test():
        system = await get_integrated_system()

        # Simuleer API call
        async def simulate_call(endpoint_name: str, call_id: int):
            @with_full_resilience(
                endpoint_name=endpoint_name,
                priority=RequestPriority.NORMAL,
                timeout=10.0
            )
            async def mock_api():
                await asyncio.sleep(0.1)  # Simuleer API latency
                return f"Result from {endpoint_name} - Call {call_id}"

            return await mock_api()

        results = []

        if test_type == "Quick Test (3 requests)":
            st.info(f"Running 3 requests to {endpoint}...")
            progress = st.progress(0)

            for i in range(3):
                start = time.time()
                try:
                    result = await simulate_call(endpoint, i)
                    elapsed = time.time() - start
                    results.append(("✅", f"Call {i}", elapsed, result))
                except Exception as e:
                    elapsed = time.time() - start
                    results.append(("❌", f"Call {i}", elapsed, str(e)))
                progress.progress((i + 1) / 3)

        elif test_type == "Stress Test (10 requests)":
            st.info(f"Running 10 parallel requests to {endpoint}...")

            tasks = [simulate_call(endpoint, i) for i in range(10)]
            start = time.time()

            completed = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(completed):
                elapsed = time.time() - start
                if isinstance(result, Exception):
                    results.append(("❌", f"Call {i}", elapsed, str(result)))
                else:
                    results.append(("✅", f"Call {i}", elapsed, result))

        else:  # Parallel Endpoints
            st.info("Running parallel requests to multiple endpoints...")

            endpoints = [
                "examples_generation_sentence",
                "examples_generation_practical",
                "definition_generation"
            ]

            tasks = []
            for ep in endpoints:
                for i in range(3):
                    tasks.append((ep, i, simulate_call(ep, i)))

            for ep, i, task in tasks:
                start = time.time()
                try:
                    result = await task
                    elapsed = time.time() - start
                    results.append(("✅", f"{ep} - Call {i}", elapsed, "Success"))
                except Exception as e:
                    elapsed = time.time() - start
                    results.append(("❌", f"{ep} - Call {i}", elapsed, str(e)))

        # Toon resultaten
        st.markdown("### 📊 Resultaten")

        # Maak tabel
        import pandas as pd
        df = pd.DataFrame(results, columns=["Status", "Request", "Time (s)", "Result"])

        # Kleur codering
        def color_status(val):
            if val == "✅":
                return 'color: green'
            elif val == "❌":
                return 'color: red'
            return ''

        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)

        # Statistieken
        success_count = sum(1 for status, _, _, _ in results if status == "✅")
        total_count = len(results)
        success_rate = success_count / total_count * 100 if total_count > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Success Rate", f"{success_rate:.0f}%")
        col2.metric("Successful", success_count)
        col3.metric("Failed", total_count - success_count)

        # System status
        st.markdown("### 🔧 System Status")
        status = system.get_system_status()

        for ep, limiter_status in status['rate_limiters'].items():
            with st.expander(f"📊 {ep}"):
                col1, col2 = st.columns(2)
                col1.metric("Current Rate", f"{limiter_status['current_rate']:.1f} req/s")
                col1.metric("Total Requests", limiter_status['stats']['total_requests'])
                col2.metric("Queued", limiter_status['stats']['total_queued'])
                col2.metric("Dropped", limiter_status['stats']['total_dropped'])

        await system.stop()

    # Run async test
    asyncio.run(run_test())

# Informatie
with st.sidebar:
    st.markdown("### i️ Rate Limiter Info")
    st.markdown("""
    **Endpoint Configuraties:**
    - `examples_generation_*`: 3 req/s
    - `definition_generation`: 2 req/s
    - `web_search`: 1 req/s

    **Features:**
    - Endpoint-specifieke token buckets
    - Priority-based queueing
    - Adaptive rate adjustment
    - Graceful degradation
    """)

    st.markdown("### 🔍 Wat te verwachten")
    st.markdown("""
    - **Quick Test**: Alle 3 requests zouden moeten slagen
    - **Stress Test**: Eerste ~3-5 slagen, rest krijgt timeout
    - **Parallel**: Elke endpoint werkt onafhankelijk
    """)

if __name__ == "__main__":
    st.write("Run with: `streamlit run test_ui_rate_limiter.py`")
