# DEF-770 restherstel — resultaat Claude-uitvoerder (v4, LOW-assertie)

25 september 2026. Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc`. Dit verwerkt de LOW-bevinding uit `logs/def770-restherstel/astra-review-v3.md` (volledig gelezen).

Niet gedaan: agents of reviewers gestart, commits, pushes of API-calls, de nieuwe proefset gelezen.
Alleen gewijzigd: `tests/unit/validation/test_def770_restherstel_zinsgrenzen.py`. Geen andere code, tests of skills.

## Wijziging

De test vergeleek de normatieve referentie met `sentence_status`, het historische automatische label. Nu wordt het normatieve veld gecontroleerd; het historische label blijft als aparte assertie staan. Beide waarden zijn in de verzegelde `t24-adjudicatie-v1.json` `pass` (gelezen, niet gewijzigd).

Herstelkopie: `logs/def770-restherstel/herstelkopie-v4/app/tests/unit/validation/test_def770_restherstel_zinsgrenzen.py` (GELIJK vóór de edit).

Exacte diff:

```diff
@@ -154,7 +154,10 @@
     normatieve referentie blijft pass en is hier zichtbaar, niet aangepast."""
     adjudicatie = json.loads(T24_ADJUDICATIE.read_text(encoding="utf-8"))
     [geval] = [c for c in adjudicatie["cases"] if c["id"] == "T20"]
-    assert geval["sentence_status"] == REFERENTIE_NORMATIEF["T20"]
+    # Normatieve as (astra-review-v3): de referentie blijft pass.
+    assert geval["normative_sentence_status"] == REFERENTIE_NORMATIEF["T20"]
+    # Historisch automatisch label van die proef, apart en onveranderd.
+    assert geval["sentence_status"] == "pass"
     detail = regeluitkomst(segmenteer(A_T20))
     delen = {p["id"]: p["status"] for p in detail["parts"]}
     assert detail["status"] == BESLUIT_AUTOMATISCH["T20"]
```

## Hash

- SHA256: `2be2d1678bb46c107eb6cc83961007b037350bbd14fcc8cbe128cd5789bae2e3`
- git blob: `ec3eb551fce06e0b28100460a61cfa08cc91241d`

## Test en lint (alleen dit bestand)

| Stap | Log | Uitkomst |
|---|---|---|
| pytest | `v4-test.log` en `.xml` | 47 tests, 0 failures, 0 skips/xfails, **exit=0** |
| Black `--check` | `v4-black.log` | ongewijzigd, exit=0 |
| Ruff 0.16.5 (gepind) | `v4-ruff-0165.log` | All checks passed, exit=0 |

Geen volledige suite gedraaid.
