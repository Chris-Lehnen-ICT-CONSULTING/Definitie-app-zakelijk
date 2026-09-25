# G24 — nieuwe onafhankelijke generatieproef: effectcriteria niet gehaald

25 september 2026. Zes nieuwe synthetische dossiers, twee herhalingen en twee varianten: 24 generatieaanroepen. Dit is een kleine AI-beoordeelde proef, geen menselijke validatie of algemene taalbetrouwbaarheidsmeting.

## Uitkomst

Van de twaalf paren zijn **twee inhoudelijk verbeterd**, **twee compacter zonder betekenisverlies**, **drie gelijk**, **twee verslechterd** en **drie onbeslist**. De ruwe en opgeschoonde teksten hebben dezelfde paaroordelen. Eén verslechtering betreft een nieuw betekenisverlies; de andere betreft herhaling en compactheid. Het criterium geen nieuwe bron-/betekenisfout en geen gepaarde verslechtering is niet gehaald. **Geen effectvrijgave.**

| Paar | Dossier / herhaling | Nieuwe tegenover oude variant |
|---|---|---|
| P01 | G05 / 2 | Verslechterd: vereiste onvolledigheidsmarkering weggevallen |
| P02 | G02 / 1 | Onbeslist: mogelijke extra registratievoorwaarde |
| P03 | G01 / 2 | Onbeslist: plaatsbeperking tegenover plaatsonafhankelijkheid |
| P04 | G02 / 2 | Inhoudelijk verbeterd: juiste koppeling van sluiting aan aanvraag |
| P05 | G03 / 1 | Gelijk |
| P06 | G05 / 1 | Verslechterd: redundante vrijgaveformulering |
| P07 | G04 / 1 | Compacter: niet-definiërende registratiebijzaak weggelaten |
| P08 | G01 / 1 | Gelijk, met gedeelde plaatsbeperking die de bron niet ondersteunt |
| P09 | G04 / 2 | Compacter: dezelfde niet-definiërende registratiebijzaak weggelaten |
| P10 | G06 / 2 | Inhoudelijk verbeterd: doelbinding en geen juistheidsbevestiging behouden |
| P11 | G06 / 1 | Onbeslist: afruil tussen doelbinding en ondubbelzinnig onmiddellijk verval |
| P12 | G03 / 2 | Gelijk |

De inhoudelijke verbeteringen zijn per paar vastgesteld. Andere herhalingen van die dossiers blijven onbeslist; er volgt geen algemene of stabiele winstclaim. Gedeelde fouten verdwijnen niet uit de rapportage doordat een paar gelijk of relatief beter is.

## Concreet resterend betekenisverlies

In G05-P01 gaat de beschikbare verzameling bij het verstrijken van de wachttijd verder **met een onvolledigheidsmarkering**. De oude tekst van herhaling 2 bevat die markering. De nieuwe tekst noemt vrijgave zodra alle pakketten aanwezig zijn of de wachttijd verstrijkt, maar laat de markering weg. De bronpassage stond volledig in beide prompts. De omissie staat al in de ruwe modeltekst en is dus niet veroorzaakt door opschoning. De gewijzigde instructies hebben dit betekenisverlies niet voorkomen.

De proef toont dit tekort; zij bewijst niet dat één specifieke instructiezin de oorzaak is. Geen nieuwe promptaanpassing of herproef is op deze set uitgevoerd.

## Onafhankelijkheid en bronbinding

- Nieuwe maker: Astra/high `01a0d535-0354-7213-81dc-9b6d9eb850a4`, zonder code, tools of eerdere uitslagen.
- Blinde eerste beoordelaars: `01a0d700-f263-7250-87e2-ecfda80babc0` en `01a0d701-04c9-7dc3-906f-54a72325d964`, Astra/high, zonder tools of kennis van variantidentiteit.
- Nieuwe blinde adjudicator: `01a0d708-089f-7ce3-9a0c-428b5b22f399`. Oordeel verzegeld vóór ontblinding. Meningsverschillen en onzekerheden zijn behouden.
- Oude bron: `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`; generatiecorrectie: `ad45a0a8af1026822d5d3ed942ca986edd11988d`. Model `claude-opus-5`, gelijke instellingen en maximaal 1.000 uitvoertokens. Alle 24 antwoorden eindigden normaal.
- Definitieve classifierbron `23cc51bfddc5ee9393dea52e6a52a55b3e65615d` heeft aantoonbaar dezelfde zes volledige generatieprompts, API-verzoeken en bronontvangstbewijzen. De offline `/6`-controle van 48 ruwe/opgeschoonde teksten levert 96 consistente serviceobservaties en 48 consistente opslagresultaten, zonder volledige INT-01-pass. Dit is technisch ketenbewijs; de inhoudelijke oordelen komen van de onafhankelijke beoordelaars.

## Kosten en vervolg

Werkelijke runkosten **US$1,99915**; cumulatief **US$5,7146**, onder het expliciet goedgekeurde plafond **US$6,50**. Er blijven US$0,7854 beschikbaar. Geen retries of extra betaalde generatiecalls.

De broncorrectie is technisch beoordeeld, maar het generatie-effect blijft open in DEF-770. Voor vrijgave is een gerichte vervolgaanpak nodig die het geconstateerde betekenisverlies oplost, gevolgd door nieuwe onafhankelijke effectmeting. Deze uitslag geeft geen toestemming voor merge of liveactivatie.

Bewijs: [vooraf vastgelegde criteria](proefafspraken-v2.md), [blinde adjudicatie](g24-adjudicatie-v1.json), [verzegeling](g24-adjudicatie-verzegeling-v1.json), [ontblinding per paar](g24-ontblinding-v1.json), [kosten en responsbinding](g24-uitvoerbinding-v1.json), [binding aan definitieve appbron](g24-contract6-binding-v1.json), [dossiers](g24-invoer-v1.json), [oude teksten](g24-nabewerking-oud-v1.json) en [nieuwe teksten](g24-nabewerking-nieuw-v1.json).
