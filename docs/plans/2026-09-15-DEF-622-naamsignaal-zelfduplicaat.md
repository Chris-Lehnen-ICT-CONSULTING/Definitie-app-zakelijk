# DEF-622 — herstel R1 en R2 na implementatiecontrole

Chris rapporteerde op 15 september 2026 twee uitvoerbaar aangetoonde gaten op gemergede PR451. Dit vervolg herstelt die gaten binnen DEF-622, met R2 als afgebakende koppeling aan DEF-677. Basis: mergecommit `6dc1e6ae87cc8020daf7abd46c6c6aad74bee4ce` (dezelfde tree als `a2f5f97cf`). Branch: `bugfix/DEF-622-naamsignaal-zelfduplicaat`.

Bronnen: actuele issues [DEF-622](https://linear.app/definitie-app/issue/DEF-622), [DEF-677](https://linear.app/definitie-app/issue/DEF-677) en [DEF-630](https://linear.app/definitie-app/issue/DEF-630), opgehaald 15 september 2026; onafhankelijke controle in de CON-01-onderzoekswerkboom onder `implementatiecontrole-20260915-v1/controle.md`. De coördinator heeft de oorspronkelijke domein-/SQLite- en Streamlit-proeven opnieuw uitgevoerd tegen de ongewijzigde productiecode: dezelfde drie bevindingen. Resultaten lokaal onder `reports/def622/r1-r2/baseline-*.json` en `.log`.

## R1 — foutief naamsignaal gemotiveerd afhandelen

Voeg in het bestaande domeincontract en de expertweergave de keuze ‘Dit is geen contextvermelding’ toe. Een mens kan daarmee bijvoorbeeld bevestigen dat gewoon ‘om’ geen verwijzing naar de vastgelegde context ‘OM’ is. Die beslissing levert voor de betreffende treffer `pass`, zonder noodzakelijke-naamclaim en zonder CON-01-cijfer. De zichtbare reden moet overeenkomen met de gekozen functie.

Behoud actor, motivering, exacte inhoudsvingerafdruk en strikte versiecontrole; ontbrekende/onbruikbare of verouderde beoordeling blijft open. Andere treffers blijven onafhankelijk te beoordelen. Geen automatische hoofdletteruitzondering en geen vierde regelstatus. Bewijs omvat domeingrenzen en echte Streamlit-keuze, opslag/readback en hertoetsing.

## R2 — eigen record uitsluiten, andere duplicaten blijven vinden

Gebruik de door ValidationOrchestratorV2 aangeleverde `definition_id` bij de kandidaatvergelijking. Sla uitsluitend aantoonbaar hetzelfde opgeslagen record over en doorloop daarna de overige kandidaten. Een ongeldige/ontbrekende eigen ID mag geen ander record uitsluiten. Behoud context- en categorievergelijking en de volledige kandidaatset.

Bewijs via echte V2-productiebedrading en tijdelijke SQLite: alleen eigen record, eigen record plus tweede echt duplicaat (ook eigen eerst), en nieuw voorstel zonder eigen ID. Andere DEF-677-vraagstukken over capability, severity en runtimecontract blijven open.

## Uitvoering en bewijsgrenzen

Claude CLI schrijft eerst onderscheidende regressietests; de desktop voert RED uit. Daarna implementeert dezelfde sessie de minimale correcties. De desktop voert GREEN, relevante bestaande regressies en projectgates uit; een afzonderlijke Codex CLI beoordeelt de concrete diff onafhankelijk. Normale hooks blijven actief. Tests gebruiken uitsluitend offline_bootstrap en synthetische tijdelijke databases. Nieuwe PR blijft draft tot afzonderlijke mergeopdracht.

R3 blijft bestaand herstelwerk in DEF-630: onder de standaardpolicy kan ontbrekend validatiebewijs via een handmatige notitie worden overruled. Positieve CON-01-proeven bewijzen dus geen algemeen gesloten vaststel-/exportcontract. De globale skillpatch is niet geïnstalleerd; automatisch CON-tekstherstel blijft DEF-638. Dit herstelpakket sluit DEF-622 of DEF-677 niet als geheel.
