# DEF-622 — uitvoeringsbesluiten 14 september 2026

Aanvulling op `2026-09-14-DEF-622-contextcontract.md`; deze besluiten zijn leidend boven de daarin nog open punten.

1. Chris kiest: **Totaalscore tijdelijk als niet beschikbaar tonen; regeluitkomsten blijven zichtbaar.** Er wordt geen nieuwe scoreformule of noemer ingevoerd. CON-01 krijgt geen cijfer of impliciete 0/1.
2. Chris geeft expliciet toestemming: **Ja, wijzig deze bestaande bestanden binnen DEF-622**, voor bestaande code-, test-, regelconfiguratie- en promptbestanden uit het plan. De lokale PreToolUse-weigering op de eerste transportpatch is voorgelegd en hiermee beantwoord. Normale controles blijven actief; een nieuwe weigering moet apart worden gerapporteerd.
3. Chris verlangt **Claude CLI voor codeerwerk, Codex CLI voor onafhankelijke code-review**. De desktoptaak coördineert en verifieert. Vanaf dit besluit doet Claude alle verdere implementatie en testwijzigingen; de twee reeds geschreven RED-testbestanden dateren van vóór deze taakverdeling.
4. Claude start via de echte binary `~/.local/bin/claude`, sessie `09cab2f3-3e97-4c40-9c75-3dcf86637141`. Gecontroleerde init-inventaris: alleen Bash, Edit, Glob, Grep, Read, Skill, Write; geen MCP-servers of delegatietools. Normale hooks en acceptEdits-permissionmode actief.
5. De aparte Codex-review mag zelf geen agents of CLI-sessies starten. De coördinator bewaakt de effectieve toolinventaris en `agents.enabled=false` conform de reviewskill.

## Reeds uitgevoerd RED-bewijs

- Contexttransport: 2 failures, exit 1; contextmetadata ontbreekt en `organisatorische_context` bereikt de service niet.
- CON-01-productiepad: 6 failures, exit 1; geen context geeft pass, dynamische geselecteerde naam geeft pass, het gewone woord juridisch geeft fail en deeluitkomsten ontbreken.
- Productiecode was bij overdracht aan Claude ongewijzigd. De geweigerde transportpatch is niet toegepast.
