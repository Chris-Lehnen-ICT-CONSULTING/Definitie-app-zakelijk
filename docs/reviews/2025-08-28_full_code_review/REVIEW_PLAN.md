# Volledige Code- en Documentatiereview — Plan

## Doel & Scope
- Doel: Volledige review van code, configuraties, JSON/YAML en documentatie met per bestand een concreet voorstel en acceptatiecriteria.
- Scope: `src/`, `tests/`, `scripts/`, `config/`, `docs/` (incl. relevante JSON/YAML/SQL).
- Uitsluitingen: Beveiliging-audit valt buiten scope (alleen informatief noteren, geen beoordeling).

## Werkwijze
1. Inventarisatie: Checklists genereren en actueel houden.
2. Diepte-review per map in vaste volgorde (zie Volgorde van Review).
3. Rapportage: Voor elk gereviewd bestand een sectie in `CODE_REVIEW_REPORT.md` met bevindingen en voorstel.
4. Afvinken: Pas afvinken in checklist wanneer het voorstel + acceptatiecriteria voor dat bestand in het rapport staan.

## Volgorde van Review
1) Kritische instappunten: `src/main.py`, `src/services/`, `src/ui/`
2) Domeinlogica: `src/domain/`, `src/ontologie/`, `src/toetsregels/`
3) Hulpfuncties & infra: `src/utils/`, `src/config/`, `src/database/`
4) Integratie & I/O: `src/integration/`, `src/export/`, `src/web_lookup/`
5) Tests & scripts: `tests/`, `scripts/`
6) Documentatie: `docs/architectuur`, `docs/workflows`, overige docs

## Statuslabels
- WACHTEND: Nog niet bekeken
- TRIAGED: Snel gescand, diepte-review gepland
- REVIEWED: Inhoudelijk beoordeeld, bevindingen genoteerd
- PROPOSED: Voorstel in rapport opgenomen (wacht op akkoord)
- DONE: Voorstel geaccepteerd/afgehandeld
- BLOCKED: Tijdelijk geblokkeerd (afhankelijkheden)

## Kwaliteitscriteria (niet-security)
- Structuur: Bestandslocatie en modulegrenzen kloppen met projectregels.
- Stijl: Consistente stijl, duidelijke namen, geen dode code of willekeurige prints.
- Types: Type hints waar zinvol; geen flagrante type-mismatches.
- Tests: Bestaande tests actueel; zo niet, actiepunt opnemen.
- Docs: NL-docstrings voor businesslogica; korte module-intro waar nuttig.
- Config: Heldere defaults; env-variabelen en documentatie aanwezig.
- Architectuur: Past binnen architectuurrichtlijnen en lagen.

## Rapportage-eis per bestand
Een bestand mag in de checklist afgevinkt worden als in `CODE_REVIEW_REPORT.md` een sectie bestaat met:
- Samenvatting (1–2 zinnen)
- Bevindingen per categorie (Stijl/Types/Tests/Docs/Architectuur)
- Concreet voorstel (min. 1–3 acties)
- Acceptatiecriteria (objectieve check op “klaar”)

## Anchors & Verwijzingen
- Ankerformaat: path naar lower-case; `/` en niet-alfanumeriek → `-`.
- Voorbeeld: `src/main.py` → `#src-main-py` in het rapport.
- Checklist link: `[src/main.py](CODE_REVIEW_REPORT.md#src-main-py)`.

## Automatisering (optioneel)
- Baseline tooling: Ruff/Black/MyPy/pytest voor mechanische feedback; security-checks blijven uit.
- BMAD: `source .bmad-core/utils/bmad-post-edit-hook.sh && trigger_post_edit_review "Codex" "src/..."` (uitsluitend mechanische issues meenemen).

## Versie & Datum
- Planversie: v1.0
- Datum: 28-08-2025
