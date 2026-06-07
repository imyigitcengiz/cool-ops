"""Modül kurulum aç/kapa — abonelik sahibi plan tavanı içinde."""

from __future__ import annotations

from common.brand_team import is_subscription_owner
from common.module_catalog import module_by_slug
from common.module_particles import particle_by_slug, resolve_particle_slug
from common.module_plan import (
    owner_selected_modules,
    owner_selected_particles,
    plan_included_modules,
    plan_included_particles,
    subscription_owner_for_user,
)
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
    slugs = {mod['slug']}
    for particle in mod.get('particle_slugs', ()):
        slugs.add(particle)
    for app_slug, particle_slug in MODULE_PARTICLE_FALLBACK.items():
        if app_slug == mod['slug'] or particle_slug in mod.get('particle_slugs', ()):
            slugs.add(particle_slug)
    return slugs


def _toggle_owner(user):
    if not user or not user.is_authenticated or user.is_superuser:
        return None
    return subscription_owner_for_user(user) or (user if is_subscription_owner(user) else None)


def _active_toggle_sets(owner):
    plan_mods = set(plan_included_modules(owner.active_plan))
    plan_parts = set(plan_included_particles(owner.active_plan))
    stored = list(getattr(owner, 'enabled_module_slugs', None) or [])
    stored_mods = [s for s in stored if not str(s).startswith('p.')]
    stored_parts = [s for s in stored if str(s).startswith('p.')]

    if stored_mods:
        active_mods = {s for s in owner_selected_modules(owner)}
    else:
        active_mods = set(plan_mods)

    if stored_parts:
        active_parts = {s for s in owner_selected_particles(owner)}
    else:
        active_parts = set(plan_parts)

    return plan_mods, plan_parts, active_mods, active_parts, bool(stored_mods), bool(stored_parts)


def _persist_owner_slugs(owner, modules: set[str], particles: set[str]) -> None:
    owner.enabled_module_slugs = sorted(modules) + sorted(particles)
    owner.save(update_fields=['enabled_module_slugs'])


def user_can_manage_modules(user) -> bool:
    if not user.is_authenticated or user.is_superuser:
        return False
    owner = _toggle_owner(user)
    if not owner:
        return False
    if owner.pk == user.pk:
        return True
    return user.has_perm_codename('access.settings')


def toggle_module_slug(user, slug: str) -> dict:
    if not user_can_manage_modules(user):
        return {'ok': False, 'error': 'Modül ayarları için yetkiniz yok.'}

    owner = _toggle_owner(user)
    if not owner:
        return {'ok': False, 'error': 'Abonelik sahibi bulunamadı.'}

    mod = module_by_slug(slug)
    if not mod or mod['slug'].startswith('agency_'):
        return {'ok': False, 'error': 'Geçersiz modül.'}

    plan_mods, plan_parts, active_mods, active_parts, explicit_mods, _ = _active_toggle_sets(owner)
    if slug not in plan_mods:
        return {'ok': False, 'error': 'Bu modül mevcut planınızda yok. Plana yükseltin.'}

    was_installed = slug in active_mods

    if was_installed:
        if not mod.get('can_disable', True):
            return {'ok': False, 'error': 'Bu modül kapatılamaz.'}
        disableable = [s for s in active_mods if module_by_slug(s) and module_by_slug(s).get('can_disable', True)]
        if len(disableable) <= 1:
            return {'ok': False, 'error': 'En az bir modül açık kalmalı.'}
        if explicit_mods:
            new_mods = active_mods - {slug}
        else:
            new_mods = plan_mods - {slug}
        new_parts = set(active_parts)
        for related in _related_slugs_for_disable(mod):
            if related.startswith('p.'):
                new_parts.discard(related)
        message = f'"{mod["name"]}" kapatıldı.'
        level = 'info'
    else:
        if explicit_mods:
            new_mods = set(active_mods)
            new_mods.add(slug)
        else:
            new_mods = set(plan_mods)
        new_parts = set(active_parts)
        message = f'"{mod["name"]}" açıldı.'
        level = 'success'

    _persist_owner_slugs(owner, new_mods, new_parts)

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


def toggle_particle_slug(user, slug: str) -> dict:
    if not user_can_manage_modules(user):
        return {'ok': False, 'error': 'Modül ayarları için yetkiniz yok.'}

    owner = _toggle_owner(user)
    if not owner:
        return {'ok': False, 'error': 'Abonelik sahibi bulunamadı.'}

    slug = resolve_particle_slug(slug)
    particle = particle_by_slug(slug)
    if not particle or slug.startswith('p.agency'):
        return {'ok': False, 'error': 'Geçersiz özellik.'}

    parent = particle.get('parent_module')
    if parent and parent not in owner_selected_modules(owner):
        mod = module_by_slug(parent)
        name = mod['name'] if mod else parent
        return {'ok': False, 'error': f'Önce "{name}" modülünü açın.'}

    plan_mods, plan_parts, active_mods, active_parts, explicit_mods, explicit_parts = _active_toggle_sets(owner)
    if slug not in plan_parts:
        return {'ok': False, 'error': 'Bu özellik mevcut planınızda yok. Plana yükseltin.'}

    was_enabled = slug in active_parts

    if was_enabled:
        if explicit_parts:
            new_parts = active_parts - {slug}
        else:
            new_parts = plan_parts - {slug}
        message = f'"{particle["name"]}" kapatıldı.'
        level = 'info'
    else:
        if explicit_parts or explicit_mods:
            new_parts = set(active_parts)
            new_parts.add(slug)
        else:
            new_parts = set(plan_parts)
        message = f'"{particle["name"]}" açıldı.'
        level = 'success'

    new_mods = set(active_mods) if explicit_mods else set(plan_mods)
    _persist_owner_slugs(owner, new_mods, new_parts)

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
