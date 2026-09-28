# Q1 — laatste gerichte F3-herreview

Jij bent dezelfde Codex CLI-reviewer, sessie01a0e8ca-2df9-7780-ba7a-b18c26caefe7. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Geen bron/test/configwijzigingen. Dezelfde werkboom en basisf9bb9e697; alleen F3-fsync-delta en directe doorwerking controleren. F1/F2 zijn eerder gesloten, heropen die niet zonder concrete gewijzigde oorzaak.

Nieuwe bronhashes:
- scripts/analysis/def835_int02_modelproef.py:94adea36ffa555a8d9fee790f5eb96ce54ece96efd107adf25dd147ccb1a637f
- tests/unit/validation/test_def835_int02_modelproef.py:60b2c420f3b7ff80582ec4e42dda80f77c986bf351e6c538637048bc2d61b79e
- tests/fixtures/def835_int02_kwalificatie_runner.json:2f50c456756614cc35e78b81f57f4c8afc748b79d4cfcd6da053306e6c8fd7a7

Dossier U relatief docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2.
Lees q1-uitvoering-v2.md, bewijs/q1-F3-fsync-deltadiff-v1.patch en q1-F3-fsync-hashmanifest-v1.json. Volledige groene run176tests plus lint is aan deze hashes gebonden. Coördinator draaide alle8F3-tests opnieuw (8passed/168deselected), bronhashes voor/na gelijk: bewijs/q1-coordinator-v3.json/.log.

Correctie: vóór grootboekafronding blijvende <fase>-afronding.open met fsync; pas na succesvolle grootboekafronding één atomaire rename naar .voltooid. Geen extra foutgevoelige schrijfstap daarna. Nieuwe runner weigert zowel aanwezige .open als ontbrekende .voltooid vóór sleutel/transport, vooraf en onder slot. Bestanden worden niet verwijderd. Fouten op markering-fsync, grootboek-fsync ná flush en rename zijn getest, evenals normale doorloop. Geen claim van stroom-/systeemuitvalgarantie.

Controleer jouw concrete fsync-na-flush-probe tegen deze code, met verse runnerinstantie en nul vervolgcalls. Gerichte aanvullende probe alleen voor concrete doorwerking. Geen algemene review-/mutatieronde. Geen goldset lezen, netwerk, productiedata, gitstage/commit/merge of activering.

Rapporteer F3 gesloten of nog open, met bewijs en ongewijzigde hashes. Als er nog een concrete fout is, meld die nauwkeurig; coördinator gaat niet automatisch een onbeperkte vierde correctieronde in. Eindrapport wordt q1-codex-F3-eindreview-v1.md in oorspronkelijke U.

