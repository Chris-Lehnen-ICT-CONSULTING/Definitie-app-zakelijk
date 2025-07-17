# Overzicht: 3 Validatie/Toetsing Mappen

## 📁 src/ai_toetser/
**ROL: Hoofdengine voor Toetsregels**

```
✅ ACTIEF - Dit is de primaire toetsing engine
├── core.py              ❌ LEGACY - 1000+ regels monolithisch (moet weg)
├── modular_toetser.py   ✅ MODERN - Nieuwe orchestrator
├── toetser.py          ❌ LEGACY - Alleen verboden woorden check
└── validators/         ✅ MODERN - Modulaire validators (16/46 klaar)
    ├── base_validator.py
    ├── content_rules.py    (CON-01, CON-02)
    ├── essential_rules.py  (ESS-01 t/m ESS-05)
    └── structure_rules.py  (STR-01 t/m STR-09)
```

**Wat doet het?**
- Voert 46 toetsregels uit op definities
- Gebruikt JSON configs uit `/config/toetsregels/regels/`
- Hybride: legacy functies + nieuwe modulaire validators
- Output: Lijst van toetsresultaten als strings

---

## 📁 src/validatie_toetsregels/
**ROL: Development Tool voor Consistentie Check**

```
⚠️ OBSOLEET - Moet gearchiveerd worden
├── __init__.py
└── validator.py  - Controleert of JSON regels Python functies hebben
```

**Wat doet het?**
- Controleert consistentie tussen JSON en Python code
- Quality assurance tool voor developers
- NIET voor runtime validatie
- **ACTIE: Archiveren naar /archive/**

---

## 📁 src/validation/
**ROL: Generiek Validatie Framework**

```
✅ ACTIEF - Algemene validatie functionaliteit
├── definitie_validator.py   ✅ Intelligente definitie validatie met scoring
├── dutch_text_validator.py  ✅ Nederlandse taal validatie
├── input_validator.py       ✅ Schema-based input validatie
├── sanitizer.py            ✅ Security en content sanering
└── log/                    📝 Validatie logs
```

**Wat doet het?**
- Generieke validatie voor ALLE input/output
- Security sanering
- Nederlandse taalkundige controles
- Definitie kwaliteitsscoring (overlap met ai_toetser!)

---

## 🔄 Probleem: Overlappingen

### Dubbele Definitie Validatie:
```
ai_toetser/modular_toetser.py
    ↓ output: List[str]
    vs.
validation/definitie_validator.py
    ↓ output: ValidationResult met scores
```

### Verschillende Output Formaten:
- `ai_toetser`: Simpele string lijst voor UI
- `validation`: Rich dataclasses met scores en violations

---

## 🎯 Aanbevolen Architectuur

```
src/
├── validation/              # Behouden: Generiek framework
│   ├── input_validator.py   # Input sanering
│   ├── dutch_text_validator.py
│   └── sanitizer.py
│
├── toetsregels/            # NIEUW: Gecombineerd
│   ├── validator.py        # DefinitieValidator (uit validation/)
│   ├── engine.py          # ModularToetser (uit ai_toetser/)
│   └── rules/             # Alle validator modules
│       ├── base.py
│       ├── content.py
│       ├── essential.py
│       └── ...
│
└── archive/
    ├── ai_toetser_core_legacy.py
    └── validatie_toetsregels/
```

---

## 📋 Actieplan

1. **DIRECT**: Archiveer `validatie_toetsregels/` map
2. **KORT**: Combineer `validation/definitie_validator.py` met `ai_toetser/`
3. **MIDDEL**: Migreer alle legacy functies naar modulaire validators
4. **LANG**: Refactor naar single verantwoordelijkheid per module