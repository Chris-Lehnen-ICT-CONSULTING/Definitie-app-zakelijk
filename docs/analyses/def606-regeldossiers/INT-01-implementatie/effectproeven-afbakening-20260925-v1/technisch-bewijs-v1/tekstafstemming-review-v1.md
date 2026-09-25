**Important-broninconsistentie gesloten. Bronvrijgave voor de proefvoorbereiding; geen nieuwe inhoudelijke bevindingen.**

- `INT-01.json:5` en de skillpassage **Toetsen** begrenzen onzekerheid nu overeenkomstig het besluit: onbekende betekenis aan het teksteinde bewijst op zichzelf geen grens of afbreking. Toegankelijkheid blijft bij INT-07. Geen algemene afkortingsvrijstelling of volledige INT-01-pass toegevoegd.
- Alleen de toelichting en corresponderende skilltekst wijzigen. Runtime, tests en generatiecode/configuratie blijven gelijk. **6/6 volledige prompts én requests** zijn bytegelijk aan HEAD en eerder G24-bewijs.
- Diff en bronhashes vóór/na gelijk. Patch-SHA256:  
  `83fdbae707472b3479d04f7d9e745ce7b400895b40a8cb91a469c625450360bb`

**Bewijsnuance:** JUnit registreert **944 tests totaal: 939 geslaagd, 5 overgeslagen**, nul failures/errors; exit 0. Dus niet 944 geslaagd plus vijf skips. Tekstcontrole en lint zijn groen.

**Nog open:** verouderde `toetsregels.zip` — skilltests 30 geslaagd, één bekende packagingfailure. Bundels herbouwen en controleren vóór publicatie. De afgeleide tar bevat uitsluitend het gewijzigde regelrecord, maar is **geen committed bron**, ondanks de behouden HEAD-header; nieuwe commit/freeze volgt.

Geen effect- of mergevrijgave. Geen edits, tests of betaalde calls uitgevoerd.