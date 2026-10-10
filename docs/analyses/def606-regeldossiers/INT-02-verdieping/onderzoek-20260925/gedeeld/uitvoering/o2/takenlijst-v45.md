# INT-02 O2 — goldset bevroren, modelproef voorbereid (takenlijst v45)

30 september 2026. Vervangt v44 als procesingang; de daarin vastgelegde deeloplevering, merge-identiteit en het uitstel van DEF-626 blijven van kracht. Branch `feature/DEF-835-int02-o2`, HEAD `a9fb4a0b7444d073813182b662056e7c3265fc7c`. Deze goldsetbestanden zijn nog lokaal en niet gecommit of gepusht.

## Afgerond sinds v44

- [x] Chris accepteerde zeven nieuwe onzekere labels, zeven verschuivingen naar aanvullend ontwikkelmateriaal en de exacte 24/16-splitsing. Besluit: `goldset-voorbereiding/labelronde-v1/besluit-chris-selectie-split-v1.md`.
- [x] Veertig synthetische gevallen met accepted hoofdlabels bevroren: 20 `pass`, 10 `fail`, 10 `review_required`; ontwikkeling 24, hold-out 16. Bronobjecten, onafhankelijke beoordelaarsvoorstellen, citaten, Chris' beslissingen en SHA-256 staan in `goldset-voorbereiding/goldset-freeze-v1/bewijsmanifest-v1.json`.
- [x] Q1-pending proefmanifest en 43 appverzoeken offline voorbereid. Runneridentiteit: `anthropic` / `claude-opus-5`, prompt `def835-int02-prompt/1`, maximaal 43 calls en US$12. Verzoeken bevatten geen goldlabels. De actuele officiële modelpagina bevestigt de basisprijzen US$5/US$25 per miljoen tokens.
- [x] Gerichte runnerproeven: 177 passed. Geen live proefmap en geen kwalificatiecalls.

## Eerstvolgende beslisgrens

- [ ] Chris bevestigt het exacte pending manifest, SHA-256 `d67659fa7fe06801b4a6c744269d06405a3eab1b3c434622605e5bd18e4bdb29`, en de 43 gevallen, SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`, voor het afzonderlijke Q1-akkoordbestand. Dit is vereist door het bestaande runnercontract; het eerdere algemene proefmandaat noemt deze latere hashes niet.

## Daarna

- [ ] Regressie C105/C107/C112: status én citaat/grond controleren. Alleen bij slagen de 24 ontwikkeling uitvoeren; daarna de 16 ongewijzigde hold-outs. Stopregels, geen retries en cumulatief budget blijven gelden.
- [ ] Inhoudelijke modelkwaliteit, kosten, latency en bewijsgrenzen rapporteren; bij tekortkoming stoppen of een geautoriseerde nieuwe profielversie voorbereiden.
- [ ] Appintegratie en eindverificatie afronden. DEF-626 blijft afzonderlijk uitgesteld.
- [ ] Alleen na afzonderlijk besluit over productieactivering O2 inschakelen. Actions blijven uit; geen nieuwe merge of publicatie in deze fase.

Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-preflight-v1.md` en `goldset-voorbereiding/labelronde-v1/takenlijst-v14.md`.
