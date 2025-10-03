# Validation Rules Extraction - Master Index

## Summary
- **Total Rules:** 46
- **Categories:** 8
- **Extraction Date:** 2025-10-02
- **Extraction Status:** COMPLETE

## Rules by Category

### ARAI (9 rules) - Aristotelian Structure
Rules ensuring Aristotelian definitional structure

- [ARAI-01](./ARAI/ARAI-01.md): geen werkwoord als kern (afgeleid)
- [ARAI-02](./ARAI/ARAI-02.md): Vermijd vage containerbegrippen
- [ARAI-02SUB1](./ARAI/ARAI-02SUB1.md): Lexicale containerbegrippen vermijden
- [ARAI-02SUB2](./ARAI/ARAI-02SUB2.md): Ambtelijke containerbegrippen vermijden
- [ARAI-03](./ARAI/ARAI-03.md): Beperk gebruik van bijvoeglijke naamwoorden
- [ARAI-04](./ARAI/ARAI-04.md): Vermijd modale hulpwerkwoorden
- [ARAI-04SUB1](./ARAI/ARAI-04SUB1.md): Beperk gebruik van modale werkwoorden
- [ARAI-05](./ARAI/ARAI-05.md): Vermijd impliciete aannames
- [ARAI-06](./ARAI/ARAI-06.md): Correcte definitiestart: geen lidwoord, geen koppelwerkwoord, geen herhaling begrip

### CON (2 rules) - Context
Rules for context-specific formulation

- [CON-01](./CON/CON-01.md): Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming
- [CON-02](./CON/CON-02.md): Baseren op authentieke bron

### DUP (1 rules) - Duplicate
Rules for duplicate detection

- [DUP_01](./DUP/DUP-01.md): Geen duplicaat definities in database

### ESS (5 rules) - Essential
Rules for essential definitional elements

- [ESS-01](./ESS/ESS-01.md): Essentie, niet doel
- [ESS-02](./ESS/ESS-02.md): Ontologische categorie expliciteren (type / particulier / proces / resultaat)
- [ESS-03](./ESS/ESS-03.md): Instanties uniek onderscheidbaar (telbaarheid)
- [ESS-04](./ESS/ESS-04.md): Toetsbaarheid
- [ESS-05](./ESS/ESS-05.md): Voldoende onderscheidend

### INT (9 rules) - Integrity
Rules for data integrity and consistency

- [INT-01](./INT/INT-01.md): Compacte en begrijpelijke zin
- [INT-02](./INT/INT-02.md): Geen beslisregel
- [INT-03](./INT/INT-03.md): Voornaamwoord-verwijzing duidelijk
- [INT-04](./INT/INT-04.md): Lidwoord-verwijzing duidelijk
- [INT-06](./INT/INT-06.md): Definitie bevat geen toelichting
- [INT-07](./INT/INT-07.md): Alleen toegankelijke afkortingen
- [INT-08](./INT/INT-08.md): Positieve formulering
- [INT-09](./INT/INT-09.md): Opsomming in extensionele definitie is limitatief
- [INT-10](./INT/INT-10.md): Geen ontoegankelijke achtergrondkennis nodig

### SAM (8 rules) - Semantic
Rules for semantic coherence

- [SAM-01](./SAM/SAM-01.md): Kwalificatie leidt niet tot afwijking
- [SAM-02](./SAM/SAM-02.md): Kwalificatie omvat geen herhaling
- [SAM-03](./SAM/SAM-03.md): Definitieteksten niet nesten
- [SAM-04](./SAM/SAM-04.md): Begrip-samenstelling strijdt niet met samenstellende begrippen
- [SAM-05](./SAM/SAM-05.md): Geen cirkeldefinities
- [SAM-06](./SAM/SAM-06.md): Één synoniem krijgt voorkeur
- [SAM-07](./SAM/SAM-07.md): Geen betekenisverruiming binnen definitie
- [SAM-08](./SAM/SAM-08.md): Synoniemen hebben één definitie

### STR (9 rules) - Structure
Rules for structural validation

- [STR-01](./STR/STR-01.md): definitie start met zelfstandig naamwoord
- [STR-02](./STR/STR-02.md): Kick-off ≠ de term
- [STR-03](./STR/STR-03.md): Definitie ≠ synoniem
- [STR-04](./STR/STR-04.md): Kick-off vervolgen met toespitsing
- [STR-05](./STR/STR-05.md): Definitie ≠ constructie
- [STR-06](./STR/STR-06.md): Essentie ≠ informatiebehoefte
- [STR-07](./STR/STR-07.md): Geen dubbele ontkenning
- [STR-08](./STR/STR-08.md): Dubbelzinnige 'en' is verboden
- [STR-09](./STR/STR-09.md): Dubbelzinnige 'of' is verboden

### VER (3 rules) - Relation
Rules for relationship validation

- [VER-01](./VER/VER-01.md): Term in enkelvoud
- [VER-02](./VER/VER-02.md): Definitie in enkelvoud
- [VER-03](./VER/VER-03.md): Werkwoord-term in infinitief

## Quick Reference Tables

### By Priority
| Priority | Count | Rules |
|----------|-------|-------|
| hoog | 23 | ARAI-06, CON-01, CON-02, DUP_01, ESS-01, ESS-02, ESS-03, ESS-05, INT-03, INT-06, INT-10, SAM-02, SAM-03, SAM-04, SAM-05, SAM-07, SAM-08, STR-01, STR-02, STR-03, STR-04, STR-06, VER-01 |
| midden | 23 | ARAI-01, ARAI-02, ARAI-02SUB1, ARAI-02SUB2, ARAI-03, ARAI-04, ARAI-04SUB1, ARAI-05, ESS-04, INT-01, INT-02, INT-04, INT-07, INT-08, INT-09, SAM-01, SAM-06, STR-05, STR-07, STR-08, STR-09, VER-02, VER-03 |
