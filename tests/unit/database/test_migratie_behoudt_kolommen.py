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


class TestGeenOnnodigeRebuild:
    """De migratie herbouwde élke run: zij voegde eerst zelf de verouderde
    kolommen toe en verwijderde die daarna weer (gemeten, DEF-664)."""

    def test_verse_canonieke_database_wordt_niet_herbouwd(self, tmp_path):
        pad = tmp_path / "vers.db"
        DefinitieRepository(str(pad))
        ddl_voor = {
            tabel: _tabel_ddl(str(pad), tabel)
            for tabel in ("definities", "definitie_voorbeelden")
        }

        assert migrate_database(str(pad)) is True

        assert {
            tabel: _tabel_ddl(str(pad), tabel)
            for tabel in ("definities", "definitie_voorbeelden")
        } == ddl_voor
        assert "voorkeursterm_is_begrip" not in _kolommen(str(pad), "definities")
        assert "is_voorkeursterm" not in _kolommen(str(pad), "definitie_voorbeelden")


class TestBackupgrensVoorDeLegacyRoute:
    def test_backup_gaat_vooraf_en_herstelt_de_toestand_van_ervoor(
        self, bestaande_database, tmp_path
    ):
        from database.sqlite_backup import create_verified_backup

        assert migrate_database(bestaande_database) is True

        backups = sorted(
            (Path(bestaande_database).parent / "backups").glob(
                "pre_legacy_migration_*.db"
            )
        )
        assert len(backups) == 1
        hersteld = tmp_path / "hersteld" / "definities.db"
        hersteld.parent.mkdir()
        create_verified_backup(backups[0], hersteld)

        # De backup is de toestand van vóór de rebuild: de verouderde kolom
        # bestaat daar nog en de sentinel staat erin.
        assert "voorkeursterm_is_begrip" in _kolommen(str(hersteld), "definities")
        assert _sentinel(str(hersteld)) == SENTINEL

    def test_zonder_kerntabel_wordt_niets_gewijzigd(self, bestaande_database):
        with sqlite3.connect(bestaande_database) as conn:
            conn.execute("DROP TABLE import_export_logs")
        voor = _schemaobjecten(bestaande_database)

        assert migrate_database(bestaande_database) is False

        assert _schemaobjecten(bestaande_database) == voor
        assert "voorkeursterm_is_begrip" in _kolommen(bestaande_database, "definities")
        assert not (Path(bestaande_database).parent / "backups").exists()


class TestVoormaligeWarningPadenFalenGesloten:
    """ADD COLUMN, backfill en indexen liepen door met alleen een warning."""

    def test_falende_synoniemenindex_levert_geen_succes(
        self, bestaande_database, monkeypatch
    ):
        import database.migrate_database as md

        monkeypatch.setattr(md, "SYNONIEMEN_INDEX_DDL", "CREATE INDEX dit is kapot")

        assert migrate_database(bestaande_database) is False
        assert _sentinel(bestaande_database) == SENTINEL

    def test_falende_backfill_laat_de_kolom_niet_half_achter(
        self, bestaande_database, monkeypatch
    ):
        import database.migrate_database as md

        with sqlite3.connect(bestaande_database) as conn:
            conn.execute("ALTER TABLE definities DROP COLUMN voorkeursterm")
        assert "voorkeursterm" not in _kolommen(bestaande_database, "definities")
        monkeypatch.setattr(
            md, "VOORKEURSTERM_BACKFILL_UIT_SYNONIEMEN_SQL", "UPDATE dit is kapot"
        )

        assert migrate_database(bestaande_database) is False

        # ADD COLUMN en backfill zijn één transactie: geen halve toestand.
        assert "voorkeursterm" not in _kolommen(bestaande_database, "definities")
        assert _sentinel(bestaande_database) == SENTINEL

    def test_falende_normalisatie_binnenin_levert_geen_succes(
        self, bestaande_database, monkeypatch
    ):
        import database.migrate_database as md

        def _klapt(raw):
            raise ValueError("geinjecteerde normalisatiefout")

        monkeypatch.setattr(md, "_normalize_list_json", _klapt)
        voor = _rijen(bestaande_database)

        assert migrate_database(bestaande_database) is False

        assert _rijen(bestaande_database) == voor
        assert _sentinel(bestaande_database) == SENTINEL


class TestHeleMigratieIsEenTransactie:
    """Rootprobe (probe-migration-atomicity): bij een afgewezen eindverificatie
    gaf de migratie False, maar de rebuild was al gecommit en de kolom
    definitief weg. ADD/backfill, rebuilds, normalisatie en eindverificatie
    moeten samen committen of samen terugrollen."""

    @pytest.fixture
    def toestand(self, bestaande_database):
        def _lees():
            return {
                "kolommen": _kolommen(bestaande_database, "definities"),
                "voorbeelden": _kolommen(bestaande_database, "definitie_voorbeelden"),
                "objecten": _schemaobjecten(bestaande_database),
                "rijen": _rijen(bestaande_database),
                "sentinel": _sentinel(bestaande_database),
                "ddl": _tabel_ddl(bestaande_database, "definities"),
                "pragmas": _pragmas(bestaande_database),
            }

        return _lees

    def test_afgewezen_eindverificatie_laat_alles_onaangeroerd(
        self, bestaande_database, toestand, monkeypatch
    ):
        import database.migrate_database as md

        voor = toestand()
        monkeypatch.setattr(
            md, "_verifieer_migratie", lambda conn, verwacht: ["injected rejection"]
        )

        assert migrate_database(bestaande_database) is False

        assert toestand() == voor
        assert "voorkeursterm_is_begrip" in _kolommen(bestaande_database, "definities")

    def test_fout_in_latere_stap_rolt_eerdere_rebuild_terug(
        self, bestaande_database, toestand, monkeypatch
    ):
        import database.migrate_database as md

        voor = toestand()

        def _klapt(raw):
            raise ValueError("geinjecteerde normalisatiefout")

        monkeypatch.setattr(md, "_normalize_list_json", _klapt)

        assert migrate_database(bestaande_database) is False

        assert toestand() == voor

    def test_commitfout_rolt_alles_terug(
        self, bestaande_database, toestand, monkeypatch
    ):
        from database import schema_contract

        voor = toestand()

        def _commit_faalt(conn):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(schema_contract, "_commit", _commit_faalt)

        assert migrate_database(bestaande_database) is False

        assert toestand() == voor

    def test_bron_die_het_profielcontract_niet_haalt_wordt_niet_gewijzigd(
        self, bestaande_database, toestand
    ):
        with sqlite3.connect(bestaande_database) as conn:
            conn.execute("DROP TRIGGER log_definitie_changes")
        voor = toestand()

        assert migrate_database(bestaande_database) is False

        assert toestand() == voor
        assert "voorkeursterm_is_begrip" in _kolommen(bestaande_database, "definities")

    def test_geslaagde_migratie_haalt_het_profielcontract(self, bestaande_database):
        from database.schema_contract import assert_startup_contract

        assert migrate_database(bestaande_database) is True

        with sqlite3.connect(bestaande_database) as conn:
            assert_startup_contract(conn)


class TestExtraKolommenOverlevenDeRebuild:
    """Rootprobe (probe-extra-column-preservation): een geldige extra kolom
    (bv. `external_reference`) verdween bij de rebuild omdat de kopieerlijst
    statisch is. Het contract laat extra kolommen toe; het bronbehoud moet ze
    dan ook werkelijk behouden — met type, default, NULL en JSON-inhoud."""

    EXTRA = {
        "definities": ("external_reference", "TEXT"),
        "definitie_voorbeelden": ("extra_json", "TEXT DEFAULT '{}'"),
    }

    @pytest.fixture
    def database_met_extra_kolommen(self, bestaande_database):
        with sqlite3.connect(bestaande_database) as conn:
            for tabel, (kolom, declaratie) in self.EXTRA.items():
                conn.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {declaratie}")
            conn.execute(
                "UPDATE definities SET external_reference = 'sentinel-extra-column' "
                "WHERE begrip = 'besluit'"
            )
            conn.execute(
                "UPDATE definities SET external_reference = NULL WHERE begrip != 'besluit'"
            )
            conn.execute(
                "INSERT INTO definitie_voorbeelden "
                "(definitie_id, voorbeeld_type, voorbeeld_tekst, extra_json) "
                "SELECT id, 'sentence', 'vb', '{\"k\": [1, null]}' FROM definities "
                "WHERE begrip = 'besluit'"
            )
        return bestaande_database

    @staticmethod
    def _kolominfo(pad: str, tabel: str) -> dict[str, tuple]:
        with sqlite3.connect(pad) as conn:
            return {
                rij[1]: (rij[2], rij[3], rij[4])
                for rij in conn.execute(f"PRAGMA table_info({tabel})")
            }

    def test_extra_kolommen_en_inhoud_overleven(self, database_met_extra_kolommen):
        pad = database_met_extra_kolommen
        info_voor = {t: self._kolominfo(pad, t) for t in self.EXTRA}

        assert migrate_database(pad) is True

        for tabel, (kolom, _) in self.EXTRA.items():
            assert kolom in _kolommen(pad, tabel), f"{tabel}.{kolom} is weggegooid"
            assert self._kolominfo(pad, tabel)[kolom] == info_voor[tabel][kolom]
        with sqlite3.connect(pad) as conn:
            waarden = conn.execute(
                "SELECT begrip, external_reference FROM definities ORDER BY begrip"
            ).fetchall()
            assert ("besluit", "sentinel-extra-column") in waarden
            assert all(w is None for b, w in waarden if b != "besluit")
            assert (
                conn.execute(
                    "SELECT extra_json FROM definitie_voorbeelden WHERE voorbeeld_tekst = 'vb'"
                ).fetchone()[0]
                == '{"k": [1, null]}'
            )
        assert _sentinel(pad) == SENTINEL
        assert "voorkeursterm_is_begrip" not in _kolommen(pad, "definities")

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param("extra_ref INTEGER REFERENCES definitie_tags(id)", id="fk"),
            pytest.param("extra_ci TEXT COLLATE NOCASE", id="collate"),
            pytest.param("extra_gen TEXT AS (begrip || '!') VIRTUAL", id="generated"),
        ],
    )
    def test_extra_kolom_met_semantiek_via_alter_faalt_gesloten(
        self, bestaande_database, declaratie
    ):
        # Rootprobe (probe-extra-unique-preservation): type/default alleen is
        # onvoldoende; FK, collatie en generated zijn semantiek die ADD COLUMN
        # in de rebuild niet reproduceert. Dan liever niets wijzigen.
        with sqlite3.connect(bestaande_database) as conn:
            conn.execute(f"ALTER TABLE definities ADD COLUMN {declaratie}")
        voor = (
            _kolommen(bestaande_database, "definities"),
            _tabel_ddl(bestaande_database, "definities"),
            _schemaobjecten(bestaande_database),
        )

        assert migrate_database(bestaande_database) is False

        assert (
            _kolommen(bestaande_database, "definities"),
            _tabel_ddl(bestaande_database, "definities"),
            _schemaobjecten(bestaande_database),
        ) == voor
        assert _sentinel(bestaande_database) == SENTINEL

    @staticmethod
    def _database_uit_schematekst(pad: Path, oud: str, nieuw: str) -> str:
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        assert tekst.count(oud) == 1, oud
        tekst = tekst.replace(oud, nieuw)
        with sqlite3.connect(str(pad)) as conn:
            conn.executescript(tekst)
            conn.execute(
                "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
            )
        return str(pad)

    @staticmethod
    def _unieke_sleutels(pad: str) -> set[tuple[str, ...]]:
        """Alle unieke sleutels op definities: UNIQUE-constraints én unique indexen."""
        with sqlite3.connect(pad) as conn:
            return {
                tuple(r[2] for r in conn.execute(f"PRAGMA index_info('{naam}')"))
                for _s, naam, uniek, _o, _p in conn.execute(
                    "PRAGMA index_list(definities)"
                )
                if uniek
            }

    @pytest.mark.parametrize(
        ("declaratie", "sleutel"),
        [
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT UNIQUE\n",
                ("external_ref",),
                id="inline",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT,\n"
                "    CONSTRAINT uq_external UNIQUE(external_ref)\n",
                ("external_ref",),
                id="benoemd",
            ),
            pytest.param(
                '    voorkeursterm TEXT,\n    external_ref TEXT,\n    UNIQUE("external_ref")\n',
                ("external_ref",),
                id="gequote",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT,\n"
                "    UNIQUE(external_ref, begrip)\n",
                ("external_ref", "begrip"),
                id="composite",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    UNIQUE(voorkeursterm)\n",
                ("voorkeursterm",),
                id="canonieke-kolom",
            ),
        ],
    )
    def test_unique_constraints_overleven_de_rebuild_met_semantiek(
        self, tmp_path, declaratie, sleutel
    ):
        # Codex-herreview P1: benoemde, gequote, composite en op-canonieke-kolom
        # UNIQUE-constraints gingen bij de rebuild stil verloren (True, geen
        # contractprobleem, dubbele waarden daarna geaccepteerd).
        pad = self._database_uit_schematekst(
            tmp_path / "uniek.db", "    voorkeursterm TEXT\n", declaratie
        )
        with sqlite3.connect(pad) as conn:
            if "external_ref" in sleutel:
                conn.execute("UPDATE definities SET external_ref = 'ref-' || id")
            conn.execute("UPDATE definities SET voorkeursterm = 'vt-' || id")
        assert sleutel in self._unieke_sleutels(pad)

        assert migrate_database(pad) is True

        assert "voorkeursterm_is_begrip" not in _kolommen(pad, "definities")
        assert sleutel in self._unieke_sleutels(pad), "UNIQUE-semantiek verdwenen"
        # Alle sleutelkolommen gelijk maken moet de uniciteit schenden.
        toewijzing = ", ".join(f"{kolom} = 'zelfde'" for kolom in sleutel)
        with sqlite3.connect(pad) as conn, pytest.raises(sqlite3.IntegrityError):
            conn.execute(f"UPDATE definities SET {toewijzing}")

    @staticmethod
    def _index_ddl(pad: str, naam: str) -> str | None:
        with sqlite3.connect(pad) as conn:
            rij = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND name=?", (naam,)
            ).fetchone()
        return None if rij is None else rij[0]

    def test_partiele_unique_index_vervangt_geen_volledige_unique(self, tmp_path):
        # Rootprobe (probe-partial-unique-equivalence): een partiële unique
        # index op dezelfde kolom gold als vervanging van de volledige UNIQUE;
        # na de rebuild bleef alleen de partiële index en werden duplicaten op
        # draft-rijen toegelaten.
        pad = self._database_uit_schematekst(
            tmp_path / "partieel.db",
            "    voorkeursterm TEXT\n",
            "    voorkeursterm TEXT,\n    external_ref TEXT UNIQUE\n",
        )
        partieel_ddl = (
            "CREATE UNIQUE INDEX custom_partial ON definities(external_ref) "
            "WHERE status='established'"
        )
        with sqlite3.connect(pad) as conn:
            conn.execute("UPDATE definities SET external_ref = 'ref-' || id")
            conn.execute(partieel_ddl)
        with sqlite3.connect(pad) as conn, pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE definities SET external_ref = 'dup', status = 'draft'")

        assert migrate_database(pad) is True

        # De volledige uniciteit geldt nog steeds, ook buiten het predicaat.
        with sqlite3.connect(pad) as conn, pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE definities SET external_ref = 'dup', status = 'draft'")
        # De partiële index zelf is via zijn volledige DDL behouden, ongewijzigd.
        assert self._index_ddl(pad, "custom_partial") == partieel_ddl

    def test_bron_met_alleen_partiele_unique_index_wordt_niet_verstrakt(self, tmp_path):
        # Tegenhanger: uitsluitend een partiële index → géén sterkere volledige
        # constraint erbij; duplicaten buiten het predicaat blijven toegestaan.
        pad = self._database_uit_schematekst(
            tmp_path / "alleen-partieel.db",
            "    voorkeursterm TEXT\n",
            "    voorkeursterm TEXT,\n    external_ref TEXT\n",
        )
        partieel_ddl = (
            "CREATE UNIQUE INDEX custom_partial ON definities(external_ref) "
            "WHERE status='established'"
        )
        with sqlite3.connect(pad) as conn:
            conn.execute("UPDATE definities SET external_ref = 'ref-' || id")
            conn.execute(partieel_ddl)
        unieke_voor = self._unieke_sleutels(pad)

        assert migrate_database(pad) is True

        assert self._index_ddl(pad, "custom_partial") == partieel_ddl
        assert self._unieke_sleutels(pad) == unieke_voor
        with sqlite3.connect(pad) as conn:
            conn.execute("UPDATE definities SET external_ref = 'dup', status = 'draft'")
            assert (
                conn.execute(
                    "SELECT COUNT(*) FROM definities WHERE external_ref = 'dup'"
                ).fetchone()[0]
                > 1
            )
            conn.rollback()

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param(
                "    voorkeursterm TEXT,\n    CHECK (begrip != '')\n", id="extra-check"
            ),
            pytest.param("    voorkeursterm TEXT COLLATE NOCASE\n", id="collate"),
            pytest.param(
                "    voorkeursterm TEXT REFERENCES definitie_tags(tag_naam)\n",
                id="extra-fk",
            ),
        ],
    )
    def test_niet_reproduceerbare_constraint_op_canonieke_kolom_faalt_gesloten(
        self, tmp_path, declaratie
    ):
        # Constraints die de rebuild niet kan nabouwen (extra CHECK, COLLATE op
        # een canonieke kolom, extra FK) mogen niet stil verdwijnen: weigeren
        # met het origineel intact.
        pad = self._database_uit_schematekst(
            tmp_path / "constraint.db", "    voorkeursterm TEXT\n", declaratie
        )
        voor = (_kolommen(pad, "definities"), _tabel_ddl(pad, "definities"))

        assert migrate_database(pad) is False

        assert (_kolommen(pad, "definities"), _tabel_ddl(pad, "definities")) == voor

    def test_niet_veilig_te_reconstrueren_extra_kolom_faalt_gesloten(self, tmp_path):
        # Een extra kolom met een CHECK kan niet via ADD COLUMN worden
        # nagebouwd: liever niets wijzigen dan de kolom stil weggooien.
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        oud = "    voorkeursterm TEXT\n"
        assert tekst.count(oud) == 1
        tekst = tekst.replace(
            oud,
            "    voorkeursterm TEXT,\n"
            "    extern_verplicht TEXT NOT NULL DEFAULT 'x' "
            "CHECK (extern_verplicht != '')\n",
        )
        pad = tmp_path / "onveilig.db"
        with sqlite3.connect(str(pad)) as conn:
            conn.executescript(tekst)
            conn.execute(
                "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
            )
        voor = (_kolommen(str(pad), "definities"), _tabel_ddl(str(pad), "definities"))

        assert migrate_database(str(pad)) is False

        assert (
            _kolommen(str(pad), "definities"),
            _tabel_ddl(str(pad), "definities"),
        ) == voor


class TestBronsemantiekDieDeRebuildNietKanNabouwen:
    """Codex-review 3: semantiek die niet in PRAGMA-metagegevens zichtbaar is
    verdween stil bij de rebuild. Alles hieronder moet óf werkelijk behouden
    blijven, óf de migratie laat de bron intact (False) — nooit een
    geslaagde migratie met ander SQL-gedrag."""

    @staticmethod
    def _bouw(pad: Path, oud: str, nieuw: str) -> str:
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        assert tekst.count(oud) == 1, oud
        with sqlite3.connect(str(pad)) as conn:
            conn.executescript(tekst.replace(oud, nieuw))
            conn.execute(
                "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
            )
        return str(pad)

    @staticmethod
    def _dup_gedrag(pad: str) -> tuple[str, int]:
        """(uitkomst, aantal rijen met external_ref 'dup') na een duplicate-insert."""
        with sqlite3.connect(pad) as conn:
            conn.execute("UPDATE definities SET external_ref = 'ref-' || id")
            conn.execute("UPDATE definities SET external_ref = 'dup' WHERE id = 1")
            try:
                cur = conn.execute(
                    "INSERT INTO definities (begrip, definitie, categorie, external_ref) "
                    "VALUES ('nieuw', 'nieuw', 'type', 'dup')"
                )
                uitkomst = f"ok:{cur.rowcount}"
            except sqlite3.IntegrityError:
                uitkomst = "integrity_error"
            aantal = conn.execute(
                "SELECT COUNT(*) FROM definities WHERE external_ref = 'dup'"
            ).fetchone()[0]
            conn.rollback()
        return uitkomst, aantal

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT UNIQUE ON CONFLICT IGNORE\n",
                id="inline-ignore",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT UNIQUE ON CONFLICT REPLACE\n",
                id="inline-replace",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT,\n"
                "    CONSTRAINT uq_ext UNIQUE(external_ref) ON CONFLICT IGNORE\n",
                id="benoemd-tabelniveau-ignore",
            ),
        ],
    )
    def test_on_conflict_gedrag_gaat_niet_verloren(self, tmp_path, declaratie):
        pad = self._bouw(
            tmp_path / "conflict.db", "    voorkeursterm TEXT\n", declaratie
        )
        voor = self._dup_gedrag(pad)
        assert voor[0] != "integrity_error", "fixture: ON CONFLICT moet vóór gelden"
        ddl_voor = _tabel_ddl(pad, "definities")

        uitkomst = migrate_database(pad)

        # Óf de bron is intact gelaten (False) óf het gedrag is echt behouden.
        if uitkomst is False:
            assert _tabel_ddl(pad, "definities") == ddl_voor
        assert self._dup_gedrag(pad) == voor

    @pytest.mark.parametrize(
        "declaratie",
        [
            # Codex-review 4 (P1): commentaar is in SQLite een tokenscheiding;
            # de normalizer plakte `ON/**/CONFLICT` aaneen tot `onconflict`.
            pytest.param(
                "    voorkeursterm TEXT UNIQUE ON/**/CONFLICT IGNORE\n",
                id="blokcommentaar-canoniek",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT UNIQUE On  \n"
                "      -- lijncommentaar\n      Conflict REPLACE\n",
                id="lijncommentaar-hoofdletters-extra",
            ),
            pytest.param(
                "    voorkeursterm TEXT,\n    external_ref TEXT,\n"
                "    CONSTRAINT uq_ext UNIQUE(external_ref) ON/* x */CONFLICT IGNORE\n",
                id="benoemd-blokcommentaar",
            ),
        ],
    )
    def test_on_conflict_met_commentaar_of_opmaak_gaat_niet_verloren(
        self, tmp_path, declaratie
    ):
        pad = self._bouw(
            tmp_path / "conflict-cm.db", "    voorkeursterm TEXT\n", declaratie
        )
        kolom = "external_ref" if "external_ref" in declaratie else "voorkeursterm"

        def _gedrag() -> str:
            with sqlite3.connect(pad) as conn:
                conn.execute(f"UPDATE definities SET {kolom} = 'ref-' || id")
                conn.execute(f"UPDATE definities SET {kolom} = 'dup' WHERE id = 1")
                try:
                    cur = conn.execute(
                        f"UPDATE definities SET {kolom} = 'dup' WHERE id = 2"
                    )
                    uitkomst = f"ok:{cur.rowcount}:" + str(
                        conn.execute(
                            f"SELECT COUNT(*) FROM definities WHERE {kolom} = 'dup'"
                        ).fetchone()[0]
                    )
                except sqlite3.IntegrityError:
                    uitkomst = "integrity_error"
                conn.rollback()
            return uitkomst

        voor = _gedrag()
        assert voor != "integrity_error", "fixture: ON CONFLICT moet vóór gelden"
        ddl_voor = _tabel_ddl(pad, "definities")

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, "definities") == ddl_voor
        assert _gedrag() == voor

    @pytest.mark.parametrize(
        "constraint",
        [
            pytest.param(
                "    UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde) "
                "ON CONFLICT REPLACE\n",
                id="gewoon",
            ),
            pytest.param(
                "    UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde) "
                "ON/**/CONFLICT REPLACE\n",
                id="blokcommentaar",
            ),
        ],
    )
    def test_on_conflict_op_definitie_voorbeelden_gaat_niet_verloren(
        self, tmp_path, constraint
    ):
        pad = self._bouw(
            tmp_path / "conflict-vb.db",
            "    UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)\n",
            constraint,
        )
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
            )
        ddl_voor = _tabel_ddl(pad, "definitie_voorbeelden")

        def _gedrag() -> str:
            with sqlite3.connect(pad) as conn:
                conn.execute(
                    "INSERT INTO definitie_voorbeelden "
                    "(definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde) "
                    "VALUES (1, 'sentence', 'een', 1)"
                )
                try:
                    conn.execute(
                        "INSERT INTO definitie_voorbeelden "
                        "(definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde) "
                        "VALUES (1, 'sentence', 'twee', 1)"
                    )
                    tekst = conn.execute(
                        "SELECT voorbeeld_tekst FROM definitie_voorbeelden "
                        "WHERE definitie_id = 1 AND voorbeeld_volgorde = 1"
                    ).fetchone()[0]
                    uitkomst = f"ok:{tekst}"
                except sqlite3.IntegrityError:
                    uitkomst = "integrity_error"
                conn.rollback()
            return uitkomst

        voor = _gedrag()
        assert voor == "ok:twee"

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, "definitie_voorbeelden") == ddl_voor
        assert _gedrag() == voor

    @pytest.mark.parametrize(
        ("tabel", "oud", "nieuw", "kolom"),
        [
            # Codex-review 4 (P1): enkel gequote, dubbel gequote met andere
            # hoofdletters, brackets en backticks zijn geldige kolomnamen in
            # deze positie; de prefixherkenning miste ze en COLLATE verdween.
            pytest.param(
                "definities",
                "    voorkeursterm TEXT\n",
                "    'voorkeursterm' TEXT COLLATE NOCASE\n",
                "voorkeursterm",
                id="canoniek-singlequoted",
            ),
            pytest.param(
                "definities",
                "    voorkeursterm TEXT\n",
                '    "Voorkeursterm" TEXT COLLATE NOCASE\n',
                "voorkeursterm",
                id="canoniek-doublequoted-hoofdletters",
            ),
            pytest.param(
                "definities",
                "    voorkeursterm TEXT\n",
                "    [voorkeursterm]  TEXT  /* c */ COLLATE   NOCASE\n",
                "voorkeursterm",
                id="canoniek-brackets-commentaar",
            ),
            pytest.param(
                "definities",
                "    voorkeursterm TEXT\n",
                '    voorkeursterm TEXT,\n    "Extra_ci" TEXT COLLATE NOCASE\n',
                "Extra_ci",
                id="extra-doublequoted",
            ),
            pytest.param(
                "definities",
                "    voorkeursterm TEXT\n",
                "    voorkeursterm TEXT,\n    'extra_ci' TEXT COLLATE NOCASE\n",
                "extra_ci",
                id="extra-singlequoted",
            ),
            pytest.param(
                "definitie_voorbeelden",
                "    beoordeeling_notities TEXT,\n",
                "    `Beoordeeling_Notities` TEXT COLLATE NOCASE,\n",
                "beoordeeling_notities",
                id="voorbeelden-backticks",
            ),
        ],
    )
    def test_collate_op_gequote_kolomnaam_gaat_niet_verloren(
        self, tmp_path, tabel, oud, nieuw, kolom
    ):
        pad = self._bouw(tmp_path / "collate-quote.db", oud, nieuw)
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
            )
            if tabel == "definitie_voorbeelden":
                conn.execute(
                    "INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, "
                    f"voorbeeld_tekst, \"{kolom}\") VALUES (1, 'sentence', 'vb', 'MiXeD')"
                )
            else:
                conn.execute(f"UPDATE {tabel} SET \"{kolom}\" = 'MiXeD'")

        def _treffers() -> int:
            with sqlite3.connect(pad) as conn:
                return conn.execute(
                    f"SELECT COUNT(*) FROM {tabel} WHERE \"{kolom}\" = 'mixed'"
                ).fetchone()[0]

        voor = _treffers()
        assert voor > 0, "fixture: NOCASE moet vóór gelden"
        ddl_voor = _tabel_ddl(pad, tabel)

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, tabel) == ddl_voor
        assert _treffers() == voor

    def test_twee_kolommen_die_alleen_in_unicode_case_verschillen_blijven_apart(
        self, tmp_path
    ):
        # Rootprobe 13 (probe-sqlite-identifier-case): "Éxtra" en "éxtra" zijn
        # in SQLite twee verschillende kolommen (alleen ASCII-hoofdletters
        # zijn identifier-gelijk). Python .lower() trok ze samen, waardoor de
        # NOCASE-declaratie van "éxtra" verloren ging.
        pad = self._bouw(
            tmp_path / "unicode-case.db",
            "    voorkeursterm TEXT\n",
            '    voorkeursterm TEXT,\n    "Éxtra" TEXT,\n    "éxtra" TEXT COLLATE NOCASE\n',
        )
        query = 'SELECT id FROM definities WHERE "éxtra" = ? ORDER BY id'
        with sqlite3.connect(pad) as conn:
            conn.execute(
                'UPDATE definities SET "Éxtra" = ?, "éxtra" = ?', ("other", "MiXeD")
            )
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        def _toestand() -> tuple[list[tuple], list[tuple]]:
            with sqlite3.connect(pad) as conn:
                return (
                    conn.execute(
                        'SELECT id, "Éxtra", "éxtra" FROM definities ORDER BY id'
                    ).fetchall(),
                    conn.execute(query, ("mixed",)).fetchall(),
                )

        voor = _toestand()
        assert voor[1] == [(1,), (2,)]
        ddl_voor = _tabel_ddl(pad, "definities")

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, "definities") == ddl_voor
        assert _toestand() == voor

    @pytest.mark.parametrize(
        ("tabel", "canoniek", "extra", "vul", "lees"),
        [
            pytest.param(
                "definities",
                "ketenpartners",
                "Ketenpartners",
                "UPDATE definities SET ketenpartners = 'canonical-sentinel', "
                "\"Ketenpartners\" = 'extra-sentinel'",
                'SELECT id, ketenpartners, "Ketenpartners" FROM definities ORDER BY id',
                id="definities-kelvin-K",
            ),
            pytest.param(
                "definitie_voorbeelden",
                "voorbeeld_tekst",
                "voorbeeld_teKst",
                "INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, "
                'voorbeeld_tekst, "voorbeeld_teKst") '
                "VALUES (1, 'sentence', 'canonical-example', 'extra-example')",
                'SELECT id, voorbeeld_tekst, "voorbeeld_teKst" FROM definitie_voorbeelden '
                "ORDER BY id",
                id="voorbeelden-kelvin-K",
            ),
        ],
    )
    def test_extra_kolom_die_via_unicode_lower_op_een_canonieke_naam_valt(
        self, tmp_path, tabel, canoniek, extra, vul, lees
    ):
        # Codex-review 5 (P1): "Ketenpartners" (Kelvinteken) is een andere
        # SQLite-kolom dan ketenpartners; Python .lower() maakte er dezelfde
        # sleutel van, de extra kolom verdween en de canonieke waarde werd
        # overschreven met de extra waarde.
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        pad = tmp_path / "kelvin.db"
        with sqlite3.connect(str(pad)) as conn:
            conn.executescript(tekst)
            conn.execute(f'ALTER TABLE {tabel} ADD COLUMN "{extra}" TEXT')
            conn.execute(
                "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
            )
            conn.execute(
                "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
            )
            conn.execute(vul)
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
            assert {canoniek, extra} <= {
                r[1] for r in conn.execute(f"PRAGMA table_info({tabel})")
            }

        def _rijen() -> list[tuple]:
            with sqlite3.connect(str(pad)) as conn:
                return conn.execute(lees).fetchall()

        voor = _rijen()
        assert any(
            r[1] and "canonical" in r[1] and r[2] == f"extra-{r[1].split('-')[1]}"
            for r in voor
        )
        ddl_voor = _tabel_ddl(str(pad), tabel)

        uitkomst = migrate_database(str(pad))

        if uitkomst is False:
            assert _tabel_ddl(str(pad), tabel) == ddl_voor
        # Beide kolommen bestaan nog met hun eigen waarde; niets is samengevoegd.
        assert _rijen() == voor

    def test_extra_not_null_en_default_op_canonieke_kolom_gaan_niet_verloren(
        self, tmp_path
    ):
        pad = self._bouw(
            tmp_path / "notnull.db",
            "    voorkeursterm TEXT\n",
            "    voorkeursterm TEXT NOT NULL DEFAULT 'sentinel'\n",
        )

        def _gedrag() -> tuple[str, str | None]:
            with sqlite3.connect(pad) as conn:
                try:
                    conn.execute(
                        "UPDATE definities SET voorkeursterm = NULL WHERE id = 1"
                    )
                    null = "ok"
                except sqlite3.IntegrityError:
                    null = "integrity_error"
                conn.rollback()
                conn.execute(
                    "INSERT INTO definities (begrip, definitie, categorie) "
                    "VALUES ('x', 'x', 'type')"
                )
                default = conn.execute(
                    "SELECT voorkeursterm FROM definities WHERE begrip = 'x'"
                ).fetchone()[0]
                conn.rollback()
            return null, default

        voor = _gedrag()
        assert voor == ("integrity_error", "sentinel")
        ddl_voor = _tabel_ddl(pad, "definities")

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, "definities") == ddl_voor
        assert _gedrag() == voor

    @pytest.mark.parametrize(
        ("tabel", "oud", "nieuw", "vul", "lees"),
        [
            pytest.param(
                "definities",
                "    voorkeursterm TEXT\n",
                "    voorkeursterm BLOB\n",
                "UPDATE definities SET voorkeursterm = 7",
                "SELECT id, voorkeursterm, typeof(voorkeursterm) FROM definities ORDER BY id",
                id="definities-blob",
            ),
            pytest.param(
                "definitie_voorbeelden",
                "    beoordeeling_notities TEXT,\n",
                "    beoordeeling_notities BLOB,\n",
                "INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, "
                "voorbeeld_tekst, beoordeeling_notities) VALUES (1, 'sentence', 'vb', 7)",
                "SELECT id, beoordeeling_notities, typeof(beoordeeling_notities) "
                "FROM definitie_voorbeelden ORDER BY id",
                id="voorbeelden-blob",
            ),
        ],
    )
    def test_andere_bronaffiniteit_op_canonieke_kolom_verandert_geen_waarden(
        self, tmp_path, tabel, oud, nieuw, vul, lees
    ):
        # Rootprobe (probe-canonical-column-affinity): een BLOB-kolom (geen
        # affiniteit) bewaart 7 als integer; na de rebuild naar TEXT werd dat
        # stil '7' (text). Waarde én type moeten vóór en na gelijk zijn, of de
        # migratie laat de bron intact.
        pad = self._bouw(tmp_path / "affiniteit.db", oud, nieuw)
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
            )
            conn.execute(vul)

        def _waarden() -> list[tuple]:
            with sqlite3.connect(pad) as conn:
                return conn.execute(lees).fetchall()

        voor = _waarden()
        assert voor and all(rij[2] == "integer" for rij in voor)
        ddl_voor = _tabel_ddl(pad, tabel)

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, tabel) == ddl_voor
        assert _waarden() == voor

    @pytest.mark.parametrize(
        ("tabel", "kolom", "oud"),
        [
            pytest.param(
                "definities",
                "version_number",
                "    version_number INTEGER NOT NULL DEFAULT 1,",
                id="definities-version-number",
            ),
            pytest.param(
                "definitie_voorbeelden",
                "voorbeeld_volgorde",
                "    voorbeeld_volgorde INTEGER DEFAULT 1,",
                id="voorbeelden-volgorde",
            ),
        ],
    )
    def test_unicode_typenaam_met_andere_affiniteit_verandert_geen_waarden(
        self, tmp_path, tabel, kolom, oud
    ):
        # Codex-review 6 (P1) / rootprobe `probe-unicode-affinity`: de bron
        # declareert `FLOATING POıNT` (dotloze ı, U+0131). SQLite geeft dat
        # REAL-affiniteit — 1.0, typeof 'real', `/2` = 0.5. De affiniteitsgrens
        # vóór de copy vergeleek met `str.upper()`, las INTEGER en liet de
        # rebuild door: waarde, typeof én rekenresultaat veranderden stil naar
        # 1 / 'integer' / 0. Python-gelijkheid maskeert dat (1 == 1.0), dus de
        # assertie leest typeof en de deling uit SQLite zelf.
        pad = self._bouw(
            tmp_path / "unicode-affiniteit.db",
            oud,
            oud.replace("INTEGER", "FLOATING POıNT"),
        )
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
            )
            if tabel == "definitie_voorbeelden":
                conn.execute(
                    "INSERT INTO definitie_voorbeelden "
                    "(definitie_id, voorbeeld_type, voorbeeld_tekst) "
                    "VALUES (1, 'sentence', 'sentinel')"
                )
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        lees = (
            f"SELECT id, {kolom}, typeof({kolom}), {kolom} / 2 "
            f"FROM {tabel} ORDER BY id"
        )

        def _waarden() -> list[tuple]:
            with sqlite3.connect(pad) as conn:
                return conn.execute(lees).fetchall()

        def _dump() -> str:
            with sqlite3.connect(pad) as conn:
                return "\n".join(conn.iterdump())

        voor = _waarden()
        assert voor and all(
            rij[2] == "real" and rij[3] == 0.5 for rij in voor
        ), f"fixture: de bron moet REAL-affiniteit hebben, niet {voor}"
        ddl_voor = _tabel_ddl(pad, tabel)
        dump_voor = _dump()

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            # Veilige weigering: bron-DDL én volledige inhoud onaangeroerd.
            assert _tabel_ddl(pad, tabel) == ddl_voor
            assert _dump() == dump_voor
        assert _waarden() == voor

    @pytest.mark.parametrize(
        ("tabel", "oud", "nieuw", "vul", "lees"),
        [
            pytest.param(
                "definities",
                "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,",
                "CREATE TABLE definities (\n    id INT PRIMARY KEY,",
                "INSERT INTO definities (begrip, definitie, categorie) "
                "VALUES ('zonder-id', 'zonder-id', 'type')",
                "SELECT id, typeof(id), begrip FROM definities ORDER BY rowid",
                id="definities-int-pk",
            ),
            pytest.param(
                "definitie_voorbeelden",
                "CREATE TABLE definitie_voorbeelden (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,",
                "CREATE TABLE definitie_voorbeelden (\n    id INT PRIMARY KEY,",
                "INSERT INTO definitie_voorbeelden (definitie_id, voorbeeld_type, "
                "voorbeeld_tekst) VALUES (1, 'sentence', 'zonder-id')",
                "SELECT id, typeof(id), voorbeeld_tekst FROM definitie_voorbeelden "
                "ORDER BY rowid",
                id="voorbeelden-int-pk",
            ),
        ],
    )
    def test_andere_sleutelallocatie_op_canonieke_pk_verandert_geen_ids(
        self, tmp_path, tabel, oud, nieuw, vul, lees
    ):
        # Rootprobe (probe-rebuild-primary-key-values-v2): `INT PRIMARY KEY`
        # is geen rowid-alias; een rij met id NULL is daar geldig en blijft
        # NULL. Na de rebuild naar INTEGER PRIMARY KEY AUTOINCREMENT werd die
        # NULL stil 3. INT en INTEGER delen affiniteit, dus alleen affiniteit
        # dekt dit niet.
        pad = self._bouw(tmp_path / "sleutel.db", oud, nieuw)
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "ALTER TABLE definitie_voorbeelden ADD COLUMN is_voorkeursterm INTEGER"
            )
            # Zonder rowid-alias zijn de seed-ids NULL; maak de bron FK-geldig
            # zoals de probe (V2) doet, vóór de rij met bewust NULL-id.
            conn.execute(f"UPDATE {tabel} SET id = rowid")
            conn.execute(vul)
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        def _rijen() -> list[tuple]:
            with sqlite3.connect(pad) as conn:
                return conn.execute(lees).fetchall()

        voor = _rijen()
        assert any(rij[0] is None and rij[1] == "null" for rij in voor)
        ddl_voor = _tabel_ddl(pad, tabel)

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, tabel) == ddl_voor
        assert _rijen() == voor

    def test_check_met_verwijderde_kolomnaam_als_literal_blijft(self, tmp_path):
        # Codex-review 3 (P1): de literal 'voorkeursterm_is_begrip' werd als
        # verwijzing naar de verwijderde kolom gezien en de CHECK verdween.
        pad = self._bouw(
            tmp_path / "literal-check.db",
            "    voorkeursterm TEXT\n",
            "    voorkeursterm TEXT CHECK(voorkeursterm != 'voorkeursterm_is_begrip')\n",
        )

        def _verboden_waarde_geweigerd() -> bool:
            with sqlite3.connect(pad) as conn:
                try:
                    conn.execute(
                        "UPDATE definities SET voorkeursterm = 'voorkeursterm_is_begrip' "
                        "WHERE id = 1"
                    )
                    geweigerd = False
                except sqlite3.IntegrityError:
                    geweigerd = True
                conn.rollback()
            return geweigerd

        assert _verboden_waarde_geweigerd() is True
        ddl_voor = _tabel_ddl(pad, "definities")

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, "definities") == ddl_voor
        assert _verboden_waarde_geweigerd() is True

    @pytest.mark.parametrize(
        "check",
        [
            pytest.param("CHECK(voorkeursterm_is_begrip IN (0, 1))", id="ongequote"),
            pytest.param('CHECK("voorkeursterm_is_begrip" IN (0, 1))', id="gequote"),
        ],
    )
    def test_check_op_echt_verwijderde_kolom_mag_vervallen(self, tmp_path, check):
        # De tegenhanger: een CHECK die de bewust verwijderde kolom als
        # identifier raakt (ook gequote) vervalt mee; de migratie slaagt.
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        oud = "    voorkeursterm TEXT\n"
        assert tekst.count(oud) == 1
        pad = tmp_path / "echte-check.db"
        with sqlite3.connect(str(pad)) as conn:
            conn.executescript(
                tekst.replace(
                    oud,
                    f"    voorkeursterm TEXT,\n    voorkeursterm_is_begrip INTEGER,\n"
                    f"    {check}\n",
                )
            )

        assert migrate_database(str(pad)) is True

        assert "voorkeursterm_is_begrip" not in _kolommen(str(pad), "definities")

    def test_deferrable_fk_gaat_niet_verloren(self, tmp_path):
        pad = self._bouw(
            tmp_path / "deferrable.db",
            "    previous_version_id INTEGER REFERENCES definities(id),",
            "    previous_version_id INTEGER REFERENCES definities(id) "
            "DEFERRABLE INITIALLY DEFERRED,",
        )

        def _child_voor_parent_lukt() -> bool:
            with sqlite3.connect(str(pad)) as conn:
                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("BEGIN")
                try:
                    conn.execute(
                        "INSERT INTO definities (id, begrip, definitie, categorie, "
                        "previous_version_id) VALUES (9001, 'kind', 'kind', 'type', 9000)"
                    )
                    conn.execute(
                        "INSERT INTO definities (id, begrip, definitie, categorie) "
                        "VALUES (9000, 'ouder', 'ouder', 'type')"
                    )
                    conn.execute("COMMIT")
                    gelukt = True
                except sqlite3.IntegrityError:
                    gelukt = False
                    conn.execute("ROLLBACK")
                if gelukt:
                    conn.execute("DELETE FROM definities WHERE id IN (9000, 9001)")
                    conn.commit()
            return gelukt

        assert _child_voor_parent_lukt() is True
        ddl_voor = _tabel_ddl(pad, "definities")

        uitkomst = migrate_database(pad)

        if uitkomst is False:
            assert _tabel_ddl(pad, "definities") == ddl_voor
        assert _child_voor_parent_lukt() is True


class TestAutoincrementTellerOverleeftDeRebuild:
    """Rootprobe (probe-autoincrement-preservation): na de rebuild stond de
    sqlite_sequence-teller op de hoogste aanwezige rij; een eerder uitgegeven
    en verwijderd id (1000) kon opnieuw worden uitgegeven."""

    @staticmethod
    def _seq(pad: str, tabel: str) -> int | None:
        with sqlite3.connect(pad) as conn:
            rij = conn.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = ?", (tabel,)
            ).fetchone()
        return None if rij is None else int(rij[0])

    @pytest.fixture
    def database_met_hoge_tellers(self, bestaande_database):
        with sqlite3.connect(bestaande_database) as conn:
            conn.execute(
                "INSERT INTO definities (id, begrip, definitie, categorie) "
                "VALUES (1000, 'tijdelijk', 'tijdelijk', 'type')"
            )
            conn.execute("DELETE FROM definities WHERE id = 1000")
            conn.execute(
                "INSERT INTO definitie_voorbeelden "
                "(id, definitie_id, voorbeeld_type, voorbeeld_tekst) "
                "SELECT 500, id, 'sentence', 'tijdelijk' FROM definities "
                "WHERE begrip = 'besluit'"
            )
            conn.execute("DELETE FROM definitie_voorbeelden WHERE id = 500")
        assert self._seq(bestaande_database, "definities") == 1000
        assert self._seq(bestaande_database, "definitie_voorbeelden") == 500
        return bestaande_database

    def test_tellers_blijven_en_oude_ids_worden_niet_hergebruikt(
        self, database_met_hoge_tellers
    ):
        # De fixture heeft beide verouderde kolommen: beide tabellen herbouwen.
        pad = database_met_hoge_tellers

        assert migrate_database(pad) is True

        assert self._seq(pad, "definities") == 1000
        assert self._seq(pad, "definitie_voorbeelden") == 500
        with sqlite3.connect(pad) as conn:
            cur = conn.execute(
                "INSERT INTO definities (begrip, definitie, categorie) "
                "VALUES ('nieuw', 'nieuw', 'type')"
            )
            assert cur.lastrowid == 1001
            cur = conn.execute(
                "INSERT INTO definitie_voorbeelden "
                "(definitie_id, voorbeeld_type, voorbeeld_tekst) "
                "VALUES (1001, 'sentence', 'nieuw')"
            )
            assert cur.lastrowid == 501

    def test_tellers_blijven_bij_rollback(self, database_met_hoge_tellers, monkeypatch):
        import database.migrate_database as md

        pad = database_met_hoge_tellers
        monkeypatch.setattr(
            md, "_verifieer_migratie", lambda conn, verwacht: ["injected rejection"]
        )

        assert migrate_database(pad) is False

        assert self._seq(pad, "definities") == 1000
        assert self._seq(pad, "definitie_voorbeelden") == 500


class TestCliExitcode:
    def test_exit_1_als_de_migratie_faalt(self, bestaande_database):
        import os
        import subprocess
        import sys

        with sqlite3.connect(bestaande_database) as conn:
            conn.execute("DROP TABLE import_export_logs")
        env = {
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parents[3] / "src"),
            "DEFINITIE_DISABLE_DOTENV": "1",
        }
        uitkomst = subprocess.run(
            [sys.executable, "-m", "database.migrate_database", bestaande_database],
            cwd=Path(bestaande_database).parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert uitkomst.returncode == 1


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
