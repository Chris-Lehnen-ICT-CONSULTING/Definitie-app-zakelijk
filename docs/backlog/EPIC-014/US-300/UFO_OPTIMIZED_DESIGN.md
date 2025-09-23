# UFO Categorie Detector - Geoptimaliseerd Ontwerp

## Executive Summary

Dit document presenteert een geoptimaliseerde beslisboom en pattern matching strategie voor automatische UFO-categorie detectie in Nederlandse juridische begrippen. De aanpak reduceert complexiteit van O(n×m) naar O(log n) door gebruik van voorgecompileerde patterns en efficiënte datastructuren.

## 1. Vereenvoudigde Beslisboom

### Hoofdbeslissing: 3-Fase Classificatie

```
FASE 1: SUBSTANTIALITEIT CHECK
├─ Is_Zelfstandig() → KIND
└─ Heeft_Drager()
   ├─ JA → FASE 2
   └─ NEE → FASE 3

FASE 2: DRAGER-AFHANKELIJK
├─ Is_Tijdsgebonden() → EVENT
├─ Is_Contextueel() → ROLE/PHASE
└─ Is_Attribuut() → MODE/QUALITY/QUANTITY

FASE 3: RELATIE-GEBASEERD
├─ Heeft_Meerdere_Deelnemers() → RELATOR
└─ Is_Abstract() → CATEGORY/MIXIN/ABSTRACT
```

### Geoptimaliseerde Beslisregels

```python
# Pseudo-code voor hoofdclassificatie
def classify_ufo_optimized(concept: ConceptData) -> UFOResult:
    # Pre-computed features (cached)
    features = FEATURE_CACHE.get_or_compute(concept.id,
                                           lambda: extract_features_batch(concept))

    # Level 1: Quick substantiality check (O(1) lookup)
    if SUBSTANTIVE_PATTERNS.matches(features.lemma):
        return UFOResult(category="Kind", confidence=0.9,
                        reason="Zelfstandig naamwoord patroon")

    # Level 2: Dependency check (O(log n) tree traversal)
    if features.has_bearer:
        return classify_dependent(features)

    # Level 3: Relation check (O(1) with pre-indexed relations)
    if features.participant_count >= 2:
        return classify_relational(features)

    # Fallback: Abstract classification
    return classify_abstract(features)
```

## 2. Geoptimaliseerde Pattern Matching

### 2.1 Datastructuur: Trie-Based Pattern Matcher

```python
class UFOPatternMatcher:
    def __init__(self):
        # Pre-compiled patterns per category
        self.tries = {
            'Kind': TrieNode(),
            'Event': TrieNode(),
            'Role': TrieNode(),
            # ... etc
        }

        # Bloom filter for quick negative matches
        self.bloom_filters = {
            category: BloomFilter(capacity=10000, error_rate=0.001)
            for category in UFO_CATEGORIES
        }

        # Compiled regex patterns (cached)
        self.regex_cache = {}

    def compile_patterns(self):
        """One-time compilation at startup"""
        for category, patterns in PATTERN_CONFIG.items():
            # Add to trie
            for pattern in patterns['exact_match']:
                self.tries[category].insert(pattern)

            # Add to bloom filter
            for pattern in patterns['all_patterns']:
                self.bloom_filters[category].add(pattern)

            # Compile regex patterns
            if patterns.get('regex'):
                self.regex_cache[category] = re.compile(
                    '|'.join(patterns['regex']),
                    re.IGNORECASE
                )
```

### 2.2 Feature Extraction Pipeline

```python
class FeatureExtractor:
    def __init__(self):
        # Pre-load NLP models
        self.nlp = spacy.load("nl_core_news_sm", disable=["ner", "parser"])
        self.lemmatizer = DutchLemmatizer()  # Custom optimized lemmatizer

        # Cache for expensive computations
        self.cache = LRUCache(maxsize=1000)

    def extract_features_batch(self, concepts: List[Concept]) -> List[Features]:
        """Batch processing for efficiency"""
        # Process all texts in one NLP call
        texts = [c.definition for c in concepts]
        docs = list(self.nlp.pipe(texts, batch_size=50))

        features = []
        for doc, concept in zip(docs, concepts):
            # Use cached result if available
            cache_key = hash(concept.definition)
            if cache_key in self.cache:
                features.append(self.cache[cache_key])
                continue

            # Extract features
            feat = Features(
                lemma=self._extract_lemma(doc),
                pos_tags=self._extract_pos(doc),
                has_bearer=self._check_bearer(doc),
                is_temporal=self._check_temporal(doc),
                participant_count=self._count_participants(doc),
                semantic_markers=self._extract_markers(doc)
            )

            self.cache[cache_key] = feat
            features.append(feat)

        return features
```

## 3. Nederlandse Taal Optimalisaties

### 3.1 Gegroepeerde Woordenlijsten

```python
DUTCH_PATTERNS = {
    'Kind': {
        'core_nouns': {
            'persoon', 'mens', 'individu',
            'organisatie', 'bedrijf', 'instelling',
            'voorwerp', 'object', 'zaak',
            'document', 'dossier', 'akte'
        },
        'legal_entities': {
            'rechtspersoon', 'natuurlijk persoon',
            'vennootschap', 'stichting', 'vereniging'
        }
    },

    'Event': {
        'process_markers': {
            'proces', 'procedure', 'handeling',
            'gebeurtenis', 'activiteit', 'verloop'
        },
        'temporal_markers': {
            'tijdens', 'gedurende', 'vanaf', 'tot',
            'doorlooptijd', 'termijn', 'periode'
        },
        'legal_processes': {
            'zitting', 'verhoor', 'onderzoek',
            'arrestatie', 'vervolging', 'berechting'
        }
    },

    'Role': {
        'role_markers': {
            'als', 'in de hoedanigheid van',
            'in de rol van', 'fungerend als'
        },
        'legal_roles': {
            'verdachte', 'getuige', 'rechter',
            'officier', 'advocaat', 'curator'
        }
    },

    'Relator': {
        'contract_types': {
            'overeenkomst', 'contract', 'convenant',
            'vergunning', 'machtiging', 'mandaat'
        },
        'legal_relations': {
            'huwelijk', 'voogdij', 'curatele',
            'dagvaarding', 'vonnis', 'beschikking'
        }
    }
}

# Synoniem mapping voor snelle lookups
SYNONYM_MAP = build_synonym_map(DUTCH_PATTERNS)  # O(1) lookup
```

### 3.2 Lemmatisering Cache

```python
class DutchLemmatizer:
    def __init__(self):
        # Pre-load common lemma mappings
        self.lemma_cache = {
            'personen': 'persoon',
            'organisaties': 'organisatie',
            'zittingen': 'zitting',
            'verdachten': 'verdachte',
            # ... thousands more pre-computed
        }

        # Suffix rules for unknown words
        self.suffix_rules = [
            (r'eren$', 'eer'),    # adviseren → adviseer
            (r'ingen$', 'ing'),   # handelingen → handeling
            (r'heden$', 'heid'),  # mogelijkheden → mogelijkheid
        ]

    def lemmatize(self, word: str) -> str:
        # O(1) cache lookup
        if word in self.lemma_cache:
            return self.lemma_cache[word]

        # Apply suffix rules
        for pattern, replacement in self.suffix_rules:
            if re.search(pattern, word):
                return re.sub(pattern, replacement, word)

        return word
```

## 4. Performance Optimalisatie Strategie

### 4.1 Lookup Table Approach

```python
class UFOClassifier:
    def __init__(self):
        # Pre-compute decision matrix
        self.decision_matrix = {
            # (has_bearer, is_temporal, participant_count, is_abstract): category
            (False, False, 0, False): 'Kind',
            (False, True, 0, False): 'Event',
            (True, False, 0, False): 'Mode',
            (True, False, 0, True): 'Quality',
            (False, False, 2, False): 'Relator',
            # ... complete matrix
        }

        # Secondary classification rules
        self.refinement_rules = {
            'Mode': self._refine_mode,
            'Quality': self._refine_quality,
            # ...
        }

    def classify(self, features: Features) -> UFOResult:
        # O(1) primary classification
        key = (
            features.has_bearer,
            features.is_temporal,
            features.participant_count,
            features.is_abstract
        )

        primary = self.decision_matrix.get(key, 'Unknown')

        # Apply refinement if needed
        if primary in self.refinement_rules:
            primary = self.refinement_rules[primary](features)

        return UFOResult(
            category=primary,
            confidence=self._calculate_confidence(features, primary),
            explanation=self._generate_explanation(features, primary)
        )
```

### 4.2 Batch Processing

```python
class BatchUFOProcessor:
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
        self.classifier = UFOClassifier()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def process_concepts(self, concepts: List[Concept]) -> List[UFOResult]:
        results = []

        # Process in batches
        for i in range(0, len(concepts), self.batch_size):
            batch = concepts[i:i+self.batch_size]

            # Parallel feature extraction
            futures = [
                self.executor.submit(self._process_single, concept)
                for concept in batch
            ]

            # Collect results
            for future in futures:
                results.append(future.result())

        return results
```

## 5. Maintenance-Vriendelijke Regel Structuur

### 5.1 Declaratieve Regel Configuratie

```yaml
# config/ufo_rules.yaml
rules:
  - id: kind_substantive
    category: Kind
    priority: 10
    conditions:
      pos_tag: ["NOUN"]
      not_has: ["bearer_markers"]
      semantic: ["concrete", "independent"]
    confidence_boost: 0.3
    explanation: "Zelfstandig naamwoord zonder drager"

  - id: event_temporal
    category: Event
    priority: 8
    conditions:
      any_of:
        - pos_tag: ["VERB"]
        - has_pattern: "temporal_markers"
      semantic: ["process", "activity"]
    confidence_boost: 0.25
    explanation: "Tijdsgebonden proces of gebeurtenis"

  - id: role_contextual
    category: Role
    priority: 7
    conditions:
      has_pattern: "role_markers"
      requires: ["bearer"]
    confidence_boost: 0.2
    explanation: "Contextuele rol met drager"
```

### 5.2 Rule Engine

```python
class RuleEngine:
    def __init__(self, config_path='config/ufo_rules.yaml'):
        self.rules = self._load_rules(config_path)
        self._compile_rules()

    def _compile_rules(self):
        """Pre-compile rules for efficiency"""
        for rule in self.rules:
            # Convert conditions to efficient checkers
            rule['compiled'] = self._compile_conditions(rule['conditions'])

    def evaluate(self, features: Features) -> List[RuleMatch]:
        matches = []

        for rule in self.rules:
            if rule['compiled'](features):
                matches.append(RuleMatch(
                    rule_id=rule['id'],
                    category=rule['category'],
                    confidence=rule['confidence_boost'],
                    explanation=rule['explanation']
                ))

        # Sort by priority
        return sorted(matches, key=lambda m: m.confidence, reverse=True)
```

## 6. Performance Benchmarks (Verwacht)

### Baseline (Huidige Aanpak)
- Gemiddelde classificatie tijd: ~50ms
- Memory footprint: ~100MB
- Accuracy: Onbekend (geen metrics)

### Geoptimaliseerde Aanpak
- **Classificatie tijd: < 5ms** (10x verbetering)
  - Feature extraction: 2ms (cached)
  - Pattern matching: 1ms (trie/bloom)
  - Rule evaluation: 1ms (compiled)
  - Result generation: 1ms

- **Memory footprint: ~50MB** (2x verbetering)
  - Trie structures: 10MB
  - Bloom filters: 5MB
  - Cache: 20MB (LRU, bounded)
  - Rules & patterns: 15MB

- **Throughput**
  - Single: 200 classifications/sec
  - Batch (100): 2000 classifications/sec

- **Accuracy (Expected)**
  - High confidence (>0.8): 85% precision
  - Medium confidence (0.5-0.8): 70% precision
  - Low confidence (<0.5): Manual review

## 7. Implementatie Roadmap

### Fase 1: Core Engine (Week 1)
1. Implement TrieNode en BloomFilter structures
2. Build FeatureExtractor met caching
3. Create RuleEngine met YAML config
4. Unit tests voor alle componenten

### Fase 2: Pattern Library (Week 2)
1. Compile Nederlandse woordenlijsten
2. Create synonym mappings
3. Build lemmatizer cache
4. Integration tests

### Fase 3: UI Integration (Week 3)
1. Service layer implementation
2. UI componenten voor suggesties
3. Audit logging
4. End-to-end tests

### Fase 4: Optimization (Week 4)
1. Performance profiling
2. Cache tuning
3. Batch processing optimization
4. Production readiness

## 8. Code Snippets

### Minimale Implementatie

```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class UFOCategory(Enum):
    KIND = "Kind"
    EVENT = "Event"
    ROLE = "Role"
    PHASE = "Phase"
    RELATOR = "Relator"
    MODE = "Mode"
    QUANTITY = "Quantity"
    QUALITY = "Quality"
    CATEGORY = "Category"
    MIXIN = "Mixin"
    ABSTRACT = "Abstract"

@dataclass
class UFOResult:
    category: UFOCategory
    confidence: float
    explanation: List[str]
    secondary_tags: List[str] = None

class MinimalUFOClassifier:
    """Minimal implementation for quick start"""

    def __init__(self):
        # Simple pattern matching
        self.patterns = {
            UFOCategory.KIND: [
                r'\b(persoon|mens|organisatie|voorwerp|document)\b',
                r'\b(rechtspersoon|natuurlijk\s+persoon)\b'
            ],
            UFOCategory.EVENT: [
                r'\b(proces|procedure|gebeurtenis|activiteit)\b',
                r'\b(tijdens|gedurende|doorlooptijd|termijn)\b'
            ],
            UFOCategory.ROLE: [
                r'\b(als|in\s+de\s+rol\s+van|fungerend\s+als)\b',
                r'\b(verdachte|getuige|rechter|advocaat)\b'
            ],
            UFOCategory.RELATOR: [
                r'\b(overeenkomst|contract|vergunning|mandaat)\b',
                r'\b(huwelijk|voogdij|dagvaarding)\b'
            ]
        }

        # Compile patterns
        self.compiled = {
            cat: re.compile('|'.join(patterns), re.IGNORECASE)
            for cat, patterns in self.patterns.items()
        }

    def classify(self, text: str) -> UFOResult:
        scores = {}
        explanations = {}

        # Score each category
        for category, pattern in self.compiled.items():
            matches = pattern.findall(text)
            if matches:
                scores[category] = len(matches) / len(text.split())
                explanations[category] = f"Gevonden: {', '.join(set(matches))}"

        if not scores:
            return UFOResult(
                category=UFOCategory.KIND,
                confidence=0.3,
                explanation=["Geen specifieke patronen gevonden, default KIND"]
            )

        # Get best match
        best_category = max(scores, key=scores.get)
        confidence = min(scores[best_category] * 10, 1.0)  # Normalize

        return UFOResult(
            category=best_category,
            confidence=confidence,
            explanation=[explanations[best_category]]
        )
```

## 9. Testing Strategy

### Unit Tests
```python
def test_kind_classification():
    classifier = MinimalUFOClassifier()
    result = classifier.classify("Een persoon is een natuurlijk mens")
    assert result.category == UFOCategory.KIND
    assert result.confidence > 0.7

def test_event_classification():
    classifier = MinimalUFOClassifier()
    result = classifier.classify("Het proces van arrestatie tijdens het onderzoek")
    assert result.category == UFOCategory.EVENT
    assert result.confidence > 0.6

def test_role_classification():
    classifier = MinimalUFOClassifier()
    result = classifier.classify("Een verdachte in de rol van getuige")
    assert result.category == UFOCategory.ROLE
    assert result.confidence > 0.5
```

### Integration Tests
```python
def test_batch_processing():
    processor = BatchUFOProcessor()
    concepts = load_test_concepts()  # 1000 test cases

    start = time.time()
    results = processor.process_concepts(concepts)
    duration = time.time() - start

    assert len(results) == len(concepts)
    assert duration < 5.0  # Should process 1000 in < 5 seconds
    assert all(r.confidence >= 0 for r in results)
```

## 10. Maintenance Guidelines

### Adding New Rules
1. Add pattern to `config/ufo_rules.yaml`
2. Update word lists in `config/dutch_patterns.yaml`
3. Run validation: `python scripts/validate_rules.py`
4. Test coverage: `pytest tests/ufo_classification/`

### Performance Monitoring
```python
# Log slow classifications
if classification_time > 10:  # ms
    logger.warning(f"Slow classification: {concept.id} took {classification_time}ms")

# Track accuracy
if user_override:
    metrics.record_override(
        suggested=result.category,
        corrected=user_choice,
        confidence=result.confidence
    )
```

### Regular Maintenance
- Weekly: Review low-confidence classifications
- Monthly: Update word lists based on overrides
- Quarterly: Retrain confidence thresholds

## Conclusie

Deze geoptimaliseerde aanpak reduceert complexiteit significant door:
1. **Vereenvoudigde beslisboom** met max 3 niveaus
2. **Efficiënte datastructuren** (Trie, Bloom filter, LRU cache)
3. **Pre-compiled patterns** en lookup tables
4. **Batch processing** capabilities
5. **Declaratieve regel configuratie** voor easy maintenance

De verwachte performance verbetering is 10x voor individuele classificaties en 20x voor batch processing, met behoud van 85% accuracy voor high-confidence predictions.