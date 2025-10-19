"""
NLP Helper functions voor UFO Classification Service.

Deze module bevat hulpfuncties voor natural language processing
specifiek voor Nederlandse juridische teksten.
"""

import re
from functools import lru_cache
from typing import Any

import spacy

# Lazy load Spacy model
_nlp_model = None


def get_nlp_model():
    """Get or load Spacy Dutch model."""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("nl_core_news_sm")
        except OSError:
            # Fallback to basic tokenizer if model not installed
            _nlp_model = spacy.blank("nl")
    return _nlp_model


@lru_cache(maxsize=1000)
def get_pos_tags(text: str) -> list[tuple[str, str]]:
    """Extract POS tags from text.

    Args:
        text: Input text

    Returns:
        List of (word, pos_tag) tuples
    """
    nlp = get_nlp_model()
    doc = nlp(text)

    return [(token.text, token.pos_) for token in doc]


@lru_cache(maxsize=1000)
def get_lemmas(text: str) -> list[str]:
    """Extract lemmas from text.

    Args:
        text: Input text

    Returns:
        List of lemmatized words
    """
    nlp = get_nlp_model()
    doc = nlp(text)

    return [token.lemma_ for token in doc if not token.is_punct]


def extract_noun_phrases(text: str) -> list[str]:
    """Extract noun phrases from text.

    Args:
        text: Input text

    Returns:
        List of noun phrases
    """
    nlp = get_nlp_model()
    doc = nlp(text)

    noun_phrases = []
    for chunk in doc.noun_chunks:
        noun_phrases.append(chunk.text)

    return noun_phrases


def extract_dependencies(text: str) -> list[dict[str, Any]]:
    """Extract dependency relations.

    Args:
        text: Input text

    Returns:
        List of dependency relations
    """
    nlp = get_nlp_model()
    doc = nlp(text)

    dependencies = []
    for token in doc:
        dependencies.append(
            {
                "text": token.text,
                "dep": token.dep_,
                "head": token.head.text,
                "children": [child.text for child in token.children],
            }
        )

    return dependencies


def is_nominalization(word: str) -> bool:
    """Check if word is a nominalization.

    Dutch nominalizations often end in:
    -ing, -atie, -tie, -age, -ment, -heid, -schap

    Args:
        word: Word to check

    Returns:
        True if word appears to be a nominalization
    """
    nominalization_suffixes = [
        "ing",
        "atie",
        "tie",
        "age",
        "ment",
        "heid",
        "schap",
        "teit",
        "sie",
    ]

    word_lower = word.lower()
    return any(word_lower.endswith(suffix) for suffix in nominalization_suffixes)


def extract_temporal_expressions(text: str) -> list[str]:
    """Extract temporal expressions from text.

    Args:
        text: Input text

    Returns:
        List of temporal expressions
    """
    temporal_patterns = [
        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",  # Dates
        r"\b\d{1,2}:\d{2}\b",  # Times
        r"\b(voordat|nadat|tijdens|gedurende|binnen|voor|na|bij|op)\b[^.]*",  # Temporal phrases
        r"\b(termijn|periode|datum|tijd|moment|jaar|maand|week|dag|uur)\b",  # Temporal nouns
        r"\b(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\b",
    ]

    temporal_expressions = []
    for pattern in temporal_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        temporal_expressions.extend([match.group() for match in matches])

    return temporal_expressions


def has_bearer_requirement(text: str) -> bool:
    """Check if text indicates a bearer requirement.

    Args:
        text: Input text

    Returns:
        True if text requires a bearer/carrier
    """
    bearer_indicators = [
        r"\bvan een\b",
        r"\bdoor een\b",
        r"\bbij een\b",
        r"\bvoor een\b",
        r"\bvan de\b",
        r"\bdoor de\b",
        r"\beigenschap van\b",
        r"\bkenmerk van\b",
        r"\battribuut van\b",
        r"\btoestand van\b",
    ]

    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in bearer_indicators)


def extract_participants(text: str) -> list[str]:
    """Extract potential participants from text.

    Args:
        text: Input text

    Returns:
        List of participant mentions
    """
    participant_patterns = [
        r"\b(partijen|deelnemers|betrokkenen|actoren)\b",
        r"\b(tussen\s+\w+\s+en\s+\w+)\b",  # "tussen X en Y"
        r"\b(verdachte|beklaagde|getuige|rechter|officier|advocaat)\b",  # Legal roles
        r"\b(werkgever|werknemer|opdrachtgever|opdrachtnemer)\b",  # Work roles
        r"\b(koper|verkoper|huurder|verhuurder)\b",  # Commerce roles
    ]

    participants = []
    for pattern in participant_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        participants.extend([match.group() for match in matches])

    return list(set(participants))  # Remove duplicates


def calculate_text_complexity(text: str) -> dict[str, float]:
    """Calculate various text complexity metrics.

    Args:
        text: Input text

    Returns:
        Dictionary with complexity metrics
    """
    words = text.split()
    sentences = text.split(".")

    # Basic metrics
    word_count = len(words)
    sentence_count = max(len(sentences), 1)
    avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
    avg_sentence_length = word_count / sentence_count

    # Dutch-specific complexity
    compound_words = sum(1 for word in words if "-" in word or len(word) > 15)

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_word_length": avg_word_length,
        "avg_sentence_length": avg_sentence_length,
        "compound_word_ratio": compound_words / max(word_count, 1),
        "complexity_score": (
            avg_word_length * 0.3
            + avg_sentence_length * 0.3
            + (compound_words / max(word_count, 1)) * 0.4
        ),
    }


# Juridische domein-specifieke functies


def extract_legal_references(text: str) -> list[dict[str, str]]:
    """Extract legal references from text.

    Args:
        text: Input text

    Returns:
        List of legal references with type and text
    """
    references = []

    # Wetboek referenties
    wetboek_pattern = r"\b(BW|Sr|Sv|Rv|Awb)\s*(art\.?|artikel)?\s*\d+[a-z]?"
    for match in re.finditer(wetboek_pattern, text):
        references.append(
            {"type": "wetboek", "text": match.group(), "code": match.group(1)}
        )

    # Jurisprudentie
    ecli_pattern = r"ECLI:[A-Z]{2}:[A-Z]+:\d{4}:[A-Z0-9]+"
    for match in re.finditer(ecli_pattern, text):
        references.append(
            {"type": "jurisprudentie", "text": match.group(), "ecli": match.group()}
        )

    # Kamerstukken
    kamerstuk_pattern = r"Kamerstukken\s+[I]{1,2}\s+\d{4}[–/]\d{4},\s*\d+"
    for match in re.finditer(kamerstuk_pattern, text):
        references.append({"type": "kamerstuk", "text": match.group()})

    return references


def identify_legal_domain(text: str, context: list[str] | None = None) -> str:
    """Identify the legal domain of the text.

    Args:
        text: Input text
        context: Optional juridische context list

    Returns:
        Identified legal domain
    """
    text_lower = text.lower()

    # Domain indicators
    domains = {
        "strafrecht": [
            "verdachte",
            "strafbaar",
            "delict",
            "misdrijf",
            "overtreding",
            "Sr",
            "Sv",
        ],
        "bestuursrecht": ["beschikking", "bezwaar", "beroep", "Awb", "bestuursorgaan"],
        "civielrecht": [
            "overeenkomst",
            "contract",
            "aansprakelijk",
            "schadevergoeding",
            "BW",
        ],
        "arbeidsrecht": [
            "arbeidsovereenkomst",
            "werkgever",
            "werknemer",
            "ontslag",
            "cao",
        ],
        "familierecht": ["huwelijk", "scheiding", "alimentatie", "gezag", "omgang"],
        "belastingrecht": ["belasting", "aangifte", "aanslag", "heffing", "fiscaal"],
    }

    scores = {}
    for domain, indicators in domains.items():
        score = sum(1 for indicator in indicators if indicator in text_lower)
        if context:
            score += sum(1 for ctx in context if domain in ctx.lower())
        scores[domain] = score

    if not scores or max(scores.values()) == 0:
        return "algemeen"

    return max(scores, key=scores.get)


def extract_definition_structure(text: str) -> dict[str, Any]:
    """Extract the structure of a definition.

    Args:
        text: Input text

    Returns:
        Dictionary with structural elements
    """
    structure = {
        "has_genus": False,  # Genus (broader category)
        "has_differentia": False,  # Differentia (distinguishing features)
        "has_examples": False,
        "has_conditions": False,
        "has_exceptions": False,
        "has_enumeration": False,
    }

    # Check for genus-differentia structure
    if re.search(r"\bis een\b|\bbetreft\b|\bwordt verstaan\b", text, re.IGNORECASE):
        structure["has_genus"] = True
        if re.search(r"\bdie\b|\bdat\b|\bwelke\b|\bwaarbij\b", text, re.IGNORECASE):
            structure["has_differentia"] = True

    # Check for examples
    if re.search(
        r"\bzoals\b|\bbijvoorbeeld\b|\bonder andere\b|\bo\.a\.\b", text, re.IGNORECASE
    ):
        structure["has_examples"] = True

    # Check for conditions
    if re.search(
        r"\bmits\b|\bindien\b|\bop voorwaarde\b|\bvoor zover\b", text, re.IGNORECASE
    ):
        structure["has_conditions"] = True

    # Check for exceptions
    if re.search(
        r"\bbehalve\b|\btenzij\b|\buitzonderingen?\b|\bmet uitzondering\b",
        text,
        re.IGNORECASE,
    ):
        structure["has_exceptions"] = True

    # Check for enumeration
    if re.search(
        r"\b[a-z]\)|[1-9]\.|ten eerste|ten tweede|\bi+\)", text, re.IGNORECASE
    ):
        structure["has_enumeration"] = True

    return structure
