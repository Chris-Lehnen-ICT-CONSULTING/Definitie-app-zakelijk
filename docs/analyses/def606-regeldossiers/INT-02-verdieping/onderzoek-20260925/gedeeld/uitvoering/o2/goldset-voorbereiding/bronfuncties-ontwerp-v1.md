# INT-02 O2 — ontwerp contract /4 met gestructureerde bronfuncties (v1)

**Status: keuzes Chris 07-10 vastgelegd in besluit 16** (`../besluit-chris-promptcorrectie-en-v3-v1.md`; alle zeven keuzes volgens het advies: 1B, 2A, 3A, 4A, 5A, 6A, 7A).

7 oktober 2026. Ontwerpstap na besluit 16 (optie A), opgesteld door Claude. Dit is een ontwerp, geen uitvoering: er is geen code gewijzigd, er zijn geen calls gedaan en `.env` is niet gelezen. Gelezen zijn alleen regressie- en ontwikkelgevallen (C105, C107, C112 en de 24 G-gevallen). De hold-out is niet ingezien: de gevallen zijn met een filter op `fase` uit `kwalificatie-gevallen-v1.json` gehaald.

Bronnen: `goldset-freeze-v1/kwalificatieproef-v7-ontwikkeling-uitslag-v1.md`, `kwalificatieproef-v7/ontwikkeling-resultaat.json` (modeloordelen), `kwalificatie-gevallen-v1.json` (alleen regressie en ontwikkeling), `kwalificatie-manifest-v7.json` (limieten, prijzen, criteria), `src/domain/int02/contract.py` (contract /3, `ANTWOORDSCHEMA`, dienstregel), `src/services/validation/int02_assessment_service.py` (prompt /4, T-tekst), `src/toetsregels/regels/INT-02.json` (norm def771-int02/2), `../besluit-chris-promptcorrectie-en-v3-v1.md` (besluiten 1, 9, 12 en 14) en `gedeeld/besluitnotitie-chris-v5.md` (K1, K2b en K5).

## Samenvatting voor Chris

- **Probleem.** Fase 2 van v7 haalde 18/24 en 0/6 bij `review_required`. Het model kiest bij bronnen die verschillende kanten op wijzen steeds één bron. Dat ligt voor een deel aan het formaat: contract /3 vraagt per passage precies één `ground`, dus het model móét kiezen.
- **Voorstel.** Het model vult per passage een `kernvorm` in (de zinsvorm van de passage, vijf waarden), en daarnaast voor elke beschikbare grondbron afzonderlijk een `function` met een letterlijk citaat. Grondbronnen zijn de bedoeling, elk contextitem en elke bron. De dienst beslist daarna mechanisch volgens een vaste volgorde van vier stappen (§2.3). Een zelfstandig voorschrift in de kern blijft altijd `fail` (besluit 1). Wijzen bronnen verschillende kanten op, dan volgt `review_required`. Een bronvoorschrift alleen draagt geen `fail` als de kern het handelen beschrijvend formuleert.
- **Paper test: 27/27**, als het model de bronfuncties invult zoals de labelredenen aangeven. Dat cijfer is geen bewijs: de regel is ontworpen terwijl deze 27 gevallen zichtbaar waren. Bij 11 gevallen kan één aannemelijke andere invulling de uitkomst breken. Bij 4 daarvan kan dat een false pass opleveren: bij G045 altijd, bij G036, G047 en C107 alleen onder bepaalde opties van keuze 1 en 5 (§3.3).
- **Normatief.** De regel maakt "strijdige betekenisgrond" uit de T-tekst mechanisch. Eén bronvoorschrift draagt een `fail` niet meer zelfstandig; dat is smaller dan besluit 1. Een `moet`-vorm in een kenmerkbijzin wordt `pass` als een bron die plicht als begripskenmerk aanwijst (zoals G041). De verschuivingen staan in §4.1.
- **Te beslissen: 7 keuzes** (§4.2). Mijn aanbevelingen: de bedoeling beslist een conflict alleen richting gebrek (1B), de dienst beslist (2A), en een bronvoorschrift zonder tweede signaal geeft review (3A).
- **Daarna nodig:** contract /4, prompt /5 (een wijziging van de promptbuilder, die overleg vraagt), schema met nieuwe pin, aanpassing van de runner, tests, manifest v8 (ontwikkeling `max_false_pass: 0`), akkoord, fase 1 en daarna fase 2.

## 1. Probleemanalyse

### 1.1 De zes gevallen

Alle zes fouten in fase 2 hebben label `review_required`. Vijf werden `pass` (G042, G045, G060, G070, G076) en één `fail` (G047). Het model gaf nergens `insufficient_information` en nergens `decisive` (zie de uitslag, §Patroon). De modeloordelen laten drie mechanismen zien:

| Geval | Gekozen grond in v7 | Wat de andere bron zegt (labelgrond) |
|---|---|---|
| G042 | B2 (legenda: criterium) | B1 art. 6 is een afschermplicht. Het model las in B1 alleen art. 2 (ploegen) en zag art. 6 over het hoofd. |
| G045 | B1 (letterlijke overeenkomst: criterium) | B1 en B2 laten "is in te dienen" open tussen plicht en mogelijkheid. |
| G047 | B2 voor de eerste helft, B1 voor de tweede (actorvoorschrift) | Niets toont of een melding na vijf werkdagen nog een afmelding is. B1 bewijst een bronvoorschrift, maar niet dat de kern dat voorschrift overneemt. |
| G060 | B2 (telling: criterium) | B1 maakt het doorgeven tot een plicht van een rol die al bestaat. |
| G070 | B1 (letterlijke definitie: criterium) | B2 maakt het vastleggen tot een taak in een dossier dat al geopend is. |
| G076 | B1 (letterlijke definitie: criterium) | B2 bepaalt aanwezigheid door fysieke deelname. Het model ziet het verschil, maar noemt het "niet relevant". |

### 1.2 Waarom prompt-instructies niet volstaan

1. **De norm staat er al, en werkt niet.** De T-tekst zegt "*Onvoldoende informatie* bij ontbrekende of strijdige betekenisgrond", en prompt /4 herhaalt dat voor een onbekende bedoeling. Toch 0/6. De instructie ontbreekt dus niet. Het model lost het conflict zelf op voordat het de onthouding overweegt.
2. **Het formaat dwingt tot kiezen.** Contract /3 en `ANTWOORDSCHEMA` vragen per passage precies één `ground`. Een antwoord dat twee bronnen tegenover elkaar zet, past niet in het schema. Geen prompttekst heft die structurele sturing op.
3. **De eigen onzekerheid is geen betrouwbare trigger.** Bij G045, G047 en G076 zag het model twijfel (`non_decisive`), maar het maakte die nooit `decisive`. Een prompt /5 met "weeg strijdigheid zwaarder" laat dezelfde afweging bij hetzelfde model.
4. **Eerdere ervaring.** De zelfcontrole-instructie voor posities hielp niet (besluit 9). C107 wisselde op dezelfde prompt 1 op 6 keer van uitkomst (besluit 12). Prompttekst stuurt kansen. Een mechanische regel is herhaalbaar en testbaar.
5. **Controleerbaarheid.** Met bronfuncties wordt elke deelbeslissing klein, geciteerd en door Chris na te lopen ("zegt B2 dit?"). De combinatie van die deelbeslissingen is deterministische code met unittests.

Wat de regel níét oplost: het model kan de bronfuncties zelf verkeerd invullen. De fout verschuift dan van het verdict naar de functie per bron (zie §4.3).

## 2. Voorstel

### 2.1 Begrippen

**Grondbronnen** van een passage zijn de bevestigde bedoeling (alleen als die niet `null` is), elk item van `organisatorische_context`, `juridische_context` en `wettelijke_basis`, en elke bronpassage. Het begrip zelf is geen grondbron. De dienst zet de sleutels deterministisch in de dataprompt, bijvoorbeeld `bedoeling`, `organisatorische_context/0`, `wettelijke_basis/1` en `bron/B1`. Het model neemt die sleutels letterlijk over.

**Kernvorm** (`kernvorm`, één per passage). Dit is de zinsvorm van de passage zelf. De kern is dus geen grondbron met een functie, maar wordt apart beschreven.

| Waarde | Betekenis (formeel, niet inhoudelijk) | Voorbeeld uit de set |
|---|---|---|
| `instruction` | zelfstandig voorschrift zonder genus en kenmerk: gebiedende wijs, of een hoofdzin met een actor als onderwerp en een handeling als gezegde | G008, G012, G052, C105 |
| `obligation_form` | een expliciet modaal woord van verplichting aan een actor ("moet", "dient te", "is verplicht") binnen een genus-kenmerkstructuur | G036, G041 |
| `discretion_form` | de passage laat de uitkomst afhangen van een oordeel, afweging of goedvinden van een actor ("naar het oordeel van", "passend vindt", "nodig acht") | C107, G050 (deel 2), mogelijk G021 |
| `descriptive_act` | een handeling of beslissing van een actor in beschrijvende vorm (indicatief, passief, voltooid, "is te"-constructie) | G015, G030, G042, G045, G047, G060, G070, G076 |
| `no_act` | geen handeling van een actor | G011, G019, G027, G007 |

**Bronfunctie** (`function`, één per grondbron per passage). Dit is de functie die de bron geeft aan **de inhoud van deze passage**. Het gaat dus niet om wat de bron in het algemeen regelt.

| Waarde | Richting | Betekenis |
|---|---|---|
| `criterion`, `derivation` | B (beschrijvend) | De bron gebruikt de inhoud als kenmerk of afleiding die bepaalt wat tot het begrip behoort. Dat geldt ook als de bron een plicht, bevoegdheid of beslissing beschrijft waarvan de passage alleen het bestaan of de uitkomst als kenmerk gebruikt (G041, G046, G055; norm: "als begripskenmerk beschrijven is op zichzelf geen overtreding"). |
| `actor_prescription`, `discretionary_decision_rule` | G (gebrek) | De bron stelt precies het handelen of de afweging uit de passage als plicht, taak of afweging van een actor. |
| `not_a_criterion` | N | De bron toont dat de inhoud níét bepaalt wat tot het begrip behoort: er vallen gevallen onder het begrip zonder dit kenmerk, of gevallen met het kenmerk vallen erbuiten (G048 B2, G070 B2, G076 B2). |
| `unclear` | O (open) | De bron gaat over de inhoud, maar laat de functie open (G045 B1). |
| `not_addressed` | — (zwijgend) | De bron zegt niets over de functie van deze inhoud. Ook een bedoeling die alleen noemt waar de term voorkomt of welke stukken zijn meegestuurd, valt hieronder (G042, G060, G070, G076). |

De opdracht noemde `niet_van_toepassing`. Ik gebruik `not_addressed`, omdat `not_applicable` al het verdict "niet van toepassing" (reikwijdte) is; dezelfde naam voor twee betekenissen is foutgevoelig. `derivation` staat erbij om gelijk op te lopen met `FUNCTIES` van /3. `not_a_criterion` is nieuw en nodig om G048 (`fail`) van G047 (`review_required`) te onderscheiden (zie stap 3).

### 2.2 Schema (JSON, binnen de structured-output-grenzen)

```json
{
  "type": "object",
  "properties": {
    "passages": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "quote": {"type": "string"},
          "kernvorm": {"type": "string", "enum": ["descriptive_act", "discretion_form", "instruction", "no_act", "obligation_form"]},
          "bronfuncties": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "bron": {"type": "string"},
                "function": {"type": "string", "enum": ["actor_prescription", "criterion", "derivation", "discretionary_decision_rule", "not_a_criterion", "not_addressed", "unclear"]},
                "quote": {"anyOf": [{"type": "string"}, {"type": "null"}]}
              },
              "required": ["bron", "function", "quote"],
              "additionalProperties": false
            }
          }
        },
        "required": ["quote", "kernvorm", "bronfuncties"],
        "additionalProperties": false
      }
    },
    "reason": {"type": "string"},
    "question": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    "uncertainty": {"type": "string", "enum": ["decisive", "non_decisive", "none"]},
    "coverage": {"type": "string", "enum": ["complete", "none", "partial"]},
    "scope_reason": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    "verdict": {"type": "string", "enum": ["fail", "insufficient_information", "not_applicable", "pass"]}
  },
  "required": ["passages", "reason", "question", "uncertainty", "coverage", "scope_reason", "verdict"],
  "additionalProperties": false
}
```

**Grenzen.** Er zijn 0 optionele velden (alles is verplicht) en 3 union-velden (`question`, `scope_reason` en `bronfuncties[].quote`), ruim binnen de grenzen van ≤24 en ≤16. Geen `minLength`/`maxLength`. De grenzen zijn overgenomen uit besluit 14; de Anthropic-documentatie heb ik voor dit ontwerp niet opnieuw nagelezen. De unie voor `ground` uit /3 vervalt: de bron is één tekstsleutel uit de dataprompt, die de code controleert.

**Volgorde.** Eerst de bronfuncties, dan de onderbouwing, als laatste het eigen `verdict` van het model. Het model legt zich zo per bron vast voordat het een eindoordeel geeft. Dat het model bij generatie de volgorde van de schema-eigenschappen volgt, is een verwachting. Ik heb dat niet gecontroleerd; fase 1 moet het laten zien. Ook de hash van het schema hangt van deze volgorde af.

**Controles in de code (niet in het schema), allemaal fail-closed als `invalid_output` of `invalid_citation`:**

1. Per passage komt elke sleutel uit de grondbronnenlijst precies één keer voor. Er zijn geen onbekende sleutels. Een bedoeling-sleutel terwijl de bedoeling `null` is, is ongeldig.
2. `quote` is verplicht (niet `null`) bij B, G en N, mag `null` zijn bij `unclear`, en moet `null` zijn bij `not_addressed`. Een citaat staat precies één keer letterlijk in de tekst van die bron (`_positie` uit /2).
3. Het passagecitaat staat precies één keer in de kern, zoals nu. Bij `not_applicable` geldt: geen passages, `scope_reason` gevuld, `coverage` `none` en `uncertainty` `none`. Anders minstens één passage.
4. Het eigen `verdict` van het model moet intern samenhangen zoals in /3 (vraag, onzekerheid, dekking). De voorwaarden op passagefuncties vervallen, omdat het model die niet meer levert.

### 2.3 Mechanische beslisregel

```python
B = {"criterion", "derivation"}
G = {"actor_prescription", "discretionary_decision_rule"}

def richting(f):
    return {"criterion": "B", "derivation": "B",
            "actor_prescription": "G", "discretionary_decision_rule": "G",
            "not_a_criterion": "N", "unclear": "O"}.get(f)   # not_addressed -> None (zwijgend)

def beoordeel_passage(p, invoer):
    # Stap 1 — besluit 1 / K1: een zelfstandig voorschrift in de kern blijft fail.
    if p.kernvorm == "instruction":
        return Gebrek("actor_prescription", grond=eerste_G_bron(p) or KERN, regel="voorschrift_in_kern")

    stem = {bf.bron: richting(bf.function) for bf in p.bronfuncties if richting(bf.function)}
    Bs = [k for k, r in stem.items() if r == "B"]
    Gs = [k for k, r in stem.items() if r == "G"]
    Ns = [k for k, r in stem.items() if r == "N"]
    Os = [k for k, r in stem.items() if r == "O"]
    bed = stem.get("bedoeling")            # None: onbekend of zwijgend

    # Stap 2 — strijdige betekenisgrond (T-tekst).
    if Bs and (Gs or Ns):
        if bed in ("G", "N"):                                   # keuze 1, optie B (aanbevolen)
            return Gebrek(gebreksoort(p), grond="bedoeling", regel="bedoeling_beslist")
        # optie 1A voegt toe:  if bed == "B": return Beschrijvend(grond="bedoeling", regel="bedoeling_beslist")
        return Review("conflict", beschrijvend=Bs[0], tegen=(Gs + Ns)[0])

    # Stap 3 — één richting (zwijgende bronnen tellen niet; O naast B of G telt niet).
    if Bs:
        return Beschrijvend(grond=Bs[0], regel="bronnen_beschrijvend")
    if Gs or Ns:
        tweede_signaal = (
            p.kernvorm in ("obligation_form", "discretion_form")   # de kern neemt de plicht/afweging in voorschrijvende vorm over (G036, G050)
            or (Gs and Ns)                                        # een bron schrijft voor en een bron toont dat het geen kenmerk is (G048)
            or bed in ("G", "N")                                  # de bedoeling zegt het zelf (C105-type)
        )
        if tweede_signaal:
            return Gebrek(gebreksoort(p), grond=(Gs + Ns)[0], regel="voorschrift_bevestigd")
        return Review("bronvoorschrift_niet_overgenomen", tegen=(Gs + Ns)[0])   # keuze 3, optie A (G047, G042)
    if Os:
        return Review("bronnen_open", open=Os[0])                 # G045

    # Stap 4 — alle grondbronnen zwijgen: alleen de kern (gedrag /3, incl. besluit 12).
    if p.kernvorm == "no_act":
        return Beschrijvend(grond=KERN, regel="alleen_kern")
    if p.kernvorm == "descriptive_act":
        if invoer.bedoeling is None:                             # keuze 5, optie A (aanbevolen)
            return Review("geen_grond_zonder_bedoeling")
        return Beschrijvend(grond=KERN, regel="alleen_kern")
    if p.kernvorm == "obligation_form":
        return Gebrek("actor_prescription", grond=KERN, regel="voorschrift_in_kern")   # besluit 1
    if p.kernvorm == "discretion_form":
        if invoer.bedoeling is None:
            return Review("discretie_zonder_bedoeling", vraag=VRAAG_DISCRETIE_ZONDER_BEDOELING)   # besluit 12
        return Gebrek("discretionary_decision_rule", grond=KERN, regel="voorschrift_in_kern")

def gebreksoort(p):
    # Discretionair als de kern discretionair geformuleerd is of de eerste G-bron discretionair is; anders actorvoorschrift.
    ...

def beoordeel(uitvoer, invoer):
    if uitvoer.verdict == "not_applicable":
        return NA                                                 # ongewijzigd t.o.v. /3
    uitkomsten = [beoordeel_passage(p, invoer) for p in uitvoer.passages]
    if any(isinstance(u, Gebrek) for u in uitkomsten):
        status = "fail"                                           # SC-C-03: open reviewpassages worden in de melding vermeld
    elif any(isinstance(u, Review) for u in uitkomsten):
        status = ("review_required", "insufficient_information")  # vaste vraag per reviewsoort (keuze 4)
    elif uitvoer.coverage != "complete":
        status = ("review_required", "insufficient_information")  # pass vereist volledige dekking, zoals /3
    else:
        status = "pass"
    afleiding = regel_van_de_dragende_passage(uitkomsten)
    omzetting = afleiding if status != status_uit(uitvoer.verdict) else None   # keuze 2: zichtbaar, nooit stil
    return document(status, afleiding, omzetting, modeluitvoer=uitvoer, afgeleide_passages=uitkomsten)
```

**Wat "de bedoeling beslist het conflict" betekent.** De bevestigde bedoeling neemt zelf één kant van het conflict in, met functie B, G of N en een letterlijk citaat uit de bedoeling. Een bedoeling die alleen gebruik of vindplaatsen noemt, is `not_addressed` en beslist niets. Onder de aanbevolen optie 1B kan de bedoeling een conflict alleen beslechten richting gebrek. Een bedoeling die "beschrijvend" zegt tegen een bron die "voorschrift" zegt, blijft dan `review_required`.

**Zwijgende bronnen.** `not_addressed` telt nergens mee. Zo'n bron veroorzaakt geen conflict, steunt geen richting en blokkeert geen `pass`. `unclear` telt alleen als er verder geen richting is (stap 3, `bronnen_open`). Zwijgen alle grondbronnen, dan beslist alleen de kernvorm (stap 4). Dat is het /3-gedrag, inclusief de dienstregel.

**Volgorde ten opzichte van de bestaande regels.**

1. Ontbrekende kern of context, een mislukte of niet uitgevoerde aanroep, structuur, citaten en volledigheid van de bronfuncties: zoals /3. Een fout hier geeft `error` of NE, en de beslisregel wordt niet bereikt.
2. Daarna stap 1: een zelfstandig actorvoorschrift in de kern is `fail` vóór elke bronafweging (besluit 1, K1).
3. Daarna stap 2 (conflict) en stap 3 (één richting).
4. De dienstregel discretie zonder bedoeling (besluit 12) is de laatste tak van stap 4. Hij werkt alleen als geen enkele grondbron iets zegt; dat volgt de geest van "alleen de kern draagt de lezing". Een discretionaire bron met een discretionaire kernvorm blijft `fail` (stap 3), net als onder besluit 12.
5. Over passages heen gaat `fail` vóór `review` vóór `pass` (SC-C-03).

**Melding en vraag.** De sjablonen V, VN en O blijven gelijk. De dienst vult `{passage}`, `{grond}` en de functie in vanuit de afgeleide passage, dus uit de dragende bron. Bij `review_required` komen in de O-melding de bron-ID's en citaten van beide kanten, bijvoorbeeld: "Bronpassage B1 stelt '…' als plicht van een actor; bronpassage B2 gebruikt '…' als kenmerk van het begrip; de bevestigde bedoeling beslist dat niet". Daarbij komt één vaste, invoeronafhankelijke vraag (keuze 4), bijvoorbeeld: "Bepaalt deze passage wat tot het begrip behoort, of schrijft zij een actor een handeling of afweging voor?". Bij `discretie_zonder_bedoeling` blijft de vaste vraag van besluit 12 staan.

**Bewaard document.** Het document bewaart de modeluitvoer (met afgeleide posities), en daarnaast de afgeleide passages in /3-vorm (`quote`, `function`, `ground`, `start`, `end`), `afleiding` (de beslissende regel) en `omzetting` (alleen als de status afwijkt van het eigen `verdict` van het model). Zo blijven UI, export en melding werken. De afwijking tussen model en regel wordt bovendien meetbaar. Bewaarde /1-, /2- en /3-documenten worden volgens hun eigen versie getoetst en zijn daarna historisch, zoals nu.

## 3. Handmatige doorrekening (paper test)

### 3.1 Aanpak

Per geval heb ik de bronfuncties ingevuld zoals de labelreden en de normgrond aangeven. Waar het label een bron niet noemt, heb ik die bron ingevuld volgens de definities in §2.1. Daarna heb ik de regel uit §2.3 met de aanbevolen opties (1B, 3A, 5A) toegepast. Contextitems zijn in alle 27 gevallen `not_addressed` ("Synthetisch afsprakenmodel…", namen van fictieve organisaties) en staan niet in de tabel.

Afkortingen: C = `criterion`, D = `derivation`, A = `actor_prescription`, R = `discretionary_decision_rule`, N = `not_a_criterion`, O = `unclear`, – = `not_addressed`. P1/P2 = passage 1 en 2.

### 3.2 Tabel

| Id | Label | Verwachte kernvorm en bronfuncties | Pad | Uitkomst | Klopt? | Gevoelig voor (andere aannemelijke invulling → uitkomst) |
|---|---|---|---|---|---|---|
| C105 | fail | `instruction`; bed A | stap 1 | fail | ✓ | robuust (ook met `descriptive_act`: bed A → fail) |
| C107 | review | `discretion_form`; bed onbekend | stap 4, besluit 12 | review | ✓ | kernvorm `descriptive_act` → review (5A) of **pass** (5B); `obligation_form` → fail |
| C112 | pass | `descriptive_act`; bed C | stap 3 | pass | ✓ | robuust |
| G011 | pass | `no_act`; bed C; B1 D | stap 3 | pass | ✓ | robuust |
| G015 | pass | P1 `no_act`, P2 `descriptive_act`; bed C; B1 C | stap 3 | pass | ✓ | robuust |
| G019 | pass | `no_act`; bed C of –; B1 C | stap 3 | pass | ✓ | robuust |
| G027 | pass | `no_act`; bed D; B1 D | stap 3 | pass | ✓ | robuust |
| G030 | pass | `descriptive_act`; bed –; B1 C (typetabel); B2 C (kopregel) | stap 3 | pass | ✓ | B2 A (werkwijzezin op dezelfde kaart) → conflict → review |
| G039 | pass | `descriptive_act`; bed C; B1 C | stap 3 | pass | ✓ | robuust |
| G007 | pass | `no_act`; bed C; B1 C | stap 3 | pass | ✓ | robuust |
| G021 | pass | `discretion_form` of `descriptive_act`; bed – of C; B1 C | stap 3 | pass | ✓ | robuust voor de kernvorm |
| G037 | pass | P1 `descriptive_act`, P2 `no_act`; bed C; B1 C (beide) | stap 3 | pass | ✓ | robuust |
| G041 | pass | `obligation_form`; bed –; B1 C ("noemt zo'n wijziging…"); B2 – | stap 3 | pass | ✓ | B1 A ("Een producent meldt…") → `obligation_form` + G → **fail** |
| G046 | pass | `descriptive_act`; bed –; B1 C; B2 C | stap 3 | pass | ✓ | B1 R ("kan … verlenen") → conflict → review |
| G055 | pass | P1 `no_act`, P2 `descriptive_act`; bed C; B1 C; B2 C | stap 3 | pass | ✓ | B1 R ("nodig acht") → conflict → pass bij 1A, review bij 1B/1C |
| G008 | fail | `instruction`; bed –; B1 A | stap 1 | fail | ✓ | robuust |
| G012 | fail | `instruction`; bed –; B1 A | stap 1 | fail | ✓ | robuust |
| G036 | fail | `obligation_form`; bed –; B1 A ("opdrachten") | stap 3, tweede signaal kernvorm | fail | ✓ | bed C ("proces waarin … opnieuw worden aangeboden") → conflict → **pass bij 1A**, review bij 1B/1C; kernvorm `descriptive_act` → review |
| G048 | fail | P1 `no_act`: B1 C, B2 C; P2 `descriptive_act`: B1 A, B2 N; bed – | P1 stap 3 B; P2 stap 3 (A + N) | fail | ✓ | B2 – bij P2 → review |
| G050 | fail | P1 `no_act`: B1 D, B2 D; P2 `discretion_form`: B1 R, B2 –; bed – | P2 stap 3, tweede signaal kernvorm | fail | ✓ | B2 C bij P2 (vastgesteld 3% als feit) → conflict → review |
| G052 | fail | `instruction`; bed –; B1 R/A; B2 – | stap 1 | fail | ✓ | robuust |
| G042 | review | `descriptive_act` (passief); bed –; B1 A (art. 6); B2 O (legenda) | stap 3, geen tweede signaal | review | ✓ | B2 C → conflict → review (blijft ✓); kernvorm `obligation_form` → **fail** |
| G045 | review | `descriptive_act` ("is in te dienen"); bed –; B1 O; B2 O of – | stap 3, alleen O | review | ✓ | B1 C (zoals in v7) → **pass**; B1 A + `obligation_form` → fail |
| G047 | review | `descriptive_act` (één passage); bed –; B1 A; B2 – | stap 3, geen tweede signaal | review | ✓ | splitsing zoals v7 (P1 C via B2, P2 A) → review (blijft ✓); bed C ("gebruikt in de maandcijfers") → conflict → **pass bij 1A** |
| G060 | review | `descriptive_act`; bed –; B1 A (rol bestaat los van naleving); B2 C (telling) | stap 2 | review | ✓ | robuust zolang B1 niet C wordt |
| G070 | review | `descriptive_act`; bed –; B1 C; B2 A/N (dossier al geopend, blijft bij weigering) | stap 2 | review | ✓ | robuust zolang B2 niet C of – wordt |
| G076 | review | `descriptive_act`; bed –; B1 C; B2 A/N (aanwezig = in de zaal); B3 O of – | stap 2 | review | ✓ | robuust zolang B2 niet C of – wordt |

### 3.3 Uitkomst

- **27/27** onder de verwachte invulling: 3/3 regressie en 24/24 ontwikkeling, waaronder 6/6 `review_required`. Ter vergelijking: v7 haalde 21/27.
- **De regel breekt bij de verwachte invulling geen enkele juiste `pass` of `fail`.** De keuzes 1A, 1B en 1C geven op deze 27 dezelfde uitkomst, net als 5A en 5B. De set onderscheidt die opties dus niet.
- **Gevoeligheid.** Bij 11 gevallen kan één aannemelijke andere invulling de uitkomst breken:
  - **false pass** mogelijk bij 4 gevallen: G045 (B1 C, precies wat v7 deed), G036 en G047 (alleen onder 1A) en C107 (alleen onder 5B);
  - **false fail** mogelijk bij G041, G042 en C107 (verkeerde kernvorm, of B1 als A);
  - **onterechte review** mogelijk bij G030, G046, G048, G050 en G055. Bij G055 voorkomt optie 1A dat juist.
- **Wat de regel wél robuust maakt:** elk geval met twee tegengestelde bronnen (G060, G070, G076, en G042 als B2 C wordt) komt in review, welke bron het model ook als "letterlijk" of "hoofdbron" ziet. Mechanismen a en c uit de uitslag vallen daardoor weg zolang het model beide bronnen eerlijk invult. Mechanisme b (zinsvorm) krijgt een eigen, smal veld (`kernvorm`). Dat veld beslist alleen bij `instruction`, als tweede signaal naast een bronvoorschrift, of als alle bronnen zwijgen.

## 4. Gevolgen, keuzes, risico's en wat er nodig is

### 4.1 Normatieve verschuivingen

1. **T-tekst ("strijdige betekenisgrond").** Niet nieuw als norm, wel nieuw als operationalisering. Strijdigheid is nu mechanisch: één bron B en één bron G of N bij dezelfde passage. Het model mag die strijdigheid niet meer zelf "niet relevant" verklaren (G076). Gevolg in de praktijk: meer `review_required` bij regelingen die een begrip zowel definiëren als er een plicht aan verbinden.
2. **Besluit 1 ("grond uit kern, bedoeling, context of bronpassage draagt de fail zelfstandig").** Voor een bronpassage wordt dat smaller. Eén bronvoorschrift draagt een `fail` alleen als de kern het voorschrift in voorschrijvende vorm overneemt, een andere bron toont dat het geen kenmerk is, of de bedoeling het voorschrift bevestigt. Anders volgt review. Dit volgt de normgrond van G070 ("B2 bewijst een bronvoorschrift, maar niet zelfstandig dat de aangeboden kern dat voorschrift uitvoert") en het label van G047. Voor de kern zelf en voor de bedoeling verandert niets.
3. **K1 (breed).** Ongewijzigd voor het zelfstandige actorvoorschrift (`instruction` is altijd `fail`). Een `moet`-vorm binnen een kenmerkbijzin is nog wel `fail` als er een bronvoorschrift naast staat of als alle bronnen zwijgen. Hij wordt `pass` als een bron de plicht als begripskenmerk aanwijst (G041), en review bij een conflict. Dat sluit aan op K2b (een modaal woord bewijst niets) en op C112, maar de zinsvorm beslist niet meer alleen.
4. **Besluit 12 (dienstregel).** De dienstregel gaat op in stap 4, met dezelfde vaste vraag en zichtbare omzetting. Twee verschillen. De voorwaarde wordt "geen enkele grondbron zegt iets" in plaats van "het model koos alleen de kern als grond". En de dienst zet niet meer alleen `fail` om naar review: onder keuze 2A beslist hij zelf. Daardoor ontstaan paden van `pass` naar review en van `pass` naar `fail`, maar óók van een `fail` van het model naar `pass`, als de bronnen de passage als kenmerk aanwijzen (bijvoorbeeld G041 als het model zelf `fail` zou geven). Besluit 12 sloot een pass-pad uitdrukkelijk uit; dat is onder 2A dus **niet** meer zo. Een `pass` vereist dan wel dat geen passage een gebrek oplevert en dat minstens één bron de passage als kenmerk geciteerd steunt, of dat alle bronnen zwijgen en de kernvorm geen voorschrift bevat. Onder 2B blijft er geen pass-pad, maar dan blijft ook een false pass van het model staan.
5. **De rol van de bedoeling.** De bevestigde bedoeling krijgt een expliciete voorrang die tot nu toe impliciet was (C105, C112). Onder 1B is die voorrang asymmetrisch.
6. **Wie beslist.** Het docstring van /3 zegt "een beoordelaar (model of mens) bepaalt per passage de functie". Onder /4 bepaalt het model per bron, en de dienst bepaalt de functie van de passage.

### 4.2 Open keuzes voor Chris

1. **De bedoeling bij een conflict.**
   - **A (symmetrisch):** de bedoeling beslist naar beide kanten. Dat redt G055 als B1 verkeerd als R wordt ingevuld, maar G036 en G047 worden **false pass** als de bedoeling verkeerd als C wordt ingevuld.
   - **B (alleen richting gebrek; aanbevolen):** een conflict met een beschrijvende bedoeling blijft review. Geen false pass via de bedoeling; wel kans op een onterechte review (G055).
   - **C (nooit):** elk conflict wordt review. Het eenvoudigst, maar dan beslist de bevestigde bedoeling ook niet als die uitdrukkelijk "opdracht aan medewerker" zegt en een bron het tegendeel beweert.
   - Op de 27 gevallen geven A, B en C dezelfde uitkomst.
2. **Wie beslist bij een verschil tussen model-`verdict` en regel.**
   - **A (dienst beslist altijd; aanbevolen):** het modelverdict is alleen diagnostisch en het verschil is zichtbaar als `omzetting`. Dit opent een pad van `fail` naar `pass`, dat besluit 12 uitsloot (§4.1, punt 4).
   - **B (dienst mag alleen naar review omzetten):** een `pass` van het model waar de regel `fail` afleidt, blijft `pass`. Dat is een false-pass-pad.
   - **C (verschil = `error`):** maakt inconsistentie zichtbaar, maar telt in de proef als fout en kost dekking.
3. **Bronvoorschrift zonder tweede signaal** (één bron G, kern `descriptive_act`, verder niets; G047, G042).
   - **A (review; aanbevolen):** volgt de labels van G047 en G070.
   - **B (fail):** volgt besluit 1 letterlijk ("bronpassage draagt zelfstandig"). Dan worden G047 en G042 false fail: 25/27.
4. **De vraag bij review.**
   - **A (vaste vraag per reviewsoort, met bron-ID's en citaten in de reden; aanbevolen):** deterministisch en testbaar, maar minder specifiek dan de labelvragen.
   - **B (modelvraag als die geldig is, anders de vaste vraag):** specifieker, maar de vraag kan over iets anders gaan (SC-C-03), en een model dat `pass` gaf heeft geen vraag.
5. **Alle bronnen zwijgen, kern `descriptive_act`, bedoeling onbekend.**
   - **A (review; aanbevolen bij `max_false_pass` 0):** dekt een C107-type met een verkeerde kernvorm af en sluit aan op de bestaande promptregel voor een onbekende bedoeling. Meer review in de app als de bedoeling vaak ontbreekt.
   - **B (pass):** minder review, maar C107 kan een false pass worden.
6. **`not_a_criterion` als eigen waarde.**
   - **A (ja; aanbevolen):** nodig om G048 (`fail`) en G047 (review) te onderscheiden.
   - **B (opgaan in G, met de regel "twee G-bronnen = fail"):** een kleinere enum, maar het onderscheid hangt dan aan het aantal bronnen in plaats van aan wat ze zeggen.
7. **Gebruik van de 27 gevallen.** De regel is ontworpen terwijl deze 27 gevallen zichtbaar waren.
   - **A:** v8 fase 2 is een **consistentietoets** (vult het model de bronfuncties in zoals verwacht?). Alleen de hold-out geldt als onafhankelijk bewijs.
   - **B:** eerst nieuwe, ongeziene ontwikkelgevallen laten maken en labelen. Dat kost een labelronde en tijd.
   - Mijn advies: A, met de verwachte invulling uit §3.2 als diagnostische vergelijking bij de inhoudelijke beoordeling.

Twee kleinere punten volg ik zoals besluit 12, tenzij Chris anders kiest. De regel geldt alleen voor actor `ai`. En ook contextitems moeten volledig worden ingevuld; dat kost tokens, maar is eenvoudig en controleerbaar.

### 4.3 Risico's

- **Inconsistente invulling door het model (hoofdrisico).** Dezelfde mechanismen kunnen terugkomen op bronniveau: een letterlijk overeenkomende bron als C, een werkinstructie met dezelfde inhoud als A (G030), of "kan" als R (G046). De regel maakt zulke fouten wel zichtbaar en citeerbaar, maar voorkomt ze niet. Mitigatie:
  - de verplichte volledigheid per bron (de G042-fout, art. 6 over het hoofd zien, wordt moeilijker);
  - verplichte citaten;
  - bronfuncties vóór het verdict in het schema;
  - definities met de normzin in de prompt;
  - meting van het aantal `omzetting`en;
  - een kleine variatiemeting op 2 à 3 gevoelige gevallen (zoals bij C107).
- **Meer review dan gewenst.** Fouten verschuiven naar review (5 van de 11 gevoelige gevallen). Dat past bij `max_false_pass` 0, maar telt mee in `min_juist` (21/24). Met vijf mogelijke onterechte reviews is 21/24 niet zeker.
- **False pass blijft mogelijk** bij een volledig verkeerde invulling in één richting (G045: B1 C). De regel kan geen grond verzinnen die het model niet geeft.
- **Kosten en tokens** (schatting, niet gemeten; prijzen uit manifest v7: US$5 per miljoen invoertokens en US$25 per miljoen uitvoertokens):
  - **Invoer:** ongeveer 700–900 tokens extra (definities en het grotere schema in `output_config`).
  - **Uitvoer:** ongeveer 4–6 bronregels per passage van 20–70 tokens. Na aftrek van `function`/`ground` per passage is dat netto ongeveer +150 tot +350 tokens. De uitvoer gaat van 251–587 naar ongeveer 450–900 tokens.
  - **Per call:** ongeveer +US$0,008 tot +US$0,013, dus US$0,045–0,050 in plaats van US$0,037 (+25 à 35%). De volle 43 calls kosten ongeveer US$2,0–2,2.
  - **Latentie:** naar schatting +2 tot 4 s per call (p95 nu 9,6 s).
  - **Uitvoerlimiet:** `max_uitvoertokens` 6.000 is ruim genoeg.
- **Overfitting.** Een aantal onderdelen is aangescherpt op één of twee zichtbare gevallen: `not_a_criterion` (G048 tegenover G047), het tweede signaal (G036 tegenover G047) en de begrenzing van B bij beschreven bevoegdheden (G055). 27/27 is daardoor een consistentiecontrole en geen prestatiemaat. De hold-out moet het werk doen, en blijft ongezien.
- **Grotere code.** Contract /4 krijgt een tweede beslislaag. Meer takken betekent meer tests en meer kans op een verkeerde volgorde. Mitigatie: een unittest per tak, de paper test als testtabel (alleen regressie en ontwikkeling) en mutaties op de naïeve varianten (stap 1 overslaan, O laten tellen naast B, de bedoeling symmetrisch maken).

### 4.4 Wat er nodig is (na akkoord op de keuzes)

1. **Contract `def835-int02-assessment/4`** in `src/domain/int02/contract.py`:
   - nieuwe uitvoervorm en `ANTWOORDSCHEMA` met een nieuwe pin;
   - controle op grondbronnen en volledigheid, en citaatregels per functie;
   - de beslisregel uit §2.3;
   - `afleiding`/`omzetting` en de afgeleide passages in het document;
   - replay van /1–/3 als historisch;
   - contractdocument `docs/architectuur/contracts/int02_assessment_contract_v4.md`.
2. **Prompt `def835-int02-prompt/5`:** systeemprompt met de definities van `kernvorm` en de bronfuncties (in casusvrije woorden, zonder materiaal uit de goldset), en een dataprompt met de lijst van grondbronsleutels. Dit is een wijziging van de promptbuilder: projectregel "niet zonder overleg", en dit document is de basis voor dat overleg.
3. **Runner** (`scripts/analysis/def835_int02_modelproef.py`):
   - nieuwe schemahash accepteren;
   - `omzetting` en `afleiding` per geval tellen;
   - `max_false_pass` voor ontwikkeling handhaven.
4. **Tests (TDD):**
   - eerst rood en dan groen;
   - een tak-test per stap;
   - de 27 verwachte invullingen uit §3.2 als tabeltest van de beslisregel (zonder hold-out);
   - schemapin en volgorde;
   - een mutatiecontrole;
   - de gerichte def835/int02-selectie, ruff en black.
5. **Onafhankelijke review** (Codex) van de diff, daarna commit en push.
6. **Manifest v8 offline:**
   - nieuwe contract-, prompt-, schema- en payloadhashes;
   - ontwikkeling `max_false_pass: 0` (afspraak processtatus v14);
   - een eventueel nieuw kostenkader op basis van §4.3;
   - de gevallen ongewijzigd (`af1ab46c…6953`).
7. **Akkoord v8 van Chris**, daarna **fase 1** (C105, C107, C112, 3 calls; tegelijk de rooktest van het nieuwe schema), bespreken, en pas na een afzonderlijk akkoord **fase 2** (24). De hold-out vraagt opnieuw een eigen akkoord.
