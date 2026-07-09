"""Unit-tests voor de PII-redactie-wiring (DEF-486).

Deze tests borgen dat het `PIIRedactingFilter` op HANDLER-niveau records van
child-loggers redigeert — de situatie die main.py in productie nodig heeft.
Bewust `unit`-gemarkeerd zodat ze in `make test` en de coverage-ratchet draaien
(de zusterfile onder tests/integration/ viel buiten die gate).

Pure in-memory logging-tests, geen I/O. Elke test gebruikt een unieke
loggernaam (uuid) zodat er geen residual state uit de globale logging-registry
naar een volgende test lekt.
"""

import logging
import uuid

import pytest

from utils.logging_filters import PIIRedactingFilter, install_pii_redaction_filter

pytestmark = [pytest.mark.unit]

TOKEN = "sk-ABCDEFGHIJKLmnopQRSTuvwx1234567890"
EMAIL_MSG = "contact=user@example.com"


def _unique(suffix: str) -> str:
    return f"test.def486.{uuid.uuid4().hex}.{suffix}"


def _capture(logger: logging.Logger):
    """Voeg een in-memory handler toe die geformatteerde records verzamelt."""
    stream: list[str] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            stream.append(self.format(record))

    handler = ListHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return stream, handler


def test_ancestor_logger_filter_does_not_reach_child_records():
    """Documenteert waarom de fix nodig is: een filter op de ancestor-LOGGER
    wordt niet toegepast op records die van child-loggers propageren."""
    parent = logging.getLogger(_unique("broken"))
    parent.setLevel(logging.INFO)
    parent.addFilter(PIIRedactingFilter())  # fout: op de logger (oud main.py-gedrag)
    stream, handler = _capture(parent)
    child = logging.getLogger(f"{parent.name}.child")
    child.setLevel(logging.INFO)
    try:
        child.info("token=%s", TOKEN)
        assert stream
        assert TOKEN in stream[-1]  # lekt: ancestor-filter wordt overgeslagen
    finally:
        for f in list(parent.filters):
            parent.removeFilter(f)
        parent.removeHandler(handler)


def test_install_redacts_child_logger_records():
    """Kern-regressietest: na install op de handlers wordt een token uit een
    child-logger-record wél gemaskeerd."""
    parent = logging.getLogger(_unique("fixed"))
    parent.setLevel(logging.INFO)
    stream, handler = _capture(parent)
    install_pii_redaction_filter(parent)
    child = logging.getLogger(f"{parent.name}.child")
    child.setLevel(logging.INFO)
    try:
        child.info("token=%s", TOKEN)
        assert stream
        msg = stream[-1]
        assert TOKEN not in msg, f"token lekte: {msg}"
        assert "***" in msg or "[REDACTED]" in msg
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_install_redacts_grandchild_records():
    """Meerlaagse propagatie (grandchild → parent-handler) wordt ook gedekt."""
    parent = logging.getLogger(_unique("multi"))
    parent.setLevel(logging.INFO)
    stream, handler = _capture(parent)
    install_pii_redaction_filter(parent)
    grandchild = logging.getLogger(f"{parent.name}.child.grandchild")
    grandchild.setLevel(logging.INFO)
    try:
        grandchild.info("token=%s", TOKEN)
        assert stream
        assert TOKEN not in stream[-1]
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_install_redacts_email_via_child_path():
    """Niet alleen sk-tokens: ook e-mail wordt via het handler-pad geredigeerd."""
    parent = logging.getLogger(_unique("email"))
    parent.setLevel(logging.INFO)
    stream, handler = _capture(parent)
    install_pii_redaction_filter(parent)
    child = logging.getLogger(f"{parent.name}.child")
    child.setLevel(logging.INFO)
    try:
        child.info(EMAIL_MSG)
        assert stream
        msg = stream[-1]
        assert "user@example.com" not in msg
        assert "[REDACTED]" in msg
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_non_propagating_child_is_a_known_gap():
    """Documenteert de bekende beperking (getrackt): een child-logger met
    `propagate=False` en een eigen handler bereikt de parent-handler niet, dus
    de root-handler-redactie geldt niet. Zie DEF-490."""
    parent = logging.getLogger(_unique("noprop"))
    parent.setLevel(logging.INFO)
    _parent_stream, parent_handler = _capture(parent)
    install_pii_redaction_filter(parent)

    child = logging.getLogger(f"{parent.name}.child")
    child.setLevel(logging.INFO)
    child.propagate = False
    own_stream, own_handler = _capture(child)  # eigen handler zónder filter
    try:
        child.info("token=%s", TOKEN)
        # Beperking: eigen handler van een non-propagerende logger is niet gedekt.
        assert own_stream and TOKEN in own_stream[-1]
    finally:
        child.propagate = True
        for f in list(own_handler.filters):
            own_handler.removeFilter(f)
        child.removeHandler(own_handler)
        for f in list(parent_handler.filters):
            parent_handler.removeFilter(f)
        parent.removeHandler(parent_handler)


def test_install_is_idempotent_count_and_behaviour():
    """Dubbel installeren stapelt geen filters (count) én verandert de output
    niet (gedrag: exact één keer geredigeerd)."""
    parent = logging.getLogger(_unique("idem"))
    parent.setLevel(logging.INFO)
    stream, handler = _capture(parent)
    install_pii_redaction_filter(parent)
    install_pii_redaction_filter(parent)
    child = logging.getLogger(f"{parent.name}.child")
    child.setLevel(logging.INFO)
    try:
        pii_filters = [f for f in handler.filters if isinstance(f, PIIRedactingFilter)]
        assert len(pii_filters) == 1  # geen stapeling

        child.info("token=%s", TOKEN)
        msg = stream[-1]
        assert TOKEN not in msg
        assert msg.count("[REDACTED]") <= 1  # geen dubbel-masking-corruptie
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_install_redacts_pii_in_positional_arg():
    """DEF-571: PII die als %s-argument wordt meegegeven (zoals de gelogde
    synoniem-term in SynonymSuggester) wordt via het handler-pad geredigeerd."""
    parent = logging.getLogger(_unique("arg"))
    parent.setLevel(logging.WARNING)
    stream, handler = _capture(parent)
    install_pii_redaction_filter(parent)
    child = logging.getLogger(f"{parent.name}.child")
    child.setLevel(logging.WARNING)
    try:
        # term-arg bevat een e-mailadres (PII); moet geredigeerd worden.
        child.warning("AI-call mislukt voor '%s': %s", "user@example.com", "boom")
        assert stream
        msg = stream[-1]
        assert "user@example.com" not in msg
        assert "[REDACTED]" in msg
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_redacts_exception_object_passed_as_arg():
    """DEF-571/DEF-575: een Exception als %s-arg is geen str en ontsnapte aan
    `_redact_args` — terwijl `logger.error("... %s", exc)` een veelgebruikt
    patroon is (o.a. synonym_suggester.py)."""
    parent = logging.getLogger(_unique("excarg"))
    parent.setLevel(logging.ERROR)
    stream, handler = _capture(parent)
    handler.setLevel(logging.ERROR)
    install_pii_redaction_filter(parent)
    try:
        fout = ValueError("contact user@example.com voor details")
        parent.error("mislukt: %s", fout)
        assert stream
        assert "user@example.com" not in stream[-1]
        assert "[REDACTED]" in stream[-1]
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_redacts_pii_in_exception_traceback():
    """DEF-575: de formatter rendert de traceback ná de filter, dus PII in een
    exception-message ontsnapte aan de redactie."""
    parent = logging.getLogger(_unique("exctb"))
    parent.setLevel(logging.ERROR)
    stream, handler = _capture(parent)
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter("%(message)s"))
    install_pii_redaction_filter(parent)
    try:
        try:
            raise ValueError("contact user@example.com voor details")
        except ValueError:
            parent.error("registry query gefaald", exc_info=True)
        assert stream
        assert "Traceback" in stream[-1], "traceback ontbreekt in de output"
        assert "user@example.com" not in stream[-1]
        assert "[REDACTED]" in stream[-1]
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_numerieke_args_blijven_intact():
    """Regressie: de arg-redactie mag %d-formatting niet slopen."""
    parent = logging.getLogger(_unique("num"))
    parent.setLevel(logging.INFO)
    stream, handler = _capture(parent)
    install_pii_redaction_filter(parent)
    try:
        parent.info("gevonden: %d van %d", 3, 10)
        assert stream[-1] == "gevonden: 3 van 10"
    finally:
        for f in list(handler.filters):
            handler.removeFilter(f)
        parent.removeHandler(handler)


def test_install_on_logger_without_handlers_is_noop():
    """Zonder handlers is install een veilige no-op (geen crash)."""
    logger = logging.getLogger(_unique("empty"))
    # geen handlers
    install_pii_redaction_filter(logger)  # mag niet crashen
    assert not logger.handlers
