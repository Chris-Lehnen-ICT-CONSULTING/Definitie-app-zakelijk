"""Tests voor TokenCounter."""

from services.rag.token_counter import tel_tokens


class TestTelTokens:
    def test_empty_string(self):
        assert tel_tokens("") == 0

    def test_simple_text(self):
        count = tel_tokens("Hallo wereld")
        assert count > 0
        assert isinstance(count, int)

    def test_artikel_tekst(self):
        tekst = "Artikel 1. In deze wet wordt verstaan onder basisregistratie."
        count = tel_tokens(tekst)
        # Typical Dutch legal sentence: 10-15 tokens
        assert 5 < count < 30

    def test_deterministic(self):
        tekst = "De burgemeester is verantwoordelijk."
        assert tel_tokens(tekst) == tel_tokens(tekst)

    def test_long_text(self):
        tekst = "woord " * 1000
        count = tel_tokens(tekst)
        assert count > 100
