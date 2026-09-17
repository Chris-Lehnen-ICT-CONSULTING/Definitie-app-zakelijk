**Niet gereed: twee concrete bevindingen, lokaal gereproduceerd zonder modelcalls.**

1. **P1 — Eén gelinkte bron maskeert een noodzakelijke bron zonder hyperlink.**  
   [contract.py:759](/private/tmp/DEF-806-hyperlink-20260917/src/domain/sources/contract.py:759) accepteert zodra *één* dragende bron een link heeft. De [menselijke correctieroute](/private/tmp/DEF-806-hyperlink-20260917/src/domain/sources/contract.py:1217) doet hetzelfde.  
   **Bewijs:** twee bronnen ondersteunen elk een afzonderlijk noodzakelijk kenmerk; beide hebben geverifieerde citaten en `locatable:true`. Bron A heeft geen URL, B wel. Replay levert drie keer `pass`, zonder uitzondering. Een menselijke verwijzingscorrectie wordt eveneens toegepast als `pass`.  
   **Minimale correctie:** controleer de hyperlink per noodzakelijke bewijsbron; B mag het ontbreken bij A niet opheffen. Voeg regressies toe voor deze combinatie, inclusief menselijke correctie. De huidige test met een andere, ongeciteerde bron dekt dit niet.

2. **P2 — Niet-lege tekst geldt ten onrechte als bruikbare hyperlink.**  
   [contract.py:764](/private/tmp/DEF-806-hyperlink-20260917/src/domain/sources/contract.py:764) controleert uitsluitend `bool(bron.url)`.  
   **Bewijs:** dezelfde record4-gebaseerde fixture geeft met `url=None` terecht `review_required`, maar met `url="https://"` of `"geen hyperlink"` gewoon `pass`.  
   **Minimale correctie:** valideer minimaal type en syntaxis van ondersteunde linkvormen, met behoud van interne links. Gebruik dezelfde bruikbaarheidsdefinitie bij AI-oordelen, menselijke correcties en uitzonderingen; voeg negatieve URL-tests toe. Hiervoor is geen netwerkcontrole nodig.

De beschreven editorweergave vormt **geen afzonderlijke blocker**: de canonieke uitkomst is open met concrete reden, terwijl het oorspronkelijke oordeel expliciet als AI-beoordeling met promptversie en “geen vaststelling” wordt getoond.

Afsluitcontrole: **alle 10 filehashes stemmen overeen** met `review-diff-identiteit.json`, tegen base `d17ea9c30915452914e450be315620e314c03468`. De groene tests dekken bovenstaande tegenvoorbeelden niet. Menselijke P01-acceptatie blijft afzonderlijk open.