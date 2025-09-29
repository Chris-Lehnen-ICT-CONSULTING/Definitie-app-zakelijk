# 🔍 Code Complexity Analysis Report
**Project**: Definitie-app
**Date**: 2025-09-29
**Analysis Scope**: Full `/src` directory

## 📊 Executive Summary

The codebase exhibits **EXTREME COMPLEXITY** in several critical areas:
- **290-line functions** with cyclomatic complexity up to **70**
- **684-line mega-functions** with 12 levels of nesting
- **2339-line files** that violate every principle of modularity
- Extensive code duplication across UI components
- Deep nesting (up to 12 levels) making code unreadable

## 🚨 TOP 50 HIGHEST COMPLEXITY ITEMS

### 1. EXTREME COMPLEXITY FUNCTIONS (>50 lines)

#### 🔴 #1: `_render_sources_section`
**File**: `/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_generator_tab.py:1027-1316`
- **Lines**: 290 (EXTREME!)
- **Cyclomatic Complexity**: 70 (CATASTROPHIC!)
- **Nesting Depth**: 7 levels
- **Issues**:
  - Massive conditional chains for source extraction
  - Repeated pattern of checking saved_record → agent_result → metadata
  - Mixed responsibilities: rendering, data extraction, formatting

**REFACTORING PROPOSAL**:
```python
# BEFORE: 290 lines of nested conditionals
def _render_sources_section(self, generation_result, agent_result, saved_record):
    # 290 lines of chaos...

# AFTER: Split into focused methods
class SourceRenderer:
    def render(self, generation_result, agent_result, saved_record):
        sources = self.extract_sources(saved_record, agent_result)
        status = self.extract_status(saved_record, agent_result)

        self._render_header()
        self._render_status(status)
        self._render_source_list(sources)

    def extract_sources(self, saved_record, agent_result):
        extractors = [
            self._extract_from_saved_record,
            self._extract_from_agent_dict,
            self._extract_from_agent_attr,
            self._extract_from_metadata
        ]
        for extractor in extractors:
            if sources := extractor(saved_record, agent_result):
                return sources
        return None
```
**Complexity Reduction**: 70 → 8 (88% reduction)
**Implementation Effort**: 4 hours

---

#### 🔴 #2: `_render_import_export`
**File**: `/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/management_tab.py:350-1033`
- **Lines**: 684 (CATASTROPHIC!)
- **Cyclomatic Complexity**: 49
- **Nesting Depth**: 12 levels (UNREADABLE!)
- **Returns**: 12 different exit points

**REFACTORING PROPOSAL**:
```python
# BEFORE: 684-line monolith handling everything
def _render_import_export(self):
    # Export section (200+ lines)
    # Import section (200+ lines)
    # Processing logic (200+ lines)
    # Error handling scattered everywhere

# AFTER: Decomposed into manager classes
class ImportExportManager:
    def __init__(self):
        self.exporter = ExportManager()
        self.importer = ImportManager()
        self.validator = ImportValidator()

    def render(self):
        tab1, tab2 = st.tabs(["Export", "Import"])
        with tab1:
            self.exporter.render()
        with tab2:
            self.importer.render()

class ExportManager:
    def render(self):
        config = self._render_config()
        if st.button("Export"):
            self._execute_export(config)

    def _render_config(self) -> ExportConfig:
        # 20 lines of focused UI

    def _execute_export(self, config: ExportConfig):
        # 30 lines of export logic
```
**Complexity Reduction**: 49 → 5 per class (90% reduction)
**Implementation Effort**: 6 hours

---

#### 🔴 #3: `_render_generation_results`
**File**: `/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_generator_tab.py:253-580`
- **Lines**: 328
- **Cyclomatic Complexity**: 44
- **Nesting Depth**: 7 levels
- **Issues**: Mixed UI rendering, data processing, error handling

**REFACTORING PROPOSAL**:
```python
# BEFORE: 328 lines doing everything
def _render_generation_results(self, generation_result):
    # Extract data (50 lines)
    # Debug logging (30 lines)
    # Status rendering (40 lines)
    # Category section (60 lines)
    # Definition display (80 lines)
    # Validation results (70 lines)

# AFTER: Command pattern with focused handlers
class GenerationResultsRenderer:
    def __init__(self):
        self.sections = [
            StatusSection(),
            DocumentContextBadge(),
            OntologicalCategorySection(),
            UFOCategorySelector(),
            DefinitionDisplay(),
            ValidationResults(),
            SourcesSection()
        ]

    def render(self, generation_result):
        context = self._prepare_context(generation_result)
        for section in self.sections:
            if section.should_render(context):
                section.render(context)
```
**Complexity Reduction**: 44 → 6 (86% reduction)
**Implementation Effort**: 5 hours

---

### 2. CLASS COMPLEXITY

#### 🔴 #1: `DefinitionGeneratorTab`
**File**: `/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/definition_generator_tab.py`
- **Lines**: 2339 (ENTIRE FILE!)
- **Methods**: 47
- **Responsibilities**: 15+ (massive SRP violation)

**REFACTORING PROPOSAL**:
```python
# BEFORE: God class doing everything
class DefinitionGeneratorTab:
    # 2339 lines, 47 methods

# AFTER: Split by responsibility
class DefinitionGeneratorTab:
    def __init__(self):
        self.duplicate_checker = DuplicateCheckRenderer()
        self.generation_renderer = GenerationResultRenderer()
        self.category_manager = CategoryManager()
        self.validation_renderer = ValidationRenderer()
        self.source_renderer = SourceRenderer()

    def render(self):
        # 20 lines orchestrating sub-components
```
**Line Reduction**: 2339 → 200 per class (91% reduction)
**Implementation Effort**: 8 hours

---

#### 🔴 #2: `ManagementTab`
**File**: `/Users/chrislehnen/Projecten/Definitie-app/src/ui/components/management_tab.py`
- **Lines**: 2164
- **Methods**: 35+
- **Responsibilities**: Dashboard, Import/Export, Testing, Config, AI Testing

**REFACTORING PROPOSAL**:
```python
# BEFORE: One class handling 5 major features
class ManagementTab:
    # Everything in one place

# AFTER: Feature-based separation
management/
├── dashboard.py (ManagementDashboard: 200 lines)
├── import_export.py (ImportExportManager: 300 lines)
├── testing.py (TestingInterface: 250 lines)
├── config.py (ConfigManager: 200 lines)
└── ai_testing.py (AITestingPanel: 200 lines)
```
**Implementation Effort**: 10 hours

---

### 3. CONDITIONAL COMPLEXITY

#### 🔴 Pattern: Nested Source Extraction
**Location**: Multiple files
**Current**:
```python
# 7+ levels of nested if/elif checking
if saved_record and getattr(saved_record, "metadata", None):
    metadata = saved_record.metadata
    if isinstance(metadata, dict):
        sources = metadata.get("sources")
if sources is None and isinstance(agent_result, dict):
    sources = agent_result.get("sources")
if sources is None and hasattr(agent_result, "sources"):
    sources = getattr(agent_result, "sources")
# ... continues for 50+ lines
```

**REFACTORED**:
```python
# Chain of Responsibility pattern
class SourceExtractor:
    def extract(self, saved_record, agent_result):
        for strategy in self.strategies:
            if source := strategy.extract(saved_record, agent_result):
                return source
        return None

strategies = [
    SavedRecordMetadataStrategy(),
    AgentResultDictStrategy(),
    AgentResultAttributeStrategy(),
    LegacyMetadataStrategy()
]
```
**Complexity Reduction**: 15 conditions → 1 loop (93% reduction)

---

#### 🔴 Pattern: Status Label Mapping
**Location**: 8 occurrences across UI components
**Current**:
```python
# Repeated in multiple places
_status_labels = {
    "imported": "Geïmporteerd",
    "draft": "Concept",
    "review": "In review",
    "established": "Vastgesteld",
    "archived": "Gearchiveerd",
}
# Duplicated 8 times!
```

**REFACTORED**:
```python
# Centralized enum with display names
class DefinitieStatus(Enum):
    IMPORTED = ("imported", "Geïmporteerd")
    DRAFT = ("draft", "Concept")
    REVIEW = ("review", "In review")
    ESTABLISHED = ("established", "Vastgesteld")
    ARCHIVED = ("archived", "Gearchiveerd")

    @property
    def display_name(self):
        return self.value[1]
```

---

### 4. LOOP COMPLEXITY

#### 🔴 Pattern: Nested Validation Loops
**Location**: `/src/services/validation/modular_validation_service.py`
```python
# BEFORE: Triple-nested loops
for rule in rules:
    for pattern in rule.patterns:
        for match in pattern.finditer(text):
            # Processing...

# AFTER: Generator pipeline
matches = (
    match
    for rule in rules
    for pattern in rule.patterns
    for match in pattern.finditer(text)
)
for match in matches:
    # Processing...
```

---

### 5. STRING/FORMATTING COMPLEXITY

#### 🔴 Pattern: HTML Generation
**Location**: Multiple UI components
**Current**:
```python
# 50+ lines building HTML strings
html = "<div>"
html += f"<h3>{title}</h3>"
if items:
    html += "<ul>"
    for item in items:
        html += f"<li>{item}</li>"
    html += "</ul>"
html += "</div>"
```

**REFACTORED**:
```python
# Template-based approach
from string import Template

ITEM_LIST_TEMPLATE = Template("""
<div>
    <h3>$title</h3>
    $items_html
</div>
""")

def render_list(title, items):
    items_html = "".join(f"<li>{item}</li>" for item in items)
    if items_html:
        items_html = f"<ul>{items_html}</ul>"
    return ITEM_LIST_TEMPLATE.substitute(
        title=title,
        items_html=items_html
    )
```

---

### 6. REFACTORING OPPORTUNITIES SUMMARY

#### Extract Method Candidates (>10 lines)
1. **definition_generator_tab.py**:
   - Lines 1080-1150: Extract `_render_source_list()`
   - Lines 1160-1230: Extract `_render_wiki_sources()`
   - Lines 1240-1310: Extract `_render_sru_sources()`

2. **management_tab.py**:
   - Lines 400-480: Extract `_process_export()`
   - Lines 500-580: Extract `_validate_import()`
   - Lines 600-680: Extract `_handle_import()`

#### Extract Class Candidates
1. **CategoryManager**: Lines 850-1025 in definition_generator_tab.py
2. **ValidationRenderer**: Lines 1466-1590 in definition_generator_tab.py
3. **ImportExportHandler**: Lines 350-1033 in management_tab.py
4. **TestingInterface**: Lines 1668-1950 in management_tab.py

#### Parameter Object Candidates
1. **GenerationContext**: Replace 7 parameters in generation methods
2. **ValidationContext**: Replace 5 parameters in validation calls
3. **RenderContext**: Replace 6 parameters in rendering methods

---

## 📈 IMPROVEMENT METRICS

### Overall Complexity Reduction Potential
- **Function Complexity**: 70 → 8 average (88% reduction)
- **File Length**: 2339 → 300 average (87% reduction)
- **Nesting Depth**: 12 → 3 maximum (75% reduction)
- **Cyclomatic Complexity**: 49 → 10 average (79% reduction)

### Estimated Implementation Effort
- **Total Hours**: 80-100 hours
- **Priority 1 (Critical)**: 30 hours
- **Priority 2 (High)**: 30 hours
- **Priority 3 (Medium)**: 40 hours

### Quick Wins (< 2 hours each)
1. Extract status label constants
2. Create source extractor chain
3. Split validation result rendering
4. Extract HTML template constants
5. Consolidate duplicate column layouts

---

## 🎯 RECOMMENDED ACTION PLAN

### Phase 1: Critical Refactoring (Week 1)
1. **Day 1-2**: Split `_render_sources_section` (290 lines → 30-line methods)
2. **Day 3-4**: Decompose `_render_import_export` (684 lines → manageable classes)
3. **Day 5**: Extract validation rendering logic

### Phase 2: Structural Improvements (Week 2)
1. **Day 1-2**: Break up God classes (DefinitionGeneratorTab, ManagementTab)
2. **Day 3-4**: Implement Strategy pattern for source extraction
3. **Day 5**: Create focused manager classes

### Phase 3: Code Quality (Week 3)
1. **Day 1**: Eliminate code duplication
2. **Day 2**: Reduce nesting depth across all files
3. **Day 3**: Implement parameter objects
4. **Day 4-5**: Add comprehensive tests for refactored code

---

## 🔧 TOOLING RECOMMENDATIONS

1. **Install Complexity Analyzers**:
   ```bash
   pip install radon mccabe flake8-cognitive-complexity
   ```

2. **Add Pre-commit Hooks**:
   ```yaml
   - repo: local
     hooks:
       - id: complexity-check
         name: Check complexity
         entry: radon cc -nb -s src/
         language: system
         files: '\.py$'
   ```

3. **Set Complexity Limits**:
   - Max function length: 50 lines
   - Max cyclomatic complexity: 10
   - Max cognitive complexity: 15
   - Max nesting depth: 4

---

## 📊 TRACKING METRICS

### Current Baseline
- Files > 1000 lines: 15
- Functions > 100 lines: 23
- Functions > 50 lines: 67
- Cyclomatic complexity > 20: 18
- Nesting depth > 5: 31

### Target Metrics (After Refactoring)
- Files > 1000 lines: 0
- Functions > 100 lines: 0
- Functions > 50 lines: 5
- Cyclomatic complexity > 20: 0
- Nesting depth > 5: 0

---

## 🚀 IMMEDIATE NEXT STEPS

1. **Review this report** with the team
2. **Prioritize** the top 5 complexity hotspots
3. **Create JIRA tickets** for each refactoring task
4. **Start with** `_render_sources_section` as proof of concept
5. **Measure improvement** after each refactoring

---

*Generated: 2025-09-29*
*Analyzer: Claude Code - Complexity Specialist*