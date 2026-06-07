"""Yerel geliştirme sunucusu için port seçimi."""

from __future__ import annotations

import re
import socket

from django.conf import settings

_ADDRPORT_RE = re.compile(
    r"""^(?:
    (?P<addr>
        (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |
        (?P<ipv6>\[[a-fA-F0-9:]+\]) |
        (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)
    ):)?(?P<port>\d+)$""",
    re.X,
)


def parse_addrport(addrport: str | None, *, use_ipv6: bool = False) -> tuple[str, int]:
    if not addrport:
        host = '::1' if use_ipv6 else '127.0.0.1'
        return host, 8000

    match = _ADDRPORT_RE.match(addrport)
    if match is None:
        raise ValueError(f'"{addrport}" geçerli bir port veya adres:port değil.')

    addr, _ipv4, _ipv6, _fqdn, port_text = match.groups()
    port = int(port_text)
    if addr:
        if _ipv6:
            return addr[1:-1], port
        return addr, port
    return ('::1' if use_ipv6 else '127.0.0.1'), port


def port_is_available(host: str, port: int) -> bool:
    family = socket.AF_INET6 if ':' in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_available_port(host: str, start_port: int = 8000, max_tries: int = 20) -> int:
    for offset in range(max_tries):
        port = start_port + offset
        if port_is_available(host, port):
            return port
    raise RuntimeError(
        f'{host} üzerinde {start_port}–{start_port + max_tries - 1} aralığında boş port bulunamadı.'
    )


def csrf_origins_for_port(port: int) -> list[str]:
    from config.settings import _csrf_origins_for_port

    return _csrf_origins_for_port(port)


def apply_dev_port(port: int) -> None:
    settings.CSRF_TRUSTED_ORIGINS = csrf_origins_for_port(port)
