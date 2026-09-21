# Kopie-notitie — ESS-04-onderzoeksdossier in de repository (DEF-767, W1-F1)

21 september 2026. Deze map is de **documentenkopie** van het afgeronde ESS-04-onderzoeksdossier van 18 september 2026 uit het handover-archief van de hoofdcheckout (`.claude/handovers/archief/worktree-cleanup-extra-20260921-103523-914902/documenten/ESS-04-onderzoek/docs/analyses/def606-regeldossiers/ESS-04-verdieping/onderzoek-20260918/`). Ieder hier opgenomen bestand is bytegelijk aan het archief; het archief is niet gewijzigd en blijft de volledige bron.

## Methode en controle

- Kopie met `shutil.copytree` (metadata behouden; equivalent van `cp -Rp`). Volledige boom vergeleken op SHA-256 per bestand: 816 van 816 bestanden identiek aan het archief. Daarna (besluit Chris, 21 september 2026) verkleind tot documenten en data: alleen `.md`, `.json` en `.yaml` zijn in de repository opgenomen (232 bestanden, 2,7 MB, tegenover 816 bestanden, 15 MB in het archief).
- Zes kernbestanden gecontroleerd tegen de vooraf opgegeven hashes, alle OK: `instructievoorstellen-v5.md` (e101cd26…), `besluitnotitie-v1.md` (3ecba8cc…), `casusregister-v2.md` (df31d1f7…), `casusindex-v2.json` (b9dc0e40…), `veldrollen-en-keten-v2.md` (114a5cea…), `bron-bewijsregister-v3.md` (a8ac7924…).

## Bewust weggelaten: tarball en codesnapshots

Niet in de repository, wel in het archief en het eindpakket-hashmanifest (`eindpakket-manifest-v1.json`, `eindverificatie-v1.json`): `codebasis-4cdb8ea43.tar` (5 MB), `codebasis-4cdb8ea43/` (volledige codesnapshot: `src/`, `config/`, SQL-migraties, `.coveragerc`), `cowork-uitwisseling/werkboom/` en `cowork-uitwisseling/werkboom-4cdb8ea43/` (codesnapshots van de werkboom, inclusief `.claude/rules/patterns.md` en `config/toetsregels/toetsregels_config.yaml` daarin), `cowork-uitwisseling/nalevering-4cdb8ea43/src/` en `cowork-uitwisseling/nalevering2-4cdb8ea43/src/` (nageleverde broncode). Reden: broncode en binaire artefacten horen niet in de documentatiemap; het archief blijft de bron. De manifesten die deze paden beschrijven (`werkboom-manifest-v1.json`, `werkboom-4cdb8ea43-manifest-v1.json`, `nalevering-manifest-v1.json`, `nalevering2-manifest-v1.json`) zijn wél opgenomen. `cowork-uitwisseling/nalevering3-4cdb8ea43/config/approval_gate.yaml` is als YAML-data wel opgenomen.

## Niet in de repository opgenomen: twaalf Python-bestanden

Los van het documentenbesluit hierboven gold al een technische grond: de pre-commit-hooks van deze repository draaien ruff (`--fix`, pre-commit-pin v0.16.5) en black op ieder gestaged Python-bestand, ook onder `docs/`. Elf onderzoeksscripts uit het dossier zouden daardoor bij het committen worden herschreven (black) of geblokkeerd (acht niet automatisch herstelbare ruff-bevindingen); één oudere codesnapshot (`cowork-uitwisseling/werkboom/src/services/export_service.py`) wordt door de pre-commit-ruff geblokkeerd op ISC004 (niet auto-fixbaar). Een herschreven bestand is geen bytegelijke kopie meer en een hook-bypass is niet toegestaan. Deze twaalf bestanden zijn daarom **niet** in deze map opgenomen; ze blijven onaangeroerd beschikbaar in het archief. Hun identiteit, zodat het archief later te verifiëren is:

| Bestand (relatief aan deze map) | SHA-256 | Bytes |
|---|---|---|
| `proef-actueel-v1.py` | a124fda7ece1c3fd90fe513baeeb72b23bbc486888bf32b196101996cce56851 | 2989 |
| `proef-v1.py` | df1f4670805d955ca38122a4353dd378c413bb0178cd44bde71d0a94001bf50b | 2966 |
| `proef-v2.py` | 6f39114f127d231da7c7be463790bb381efeb58af00b040e8739a0ac18637722 | 2989 |
| `reviewproef-v1.py` | a005c68ca0cf83ea97aa1db8b57818e863ffc71f5ce3b9924eb76b7f16f2b825 | 1715 |
| `verifieer-eindpakket-v1.py` | 68e13fa8699e66c092d2d374a8c4f8689ac0c18636c45bbf5a4bcf50b93ea319 | 3744 |
| `verifieer-eindpakket-v2.py` | dd020c04704fb3d1d0eaad562b558cf53a35a38cdafe0e89d40139a3cf211f62 | 4244 |
| `cowork-uitwisseling/codex-reviewpakket-v1/proef-actueel-v1.py` | a124fda7ece1c3fd90fe513baeeb72b23bbc486888bf32b196101996cce56851 | 2989 |
| `cowork-uitwisseling/codex-reviewpakket-v1/proef-v1.py` | df1f4670805d955ca38122a4353dd378c413bb0178cd44bde71d0a94001bf50b | 2966 |
| `cowork-uitwisseling/codex-reviewpakket-v1/proef-v2.py` | 6f39114f127d231da7c7be463790bb381efeb58af00b040e8739a0ac18637722 | 2989 |
| `cowork-uitwisseling/cowork-bewijs-v1/proef-ess04-v1.py` | 466346240ef2a1e5186ff1b286ed6b6e1c48fd849037b25286921d27ae02dabd | 3065 |
| `cowork-uitwisseling/reviewproef/reviewproef-v1.py` | a005c68ca0cf83ea97aa1db8b57818e863ffc71f5ce3b9924eb76b7f16f2b825 | 1715 |
| `cowork-uitwisseling/werkboom/src/services/export_service.py` | 58874058e090f3ae2c57bf0fc0b4cde02eab99c39877b63eb468705889625dee | 39248 |

De 229 overgenomen archiefdocumenten (onder meer de besluit-, bron- en casusregisters, `bronnen/`, `cowork-uitwisseling/` zonder codesnapshots, en `feitenbasis/`) staan hier bytegelijk. De proefuitkomsten van de scripts (`proefuitkomsten-v1.json`, `reviewproef-uitvoer-v1.json`, `verificatie-v1.json`, `eindverificatie-v1.json`) zijn wél opgenomen.

## Toegevoegd in deze map (geen archiefinhoud)

- `casusregister-v3.md` en `casusindex-v3.json` (DEF-767, W1-F2/F3): v2 plus recordvoorbeeldstatus en verwachte toestand na menselijke beoordeling (T2-2).
- Deze notitie.
