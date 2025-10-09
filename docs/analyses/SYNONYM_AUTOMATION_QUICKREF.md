# Synonym Automation - Developer Quick Reference

**Last Updated**: 8 oktober 2025
**Full Analysis**: `docs/analyses/SYNONYM_AUTOMATION_ANALYSIS.md`

---

## TL;DR

**Recommended**: GPT-4 Suggest + Human Approve workflow
**Cost**: $3 one-time, $0.30/month
**Timeline**: 5-8 days implementation
**Expected Impact**: 50 → 150 termen, 184 → 450 synoniemen

---

## Implementation Checklist

### Phase 1: GPT-4 Suggester Service (Days 1-2)

```python
# File: src/services/synonym_automation/gpt4_suggester.py

class GPT4SynonymSuggester:
    PROMPT_TEMPLATE = """
    Je bent een expert in Nederlands juridisch taalgebruik.
    Genereer synoniemen voor: {term}

    Context: {context}
    Definitie: {definitie}

    Output (JSON):
    {{"synoniemen": [{{"term": "...", "confidence": 0.95, "rationale": "..."}}]}}
    """

    async def suggest_synonyms(
        self,
        term: str,
        definitie: str = None,
        context: list[str] = None
    ) -> list[SynonymSuggestion]:
        # 1. Build prompt
        # 2. Call GPT-4 (temp=0.3, max_tokens=500)
        # 3. Parse JSON response
        # 4. Filter low confidence (<0.6)
        # 5. Return suggestions
```

**Dependencies**: `AIServiceV2` (already in project)

---

### Phase 2: Database Schema (Day 3)

```sql
-- File: src/database/migrations/XXX_add_synonym_suggestions.sql

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

CREATE INDEX idx_suggestions_status ON synonym_suggestions(status);
CREATE INDEX idx_suggestions_hoofdterm ON synonym_suggestions(hoofdterm);
```

**Migration**: `python src/database/migrate_database.py`

---

### Phase 3: Repository Layer (Day 4)

```python
# File: src/repositories/synonym_repository.py

class SynonymRepository:
    async def save_suggestion(
        self, hoofdterm: str, synoniem: str,
        confidence: float, rationale: str
    ) -> int:
        """Save suggestion voor human review."""

    async def get_pending_suggestions(
        self, hoofdterm_filter: str = None,
        min_confidence: float = 0.0
    ) -> list[SynonymSuggestion]:
        """Get all pending suggestions."""

    async def update_status(
        self, suggestion_id: int, status: str,
        reviewed_by: str, rejection_reason: str = None
    ) -> None:
        """Update suggestion status."""
```

---

### Phase 4: YAML Auto-Update (Day 5)

```python
# File: src/services/synonym_automation/yaml_updater.py

class YAMLConfigUpdater:
    def __init__(self, yaml_path: str = "config/juridische_synoniemen.yaml"):
        self.yaml_path = Path(yaml_path)

    async def add_synonym(self, hoofdterm: str, synoniem: str) -> None:
        # 1. Backup existing YAML
        # 2. Load current data
        # 3. Add synoniem (normalize hoofdterm: spaces → underscores)
        # 4. Validate (no duplicates)
        # 5. Write back
        # 6. Git commit (optional)
```

**Backup strategy**: `config/juridische_synoniemen.yaml.backup.YYYYMMDD-HHMMSS`

---

### Phase 5: Streamlit Review UI (Days 6-7)

```python
# File: src/ui/tabs/synonym_review.py

def render_synonym_review_tab():
    st.title("✅ Synoniemen Review")

    # Sidebar: Statistics
    with st.sidebar:
        stats = get_stats()
        st.metric("Pending", stats['pending'])
        st.metric("Approved", stats['approved'])
        st.metric("Approval Rate", f"{stats['approval_rate']:.1%}")

    # Main: Review interface
    suggestions = load_pending_suggestions(
        min_confidence=st.slider("Min confidence", 0.0, 1.0, 0.6)
    )

    for suggestion in suggestions:
        with st.expander(f"{suggestion.hoofdterm} → {suggestion.synoniem}"):
            st.info(suggestion.rationale)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve"):
                    approve_synonym(suggestion.id)
            with col2:
                if st.button("❌ Reject"):
                    reject_synonym(suggestion.id)
            with col3:
                if st.button("✏️ Edit"):
                    edit_synonym(suggestion.id)
```

**Navigation**: Add to `src/ui/tabs/__init__.py` → `TABS` dict

---

### Phase 6: Workflow Orchestration (Day 8)

```python
# File: src/services/synonym_automation/workflow.py

class SynonymWorkflow:
    def __init__(
        self,
        suggester: GPT4SynonymSuggester,
        repository: SynonymRepository,
        yaml_updater: YAMLConfigUpdater
    ):
        self.suggester = suggester
        self.repository = repository
        self.yaml_updater = yaml_updater

    async def batch_suggest(self, terms: list[str]) -> dict:
        """Batch process synonym suggestions."""
        for term in terms:
            # Get context from database
            context = await self._get_db_context(term)

            # Generate suggestions
            suggestions = await self.suggester.suggest_synonyms(
                term=term,
                definitie=context.get('definitie'),
                context=context.get('juridische_context')
            )

            # Save for review
            for s in suggestions:
                await self.repository.save_suggestion(
                    hoofdterm=term,
                    synoniem=s.term,
                    confidence=s.confidence,
                    rationale=s.rationale
                )

    async def approve_synonym(self, suggestion_id: int, curator_id: str):
        """Approve + update YAML."""
        suggestion = await self.repository.get_suggestion(suggestion_id)

        # Update DB status
        await self.repository.update_status(
            suggestion_id, 'approved', curator_id
        )

        # Update YAML
        await self.yaml_updater.add_synonym(
            suggestion.hoofdterm, suggestion.synoniem
        )
```

---

## Batch Processing Script

```bash
# File: scripts/batch_suggest_synonyms.py

python scripts/batch_suggest_synonyms.py \
    --source database \           # or: file, manual
    --terms-file terms.txt \      # Optional: specific terms
    --max-terms 50 \              # Batch limit
    --min-confidence 0.6          # Filter threshold
```

**Output**: Suggestions saved in DB → review in UI

---

## Testing Strategy

### Unit Tests

```python
# tests/services/synonym_automation/test_gpt4_suggester.py

@pytest.mark.asyncio
async def test_suggest_synonyms_with_context():
    suggester = GPT4SynonymSuggester(mock_ai_service)

    suggestions = await suggester.suggest_synonyms(
        term="voorlopige hechtenis",
        definitie="Tijdelijke vrijheidsbeneming...",
        context=["Sv", "strafrecht"]
    )

    assert len(suggestions) > 0
    assert all(s.confidence >= 0.6 for s in suggestions)
    assert all(s.rationale for s in suggestions)
```

### Integration Tests

```python
# tests/integration/test_synonym_workflow.py

@pytest.mark.integration
async def test_end_to_end_workflow():
    workflow = SynonymWorkflow(...)

    # 1. Batch suggest
    stats = await workflow.batch_suggest(["verdachte", "vonnis"])
    assert stats['suggestions_created'] > 0

    # 2. Approve
    suggestions = await workflow.repository.get_pending_suggestions()
    await workflow.approve_synonym(suggestions[0].id, "curator_1")

    # 3. Verify YAML updated
    yaml_data = load_yaml_config()
    assert suggestions[0].synoniem in yaml_data['verdachte']
```

---

## Configuration

```yaml
# config/web_lookup_defaults.yaml

web_lookup:
  synonyms:
    automation:
      enabled: true
      gpt4:
        model: "gpt-4-turbo"
        temperature: 0.3
        max_tokens: 500
        max_synonyms_per_term: 8
        min_confidence: 0.6
      batch:
        max_terms_per_run: 50
        daily_limit: 100
      approval:
        auto_approve_threshold: 0.95  # Auto-approve if confidence > 0.95
        require_rationale: true
```

---

## API Cost Monitoring

```python
# File: src/services/synonym_automation/cost_tracker.py

class CostTracker:
    def __init__(self):
        self.costs = []

    def track_request(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4-turbo"
    ):
        # GPT-4-turbo pricing (as of Oct 2025)
        PRICES = {
            "gpt-4-turbo": {
                "input": 0.01 / 1000,   # $0.01 per 1K tokens
                "output": 0.03 / 1000   # $0.03 per 1K tokens
            }
        }

        cost = (
            input_tokens * PRICES[model]["input"] +
            output_tokens * PRICES[model]["output"]
        )

        self.costs.append({
            'timestamp': datetime.now(),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost
        })

    def get_daily_cost(self) -> float:
        today = datetime.now().date()
        return sum(
            c['cost'] for c in self.costs
            if c['timestamp'].date() == today
        )
```

**Dashboard**: Integrate in Streamlit sidebar

---

## Troubleshooting

### Issue: GPT-4 returns malformed JSON

**Solution**: Add JSON validation + retry logic

```python
async def suggest_synonyms(self, term: str) -> list[SynonymSuggestion]:
    for attempt in range(3):  # Max 3 retries
        try:
            response = await self.ai_service.generate(prompt)
            suggestions = self._parse_json(response)
            return suggestions
        except json.JSONDecodeError:
            if attempt == 2:
                raise
            continue  # Retry
```

---

### Issue: Low-quality suggestions

**Solution**: Improve prompt with examples

```python
PROMPT_TEMPLATE = """
...

VOORBEELDEN VAN GOEDE SYNONIEMEN:
- "voorlopige hechtenis" → "voorarrest", "bewaring" (hoge confidence)
- "onherroepelijk" → "kracht van gewijsde", "rechtskracht"

VOORBEELDEN VAN SLECHTE SYNONIEMEN (VERMIJD):
- "voorlopige hechtenis" → "gevangenis" (te algemeen)
- "verdachte" → "crimineel" (pejoratief, niet juridisch)

...
"""
```

---

### Issue: YAML corruption

**Solution**: Validate before commit

```python
async def add_synonym(self, hoofdterm: str, synoniem: str):
    # 1. Backup
    self._create_backup()

    # 2. Load + modify
    data = self._load_yaml()
    data[hoofdterm].append(synoniem)

    # 3. Validate
    try:
        yaml.safe_load(yaml.dump(data))
    except yaml.YAMLError as e:
        self._restore_backup()
        raise ValueError(f"YAML validation failed: {e}")

    # 4. Write
    self._write_yaml(data)
```

---

## Performance Optimization

### Cache GPT-4 Responses

```python
class CachedGPT4Suggester(GPT4SynonymSuggester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}  # {term: suggestions}

    async def suggest_synonyms(self, term: str, **kwargs) -> list[SynonymSuggestion]:
        cache_key = (term, frozenset(kwargs.items()))

        if cache_key in self.cache:
            return self.cache[cache_key]

        suggestions = await super().suggest_synonyms(term, **kwargs)
        self.cache[cache_key] = suggestions

        return suggestions
```

---

## Monitoring & Alerts

```python
# File: src/services/synonym_automation/monitoring.py

class SynonymWorkflowMonitor:
    def check_daily_limits(self):
        """Alert if daily API limits exceeded."""
        daily_cost = cost_tracker.get_daily_cost()
        if daily_cost > 1.0:  # $1 daily limit
            send_alert(f"Daily cost exceeded: ${daily_cost:.2f}")

    def check_approval_rate(self):
        """Alert if approval rate drops below threshold."""
        rate = repository.get_approval_rate(last_n_days=7)
        if rate < 0.7:  # 70% threshold
            send_alert(f"Low approval rate: {rate:.1%}")
```

**Cron**: Run daily checks via `scripts/monitor_synonyms.py`

---

## Quick Commands

```bash
# Generate suggestions for all database terms
python scripts/batch_suggest_synonyms.py --source database

# Generate for specific terms
python scripts/batch_suggest_synonyms.py --terms "verdachte,vonnis,cassatie"

# Export pending suggestions to CSV
python scripts/export_suggestions.py --status pending --output pending.csv

# Backup YAML config
cp config/juridische_synoniemen.yaml config/juridische_synoniemen.yaml.backup.$(date +%Y%m%d)

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/juridische_synoniemen.yaml'))"

# Monitor costs
python scripts/monitor_synonyms.py --check-costs

# Generate quality report
python scripts/generate_synonym_quality_report.py --output docs/reports/synonym_quality.md
```

---

## Resources

- **Full Analysis**: `docs/analyses/SYNONYM_AUTOMATION_ANALYSIS.md` (100+ pages)
- **Summary**: `docs/analyses/SYNONYM_AUTOMATION_SUMMARY.md` (executive summary)
- **Current Implementation**: `src/services/web_lookup/synonym_service.py`
- **Config**: `config/juridische_synoniemen.yaml`
- **Tests**: `tests/services/web_lookup/test_synonym_service.py`

---

**Status**: Ready for implementation
**Estimated Effort**: 5-8 days
**Expected ROI**: 200% more synonyms, 75% less maintenance
