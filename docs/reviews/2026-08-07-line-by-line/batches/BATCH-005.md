# BATCH-005

- Status: `verified`
- Reviewgroep: `1` — Entrypoints, build, dependencies en configuratie
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `8db11e15c2ad081e3074a8867df0e9cfb3cff227e867f160c08385ae348d7cee`
- Bestanden: `14`
- Fysieke regels: `5181`
- Python-symbolen: `0`
- Reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `requirements-dev.txt` | `cmVxdWlyZW1lbnRzLWRldi50eHQ=` | `1-1634` | 0 | `3a3b4e1c9ed29c688a90d25993c93288d9bd0129` |
| `requirements.in` | `cmVxdWlyZW1lbnRzLmlu` | `1-81` | 0 | `99b1d530222a71a439fbca9a81488068657c917d` |
| `requirements.txt` | `cmVxdWlyZW1lbnRzLnR4dA==` | `1-2493` | 0 | `4caba97d477be3bda1499870533e268a2be6fd78` |
| `.claude/rules/patterns.md` | `LmNsYXVkZS9ydWxlcy9wYXR0ZXJucy5tZA==` | `1-48` | 0 | `e8fc17d96ba9b32c68ee68270333913dec41b134` |
| `.claude/rules/project-rules.md` | `LmNsYXVkZS9ydWxlcy9wcm9qZWN0LXJ1bGVzLm1k` | `1-6` | 0 | `7961ccac0059b3611328d1dbee6675a85b54bf03` |
| `.claude/rules/streamlit-patterns.md` | `LmNsYXVkZS9ydWxlcy9zdHJlYW1saXQtcGF0dGVybnMubWQ=` | `1-34` | 0 | `b5b3be1e173477c31afe1fe0f6ba10f26528f6b6` |
| `.gitignore` | `LmdpdGlnbm9yZQ==` | `1-207` | 0 | `a21df1441704efc41d6bd2bbbcb65933d0807cd3` |
| `.gitleaksignore` | `LmdpdGxlYWtzaWdub3Jl` | `1-56` | 0 | `b4dea8cffefbd628ff2ecb39b29daded2c9d4a27` |
| `.prompt-forge/analysis-report.md` | `LnByb21wdC1mb3JnZS9hbmFseXNpcy1yZXBvcnQubWQ=` | `1-196` | 0 | `f53654f765725a8996fbc7e4d817d01f4010349c` |
| `.prompt-forge/linear-vs-codereview-report.md` | `LnByb21wdC1mb3JnZS9saW5lYXItdnMtY29kZXJldmlldy1yZXBvcnQubWQ=` | `1-204` | 0 | `c3370dab7e09aa631bf11933aba27f2aa694ac0b` |
| `.prompt-forge/werklijst-security-sprint.md` | `LnByb21wdC1mb3JnZS93ZXJrbGlqc3Qtc2VjdXJpdHktc3ByaW50Lm1k` | `1-204` | 0 | `16dd861d9ee97eea69bd569a9945d05bf7bfc178` |
| `.trunk/.gitignore` | `LnRydW5rLy5naXRpZ25vcmU=` | `1-9` | 0 | `15966d087ebc05fc3e0a2effab401a41f43c00bf` |
| `.trunk/configs/.isort.cfg` | `LnRydW5rL2NvbmZpZ3MvLmlzb3J0LmNmZw==` | `1-2` | 0 | `b9fb3f3e8caa50cb46d61e0d193bad2624b598c9` |
| `.trunk/configs/.shellcheckrc` | `LnRydW5rL2NvbmZpZ3MvLnNoZWxsY2hlY2tyYw==` | `1-7` | 0 | `8c7b1ada8a3e17d42d1022b2caddc39ba83e1466` |

## Verplichte reviewchecklist

- [x] Iedere toegewezen regel rechtstreeks uit het immutable object-ID gelezen.
- [x] Ieder toegewezen symbool en iedere functie line-by-line beoordeeld.
- [x] Callers, afhankelijkheden, tests en foutpaden gecontroleerd.
- [x] Codekwaliteit en architectuur beoordeeld.
- [x] Bugs, security en foutafhandeling beoordeeld.
- [x] Functionaliteit en relevante tests beoordeeld.
- [x] UI/UX, toegankelijkheid en responsive gedrag beoordeeld indien van toepassing.
- [x] Findings bevatten prioriteit, bewijs, reproductie en oplossing.
- [x] Bewezen, vermoed en niet-getest expliciet onderscheiden.
- [x] Onafhankelijke tweede reviewer heeft scope en findings geverifieerd.

## Bevindingen

- P2/proven: `B005-001` — UV-hashlocks laten de dependency-confusion-gate nul dependencies controleren.
- P2/proven: `B005-002` — Productie-lock mist de parser voor een actief aangeboden RTF-uploadpad.
- P2/proven: `B005-003` — Uitvoerbare Prompt-Forge-werklijst instrueert verouderde fixes en onveilige dependency-mutaties.
- P3/proven: `B005-004` — Bedoelde handover-uitzondering blijft door de uitgesloten parentdirectory genegeerd.
- P3/proven: `B005-005` — Projectregel verbiedt zeven bestaande rootbestanden inclusief de canonieke lockbronnen.

- P2/proven: `B005-006` — Actieve aiohttp-client gebruikt een versie met een bereikbaar malformed-response-DoS.
- P3/proven: `B005-007` — Verouderde expliciete GitPython-pin houdt zeven advisories in de runtime-lock.
- P2/suspected: `B005-008` — Actieve PyMuPDF-PDF/RAG-flow mist aantoonbare keuze tussen AGPL-compliance en commerciële licentie.

## Resultaat

Geverifieerd door twee verschillende reviewers. Alle 14 toegewezen bereiken en 5181 fysieke regels zijn line-by-line beoordeeld; reproducties en beperkingen staan in het bewijsdossier.
