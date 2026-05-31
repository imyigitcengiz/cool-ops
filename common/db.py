"""Veritabanı motoru yardımcıları."""

from __future__ import annotations

from django.conf import settings


def database_engine() -> str:
    return settings.DATABASES['default']['ENGINE']


def uses_sqlite() -> bool:
    return database_engine().endswith('sqlite3')


def uses_postgresql() -> bool:
    return 'postgresql' in database_engine()


def database_label() -> str:
    if uses_postgresql():
        db = settings.DATABASES['default']
        host = db.get('HOST') or 'localhost'
        name = db.get('NAME') or 'postgres'
        return f'PostgreSQL ({host}/{name})'
    name = settings.DATABASES['default'].get('NAME', '')
    return f'SQLite ({name})'
