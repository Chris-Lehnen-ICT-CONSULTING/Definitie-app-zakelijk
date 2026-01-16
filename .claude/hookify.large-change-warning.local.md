---
name: large-change-warning
enabled: true
event: prompt
action: warn
conditions:
  - field: user_prompt
    operator: regex_match
    # Detecteert prompts die wijzen op grote wijzigingen (>100 lines OR >5 files)
    # Keywords: refactor all/everything, redesign, rewrite, migrate all, restructure entire
    pattern: (?i)\b(refactor\s+(all|everything|entire|complete|whole)|redesign\s+(the|entire|complete)|rewrite\s+(all|the\s+entire)|migrate\s+(all|everything)|restructure\s+(entire|complete|all)|overhaul|complete\s+rewrite|from\s+scratch|alle\s+bestanden|heel\s+de|volledige\s+refactor|alles\s+(herschrijven|refactoren|migreren))\b
---

**GROTE WIJZIGING GEDETECTEERD**

Dit lijkt een grote refactoring/redesign te zijn. Volgens CLAUDE.md §Critical Rules:

> **Ask first for large changes** - >100 lines OR >5 files

**Voordat je verdergaat, vraag jezelf af:**

1. **Scope**: Hoeveel bestanden worden geraakt?
2. **Impact**: Zijn er breaking changes?
3. **Alternatieven**: Kan dit incrementeel?

**Aanbevolen aanpak:**

1. **Vraag goedkeuring** als dit >5 bestanden raakt
2. **Maak een plan** met concrete stappen
3. **Werk incrementeel** - commit per logische stap
4. **Test continu** - na elke wijziging

**Solo dev constraint:**
Dit is een solo-developer project. Grote refactorings zonder backup zijn riskant.

**Opties:**
- **Doorgaan**: Als je zeker bent dat dit <5 bestanden en <100 regels is
- **Plan maken**: Gebruik `prompt-forge forge "<taak>" -r` voor een gestructureerd plan
- **Opsplitsen**: Verdeel in kleinere, testbare stappen

**Zie:** CLAUDE.md §Critical Rules, §Extended Instructions
