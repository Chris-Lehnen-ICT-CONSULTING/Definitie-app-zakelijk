---
canonical: false
status: active
owner: architecture
last_verified: 2025-09-05
applies_to: definitie-app@current
---

# Workflow Routing

Doel: eenduidige keuze van de juiste workflow per opdracht, met consistente handoffs tussen agents. Dit document beschrijft hoe we de routing bepalen en hoe Claude Code agents worden aangestuurd.

## Signalen voor routing
- Intent: vrije tekst (bv. “review deze PR”, “analyseer dit verzoek”).
- Bestandsset: vooral `docs/**` → Document Cleanup; code‑diff → Review/Refactor Only; mixed → Full TDD.
- Labels/urgentie: `incident`, `hotfix`, `p1` → Hotfix.
- Commit‑prefixen: `docs:`, `refactor:`, `feat:`, `fix:`.

## Bronbestand
- Declaratieve definitie: `docs/guidelines/workflows.yaml`
  - Beschrijft workflows (fasen, agents, gates) en routingregels.
  - Kan door een router‑agent gebruikt worden, of handmatig gevolgd worden door mensen/agents.

## Router Agent (concept)
- Naam: workflow-router (zie `docs/agents/workflow-router.md` voor prompt‑definitie)
- Taken:
  1) Classificeer de opdracht op basis van intent, files en labels.
  2) Kies workflow uit `workflows.yaml`.
  3) Stel handoff‑payload op: `id, phase, gates, artifacts, next_agent`.
  4) Roep volgende agent aan via Claude Code Task met minimale context.

## Handoff‑payload (norm)
```json
{
  "work_unit_id": "FEAT-001",
  "workflow": "REVIEW",
  "phase": "REVIEW",
  "description": "Review van PR #123",
  "artifacts": ["diff:...", "tests/report.html"],
  "gate_conditions": ["review_report_created", "no_critical_issues", "verdict_stated"],
  "next": {"on_success": "OPTIONAL-FOLLOWUP", "on_block": "REVIEW"}
}
```

## Claude Code: aanroepen van agents
- Handoff naar agent: `Task("code-reviewer-comprehensive", payload)`
- Phase‑wissel: router valideert gates en roept daarna de volgende agent aan met bijgewerkte payload.

## Kwaliteitsgates per workflow (samenvatting)
- ANALYSIS: SMART + BDD + EA/SA/TA + canonical docs.
- REVIEW: volledig reviewrapport; geen 🔴 blockers.
- DOC_CLEANUP: frontmatter, canonical, links ok; index geüpdatet.
- REFACTOR_ONLY: tests groen; gedrag onveranderd; refactor‑log.
- HOTFIX: override‑approval, reproduceerbaarheid of mini‑test, staging ok, rollback‑plan, manual prod approve.
- FULL_TDD: zie TDD_TO_DEPLOYMENT_WORKFLOW.md (alle fasen).
