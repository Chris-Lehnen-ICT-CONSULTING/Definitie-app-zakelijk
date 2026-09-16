# DEF-747 — technische overdracht en uitvoerbaar B1
16 september 2026, implementatiebasis 29b0900d plus DEF-746 A.

## Beschikbaarheid en besluit
De huidige bron heeft EvaluationOutcome, ReviewRequirement (reason/signals) en rule_results, plus CON-01/02-specifieke bewijsvelden. Er is geen gedeelde append-only validatiesnapshotrepository of vertrouwd ESS-beoordelingscontract. Historische context_snapshot en ontological_models.snapshot_json zijn geen validatiesnapshots. Bronbewijs mag niet als ESS-container dienen.

B1 is onafhankelijk uitvoerbaar onder DEF-624: validate_text en validate_definition sturen exact de invoer naar validatie én bronbeoordeling, zonder cleaner-aanroep of objectmutatie. De bestaande cleaner blijft voor expliciete generatie-/voorstelroutes beschikbaar; de constructor blijft compatibel. Bewijs: echte CleaningService als detectie van huidige mutatie, capture van validatortransport en objectvergelijking, plus bestaande CON-01/02-regressies. Geen echte provider.

## Concrete deelleveringen zonder issuecirkel
1. DEF-624: gedeeld beoordelingscontract met regel/normversie, inputbinding, passages/rollen, status/reden/bewijs en uitvoerherkomst; menselijke beoordeling geen inputveld actor/pass.
2. DEF-624: vertrouwde beoordelingsschrijfroute met actor uit de bevoegde gebruikerscontext, versieconflictcontrole en onderscheid tussen regeloordeel en algemene vaststelling. De bestaande CON setters controleren een niet-lege actorstring; dat is geen bewijs van authenticatie.
3. DEF-626: append-only snapshot en beoordelingsgebeurtenissen, atomair met definitieversie en expected_version. Snapshotfout rollback; eventueel draftfallback alleen expliciet unknown/stale.
4. DEF-627: gedeelde toepasbaarheid op tekst, term, context, relevante bronset/-versie en normversie. Historisch bewijs blijft ongewijzigd.
5. DEF-626: get_contractvelden/DefinitieRecord/_record_to_definition vervoeren dezelfde opgeslagen snapshot en toepasbaarheid naar nieuwe repository-instantie, editor en expert.
6. DEF-630/747: expert-/exportconsumers gebruiken die readback; ESS-fail/open blijft zichtbaar zonder aparte ESS-akkoordplicht, behoud CON-01-blokkade en CON-02-afspraken.

Volgorde van deze deelleveringen: 1–2 → 3 → 4–5 → 6. Geen afhankelijkheid van volledig sluiten DEF-745/747 terug naar de voorzieningen. B1 wacht niet op snapshots; B2 opslag/beoordeling/export wordt pas uitgevoerd wanneer de gedeelde interfaces geleverd zijn. De bestaande roadmapblokkades worden niet stil gewijzigd; dit document specificeert de benodigde faseoverdracht.

## Acceptatie en resterend werk
B1 bewijst exact transport bij uitsluitend toetsen. B2 vereist echte tijdelijke SQLite save→nieuwe repository→reload, stale-gevallen, vertrouwde actorbinding, expertvaststelling en alle exports; dit bewijs is nu niet beschikbaar. DEF-747 blijft open.
DEF-748/638 blijft uitgesteld. Eerst bovenstaande herleidbare basis; pas na afzonderlijke opdracht één onderbouwde kandidaat met origineel/diff/hertoetsing. A/B activeert geen repair of modelcalls.
