# cowork-toegang-v1.md — geverifieerde toegang en hashes

Auteur: Claude Cowork (afzonderlijke ESS-04-onderzoekssessie). Datum: 18 september 2026.
Status: feitelijke toegangsverantwoording. Bevat geen onderzoeksconclusies.

## 1. Werkelijke padmapping Mac -> Cowork

| Laag | Pad |
|---|---|
| Mac (host, door Chris gedeeld) | `/Users/chrislehnen/.codex/worktrees/6ff5/Definitie-app/docs/analyses/def606-regeldossiers/ESS-04-verdieping/onderzoek-20260918/cowork-uitwisseling/` |
| Cowork-shell op de Mac (`device_bash`) | `$HOME/mnt/cowork-uitwisseling/` |
| Cowork-cloudcontainer | geen mount; de cloudcontainer heeft deze map niet. Alle lees- en schrijfacties lopen via de shell op de Mac. |

Feitelijk aangetoond, niet geplakt: de map is gelist, elk bestand is gelezen en elke hash is ter plaatse herberekend.
Alleen deze ene map is gemount; de projectmap `/Users/chrislehnen/.codex/worktrees/6ff5/Definitie-app` zelf is **niet** bereikbaar. Buiten `cowork-uitwisseling/` is niets leesbaar.

## 2. Omvang van het pakket

- Bestanden: 135
- Totale omvang: 2.12 MB
- Topniveau: `LEES-EERST.md`, `startstatus-v3.md`, `cowork-opdracht-v1.md`, `feitenbasis-aanvulling-v2.md`, `bronnen/`, `feitenbasis/`, `werkboom/`, `werkboom-4cdb8ea43/`, twee werkboommanifesten.

## 3. Hashcontrole werkboom-4cdb8ea43 (actuele bevroren codebasis)

Commit in manifest: `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`.

| # | Pad | SHA-256 (herberekend) | Oordeel |
|---|---|---|---|
| 1 | `config/toetsregels/toetsregels_config.yaml` | `7a7bcb7b287ac533f51ef0242305e7fb30a5b9e90f2d14b1748daa1abff95e41` | GELIJK |
| 2 | `src/toetsregels/manager.py` | `8c8807bc7cd565c6a1f7d3632f4a256e8d5f7419a91ac3adbee6150b8032d3d6` | GELIJK |
| 3 | `src/toetsregels/rule_cache.py` | `32966b1b3c9e0cc60f844a976806141a8cb1f9195bb57222a1ba6d39c6ca3120` | GELIJK |
| 4 | `src/toetsregels/cached_manager.py` | `6ff2a795f270570a739d8343318bd55d5fec3e25fa7ae89505138b4d1a6bd3c4` | GELIJK |
| 5 | `src/toetsregels/runtime_contract.py` | `939437299a72cc633df8a229b90d151aa3310929e8418b9cfca08161215e8807` | GELIJK |
| 6 | `src/services/validation/evaluators/judgment_review.py` | `cd1558eef653f93267dfa5121651f34a78b347458e25fcff59017ea775bbfe15` | GELIJK |
| 7 | `src/services/validation/evaluators/base.py` | `638481fd50eea860d8b493a4e40ca5156944641ed7e1cb9e891303098331817d` | GELIJK |
| 8 | `src/services/validation/modular_validation_service.py` | `33c5de5482164a9e2aea3be5a449f65576f733f25cf8dbc8c4a50ecb760e0919` | GELIJK |
| 9 | `src/services/validation/types.py` | `96fcba329d88910d9942a96c648b7c1427fdb1d76b7c1a53117eea82849ad41d` | GELIJK |
| 10 | `src/services/validation/mappers.py` | `17f19baa4fd972586cc9c0acaaae54f7fdf0a5de4eaab126a037e620a3053fc4` | GELIJK |
| 11 | `src/services/validation/interfaces.py` | `62bce2c79dec19a56546428c860ce285580ae1bd6f7dd4878720b0629c5027a8` | GELIJK |
| 12 | `src/services/orchestrators/validation_orchestrator_v2.py` | `6c22ae0394697119c7a22e03a3e8391edde9154ca9aaaa1dfcc23cbfba542bd5` | GELIJK |
| 13 | `src/services/orchestrators/definition_orchestrator_v2.py` | `e970830fb73bb7cf5a3b9d43a4da1e31539abf9a7a41aa6fe99accba300b56f9` | GELIJK |
| 14 | `src/services/prompts/modules/json_based_rules_module.py` | `c9e51dd7ec844c073baa5c5ac2408f9718f0d7e073cd83b2163ef0ed8677598e` | GELIJK |
| 15 | `src/services/cleaning_service.py` | `b543f964e7dab496cd664b38ca5e6a485796302fa89ef3ab1052cb15f4cb8005` | GELIJK |
| 16 | `src/opschoning/opschoning.py` | `48c79e39207cd16f85d511d2b6fa3b81e4b739dcfc0c04f1142d38d96499cdc5` | GELIJK |
| 17 | `src/opschoning/opschoning_enhanced.py` | `9579fcafc875a4b8600a3d4de16c8526b8b099ca6eba61c0e2e76de897207acc` | GELIJK |
| 18 | `src/ui/components/expert_review_tab.py` | `0468c8c423b6543099103a15d1276d959c506d6e7aad518c02bde466b35afc31` | GELIJK |
| 19 | `src/ui/components/validation_renderer.py` | `7b1a876d6d6254eb68af7b5e81b6d4e2846a80fe117f1ff559afd8ab81f6c545` | GELIJK |
| 20 | `src/ui/components/validation_view.py` | `624989255867557cf14584b7a85906f085316769bc949669f55fa9c50965532b` | GELIJK |
| 21 | `src/services/definition_workflow_service.py` | `5e17dffc6f458f05449d655f9a4604a503d44f3f542a8749a1a01863955622a2` | GELIJK |
| 22 | `src/services/export_service.py` | `0d7607a19c3ffe920d396744b2d101043405f48d83e192bceb427d070876cf31` | GELIJK |
| 23 | `src/database/schema.sql` | `a92c2344bc8e2a7e7a3919811b21524e34d2d5a65e5a822a74bae999cc4cdd08` | GELIJK |
| 24 | `src/services/definition_repository.py` | `a42e227c4077fd7dd570edf3a3d4cdd3ca14c5536aed342f3efe1c915c495ee0` | GELIJK |
| 25 | `src/ui/components/definition_edit_tab.py` | `eea833b998d9023c5a4e5a25b12c2d525976305203f041fd25bb1f83ade1e877` | GELIJK |
| 26 | `src/toetsregels/regels/ESS-04.json` | `78537a76b454e1c652a1601b1804abdf3b28092f88547de3fea9c410d91a389c` | GELIJK |
| 27 | `src/toetsregels/regels/ESS-01.json` | `ce30d0aa3b40701ff1398f8e17e54bacfe08b2a240f93a82bea3b45ace13c446` | GELIJK |
| 28 | `src/toetsregels/regels/ESS-02.json` | `6e05bf3e84c80204bd29dd5aa165901539d9d6594b741bd3eed3153c1abfe805` | GELIJK |
| 29 | `src/toetsregels/regels/ESS-03.json` | `a5a177dea23b6348ace90ab1be914680b7394235ca9e6cc8d5ab1af01f61643a` | GELIJK |
| 30 | `src/toetsregels/regels/ESS-05.json` | `5f50bbcfe7f8908100133878e8b7f7e37269c7730e0cd0166807356e3e91ef81` | GELIJK |
| 31 | `src/toetsregels/regels/ARAI-03.json` | `86ae6c76610b35bfcb337d036533a3f21c799ff2ba1ddd89f873fc1c44099a5f` | GELIJK |
| 32 | `src/toetsregels/regels/CON-01.json` | `8b671ff75b6ea668618499202de1751d7be71fde00caa0a31ab07a32a22897b9` | GELIJK |
| 33 | `src/toetsregels/regels/CON-02.json` | `1b59b4706d7d86ab573f9437344e30f569db8fc240e06577c8fcfee03666edd4` | GELIJK |

Resultaat: 33 van 33 bestanden aanwezig, leesbaar en hashgelijk. Geen afwijking, geen ontbrekend bestand, geen bestand buiten het manifest.

## 4. Hashcontrole werkboom (oudere vergelijkingsbasis)

Commit in manifest: `50d0770ded6f4e8337738126d6bc2aa8f169e3de`.

- Aanwezig en hashgelijk: 35 van 36.
- Hashafwijkend: 0.
- **Ontbrekend, wel in manifest genoemd:** `src/services/import_service.py`.

Het manifest van de oudere werkboom noemt `src/services/import_service.py`, maar dat bestand is niet aanwezig.
Bovendien noemt het actuele manifest `werkboom-4cdb8ea43-manifest-v1.json` dit bestand in het geheel niet.
**Gevolg voor het onderzoek:** de ingang *import* uit de Q4-lijst (generatie, alleen toetsen, import, bewerken, review, conceptopslag, vaststelling, export/herbeoordeling) heeft geen codeleesbasis.
Claims over importgedrag worden daarom uitdrukkelijk als niet-bewezen gemarkeerd. Dit is de eerste gerichte nalevering die ik opvraag.

Ter vergelijking: extra bestanden die alleen in de oudere werkboom staan en niet in de actuele snapshot zitten:
`.claude/rules/patterns.md` en `tests/unit/validation/test_v2_golden_ess_more.py`. Die zijn gelezen als historische vergelijking, niet als actuele codeclaim.

## 5. Hashcontrole feitenbasis (historische dossiers en actieve skills)

`feitenbasis/bestanden-v1.json` bindt 36 bronkopieën aan hun oorspronkelijke Mac-pad.
Alle 36 kopieën zijn aanwezig, leesbaar en hashgelijk: ja. Geen ontbrekend bestand.

Let op één bronfeit: de `source`-paden in dit bestand verwijzen naar `/Users/chrislehnen/Projecten/Definitie-app/...`, dus de **historische oorspronkelijke projectmap**, terwijl de werkbomen uit de worktree `/Users/chrislehnen/.codex/worktrees/6ff5/Definitie-app` komen. Historische dossiers en actuele code komen dus uit verschillende mappen; ik houd die versies gescheiden.

## 6. Gelezen bronnen in `bronnen/`

| Bestand | SHA-256 | Bytes |
|---|---|---|
| `besluiten-ESS02-20260918.json` | `e0fe234830132011aafac77425da57dc56817531632cf86afb15887240a2f63c` | 14068 |
| `comments-DEF-606-20260918.json` | `80385de990d7661758cd8490636d01186b4f9ede17d0a3e33e29b7511f0fac8a` | 12061 |
| `comments-DEF-745-20260918.json` | `3840fdc89039897d8870b68ef022065ce1d21c2940da2081d7c2165905e44f62` | 21168 |
| `comments-DEF-749-20260918.json` | `b5e79e942099fbd50cea80fa62468a936fd111b6b9c1905eba70fac860054815` | 3871 |
| `comments-DEF-750-20260918.json` | `3c45b9cec5ede6dc44cab36c1d171b2b8829b4f2bec06d9a46ac344dd2828c23` | 7832 |
| `comments-DEF-751-20260918.json` | `98ab1c5cf84b46b3adac9194e89e98049218319263f352e8b63d05cbd39ded20` | 25821 |
| `comments-DEF-752-20260918.json` | `b32ad8d3b639f9113d10c22d339775faf91a0ff2396cc609dca8efea9ae00c15` | 2592 |
| `comments-DEF-754-20260918.json` | `041c092eb1e98c67cb572f7b9889afa174b043b5dba791116cc32826d2929b23` | 6465 |
| `comments-DEF-767-20260918.json` | `77bdbd208486b1cdcf15fee2fa8fe972974355c859df13093d7eeb9eb28cba1b` | 36 |
| `linear-DEF-606-20260918.json` | `0a787a568a2bb9c60e587f7f64b4b68ff01ebbf2a42d89a0d54181b95b04260a` | 58840 |
| `linear-DEF-622-20260918.json` | `cb67b401b0c4b5faac22f0a4b06141bd7d1d4ae7dbfb9d25a441f5605feff3fa` | 43210 |
| `linear-DEF-624-20260918.json` | `c3a67f217d0546ec7b6e3487ccc5e57f2e1f5ccb00d43a1e866d66db524968ef` | 29271 |
| `linear-DEF-630-20260918.json` | `35eb11682e526b25ce1742e75b45637397f9080070ccdbc576354af52310fb60` | 18081 |
| `linear-DEF-638-20260918.json` | `cd53415d57d27bd7f7e6e94b968d60b6b96681bc35079e0379ec3bfd7ea6a714` | 12051 |
| `linear-DEF-743-20260918.json` | `b803c67ced871a43b0c8e1b48a83949eb2fb67973bc26906974acd185fbfe152` | 39577 |
| `linear-DEF-745-20260918.json` | `b6ccc483dc272baf80c4a29c7083f2e18cdd5c55eb05329eacab11add4bc02cf` | 17025 |
| `linear-DEF-749-20260918.json` | `5bc3e9e59d2c6a3ec71f5b2582d524cdc4c2b6f4f30712aa4529800362f25b45` | 18062 |
| `linear-DEF-750-20260918.json` | `27951a2b9b0de3b29492d42825f80b8b06cde5f307968f69165c248c702b0429` | 8377 |
| `linear-DEF-751-20260918.json` | `efdf86b63ce3a6ba676a3bb92752c3727dad0e6ee2e4e63b01fec7307054a35e` | 10647 |
| `linear-DEF-752-20260918.json` | `22fc8bc03f714a537a6521df8bf0cb5b8eca7d697d8e6f81f1430528fca00774` | 8090 |
| `linear-DEF-753-20260918.json` | `9004a6cac7bd85aa2ba4bd7ae79a7c0b1533a83e38fcd1a870ecfbc0790cb328` | 9867 |
| `linear-DEF-754-20260918.json` | `88a23c43266a87774ca2cf74a409ff3fedf1c8119975ac43f6f0d2186cba09a8` | 9466 |
| `linear-DEF-767-20260918.json` | `b6ac656467ebf33eb80e89453490dbc653d22353da5ef1fca2171fcda152f4c5` | 9997 |

Alle in `cowork-opdracht-v1.md` en `feitenbasis-aanvulling-v2.md` genoemde Linear-bronnen zijn aanwezig: DEF-767, DEF-606, DEF-622 (CON-01), DEF-743 (CON-02), DEF-745 (ESS-01), DEF-749 en DEF-750 t/m 754 (ESS-02), DEF-624, DEF-630, DEF-638, het document besluiten-ESS02 en de comments van DEF-767/606/745/749/750/751/752/754.

## 7. Wat ontbreekt of begrensd is

1. `src/services/import_service.py` — ontbreekt (zie §4). Blokkeert bewijs voor de ingang *import*.
2. De volledige projectmap op de Mac is niet gemount; ik kan geen extra codebestanden zelf opzoeken. Ontbrekende bestanden vraag ik gericht op uit commit `4cdb8ea43`.
3. Er zijn geen productiegegevens gedeeld en die zijn voor dit onderzoek ook niet nodig.
4. Er zijn geen nieuwe Codex-conclusies in deze map aanwezig; ik heb er dus ook geen gelezen. Mijn eerste versie is onafhankelijk.
5. De actieve skills in `feitenbasis/actieve-skills/` zijn onderzoeksmateriaal, geen normbron; zo behandel ik ze.

## 8. Naleving van de grenzen

Ik schrijf uitsluitend nieuwe bestanden in deze map. Ik heb geen bestaand bestand gewijzigd of verwijderd, niets extern gedeeld, geen productcode, database of actieve skill aangeraakt, geen issue of PR gemaakt en geen extra sessie of agent gestart.

## 9. Volgende actie

Direct doorgaan met het volledige onafhankelijke onderzoek Q1-Q6, G/T/H, veldrollen, de veertien dossieronderdelen en de acceptatiegevallen, en dat opslaan als `cowork-onderzoek-v1.md` vóór ontvangst van nieuwe Codex-conclusies.
