# DEF-835 — actuele takenlijst v26

28 september 2026. Vervangt v25 als actuele ingang; eerdere versies blijven behouden. Werkboom /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2; branch feature/DEF-835-int02-o2; basiscommit f9bb9e6973926a3cf768995f5d879f6edfd6322d.

## Mandaat
- [x] Chris: "akkoord! go" op S1/S2/U1/E1 en kwalificatieprotocol/Q1, inclusief2triggervervangingen en maximaal43appcalls/43tokenmetingen/US$12. Exacte binding: vervolg-akkoord-v1.md.
- [ ] Goldsetbeoordelaars nog te kiezen:2mensen of2onafhankelijkeCLIvoorstellen met Chris als inhoudelijke beoordelaar. Deze vraag staat open; offline code loopt door.
- Geen Actions, push, merge, productieactivering of productiedata. Nog0nieuweappcalls besteed.

## Afgerond
- [x] WP5a/F1–F4/typefixes gecommit en gereviewd, bewijs526tests/mypy411/lint; eerdere brede regressie2966. Geen volledige-suiteclaim.
- [x] Actuele bronnen/fetch en concrete vervolgplannen vastgesteld; cli-auth bruikbaar.
- [x] Q1 eerste implementatie door Claude:3software/testbestanden. RED79failed/77passed;GREEN156passed.
- [x] Coördinator:156passed23.99s,Ruff/Blackexit0 en hashes voor/na gelijk (bewijs/q1-coordinator-v1.json/.log).
- [x] Onafhankelijke Codex CLI-review op bytegelijke kopie:3blokkerende fouten bewezen met offline probes, alle fixnu.
- [x] Veertig unieke, ongelabelde synthetische conceptgevallen geschreven en teruggelezen; geen labels/freeze/modelproef. Buiten ontwikkel-/reviewcontext in goldset-voorbereiding/.
- [x] Reviewprobe duurzaam in dossier bewaard: bewijs/q1-codex-probe-v1.py/.log.

## Q1 open bevindingen — correctie loopt
- [ ] F1: exclusief processlot vóór lezen/budgetcontrole; parallelle runs konden51calls versturen bij43maximum.
- [ ] F2: holdout-p95≤90s echt handhaven;91s werd ten onrechte goedgekeurd.
- [ ] F3: bewijs duurzaam publiceren vóór succesvolle faseafronding; opslagfout mocht vervolg24calls starten.
- [ ] Gerichte RED/GREEN en onafhankelijke herreview door dezelfde reviewer.
- [ ] Normale lokale commit na gesloten bevindingen.

Claude-sessie585f02d8-1256-466a-a2ac-ae45d7cbc746 hervat met q1-F123-opdracht-claude-v1.md. Eerste turn is door coördinator gericht onderbroken om terug te keren naar de noodzakelijke correcties;156groen en aanvullende11mutatiechecks waren al voltooid, geen bron teruggedraaid.
Codex-reviewer01a0e8ca-2df9-7780-ba7a-b18c26caefe7; reviewwerkboom /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app. Rapport q1-codex-review-v1.md.

## Daarna — reeds geaccordeerd
- [ ] S1 gedeelde opslag/historie op eigen DEF-626branch; s1-opdracht-claude-concept-v1.md is voorbereid, nog niet verstuurd.
- [ ] S2 O2-documentopslag/herladen/C118.
- [ ] U1 editor/weergave; E1 export.
- [ ] Goldsetlabels door benoemde beoordelaars en Chris' acceptatie, daarna freeze.
- [ ] Begrensde kwalificatie volgens protocol, pas na labels/freeze.
- [ ] Geïntegreerde verificatie en oplevering; afzonderlijk activeringsbesluit.

## Proces
De lokale hook weigerde een update van bestaande takenlijst-v25.md ondanks vooraf gemaakte herstelkopie. Dat bestand is intact gebleven; volgens de gebruikersafspraak staat deze status in een vrije nieuwe versie. Geen alternatieve schrijfmethode gebruikt voor het geweigerde doel. Prompt Forge-fallback blijft geldig.

Exacte volgende stap: wacht op correctie-uitvoerder; verifieer uiteindelijke bron/testbewijs; kopieer de gecorrigeerde delta met herstelkopieën/hashcontrole naar dezelfde reviewwerkboom; hervat dezelfde Codex-reviewer alleen voor F1–F3 en doorwerking. Geen nieuwe algemene toestemming vragen.

