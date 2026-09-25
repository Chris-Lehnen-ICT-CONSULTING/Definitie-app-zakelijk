**Nog geen bronvrijgave: R1 blijft gedeeltelijk open; R2 is gesloten.**

- **R1 — Important, fix-nu.** De eerdere repro’s `(Stop!)`, `(Wacht.)` en `(De registratie sluit in dec.)` worden nu correct onzeker. Maar de nieuwe uitzondering in [zinsgrenzen.py:435](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:435) behandelt iedere consonantvorm als bewezen afkortingsfragment. Schrijfvrij gereproduceerd: `register voor deelnemers (Psst!)` en dezelfde tekst met `(Brr!)` krijgen **zinsstructuur-pass zonder onzekerheidsdeel**. Zulke zelfstandige uitroepen zijn niet door hun spelling uitgesloten. [Regel 419](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:419) maakt hier opnieuw een onbewezen positieve deelclaim.  
  **Herstel:** beperk de fragmentvrijstelling tot aantoonbare fragmentpatronen; een onbekende consonantvorm alleen bewijst geen afkortingsfunctie. Deze tegenhangers moeten onzeker blijven, met behoud van de beschermde getal-/afkortingsfragmenten. Geen woordwhitelist nodig.

- **R2 — gesloten.** `Chr. Huygens`, `Nvr. Nieuwe` en `NVR. Nieuwe` leveren nu onzekerheid met passage/positie. Gewone woorden vóór een duidelijk nieuw zinsbegin blijven zeker fail.

T17/T20 blijven correct op de oorspronkelijke teksten; hun citaatfuncties zijn AST-gelijk aan de eerder beoordeelde versie. `/4` en de uitsluiting van oude versies blijven intact. Kleineletteronzekerheid en afzonderlijk open compactheid/begrijpelijkheid blijven behouden. Skillsidentiteit is ongewijzigd.

Gelezen bewijs: **RED 17/259, definitief GREEN 259/259**, inclusief beide laadpaden; `make lint` exit 0. Zelf alleen korte schrijfvrije tegenproeven uitgevoerd. De brede rootgate is niet uitgevoerd of als voltooid aangemerkt.

Base `6c18ce7127f0a785fefdd6bc952175a030be8643`; alle manifesthashes vóór/na gelijk, actuele app- en skillsdiffs gebonden:

- App SHA256: `03853484c22f57748013f159ad488ace7391cd318d73bcb6f3e79173a01c717f`
- Skills SHA256: `8ae7c7c280c916843c2bd6ed60e968b2139eef44e6bc133a4da269153abacdec`

Geen edits, effectclaim of inzage in de quarantaineset.