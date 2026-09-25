**De finale unitgate is gesloten; T24-acceptatie nog niet.** T17 en T24 vragen eerst verduidelijking van de referentieafbakening. Daarnaast is één concrete diagnostiekfout bevestigd.

1. **T17 — referentie-interpretatieprobleem; geen bewezen nieuwe classifierbug.**  
   Referentie A verwachtte automatisch `pass`, B `review_required`; de adjudicator koos B omdat het proefcontract bij waar-plus-voorzetsel geen interne slotpunctuatie vereist. Die lezing is verdedigbaar vanuit [referentie-contract-v1.md:7](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-citaatbeleid-20260925-v2/referentie-contract-v1.md:7).  
   Daartegenover specificeert het [leidende besluit:5](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/herstel-20260924-v1/algemeen-citaatbesluit-v1.md:5) **interne zinseindpunctuatie**, en de voorafgaande bronreviews behielden expliciet citaten zonder slotteken. Normatief zijn beide referenties eensgezind: één formulering.  
   **Dispositie:** acceptatieblokkade door onvoldoende eenduidige contractoverdracht. Verduidelijk vóór een nieuwe proef of deze categorie zonder slotpunctuatie onder het beleid valt. Geen code- of historische labelwijziging op basis van deze review.

2. **T24 — geen aangetoonde buitenste grens; referentiegrond onvoldoende voor een automatische codecorrectie.**  
   `zkr.` staat op het teksteinde. Er volgt geen tekst; [zinsgrenzen.py:356](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:356) maakt daarom geen grenskandidaat. De probe met `zkr. daarna volgt controle` levert wél onzekerheid.  
   Beide referenties beroepen zich op de onbekende afkorting en mogelijke onvolledigheid. Het proefcontract ondersteunt die conservatieve lezing tekstueel, maar hun motivering toont geen afgebroken zinsstructuur aan: onbekende betekenis bewijst geen onvoltooide formulering. Begrijpelijkheid blijft in de app al afzonderlijk open.  
   **Dispositie:** verduidelijk vooraf of onbekende slotafkortingen een zelfstandig open *formuleringsonderdeel* vereisen, ook zonder grens naar vervolgtekst. Niet stil een nieuwe grensregel invoeren. Dit is geen vrijspraak tegen de letterlijke proefverwachting, maar een afbakeningsvraag.

3. **LOW — T08: foutieve extra onzekerheid bij `bijv. 12.`. Dispositie: fix nu.**  
   Beide referenties onderbouwen de afkortingspunt als intern; de werkelijke grens ligt na `12.`. De app meldt beide. Reproduceerbaar met `kaart met een nummer, bijv. 12.`.  
   **Oorzaak:** [zinsgrenzen.py:662](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:662) behandelt het numerieke vervolg eerder dan de specifieke voorbeeldvrijstelling. Begrens herstel tot positief aangekondigde numerieke voorbeelden; behoud de echte grens na het getal en onzekerheid bij andere afkortingen.

De overige **21 gevallen** hebben passende redenen, passages en broncitaatstatus. Historisch blijft de telling **22/24 statussen**; T08 verhindert bovendien volledige diagnostische conformiteit. Beide laadpaden en opslag zijn consistent, zonder volledige INT-01-pass. T17/T24 waren ook op de oude proefbron al pass; geen nieuwe zekere fout door `/9` aangetoond.

Bronfreeze, seals, archief en manifesthashes kloppen; geen drift. Commit: `58f70cb1dc1e3f78381f420a716220058a623105`. Resultaat-SHA256: `d4190b70eff9462aad974188d8a31443488d673e2ba2ab40d41fdfa64b7c7a7d`.

Canonieke gate bevestigd: **7546 passed, 75 skipped, 1 DEF-609-xfail, 21 subtests; exit 0**, offlinebeveiliging actief. Alleen schrijfvrije probes; geen edits, nieuwe suite of G24-herbeoordeling.