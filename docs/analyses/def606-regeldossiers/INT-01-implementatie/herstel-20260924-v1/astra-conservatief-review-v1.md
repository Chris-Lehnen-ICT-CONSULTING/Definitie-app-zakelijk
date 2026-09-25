**Geen vrijgave: R1 blijft open — Important, fix-nu vóór vrijgave.**

[ziensgrenzen.py:633](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:633) herkent ieder toegestaan lidwoord/aanwijzend woord met extra woorden vóór de persoonsvorm als onderwerp. Dat onderscheidt een onderwerp niet van een tijdsbepaling.

Rechtstreeks gereproduceerd onder `/3`:

| Invoer | Werkelijke appuitkomst |
|---|---|
| `regeling. de hele dag wordt toegepast` | `fail` |
| `regeling. elke dag wordt toegepast` | `fail` |
| `regeling. deze week wordt toegepast` | `fail` |

De reden claimt telkens een zelfstandige tweede zin. De genoemde woordgroepen kunnen hier tijdsbepalingen zijn; een eigen onderwerp is niet bewezen. Volgens het nieuwe besluit hoort deze onzekerheid zichtbaar te blijven. **Benodigd herstel:** beperk automatische zekerheid tot daadwerkelijk onderbouwde gevallen; behandel deze ambigue constructies als onzeker. Alleen een lidwoordgroep aantreffen volstaat niet.

Verder binnen scope:

- Het verworpen woord-plus-voorzetselgroep-patroon is verwijderd. De oude T24-tekst geeft correct twee onzekere grenzen; de aangepaste testverwachting volgt het expliciete besluit.
- `/3` gebruikt de bestaande versiebinding. Tests dekken niet-actuele `/1`- en `/2`-uitkomsten, weergave, historie en opslag.
- Ongewijzigd R2/R3-bewijs blijft geldig.
- Geen afzonderlijke bevinding in de skillregel, proefafspraken-v2 of referentie-contract-v2. Zij scheiden normatieve labels van automatische verwachtingen en staan vals-zekere beslissingen niet toe.

Gelezen bewijs: RED **11 failures/184 tests**, GREEN **184/184**, lint exit 0. Zelf zeven schrijfvrije segmentatieproeven uitgevoerd. Brede gate en bundelbuild blijven nog uit te voeren; geen effectclaim.

Alle manifesthashes kloppen vóór en na review; geen drift:

- Appbasis: `1c879427b729c6aaa26f830565a83ea55d6a2250`
- Appdelta: `269320dce743f639310f4dbb0d6c8eac84ef1080b69155124ab00ff69daddae7`
- Skillsbasis: `0e2b5e914483800d14bdffc90be0af2a98bd999d`
- Skillsdelta: `2a9899fa4f9bd57605e7db86a0108da6c10f96c21bebbe4e5452df5e7376db85`

Geen edits, delegatie, betaalde calls of live activatie.