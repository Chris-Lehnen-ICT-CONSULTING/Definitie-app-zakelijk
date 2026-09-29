# DEF-771 — takenlijst v9: voorbereiding op merge

Voortzetting van takenlijst-v8. Chris vraagt of de O1-basis al gemergd kan worden. De coördinator bereidt een concreet mergevoorstel voor; daadwerkelijke PR-merges en actieve skillpublicatie wachten op expliciet akkoord.

- [x] Aanvullend ketenbewijs en gesloten onafhankelijke review vastgelegd en gepusht: appcommit b56e2878268f744f224e8d1326c9198378b025bc.
- [x] Actuele main opgehaald; app 076c916671e4e7e9f2843d22669df38eeb79e170, skills 770de55ece429fec826c9d53fd873a109ed8e670.
- [x] Samenloop vastgesteld: één app-promptconflict, vier skilltekstconflicten en twee ZIP-conflicten met INT-03.
- [x] Volledige integratieopdracht opgeslagen en naar dezelfde Claude Code CLI-uitvoerder gestuurd. De bestaande omvangverruiming geldt.
- [ ] Beide featurebranches integreren met main; beide INT-02/INT-03-instructies behouden, contractkopieën en ZIP's verifiëren.
- [ ] Gerichte tests, ongewijzigde ketenproef v3 en lint op de geïntegreerde bron controleren.
- [ ] Gewone integratiecommits maken op beide featurebranches.
- [ ] Volledige offline pytest draaien; failures letterlijk melden en concrete nieuwe afwijkingen onderzoeken.
- [ ] Dezelfde onafhankelijke Codex CLI-reviewer controleert de concrete integratie.
- [ ] Bewijs, PR-beschrijvingen en DEF-771-oplevercomment actualiseren; concreet mergevoorstel aan Chris.
- [ ] Na expliciet akkoord: beide PR's regulier mergen en apart geaccordeerde actieve skillpublicatie uitvoeren.

Open vervolg blijft: gedeelde gewone opslag/herlaadketen (DEF-626), O2 (DEF-835), effectmeting en eerder vastgelegde grenzen. Geen zelfstandig INT-02-poort-/herstelbeleid, geen legacyverwijdering. Skill-CI is op verzoek disabled_manually; dat is geen geslaagde CI-run.
