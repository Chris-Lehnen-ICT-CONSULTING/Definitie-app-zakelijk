"""De migratie mag geen kolom laten verdwijnen (DEF-672).

`migrate_database()` bouwt de tabel `definities` opnieuw op om de deprecated
kolom `voorkeursterm_is_begrip` te verwijderen. Die rebuild gebruikt
`DEFINITIES_TABLE_SQL` plus een expliciete `INSERT … SELECT`-kolomlijst — en
`generation_prompt_data` ontbrak in beide. De kolom werd dus stil weggegooid,
mét inhoud.

Gemeten op een tijdelijke kopie van de echte database:

- vóór migratie: kolom aanwezig, 56 gevulde waarden;
- ná `migrate_database()`: kolom verdwenen;
- de nieuwe NOCASE-index was wél aangemaakt.

Het defect is ouder dan deze PR — `DEFINITIES_TABLE_SQL` heeft de kolom ook op
`main` niet — maar het werd pas gevaarlijk toen de NOCASE-index een reden gaf om
`migrate_database()` daadwerkelijk te draaien. De eerdere test riep alleen
`_ensure_definities_indexes()` rechtstreeks aan en raakte het rebuild-pad dus
nooit; die valse zekerheid is hier de eigenlijke les.

Deze suite draait uitsluitend op een tijdelijke database. Nooit op
`data/definities.db`.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pytest

from database.definitie_duplicates import KANDIDATEN_INDEX, KANDIDATEN_QUERY
from database.definitie_repository import DefinitieRepository
from database.migrate_database import migrate_database

pytestmark = [pytest.mark.unit]

SENTINEL = '{"prompt": "sentinel-DEF-672", "model": "test", "tokens_used": 42}'

# Kolommen die de migratie bewust verwijdert. Alleen deze mogen ontbreken; elke
# andere verdwenen kolom is dataverlies.
BEWUST_VERWIJDERD = {
    "definities": {"voorkeursterm_is_begrip"},
    "definitie_voorbeelden": {"is_voorkeursterm"},
}


def _kolommen(pad: str, tabel: str) -> set[str]:
    with sqlite3.connect(pad) as conn:
        return {rij[1] for rij in conn.execute(f"PRAGMA table_info({tabel})")}


def _triggers(pad: str, tabel: str = "definities") -> set[str]:
    with sqlite3.connect(pad) as conn:
        return {
            rij[0]
            for rij in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                (tabel,),
            )
        }


def _indexen(pad: str, tabel: str = "definities") -> set[str]:
    with sqlite3.connect(pad) as conn:
        return {
            rij[0]
            for rij in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
                (tabel,),
            )
        }


def _schemaobjecten(pad: str) -> set[tuple[str, str]]:
    with sqlite3.connect(pad) as conn:
        return {
            (rij[0], rij[1])
            for rij in conn.execute(
                "SELECT type, name FROM sqlite_master "
                "WHERE type IN ('table','index','trigger','view') "
                "AND name NOT LIKE 'sqlite_%'"
            )
        }


def _rijen(pad: str, tabel: str = "definities") -> int:
    with sqlite3.connect(pad) as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0])


def _sentinel(pad: str) -> str | None:
    with sqlite3.connect(pad) as conn:
        rij = conn.execute(
            "SELECT generation_prompt_data FROM definities WHERE begrip = ?",
            ("besluit",),
        ).fetchone()
    return rij[0] if rij else None


def _pragmas(pad: str) -> dict[str, int]:
    with sqlite3.connect(pad) as conn:
        return {
            naam: int(conn.execute(f"PRAGMA {naam}").fetchone()[0])
            for naam in ("foreign_keys", "legacy_alter_table")
        }


def _injecteer_fout(monkeypatch, doelwit: str) -> None:
    """Laat één migratiestap falen met een echte SQLite-fout.

    Voor `herstel-ddl` wordt niet de hele functie vervangen maar één bewaarde
    DDL onbruikbaar gemaakt. Dat raakt de foutafhandeling *binnen*
    `_herstel_afhankelijke_objecten` — een injectie die de functie zelf
    vervangt zou nooit merken dat die functie haar fouten slikt.
    """
    import database.migrate_database as md

    if doelwit == "herstel-ddl":
        origineel = md._bewaar_afhankelijke_objecten

        def _met_kapotte_ddl(conn, tabel):
            bewaard = origineel(conn, tabel)
            return [*bewaard, "CREATE INDEX dit is geen geldige ddl"]

        monkeypatch.setattr(md, "_bewaar_afhankelijke_objecten", _met_kapotte_ddl)
        return

    if doelwit == "datakopie":
        # Laat de INSERT … SELECT falen. De kopieerlijst wordt gefilterd op wat
        # de óude tabel heeft, dus een verzonnen naam valt weg; een kolom die
        # wél in de oude maar niet in de nieuwe tabel zit breekt de INSERT echt.
        monkeypatch.setattr(
            md,
            "DEFINITIES_KOLOMMEN",
            (*md.DEFINITIES_KOLOMMEN, "voorkeursterm_is_begrip"),
        )
        return

    def _klapt(*args, **kwargs):
        raise sqlite3.OperationalError(f"geïnjecteerde fout in {doelwit}")

    monkeypatch.setattr(md, doelwit, _klapt)


@pytest.fixture
def bestaande_database(tmp_path: Path) -> str:
    """Een tijdelijke database zoals een gegroeide productie-installatie.

    Het canonieke schema plus de twee deprecated kolommen die de rebuild moet
    opruimen. Zonder die kolommen slaat `migrate_database()` het rebuild-pad
    over en toetst deze suite niets.
    """
    pad = tmp_path / "bestaand.db"
    DefinitieRepository(str(pad))

    with sqlite3.connect(str(pad)) as conn:
        conn.execute(
            "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
        )
        conn.execute(
            "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
        )
        conn.execute(
            """
            INSERT INTO definities
                (begrip, definitie, categorie, organisatorische_context,
                 juridische_context, wettelijke_basis, status,
                 generation_prompt_data)
            VALUES (?, ?, 'type', '["DJI"]', '["strafrecht"]', '["Awb"]', 'draft', ?)
            """,
            ("besluit", "besluit: een schriftelijke beslissing", SENTINEL),
        )
    return str(pad)


class TestOpzetKlopt:
    """Zonder deze controles bewijst de rest niets."""

    def test_de_kolom_bestaat_en_is_gevuld_voor_de_migratie(self, bestaande_database):
        assert "generation_prompt_data" in _kolommen(bestaande_database, "definities")
        with sqlite3.connect(bestaande_database) as conn:
            waarde = conn.execute(
                "SELECT generation_prompt_data FROM definities WHERE begrip = ?",
                ("besluit",),
            ).fetchone()[0]
        assert waarde == SENTINEL

    def test_het_rebuild_pad_wordt_daadwerkelijk_geraakt(self, bestaande_database):
        # De rebuild draait alleen als de deprecated kolom er nog is. Ontbreekt
        # die, dan slaat de migratie het pad over en meet deze suite niets.
        assert "voorkeursterm_is_begrip" in _kolommen(bestaande_database, "definities")


class TestMigratieBehoudtData:
    @pytest.fixture
    def na_migratie(self, bestaande_database):
        voor = {
            tabel: _kolommen(bestaande_database, tabel)
            for tabel in ("definities", "definitie_voorbeelden")
        }
        assert migrate_database(bestaande_database) is True
        na = {
            tabel: _kolommen(bestaande_database, tabel)
            for tabel in ("definities", "definitie_voorbeelden")
        }
        return bestaande_database, voor, na

    def test_de_kolom_overleeft_de_migratie(self, na_migratie):
        _, _, na = na_migratie
        assert (
            "generation_prompt_data" in na["definities"]
        ), "generation_prompt_data is door de rebuild weggegooid"

    def test_de_inhoud_overleeft_de_migratie(self, na_migratie):
        pad, _, _ = na_migratie
        with sqlite3.connect(pad) as conn:
            waarde = conn.execute(
                "SELECT generation_prompt_data FROM definities WHERE begrip = ?",
                ("besluit",),
            ).fetchone()[0]
        assert (
            waarde == SENTINEL
        ), "de kolom bestaat maar de inhoud is niet meegekopieerd"

    @pytest.mark.parametrize("tabel", ["definities", "definitie_voorbeelden"])
    def test_alleen_bewust_verwijderde_kolommen_verdwijnen(self, na_migratie, tabel):
        _, voor, na = na_migratie
        verdwenen = voor[tabel] - na[tabel]
        onverwacht = verdwenen - BEWUST_VERWIJDERD[tabel]
        assert (
            not onverwacht
        ), f"{tabel}: kolommen stil verdwenen bij de migratie: {sorted(onverwacht)}"

    @pytest.mark.parametrize("tabel", ["definities", "definitie_voorbeelden"])
    def test_de_deprecated_kolom_is_echt_verwijderd(self, na_migratie, tabel):
        # De tegenhanger: de migratie moet zijn eigen werk wél doen, anders zou
        # "niets verdwenen" trivialiter waar zijn.
        _, _, na = na_migratie
        assert not (BEWUST_VERWIJDERD[tabel] & na[tabel]), na[tabel]

    def test_de_rij_blijft_bestaan(self, na_migratie):
        pad, _, _ = na_migratie
        with sqlite3.connect(pad) as conn:
            aantal = conn.execute(
                "SELECT COUNT(*) FROM definities WHERE begrip = ?", ("besluit",)
            ).fetchone()[0]
        assert aantal == 1


class TestMigratieBehoudtSchemaobjecten:
    """De rebuild sloopte meer dan alleen een kolom.

    `ALTER TABLE … RENAME` laat indexen én viewdefinities meeverhuizen naar
    `definities_old`. De `CREATE INDEX IF NOT EXISTS` die daarna volgt is dus
    een no-op — de naam is bezet — en `DROP TABLE definities_old` neemt alle
    indexen mee. De views blijven achter met een verwijzing naar een tabel die
    niet meer bestaat.

    Beide gaten zijn ouder dan deze PR en gemeten op zowel `main` als deze
    branch. Ze staan hier omdat de NOCASE-index een reden geeft om
    `migrate_database()` daadwerkelijk te draaien: een migratie die de schema-
    objecten sloopt mag niet het advies zijn.
    """

    @pytest.fixture
    def gemigreerd(self, bestaande_database):
        voor = _indexen(bestaande_database)
        assert migrate_database(bestaande_database) is True
        return bestaande_database, voor

    def test_alle_bestaande_indexen_overleven(self, gemigreerd):
        pad, voor = gemigreerd
        na = _indexen(pad)
        verdwenen = voor - na
        assert (
            not verdwenen
        ), f"indexen weggevallen bij de migratie: {sorted(verdwenen)}"

    def test_er_blijven_ueberhaupt_indexen_over(self, gemigreerd):
        # Zonder deze assert zou "niets verdwenen" ook waar zijn als er vooraf
        # al niets stond.
        pad, _ = gemigreerd
        assert len(_indexen(pad)) >= 6, _indexen(pad)

    def test_alle_triggers_overleven(self, gemigreerd):
        """Triggers verhuizen net als indexen mee met de hernoemde tabel.

        `_ensure_definities_indexes` maakt alleen indexen opnieuw aan, dus
        zonder expliciet herstel verdwijnen de triggers zonder spoor — en
        `update_definities_timestamp` houdt `updated_at` bij.
        """
        pad, _ = gemigreerd
        assert _triggers(pad) >= {
            "update_definities_timestamp",
            "log_definitie_changes",
        }, _triggers(pad)

    def test_de_timestamptrigger_werkt_nog(self, gemigreerd):
        # Bestaan is niet genoeg: de trigger moet ook vuren op de nieuwe tabel.
        pad, _ = gemigreerd
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "UPDATE definities SET updated_at = '2000-01-01 00:00:00' "
                "WHERE begrip = ?",
                ("besluit",),
            )
            conn.execute(
                "UPDATE definities SET definitie = ? WHERE begrip = ?",
                ("besluit: een gewijzigde beslissing", "besluit"),
            )
            bijgewerkt = conn.execute(
                "SELECT updated_at FROM definities WHERE begrip = ?", ("besluit",)
            ).fetchone()[0]
        assert not str(bijgewerkt).startswith(
            "2000-01-01"
        ), "update_definities_timestamp vuurt niet meer na de rebuild"

    @pytest.mark.parametrize(
        "view",
        ["actieve_definities", "vastgestelde_definities", "definitie_statistieken"],
    )
    def test_de_views_blijven_bevraagbaar(self, gemigreerd, view):
        pad, _ = gemigreerd
        with sqlite3.connect(pad) as conn:
            conn.execute(f"SELECT * FROM {view} LIMIT 1").fetchall()

    def test_geen_verwijzing_naar_de_oude_tabel(self, gemigreerd):
        pad, _ = gemigreerd
        with sqlite3.connect(pad) as conn:
            resten = [
                rij[0]
                for rij in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE sql LIKE '%definities_old%'"
                )
            ]
        assert not resten, f"objecten verwijzen nog naar definities_old: {resten}"


class TestMigratieLevertDeIndex:
    """De reden om de migratie te draaien moet ook echt landen."""

    @pytest.fixture
    def gemigreerd(self, bestaande_database):
        assert migrate_database(bestaande_database) is True
        return bestaande_database

    def test_de_nocase_index_bestaat(self, gemigreerd):
        with sqlite3.connect(gemigreerd) as conn:
            namen = {
                rij[0]
                for rij in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND tbl_name='definities'"
                )
            }
        assert KANDIDATEN_INDEX in namen, sorted(namen)

    def test_de_productiequery_gebruikt_die_index(self, gemigreerd):
        with sqlite3.connect(gemigreerd) as conn:
            plan = list(
                conn.execute(
                    "EXPLAIN QUERY PLAN " + KANDIDATEN_QUERY, ("besluit", 0, 10)
                )
            )
        tekst = " ".join(str(rij[3]) for rij in plan)
        assert "SCAN definities" not in tekst, f"volledige tabelscan: {tekst}"
        assert KANDIDATEN_INDEX in tekst, tekst

    def test_migratie_is_herhaalbaar(self, gemigreerd):
        # Tweede keer draaien mag niets kapotmaken en niets verliezen.
        assert migrate_database(gemigreerd) is True
        assert "generation_prompt_data" in _kolommen(gemigreerd, "definities")
        with sqlite3.connect(gemigreerd) as conn:
            waarde = conn.execute(
                "SELECT generation_prompt_data FROM definities WHERE begrip = ?",
                ("besluit",),
            ).fetchone()[0]
        assert waarde == SENTINEL


class TestFoutpadIsAtomair:
    """Een mislukte migratie mag niets slopen en nooit succes melden.

    Gemeten vóór deze reparatie, met een `OperationalError` in
    `_create_definities_table()`: `migrate_database()` gaf **True**, `definities`
    bestond niet meer, alleen `definities_old` restte, en de sentineldata stond
    nog uitsluitend in die oude tabel.

    Drie oorzaken: de rebuild ving fouten af met een warning en ging door,
    `executescript()` committe de voorafgaande rename impliciet, en het herstel
    van indexen en triggers slikte zijn eigen fouten.
    """

    INJECTIES = [
        pytest.param("_create_definities_table", id="CREATE van de nieuwe tabel"),
        pytest.param("herstel-ddl", id="herstel van een index/trigger"),
        pytest.param("datakopie", id="datakopie"),
    ]

    @pytest.fixture
    def voor_toestand(self, bestaande_database):
        pad = bestaande_database
        return {
            "kolommen": _kolommen(pad, "definities"),
            "indexen": _indexen(pad),
            "triggers": _triggers(pad),
            "objecten": _schemaobjecten(pad),
            "rijen": _rijen(pad),
            "sentinel": _sentinel(pad),
            "pragmas": _pragmas(pad),
        }

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_mislukte_migratie_meldt_geen_succes(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        _injecteer_fout(monkeypatch, doelwit)
        assert (
            migrate_database(bestaande_database) is False
        ), f"migratie meldde succes terwijl {doelwit} faalde"

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_de_data_blijft_volledig_intact(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        _injecteer_fout(monkeypatch, doelwit)
        migrate_database(bestaande_database)

        pad = bestaande_database
        assert _kolommen(pad, "definities") == voor_toestand["kolommen"]
        assert _rijen(pad) == voor_toestand["rijen"]
        assert _sentinel(pad) == voor_toestand["sentinel"] == SENTINEL

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_de_schemaobjecten_blijven_intact(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        _injecteer_fout(monkeypatch, doelwit)
        migrate_database(bestaande_database)

        pad = bestaande_database
        assert _indexen(pad) >= voor_toestand["indexen"]
        assert _triggers(pad) >= voor_toestand["triggers"]
        verdwenen = voor_toestand["objecten"] - _schemaobjecten(pad)
        assert (
            not verdwenen
        ), f"schemaobjecten verdwenen bij een mislukte migratie: {verdwenen}"

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_geen_tijdelijke_tabellen_blijven_staan(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        _injecteer_fout(monkeypatch, doelwit)
        migrate_database(bestaande_database)

        with sqlite3.connect(bestaande_database) as conn:
            tabellen = {
                rij[0]
                for rij in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        resten = {naam for naam in tabellen if naam.endswith(("_old", "_old2"))}
        assert not resten, f"tijdelijke rebuild-tabellen blijven staan: {resten}"

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_de_views_blijven_werken(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        _injecteer_fout(monkeypatch, doelwit)
        migrate_database(bestaande_database)

        with sqlite3.connect(bestaande_database) as conn:
            for view in (
                "actieve_definities",
                "vastgestelde_definities",
                "definitie_statistieken",
            ):
                conn.execute(f"SELECT * FROM {view} LIMIT 1").fetchall()

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_pragmas_zijn_hersteld(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        # `foreign_keys` en `legacy_alter_table` horen terug op hun
        # oorspronkelijke waarde, ook als de rebuild halverwege afbreekt.
        _injecteer_fout(monkeypatch, doelwit)
        migrate_database(bestaande_database)
        assert _pragmas(bestaande_database) == voor_toestand["pragmas"]

    @pytest.mark.parametrize("doelwit", INJECTIES)
    def test_de_database_blijft_consistent(
        self, bestaande_database, voor_toestand, monkeypatch, doelwit
    ):
        _injecteer_fout(monkeypatch, doelwit)
        migrate_database(bestaande_database)

        with sqlite3.connect(bestaande_database) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    def test_een_mislukte_migratie_is_daarna_alsnog_uitvoerbaar(
        self, bestaande_database, monkeypatch
    ):
        # De sluitsteen: na een rollback moet een tweede, ongestoorde poging
        # gewoon slagen. Anders zou "niets kapot" nog steeds een doodlopende
        # database kunnen betekenen.
        _injecteer_fout(monkeypatch, "_create_definities_table")
        assert migrate_database(bestaande_database) is False
        monkeypatch.undo()
        assert migrate_database(bestaande_database) is True
        assert "generation_prompt_data" in _kolommen(bestaande_database, "definities")
        assert _sentinel(bestaande_database) == SENTINEL


class TestSuccesIsGemetenNietAangenomen:
    """`migrate_database()` mag alleen True melden als de uitkomst klopt.

    Een migratie kan zonder uitzondering aflopen en tóch een halve database
    achterlaten. De eindverificatie controleert daarom de werkelijke toestand:
    geen verdwenen schemaobjecten, geen tijdelijke tabellen, de vereiste index
    aanwezig, en `foreign_key_check` en `integrity_check` schoon.
    """

    def test_ontbrekende_index_levert_geen_succes(
        self, bestaande_database, monkeypatch
    ):
        import database.migrate_database as md

        # Een database van vóór DEF-672 heeft de NOCASE-index nog niet, dus
        # `_ensure_definities_indexes` is dan de énige bron. Zonder die stap
        # loopt de migratie zonder uitzondering af en zou zij zonder
        # eindverificatie succes melden.
        with sqlite3.connect(bestaande_database) as conn:
            conn.execute(f"DROP INDEX IF EXISTS {KANDIDATEN_INDEX}")
        monkeypatch.setattr(md, "_ensure_definities_indexes", lambda conn: None)

        assert (
            migrate_database(bestaande_database) is False
        ), "migratie meldde succes terwijl de vereiste index ontbreekt"

    def test_achtergebleven_tijdelijke_tabel_levert_geen_succes(
        self, bestaande_database, monkeypatch
    ):
        import database.migrate_database as md

        origineel = md._rebuild_tabel_atomair

        def _laat_rest_achter(conn, **kwargs):
            origineel(conn, **kwargs)
            conn.execute("CREATE TABLE IF NOT EXISTS definities_old (id INTEGER)")

        monkeypatch.setattr(md, "_rebuild_tabel_atomair", _laat_rest_achter)
        assert migrate_database(bestaande_database) is False

    def test_de_ongestoorde_migratie_meldt_wel_succes(self, bestaande_database):
        # De tegenhanger: zonder deze assert zou een verificatie die altijd
        # faalt ook "geslaagd" lijken in de tests hierboven.
        assert migrate_database(bestaande_database) is True


class TestNormalisatiefoutMeldtGeenSucces:
    def test_falende_normalisatie_levert_false(self, bestaande_database, monkeypatch):
        _injecteer_fout(monkeypatch, "_normalize_wettelijke_basis")
        assert migrate_database(bestaande_database) is False

    def test_data_blijft_intact_bij_normalisatiefout(
        self, bestaande_database, monkeypatch
    ):
        voor = _rijen(bestaande_database)
        _injecteer_fout(monkeypatch, "_normalize_wettelijke_basis")
        migrate_database(bestaande_database)
        assert _rijen(bestaande_database) == voor
        assert _sentinel(bestaande_database) == SENTINEL


class TestSchemaDefinitiesLopenNietUiteen:
    """`schema.sql` en `DEFINITIES_TABLE_SQL` beschrijven dezelfde tabel.

    Lopen die twee uiteen, dan verliest de rebuild precies het verschil — wat
    hier gebeurde. Deze test vangt de volgende afwijking meteen af, in plaats
    van pas nadat er data weg is.
    """

    def test_kolomsets_zijn_gelijk(self, tmp_path):
        from database.migrate_database import DEFINITIES_TABLE_SQL

        vers = tmp_path / "vers.db"
        DefinitieRepository(str(vers))
        uit_schema = _kolommen(str(vers), "definities")

        uit_migratie_pad = tmp_path / "uit_migratie.db"
        with sqlite3.connect(str(uit_migratie_pad)) as conn:
            conn.executescript(DEFINITIES_TABLE_SQL.format(table_name="definities"))
        uit_migratie = _kolommen(str(uit_migratie_pad), "definities")

        assert uit_schema == uit_migratie, (
            f"alleen in schema.sql: {sorted(uit_schema - uit_migratie)} · "
            f"alleen in DEFINITIES_TABLE_SQL: {sorted(uit_migratie - uit_schema)}"
        )


def _tabel_ddl(pad: str, tabel: str) -> str:
    with sqlite3.connect(pad) as conn:
        return conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tabel,)
        ).fetchone()[0]


@pytest.fixture
def database_met_fk_naar_definities_old(tmp_path: Path) -> str:
    """Synthetische fixture met uitsluitend de DEF-688-preconditie.

    Dit is géén volledige pre-DEF-672-database. Alleen de FK-clausule van
    `definitie_voorbeelden` wijst hier naar `definities_old`, aangebracht met
    `writable_schema` zonder data, indexen of triggers te raken. Een echte
    rename van vóór DEF-672 besmette meer verwijzende tabellen tegelijk; die
    staan hier bewust canoniek.
    """
    pad = tmp_path / "pre_def672.db"
    DefinitieRepository(str(pad))
    with sqlite3.connect(str(pad)) as conn:
        conn.executescript(
            "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER;"
            "INSERT INTO definities (begrip, definitie, categorie,"
            " organisatorische_context, juridische_context, wettelijke_basis, status)"
            " VALUES ('besluit', 'besluit: een schriftelijke beslissing', 'type',"
            " '[\"DJI\"]', '[\"strafrecht\"]', '[\"Awb\"]', 'draft');"
            "INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type,"
            " voorbeeld_tekst) SELECT id, 'sentence', 'Het besluit is genomen.'"
            " FROM definities;"
            "PRAGMA writable_schema=ON;"
            "UPDATE sqlite_master SET sql = replace(sql, 'REFERENCES definities(id)',"
            " 'REFERENCES definities_old(id)') WHERE type='table'"
            " AND name='definitie_voorbeelden';"
            "PRAGMA writable_schema=OFF;"
        )
    return str(pad)


class TestStap1HersteltDeFkNaarDefinitiesOld:
    """Stap 1 herstelt een FK van `definitie_voorbeelden` naar `definities_old` (DEF-688).

    Deze test simuleert géén volledige pre-DEF-672-back-up. Een echte oude
    rename besmette ook `definitie_geschiedenis`, `definitie_tags` en
    `synonym_group_members`; die historische beschadiging wordt door deze
    synthetische fixture niet nagebootst en hier dus ook niet getest — zij valt
    onder DEF-664. Bewezen wordt uitsluitend dat de rebuild in stap 1 de FK van
    `definitie_voorbeelden` terugzet — precies waarom het aparte
    `_old2`-correctiepad kon vervallen.
    """

    def test_stap_1_herstelt_de_fk(self, database_met_fk_naar_definities_old, caplog):
        pad = database_met_fk_naar_definities_old
        # Zonder een werkelijk kapotte FK vooraf bewijst de rest niets.
        assert "REFERENCES definities_old(id)" in _tabel_ddl(
            pad, "definitie_voorbeelden"
        )
        objecten_voor = _schemaobjecten(pad)
        rijen_voor = (_rijen(pad), _rijen(pad, "definitie_voorbeelden"))
        assert min(rijen_voor) >= 1, rijen_voor

        with caplog.at_level(logging.INFO, logger="database.migrate_database"):
            assert migrate_database(pad) is True

        ddl = _tabel_ddl(pad, "definitie_voorbeelden")
        assert "REFERENCES definities(id) ON DELETE CASCADE" in ddl
        assert "definities_old" not in ddl
        # Attributie: het herstel komt van de rebuild in stap 1 zelf.
        assert (
            "Rebuild 'definitie_voorbeelden' zonder kolom 'is_voorkeursterm'"
            in caplog.text
        ), f"stap 1 heeft 'definitie_voorbeelden' niet herbouwd; log: {caplog.text}"
        assert not objecten_voor - _schemaobjecten(pad)
        assert (_rijen(pad), _rijen(pad, "definitie_voorbeelden")) == rijen_voor
        assert not {
            naam
            for soort, naam in _schemaobjecten(pad)
            if soort == "table" and naam.endswith(("_old", "_old2"))
        }
        # Idempotent: tweede run laat DDL, objecten en rijaantallen ongemoeid.
        objecten_na_eerste = _schemaobjecten(pad)
        assert migrate_database(pad) is True
        assert _tabel_ddl(pad, "definitie_voorbeelden") == ddl
        assert _schemaobjecten(pad) == objecten_na_eerste
        assert (_rijen(pad), _rijen(pad, "definitie_voorbeelden")) == rijen_voor

    def test_achtergebleven_old_tabel_wordt_nog_steeds_gemeld(self, bestaande_database):
        # De `_old2`-tak verviel met het correctiepad; de `_old`-tak moet blijven.
        import database.migrate_database as md

        assert migrate_database(bestaande_database) is True
        with sqlite3.connect(bestaande_database) as conn:
            verwacht = md._schemaobjecten(conn)
            assert md._verifieer_migratie(conn, verwacht) == []
            conn.execute("CREATE TABLE definitie_voorbeelden_old (id INTEGER)")
            problemen = md._verifieer_migratie(conn, verwacht)
        assert any("definitie_voorbeelden_old" in p for p in problemen), problemen
