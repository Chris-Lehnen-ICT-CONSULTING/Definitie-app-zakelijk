# Q1 — gerichte herreview van F1–F3

Jij bent dezelfde Codex CLI-reviewer, sessie 01a0e8ca-2df9-7780-ba7a-b18c26caefe7. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Wijzig geen bronbestanden/tests/configuratie.

Dezelfde aparte reviewwerkboom is bijgewerkt met bytegelijke kopieën. Basis blijft f9bb9e6973926a3cf768995f5d879f6edfd6322d. Nieuwe hashes:
- scripts/analysis/def835_int02_modelproef.py: af59b9e0e2d86d29442a4e17865f8dc42c272ba11cb30e4fcd9ea3f5962373ab
- tests/unit/validation/test_def835_int02_modelproef.py: 111a4ef8b478bc8557806904929426bf2936cac03ca912912cd4f94de81e7eb3
- tests/fixtures/def835_int02_kwalificatie_runner.json: 2f50c456756614cc35e78b81f57f4c8afc748b79d4cfcd6da053306e6c8fd7a7 (ongewijzigd)

Relatief U: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2.
Lees U/q1-uitvoering-v1.md en bewijs/q1-F123-deltadiff-v1.patch, q1-F123-red-v1.log, q1-coordinator-v2.json/.log. Nieuw rood15failed/156passed; nieuw groen171passed. Coördinator herhaalde alle171 en Ruff/Black, exit0, bronhashes voor/na gelijk. Hergebruik dit bewijs waar geldig.

Opdracht beperkt tot jouw drie bevestigde bevindingen en hun doorwerking:
F1 processlot vóór stand/ruimtelezen en tot bewijsafronding; tweede proces doet nul transport, slot blijft staan.
F2 hold-out p95≤90000 als bevroren criterium; ontbrekende/ongeldige metingen blokkeren; grens exact getest.
F3 bundel/resultaat vóór succesvolle fase_einde; opslagfalen sluit fase als mislukt of open; vervolgfase doet nul calls. Beide artefactfouten en grootboekfout zijn getest.

Controleer zelfstandig of de concrete correcties jouw probes werkelijk afdekken. Pas alleen tijdelijke eigen probes aan als nodig; bestaande dossierprobe blijft behouden. Geen nieuwe algemene review van ongewijzigde delen, modelmeting of mutatietestronde. Uitvoerder noemt onder andere geen directory-fsync en POSIX-only: beoordeel alleen hun concrete relevantie voor de afgesproken duurzaamheids-/foutclaims, geen hypothetische verbreding.

Goldset-voorbereiding NIET lezen; echte cases zijn niet in reviewroot. Geen netwerk/productiedata, stage/commit/merge/activering. Gebruik offline-bootstrap voor alle probes; providerkeys neutraal.

Rapporteer per F1/F2/F3 gesloten of nog open met bewijs. Nieuwe door de correctie ontstane concrete bevindingen ook met locatie/trace en kleinste herstel. Bronhashes vóór/na moeten gelijk blijven. De laatste tekst wordt opgeslagen als U/q1-codex-herreview-v1.md.

