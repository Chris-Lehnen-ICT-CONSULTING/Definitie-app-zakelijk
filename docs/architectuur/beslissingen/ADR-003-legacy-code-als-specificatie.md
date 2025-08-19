# ADR-003: Legacy Code als Specificatie

**Status:** Geaccepteerd
**Datum:** 2025-07-17
**Deciders:** Development Team

## Context

De legacy codebase van DefinitieAgent bevat jaren aan impliciete business rules, edge case handling, en domein kennis die nergens formeel gedocumenteerd is. Tijdens de refactoring en modernisatie moet besloten worden hoe om te gaan met deze impliciete kennis.

Specifieke uitdagingen:
- 46 validatieregels met complexe interacties
- Ontologie-gebaseerde kwaliteitscontrole met subtiele nuances
- Specifieke formatting en output conventies
- Edge cases voor Nederlandse taal peculiarities
- Impliciete aannames over juridische terminologie

## Probleemstelling

Hoe behouden we de waardevolle domein kennis en business logic uit de legacy code tijdens modernisatie zonder functionaliteit te verliezen?

## Beslissing

We behandelen de legacy code als de officiële specificatie en behouden alle bestaande functionaliteit exact zoals geïmplementeerd, gebruikmakend van het "Legacy Wrapper" pattern voor geleidelijke modernisatie.

## Rationale

1. **Battle-tested logic**: Legacy code heeft bewezen te werken in productie context
2. **Impliciete kennis**: Bevat jaren van bugfixes en edge case handling
3. **Geen specificatie**: Bij afwezigheid van formele specs is code de waarheid
4. **Risk mitigation**: Voorkomt regressies in kritieke business logic
5. **A/B testing**: Mogelijk om oude vs nieuwe implementatie te vergelijken
6. **Gradual formalization**: Geeft tijd om impliciete regels te documenteren

## Gevolgen

### Positief
- ✅ Geen functionaliteit verlies tijdens migratie
- ✅ Behoud van domein expertise
- ✅ Mogelijkheid voor A/B testing
- ✅ Graduale knowledge extraction
- ✅ Lage risk refactoring
- ✅ Vertrouwen bij stakeholders

### Negatief
- ❌ Legacy patterns tijdelijk behouden
- ❌ Mogelijk suboptimale implementaties gekopieerd
- ❌ Extra werk voor wrapper layers
- ❌ Documentatie achterstand blijft

### Neutraal
- 🔄 Characterization tests nodig voor legacy behavior
- 🔄 Parallelle implementaties tijdens transitie

## Implementatie Aanpak

### 1. Legacy Wrapper Pattern

```python
class ModernDefinitionService:
    def __init__(self):
        self.legacy_service = LegacyDefinitionGenerator()
        self.feature_flags = FeatureFlags()

    def generate(self, term: str, context: str = None) -> Definition:
        # Check feature flag voor graduale rollout
        if self.feature_flags.is_enabled("use_modern_implementation"):
            try:
                return self._modern_implementation(term, context)
            except Exception as e:
                logger.warning(f"Modern implementation failed, falling back: {e}")
                return self._wrap_legacy_response(
                    self.legacy_service.genereer_definitie(term, context)
                )

        # Default naar legacy
        return self._wrap_legacy_response(
            self.legacy_service.genereer_definitie(term, context)
        )
```

### 2. Characterization Tests

Voor elke legacy functie:

```python
def test_legacy_behavior_definitie_generatie():
    """Test die exact legacy gedrag vastlegt"""
    # Arrange
    legacy_service = LegacyDefinitionGenerator()

    # Act - test met bekende inputs
    result = legacy_service.genereer_definitie("authenticatie", "juridisch")

    # Assert - exact output zoals legacy
    assert "proces" in result.lower()
    assert "identiteit" in result.lower()
    assert result.startswith(result[0].upper())  # Hoofdletter
    assert result.endswith(".")  # Punt
```

### 3. Knowledge Extraction Process

1. **Identify**: Vind impliciete regels in legacy code
2. **Document**: Schrijf als expliciete business rules
3. **Test**: Maak tests die regel valideren
4. **Formalize**: Voeg toe aan nieuwe implementatie
5. **Verify**: A/B test tegen legacy

### 4. Documentatie Strategie

Voor elke legacy functie documenteren we:

```markdown
## Legacy Behavior: [Function Name]

### Observed Rules
1. [Impliciete regel uit code]
2. [Edge case handling]

### Examples
- Input: X → Output: Y
- Input: Z → Output: W

### Quirks & Exceptions
- [Onverwacht gedrag dat behouden moet worden]

### Migration Notes
- [Notities voor moderne implementatie]
```

## Success Criteria

- [ ] 100% feature parity met legacy systeem
- [ ] Alle characterization tests groen
- [ ] A/B tests tonen identiek gedrag
- [ ] Graduale migration plan actief
- [ ] Business rules gedocumenteerd

## Migration Milestones

1. **Phase 1**: Wrap alle legacy services (Week 1)
2. **Phase 2**: Characterization tests complete (Week 2-3)
3. **Phase 3**: Start moderne implementaties (Week 4+)
4. **Phase 4**: A/B testing en validation (Week 6+)
5. **Phase 5**: Legacy code removal (Future)

## Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Legacy bugs gekopieerd | Medium | Flag bekend bugs, fix in v2 |
| Performance issues | Low | Profile en optimaliseer hot paths |
| Kennis verlies | High | Pair programming, documentation |
| Scope creep | Medium | Strict feature parity focus |

## Review Triggers

- Als >20% tests falen na refactoring
- Bij ontdekking van security issues in legacy
- Als performance 2x slechter wordt
- Bij major bugs in legacy logic

## Gerelateerde Beslissingen

- ADR-002: Features First (legacy features zijn de features)
- ADR-004: Incrementele Migratie (graduale transitie)

## Status Updates

- 2025-07-17: Beslissing genomen tijdens refactoring
- [Toekomstige updates hier]

## Referenties

- [Working Effectively with Legacy Code - Michael Feathers](https://www.goodreads.com/book/show/44919.Working_Effectively_with_Legacy_Code)
- [Strangler Fig Pattern - Martin Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Characterization Testing](https://en.wikipedia.org/wiki/Characterization_test)
