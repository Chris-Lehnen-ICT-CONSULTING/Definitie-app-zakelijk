**Akkoord voor deze concrete correctiedelta. R1 gesloten; geen nieuwe bevindingen of inhoudelijke blockers binnen scope.**

- **R1:** [zinsgrenzen.py:517](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:517) bevat geen kleineletter-zekerheidsheuristiek meer. De drie tijdsbepalingen, lidwoordgroep en historische T24-tekst geven onzekerheid met correcte grensposities.
- **R2/R3:** behouden. AST-vergelijking met de vorige gebonden bron bevestigt dat de gedeelde citaatfuncties en constanten ongewijzigd zijn. Verwijderde helpers hebben geen resterende verwijzingen.
- Gewone hoofdlettergrenzen blijven `fail`; ononderbroken formuleringen kunnen zinsstructuur-pass krijgen. Afkortingen en getallen blijven beschermd. Geen volledige INT-01-pass.
- `/3`-binding blijft intact. Testwijzigingen volgen de expliciete conservatieve afbakening. De skillregel, proefafspraken-v3 en referentie-contract-v3 sluiten daarop aan; geen afzonderlijke bevinding.

Bewijs: RED **11 failures/191 tests**, GREEN **191/191**, lint exit 0. Zelf **12 schrijfvrije tegenproeven**, AST-vergelijking en verwijzingscontrole uitgevoerd.

Hashes vóór en na correct; geen drift:

| Identiteit | SHA |
|---|---|
| Appbasis | `1c879427b729c6aaa26f830565a83ea55d6a2250` |
| Appdelta-v2 SHA256 | `edc95504b9ada37c59bec1ffc346b380616e14f49b51d50271114c8008d83654` |
| Skillsdelta-v2 SHA256 | `8c95977e2915d8eced88b0d6718149b1d162bc8ff354da05da117fc70af17f92` |

Dit is vrijgave van de beoordeelde broncorrectie. De onafhankelijke brede gate en nieuwe bundelbuild zijn hiermee niet afgetekend. Geen effectwinstclaim; de nieuwe eindproef moet nog volgen. Geen edits, extra sessies of live activatie.