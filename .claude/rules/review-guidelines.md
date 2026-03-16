# Review Guidelines

> Generieke review-richtlijnen. Project-specifieke regels in aparte bestanden hebben voorrang.
> Bron: ALG-68 | v1.1

## Severity Levels

Elke bevinding MOET een severity krijgen. Zonder severity = niet rapporteren.

| Level | Betekenis | Merge impact | Bewijs vereist |
|-------|-----------|-------------|----------------|
| CRITICAL | Security, data loss, crash | Blokkeert merge | Stack trace, exploit-pad, crash |
| HIGH | Bug met impact | Moet geadresseerd | Reproduceerbare stappen |
| MEDIUM | Aanbeveling | Optioneel | Best practice + projectrelevantie |
| LOW | Informatief | Geen | Geen |

Bij twijfel → één level lager. Liever een missed HIGH dan een false CRITICAL.

## Bewijs-Eisen

**GEEN BEWIJS = NIET RAPPORTEREN.**

| Type | Moet bewijzen | Red flag (= false positive) |
|------|---------------|-----------------------------|
| FIX | Bug bestaat echt (trace/stappen/test) | "Zou kunnen falen" |
| REFACTOR | Code objectief slecht (>1000 LOC, coupling) | LOC drempels <500 |
| OPTIMIZE | Meetbaar probleem (N+1, O(n²)) | "Zou sneller kunnen" |
| DOCS | Publieke API zonder docs | Private methods |

## False Positive Patronen — NIET rapporteren

| Patroon | Probleem | Regel |
|---------|----------|-------|
| LOC-threshold blindness | Arbitraire >200 LOC grens | Alleen bij >1000 LOC of CC >15 |
| Pattern zealotry | Enterprise patterns forceren | Alleen als huidige code problemen veroorzaakt |
| Verificatie failure | "Ontbreekt" zonder te checken | ALTIJD eerst grep/read |
| Style vs Bug confusion | Lint issues als bugs | Max LOW severity, linter handelt af |
| Premature optimization | Performance zonder metrics | Alleen met profiling/O-notatie bewijs |
| Context blindness | Generieke regels zonder context | Eerst .claude/rules/ en CLAUDE.md lezen |

## Confidence & Consensus

Alleen bevindingen met confidence ≥70 rapporteren (0-69 = niet rapporteren).

| Conditie | Actie |
|----------|-------|
| ≥2 agents confidence ≥70 zelfde issue | Bevestigd |
| 1 agent confidence ≥90 | Bevestigd |
| 1 agent 70-89, geen bevestiging | "Needs review" |
| Agents spreken tegen | Judge beslist op bewijs |

**Gewichten:** Architecture 2.0x · Security 1.5x · Bug Hunter 1.5x · Test & Quality 1.0x
