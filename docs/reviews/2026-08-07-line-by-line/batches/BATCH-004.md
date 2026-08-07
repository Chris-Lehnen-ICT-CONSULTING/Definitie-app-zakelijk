# BATCH-004

- Status: `pending`
- Reviewgroep: `1` — Entrypoints, build, dependencies en configuratie
- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Membership-SHA256: `560f8f15884aa886a5a697b6f35bb941db33d80f768afa205eb9ac93cdebeb38`
- Bestanden: `26`
- Fysieke regels: `5226`
- Python-symbolen: `0`
- Reviewer: ``
- Onafhankelijke verifier: ``

## Scope

| Pad | path_b64 | Regelbereik | Symbolen | Object-ID |
|---|---|---:|---:|---|
| `.gitleaks.toml` | `LmdpdGxlYWtzLnRvbWw=` | `1-141` | 0 | `663cc49c433f63aa696df07b087bd6f49b9540a9` |
| `.pre-commit-config.yaml` | `LnByZS1jb21taXQtY29uZmlnLnlhbWw=` | `1-124` | 0 | `cfe2180ed55fb274285cbd5b8700e12c97a3b0b0` |
| `.trunk/configs/.markdownlint.yaml` | `LnRydW5rL2NvbmZpZ3MvLm1hcmtkb3dubGludC55YW1s` | `1-2` | 0 | `b40ee9d7a7aa5edd0a22f9beb16d33c8b147269c` |
| `.trunk/configs/.yamllint.yaml` | `LnRydW5rL2NvbmZpZ3MvLnlhbWxsaW50LnlhbWw=` | `1-7` | 0 | `184e251f8deb169e6cc659d3a43ff4cac1c54d68` |
| `.trunk/configs/ruff.toml` | `LnRydW5rL2NvbmZpZ3MvcnVmZi50b21s` | `1-6` | 0 | `41de1747803c35cf2b0f541aa430ded3a54ac872` |
| `.trunk/trunk.yaml` | `LnRydW5rL3RydW5rLnlhbWw=` | `1-53` | 0 | `1722ea4682d4756904e1c6fbf59d49b76e27aa05` |
| `config/.coveragerc` | `Y29uZmlnLy5jb3ZlcmFnZXJj` | `1-55` | 0 | `9d3ce94db3944136c8eff3240c98dd248de58936` |
| `config/approval_gate.yaml` | `Y29uZmlnL2FwcHJvdmFsX2dhdGUueWFtbA==` | `1-26` | 0 | `6272be07ff78729866dcd1015d805647aabe8cd8` |
| `config/cache_config.yaml` | `Y29uZmlnL2NhY2hlX2NvbmZpZy55YW1s` | `1-256` | 0 | `251ad07ee53a9bb13cee10229b6bb5d5d3c751c0` |
| `config/classification/term_patterns.yaml` | `Y29uZmlnL2NsYXNzaWZpY2F0aW9uL3Rlcm1fcGF0dGVybnMueWFtbA==` | `1-115` | 0 | `67818c2334ad2461be190977be96150feff55a49` |
| `config/config.yaml` | `Y29uZmlnL2NvbmZpZy55YW1s` | `1-210` | 0 | `a601df31f7a73a0f2118736a384f0449e8c1f08c` |
| `config/juridische_keywords.yaml` | `Y29uZmlnL2p1cmlkaXNjaGVfa2V5d29yZHMueWFtbA==` | `1-75` | 0 | `7b0bd8a2aa625ab9888fea6090b4cfe3d81a39b4` |
| `config/juridische_synoniemen.yaml` | `Y29uZmlnL2p1cmlkaXNjaGVfc3lub25pZW1lbi55YW1s` | `1-361` | 0 | `48866318aaa1c6dd6a815ae2ef6c1a44a408ac7b` |
| `config/logging_config.yaml` | `Y29uZmlnL2xvZ2dpbmdfY29uZmlnLnlhbWw=` | `1-321` | 0 | `6d0933eecba1df0dec3c4a7ea619ecc2def89d7b` |
| `config/logging_structured.yaml` | `Y29uZmlnL2xvZ2dpbmdfc3RydWN0dXJlZC55YW1s` | `1-85` | 0 | `41062d250ebb78e1f33c47a4c84a086a59f78bac` |
| `config/monitoring.yaml` | `Y29uZmlnL21vbml0b3JpbmcueWFtbA==` | `1-11` | 0 | `6b1d52ce3d9b427e19a27a127928b245865c29ab` |
| `config/ontology/category_patterns.yaml` | `Y29uZmlnL29udG9sb2d5L2NhdGVnb3J5X3BhdHRlcm5zLnlhbWw=` | `1-221` | 0 | `825634511691a89cb8763f5308812695650f9229` |
| `config/synonym_config.yaml` | `Y29uZmlnL3N5bm9ueW1fY29uZmlnLnlhbWw=` | `1-86` | 0 | `bca7e74fa9dff7e7340a30655b2a6a6f463d6bbd` |
| `config/toetsregels/toetsregels_config.yaml` | `Y29uZmlnL3RvZXRzcmVnZWxzL3RvZXRzcmVnZWxzX2NvbmZpZy55YW1s` | `1-244` | 0 | `40dd16aedab4b1b7007e1c8784f0a4974785def5` |
| `config/ufo_rules.yaml` | `Y29uZmlnL3Vmb19ydWxlcy55YW1s` | `1-1802` | 0 | `1847a906c4bad882bec2e815a8560db3d461bb32` |
| `config/ufo_rules_v5.yaml` | `Y29uZmlnL3Vmb19ydWxlc192NS55YW1s` | `1-380` | 0 | `90ea16ac2de89ca9f6097ab8fd1a1f23b224b5ef` |
| `config/validation/rule_reasoning_config.yaml` | `Y29uZmlnL3ZhbGlkYXRpb24vcnVsZV9yZWFzb25pbmdfY29uZmlnLnlhbWw=` | `1-151` | 0 | `b69aa1daed59b0974af2c78fbc8ed8d97892347b` |
| `config/web_lookup_defaults.yaml` | `Y29uZmlnL3dlYl9sb29rdXBfZGVmYXVsdHMueWFtbA==` | `1-161` | 0 | `3c4de6d65d2f739074991dcae6254dddb0054bda` |
| `pyproject.toml` | `cHlwcm9qZWN0LnRvbWw=` | `1-233` | 0 | `6587fb7be7e3062a3f3faf3a2030128f0ec2db07` |
| `pytest.ini` | `cHl0ZXN0LmluaQ==` | `1-60` | 0 | `a025c5965bede33dee5942894641c74304a145dc` |
| `requirements-dev.in` | `cmVxdWlyZW1lbnRzLWRldi5pbg==` | `1-40` | 0 | `117ff514e49592cceec9d33c6f931e8dbb7ee765` |

## Verplichte reviewchecklist

- [ ] Iedere toegewezen regel rechtstreeks uit het immutable object-ID gelezen.
- [ ] Ieder toegewezen symbool en iedere functie line-by-line beoordeeld.
- [ ] Callers, afhankelijkheden, tests en foutpaden gecontroleerd.
- [ ] Codekwaliteit en architectuur beoordeeld.
- [ ] Bugs, security en foutafhandeling beoordeeld.
- [ ] Functionaliteit en relevante tests beoordeeld.
- [ ] UI/UX, toegankelijkheid en responsive gedrag beoordeeld indien van toepassing.
- [ ] Findings bevatten prioriteit, bewijs, reproductie en oplossing.
- [ ] Bewezen, vermoed en niet-getest expliciet onderscheiden.
- [ ] Onafhankelijke tweede reviewer heeft scope en findings geverifieerd.

## Bevindingen

Nog niet geregistreerd.

## Resultaat

Nog niet uitgevoerd.
