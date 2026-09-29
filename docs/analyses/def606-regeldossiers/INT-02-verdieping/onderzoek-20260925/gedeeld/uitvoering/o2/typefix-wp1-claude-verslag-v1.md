# DEF-835 WP1 typefix — verslag Claude Code CLI v1

28-09-2026 · werkboom `DEF-835-int02-o2`, HEAD `d769276041e619103ace7bc66e65419d480dae99` · alleen `src/domain/int02/contract.py` gewijzigd. Geen gitmutaties, geen livecalls, geen verwijderingen. De overige werkboomwijzigingen zijn niet aangeraakt.

**Herstelkopieën.** Beide bestanden stonden al in `bewijs/typefix-vooraf-v1/` en zijn bytegelijk aan de uitgangsversie:
- `contract.py` `4791cc06…`;
- `int02_assessment_service.py` `99f1381e…`.

**Rood.** `mypy src/ --check-untyped-defs --no-incremental` gaf 13 fouten, exit 1. Het log `typefix-wp1-mypy-voor-v1.log` herbevestigt de baseline van F23.

**Correctie** (+11/−3, zie `typefix-wp1-diff-v1.patch`):
1. **Regel 507 (`no-any-return`).** `_grondbron` geeft nu `cast(str, tekst)` terug. De bestaande runtimecontrole `_citaat(_gevuld(tekst))` vlak daarvoor eist `isinstance(tekst, str)` en werpt anders `_AfwijzingError(invalid_citation)`. Die controle staat er nog en heeft een verwijzend commentaar gekregen. `typing` importeert nu `cast`.
2. **Regel 713 plus de vijf afgeleide Any-returns (732/736/738/747/749).** De geneste `document` is volledig geannoteerd:
   - `status`/`melding`: `str`;
   - `reden`/`fout`/`vraag`: `str | None`;
   - `uitvoer`: `dict[str, Any] | None`;
   - returntype `Beoordelingsdocument`.

Ongewijzigd: gedrag, validatie, foutklassen en -berichten, statusmapping en het publieke contract. Er is geen `Any`, `ignore` of `noqa` toegevoegd.

**Groen:**
- `mypy` gaf **6 fouten in 1 bestand**, exit 1. Het zijn uitsluitend de verwachte WP2-fouten in `int02_assessment_service.py` (regels 245–248, 765 en 829); er is geen `contract.py`-fout meer. Log: `typefix-wp1-mypy-na-v1.log`.
- `pytest tests/unit/domain/test_def835_int02_contract.py`: 177 passed, exit 0.
- `ruff check` op het bestand: "All checks passed!", exit 0.
- `black --check` op het bestand: "1 file would be left unchanged", exit 0.

Log: `typefix-wp1-tests-lint-v1.log`.

**Hashes (SHA-256):**

| | |
|---|---|
| `contract.py` voor | `4791cc0692dcc12981c6529b9a7446cce5f440cec72f9fc767f972dc19c39896` |
| `contract.py` na | `6dcae57bc60d1edec09d49fa35d21d135cf0dd43e587ef7e8ba60dac22f16ca8` |
| `typefix-wp1-mypy-voor-v1.log` | `65bed3b6…` |
| `typefix-wp1-mypy-na-v1.log` | `3d82c564…` |
| `typefix-wp1-tests-lint-v1.log` | `3a9c9536…` |
| `typefix-wp1-diff-v1.patch` | `58567b72…` |

**Niet uitgevoerd:** de volledige suite en WP2 (de coördinator organiseert WP2).
