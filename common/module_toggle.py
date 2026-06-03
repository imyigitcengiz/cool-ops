"""Modül kurulum aç/kapa — API ve form POST ortak mantığı."""

from __future__ import annotations

from common.module_catalog import module_by_slug
from common.module_particles import particle_by_slug, resolve_particle_slug
from common.module_runtime import (
    MODULE_PARTICLE_FALLBACK,
    build_module_hub_context,
    build_module_record,
    build_particles_by_parent_module,
    get_enabled_module_slugs,
    get_enabled_particle_slugs,
    is_module_installed,
    is_particle_enabled,
)


def _related_slugs_for_disable(mod: dict) -> set[str]:
    """Modül kapatılırken listeden çıkarılacak slug'lar (parçacık yedekleri dahil)."""
    slugs = {mod['slug']}
    for particle in mod.get('particle_slugs', ()):
        slugs.add(particle)
    for app_slug, particle_slug in MODULE_PARTICLE_FALLBACK.items():
        if app_slug == mod['slug'] or particle_slug in mod.get('particle_slugs', ()):
            slugs.add(particle_slug)
    return slugs


def user_can_manage_modules(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.has_perm_codename('access.settings'))
    )


def toggle_module_slug(user, slug: str) -> dict:
    if not user_can_manage_modules(user):
        return {'ok': False, 'error': 'Modül ayarları için yetkiniz yok.'}

    mod = module_by_slug(slug)
    if not mod or mod['slug'].startswith('agency_'):
        return {'ok': False, 'error': 'Geçersiz modül.'}

    modules = list(get_enabled_module_slugs())
    particles = set(get_enabled_particle_slugs())
    was_installed = slug in modules

    if was_installed:
        if not mod.get('can_disable', True):
            return {'ok': False, 'error': 'Bu modül kapatılamaz.'}
        disableable = [
            s for s in modules
            if module_by_slug(s) and module_by_slug(s).get('can_disable', True)
        ]
        if len(disableable) <= 1:
            return {'ok': False, 'error': 'En az bir modül açık kalmalı.'}
        modules = [s for s in modules if s != slug]
        for related in _related_slugs_for_disable(mod):
            if related.startswith('p.'):
                particles.discard(related)
            else:
                modules = [s for s in modules if s != related]
        message = f'"{mod["name"]}" kapatıldı.'
        level = 'info'
    else:
        if slug not in modules:
            modules.append(slug)
        message = f'"{mod["name"]}" açıldı.'
        level = 'success'

    _persist_enabled_slugs(modules, particles)

    record = build_module_record(user, mod)
    installed = is_module_installed(slug)
    hub = build_module_hub_context(user)

    from common.capability_hub import build_capabilities_hub_context

    caps = build_capabilities_hub_context(user)

    return {
        'ok': True,
        'slug': slug,
        'installed': installed,
        'can_open': record['can_open'],
        'open_url': record.get('open_url') or '',
        'can_toggle': record.get('can_toggle', True),
        'name': mod['name'],
        'kind': mod.get('kind'),
        'message': message,
        'level': level,
        'installed_count': hub['module_installed_count'],
        'capabilities_enabled': caps['capabilities_enabled'],
        'capabilities_total': caps['capabilities_total'],
    }


def _persist_enabled_slugs(modules: list[str], particles: set[str]) -> None:
    from core_settings.models import SiteSettings

    settings = SiteSettings.objects.first()
    if not settings:
        settings = SiteSettings.objects.create()
    settings.enabled_module_slugs = modules + sorted(particles)
    settings.save(update_fields=['enabled_module_slugs'])


def toggle_particle_slug(user, slug: str) -> dict:
    if not user_can_manage_modules(user):
        return {'ok': False, 'error': 'Modül ayarları için yetkiniz yok.'}

    slug = resolve_particle_slug(slug)
    particle = particle_by_slug(slug)
    if not particle or slug.startswith('p.agency'):
        return {'ok': False, 'error': 'Geçersiz özellik.'}

    parent = particle.get('parent_module')
    if parent and not is_module_installed(parent):
        mod = module_by_slug(parent)
        name = mod['name'] if mod else parent
        return {
            'ok': False,
            'error': f'Önce "{name}" modülünü açın.',
        }

    modules = list(get_enabled_module_slugs())
    particles = set(get_enabled_particle_slugs())
    was_enabled = slug in particles

    if was_enabled:
        particles.discard(slug)
        message = f'"{particle["name"]}" kapatıldı.'
        level = 'info'
    else:
        particles.add(slug)
        message = f'"{particle["name"]}" açıldı.'
        level = 'success'

    _persist_enabled_slugs(modules, particles)

    hub = build_module_hub_context(user)
    by_parent = build_particles_by_parent_module()
    from common.capability_hub import build_capabilities_hub_context

    caps = build_capabilities_hub_context(user)

    return {
        'ok': True,
        'slug': slug,
        'parent_module': parent,
        'enabled': is_particle_enabled(slug),
        'name': particle['name'],
        'kind': 'particle',
        'message': message,
        'level': level,
        'installed_count': hub['module_installed_count'],
        'capabilities_enabled': caps['capabilities_enabled'],
        'capabilities_total': caps['capabilities_total'],
        'particles': by_parent.get(parent or '', []),
    }
