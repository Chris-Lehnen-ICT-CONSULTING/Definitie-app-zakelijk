"""DEF-768 WP7 — invoerlaag van de ESS-05-proefrunner (offline, geen modelcalls).

Bewijst: labels (`verwacht`, `verwacht_per_buur`, `grond`, …) bereiken het
model nooit; transport past alleen de vorm aan (IDs via productie); de
nulcallroutes volgen het orchestratorcontract; het generieke gevallenschema
van de eindset wordt fail-closed gecontroleerd; de G-varianten verschillen
uitsluitend in de ESS-05-instructieregel.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from domain.ess05.contract import buur_id
from services.validation.ess05_assessment_service import laad_ess05_norm

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "ess05"))

import proefinvoer as pi

CONTEXT = {
    "organisatorische_context": ["Synthetische Uitleendienst"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
GROND = "Arbeidsovereenkomst en lening zijn verschillende kenmerken; overlap mag."


def _geval(**extra):
    geval = {
        "id": "T-01",
        "begrip": "lener",
        "tekst": "Persoon met een actuele lening bij de instelling.",
        "toelichting": "Iemand die iets leent.",
        "categorie": None,
        "context": copy.deepcopy(CONTEXT),
        "bronnen": [
            {"doc_id": "d1", "title": "Reglement", "snippet": "De lener leent."}
        ],
        "buren": [
            {
                "term": "werknemer",
                "definitie": "Persoon met een arbeidsovereenkomst met de instelling.",
                "herkomst": "gebruiker",
                "bevestigd": True,
            }
        ],
        "verwacht": "pass",
        "verwacht_per_buur": {"werknemer": "distinguished"},
        "grond": GROND,
    }
    geval.update(extra)
    return geval


class TestAfscherming:
    def test_projectie_bevat_alleen_modelvelden(self):
        projectie = pi.modelprojectie(
            _geval(doel="Controleer overlap.", notitie="intern", herkomst={"x": 1})
        )
        assert set(projectie) <= set(pi.MODELVELDEN)
        for label in ("verwacht", "verwacht_per_buur", "grond", "doel", "notitie"):
            assert label not in projectie

    def test_labels_staan_niet_in_de_prompt_en_veranderen_hem_niet(self):
        norm = laad_ess05_norm()
        geval = _geval(doel="Het doel van dit geval is overlap toetsen.")
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        pi.controleer_afscherming(geval, prompt.teksten, norm)
        anders = _geval(
            verwacht="fail",
            verwacht_per_buur={"werknemer": "not_distinguished"},
            grond="Een heel andere grond die nergens mag verschijnen.",
        )
        assert pi.bouw_t_prompt(pi.modelprojectie(anders), norm).teksten == (
            prompt.teksten
        )
        for tekst in prompt.teksten:
            assert GROND not in tekst
            assert "Het doel van dit geval" not in tekst

    def test_label_dat_in_modelinvoer_lekt_wordt_geweigerd(self):
        norm = laad_ess05_norm()
        geval = _geval(toelichting=GROND)
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        with pytest.raises(pi.InvoerfoutError, match="afgeschermd"):
            pi.controleer_afscherming(geval, prompt.teksten, norm)


class TestTransport:
    def test_bron_krijgt_documentprovider_zonder_inhoudswijziging(self):
        bronnen, _ = pi.transport(pi.modelprojectie(_geval()))
        assert bronnen == [
            {
                "doc_id": "d1",
                "title": "Reglement",
                "snippet": "De lener leent.",
                "provider": "documents",
            }
        ]

    def test_buur_ids_komen_uit_productie(self):
        geval = _geval()
        geval["buren"][0]["id"] = "zelfverzonnen"
        _, buren = pi.transport(pi.modelprojectie(geval))
        assert "id" not in buren[0]
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), laad_ess05_norm())
        assert prompt.buren[0].id == buur_id("gebruiker", "werknemer")
        assert "zelfverzonnen" not in prompt.teksten[1]


class TestRoutes:
    @pytest.mark.parametrize(
        ("wijziging", "status"),
        [
            ({"context": {}}, "not_evaluated"),
            ({"tekst": "  "}, "not_evaluated"),
            (
                {"buren": [{"term": "x", "herkomst": "gebruiker", "bevestigd": "ja"}]},
                "error",
            ),
        ],
    )
    def test_nulcallroutes(self, wijziging, status):
        route = pi.route(pi.modelprojectie(_geval(**wijziging)), None)
        assert (route["soort"], route["uitkomst"]["status"]) == ("nulcall", status)

    def test_lege_ruimte_gebonden_aan_actuele_vingerafdruk_is_nulcall_pass(self):
        geval = _geval(buren=[])
        lege = pi.bind_lege_ruimte(
            pi.modelprojectie(geval),
            {"grond": "Geen verwante begrippen.", "actor": "x"},
        )
        route = pi.route(pi.modelprojectie(geval), lege)
        assert (route["soort"], route["uitkomst"]["status"]) == ("nulcall", "pass")

    def test_verouderde_lege_ruimte_is_geen_nulcall(self):
        lege = {
            "contract_version": "ess05/1",
            "fingerprint": "0" * 64,
            "grond": "g",
            "actor": "x",
        }
        route = pi.route(pi.modelprojectie(_geval(buren=[])), lege)
        assert route["soort"] == "aanroep"

    def test_zonder_buren_en_zonder_bevestiging_wel_een_aanroep(self):
        """K-8 en K-1: context zonder bekende buren roept het model wél aan."""
        assert pi.route(pi.modelprojectie(_geval(buren=[])), None)["soort"] == (
            "aanroep"
        )

    def test_te_lange_buurdefinitie_zonder_aanroep(self):
        geval = _geval()
        geval["buren"][0]["definitie"] = "x" * 8001
        route = pi.route(pi.modelprojectie(geval), None)
        assert route["soort"] == "nulcall"
        assert route["uitkomst"]["status"] == "error"
        assert "input_truncated" in route["reden"]


class TestSchema:
    def _bestand(self, n=5, herhaal=4):
        gevallen = [_geval(id=f"E-{i:02d}") for i in range(n)]
        return {
            "gevallen": gevallen,
            "herhaal_ids": [g["id"] for g in gevallen[:herhaal]],
        }

    def test_generieke_eindset_vorm_wordt_geaccepteerd(self):
        bestand = self._bestand()
        gevallen, herhaal = pi.valideer_gevallenbestand(bestand, herhaal_vereist=True)
        assert len(gevallen) == 5
        assert herhaal == ["E-00", "E-01", "E-02", "E-03"]

    @pytest.mark.parametrize(
        ("mutatie", "melding"),
        [
            (lambda b: b["gevallen"][0].pop("verwacht"), "verwacht"),
            (lambda b: b["gevallen"][0].update(verwacht="voldoet"), "verwacht"),
            (lambda b: b["gevallen"][0].pop("grond"), "grond"),
            (lambda b: b["gevallen"][1].update(id="E-00"), "dubbel"),
            (lambda b: b.update(herhaal_ids=["E-00", "E-01", "E-02"]), "herhaal_ids"),
            (lambda b: b.update(herhaal_ids=["E-00", "E-01", "E-02", "Z"]), "onbekend"),
            (
                lambda b: b["gevallen"][0].update(
                    verwacht_per_buur={"klant": "unclear"}
                ),
                "verwacht_per_buur",
            ),
            (
                lambda b: b["gevallen"][0].update(
                    verwacht_per_buur={"werknemer": "voldoet"}
                ),
                "verwacht_per_buur",
            ),
            (lambda b: b["gevallen"][0].update(context=[]), "context"),
            (lambda b: b["gevallen"][0]["bronnen"][0].pop("snippet"), "bron"),
        ],
    )
    def test_fail_closed(self, mutatie, melding):
        bestand = self._bestand()
        mutatie(bestand)
        with pytest.raises(pi.InvoerfoutError, match=melding):
            pi.valideer_gevallenbestand(bestand, herhaal_vereist=True)


#: Volledig zelfbedacht geval in het afgesproken eindsetschema
#: (`def768-wp7-eindset/1`); geen inhoud uit de eindset.
CITAAT = "een actuele lening bij de instelling"


def _schemageval(gid="S-01"):
    return {
        "id": gid,
        "begrip": "lener",
        "tekst": f"Persoon met {CITAAT}.",
        "toelichting": None,
        "categorie": None,
        "context": copy.deepcopy(CONTEXT),
        "bronnen": [
            {
                "provider": "documents",
                "doc_id": "s-doc",
                "title": "Synthetisch reglement",
                "snippet": f"Een lener is een persoon met {CITAAT}.",
            }
        ],
        "buren": [
            {
                "term": "werknemer",
                "definitie": "Persoon met een arbeidsovereenkomst met de instelling.",
                "herkomst": "gebruiker",
                "bevestigd": True,
            },
            {
                "term": "bezoeker",
                "definitie": None,
                "herkomst": "gebruiker",
                "bevestigd": True,
            },
        ],
        "verwacht": "pass",
        "verwacht_per_buur": [
            {
                "term": "werknemer",
                "distinction": "distinguished",
                "dragend_citaat": CITAAT,
                "ontbrekend_kenmerk": None,
                "grond": "De lening onderscheidt de lener van de werknemer.",
            },
            {
                "term": "bezoeker",
                "distinction": "unclear",
                "dragend_citaat": None,
                "ontbrekend_kenmerk": None,
                "grond": "Zonder definitie van bezoeker blijft dit open.",
            },
        ],
        "grond": "Synthetische grond: de lening is het onderscheidende kenmerk.",
        "doel": "Synthetisch: citaat in kandidaat en bron.",
        "parafrase": False,
        "toegestane_vraag": "Wat onderscheidt een lener van een bezoeker?",
    }


def _schemabestand(n=5):
    gevallen = [_schemageval(f"S-{i:02d}") for i in range(n)]
    return {
        "schema": "def768-wp7-eindset/1",
        "gevallen": gevallen,
        "herhaal_ids": [g["id"] for g in gevallen[:4]],
    }


class TestEindsetschema:
    """Punt 1: `verwacht_per_buur` als lijst (afgesproken eindsetschema)."""

    def test_lijstvorm_wordt_geaccepteerd(self):
        gevallen, herhaal = pi.valideer_gevallenbestand(
            _schemabestand(), herhaal_vereist=True
        )
        assert len(gevallen) == 5
        assert herhaal == ["S-00", "S-01", "S-02", "S-03"]

    def test_adapter_bewaart_uitgebreide_labels(self):
        verwachtingen = pi.per_buur_verwachtingen(_schemageval())
        assert verwachtingen == [
            {
                "term": "werknemer",
                "distinction": "distinguished",
                "dragend_citaat": CITAAT,
                "ontbrekend_kenmerk": None,
                "grond": "De lening onderscheidt de lener van de werknemer.",
            },
            {
                "term": "bezoeker",
                "distinction": "unclear",
                "dragend_citaat": None,
                "ontbrekend_kenmerk": None,
                "grond": "Zonder definitie van bezoeker blijft dit open.",
            },
        ]

    def test_adapter_zet_de_ontwikkelmapping_om(self):
        assert pi.per_buur_verwachtingen(_geval()) == [
            {
                "term": "werknemer",
                "distinction": "distinguished",
                "dragend_citaat": None,
                "ontbrekend_kenmerk": None,
                "grond": None,
            }
        ]
        assert pi.per_buur_verwachtingen(_geval(verwacht_per_buur=None)) == []

    @pytest.mark.parametrize(
        "mutatie",
        [
            lambda v: v[0].update(term="klant"),
            lambda v: v[0].update(distinction="voldoet"),
            lambda v: v[0].pop("distinction"),
            lambda v: v[0].pop("term"),
            lambda v: v[0].update(dragend_citaat=3),
            lambda v: v[0].update(grond=["geen tekst"]),
            lambda v: v[1].update(term="werknemer"),
            lambda v: v.append("werknemer"),
        ],
    )
    def test_ongeldige_lijst_fail_closed(self, mutatie):
        bestand = _schemabestand()
        mutatie(bestand["gevallen"][0]["verwacht_per_buur"])
        with pytest.raises(pi.InvoerfoutError, match="verwacht_per_buur"):
            pi.valideer_gevallenbestand(bestand, herhaal_vereist=True)


#: Fictieve buurterm langer dan de labelgrens (geen eindsetmateriaal).
LANGE_TERM = "uitleenbemiddelaar"


def _langeterm_geval():
    return _geval(
        buren=[
            {
                "term": LANGE_TERM,
                "definitie": "Persoon die leningen tussen instelling en lener regelt.",
                "herkomst": "gebruiker",
                "bevestigd": True,
            }
        ],
        verwacht_per_buur=[
            {
                "term": LANGE_TERM,
                "distinction": "distinguished",
                "dragend_citaat": None,
                "ontbrekend_kenmerk": None,
                "grond": "Synthetische grond per buur, uitsluitend lokaal.",
            }
        ],
    )


class TestLegitiemeOverlap:
    """Punt 2: echte invloed geweigerd; letterlijke overlap met invoer toegestaan."""

    def test_dragend_citaat_in_kandidaat_en_bron_is_geen_lek(self):
        norm = laad_ess05_norm()
        geval = _schemageval()
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        assert CITAAT in prompt.teksten[1]
        pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_reviewrepro_ontwikkelgeval_met_citaat(self):
        norm = laad_ess05_norm()
        geval = _geval(
            verwacht_per_buur=[
                {
                    "term": "werknemer",
                    "distinction": "distinguished",
                    "dragend_citaat": CITAAT,
                    "ontbrekend_kenmerk": None,
                    "grond": "Synthetische grond per buur.",
                }
            ]
        )
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_buurterm_als_per_buurverwijzing_is_geen_lek(self):
        """Preflightfout eindrun: een geldige buurterm (≥ labelgrens) in
        `verwacht_per_buur[].term` staat terecht in de prompt — als buur."""
        norm = laad_ess05_norm()
        geval = _langeterm_geval()
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        assert LANGE_TERM in prompt.teksten[1]
        assert len(LANGE_TERM) >= pi._MIN_LABELLENGTE
        pi.valideer_gevallenbestand({"gevallen": [geval]}, herhaal_vereist=False)
        pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_verwijzing_die_geen_buurterm_is_en_in_de_prompt_lekt_blijft_lek(
        self, monkeypatch
    ):
        norm = laad_ess05_norm()
        geval = _langeterm_geval()
        lek = "uitsluitend-labelterm"
        geval["verwacht_per_buur"][0]["term"] = lek
        echte_projectie = pi.modelprojectie

        def lekkend(g):
            projectie = echte_projectie(g)
            per_buur = g.get("verwacht_per_buur")
            if isinstance(per_buur, list) and isinstance(per_buur[0], dict):
                projectie["toelichting"] = per_buur[0].get("term")
            return projectie

        monkeypatch.setattr(pi, "modelprojectie", lekkend)
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        assert lek in prompt.teksten[1]
        with pytest.raises(pi.InvoerfoutError, match="afgeschermd"):
            pi.controleer_afscherming(geval, prompt.teksten, norm)

    @pytest.mark.parametrize(
        ("veld", "waarde"),
        [
            ("grond", LANGE_TERM),
            ("doel", {"term": LANGE_TERM}),
            ("toegestane_vraag", LANGE_TERM),
        ],
    )
    def test_buurterm_buiten_de_per_buurverwijzing_blijft_lek(self, veld, waarde):
        """De uitzondering hangt aan `verwacht_per_buur[].term`, niet aan de tekst."""
        norm = laad_ess05_norm()
        geval = {**_langeterm_geval(), veld: waarde}
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        with pytest.raises(pi.InvoerfoutError, match="afgeschermd"):
            pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_langere_grond_per_buur_naast_geldige_verwijzing_blijft_lek(
        self, monkeypatch
    ):
        norm = laad_ess05_norm()
        geval = _langeterm_geval()
        echte_projectie = pi.modelprojectie

        def lekkend(g):
            projectie = echte_projectie(g)
            per_buur = g.get("verwacht_per_buur")
            if isinstance(per_buur, list) and isinstance(per_buur[0], dict):
                projectie["toelichting"] = per_buur[0].get("grond")
            return projectie

        monkeypatch.setattr(pi, "modelprojectie", lekkend)
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        with pytest.raises(pi.InvoerfoutError, match="afgeschermd"):
            pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_citaat_dat_niet_in_de_invoer_staat_maar_wel_in_de_prompt_is_lek(
        self, monkeypatch
    ):
        """Een 'citaat' dat alleen via een label in de prompt komt, is een lek."""
        norm = laad_ess05_norm()
        geval = _schemageval()
        lek = "Een zin die uitsluitend in het label staat."
        geval["verwacht_per_buur"][0]["dragend_citaat"] = lek
        echte_projectie = pi.modelprojectie

        def lekkend(g):
            projectie = echte_projectie(g)
            per_buur = g.get("verwacht_per_buur")
            if isinstance(per_buur, list) and isinstance(per_buur[0], dict):
                projectie["toelichting"] = per_buur[0].get("dragend_citaat")
            return projectie

        monkeypatch.setattr(pi, "modelprojectie", lekkend)
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        assert lek in prompt.teksten[1]
        with pytest.raises(pi.InvoerfoutError, match="afgeschermd"):
            pi.controleer_afscherming(geval, prompt.teksten, norm)

    @pytest.mark.parametrize("veld", ["grond", "doel", "toegestane_vraag", "notitie"])
    def test_mutatie_van_niet_invoerveld_verandert_prompt_niet(self, veld):
        norm = laad_ess05_norm()
        geval = _schemageval()
        geval["notitie"] = {"intern": "herkomst synthetisch"}
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        pi.controleer_afscherming(geval, prompt.teksten, norm)
        anders = {**geval, veld: "Volledig andere synthetische labelwaarde."}
        assert pi.bouw_t_prompt(pi.modelprojectie(anders), norm).teksten == (
            prompt.teksten
        )

    def test_echte_invloed_van_een_genest_label_wordt_geweigerd(self, monkeypatch):
        """Invloed via een genest label (per-buurgrond) valt op door mutatie."""
        norm = laad_ess05_norm()
        geval = _schemageval()
        echte_projectie = pi.modelprojectie

        def lekkend(g):
            projectie = echte_projectie(g)
            per_buur = g.get("verwacht_per_buur")
            if (
                isinstance(per_buur, list)
                and per_buur[0].get("distinction") == "distinguished"
            ):
                projectie["toelichting"] = "Afhankelijk van een label."
            return projectie

        monkeypatch.setattr(pi, "modelprojectie", lekkend)
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), norm)
        with pytest.raises(pi.InvoerfoutError, match="hangt af"):
            pi.controleer_afscherming(geval, prompt.teksten, norm)


class TestGVarianten:
    HUIDIG = "Kies een kenmerk."
    BASIS = "Maak het verschil duidelijk."

    def _prompt(self, n=1):
        regels = ["Kop", "🔹 **ESS-05 - Onderscheid**", "- uitleg"]
        regels += [f"- **Instructie:** {self.HUIDIG}"] * n
        return "\n".join([*regels, "- **Instructie:** iets anders", "Slot"])

    def test_basisvariant_verschilt_in_precies_een_regel(self):
        basis, verschil = pi.basisvariant(self._prompt(), self.HUIDIG, self.BASIS)
        assert verschil == {
            "verwijderd": [f"- **Instructie:** {self.HUIDIG}"],
            "toegevoegd": [f"- **Instructie:** {self.BASIS}"],
        }
        assert basis.count(self.BASIS) == 1

    @pytest.mark.parametrize("n", [0, 2])
    def test_instructie_moet_precies_eenmaal_voorkomen(self, n):
        with pytest.raises(pi.InvoerfoutError, match="precies één"):
            pi.basisvariant(self._prompt(n), self.HUIDIG, self.BASIS)

    async def test_echte_promptopbouw_met_documenten(self):
        invoer = {
            "id": "G-x",
            "begrip": "lener",
            "organisatorische_context": ["Synthetische Uitleendienst"],
            "juridische_context": [],
            "wettelijke_basis": [],
            "ontologische_categorie": "type",
            "documenten": [
                {
                    "doc_id": "g-doc-1",
                    "title": "Synthetisch reglement",
                    "snippet": "Een lener heeft een actuele lening bij de dienst.",
                }
            ],
            "aandachtspunten": "Label: mag nooit in de prompt staan.",
        }
        eerste = await pi.bouw_g_prompt(invoer)
        tweede = await pi.bouw_g_prompt(copy.deepcopy(invoer))
        assert eerste == tweede  # deterministisch
        assert "Een lener heeft een actuele lening bij de dienst." in eerste
        assert "mag nooit in de prompt" not in eerste
        huidig = pi.huidige_g_instructie()
        basis, verschil = pi.basisvariant(eerste, huidig, "Oude instructie.")
        assert len(verschil["verwijderd"]) == len(verschil["toegevoegd"]) == 1
        assert basis.replace("Oude instructie.", huidig) == eerste

    # WP7-G-kanaal: buren via de normale keten (request → orchestrator → prompt).
    G_BUREN = {
        "id": "G-b",
        "begrip": "lener",
        "organisatorische_context": ["Synthetische Uitleendienst"],
        "juridische_context": [],
        "wettelijke_basis": [],
        "ontologische_categorie": "type",
        "documenten": [
            {
                "doc_id": "g-doc-b",
                "title": "Synthetisch reglement",
                "snippet": "Een lener heeft een actuele lening bij de dienst.",
            }
        ],
        "repository_buren": [
            {"id": 9001, "begrip": "werknemer", "definitie": "persoon in dienst"}
        ],
        "gerelateerde_begrippen": ["werknemer"],
        "ess05_buren": [
            {
                "term": "abonnee",
                "definitie": "persoon met een abonnement",
                "herkomst": "bron",
                "bevestigd": True,
            },
            {"term": "gast", "herkomst": "model", "bevestigd": False},
        ],
        "aandachtspunten": "Label: mag nooit in de prompt staan.",
    }

    async def test_buren_reizen_via_de_normale_keten_in_beide_varianten(self):
        from domain.ess05.contract import buur_id

        prompt, kwitantie = await pi.bouw_g_prompt_met_buren(self.G_BUREN)
        assert prompt == await pi.bouw_g_prompt(copy.deepcopy(self.G_BUREN))
        assert kwitantie == {
            "status": "ok",
            "aantal": 3,
            "ids": [
                buur_id("bron", "abonnee"),
                buur_id("model", "gast"),
                "repository:9001",
            ],
            "uitgesloten": 0,
        }
        blok = prompt.split("<verwante_begrippen>", 1)[1]
        assert (
            '<buur id="repository:9001" herkomst="repository" bevestigd="ja">' in blok
        )
        assert "<beschrijving>persoon in dienst</beschrijving>" in blok
        assert 'herkomst="model" bevestigd="nee"' in blok
        assert "mag nooit in de prompt" not in prompt
        huidig = pi.huidige_g_instructie()
        basis, _ = pi.basisvariant(prompt, huidig, "Oude instructie.")
        burenblok = prompt[prompt.index("Aangeleverde verwante begrippen in deze") :]
        assert basis.endswith(burenblok)  # transport identiek in beide varianten

    async def test_ongeldige_burenlijst_stopt_de_proef(self):
        invoer = copy.deepcopy(self.G_BUREN)
        invoer["ess05_buren"] = [
            {"term": "x", "herkomst": "onbekend", "bevestigd": True}
        ]
        with pytest.raises(pi.InvoerfoutError, match="invalid_neighbours"):
            await pi.bouw_g_prompt(invoer)
