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
