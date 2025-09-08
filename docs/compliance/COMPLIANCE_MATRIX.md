# Compliance Matrix Skeleton

Doel: traceerbaarheid tussen wettelijke/enterprise eisen (BIO, NORA, GDPR/AVG, WCAG, ISO 27001) en concrete maatregelen, eigenaarschap en status.

## Scope

- Toepassingen: DefinitieAgent UI, services, repositories, integraties
- Omgevingen: Dev/Test/Prod (cloud-first, Zero Trust)
- Periodiciteit: Maandelijks review; kwartaal-audit

## Matrix (invulsjabloon)

| Standaard | Requirement | Control ID | Maatregel | Implementatie | Bewijs | Eigenaar | Status | Risico | Deadline |
|---|---|---|---|---|---|---|---|---|---|
| BIO | Toegangsbeveiliging (AC) | AC-1 | OIDC AuthN + RBAC AuthZ | API Gateway + Service Guard | Configs, testverslagen | Beveiliging Lead | Open | Hoog | W2 |
| BIO | Cryptografie (SC) | SC-2 | Encryptie at rest | SQLCipher of beheerde DB | Key mgmt doc | Infra Lead | Open | Hoog | W2 |
| BIO | Logging & Monitoring (AU) | AU-1 | Structured logging + audit trail | Central logging + immutability | Log samples, retention policy | Platform Eng | Open | Middel | W4 |
| NORA | Interoperabiliteit | INT-1 | OpenAPI 3, API-first | Spec templates + gateway | OpenAPI repos | Arch Lead | In voorbereiding | Middel | W6 |
| GDPR/AVG | Dataminimalisatie | PRIV-1 | PII-uitsluiting in definities | Validators + DLP checks | Testcases | DPO | Lopend | Middel | W5 |
| GDPR/AVG | Rechten betrokkenen | PRIV-2 | Inzage/export/delete processen | Data subject procedures | SOP’s | DPO | Backlog | Laag | W8 |
| WCAG 2.1 | Conformiteit AA | A11Y-1 | Contrasten, toetsenbord, ARIA | UI checklists + linting | A11Y rapport | UX Lead | Backlog | Middel | W6 |
| ISO 27001 | Change mgmt | CM-1 | ADRs + CI gates | PR templates + gates | ADR log, pipeline | Arch Lead | Lopend | Laag | W3 |

Legenda status: Open, In voorbereiding, Lopend, Afgerond.

## RASCI

- R: Beveiliging Lead (BIO), DPO (AVG), UX Lead (WCAG), Arch Lead (NORA/ISO)
- A: CIO/CTO
- S: Platform Engineering, Backend, UI/UX
- C: Legal/Privacy, Business owners
- I: Architecture Board

## Evidence Register (te vullen)

- Policies: Beveiliging policy, Key management, Logging retention
- Procedures: Incident response, Change management, Data subject requests
- Artefacts: OpenAPI specs, testverslagen, audit logs, pentest rapport

## Roadmap-koppeling

- W1–W2: AuthN/Z, encryptie at rest
- W3–W4: Logging/monitoring, observability
- W5–W8: WCAG checks, DLP/PII validators uitbreiden
