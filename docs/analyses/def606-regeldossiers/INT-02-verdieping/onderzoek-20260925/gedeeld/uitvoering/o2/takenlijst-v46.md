# INT-02 O2 — kwalificatie gestopt op tokenmeting (takenlijst v46)

30 september 2026. Vervangt v45 als procesingang; de daarin beschreven freeze en eerdere deeloplevering blijven gelden.

## Afgerond

- [x] Chris' exacte akkoord voor het pending manifest en 43 gevallen geregistreerd in `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-akkoord-registratie-v1.md` en het machineleesbare akkoordbestand.
- [x] Offline akkoordcontrole geslaagd: manifest, gevallen, protocol, profiel en limieten zijn exact gebonden.
- [x] Eén regressie-uitvoering geprobeerd. Eerste start weigerde vóór verzending wegens ontbrekende sleutel in deze werkboom; tweede start gebruikte de bestaande projectsleutel zonder deze af te drukken.
- [x] Runnerstop `tokenmeting_mislukt` na verbindingsfout vastgelegd. 0 inferenties, 1 gereserveerde tokenmeting, US$0 geboekt; geen modelantwoord. Grootboek en resultaat zijn duurzaam opgeslagen. Zie `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-uitvoeringsverslag-v1.md`.
- [x] Geen automatische retry; geen ontwikkeling, hold-out of O2-activering. Actions blijven uit.

## Open

- [ ] Oorzaak van de verbindingsfout buiten de mislukte proef vaststellen via een toegestane diagnostische route. De lokale PreToolUse-hook blokkeerde de credentialvrije `curl`-controle; de exacte SDK-foutoorzaak is nog niet bewezen.
- [ ] Daarna een nieuwe begrensde proef met nieuw manifest en exact menselijk akkoord voorbereiden; het mislukte grootboek blijft bewaard. Geen hergebruik of overschrijven van de bestaande proefmap.
- [ ] Regressie C105/C107/C112 inhoudelijk uitvoeren en pas na slagen beslissen over ontwikkeling en hold-out.
- [ ] Modelkwaliteit en activering afzonderlijk beoordelen; appintegratie en DEF-626-grens daarna afronden. Geen nieuwe merge onder dit besluit.
