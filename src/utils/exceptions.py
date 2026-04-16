"""Project-specific exceptions."""

from __future__ import annotations


class PipelineError(Exception):
    """Base exception for the new NLP pipeline."""


class DataValidationError(PipelineError):
    """Raised when input data violates the declared schema."""


class LabelMappingError(PipelineError):
    """Raised when labels cannot be mapped safely."""
