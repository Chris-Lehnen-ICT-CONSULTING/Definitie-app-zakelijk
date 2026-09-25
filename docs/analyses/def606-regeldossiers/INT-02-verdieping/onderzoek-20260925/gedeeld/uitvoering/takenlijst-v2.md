# DEF-771 — actuele takenlijst v2

25 september 2026. De taak-ID's en voltooiingsvoorwaarden uit [takenlijst-v1.md](takenlijst-v1.md) blijven gelden. Deze versie registreert de actuele stand; v1 blijft bewaard. Basis: [plan-v1.md](plan-v1.md).

Chris gaf na de takenlijst “akkoord”. Daarmee is het plan goedgekeurd. De afzonderlijke omvangakkoorden voor WP1/WP3 en de concrete S1-selectie blijven volgens dat plan vereist. Geen implementatie gestart. Volgende stap: W1.1.

## Voorbereiding en startvoorwaarden

- [x] V01 — Fetch en appbranch vanaf origin/main. Bewijs 25-09: plan-v1, basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d.
- [x] V02 — Dossier gelezen, opdracht-SHA gecontroleerd. Bewijs 25-09: plan-v1.
- [x] V03 — Vijf Linear-issues opgehaald. Bewijs 25-09: plan-v1.
- [x] V04 — Actuele code, regels en skillbron geïnventariseerd. Bewijs 25-09: plan-v1 en onderstaande actualisering.
- [x] V05 — Plan opgesteld. Bewijs 25-09: plan-v1.
- [x] A01 — Planakkoord ontvangen. Bewijs 25-09: bericht Chris “akkoord”.
- [ ] A02 — Tweede skillbranch/PR valt onder planakkoord; afhandeling van actieve kopieën vóór publicatie nog bepalen.
- [x] A03 — Contextkeuze vastgelegd onder planakkoord van 25-09: context_lists plus exacte NE-melding via gerichte servicewijziging. Concrete uitvoering na WP3-akkoord.
- [x] A04 — Nieuwe C1-replay vastgelegd onder planakkoord van 25-09: historisch bewijs behouden, context voor RR en aparte NE-gevallen.
- [ ] A05 — BEZIG: CLI-toegang bevestigd; skillwerkboom, schrijverschap en uitvoeringsscope nog afronden.

## WP1 — contract

- [ ] W1.1 — Afzonderlijk omvangakkoord: acht bestanden, 220–340 regels.
- [ ] W1.2 — Volledige Claude-opdracht opslaan, rol en scope vastleggen; Prompt Forge alleen indien bereikbaar.
- [ ] W1.3 — Contracttests RED met uitvoer bewaren.
- [ ] W1.4 — Canoniek contract, bytegelijke kopie, record en skills via Claude implementeren.
- [ ] W1.5 — GREEN, lint, tekstcontrole en bewijs; Chris terugkoppelen.

## WP2 — generatie

- [ ] W2.1 — Opdracht en RED-promptrenderingtests.
- [ ] W2.2 — Exacte G via Claude implementeren.
- [ ] W2.3 — Rendering met/zonder voorbeelden, lint en conflictmelding verifiëren.

## WP3 — O1 en S1

- [ ] W3.1 — Concrete S1-lijst en casusrisico's expliciet laten goedkeuren.
- [ ] W3.2 — Omvang en concrete contractwijziging afzonderlijk laten goedkeuren; opdracht opslaan.
- [ ] W3.3 — RED-tests status, reden, zinsdeel, positie en UI.
- [ ] W3.4 — Goedgekeurde O1/S1/contextwijzigingen via Claude implementeren.
- [ ] W3.5 — GREEN, lint en casussen verifiëren.
- [ ] W3.6 — Nieuwe C1-proef en bewijs vastleggen; terugkoppelen.

## WP4 — bestaande tests

- [ ] W4.1 — Opdracht en relevante bestaande rode verwachting vastleggen.
- [ ] W4.2 — Naam en C24/C25-context via Claude herijken; geen geval verwijderen.
- [ ] W4.3 — Golden-tests, matrix en lint controleren; terugkoppelen.

## WP5 — onafhankelijke review en verificatie

- [ ] W5.1 — Definitieve diffs, identiteit, bewijs en reviewopdracht vastleggen.
- [ ] W5.2 — Afzonderlijke verse Codex CLI-review uitvoeren.
- [ ] W5.3 — Bevindingen afhandelen via dezelfde uitvoerder/reviewer.
- [ ] W5.4 — make test, make lint en volledige offline pytest; failures verklaren.
- [ ] W5.5 — Contracten, casussen, tekstbehoud en actieve skillversies controleren.

## WP6 — opleveren

- [ ] W6.1 — App-PR en gekoppelde skill-PR; geen merge.
- [ ] W6.2 — Linear-oplevering met bewezen criteria en contract-SHA.
- [ ] W6.3 — O2-issue uitsluitend na afzonderlijk expliciet akkoord.
- [ ] W6.4 — Eindbericht met commits, PR's, CLI-bewijs, tests en open vervolgwerk.

## Actualisering en beperkingen

Claude Code 2.1.282 en Codex CLI 0.157.0 zijn beschikbaar en aangemeld. Claude-authstatus slaagt buiten de sandbox; de eerste controle binnen de sandbox had geen toegang tot de aanmelding. Geen modelproef of uitvoerderssessie gestart.

Na fetch staat origin/main van de skillrepository op 1e27a2da7668437423af3962cce48af5f1bc591b. De lokale checkout staat op dc7dc644438a05d602f05bc115ae16ac85b83169 en heeft bestaande andere wijzigingen. Origin/main bevat inmiddels de INT-01-aanvullingen in de vier relevante skillbestanden; die blijven behouden. De oude INT-02-zinnen staan nog op reference.md:63 en :186. De skillbranch krijgt deze actuele main als basis. Actieve kopieën zijn nog niet gepubliceerd.

De PreToolUse-hook heeft bijwerken van de bestaande takenlijst/processtatus geweigerd wegens vereiste bestandstoestemming. Er zijn unieke herstelkopieën gemaakt; de bestaande bestanden zijn ongewijzigd. Daarom is deze nieuwe versie de actuele werkstaat én processtatus totdat bijwerken is toegestaan. Een eerste poging deze nieuwe versie te schrijven strandde op de commandoparser; er is geen beveiliging omzeild.

De eerdere Prompt Forge-netwerkcontrole is door de PreToolUse-hook geweigerd. Backendbereikbaarheid is niet vastgesteld; volledige dossieropslag volstaat volgens de opdracht.
