"""Shared startup hooks for IPE services."""

from ipe_shared.config_validator import validate_config_fatal


def validate_startup_config() -> None:
    """Fail fast when critical environment variables are missing."""
    validate_config_fatal()
