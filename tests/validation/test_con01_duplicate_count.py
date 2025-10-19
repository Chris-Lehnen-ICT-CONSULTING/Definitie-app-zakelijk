import types

import pytest


def _make_validator(monkeypatch, count_return: int):
    # Lazy import module
    import toetsregels.validators.CON_01 as con01_mod

    # Fake repo with desired count
    class FakeRepo:
        def count_exact_by_context(
            self,
            *,
            begrip,
            organisatorische_context,
            juridische_context="",
            wettelijke_basis=None,
        ) -> int:
            return count_return

    # Patch repository class in module
    monkeypatch.setattr(con01_mod, "DefinitieRepository", FakeRepo)

    # Build validator
    return con01_mod.create_validator()


def test_con01_fails_when_multiple_definitions_same_context(monkeypatch):
    validator = _make_validator(monkeypatch, count_return=2)

    definitie = "Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem."
    begrip = "Registratie"
    context = {
        "organisatorische_context": ["OM"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": ["Art. 27 Sv"],
    }

    ok, msg, score = validator.validate(definitie, begrip, context)
    assert ok is False
    assert "meerdere definities" in msg


def test_con01_passes_with_single_definition(monkeypatch):
    validator = _make_validator(monkeypatch, count_return=1)

    definitie = "Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem."
    begrip = "Registratie"
    context = {
        "organisatorische_context": ["DJI"],
        "juridische_context": ["Bestuursrecht"],
        "wettelijke_basis": ["Art. 3:2 Awb"],
    }

    ok, msg, score = validator.validate(definitie, begrip, context)
    assert ok is True
    # Score may vary by other checks; we only assert success here
