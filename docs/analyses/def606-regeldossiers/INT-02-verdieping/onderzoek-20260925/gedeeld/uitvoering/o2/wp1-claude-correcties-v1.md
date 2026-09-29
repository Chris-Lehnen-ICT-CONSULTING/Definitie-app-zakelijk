# DEF-835 WP1 — rapport Claude Code CLI, reviewcorrecties v1

26 september 2026 · uitvoerder: Claude Code CLI (Opus 5.5), sessie `177f1484-4e5c-482e-b431-450befdab835` · opdracht: `wp1-opdracht-claude-correcties-v1.md` · review: `wp1-codex-review-v1.md` (drie P2-bevindingen, alle "fix nu") · reviewerprobes: `bewijs/wp1-codex-probes-v1.py`.

**Status: correcties met volledig bewijs gereed.** Er is niets gecommit of gepusht. Er zijn geen modelcalls gedaan, er is geen netwerk gebruikt, de app is niet geactiveerd en er zijn geen dependencies toegevoegd. Er is niets verwijderd. Alleen drie van de vijf geaccordeerde WP1-bestanden zijn gewijzigd; de fixture en `__init__.py` zijn ongewijzigd. Er is geen nieuwe contractversie: dit zijn v1-correcties vóór activering.

Basis en herstelpunt: gecommitteerde HEAD `314b817aabcaaa9f5a00d74a7633155ec74b799c` op `feature/DEF-835-int02-o2`. Daar hadden de bestanden dezelfde hashes als bij mijn GREEN, onder meer `contract.py` `915d2537…`.

## Werkwijze en bewijs

1. De reviewerprobes zijn gereproduceerd op de ongewijzigde werkboom, met als enige aanpassing het ROOT-pad naar deze werkboom. Alle drie de bevindingen bleken te kloppen. Bij het nagaan van de decoderfouten bleek bovendien dat JSON van diepte 100000 een `RecursionError` geeft. Dat geldt voor zowel geldige als ongeldige JSON, en die fout lekt via dezelfde replayroute. Dat is als concreet relevante decoderfout meegenomen. De `[`×1100 uit de probe gaf al `error`.
2. De regressietests heb ik eerst toegevoegd en daarna gedraaid op de ongewijzigde contractimplementatie (`915d2537…`, "ongewijzigd t.o.v. HEAD: ja" in het log).
3. Daarna heb ik de drie punten gecorrigeerd en de volledige module, Ruff en Black gedraaid. De reviewerprobes zijn opnieuw uitgevoerd.

| Bewijs (`bewijs/`) | SHA-256 | Uitkomst |
|---|---|---|
| `wp1-correcties-rood-v1.log` | `3bc8ba8e604ac00d7c7c56e7e028f83037a435d7e03026886910aee499840eec` | **15 failed, 162 passed, exit 1**: 12× AssertionError, 2× RecursionError, 1× ValueError, precies op het beschreven gedrag. De 162 bestaande tests bleven groen. |
| `wp1-correcties-groen-v1.log` | `9eb66fa97428f0bf76b1ff3f279070e5eec3ea60f58fad0a1b058256446cc718` | **177 passed, exit 0** |
| `wp1-correcties-lint-v1.log` | `c85f8ee97ecb4046ec5567cd0824a280d5d6edfeb5576abe05efe001a5571636` | `ruff check` "All checks passed!", exit 0 · `black --check` "3 files would be left unchanged", exit 0 · `ruff format --check` "3 files already formatted", exit 0 |
| `wp1-correcties-probes-v1.log` | `18ae0a32e2ecf5ecaae2dab1beaa96eb758e79d4f9889f6b6e89f9bbace52d77` | Reviewerprobes op de gecorrigeerde code, exit 0: 8/8 lege gronden → `error/invalid_citation` (ook bij replay); citaten letterlijk behouden; 1 vraagteken; alle drie de replayvarianten → `error` |

Elk log vermeldt tijdstip, werkboom, branch, HEAD, commando en exitcode, met de SHA-256 van de beoordeelde bestanden. Het RED-log hoort bij testbestand `b0b53eb8…` en `contract.py` `915d2537…`. De GREEN-, lint- en probelogs horen bij de eindversie `contract.py` `4791cc06…`.

Commando's, telkens met `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`:
- `-m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra`
- `-m ruff check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py`
- `-m black --check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py`

## Per reviewpunt

### P2-1 — Een lege grond kan pass/fail dragen

- **Oorzaak.** `_grondbron` controleerde alleen of er een grond bestond: bedoeling niet `None`, bron-ID aanwezig, index binnen de lijst. Of de opgeloste tekst gevuld was, werd niet gecontroleerd. Zonder grondcitaat volgde er daarna geen controle meer. Een leeg begrip of een lege bron kon zo een pass (C112) of fail (C105) dragen.
- **Verandering** (`contract.py`, `_grondbron`). De opgeloste grondtekst wordt nu voor alle grondvelden aan dezelfde eis getoetst: `_citaat(_gevuld(tekst))`, ook zonder citaat. Een onbekende bedoeling valt daar ook onder, dus de losse `None`-controle is opgegaan in deze eis. Kern, bedoeling en contextwaarden kunnen al niet leeg zijn, omdat de invoervalidatie of de NE-regel dat afvangt. In de praktijk raakt de wijziging dus het begrip en de bronnen. De invoer zelf blijft toegestaan: een leeg begrip of een lege bron is geen invoerfout, maar kan geen oordeel dragen.
- **Nieuwe test.** `test_lege_grondtekst_draagt_geen_oordeel` heeft 8 parametrisaties: pass (C112) en fail (C105), grondveld begrip en bron, leeg `""` en alleen witruimte `" \t\n"`. Verwacht wordt telkens `error`, `invalid_citation`, melding E, `oordeel is None`, en `error` bij replay.
- **Rood → groen.** 8 failed (AssertionError: `('pass'|'fail', None…) != ('error', 'invalid_citation'…)`) → 8 passed.

### P2-2 — De meldingsopbouw verandert citaten en verdubbelt vragen

- **Oorzaak.** `_status_en_melding` gebruikte een reeks opeenvolgende `str.replace`-aanroepen. Een eerder ingevoegde waarde werd daardoor door de volgende `replace` opnieuw bewerkt. Een citaat met `{grond}` of `{handeling/afweging}` veranderde zo, en een reden met `{één vraag}` kreeg de vraag erin.
- **Verandering** (`contract.py`). De nieuwe functie `_vul(sjabloon, waarden)` vult de plaatshouders in één doorgang met `re.sub` over een alternatie van de exacte sleutels. De vervangfunctie geeft de waarde letterlijk terug. Alleen het oorspronkelijke sjabloon wordt gescand; ingevoegde waarden worden nooit opnieuw geïnterpreteerd. V, VN, de discretievariant, O en NA gebruiken nu `_vul`.
  - De letterlijke synthesesjablonen (`MELDING_*`) zijn ongewijzigd.
  - De NE-melding gebruikt nog één `replace` met de vaste interne waarden "kern", "context" of "kern en context". Daarin kan geen plaatshouder voorkomen, dus ik heb die bewust niet aangepast ("niets anders polijsten").
- **Nieuwe tests.** Alle verwachte eindstrings zijn letterlijk uitgeschreven in de test, zonder renderlogica:
  - `test_melding_laat_plaatshouders_in_citaat_ongemoeid[pass]`, met kern en citaat `Veld met {criterium/afleiding/kenmerk} en {grond}.`;
  - `test_melding_laat_plaatshouders_in_citaat_ongemoeid[fail-handeling]`, met `De medewerker vult {grond} en {handeling/afweging} in.`;
  - `test_melding_laat_plaatshouders_in_citaat_ongemoeid[fail-discretie]`, met `De autoriteit beslist over {grond} naar eigen {citaat}.`: VN-basistekst en discretievariant samen;
  - `test_melding_laat_plaatshouder_in_reden_ongemoeid`, met C107, reden `De betekenis van {één vraag} is onbekend.` en vraag `Wat betekent dit veld?`. Verwacht wordt de letterlijke O-melding met precies één vraagteken.
- **Rood → groen.** 4 failed. Voorbeeld uit het log: `+ rker vult de kern en een handeling in.` tegenover de verwachte `{grond} en {handeling/afweging}`. Daarna 4 passed.
- **Niet als regressietest opgenomen.** Plaatshouders in de grond-, vraag- of NA-waarde werden niet door de fout geraakt, omdat die waarde als laatste of enige werd ingevuld. Ze zouden in RED niet falen. Ik heb daarom geen tests toegevoegd die al groen waren. Na de correctie loopt elke waarde via dezelfde `_vul`.

### P2-3 — Ongeldige replay-JSON lekt een exception

- **Oorzaak.** `_herleidbaar` ving alleen `Int02ContractError` en `json.JSONDecodeError`. Bij het decoderen van `oordeel_json` (via `Beoordelingsdocument.oordeel`) kunnen ook een gewone `ValueError` optreden (bij een getal boven de cijferlimiet van `int`, 4300) en een `RecursionError` (bij nesting die te diep is voor de C-decoder). Die lekten uit `toets_actualiteit`.
- **Verandering** (`contract.py`, `_herleidbaar`). Het decoderen staat nu in een eigen, smal `try`-blok dat `(ValueError, RecursionError)` vangt en dan "niet herleidbaar" geeft, dus `Actualiteit("error", None, MELDING_E)`. `JSONDecodeError` is een subklasse van `ValueError`. De hervalidatie van de onderdelen en de herbeoordeling vangen elk alleen `Int02ContractError`. Er is geen catch-all en een fout wordt nooit als oordeel behandeld.
- **Nieuwe test.** `test_niet_decodeerbaar_oordeel_geeft_bij_replay_error`, met parametrisaties `getal-boven-cijferlimiet` (`"1"*5000`), `geldig-te-diep` (`"["*100000 + "]"*100000`) en `ongeldig-te-diep` (`"["*100000`). Het document komt via `dataclasses.replace`, dus gewone stringinhoud via de documentconstructor. Verwacht: `("error", None, E)`.
- **Rood → groen.** 3 failed (1× ValueError, 2× RecursionError) → 3 passed.

## Exacte wijzigingen in het bestaande testbestand

`git diff 314b817aa -- tests/unit/domain/test_def835_int02_contract.py` telt **110 regels erbij en 0 eraf**:
- `import dataclasses` erbij, bij de bestaande imports;
- een nieuwe sectie aan het eind: "Reviewcorrecties v1 (wp1-codex-review-v1.md, P2 1-3)", met de helper `_met_eigen_kern`, de tabel `LETTERLIJKE_MELDINGEN` en de vier testfuncties hierboven (15 testgevallen).

Er is geen bestaande test gewijzigd, verwijderd of afgezwakt. Totaal: 177 tests (162 + 15).

Semantisch effect op bestaand gedrag:
- Een grond die verwijst naar een leeg of alleen-witruimte begrip of een lege bron, geeft nu `error` in plaats van pass/fail.
- Meldingen blijven bytegelijk voor alle invoer zonder plaatshoudertekst. Dat bewijzen de ongewijzigde bestaande meldingstests.

## Contractdocument

`docs/architectuur/contracts/int02_assessment_contract_v1.md`, 14 regels gewijzigd:
- **Grondregel**: niet-lege grondtekst, ook zonder citaat, met de lijst van `invalid_citation`-gevallen.
- **Renderer**: één doorgang, en ingevoegde waarden worden nooit opnieuw geïnterpreteerd.
- **Replay**: een niet te decoderen `oordeel_json` (ongeldige JSON, cijferlimiet, te diep) geeft `error`, zonder catch-all.

Alle drie zijn gemarkeerd als "v1-correctie na review". De norm en de contractversie zijn ongewijzigd.

## Finale bestanden

| Bestand | Regels | SHA-256 | Diff t.o.v. `314b817aa` |
|---|---|---|---|
| `src/domain/int02/__init__.py` | 6 | `7c581491801ded0b0ab20e46ef54c8c477d930480dc93dc1fbe40256e8e961cb` | ongewijzigd |
| `src/domain/int02/contract.py` | 823 | `4791cc0692dcc12981c6529b9a7446cce5f440cec72f9fc767f972dc19c39896` | 93 regels in `git diff --stat` (toevoegingen + verwijderingen) |
| `tests/unit/domain/test_def835_int02_contract.py` | 1214 | `b0b53eb8b8910a800b7757c64c1476cbed69ca599619d85b8808d7dd1713e1f5` | +110 / −0 |
| `tests/fixtures/def835_int02_ontwerpgevallen.json` | 414 | `e18adb97279fa0fe75889df3541186c9341051c33348d1dd848526867239867d` | ongewijzigd |
| `docs/architectuur/contracts/int02_assessment_contract_v1.md` | 183 | `6e00cdef89c9d11680d80249ef3934ac53f08b39a1bbf4e7140b2eac18c32bf4` | 14 regels in `git diff --stat` |

Totaal volgens `git diff --stat HEAD`: 186 regels erbij, 31 eraf.

## Grenzen

- Alleen de WP1-testmodule is gedraaid, geen volledige suite. De module wordt buiten de eigen test nergens geïmporteerd.
- De eerdere bewijsgrenzen blijven gelden: geen persistentie of authenticiteit, geen semantische modelkwaliteit, geen app-route.
- De decodercorrectie betreft de replayroute. De property `Beoordelingsdocument.oordeel` zelf decodeert nog steeds zonder afvanging, want een document dat door `beoordeel` is gemaakt bevat altijd canonieke, decodeerbare JSON. Verdere hypothetische hardening valt buiten deze opdracht.

## Omgeving

- `.claude/hooks/check-silent-exceptions.py` is nog steeds de lokale symlink. **Niet committen.**
- De probe-adaptatie `/tmp/def835_probes_lokaal.py` staat buiten de repository; de inhoud is `bewijs/wp1-codex-probes-v1.py` met alleen ROOT aangepast (zie de kop van het probelog).
- Bestaande bewijsrapporten zijn niet gewijzigd; alle bewijsbestanden zijn nieuw.

**Correcties met volledig bewijs gereed; wacht op coördinator en gerichte Codex-controle.**
