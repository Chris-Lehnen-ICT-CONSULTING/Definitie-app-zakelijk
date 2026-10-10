# INT-02 O2 — eerste kwalificatie-uitvoering gestopt (v1)

30 september 2026. Branch `feature/DEF-835-int02-o2`. Chris bevestigde het exacte manifest en gevallenbestand in deze chat; registratie: `kwalificatie-akkoord-registratie-v1.md`. De runner accepteerde het bijbehorende `kwalificatie-akkoord-v1.json` (SHA-256 `5bc122bc205fc995cfaa2cd1997fa63106df1f7b64fa94192462721dfcce767d`).

## Verloop

1. De eerste start werd vóór verzending geweigerd met `sleutel_ontbreekt`: de werkboom heeft geen eigen `.env`. Er was geen proefmap, geen tokenmeting en geen modelaanroep.
2. De tweede start kreeg uitsluitend de bestaande `ANTHROPIC_API_KEY` uit de `.env` van dezelfde projectrepository als procesomgevingsvariabele; de sleutel is niet afgedrukt of opgeslagen in dit dossier. De runner begon de regressiefase en probeerde de tokenmeting voor C105.
3. Die meting eindigde met `connection` / `AIServiceError`. De runner registreerde `tokenmeting_mislukt`, beëindigde de fase als mechanisch mislukt en sloeg het bewijs op. **0 inferenties, 1 tokenmeting gereserveerd, US$0 conservatief geboekt; geen modelantwoord en geen beoordeelde definitie.** C107 en C112 zijn niet uitgevoerd.

Het grootboek bevat `mandaat`, `fase_start`, `tel_reservering` en `fase_einde` met `mechanisch_geslaagd=false` en `bewijs_opgeslagen=true`. `regressie-afronding.voltooid` bestaat. De technische fout telt in de runnerstatistiek als fout op C105; de daaruit afgeleide teller voor een gemiste overtreding is **geen inhoudelijke modeluitkomst**.

Bewijs:

- `kwalificatieproef-v1/grootboek.jsonl`, SHA-256 `1bcf456b76a676e78b4e7e97c6cf095384a8fb3163a6b3ae80f3bec43d2b02e5`;
- `kwalificatieproef-v1/regressie-resultaat.json`, SHA-256 `783eacd4263d1dfe31c912f571dd5d265aa2a16949874dec3419fe4dad60ff68`;
- `kwalificatieproef-v1/regressie-bundel.json`, SHA-256 `d64974a62e0fec29fa7e1d197323f5223bb6eacea72a1373de6d2e2222fcd475`.

De precieze netwerkreden is met dit bewijs niet vastgesteld. Een credentialvrije `curl --head`-diagnose naar `https://api.anthropic.com` werd door de lokale PreToolUse-hook geblokkeerd met de melding dat netwerktools data kunnen exfiltreren. Dat toont een lokale diagnostische toegangsgrens, maar bewijst op zichzelf niet dat dezelfde hook de SDK-tokenmeting heeft geblokkeerd.

## Beslisgrens

Het protocol schrijft nul retries en stoppen bij een technische fout voor. Het bestaande grootboek markeert de regressiefase als uitgevoerd en mislukt; ontwikkeling en hold-out mogen onder dit manifest niet volgen. Eerst is een concrete diagnose of toegestane netwerkroute nodig. Een nieuwe proef vereist een nieuw, exact gebonden manifest en een afzonderlijk begrensd besluit; deze poging en haar bewijs blijven ongewijzigd bewaard. Er is geen O2-activering, Actions-wijziging, push of merge gedaan.
