"""Authentication token classification helpers."""

from __future__ import annotations


GOOGLE_API_KEY_PREFIXES = ("AIza", "AQ.")
NANODE_TOKEN_PREFIX = "nk_"


def normalize_token(token: str | None) -> str:
    return (token or "").strip()


def is_nanode_token(token: str | None) -> bool:
    return normalize_token(token).startswith(NANODE_TOKEN_PREFIX)


def is_google_api_key(token: str | None) -> bool:
    value = normalize_token(token)
    return len(value) >= 20 and value.startswith(GOOGLE_API_KEY_PREFIXES)


def is_configured_token(token: str | None) -> bool:
    return bool(normalize_token(token))
