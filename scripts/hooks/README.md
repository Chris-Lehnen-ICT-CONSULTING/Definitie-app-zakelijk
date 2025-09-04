## Documentation Hooks

Deze map bevat pre-commit hooks die documentatie bewaken:

- `check-doc-location.py`
  - Controleert of bestanden in toegestane mappen staan (whitelist per extensie).
  - Whitelist: `validation-status.json` mag in de root staan.

- `check-doc-links.py`
  - Valideert interne Markdown-links (binnen `docs/`).
  - Slaat externe links en `docs/archief` over.

- `check-doc-metadata.py`
  - Leest frontmatter (`canonical`, `status`, `last_verified`).
  - Waarschuwt wanneer `last_verified` ouder is dan 90 dagen (faalt commit niet).

### Lokale installatie

1) Pre-commit installeren:

```bash
pip install pre-commit
pre-commit install
```

2) Hooks draaien op alle bestanden:

```bash
pre-commit run --all-files
```

3) Specifieke hook tijdelijk overslaan (alleen indien noodzakelijk):

```bash
SKIP=check-doc-location pre-commit run --all-files
```

### CI

Deze hooks draaien lokaal via pre-commit. Integratie in GitHub Actions kan later worden toegevoegd voor server‑side bewaking.
