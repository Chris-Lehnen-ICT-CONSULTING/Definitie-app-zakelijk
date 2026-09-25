**Geen bronvrijgave: twee concrete blockers blijven over.** De oorspronkelijke proefteksten zijn hersteld, maar directe tegenhangers tonen onvoldoende afbakening.

1. **R1/T15 — gesloten.**  
   De dubbele punt geldt nu voor het aaneengesloten lijstblok. Gerichte tests en schrijfvrije probes bevestigen behoud van onzekerheid bij blokonderbreking en zelfstandige vervolgtekst; echte zinseindtekens blijven beoordeeld. Geen nieuwe grammaticale aanname aangetroffen.

2. **R2/T17–T20 — gedeeltelijk hersteld, Important blijft open; dispositie: fix nu.**  
   De oorspronkelijke gevallen met komma én spatie leveren de juiste grenzen, passages en bewijsposities. Zonder spatie blijft dezelfde kandidaat echter verdwijnen:
   ```
   bord met de tekst ‘kom terug!’,dat verschijnt
   ```
   Dit geeft onder `/9` nog zinsstructuur-pass; met spatie volgt terecht onzekerheid. Ook `‘kom terug!’;de lamp brandt` blijft stil positief.  
   **Oorzaak:** [zinsgrenzen.py:380](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:380) vereist witruimte na het scheidingsteken. Ontbrekende witruimte bewijst geen samenhang en rechtvaardigt geen pass onder het citaatbeleid.  
   **Correctie:** laat deze direct vergelijkbare overgangen de bestaande onzekerheidsroute bereiken, met behoud van de oorspronkelijke slottekenpositie. Geen nieuwe taalheuristiek nodig.

3. **R3/T08 — oorspronkelijke LOW gesloten; nieuwe Important-regressie, dispositie: fix nu.**  
   T08 behoudt nu uitsluitend de echte grens na `R7.`. De vrijstelling geldt echter ook voor onverklaarde afkortingsvormen:
   ```
   houder volgens q.z. AB-12.
   ```
   Base `/8`: onzeker bij `q.z.`. Kandidaat `/9`: zinsstructuur-pass. Zonder afsluitende punt gebeurt hetzelfde.  
   **Oorzaak:** `_afkortingsfunctie` classificeert willekeurige gestippelde lettervormen als `afkorting`; [zinsgrenzen.py:675](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:675) stelt die vervolgens vrij zodra een afsluitende code volgt. De codevorm bewijst noch de betekenis van de onbekende afkorting, noch haar aansluiting.  
   **Correctie:** beperk de vrijstelling tot positief ondersteunde voorbeeldcontext; behoud onzekerheid bij onbekende afkortingen. De algemene aanname dat een losse code geen zelfstandige uiting kan zijn, levert daarvoor onvoldoende bewijs.

Contract `/9`, afwijzing van `/1`–`/8`, beide servicelaadpaden en beoordeling/opslagbinding zijn ondersteund. De skillsreferentie sluit aan; geen afzonderlijke skillsbevinding. Generatiebron, configuratie en Nederlandse-generatieskill zijn ongewijzigd.

Gelezen bewijs: **34 RED-failures/51 tests; 501 gericht groen; 1054 regressietests groen; integratie 27 geslaagd, 1 skip; lint groen.** De canonieke unitgate had bij de laatste controle nog geen eindresultaat. Geen volledige gateclaim.

Beide patches reconstrueren de zeven manifestbestanden exact; hashes vóór en na gelijk. Bases: app `ad4be749b2e38b968a22605f3842e244e6a766b7`, skills `e414eee84552b74818233e5c0fc4dacf36cd729a`.

SHA256:

- Appdiff: `05b375819a7e5156e03bf1fe401ef21eb6985ea6f12c56cd0f528bd6b295fc42`
- Skillsdiff: `28b993bb8f08c120376611b953710d64fde36f6ce79e06c47e08ff4e01bb874e`
- Manifest: `d9c24491e248a7c55dcdc0db1b5205542efd7508f233b27d171ebc9eabed3119`

Geen edits, brede testherhaling of betaalde calls. Nieuwe proefdata niet gelezen; historische labels ongewijzigd.