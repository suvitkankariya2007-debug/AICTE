import os
from dataclasses import dataclass
from urllib.parse import urlparse


def _required_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{name} must be true or false")
    return normalized == "true"


def _validate_database_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"sqlite", "postgresql", "postgres", "postgresql+psycopg"}:
        raise ValueError("DATABASE_URL must use sqlite or postgresql")
    if parsed.scheme == "sqlite" and not parsed.path:
        raise ValueError("DATABASE_URL must include a SQLite database path")
    if parsed.scheme in {"postgresql", "postgres", "postgresql+psycopg"} and not parsed.hostname:
        raise ValueError("DATABASE_URL must include a PostgreSQL host")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    cookie_secure: bool
    frontend_origin: str
    demo_mode: bool
    auto_create_schema: bool


def load_settings() -> Settings:
    database_url = _validate_database_url(
        os.getenv("DATABASE_URL", "sqlite:///./aicte.db")
    )
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip()
    if not frontend_origin:
        raise ValueError("FRONTEND_ORIGIN must not be empty")
    return Settings(
        database_url=database_url,
        cookie_secure=_required_bool(
            os.getenv("COOKIE_SECURE", "false"), "COOKIE_SECURE"
        ),
        frontend_origin=frontend_origin,
        demo_mode=_required_bool(os.getenv("DEMO_MODE", "true"), "DEMO_MODE"),
        auto_create_schema=_required_bool(
            os.getenv("AUTO_CREATE_SCHEMA", "true"), "AUTO_CREATE_SCHEMA"
        ),
    )
