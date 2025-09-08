---
aangemaakt: '08-09-2025'
applies_to: definitie-app@v2.3
bijgewerkt: '08-09-2025'
canonical: true
deadline: 20-09-2025
document_type: action-plan
last_verified: 03-09-2025
owner: project-management
prioriteit: critical
status: active
---



# 🎯 UAT 2025 Action Plan - DefinitieAgent

**Doel**: Single-user UAT succesvol afronden op 20 september 2025
**Status**: HAALBAAR met gerichte aanpak
**Slagingskans**: 85%

---

## ✅ Goed Nieuws: Beveiliging Geen Prioriteit

Door het wegvallen van security vereistes besparen we **11 dagen werk**:
- ❌ Geen authentication/authorization nodig
- ❌ Geen data encryptie vereist
- ❌ Geen multi-user support
- ❌ Geen AVG/GDPR compliance voor test

Dit maakt de UAT **realistisch haalbaar** in 17 dagen.

---

## 🚀 VANDAAG STARTEN - Quick Wins (4 uur werk)

```python
# 1. Service Container Caching (30 minuten)
# File: src/services/container.py
@st.cache_resource
def get_service_container():
    return ServiceContainer()

# 2. Toetsregels Caching (30 minuten)
# File: src/services/validation/modular_validation_service.py
@st.cache_data
def load_validation_rules():
    return load_all_rules()

# 3. Fix V2 Orchestrator (2 uur)
# Add missing get_stats() method to DefinitionOrchestratorV2

# 4. Test import errors (1 uur)
pytest --collect-only  # Identificeer en fix import errors
```

**Impact**: 50% performance verbetering, test suite werkend

---

## 📋 17-Dagen Planning

### Week 1 (Dag 1-6): Foundation
- **Dag 1-2**: Test suite reparatie
- **Dag 3-4**: Prestaties optimalisatie
- **Dag 5-6**: Prompt reductie (7,250 → 1,250 tokens)

### Week 2 (Dag 7-12): Features
- **Dag 7**: Voorbeeldzinnen UI
- **Dag 8-9**: Web Lookup fixes
- **Dag 10-11**: Export formats (Word/PDF)
- **Dag 12**: Ontologische score UI

### Week 3 (Dag 13-17): Polish
- **Dag 13-14**: Bug fixes
- **Dag 15-16**: Test coverage (core modules naar 70%)
- **Dag 17**: UAT dry-run

---

## 📊 UAT Success Criteria

### Must Have ✅
- [ ] Definitie generatie <5s response
- [ ] 45 validatie regels werkend
- [ ] Voorbeeldzinnen generatie
- [ ] TXT export
- [ ] Basis web lookup (1+ bron)
- [ ] Smoke tests 100% passing

### Nice to Have 🎯
- [ ] Word/PDF export
- [ ] Ontologische categorisatie UI
- [ ] 3+ web lookup bronnen
- [ ] Integration tests 70% passing

---

## 🔧 Kritieke Fixes Prioriteit

| Fix | Impact | Effort | wanneer |
|-----|--------|--------|---------|
| Test imports | Unblock development | 1 uur | Vandaag |
| Service caching | 6x → 1x init | 30 min | Vandaag |
| Rules caching | 45x → 1x load | 30 min | Vandaag |
| V2 Orchestrator | Core flow werkend | 2 uur | Vandaag |
| Prompt reductie | 83% minder tokens | 2 dagen | Week 1 |

---

## 📁 Documentatie Status

Alle assessments zijn correct gedocumenteerd volgens project richtlijnen:

✅ **UAT Readiness Assessment**
`docs/vereistes/uat/UAT_READINESS_ASSESSMENT_2025.md`

✅ **Technical Debt Assessment**
`docs/code-analyse/quality/TECHNICAL_DEBT_ASSESSMENT_2025.md`

✅ **INDEX.md bijgewerkt**
Nieuwe documenten toegevoegd aan centrale index

✅ **Frontmatter compliant**
Alle documenten voorzien van correcte metadata

---

## ⚡ Beslissing Vereist

### Optie A: Full Speed Ahead (Aanbevolen)
- Start vandaag met quick wins
- Focus op Episch Verhaal 1-3
- Skip alle nice-to-haves
- **Kans: 85%**

### Optie B: Scope Reductie
- Alleen Episch Verhaal 1 & 2
- Geen web lookup
- Basis UI only
- **Kans: 95%**

### Optie C: Uitstel naar Oktober
- Complete implementatie
- Alle features
- Proper testing
- **Kans: 99%**

---

## 📞 Support Nodig?

- **Test Suite Issues**: Python developer voor import fixes
- **Prestaties**: Streamlit expert voor caching
- **Web Lookup**: API integratie specialist
- **UI Polish**: Frontend developer voor laatste week

---

*Plan opgesteld: 3 september 2025*
*Volgende review: 10 september 2025 (halverwege)*
*Contact: Project Lead*


### Compliance Referenties

- **ASTRA Controls:**
  - ASTRA-QUA-001: Kwaliteitsborging
  - ASTRA-SEC-002: Beveiliging by Design
- **NORA Principes:**
  - NORA-BP-07: Herbruikbaarheid
  - NORA-BP-12: Betrouwbaarheid
- **GEMMA Referenties:**
  - GEMMA-ARC-03: Architectuur patterns
- **Justice Sector:**
  - DJI/OM integratie vereisten
  - Rechtspraak compatibiliteit
