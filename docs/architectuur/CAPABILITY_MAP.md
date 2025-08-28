# DefinitieAgent Capability Map (Compact)

Doel: snel overzicht van enterprise capabilities met clustering per laag (Core, Supporting, Platform, Governance) en huidige maturiteit.

## Visual (Mermaid)

```mermaid
flowchart TB
    subgraph Core[Core Capabilities]
        A[AI Definition Generation]
        B[Multi-level Validation]
        C[Context & Ontology]
        D[Duplicate Detection]
        E[Generation Orchestration]
    end

    subgraph Supporting[Supporting Capabilities]
        F[External Web Lookup]
        G[Document Processing]
        H[Expert Review Workflow]
        I[Export & Publishing]
        J[Usage Analytics]
    end

    subgraph Platform[Platform Capabilities]
        K[IAM & AuthZ]
        L[Observability & Monitoring]
        M[Config & Feature Flags]
        N[Data Management & Repository]
        O[API Gateway & Adapters]
        P[CI/CD & Quality Gates]
    end

    subgraph Governance[Governance]
        Q[Architecture Governance & ADRs]
        R[Compliance (BIO/NORA/GDPR/WCAG)]
        S[Risk Management]
    end

    A --> B --> E
    C --> A
    D --> A
    F --> A
    G --> C
    H --> B
    I --> E
    J --> Governance

    K --> Core
    L --> Core
    M --> Core
    N --> Core
    O --> Supporting
    P --> Platform
    Q --> Platform
    R --> Platform
    S --> Platform
```

## Maturiteit (Indicatief 2025-08-28)

- Core: hoog (AI/Validatie/Repo) — open: 1/46 regel, prompt tuning
- Supporting: middel — Web Lookup UI-integratie open, Expert Review uitbreiden
- Platform: laag-middel — Auth/IAM ontbreekt, observability en feature flags verbeteren
- Governance: middel — ADRs aanwezig, compliance-matrix skeleton toegevoegd

## Scope & Kaders

- Principes: API-first, Clean Architecture, Testbaarheid zonder UI-coupling
- Standaarden: BIO/NORA/GDPR/WCAG, OpenAPI 3, Zero Trust

## Volgende stappen

- Platform: implementeren OIDC/IAM, uniform rate limiting en structured logging
- Supporting: UI-koppeling Web Lookup, reviewworkflows afronden
- Core: finalize 46/46 regels, duplicaatdetectie verfijnen
- Governance: compliance-matrix invullen en borgen in CI-gates
