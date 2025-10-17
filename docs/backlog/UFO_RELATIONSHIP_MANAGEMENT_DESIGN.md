# UFO Relationship Management - Design Voorstel

**Datum**: 2025-10-13
**Status**: 📋 DESIGN PROPOSAL
**Auteur**: Product Owner + Claude Code
**Doel**: Ontologie-laag toevoegen voor relaties tussen juridische begrippen op basis van Unified Foundational Ontology (UFO)

---

## 🎯 Executive Summary

Uitbreiding van DefinitieAgent met UFO-gebaseerde ontologische relaties tussen begrippen. Hiermee kunnen we:
- **Begrippen classificeren** volgens UFO lagen (A/B/C)
- **Relaties vastleggen** tussen begrippen (participates_in, part_of, creates, etc.)
- **Visueel exploreren** van begrippenkaders in juridische context
- **Valideren** of definities consistent zijn met hun ontologische aard

---

## 📚 UFO Fundamentals

### UFO Lagen voor Juridische Begrippen

**UFO-A: Enduranten** - Dingen die bestaan in tijd
- **Definitie**: Entiteiten die door tijd heen bestaan en kunnen veranderen maar hun identiteit behouden
- **Juridische voorbeelden**:
  - Personen: verdachte, rechter, getuige, advocaat, officier van justitie
  - Rollen: beklaagde, eiser, gedaagde
  - Objecten: bewijsstuk, dossier, document
  - Organisaties: rechtbank, openbaar ministerie, politie

**UFO-B: Perduranten** - Gebeurtenissen die gebeuren
- **Definitie**: Gebeurtenissen die plaatsvinden in tijd, met duidelijk begin en eind
- **Juridische voorbeelden**:
  - Procedures: hoorzitting, vonnis, uitspraak, arrest
  - Acties: dagvaarding, aanhouding, schorsing
  - Processen: voorlopige hechtenis, strafvervolging
  - Termijnen: vervaltermijn, appeltermijn

**UFO-C: Sociale Entiteiten** - Sociale constructen
- **Definitie**: Entiteiten die bestaan door sociale overeenstemming en juridische erkenning
- **Juridische voorbeelden**:
  - Instrumenten: overeenkomst, bezwaar, beroep, rechtsmiddel
  - Statussen: schuldig, onschuldig, onherroepelijk
  - Rechten: eigendomsrecht, vorderingsrecht
  - Gevolgen: straf, schadevergoeding, boete

---

## 🔗 Relatie Types

### 1. `participates_in` (A → B)
**Betekenis**: Een endure neemt deel aan een gebeurtenis
**Voorbeelden**:
- verdachte `participates_in` hoorzitting
- getuige `participates_in` verhoor
- rechter `participates_in` vonnis
- advocaat `participates_in` pleidooi

**Inverse**: `has_participant` (B → A)

---

### 2. `part_of` (A → A, B → B, C → C)
**Betekenis**: Is onderdeel van (binnen zelfde laag)
**Voorbeelden**:
- advocaat `part_of` verdediging (A → A)
- verhoor `part_of` vooronderzoek (B → B)
- bezwaar `part_of` rechtsmiddelen (C → C)

**Inverse**: `has_part`

---

### 3. `creates` (B → C)
**Betekenis**: Gebeurtenis creëert sociaal construct
**Voorbeelden**:
- vonnis `creates` rechtsgevolg
- uitspraak `creates` straf
- overeenkomst sluiten `creates` verbintenis

**Inverse**: `created_by` (C → B)

---

### 4. `has_role_in` (A → C)
**Betekenis**: Endure heeft een rol in sociaal construct
**Voorbeelden**:
- rechter `has_role_in` rechtspraak
- verdachte `has_role_in` strafvervolging
- officier van justitie `has_role_in` openbaar ministerie

**Inverse**: `involves_role` (C → A)

---

### 5. `precedes` / `follows` (B → B)
**Betekenis**: Temporele volgorde tussen gebeurtenissen
**Voorbeelden**:
- dagvaarding `precedes` hoorzitting
- hoorzitting `precedes` vonnis
- vonnis `follows` hoorzitting

**Inverse**: Bidirectioneel (precedes ↔ follows)

---

### 6. `causes` / `caused_by` (B → B, B → C)
**Betekenis**: Causale relatie
**Voorbeelden**:
- misdrijf plegen `causes` strafvervolging (B → B)
- vonnis `causes` straf (B → C)

**Inverse**: Bidirectioneel (causes ↔ caused_by)

---

## 🗄️ Database Schema

### Tabel: `ufo_classifications`

```sql
CREATE TABLE ufo_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    ufo_layer TEXT NOT NULL CHECK(ufo_layer IN ('UFO-A', 'UFO-B', 'UFO-C')),
    classification_type TEXT,  -- person, event, social_construct, etc.
    properties JSON,           -- Layer-specific metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    FOREIGN KEY (definitie_id) REFERENCES definities(id) ON DELETE CASCADE,
    UNIQUE(definitie_id)  -- Each definitie has exactly 1 classification
);

CREATE INDEX idx_ufo_class_definitie ON ufo_classifications(definitie_id);
CREATE INDEX idx_ufo_class_layer ON ufo_classifications(ufo_layer);
CREATE INDEX idx_ufo_class_type ON ufo_classifications(classification_type);
```

**Properties JSON voorbeelden**:
```json
// UFO-A (person)
{
  "role_type": "legal_professional",
  "can_change_roles": true,
  "typical_contexts": ["strafrecht", "civielrecht"]
}

// UFO-B (event)
{
  "typical_duration": "2-4 uur",
  "required_participants": ["rechter", "verdachte"],
  "produces_outcome": "vonnis"
}

// UFO-C (social_construct)
{
  "legal_basis": "Wetboek van Strafvordering",
  "requires_authority": "rechter",
  "temporal_validity": "onbepaald"
}
```

---

### Tabel: `ufo_relationships`

```sql
CREATE TABLE ufo_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_definitie_id INTEGER NOT NULL,
    target_definitie_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,  -- participates_in, part_of, creates, etc.
    relationship_direction TEXT DEFAULT 'forward'
        CHECK(relationship_direction IN ('forward', 'bidirectional')),
    strength REAL DEFAULT 1.0 CHECK(strength >= 0.0 AND strength <= 1.0),
    context_json TEXT,         -- Additional context/rationale
    validated_by TEXT,
    validated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    FOREIGN KEY (source_definitie_id) REFERENCES definities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_definitie_id) REFERENCES definities(id) ON DELETE CASCADE,
    UNIQUE(source_definitie_id, target_definitie_id, relationship_type)
);

CREATE INDEX idx_ufo_rel_source ON ufo_relationships(source_definitie_id);
CREATE INDEX idx_ufo_rel_target ON ufo_relationships(target_definitie_id);
CREATE INDEX idx_ufo_rel_type ON ufo_relationships(relationship_type);
CREATE INDEX idx_ufo_rel_both ON ufo_relationships(source_definitie_id, target_definitie_id);
```

**Context JSON voorbeeld**:
```json
{
  "rationale": "Verdachte neemt verplicht deel aan hoorzitting volgens art. 268 Sv",
  "legal_basis": "Wetboek van Strafvordering art. 268",
  "exceptions": ["Afwezigheidsprocedure bij non-verschijning"],
  "cardinality": "1:N",  // 1 verdachte kan in meerdere hoorzittingen participeren
  "temporal_constraints": "Tijdens strafprocedure"
}
```

---

## 🏗️ Architecture (volgt bestaand patroon)

### Repository Laag
```
src/repositories/
  ufo_repository.py          # Data access voor classifications & relationships
```

**Verantwoordelijkheden**:
- CRUD voor `ufo_classifications`
- CRUD voor `ufo_relationships`
- Validation van UFO constraints (bijv. UFO-A kan niet `participates_in` UFO-A)
- Bidirectional lookup (gegeven begrip, vind alle relaties)
- Graph queries (transitieve relaties, pad tussen begrippen)

---

### Service Laag
```
src/services/
  ufo_classifier_service.py   # Classificatie business logic
  ufo_relationship_service.py # Relatie business logic + validation
  ufo_validator.py            # UFO constraint validation
```

**UFO Validator Rules**:
```python
# Allowed relationship directions per UFO layers
RELATIONSHIP_RULES = {
    "participates_in": {
        "allowed": [("UFO-A", "UFO-B")],
        "description": "Endures participate in events"
    },
    "part_of": {
        "allowed": [("UFO-A", "UFO-A"), ("UFO-B", "UFO-B"), ("UFO-C", "UFO-C")],
        "description": "Within-layer composition"
    },
    "creates": {
        "allowed": [("UFO-B", "UFO-C")],
        "description": "Events create social entities"
    },
    "has_role_in": {
        "allowed": [("UFO-A", "UFO-C")],
        "description": "Endures have roles in social entities"
    },
    "precedes": {
        "allowed": [("UFO-B", "UFO-B")],
        "description": "Temporal ordering of events"
    },
    "causes": {
        "allowed": [("UFO-B", "UFO-B"), ("UFO-B", "UFO-C")],
        "description": "Causal relationships"
    }
}
```

---

### Models
```
src/models/
  ufo_models.py              # UFOClassification, UFORelationship dataclasses
```

```python
@dataclass
class UFOClassification:
    id: int | None
    definitie_id: int
    ufo_layer: str  # UFO-A, UFO-B, UFO-C
    classification_type: str | None
    properties: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None
    created_by: str

@dataclass
class UFORelationship:
    id: int | None
    source_definitie_id: int
    target_definitie_id: int
    relationship_type: str
    relationship_direction: str  # forward, bidirectional
    strength: float
    context_json: str | None
    validated_by: str | None
    validated_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    created_by: str
```

---

### Config
```
config/
  ufo_config.yaml            # UFO layer definitions & relationship rules
```

**Voorbeeld config**:
```yaml
ufo_layers:
  UFO-A:
    name: "Enduranten (Objecten & Personen)"
    description: "Entiteiten die in tijd bestaan en kunnen veranderen"
    icon: "👤"
    classification_types:
      person:
        label: "Persoon"
        examples: ["verdachte", "rechter", "getuige"]
      role:
        label: "Rol"
        examples: ["advocaat", "officier van justitie"]
      object:
        label: "Object"
        examples: ["bewijsstuk", "dossier"]
      organization:
        label: "Organisatie"
        examples: ["rechtbank", "openbaar ministerie"]

  UFO-B:
    name: "Perduranten (Gebeurtenissen)"
    description: "Gebeurtenissen die plaatsvinden in tijd"
    icon: "⚡"
    classification_types:
      judicial_event:
        label: "Juridische Gebeurtenis"
        examples: ["hoorzitting", "vonnis", "uitspraak"]
      procedural_event:
        label: "Procedurele Gebeurtenis"
        examples: ["dagvaarding", "aanhouding"]
      temporal_event:
        label: "Temporele Gebeurtenis"
        examples: ["termijn", "schorsing"]

  UFO-C:
    name: "Sociale Entiteiten (Concepten)"
    description: "Sociale constructen en intentionele entiteiten"
    icon: "🏛️"
    classification_types:
      legal_construct:
        label: "Juridisch Construct"
        examples: ["overeenkomst", "recht", "plicht"]
      legal_status:
        label: "Juridische Status"
        examples: ["schuldig", "onschuldig"]
      legal_instrument:
        label: "Juridisch Instrument"
        examples: ["bezwaar", "beroep", "rechtsmiddel"]
      legal_consequence:
        label: "Juridisch Gevolg"
        examples: ["straf", "schadevergoeding"]

relationship_types:
  participates_in:
    allowed_directions: ["A->B"]
    description: "Een persoon/object neemt deel aan gebeurtenis"
    inverse: "has_participant"
    bidirectional: false

  part_of:
    allowed_directions: ["A->A", "B->B", "C->C"]
    description: "Is onderdeel van"
    inverse: "has_part"
    bidirectional: false

  creates:
    allowed_directions: ["B->C"]
    description: "Gebeurtenis creëert sociaal construct"
    inverse: "created_by"
    bidirectional: false

  has_role_in:
    allowed_directions: ["A->C"]
    description: "Heeft een rol in sociaal construct"
    inverse: "involves_role"
    bidirectional: false

  precedes:
    allowed_directions: ["B->B"]
    description: "Gebeurt voor"
    inverse: "follows"
    bidirectional: true

  causes:
    allowed_directions: ["B->B", "B->C"]
    description: "Veroorzaakt"
    inverse: "caused_by"
    bidirectional: true
```

---

## 🎨 UI Design: UFO Admin Page

**Locatie**: `src/pages/ufo_admin.py` (volgt `synonym_admin.py` patroon)

### Tab 1: 📊 Classificatie

**Doel**: Assign UFO layers aan begrippen

**Layout**:
```
┌────────────────────────────────────────────────────────┐
│ 🔍 Zoek Begrip: [_________________] 🔄 Refresh         │
├────────────────────────────────────────────────────────┤
│ Filter: ○ Alle  ○ Geclassificeerd  ○ Niet-geclassific.│
│ UFO Layer: ○ Alle  ○ UFO-A  ○ UFO-B  ○ UFO-C          │
├────────────────────────────────────────────────────────┤
│ Begrip           │ UFO Layer    │ Type           │ Act.│
├──────────────────┼──────────────┼────────────────┼─────┤
│ verdachte        │ 👤 UFO-A     │ person         │ ✏️  │
│ hoorzitting      │ ⚡ UFO-B     │ judicial_event │ ✏️  │
│ vonnis           │ ⚡ UFO-B     │ judicial_event │ ✏️  │
│ straf            │ 🏛️ UFO-C    │ legal_conseq.  │ ✏️  │
│ getuige          │ [Niet gecl.] │ -              │ ➕  │
└──────────────────┴──────────────┴────────────────┴─────┘

📌 Bulk Acties:
[✅ Classificeer Geselecteerd] [❌ Verwijder Classificaties]
```

**Edit Dialog** (bij klik op ✏️ of ➕):
```
┌─── Classificeer: verdachte ───────────────────────┐
│                                                    │
│ UFO Layer: ● UFO-A  ○ UFO-B  ○ UFO-C             │
│                                                    │
│ Classification Type:                               │
│ [person                    ▼]                      │
│                                                    │
│ Properties (optioneel):                            │
│ ┌────────────────────────────────────────────┐   │
│ │ {                                           │   │
│ │   "role_type": "legal_participant",         │   │
│ │   "can_change_roles": true                  │   │
│ │ }                                           │   │
│ └────────────────────────────────────────────┘   │
│                                                    │
│ [💾 Opslaan]  [❌ Annuleren]                      │
└────────────────────────────────────────────────────┘
```

---

### Tab 2: 🔗 Relaties

**Doel**: Manage relationships tussen begrippen

**Layout**:
```
┌────────────────────────────────────────────────────────┐
│ Filter Relaties:                                        │
│ Type: [Alle types          ▼]                          │
│ Van Layer: ○ Alle  ○ UFO-A  ○ UFO-B  ○ UFO-C          │
│ Naar Layer: ○ Alle  ○ UFO-A  ○ UFO-B  ○ UFO-C         │
├────────────────────────────────────────────────────────┤
│ Van (Source)    │ Relatie       │ Naar (Target)  │ Act │
├─────────────────┼───────────────┼────────────────┼─────┤
│ 👤 verdachte    │ participates  │ ⚡ hoorzitting │ ✏️  │
│ ⚡ hoorzitting  │ precedes      │ ⚡ vonnis      │ ✏️  │
│ ⚡ vonnis       │ creates       │ 🏛️ straf      │ ✏️  │
│ 👤 rechter      │ has_role_in   │ 🏛️ rechtspraak│ ✏️  │
└─────────────────┴───────────────┴────────────────┴─────┘

[➕ Nieuwe Relatie]
```

**Nieuwe Relatie Wizard**:
```
┌─── Nieuwe Relatie ──────────────────────────────────┐
│                                                      │
│ Stap 1/3: Selecteer Source Begrip                   │
│ [verdachte                              ▼]           │
│ UFO Layer: 👤 UFO-A (person)                        │
│                                                      │
│ Stap 2/3: Selecteer Relatie Type                    │
│ ● participates_in → Een persoon neemt deel aan ...  │
│ ○ part_of → Is onderdeel van ...                    │
│ ○ has_role_in → Heeft rol in ...                    │
│ (Alleen relaties die UFO-A mag gebruiken)           │
│                                                      │
│ Stap 3/3: Selecteer Target Begrip                   │
│ [hoorzitting                            ▼]           │
│ UFO Layer: ⚡ UFO-B (judicial_event)                │
│ (Gefilterd: alleen UFO-B begrippen)                 │
│                                                      │
│ Strength: [████████░░] 0.80                          │
│                                                      │
│ Rationale (optioneel):                               │
│ ┌──────────────────────────────────────────────┐   │
│ │ Verdachte moet aanwezig zijn bij hoorzitting │   │
│ │ volgens Wetboek van Strafvordering art. 268  │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ [💾 Aanmaken]  [❌ Annuleren]                        │
└──────────────────────────────────────────────────────┘
```

---

### Tab 3: 📈 Visualisatie

**Doel**: Network graph van begrippen en relaties

**Layout**:
```
┌────────────────────────────────────────────────────────┐
│ 🎨 Visualisatie Opties:                                 │
│ UFO Layer: ☑ UFO-A  ☑ UFO-B  ☑ UFO-C                   │
│ Relatie: ☑ participates_in ☑ creates ☑ precedes       │
│ Centrale Begriff: [verdachte          ▼] Diepte: [2]  │
│ Layout: ○ Force  ● Hierarchisch  ○ Circulair          │
├────────────────────────────────────────────────────────┤
│                                                         │
│          👤 getuige                                     │
│               ↓ participates_in                         │
│          ⚡ hoorzitting                                 │
│            ↙           ↘                               │
│  participates_in    precedes                            │
│         ↙               ↘                              │
│   👤 verdachte      ⚡ vonnis                           │
│         ↓               ↓                               │
│   has_role_in       creates                             │
│         ↓               ↓                               │
│   🏛️ strafvervolging  🏛️ straf                        │
│                                                         │
│ [💾 Export PNG] [📊 Export GraphML] [🔍 Zoom In]       │
└────────────────────────────────────────────────────────┘

📌 Klik op node voor details
```

**Graph Implementatie**:
- **Option 1** (eenvoudig): Plotly network graph
- **Option 2** (geavanceerd): Cytoscape.js voor interactieve graaf
- **Export formats**: PNG, GraphML, JSON

---

## 🔄 Integration met Bestaande Features

### 1. Definition Generation
**Optioneel**: UFO classificatie suggereren tijdens generatie
```python
# In DefinitionGenerator
if term_has_ufo_classification(begrip):
    classification = get_ufo_classification(begrip)
    prompt += f"\nOntologische categorie: {classification.ufo_layer}"
```

### 2. Validation Rules
**Nieuw**: UFO consistency validation
```python
# Toetsregel: UFO-0001 - Consistency Check
def validate_ufo_consistency(definitie: Definitie) -> ValidationResult:
    """Check of definitie consistent is met UFO classificatie"""
    classification = get_ufo_classification(definitie.id)

    if classification.ufo_layer == "UFO-B":
        # Events moeten temporele markers hebben
        if not has_temporal_markers(definitie.definitie):
            return ValidationResult(
                passed=False,
                message="UFO-B begrip moet temporele markers bevatten"
            )
```

### 3. CSV Import/Export
**Uitbreiding**: Voeg UFO kolommen toe
```csv
Begrip,Definitie,UFO_Layer,UFO_Type,Related_To
verdachte,"...",UFO-A,person,"hoorzitting|participates_in"
hoorzitting,"...",UFO-B,judicial_event,"vonnis|precedes"
```

---

## 📋 Implementation Roadmap

### Fase 1: Foundation (1 week)
- [ ] Database migration: `ufo_classifications` & `ufo_relationships` tables
- [ ] Models: `UFOClassification`, `UFORelationship` dataclasses
- [ ] Repository: `UFORepository` met CRUD operaties
- [ ] Config: `ufo_config.yaml` met layer definitions

### Fase 2: Services (1 week)
- [ ] `UFOClassifierService`: Classificatie business logic
- [ ] `UFORelationshipService`: Relatie business logic
- [ ] `UFOValidator`: Constraint validation (allowed relationships)
- [ ] Unit tests voor services

### Fase 3: UI - Tab 1 Classificatie (3 dagen)
- [ ] Page skeleton: `src/pages/ufo_admin.py`
- [ ] Tab 1: Begrippen lijst met UFO classificaties
- [ ] Edit dialog voor classificeren
- [ ] Bulk operations

### Fase 4: UI - Tab 2 Relaties (3 dagen)
- [ ] Relaties tabel view
- [ ] Nieuwe relatie wizard (3-step)
- [ ] Validation van allowed relationships
- [ ] Edit/delete functionaliteit

### Fase 5: UI - Tab 3 Visualisatie (4 dagen)
- [ ] Graph data preparation
- [ ] Plotly/Cytoscape.js implementatie
- [ ] Filter & zoom controls
- [ ] Export functionaliteit (PNG, GraphML)

### Fase 6: Integration & Testing (2 dagen)
- [ ] Integration tests voor volledige flows
- [ ] CSV import/export uitbreiding
- [ ] Documentatie bijwerken
- [ ] User acceptance testing

**Totaal**: ~3 weken development

---

## 🎯 Success Metrics

- [ ] Alle juridische begrippen geclassificeerd (100% coverage UFO layers)
- [ ] Minimaal 50 relaties vastgelegd tussen begrippen
- [ ] Visualisatie werkend voor minimaal 20 begrippen netwerk
- [ ] 0 invalid relationships (alle UFO constraints gerespecteerd)
- [ ] Export/import functionaliteit werkend
- [ ] Performance: Graph render < 2 seconden voor 100 begrippen

---

## 🚧 Open Questions

1. **AI-assisted classification**: Moet GPT-4 UFO classificaties kunnen suggereren?
   - Pro: Snellere classificatie van bestaande begrippen
   - Con: Mogelijk onnauwkeurig, vereist menselijke review

2. **Transitieve relaties**: Automatisch afleiden van transitieve relaties?
   - Voorbeeld: Als A `part_of` B en B `part_of` C, dan A `part_of` C?
   - Implementatie: Zou graph queries complexer maken

3. **Cardinality constraints**: Moeten we cardinaliteit vastleggen (1:1, 1:N, M:N)?
   - Voorbeeld: 1 verdachte kan in meerdere hoorzittingen participeren (1:N)
   - Zou als property in `context_json` kunnen

4. **Visualization library**: Plotly (simpel) of Cytoscape.js (geavanceerd)?
   - Plotly: Sneller te implementeren, basic interactiviteit
   - Cytoscape.js: Krachtigere graph layouts, betere UX

---

## 📚 References

- **UFO Specification**: https://nemo.inf.ufes.br/en/projects/ufo/
- **UFO-A (Structural)**: Enduring entities, objects, relations
- **UFO-B (Dynamics)**: Events, processes, states
- **UFO-C (Social)**: Social entities, norms, roles

---

**Status**: 📋 Design gereed voor review
**Next**: Feedback van Product Owner → Prioritering → EPIC aanmaken
