**Gerichte publicatievrijgave; geen bevindingen.**

- Alle zes waarden zelfstandig herberekend met de canonieke JSON-serialisatie uit `effectproef_bron.py`: het zijn verzoekbody-hashes, geen authenticatiegegevens.
- Exact zes vervangingen bevestigd. Alle overige bytes, promptvingerafdrukken, pariteitsuitkomsten en exitstatus zijn behouden.
- Het origineel bestaat nog lokaal en staat niet in staging. Geen gewijzigde scannerconfiguratie, allowlist of hooks aangetroffen.
- Bewijsbinding v2 klopt. Eindstand v2 wijzigt uitsluitend verwijzingen en redactietoelichting; inhoudelijke acceptatieclaims blijven gelijk.

SHA256 publicatiekopie:
`1999c093f84a6496de3bb281cf08ccccd10b4eebfffdcf661f38a40b19b95e87`

SHA256 eindstand v2:
`ea124029d5963dda1dce72ad9040d9ea11fb5c1b5b8c8d836a3b73158731a447`

De normale commitcontrole blijft vereist; die verklaar ik hier niet geslaagd. Geen edits, tests of modelcalls uitgevoerd.