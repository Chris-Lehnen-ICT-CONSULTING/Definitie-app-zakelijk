import importlib
import inspect
from collections.abc import Callable
from pathlib import Path

import pytest

VALIDATORS_DIR = Path("src/toetsregels/validators")


def _iter_validator_classes(module):
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if name.endswith("Validator") and obj.__module__ == module.__name__:
            yield obj


@pytest.mark.parametrize(
    "module_path",
    sorted(p for p in VALIDATORS_DIR.glob("*.py") if p.name != "__init__.py"),
)
def test_validator_modules_expose_validate(module_path):
    # Import module by dotted path
    dotted = f"toetsregels.validators.{module_path.stem}"
    mod = importlib.import_module(dotted)

    # At least one class *Validator
    classes = list(_iter_validator_classes(mod))
    assert classes, f"No Validator class found in {dotted}"

    # Each validator can be instantiated with minimal config and has validate()
    for cls in classes:
        # Require __init__(config: dict)
        sig = inspect.signature(cls)
        params = list(sig.parameters.values())
        assert params and params[0].name in {
            "config",
            "cfg",
        }, f"{cls.__name__} should accept config dict"

        inst = cls({})
        assert hasattr(inst, "validate"), f"{cls.__name__} has no validate()"
        # Call with minimal inputs
        ok, msg, score = inst.validate("korte definitie", "begrip", context={})
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
