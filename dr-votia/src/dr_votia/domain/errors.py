"""Domain-level exceptions."""

from __future__ import annotations


class DrContextoError(Exception):
    """Base class for all domain errors."""


class UnsupportedFormatError(DrContextoError):
    """No registered reader can handle the given file."""
