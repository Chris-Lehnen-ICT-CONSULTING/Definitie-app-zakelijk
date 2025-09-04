---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# Documentatie Policy (Single Source of Truth)

Doel: per onderwerp precies één canonieke bron die de werkelijkheid en planning reflecteert.

Principes
- Canoniek: Eén document per onderwerp gemarkeerd met `canonical: true` en `status: active`.
- Realiteitscheck: `last_verified` datum bijwerken wanneer relevante code wijzigt.
- Transparant: elk document heeft frontmatter: `canonical`, `status`, `owner`, `last_verified`, `applies_to`.
- Minimale overlap: duplicaten krijgen een korte stub met redirect naar de canonieke bron of worden gearchiveerd (`status: archived`).
- Vindbaarheid: `docs/INDEX.md` bevat een mapping Onderwerp → Canonieke doc.

Labels (frontmatter)
- `canonical: true|false` – markeer de enige bron per onderwerp.
- `status: active|draft|archived` – levend, concept of gearchiveerd.
- `owner: architecture|validation|platform|product|domain` – verantwoordelijke.
- `last_verified: YYYY-MM-DD` – laatste inhoudsverificatie.
- `applies_to: definitie-app@v2` – scope/versie waarop de inhoud van toepassing is.

Workflow
1) Nieuwe of gewijzigde functionaliteit → update relevante canonieke docs en `last_verified`.
2) Nieuwe beslissingen → leg vast als ADR onder `docs/architectuur/beslissingen/` en link vanuit Solution Architecture.
3) Verouderde/overlappende docs → verplaats naar `status: archived` met een 5‑regelige stub die verwijst naar de canonieke bron.

## 🚫 KRITIEKE REGELS - Document Management

### 📁 Archivering
**GEBRUIK ALTIJD:** `/docs/archief/` voor archivering
- ❌ NOOIT nieuwe directories maken zoals `archive`, `archief2`, `old`, etc.
- ✅ ALTIJD gebruik maken van de bestaande `/docs/archief/` structuur
- Subdirectories in archief: `stories/`, `architecture/`, `requirements/`, etc.

### 🔍 Duplicate Check Workflow
**VOORDAT je een nieuw document maakt:**
1. **SEARCH FIRST:** Gebruik grep/search om te checken of het onderwerp al bestaat
   ```bash
   grep -r "onderwerp" docs/
   ls docs/**/*relevante-term*.md
   ```
2. **CHECK MASTER DOCS:** Controleer eerst master documenten:
   - `docs/stories/MASTER-EPICS-USER-STORIES.md` voor epics/stories
   - `docs/INDEX.md` voor documentatie overzicht
   - `docs/CANONICAL_LOCATIONS.md` voor juiste locaties
3. **CHECK ARCHIEF:** Kijk ook in `/docs/archief/` of het al bestaat
4. **UPDATE BESTAAND:** Als het bestaat, update dat document i.p.v. nieuw maken

CI/Review Richtlijnen
- Blokkeer meerdere `canonical: true` voor hetzelfde onderwerp (lint).
- Waarschuw als `last_verified` > 90 dagen voor actieve canonieke docs.
- Linkcheck: interne links moeten geldig zijn.
- Detecteer duplicaat bestanden met vergelijkbare namen
- Waarschuw bij creatie buiten canonieke locaties

## 📝 Document Creatie Checklist

**Voor ELKE nieuwe file:**
- [ ] Gezocht naar bestaande documenten? (grep/ls)
- [ ] Master documenten gecheckt?
- [ ] Archief gecheckt?
- [ ] Canonieke locatie gebruikt? (zie CANONICAL_LOCATIONS.md)
- [ ] Frontmatter toegevoegd? (canonical, status, owner, etc.)
- [ ] INDEX.md bijgewerkt?
- [ ] Geen duplicaat van bestaand werk?
