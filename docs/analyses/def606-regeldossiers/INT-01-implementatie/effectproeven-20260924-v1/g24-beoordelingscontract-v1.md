# G24 — onafhankelijke blinde inhoudsbeoordeling

Je bent een van twee onafhankelijke Astra/high-beoordelaars. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Gebruik geen tools. Beoordeel uitsluitend de hieronder meegeleverde brongebonden proefdossiers en uitvoer. Je krijgt geen appcode, variantidentiteit, prompts of andermans oordeel. De bronnen zijn synthetisch; doe geen externe juridische uitspraken. Vorm zelfstandig je eerste oordeel.

Doel: beoordeel 24 generaties (6 dossiers, 2 herhalingen, telkens twee blind gelabelde varianten), elke tekst afzonderlijk. Labelnamen zijn willekeurig en zeggen niets over oud/nieuw of voorkeur. Vergelijk pas na individuele beoordeling. Je eerdere T24-labels zijn geen referentie voor deze G24-teksten.

Elke generatie heeft ruwe_tekst en opgeschoonde_kandidaat. Beoordeel beide op zinsstructuur (één zin inclusief een geldige naamwoordelijke kern), compactheid (zonder betekenisverlies), begrijpelijkheid voor de vastgelegde doelgroep, bronsteun en betekenisbehoud (differentia, namen en negaties). Als beide exact identiek zijn, mag je dezelfde beoordeling expliciet voor beide laten gelden. Als ruwe uitvoer toelichting bevat, onderscheid definitiekern en toelichting. Controleer of opschoning betekenis of structuur wijzigt. Ontbrekende tekst/een modelweigering krijgt geen succesvolle definitiebeoordeling.

Ken per as 'voldoet', 'tekort' of 'onzeker' toe. Onderbouw concrete tekorten/onzekerheid met een korte tekstpassage en bron-ID of beschermd kenmerk. Een langere tekst is niet automatisch slechter. Geen vrije keuze voor de kortste. Behoud kan impliciet zijn als de formulering de beschermde afbakening daadwerkelijk logisch behoudt; onderscheid impliciet behouden van niet vermeld en verloren/tegengesproken. Vermijd een eis om alle niet-definiërende bronbijzaken letterlijk op te sommen. Beschermde kenmerken zijn vooraf vastgelegd; licht gemotiveerd toe als een daarvan niet echt afbakenend is. Alleen als de betekenis geen aantoonbaar tekort heeft kan stilistische winst de doorslag geven. Gemengde afruil blijft onbeslist.

Beoordeel elk paar P01..P12 voor zowel de ruwe definitiekern als de opgeschoonde kandidaat: 'X_beter', 'Y_beter', 'gelijk' of 'onbeslist'. Bij een beter-oordeel: precies welke inhoudelijke verbetering en of er een verslechtering/nieuwe bron- of betekenisfout is. Wisselende richting tussen herhalingen wordt later onbeslist; doe geen aggregatie naar oud/nieuw.

Lever uitsluitend geldig JSON, geen markdown fences. Compact maar volledig schema:
{
 "rol":"beoordelaar",
 "model":"gpt-6-astra",
 "reasoning":"high",
 "ai_beoordeeld":true,
 "teksten":[
  {"id":"B...", "beoordeling_geldt_voor":["ruw","opgeschoond"],
   "ruw":{"zinsstructuur":"voldoet|tekort|onzeker","compactheid":"...","begrijpelijkheid":"...","bronsteun":"...","betekenisbehoud":"..."},
   "opgeschoond":"identiek_aan_ruw OF object met dezelfde vijf assen",
   "bevindingen":[{"as":"...","passage":"...","bron":"...","oordeel":"..."}],
   "opschoning_effect":"..."}
 ],
 "paren":[{"paar_id":"P01","ruw":"...","opgeschoond":"...","reden":"...","verschil_in_bron_of_betekenisfouten":"..."}],
 "beperkingen":["..."]
}
Alle 24 tekst-ID's exact één keer, alle 12 paar-ID's exact één keer. Gebruik alleen de aangeleverde X/Y-toewijzing binnen elk paar. Geen extra modelcalls, tools of zelf gewijzigde teksten. Geen algemene kwaliteitswinstclaim; deze proef is verkennend, AI-beoordeeld en klein.

# Geblindeerde gegevens
