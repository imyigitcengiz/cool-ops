"""WhatsApp Node köprüsünü başlatma — Windows'ta görünür konsol, port çakışması ve yönetici modu."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings

_LAST_SPAWN_MONO = 0.0
_DEBOUNCE_SEC = 8.0


def _bridge_base_url() -> str:
    return getattr(settings, 'WHATSAPP_BRIDGE_URL', 'http://127.0.0.1:3939').rstrip('/')


def _bridge_port() -> int:
    u = urlparse(_bridge_base_url())
    if u.port:
        return u.port
    return 3939


def _bridge_dir() -> Path:
    return Path(settings.BASE_DIR) / 'tools' / 'whatsapp_bridge'


def _log_path() -> Path:
    return _bridge_dir() / 'bridge_ui.log'


def _append_spawn_log(message: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] [spawn] {message}\n"
    try:
        _log_path().parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path(), 'a', encoding='utf-8') as fh:
            fh.write(line)
    except OSError:
        pass


def _is_local_bridge_url() -> bool:
    host = (urlparse(_bridge_base_url()).hostname or '').lower()
    return host in ('127.0.0.1', 'localhost', '::1')


def bridge_spawn_allowed() -> bool:
    """Yerel Node süreci Django tarafından başlatılabilir mi (geliştirme / Windows)."""
    if not getattr(settings, 'WHATSAPP_BRIDGE_CAN_SPAWN', True):
        return False
    return _is_local_bridge_url()


def _offline_detail_local() -> str:
    if bridge_spawn_allowed():
        return 'Köprü kapalı. "Köprüyü başlat" ile açın veya birkaç saniye bekleyin.'
    return (
        'Köprü bu sunucuda otomatik başlatılmıyor. '
        'whatsapp-bridge servisini çalıştırın ve WHATSAPP_BRIDGE_URL ayarlayın '
        '(DEPLOY.md).'
    )


def _offline_detail_remote(base: str, err: str | None = None) -> str:
    msg = f'Köprüye ulaşılamıyor ({base}).'
    if err:
        short = err.replace('\n', ' ')[:160]
        msg += f' Hata: {short}'
    msg += ' whatsapp-bridge konteynerinin/sürecinin çalıştığını doğrulayın.'
    return msg


def probe_bridge(timeout: float = 0.6) -> dict:
    """Köprü durumu: none | legacy | modern | blocked."""
    base = _bridge_base_url()
    port = _bridge_port()
    local = _is_local_bridge_url()
    can_spawn = bridge_spawn_allowed()
    out = {
        'state': 'none',
        'legacy': False,
        'modern': False,
        'detail': '',
        'can_spawn': can_spawn,
        'bridge_url': base,
        'is_local': local,
    }

    if local and not _port_is_listening(port):
        out['detail'] = _offline_detail_local()
        return out

    try:
        r_modern = requests.get(f'{base}/api/connections', timeout=timeout)
        if r_modern.ok:
            out.update(state='modern', modern=True, detail='Köprü çalışıyor.')
            return out
    except requests.RequestException as exc:
        if not local:
            out['detail'] = _offline_detail_remote(base, str(exc))
            return out

    try:
        r_legacy = requests.get(f'{base}/api/status', timeout=timeout)
        if r_legacy.ok:
            out.update(
                state='legacy',
                legacy=True,
                detail='Eski köprü sürümü algılandı; yeniden başlatın.',
            )
            return out
    except requests.RequestException:
        pass

    if local:
        if _port_is_listening(port):
            out.update(
                state='blocked',
                detail=(
                    f'Port {port} dolu ama köprü yanıt vermiyor — '
                    'süreç kapatılıp yeniden açılacak.'
                ),
            )
        else:
            out['detail'] = _offline_detail_local()
        return out

    out['detail'] = _offline_detail_remote(base)
    return out


def bridge_reachable(timeout: float = 0.8) -> bool:
    return probe_bridge(timeout).get('modern') is True


def _resolve_node_executable() -> str | None:
    configured = (getattr(settings, 'WHATSAPP_BRIDGE_NODE', '') or '').strip()
    if configured and Path(configured).is_file():
        return configured

    candidates = [
        Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'nodejs' / 'node.exe',
        Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'nodejs' / 'node.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'node' / 'node.exe',
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    found = shutil.which('node') or shutil.which('node.exe')
    if not found:
        return None
    low = found.lower()
    if 'cursor' in low and 'helpers' in low:
        _append_spawn_log(f'Uyarı: IDE içi node kullanılıyor ({found}); gerçek Node.js kurulumu önerilir.')
    return found


def _port_is_listening(port: int) -> bool:
    if sys.platform == 'win32':
        try:
            out = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        needle = f':{port}'
        for line in out.stdout.splitlines():
            if 'LISTENING' not in line.upper():
                continue
            if needle in line:
                return True
        return False

    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0


def _pid_on_port(port: int) -> int | None:
    if sys.platform != 'win32':
        return None
    try:
        out = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    pattern = re.compile(rf':{port}\s+.*?LISTENING\s+(\d+)', re.IGNORECASE)
    for line in out.stdout.splitlines():
        m = pattern.search(line.replace('\t', ' '))
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return None


def _kill_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    _append_spawn_log(f'Port {_bridge_port()} üzerindeki süreç sonlandırılıyor: PID {pid}')
    try:
        if sys.platform == 'win32':
            r = subprocess.run(
                ['taskkill', '/PID', str(pid), '/F', '/T'],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
            return r.returncode == 0
        os.kill(pid, 9)
        return True
    except OSError as exc:
        _append_spawn_log(f'taskkill başarısız: {exc}')
        return False


def _ensure_start_script(node_exe: str, bridge_dir: Path) -> Path:
    bat = bridge_dir / 'start_bridge.cmd'
    content = f'''@echo off
chcp 65001 >nul
title GY WhatsApp Bridge
cd /d "{bridge_dir}"
echo [%date% %time%] Köprü baslatiliyor...
echo Node: "{node_exe}"
"{node_exe}" server.js
if errorlevel 1 (
  echo.
  echo HATA: Köprü kapandi. Yukaridaki kirmizi mesaji okuyun.
  echo node_modules yoksa: npm install
  pause
)
'''
    bat.write_text(content, encoding='utf-8')
    return bat


def _spawn_windows(node_exe: str, bridge_dir: Path, bat_path: Path, *, as_admin: bool) -> None:
    bat_quoted = str(bat_path).replace("'", "''")
    work_quoted = str(bridge_dir).replace("'", "''")

    if as_admin:
        ps = (
            f"Start-Process -FilePath '{bat_quoted}' "
            f"-WorkingDirectory '{work_quoted}' -Verb RunAs"
        )
        _append_spawn_log('Yönetici olarak başlatılıyor (UAC penceresi gelebilir)…')
        subprocess.Popen(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps],
            cwd=str(bridge_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        return

    _append_spawn_log('Görünür CMD penceresinde başlatılıyor…')
    subprocess.Popen(
        ['cmd', '/c', 'start', 'GY WhatsApp Bridge', '/D', str(bridge_dir), str(bat_path)],
        cwd=str(bridge_dir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def try_spawn_bridge_process(*, force: bool = False, as_admin: bool | None = None) -> dict:
    global _LAST_SPAWN_MONO

    probe = probe_bridge()

    if not bridge_spawn_allowed():
        return {
            'spawned': False,
            'reason': 'spawn_disabled',
            'message': probe.get('detail') or _offline_detail_local(),
            'probe': probe,
        }

    now = time.monotonic()
    if not force and now - _LAST_SPAWN_MONO < _DEBOUNCE_SEC:
        return {
            'spawned': False,
            'reason': 'recent',
            'message': 'Az önce başlatma denendi; birkaç saniye bekleyin.',
            'probe': probe,
        }

    if probe['modern']:
        return {'spawned': False, 'reason': 'already_running', 'message': None, 'probe': probe}

    if not _is_local_bridge_url():
        return {
            'spawned': False,
            'reason': 'not_localhost',
            'message': 'WHATSAPP_BRIDGE_URL yerel adres değil; otomatik başlatılamıyor.',
            'probe': probe,
        }

    bridge_dir = _bridge_dir()
    server_js = bridge_dir / 'server.js'
    if not server_js.is_file():
        return {
            'spawned': False,
            'reason': 'missing_dir',
            'message': 'tools/whatsapp_bridge/server.js bulunamadı.',
            'probe': probe,
        }

    if not (bridge_dir / 'node_modules').is_dir():
        return {
            'spawned': False,
            'reason': 'no_node_modules',
            'message': (
                'Köprü bağımlılıkları yok. Terminalde: '
                f'cd "{bridge_dir}" && npm install'
            ),
            'probe': probe,
        }

    node_exe = _resolve_node_executable()
    if not node_exe:
        return {
            'spawned': False,
            'reason': 'no_node',
            'message': 'Node.js bulunamadı. https://nodejs.org kurun veya WHATSAPP_BRIDGE_NODE ayarlayın.',
            'probe': probe,
        }

    port = _bridge_port()
    killed_pid = None
    if probe['state'] in ('legacy', 'blocked') or (probe['state'] == 'none' and _port_is_listening(port)):
        pid = _pid_on_port(port)
        if pid:
            if not _kill_pid(pid):
                return {
                    'spawned': False,
                    'reason': 'port_blocked',
                    'message': (
                        f'Port {port} meşgul (PID {pid}). '
                        'Görev Yöneticisi\'nden node.exe sürecini kapatın veya Django\'yu yönetici olarak çalıştırın.'
                    ),
                    'probe': probe,
                    'pid': pid,
                }
            killed_pid = pid
            time.sleep(1.0)

    if as_admin is None:
        as_admin = bool(force and getattr(settings, 'WHATSAPP_BRIDGE_RUN_AS_ADMIN', False))

    _LAST_SPAWN_MONO = now
    bat_path = _ensure_start_script(node_exe, bridge_dir)
    _append_spawn_log(f'Başlat: node={node_exe} admin={as_admin} port={port} killed={killed_pid}')

    try:
        if sys.platform == 'win32':
            _spawn_windows(node_exe, bridge_dir, bat_path, as_admin=as_admin)
        else:
            subprocess.Popen(
                [node_exe, str(server_js)],
                cwd=str(bridge_dir),
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
    except OSError as exc:
        _append_spawn_log(f'Popen hatası: {exc}')
        return {
            'spawned': False,
            'reason': 'exec_error',
            'message': str(exc),
            'probe': probe,
        }

    return {
        'spawned': True,
        'reason': None,
        'message': None,
        'probe': probe,
        'killed_pid': killed_pid,
        'as_admin': as_admin,
        'node': node_exe,
    }
