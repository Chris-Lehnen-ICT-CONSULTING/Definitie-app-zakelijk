---
id: EPIC-015
titel: Multi-User & Externalisatie
status: TE_DOEN
prioriteit: GEMIDDELD
owner: architecture
canonical: true
last_verified: 2025-09-11
stories:
- US-124
- US-125
- US-126
- US-127
- US-128
- US-129
- US-130
- US-131
- US-132
- US-133
- US-134
---

# EPIC-015: Multi-User & Externalisatie

Deze EPIC groepeert functionaliteit die buiten de single‑user scope valt: multi‑user, externe interfaces en platform‑uitbreidingen.

## Doelen
- Meerdere gebruikers veilig ondersteunen (auth, RBAC, keys)
- Externe integratie via stabiele API‑laag (met versiebeleid)
- Publiceerbare Portal en multi‑repo aggregatie
- Auditeerbaarheid en privacy‑borging bij uitrol (PII‑tooling)
- Inzicht in prestaties via metrics/dashboards
- Werkstromen parametriseerbaar maken (custom workflows)

## Non‑goals
- Geen verandering aan single‑user UX/flows (blijft werken zonder auth)
- Geen vendor‑afhankelijk monitoring/hosting lock‑ins (neutraal ontwerp)

## Scope
- Authenticatie (US‑124), RBAC (US‑125), API‑keys (US‑126)
- Externe API (US‑127), Collaboration (US‑128), Versioning (US‑129)
- Portal hosting (US‑130), Hub/aggregator (US‑131)
- Audit trail + PII‑scanner (US‑132)
- Observability (US‑133)
- Custom workflows (US‑134)

## Succesmetrieken
- API uptime ≥ 99.5% met rate limiting en versiebeleid
- Auth events en RBAC decisions gelogd (0 high‑risk findings)
- Portal publiek/artefact: reproduceerbaar via CI (≤ 5 min)
- PII‑scanner detecteert en maskeert 100% testcases
- Metrics zichtbaar (lateny/errors) voor top 3 kritieke paden

## Mijlpalen
1) Auth + RBAC + Keys (US‑124..126)
2) Externe API + versioning (US‑127/US‑129)
3) Portal hosting + Hub (US‑130/US‑131)
4) Audit/PII + Observability (US‑132/US‑133)
5) Custom workflows (US‑134)

## Risico's
- Privacy/compliance: mitigeren via PII‑scanner, logsanitisatie
- API breuk: mitigeren via versioning/contract tests
- Scope creep: faseren + duidelijke Non‑goals

## Traceability
- Security: REQ‑001, REQ‑004, REQ‑015 (ketenintegratie), REQ‑050/079/086
- Observability: interne NFR’s
