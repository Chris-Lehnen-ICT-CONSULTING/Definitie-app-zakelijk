# DEF-835 — Q1 uitvoeringsverslag v2: F3 fsync-fout ná flush

28 september 2026. Claude Code CLI-uitvoerder, sessie 585f02d8-1256-466a-a2ac-ae45d7cbc746. Dit verslag vult `q1-uitvoering-v1.md` aan; v1 blijft ongewijzigd.

Deze stap corrigeert F3 naar aanleiding van `q1-codex-herreview-v1.md` en `bewijs/q1-codex-herprobe-v1.py/.log`. De probe heb ik niet gewijzigd. F1 (processlot) en F2 (p95) zijn door de reviewer gesloten; die code is ongewijzigd gebleven.

Randvoorwaarden:
- basis `f9bb9e697`;
- geen livecalls;
- geen goldset gelezen;
- geen nieuwe dependency;
- niets gestaged of gecommit.

## Defect

Na drie correcte regressies schreef en flushte `Grootboek.schrijf` de regel `fase_einde` (`mechanisch_geslaagd=true`). Daarna gaf `os.fsync` een EIO-fout. De run brak af, maar een nieuwe lezing zag `regressie=true` en `open_fase=None`. De ontwikkelfase verstuurde daarop 24 calls.

## Oplossing: vooraf vastgelegde afrondingsblokkade

`_sluit_fase` verloopt nu in drie stappen, volledig onder het bestaande F1-slot:

1. **Blokkade vastleggen.** `<fase>-afronding.open` wordt exclusief geschreven (`open("x")`, flush, fsync). Zodra dit bestand bestaat, ook na een fsync-fout, blokkeert het. Lukt het schrijven niet, dan volgt geen `fase_einde` en blijft de fase open (`grootboek_open`).
2. **`fase_einde` naar het grootboek.** Elke fout hier, ook een fsync-fout terwijl de succesregel al leesbaar is, laat de blokkade staan.
3. **Opheffen** met één `os.rename` naar `<fase>-afronding.voltooid`. Dit is een enkele, atomaire systeemaanroep zonder vervolgstap. Faalt de rename, dan blijft de blokkade staan. Het bestand blijft als `.voltooid` bewaard; er wordt niets verwijderd.

Toelating van een volgende fase (`_eis_afronding_voltooid`) gebeurt zowel in de vroege controle als opnieuw onder het slot, en altijd vóór het lezen van de sleutel en vóór transport. Weigering met `afronding_onvolledig` volgt als:
- er een `*-afronding.open` bestaat; of
- voor een beëindigde fase in het grootboek geen `.voltooid` bestaat.

Een leesbare succesregel heft de blokkade dus nooit op. Opheffing volgt alleen na een geslaagde `fase_einde` inclusief fsync. De eerdere controles blijven eerst gelden: `grootboek_open`, `fase_al_uitgevoerd` en `fasevolgorde`.

## Foutmomenten en bewijs

| Foutmoment | Gevolg | Test |
| --- | --- | --- |
| fsync van de `fase_einde`-regel ná flush (reviewgeval) | succesregel leesbaar, blokkade staat; nieuwe runnerinstantie: `afronding_onvolledig`, 0 requests, sleutel niet gelezen | `test_f3_fout_na_flush_van_afronding_blokkeert_blijvend[fsync-fase-einde…]` |
| fsync van het blokkadebestand ná flush | geen `fase_einde`; vervolg `grootboek_open`, 0 requests | `[fsync-blokkade…]` |
| opheffen (rename) faalt | succesregel leesbaar, blokkade blijft; vervolg `afronding_onvolledig`, 0 requests | `[opheffen-blokkade…]` |
| beëindigde fase zonder `.voltooid` | `afronding_onvolledig`, 0 requests | `test_f3_beeindigde_fase_zonder_voltooiingsbewijs_blokkeert` |
| normale afronding | `.voltooid` bestaat, geen `.open`, volgende fase loopt (24 calls) | `test_f3_geslaagde_afronding_heft_blokkade_atomair_op` |

De "nieuwe runnerinstantie" is een apart geladen module van hetzelfde script, onder een eigen modulenaam. Die leest het grootboek opnieuw vanaf schijf.

Aanpassing aan een bestaande eigen test: `test_f1_slot_vast_van_transport_tot_na_bewijs_en_afronding` verwacht nu ook `regressie-afronding.open` onder de onder slot geschreven bestanden, vóór `fase_einde`. Er is geen testcase verwijderd.

Bewijsbestanden (onder `bewijs/`):

| Stap | Bestand | Uitkomst |
| --- | --- | --- |
| Herstelkopieën | `q1-F3-fsync-herstel-v1/` | herreviewde staat |
| Rood (formeel) | `q1-F3-fsync-red-v1.log` | 5 nieuwe failed op de ontbrekende constanten; 171 eerdere tests passed |
| Rood (gedrag) | `q1-F3-fsync-red-gedrag-v1.log` | met plugin `q1-F3-fsync-redplugin-v1.py`, die alleen de twee naamconstanten in het geheugen zet; oude code, 5 failed |
| Groen | `q1-F3-fsync-green-v1.log` | **176 passed** (alle Q1-tests) |
| Lint | `q1-F3-fsync-lint-v1.log` | Black, Ruff 0.15.17 en Ruff 0.16.5 schoon |
| Diffs en hashes | `q1-F3-fsync-deltadiff-v1.patch`, `q1-F3-fsync-diff-v1.patch`, `q1-F3-fsync-hashmanifest-v1.json` | delta t.o.v. herreviewde staat, volledige diff t.o.v. basis |

De gedragsrode run toont in het reviewgeval dat de run wel afbreekt maar dat er geen blokkade bestaat. De 24 vervolgcalls zelf staan in de herprobe van de reviewer.

## Bronhashes na correctie

| Bestand | SHA-256 |
| --- | --- |
| `scripts/analysis/def835_int02_modelproef.py` | `94adea36ffa555a8d9fee790f5eb96ce54ece96efd107adf25dd147ccb1a637f` |
| `tests/unit/validation/test_def835_int02_modelproef.py` | `60b2c420f3b7ff80582ec4e42dda80f77c986bf351e6c538637048bc2d61b79e` |
| `tests/fixtures/def835_int02_kwalificatie_runner.json` (ongewijzigd) | `2f50c456756614cc35e78b81f57f4c8afc748b79d4cfcd6da053306e6c8fd7a7` |

## Beperkingen

- Deze correctie sluit het lokale proces- en I/O-foutgedrag. Er is geen garantie tegen stroom- of systeemuitval: er wordt geen directory-fsync gedaan na aanmaak of rename. Gaat een blokkade of `.voltooid` door een systeemcrash verloren, dan kan de toestand afwijken. Bij een verloren `.voltooid` blokkeert de runner (veilige kant). Bij een verloren `.open` met een al duurzame succesregel zonder `.voltooid` weigert de controle "beëindigde fase zonder `.voltooid`" eveneens.
- Een overgebleven blokkade blokkeert het mandaat blijvend; er is bewust geen hervatfunctie. Opheffen vraagt een nieuw, expliciet besluit (nieuw mandaat of manifest).
- De borging blijft procedureel. Wie blokkade- of `.voltooid`-bestanden handmatig verwijdert, hernoemt of aanmaakt, omzeilt de runner.
- De eerdere beperkingen uit v1 blijven gelden: flock alleen lokaal/POSIX, labelhashes niet geheim, 4/8/4-verdeling verplicht, inhoudelijke beoordeling open voor Chris.
