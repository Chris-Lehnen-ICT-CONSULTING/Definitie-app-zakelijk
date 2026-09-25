# DEF-771 — actuele takenlijst v3

25 september 2026. De taak-ID's en voltooiingsvoorwaarden uit [takenlijst-v1.md](takenlijst-v1.md) blijven gelden. Deze versie registreert de actuele stand; v1 blijft bewaard. Basis: [plan-v1.md](plan-v1.md).

Actuele stand na hervatten op 25-09: WP1 afgerond voor het pakketcontrolepunt; WP2 technisch geverifieerd, maar met een niet vooraf gemelde omvangoverschrijding. WP3 is voorbereid en wacht op afzonderlijk akkoord. Deze versie vervangt de eerdere voortgangsnotities als actuele ingang.

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
- [x] A05 — CLI-toegang en skillwerkboom bevestigd; dezelfde Claude-sessie hervat na limiet. Bewijs: wp-1-claude-vervolg-stream.jsonl.

## WP1 — contract

- [x] W1.1 — Afzonderlijk WP1-akkoord ontvangen op 25-09, inclusief werkstaat bijhouden.
- [x] W1.2 — Volledige start- en vervolgopdracht opgeslagen; werkelijke sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90.
- [x] W1.3 — RED bewezen: wp1-red-contracttest.log (7 failed, 1 passed, 6 errors door ontbrekende contracten).
- [x] W1.4 — Acht inhoudelijke WP1-bestanden door Claude geleverd; versie def771-int02/1 en bytegelijke contractkopie.
- [x] W1.5 — 18 tests, Ruff en Black groen; tekstvergelijking, AST-gelijkheid na formattering en reproduceerbaarheid gecontroleerd. Bewijs: wp1-na-formattering-verificatie.log. Afzonderlijke eindreview volgt in WP5.

## WP2 — generatie

- [x] W2.1 — Opdracht opgeslagen; RED 4 failed vóór modulewijziging. Bewijs: wp-2-opdracht-claude.md en wp2-red-promptnorm.log.
- [x] W2.2 — Exacte G geïmplementeerd door dezelfde Claude-sessie; overige module-instructies ongewijzigd.
- [ ] W2.3 — Technisch groen: 6 tests, Ruff, Black en make lint; exacte rendering met/zonder voorbeelden. Omvangakkoord voor 133 regels ontbreekt nog. Bewijs: wp2-green-promptnorm-v2.log en wp2-coordinator-verificatie.log.

## WP3 — O1 en S1

- [ ] W3.1 — Concrete zes S1-markers en casusrisico’s klaar in wp3-s1-en-omvang-ter-akkoord.md; wacht op expliciet akkoord.
- [ ] W3.2 — WP3-scope van twaalf inhoudelijke bestanden, 300–500 code/testregels plus 30–60 documentregels ter akkoord. Nog geen uitvoerdersopdracht verzonden.
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


## Akkoordpunten en bewijsgrenzen

WP2: 133 gewijzigde regels in twee inhoudelijke bestanden (27+/1− module, 105 nieuwe testregels), boven de grens van 100. Claude had vooraf moeten melden en deed dat niet; de coördinator heeft dit bij de omvangcontrole gemeld en start geen volgend pakket. De wijziging ligt nu ter expliciete acceptatie voor. Er wordt niet kunstmatig code samengeperst om de grens te maskeren.

WP3: voorstel in wp3-s1-en-omvang-ter-akkoord.md; behoud zeven patronen en voeg van oordeel is, naar eigen inzicht, redelijk acht, kan … besluiten, moet en dient te toe. C83 treft; C13/C59/C105 blijven signaalloos. C02 krijgt door moet een neutrale passagevraag. Beschrijvende treffers blijven RR, nooit automatische afkeur. Zes nieuwe regexen zijn alleen als voorstel onderzocht (wp3-s1-voorstel-vindbaarheid.json).

WP1 heeft 537 toegevoegde en 10 vervangen oude regels in acht bestanden, plus een historisch opbouwscript van 265 regels. De contract-SHA blijft 235c584234218420cf33275031e589047404b6957ddfe13e1efa893eb7bf5b9a. WP2 heeft afzonderlijke render- en vervangscripts als bewijsartefacten. Alle inhoudelijke wijzigingen, inclusief scripts, moeten in WP5 worden meegenomen.

DEF-612-voorbeeldconflict blijft bestaan en is gerenderd: INT-01 goed bevat moet ondersteunen; INT-02 bewaart dit als ASTRA-foutvoorbeeld. Geen buurregel gewijzigd. De aanpalende test_no_negative_commands_in_guide-failure is identiek op de basiscommit bewezen (12 < 10). Geen volledige suiteclaim.

Volledig WP1-contractbewijs vereist DEF771_SKILLS_ROOT expliciet naar de beheerde skillwerkboom; anders zijn tien tests zichtbaar overgeslagen. Geen nieuwe actieve skillpublicatie, commit, PR, Linear-mutatie of onafhankelijke CLI-review uitgevoerd. Appbasis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d; skillbasis 1e27a2da7668437423af3962cce48af5f1bc591b; beide feature/DEF-771-int02-contract-o1.

De updatehook weigerde eerder bestaande werkstaatbestanden ondanks akkoord; daarom wordt deze nieuwe versie gebruikt. Geen instellingen aangepast of blokkade omzeild. Prompt Forge-bereikbaarheid bleef door de eerder geweigerde netwerkcheck onbevestigd; volledige dossieropslag toegepast volgens opdracht.
