# DEF-771 — offline ketenverificatie INT-02 (v3)

26 september 2026. Claude Code CLI-uitvoerder a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Verwerkt de twee resterende bevindingen uit `vervolg-keten-codex-correctiereview-v1.md`. `vervolg-keten-rapport-v1.md`/`-v2.md` en replay v1/v2 blijven ongewijzigd. Omvang valt onder `akkoord-int02-omvangverruiming-v1.md`.

Bronidentiteit: app-HEAD e9a865b856ca6dba85ee73bedc0e303f05fa86fb, skill-HEAD 750068253a7389e201daedc5b9aa0afd5c0be032; `src/` en `tests/` ongewijzigd; evaluator `judgment_review.py` SHA-256 ca35ad6a…0d2771.

## Bewijsbestanden

| Bestand | SHA-256 | Inhoud |
|---|---|---|
| `vervolg-keten-replay-v3.py` | d36c4b5f…1df2fe3 | proef (v2 64ef833c… ongewijzigd) |
| `vervolg-keten-replay-v3.json` | a4037120…217ebd | uitkomst, `exitstatus: 0` |
| `vervolg-keten-replay-v3.log` | 1cc3e6bc…fcaeb | commando en exit 0 |
| `vervolg-keten-negatieve-controle-v1.log` | fa77e1f6…d7801 | drie geïnjecteerde fouten, commando, scriptinhoud, exit 0 (= alle drie afgewezen) |
| `vervolg-keten-replay-v3-lint.log` | — | Ruff exit 0, Black exit 0, omvang v2→v3 |

## Wijziging v2 → v3 (mini-diff)

- Nieuw `route_b_fouten(naam, b)`: fout als route B niet is uitgevoerd; controleert de verse uitkomst; fout als de teruggelezen registratie ontbreekt; controleert de teruggelezen uitkomst met dezelfde `controleer()`-verwachtingen (status, signalen, vaste tekst, exacte NE-melding, geen reviewvraag bij NE); vergelijkt status, reden, signalen en deel met de verse uitkomst.
- Nieuw `eindstatus(uit)`: 1 zodra route A óf `route_b_fouten` van een casus een fout geeft. Bestaande `fouten` in de JSON worden niet meer als enige bron gebruikt, ook niet bij een vroegtijdig afgebroken route B.
- `schrijfroute()` legt `route_b_fouten` vast in plaats van alleen de verse controle; docstring aangevuld.
- Omvang (na Black, `vervolg-keten-omvangmeting-v1.py` met v2 en v3 als argumenten — de uitvoerlabels "v1/v2" betekenen hier v2/v3): 21 uitvoerbare regels toegevoegd, 6 verwijderd; v3 telt 288 uitvoerbare en 333 fysieke regels. `diff`: 31 regels erbij, 7 eraf.

## Normale run v3

Exit 0; voor C83, C105 en C56 zijn route A en route B foutloos, route B `uitgevoerd: true`. De teruggelezen `applied.validation` voldoet in elke casus aan de verwachting en is in alle vier velden gelijk aan de verse uitkomst; bij C56 is de exacte melding "INT-02 — Niet uitgevoerd: context ontbreekt. Er is geen inhoudelijk oordeel." getoetst. Deze controle is nu automatisch en laat de proef falen bij afwijking.

## Negatieve controle (`vervolg-keten-negatieve-controle-v1.log`)

Tijdelijk script (inhoud in de log) laadt v3 en de echte v3-JSON, injecteert één fout per keer in een kopie en roept `route_b_fouten` en `eindstatus` aan:

| Geïnjecteerde fout | eindstatus | Fout |
|---|---|---|
| geen (basis) | 0 | — |
| route B niet uitgevoerd (C83) | 1 | "route B niet uitgevoerd" |
| teruggelezen registratie ontbreekt (C105) | 1 | "teruggelezen registratie ontbreekt" |
| verkeerde teruggelezen NE-melding (C56: "kern" i.p.v. "context") | 1 | tekst wijkt af + wijkt af van verse uitkomst |

Afgewezen 3/3, scriptexit 0. De log is gefilterd op Streamlit bare-mode-waarschuwingen (vermeld in de log).

## Route A en route B — ongewijzigd ten opzichte van v2

Route A (invoer, herladen, tweemaal verse validatie, renderer, berekende issues-projectie, expertlezing, vaststelpreview, export met en zonder gate) en route B (bronvoorsteltoepassing via `DefinitionEditService.pas_voorstel_toe` → `apply_source_proposal`, teruglezen, expertlezing, twee diagnostische exports zonder gate) zijn inhoudelijk gelijk aan v2; zie `vervolg-keten-rapport-v2.md` voor de per-functietabellen. De begrenzingen daar blijven gelden: geen browser of knoppen, geen geslaagde vaststelling; de drie previews blokkeren op de genoemde bestaande voorwaarden (inclusief "Geen validatieresultaat beschikbaar") en noemen INT-02 niet als afzonderlijke blokkade; B5 blijft het geldende besluit; exports zonder gate zijn diagnostisch.

## Opslag — afbakening

Route A schrijft geen validatieresultaat; behoud bij gewone opslag is niet onderzocht. Route B bewijst opslag bij toepassing van een bronvoorstel.

## Beperkte conclusie

De onderzochte expertlezing (`ExpertReviewTab._v2_uit_opgeslagen_validatie`) en recordexport (JSON, zonder aangeleverd resultaat) gebruiken het bewaarde voorstelresultaat niet als INT-02. Expliciet aangeleverde `toetsresultaten` brengen INT-02 wel in de JSON-export. Dit is geen volledige ketenoplevering. Een eventuele gedeelde opslag- of doorgifteoplossing hoort bij DEF-626 en vraagt een apart ontwerpbesluit.
