**P1 gesloten; P2 nog niet volledig gesloten. Diff nog niet gereed.**

**P2 — Ongeldige poorten worden als bruikbare hyperlink geaccepteerd.**  
[contract.py:795](/private/tmp/DEF-806-hyperlink-20260917/src/domain/sources/contract.py:795) controleert schema en hostname, maar leest `delen.port` niet. Daardoor blijven deze URLs positief:

- `https://intern.example:ongeldig/awb`
- `https://intern.example:99999/awb`

**Lokaal gereproduceerd:** beide geven `is_bruikbare_hyperlink=True` en `reference_quality=pass`. Bij de eerste wordt bovendien de expliciete uitzondering geweigerd omdat de bron volgens de helper een bruikbare link heeft. Het gedeelde UI-filter sluit die bron eveneens uit.

**Minimale correctie:** valideer ook `delen.port` binnen de `ValueError`-afhandeling. Voeg regressies toe voor niet-numerieke/buitenbereikpoorten en behoud geldige intranetlinks, ook met expliciete poort.

**P1:** de gerichte controles voor gemengde bronnen, beide bronnen gelinkt en menselijke correctie slagen nu. De link van B heft het ontbreken bij A niet meer op.

**Bewijsgrenzen:** 43 gerichte tests zijn groen; de finale volledige suite liep bij afsluiten nog. Record5 toont verwijzing open met de ontbrekende-hyperlinkreden onder `con02-assess/2`, maar is gegenereerd met de eerste patch. Definitieve readback/replay van record4+5 en menselijke P01-acceptatie blijven afzonderlijk open.

**Eindcontrole:** alle **11 hashes** matchen `review-diff-identiteit-v3.json`; base klopt en de prompt is bytegelijk gebleven. Geen bronwijzigingen of modelcalls uitgevoerd.