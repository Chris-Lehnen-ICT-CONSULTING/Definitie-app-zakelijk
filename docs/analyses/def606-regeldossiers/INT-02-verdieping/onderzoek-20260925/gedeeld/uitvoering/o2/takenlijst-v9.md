# DEF-835 — actuele takenlijst v9

Actuele ingang; v8 en eerdere versies blijven historisch bewijs.

- [x] WP1 en offline WP2 afgerond; code `48a6b3fa5`, dossier-HEAD `2be81c577`.
- [x] Akkoord voor het beschreven WP3-contract en de zeven geplande bestanden ontvangen.
- [x] Werkboom en beide CLI's gecontroleerd; branch `feature/DEF-835-int02-o2`.
- [x] Voorstel voor twee noodzakelijke aanvullingen opgesteld: `wp3-scopeaanvulling-v1.md`.
- [x] Bestaande nulmeting uitgevoerd: **55 passed in 1.36s**, exit 0; volledig bewijs in `bewijs/wp3-nulmeting-v1.log`, HEAD `2be81c577653f8efbab6fa2c3794598556d32d13`.
- [ ] Chris: aanvulling van zeven naar negen bestanden akkoord. De reeds gestelde vraag blijft open; geen WP3-code gewijzigd.
- [ ] WP3: Claude CLI RED → GREEN → coördinatorverificatie → onafhankelijke Codex CLI-review → commit/rapportage.
- [ ] Kostenplafond en profiel voor de reeds toegestane echte technische modelproef vaststellen.
- [ ] WP4: goldset/hold-out en inhoudelijke modelevaluatie.
- [ ] WP5: gedeelde opslag DEF-626 en appintegratie, inclusief ketenlogging/providervoorwaarden.
- [ ] WP6: eindverificatie/PR en afzonderlijke activering.

## Vastgelegde grens WP3 / WP5

WP3 bewijst de evaluator via de registry en de publieke schemaweergave, met tijdelijk testrecord. Het actieve INT-02-record blijft O1. Dit bewijst nog geen O2-uitvoer door de volledige validatieservice.

Bij WP5 moet ook `src/services/validation/modular_validation_service.py` concreet in het integratieplan worden opgenomen. De set `_EVALUATORS_MET_DEELUITKOMST` op regels 102–104 bevat alleen `SENTENCE_BOUNDARY` en `PRONOUN_REFERENCE_ASSESSMENT`; regels 1018–1023 selecteren daarmee welke evaluators een gestructureerde deeluitkomst krijgen. `_verwerk_uitkomst` op regels 1635–1641 boekt zo'n resultaat alleen bij `geen_cijfer` of een NE-deeluitkomst. Zonder gerichte aansluiting kan de volledige service het nieuwe assessment dus niet op alle statuspaden publiek doorgeven. Dit bestand valt buiten WP3; geen stille tiende bestandswijziging en geen claim dat de appintegratie al werkt.

Actions blijven uit. Geen echte appmodelcalls uitgevoerd. De toestemming daarvoor is aanwezig; het concrete proefbedrag is nog niet vastgesteld.
