Title: Toetsregels 45x opnieuw geladen – herhaaldelijke load-calls

Status: Open
Severity: Medium (prestaties), kan cumuleren met BUG-010
Componenten: toetsregels.loader, services.prompts.modules.*

Beschrijving
- In de logs verschijnt meerdere keren achter elkaar: "Geladen 45 toetsregels uit individuele bestanden".
- Dit duidt op herhaaldelijk laden van dezelfde regels bij initialisatie van verschillende prompt-modules of services.

Reproductie
1) Start UI en trigger generatie.
2) Logs tonen meerdere, identieke loader-meldingen met korte tussenpozen.

Analyse/Root cause hypothese
- Elke module of component roept de loader aan i.p.v. gedeelde cache/loader‐resultaat te hergebruiken.
- Mogelijke import-cycli of init-paden waarbij modules de loader tijdens init uitvoeren.

Impact
- Overbodige I/O en CPU-tijd; vertraagt start/generatie en vervuilt logs.

Acceptatiecriteria
- Toetsregels worden maximaal één keer geladen per sessie (of met expliciete invalidatie).
- Modules gebruiken een gedeelde cache of krijgen regels geïnjecteerd.

Aanpakvoorstel
- Voeg memoization/caching toe in loader (bv. module‐global cache met versiestempel/mtime).
- Verplaats laden naar een hoger niveau (bv. ServiceContainer) en injecteer naar modules.
- Voeg defensieve "already loaded" guard toe in module-inits.

Referenties
- `src/toetsregels/loader.py` en `src/toetsregels/modular_loader.py`
- `src/services/prompts/modules/*`

