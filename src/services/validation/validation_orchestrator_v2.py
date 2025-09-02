"""Compatibility shim for test import path.

Re-exports ValidationOrchestratorV2 from the orchestrators package so that
tests importing `services.validation.validation_orchestrator_v2` keep working.
"""

from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2

__all__ = ["ValidationOrchestratorV2"]
