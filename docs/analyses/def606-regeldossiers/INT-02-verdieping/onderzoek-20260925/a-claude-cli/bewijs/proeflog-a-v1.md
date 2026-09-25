# Proeflog — onderzoekslijn A (INT-02), 25-09-2026

Verwachtingen vooraf: [`verwachtingen-a-v1.md`](verwachtingen-a-v1.md) (geschreven vóór uitvoering). Leesbasis: HEAD `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` (checkout-branch `onderzoek/DEF-772-INT-03-20260925`, geen getrackte wijzigingen — `git status --porcelain --untracked-files=no` leeg; commit gelijk aan de in de opdracht genoemde main-HEAD). Runtime: `.venv/bin/python` 3.13.15. Geen modelcalls, geen netwerk, geen productiedata; de `ModularValidationService` krijgt geen cleaning-service en geen repository.

**Beperking vastlegging:** in deze sessie werden shell-omleidingen (`> bestand`, `;`, `echo $?`) door de toolpermissie geweigerd. De scripts schrijven daarom zelf hun invoer/uitkomst naar JSON; stdout staat hieronder letterlijk overgenomen uit de tooluitvoer; de exitstatus is 0 afgeleid uit het ontbreken van een foutmelding van de Bash-tool (die een niet-nul exit als fout rapporteert).

## P1 — servicegedrag (bewijssoort: offline routeproef op servicelaag, geen UI)

- Commando (vanuit repo-root): `PYTHONPATH=src .venv/bin/python docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/a-claude-cli/bewijs/proef-p1-service.py`
- Invoer: `p1-invoer.json` (25 casussen) · Uitkomst: `p1-uitkomsten.json` · Exit: 0
- Stdout (letterlijk):

```
INT02-C01 review_required [] viol= ['CON-01', 'CON-CIRC-001', 'ESS-05', 'INT-01', 'VER-01']
INT02-C02 review_required [] viol= ['ARAI-04', 'ARAI-04SUB1', 'CON-01', 'CON-CIRC-001', 'ESS-05', 'INT-01', 'VER-01']
INT02-C03 review_required ['\\bindien\\b'] viol= ['CON-01', 'CON-CIRC-001', 'ESS-05', 'INT-01', 'INT-10', 'VER-01']
INT02-C04 review_required ['\\bindien\\b'] viol= ['CON-01', 'ESS-05', 'INT-01', 'INT-08', 'INT-10', 'VER-01']
INT02-C05 review_required [] viol= ['CON-01', 'ESS-05', 'INT-08']
INT02-C06 review_required [] viol= ['CON-01', 'ESS-05', 'ESS-CONT-001', 'STR-FORM-001', 'VAL-EMP-001', 'VAL-LEN-001']
INT02-C10 review_required [] viol= ['CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C11 review_required ['\\bindien\\b'] viol= ['CON-01', 'CON-CIRC-001', 'ESS-05', 'INT-01', 'INT-10', 'VER-01']
INT02-C12 review_required ['\\btenzij\\b'] viol= ['ARAI-04', 'CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C13 review_required [] viol= ['CON-01', 'ESS-05', 'VER-01']
INT02-C14 review_required [] viol= ['ARAI-04', 'ARAI-04SUB1', 'CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C15 review_required [] viol= ['CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C16 review_required [] viol= ['CON-01', 'ESS-05', 'INT-01', 'INT-08', 'VER-01']
INT02-C17 review_required ['\\bindien\\b'] viol= ['ARAI-06', 'CON-01', 'ESS-05', 'INT-01', 'INT-10', 'STR-01', 'VER-01', 'VER-03']
INT02-C18 review_required [] viol= ['CON-01', 'ESS-05', 'VER-01', 'VER-03']
INT02-C19 review_required ['\\bmits\\b'] viol= ['ARAI-06', 'CON-01', 'ESS-05', 'INT-01', 'STR-01', 'VER-01', 'VER-03']
INT02-C20 review_required ['\\bvoor zover\\b'] viol= ['CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C21 review_required [] viol= ['CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C22 review_required [] viol= ['CON-01', 'ESS-05', 'INT-01', 'VER-01']
INT02-C23 review_required [] viol= ['CON-01', 'CON-CIRC-001', 'ESS-05', 'ESS-CONT-001', 'STR-FORM-001', 'VAL-LEN-001']
INT02-C24 review_required ['\\bindien\\b'] viol= ['CON-01', 'CON-CIRC-001', 'ESS-05', 'INT-01', 'INT-10', 'SAM-04', 'VER-01', 'VER-02']
INT02-C25 review_required ['\\bindien\\b'] viol= ['CON-01', 'CON-CIRC-001', 'ESS-05', 'ESS-CONT-001', 'INT-01', 'INT-10', 'SAM-04', 'STR-FORM-001', 'VER-01']
INT02-C26 review_required ['\\bindien\\b'] viol= ['ARAI-06', 'CON-01', 'ESS-05', 'INT-01', 'INT-08', 'INT-10', 'STR-01', 'VER-01']
INT02-C27 review_required [] viol= ['CON-01', 'ESS-05', 'INT-01', 'VER-01', 'VER-03']
INT02-C29 review_required ['\\bindien\\b'] viol= ['CON-CIRC-001', 'ESS-05', 'INT-01', 'INT-10', 'VER-01']
```

### Toetsing aan de verwachtingen

| Verwachting | Uitkomst |
|---|---|
| V1 altijd review_required, nooit pass/violation | **Bevestigd** voor alle 25 (ook lege tekst C06 en alleen-term C23). |
| V2 reden = letterlijke toetsvraag, geen passagecitaat | **Bevestigd** 25/25 (`p1-uitkomsten.json`, veld `int02_reason`). |
| V3 signalen precies bij patroonwoorden | **Bevestigd met twee afwijkingen in de voorspelling, niet in de code:** C21 ("tenzij-clausule") geeft geen signaal omdat de term niet in de getoetste tekst staat (casusconstructie: alleen `begrip`, geen `term:`-aanhef) — mijn voorspelling was fout; C15 bevat geen "moet" (zie V6). Alle andere 23 conform. |
| V4 context verandert INT-02 niet | **Bevestigd** (C29 = C03 + context: zelfde status, reden, signaal). CON-01 verdwijnt uit de violations; INT-02 ongemoeid. |
| V5 `indien` → gescoorde violation INT-01/INT-10 | **Bevestigd, scherper dan voorspeld:** INT-10 faalt op álle 8 `indien`-teksten (C03, C04, C11, C17, C24, C25, C26, C29) en op geen enkele tekst zonder `indien` (C12 tenzij, C19 mits, C20 voor zover: INT-10 pass). INT-01 faalt ook op vrijwel alle teksten zónder `indien` (C01, C10, C14, C15, C16, C21, C22, C27) — INT-01 is hier geen onderscheidend signaal. |
| V6 `moet` → ARAI-04/ARAI-04SUB1 | **Bevestigd** voor C02 en C14 (beide regels). C15 bevat geen `moet` (voorspelling fout geformuleerd). C12 geeft ARAI-04 (niet SUB1) — vermoedelijk op "zou"; niet nader onderzocht. |
| V7 historische C01–C06 gereproduceerd | **Bevestigd**: statussen en signalen identiek aan `INT-02-bewijs-v1/uitkomsten.json` (11-09, `d68a98a9`). |

Nevenwaarneming: `overall_score` is `None` en `is_acceptable` `false` in elke casus (algemeen ketenfeit DEF-622/630; niet INT-02-specifiek).

## P2 — generatieprompt-rendering (bewijssoort: offline moduleproef; geen volledige `build_prompt`, geen modeluitvoer)

- Commando: `PYTHONPATH=src .venv/bin/python docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/a-claude-cli/bewijs/proef-p2-prompt.py`
- Uitkomst: `p2-uitkomsten.json` · Exit: 0
- Stdout (letterlijk):

```
{
  "include_examples_in_rules": true,
  "integrity_rules_module_geregistreerd": false,
  "dode_toegang_voorbeeld_in_uitvoer": false,
  "int02_blok_letterlijk": [
    "🔹 **INT-02 - Geen beslisregel**",
    "- Een definitie bevat geen beslisregels of voorwaarden.",
    "- **Instructie:** Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'",
    "  ✅ transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken.",
    "  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken."
  ]
}
```

| Verwachting | Uitkomst |
|---|---|
| W1 INT-02-blok letterlijk | **Bevestigd** (zie stdout). |
| W2 IntegrityRulesModule niet geregistreerd; "toestemming verleend…"-voorbeeld nergens in uitvoer | **Bevestigd** (15 geregistreerde modules, `integrity_rules` = `JSONBasedRulesModule`). |
| W3 STR-09 ✅-voorbeeld met `indien` | **Bevestigd**: `  ✅ Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart`. |
| W4 ESS-03-instructie "behoud inhoudelijk noodzakelijke namen en voorwaarden" | **Bevestigd** (letterlijk in `p2-uitkomsten.json` → `ess_rules`). |
| W5 INT-01/ARAI-04-instructies | **Gedeeltelijk**: koppen `INT-01`, `ARAI-04`, `ARAI-04SUB1` vastgelegd; de instructieregels zelf vielen buiten het zoekfilter van het script (bron: `json_based_rules_module.py:303-304, 376` — codelezing). |

## Niet uitgevoerd (bewust)

Volledige promptassemblage met echte `EnrichedContext`; echte modelgeneratie (G-kwaliteit); UI-weergave (Streamlit); opslag/snapshot, vaststelgate, import, export (alleen codelezing); ARAI-04-oorzaak bij C12; INT-10-meldingstekst voor de gebruiker; casussen C28 en C30–C33 (ontwerpcasussen).
