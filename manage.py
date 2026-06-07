#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _prepare_runserver_argv(argv):
    """runserver: istenen port doluysa bir sonraki boş porta kaydır."""
    if len(argv) < 2 or argv[1] != 'runserver':
        return argv

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        import django

        django.setup()
    except Exception:
        return argv

    from common.dev_server import (
        apply_dev_port,
        find_available_port,
        parse_addrport,
        port_is_available,
    )

    use_ipv6 = '--ipv6' in argv or '-6' in argv
    addrport = None
    for arg in argv[2:]:
        if arg.startswith('-'):
            continue
        addrport = arg
        break

    try:
        host, requested_port = parse_addrport(addrport, use_ipv6=use_ipv6)
    except ValueError:
        return argv

    port = requested_port
    if not port_is_available(host, port):
        port = find_available_port(host, start_port=requested_port)
        print(
            f'Port {requested_port} dolu — sunucu {port} portunda başlatılıyor.',
            file=sys.stderr,
        )

    apply_dev_port(port)
    resolved = f'{host}:{port}'

    new_argv = list(argv)
    if addrport is not None:
        for idx, arg in enumerate(new_argv[2:], start=2):
            if not arg.startswith('-'):
                new_argv[idx] = resolved
                break
    else:
        new_argv.insert(2, resolved)
    return new_argv


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(_prepare_runserver_argv(sys.argv))


if __name__ == '__main__':
    main()
