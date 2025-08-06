"""
Módulo de validações automáticas de documentação
"""

from .document_validator import DocumentValidator, ValidationReport, ValidationIssue, ValidationSeverity

__all__ = ['DocumentValidator', 'ValidationReport', 'ValidationIssue', 'ValidationSeverity']