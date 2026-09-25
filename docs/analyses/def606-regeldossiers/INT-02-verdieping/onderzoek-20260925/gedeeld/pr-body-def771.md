## Wat

Onderzoeksdossier **INT-02 — Geen beslisregel** (DEF-771) onder `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/`: 161 bestanden, alleen documentatie en bewijs. **Geen code-, norm- of skillwijziging.**

- Vier onafhankelijke onderzoekslijnen: A (Claude Code CLI), B (Codex CLI), C (Codex in de ChatGPT-app), coördinator (Cowork); wederzijdse reviews, verwerkingen, synthesecontroles B (v1/v2) en C (v1/v2): **A + B + C inhoudelijk afgerond**.
- Publicatieversies: `gedeeld/gezamenlijke-synthese-v5.md`, `besluitnotitie-chris-v5.md`, `gezamenlijk-casusregister-v5.md` (76 casus-ID's); eerdere versies bewaard.
- **Besluiten Chris 25-09-2026** in `gedeeld/besluiten-chris-v1.md`: K1 breed · K2 O1 nu, O2 inplannen · K2b S1 · K3 één versiegebonden contract · K4 geen zelfstandige poort (→ DEF-831, alle toetsregels) · K5 geen herstel; automatisch herstel alleen voor vormregels (→ DEF-832).
- Bewijs: proefscripts, uitkomsten, logs en manifests met SHA-256; `gedeeld/processtatus.md` en `gedeeld/ontvangstlog.txt`.
- `gedeeld/uitvoeringsopdracht-codex-coordinator-v1.md`: opdracht voor de afzonderlijke uitvoering (Codex coördineert, Claude Code CLI implementeert, verse Codex CLI reviewt de diff). **Niet gestart.**

## Waarom een aparte docs-branch

De hoofdwerkboom staat op de INT-03-branch van een andere sessie; dit dossier is in een eigen worktree vanaf `origin/main` gecommit (`gedeeld/git-publicatie-def771.sh`).

## Hooks

`black` en `ruff` zijn bij commit en push overgeslagen (`SKIP=black,ruff`), omdat de bewijsscripts byte-gelijk moeten blijven aan de SHA-256-manifests van de onderzoekers; alle overige hooks (gitleaks, bronquarantaine DEF-666, root-allowlist DEF-685, smoke tests, pip-audit) zijn gedraaid en geslaagd. Aanvullend `gitleaks git origin/main..HEAD`: no leaks found.

## Linear

DEF-771 (oplevercomment 25-09-2026), DEF-831, DEF-832.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01J97BQmzDZQwpmjJXXrccdi
