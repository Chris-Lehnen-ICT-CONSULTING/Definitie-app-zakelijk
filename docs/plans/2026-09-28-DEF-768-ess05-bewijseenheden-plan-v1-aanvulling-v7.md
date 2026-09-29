# DEF-768 — aanvulling v7 op het plan bewijseenheden (F7-besluit: ja)

> **Aanvulling op** het plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` (sha256 `4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3`) en de aanvullingen v1–v6 (v4: `922a63a6b9bcec13bd49bace58554801eb3cd73da15d6bcb0f5cfc184b3ab120`, v5: `a3552cb04cb3439a02f774193e56069fb5efde038a5d112dca966a65562a74d9`, v6: `cb510963e5f38a66b03e8d1240249821bcb7f5e41225ecc4bf14a3f9105b1f26`).
>
> Plan en eerdere aanvullingen blijven ongewijzigd. Waar deze aanvulling afwijkt, gaat zij voor. Zij vervangt de F7-behandeling uit het plan (regel 827 en 1110: F7 apart rapporteren, niet geslaagd en niet kritiek, wachten op het F7-besluit) en het orakel van casus A.
>
> **Grenzen ongewijzigd:** geen wijziging aan `src/`, de norm, de prompt, de lokale controle, skills of config; geen budgetbesluit, geen freeze, geen netwerk- of betaalde aanroep; R1–R17 en budget (399/417/427) ongemoeid.

---

## Besluit van Chris (29-09-2026): F7 = ja

De naam van een verwant begrip (buurnaam) draagt betekenis. Chris: **"Verhuur is altijd betaald."**

Voor casus A (uitleen = tijdelijk + kosteloos; buur verhuur = tijdelijk, kosten niet in het materiaal) zijn daarom **twee antwoorden juist**, beide volwaardig geslaagd:

| | `kosteloos` bij `verhuur` | Uitkomst | Betekenis |
|---|---|---|---|
| (a) | `ontkend` | `pass` | verhuur is betaald (uit de buurnaam) |
| (b) | `onbesproken` | `review_required` | voorzichtig: het materiaal noemt geen kosten van verhuur; niet fout |

Er is **geen aparte F7-categorie** meer en **geen wachten op een F7-besluit**. De F7-route is verwijderd uit scorer, proefoordeel en eindoordeel (`f7_afwijkingen`, `m_b_dragend_ok_zonder_f7`, `m_c_dragend_ok_zonder_f7`, categorie `f7`, oordeel `wacht_op_f7_besluit`, orakelveld `f7`).

## Koppeling toestand ↔ uitkomst

De twee antwoorden zijn alleen juist mét hun eigen uitkomst: `ontkend` + `review_required` en `onbesproken` + `pass` zijn **niet geslaagd**.

**Uitdrukking in het orakel.** Het feit `kosteloos`/`verhuur` van A:

```json
{
  "toestand": ["onbesproken", "ontkend"],
  "vereist": [],
  "toegestaan": ["Verhuur:", "<buurbeschrijving>"],
  "uitkomst_per_toestand": {"onbesproken": ["review_required"], "ontkend": ["pass"]}
}
```

De orakeluitkomst van A wordt `["review_required", "pass"]`.

**Uitdrukking in de scorer.** Er komt geen nieuwe runcategorie bij; de bestaande maten doen het werk:
- **M-c:** de toestand is juist als het model voor het feit precies één toestand noemt en die in `toestand` staat. Voor de bestaande orakels met één toestand is dat gelijk aan de oude regel. Twee strijdige toestanden tegelijk (onbesproken én ontkend) zijn niet juist.
- **M-d:** juist als de uitkomst in de orakeluitkomst staat **én** hoort bij de gekozen toestand volgens `uitkomst_per_toestand`. Een verkeerde combinatie is dus gewoon een M-d-fout: `niet_geslaagd`, volgens de bestaande regels. Kritiek is die combinatie alleen als M-c of M-b dan ook onwaar is bij `pass`/`fail`, zoals voor elke run.
- **Controle vooraf** (`controleer_orakel`): `uitkomst_per_toestand` moet voor precies de toestanden een niet-lege lijst uitkomsten geven, die samen precies de orakeluitkomsten zijn. Het oude veld `f7` is een orakelfout.

**Bewijs (M-b), in lijn met aanvulling C3.**
- `vereist` noemt eenheden die het feit zelf dragen. Het materiaal zegt niets over kosten van verhuur, dus is er **niets vereist**.
- De kennis "betaald" komt uit de buurnaam. Daarom zijn alleen de eenheden die die naam dragen **toegestaan**: de Verhuur-zin (`Verhuur:`) en de buurbeschrijving. Elke andere eenheid, zoals de Uitleen-zin, laat het feit niet dragen.
- Bij `onbesproken` zonder bewijs draagt het feit, zoals voorheen.
- De bewijsregels (`src/domain/ess05/bewijsregels.py`, ongewijzigd) eisen bij `ontkend` al een eenheid die "verhuur" noemt: zonder eenheid is het een `schemafout`, met de Uitleen-zin een `onderwerpfout`. Beide geven `error`, dus niet geslaagd.
- Een niet-lege `vereist` zou het voorzichtige antwoord (b) onterecht laten falen; daarom blijft `vereist` leeg.

## Invoer v6

- **Schema:** het invoerschema wordt `def768-ess05-bewijsregel-invoer/7`.
- **Orakel A:** zoals hierboven. C, D en E zijn ongewijzigd; alle casusteksten zijn ongewijzigd.
- **Nieuw bestand:** `reports/DEF-768-AI-20260928-R18/bewijsregel-invoer-v6.json`, gemaakt met de generator. `-v1` t/m `-v5` worden niet overschreven.
- **Maker:** de maker pint deze aanvulling (v7) op sha256.
- **Runner en `r18_e_oordeel.py`:** de runner pint `-v6`, en `r18_e_oordeel.py --invoer` gebruikt `-v6` als standaard. `-v1` t/m `-v5` worden op schema en invoerhash geweigerd; het A-orakel van `-v5` ook op het veld `f7`.
- **Hash:** de sha256 van `-v6` staat in de runner (`R18_I_INVOER_SHA256`) en in `logs/def768/bewijseenheden-b-v1/resultaat-v8.md`. Deze aanvulling kan die hash niet zelf bevatten, omdat de invoer deze aanvulling pint.

## Gevolg voor norm en app

Buiten deze proef verandert niets. `src/` en de interpretatieprompt zijn ongewijzigd. Of de app-prompt of de norm dit besluit expliciet moet maken, is een **apart, later besluit** van Chris.

## Notitie (zonder gevolg voor de proef)

Chris merkt op dat uitlenen en verhuur niet altijd aan medewerkers zijn. In casus A is "aan een medewerker" lokale testcontext (de werkinstructie van de servicedesk). Het staat in beide definities en raakt het onderscheid tussen uitleen en verhuur niet. De casustekst blijft ongewijzigd, voor vergelijkbaarheid met R16/R17.

## Wat ongewijzigd blijft

- **Oordelen en E:** besluit optie 2 (voorwaardeoordeel E van Chris), `EINDREGEL`, de oordeelroute (v4/v5) en B8 als geaccepteerd restrisico (v6).
- **C1 en de orakels van C, D en E.**
- **Budget:** 18 aanroepen, cumulatief 399 → maximaal 417 binnen 427.
- **R18B:** `lokale-invoer-v1.json` (sha `a36172a0…5b81`).
- **Contract:** `ess05-bewijsregels/6`, prompt /4.
- **Uitvoering:** een betaalde stap alleen na een "go" van Chris met een eigen budgetbesluit.
