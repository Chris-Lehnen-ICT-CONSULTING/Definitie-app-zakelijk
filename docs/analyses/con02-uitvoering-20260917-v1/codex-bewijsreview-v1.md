**Ja. Bevestigde bevinding — ernst: Important (hoog); dispositie: repareren vóór acceptatie.** Record 4 krijgt ten onrechte een gewone positieve verwijzingsbeoordeling zonder hyperlink of menselijke uitzondering. Onzekerheid over versie en gezag staat daarvan los.

**Verwachting en waarneming**

Het [afgesproken contract](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/docs/analyses/con02-acceptatie-20260916-v1/synthese-en-beslispunten-v1.md:43) verlangt aantoonbare doorgifte van bronversie, vindplaats en gerichte hyperlink. Een [deskundige verwijzingsuitzondering](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/docs/analyses/con02-acceptatie-20260916-v1/basis/besluiten-20260915-v3.md:3) blijft herkenbaar een uitzondering.

In het [bewijsrecord](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/docs/analyses/con02-uitvoering-20260917-v1/generatie-record4-v1.json:29):

- Zijn alle vier bron-URLs en beoordelingsbronversies `null`.
- Is `reference_quality.status = pass`, uitsluitend onderbouwd met de vindplaats Awb, artikel 1:3 lid 1.
- Ontbreekt een menselijke uitzonderingsregistratie.
- Levert een door mij uitgevoerde, zuiver lokale replay eveneens CON-02 `pass`, verwijskwaliteit `pass` en **“Geen actie nodig”**. Daarbij staan `assessment.applied = true` en `review.applied = false`.

Dit bewijst dat de onterechte positieve beoordeling door de beoordelingskern wordt overgenomen.

**Drie afzonderlijke conclusies**

1. **Hyperlink: concreet verwijstekort.** De vereiste link ontbreekt daadwerkelijk in het record. Een exacte artikelverwijzing vervangt die niet. Zonder geaccepteerde uitzondering is gewoon `pass` onjuist. Het bewijs toont niet dat een bruikbare link onmogelijk beschikbaar was.
2. **Versie en gezag: onvoldoende bewezen.** Versie en peildatum zijn onbekend; de bestandsnaam bewijst geen geldigheid of authenticiteit. Dat rechtvaardigt een open beoordelingspunt, geen conclusie dat de bron aantoonbaar verouderd of ongezaghebbend is. Het model vermeldt deze onzekerheid, maar geeft toch `source_authority: pass`.
3. **Betekenissteun: afzonderlijk modeloordeel.** De Awb-passage bevat de drie geciteerde kenmerken. Dat bewijst geen deskundigenacceptatie van de volledige gegenereerde definitie, inclusief “resultaat van besluitvorming”.

**Prompt receipt en oordeelattributie**

De bestandshash is exact de opgegeven SHA-256. Dossier-HEAD is `8f012f4129f92c91ab3e00368854fa93335bed05`. Acht relevante snapshotbestanden zijn bytegelijk aan broncommit `d17ea9c30915452914e450be315620e314c03468`.

Alle vier XML-bronblokken staan letterlijk in de opgeslagen generatieprompt; hun inhoudshashes kloppen. De beoordelingsreceipt bevat dezelfde vier passages, met correcte hashes. Alle oordeelcitaten zijn letterlijk teruggevonden. Het vierde fragment is bij generatie afgekapt; de beoordeling ontvangt die reeds verkorte tekst.

De opgeslagen attributie noemt `anthropic`, `claude-opus-4-8`, `task_type: validation`, `cached: false` en promptversie `con02-assess/1`. Dit is dus een **AI-oordeel**, technisch geaccepteerd door de code. Het dossier bevat geen volledige ruwe beoordelingsrequest/-response waarmee het providertransport onafhankelijk kan worden bewezen; van het ruwe antwoord is alleen een hash bewaard.

**Concreet relevante oorzaak**

De [beoordelingsprompt](/tmp/DEF-743-praktijk-20260917-v1/app/src/services/validation/source_assessment_service.py:97) vraagt naar precieze en beknopte terugvindbaarheid via artikel/lid/vindplaats, maar noemt de verplichte hyperlink en uitzonderingsvoorwaarden niet.

De [positieve verwijzingscontrole](/tmp/DEF-743-praktijk-20260917-v1/app/src/domain/sources/contract.py:652) accepteert vervolgens `locatable: true` met een geverifieerd citaat uit die bron. Zij controleert daarbij geen hyperlink. Deze combinatie verklaart de waargenomen fout; waar URL- of versiemetadata eerder verloren gingen, is hiermee niet vastgesteld.

**Minimale reparatie-acceptatiecriteria**

- Ditzelfde record mag zonder hyperlink en uitzondering geen gewone verwijzings-`pass` krijgen, ook wanneer het model `locatable: true` antwoordt.
- Het concrete hyperlinkgebrek blijft zichtbaar naast afzonderlijke onzekerheid over versie, herkomst en toepasselijkheid.
- Een geldige deskundige uitzondering blijft herkenbaar een uitzondering; een bruikbare interne link is toegestaan.
- Prompt, technische controle en replay volgen dezelfde voorwaarden. Verifieer dit met dezelfde invoer en een gerichte nieuwe app-probe; behoud receipts en attributie.
- Geen automatische wijziging van de definitiezin vanwege dit verwijstekort.

**Verder testen is verantwoord als diagnostisch onderzoek in de geïsoleerde omgeving.** Gebruik deze uitkomst niet als acceptatiebewijs; herstel en hertoets deze bevinding vóór positieve CON-02-acceptatie. Dit betreft één generatieprobe, niet de vaste P01-definitie. Menselijke semantische acceptatie ontbreekt; over slagen of falen van de 31 casussen volgt geen conclusie.