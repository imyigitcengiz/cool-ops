"""Veritabanı yapılandırması — PostgreSQL (önerilen) veya SQLite (geliştirme yedeği)."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse


def _env(name: str, default: str = '') -> str:
    return os.environ.get(name, default).strip()


def _postgres_options() -> dict:
    options: dict = {
        'connect_timeout': int(_env('POSTGRES_CONNECT_TIMEOUT', '10') or '10'),
    }
    sslmode = _env('POSTGRES_SSLMODE')
    if sslmode:
        options['sslmode'] = sslmode
    return options


def _postgres_from_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ('postgres', 'postgresql'):
        raise ValueError(f'Desteklenmeyen DATABASE_URL şeması: {parsed.scheme}')
    db_name = unquote(parsed.path.lstrip('/'))
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': unquote(parsed.username or ''),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port or 5432),
        'CONN_MAX_AGE': int(_env('POSTGRES_CONN_MAX_AGE', '60') or '60'),
        'OPTIONS': _postgres_options(),
    }


def _postgres_from_env() -> dict:
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _env('POSTGRES_DB', 'kobiops'),
        'USER': _env('POSTGRES_USER', 'kobiops'),
        'PASSWORD': _env('POSTGRES_PASSWORD', ''),
        'HOST': _env('POSTGRES_HOST', 'localhost'),
        'PORT': _env('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': int(_env('POSTGRES_CONN_MAX_AGE', '60') or '60'),
        'OPTIONS': _postgres_options(),
    }


def _sqlite_from_env(base_dir: Path) -> dict:
    name = base_dir / 'db.sqlite3'
    db_path = _env('DJANGO_DB_PATH')
    if db_path:
        name = Path(db_path)
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': name,
    }


def build_databases(base_dir: Path) -> dict:
    """
    Öncelik:
      1. DATABASE_URL (postgresql://…)
      2. POSTGRES_HOST
      3. SQLite (DJANGO_DB_PATH veya db.sqlite3)
    """
    database_url = _env('DATABASE_URL')
    if database_url:
        return {'default': _postgres_from_url(database_url)}

    if _env('POSTGRES_HOST') or _env('DJANGO_DB_ENGINE') == 'postgresql':
        return {'default': _postgres_from_env()}

    return {'default': _sqlite_from_env(base_dir)}
