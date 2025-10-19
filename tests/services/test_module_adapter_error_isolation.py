import pytest


class _BoomRule:
    code = "TST_999"

    def validate(self, ctx):  # sync rule that raises
        msg = "boom"
        raise RuntimeError(msg)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_module_adapter_catches_rule_exceptions_and_marks_errored():
    m = pytest.importorskip(
        "services.validation.module_adapter",
        reason="ValidationModuleAdapter not implemented yet",
    )
    t = pytest.importorskip(
        "services.validation.types_internal",
        reason="types_internal not implemented yet",
    )

    adapter = m.ValidationModuleAdapter()

    # Minimal EvaluationContext stub is acceptable for this test
    ctx = getattr(t, "EvaluationContext", None)
    if ctx is None:

        class DummyCtx:  # fallback if context type is not provided yet
            pass

        eval_ctx = DummyCtx()
    else:
        # Construct with minimal arguments if dataclass exists
        try:
            eval_ctx = ctx(raw_text="x", cleaned_text="x")  # type: ignore[call-arg]
        except TypeError:
            eval_ctx = ctx  # fallback to passing the type if it acts as a namespace

    rr = await adapter.evaluate(_BoomRule(), eval_ctx)

    assert hasattr(rr, "errored") or isinstance(rr, dict)
    # Accept either dataclass-like or dict-like result shapes
    if isinstance(rr, dict):
        assert rr.get("rule_code") == "TST_999"
        assert rr.get("errored") is True
        assert rr.get("violations") == []
    else:
        assert rr.rule_code == "TST_999"
        assert rr.errored is True
        assert rr.violations == []
