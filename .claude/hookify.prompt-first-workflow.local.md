---
name: prompt-first-workflow
enabled: true
event: prompt
action: warn
conditions:
  - field: user_prompt
    operator: regex_match
    # Geoptimaliseerd pattern op basis van multiagent research (2025-12-04)
    # Bronnen: Perplexity (dev terminology), Context7 (Claude Code best practices), Codebase analyse
    # Strategie: High-confidence keywords + Nederlandse domein-termen
    pattern: (?i)\b(analy[sz]e|analyseer|analyseren|onderzoek|audit|evalueer|beoordeel|review|code.?review|pr.?review|architecture.?review|security.?review|controleer|bekijk|implementeer|implementeren|implement|implementatie|bouw|build|bouwen|maak|create|add|toevoegen|refactor|refactoren|restructur|herstructur|migreer|migrat|migrate|moderniseer|moderniz|ontwikkel|develop|fix|fixen|repareer|los.?op|debug|debuggen|patch|corrigeer|correct|herstel|optim|optimaliseer|verbeter|improve|security|beveilig|performance|prestatie|bottleneck|profil|benchmark|technical.?debt|technische.?schuld|architect|orchestr|strangler|breaking.?change|silent.?exception|silent.?failure|race.?condition|type.?error|import.?violation|toetsregel|validation.?rule|system.?wide|systeembreed|legacy|monolith|microservice|comprehensive|uitgebreid|gefaseerd|stapsgewijs)\b
---

**Prompt-First Workflow Reminder**

Dit lijkt een taak te zijn waarvoor een gestructureerde prompt nuttig kan zijn.

**Vraag aan gebruiker:**
> Wil je dat ik eerst een gestructureerde prompt genereer?
> - **Ja**: Prompt opslaan in `/prompts/` met multiagent framework
> - **Nee**: Direct uitvoeren
> - **Ja + Uitvoeren**: Genereer EN voer direct uit

**Wanneer WEL prompt genereren:**
- Complexe analyse (>5 bestanden)
- Kritieke wijzigingen
- Kwaliteitsborging nodig

**Wanneer NIET:**
- Simpele fix (<10 regels)
- Duidelijke opdracht
- Tijdskritiek

Zie `prompts/README.md` voor templates.
