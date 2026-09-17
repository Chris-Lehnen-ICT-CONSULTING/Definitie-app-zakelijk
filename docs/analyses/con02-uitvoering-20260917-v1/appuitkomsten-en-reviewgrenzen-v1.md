# Appuitkomsten naast modeloordelen

Aanvulling op `casusbatch-v1.md`: dat document toont de onbewerkte modeloordelen. Hieronder staan de uitkomsten nadat de app de citaten en binding heeft gecontroleerd. Geen van deze rijen geldt als complete casusacceptatie.

| Casus | Gezag | Betekenis | Verwijzing | CON-02 totaal (zonder cijfer) |
|---|---|---|---|---|
| C02-P01 | pass | pass | pass | pass |
| C02-P02 | pass | fail | pass | fail |
| C02-P04 | pass | pass | pass | pass |
| C02-P11 | pass | fail | review_required | fail |
| C02-P16 | error | error | error | error |
| C02-P31 | pass | pass | review_required | review_required |

## Reviewverduidelijkingen

- P31: model zegt positief, maar de app verwerpt het verwijzingsbewijs omdat het citaat niet in de bron staat; appuitkomst blijft open. Geen bewezen gewone app-pass voor deze serviceprobe.
- P01/P04 tonen bij deze service-invoer wel een positieve verwijzing zonder geregistreerde link; de aparte browserprobe + Codex-replay bevestigen DEF-806 onafhankelijk.
- Zes bronbeoordelingsaanroepen aan de AI-service zijn geteld. Dit is geen bewijs van exact zes HTTP-providerrequests: SDK-retries kunnen afwijken. Vijf assessments afgerond, één timeout.
- P07 muteert zowel definitie als bronset en is dus geen zuivere test van alleen bronmutatie.
- P10 gebruikt een voorbereide bronselectie en voert geen echte top-k-retrieval uit.
- P25–P27 leveren geen opslag-/exportbewijs; behoud alleen de cache-/bindingswaarneming.

- P28 heeft de bedoelde score-invoer `0.99` niet uitgevoerd; dus geen scoregrensbewijs voor die casus.
- De drie rapportagebevindingen uit `codex-runreview-v1.md` zijn door deze expliciete beperkingen verwerkt; ongewijzigde ruwe plan/resultaatdata zijn historische uitvoeringsgegevens, niet de eindconclusies.
