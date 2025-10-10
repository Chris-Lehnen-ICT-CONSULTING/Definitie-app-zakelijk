"""
Document Processing Module voor DefinitieAgent.

Upload en verwerk documenten voor context verrijking en hybride definitie generatie.
Ondersteunt PDF, DOCX, TXT en andere documentformaten voor tekstextractie.
"""

from .document_extractor import (  # Tekst extractie functionaliteit
    extract_text_from_file,
    supported_file_types,
)

# Importeer document processing componenten voor bestandsverwerking
from .document_processor import (  # Document processor en resultaat klassen
    DocumentProcessor,
    ProcessedDocument,
)

# Exporteer publieke interface - alle document processing componenten
__all__ = [
    "DocumentProcessor",  # Hoofdklasse voor document verwerking
    "ProcessedDocument",  # Container voor verwerkt document
    "extract_text_from_file",  # Functie voor tekst extractie uit bestanden
    "supported_file_types",  # Lijst van ondersteunde bestandsformaten
]
