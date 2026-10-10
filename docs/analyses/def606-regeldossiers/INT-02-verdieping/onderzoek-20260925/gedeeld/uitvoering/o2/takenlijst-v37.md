# INT-02 O2 — takenlijst v37
29 september 2026. Deze versie vervangt v36 als actuele ingang.

## Besluiten
- [x] Chris: “akkoord op 1 en 2” — vierde R08-correctie én scopeaanvulling-v2 met 50 extra bestaande bestanden geautoriseerd.
- [x] Besluit duurzaam vastgelegd in het S1-dossier: s1-akkoord-vervolg-20260929-v1.md.
- [x] Beide CLI’s beschikbaar/ingelogd; zestien bronhashes gelijk aan herreview3; uitgangshashes50extra bestanden vastgelegd.
- Actions blijven uit. Geen push, merge, productieactivering, echte database of externe publicatie.

## Reeds bewezen
- [x] Q1 kwalificatierunner: commit ebe9c1b7c, 176tests; onafhankelijke review afgerond.
- [x] S1 R01/R02/R09 gesloten binnen bestaand bewijsbereik.
- [x] R03 centrale writer en R07 interne draftcreate gecorrigeerd.
- [x] R08 editorherhaling met categoriekeuze en update-auditredenen gecorrigeerd; herreview3 bevestigt dit.
- [x] Correctie3:63gerichteR-tests; geen totaleS1groenclaim.

## Uitvoervolgorde
- [ ] **Actief:** vierde R08-correctie — oorspronkelijke create-actie moet de vergelijking van de reden met/zonder duplicaatdeel bepalen. Exacte oude eventtekst als afwijkende nieuwe reden moet worden geweigerd. Eerst gerichte RED, dan minimale fix, zelfde reviewer. Claude-exec94492.
- [ ] Daarna de goedgekeurde50bestanden: R04/R07 leestransacties/voorkeurstermschrijver, R05historischschemaherstel, R06fixtures, R03versies bij9productieaanroepers en32testfiles.
- [ ] Onafhankelijke review van concrete correcties, gerichte en passende bredere verificatie; normale lokale commit pas als S1 aantoonbaar gereed is.
- [ ] Daarna S2documentbewaring/herladen, U1editor en E1export (al geaccordeerd).
- [ ] Goldsetbeoordelaars kiezen, labels accepteren, freeze; modelkwalificatie binnen43appcalls+43tokenmetingen/US$12. Nog nul nieuweappcalls.
- [ ] Eindcontrole en oplevering. Activering afzonderlijk.

## Actuele bron en eigenaarschap
Werkboom /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app; branch feature/DEF-626-validatiesnapshots; HEAD ebe9c1b7c26ffe6040bffb66db4937b932406dc8. S1 ongecommit.
Dossier /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2.
Claude-sessie7f05cfbc-1970-4a7b-a241-c4693f11f217 implementeert; Codex-reviewer01a0e928-8d33-7c31-b145-6aec14fe4d59 in /Users/chrislehnen/.codex/worktrees/def626-s1-review/Definitie-app reviewt zonderbronwijzigingen.
Leidende opdracht: s1-reviewcorrectie4-opdracht-claude-v1.md.
Leidend scopevoorstel: s1-scopeaanvulling-voorstel-v2.md, SHAadd22e59887ef5187275a63c33ebd9b358674afaa96f74e1d850e164c17ce740.
Bewijs bij start: s1-correctie3-reviewmanifest-v1.json; fulldiffa5ec70465099edddab285cdc08e265ad538b464b01aec406a6900605afab6f90.

## Grenzen
De vorige24gerichtefailures/115R03IDs zijn nog open; de uitbreiding is nu geautoriseerd maar nog niet uitgevoerd. Complexiteit204>201 (basis205), geen drempelophoging.
Goldsetbeoordelaars en specifiekeLinearpublicatie zijn nog niet beslist. PromptForgefallback na eerdereweigering blijft gelden. Geen ongeautoriseerde nieuwe schema-/contractwijziging.
