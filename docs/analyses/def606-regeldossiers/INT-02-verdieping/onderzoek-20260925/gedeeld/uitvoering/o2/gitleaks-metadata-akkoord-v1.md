# DEF-835 — akkoord exacte metadata-uitzondering

28 september 2026. Chris antwoordde in deze chat op het concrete voorstel `gitleaks-metadata-uitzondering-voorstel-v1.md`:

> Ja, alleen deze exacte uitzondering met tests

Mandaat: uitsluitend de twee exacte manifestpaden EN volledige hashregel onder generic-api-key, met positieve en negatieve regressietests; `.gitleaks.toml` en nieuw `scripts/ci/test_secret_scan_def835_metadata.py`. Geen bredere scanuitzondering, scopeverkleining of uitschakeling. Normale volledige staged-gate blijft verplicht. Uitvoering volgt na WP5a, via Claude Code CLI en onafhankelijke Codex CLI-review.
