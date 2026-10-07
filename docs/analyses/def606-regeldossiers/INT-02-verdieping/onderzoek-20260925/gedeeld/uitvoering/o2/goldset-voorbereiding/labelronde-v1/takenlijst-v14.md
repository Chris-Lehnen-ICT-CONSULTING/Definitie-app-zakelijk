# Takenlijst — INT-02 O2 labelronde (v14)

30 september 2026. Vervolg op v13; eerdere versies blijven als historisch bewijs bestaan.

- [x] Chris' akkoord op de zeven nieuwe `review_required`-labels, zeven verschuivingen naar aanvullend ontwikkelmateriaal en de exacte 24/16-splitsing vastgelegd in `besluit-chris-selectie-split-v1.md`.
- [x] De 40 gekozen synthetische gevalobjecten, labels, relevante passages, normgronden, beoordelaarbronnen en adjudicatie versiegebonden vastgelegd onder `../goldset-freeze-v1/`. Ontwikkeling en hold-out staan in afzonderlijke bestanden; hold-outinhoud wordt niet aan promptontwikkelaars of implementatoren gegeven.
- [x] Bronhashes, exacte citaten en verdeling gecontroleerd: 40 unieke IDs; 20 `pass`, 10 `fail`, 10 `review_required`; per familie 6 ontwikkeling en 4 hold-out. De twee onafhankelijke beoordelaarvoorstellen en Chris' besluiten zijn per geval traceerbaar in `bewijsmanifest-v1.json`.
- [x] Het Q1-runnerbestand met de drie bekende regressies plus de 40 nieuwe gevallen offline gevalideerd. Het pending proefmanifest bindt model, prompt, router, norm, bronbestanden, 43 payloadhashes, prijzen en limieten. In de 43 voorbereide appverzoeken staan geen goldlabels.
- [x] Gerichte Q1-tests: 177 geslaagd. Geen live-proefmap en geen kwalificatiecalls.
- [ ] Chris bindt zijn eerdere proefmandaat expliciet aan het nu bekende SHA-256 van het pending kwalificatiemanifest en het gevallenmanifest, conform het Q1-runnercontract. Zonder dit aparte akkoordbestand weigert de runner verzending.
- [ ] Regressiefase C105/C107/C112 uitvoeren en inhoudelijke citaten controleren; alleen bij slagen doorgaan naar 24 ontwikkelgevallen en daarna 16 ongewijzigde hold-outs, binnen maximaal 43 calls en US$12 cumulatief.
- [ ] Resultaten, kosten, latentie, fouten en bewijsgrenzen rapporteren; daarna afzonderlijk over eventuele activering besluiten. O2 en Actions blijven uit; niets gemergd.

De beoordelaarsmotiveringen en citaten zijn als bronvoorstellen overgenomen; Chris accepteerde de gevalinhoud en hoofdlabels. De mechanische controle bewijst alleen dat citaten exact in de gevaltekst staan, niet dat de appmodelredenering inhoudelijk juist zal zijn.
