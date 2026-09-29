# DEF-835 — actuele takenlijst v24

28 september 2026. Vervangt v23 als actuele ingang. Branch `feature/DEF-835-int02-o2`, HEAD `f9bb9e6973926a3cf768995f5d879f6edfd6322d`.

## Afgerond en bewezen

- [x] WP5a, F1–F4 en de dertien typefouten afgerond; onafhankelijke CLI-reviews gesloten.
- [x] Bestaand eindbewijs: 526 tests, mypy 411 bestanden en lint groen; brede eerdere regressie 2.966 tests. Geen volledige-suiteclaim.
- [x] Normale lokale commit f9bb9e697; hooks inclusief Gitleaks geslaagd.
- [x] Hervatting: git fetch origin; main heeft geen nieuwere commits voor deze branch.
- [x] Actuele DEF-626/835/815 opgehaald; opslag en UI/export gericht alleen-lezen verkend.
- [x] Concrete vervolgplannen opgeslagen: `kwalificatieprotocol-v1.md` en `vervolgplan-opslag-ui-v1.md`.

## Nog uit te voeren, in volgorde

- [ ] Chris kiest goldsetbeoordelaars: twee mensen of onafhankelijke CLI-voorstellen met zijn inhoudelijke eindbeoordeling.
- [ ] Protocol, kwaliteitsgrenzen en nieuw proefmandaat vaststellen: maximaal 43 appcalls/43 tokenmetingen, US$12, fasen 3+24+16; geen livecalls vóór akkoord en freeze.
- [ ] Q1: veilige proefrunner offline uitbreiden, tests rood→groen, CLI-review.
- [ ] 40 nieuwe gevallen onafhankelijk labelen; Chris accepteert; 24 ontwikkeling/16 hold-out bevriezen.
- [ ] S1 expliciet accorderen: gedeeld DEF-626-schema/contract, 16 bestanden en vervanging van precies twee oude triggers.
- [ ] S1 bouwen/reviewen: immutable versies/snapshots, één atomaire schrijver, echte save→reload en foutrollback.
- [ ] S2 accorderen/bouwen/reviewen: O2-foutdocumenten behouden, strikte replay en C118, geen modelcall bij herladen.
- [ ] U1/E1 accorderen/bouwen/reviewen: editor, actuele/historische weergave, additief exportveld.
- [ ] Modelkwalificatie uitvoeren met geaccepteerde labels en binnen nieuw mandaat; C107/C112 blijven concrete risico's.
- [ ] Geïntegreerde offline eindcontrole, alle failures verklaren, onafhankelijke finale diffreview waar nog nodig.
- [ ] O2-oplevering en afzonderlijk activeringsbesluit.

## Grenzen

Geen nieuwe softwarewijziging of livecall in deze voorbereidingsbeurt. Actions blijven uit, O1 blijft actief. Geen push/merge/activering. DEF-626 is nog geen geleverde voorziening; geen parallelle INT-02-opslagroute. Details in `processtatus-uitvoering-v12.md`.

