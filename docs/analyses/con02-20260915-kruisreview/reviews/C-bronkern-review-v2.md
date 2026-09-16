**Vier bevindingen gesloten; drie blijven gedeeltelijk open.**

## Resterende bevindingen

### P1 — #1: één gebonden claim kan andere claims laten meeliften

[contract.py:601](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/domain/sources/contract.py:601) gebruikt `any(...)` voor de bewijsassociatie. Bij twee claims met `supported=true`, waarvan één naar een bewijsbron verwijst en de andere `source_id=None` heeft, blijft `semantic_support=pass`. Ook een onbekend bron-ID wordt eerst `None` en kan zo meeliften.

Daarnaast accepteren de controles voor gezag en verwijzing één positieve entry naast een tegenstrijdige entry voor **hetzelfde bron-ID**.

**Aanpassing:** vereis bewijsassociatie voor iedere positief beoordeelde claim en detecteer tegenstrijdige oordelen over hetzelfde bron-ID. De huidige regressietests dekken hoofdzakelijk afzonderlijke ongeldige entries, niet deze combinaties.

### P1 — #5: replay bindt receipt-inhoud onvoldoende aan de oorspronkelijke passage

[contract.py:775](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/domain/sources/contract.py:775) controleert de hash van `content`, maar niet dat `content` overeenkomt met het bronprefix volgens `max_passage_chars`.

Concrete trigger: neem een echte beoordeling met afkapgrens 300, vervang receipt-`content` door de volledige oorspronkelijke passage, bereken de bijbehorende `content_hash` opnieuw en voeg een citaat voorbij positie 300 toe. De oorspronkelijke bronhash en fingerprint blijven gelijk; replay accepteert het onverzonden citaat. Ook `truncated` en `source_version` worden niet gecontroleerd.

**Aanpassing:** verifieer de exacte inhoud tegen bronpassage en afkapgrens, plus versie en afkapmarkering. De nieuwe kwitantie wordt correct geproduceerd; de replaycontrole sluit deze wijziging nog niet uit.

### P2 — #6: een misvormde alias omzeilt conflictcontrole

[validation_orchestrator_v2.py:50](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/orchestrators/validation_orchestrator_v2.py:50) bepaalt aanwezigheid met `isinstance(..., list)`.

Met `provenance_sources=[bron]` en `sources="beschadigd"` zijn beide sleutels aanwezig en ongelijk, maar wordt zonder fout de canonieke lijst beoordeeld. Dit geldt ook voor recordvalidatie en verzwakt de eerdere controle op aanwezige sleutels.

**Aanpassing:** onderscheid aanwezigheid van typegeldigheid; behandel aanwezige misvormde of conflicterende aliassen als technische fout.

## Dispositie van alle zeven

| # | Status | Controle |
|---|---|---|
| 1 | Gedeeltelijk open | Losse inconsistenties afgewezen; combinaties hierboven blijven slagen. |
| 2 | **Gesloten** | Feitelijke `identity`-metadata bereikt de geëscapete prompt en daarmee de AI-cache-invoer. |
| 3 | **Gesloten** | Foutkwitantie gaat vóór lege bronnen in beide wrappers én replay. |
| 4 | **Gesloten** | Ontbrekende/verkeerd gevormde onderdelen geven `malformed_response` zonder assessment-cacheboeking; echte onzekerheid blijft open. |
| 5 | Gedeeltelijk open | Exacte beoordelingskwitantie aanwezig; replaybinding onvoldoende. |
| 6 | Gedeeltelijk open | Geldige aliases, lijstconflicten en invoerimmutabiliteit afgehandeld; misvormde alias uitgezonderd. |
| 7 | **Gesloten** | Tegenvoorbeeld beschrijft nu het ontbreken van de eerste alternatiefgroep, zonder haar voorwaarde algemeen verplicht te maken. |

Bij `part_correction` geen aanvullende regressie vastgesteld: één onderdeel, gebonden deskundigenbewijs en behoud van het oorspronkelijke oordeel blijven aanwezig.

**Verificatie:** [manifest v3](/tmp/DEF-743-core-hashes-v3.log) **29/29 gelijk bij start én einde**. Aangeleverde logs vermelden **1628 passed, 21 subtests**, exit 0 en schone lint; niet door mij uitgevoerd. Mutatiebewijs betreft discriminatie, geen chronologisch RED-before-GREEN. Dit oordeel betreft de statische C-fixes, niet afronding van DEF-743 of de actieve D/F-integratie.