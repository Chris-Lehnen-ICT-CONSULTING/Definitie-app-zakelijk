# DEF-622 — besloten vervolgcriteria en herstel

Chris geeft na controle van de bijgewerkte Linear-specificatie opdracht de nieuwe criteria functioneel te verifiëren en zo nodig te herstellen, inclusief beide open versiebindingsproblemen. Dit is de leidende aanvulling op het bestaande implementatieplan. Startbron: `9ba0a5b4b0365815fb4b1383fda63534053c134f`.

## Werkpakketten

1. **Strikte versiebinding.** Payload, opgeslagen review, gate en overname bij vaststelling hanteren dezelfde integerconventie. Ontbrekend/null/string/bool/float mag een versiegebonden oordeel niet geldig maken. `expected_version` blijft een afzonderlijke concurrencycontrole. De echte caller levert de beoordeelde versie. Bewijs geldige integerflow, fouttypen, verouderde versie, tekst wijzigen/terugzetten en statusovergang/readback.
2. **Generatie en betekenisbehoud.** Inventariseer relevante generatie-ingangen; lege context start geen modelaanroep. Controleer daadwerkelijke eindprompt en noodzakelijke naamuitzondering. Bescherm bovenbegrip en betekenisdragende woorden tegen nabewerking. Kern en toelichting blijven gescheiden. De zichtbare/opgeslagen eindkandidaat is exact de getoetste tekst; latere mutatie vereist hertoetsing.
3. **Tekstvergelijking.** Bewaar de echte geëxtraheerde definitiekern vóór nabewerking en de uiteindelijke tekst via passende bestaande metadata. Alleen bij verandering verschijnt ‘De tekst is na generatie aangepast. Bekijk wijzigingen.’ Uitklappen toont herkenbare woordtoevoegingen en -verwijderingen. Geen verzonnen beginversie bij historische records. Bewijs gewijzigde/ongewijzigde UI en readback.
4. **Casussen en oplevering.** Behoud alle 14 CON-GT- en 12 CW-GEN-ID's afzonderlijk in de bewijsmapping. Gebruik echte productiegrenzen met bevroren modeluitvoer en synthetische opslag. Benoem uitgesloten herstel- en buurgatesscope eerlijk. Onafhankelijke review, relevante projectgates en bijgewerkte draft-PR/Linear volgen.

## Besluiten en grenzen

- Naamnoodzaak wordt onderbouwd in bestaande CON-01-toelichting; geen nieuw gebruikersveld.
- Automatisch tekstherstel blijft uit: DEF-638 is vervolg en blokkeert DEF-622 niet. Geen automatische vaststelling.
- Totaalscore blijft tijdelijk niet beschikbaar; DEF-624 bepaalt latere formule.
- DEF-630 houdt de volledige gedeelde gate; dit vervolg bewijst CON-01-aansluiting en neemt die algemene scope niet over.
- Claude CLI implementeert alle code/tests/config; desktop coördineert en verifieert; afzonderlijke Codex CLI reviewt. Geen verdere delegatie.
- Geen nieuwe dependencies of databaseschema, geen broncheckout- of gebruikersdatabasewijziging, geen globale skillinstallatie, geen merge/deploy. Bestaande normale controles blijven actief.
- De nieuwe opdracht heropent expliciet de eerdere V2b-stop. Per concrete actie geldt opnieuw de bestaande pogingenlimiet; weigeringen worden niet omzeild.

## Bronnen

- [Actuele DEF-622](https://linear.app/definitie-app/issue/DEF-622), opgehaald 14 september 2026, beschrijving bijgewerkt 19:28:50 UTC.
- `casusregister-generatie-v2.md` en `gezamenlijk-besluitvoorstel-generatie-v2.md` in de hoofdcheckout onder `docs/analyses/def606-regeldossiers/CON-01-verdieping/generatie-toetsing-vervolg-20260914/`; alleen gelezen. Onderzoeksvoorstellen gelden uitsluitend voor zover later besloten.
- Bestaande review `docs/analyses/DEF-622-vaststel-review-v4.md` en opleveringsbewijs `DEF-622-oplevering-v1.md` blijven historisch brongebonden bewijs.
