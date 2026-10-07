# INT-02 O2 — offline preflight kwalificatie (v1)

30 september 2026. Branch `feature/DEF-835-int02-o2`. Alleen synthetische gevallen; geen productiedata, geen live kwalificatiecalls. Actions en O2 blijven uit.

## Bron en freeze

- Selectiebesluit: `../labelronde-v1/besluit-chris-selectie-split-v1.md`, SHA-256 `6c80ae8b1ed354ea5d2a6039310c84f53eba0e41184c9b596c39609e903f7465`.
- Ontwikkelset: `ontwikkeling-v1.json`, SHA-256 `51905799fb18731cbbb959acaef13accf17c3a338260e524ab5d8250f50d4b83`.
- Hold-outset: `holdout-v1.json`, SHA-256 `0378ccf3a7ddf88e11ccebdba3b3118c26cce536801c06abf954a21772fc1fd3`.
- Bron- en adjudicatieregister: `bewijsmanifest-v1.json`, SHA-256 `374f8e9113f9a9f5b9ad3fadd5b1c854b0da9b52a58eef5ac7c12ecf1a973d9d`.
- Runnergevallen (3 regressie + 24 ontwikkeling + 16 hold-out): `kwalificatie-gevallen-v1.json`, SHA-256 `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`.
- Pending manifest: `kwalificatie-manifest-v1.json`, SHA-256 `d67659fa7fe06801b4a6c744269d06405a3eab1b3c434622605e5bd18e4bdb29`; identiteits-SHA-256 `ba72109ea0b89254ee70b2d4aaf008fcd2ac5dcf8f1a8814de9db256851a027c`.
- Voorbereide verzoeken: `kwalificatie-payloads-v1.json`, SHA-256 `46d0d1062487ea406ab94f85537540b8f91ba3ab4b53a855c245bd067b735e06`. De 43 verzoeken hebben geen labelveld. Dit bestand bevat hold-outinvoer en wordt daarom niet gedeeld met promptontwikkelaars of implementatoren.

Alle 40 gekozen gevallen hebben A- en B-beoordelingsbronnen met exact controleerbare passages en grondcitaten. Waar hun familie-indeling verschilde, volgt de freeze Chris' latere besluit. Voor G042/G045/G047 is de geaccepteerde onzekere lezing van B gebruikt; G030 gebruikt de herbeoordeling na broncorrectie. De gelabelde set telt 20 `pass`, 10 `fail`, 10 `review_required`; hold-out telt 8/4/4.

## Offline verificatie

De runner produceerde het pending manifest zonder netwerk- of sleutelgebruik. `tests/unit/validation/test_def835_int02_modelproef.py`: **177 passed in 25.70s**. De live-proefmap `kwalificatieproef-v1` bestaat niet. In de routeridentiteit staat `anthropic` / `claude-opus-5`, prompt `def835-int02-prompt/1`, maximaal 43 inferenties en 43 tokenmetingen, 16.000 input- en 6.000 outputtokens per call, 120 seconden per call, 6.000 seconden totaal en US$12 cumulatief. Routerprijzen: US$5 per miljoen input- en US$25 per miljoen outputtokens. Op 30 september 2026 zijn model en basisprijzen opnieuw gecontroleerd tegen de officiële Anthropic-modelpagina: https://platform.claude.com/docs/en/models/opus-5/overview .

## Nog vereiste binding

`scripts/analysis/def835_int02_modelproef.py::_controleer_kwalificatieakkoord` vereist een **apart akkoordbestand** met de exacte SHA-256 van het pending manifest en van het gevallenmanifest. Het algemene proefmandaat in `vervolg-akkoord-v1.md` (28 september) is verleend voordat deze hashes bestonden; het selectieakkoord van 30 september bindt de gevalinhoud en split, maar noemt het pending manifest nog niet. Daarom nog geen live verzending. Na Chris' expliciete bevestiging worden alleen die exacte hashes in een nieuw akkoordbestand vastgelegd en start eerst de regressiefase. De runner voert één fase per aanroep uit en stopt bij de vastgelegde technische of inhoudelijke foutgrens.

Inhoudelijke modelkwaliteit, geldige passagegrond en statusgrenzen zijn nog niet bewezen. De freeze is een geaccepteerde synthetische testset, geen praktijksteekproef of statistische garantie.
