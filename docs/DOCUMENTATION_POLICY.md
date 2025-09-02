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

CI/Review Richtlijnen
- Blokkeer meerdere `canonical: true` voor hetzelfde onderwerp (lint).
- Waarschuw als `last_verified` > 90 dagen voor actieve canonieke docs.
- Linkcheck: interne links moeten geldig zijn.
