# DEF-768 — aanvulling v3 op het plan bewijseenheden (correctie na Codex-hercontrole v2, B2-rest-2)

> **Aanvulling op** het plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` (sha256 `4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3`), aanvulling v1 (`…-aanvulling-v1.md`, sha256 `a81e6af1314e7a01b9773c30ca87ca54069a0e333f192f370002d0a6d1324f3b`) en aanvulling v2 (`…-aanvulling-v2.md`, sha256 `3c409857a29f908000c098652378507230ca4e7d29331ad8bf6c51a39c2258e2`).
>
> Plan en eerdere aanvullingen blijven ongewijzigd. Waar deze aanvulling afwijkt, gaat zij voor. Zij vervangt **regel 1 van C2 v2** (automatisch "behouden") en de invoer. De overige regels van C2 v2 blijven gelden, net als C1 en C3.
>
> **Aanleiding:** de Codex-hercontrole v2 (`logs/def768/bewijseenheden-b-v1/codex-hercontrole-result-v2.md`) geeft NO-GO op HEAD `51bd6d5a0` met blocker B2-rest-2. Vier formuleringen kregen automatisch `behouden` en `geslaagd`:
> - "bij afwezigheid van storing";
> - "als storing ontbreekt";
> - "bij storing of op verzoek";
> - "bij de storingsdienst".
>
> Met drie zulke E-runs werd de proef weer 12/12 geslaagd. Oorzaak: een voorwaardelijke aanhef zonder markering bewijst niet dat de oorspronkelijke voorwaarde behouden is.
>
> **Besluit van Chris (optie 1):** automatisch behouden alleen bij een exacte match met een vooraf geregistreerde positieve formulering.
>
> **Grenzen ongewijzigd:**
> - geen wijziging aan de norm, `src/`, de prompt, de lokale controle, skills of config;
> - geen budgetbesluit, geen freeze en geen netwerk- of betaalde aanroep.

---

## C2 v3 — regel 1: alleen een exacte, geregistreerde formulering

**Behouden.** Een E-run is alleen automatisch `behouden` als aan beide voorwaarden is voldaan:
1. **Exacte formulering.** Een element van `voorwaarden` van een doelantwoord is na normalisatie **exact gelijk** aan een formulering in `voorwaarde_formuleringen` van het E-orakel. Het doelantwoord mag bovendien niet opgeheven zijn door een onvoorwaardelijk gelijk doelantwoord (zoals in C2 v1).
2. **Juiste uitkomst.** De deterministische uitkomst van `bepaal` is `error/buiten_bereik`.

**Normalisatie** (`bewijsscorer._normaliseer`), in deze volgorde:
1. casefold;
2. elke reeks witruimte (ook tabs) wordt één spatie;
3. trimmen;
4. afsluitende `.`, `,`, `;` en `:` (met tussenliggende spaties) verwijderen.

Andere leestekens, haakjes, meervoud of extra woorden maken de tekst niet exact.

**De geregistreerde lijst** (E-orakel, veld `voorwaarde_formuleringen`):

| # | Formulering |
|---|---|
| 1 | `bij storing` |
| 2 | `bij een storing` |
| 3 | `alleen bij storing` |
| 4 | `uitsluitend bij storing` |
| 5 | `in geval van storing` |
| 6 | `in geval van een storing` |

De bron van E gebruikt letterlijk "Uitleen: **bij storing** stelt de servicedesk …". Dat is formulering 1, dus een andere canonieke formulering was niet nodig. De lijst is de voorgestelde lijst uit het besluit, ongewijzigd.

**Controle van het orakel** (`controleer_orakel`). Het orakel wordt geweigerd als `voorwaarde_formuleringen`:
- niet bij een `voorwaarde` hoort;
- geen niet-lege lijst van teksten is;
- een dubbele formulering bevat;
- een formulering bevat die niet al genormaliseerd is;
- een formulering bevat zonder de frase;
- een formulering bevat met een markering.

Een orakel zonder het veld geeft nooit automatisch behouden.

**Alles wat niet exact matcht, wordt `handmatig_beoordelen`.** Dat is niet geslaagd, niet automatisch kritiek, stopt niet en telt niet voor M-d of voor "E 3/3 behouden".

Onder regel 1 van v2 slaagden deze voorbeelden nog; nu worden ze handmatig:
- de vier Codex-voorbeelden;
- "als storing", "wanneer storing", "indien storing" en "mits storing";
- "bij storing (altijdgeldig)" en "bij storingen".

**De AANHEF-prefixlogica van v2 is verwijderd.** Een aanhef is geen basis meer voor slagen en wordt ook niet meer voor diagnose gebruikt. De vermeldingen in het record (pad, tekst, plek, markering) blijven wel volledig.

**Ongewijzigd uit C2 v2:**
- **Markering:** een markering in een doelvoorwaarde of M-kenmerk geeft `ontkend`. De markeringenlijst is gelijk aan die van v2.
- **M-kenmerk:** het M-kenmerkpad geeft nooit automatisch behouden.
- **Weggevallen:** een frase die nergens staat, geeft `weggevallen` (kritiek).
- **Runoordeel en proefoordeel:** ongewijzigd. Behouden kan nu alleen nog met een exacte formulering en `error/buiten_bereik`.

**Proef.** Twaalf van twaalf geslaagd is met een niet-geregistreerde formulering niet meer haalbaar. Drie E-runs met een Codex-voorbeeld plus negen juiste runs geven `wacht_op_handmatige_beoordeling` (M-d 9, E behouden 0/3).

## Invoer v4

- **Schema.** Het invoerschema wordt `def768-ess05-bewijsregel-invoer/5`.
- **E-orakel.** Het E-orakel krijgt `voorwaarde_formuleringen` (de lijst hierboven) en een nieuwe toelichting. A, C en D blijven gelijk.
- **Nieuw bestand.** De invoer wordt opnieuw gemaakt als nieuw bestand `reports/DEF-768-AI-20260928-R18/bewijsregel-invoer-v4.json`. `-v1` tot en met `-v3` worden niet overschreven.
- **Maker.** De maker pint deze aanvulling (v3) op sha256.
- **Runner.** De runner pint `-v4`. Hij weigert `-v3` en `-v2` op schema en invoerhash, en `-v1` zoals voorheen.

## Risico's (herziene beschrijving)

**Correctie op aanvulling v2.** Aanvulling v2 schreef dat alle lexicale fouten conservatief zijn. Dat was **onjuist**: "bij de storingsdienst" en "bij afwezigheid van storing" leverden een onterecht succes op (false accept) via de aanhefprefix. Die route bestaat niet meer, want automatisch behouden vereist nu een exacte match met een vooraf vastgelegde, positieve formulering.

**Restrisico (bewust aanvaard): te streng.** Een inhoudelijk juiste formulering die niet op de lijst staat, slaagt niet automatisch. Voorbeelden: "wanneer er een storing is", "tijdens een storing", "in het geval van storing", "bij storingen" of "bij storing (servicedesk)". Zo'n run wordt `handmatig_beoordelen`. Dat betekent:
- meer handmatig beoordelingswerk;
- bij drie afwijkende E-runs geen automatisch geslaagde proef, hoogstens `wacht_op_handmatige_beoordeling`.

Dit is een bewuste keuze: liever een onterecht handmatige run dan een onterecht geslaagde.

**Blijvend (ongewijzigd uit v1/v2).**
- **Markeringen.** Die worden lexicaal herkend. "alleen bij storing, niet daarbuiten" is `ontkend`. Dat is conservatief en kan een onterechte kritieke stop geven.
- **M-kenmerk.** Een M-kenmerk naast een juiste doelvoorwaarde maakt de run handmatig.

**Wat de exacte match niet uitsluit.** De match controleert alleen de tekst van `voorwaarden`, niet of het model de voorwaarde aan het juiste kenmerk (K2, kosteloos) hangt. Een exacte formulering op een ander doelantwoord telt ook, net als in v1/v2. De uitkomst `error/buiten_bereik` van `bepaal` blijft de deterministische eis.

## Wat ongewijzigd blijft

- **C1 en C3.** Stop en duurzaamheid (C1) en de orakels A, C en D (C3).
- **Budget.** 18 aanroepen, cumulatief 399 → maximaal 417 binnen 427.
- **R18B.** `lokale-invoer-v1.json` (sha `a36172a0…5b81`).
- **Contract.** `ess05-bewijsregels/6`, prompt /4.
- **Uitvoering.** Geen retry, geen cache. Een betaalde stap alleen na een "go" van Chris met een eigen budgetbesluit, en pas nadat Codex deze correctie heeft gecontroleerd.
