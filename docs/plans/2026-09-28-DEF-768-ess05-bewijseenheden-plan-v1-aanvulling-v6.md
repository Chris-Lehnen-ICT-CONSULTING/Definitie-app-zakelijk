# DEF-768 — aanvulling v6 op het plan bewijseenheden (B8 geaccepteerd als restrisico)

> **Aanvulling op** het plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` en de aanvullingen v1–v5 (v5: sha256 `a3552cb04cb3439a02f774193e56069fb5efde038a5d112dca966a65562a74d9`). Plan en eerdere aanvullingen blijven ongewijzigd. Deze aanvulling wijzigt geen code, geen beslisregel, geen orakel en geen invoer (v5 blijft gepind).
>
> **Aanleiding:** Codex-hercontrole v6 (`logs/def768/bewijseenheden-b-v1/codex-hercontrole-result-v6.md`) op HEAD `f6ad9806f` bevestigt B7 als opgelost en vindt geen route naar `geslaagd` zonder drie geldige E-oordelen van Chris. Wel NO-GO op **B8**: de functie `bewijsscorer.eindoordeel`, rechtstreeks aangeroepen met zelf samengestelde runoordelen in het geheugen, valideert typen en onderlinge consistentie van de nakijkvelden (M-a..M-d, categorie, uitkomst) van A/C/D niet volledig; tegenstrijdige of als tekst ("False") opgegeven waarden kunnen dan `geslaagd` opleveren. De bestandsroute (`scripts/ess05/r18_e_oordeel.py`) weigert al deze varianten, omdat zij alles uit de gehashte ruwe modeluitvoer herberekent.

## Besluit van Chris (29-09-2026)

B8 wordt **niet** verder uitgewerkt en is een **geaccepteerd restrisico**. Reden: proportionaliteit. De oordeelroute is na drie herstelrondes (B5/B6, B7, B8) zwaarder geworden dan de proef zelf; B8 is alleen bereikbaar door handmatig vervalste gegevens rechtstreeks aan een interne functie te geven, niet via de modeluitvoer of de normale proefgang. Er volgt geen nieuwe Codex-hercontrole op dit punt.

## Gebruiksregel (verplicht)

1. Het eindoordeel van R18 wordt **uitsluitend** bepaald via de bestandsroute: `scripts/ess05/r18_e_oordeel.py eindoordeel` op de door de runner geregistreerde callrecords, met de gepinde invoer v5 en het oordeelbestand van Chris.
2. `bewijsscorer.eindoordeel` mag niet rechtstreeks worden aangeroepen met zelf samengestelde of bewerkte runoordelen; een uitkomst die zo tot stand komt, is geen geldig proefoordeel.
3. Wie later een andere ingang bouwt, moet eerst B8 oplossen (volledige schema- en consistentievalidatie, of uitsluitend herberekening uit ruwe records).

## Restrisico

- **Wat kan misgaan:** een toekomstige ontwikkelaar of agent die de gebruiksregel negeert en `eindoordeel` rechtstreeks voedt, kan een onterecht `geslaagd` krijgen.
- **Wat niet kan misgaan:** het model kan dit niet uitbuiten (zijn uitvoer komt alleen via de callrecords binnen en wordt herberekend); de normale proefgang weigert B8.
- **Ongewijzigd uit v5:** consistent nagemaakte records worden zonder grootboekcontrole niet herkend; een latere scorerwijziging maakt oude records strijdig.

## Stand

Deel B is afgerond op HEAD `f6ad9806f` plus deze aanvulling. Alle overige punten zijn door Codex bevestigd: invoer v5 gepind (v1–v4 geweigerd), B1, B3/B4, netwerkgrens, R1–R17-pinning, budget 18 / 399 → 417 ≤ 427. Deel C (de betaalde proef) start pas na een uitdrukkelijk "go" en budgetbesluit van Chris.
