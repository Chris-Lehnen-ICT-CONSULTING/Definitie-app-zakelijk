# Beslispunt: grens van automatische titelbeoordeling

## Aanleiding en vastgestelde stand

De laatste gerichte Codex CLI-review op Astra/high (logs/def770-vervolg/astra-review-v3.md) sluit de afkortingsbevinding T24. De titelherkenning T20 blijft onveilig: een vervolg met verwisselde woordrollen kan nog een onbewezen zins-pass krijgen. Drie gerichte correctiepogingen zijn benut. AGENTS.md verlangt daarna stoppen en de oorzaak/aanpak herbeoordelen; er volgt geen vierde variatie op dezelfde heuristiek.

Oorspronkelijke definitietekst:

> Spelkaart met de titel ‘Wie woont hier?’ waarop aanwijzingen voor een fictief dierverblijf staan.

De inhoudelijke referentie beoordeelt dit als één formulering. De eerdere automatische verwachting is eveneens pass. De huidige techniek kan de daarvoor noodzakelijke woordrollen echter niet betrouwbaar vaststellen. De vijf bijbehorende ontwikkeltests staan zichtbaar als strikte verwachte mislukkingen; historische referenties zijn niet aangepast. Dit vormt geen acceptatievrijgave.

Een door de reviewer gereproduceerd tegenvoorbeeld:

> kaart met de titel ‘Klaar?’ waarop het werkt de deelnemers wachten

Hier worden het/werkt ten onrechte als naamwoordgroep behandeld. Een lijst werkwoorduitgangen of naamwoordmarkeringen geeft geen voldoende onderscheidend bewijs.

## Voorgestelde richting — inhoudelijke beoordeling

Schakel de nieuw toegevoegde automatische positieve herkenning van deze voortzettingen na een titel/citaat uit. Ze volgen de bestaande route voor inhoudelijke beoordeling. Handhaaf veilige reeds bestaande detecties en de afzonderlijk herstelde afkortingsmelding. Werk appinstructie, skills en actuele ontwikkeltests daarmee gelijk. Een inhoudelijk beoordelaar kan voor de oorspronkelijke titelzin nog steeds zins-pass vaststellen; de automatische controle claimt dat niet.

Deze keuze verandert de gewenste automatische uitkomst voor deze klasse. Daarom wordt dit als nieuw expliciet besluit voorgelegd. Oude proefuitslagen, normatieve labels en automatische referenties blijven onveranderd historisch bewijs. Een nieuwe generieke afbakening wordt vóór de nog afgeschermde onafhankelijke acceptatie vastgesteld; geen score wordt achteraf verbeterd door labels om te zetten. Nieuwe acceptatie rapporteert opnieuw dekking en doorverwijzingen.

## Alternatief — aanvullende taalkundige ondersteuning

Onderzoek eerst welke lexicalische of syntactische ondersteuning de noodzakelijke woordrollen kan leveren, welke fouten en onzekerheden blijven en wat integratie kost. Daarna een concreet ontwerpbesluit, eventueel met nieuwe dependency/modelbron. Er is nog geen techniek geselecteerd of betrouwbaarheid aangetoond. Dit is een andere aanpak dan nog een regexuitzondering.

## Onafhankelijk uitvoerbaar

De bronreview van de generatiecorrectie blijft geldig: deze bron is gedurende de drie correcties bytegelijk gebleven. Generatieonderzoek en de voorbereiding van een nieuwe G24-proef kunnen doorgaan zonder titel- of totale acceptatievrijgave. Betaalde uitvoering blijft afhankelijk van een concrete tokenraming binnen het bestaande kostenplafond of aanvullend mandaat. Geen merge of liveactivatie.
