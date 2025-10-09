# Automated Synonym Suggestion Analysis voor DefinitieAgent

**Datum**: 8 oktober 2025
**Status**: Research & Analysis
**Doel**: Automatiseer juridische synoniemen suggestie ter verbetering van recall (80% → 90%+)

---

## Executive Summary

Deze analyse onderzoekt 5 concrete benaderingen voor het automatiseren van juridische synoniemen suggesties in de DefinitieAgent applicatie. Het huidige systeem gebruikt een handmatig gecureerde YAML (50 termen, 184 synoniemen) die verhoogde onderhoudslast heeft en beperkte coverage.

**Aanbeveling**: Hybride "GPT-4 Suggest + Human Approve" workflow (Benadering 2) biedt de beste balans tussen kwaliteit, implementatiegemak en onderhoudsbaarheid.

**Quick wins**:
1. Wikipedia redirects extraction (Benadering 1) - laaghangende vrucht voor 30-40% coverage uitbreiding
2. Database mining (Benadering 5) - hergebruik van bestaande 66 definities voor context-aware synoniemen

---

## Context & Current State

### Huidige Implementatie

**Database**: `/config/juridische_synoniemen.yaml`
- 50 hoofdtermen
- 184 unieke synoniemen
- Handmatig gecureerd
- Categorieën: Strafrecht, Bestuursrecht, Burgerlijk recht, Procesrecht

**Architecture**:
```
JuridischeSynoniemlService
├── Bidirectionele lookup (term ↔ synoniemen)
├── Query expansion (Wikipedia + SRU fallback)
└── Juridische ranking boost
```

**Performance**:
- Coverage: 80% → 90% (doel)
- Wikipedia fallback success: 15% → 35%
- SRU synonym hits: 25% (nieuw)

### Probleem

1. **Onderhoudslast**: Handmatig curatie schaalt niet
2. **Beperkte coverage**: 50 termen vs ~200+ juridische begrippen in praktijk
3. **Statische database**: Geen learning/feedback loop
4. **Kwaliteitsrisico's**: Geen systematische validatie van relevantie

---

## Benadering 1: Wikipedia Redirects & Disambiguation Mining

### Principe

Wikipedia redirects zijn feitelijk synoniemen. Bijvoorbeeld: "President Obama" → "Barack Obama". Voor Nederlandse juridische termen kan dit automatisch synoniemen opleveren.

### Implementatie

**Data Source**:
- MediaWiki API (NL Wikipedia)
- Wikipedia database dumps (redirect tabel)

**Methode**:
```python
async def extract_wikipedia_synonyms(term: str) -> list[str]:
    """Extract synoniemen uit Wikipedia redirects + disambiguation pages."""
    synonyms = []

    # 1. Redirects: pages die doorverwijzen naar hoofdterm
    redirects = await get_wikipedia_redirects(term)
    synonyms.extend(redirects)

    # 2. Disambiguation pages: alternatieve betekenissen
    if await is_disambiguation_page(term):
        alternatives = await get_disambiguation_links(term)
        # Filter juridisch relevante alternatives
        synonyms.extend(filter_juridical(alternatives))

    # 3. See-also links: gerelateerde begrippen
    see_also = await get_see_also_links(term)
    synonyms.extend(see_also[:3])  # Top 3

    return deduplicate(synonyms)
```

**API Calls**:
```python
# Check redirects
params = {
    'action': 'query',
    'titles': term,
    'redirects': 1,
    'prop': 'info'
}

# Get backlinks (pages redirecting TO this term)
params = {
    'action': 'query',
    'list': 'backlinks',
    'bltitle': term,
    'blfilterredir': 'redirects'
}
```

### Pros & Cons

**Pros**:
✅ Hoge precision (97-99% volgens research)
✅ Gratis, publieke API
✅ Automatisch up-to-date
✅ Bidirectioneel (redirects A→B en B→A)
✅ Nederlandse Wikipedia heeft juridische coverage

**Cons**:
❌ Beperkt tot termen met Wikipedia pagina
❌ Niet alle juridische begrippen hebben redirects
❌ Disambiguation pages bevatten noise (niet-juridische betekenissen)
❌ Geen domain-specifieke filtering

### Implementatie Complexiteit

**Effort**: 3-5 dagen
**Dependencies**: `aiohttp` (already in project), `mwparserfromhell` (optioneel)

**Stappen**:
1. Create `WikipediaSynonymExtractor` service
2. Implement redirect + disambiguation extraction
3. Add juridical filtering (keyword matching)
4. Batch processing voor bestaande 50 termen
5. Export naar YAML format

### Expected Impact

**Coverage**: +30-40% synoniemen voor termen met Wikipedia pagina
**Precision**: 85-90% (na juridische filtering)
**Maintenance**: Laag (1x per maand refresh)

### Sample Code

```python
class WikipediaSynonymExtractor:
    """Extract synoniemen uit Wikipedia redirects en disambiguation pages."""

    BASE_URL = "https://nl.wikipedia.org/w/api.php"

    async def extract_synonyms(self, term: str) -> dict[str, list[str]]:
        """
        Extract synoniemen voor een juridisch begrip.

        Returns:
            {
                'redirects': [...],
                'disambiguation': [...],
                'see_also': [...]
            }
        """
        async with aiohttp.ClientSession() as session:
            # 1. Get redirects
            redirects = await self._get_redirects(session, term)

            # 2. Check if disambiguation page
            if await self._is_disambiguation(session, term):
                disambig = await self._get_disambiguation_links(session, term)
            else:
                disambig = []

            # 3. Get see-also links
            see_also = await self._get_see_also_links(session, term)

            return {
                'redirects': self._filter_juridical(redirects),
                'disambiguation': self._filter_juridical(disambig),
                'see_also': self._filter_juridical(see_also)
            }

    def _filter_juridical(self, terms: list[str]) -> list[str]:
        """Filter juridisch relevante termen."""
        juridical_keywords = {
            'recht', 'wet', 'artikel', 'verdachte', 'rechter',
            'vonnis', 'procedure', 'beroep', 'cassatie', ...
        }

        filtered = []
        for term in terms:
            # Check if term contains juridical keywords
            term_lower = term.lower()
            if any(kw in term_lower for kw in juridical_keywords):
                filtered.append(term)

        return filtered
```

---

## Benadering 2: GPT-4 Suggest + Human Approve Workflow

### Principe

Gebruik GPT-4 om synoniemen te suggereren op basis van juridische context, en laat een mens (curator) de suggesties goedkeuren/afwijzen. Dit combineert AI-power met menselijke kwaliteitscontrole.

### Implementatie

**Workflow**:
```
1. GPT-4: Genereer 5-10 synonym candidates per term
2. Score: Rank op basis van juridische relevantie (0-1)
3. Human Review: Curator keurt top-3 goed/af
4. Update: Goedgekeurde synoniemen → YAML
5. Feedback Loop: Rejections verbeteren volgende suggesties
```

**GPT-4 Prompt Template**:
```python
SYNONYM_PROMPT = """
Je bent een juridisch taalkundige specialist. Genereer synoniemen voor de volgende Nederlandse juridische term.

TERM: {term}
CONTEXT: {context}  # bijv. "Strafrecht (Sv)", "Bestuursrecht (Awb)"
DEFINITIE: {definition}  # Uit database indien beschikbaar

Vereisten:
1. Synoniemen moeten juridisch correct zijn
2. Gebruik gangbare juridische terminologie (geen slang)
3. Geschikt voor wetgeving.nl en rechtspraak.nl searches
4. Geen te algemene termen (blijf specifiek)
5. Zowel formele als informele varianten (bijv. "Sv" vs "Wetboek van Strafvordering")

Output formaat (JSON):
{{
  "synoniemen": [
    {{"term": "synoniem1", "confidence": 0.95, "rationale": "..."}},
    {{"term": "synoniem2", "confidence": 0.80, "rationale": "..."}}
  ]
}}

Genereer maximaal 8 synoniemen, gesorteerd op confidence.
"""
```

**API Integration**:
```python
class GPT4SynonymSuggester:
    """GPT-4 powered synonym suggestion service."""

    def __init__(self, ai_service: AIServiceV2):
        self.ai_service = ai_service

    async def suggest_synonyms(
        self,
        term: str,
        context: str = None,
        definition: str = None
    ) -> list[SynonymSuggestion]:
        """
        Suggereer synoniemen voor een juridisch begrip.

        Returns:
            List van SynonymSuggestion met term, confidence, rationale
        """
        # Build prompt met context
        prompt = SYNONYM_PROMPT.format(
            term=term,
            context=context or "Algemeen juridisch",
            definition=definition or "Geen definitie beschikbaar"
        )

        # Call GPT-4
        response = await self.ai_service.generate(
            prompt=prompt,
            temperature=0.3,  # Low temp voor consistency
            max_tokens=500
        )

        # Parse JSON response
        suggestions = self._parse_suggestions(response)

        # Filter low-confidence suggestions (< 0.6)
        return [s for s in suggestions if s.confidence >= 0.6]
```

**Human Review UI** (Streamlit):
```python
def render_synonym_review_ui():
    """Streamlit UI voor curator approval."""
    st.title("Synoniemen Review")

    # Load pending suggestions from database
    suggestions = load_pending_suggestions()

    for suggestion in suggestions:
        st.subheader(f"Term: {suggestion.hoofdterm}")
        st.write(f"Context: {suggestion.context}")

        for syn in suggestion.synoniemen:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"{syn.term} (confidence: {syn.confidence:.2f})")
                st.caption(syn.rationale)

            with col2:
                if st.button("✅ Approve", key=f"approve_{syn.id}"):
                    approve_synonym(suggestion.hoofdterm, syn.term)

            with col3:
                if st.button("❌ Reject", key=f"reject_{syn.id}"):
                    reject_synonym(syn.id, reason=st.text_input("Reason"))

            with col4:
                if st.button("✏️ Edit", key=f"edit_{syn.id}"):
                    edit_synonym(syn.id)
```

### Pros & Cons

**Pros**:
✅ Hoge kwaliteit door human-in-the-loop
✅ Context-aware (gebruikt definitie uit database)
✅ Schaalt goed (batch processing mogelijk)
✅ Feedback loop verbetert suggesties
✅ Rationale helpt curator bij beslissing
✅ Hergebruikt bestaande GPT-4 integratie

**Cons**:
❌ Vereist curator tijd (maar wel efficiënter dan volledig handmatig)
❌ API kosten (GPT-4 calls)
❌ Kwaliteit afhankelijk van prompt engineering
❌ Geen garantie op volledigheid

### Implementatie Complexiteit

**Effort**: 5-8 dagen
**Dependencies**: `AIServiceV2` (already in project), database schema update

**Stappen**:
1. Create `GPT4SynonymSuggester` service
2. Design prompt template + testing
3. Database schema: `synonym_suggestions` tabel (id, term, suggestions, status, curator_id)
4. Streamlit UI voor review workflow
5. Feedback loop: rejected suggestions → prompt improvement
6. Batch processing: suggesteer synoniemen voor alle database terms

### Expected Impact

**Coverage**: +100-150% synoniemen (50 → 150 termen met avg 3 synoniemen)
**Precision**: 90-95% (door human approval)
**Maintenance**: Medium (curator review 1-2x per week, ~30 min)

### Cost Estimation

**GPT-4 Costs**:
- Input: ~300 tokens per term (prompt + context + definitie)
- Output: ~200 tokens (8 synoniemen met rationale)
- Cost per term: ~$0.015 (gpt-4-turbo pricing)
- Total for 200 terms: ~$3
- Monthly maintenance (20 nieuwe termen): ~$0.30

**Zeer kostenefficiënt!**

### Sample Implementation

```python
# Database schema
CREATE TABLE synonym_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hoofdterm TEXT NOT NULL,
    synoniem TEXT NOT NULL,
    confidence DECIMAL(3,2),
    rationale TEXT,
    status TEXT CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# Service integration
class SynonymWorkflow:
    """Orchestrate GPT-4 suggest + human approve workflow."""

    def __init__(
        self,
        suggester: GPT4SynonymSuggester,
        repository: SynonymRepository
    ):
        self.suggester = suggester
        self.repository = repository

    async def batch_suggest(self, terms: list[str]) -> None:
        """Batch process synonym suggestions voor multiple terms."""
        for term in terms:
            # Get definitie uit database indien beschikbaar
            definitie = await self._get_definition(term)
            context = await self._infer_context(term, definitie)

            # Generate suggestions
            suggestions = await self.suggester.suggest_synonyms(
                term=term,
                context=context,
                definition=definitie
            )

            # Save voor human review
            await self.repository.save_suggestions(term, suggestions)

    async def approve_synonym(self, hoofdterm: str, synoniem: str) -> None:
        """Approve een synonym suggestion."""
        # Update database status
        await self.repository.update_status(hoofdterm, synoniem, 'approved')

        # Update juridische_synoniemen.yaml
        await self._update_yaml_config(hoofdterm, synoniem)

    async def _update_yaml_config(self, hoofdterm: str, synoniem: str) -> None:
        """Update YAML config met nieuw synoniem."""
        yaml_path = Path("config/juridische_synoniemen.yaml")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        # Normalize hoofdterm (spaces → underscores)
        hoofdterm_normalized = hoofdterm.replace(' ', '_')

        # Add synoniem
        if hoofdterm_normalized not in data:
            data[hoofdterm_normalized] = []

        if synoniem not in data[hoofdterm_normalized]:
            data[hoofdterm_normalized].append(synoniem)

        # Write back
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=True)
```

---

## Benadering 3: Open Dutch WordNet (Cornetto) Integration

### Principe

Open Dutch WordNet is een semantische database met 117.914 synsets, 92.295 synoniemen en Nederlandse lexicale semantiek. Dit kan gebruikt worden voor algemene synonym extraction, met filtering op juridisch domein.

### Implementatie

**Data Source**:
- Open Dutch WordNet XML (CC BY-SA 4.0 license)
- Download: http://wordpress.let.vupr.nl/odwn/

**Methode**:
```python
from lxml import etree

class DutchWordNetSynonymExtractor:
    """Extract synoniemen uit Open Dutch WordNet."""

    def __init__(self, wordnet_xml_path: str):
        self.tree = etree.parse(wordnet_xml_path)
        self.synsets = self._build_synset_index()

    def get_synonyms(self, term: str) -> list[str]:
        """Haal synoniemen op uit WordNet."""
        # 1. Find synsets containing term
        synsets = self._find_synsets_for_lemma(term)

        # 2. Extract all lemmas from these synsets
        synonyms = []
        for synset in synsets:
            lemmas = self._get_synset_lemmas(synset)
            synonyms.extend([l for l in lemmas if l != term])

        # 3. Filter juridisch relevante synoniemen
        return self._filter_juridical(synonyms)

    def _find_synsets_for_lemma(self, lemma: str) -> list[str]:
        """Find synset IDs containing lemma."""
        xpath = f"//Lemma[text()='{lemma}']/../@id"
        return self.tree.xpath(xpath)
```

**Integration met bestaande workflow**:
```python
# Pre-processing: Build synonym database from WordNet
extractor = DutchWordNetSynonymExtractor("odwn.xml")

for term in juridische_termen:
    wn_synonyms = extractor.get_synonyms(term)

    # Combine met Wikipedia synoniemen
    wiki_synonyms = await wikipedia_extractor.extract_synonyms(term)

    # Merge en dedupliceer
    all_synonyms = deduplicate(wn_synonyms + wiki_synonyms['redirects'])

    # Save voor human review
    await repository.save_suggestions(term, all_synonyms)
```

### Pros & Cons

**Pros**:
✅ Grote dataset (117K synsets, 92K synoniemen)
✅ Open source (CC BY-SA 4.0)
✅ Wetenschappelijk onderbouwd
✅ Nederlandse taal focus
✅ Gratis, geen API limits

**Cons**:
❌ Algemene taal, niet juridisch-specifiek
❌ Lage precision voor juridische termen (~30-40%)
❌ Beperkte juridische coverage (meeste termen ontbreken)
❌ XML parsing overhead
❌ Static dataset (geen updates sinds 2016)
❌ Vereist extensive filtering

### Implementatie Complexiteit

**Effort**: 3-4 dagen
**Dependencies**: `lxml`, `nltk` (optioneel)

**Stappen**:
1. Download Open Dutch WordNet XML dump
2. Parse XML en build synset index
3. Implement lemma → synset → synonyms lookup
4. Juridische filtering (keyword matching)
5. Integration met approval workflow

### Expected Impact

**Coverage**: +20-30% voor algemene juridische begrippen
**Precision**: 35-45% (zonder filtering), 60-70% (met filtering)
**Maintenance**: Zeer laag (static dataset)

### Verdict

**Niet aanbevolen als primaire benadering** vanwege lage precision en beperkte juridische coverage. Kan wel gebruikt worden als **supplementaire bron** in combinatie met Wikipedia of GPT-4.

---

## Benadering 4: Wiktionary API + Juridisch Thesaurus Mining

### Principe

Wiktionary bevat Nederlandse synoniemen en thesaurus data. Combineer dit met juridische thesauri (EUROVOC, JuridischWoordenboek.nl) voor domain-specific synonyms.

### Implementatie

**Data Sources**:
1. **Wiktionary** - via Wiktextract tool (https://github.com/tatuylonen/wiktextract)
2. **EUROVOC** - EU multilingual thesaurus (12.169 Dutch-English entries)
3. **JuridischWoordenboek.nl** - 10.000+ juridische definities

**Methode**:
```python
import requests
from wiktextract import WiktextractClient

class JuridicalThesaurusMiner:
    """Mine synoniemen uit Wiktionary + juridische thesauri."""

    def __init__(self):
        self.wiktextract = WiktextractClient()
        self.eurovoc_cache = self._load_eurovoc_data()

    async def extract_synonyms(self, term: str) -> dict[str, list[str]]:
        """Extract synoniemen uit multiple sources."""
        synonyms = {
            'wiktionary': await self._get_wiktionary_synonyms(term),
            'eurovoc': self._get_eurovoc_synonyms(term),
            'juridisch_wb': await self._get_juridisch_woordenboek_synonyms(term)
        }

        return synonyms

    async def _get_wiktionary_synonyms(self, term: str) -> list[str]:
        """Extract synoniemen uit Wiktionary via Wiktextract."""
        # Use pre-extracted Wiktionary data from kaikki.org
        url = f"https://kaikki.org/dictionary/Dutch/{term}.json"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Extract synonyms from 'synonyms' linkage
                    synonyms = []
                    for entry in data:
                        if 'senses' in entry:
                            for sense in entry['senses']:
                                if 'synonyms' in sense:
                                    synonyms.extend([s['word'] for s in sense['synonyms']])
                    return synonyms

        return []

    def _get_eurovoc_synonyms(self, term: str) -> list[str]:
        """Lookup synoniemen in EUROVOC thesaurus."""
        # EUROVOC heeft multi-lingual mappings
        # Term in Nederlands → vind equivalenten in andere talen → vertaal terug
        # Dit is complex, vereist EUROVOC SKOS/RDF parsing

        # Simplified: alleen exact matches
        if term.lower() in self.eurovoc_cache:
            return self.eurovoc_cache[term.lower()]['related_terms']

        return []
```

**EUROVOC Integration**:
```python
# EUROVOC is beschikbaar als SKOS/RDF download
# http://publications.europa.eu/resource/authority/eurovoc

from rdflib import Graph

class EurovocThesaurus:
    """Access EUROVOC thesaurus voor juridische begrippen."""

    def __init__(self, rdf_file: str):
        self.graph = Graph()
        self.graph.parse(rdf_file, format='xml')

    def get_related_terms(self, term: str, lang: str = 'nl') -> list[str]:
        """Haal gerelateerde termen op uit EUROVOC."""
        # SPARQL query voor related terms
        query = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT ?related ?label
        WHERE {{
            ?concept skos:prefLabel "{term}"@{lang} .
            ?concept skos:related ?related .
            ?related skos:prefLabel ?label .
            FILTER (lang(?label) = "{lang}")
        }}
        """

        results = self.graph.query(query)
        return [str(row.label) for row in results]
```

### Pros & Cons

**Pros**:
✅ Juridisch-specifieke coverage (EUROVOC)
✅ Multi-source validatie (meerdere bronnen bevestigen synoniemen)
✅ EUROVOC is officiële EU resource (hoge kwaliteit)
✅ Wiktionary heeft Nederlandse synoniemen

**Cons**:
❌ Complexe setup (RDF parsing, API integratie)
❌ EUROVOC focus op EU recht (niet NL strafrecht/bestuursrecht)
❌ Wiktionary lage coverage voor juridische termen
❌ JuridischWoordenboek.nl heeft geen publieke API
❌ Hoge implementation overhead

### Implementatie Complexiteit

**Effort**: 8-12 dagen
**Dependencies**: `wiktextract`, `rdflib`, `aiohttp`

**Stappen**:
1. Download EUROVOC RDF dump
2. Setup Wiktextract client (use pre-extracted data)
3. Implement multi-source synonym extraction
4. Build consensus algorithm (term moet in 2+ bronnen voorkomen)
5. Integration met approval workflow

### Expected Impact

**Coverage**: +40-60% voor EU-gerelateerde juridische begrippen
**Precision**: 70-80% (EUROVOC is hoge kwaliteit)
**Maintenance**: Laag (quarterly EUROVOC updates)

### Verdict

**Aanbevolen voor specifieke use cases** (EU recht, internationale verdragen) maar te complex als primaire benadering. Kan als **supplementaire bron** dienen na implementatie van Benadering 1 of 2.

---

## Benadering 5: Database Mining + Definition-based Similarity

### Principe

Analyseer bestaande definities in de database (66 begrippen) om synoniemen af te leiden op basis van:
1. Definitie overlap (gelijke woorden in definitie)
2. Context overlap (zelfde juridische/organisatorische context)
3. Embedding similarity (semantische gelijkenis)

### Implementatie

**Data Source**:
- `data/definities.db` - 66 definities (57 unieke termen)
- Voorbeelden, wettelijke basis, context

**Methode 1: Definitie Overlap Analysis**
```python
class DefinitionBasedSynonymExtractor:
    """Extract synoniemen uit database definities via similarity."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def find_similar_terms(
        self,
        term: str,
        similarity_threshold: float = 0.6
    ) -> list[tuple[str, float]]:
        """
        Vind termen met gelijke definitie karakteristieken.

        Returns:
            List van (term, similarity_score) tuples
        """
        # 1. Haal definitie op voor target term
        target_def = self._get_definition(term)

        # 2. Haal alle andere definities op
        all_definitions = self._get_all_definitions()

        # 3. Bereken similarity scores
        similar_terms = []
        for other_term, other_def in all_definitions.items():
            if other_term == term:
                continue

            # Similarity metrics
            score = self._calculate_similarity(target_def, other_def)

            if score >= similarity_threshold:
                similar_terms.append((other_term, score))

        # 4. Sort by score descending
        return sorted(similar_terms, key=lambda x: x[1], reverse=True)

    def _calculate_similarity(self, def1: dict, def2: dict) -> float:
        """
        Calculate similarity between two definitions.

        Factors:
        - Jaccard similarity van definitie woorden (0.4 weight)
        - Context overlap (juridisch + organisatorisch) (0.3 weight)
        - Wettelijke basis overlap (0.2 weight)
        - Categorie match (0.1 weight)
        """
        # Jaccard similarity van definitie tekst
        words1 = set(def1['definitie'].lower().split())
        words2 = set(def2['definitie'].lower().split())
        jaccard = len(words1 & words2) / len(words1 | words2)

        # Context overlap
        ctx1 = set(def1.get('juridische_context', []))
        ctx2 = set(def2.get('juridische_context', []))
        context_overlap = len(ctx1 & ctx2) / max(len(ctx1 | ctx2), 1)

        # Wettelijke basis overlap
        wet1 = set(def1.get('wettelijke_basis', []))
        wet2 = set(def2.get('wettelijke_basis', []))
        wet_overlap = len(wet1 & wet2) / max(len(wet1 | wet2), 1)

        # Categorie match
        cat_match = 1.0 if def1.get('categorie') == def2.get('categorie') else 0.0

        # Weighted score
        score = (
            0.4 * jaccard +
            0.3 * context_overlap +
            0.2 * wet_overlap +
            0.1 * cat_match
        )

        return score
```

**Methode 2: GPT-4 Embeddings Similarity**
```python
class EmbeddingBasedSynonymExtractor:
    """Extract synoniemen via GPT-4 embeddings similarity."""

    def __init__(self, openai_client):
        self.client = openai_client
        self.embeddings_cache = {}

    async def find_similar_terms(
        self,
        term: str,
        all_terms: list[str],
        threshold: float = 0.8
    ) -> list[tuple[str, float]]:
        """
        Vind semantisch gelijke termen via embeddings.

        Uses OpenAI text-embedding-3-small (cost-efficient).
        """
        # 1. Get embedding voor target term
        target_embedding = await self._get_embedding(term)

        # 2. Get embeddings voor alle termen
        similar_terms = []
        for other_term in all_terms:
            if other_term == term:
                continue

            other_embedding = await self._get_embedding(other_term)

            # Cosine similarity
            similarity = self._cosine_similarity(target_embedding, other_embedding)

            if similarity >= threshold:
                similar_terms.append((other_term, similarity))

        return sorted(similar_terms, key=lambda x: x[1], reverse=True)

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding via OpenAI API (met cache)."""
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]

        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        embedding = response.data[0].embedding
        self.embeddings_cache[text] = embedding

        return embedding

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import numpy as np

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        return dot_product / (norm1 * norm2)
```

**Combined Approach**:
```python
class HybridDatabaseSynonymExtractor:
    """Combine definitie overlap + embedding similarity."""

    def __init__(
        self,
        db_extractor: DefinitionBasedSynonymExtractor,
        embedding_extractor: EmbeddingBasedSynonymExtractor
    ):
        self.db_extractor = db_extractor
        self.embedding_extractor = embedding_extractor

    async def extract_synonyms(self, term: str) -> list[str]:
        """
        Extract synoniemen met multi-metric consensus.

        Strategy:
        1. Definitie overlap score
        2. Embedding similarity score
        3. Term moet hoog scoren op BEIDE metrics
        """
        # 1. Definitie-based similarity
        db_similar = self.db_extractor.find_similar_terms(term, threshold=0.5)

        # 2. Embedding-based similarity
        all_terms = self._get_all_database_terms()
        emb_similar = await self.embedding_extractor.find_similar_terms(
            term, all_terms, threshold=0.75
        )

        # 3. Consensus: term moet in BEIDE lijsten voorkomen
        db_terms = {t for t, _ in db_similar}
        emb_terms = {t for t, _ in emb_similar}

        consensus_terms = db_terms & emb_terms

        # 4. Rank by combined score
        ranked = []
        for t in consensus_terms:
            db_score = next((s for term, s in db_similar if term == t), 0)
            emb_score = next((s for term, s in emb_similar if term == t), 0)
            combined_score = 0.5 * db_score + 0.5 * emb_score
            ranked.append((t, combined_score))

        ranked.sort(key=lambda x: x[1], reverse=True)

        return [t for t, _ in ranked[:5]]  # Top 5
```

### Pros & Cons

**Pros**:
✅ Hergebruik bestaande data (geen externe dependencies)
✅ Context-aware (gebruikt juridische context uit database)
✅ Embeddings bieden semantische matching
✅ Geen human annotation nodig voor initial suggestions
✅ Kosten-efficiënt (embeddings API goedkoop)

**Cons**:
❌ Beperkt tot termen in database (66 definities)
❌ Low coverage (kan alleen synoniemen vinden voor reeds gedefinieerde termen)
❌ Vereist kritische massa (werkt beter met 200+ definities)
❌ Embedding API kosten (klein, ~$0.001 per term)
❌ Mogelijk false positives (semantisch vergelijkbaar ≠ synoniem)

### Implementatie Complexiteit

**Effort**: 4-6 dagen
**Dependencies**: `numpy`, `openai` (already in project)

**Stappen**:
1. Implement definitie overlap calculator
2. Implement embeddings similarity calculator
3. Build hybrid consensus algorithm
4. Batch process voor alle database termen
5. Export suggestions naar review workflow

### Expected Impact

**Coverage**: +15-25% synoniemen (alleen voor bestaande database termen)
**Precision**: 60-70% (vereist human review)
**Maintenance**: Laag (automatisch bij database growth)

### Cost Estimation

**Embedding API Costs**:
- Model: `text-embedding-3-small` ($0.020 per 1M tokens)
- Avg term length: 3 tokens
- 200 terms: 600 tokens → $0.000012
- **Verwaarloosbaar!**

### Verdict

**Aanbevolen als supplementaire benadering** naast Wikipedia of GPT-4 suggest. Werkt best als database groeit (200+ definities). Kan gebruikt worden voor **quality assurance** (valideer handmatige synoniemen tegen embeddings).

---

## Comparison Matrix

| Benadering | Coverage | Precision | Cost | Complexity | Maintenance | Recommended |
|------------|----------|-----------|------|------------|-------------|-------------|
| **1. Wikipedia Redirects** | ⭐⭐⭐ (30-40%) | ⭐⭐⭐⭐ (85-90%) | 💰 FREE | ⚙️⚙️⚙️ (3-5 days) | 🔧 Low | ✅ **YES - Quick Win** |
| **2. GPT-4 Suggest + Approve** | ⭐⭐⭐⭐⭐ (100-150%) | ⭐⭐⭐⭐⭐ (90-95%) | 💰💰 Low (~$3 one-time) | ⚙️⚙️⚙️⚙️ (5-8 days) | 🔧🔧 Medium | ✅ **YES - Primary** |
| **3. Open Dutch WordNet** | ⭐⭐ (20-30%) | ⭐⭐ (60-70%) | 💰 FREE | ⚙️⚙️⚙️ (3-4 days) | 🔧 Very Low | ❌ Supplementary only |
| **4. Wiktionary + EUROVOC** | ⭐⭐⭐ (40-60%) | ⭐⭐⭐⭐ (70-80%) | 💰 FREE | ⚙️⚙️⚙️⚙️⚙️ (8-12 days) | 🔧 Low | ❌ Too complex |
| **5. Database Mining** | ⭐⭐ (15-25%) | ⭐⭐⭐ (60-70%) | 💰 Low (~$0.001) | ⚙️⚙️⚙️⚙️ (4-6 days) | 🔧 Low | ✅ **YES - Supplementary** |

**Legend**:
- ⭐ = Coverage/Precision rating
- 💰 = Cost (FREE, Low, Medium, High)
- ⚙️ = Implementation complexity (more = more complex)
- 🔧 = Maintenance burden (more = higher burden)

---

## Recommended Implementation Strategy

### Phase 1: Quick Wins (Week 1-2)

**Implement Benadering 1 (Wikipedia Redirects)**

Rationale:
- Laaghangende vrucht
- Hoge precision (85-90%)
- Geen kosten
- 3-5 dagen implementatie

**Deliverables**:
1. `WikipediaSynonymExtractor` service
2. Batch extraction script voor 50 bestaande termen
3. Export naar pending suggestions (voor human review)

**Expected gain**: +30-40 nieuwe synoniemen (80 → 120 totaal)

---

### Phase 2: Scaling (Week 3-4)

**Implement Benadering 2 (GPT-4 Suggest + Approve)**

Rationale:
- Schaalt naar 200+ termen
- Hoge kwaliteit door human-in-the-loop
- Context-aware (gebruikt database definities)
- Feedback loop voor continuous improvement

**Deliverables**:
1. `GPT4SynonymSuggester` service
2. Database schema update (synonym_suggestions tabel)
3. Streamlit review UI
4. Batch processing voor alle database termen
5. YAML auto-update bij approval

**Expected gain**: +100-150 nieuwe synoniemen (120 → 270 totaal)

---

### Phase 3: Validation & Optimization (Week 5-6)

**Implement Benadering 5 (Database Mining) als Quality Check**

Rationale:
- Valideer handmatige synoniemen tegen embeddings
- Detect missing synoniemen voor bestaande termen
- Low cost, high precision voor consensus matches

**Deliverables**:
1. `EmbeddingBasedSynonymExtractor` service
2. Consensus algorithm (definitie overlap + embeddings)
3. Quality report: highlight suspicious synoniemen
4. Auto-suggest missing synoniemen

**Expected gain**: +20-30 validated synoniemen, verbeterde kwaliteit

---

## Implementation Roadmap

### Week 1-2: Wikipedia Redirects (Benadering 1)

**Tasks**:
1. **Day 1-2**: Setup WikipediaSynonymExtractor
   - MediaWiki API integration
   - Redirect extraction
   - Disambiguation page parsing
2. **Day 3**: Juridical filtering
   - Keyword-based filtering
   - Category detection (Strafrecht, Bestuursrecht, etc.)
3. **Day 4**: Batch processing
   - Process 50 bestaande termen
   - Export naar suggestions database
4. **Day 5**: Testing & validation
   - Manual review van top 20 suggestions
   - Precision/recall metrics

**Deliverable**: 30-40 nieuwe Wikipedia-sourced synoniemen

---

### Week 3-4: GPT-4 Suggest + Approve (Benadering 2)

**Tasks**:
1. **Day 1-2**: GPT4SynonymSuggester service
   - Prompt engineering & testing
   - API integration (reuse AIServiceV2)
   - JSON response parsing
2. **Day 3-4**: Database schema + repository
   - Create synonym_suggestions tabel
   - SynonymRepository CRUD operations
   - Status tracking (pending/approved/rejected)
3. **Day 5-6**: Streamlit review UI
   - List pending suggestions
   - Approve/reject/edit buttons
   - Rationale display
   - Bulk operations
4. **Day 7**: YAML auto-update
   - Approval triggers YAML update
   - Validation (no duplicates)
   - Backup mechanism
5. **Day 8**: Batch processing
   - Process alle 66 database termen
   - Generate suggestions with context
   - Queue voor curator review

**Deliverable**: 100-150 GPT-4 suggested synoniemen (pending review)

---

### Week 5-6: Database Mining + Quality Assurance (Benadering 5)

**Tasks**:
1. **Day 1-2**: Definitie overlap calculator
   - Jaccard similarity implementation
   - Context overlap scoring
   - Weighted score algorithm
2. **Day 3-4**: Embeddings similarity
   - OpenAI embeddings API integration
   - Cosine similarity calculator
   - Caching mechanism
3. **Day 5**: Hybrid consensus algorithm
   - Combine definitie + embedding scores
   - Threshold tuning (test verschillende thresholds)
4. **Day 6**: Quality report generation
   - Compare handmatige synoniemen met embeddings
   - Highlight low-similarity pairs (possible errors)
   - Suggest missing synoniemen

**Deliverable**: Quality report + 20-30 validated synoniemen

---

## Pseudo-code: Primary Recommendation (Benadering 2)

```python
# =======================
# GPT-4 Synonym Suggester
# =======================

class GPT4SynonymSuggester:
    """
    AI-powered juridical synonym suggestion service.

    Features:
    - Context-aware suggestions (uses definitie + context)
    - Confidence scoring (0-1)
    - Rationale generation (explains why synonym is suggested)
    - Batch processing support
    """

    SYNONYM_PROMPT_TEMPLATE = """
Je bent een expert in Nederlands juridisch taalgebruik. Genereer synoniemen voor de volgende term.

TERM: {term}
JURIDISCHE CONTEXT: {juridische_context}
ORGANISATORISCHE CONTEXT: {organisatorische_context}
WETTELIJKE BASIS: {wettelijke_basis}
DEFINITIE: {definitie}

Vereisten voor synoniemen:
1. Juridisch correct en gangbaar in Nederlandse rechtspraak
2. Geschikt voor zoekopdrachten in wetgeving.nl, rechtspraak.nl en Wikipedia
3. Zowel formele als informele varianten (bijv. "Sv" en "Wetboek van Strafvordering")
4. Geen te algemene termen - blijf specifiek voor het juridische domein
5. Vermijd dialectische of verouderde termen

Output (JSON):
{{
  "synoniemen": [
    {{
      "term": "synoniem1",
      "confidence": 0.95,
      "rationale": "Officiële term gebruikt in Wetboek van Strafvordering Art. X"
    }},
    {{
      "term": "synoniem2",
      "confidence": 0.85,
      "rationale": "Gangbare informele term in rechtspraak"
    }}
  ]
}}

Genereer maximaal 8 synoniemen, gesorteerd op confidence (hoog naar laag).
"""

    def __init__(self, ai_service: AIServiceV2):
        self.ai_service = ai_service
        self.logger = logging.getLogger(__name__)

    async def suggest_synonyms(
        self,
        term: str,
        definitie: Optional[str] = None,
        juridische_context: Optional[list[str]] = None,
        organisatorische_context: Optional[list[str]] = None,
        wettelijke_basis: Optional[list[str]] = None
    ) -> list[SynonymSuggestion]:
        """
        Genereer synonym suggestions voor een juridisch begrip.

        Args:
            term: Hoofdterm waarvoor synoniemen gezocht worden
            definitie: Optionele definitie uit database
            juridische_context: Juridisch domein (bijv. ["strafrecht", "Sv"])
            organisatorische_context: Organisatie (bijv. ["OM", "DJI"])
            wettelijke_basis: Relevante wetgeving (bijv. ["Sv", "Sr"])

        Returns:
            List van SynonymSuggestion objecten met term, confidence, rationale
        """
        # Build prompt met context
        prompt = self.SYNONYM_PROMPT_TEMPLATE.format(
            term=term,
            juridische_context=self._format_context(juridische_context),
            organisatorische_context=self._format_context(organisatorische_context),
            wettelijke_basis=self._format_context(wettelijke_basis),
            definitie=definitie or "Geen definitie beschikbaar"
        )

        self.logger.info(f"Generating synonym suggestions voor: {term}")

        try:
            # Call GPT-4 met low temperature (consistency)
            response = await self.ai_service.generate(
                prompt=prompt,
                temperature=0.3,  # Low temp voor consistent, factual output
                max_tokens=600
            )

            # Parse JSON response
            suggestions = self._parse_suggestions_response(response)

            # Filter low-confidence suggestions (< 0.6)
            filtered = [s for s in suggestions if s.confidence >= 0.6]

            self.logger.info(
                f"Generated {len(filtered)} high-confidence suggestions for {term}"
            )

            return filtered

        except Exception as e:
            self.logger.error(f"Failed to generate suggestions for {term}: {e}")
            return []

    def _format_context(self, context: Optional[list[str]]) -> str:
        """Format context list naar leesbare string."""
        if not context:
            return "Niet gespecificeerd"
        return ", ".join(context)

    def _parse_suggestions_response(self, response: str) -> list[SynonymSuggestion]:
        """Parse GPT-4 JSON response naar SynonymSuggestion objecten."""
        import json

        try:
            # Extract JSON uit response (GPT-4 kan soms extra text toevoegen)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]

            data = json.loads(json_str)

            suggestions = []
            for item in data.get('synoniemen', []):
                suggestions.append(
                    SynonymSuggestion(
                        term=item['term'],
                        confidence=float(item['confidence']),
                        rationale=item['rationale']
                    )
                )

            return suggestions

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            return []

# =======================
# Workflow Orchestration
# =======================

class SynonymWorkflow:
    """
    Orchestrate synonym suggestion → approval → YAML update workflow.
    """

    def __init__(
        self,
        suggester: GPT4SynonymSuggester,
        repository: SynonymRepository,
        yaml_updater: YAMLConfigUpdater
    ):
        self.suggester = suggester
        self.repository = repository
        self.yaml_updater = yaml_updater
        self.logger = logging.getLogger(__name__)

    async def batch_suggest(
        self,
        terms: list[str],
        use_database_context: bool = True
    ) -> dict[str, int]:
        """
        Batch process synonym suggestions voor multiple terms.

        Args:
            terms: List van termen om te processen
            use_database_context: Haal context op uit database indien beschikbaar

        Returns:
            Dict met statistics: {'processed': N, 'suggestions_created': M}
        """
        stats = {'processed': 0, 'suggestions_created': 0}

        for term in terms:
            self.logger.info(f"Processing term: {term}")

            # Haal context op uit database indien beschikbaar
            if use_database_context:
                context = await self._get_database_context(term)
            else:
                context = {}

            # Generate suggestions
            suggestions = await self.suggester.suggest_synonyms(
                term=term,
                definitie=context.get('definitie'),
                juridische_context=context.get('juridische_context'),
                organisatorische_context=context.get('organisatorische_context'),
                wettelijke_basis=context.get('wettelijke_basis')
            )

            # Save suggestions voor human review
            for suggestion in suggestions:
                await self.repository.save_suggestion(
                    hoofdterm=term,
                    synoniem=suggestion.term,
                    confidence=suggestion.confidence,
                    rationale=suggestion.rationale,
                    status='pending'
                )
                stats['suggestions_created'] += 1

            stats['processed'] += 1

        self.logger.info(
            f"Batch processing complete: {stats['processed']} terms, "
            f"{stats['suggestions_created']} suggestions created"
        )

        return stats

    async def approve_synonym(
        self,
        suggestion_id: int,
        curator_id: str
    ) -> None:
        """
        Approve een synonym suggestion en update YAML config.

        Args:
            suggestion_id: Database ID van suggestion
            curator_id: ID van curator die approveert
        """
        # Haal suggestion op
        suggestion = await self.repository.get_suggestion(suggestion_id)

        # Update status in database
        await self.repository.update_status(
            suggestion_id=suggestion_id,
            status='approved',
            reviewed_by=curator_id
        )

        # Update YAML config
        await self.yaml_updater.add_synonym(
            hoofdterm=suggestion.hoofdterm,
            synoniem=suggestion.synoniem
        )

        self.logger.info(
            f"Approved synonym: {suggestion.synoniem} for {suggestion.hoofdterm} "
            f"(curator: {curator_id})"
        )

    async def reject_synonym(
        self,
        suggestion_id: int,
        curator_id: str,
        reason: str
    ) -> None:
        """
        Reject een synonym suggestion (met feedback voor learning).

        Args:
            suggestion_id: Database ID van suggestion
            curator_id: ID van curator die reject
            reason: Reden voor rejection (gebruikt voor prompt improvement)
        """
        await self.repository.update_status(
            suggestion_id=suggestion_id,
            status='rejected',
            reviewed_by=curator_id,
            rejection_reason=reason
        )

        self.logger.info(
            f"Rejected suggestion {suggestion_id}: {reason} "
            f"(curator: {curator_id})"
        )

    async def _get_database_context(self, term: str) -> dict:
        """Haal context op uit database voor een term."""
        # Query database voor definitie + context
        query = """
        SELECT definitie, juridische_context, organisatorische_context, wettelijke_basis
        FROM definities
        WHERE begrip = ?
        LIMIT 1
        """

        # Execute query (implementation depends on repository pattern)
        result = await self.repository.execute_query(query, (term,))

        if result:
            return {
                'definitie': result['definitie'],
                'juridische_context': json.loads(result['juridische_context']),
                'organisatorische_context': json.loads(result['organisatorische_context']),
                'wettelijke_basis': json.loads(result['wettelijke_basis'])
            }

        return {}

# =======================
# Streamlit Review UI
# =======================

def render_synonym_review_ui():
    """
    Streamlit UI voor curator approval van synonym suggestions.

    Features:
    - List pending suggestions
    - Approve/reject buttons
    - Rationale display
    - Bulk operations
    - Statistics dashboard
    """
    st.title("✅ Synoniemen Review Dashboard")

    # Initialize services
    workflow = get_synonym_workflow()  # Dependency injection

    # Sidebar: Statistics
    with st.sidebar:
        st.header("📊 Statistics")
        stats = workflow.repository.get_stats()
        st.metric("Pending Review", stats['pending'])
        st.metric("Approved", stats['approved'])
        st.metric("Rejected", stats['rejected'])
        st.metric("Approval Rate", f"{stats['approval_rate']:.1%}")

    # Main area: Review interface
    st.header("Pending Suggestions")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        filter_term = st.text_input("Filter by hoofdterm", "")
    with col2:
        min_confidence = st.slider("Min confidence", 0.0, 1.0, 0.6)

    # Load pending suggestions
    suggestions = workflow.repository.get_pending_suggestions(
        hoofdterm_filter=filter_term,
        min_confidence=min_confidence
    )

    if not suggestions:
        st.info("🎉 No pending suggestions! All caught up.")
        return

    # Render suggestions
    for suggestion in suggestions:
        with st.expander(
            f"**{suggestion.hoofdterm}** → {suggestion.synoniem} "
            f"(confidence: {suggestion.confidence:.2f})",
            expanded=False
        ):
            # Rationale
            st.write("**Rationale:**")
            st.info(suggestion.rationale)

            # Context (if available)
            if suggestion.context:
                st.write("**Context:**")
                st.json(suggestion.context)

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Approve", key=f"approve_{suggestion.id}"):
                    workflow.approve_synonym(
                        suggestion_id=suggestion.id,
                        curator_id=st.session_state.user_id
                    )
                    st.success(f"Approved: {suggestion.synoniem}")
                    st.rerun()

            with col2:
                if st.button("❌ Reject", key=f"reject_{suggestion.id}"):
                    reason = st.text_input(
                        "Rejection reason",
                        key=f"reason_{suggestion.id}"
                    )
                    if reason:
                        workflow.reject_synonym(
                            suggestion_id=suggestion.id,
                            curator_id=st.session_state.user_id,
                            reason=reason
                        )
                        st.warning(f"Rejected: {suggestion.synoniem}")
                        st.rerun()

            with col3:
                if st.button("✏️ Edit", key=f"edit_{suggestion.id}"):
                    edited_term = st.text_input(
                        "Edit synonym",
                        value=suggestion.synoniem,
                        key=f"edit_input_{suggestion.id}"
                    )
                    if edited_term != suggestion.synoniem:
                        workflow.repository.update_suggestion(
                            suggestion_id=suggestion.id,
                            synoniem=edited_term
                        )
                        st.success(f"Updated to: {edited_term}")
                        st.rerun()

    # Bulk operations
    st.divider()
    st.subheader("Bulk Operations")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Approve All High-Confidence (>0.9)"):
            high_conf_suggestions = [
                s for s in suggestions if s.confidence > 0.9
            ]
            for s in high_conf_suggestions:
                workflow.approve_synonym(s.id, st.session_state.user_id)
            st.success(f"Approved {len(high_conf_suggestions)} high-confidence suggestions")
            st.rerun()

    with col2:
        if st.button("❌ Reject All Low-Confidence (<0.65)"):
            low_conf_suggestions = [
                s for s in suggestions if s.confidence < 0.65
            ]
            for s in low_conf_suggestions:
                workflow.reject_synonym(
                    s.id,
                    st.session_state.user_id,
                    reason="Low confidence (auto-rejected)"
                )
            st.warning(f"Rejected {len(low_conf_suggestions)} low-confidence suggestions")
            st.rerun()

# =======================
# Usage Example
# =======================

async def main():
    """Example: Generate synonym suggestions voor database termen."""

    # Initialize services
    ai_service = AIServiceV2()
    suggester = GPT4SynonymSuggester(ai_service)
    repository = SynonymRepository("data/definities.db")
    yaml_updater = YAMLConfigUpdater("config/juridische_synoniemen.yaml")

    workflow = SynonymWorkflow(suggester, repository, yaml_updater)

    # Batch suggest voor alle database termen
    all_terms = await repository.get_all_unique_terms()

    print(f"Processing {len(all_terms)} terms...")

    stats = await workflow.batch_suggest(
        terms=all_terms,
        use_database_context=True
    )

    print(f"✅ Complete! {stats['suggestions_created']} suggestions created")
    print("Review suggestions in Streamlit UI")

# Run
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Measurement & Success Criteria

### Metrics to Track

**Coverage Metrics**:
- Aantal unieke termen met synoniemen (target: 150+)
- Gemiddeld aantal synoniemen per term (target: 3-5)
- % database termen met synoniemen (target: 80%)

**Quality Metrics**:
- Precision (approved / total suggested) - target: 80%+
- Recall (synoniemen gevonden / alle mogelijke synoniemen) - moeilijk te meten
- Curator review time per suggestion (target: <30 sec)

**Impact Metrics**:
- Web lookup coverage verbetering (80% → 90%)
- Wikipedia fallback success rate (15% → 35%)
- SRU synonym query hit rate (target: 25%)

### Quality Gates

**Before Deployment**:
1. Manual review van 20 random suggestions (precision check)
2. Curator approval van minimum 50 suggestions (workflow validation)
3. A/B test: handmatige vs GPT-4 synoniemen (quality comparison)

**During Operation**:
1. Weekly curator review sessions (max 30 min)
2. Monthly precision audit (sample 20 random approved synoniemen)
3. Quarterly feedback loop: rejected synoniemen → prompt improvement

---

## Risk Mitigation

### Risk 1: GPT-4 Hallucinations

**Mitigation**:
- Human approval vereist (geen auto-commit)
- Low temperature (0.3) voor factual output
- Confidence scoring + rationale vereist
- Curator kan rationale valideren

### Risk 2: Maintenance Burden

**Mitigation**:
- Batch processing (niet real-time)
- Bulk operations in UI (approve/reject multiple)
- High-confidence auto-approve optie (>0.95)
- Weekly review sessions (max 30 min)

### Risk 3: YAML Config Corruption

**Mitigation**:
- Automated backup voor elke update
- YAML validation na elke write
- Version control (git commit bij updates)
- Rollback functie

### Risk 4: API Cost Overruns

**Mitigation**:
- Batch processing limiet (max 50 terms per dag)
- Cost monitoring dashboard
- Cache GPT-4 responses (avoid re-processing)
- Fallback naar Wikipedia bij budget limit

---

## Next Steps

### Immediate Actions (This Week)

1. **Stakeholder Alignment**
   - Review analysis met product owner
   - Approve recommended strategy (Benadering 2)
   - Set budget for GPT-4 API (~$5 total)

2. **Prototype** (Day 1-2)
   - Implement GPT4SynonymSuggester
   - Test prompt with 5 sample terms
   - Validate output quality

3. **Decision Point** (Day 3)
   - GO/NO-GO based on prototype results
   - If GO: proceed with full implementation
   - If NO-GO: fallback to Benadering 1 (Wikipedia)

### Implementation Timeline

**Week 1-2**: Wikipedia Redirects (Quick Win)
**Week 3-4**: GPT-4 Suggest + Approve (Primary)
**Week 5-6**: Database Mining (Validation)

**Total Effort**: 15-18 days (~3-4 weeks)

---

## Conclusion

**Recommended Strategy**: **Hybride GPT-4 Suggest + Human Approve (Benadering 2)**

**Rationale**:
- ✅ Beste balans tussen kwaliteit, schaalbaarheid en onderhoudsbaarheid
- ✅ Context-aware (gebruikt database definities)
- ✅ Human-in-the-loop voorkomt hallucinations
- ✅ Feedback loop voor continuous improvement
- ✅ Zeer kostenefficiënt (~$3 one-time, ~$0.30/maand)
- ✅ Hergebruikt bestaande GPT-4 integratie

**Quick Win**: Start met Wikipedia Redirects (Benadering 1) voor 30-40 synoniemen in Week 1-2.

**Long-term**: Supplement met Database Mining (Benadering 5) voor quality assurance en auto-detection van missing synoniemen.

---

**Document Status**: ✅ Complete
**Last Updated**: 8 oktober 2025
**Author**: Claude Code (DefinitieAgent AI Assistant)
**Review Status**: Pending stakeholder review
