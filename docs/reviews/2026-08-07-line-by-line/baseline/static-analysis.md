# Static analysis and dependency baseline

## Codekwaliteit

| Controle | Resultaat | Concreet bewijs |
|---|---|---|
| Ruff | PASS | `All checks passed!` |
| Black | PASS | 371 bestanden unchanged |
| Mypy | PASS | baseline 0 fouten |
| Untyped-def overrides | PASS ratchet | baseline 2 |
| Toolpins | PASS | Ruff 0.15.20, mypy 1.18.2, Black 26.5.1 consistent |
| Complexity | PASS ratchet, schuld aanwezig | 200 overtredingen: C901=90, PLR0911=18, PLR0912=54, PLR0915=38 |
| Duplicatie | NIET GETEST | repository heeft geen geconfigureerde duplicatiescanner/gate |

**Bewezen:** de complexiteitsratchet verbetert van 201 naar 200 en faalt dus
niet. De resterende 200 overtredingen zijn wel bestaande technische schuld;
de tool adviseert `--update`, maar de baseline is niet gewijzigd.

## Dependency-audit

`pip-audit` vindt vijf advisories in twee gepinde packages en eindigt met exit 2.
De matching packageversies zijn bewezen; bereikbaarheid is afzonderlijk
beoordeeld.

| Advisory | Classificatie na broninspectie | Bewijs / aanbeveling |
|---|---|---|
| `aiohttp==3.14.1`, `PYSEC-2026-3545` | **P2 suspected reachability**; dependencymatch proven | `aiohttp.ClientSession` verwerkt responses van externe bronnen in `src/services/web_lookup/{sru,rechtspraak_rest,wiktionary,wikipedia,wikipedia_synonym_extractor}_service.py`; C-extensies zijn actief. Malforme response kan de kwetsbare parser bereiken. Upgrade naar `aiohttp>=3.14.3`; tijdelijk `AIOHTTP_NO_EXTENSIONS=1`. Exploit is niet live uitgevoerd. |
| `aiohttp==3.14.1`, `PYSEC-2026-3546` | false positive voor huidige app | server-side WebSocketpad vereist; app serveert met FastAPI/Uvicorn en gebruikt geen aiohttp-server/WebSocket. Upgrade blijft aanbevolen. |
| `aiohttp==3.14.1`, `PYSEC-2026-3547` | false positive voor huidige app | vereist aiohttp WebSocket-client; geen `ws_connect` of aiohttp-WebSocketcode gevonden. |
| `gitpython==3.1.55`, `GHSA-3f7w-8rr8-f37f` | niet bereikbaar in huidige app | geen GitPython-import of `IndexFile.checkout`/`TagReference.create` in `src`/`tests`; upgrade naar `>=3.1.57` voor defense-in-depth. |
| `gitpython==3.1.55`, `GHSA-p538-c434-8v24` | niet bereikbaar in huidige app | geen `Commit.count`-pad gevonden; upgrade naar `>=3.1.57`. |

`pip check` meldt geen gebroken requirements. Dat bewijst dependency-
compatibiliteit, niet lock-pariteit: `requirements.txt` pint GitPython 3.1.55,
terwijl de gedeelde venv 3.1.45 bevat.

## Bandit

Bandit scant `src` zonder scannererrors en rapporteert 14 resultaten: 4 HIGH en
10 MEDIUM. Na handmatige broninspectie:

### Kandidaten voor formele findings

1. **P2 suspected — onbegrensde externe XML-parsing.** Vier B314-meldingen:
   `src/services/web_lookup/rechtspraak_rest_service.py:83` en
   `src/services/web_lookup/sru_service.py:279`, `:787`, `:931`. Externe XML
   bereikt `xml.etree.ElementTree.fromstring`. Een exploit/DoS is niet live
   uitgevoerd. Aanbevolen: `defusedxml`, harde responsegroottelimiet en
   structurele diepte-/recordlimieten.
2. **P3 suspected — lokale pickle-cache.**
   `src/voorbeelden/robust_cache.py:185` laadt lokale cachebytes met
   `pickle.load`. Het codepad is bereikbaar via lokale cachebestanden; geen
   remote schrijfpad is aangetoond. Aanbevolen: JSON/msgpack of ondertekende,
   permission-beperkte cache met veilige invalidatie.

### Contextueel false positive

- 5× B608: dynamische SQL gebruikt vaste/geallowliste identifiers,
  placeholderconstructies of tabelnamen uit SQLite-metadata; waarden blijven
  geparameteriseerd.
- 4× B324: MD5 wordt alleen gebruikt voor niet-authenticatieve cachekeys en een
  edit-session-id, niet voor cryptografische integriteit of secrets.

## Waarschuwingen en grenzen van de baseline

- De codeformatter en typechecker zijn groen, maar bewijzen geen runtimecorrectheid.
- De complexiteitsgate is een ratchet, geen absolute `max-complexity=10`-clean
  state; 200 overtredingen blijven bewezen aanwezig.
- De coverage is 49,21%: boven de projectvloer 45%, onder de globale 80%-norm.
- Live exploitatie, live AI-calls en WebSocketpaden zijn niet uitgevoerd.
- De dependency-audit leest `requirements.txt`; de gedeelde venv wijkt voor
  GitPython af. Beide toestanden zijn vastgelegd en mogen niet worden verward.

Volledige machine-output staat in `baseline/logs/quality-*.log` en
`baseline/logs/security-*.log` binnen `baseline/logs.tar.gz`; de afzonderlijke
SHA-256-digests staan in `baseline/logs-manifest.sha256`.
