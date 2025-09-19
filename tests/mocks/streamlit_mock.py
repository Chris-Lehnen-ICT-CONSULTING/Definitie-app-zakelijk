"""
Central Streamlit mock for tests with no-op cache decorators.

Provides:
- st.cache_data(...) decorator → passthrough, with .clear() method
- st.cache_resource(...) decorator → passthrough, with .clear() method
- st.session_state dict

This allows importing modules that use Streamlit caching without requiring
the real Streamlit package during tests.
"""

from typing import Any, Callable


class _NoOpDecorator:
    """No-op decorator emulating Streamlit's cache decorators with clear()."""

    def __call__(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return _decorator

    # Some code may call st.cache_data.clear() — keep as harmless no-op
    def clear(self) -> None:  # pragma: no cover - trivial
        return None


class MockStreamlit:
    def __init__(self) -> None:
        class _SessionState(dict):
            def __getattr__(self, name: str) -> Any:
                try:
                    return self[name]
                except KeyError as e:
                    raise AttributeError(name) from e
            def __setattr__(self, name: str, value: Any) -> None:
                # allow normal dict attributes to be set on class, not instance items
                if name in {"__class__", "__dict__", "__weakref__"}:
                    return super().__setattr__(name, value)
                self[name] = value

        self.session_state = _SessionState()
        # Simple message sink used by some UI tests
        self.messages: list[tuple[str, object]] = []
        self.cache_data = _NoOpDecorator()
        self.cache_resource = _NoOpDecorator()
        # Define common UI callables so tests can patch them
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None

        class _Ctx:
            def __enter__(self, *a: Any, **k: Any):
                return self
            def __exit__(self, *a: Any, **k: Any):
                return False
            # Allow common calls inside contexts
            def button(self, *a: Any, **k: Any):
                return False
            def selectbox(self, *a: Any, **k: Any):
                return None
            def write(self, *a: Any, **k: Any):
                return None
            def success(self, *a: Any, **k: Any):
                return None
            def error(self, *a: Any, **k: Any):
                return None
            def warning(self, *a: Any, **k: Any):
                return None

        self.text_input = _noop
        self.text_area = _noop
        self.selectbox = _noop
        self.multiselect = _noop
        self.button = _noop
        self.file_uploader = _noop
        self.set_page_config = _noop
        self.title = _noop
        self.header = _noop
        self.markdown = _noop
        self.metric = _noop
        self.rerun = _noop
        self.json = _noop
        self.line_chart = _noop
        # Capture common UI outputs for assertions in tests
        self.success = lambda msg=None, *a, **k: self.messages.append(("success", msg))
        self.error = lambda msg=None, *a, **k: self.messages.append(("error", msg))
        self.warning = lambda msg=None, *a, **k: self.messages.append(("warning", msg))
        self.info = lambda msg=None, *a, **k: self.messages.append(("info", msg))
        self.write = lambda msg=None, *a, **k: self.messages.append(("write", msg))
        self.expander = lambda *a, **k: _Ctx()
        self.sidebar = _Ctx()
        self.tabs = lambda names: [_Ctx() for _ in (names or [])]
        self.columns = lambda spec: [_Ctx() for _ in range(spec if isinstance(spec, int) else len(spec))]
        self.download_button = _noop


def get_streamlit_mock() -> MockStreamlit:
    """Factory to obtain a fresh MockStreamlit instance."""
    return MockStreamlit()
