# ESS-03 — resterende browseracceptatie na correctieronde

Dit is een vooraf vastgelegde controlelijst, geen resultaatbewijs. Coördinator bedient uitsluitend via cua_repl; uitvoerbare testcode blijft bij Claude CLI. Herstart de lokale app op de technisch gereviewde bronstand voordat de correcties als werkend worden beschreven. Gebruik de bestaande synthetische lokale recordset; behoud bestaande gegevens. Geen zelfstandige bronzoekactie voor ESS-03.

1. Open de eerder opgeslagen synthetische kleurpasta-record. Een fase1-oordeel met oude prompt/binding mag na de promptversiewijziging niet als actueel verschijnen. Leg bronversie, zichtbaar label en historievermelding vast.
2. Gebruik een afzonderlijk synthetisch ontwikkelgeval voor een ontbrekende registratieconventie (geen onafhankelijke eindtestdata). Toets in de editor en controleer expliciet label Onvoldoende informatie, één gerichte vraag, reden, bewijs en modelherkomst. Geen automatische wijziging van de definitie.
3. Beantwoord de vraag met de vooraf vastgelegde synthetische conventie, toets opnieuw, sla op en heropen. Controleer dat de nieuwe verduidelijking bewaard is en het actuele oordeel op die gegevens berust. Bewaar de eerste modeluitkomst ook bij een afwijkend label.
4. Wis de verduidelijking bewust en sla op zonder eerst opnieuw te toetsen. Heropen en controleer dat het veld leeg blijft en het oude oordeel niet actueel is. Dit gebruikt geen extra AI-call.
5. Gebruik een bekend ontwikkelgeval met een bewezen identificatiedefect, controleer zichtbaar Voldoet niet en geen ESS03-cijfer. Controleer de relevante vaststel-/exportactie voor zover andere regels deze specifieke invoer niet terecht blokkeren. Een blokkade door een andere regel is geen bewijs van ESS03-blokkering. De volledig gekoppelde technische actietests zijn aanvullend bewijs; stel een daadwerkelijke UI-actielimiet expliciet vast als die overblijft.
6. De technische foutpresentatie en volledige readbackmatrix worden via de door Claude geschreven tests gecontroleerd. Bewijs uit mockweergave niet beschrijven als een echte providerstoring in de browser.

Voorgenomen aantal nieuwe browserbeoordelingen: drie, eventueel één noodzakelijke gerichte hercontrole binnen de resterende callruimte. Controleer vóór uitvoering het bijgewerkte totale pogingentellerbudget (initieel60); bestaande browserfase1 telt14 logische beoordelingen en conservatief15 transportpogingen inclusief eerste ontwikkeling. Geen extra beoordelingscalls voor louter visuele herhaling.

Bestaande beperking: nieuw geïnitialiseerde testdatabase mist definitie_drafts; autosave meldt een fout, handmatig opslaan heeft gewerkt. Geen brede schemafix of bestaande migratie met DELETE uitvoeren binnen deze opdracht. Benoem wat deze beperking betekent voor de uitgevoerde route.
