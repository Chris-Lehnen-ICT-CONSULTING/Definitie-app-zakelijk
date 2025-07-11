"""
Document Processing Module - Upload en verwerk documenten voor context enrichment.
"""

from .document_processor import DocumentProcessor, ProcessedDocument
from .document_extractor import extract_text_from_file, supported_file_types

__all__ = [
    'DocumentProcessor', 
    'ProcessedDocument',
    'extract_text_from_file',
    'supported_file_types'
]