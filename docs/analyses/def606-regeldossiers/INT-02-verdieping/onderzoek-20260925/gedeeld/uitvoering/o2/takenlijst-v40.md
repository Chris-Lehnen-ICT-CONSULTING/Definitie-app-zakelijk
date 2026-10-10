# INT-02 O2 — takenlijst v40
29 september 2026. Vervangt v39.

## Afgerond bewijs
- [x] Akkoord op vierde R08-correctie en uitbreiding met50bestanden vastgelegd.
- [x] Goedgekeurde uitbreiding uitgevoerd;51van66bronbestanden gewijzigd.
- [x] Eindbewijs gecontroleerd:116/116bekendeR03gevallen groen;55nieuwe testgevallen,0bestaandeIDsverdwenen;51rood/4alnegatiefgroen op pakketstart;16onderscheidende mutanten(v3).
- [x] Brede unitrun:8656passed,13failed,1error. Geen totalegroenclaim;11nieuwefailuresbuitenscope,2baselinefailures+1baselineverzamelfout.
- [x] Ruff/Black/mypy en twee relevante gates groen;complexiteitsgate204>201 blijftfalend,zelfdepakketstart.
- [x] Zelfde onafhankelijke Codex-reviewer beoordeelde de concrete delta en reproduceerde UFO-race plus voorkeurstermregressies.
- [x] Eindrapport+29bewijsbestanden na hashcontrole aanreviewer overgedragen;66bronhashes gelijk. Reviewer moet deze finalelogs nog afhandelen.

## Nu
- [ ] Claude corrigeert S1-R10 binnen de bestaande scope: getoonde kandidaatbinding bij UFO-opslag en indienen, twee racevensters.
- [ ] Claude bewaart de2afgewezen tijdelijke checkerproeven met herkomst en corrigeert de tebrede claim “nietsverwijderd”. Bestaande test-IDszijn behouden.
- [ ] Dezelfde Codex-reviewer controleert daarna R10delta en de nog open finale bewijsclaims R04/R05/R06/R07.

## Wacht op afzonderlijk besluit
- [ ] R08-opslagactievoorstel-v1 (interne audit-JSONafspraak plus begrensde helpervervanging).
- [ ] Restdoorwerking-voorstel-v1:9extrabestanden, voorkeurstermroutes/testherijking en eerlijke importmelding bij gedeeltelijke opslag. Dit is buiten het akkoord op50extra.
- [ ] Goldsetbeoordelaars/labels/freeze en specifieke eerdergeblokkeerdeLinearpublicatie.

## Daarna
- [ ] AlleS1bevindingen sluiten en lokaalcommitteren.
- [ ] S2/U1/E1 (algeaccordeerd), modelkwalificatie en geïntegreerdeappverificatie.
- [ ] Oplevering; activeringafzonderlijk.

## Verwijzingen
Werkboom: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app
Branch:feature/DEF-626-validatiesnapshots;HEADebe9c1b7c26ffe6040bffb66db4937b932406dc8.
Claude7f05cfbc-1970-4a7b-a241-c4693f11f217,exec32624,opdracht s1-r10-correctie-opdracht-claude-v1.md.
Codex01a0e928-8d33-7c31-b145-6aec14fe4d59,inactiefnadelta-review.
Dossier relatief:docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2.
Uitvoering:s1-scopeaanvulling-uitvoering-v1.md SHA1f81917276a6a0d1893564c27b96b814505cd63f955cf6989d7aac6ed27b4b9b.
Review:s1-codex-review-scopeaanvulling-v1.md SHA5aac706ecb4a05583cb01f06cbd22cda2ef037e28428451a7b89a7c5c5a38bbd.
Restvoorstel:s1-restdoorwerking-voorstel-v1.md SHAd6b3d2b0e32fd08cf0e04ea287a0775e29ddbf679ec2430194b9fa164ef8c987.
ActionsUIT;geenpush/merge/productieactivering/echteDBmigratie/modelcalls. Nieuwbudgetverbruik0. PromptForgefallbackenbeveiligingsgrenzenblijven.
