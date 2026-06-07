"""İstek bazlı modül kullanıcı bağlamı."""

from __future__ import annotations

from contextvars import ContextVar

_module_user: ContextVar = ContextVar('module_user', default=None)


def bind_module_user(user):
    return _module_user.set(user)


def reset_module_user(token) -> None:
    _module_user.reset(token)


def current_module_user():
    return _module_user.get()
