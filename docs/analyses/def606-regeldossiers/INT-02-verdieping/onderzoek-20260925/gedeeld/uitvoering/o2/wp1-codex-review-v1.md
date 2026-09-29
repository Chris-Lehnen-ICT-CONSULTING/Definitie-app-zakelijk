**Oordeel: WP1 vereist concrete correcties.** Drie bevestigde bevindingen, alle **P2 — fix vóór WP1-acceptatie**.

1. **Een lege grond kan pass/fail dragen.**  
   [contract.py:488](/private/tmp/def835-wp1-review-20260926/src/domain/int02/contract.py:488), regels 488–513: `_grondbron` controleert aanwezigheid, maar geen niet-lege tekst. Zonder grondcitaat volgt geen verdere controle.

   **Reproductie:** neem fixture C112, zet `invoer.begrip=""` en vervang de grond door:
   ```json
   {"field":"begrip","ref":null,"quote":null,"start":null,"end":null}
   ```
   Resultaat: `pass`, ook bij replay. Met C105 ontstaat `fail`. Hetzelfde gebeurt bij een bestaande bron `{"id":"B1","tekst":""}` en grondverwijzing naar B1. Alleen witruimte wordt eveneens geaccepteerd: acht bevestigde varianten.

   **Gevolg:** lege bewijsvoering draagt een inhoudelijk oordeel, in strijd met plan-v1, ontwerpvoorstel punt 6. **Correctie:** vereis niet-lege opgeloste grondtekst, ook zonder citaat; wijs deze uitvoer af als `error/invalid_citation`. Voeg regressietests voor beide verdicts en grondtypen toe.

2. **Meldingsopbouw verandert gevalideerde citaten en verdubbelt vragen.**  
   [contract.py:578](/private/tmp/def835-wp1-review-20260926/src/domain/int02/contract.py:578), regels 578–600: opeenvolgende `replace`-aanroepen verwerken ook eerder ingevoegde tekst.

   **Reproductie:** kern en volledig passagecitaat `De medewerker vult {grond} in.`, correcte offsets en grond `kern` zonder citaat. De fail-melding citeert vervolgens **`De medewerker vult de kern in.`** Dezelfde fout treedt bij pass op. Bij C107 met `reason="De betekenis van {één vraag} is onbekend."` en `question="Wat betekent dit veld?"` verschijnt de vraag tweemaal.

   **Gevolg:** de melding bevat een ander citaat dan de gecontroleerde invoer; één gevalideerde vraag verschijnt dubbel. **Correctie:** vul uitsluitend placeholders in het oorspronkelijke sjabloon in, zonder vervanging binnen ingevoegde waarden. Test letterlijke placeholdertekst; de huidige meldingstests herhalen dezelfde vervangingsketen.

3. **Ongeldige replay-JSON kan een onverwachte exception lekken.**  
   [contract.py:753](/private/tmp/def835-wp1-review-20260926/src/domain/int02/contract.py:753), regels 753–757: de foutafhandeling vangt niet alle relevante JSON-decoderfouten.

   **Reproductie:** maak een geldig C112-document en roep aan:
   ```python
   toets_actualiteit(replace(doc, oordeel_json="1" * 5000), doc.invoer, cfg)
   ```
   Waargenomen trace: `toets_actualiteit:783 → _herleidbaar:754 → oordeel:636 → json.loads → ValueError: Exceeds the limit (4300 digits)`. Er komt geen `Actualiteit(status="error")`.

   **Gevolg:** niet-herleidbare replay breekt de aanroep af. **Correctie:** handel deze decoderfout af binnen de replayvalidatie en voeg een regressietest toe. Dit betreft gewone stringinhoud via de documentconstructor, geen claim over willekeurige objectmanipulatie.

Beoordeeld:  
Base `84bdc8c1b060ab50a1bd1428aed778bb2ed6007f`  
Head `314b817aabcaaa9f5a00d74a7633155ec74b799c`

Eigen offline test: **162 passed in 0.70s**, exit 0:
```sh
PYTHONDONTWRITEBYTECODE=1 /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra -p no:cacheprovider
```

De [tijdelijke probes](/private/tmp/def835-review-probes-20260926-v1.py) zijn uitgevoerd met:
```sh
PYTHONDONTWRITEBYTECODE=1 /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python /private/tmp/def835-review-probes-20260926-v1.py
```

Daarnaast gecontroleerd: gesloten uitvoer, citaatposities, statuspaden, scoreloosheid, metadata, bindingswijzigingen, historische afwijzing en exacte snapshots. De hashes van het groene test-/lintbewijs passen bij deze bestanden. De bestaande **282 passed** is gelezen bewijs, geen eigen heruitvoering. Geen volledige suite, modelkwaliteit, opslag of appintegratie beoordeeld.

Werkboom bleef schoon; geen delegatie of netwerk gebruikt. Geen delegatietools zichtbaar, maar wel MCP-tools: volledige MCP-uitschakeling en `agents.enabled=false` zijn daarmee niet bevestigd. Modelcontext noemt GPT-6; exacte modelalias/redeneerinstelling niet zichtbaar of gewijzigd.