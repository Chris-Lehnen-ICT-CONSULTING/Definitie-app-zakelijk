"""
AI Code Reviewer Package v2.0.0
Automated code review system met AI integratie, BMAD Method ondersteuning 
en universele post-edit hooks voor continue kwaliteitsbewaking.

Nieuwe features v2.0.0:
- Universal BMAD post-edit hooks
- Enhanced SQL injection detection 
- AI agent auto-detection
- Context-aware false positive filtering
- Extended BMAD integration
"""

__version__ = "2.0.0"
__author__ = "Chris Lehnen"
__email__ = "chris@example.com"

from .core import AICodeReviewer, ReviewResult, ReviewIssue
from .cli import main

__all__ = [
    "AICodeReviewer", 
    "ReviewResult", 
    "ReviewIssue",
    "main"
]