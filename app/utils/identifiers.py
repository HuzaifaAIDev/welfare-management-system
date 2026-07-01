"""Helpers for generating human-friendly display IDs (e.g. DON-0001)."""


def format_id(prefix: str, numeric_id: int) -> str:
    """Format a numeric primary key into a zero-padded, prefixed display ID."""
    return f"{prefix}-{numeric_id:04d}"
