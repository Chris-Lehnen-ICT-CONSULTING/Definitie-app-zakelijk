"""
Ontologische Analyzer - Implementatie van 6-stappen protocol voor ontologische categorisering.

Dit module implementeert het volledige 6-stappen ontologisch protocol zoals beschreven in
docs/ontologie-6-stappen.md, met integratie van de bestaande weblookup functionaliteit.

De stappen zijn:
1. Lexicale en Conceptuele Verkenning (via weblookup)
2. Context- en Domeinanalyse (via juridische lookup)
3. Formele Categorietoets (AI-gedreven classificatie)
4. Identiteits- en Persistentiecriteria
5. Rol versus Intrinsieke Eigenschappen
6. Documentatie en Definitieconstructie
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from generation.definitie_generator import OntologischeCategorie
from web_lookup.bron_lookup import herken_bronnen_in_definitie
from web_lookup.definitie_lookup import DefinitieZoeker
from web_lookup.juridische_lookup import zoek_wetsartikelstructuur

logger = logging.getLogger(__name__)


class OntologischeAnalyzer:
    """
    Hoofdklasse voor ontologische analyse volgens het 6-stappen protocol.

    Integreert weblookup functionaliteit voor lexicale verkenning en context-analyse,
    en gebruikt AI-gedreven classificatie voor robuste categorisering.
    """

    def __init__(self):
        """Initialiseer de analyzer met weblookup integratie."""
        self.definitie_zoeker = DefinitieZoeker()
        self.category_templates = self._load_category_templates()
        logger.info("OntologischeAnalyzer geïnitialiseerd met weblookup integratie")

    def _load_category_templates(self) -> Dict[str, str]:
        """Laad de definitie templates per ontologische categorie."""
        return {
            "type": "Een {genus} dat {kenmerken}",
            "proces": "Het {proces} waarbij {actor} {handeling}",
            "resultaat": "De {uitkomst} van {proces}",
            "exemplaar": "Een specifiek {type} dat {eigenschappen}",
        }

    async def bepaal_ontologische_categorie(
        self, begrip: str, org_context: str = "", jur_context: str = ""
    ) -> Tuple[OntologischeCategorie, Dict[str, Any]]:
        """
        Doorloop het volledige 6-stappen protocol voor ontologische categorisering.

        Args:
            begrip: Het te analyseren begrip
            org_context: Organisatorische context
            jur_context: Juridische context

        Returns:
            Tuple van (OntologischeCategorie, analyse_resultaat)
        """
        try:
            logger.info(f"Start ontologische analyse voor begrip: '{begrip}'")

            # Stap 1: Lexicale en Conceptuele Verkenning
            semantisch_profiel = await self._stap1_lexicale_verkenning(begrip)

            # Stap 2: Context- en Domeinanalyse
            context_map = await self._stap2_context_analyse(
                begrip, org_context, jur_context
            )

            # Stap 3: Formele Categorietoets
            categorie_resultaat = await self._stap3_formele_categorietoets(
                begrip, semantisch_profiel, context_map
            )

            # Stap 4: Identiteits- en Persistentiecriteria
            identiteit_criteria = await self._stap4_identiteit_persistentie(
                begrip, categorie_resultaat
            )

            # Stap 5: Rol versus Intrinsieke Eigenschappen
            rol_analyse = await self._stap5_rol_analyse(begrip, categorie_resultaat)

            # Stap 6: Documentatie en Definitieconstructie
            documentatie = self._stap6_documentatie(
                begrip, categorie_resultaat, identiteit_criteria, rol_analyse
            )

            # Compileer volledig resultaat
            analyse_resultaat = {
                "begrip": begrip,
                "semantisch_profiel": semantisch_profiel,
                "context_map": context_map,
                "categorie_resultaat": categorie_resultaat,
                "identiteit_criteria": identiteit_criteria,
                "rol_analyse": rol_analyse,
                "documentatie": documentatie,
                "reasoning": self._generate_comprehensive_reasoning(
                    begrip, categorie_resultaat, semantisch_profiel, context_map
                ),
            }

            logger.info(
                f"Ontologische analyse voltooid voor '{begrip}': {categorie_resultaat['primaire_categorie']}"
            )

            return (
                OntologischeCategorie(categorie_resultaat["primaire_categorie"]),
                analyse_resultaat,
            )

        except Exception as e:
            logger.error(f"Fout in ontologische analyse voor '{begrip}': {e}")
            # Fallback naar eenvoudige analyse
            return await self._fallback_analyse(begrip, org_context, jur_context)

    async def _stap1_lexicale_verkenning(self, begrip: str) -> Dict[str, Any]:
        """
        Stap 1: Lexicale en Conceptuele Verkenning via weblookup.

        Verzamelt alle betekenisaspecten van het begrip uit verschillende bronnen.
        """
        logger.info(f"Stap 1: Lexicale verkenning voor '{begrip}'")

        try:
            # Zoek definities in alle beschikbare bronnen
            zoek_resultaten = await self.definitie_zoeker.zoek_definities(
                begrip, context={"rechtsgebied": "algemeen"}
            )

            # Analyseer semantische kenmerken
            kenmerken = self._analyseer_semantische_kenmerken(
                begrip, zoek_resultaten.definities
            )

            # Identificeer synoniemen en gerelateerde begrippen
            synoniemen = self._extracteer_synoniemen(zoek_resultaten.definities)

            return {
                "definities": zoek_resultaten.definities,
                "semantische_kenmerken": kenmerken,
                "synoniemen": synoniemen,
                "sleutelwoorden": self._extracteer_sleutelwoorden(
                    zoek_resultaten.definities
                ),
                "bron_kwaliteit": zoek_resultaten.metadata.get("gemiddelde_score", 0.0),
            }

        except Exception as e:
            logger.warning(f"Fout in lexicale verkenning: {e}")
            return {
                "definities": [],
                "semantische_kenmerken": self._analyseer_semantische_kenmerken(
                    begrip, []
                ),
                "synoniemen": [],
                "sleutelwoorden": [],
                "bron_kwaliteit": 0.0,
            }

    async def _stap2_context_analyse(
        self, begrip: str, org_context: str, jur_context: str
    ) -> Dict[str, Any]:
        """
        Stap 2: Context- en Domeinanalyse via juridische weblookup.

        Bepaalt rol en afhankelijkheden in juridische/organisatorische context.
        """
        logger.info(f"Stap 2: Context-analyse voor '{begrip}'")

        try:
            # Juridische context analyse
            juridische_verwijzingen = zoek_wetsartikelstructuur(
                f"{begrip} {jur_context}"
            )

            # Bron analyse voor context
            context_tekst = f"{begrip} {org_context} {jur_context}"
            gedetecteerde_bronnen = herken_bronnen_in_definitie(context_tekst)

            # Bepaal domein en procesrollen
            domein_analyse = self._analyseer_domein_context(
                begrip, org_context, jur_context
            )

            return {
                "juridische_verwijzingen": juridische_verwijzingen,
                "gedetecteerde_bronnen": gedetecteerde_bronnen,
                "domein_analyse": domein_analyse,
                "organisatorische_context": org_context,
                "juridische_context": jur_context,
                "afhankelijkheden": self._bepaal_context_afhankelijkheden(
                    begrip, org_context, jur_context
                ),
            }

        except Exception as e:
            logger.warning(f"Fout in context-analyse: {e}")
            return {
                "juridische_verwijzingen": [],
                "gedetecteerde_bronnen": [],
                "domein_analyse": {},
                "organisatorische_context": org_context,
                "juridische_context": jur_context,
                "afhankelijkheden": [],
            }

    async def _stap3_formele_categorietoets(
        self,
        begrip: str,
        semantisch_profiel: Dict[str, Any],
        context_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Stap 3: Formele Categorietoets - AI-gedreven classificatie.

        Classificeert volgens standaard ontologie met testvragen.
        """
        logger.info(f"Stap 3: Formele categorietoets voor '{begrip}'")

        # Categorieën met testvragen (aangepast aan bestaande enum)
        categorie_tests = {
            "type": self._test_type,
            "proces": self._test_proces,
            "resultaat": self._test_resultaat,
            "exemplaar": self._test_exemplaar,
        }

        # Voer tests uit per categorie
        test_resultaten = {}
        for categorie, test_func in categorie_tests.items():
            try:
                score = await test_func(begrip, semantisch_profiel, context_map)
                test_resultaten[categorie] = score
                logger.debug(f"Test {categorie} voor '{begrip}': {score}")
            except Exception as e:
                logger.warning(f"Fout in test {categorie}: {e}")
                test_resultaten[categorie] = 0.0

        # Bepaal primaire categorie
        primaire_categorie = max(test_resultaten, key=test_resultaten.get)

        # Bepaal secundaire aspecten (scores > 0.3)
        secundaire_aspecten = [
            cat
            for cat, score in test_resultaten.items()
            if cat != primaire_categorie and score > 0.3
        ]

        return {
            "primaire_categorie": primaire_categorie,
            "secundaire_aspecten": secundaire_aspecten,
            "test_scores": test_resultaten,
            "confidence": test_resultaten[primaire_categorie],
        }

    async def _stap4_identiteit_persistentie(
        self, begrip: str, categorie_resultaat: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stap 4: Identiteits- en Persistentiecriteria.

        Bepaalt wat instanties uniek maakt en wanneer ze ophouden te bestaan.
        """
        logger.info(f"Stap 4: Identiteit/persistentie analyse voor '{begrip}'")

        categorie = categorie_resultaat["primaire_categorie"]

        # Categorie-specifieke identiteitscriteria
        identiteit_mapping = {
            "type": self._identiteit_type,
            "proces": self._identiteit_proces,
            "resultaat": self._identiteit_resultaat,
            "exemplaar": self._identiteit_exemplaar,
        }

        try:
            handler = identiteit_mapping.get(categorie, self._identiteit_fallback)
            return await handler(begrip, categorie_resultaat)
        except Exception as e:
            logger.warning(f"Fout in identiteit/persistentie analyse: {e}")
            return {
                "identiteitscriteria": [],
                "persistentiecriteria": {
                    "ontstaat_door": "Onbekend",
                    "eindigt_door": "Onbekend",
                },
            }

    async def _stap5_rol_analyse(
        self, begrip: str, categorie_resultaat: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stap 5: Rol versus Intrinsieke Eigenschappen.

        Scheidt contextuele rollen van inherente categorieën.
        """
        logger.info(f"Stap 5: Rol-analyse voor '{begrip}'")

        # Check voor rol-indicatoren
        rol_indicatoren = self._detecteer_rol_indicatoren(begrip)
        is_contextueel = len(rol_indicatoren) > 0

        if is_contextueel:
            # Identificeer basisentiteit
            basis_entiteit = self._identificeer_basis_entiteit(begrip)
            rol_specificatie = self._bepaal_rol_specificatie(begrip)

            return {
                "is_contextueel": True,
                "basis_entiteit": basis_entiteit,
                "rol_specificatie": rol_specificatie,
                "rol_indicatoren": rol_indicatoren,
                "context_vereist": True,
            }
        else:
            # Intrinsieke eigenschappen
            return {
                "is_contextueel": False,
                "basis_entiteit": None,
                "rol_aspecten": [],
                "context_vereist": False,
            }

    def _stap6_documentatie(
        self,
        begrip: str,
        categorie_resultaat: Dict[str, Any],
        identiteit_criteria: Dict[str, Any],
        rol_analyse: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Stap 6: Documentatie en Definitieconstructie.

        Legt vast en construeert definitie volgens de categorie.
        """
        logger.info(f"Stap 6: Documentatie voor '{begrip}'")

        categorie = categorie_resultaat["primaire_categorie"]
        template = self.category_templates.get(
            categorie, "Een {begrip} dat {kenmerken}"
        )

        # Genereer definitie volgens template
        definitie = self._genereer_definitie(begrip, categorie, template, rol_analyse)

        return {
            "ontologische_categorie": categorie,
            "basis_entiteit": rol_analyse.get("basis_entiteit"),
            "definitie_template": template,
            "gegenereerde_definitie": definitie,
            "identiteitscriteria": identiteit_criteria.get("identiteitscriteria", []),
            "persistentiecriteria": identiteit_criteria.get("persistentiecriteria", {}),
            "context_afhankelijkheden": rol_analyse.get("rol_indicatoren", []),
        }

    # === Test functies per categorie ===

    async def _test_type(self, begrip: str, profiel: Dict, context: Dict) -> float:
        """Test of begrip een type is - abstracte klasse/categorie."""
        score = 0.0

        # Lexicale indicatoren - uitgebreid
        type_woorden = [
            "type",
            "soort",
            "klasse",
            "categorie",
            "vorm",
            "systeem",
            "methode",
            "instrument",
            "tool",
            "middel",
        ]
        for woord in type_woorden:
            if woord in begrip.lower():
                score += 0.3

        # Speciale woorden die sterk type-indicatief zijn
        sterke_type_woorden = ["toets", "test", "document", "formulier", "certificaat"]
        for woord in sterke_type_woorden:
            if woord in begrip.lower():
                score += 0.5

        # Semantische kenmerken
        kenmerken = profiel.get("semantische_kenmerken", {})
        if kenmerken.get("is_abstract", False):
            score += 0.2
        if kenmerken.get("is_concreet", False):
            score += 0.3  # Concrete objecten zijn vaak types
        if kenmerken.get("is_classificeerbaar", False):
            score += 0.4

        return min(score, 1.0)

    async def _test_proces(self, begrip: str, profiel: Dict, context: Dict) -> float:
        """Test of begrip een proces is - heeft begin en eind."""
        score = 0.0

        # Lexicale indicatoren - proces eindingen
        proces_eindingen = ["atie", "tie", "ing", "eren", "ering"]
        for eind in proces_eindingen:
            if begrip.lower().endswith(eind):
                score += 0.4
                break  # Alleen één keer tellen

        # Proces woorden
        proces_woorden = [
            "proces",
            "handeling",
            "actie",
            "operatie",
            "procedure",
            "behandeling",
            "verwerking",
        ]
        for woord in proces_woorden:
            if woord in begrip.lower():
                score += 0.3

        # Semantische kenmerken
        kenmerken = profiel.get("semantische_kenmerken", {})
        if kenmerken.get("gebeurt_in_tijd", False):
            score += 0.4
        if kenmerken.get("heeft_actoren", False):
            score += 0.2

        return min(score, 1.0)

    async def _test_resultaat(self, begrip: str, profiel: Dict, context: Dict) -> float:
        """Test of begrip een resultaat is - uitkomst van proces."""
        score = 0.0

        # Lexicale indicatoren
        resultaat_woorden = ["resultaat", "uitkomst", "gevolg", "conclusie", "besluit"]
        if any(woord in begrip.lower() for woord in resultaat_woorden):
            score += 0.4

        # Semantische kenmerken
        kenmerken = profiel.get("semantische_kenmerken", {})
        if kenmerken.get("is_uitkomst", False):
            score += 0.4
        if kenmerken.get("heeft_oorzaak", False):
            score += 0.3

        return min(score, 1.0)

    async def _test_exemplaar(self, begrip: str, profiel: Dict, context: Dict) -> float:
        """Test of begrip een exemplaar is - specifieke instantie."""
        score = 0.0

        # Lexicale indicatoren
        exemplaar_woorden = ["specifiek", "individueel", "concreet", "bepaald"]
        if any(woord in begrip.lower() for woord in exemplaar_woorden):
            score += 0.4

        # Semantische kenmerken
        kenmerken = profiel.get("semantische_kenmerken", {})
        if kenmerken.get("is_specifiek", False):
            score += 0.4
        if kenmerken.get("is_instantie", False):
            score += 0.3

        return min(score, 1.0)

    # === Helper functies ===

    def _analyseer_semantische_kenmerken(
        self, begrip: str, definities: List
    ) -> Dict[str, bool]:
        """Analyseer semantische kenmerken van het begrip."""
        kenmerken = {
            "is_abstract": False,
            "is_concreet": False,
            "is_classificeerbaar": False,
            "gebeurt_in_tijd": False,
            "heeft_actoren": False,
            "is_uitkomst": False,
            "heeft_oorzaak": False,
            "is_specifiek": False,
            "is_instantie": False,
        }

        begrip_lower = begrip.lower()

        # Verbeterde abstractie-indicatoren
        abstractie_woorden = [
            "type",
            "soort",
            "klasse",
            "categorie",
            "vorm",
            "systeem",
            "methode",
            "instrument",
        ]
        if any(woord in begrip_lower for woord in abstractie_woorden):
            kenmerken["is_abstract"] = True

        # Concreetheid voor fysieke objecten
        concreet_woorden = [
            "toets",
            "test",
            "document",
            "object",
            "tool",
            "apparaat",
            "middel",
        ]
        if any(woord in begrip_lower for woord in concreet_woorden):
            kenmerken["is_concreet"] = True

        # Standaard naar concreet als geen abstractie gevonden
        if not kenmerken["is_abstract"]:
            kenmerken["is_concreet"] = True

        # Verbeterde classificatie-indicatoren
        classificatie_woorden = [
            "classificatie",
            "indeling",
            "typologie",
            "test",
            "toets",
            "evaluatie",
        ]
        if any(woord in begrip_lower for woord in classificatie_woorden):
            kenmerken["is_classificeerbaar"] = True

        # Verbeterde tijd-indicatoren
        tijd_woorden = [
            "proces",
            "handeling",
            "actie",
            "operatie",
            "atie",
            "ing",
            "eren",
        ]
        if any(woord in begrip_lower for woord in tijd_woorden):
            kenmerken["gebeurt_in_tijd"] = True

        # Verbeterde actor-indicatoren
        actor_woorden = [
            "door",
            "tussen",
            "namens",
            "uitgevoerd",
            "door persoon",
            "door systeem",
        ]
        if any(woord in begrip_lower for woord in actor_woorden):
            kenmerken["heeft_actoren"] = True

        # Verbeterde uitkomst-indicatoren
        uitkomst_woorden = [
            "resultaat",
            "uitkomst",
            "gevolg",
            "besluit",
            "conclusie",
            "bevinding",
        ]
        if any(woord in begrip_lower for woord in uitkomst_woorden):
            kenmerken["is_uitkomst"] = True

        # Verbeterde oorzaak-indicatoren
        oorzaak_woorden = ["vanwege", "door", "als gevolg", "veroorzaakt door"]
        if any(woord in begrip_lower for woord in oorzaak_woorden):
            kenmerken["heeft_oorzaak"] = True

        # Verbeterde specificiteit-indicatoren
        specificiteit_woorden = [
            "specifiek",
            "bepaald",
            "concreet",
            "individueel",
            "uniek",
        ]
        if any(woord in begrip_lower for woord in specificiteit_woorden):
            kenmerken["is_specifiek"] = True

        # Verbeterde instantie-indicatoren
        instantie_woorden = [
            "individueel",
            "exemplaar",
            "geval",
            "instantie",
            "specifiek",
        ]
        if any(woord in begrip_lower for woord in instantie_woorden):
            kenmerken["is_instantie"] = True

        return kenmerken

    def _extracteer_synoniemen(self, definities: List) -> List[str]:
        """Extracteer synoniemen uit gevonden definities."""
        synoniemen = []

        for definitie in definities:
            if hasattr(definitie, "definitie"):
                tekst = definitie.definitie.lower()
            else:
                tekst = str(definitie).lower()

            # Zoek naar synoniemen patronen
            synoniem_patronen = [
                r"ook wel.*?genoemd",
                r"synoniem.*?voor",
                r"anders.*?voor",
                r"hetzelfde.*?als",
            ]

            for patroon in synoniem_patronen:
                matches = re.findall(patroon, tekst)
                synoniemen.extend(matches)

        return list(set(synoniemen))  # Remove duplicates

    def _extracteer_sleutelwoorden(self, definities: List) -> List[str]:
        """Extracteer belangrijke sleutelwoorden uit definities."""
        sleutelwoorden = []

        for definitie in definities:
            if hasattr(definitie, "definitie"):
                tekst = definitie.definitie
            else:
                tekst = str(definitie)

            # Eenvoudige keyword extractie
            woorden = tekst.split()
            belangrijke_woorden = [
                woord
                for woord in woorden
                if len(woord) > 3
                and woord.lower() not in ["een", "het", "van", "voor", "met", "door"]
            ]

            sleutelwoorden.extend(belangrijke_woorden[:5])  # Top 5 per definitie

        return list(set(sleutelwoorden))

    def _analyseer_domein_context(
        self, begrip: str, org_context: str, jur_context: str
    ) -> Dict[str, Any]:
        """Analyseer het domein en context van het begrip."""
        domein = {
            "rechtsgebied": "onbekend",
            "organisatie_type": "onbekend",
            "proces_domein": "onbekend",
        }

        context_tekst = f"{begrip} {org_context} {jur_context}".lower()

        # Rechtsgebied bepaling
        if any(
            woord in context_tekst for woord in ["straf", "strafrecht", "strafbaar"]
        ):
            domein["rechtsgebied"] = "strafrecht"
        elif any(
            woord in context_tekst for woord in ["bestuurs", "bestuur", "gemeente"]
        ):
            domein["rechtsgebied"] = "bestuursrecht"
        elif any(woord in context_tekst for woord in ["civiel", "burgerlijk"]):
            domein["rechtsgebied"] = "burgerlijk recht"

        # Organisatie type
        if any(woord in context_tekst for woord in ["gemeente", "gemeentelijk"]):
            domein["organisatie_type"] = "gemeente"
        elif any(woord in context_tekst for woord in ["provincie", "provinciaal"]):
            domein["organisatie_type"] = "provincie"
        elif any(woord in context_tekst for woord in ["rijk", "nationaal"]):
            domein["organisatie_type"] = "rijk"

        return domein

    def _bepaal_context_afhankelijkheden(
        self, begrip: str, org_context: str, jur_context: str
    ) -> List[str]:
        """Bepaal context afhankelijkheden van het begrip."""
        afhankelijkheden = []

        context_tekst = f"{begrip} {org_context} {jur_context}".lower()

        # Juridische afhankelijkheden
        if "wet" in context_tekst:
            afhankelijkheden.append("Wettelijk kader")

        # Organisatorische afhankelijkheden
        if any(
            woord in context_tekst for woord in ["procedure", "proces", "handeling"]
        ):
            afhankelijkheden.append("Organisatorisch proces")

        # Technische afhankelijkheden
        if any(
            woord in context_tekst for woord in ["systeem", "technisch", "digitaal"]
        ):
            afhankelijkheden.append("Technisch systeem")

        return afhankelijkheden

    # === Identiteit functies per categorie ===

    async def _identiteit_type(
        self, begrip: str, categorie_resultaat: Dict
    ) -> Dict[str, Any]:
        """Bepaal identiteit voor type categorie."""
        return {
            "identiteitscriteria": [
                "Definitie eigenschappen",
                "Classificatie criteria",
                "Onderscheidende kenmerken",
            ],
            "persistentiecriteria": {
                "ontstaat_door": "Conceptuele definitie",
                "eindigt_door": "Herdefiniëring",
            },
        }

    async def _identiteit_proces(
        self, begrip: str, categorie_resultaat: Dict
    ) -> Dict[str, Any]:
        """Bepaal identiteit voor proces categorie."""
        return {
            "identiteitscriteria": [
                "Betrokken actoren",
                "Tijdstip van uitvoering",
                "Specifieke stappen",
            ],
            "persistentiecriteria": {
                "ontstaat_door": "Start van handeling",
                "eindigt_door": "Voltooiing van handeling",
            },
        }

    async def _identiteit_resultaat(
        self, begrip: str, categorie_resultaat: Dict
    ) -> Dict[str, Any]:
        """Bepaal identiteit voor resultaat categorie."""
        return {
            "identiteitscriteria": [
                "Oorsprong proces",
                "Specifieke uitkomst",
                "Tijdstip van ontstaan",
            ],
            "persistentiecriteria": {
                "ontstaat_door": "Voltooiing proces",
                "eindigt_door": "Nieuwe bewerking",
            },
        }

    async def _identiteit_exemplaar(
        self, begrip: str, categorie_resultaat: Dict
    ) -> Dict[str, Any]:
        """Bepaal identiteit voor exemplaar categorie."""
        return {
            "identiteitscriteria": [
                "Unieke identifier",
                "Specifieke eigenschappen",
                "Historische context",
            ],
            "persistentiecriteria": {
                "ontstaat_door": "Instantiatie",
                "eindigt_door": "Vernietiging",
            },
        }

    async def _identiteit_fallback(
        self, begrip: str, categorie_resultaat: Dict
    ) -> Dict[str, Any]:
        """Fallback identiteit bepaling."""
        return {
            "identiteitscriteria": ["Onbekend"],
            "persistentiecriteria": {
                "ontstaat_door": "Onbekend",
                "eindigt_door": "Onbekend",
            },
        }

    def _detecteer_rol_indicatoren(self, begrip: str) -> List[str]:
        """Detecteer indicatoren voor contextuele rollen."""
        rol_indicatoren = []
        begrip_lower = begrip.lower()

        # Rol-eindingen
        rol_eindingen = ["er", "aar", "houder", "beheerder", "eigenaar"]
        for eind in rol_eindingen:
            if begrip_lower.endswith(eind):
                rol_indicatoren.append(f"Rol-einding: {eind}")

        # Functie-woorden
        functie_woorden = ["functie", "rol", "positie", "taak"]
        for woord in functie_woorden:
            if woord in begrip_lower:
                rol_indicatoren.append(f"Functie-indicator: {woord}")

        return rol_indicatoren

    def _identificeer_basis_entiteit(self, begrip: str) -> Optional[str]:
        """Identificeer de basis-entiteit bij rollen."""
        begrip_lower = begrip.lower()

        # Algemene rol-patronen
        if any(
            woord in begrip_lower for woord in ["persoon", "natuurlijk", "individu"]
        ):
            return "Persoon"
        elif any(
            woord in begrip_lower for woord in ["organisatie", "bedrijf", "instelling"]
        ):
            return "Organisatie"
        elif any(woord in begrip_lower for woord in ["orgaan", "bestuurs", "overheid"]):
            return "Bestuursorgaan"

        # Specifieke rol-eindingen
        if begrip_lower.endswith("er"):
            return "Persoon"
        elif begrip_lower.endswith("houder"):
            return "Persoon/Organisatie"
        elif begrip_lower.endswith("beheerder"):
            return "Persoon/Organisatie"

        return "Onbekend"

    def _bepaal_rol_specificatie(self, begrip: str) -> str:
        """Bepaal de specifieke rol-functie."""
        begrip_lower = begrip.lower()

        if "eigenaar" in begrip_lower:
            return "Eigendomsrol"
        elif "beheerder" in begrip_lower:
            return "Beheersrol"
        elif "aanvrager" in begrip_lower:
            return "Aanvraagrol"
        elif "houder" in begrip_lower:
            return "Houderschap"

        return "Algemene rol"

    def _genereer_definitie(
        self, begrip: str, categorie: str, template: str, rol_analyse: Dict
    ) -> str:
        """Genereer definitie volgens categorie template."""
        try:
            if rol_analyse.get("is_contextueel"):
                basis = rol_analyse.get("basis_entiteit", "entiteit")
                functie = rol_analyse.get("rol_specificatie", "functie")
                return f"Een {basis} die {functie} vervult"

            # Voor andere categorieën gebruik basis template
            return template.format(
                begrip=begrip,
                genus="entiteit",
                kenmerken="specifieke eigenschappen heeft",
                proces="proces",
                actor="actor",
                handeling="handeling uitvoert",
                uitkomst="uitkomst",
                type="type",
                eigenschappen="eigenschappen",
            )
        except Exception as e:
            logger.warning(f"Fout bij definitie generatie: {e}")
            return f"Een {begrip} zoals gedefinieerd in de context"

    def _generate_comprehensive_reasoning(
        self,
        begrip: str,
        categorie_resultaat: Dict,
        semantisch_profiel: Dict,
        context_map: Dict,
    ) -> str:
        """Genereer uitgebreide redenering voor de categorisering."""
        categorie = categorie_resultaat["primaire_categorie"]
        confidence = categorie_resultaat["confidence"]

        reasoning = (
            f"Ontologische categorisering van '{begrip}' als {categorie.upper()} "
        )
        reasoning += f"(confidence: {confidence:.2f})\n\n"

        # Test scores
        scores = categorie_resultaat.get("test_scores", {})
        reasoning += "Test scores per categorie:\n"
        for cat, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            reasoning += f"- {cat}: {score:.2f}\n"

        # Semantische kenmerken
        kenmerken = semantisch_profiel.get("semantische_kenmerken", {})
        positieve_kenmerken = [k for k, v in kenmerken.items() if v]
        if positieve_kenmerken:
            reasoning += (
                f"\nGedetecteerde kenmerken: {', '.join(positieve_kenmerken)}\n"
            )

        # Context
        domein = context_map.get("domein_analyse", {})
        if domein.get("rechtsgebied") != "onbekend":
            reasoning += f"Rechtsgebied: {domein['rechtsgebied']}\n"

        # Secundaire aspecten
        secundaire = categorie_resultaat.get("secundaire_aspecten", [])
        if secundaire:
            reasoning += f"Secundaire aspecten: {', '.join(secundaire)}\n"

        return reasoning

    async def _fallback_analyse(
        self, begrip: str, org_context: str, jur_context: str
    ) -> Tuple[OntologischeCategorie, Dict[str, Any]]:
        """Fallback analyse bij fouten in hoofdanalyse."""
        logger.warning(f"Fallback analyse voor '{begrip}'")

        # Gebruik QuickOntologischeAnalyzer voor fallback
        quick_analyzer = QuickOntologischeAnalyzer()
        categorie, reasoning = quick_analyzer.quick_categoriseer(begrip)

        fallback_resultaat = {
            "begrip": begrip,
            "categorie_resultaat": {
                "primaire_categorie": categorie.value,
                "confidence": 0.5,
                "test_scores": {categorie.value: 0.5},
            },
            "reasoning": f"Fallback analyse - {reasoning}",
        }

        return categorie, fallback_resultaat


# === Quick Decision Tree voor eenvoudige gevallen ===


class QuickOntologischeAnalyzer:
    """
    Snelle analyzer voor 80% van de gevallen via decision tree.

    Implementeert de quick-check uit het protocol:
    1. Gebeurt het? → PROCES
    2. Is het een ding? → TYPE
    3. Is het een kenmerk? → RESULTAAT
    4. Is het een positie/functie? → EXEMPLAAR
    """

    def __init__(self):
        self.proces_patronen = ["atie", "tie", "ing", "eren", "ering"]
        self.type_patronen = ["type", "soort", "klasse", "systeem", "vorm"]
        self.resultaat_patronen = ["resultaat", "uitkomst", "gevolg", "conclusie"]
        self.exemplaar_patronen = ["specifiek", "individueel", "concreet", "bepaald"]

    def quick_categoriseer(self, begrip: str) -> Tuple[OntologischeCategorie, str]:
        """
        Snelle categorisering via decision tree.

        Returns:
            Tuple van (categorie, redenering)
        """
        begrip_lower = begrip.lower()

        # 1. Gebeurt het? → PROCES
        if any(begrip_lower.endswith(patroon) for patroon in self.proces_patronen):
            return (
                OntologischeCategorie.PROCES,
                f"Proces patroon gedetecteerd (eindigt op {[p for p in self.proces_patronen if begrip_lower.endswith(p)][0]})",
            )

        # 2. Is het een ding? → TYPE
        if any(patroon in begrip_lower for patroon in self.type_patronen):
            return OntologischeCategorie.TYPE, "Type patroon gedetecteerd"

        # 3. Is het een kenmerk? → RESULTAAT
        if any(patroon in begrip_lower for patroon in self.resultaat_patronen):
            return OntologischeCategorie.RESULTAAT, "Resultaat patroon gedetecteerd"

        # 4. Is het een positie/functie? → EXEMPLAAR
        if any(patroon in begrip_lower for patroon in self.exemplaar_patronen):
            return OntologischeCategorie.EXEMPLAAR, "Exemplaar patroon gedetecteerd"

        # 5. Default → TYPE
        return (
            OntologischeCategorie.TYPE,
            "Standaard categorie (geen specifieke patronen)",
        )
