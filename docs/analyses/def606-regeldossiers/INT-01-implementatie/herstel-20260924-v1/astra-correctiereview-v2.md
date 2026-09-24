**Nog geen akkoord: R1/R2 blijven gedeeltelijk open; daarnaast één nieuwe fout. Alle drie Important, fix-nu.**

- **R1 — onderwerp nog niet bewezen.**  
  [zinsgrenzen.py:605](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:605): `regeling. opnieuw wordt toegepast` geeft **fail**, met de claim “zelfstandige zin”. `Opnieuw` is geen onderwerp. Dit is de directe tegenhanger van het inmiddels beschermde `uitsluitend wordt toegepast`. Laat een onbewezen onderwerp onzeker; afwezigheid van een werkwoordelijke vorm bewijst geen onderwerp.

- **R2 — korte bijzinmarkering bewijst geen open bijzin.**  
  [zinsgrenzen.py:448](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:448): `code die meldt “Gereed.” na gebruik volgt controle` geeft **zinsstructuur pass**, zonder grens. `Die meldt` wordt als markering plus lijdend voorwerp behandeld; vervolgens geldt het voorzetselbegin als voortzetting, terwijl `na gebruik volgt controle` een zelfstandige vervolgzin is. Laat deze onbewezen voortzetting onzeker; behoud de expliciete geldige citaatgevallen.

- **Nieuwe regressie — onvolledige voortzetting veroorzaakt uitzondering.**  
  [zinsgrenzen.py:421](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:421): `code met de melding “Gereed.” op` veroorzaakt **`IndexError: list index out of range`** door `woorden[1]` bij één token. Controleer de minimumlengte en retourneer onzekerheid met passage/positie.

De **vier vorige repro’s zijn wel hersteld**: alle vier blijven onzeker met correcte puntpositie. T24 behoudt één zekere en één onzekere grens. De gecontroleerde voortzettingen `… toont`, `… op het scherm` en T17 blijven beschermd. Dit vraagt geen taalgarantie; bovenstaande fouten zijn rechtstreeks gereproduceerde nabije tegenhangers.

Bewijs gelezen: RED **11/81 failures**, GREEN **81/81**, brede gate **7161 passed, 75 skipped, 1 xfailed**, exit 0; lint en test-Ruff/Black groen. Zelf elf schrijfvrije segmentatieproeven uitgevoerd, geen brede suite herhaald.

Hashbinding vóór en na correct; uitsluitend de twee opgegeven bestanden verschillen van manifest-v2:

- Basis: `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0`
- Volledige diff-v3 SHA256: `60af7f144235e4ed10be7af41224b50f923c63bb7240ee83320171d0f1a7b209`
- Correctiedelta-v2 SHA256: `fe312ede6e0a45bbc2f7f095abcce6e55fe425ca19192dab9dfc247b190b12b6`

Geen bronwijzigingen of nieuwe skillsreview. Geen effectclaim; de onafhankelijke eindproef moet nog volgen.