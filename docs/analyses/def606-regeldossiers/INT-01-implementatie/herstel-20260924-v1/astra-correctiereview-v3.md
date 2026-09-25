**Geen vrijgave: R1 blijft een echte blokkade na de derde herstelpoging. R2 en R3 zijn binnen de gerichte scope gesloten.**

- **R1 — open, Important; herstel vereist vóór vrijgave.**  
  [zinsgrenzen.py:637](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:637) behandelt *woord + voorzetselgroep* als bewezen onderwerp. Rechtstreeks gereproduceerd:
  - `regeling. opnieuw volgens protocol wordt toegepast` → **fail**.
  - `regeling. daarna volgens protocol wordt toegepast` → **fail**.

  Het vervolg bevat twee bepalingen, geen onderwerp. Toch luidt de reden “zelfstandige zin met kleine beginletter”. De aanname van grammaticaal correcte invoer bewijst dat niet. **Herstelanalyse-v5 erkent dit resterende probleem; dat is geen geaccepteerde waiver.** Conform opdracht stoppen de implementatiepogingen hier. De aanpak vereist een expliciet vervolgbesluit; geen vierde losse uitzondering of wijziging van proeflabels.

- **R2 — gesloten voor de gemelde fout en onderzochte tegenhangers.**  
  `die meldt “Gereed.” na gebruik volgt controle` en `die het meldt …` blijven nu onzeker, met passage en correcte puntpositie. De expliciete voortzettingen `die de melding … toont`, T17 en `… op het scherm` blijven beschermd.

- **R3 — gesloten.**  
  Citaat gevolgd door `op`, `op de`, `op het` of `–` levert onzekerheid met correcte positie, zonder uitzondering. De lengtecontrole in [zinsgrenzen.py:644](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:644) adresseert de IndexError.

T24 behoudt één zekere en één onzekere grens. Zelf **14 schrijfvrije tegenproeven** uitgevoerd; geen brede suite herhaald.

Bewijs gelezen: RED **13/99 failures**, GREEN-v2 **99/99**, lint-v3 en test-Ruff/Black groen. Brede test-v1: **7179 passed**, exit 0. **Test-v2 is niet geldig afgerond:** de log bevat een `F` en eindigt inmiddels met `Terminated: 15`; oorzaak en testidentiteit zijn daarin nog niet vastgesteld.

Hashes vóór en na gelijk; geen drift, uitsluitend de twee opgegeven bestanden gewijzigd sinds vorige review:

- Basis: `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0`
- Volledige diff-v4: `551ea1fad26bc7c20fe7fce062c458367c7ab79d3defec522247572491743a10`
- Correctiedelta-v3: `5baaf3ba528920eb16049ee11be92a9396f7a8d925ac9fb6066209dfdc6a21c6`

Geen edits, extra sessies of skillsreview. Geen effectclaim; de onafhankelijke eindproef is nog niet gestart.