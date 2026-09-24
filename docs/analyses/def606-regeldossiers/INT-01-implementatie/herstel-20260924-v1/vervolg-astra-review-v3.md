**R2 gesloten. R1 blijft Important en blokkeert zowel classifierveiligheid als volledige acceptatie. Geen vierde heuristische correctieronde.**

- **R1: resterende onbewezen zinsstructuur-pass.**  
  Schrijfvrij gereproduceerd:  
  `kaart met de titel ‘Klaar?’ waarop het werkt de deelnemers wachten`  
  krijgt zinsstructuur-pass zonder onzekerheidsdeel; hetzelfde gebeurt met `dit werkt`. [zinsgrenzen.py:664](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:664) behandelt `het`/`dit` als naamwoordmarkering en `werkt` vervolgens als naamwoordkern. Hier kunnen zij juist voornaamwoord en persoonsvorm zijn, gevolgd door de zelfstandige mededeling `de deelnemers wachten`. De gemarkeerde groepen bewijzen dus nog steeds geen enkelvoudige bijzin.  
  **Dispositie:** open blocker binnen DEF-770; na drie pogingen codewerk stoppen. Verantwoorde positieve herkenning vraagt een andere bewijsbasis voor syntactische rollen, geen volgende losse uitzondering. De overeenkomstige positieve skillsclaim is hiermee evenmin onderbouwd.

- **T20-functioneelcriterium blijft afzonderlijk open.**  
  De oorspronkelijke tekst wordt nu onzeker terwijl de referentie pass blijft. De vijf tests zijn zichtbaar `strict=True` xfail; referentieteksten, labels en serviceverwachtingen zijn AST-gelijk gebleven. Dit registreert het tekort eerlijk, maar is geen waiver of acceptatiebewijs.

- **R2/T24: gesloten binnen de gerichte scope.**  
  Onderdrukking en vervangende melding gebruiken dezelfde vermelding. Gecontroleerd: nul/één/meerdere spaties, tab, newline, dubbele haakjes, latere afkortingsgrens en duidelijke volgende zin. Geen onterechte pass; latere grenzen blijven zichtbaar. Oorspronkelijke T24 behoudt de aansluitingsgrond.

Generatiebron en Nederlandse-definities-skill zijn bytegelijk. Hun eerdere bronreview blijft geldig; afzonderlijk generatieonderzoek kan daarop voortbouwen zonder classifier- of effectvrijgave te impliceren.

Bewijs: **364 tests = 359 geslaagd + vijf T20-xfail**; regressie 1189 totaal met tien skips/xfails. Gepinde lint groen. Zelf dertien korte classifierproeven; geen brede suite. De v3-brede gate en actuele bundels zijn hiermee niet bevestigd.

Manifest, patches en bronhashes vóór/na gecontroleerd; geen drift. Bases: app `7ee7d7d293770dd86f2dd70f1b4945b25ead3c94`, skills `ed0fcfdcc169c37058f0436fc92c1e07752366b8`.

- Appdiff SHA256: `e32225176a9d70afb5b3592d126a0963daae1180125e88bd4034a7c508957e77`
- Skillsdiff SHA256: `68b489b6929c0fa0c0d5ef0e9b971be4822fc709baf77df32e169455bb053894`

Geen edits, modelcalls, nieuwe proefinhoud of effectclaim.