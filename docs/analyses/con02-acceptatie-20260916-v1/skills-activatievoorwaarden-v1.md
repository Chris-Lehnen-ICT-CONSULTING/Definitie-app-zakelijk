# CON-02-skills — publicatie en activatie

16 september 2026. Bronwerkboom: `/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-743-con02-skills`, branch `feature/DEF-743-con02-skills`.

## Afgebakende inhoud

Drie gekoppelde skills: `definitie-toetsregels`, `definitie-nederlandse-definities` en `definitie-juridisch-nederland`. De gereviewde CON-02-instructies zijn samengevoegd met de reeds gepubliceerde CON-01-instructies van `3d8dd6609d9db7dd57c0edd86b1130eaede615ee`. De drie canonieke Cowork-ZIPs moeten dezelfde samengevoegde bronbestanden bevatten.

Publicatie in Git is afzonderlijk van installatie. Een samengevoegde PR, geldige ZIP of identiek bestand bewijst niet dat een lopende clientsessie de nieuwe instructies heeft geladen of correct toepast. De definitieve publicatiestatus en verificatieresultaten worden in de overdracht bij dit pakket vastgelegd.

## Vastgestelde installatiegrens

De marker `/Users/chrislehnen/.claude/.global-setup-deployment-freeze-ALG-391` bestaat. Letterlijke instructie daarin:

> Opheffen: UITSLUITEND handmatig, na expliciet akkoord — plan v7 Task 10. Nooit als onderdeel van een commit, script of achtergrondproces.

`install.sh` controleert de marker vóór live writes. De gewone post-commit- en launchd-route komen daardoor niet langs de freeze. De aparte canaryroute is uitsluitend voor securitytargets en is geen skill-installatieroute. Er is geen gerichte drie-skills-optie in deze installer; de volledige installer raakt ook andere instellingen en bevat verwijderstappen. Die valt buiten deze CON-02-opdracht.

Het live [ALG-391-issue](https://linear.app/definitie-app/issue/ALG-391/borg-hookcompatibiliteit-in-claude-code-codex-integratie) vermeldt eveneens dat beperkte herstelproeven de deploymentfreeze niet opheffen. De taak geeft dus geen bewijs dat Task 10 is vrijgegeven.

## Geconstateerde verschillen met lokale installatie

Op beide lokale locaties, `~/.claude/skills` en `~/.agents/skills`, wijken vijf bestaande bestanden af van het samengevoegde bronpakket:

- `definitie-toetsregels/SKILL.md` en `reference.md`;
- `definitie-nederlandse-definities/SKILL.md`;
- `definitie-juridisch-nederland/SKILL.md` en `reference.md`.

`definitie-toetsregels/references/con02-bronbasis.md` ontbreekt op beide locaties. Dit is een gelezen bestandsvergelijking, geen wijziging of clientuitvoering.

## Nog uit te voeren na geldige vrijgave

1. Kies de volgens ALG-391/397 vrijgegeven installatieroute en controleer opnieuw de exacte publicatiecommit en targetinhoud. Verander de freeze niet als neveneffect van deze taak.
2. Bewaar de oude skillversies herstelbaar, zonder ongeautoriseerde verwijdering; installeer uitsluitend de vrijgegeven scope.
3. Controleer de uiteindelijke bestanden en referenties tegen een SHA-256-manifest van die commit.
4. Voor Cowork: gebruik de ondersteunde ZIP-import via Customize → Skills. De bronrepository waarschuwt dat directe writes in Coworks lokale pluginmap door cloudsynchronisatie kunnen verdwijnen. Geen activatieclaim op basis van zo een kopie.
5. Start per client een nieuwe laadproef met de geïnstalleerde versie: juiste betekenis met ontbrekende link (P31), inhoudelijke tegenspraak (P11/P16) en ontbrekende herkomst (P04). Bewaar de daadwerkelijke antwoorden en gebruikte skillversies.
6. Beoordeel die antwoorden tegen de menselijke acceptatiecriteria. Een AI-proef vervangt de deskundige vaststelling van de criteria niet.

Voor dit pakket is geen live skillinstallatie, freeze-opheffing of nieuwe clientacceptatie uitgevoerd.
