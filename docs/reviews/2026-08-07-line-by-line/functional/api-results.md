# Functionele API-resultaten

## Bewezen gedrag

| Flow | Zonder statusartefact | Met geldige tijdelijke fixture |
|---|---|---|
| `GET /api/feature-status` | 500 | 200 |
| `GET /api/feature-status/summary` | 500 | 200 |
| `GET /api/feature-status/epic/{id}` | 500 | 200 of 404 |
| `GET /api/feature-status/by-status/{status}` | 500 voor geldige status; 400 voor ongeldige status | 200 of 400 |

De enige JSON-bron `docs/architectuur/feature-status.json` ontbreekt en de
updater genereert een ander HTML-artefact. Dit is finding `B006-009`. Met een
gemockte geldige JSON-fixture gedragen happy paths en 404/400-contracten zich
correct.

De gerichte feature-status- en security-wiringtests waren 18/18 groen. Security
headers en CORS-wiring bleven intact in de lokale TestClient-run. Een echte
Uvicorn-deployment, externe netwerkcalls en productie-auth zijn niet getest.
