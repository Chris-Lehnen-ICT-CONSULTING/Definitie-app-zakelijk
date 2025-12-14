# Docs Directory Cleanup Analyse

## Execution Mode
- **ULTRATHINK**: Ja
- **MULTIAGENT**: 6 agents
- **CONSENSUS**: Vereist (voor delete beslissingen)

## Agent Configuratie

| Agent | Rol | Verantwoordelijkheid |
|-------|-----|---------------------|
| Explorer | Codebase Verkenner | Map alle docs, timestamps, structuur |
| Architect | Structuur Analyst | Beoordeel documentatie architectuur |
| Code Reviewer | Duplicatie Checker | Identificeer overlap met CLAUDE.md en code |
| PM | Impact Assessor | Linear issue correlatie, business waarde |
| Silent Failure Hunter | Stale Doc Hunter | Vind verouderde, misleidende docs |
| Researcher | Best Practice Expert | Valideer tegen industry standards |

## Opdracht

Analyseer de `docs/` directory (2363 bestanden, 1639 >30 dagen oud) en categoriseer elk document als:
- **DELETE**: Kan definitief verwijderd worden
- **ARCHIVE**: Verplaats naar docs/archief/
- **KEEP**: Blijft relevant, geen actie nodig
- **UPDATE**: Behouden maar moet geüpdatet worden

## Deletion Criteria (alle moeten waar zijn voor DELETE)

1. **Ouderdom**: >30 dagen niet gewijzigd ÉN
2. **Relevantie**: Minstens één van:
   - Gerelateerd aan afgerond Linear issue (status: Done/Cancelled)
   - Beschrijft deprecated/verwijderde feature
   - Tijdelijk onderzoeksdocument (exploratory analysis)
   - Volledig vervangen door nieuwere versie
3. **Geen unieke waarde**: Informatie beschikbaar elders (CLAUDE.md, code, andere doc)
4. **Geen compliance risico**: Geen audit trail, beslissing, of ADR

## Archive Criteria (DELETE criteria NIET volledig, maar wel)

- >30 dagen oud
- Historische waarde (beslissingen, handovers, retrospectives)
- Verouderd maar mogelijk referentie-waardig
- Completed implementation plans

## Keep Criteria

- Actief onderhouden (<30 dagen of regelmatig bijgewerkt)
- Core documentatie (PRD, architectuur, README)
- Active guidelines en workflows
- Nog open Linear issues

## Context

**Codebase:** Definitie-app (Dutch AI Definition Generator)
**Huidige staat:** 2363 markdown bestanden, 69% ouder dan 30 dagen
**Reeds gearchiveerd:** docs/archief/ bevat 143 items
**Doel:** Opschonen naar <500 actieve documenten

## Best Practices (Research)

Uit industry best practices:
- "Dead docs are bad. They misinform, they slow down" - Google Style Guide
- Archive > Delete voor historische context
- Quarterly cleanup cadence recommended
- Mark deprecated docs clearly before deletion
- Preserve ADRs (Architecture Decision Records) altijd

## Fasen

### Fase 1: Inventory (Explorer)
- Lijst alle bestanden met metadata (path, size, modified date)
- Categoriseer per directory (analyses/, technisch/, archief/, etc.)
- Identificeer duplicaat bestandsnamen

### Fase 2: Linear Correlation (PM)
- Map documenten naar Linear issues
- Identificeer docs voor closed/cancelled issues
- Check backlog voor gerelateerde items

### Fase 3: Duplicatie Analyse (Code Reviewer)
- Vergelijk met CLAUDE.md secties
- Check overlap met code comments/docstrings
- Identificeer redundante docs binnen docs/

### Fase 4: Stale Analysis (Silent Failure Hunter + Architect)
- Identificeer misleidende/verouderde informatie
- Check of beschreven features nog bestaan
- Valideer tegen huidige codebase

### Fase 5: Consensus Classificatie (Alle Agents)
- Elke agent classificeert: DELETE/ARCHIVE/KEEP/UPDATE
- Bij disagreement: discussie en consensus
- Finale lijst met confidence scores

## Output Format

### 1. Executive Summary
- Totaal aantal docs per categorie
- Top 10 prioriteit deletions
- Geschatte tijdsbesparing

### 2. DELETE Lijst (gesorteerd op confidence)
| Bestand | Reden | Linear Issue | Confidence |
|---------|-------|--------------|------------|
| path/to/file.md | [reden] | DEF-XXX (Done) | 95% |

### 3. ARCHIVE Lijst
| Bestand | Reden | Archief Locatie |
|---------|-------|-----------------|

### 4. UPDATE Lijst
| Bestand | Wat moet geüpdatet | Prioriteit |
|---------|-------------------|------------|

### 5. Consensus Rapport
- Agent agreement percentages
- Discussiepunten en resoluties
- Confidence niveau per beslissing

## Constraints

- GEEN bestanden daadwerkelijk verwijderen (alleen rapport)
- CLAUDE.md is altijd KEEP
- docs/archief/ wordt niet opnieuw geclassificeerd
- Bij twijfel: ARCHIVE niet DELETE
- ADRs en decision docs altijd KEEP of ARCHIVE
