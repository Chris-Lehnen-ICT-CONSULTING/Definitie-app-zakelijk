# Toetsregels Architectuur: Scheiding Toetsing vs. Generatie

## Probleem

De huidige architectuur mengt twee verschillende verantwoordelijkheden:
1. **TOETSING**: Validatie van definities (ongeacht bron: AI, mens, import)
2. **GENERATIE**: Criteria doorgeven aan prompt builder voor AI generatie

Deze vermenging zorgt voor:
- Onduidelijke verantwoordelijkheden
- Moeilijk te testen code
- Inconsistente regeltoepassing
- Beperkte flexibiliteit

## Oplossing: Strikte Scheiding

### 1. ToetsregelValidator (Alleen voor Toetsing)

```
src/validation/
├── toetsregel_validator.py      # Hoofdklasse voor validatie
├── toetsregel_loader.py         # Laadt JSON configs
├── validators/                   # Modulaire validators
│   ├── base_validator.py
│   ├── content_validators.py    # CON-01, CON-02
│   ├── essential_validators.py  # ESS-01 t/m ESS-05
│   ├── integrity_validators.py  # INT-01 t/m INT-08
│   ├── coherence_validators.py  # SAM-01 t/m SAM-08
│   ├── structure_validators.py  # STR-01 t/m STR-09
│   ├── verifiability_validators.py  # VER-01 t/m VER-05
│   └── arai_validators.py       # ARAI01 t/m ARAI06
└── validation_result.py         # Resultaat datastructuur
```

**Verantwoordelijkheden:**
- Laden van alle 46 toetsregels uit JSON
- Valideren van definities tegen regels
- Gedetailleerde feedback genereren
- Score berekening
- GEEN kennis van prompt building

### 2. ToetsregelCriteria (Alleen voor Generatie)

```
src/generation/
├── toetsregel_criteria.py       # Criteria voor prompt building
├── criteria_selector.py         # Selecteert relevante criteria
└── criteria_formatter.py        # Formatteert voor prompts
```

**Verantwoordelijkheden:**
- Selecteren van subset regels voor generatie (TOEGESTANE_TOETSREGELS)
- Vertalen van regels naar prompt instructies
- Formatteren voor GPT consumptie
- GEEN validatie logica

## Implementatie Details

### ToetsregelValidator

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ViolationType(Enum):
    FORBIDDEN_PATTERN = "forbidden_pattern"
    MISSING_ELEMENT = "missing_element"
    STRUCTURE_ISSUE = "structure_issue"
    CLARITY_ISSUE = "clarity_issue"

@dataclass
class ValidationViolation:
    rule_id: str
    rule_name: str
    violation_type: ViolationType
    message: str
    severity: str  # "error", "warning", "info"
    detected_pattern: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationResult:
    definitie: str
    begrip: str
    violations: List[ValidationViolation]
    passed_rules: List[str]
    total_score: float
    per_rule_scores: Dict[str, float]
    
    @property
    def is_valid(self) -> bool:
        return len([v for v in self.violations if v.severity == "error"]) == 0
    
    @property
    def has_warnings(self) -> bool:
        return len([v for v in self.violations if v.severity == "warning"]) > 0

class ToetsregelValidator:
    """Valideert definities tegen toetsregels."""
    
    def __init__(self, rules_dir: str = "config/toetsregels/regels"):
        self.rules = self._load_rules(rules_dir)
        self.validators = self._initialize_validators()
    
    def validate(
        self,
        definitie: str,
        begrip: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Valideert een definitie tegen alle toetsregels.
        
        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context (organisatie, juridisch, etc.)
            
        Returns:
            ValidationResult met alle bevindingen
        """
        violations = []
        passed_rules = []
        per_rule_scores = {}
        
        for rule_id, rule_config in self.rules.items():
            validator = self.validators.get(rule_id)
            if not validator:
                continue
                
            result = validator.validate(definitie, begrip, rule_config, context)
            
            if result.violations:
                violations.extend(result.violations)
            else:
                passed_rules.append(rule_id)
            
            per_rule_scores[rule_id] = result.score
        
        total_score = self._calculate_total_score(per_rule_scores)
        
        return ValidationResult(
            definitie=definitie,
            begrip=begrip,
            violations=violations,
            passed_rules=passed_rules,
            total_score=total_score,
            per_rule_scores=per_rule_scores
        )
```

### ToetsregelCriteria

```python
from typing import List, Dict, Any, Set
from dataclasses import dataclass

# Regels die nuttig zijn voor AI generatie
GENERATION_RELEVANT_RULES = {
    "CON-01", "CON-02",  # Context guidance
    "ESS-01", "ESS-02", "ESS-04", "ESS-05",  # Essentiële elementen
    "INT-01", "INT-02", "INT-03",  # Integriteit
    "STR-01", "STR-02", "STR-03",  # Structuur
    # etc...
}

@dataclass 
class GenerationCriterion:
    rule_id: str
    instruction: str  # Positief geformuleerde instructie voor GPT
    examples: List[str]  # Goede voorbeelden
    priority: str  # Voor volgorde in prompt

class ToetsregelCriteria:
    """Beheert criteria voor definitie generatie."""
    
    def __init__(self, rules_dir: str = "config/toetsregels/regels"):
        self.all_rules = self._load_rules(rules_dir)
        self.generation_rules = self._filter_for_generation()
    
    def get_criteria_for_generation(
        self,
        categorie: str,
        prioriteit: str = "all"
    ) -> List[GenerationCriterion]:
        """
        Haalt criteria op voor definitie generatie.
        
        Args:
            categorie: Ontologische categorie (type, proces, etc.)
            prioriteit: Filter op prioriteit (hoog, all, etc.)
            
        Returns:
            Lijst van GenerationCriterion voor prompt building
        """
        criteria = []
        
        for rule_id, rule_config in self.generation_rules.items():
            if prioriteit != "all" and rule_config.get("prioriteit") != prioriteit:
                continue
                
            criterion = self._convert_to_criterion(rule_id, rule_config)
            criteria.append(criterion)
        
        # Sorteer op prioriteit
        criteria.sort(key=lambda c: (
            0 if c.priority == "hoog" else 1,
            c.rule_id
        ))
        
        return criteria
    
    def _convert_to_criterion(
        self, 
        rule_id: str, 
        rule_config: Dict[str, Any]
    ) -> GenerationCriterion:
        """Converteer regel naar generatie criterium."""
        # Positieve formulering voor GPT
        instruction = self._create_positive_instruction(rule_config)
        
        return GenerationCriterion(
            rule_id=rule_id,
            instruction=instruction,
            examples=rule_config.get("goede_voorbeelden", []),
            priority=rule_config.get("prioriteit", "midden")
        )
    
    def _create_positive_instruction(self, rule_config: Dict[str, Any]) -> str:
        """Creëer positieve instructie uit regel config."""
        # Transformeer uitleg naar positieve instructie
        uitleg = rule_config.get("uitleg", "")
        
        # Voorbeelden van transformaties:
        # "Vermijd X" -> "Gebruik Y in plaats van X"
        # "Niet A" -> "Wel B"
        
        return uitleg  # TODO: Implementeer transformatie logica
```

## Gebruik in de Applicatie

### Voor Toetsing (Validatie)

```python
# In UI of service layer
validator = ToetsregelValidator()
result = validator.validate(
    definitie="Een proces waarbij...",
    begrip="toezicht",
    context={"organisatie": "DJI", "juridisch": "Strafrecht"}
)

if not result.is_valid:
    # Toon errors
    for violation in result.violations:
        if violation.severity == "error":
            st.error(f"{violation.rule_name}: {violation.message}")
```

### Voor Generatie (Prompt Building)

```python
# In prompt builder
criteria_manager = ToetsregelCriteria()
criteria = criteria_manager.get_criteria_for_generation(
    categorie="proces",
    prioriteit="hoog"
)

# Bouw prompt met criteria
prompt_parts = []
for criterion in criteria:
    prompt_parts.append(f"- {criterion.instruction}")
    if criterion.examples:
        prompt_parts.append(f"  Voorbeeld: {criterion.examples[0]}")
```

## Voordelen van deze Architectuur

1. **Single Responsibility**: Elke klasse heeft één duidelijke verantwoordelijkheid
2. **Testbaarheid**: Validatie en generatie kunnen onafhankelijk getest worden
3. **Flexibiliteit**: Verschillende regel sets voor verschillende doeleinden
4. **Uitbreidbaarheid**: Nieuwe validators/criteria eenvoudig toe te voegen
5. **Onderhoudbaarheid**: Duidelijke structuur en scheiding van concerns

## Migratie Strategie

1. **Fase 1**: Implementeer nieuwe ToetsregelValidator naast bestaande code
2. **Fase 2**: Migreer UI/services naar nieuwe validator
3. **Fase 3**: Implementeer ToetsregelCriteria voor prompt building
4. **Fase 4**: Verwijder oude code (core.py, modular_toetser.py)

## Testing Strategie

- Unit tests voor elke validator
- Integration tests voor complete validatie flows
- Separate tests voor criteria selectie en formatting
- Performance tests voor bulk validatie