from __future__ import annotations


class AppError(Exception):
    """Base application exception."""


class NotFoundError(AppError):
    """Raised when an entity is not found."""


class ValidationAppError(AppError):
    """Raised for domain-level validation errors."""


class IntegrationError(AppError):
    """Raised for external integration errors."""
