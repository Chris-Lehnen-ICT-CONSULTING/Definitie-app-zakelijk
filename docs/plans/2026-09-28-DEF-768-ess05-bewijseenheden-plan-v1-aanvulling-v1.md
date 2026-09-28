# DEF-768 — aanvulling v1 op het plan bewijseenheden (correcties na Codex-review deel B)

> **Aanvulling op** `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` (sha256 `4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3`). Het plan zelf blijft ongewijzigd. Waar deze aanvulling afwijkt, gaat zij voor.
>
> **Aanleiding:** de Codex-review van deel B, `logs/def768/bewijseenheden-b-v1/codex-review-result-v1.md`, geeft NO-GO op HEAD `334ba89aa62a6cd1023f3ddbd82636c160fc76a7`. Er zijn vier bevindingen, B1–B4. Chris heeft ingestemd met de herstelrichting uit de vervolgopdracht van 28-09. Drie van de vier fouten zaten al in het plan: deel C (stop), taak B1 (`_voorwaarde_behouden`) en taak B2 (orakels D en A/C).
>
> **Grenzen ongewijzigd:**
> - geen wijziging aan de norm, het bewijsregels-productiepad (`src/`), de prompt, de lokale controle, skills of config;
> - geen budgetbesluit, geen freeze en geen netwerk- of betaalde aanroep.

---

## C1 — R18A stopt na een kritieke run (bevinding B1, blocker)

**Afwijking van de uitvoering in B3.** B3 liep door na een kritieke run en velde het oordeel pas achteraf. Deel C schrijft een stop voor.

**Nieuwe eis.** Zodra een run is vastgesteld die de proef afkeurt, vertrekt er in fase `interpretatie` geen volgende interpretatieaanroep meer. Zo'n run is:
- een **kritieke run** volgens deel C: `pass` of `fail` terwijl M-c of M-b op een dragend feit onwaar is, of een E-run die volgens C2 kritiek is;
- **of een M-d-afkeur** ("Ook bij M-d ≤ 8/12 stopt de proef", deel C). Dat is het geval als het aantal juiste M-d plus de nog niet uitgevoerde runs plus de runs die op handmatige beoordeling wachten (C2) niet boven 8 kan komen.

**Duurzaam:**
- **In het grootboek.** De stoppende run krijgt `inhoudelijke_stop` (de reden) in haar gevalrecord. De details bevatten de run en het aantal resterende, niet-gestarte aanroepen.
- **Weigering.** `controleer_fasestart` en elke reservering in die fase weigeren daarna. Een herstart, ook met een nieuw proces, kan de stop dus niet omzeilen.
- **Samenvatting.** De samenvatting krijgt `stop`: reden, run en niet-gestarte aanroepen. Het grootboek heeft het veld `inhoudelijke_stop`.
- **Telling.** De M-d-stop en het proefoordeel in de samenvatting tellen alle geregistreerde runs van de fase uit het grootboek, dus ook runs van een eerdere start.

**Reikwijdte:**
- **Alleen de eigen fase.** De stop geldt alleen voor `interpretatie`. R18B (`lokale_verificatie`) is een onafhankelijke meting van de lokale controle op synthetische pakketten en blijft uitvoerbaar. Technische stops blijven zoals ze waren: die gelden voor het hele grootboek.
- **Alleen voor R18.** De mogelijkheid staat alleen open voor identiteiten met `inhoudelijke_stop=True`. Dat is alleen R18. R1–R17 blijven gelijk.

## C2 — voorwaardebehoud bij E (bevinding B2, blocker)

**Afwijking van plan taak B1.** In het plan was `_voorwaarde_behouden` een woordzoeking. Deel C beschreef E alleen met "voorwaarde weggevallen". De scorer geeft nu per E-run een status: behouden, ontkend, handmatig_beoordelen of weggevallen. Hieronder staat hoe elke status wordt vastgesteld.

**Behouden.** De voorwaarde telt als behouden bij:
- **(a)** een doelantwoord (`onderwerp` = doel) met een voorwaarde die de frase bevat, zonder ontkennende of opheffende markering;
- **(b)** een `buiten_kern`-kenmerk waarvan `kenmerk` of `waarde` de frase als voorwaarde uitdrukt, dat voor het doel `bevestigd` is, eveneens zonder markering.

**Markering.** Minimaal herkend worden: "zonder", "niet", "geen", "ongeacht", "ook zonder", "ook buiten", "altijd" en "ongeacht of" (`bewijsscorer.MARKERINGEN`). "Rond de frase" betekent: in dezelfde tekstwaarde als de frase. Dat is één voorwaarde uit `voorwaarden`, of één `kenmerk` of `waarde` van een `buiten_kern`-kenmerk. Zo'n waarde is kort, dus de hele waarde telt: vóór en na de frase, ook over komma's heen. Zo valt "altijd, ook bij storing" niet buiten de controle. De markering telt als heel woord, ongeacht hoofdletters; "nietig" bevat dus geen markering.

**Ontkend.** Staat een markering in een tekstwaarde op een van de plekken van (a) of (b) die de frase bevat, dan is de voorwaarde **ontkend** (niet behouden). Die plekken zijn een voorwaarde van een doelantwoord, of `kenmerk`/`waarde` van een `buiten_kern`-kenmerk. Dat geldt ook als een andere vermelding (a) of (b) haalt.

Een markering elders, bijvoorbeeld in een `buiten_bereik`-reden als "staat niet in de bron", maakt de voorwaarde niet ontkend. Zo'n vermelding telt hoogstens mee voor handmatig beoordelen.

**Vermeldingen.** Elke vermelding van de frase komt in het record onder `voorwaarde_vermeldingen`: pad, tekst, plek (`doelvoorwaarde`, `m_kenmerk` of `elders`) en gevonden markeringen.

**Handmatig beoordelen.** Komt de frase voor, maar valt geen vermelding eenduidig onder (a) of (b), dan is de status **handmatig_beoordelen**. Voorbeelden:
- alleen in `buiten_bereik`;
- in een M-kenmerk dat niet bevestigd is;
- in een voorwaardelijk doelantwoord naast een onvoorwaardelijk gelijk antwoord;
- in een ongeldige structuur.

**Weggevallen.** Komt de frase nergens voor, dan is de voorwaarde **weggevallen**.

**Runoordeel bij E:**

| Status | Kritiek? | M-d telt? | Categorie zonder andere kritiek |
|---|---|---|---|
| behouden | nee | als `m_d.ok` | volgens de gewone regels |
| ontkend | ja, tenzij de uitkomst `error/buiten_bereik` is | nee | `kritiek`, anders `niet_geslaagd` |
| weggevallen | ja (deel C) | nee | `kritiek` |
| handmatig_beoordelen | nee | nee | `handmatig_beoordelen` |

Bij "ontkend" is de regel letterlijk: elke andere uitkomst dan `error/buiten_bereik` maakt de run kritiek.

**Categorievolgorde:** kritiek > handmatig_beoordelen > f7 > geslaagd > niet_geslaagd. Een run in `handmatig_beoordelen` is niet geslaagd en niet automatisch kritiek. Hij stopt de proef niet en staat in het proefoordeel apart onder `handmatig_beoordelen`.

**Proefoordeel:**
- `afgekeurd` bij een kritieke run, of als M-d plus de ontbrekende runs plus de runs voor handmatige beoordeling ≤ 8 blijft. Op een run die nog handmatig beoordeeld wordt, keurt de proef dus niet automatisch af.
- `onvolledig` onder 12 runs.
- `geslaagd` zoals in deel C. Een handmatige E-run is niet behouden, dus dan niet geslaagd.
- Anders `wacht_op_handmatige_beoordeling` als er handmatige runs zijn en M-d plus die runs 11 nog haalt.
- Anders `wacht_op_f7_besluit` bij F7.
- Anders `tussengebied`.

**Stop.** Een run in `handmatig_beoordelen` stopt de proef niet. Een kritieke run door een ontkende of weggevallen voorwaarde stopt wel (C1).

**Risico (open punt).** De markering wordt lexicaal herkend binnen de tekstwaarde. Een correcte formulering als "alleen bij storing, niet daarbuiten" wordt daardoor "ontkend". Zo'n fout is conservatief: er ontstaat geen onterecht succes, maar mogelijk wel een onterechte kritieke run en dus een stop. De ruwe uitvoer en de vermeldingen staan altijd in het callrecord, zodat de inhoudsreviewer het kan nagaan.

## C3 — orakelstructuur `vereist` en `toegestaan` (bevindingen B3 en B4, important)

**Afwijking van plan taak B1 en B2.** In het plan had elk feit één lijst `eenheden`. Elke genoemde eenheid moest met een van die prefixen beginnen. Die lijst mengde twee dingen:
- verplicht dragend bewijs;
- toegestane context.

Daardoor liet D de buurbeschrijving als zelfstandig kostenbewijs toe (B3) en keurde D een terechte Uitleen-zin naast de betaalzin af (B4).

**Nieuwe structuur.** Per feit geldt: `{"toestand": [...], "vereist": [...], "toegestaan": [...], "f7": [...]?}`.

**Regel M-b per feit:**
- elke genoemde eenheid begint met een prefix uit `vereist` of `toegestaan`;
- als `vereist` niet leeg is, begint minstens één genoemde eenheid met een prefix uit `vereist`;
- als `vereist` en `toegestaan` beide leeg zijn, draagt het feit alleen zonder bewijs (onbesproken).

Een antwoord met alleen toegestane context en geen vereiste eenheid heeft dus M-b onwaar. `controleer_orakel` weigert een orakel met het oude veld `eenheden` of met onbekende velden.

**Orakels, consequent voor alle vier gevallen:**

| Geval | Feit / onderwerp | toestand | vereist | toegestaan |
|---|---|---|---|---|
| A | tijdelijk / doel | bevestigd | "Uitleen:" | — |
| A | tijdelijk / verhuur | bevestigd | "Verhuur:", `<buurbeschrijving>` (beide dragen tijdelijk) | — |
| A | kosteloos / doel | bevestigd | "Uitleen:" | — |
| A | kosteloos / verhuur | onbesproken (f7: ontkend) | — | — |
| C | tijdelijk / doel | bevestigd | "Uitleen:" | — |
| C | tijdelijk / verhuur | ontkend | "Verhuur:", `<buurbeschrijving>` (beide dragen permanent) | — |
| D | kosteloos / doel | bevestigd | "Voor uitleen betaalt" | "Uitleen:" |
| D | kosteloos / verhuur | ontkend | "Voor verhuur betaalt" | "Verhuur:", `<buurbeschrijving>` |
| E | — (geen dragende kenmerken) | — | — | — |

Bij E blijft voorwaarde "storing" staan, met `voorwaarde_vereist_voor` = `error/buiten_bereik` en `review_required`. De toelichting volgt C2.

Voor D betekent dit:
- blind hergebruik (alleen "Uitleen:") geeft M-b onwaar;
- alleen de buurbeschrijving bij verhuur geeft M-b onwaar;
- de Uitleen-zin samen met de betaalzin geeft M-b waar.

Over de betekenis van de buurnaam beslist F7; dat blijft open. De buurbeschrijving telt bij D daarom alleen als context, nooit als kostenbewijs.

**Invoer:**
- **Schema.** Het invoerschema wordt `def768-ess05-bewijsregel-invoer/3`.
- **Nieuw bestand.** De invoer wordt opnieuw gemaakt als nieuw bestand `reports/DEF-768-AI-20260928-R18/bewijsregel-invoer-v2.json`. `-v1.json` wordt niet overschreven. De maker pint ook deze aanvulling op sha256.
- **Runner.** De runner pint `-v2`. Hij weigert `-v1` op de invoerhash, op het schema (`/2`) en op het orakelveld `eenheden`.

**Eén commit voor B3 en B4.** Beide wijzigen dezelfde orakelstructuur en hetzelfde invoerbestand `-v2`. Gescheiden commits zouden een tussenstand opleveren waarin de maker en het gepinde invoerbestand niet overeenkomen, of een extra invoerversie. Rood wordt wel per bevinding apart gelogd.

## Wat ongewijzigd blijft

- **Budget.** 18 aanroepen, cumulatief 399 → maximaal 417 binnen 427. Kostenplafond USD 6,03 binnen de kaderrest USD 21,798865.
- **R18B.** De zes pakketten en `lokale-invoer-v1.json` (sha `a36172a0…5b81`) blijven gelijk.
- **Contract.** `ess05-bewijsregels/6`, prompt /4, systeemprompthash `a18e2e07…d465`.
- **Uitvoering.** Geen retry, geen cache, geen technische herhaling. Een betaalde stap alleen na een "go" van Chris met een eigen budgetbesluit, en pas nadat Codex deze correcties heeft gecontroleerd.
