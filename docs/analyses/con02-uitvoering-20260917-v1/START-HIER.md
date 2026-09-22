# CON-02 — eerste actieve acceptatieronde, 17 september 2026

**Uitkomst: nog geen acceptatie.** De ronde is gestart en heeft een concrete blokkerende contractafwijking gevonden: [DEF-806](https://linear.app/definitie-app/issue/DEF-806). De app accepteert verwijskwaliteit zonder vereiste hyperlink en zonder deskundige uitzondering. Een echte generatie, editorreadback en onafhankelijke lokale replay bevestigen dat gedrag.

## Leesvolgorde

1. `browser-generatie-readback-v1.md`: echte UI-probe met bronaanvoer en opgeslagen oordeel.
2. `codex-bewijsreview-v1.md`: onafhankelijke bevestiging en minimale herstelcriteria.
3. `casusbatch-v1.md` plus **`appuitkomsten-en-reviewgrenzen-v1.md` en `codex-runreview-v1.md`**: vijf afgeronde beoordelingen, één timeout en de beperktere dekking van de overige casussen. De aanvullingen begrenzen de ruwe plantitels; P10 is synthetische aanvoer, P07 geen geïsoleerde bronmutatie en de teller telt serviceaanroepen.
4. `deelchecks-en-scorebeleid-v1.md`: invoer, beoordelaar, automatiseringsgrens en scorebeleid per onderdeel.
5. `generatie-record4-v1.json` en `cli-bewijs/runmatrix-ruw.json`: onderliggend bewijs.

## Wat blijft open

- DEF-806 herstellen en met dezelfde input plus een nieuwe echte app-probe hertoetsen.
- Volledige uitvoering van vereiste ketenstappen voor de 31 casussen, inclusief live retrieval waar voorgeschreven. P16 gaf een technische timeout; geen semantische conclusie.
- Menselijke acceptatie: P01 is aan Chris voorgelegd, antwoord nog niet ontvangen. Daarna de overige voorgestelde startcasussen en verschilpunten P14/P24/P30. Alle deskundigenvelden in het oude pakket zijn onaangeroerd.
- [DEF-804](https://linear.app/definitie-app/issue/DEF-804) (OTH-editorcrash) en [DEF-805](https://linear.app/definitie-app/issue/DEF-805) (reviewdatumsortering) zijn apart getrieerd; beide hebben een workaround voor dit onderzoek.
- DEF-743 blijft In Progress; PR455 blijft draft. De code in de eerdere implementatie-PR454 is al gemerged; deze nieuwe uitvoeringsbevindingen zijn geen bewijs dat de inhoudelijke acceptatie toen al klaar was.

## Uitvoeringsidentiteit

- Geteste app: actuele maincommit `d17ea9c30915452914e450be315620e314c03468`, geïsoleerde gitarchive in `/tmp/DEF-743-praktijk-20260917-v1/app` met eigen database; geen productiedata gewijzigd.
- Basis acceptatiepakket: `8f012f4129f92c91ab3e00368854fa93335bed05`; 31 cases en 94 historische IDs behouden.
- Claude Code CLI: echte binary `~/.local/bin/claude` 2.1.270; sessie `3bc3d720-93ab-43a9-8380-3b2cb7ad2848`. Maakte en draaide de tijdelijke testhelper. Volledig lokaal log: `/tmp/DEF-743-praktijk-20260917-v1/claude-uitvoering.jsonl`.
- Codex CLI: 0.154.0; onafhankelijke reviewersessie `01a0aefc-3e11-7862-9ba6-bdbab5499215`. Logs `/tmp/DEF-743-praktijk-20260917-v1/codex-review-v1.jsonl` en `codex-runreview-v1.jsonl`. Broncode alleen gelezen; eigen bewijsreplay zonder extra modelcall.
- Coördinator: echte browserflow, SQLite-bewijs vastleggen, beperkingen controleren en bevindingen triëren. Geen applicatiecode gewijzigd.
- AI-attributie van de app: `anthropic/claude-opus-4-8`, bronbeoordelingsprompt `con02-assess/1`, contract `con02/1`.
- Eerder Cowork-onderzoek blijft afzonderlijk beschikbaar in het acceptatiepakket van 16 september; geen nieuw Cowork-deskundigenakkoord gefabriceerd.

## Verificatiegrenzen

De run eindigde met exitcode 0 en zes gebudgetteerde aanroepen aan de AI-service (geen exacte telling van HTTP-providerrequests). Dat betekent dat de testhelper voltooide, niet dat alle cases slaagden. Eén AI-aanroep gaf timeout. Er zijn geen productiewijzigingen, geen nieuwe volledige unittest-/lintclaim en geen claim op complete ketendekking. De basis-CSV-export van de generatieprobe behield `draft` en een leeg cijfer; volledige CON-02-exportdekking is hiermee niet bewezen.

## Afsluiting van deze batch

De tijdelijke appserver is gestopt; database en bewijsbestanden zijn behouden. De Claude CLI-sessie is na de voltooide run en onafhankelijke review door de coördinator gestopt terwijl de verdere analyse nog liep (`aborted_streaming`). Het uitvoeringsbewijs is de afgeronde helperrun met exitcode 0, niet een succesvol CLI-eindrapport. De coördinator heeft de begrensde rapportage opgesteld en de Codex-reviewbevindingen verwerkt.

### Publicatie van de testhelper

De commitcontrole wees lintfouten aan in de kopie van de tijdelijke helper. Dezelfde Claude-uitvoerder corrigeerde alleen die kopie; ruff, black en compilecontrole slagen. `cli-bewijs/uitgevoerde-helper-brontekst.txt` bewaart exact de werkelijk uitgevoerde historische brontekst (SHA-256 `68643bb3b69c06e2ec60ba9dc4733b3d01a61262652038048742087fedcb015e`). `cli-bewijs/run_con02.py` is de opgeschoonde publicatiekopie en heeft geen nieuwe externe testrun gehad. De oorspronkelijke testresultaten blijven bij de historische brontekst horen. Zie `claude-lintresultaat-v1.md` en de gerichte Codex-deltareview.
