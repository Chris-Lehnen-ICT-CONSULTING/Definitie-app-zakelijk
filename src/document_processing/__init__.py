"""
Document Processing Module voor DefinitieAgent.

Upload en verwerk documenten voor context verrijking en hybride definitie generatie.
Ondersteunt PDF, DOCX, TXT en andere documentformaten voor tekstextractie.
"""

# Importeer document processing componenten voor bestandsverwerking
from .document_processor import DocumentProcessor, ProcessedDocument  # Document processor en resultaat klassen
from .document_extractor import extract_text_from_file, supported_file_types  # Tekst extractie functionaliteit

# Exporteer publieke interface - alle document processing componenten
__all__ = [
    'DocumentProcessor',      # Hoofdklasse voor document verwerking
    'ProcessedDocument',      # Container voor verwerkt document
    'extract_text_from_file', # Functie voor tekst extractie uit bestanden
    'supported_file_types'    # Lijst van ondersteunde bestandsformaten
]