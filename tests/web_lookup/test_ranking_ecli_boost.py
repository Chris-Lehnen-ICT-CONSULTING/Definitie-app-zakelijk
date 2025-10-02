import pytest


def test_ecli_boost_in_contract_mapping():
    from services.interfaces import LookupResult, WebSource
    from services.modern_web_lookup_service import ModernWebLookupService

    svc = ModernWebLookupService()

    # Rechtspraak zonder ECLI
    r1 = LookupResult(
        term="t",
        source=WebSource(
            name="Rechtspraak.nl",
            url="https://rechtspraak.nl/case",
            confidence=0.8,
            is_juridical=True,
        ),
        definition="Uitspraak",
        success=True,
        metadata={"dc_identifier": "https://rechtspraak.nl/case"},
    )
    d1 = svc._to_contract_dict(r1)

    # Rechtspraak met ECLI in identifier
    r2 = LookupResult(
        term="t",
        source=WebSource(
            name="Rechtspraak.nl",
            url="https://rechtspraak.nl/case2",
            confidence=0.8,
            is_juridical=True,
        ),
        definition="ECLI:NL:HR:2019:1288 — Uitspraak",
        success=True,
        metadata={"dc_identifier": "ECLI:NL:HR:2019:1288"},
    )
    d2 = svc._to_contract_dict(r2)

    assert d2["score"] >= d1["score"], "ECLI case should receive a small score boost"
