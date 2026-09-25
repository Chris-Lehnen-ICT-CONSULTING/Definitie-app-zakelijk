# G24 — blinde adjudicatie

Je bent de nieuwe onafhankelijke adjudicator (Astra/high). Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Gebruik geen tools. Je krijgt de originele zes synthetische dossiers, 24 blind gelabelde generaties (ruw en opgeschoond) en twee zelfstandig gevormde beoordelingen. Je krijgt GEEN oud/nieuw-mapping, appcode, prompts of automatische evaluatoruitslagen. Beoordeel geen echte rechtsbronnen.

Los de inhoudelijke discrepanties op vóór deblindering. Gebruik bronpassages, bedoelde betekenis, doelgroep en vooraf beschermde kenmerken/namen/negaties. Behoud expliciete onzekerheid wanneer je geen eenduidig oordeel kunt geven. Stem niet automatisch met meerderheid of één beoordelaar in. Expliciet en impliciet behouden verschillen van ontbrekend/tegengesproken; verzin geen nieuwe kenmerken. Bronbijzaken hoeven niet letterlijk in de definitie. Langere of kortere tekst is niet vanzelf beter. Zelfde maatstaf voor alle tekst-IDs.

De vijf assen zijn: zinsstructuur (één definitieformulering), compactheid zonder betekenisverlies, doelgroepbegrijpelijkheid, bronsteun en betekenisbehoud. Status: voldoet/tekort/onzeker. Geef alle 24 uiteindelijke tekstoordelen (ruw en opgeschoond). Als hun assen gelijk zijn, mag opgeschoond naar ruw verwijzen; geef inhoudelijk effect van opschoning expliciet. Toon elke echte discrepantie van A/B en je gemotiveerde beslissing met een tekstpassage en bron/kenmerk. Overeenstemmende oordelen hoeven geen nieuwe volledige analyse, maar signaleer aantoonbare gezamenlijke bronfouten.

Geef alle 12 gepaarde oordelen ruw en opgeschoond: X_beter/Y_beter/gelijk/onbeslist. Vermeld per richting wat inhoudelijk verbetert en of er een nieuwe bron- of betekenisfout of verslechtering ontstaat. Gemengde trade-offs blijven onbeslist. Gedeelde fouten moeten zichtbaar blijven, maar een aantoonbare inhoudelijke verbetering mag je erkennen als die geen nieuwe fout/verslechtering introduceert; stijlvoorkeur alleen rechtvaardigt geen inhoudelijke winstclaim. Geen aggregatie naar oud/nieuw; de sleutel blijft verborgen tot je oordeel vaststaat.

Lever uitsluitend geldig JSON, geen markdown:
{
 "rol":"adjudicator", "ai_beoordeeld":true,
 "teksten":[{"id":"B...","ruw":{"zinsstructuur":"...","compactheid":"...","begrijpelijkheid":"...","bronsteun":"...","betekenisbehoud":"..."},"opgeschoond":"identiek_aan_ruw OF vijf-assen-object","kernbevindingen":["brongebonden bevinding of leeg"],"opschoning_effect":"..."}],
 "discrepanties":[{"id":"tekst of paar","A":"...","B":"...","beslissing":"...","brononderbouwing":"..."}],
 "paren":[{"paar_id":"P01","ruw":"...","opgeschoond":"...","reden":"...","nieuwe_bron_of_betekenisfout_X_tov_Y":false,"nieuwe_bron_of_betekenisfout_Y_tov_X":false,"toelichting_foutvergelijking":"..."}],
 "onopgeloste_disputen":["..."],"beperkingen":["..."]
}
Alle 24 unieke tekst-IDs en alle 12 paar-IDs moeten aanwezig zijn. De uitvoer is een AI-beoordeling van een kleine verkennende proef, geen menselijke validatie of algemene kwaliteitsclaim.
