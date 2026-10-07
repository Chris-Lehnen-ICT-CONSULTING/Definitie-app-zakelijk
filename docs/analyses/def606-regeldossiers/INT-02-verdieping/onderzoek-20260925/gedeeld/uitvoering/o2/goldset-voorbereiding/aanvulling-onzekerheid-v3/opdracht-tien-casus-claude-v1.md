# DEF-835 — derde en laatste redactionele poging voor open INT-02-functiegronden

Je bent tekstredacteur in een **verse Claude Code CLI-sessie**. Doe deze documenttaak zelf, zonder agents of herdelegatie. Je bent niet alleen in de repo; lees alleen de genoemde bronnen en wijzig of verwijder geen bestanden. Geen Git-, app-, web-, API-, modelkwalificatie- of productiedatahandelingen. Lever uitsluitend geldig JSON als definitief antwoord. De coördinator bewaart het resultaat in een nieuw dossierbestand. Je mag later geen O2-promptontwikkelaar of appimplementator zijn omdat je mogelijke eindtestgevallen ziet.

## Bronnen — volledig lezen

1. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md` — INT-02-norm en statusgrenzen.
2. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md` — besluitenbasis.
3. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/ontwerpregister.md` — 76 ontwerpgevallen, uitsluitend overlapcontrole.
4. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/herwerking-v1/casuspool-kandidaat-v4.json` — 40 huidige kandidaten, uitsluitend overlapcontrole.
5. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/aanvulling-onzekerheid-v1/zeven-onzekerheidsgevallen-gevalobjecten-v1.json` — G057–G063, uitsluitend overlapcontrole.
6. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/aanvulling-onzekerheid-v2/zes-onzekerheidsgevallen-gevalobjecten-v1.json` — G064–G069, uitsluitend overlapcontrole.
7. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/../kwalificatieprotocol-v1.md` — onafhankelijke procedure en vier families. Het selectieplan is geen labelquotum.

De gebruiker heeft beperkte externe verwerking van synthetische gevallen, normteksten en besluiten toegestaan. Alle casussen en bronnen zijn fictief; geen claim over geldend recht en geen persoonsgegevens. Lees geen individuele labelbesluiten, beoordelaarsvoorstellen, appuitkomsten of kwalificatieproef.

## Probleem en toets voor de redacteur

Eerdere pogingen leverden meerdere goede, maar door de bronnen **oplosbare** begripscriteria of voorschriften op. Dat is een waardevol ontwerpresultaat, maar vult de ontbrekende onzekerheidsfamilie niet. Dit is de laatste redactionele poging binnen de afgesproken max. drie pogingen per actie. Bereid **maximaal tien** nieuwe gevallen G070–G079 voor, of minder als niet alle tien zonder kunstgreep haalbaar zijn.

Elk aangeboden geval moet de **functie van één exacte zinsdeel** werkelijk openlaten. De concrete bronnen moeten zowel deze lezing steunen: (A) de passage is een kenmerk/status/afleiding waarmee het begrip wordt afgebakend, als deze: (B) dezelfde passage neemt een handelings- of beslisregel voor een actor over. De bronnen mogen op dit punt botsen, maar zijn elk op zichzelf een plausibel document in hetzelfde fictieve domein. Leg in de bedoeling geen voorrang, werkelijke praktijk of gewenste uitkomst vast. Een enkele bron die de kwestie ondubbelzinnig oplost, een algemene opmerking dat iets dubbelzinnig is, of een uitsluitend andere kwaliteitsvraag is onvoldoende.

**Voer intern per ontwerp een tegenproef uit voordat je het aanbiedt:** wijs precies één concreet tekstfragment vóór lezing A en één vóór lezing B aan. Zoek vervolgens of een ander fragment één lezing alsnog uitsluit. Zo ja: laat het geval vervallen of herontwerp inhoudelijk; publiceer geen gerepareerde schijnonzekerheid. Houd die tegenproef in het selectiepunt, buiten het gevalobject. Dat selectiepunt krijgen de onafhankelijke beoordelaars niet. Gebruik waar passend feitelijke tegenvoorbeelden in bronnen (bijvoorbeeld een geregistreerd geval waarin de handeling uitbleef), maar alleen als dat een echte interpretatievraag openlaat, niet als het al één lezing bewijst. Geen bron die zelf het INT-02-label geeft.

Spreid de tien gevallen over verschillende domeinen en **verschillende bronrelaties**. Niet tien varianten van “object dat actor binnen termijn X doet”. Varieer tussen status versus uitvoeringsregel, constitutieve beslissing versus procedure, normatief eigenschap versus nalevingsopdracht, dossierclassificatie versus interventie, afleidbare grootheid versus reken-/betaalstap, en andere werkelijk zelfstandige functiegrenzen. Vermijd oppervlakkige varianten van de 40 G-kandidaten, eerdere aanvullingen en 76 C-ontwerpen. Een ander zelfstandig onderwerp is niet genoeg als de bronlogica identiek blijft. Geen geforceerde familieaantallen of labels: beoordelaars en Chris beslissen later.

## Structuur en herkomst

Per gevalobject **exact**: `id`, `herkomst`, `begrip`, `kern`, `bedoeling`, `context`, `bronnen`. `context` bevat exact lijsten `organisatorische_context`, `juridische_context`, `wettelijke_basis`. Iedere bron heeft `id`, `tekst`, `herkomst`. Gebruik voor geval en bronnen: `Synthetisch concept, voorbereid door Claude Code CLI op 30 september 2026 voor DEF-835; geen praktijk- of expertbewijs.` De context noemt expliciet fictie en geen claim over bestaand recht. Geen labels, verwachte status, familie of split in het gevalobject of selectiepunt.

Per aangeboden geval een apart selectiepunt `{id,inhoudelijke_nieuwheid,nabije_ids,open_bronvraag,tegenproef_a,tegenproef_b,waarom_niet_beslist,risico_op_triviale_variant}`. De twee tegenproefvelden verwijzen naar concrete bronfragmenten, maar noemen geen verwacht oordeel. Leg ontbrekende IDs expliciet uit in `niet_aangeboden`; verzin geen zwakke gevallen om tot tien te komen.

## Exacte uitvoer

Eén geldig JSON-object, zonder Markdown:

{
  "status": "concept_niet_geaccepteerd",
  "normversie": "def771-int02/2",
  "gevallen": [maximaal tien volledige gevalobjecten in ID-volgorde G070..G079],
  "selectiepunten": [één per aangeboden geval],
  "niet_aangeboden": [objecten met id en concrete reden voor ieder overgeslagen ID],
  "bewijsgrenzen": [korte Nederlandse teksten]
}

Controleer vóór definitief antwoord: unieke IDs, zeven velden per geval, consistente fictieve bronnen, neutrale bedoeling, twee brongebonden functie-lezingen die niet meteen worden opgelost, inhoudelijke afstand, geen label of split en geen wijziging van de bestaande pool. De output is geen goldset.
