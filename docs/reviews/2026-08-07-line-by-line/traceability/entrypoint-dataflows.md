# Entrypoints en dataflows

| Entrypoint | Hoofdstroom | Belangrijkste grenzen | Reviewrisico's |
|---|---|---|---|
| `src/main.py` | Streamlit UI → session state → container → repositories/services | UI, SQLite, AI-clients | sessie-isolatie, ruwe fouten/PII, stale links, a11y |
| `src/api/feature_status_api.py` | FastAPI GET → status-JSON → responsemodel | API, filesystemartefact | ontbrekende bron veroorzaakt 500 (`B006-009`) |
| `src/services/orchestrators/definition_orchestrator_v2.py` | request → classificatie/context/weblookup → prompt → AI → validatie → opslag | providers, webbronnen, validators, DB | contextverlies, provenance, providerfouten, transacties |
| `src/document_processing/*` + RAG renderer | upload → extractie → chunks → vectorstore | bestandsparser, PyMuPDF, embeddings | RTF-placeholder als inhoud, bestandsnaamlogging, licentie |
| `src/database/*` en repositories | domeinservice → SQLite query/transactie → persistentie | connection ownership, WAL, migraties | data-integriteit en recovery vormen grootste P1-cluster |
| `scripts/*` | handmatige operatie → Git/DB/docs/config | operatorinput, cwd, defaultpaden | meerdere destructieve of fail-open runbooks |
| `.github/workflows/*` en Makefile | CI-event → scripts/tests/scanners | GitHub permissions, toolchain, markers | shellinjectie, fail-open scans, verkeerde testinterpreter |

De volledige symboolmapping staat in `production-to-tests.csv`. Deze tabel is
een architectuursamenvatting, geen vervanging van de per-symbooltrace.
