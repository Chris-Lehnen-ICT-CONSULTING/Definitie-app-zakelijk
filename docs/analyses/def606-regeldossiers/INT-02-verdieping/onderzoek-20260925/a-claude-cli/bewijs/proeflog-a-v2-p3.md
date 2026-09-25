# Proeflog P3 — onderzoekslijn A, review op B (25-09-2026)

Aanleiding: de P1 van B filtert violations op `code == "INT-02"` (`b-codex-cli/bewijs/proeven-b-v1.py:35`), waardoor het buurregeleffect van `indien` buiten beeld blijft. A-P1 (`proeflog-a-v1.md`) toonde een INT-10-fail op elke `indien`-tekst, maar legde niet de melding en de ernst vast. P3 legt die vast.

- Verwachting vooraf: in de docstring van [`proef-p3-int10-melding.py`](proef-p3-int10-melding.py), geschreven vóór uitvoering.
- Commando (repo-root): `PYTHONPATH=src .venv/bin/python docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/a-claude-cli/bewijs/proef-p3-int10-melding.py`
- Commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Offline, synthetisch, geen modelcalls. Context `{"organisatorische_context": ["Synthetische wiskundeles"]}` (K-9-conform).
- Exit 0 (de Bash-tool meldde geen fout). Uitkomst: [`p3-uitkomsten.json`](p3-uitkomsten.json).

## Waarneming

| Casus | INT-02 | INT-10 | INT-01 |
|---|---|---|---|
| C04 "Getal dat even is indien het zonder rest door twee deelbaar is." | review_required | **fail** · `severity: "error"`, `severity_level: "critical"` · message "Verboden patroon gedetecteerd: \bindien\b" · suggestion "Herschrijf de zin zodat de gedetecteerde patronen niet voorkomen." | fail · `warning`/`low` · zelfde message en suggestion |
| C05 "Geheel getal dat zonder rest door twee deelbaar is." | review_required | pass | pass |

## Toetsing aan de verwachting

- **Bevestigd:** INT-10 faalt op C04 en niet op C05, en de melding is generiek en patroongebaseerd. Ze zegt niets over achtergrondkennis.
- **Gedeeltelijk anders:** de ernst is `severity_level: "critical"`. De gate leest echter het veld `severity` (`definition_workflow_service.py:741-742`), en `issues_uit_validatieresultaat` slaat `severity` op, niet `severity_level` (`src/database/models.py:150-153`). Dat veld is hier `"error"`, niet `"critical"`. De regel "Kritieke issues aanwezig" wordt dus naar codelezing niet geraakt. Dat is niet als gateproef uitgevoerd.
- **Aanvullende codelezing:**
  - `definition_orchestrator_v2.py:1263-1275` en `1976-1999` sturen gewone violations als "herstelbare overtredingen" naar de enhancement-service, zodra die actief is.
  - In de container is `enhancement_service=None` ("Not implemented yet", `container.py:384`).
  - Het effect is dus **latent**: bij activering (DEF-638-richting) zou een INT-10/INT-01-violation op `indien` een herschrijving kunnen aansturen met het advies het patroon te verwijderen. Die herschrijving zou een criterium kunnen laten vallen.
  - Niet uitgevoerd.
