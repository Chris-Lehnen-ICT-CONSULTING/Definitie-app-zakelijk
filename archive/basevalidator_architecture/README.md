# Gearchiveerd: BaseValidator Architectuur

## Archiveringsdatum
17 januari 2025

## Reden voor archivering
De BaseValidator architectuur is vervangen door een flexibelere JSON/Python validator architectuur waar elke toetsregel zijn eigen JSON configuratie en Python implementatie heeft.

## Wat zat in deze architectuur?

### BaseValidator Pattern
- Abstract base class voor alle validators
- ValidationContext en ValidationOutput dataclasses
- Registry pattern voor validator management
- 16 validators geïmplementeerd (CON-01/02, ESS-01/05, STR-01/09)

### Enhanced Features
- Rich validation output met scores en violations
- ToetsregelValidationResult voor geaggregeerde resultaten
- Severity levels en violation tracking

## Waarom gearchiveerd?

1. **Te rigide structuur** - BaseValidator dwingt een vaste interface af
2. **Geen directe JSON koppeling** - Validators waren losstaand van JSON configs
3. **Complexiteit** - Te veel abstractie voor de use case
4. **Flexibiliteit** - Moeilijk om nieuwe velden toe te voegen per regel

## Nieuwe architectuur

De nieuwe architectuur gebruikt:
- Individuele JSON bestanden per toetsregel
- Bijbehorende Python validator per regel
- Directe config injectie in validator constructor
- Flexibele velden (niet alle regels hoeven goede/foute voorbeelden)
- 45 validators volledig geïmplementeerd

## Bestanden in dit archief

- `validators/` - De 16 BaseValidator implementaties
- `enhanced_toetser.py` - Enhanced versie met rich output
- `models.py` - Dataclasses voor rich validation
- `modular_toetser.py` - Originele modular toetser

## Migratie

Als je features uit deze architectuur wilt gebruiken:
1. Rich output kan toegevoegd worden aan individuele validators
2. Scoring kan per validator geïmplementeerd worden
3. Registry pattern kan vervangen worden door JSONValidatorLoader