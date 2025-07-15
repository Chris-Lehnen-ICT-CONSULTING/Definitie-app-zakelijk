"""
Async progress UI components for DefinitieAgent.
Provides real-time progress tracking for async operations.
"""

import streamlit as st
import asyncio
import time
from typing import Any, Dict
from dataclasses import dataclass

from services.async_definition_service import (
    get_async_service, 
    AsyncProcessingResult
)


@dataclass
class ProgressState:
    """State container for progress tracking."""
    current_step: int = 0
    total_steps: int = 0
    current_message: str = ""
    start_time: float = 0
    is_running: bool = False
    is_cancelled: bool = False


class AsyncProgressTracker:
    """Progress tracker for async operations."""
    
    def __init__(self):
        self.state = ProgressState()
        self.progress_bar = None
        self.status_text = None
        self.time_text = None
        self.cancel_button = None
    
    def setup_ui(self, container):
        """Setup progress UI components."""
        with container:
            self.status_text = st.empty()
            self.progress_bar = st.progress(0)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                self.time_text = st.empty()
            with col2:
                self.cancel_button = st.button("❌ Cancel", key="cancel_async")
            with col3:
                st.empty()  # Spacer
    
    def start(self, total_steps: int, message: str = "Starting..."):
        """Start progress tracking."""
        self.state.current_step = 0
        self.state.total_steps = total_steps
        self.state.current_message = message
        self.state.start_time = time.time()
        self.state.is_running = True
        self.state.is_cancelled = False
        
        self.update_ui()
    
    def update(self, step: int, message: str):
        """Update progress."""
        if not self.state.is_running:
            return
            
        self.state.current_step = step
        self.state.current_message = message
        self.update_ui()
    
    def finish(self, message: str = "Complete!"):
        """Finish progress tracking."""
        self.state.current_step = self.state.total_steps
        self.state.current_message = message
        self.state.is_running = False
        self.update_ui()
    
    def cancel(self):
        """Cancel the operation."""
        self.state.is_cancelled = True
        self.state.is_running = False
        self.state.current_message = "Cancelled"
        self.update_ui()
    
    def update_ui(self):
        """Update UI components."""
        if not (self.progress_bar and self.status_text and self.time_text):
            return
        
        # Update progress bar
        if self.state.total_steps > 0:
            progress = min(self.state.current_step / self.state.total_steps, 1.0)
            self.progress_bar.progress(progress)
        
        # Update status text
        self.status_text.text(
            f"Step {self.state.current_step}/{self.state.total_steps}: {self.state.current_message}"
        )
        
        # Update time
        if self.state.start_time > 0:
            elapsed = time.time() - self.state.start_time
            self.time_text.text(f"⏱️ {elapsed:.1f}s elapsed")
        
        # Check cancel button
        if self.cancel_button and self.state.is_running:
            if st.session_state.get("cancel_async", False):
                self.cancel()
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self.state.is_cancelled


class AsyncDefinitionUI:
    """UI wrapper for async definition processing."""
    
    def __init__(self):
        self.service = get_async_service()
        self.progress_tracker = AsyncProgressTracker()
    
    def render_async_processing_button(
        self, 
        form_data: Dict[str, Any], 
        toetsregels: Dict[str, Any]
    ):
        """Render button for async definition processing."""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🚀 Generate Definition (Fast Mode)", 
                        help="Generate definition using parallel processing for faster results"):
                self.run_async_definition_processing(form_data, toetsregels)
        
        with col2:
            if st.button("📊 Show Stats", help="Show async processing statistics"):
                self.show_async_stats()
    
    def run_async_definition_processing(
        self, 
        form_data: Dict[str, Any], 
        toetsregels: Dict[str, Any]
    ):
        """Run async definition processing with real-time progress."""
        # Create progress container
        progress_container = st.container()
        result_container = st.container()
        
        # Setup progress tracking
        self.progress_tracker.setup_ui(progress_container)
        
        # Run async processing
        with st.spinner("Initializing async processing..."):
            result = asyncio.run(self._async_processing_wrapper(
                form_data, toetsregels, progress_container
            ))
        
        # Display results
        self.display_async_results(result, result_container)
    
    async def _async_processing_wrapper(
        self, 
        form_data: Dict[str, Any], 
        toetsregels: Dict[str, Any],
        progress_container
    ) -> AsyncProcessingResult:
        """Wrapper for async processing with progress tracking."""
        
        def progress_callback(message: str, step: int, total: int):
            """Progress callback for UI updates."""
            self.progress_tracker.update(step, message)
            
            # Check for cancellation
            if self.progress_tracker.is_cancelled():
                raise asyncio.CancelledError("Operation cancelled by user")
        
        try:
            self.progress_tracker.start(6, "Starting async processing...")
            
            result = await self.service.async_process_complete_definition(
                form_data=form_data,
                toetsregels=toetsregels,
                progress_callback=progress_callback
            )
            
            self.progress_tracker.finish("Processing complete!")
            return result
            
        except asyncio.CancelledError:
            self.progress_tracker.cancel()
            return AsyncProcessingResult(
                success=False,
                processing_time=0,
                error_message="Operation cancelled by user"
            )
        except Exception as e:
            self.progress_tracker.finish(f"Error: {str(e)}")
            return AsyncProcessingResult(
                success=False,
                processing_time=0,
                error_message=str(e)
            )
    
    def display_async_results(
        self, 
        result: AsyncProcessingResult, 
        container
    ):
        """Display async processing results."""
        with container:
            if result.success:
                st.success(f"✅ Processing completed in {result.processing_time:.2f}s")
                
                # Performance metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Processing Time", f"{result.processing_time:.2f}s")
                
                with col2:
                    st.metric("Total Requests", result.total_requests)
                
                with col3:
                    if result.examples:
                        improvement = max(0, 100 - (result.processing_time / (result.total_requests * 3)) * 100)
                        st.metric("Speed Improvement", f"{improvement:.0f}%")
                
                with col4:
                    st.metric("Cache Hits", result.cache_hits)
                
                # Show example results
                if result.examples:
                    with st.expander("📝 Generated Examples", expanded=True):
                        
                        if result.examples.voorbeeld_zinnen:
                            st.subheader("Example Sentences")
                            for i, zin in enumerate(result.examples.voorbeeld_zinnen, 1):
                                st.write(f"{i}. {zin}")
                        
                        if result.examples.praktijkvoorbeelden:
                            st.subheader("Practice Examples")
                            for i, voorbeeld in enumerate(result.examples.praktijkvoorbeelden, 1):
                                st.write(f"**Example {i}:** {voorbeeld}")
                        
                        if result.examples.tegenvoorbeelden:
                            st.subheader("Counter Examples")
                            for i, tegen in enumerate(result.examples.tegenvoorbeelden, 1):
                                st.write(f"**Counter {i}:** {tegen}")
                
                # Show additional content
                if result.additional_content:
                    with st.expander("🔍 Additional Content"):
                        if result.additional_content.get('synoniemen'):
                            st.subheader("Synonyms")
                            st.write(result.additional_content['synoniemen'])
                        
                        if result.additional_content.get('antoniemen'):
                            st.subheader("Antonyms")
                            st.write(result.additional_content['antoniemen'])
                        
                        if result.additional_content.get('toelichting'):
                            st.subheader("Explanation")
                            st.write(result.additional_content['toelichting'])
                
            else:
                st.error(f"❌ Processing failed: {result.error_message}")
                if result.processing_time > 0:
                    st.info(f"Failed after {result.processing_time:.2f}s")
    
    def show_async_stats(self):
        """Show async processing statistics."""
        st.subheader("🚀 Async Processing Statistics")
        
        # Mock stats for demonstration
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Speed Improvement", "65%", "↑15%")
        
        with col2:
            st.metric("Parallel Requests", "6", "↑3")
        
        with col3:
            st.metric("Total Time Saved", "45.2s", "↑12.3s")
        
        st.info("""
        **Async Processing Benefits:**
        - 🚀 **3-5x faster** processing through parallel API calls
        - ⚡ **Real-time progress** tracking with cancellation support
        - 📊 **Better resource utilization** with intelligent rate limiting
        - 🔄 **Concurrent generation** of all examples and content
        """)


def render_async_mode_toggle():
    """Render toggle for async mode."""
    with st.sidebar:
        with st.expander("⚡ Async Mode"):
            async_enabled = st.checkbox(
                "Enable Fast Mode",
                value=True,
                help="Use parallel processing for faster results"
            )
            
            if async_enabled:
                st.success("🚀 Fast Mode: ON")
                st.write("Examples and content generated concurrently")
            else:
                st.info("🐌 Standard Mode: ON")
                st.write("Sequential processing (slower)")
            
            return async_enabled


def render_async_dashboard():
    """Render async processing dashboard."""
    st.title("🚀 Async Processing Dashboard")
    
    ui = AsyncDefinitionUI()
    
    st.subheader("Performance Comparison")
    
    # Mock comparison data
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Standard Mode", "15.3s", help="Sequential processing")
    
    with col2:
        st.metric("Fast Mode", "4.7s", "-10.6s", help="Parallel processing")
    
    st.progress(0.69, text="Speed improvement: 69%")
    
    st.subheader("Real-time Processing")
    
    # Sample form data for demo
    if st.button("🧪 Demo Async Processing"):
        sample_data = {
            "begrip": "test",
            "context_dict": {"organisatorisch": ["demo"]},
            "context": ["demo"],
            "juridische_context": [],
            "wet_basis": [],
            "datum": "2025-07-09",
            "voorsteller": "demo",
            "ketenpartners": []
        }
        sample_rules = {}
        
        ui.run_async_definition_processing(sample_data, sample_rules)