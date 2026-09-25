# DEF-770 restherstel — resultaat Claude-uitvoerder (v1)

25 september 2026. Uitvoerder: Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc` (claude-opus-5-5). Opdracht: `logs/def770-restherstel/claude-opdracht-v1.md`.
Uitgangspunt: app HEAD `e38ad957…` (bron `23cc51bf…`, contract /6) en skills HEAD `a048806c…`; preflight klopte.
Niet gedaan: agents, reviewers of extra CLI-sessies gestart, commits, pushes, merges, betaalde calls, nieuwe acceptatiegevallen, of wijzigingen aan labels, eerdere besluiten of historische proefdata.

**Kort:**
- T20 en T22 zijn hersteld onder contract **/7**.
- Voor de generatie is **eerst een beslispunt nodig**. Een promptwijziging alleen is niet te onderbouwen (zie §3). Er is geen generatiecode gewijzigd.

## 1. T20 — nominale titelvoortzetting

**Oorzaak.** Bevestigd, zoals astra-acceptatiebevindingen-v1 al vaststelde. `_voorzetselgroepen` stond na het lidwoord precies één woord toe. Daardoor strandde ‘van de bijbehorende opdracht’. De oefenboektitel speelde geen rol.

**Ontwerp.** Eén extra woord in een voorzetselgroep is toegestaan, maar alleen waar de structuur een zelfstandige zin uitsluit. Het mechanisme is structureel: er is geen woordenlijst en er worden geen woordrollen of woordsoorten herkend. De functie is `_groep_met_extra_woord` in `zinsgrenzen.py`. Een zelfstandige Nederlandse zin vraagt een persoonsvorm met een onderwerp, of een infinitief zonder onderwerp. Vier voorwaarden sluiten dat uit:

1. **Het voorzetsel is geen scheidbaar werkwoorddeel en geen voegwoord.**
   - Toegestaan: `van`, `met`, `tijdens`, `volgens`, `via`, `per`, `vanaf`.
   - Buiten de uitbreiding: ‘op’/‘uit’ (‘roept … uit’) en ‘voor’/‘sinds’ (‘voor de speler wacht’).
   - Daardoor blijft de historische verwachting ‘… “Gereed.” op het grote scherm’ (0/1) staan.
2. **Na het voorzetsel staat alleen ‘de’ of ‘het’.** Na een voorzetsel kunnen die geen voornaamwoord zijn: voornaamwoord ‘het’ wordt ‘er-’. ‘deze’, ‘dit’ en ‘een’ kunnen dat wel (‘met dit speelde hij’) en vallen dus buiten de uitbreiding.
3. **Een persoonsvorm als tweede woord heeft geen onderwerp.** Erna volgt alleen een nieuwe voorzetselgroep of het einde van de tekst.
4. **Het tweede woord eindigt niet op -n.** Elke Nederlandse infinitief eindigt op -n. Dit dient alleen als uitsluiting, niet als bewijs voor een woordsoort. Het kost bewust dekking: ‘van de gele kaarten’ blijft onzeker.

De bestaande globale persoonsvormcontrole blijft gelden, en de ‘waar’ + voorzetsel-route blijft volgens het titelbesluit onzeker.

**Tests** (`test_def770_restherstel_zinsgrenzen.py`):
- Wordt (0,0):
  - de exacte T20-tekst, plus het minimale contrast zonder extra woord;
  - ‘van het grote vak’, ‘volgens de vaste volgorde’ en het extra woord midden in de reeks;
  - onbekende woorden (‘met de blorse vek’).
- Een zekere grens verderop blijft een zekere grens (1,0).
- Blijven onzeker (0,1):
  - drie woorden in de groep, of twee bijvoeglijke naamwoorden;
  - een laatste woord dat een infinitief kan zijn, ook bij onbekende woorden;
  - ‘op’/‘uit’ en ‘voor’/‘sinds’;
  - ‘deze’/‘een’/‘dit’ na het voorzetsel, of een bijzinwoord als extra woord;
  - een persoonsvorm, of een woord buiten een groep;
  - de tegenvoorbeelden uit het titelbeleid.
- De onzekere grens houdt haar passage en reden.

## 2. T22 — los label

**Oorzaak.** Bevestigd. `_grensdelen` maakte van het ontbreken van grenzen automatisch `zinsstructuur: pass`. Alleen een label dat op een dubbele punt eindigt, werd herkend.

**Ontwerp.** De controle zit in de domeinlaag, waar ook de pass ontstaat.
- `Segmentatie` krijgt het veld `zonder_formulering`, met standaardwaarde, zodat bestaande aanroepen blijven werken.
- `_los_label` herkent een kern met hooguit één inhoudswoord, eventueel na een lidwoord. De structurele grond: een definitie noemt ten minste een bovenbegrip met een onderscheidend kenmerk. Het is geen lijst met woorden.
- In zo'n geval komt er geen zinsstructuur-pass, maar het open onderdeel `formulering` (`review_required`), met passage (`evidence`), positie en reden.
- `open_melding` meldt: “Geen definitieformulering vastgesteld”.

Een label met dubbele punt houdt de bestaande onzekere grens en krijgt geen tweede melding. Lege tekst blijft `not_evaluated`. Een naamwoordelijke definitie zonder werkwoord houdt haar pass. Evaluator, opslag en UI tonen het nieuwe onderdeel generiek; die code is niet gewijzigd.

**Tests:**
- Labelvarianten: exact, met hoofdletter en punt, met witruimte, tussen aanhalingstekens, met koppelteken, met lidwoord, een ander woord, en met uitroepteken.
- Label met dubbele punt, en lege tekst.
- Vier nominale definities die hun pass houden, waaronder ‘tijdelijke opslag’ en ‘Schakelblad (SB)’.
- Service via beide laadpaden (T20 en T22), opslag plus teruglezen (`applied`, contract, onderdelen).

**Contract.** /6 → /7.
- `test_def770_herstel_zinsgrenzen.py`: de contracttest bevat nu de volledige versiegeschiedenis in de docstring, en `/6` staat in de lijst van niet-actuele versies.
- Historische verwachtingen in de vervolg- en int01-tests zijn ongewijzigd (bytegelijk aan de herstelkopie).

**Skills.** `skills/definitie-toetsregels/reference.md`: toetsalinea uitgelijnd op de voortzetting met voorzetselgroepen en op het losse label; contract `/7`. De NL-definities-skill is ongewijzigd. Bundels bouwt de coördinator.

## 3. Generatie — beslispunt nodig

Gelezen:
- `g24-rapport-v1.md`, `g24-adjudicatie-v1.json` en `g24-invoer-v1.json`;
- alle 48 generatie- en aanvraagbestanden in `g24-generaties-v1/`;
- de volledige G05-prompt uit `logs/def770-vervolg/g24-voorbereiding-contract6-v1.json`: `api_verzoek.messages[0].content` is gelijk aan de prompt; kopie in `analyse-prompt-G05-nieuw-v1.txt`;
- het bronontvangstbewijs.

**Vastgestelde mechanieken:**

1. **Steekproefvariatie bij identieke verzoeken.** Voor Opus 5 wordt `temperature` volgens de configuratie niet meegestuurd (`beleid.temperature_meegestuurd: False`; `anthropic_client._verzendbeleid`; `config.yaml`, `model_routing.capabilities`).
   - Van de twaalf dossier/variant-combinaties hadden h1 en h2 steeds hetzelfde `request_sha256`. Toch verschilt de uitvoer in 11 van de 12 (`analyse-herhalingen-v1.py`).
   - De G05-omissie zit in één van twee trekkingen van byte-identieke verzoeken. G05 nieuw h1 behoudt de markering, h2 niet.
   - Een promptzin kan de kans verschuiven, maar het behoud niet garanderen. Dat verklaart ook waarom ad45 niet stabiel helpt.
2. **Gevolgen vallen systematisch weg, in beide armen.** Het gaat om gevolgen die aan een voorwaarde of status vastzitten, en om ontkende gevolgen:
   - G02: ‘registratie heropent niet automatisch’ ontbreekt in alle vier teksten (B13/B15/B16/B20).
   - G06: de stopplicht, de voortduring tot afronding en de afzonderlijke statusbeslissing ontbreken in alle vier (B08/B10/B11/B18).
   - G05: de markering bij de wachttijdroute ontbreekt in één van vier (B03).

   Dit is een promptconflict zonder beslisregel (regelnummers in de G05-prompt):
   - KWALITEITSCONTROLE r283–288 (`definition_task_module.py`:295–300) controleert handeling, relatie en modaliteit. Een koppeling tussen voorwaarde en gevolg, of een ontkend gevolg, controleert zij niet. Wel geeft zij een weglaatlicentie: “Een werkafspraak of mogelijkheid die het begrip niet afbakent, laat je weg”.
   - INT-01 r245 (`json_based_rules_module.py`:446) zegt “Neem bronbijzaken … niet op” en vraagt compactheid.
   - ESS-01 r162–163 (`ESS-01.json`) sluit een “gewenst effect … of gebruik” uit.

   Een gevolg lijkt daardoor op een bijzaak of effect. Het model moet zelf kiezen tussen weglaten en behouden, zonder criterium. G05 h2 voegt de twee vrijgavegronden samen tot één ‘of’ en laat daarbij het gevolg van één tak weg (zie ook STR-09 r232–236).
3. **Vernauwen met een variabele eigenschap (G01).** ‘op de (centrale) sorteertafel’ staat in alle vier teksten, terwijl de bron zegt dat de plaats mag veranderen.
   - Er is een conflict tussen MECHANISME 2 “Vernauw begrippen met domein-qualifiers” (r22–26; `context_awareness_module.py`:206) en INT-01 “maak de betekenis niet smaller”.
   - ARAI-04 r126 regelt alleen wat met de toestemming zelf gebeurt. Dat die toestemming een eigenschap als niet-bepalend aanwijst, staat er niet in.
   - Causaliteit is niet bewezen; het is een samenhang in beide armen.
4. **Nevenbevinding, niet de oorzaak in de proef:**
   - De app kapt elke documentsnippet af op 500 tekens (`prompt_service_v2._sanitized_passage` met `max_length=500`). Standaard geldt een totaalbudget van 800 tekens (`DOCUMENT_SNIPPETS_MAX_CHARS`).
   - In de proef was de bron vooraf in fragmenten van hooguit 450 tekens gesplitst, dus volledig aanwezig (`alles_volledig_in_prompt: True`).
   - In productie zou de G05-bronpassage (945 tekens) vóór de onvolledigheidsmarkering worden afgekapt. De kwitantie legt `truncated` vast.
   - Ook in de proef loopt de voorwaardezin over twee `<bron>`-elementen (“…of zodra” | “de ingestelde wachttijd verstrijkt”).

**Waarom nu geen promptcorrectie:**
- Een vierde controlepunt (“voorwaarde → gevolg, ontkend gevolg, variabele eigenschap”) is precies het soort extra instructietekst waarvan het effect niet bewezen is. Mechaniek 1 laat zien dat zo'n zin behoud niet kan garanderen.
- Het effect is nu niet te meten: geen betaalde calls, en er rest US$0,7854.
- Wijzigen van ESS-01 of INT-01 zelf raakt de toetsregelbron en valt buiten dit mandaat.

**Voorstel ter beslissing:**
- **A — aanbevolen: onafhankelijke controle op betekenisbehoud na generatie.**
  - Een tweede, afzonderlijke modelaanroep krijgt de gebruikte bronpassages uit de kwitantie plus de kandidaat.
  - Zij geeft per bronbewering van het type voorwaarde, gevolg, uitzondering, negatie of variabele eigenschap een gestructureerde dispositie: `behouden`, `weggelaten` (met de reden bijzaak of afbakenend) of `toegevoegd zonder bron`.
  - De uitkomst wordt als `review_required`-onderdeel bij de kandidaat getoond. De app herschrijft niet automatisch en genereert niet opnieuw.
  - Nodig:
    - een nieuwe promptmodule en een parser;
    - een aanroep via `AIServiceV2` en `ModelRouter`;
    - een veld in het generatieresultaat of de registratie (JSON in `generation_prompt_data`, zonder nieuwe kolom);
    - UI-weergave;
    - kosten van ongeveer één extra call per generatie;
    - extra latentie, in strijd met het doel van minder dan 5 s generatietijd.
  - Grens: dit is een AI-oordeel, geen bewijs. Het maakt verlies zichtbaar in plaats van het te voorkomen. Een effectmeting vraagt een nieuwe proef met budget.
- **B — gestructureerde invoer.** De gebruiker legt bepalende kenmerken en negaties vast. Dat vraagt een schema-, UI- en requestwijziging. Parafrase maakt een lexicale controle onbetrouwbaar, dus ook hier is een semantische controle nodig. Alleen zinvol in combinatie met A.
- **C — alleen prompt:** een vierde controlepunt, en MECHANISME 2 afstemmen op “niet smaller”. Goedkoop, maar zonder meting geen effectclaim, en behoud is nooit gegarandeerd (mechaniek 1). Hooguit als aanvulling op A.
- **Los daarvan:** een besluit over de afkapping van snippets op 500 en 800 tekens. Daarbij spelen kosten, promptlengte en bronintegriteit.

## 4. RED/GREEN en logs (`logs/def770-restherstel/`)

| Stap | Log | Uitkomst |
|---|---|---|
| Herstelkopieën | `herstelkopie-v1/` (10 bestanden, via `herstelkopie-maken-v1.py`) | alle GELIJK vóór de edits |
| RED | `int01-red-v1.log` en `.xml` | 410 tests, **25 failures**: exact de positieve T20-gevallen, alle T22-labelvarianten, de service (T20/T22, beide laadpaden) en contract /7; alle tegenvoorbeelden waren al groen |
| GREEN | `int01-green-v1.log` en `.xml` | 410 tests, 0 failures, exit 0 |
| Gerichte regressie | `int01-gericht-regressie-v1.log` en `.xml` | **1245 tests, 0 failures, 5 bestaande skips**, exit 0 |
| Aanvullende INT-01-raakvlakken | `int01-aanvullend-regressie-v1.log` en `.xml` | 54 tests, 0 failures |
| Integratie (offline journey, export) | `int01-integratie-v2.log` en `.xml` | 28 tests, 0 failures, 1 skip |
| T24-set als ontwikkelregressie | `t24-ontwikkelregressie-v1.log` (`analyse-t24-regressie-v1.py`) | 24/24 conform op de zinsstructuuras (was 22/24); ontwikkelbewijs, geen acceptatie |
| Black | `int01-black-v1.log`, `int01-black-v2.log` | ongewijzigd, exit 0 |
| Ruff 0.16.5 (gepind) | `int01-ruff-0165-v1.log` (1× ISC004 in de nieuwe test, hersteld), `int01-ruff-0165-v2.log` | All checks passed |
| make lint | `int01-make-lint-v1.log` | exit 0 |
| Diffs t.o.v. herstelkopie | `restherstel-diff-app-v1.log`, `restherstel-diff-skills-v1.log` | — |

`int01-integratie-v1.log` staat er ook, maar de run faalde op de ontbrekende `timeout`-binary (exit 127). Er liep toen geen test.

Analysescripts (alleen lezen, geen productcode): `analyse-*.py`, `diff-vastleggen-v1.py`.

## 5. Gewijzigde bestanden

| Bestand | SHA256 |
|---|---|
| `src/domain/int01/zinsgrenzen.py` | `12f0cd61d4d48c00f50d82f95a6b23bf5936661d66a709a952001446a552651a` |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` | `077bd0630c44cc3f6097309f44ca21044649e04012f2f5bc145336533c5dd36d` |
| `tests/unit/validation/test_def770_restherstel_zinsgrenzen.py` (nieuw) | `a505d4f3fe4436d7e1df33b06ec6c000942304e391dafb6ed27b4a748a4be808` |
| skills `skills/definitie-toetsregels/reference.md` | `a759935adfe33be77d8054d4cf444f155efbca5ea59a3ace5daba81042dfeabd` |

Aantoonbaar ongewijzigd (`filecmp` t.o.v. de herstelkopie):
- `definition_task_module.py` en `json_based_rules_module.py`;
- de NL-definities `SKILL.md` en `reference.md`;
- `test_def770_vervolg_zinsgrenzen.py`, `test_def770_int01_zinsgrenzen.py` en `test_def770_int01_opslag.py`.

## 6. Resterende beperkingen

- **T20-dekking bewust beperkt.** Alleen één extra woord, na ‘de’ of ‘het’, bij zeven voorzetsels, en een laatste woord zonder -n. Langere groepen, meervoud op -n, ‘een’ of ‘op’ blijven naar beoordeling gaan. Dat is een conservatief dekkingsverlies, geen fout.
- **Grenzen zonder leesteken worden nergens gedetecteerd.** Dit is een bestaande, algemene beperking van de classifier. Een voorbeeld: ‘Hij roept ‘Klaar?’ uit het regent’. Daar valt de echte grens na ‘uit’, niet bij het leesteken. Onder /6 werd dit al geaccepteerd, en /7 verandert dat niet. Dispositie door de coördinator: tracken of een waiver.
- **T22 dekt alleen het losse label (hooguit één inhoudswoord).** Het volgende blijft zinsstructuur-pass:
  - een label van meer woorden zonder formulering;
  - een tekst gelijk aan een begrip van meer woorden.

  Voor dat laatste zou de domeinfunctie het begrip moeten krijgen. Dat raakt de handtekening van opslag en repository, en is niet gedaan.
- **Generatie:** het beslispunt uit §3 staat open. Er is geen verbetering geclaimd. Contract, bron en tests zijn geen effectbewijs.
- **Na de broncontrole volgt eerst de review door dezelfde Codex-reviewer**, daarna de brede gate en de bundels door de coördinator. De onafhankelijke acceptatie van T20 en T22 staat nog open.

Bronnen: `docs/analyses/def606-regeldossiers/INT-01-implementatie/herstel-20260924-v1/astra-acceptatiebevindingen-v1.md`, `eindstatus-titelbeleid-v1.md`, `titel-en-budgetbesluit-v1.md`; `effectproeven-vervolg-20260924-v1/t24-gevallen-v1.json`, `t24-adjudicatie-v1.json`, `g24-rapport-v1.md`, `g24-adjudicatie-v1.json`, `g24-invoer-v1.json`, `g24-generaties-v1/*`; `logs/def770-vervolg/g24-voorbereiding-contract6-v1.json`; `src/services/prompts/prompt_service_v2.py`:94 en 757–784; `src/services/ai/anthropic_client.py`:33–41 en 216–250; `config/config.yaml`:227–239.
