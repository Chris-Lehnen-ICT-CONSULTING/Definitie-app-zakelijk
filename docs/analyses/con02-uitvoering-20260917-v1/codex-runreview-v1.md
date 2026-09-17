**De helper levert bruikbaar bewijs op component- en serviceniveau, maar geen volledige casusacceptatie of end-to-end-bewijs.** Drie rapportagepunten moeten worden begrensd. DEF-806 blijft buiten deze vervolgbeoordeling.

De hashes van helper en plan zijn exact gelijk aan de opgegeven waarden. Tijdens het lezen kwamen alle 31 resultaatbestanden en de [runmatrix](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/resultaten/runmatrix-ruw.json) beschikbaar; ik heb niet gewacht. De matrix komt overeen met de losse bestanden en vermeldt broncommit `d17ea9c30915452914e450be315620e314c03468`.

**Bevindingen over bewijskracht**

1. **Important — P10 bewijst geen uitgevoerde top-k-selectie.**  
   Het [plan](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/plan.json:40) zegt “top_k=5 toegepast”. De [helper](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/run_con02.py:54) bouwt rechtstreeks vijf vooraf gekozen bronobjecten. Hij voert geen zoekactie, rangschikking of selectie uit de zeven kandidaten uit.  
   **Dispositie:** rapporttekst corrigeren naar “de vijf verwachte bronnen synthetisch aangeleverd”. Geen claim over werkende retrieval of uitsluiting door de app.

2. **Important — P07 isoleert bronmutatie niet als oorzaak van afwijzing.**  
   De [replay](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/run_con02.py:101) gebruikt de P04-beoordeling, terwijl P07 zowel een andere definitie als een andere bronset heeft. Mijn lokale controle met uitsluitend de gewijzigde tekst en de oorspronkelijke P04-bronnen wijst de beoordeling eveneens af.  
   **Dispositie:** uitsluitend rapporteren dat de samengestelde binding niet meer past. Voor bewijs van bronmutatie als afzonderlijke oorzaak is een controle met gelijkblijvende tekst/context nodig. De verschillende bestandshashes en document-ID’s zijn wel aantoonbaar.

3. **Important voor budgetclaims — de teller telt serviceaanroepen.**  
   De [bewaking](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/run_con02.py:115) telt vóór `AIService.generate_definition`, dus vóór eventuele cacheafhandeling; retries binnen de providerclient vallen eronder. De teller is daarom geen exact aantal externe requests.  
   **Waargenomen:** zes serviceaanroepen, vijf afgeronde beoordelingen met `cached:false`, één timeout bij P16. Het log bevat vijf Anthropic HTTP-200-responses. Er is geen bewijs van budgetoverschrijding, maar evenmin een volledige telling van providerpogingen.  
   **Dispositie:** deze aantallen afzonderlijk noemen; niet “zes geslaagde modelbeoordelingen”.

**Wat de routes daadwerkelijk bewijzen**

| Route | Verantwoorde claim | Niet bewezen |
|---|---|---|
| Upload | Echte `DocumentProcessor` en bestaande snippetselectie aangeroepen | Streamlit-uploadflow, generatieprompt, volledige gebruikersketen |
| RAG | Geconstrueerde bronobjecten met manifestpassages verwerkt | Indexering, embeddings, live retrieval, echte chunk-ID’s |
| Contract | Validatie van expliciet samengestelde brongegevens | Dat de app deze metadata zelf ophaalt of doorgeeft |
| Cached/replay | Hergebruik of afwijzing van bestaande assessmentbinding | Nieuwe onafhankelijke beoordeling, opslag-/export-/vaststelpoort |

De uploadroute roept een [private helper via `__new__`](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/run_con02.py:46) aan. De validatieroute gebruikt wel de publieke `validate_text`, maar met [handmatig opgebouwde servicecompositie](/tmp/DEF-743-praktijk-20260917-v1/cli-uitvoering/run_con02.py:108). Dat is bruikbaar integratiebewijs binnen die grens.

De contextmapping is expliciet: de volledige historische contextstring wordt één `juridische_context`-waarde; wettelijke basis en organisatorische context blijven leeg, peildatum ontbreekt. Dit is een adapterkeuze, geen bewijs van dezelfde contextinvoer als in de browserprobe.

**Integriteit en hergebruik**

Zelf gecontroleerd:

- Alle 31 historische inputs en scenariohashes kloppen.
- Alle berekende fingerprints kloppen; aanwezige assessments passen bij hun invoer.
- Alle twaalf gebruikte fixturehashes kloppen; manifestpassages staan letterlijk in de fixtures.
- Bij de afgeronde assessments kloppen receipt-hashes en passagebindingen.
- P25 gebruikt bij publieke validatie de cache van **P02**; de afzonderlijke replay verwerpt **P01**. P26/P27 hergebruiken P01.

Deze controles bewijzen integriteit van de onderzochte gegevens, niet dat alle beschreven casusstappen zijn uitgevoerd. `used_in_prompt:true` bewijst op zichzelf geen modelontvangst. P16 heeft door de timeout geen beoordelingsreceipt of inhoudelijk oordeel.

**Veilige rapportage van de uitvoering**

- Vijf afgeronde nieuwe bronbeoordelingen: P01, P02, P04, P11 en P31.
- Eén technische timeout: P16; geen inhoudelijke casus-fail.
- Drie cachevalidaties: P25–P27.
- Twee bronloze validaties: P03/P28, beide `review_required`.
- Achttien transport-/constructieprobes, deels met replay; twee geblokkeerde scenario’s.
- P25–P28 bewijzen geen opslag, herladen, vaststelling of export. De bedoelde score-invoer `0.99` van P28 is niet uitgevoerd.
- Aantallen canonieke bronnen bij P06/P23 zijn geen aantallen onafhankelijke bewijsbronnen.
- P31 eindigt open doordat een citaat wordt afgewezen; dat bewijst geen werkende hyperlinkcontrole.

**Opleveradvies:** publiceer dit als begrensd uitvoeringsrapport met bovenstaande correcties en beperkingen. De ruwe `pass`/`fail`-waarden zijn app-uitkomsten, geen geslaagde/mislukte acceptatietests. Er is geen grond voor “alle 31 casussen getest en geaccepteerd”. Ik heb niets gewijzigd en geen modelcalls of extra sessies gestart.