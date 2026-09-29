# DEF-771 — actuele takenlijst v4

25 september 2026. Actuele ingang; eerdere versies blijven bewijs van hun tijdstip. Specificatie: plan-v1.md. Akkoorden: akkoord-wp2-wp3-s1.md. Nieuwe bevinding en concreet aanvullingsvoorstel: wp3-transportbesluit-v1.md.

## Voorbereiding

- [x] V01 — Fetch en appbranch vanaf origin/main; basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d.
- [x] V02 — Dossier gelezen en opdracht-SHA gecontroleerd.
- [x] V03 — Linear-bronnen opgehaald; DEF-771 bij deze controle nog onderzoeks-Done met implementatiecriterium open.
- [x] V04 — Code, regels en beheerde skillbron geïnventariseerd.
- [x] V05 — Plan opgesteld.
- [x] A01 — Planakkoord ontvangen.
- [ ] A02 — Tweede skillbranch/PR goedgekeurd en werkboom aanwezig; actieve kopieën vóór publicatie nog afhandelen.
- [x] A03 — context_lists en gerichte interne NE-reden goedgekeurd.
- [x] A04 — Nieuwe C1-replay naast historisch bewijs goedgekeurd.
- [x] A05 — CLI's en skillwerkboom bevestigd; Claude-sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90.

## WP1 — contract

- [x] W1.1 — Afzonderlijk omvangakkoord.
- [x] W1.2 — Opdracht en prompts opgeslagen.
- [x] W1.3 — RED bewezen; wp1-red-contracttest.log.
- [x] W1.4 — Acht inhoudelijke bestanden geleverd; contractkopie bytegelijk.
- [x] W1.5 — Pakketcontrole groen; wp1-na-formattering-verificatie.log. Onafhankelijke review volgt bij WP5.

## WP2 — generatie

- [x] W2.1 — Opdracht en RED; wp2-red-promptnorm.log.
- [x] W2.2 — Exacte G door dezelfde Claude-sessie geïmplementeerd.
- [x] W2.3 — Zes tests en lint groen, rendering gecontroleerd; 133 regels expliciet geaccepteerd door Chris.

## WP3 — O1 en S1

- [x] W3.1 — Zes S1-markers expliciet goedgekeurd.
- [x] W3.2 — Twaalf inhoudelijke bestanden goedgekeurd; volledige opdracht opgeslagen en uitgevoerd.
- [x] W3.3 — RED: 31 failures vóór productieaanpassing; wp3-red.log, exit 1.
- [x] W3.4 — O1/S1/context en contractversie /2 gebouwd binnen de twaalf bestanden. Werkelijke omvang: 685 regels.
- [ ] W3.5 — Coördinator bevestigt 45 groene tests (wp3-coordinator-tussenverificatie.log, exit 0); definitieve lint-/behoudcontrole nog open.
- [ ] W3.6 — Nieuwe C1-replay afronden en uitvoeren; uitkomsten nog niet beschikbaar.
- [ ] A06 — Aanvullend akkoord gevraagd voor publieke NE-doorgifte via bestaande rule_results/UI en gerichte schema-uitbreiding (wp3-transportbesluit-v1.md). Wachten op Chris vóór deze uitbreiding.

## WP4 — bestaande tests

- [ ] W4.1 — Opdracht en rode bestaande verwachtingen vastleggen.
- [ ] W4.2 — Naam en C24/C25-context herijken via Claude; gevallen behouden.
- [ ] W4.3 — Golden-tests, matrix en lint controleren.

## WP5 — onafhankelijke review en verificatie

- [ ] W5.1 — Definitieve diffs, identiteit, bewijs en reviewopdracht vastleggen.
- [ ] W5.2 — Verse afzonderlijke Codex CLI-sessie in aparte werkroot reviewt.
- [ ] W5.3 — Bevindingen via dezelfde uitvoerder/reviewer afhandelen.
- [ ] W5.4 — make test, make lint en volledige offline pytest; iedere failure verklaren.
- [ ] W5.5 — Contracten, casussen, tekstbehoud en actieve skillversies controleren.

## WP6 — oplevering

- [ ] W6.1 — App-PR en gekoppelde skill-PR; geen merge.
- [ ] W6.2 — Linear-oplevering met bewezen criteria en contract-SHA.
- [ ] W6.3 — O2-issue uitsluitend na afzonderlijk expliciet akkoord.
- [ ] W6.4 — Eindbericht met commits, PR's, CLI-bewijs, tests en vervolgwerk.

## Bewijsgrenzen en processtatus

De exacte NE-reden staat intern goed, maar ontbreekt bewezen in het publieke resultaat: wp3-ne-transportcontrole.log. Daarom geen claim dat de NE-appmelding is opgeleverd. De aanvullende contractwijziging is nog niet uitgevoerd. Geen WP4 gestart.

De volledige suite en onafhankelijke review zijn nog niet uitgevoerd. DEF-612-voorbeeldconflict en de bewezen basisfailure test_no_negative_commands_in_guide blijven open buiten deze scope. Volledig contractbewijs vereist DEF771_SKILLS_ROOT naar de beheerde skillwerkboom. Actieve skillkopieën zijn nog niet gepubliceerd.

Geen commits, PR's, Linear-mutaties of merge. Alle prompts en CLI-uitvoer staan in deze uitvoeringsmap. Prompt Forge blijft de geautoriseerde dossierfallback volgen na de eerder geweigerde bereikbaarheidscontrole. Omdat de updatehook eerdere bestaande werkstaatbestanden weigerde, gebruikt deze voortgang een nieuwe versie.
