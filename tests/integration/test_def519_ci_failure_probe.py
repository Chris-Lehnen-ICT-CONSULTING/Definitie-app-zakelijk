"""DEF-519: opzettelijk falende CI-bewijsprobe.

Dit bestand is UITSLUITEND bewijsmateriaal: het bewijst dat de verplichte
integration-tests-job in CI daadwerkelijk rood wordt op een falende test.
De test faalt onvoorwaardelijk en er hoort geen productie-implementatie of
GREEN-fix bij.

NOOIT MERGEN naar de productbranch. Dit bestand blijft alleen in de aparte
bewijsbranch codex/DEF-519-ci-failure-proof bestaan.
"""

import pytest

pytestmark = [pytest.mark.integration]


def test_def519_ci_failure_probe_faalt_onvoorwaardelijk() -> None:
    """Faalt altijd, zodat de CI-integrationgate aantoonbaar rood wordt."""
    raise AssertionError("DEF519_EXPECTED_CI_FAILURE_PROOF")
