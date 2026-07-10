"""De dedicated enrichment-logger moet PII redigeren (DEF-571, review PR #372).

`synonym_enrichment` heeft `propagate = False` en eigen handlers. Een filter op
de root-handlers bereikt hem dus nooit — terwijl juist deze logger de term bij
elke definitiegeneratie wegschrijft naar logs/synonym_enrichment.log.

De tests hieronder zetten de logger hermetisch opnieuw op. Een eerdere versie
itereerde over `enrichment_logger.handlers` zoals die op dat moment waren, en
brak in CI zodra pytest er een `LogCaptureHandler` bij had gezet: die heeft
uiteraard geen PII-filter. Dat is een test die de omgeving *aanneemt* in plaats
van hem af te dwingen — precies wat we hier willen toetsen.
"""

import logging

import pytest

pytestmark = pytest.mark.unit

from utils.logging_filters import PIIRedactingFilter


@pytest.fixture
def verse_enrichment_logger():
    """Draai `_setup_enrichment_logger()` opnieuw op een lege handlerlijst.

    Zo toetsen we uitsluitend de handlers die de productiecode zélf aanmaakt,
    niet wat pytest of een eerdere test erbij hing.
    """
    import services.synonym_orchestrator as so

    logger = so.enrichment_logger
    originele_handlers = list(logger.handlers)
    originele_propagate = logger.propagate

    logger.handlers = []
    so._setup_enrichment_logger()
    try:
        yield logger
    finally:
        for handler in logger.handlers:
            handler.close()
        logger.handlers = originele_handlers
        logger.propagate = originele_propagate


def test_setup_installeert_pii_filter_op_elke_eigen_handler(verse_enrichment_logger):
    assert verse_enrichment_logger.handlers, "setup maakte geen handlers aan"
    for handler in verse_enrichment_logger.handlers:
        assert any(isinstance(f, PIIRedactingFilter) for f in handler.filters), (
            f"handler {type(handler).__name__} van de enrichment-logger mist de "
            "PII-redactie; propagate=False dus de root-filter dekt hem niet"
        )


def test_enrichment_logger_propageert_niet_naar_root(verse_enrichment_logger):
    # Vangnet: als dit ooit True wordt, dekt de root-filter hem alsnog en is de
    # bovenstaande test niet langer de enige bescherming.
    assert verse_enrichment_logger.propagate is False


def test_enrichment_logger_redigeert_email_in_term(verse_enrichment_logger):
    """Het echte scenario: een term met een e-mailadres mag niet ongeredigeerd
    door de eigen handlers van de enrichment-logger heen komen.

    De test legt zelf GEEN filter aan — dat zou de productie-wiring maskeren.
    Hij hangt een spion ná de PII-filter op een productie-handler en leest het
    record zoals de handler het zou schrijven.
    """
    productie_handler = verse_enrichment_logger.handlers[0]
    opgevangen: list[logging.LogRecord] = []

    class _Spion(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            opgevangen.append(record)
            return False  # niet daadwerkelijk naar het logbestand schrijven

    spion = _Spion()
    productie_handler.addFilter(spion)
    try:
        term = "jan.jansen@gemeente.nl valt onder art. 27 Sv"
        verse_enrichment_logger.info("Starting AI-enrichment for '%s'", term)
        assert opgevangen, "er is niets gelogd"
        tekst = opgevangen[-1].getMessage()
        assert "jan.jansen@gemeente.nl" not in tekst
        assert "[REDACTED]" in tekst
    finally:
        productie_handler.removeFilter(spion)


def test_vreemde_handler_maakt_de_guard_niet_rood(verse_enrichment_logger):
    """Een handler die een testframework toevoegt (pytest's LogCaptureHandler)
    hoort de guard niet te breken — die toetst de productie-wiring.

    Deze test legt vast waaróm de fixture bestaat: zonder hem faalde de suite in
    CI zodra caplog een handler op deze logger zette.
    """
    verse_enrichment_logger.addHandler(logging.NullHandler())
    eigen = [h for h in verse_enrichment_logger.handlers if h.filters]
    assert eigen, "productie-handlers verdwenen"
    assert all(any(isinstance(f, PIIRedactingFilter) for f in h.filters) for h in eigen)
