"""De dedicated enrichment-logger moet PII redigeren (DEF-571, review PR #372).

`synonym_enrichment` heeft `propagate = False` en eigen handlers. Een filter op
de root-handlers bereikt hem dus nooit — terwijl juist deze logger de term bij
elke definitiegeneratie wegschrijft naar logs/synonym_enrichment.log.
"""

import logging

import pytest

pytestmark = pytest.mark.unit

from utils.logging_filters import PIIRedactingFilter


def test_enrichment_logger_heeft_pii_filter_op_elke_handler():
    import services.synonym_orchestrator as so

    assert so.enrichment_logger.handlers, "logger heeft geen handlers"
    for handler in so.enrichment_logger.handlers:
        assert any(isinstance(f, PIIRedactingFilter) for f in handler.filters), (
            f"handler {type(handler).__name__} van de enrichment-logger mist de "
            "PII-redactie; propagate=False dus de root-filter dekt hem niet"
        )


def test_enrichment_logger_propageert_niet_naar_root():
    # Vangnet: als dit ooit True wordt, dekt de root-filter hem alsnog en is de
    # bovenstaande test niet langer de enige bescherming.
    import services.synonym_orchestrator as so

    assert so.enrichment_logger.propagate is False


def test_enrichment_logger_redigeert_email_in_term():
    """Het echte scenario: een term met een e-mailadres mag niet ongeredigeerd
    door de bestaande handlers van de enrichment-logger heen komen.

    Deze test legt zelf GEEN filter aan — dat zou de productie-wiring maskeren
    en de andere tests order-afhankelijk maken. Hij hangt alleen een capture op
    de eerste productie-handler, die zijn eigen PII-filter hoort te hebben.
    """
    import services.synonym_orchestrator as so

    productie_handler = so.enrichment_logger.handlers[0]
    opgevangen: list[logging.LogRecord] = []

    class _Spion(logging.Filter):
        """Draait ná de PII-filter op dezelfde handler en ziet dus het
        geredigeerde record."""

        def filter(self, record: logging.LogRecord) -> bool:
            opgevangen.append(record)
            return False  # niet daadwerkelijk naar het logbestand schrijven

    spion = _Spion()
    productie_handler.addFilter(spion)
    try:
        term = "jan.jansen@gemeente.nl valt onder art. 27 Sv"
        so.enrichment_logger.info("Starting AI-enrichment for '%s'", term)
        assert opgevangen, "er is niets gelogd"
        tekst = opgevangen[-1].getMessage()
        assert "jan.jansen@gemeente.nl" not in tekst
        assert "[REDACTED]" in tekst
    finally:
        productie_handler.removeFilter(spion)
