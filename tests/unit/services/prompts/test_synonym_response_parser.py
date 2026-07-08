import pytest

pytestmark = pytest.mark.unit

from services.gpt4_synonym_suggester import SynonymSuggestion
from services.prompts.synonym_response_parser import parse_synonym_response


def test_parse_geldige_json():
    raw = (
        '{"synoniemen": ['
        '{"synoniem": "beklaagde", "confidence": 0.9, "rationale": "strafproces"},'
        '{"synoniem": "gedaagde", "confidence": 0.6, "rationale": "civiel"}'
        "]}"
    )
    result = parse_synonym_response(raw)
    assert len(result) == 2
    assert all(isinstance(s, SynonymSuggestion) for s in result)
    assert result[0].synoniem == "beklaagde"


def test_parse_json_in_markdown_fence():
    raw = '```json\n{"synoniemen": [{"synoniem": "x", "confidence": 0.5, "rationale": "y"}]}\n```'
    assert len(parse_synonym_response(raw)) == 1


def test_parse_confidence_buiten_bereik_wordt_geclampt():
    raw = '{"synoniemen": [{"synoniem": "x", "confidence": 1.7, "rationale": "y"}]}'
    result = parse_synonym_response(raw)
    assert result[0].confidence == 1.0


def test_parse_confidence_negatief_wordt_geclampt():
    raw = '{"synoniemen": [{"synoniem": "x", "confidence": -0.4, "rationale": "y"}]}'
    result = parse_synonym_response(raw)
    assert result[0].confidence == 0.0


def test_parse_confidence_niet_numeriek_valt_terug():
    raw = '{"synoniemen": [{"synoniem": "x", "confidence": "hoog", "rationale": "y"}]}'
    result = parse_synonym_response(raw)
    assert result[0].confidence == 0.5  # expliciete fallback-waarde


def test_parse_slaat_ongeldige_items_over():
    raw = (
        '{"synoniemen": ['
        '{"synoniem": "", "confidence": 0.9, "rationale": "leeg"},'
        '{"confidence": 0.9, "rationale": "geen synoniem-key"},'
        '{"synoniem": "geldig", "confidence": 0.8, "rationale": "ok"}'
        "]}"
    )
    result = parse_synonym_response(raw)
    assert len(result) == 1
    assert result[0].synoniem == "geldig"


def test_parse_ontbrekende_rationale_wordt_lege_string():
    raw = '{"synoniemen": [{"synoniem": "x", "confidence": 0.8}]}'
    result = parse_synonym_response(raw)
    assert result[0].rationale == ""


def test_parse_natekst_met_accolades_behoudt_data():
    # LLM-output met trailing prose die zelf accolades bevat (bv. {term}-placeholder).
    # Een greedy \{.*\}-regex zou hier de hele data verliezen.
    raw = (
        '{"synoniemen": [{"synoniem": "beklaagde", "confidence": 0.9, "rationale": "y"}]}'
        "\n\nLet op: gebruik de placeholder {term} in je zoekopdracht."
    )
    result = parse_synonym_response(raw)
    assert len(result) == 1
    assert result[0].synoniem == "beklaagde"


def test_parse_meerdere_objecten_kiest_synoniemen_object():
    # Als er twee JSON-objecten in de output staan, moet die met 'synoniemen' gekozen worden.
    raw = (
        'Voorbeeld: {"foo": 1}. '
        'Antwoord: {"synoniemen": [{"synoniem": "gedaagde", "confidence": 0.7, "rationale": "z"}]}'
    )
    result = parse_synonym_response(raw)
    assert len(result) == 1
    assert result[0].synoniem == "gedaagde"


def test_parse_geneste_accolades_in_geldig_object():
    raw = '{"synoniemen": [{"synoniem": "x", "confidence": 0.8, "rationale": "zie {bron}"}]}'
    result = parse_synonym_response(raw)
    assert len(result) == 1
    assert result[0].rationale == "zie {bron}"


def test_parse_kapotte_json_geeft_lege_lijst():
    assert parse_synonym_response("dit is geen json {{{") == []


def test_parse_synoniemen_geen_lijst_geeft_lege_lijst():
    assert parse_synonym_response('{"synoniemen": "geen lijst"}') == []


def test_parse_lege_of_none_input():
    assert parse_synonym_response("") == []
    assert parse_synonym_response(None) == []
