**Gerichte delta akkoord; de bevinding over het verdwijnende naamveld is gesloten.** Geen resterende bevindingen binnen deze correctie.

- **HEAD:** `503bbe04d0804e774748784166a93f82c21c873c`
- **Beoordeeld:** `c18a7ec3..503bbe04`, uitsluitend de identiteitlookup, renderconditie en bijbehorend testbewijs.
- Het naamveld hangt niet langer af van zijn eigen waarde. De ingevoerde actor wordt doorgegeven; een ingelogde identiteit behoudt voorrang.
- De AppTest dekt echte widgetcleanup, meerdere reruns en opslag/readback. Zelf de vijf testasserties tegen de opgeslagen waarnemingen gecontroleerd: RED faalt op naambehoud en opslag; GREEN slaagt volledig. De AppTest-driver is niet opnieuw uitgevoerd.

Werkboom schoon; niets gewijzigd. Volledige suite v2 en browserhertoets blijven afzonderlijk open. Bestaande P2/LOW blijven gesloten; de voorstelsectie blijft buiten scope.