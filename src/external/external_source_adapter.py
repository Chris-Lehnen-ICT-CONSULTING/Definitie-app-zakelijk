"""
External Source Adapter - Interface voor externe definitie bronnen.
Biedt adapter pattern voor toekomstige integratie met externe systemen.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from database.definitie_repository import DefinitieRecord, DefinitieStatus, SourceType

logger = logging.getLogger(__name__)


class ExternalSourceType(Enum):
    """Types van externe bronnen."""

    DATABASE = "database"
    REST_API = "rest_api"
    FILE_SYSTEM = "file_system"
    WEB_SERVICE = "web_service"
    GRAPH_API = "graph_api"


@dataclass
class ExternalSourceConfig:
    """Configuratie voor externe bron."""

    source_id: str
    source_name: str
    source_type: ExternalSourceType
    connection_string: str
    api_key: str | None = None
    username: str | None = None
    password: str | None = None
    timeout: int = 30
    retry_count: int = 3
    custom_config: dict[str, Any] = None

    def __post_init__(self):
        if self.custom_config is None:
            self.custom_config = {}


@dataclass
class ExternalDefinition:
    """Externe definitie van een bron."""

    external_id: str
    begrip: str
    definitie: str
    categorie: str | None = None
    context: str | None = None
    juridische_context: str | None = None
    status: str | None = None
    version: str | None = None
    last_modified: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_definitie_record(
        self, source_config: ExternalSourceConfig
    ) -> DefinitieRecord:
        """Converteer naar DefinitieRecord voor interne database."""
        return DefinitieRecord(
            begrip=self.begrip,
            definitie=self.definitie,
            categorie=self.categorie or "type",
            organisatorische_context=self.context or "unknown",
            juridische_context=self.juridische_context,
            status=self._map_external_status(self.status),
            source_type=SourceType.IMPORTED.value,
            source_reference=f"{source_config.source_id}:{self.external_id}",
            imported_from=source_config.source_name,
        )

    def _map_external_status(self, external_status: str | None) -> str:
        """Map externe status naar interne status."""
        if not external_status:
            return DefinitieStatus.DRAFT.value

        status_mapping = {
            "draft": DefinitieStatus.DRAFT.value,
            "concept": DefinitieStatus.DRAFT.value,
            "review": DefinitieStatus.REVIEW.value,
            "pending": DefinitieStatus.REVIEW.value,
            "approved": DefinitieStatus.ESTABLISHED.value,
            "established": DefinitieStatus.ESTABLISHED.value,
            "final": DefinitieStatus.ESTABLISHED.value,
            "archived": DefinitieStatus.ARCHIVED.value,
            "deprecated": DefinitieStatus.ARCHIVED.value,
        }

        return status_mapping.get(external_status.lower(), DefinitieStatus.DRAFT.value)


class ExternalSourceAdapter(ABC):
    """Abstract base class voor externe bron adapters."""

    def __init__(self, config: ExternalSourceConfig):
        """
        Initialiseer adapter met configuratie.

        Args:
            config: ExternalSourceConfig met connectie details
        """
        self.config = config
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Maak verbinding met externe bron.

        Returns:
            True als verbinding succesvol
        """

    @abstractmethod
    def disconnect(self):
        """Sluit verbinding met externe bron."""

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test verbinding met externe bron.

        Returns:
            True als verbinding werkt
        """

    @abstractmethod
    def search_definitions(
        self,
        query: str = None,
        categorie: str = None,
        context: str = None,
        limit: int = 100,
    ) -> list[ExternalDefinition]:
        """
        Zoek definities in externe bron.

        Args:
            query: Zoekterm
            categorie: Filter op categorie
            context: Filter op context
            limit: Maximum aantal resultaten

        Returns:
            List van ExternalDefinition objecten
        """

    @abstractmethod
    def get_definition(self, external_id: str) -> ExternalDefinition | None:
        """
        Haal specifieke definitie op via ID.

        Args:
            external_id: Externe ID van definitie

        Returns:
            ExternalDefinition of None
        """

    @abstractmethod
    def create_definition(self, definition: ExternalDefinition) -> bool:
        """
        Maak nieuwe definitie aan in externe bron.

        Args:
            definition: ExternalDefinition object

        Returns:
            True als succesvol aangemaakt
        """

    @abstractmethod
    def update_definition(
        self, external_id: str, definition: ExternalDefinition
    ) -> bool:
        """
        Update bestaande definitie in externe bron.

        Args:
            external_id: Externe ID van definitie
            definition: Geüpdatete ExternalDefinition

        Returns:
            True als succesvol geüpdatet
        """

    @abstractmethod
    def delete_definition(self, external_id: str) -> bool:
        """
        Verwijder definitie uit externe bron.

        Args:
            external_id: Externe ID van definitie

        Returns:
            True als succesvol verwijderd
        """

    def get_source_info(self) -> dict[str, Any]:
        """Haal informatie over externe bron op."""
        return {
            "source_id": self.config.source_id,
            "source_name": self.config.source_name,
            "source_type": self.config.source_type.value,
            "connected": self.connected,
        }


class MockExternalAdapter(ExternalSourceAdapter):
    """Mock adapter voor testing en development."""

    def __init__(self, config: ExternalSourceConfig):
        super().__init__(config)
        self._mock_data = self._create_mock_data()

    def connect(self) -> bool:
        """Simuleer verbinding."""
        logger.info(f"Connecting to mock source {self.config.source_name}")
        self.connected = True
        return True

    def disconnect(self):
        """Simuleer disconnect."""
        logger.info(f"Disconnecting from mock source {self.config.source_name}")
        self.connected = False

    def test_connection(self) -> bool:
        """Simuleer connection test."""
        return True

    def search_definitions(
        self,
        query: str = None,
        categorie: str = None,
        context: str = None,
        limit: int = 100,
    ) -> list[ExternalDefinition]:
        """Simuleer zoeken in mock data."""
        results = []

        for definition in self._mock_data:
            # Apply filters
            if (
                query
                and query.lower() not in definition.begrip.lower()
                and query.lower() not in definition.definitie.lower()
            ):
                continue
            if categorie and definition.categorie != categorie:
                continue
            if context and definition.context != context:
                continue

            results.append(definition)

            if len(results) >= limit:
                break

        logger.info(f"Mock search returned {len(results)} results")
        return results

    def get_definition(self, external_id: str) -> ExternalDefinition | None:
        """Simuleer ophalen specifieke definitie."""
        for definition in self._mock_data:
            if definition.external_id == external_id:
                return definition
        return None

    def create_definition(self, definition: ExternalDefinition) -> bool:
        """Simuleer aanmaken definitie."""
        definition.external_id = f"mock_{len(self._mock_data) + 1}"
        self._mock_data.append(definition)
        logger.info(f"Mock created definition {definition.external_id}")
        return True

    def update_definition(
        self, external_id: str, definition: ExternalDefinition
    ) -> bool:
        """Simuleer updaten definitie."""
        for i, existing in enumerate(self._mock_data):
            if existing.external_id == external_id:
                definition.external_id = external_id
                self._mock_data[i] = definition
                logger.info(f"Mock updated definition {external_id}")
                return True
        return False

    def delete_definition(self, external_id: str) -> bool:
        """Simuleer verwijderen definitie."""
        for i, definition in enumerate(self._mock_data):
            if definition.external_id == external_id:
                del self._mock_data[i]
                logger.info(f"Mock deleted definition {external_id}")
                return True
        return False

    def _create_mock_data(self) -> list[ExternalDefinition]:
        """Maak mock data voor testing."""
        return [
            ExternalDefinition(
                external_id="ext_001",
                begrip="externe_verificatie",
                definitie="Verificatieproces uitgevoerd door een externe, geaccrediteerde instantie",
                categorie="proces",
                context="externe_partij",
                status="approved",
                metadata={"source": "mock", "priority": "high"},
            ),
            ExternalDefinition(
                external_id="ext_002",
                begrip="authenticiteitsbewijs",
                definitie="Document dat de echtheid van een ander document of gegeven bevestigt",
                categorie="type",
                context="externe_partij",
                status="draft",
                metadata={"source": "mock", "priority": "medium"},
            ),
            ExternalDefinition(
                external_id="ext_003",
                begrip="crosscheck",
                definitie="Controlemechanisme waarbij gegevens worden geverifieerd tegen meerdere onafhankelijke bronnen",
                categorie="proces",
                context="kwaliteitscontrole",
                status="approved",
                metadata={"source": "mock", "priority": "high"},
            ),
        ]


class FileSystemAdapter(ExternalSourceAdapter):
    """Adapter voor file system gebaseerde definities (JSON/CSV files)."""

    def connect(self) -> bool:
        """Check of bestand/directory bestaat."""
        from pathlib import Path

        try:
            path = Path(self.config.connection_string)
            if path.exists():
                self.connected = True
                logger.info(f"Connected to file system source: {path}")
                return True
            logger.error(f"File system path not found: {path}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to file system: {e}")
            return False

    def disconnect(self):
        """File system heeft geen echte disconnect."""
        self.connected = False

    def test_connection(self) -> bool:
        """Test of bestand leesbaar is."""
        return self.connect()

    def search_definitions(
        self,
        query: str = None,
        categorie: str = None,
        context: str = None,
        limit: int = 100,
    ) -> list[ExternalDefinition]:
        """Laad en filter definities uit bestand."""
        # Placeholder - zou echte file parsing implementeren
        logger.info("FileSystemAdapter: search_definitions not fully implemented")
        return []

    def get_definition(self, external_id: str) -> ExternalDefinition | None:
        """Haal definitie op uit bestand op basis van ID."""
        # Placeholder - zou echte file parsing implementeren
        logger.info(
            f"FileSystemAdapter: get_definition({external_id}) not fully implemented"
        )
        return None

    def create_definition(self, definition: ExternalDefinition) -> bool:
        """Voeg definitie toe aan bestand."""
        # Placeholder - zou echte file writing implementeren
        logger.info("FileSystemAdapter: create_definition not fully implemented")
        return False

    def update_definition(
        self, external_id: str, definition: ExternalDefinition
    ) -> bool:
        """Update definitie in bestand."""
        # Placeholder - zou echte file updating implementeren
        logger.info(
            f"FileSystemAdapter: update_definition({external_id}) not fully implemented"
        )
        return False

    def delete_definition(self, external_id: str) -> bool:
        """Verwijder definitie uit bestand."""
        # Placeholder - zou echte file updating implementeren
        logger.info(
            f"FileSystemAdapter: delete_definition({external_id}) not fully implemented"
        )
        return False


class ExternalSourceManager:
    """Manager voor meerdere externe bronnen."""

    def __init__(self):
        self.adapters: dict[str, ExternalSourceAdapter] = {}

    def register_source(self, adapter: ExternalSourceAdapter) -> bool:
        """
        Registreer externe bron adapter.

        Args:
            adapter: ExternalSourceAdapter instance

        Returns:
            True als succesvol geregistreerd
        """
        source_id = adapter.config.source_id

        if source_id in self.adapters:
            logger.warning(f"Source {source_id} already registered, overwriting")

        self.adapters[source_id] = adapter
        logger.info(f"Registered external source: {source_id}")
        return True

    def unregister_source(self, source_id: str) -> bool:
        """
        Deregistreer externe bron.

        Args:
            source_id: ID van bron om te deregistreren

        Returns:
            True als succesvol gederegistreerd
        """
        if source_id in self.adapters:
            adapter = self.adapters[source_id]
            adapter.disconnect()
            del self.adapters[source_id]
            logger.info(f"Unregistered external source: {source_id}")
            return True
        return False

    def get_adapter(self, source_id: str) -> ExternalSourceAdapter | None:
        """Haal adapter op voor specifieke bron."""
        return self.adapters.get(source_id)

    def search_all_sources(
        self,
        query: str = None,
        categorie: str = None,
        context: str = None,
        limit_per_source: int = 50,
    ) -> dict[str, list[ExternalDefinition]]:
        """
        Zoek in alle geregistreerde bronnen.

        Args:
            query: Zoekterm
            categorie: Filter op categorie
            context: Filter op context
            limit_per_source: Limit per bron

        Returns:
            Dictionary met source_id -> definitie list mapping
        """
        results = {}

        for source_id, adapter in self.adapters.items():
            try:
                if not adapter.connected:
                    adapter.connect()

                source_results = adapter.search_definitions(
                    query, categorie, context, limit_per_source
                )
                results[source_id] = source_results

            except Exception as e:
                logger.error(f"Error searching source {source_id}: {e}")
                results[source_id] = []

        return results

    def get_source_info(self) -> list[dict[str, Any]]:
        """Haal informatie over alle geregistreerde bronnen."""
        return [adapter.get_source_info() for adapter in self.adapters.values()]


# Convenience functions
def create_mock_source(
    source_name: str = "Mock External Source",
) -> MockExternalAdapter:
    """Maak mock externe bron voor testing."""
    config = ExternalSourceConfig(
        source_id="mock_source",
        source_name=source_name,
        source_type=ExternalSourceType.DATABASE,
        connection_string="mock://localhost",
    )
    return MockExternalAdapter(config)


def create_file_source(file_path: str, source_name: str = None) -> FileSystemAdapter:
    """Maak file system externe bron."""
    config = ExternalSourceConfig(
        source_id=f"file_{hash(file_path) % 10000}",
        source_name=source_name or f"File Source: {file_path}",
        source_type=ExternalSourceType.FILE_SYSTEM,
        connection_string=file_path,
    )
    return FileSystemAdapter(config)


if __name__ == "__main__":
    # Test de adapters
    print("🔌 Testing External Source Adapters")
    print("=" * 40)

    # Test mock adapter
    mock_adapter = create_mock_source("Test Mock Source")

    if mock_adapter.connect():
        print("✅ Mock adapter connected")

        # Test search
        results = mock_adapter.search_definitions(query="verificatie")
        print(f"🔍 Found {len(results)} results for 'verificatie'")

        for result in results:
            print(f"   - {result.begrip}: {result.definitie[:50]}...")

        mock_adapter.disconnect()

    # Test manager
    manager = ExternalSourceManager()
    manager.register_source(mock_adapter)

    source_info = manager.get_source_info()
    print(f"\n📊 Registered sources: {len(source_info)}")
    for info in source_info:
        print(f"   - {info['source_name']} ({info['source_type']})")

    print("\n🎯 External source adapter test completed")
