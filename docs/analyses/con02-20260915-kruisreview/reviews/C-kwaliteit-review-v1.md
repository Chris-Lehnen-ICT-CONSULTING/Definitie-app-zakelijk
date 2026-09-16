### Eén resterende P2

**[contract.py:916](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/domain/sources/contract.py:916) — eager evaluatie doorbreekt veilige kwitantieafwijzing.**

Trigger: vervang in een verder geldige `assessment_receipt` één `content` door `"\ud800"` (een los surrogaatteken), met ongewijzigde brongegevens.

Voorheen wees de prefixcontrole dit af vóór UTF-8-encoding. Nu berekent de tuple voor `_eerste_reden` alsnog de hash: `UnicodeEncodeError`. `valideer_beoordeling` raiset; de overkoepelende replay vangt dit af als “beoordeling onleesbaar” en verliest de specifieke kwitantiereden en modelherkomst. Er ontstaat geen positieve beoordeling.

**Correctie:** laat hashberekening pas plaatsvinden nadat oorspronkelijke hash, inhoudstype en exacte prefix zijn geaccepteerd. Voeg bovenstaande mutatie toe aan de bestaande kwitantiematrix.

### Overige delta en bewijsgrenzen

Geen andere concrete P1/P2 gevonden in de vijf kwaliteitsdelta’s tegenover de prequality-snapshots.

- Onafhankelijke SHA-256-controle begin/einde: **5/5 owned bestanden** gelijk aan het [owned manifest](/tmp/DEF-743-quality-C-hashes.log); **13/13 bijbehorende testbestanden** ongewijzigd tegenover [prequality](/tmp/DEF-743-prequality.json). Geen nieuwe tests in deze delta.
- Rapport- en bewijsloghashes bleven gelijk.
- Bestaande logs geïnspecteerd: **2170 passed, 5 skipped, 1 xfailed, 21 subtests passed**; journey **3 passed**; owned lint/typing/complexiteit schoon.
- Uitsluitend statische review; geen tests/imports uitgevoerd. De gemelde trigger is statisch afgeleid.

Eerdere functionele reviews blijven gesloten. Gecombineerde root-gates en volledige story-acceptatie vallen buiten dit oordeel.