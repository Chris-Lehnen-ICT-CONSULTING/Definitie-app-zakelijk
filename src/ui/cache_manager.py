"""
Cache management UI components for DefinitieAgent.
Provides interface for monitoring and managing the caching system.
"""

import streamlit as st

from utils.cache import clear_cache, configure_cache, get_cache_stats


class CacheManager:
    """Cache management interface for Streamlit."""

    @staticmethod
    def display_cache_stats() -> None:
        """Display cache statistics in Streamlit."""
        stats = get_cache_stats()

        st.subheader("📊 Cache Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Cache Entries", stats["entries"])

        with col2:
            st.metric("Cache Size", f"{stats['total_size_mb']:.1f} MB")

        with col3:
            if stats["entries"] > 0:
                st.metric("Cache Efficiency", "Active")
            else:
                st.metric("Cache Efficiency", "Empty")

        if stats["entries"] > 0:
            st.write(f"**Oldest Entry:** {stats['oldest_entry']}")
            st.write(f"**Newest Entry:** {stats['newest_entry']}")

    @staticmethod
    def display_cache_controls() -> None:
        """Display cache control buttons."""
        st.subheader("🛠️ Cache Management")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear Cache", help="Remove all cached entries"):
                clear_cache()
                st.success("Cache cleared successfully!")
                st.rerun()

        with col2:
            if st.button("📊 Refresh Stats", help="Update cache statistics"):
                st.rerun()

    @staticmethod
    def display_cache_settings() -> None:
        """Display cache configuration settings."""
        st.subheader("⚙️ Cache Settings")

        with st.expander("Advanced Cache Configuration"):
            col1, col2 = st.columns(2)

            with col1:
                default_ttl = st.number_input(
                    "Default TTL (seconds)",
                    min_value=60,
                    max_value=86400,  # 24 hours
                    value=3600,  # 1 hour
                    help="Default time-to-live for cache entries",
                )

                max_entries = st.number_input(
                    "Max Cache Entries",
                    min_value=100,
                    max_value=10000,
                    value=1000,
                    help="Maximum number of cache entries",
                )

            with col2:
                enable_cache = st.checkbox(
                    "Enable Caching",
                    value=True,
                    help="Enable/disable the caching system",
                )

                cache_dir = st.text_input(
                    "Cache Directory", value="cache", help="Directory for cache files"
                )

            if st.button("Apply Settings"):
                configure_cache(
                    cache_dir=cache_dir,
                    default_ttl=default_ttl,
                    max_cache_size=max_entries,
                    enable_cache=enable_cache,
                )
                st.success("Cache settings applied!")

    @staticmethod
    def display_cache_info() -> None:
        """Display information about caching benefits."""
        st.subheader("i️ Cache Information")

        st.info("""
        **Caching Benefits:**
        - ⚡ Faster response times for repeated requests
        - 💰 Reduced API costs by avoiding duplicate calls
        - 🔄 Better reliability during high usage
        - 📊 Consistent results for identical inputs

        **Cached Operations:**
        - Definition generation (1 hour TTL)
        - Example generation (30 minutes TTL)
        - Synonym/antonym generation (2 hours TTL)
        - GPT prompt responses (1 hour TTL)
        """)

    @staticmethod
    def render_cache_dashboard() -> None:
        """Render complete cache management dashboard."""
        st.title("🗄️ Cache Management Dashboard")

        # Display cache statistics
        CacheManager.display_cache_stats()

        st.divider()

        # Display cache controls
        CacheManager.display_cache_controls()

        st.divider()

        # Display cache settings
        CacheManager.display_cache_settings()

        st.divider()

        # Display cache information
        CacheManager.display_cache_info()


def render_cache_sidebar() -> None:
    """Render cache information in sidebar."""
    with st.sidebar, st.expander("📊 Cache Status"):
        stats = get_cache_stats()
        st.write(f"**Entries:** {stats['entries']}")
        st.write(f"**Size:** {stats['total_size_mb']:.1f} MB")

        if st.button("Clear Cache", key="sidebar_clear_cache"):
            clear_cache()
            st.success("Cache cleared!")
            st.rerun()
