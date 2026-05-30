"""Entegrasyon URL yardımcıları."""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse

from common.module_catalog import module_by_slug

CAPABILITIES_HUB_URL_NAME = 'capabilities_hub'


def resolve_capabilities_hub_url() -> str | None:
    try:
        return reverse(CAPABILITIES_HUB_URL_NAME)
    except NoReverseMatch:
        return None


def resolve_integration_url(module_slug: str) -> str | None:
    mod = module_by_slug(module_slug)
    if not mod or not mod.get('hub_url_name'):
        return None
    try:
        return reverse(mod['hub_url_name'])
    except NoReverseMatch:
        return None
