# DEF-768 — aanvulling v4 op het plan bewijseenheden (besluit na Codex-hercontrole v3, B2-rest-3)

> **Aanvulling op** het plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` (sha256 `4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3`) en de aanvullingen v1 (sha256 `a81e6af1314e7a01b9773c30ca87ca54069a0e333f192f370002d0a6d1324f3b`), v2 (sha256 `3c409857a29f908000c098652378507230ca4e7d29331ad8bf6c51a39c2258e2`) en v3 (sha256 `3e338a78daa7334ab2441ee8847cd2e9514fd4ed2fed9fb124ce5d6f9803079d`).
>
> Plan en eerdere aanvullingen blijven ongewijzigd. Waar deze aanvulling afwijkt, gaat zij voor. Zij vervangt **C2 in zijn geheel** (v1, v2 en v3: elke automatische voorwaardestatus bij E) en de invoer. C1 en C3 blijven gelden.
>
> **Aanleiding:** de Codex-hercontrole v3 (`logs/def768/bewijseenheden-b-v1/codex-hercontrole-result-v3.md`) geeft NO-GO op HEAD `951ccdf35` met blocker B2-rest-3. Eén exacte match overheerste strijdige aanvullende voorwaarden:
> - `["bij storing", "deze voorwaarde is optioneel"]`;
> - `["bij storing", "als storing ontbreekt"]`;
> - `["bij storing", "of op verzoek"]`;
> - een exacte doelvoorwaarde naast het M-kenmerk `kenmerk="geldigheid van deze voorwaarde"`, `waarde="optioneel"`.
>
> Met drie zulke E-runs werd de proef weer 12/12 geslaagd.
>
> **Besluit van Chris (optie 2):** casus E wordt nooit automatisch als voorwaarde-`behouden` of geslaagd gescoord. Het voorwaardeoordeel van elke E-run is altijd een menselijk oordeel van Chris. A, C en D blijven volledig automatisch.
>
> **Grenzen ongewijzigd:**
> - geen wijziging aan de norm, `src/`, de prompt, de lokale controle, skills of config;
> - geen budgetbesluit, geen freeze en geen netwerk- of betaalde aanroep.

---

## Reden

Vier lexicale rondes (C2 v1, v2, v3 en de exacte lijst) sloten telkens een route af, waarna de volgende Codex-controle een nieuwe onterechte `behouden` vond: een voorwaardelijke aanhef zonder markering, een formulering buiten de lijst, en nu een exacte formulering naast een strijdige aanvulling. Of een voorwaarde "behouden" is, is een betekenisvraag over de hele combinatie van voorwaarden en kenmerken. Een lexicale regel die dat automatisch beslist, blijft te omzeilen. Daarom beslist de scorer het niet meer.

## C2 v4 — beslisregel

**Automatisch (ongewijzigd deterministisch):**
- M-a, M-b, M-c en M-d worden gescoord zoals voorheen.
- Een E-run met een uitkomst anders dan `error/buiten_bereik` (M-d fout) is automatisch `niet_geslaagd`.
- Een E-run met M-c of M-b onwaar is kritiek, zoals elke run.
- Een E-run met juiste uitkomst krijgt categorie `handmatig_beoordelen` (`HANDMATIG_E`) en `voorwaarde_status: handmatig_beoordelen`. Hij telt niet mee voor M-d en niet voor "E behouden", tot Chris oordeelt.
- Kritieke runs, de afkeur bij M-d ≤ 8 en de duurzame stop (C1) werken voor alle runs zoals voorheen.
- Een proef met E-runs is daardoor nooit automatisch `geslaagd`; hoogstens `wacht_op_handmatige_beoordeling`. Negen juiste A-, C- en D-runs plus drie juiste E-runs geven `wacht_op_handmatige_beoordeling` (M-d 9, E behouden 0/3).

**Lexicale signalen: verwijderd, niet als hint bewaard.** De markeringenlijst, de normalisatie, de aanhef, `voorwaarde_formuleringen` en `voorwaarde_vereist_voor` zijn uit scorer en orakel verwijderd. Een niet-bindende hint zou het oordeel van Chris kunnen sturen en is aantoonbaar onbetrouwbaar. Het record bevat geen voorwaardevermeldingen meer; het beoordelingsblad toont de volledige uitvoer.

**Eindregel.** De proef is **geslaagd alleen als** alle automatische criteria van deel C slagen (M-d ≥ 11, M-c en M-b 12/12, geen kritieke run) **én** Chris elke E-run `behouden` oordeelt. Een E-run telt pas als behouden bij dat oordeel én uitkomst `error/buiten_bereik`.

Per oordeel:
- `behouden` — telt voor M-d en "E behouden", alleen als de run automatisch `handmatig_beoordelen` was. Een automatisch niet-geslaagde run wordt hierdoor niet geslaagd.
- `ontkend` — kritiek, tenzij de uitkomst `error/buiten_bereik` is; dan `niet_geslaagd`.
- `weggevallen` — kritiek.

## Oordeelprocedure

1. Na de proef: `scripts/ess05/r18_e_oordeel.py blad --calls <uitmap>/interpretatie-*/calls --doel <blad>.md`. Het blad toont per E-run de volledige modeluitvoer (antwoordtabel met voorwaarden en bewijseenheden met hun tekst, kern, buiten de kern, buurgroepen, buiten bereik, de volledige ruwe uitvoer), de bron met eenheden, de deterministische uitkomst en de sha256 van de beoordeelde uitvoer. Geen hints of voorlopige status.
2. Chris vult het sjabloon onderaan het blad in als oordeelbestand (schema `def768-ess05-e-oordeel/1`): per E-run `run`, `e_uitvoer_sha256`, `status` (`behouden`, `ontkend` of `weggevallen`), `beoordelaar` en `datum` (JJJJ-MM-DD).
3. `scripts/ess05/r18_e_oordeel.py eindoordeel --calls … --oordeel <oordeel>.json --doel <eindoordeel>.json` combineert proefoordeel en oordeelbestand (`bewijsscorer.eindoordeel`).
4. Het eindoordeel wordt geweigerd (en niets geschreven) bij: een ontbrekend, dubbel of onbekend oordeel, een afwijkende `e_uitvoer_sha256`, een ongeldige status, een lege beoordelaar, een ongeldige datum, een onbekend schema of onbekende velden. De sha256 van de ruwe uitvoer in elk callrecord wordt opnieuw berekend; een gewijzigd record wordt geweigerd.
5. Het eindoordeel bevat de beslisregel, de oordelen en de sha256 van het oordeelbestand; doelen worden nooit overschreven.

## Invoer v5

- **Schema.** Het invoerschema wordt `def768-ess05-bewijsregel-invoer/6`.
- **E-orakel.** `voorwaarde_formuleringen` en `voorwaarde_vereist_voor` vervallen; `voorwaarde` (`storing`) en `uitkomst` (`error/buiten_bereik`) blijven, met een nieuwe toelichting. A, C en D blijven gelijk.
- **Nieuw bestand.** `reports/DEF-768-AI-20260928-R18/bewijsregel-invoer-v5.json`. `-v1` tot en met `-v4` worden niet overschreven.
- **Maker.** De maker pint deze aanvulling (v4) op sha256.
- **Runner.** De runner pint `-v5` en weigert `-v1` tot en met `-v4` (schema en invoerhash); het v4-orakel wordt ook door `controleer_orakel` geweigerd (onbekende velden).

## Risico's

**Correctie op aanvulling v3.** Aanvulling v3 schreef: "Twaalf van twaalf geslaagd is met een niet-geregistreerde formulering niet meer haalbaar." Dat was **onjuist**. Een niet-geregistreerde, strijdige formulering naast een exacte match ("bij storing" plus "deze voorwaarde is optioneel") gaf automatisch `behouden`, en drie zulke runs gaven 12/12. Het combinatierisico ontbrak in de beschrijving. Onder v4 kan geen enkele formulering of combinatie automatisch slagen.

**Nieuwe, bewust aanvaarde risico's:**
- **Tijd.** Elke proef met E vraagt handwerk van Chris: drie E-runs lezen en oordelen. Zonder oordeel blijft de proef `wacht_op_handmatige_beoordeling`.
- **Subjectiviteit.** Het oordeel is menselijk en niet reproduceerbaar door een tweede run van de scorer. De hash-binding legt vast wélke uitvoer beoordeeld is, niet dat het oordeel juist is.
- **Beoordeling pas na de proef.** Chris ziet de E-runs pas na afloop. Een E-run met juiste uitkomst stopt de proef tijdens de uitvoering niet meer (de lexicale kritieke stop van v1–v3 bestaat niet meer); kritiek volgt pas uit het oordeel. De deterministische stops (M-c/M-b, afkeur bij M-d ≤ 8, C1) blijven wel tijdens de uitvoering werken. Een slechte E-run kan dus budget voor latere runs laten verbruiken dat onder v3 bespaard was.
- **Geen automatische 12/12.** Een volledig automatisch geslaagde R18A bestaat niet meer; geslaagd vereist altijd het eindoordeel.

## Wat ongewijzigd blijft

- **C1 en C3.** Stop en duurzaamheid (C1) en de orakels A, C en D (C3).
- **Budget.** 18 aanroepen, cumulatief 399 → maximaal 417 binnen 427.
- **R18B.** `lokale-invoer-v1.json` (sha `a36172a0…5b81`).
- **Contract.** `ess05-bewijsregels/6`, prompt /4.
- **Uitvoering.** Geen retry, geen cache. Een betaalde stap alleen na een "go" van Chris met een eigen budgetbesluit, en pas nadat Codex deze correctie heeft gecontroleerd.
