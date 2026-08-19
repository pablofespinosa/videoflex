#!/usr/bin/env python3
"""
VideoFlex - Descargador Universal de Videos y Torrents
Versión: 1.5.1
Autor: Pablo F. Espinosa
Empresa: PFE Computación
Copyright (C) 2025-2026

Este programa es software libre: puedes redistribuirlo y/o modificarlo
bajo los términos de la Licencia Pública General de GNU publicada por
la Free Software Foundation, ya sea la versión 3 de la Licencia, o
(a tu elección) cualquier versión posterior.

Este programa se distribuye con la esperanza de que sea útil,
pero SIN GARANTÍA ALGUNA; ni siquiera la garantía implícita de
COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la
Licencia Pública General de GNU para más detalles.

Deberías haber recibido una copia de la Licencia Pública General de GNU
junto con este programa. Si no, vea <https://www.gnu.org/licenses/>.
"""

import flet as ft
import requests
import json
import os
import threading
import time
import platform
import asyncio
import webbrowser
from pathlib import Path
import urllib.parse
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
import subprocess
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog
import pyperclip
import psutil
from datetime import datetime, timedelta
import re
import csv
from collections import deque

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL
# ═══════════════════════════════════════════════════════════════
APP_NAME = "VideoFlex"
APP_VERSION = "1.6.0"
APP_AUTHOR = "Pablo F. Espinosa"
APP_COMPANY = "PFE Computación"
APP_YEAR = "2025-2026"
APP_DESCRIPTION = "Descargador Universal de Videos y Torrents"
APP_GITHUB_URL = "https://github.com/pablofespinosa/videoflex"
APP_LICENSE = "GPL-3.0"

# Archivo de log de errores
ERROR_LOG_FILE = Path.home() / ".videoflex_errors.log"
LOG_FILE = Path.home() / ".videoflex_app.log"

# Archivos de persistencia (globales)
CONFIG_FILE = Path.home() / ".videoflex_config.json"
HISTORY_FILE = Path.home() / ".videoflex_history.json"
CLIPBOARD_HISTORY_FILE = Path.home() / ".videoflex_clipboard.json"


# ═══════════════════════════════════════════════════════════════
# SISTEMA DE LOGGING MEJORADO
# ═══════════════════════════════════════════════════════════════
class AppLogger:
    def __init__(self):
        self.max_log_size = 5 * 1024 * 1024  # 5MB
        self.max_backups = 3

    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        try:
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > self.max_log_size:
                self._rotate_logs()
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass

    def _rotate_logs(self):
        for i in range(self.max_backups - 1, 0, -1):
            old_file = LOG_FILE.parent / f"{LOG_FILE.name}.{i}"
            new_file = LOG_FILE.parent / f"{LOG_FILE.name}.{i+1}"
            if old_file.exists():
                shutil.move(old_file, new_file)
        if LOG_FILE.exists():
            shutil.move(LOG_FILE, LOG_FILE.parent / f"{LOG_FILE.name}.1")

    def info(self, msg: str):
        self.log("INFO", msg)

    def error(self, msg: str):
        self.log("ERROR", msg)
        try:
            with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] {msg}\n")
        except Exception:
            pass

    def debug(self, msg: str):
        self.log("DEBUG", msg)

    def warning(self, msg: str):
        self.log("WARNING", msg)


logger = AppLogger()


# ═══════════════════════════════════════════════════════════════
# FUNCIONES HELPER PARA FLET
# ═══════════════════════════════════════════════════════════════
def with_opacity(opacity: float, color: str) -> str:
    """Convierte un color con opacidad a formato rgba."""
    color_map = {
        "white": "#ffffff",
        "black": "#000000",
        "red": "#ff0000",
        "green": "#00ff00",
        "blue": "#0000ff",
        "grey": "#808080",
        "orange": "#ffa500",
        "purple": "#800080",
    }
    color = color_map.get(color.lower(), color)
    if color.startswith("#"):
        hex_color = color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {opacity})"
        except ValueError:
            return color
    return color


# ═══════════════════════════════════════════════════════════════
# FUNCIONES MULTIPLATAFORMA
# ═══════════════════════════════════════════════════════════════
def get_default_download_path():
    """Retorna la ruta de descargas predeterminada según el SO."""
    home = Path.home()
    if platform.system() == "Windows":
        return str(home / "Downloads" / "VideoFlex")
    elif platform.system() == "Darwin":
        return str(home / "Downloads" / "VideoFlex")
    else:
        downloads = home / "Downloads"
        if downloads.exists():
            return str(downloads / "VideoFlex")
        return str(home / "VideoFlex")


def get_default_video_path():
    """Ruta predeterminada para videos."""
    base = get_default_download_path()
    return os.path.join(base, "Videos")


def get_default_torrent_path():
    """Ruta predeterminada para torrents."""
    base = get_default_download_path()
    return os.path.join(base, "Torrents")


def get_vlc_executable():
    """Retorna la ruta del ejecutable de VLC según el SO."""
    system = platform.system()
    if system == "Windows":
        vlc_paths = [
            os.environ.get('PROGRAMFILES', 'C:\\Program Files') + '\\VideoLAN\\VLC\\vlc.exe',
            os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)') + '\\VideoLAN\\VLC\\vlc.exe',
            'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe',
            'C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe',
        ]
        for path in vlc_paths:
            if os.path.exists(path):
                return path
        return "vlc.exe"
    elif system == "Darwin":
        mac_paths = [
            "/Applications/VLC.app/Contents/MacOS/VLC",
            os.path.expanduser("~/Applications/VLC.app/Contents/MacOS/VLC"),
        ]
        for path in mac_paths:
            if os.path.exists(path):
                return path
        return "vlc"
    else:
        linux_paths = ["/usr/bin/vlc", "/usr/local/bin/vlc", "/snap/bin/vlc", "/usr/bin/flatpak"]
        for path in linux_paths:
            if os.path.exists(path):
                return path
        return "vlc"


def get_qbittorrent_executable():
    """Localiza el ejecutable de qBittorrent segun el SO."""
    system = platform.system()
    if system == "Windows":
        candidates = []
        for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            base = os.environ.get(env, '')
            if base:
                candidates.append(os.path.join(base, 'qBittorrent', 'qbittorrent.exe'))
                candidates.append(os.path.join(base, 'Programs', 'qBittorrent', 'qbittorrent.exe'))
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return shutil.which('qbittorrent')
    elif system == "Darwin":
        p = "/Applications/qBittorrent.app/Contents/MacOS/qbittorrent"
        return p if os.path.exists(p) else shutil.which('qbittorrent')
    else:
        return shutil.which('qbittorrent') or '/usr/bin/qbittorrent'

def open_file_externally(file_path: str):
    """Abre un archivo con el programa predeterminado del sistema."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(file_path)
        elif system == "Darwin":
            subprocess.call(['open', file_path])
        else:
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception as e:
        logger.error(f"Error abriendo archivo: {e}")
        return False


def open_folder_externally(folder_path: str):
    """Abre una carpeta en el explorador de archivos del sistema."""
    system = platform.system()
    try:
        if system == "Windows":
            if os.path.isfile(folder_path):
                subprocess.run(['explorer', '/select,', folder_path])
            else:
                subprocess.run(['explorer', folder_path])
        elif system == "Darwin":
            if os.path.isfile(folder_path):
                subprocess.call(['open', '-R', folder_path])
            else:
                subprocess.call(['open', folder_path])
        else:
            if os.path.isfile(folder_path):
                subprocess.call(['xdg-open', os.path.dirname(folder_path)])
            else:
                subprocess.call(['xdg-open', folder_path])
        return True
    except Exception as e:
        logger.error(f"Error abriendo carpeta: {e}")
        return False


def get_ffmpeg_path():
    """Retorna la ruta de ffmpeg según el SO."""
    system = platform.system()
    if system == "Windows":
        ffmpeg_paths = [
            os.environ.get('PROGRAMFILES', 'C:\\Program Files') + '\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            os.path.expanduser('~\\scoop\\apps\\ffmpeg\\current\\bin\\ffmpeg.exe'),
        ]
        for path in ffmpeg_paths:
            if os.path.exists(path):
                return path
    elif system == "Darwin":
        mac_paths = ["/usr/local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg"]
        for path in mac_paths:
            if os.path.exists(path):
                return path
    else:
        linux_paths = ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/snap/bin/ffmpeg"]
        for path in linux_paths:
            if os.path.exists(path):
                return path
    return shutil.which("ffmpeg") or "ffmpeg"


def play_notification_sound():
    """Reproduce un sonido de notificación según el SO."""
    try:
        current_os = platform.system()
        if current_os == "Windows":
            import winsound
            winsound.MessageBeep()
        elif current_os == "Darwin":
            os.system('afplay /System/Library/Sounds/Glass.aiff &')
        else:
            os.system(
                'paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || '
                'aplay /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null &'
            )
    except Exception:
        pass


def validate_video_url(url: str) -> Tuple[bool, str]:
    """Valida si la URL es de una plataforma soportada."""
    if not url:
        return False, "URL vacía"
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False, "Esquema de URL inválido"
    supported_domains = [
        'youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com',
        'twitter.com', 'x.com', 'facebook.com', 'vimeo.com',
        'dailymotion.com', 'twitch.tv', 'reddit.com', 'fb.watch'
    ]
    domain = parsed.netloc.lower()
    for d in supported_domains:
        if d in domain:
            return True, ""
    return True, ""  # Permitir URLs genéricas


# ═══════════════════════════════════════════════════════════════
# SISTEMA DE NOTIFICACIONES NATIVAS
# ═══════════════════════════════════════════════════════════════
class NotificationManager:
    def __init__(self):
        self.enabled = True
        self.system = platform.system()

    def notify(self, title: str, message: str):
        if not self.enabled:
            return
        try:
            if self.system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=3, threaded=True)
                except ImportError:
                    try:
                        import winsound
                        winsound.MessageBeep()
                    except ImportError:
                        pass
            elif self.system == "Darwin":
                script = f'display notification "{message}" with title "{title}" sound name "Glass"'
                subprocess.run(['osascript', '-e', script], check=False)
            else:
                subprocess.run([
                    'notify-send',
                    '--app-name=VideoFlex',
                    '--icon=video-x-generic',
                    title,
                    message
                ], check=False)
        except Exception as e:
            logger.error(f"Error en notificación: {e}")


notification_mgr = NotificationManager()


# ═══════════════════════════════════════════════════════════════
# MONITOR DE ESPACIO EN DISCO
# ═══════════════════════════════════════════════════════════════
class DiskSpaceMonitor:
    @staticmethod
    def get_free_space(path: str) -> Tuple[float, float, float]:
        """Retorna (libre_gb, total_gb, usado_gb)."""
        try:
            usage = psutil.disk_usage(path)
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            return free_gb, total_gb, used_gb
        except Exception:
            return 0.0, 0.0, 0.0

    @staticmethod
    def has_enough_space(path: str, required_mb: float = 100) -> bool:
        free, _, _ = DiskSpaceMonitor.get_free_space(path)
        return free * 1024 > required_mb


# ═══════════════════════════════════════════════════════════════
# ENUMS Y DATACLASSES
# ═══════════════════════════════════════════════════════════════
class DownloadStatus(Enum):
    PENDING = "Pendiente"
    QUEUED = "En Cola"
    DOWNLOADING = "Descargando"
    COMPLETED = "Completado ✓"
    ERROR = "Error"
    CANCELLED = "Cancelado"
    PAUSED = "Pausado"


@dataclass
class VideoDownload:
    id: int
    name: str
    progress: float = 0.0
    status: DownloadStatus = DownloadStatus.PENDING
    speed: str = "0 KB/s"
    thumbnail: Optional[str] = None
    filepath: Optional[str] = None
    url: str = ""
    error_msg: str = ""
    _cancelled: bool = field(default=False, repr=False)
    _paused: bool = field(default=False, repr=False)
    added_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_size: int = 0
    quality: str = "1080"
    use_cookies: bool = False
    cookies_path: str = ""
    audio_only: bool = False
    audio_format: str = "mp3"
    scheduled_time: Optional[str] = None

    def cancel(self):
        self._cancelled = True
        self.status = DownloadStatus.CANCELLED

    def pause(self):
        self._paused = not self._paused
        self.status = DownloadStatus.PAUSED if self._paused else DownloadStatus.DOWNLOADING


@dataclass
class AppConfig:
    qb_host: str = "http://localhost"
    qb_port: str = "8080"
    qb_user: str = "admin"
    qb_pass: str = "adminadmin"
    auto_connect: bool = True
    video_path: str = field(default_factory=get_default_video_path)
    torrent_path: str = field(default_factory=get_default_torrent_path)
    theme: str = "dark"
    use_cookies: bool = False
    cookies_path: str = field(default_factory=lambda: str(Path.home() / ".videoflex_cookies.txt"))
    video_quality: str = "1080"
    max_concurrent_downloads: int = 3
    notifications_enabled: bool = True
    auto_start_downloads: bool = True
    minimize_to_tray: bool = False
    check_updates: bool = True
    auto_update_ytdlp: bool = False
    proxy_enabled: bool = False
    proxy_url: str = ""
    proxy_username: str = ""
    proxy_password: str = ""
    auto_detect_cookies: bool = False
    cookies_browser: str = "chrome"
    subtitles_enabled: bool = False
    subtitles_langs: str = "es"
    subtitles_format: str = "srt"
    embed_subtitles: bool = False
    auto_convert_to_mp4: bool = True


# ═══════════════════════════════════════════════════════════════
# GESTOR DE HISTORIAL DE PORTAPAPELES
# ═══════════════════════════════════════════════════════════════
class ClipboardHistory:
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self._history: deque = deque(maxlen=max_items)
        self._load()

    def _load(self):
        try:
            if CLIPBOARD_HISTORY_FILE.exists():
                with open(CLIPBOARD_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._history = deque(data[-self.max_items:], maxlen=self.max_items)
        except Exception:
            pass

    def _save(self):
        try:
            with open(CLIPBOARD_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self._history), f, indent=2)
        except Exception:
            pass

    def add(self, url: str):
        if url and url not in self._history:
            self._history.appendleft(url)
            self._save()

    def get_recent(self, count: int = 5) -> List[str]:
        return list(self._history)[:count]

    def clear(self):
        self._history.clear()
        self._save()


# ═══════════════════════════════════════════════════════════════
# GESTOR DE HISTORIAL MEJORADO
# ═══════════════════════════════════════════════════════════════
class DownloadHistory:
    def __init__(self):
        self._history: List[Dict] = []
        self._load_history()

    def _load_history(self):
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")

    def add_entry(self, name: str, url: str, filepath: str, size_bytes: int = 0,
                  duration: float = 0, quality: str = "1080"):
        entry = {
            "name": name,
            "url": url,
            "filepath": filepath,
            "size_bytes": size_bytes,
            "duration_seconds": duration,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "date": time.strftime("%Y-%m-%d"),
            "quality": quality,
            "platform": self._detect_platform(url)
        }
        self._history.insert(0, entry)
        self._history = self._history[:100]
        self._save_history()

    def _detect_platform(self, url: str) -> str:
        url_lower = url.lower()
        platforms = {
            'youtube.com': 'YouTube',
            'youtu.be': 'YouTube',
            'tiktok.com': 'TikTok',
            'instagram.com': 'Instagram',
            'twitter.com': 'Twitter',
            'x.com': 'Twitter',
            'facebook.com': 'Facebook',
            'vimeo.com': 'Vimeo'
        }
        for domain, name in platforms.items():
            if domain in url_lower:
                return name
        return 'Otro'

    def get_history(self, search_query: str = "", date_filter: str = "",
                    min_size_mb: float = 0) -> List[Dict]:
        filtered = self._history
        if search_query:
            filtered = [h for h in filtered if search_query.lower() in h.get('name', '').lower()]
        if date_filter:
            filtered = [h for h in filtered if h.get('date', '').startswith(date_filter)]
        if min_size_mb > 0:
            filtered = [h for h in filtered if (h.get('size_bytes', 0) / (1024 * 1024)) >= min_size_mb]
        return filtered

    def get_stats(self) -> Dict:
        total_downloads = len(self._history)
        total_size = sum(e.get('size_bytes', 0) for e in self._history)
        total_duration = sum(e.get('duration_seconds', 0) for e in self._history)
        by_date = {}
        by_platform = {}
        for e in self._history:
            date = e.get('date', 'Unknown')
            plat = e.get('platform', 'Unknown')
            by_date[date] = by_date.get(date, 0) + 1
            by_platform[plat] = by_platform.get(plat, 0) + 1
        avg_size = total_size / total_downloads if total_downloads > 0 else 0
        today = datetime.now().date()

        def _safe_date(s):
            try:
                return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
            except Exception:
                return today

        last_7_days = sum(
            1 for e in self._history
            if (today - _safe_date(e.get('date', str(today)))).days <= 7
        )
        return {
            "total_downloads": total_downloads,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_size_gb": total_size / (1024 * 1024 * 1024),
            "total_duration_seconds": total_duration,
            "average_size_mb": avg_size / (1024 * 1024),
            "by_date": by_date,
            "by_platform": by_platform,
            "recent_dates": sorted(by_date.keys(), reverse=True)[:7],
            "last_7_days": last_7_days,
            "trend": "↑" if last_7_days > (total_downloads / 4) else "↓" if last_7_days < (total_downloads / 8) else "→"
        }

    def export_to_csv(self, filepath: str) -> bool:
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Fecha', 'Nombre', 'Plataforma', 'URL', 'Tamaño_MB', 'Calidad', 'Ruta'])
                for entry in self._history:
                    writer.writerow([
                        entry.get('date', ''),
                        entry.get('name', ''),
                        entry.get('platform', ''),
                        entry.get('url', ''),
                        round(entry.get('size_bytes', 0) / (1024 * 1024), 2),
                        entry.get('quality', ''),
                        entry.get('filepath', '')
                    ])
            return True
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")
            return False

    def clear_history(self):
        self._history = []
        self._save_history()


# ═══════════════════════════════════════════════════════════════
# API QBITTORRENT MEJORADA
# ═══════════════════════════════════════════════════════════════
class QBittorrentAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = ""
        self.connected = False
        self.last_error = ""
        self._lock = threading.RLock()
        self.timeout = 10
        self.retry_count = 2
        self.version = ""

    def connect(self, host: str, port: str, username: str, password: str) -> Tuple[bool, str]:
        with self._lock:
            for attempt in range(self.retry_count):
                try:
                    host = host.strip()
                    if not host.startswith(("http://", "https://")):
                        host = f"http://{host}"
                    host = host.rstrip('/')
                    self.base_url = f"{host}:{port}/api/v2"
                    host_port = f"{host.split('://', 1)[-1]}:{port}"
                    self.session = requests.Session()
                    self.session.headers.update({
                        'Referer': f"{host}:{port}/",
                        'Origin': f"{host}:{port}",
                        'X-Forwarded-Host': host_port,
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) VideoFlex/3.1',
                        'Accept': '*/*',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept-Encoding': 'gzip, deflate',
                    })
                    login_url = f"{self.base_url}/auth/login"
                    resp = self.session.post(
                        login_url,
                        data={"username": username, "password": password},
                        timeout=self.timeout
                    )
                    resp_text = resp.text.strip().lower()
                    if 200 <= resp.status_code < 300 and resp_text not in ("fails.", "fail"):
                        version_url = f"{self.base_url}/app/version"
                        version_resp = self.session.get(version_url, timeout=self.timeout)
                        if 200 <= version_resp.status_code < 300:
                            self.connected = True
                            self.version = version_resp.text.strip()
                            self.last_error = ""
                            logger.info(f"Conectado a qBittorrent v{self.version}")
                            return True, f"✅ Conectado a qBittorrent v{self.version}"
                        elif version_resp.status_code == 403:
                            self.last_error = (
                                f"❌ Error de CSRF/autenticación (intento {attempt + 1}).\n"
                                "Asegúrate de que en qBittorrent → Configuración → WebUI:\n"
                                "• 'Habilitar protección de encabezado de anfitrión' esté desactivado, O\n"
                                "• Añade '127.0.0.1' y 'localhost' a la lista blanca de anfitriones."
                            )
                            time.sleep(1)
                            continue
                        else:
                            self.last_error = f"Error verificando sesión: HTTP {version_resp.status_code} (intenta desactivar 'Protección de encabezado' en qBittorrent)"
                            continue
                    else:
                        if resp.status_code == 403:
                            self.last_error = (
                                f"❌ Acceso denegado (HTTP 403).\n"
                                "Puede ser un bloqueo CSRF. En qBittorrent → Configuración → WebUI:\n"
                                "• Desactiva 'Habilitar protección de encabezado de anfitrión', O\n"
                                "• Añade 'localhost' y '127.0.0.1' a la lista blanca de anfitriones."
                            )
                        elif resp.status_code == 404:
                            self.last_error = "WebUI no habilitada en qBittorrent o puerto incorrecto"
                        elif resp_text in ("fails.", "fail"):
                            self.last_error = "❌ Credenciales incorrectas (usuario o contraseña)"
                        else:
                            error_msg = resp.text[:150] if resp.text else "Sin respuesta"
                            self.last_error = f"Error HTTP {resp.status_code}: {error_msg}"
                        continue
                except requests.exceptions.ConnectionError as e:
                    self.last_error = (
                        f"❌ No se puede conectar (intento {attempt + 1}/{self.retry_count}).\n"
                        f"Verifica:\n"
                        f"  1. qBittorrent está abierto\n"
                        f"  2. WebUI está habilitada (Configuración → WebUI)\n"
                        f"  3. Puerto {port} está accesible\n"
                        f"  4. Intenta usar '127.0.0.1' en vez de 'localhost'"
                    )
                    logger.error(f"ConnectionError QB: {e}")
                    time.sleep(1)
                    continue
                except requests.exceptions.Timeout:
                    self.last_error = f"⏱️ Timeout de conexión (intento {attempt + 1}/{self.retry_count})"
                    time.sleep(1)
                    continue
                except Exception as e:
                    self.last_error = f"❌ Error inesperado: {str(e)}"
                    logger.error(f"Error en connect QB: {e}")
                    time.sleep(1)
                    continue
            self.connected = False
            return False, self.last_error

    def get_torrents(self) -> List[Dict]:
        with self._lock:
            if not self.connected:
                return []
            try:
                resp = self.session.get(f"{self.base_url}/torrents/info", timeout=10)
                if 200 <= resp.status_code < 300:
                    return resp.json()
                elif resp.status_code == 403:
                    self.connected = False
                    self.last_error = "Sesión expirada"
            except Exception as e:
                self.connected = False
                self.last_error = str(e)
            return []

    def add_magnet(self, magnet: str, save_path: Optional[str] = None) -> Tuple[bool, str]:
        with self._lock:
            if not self.connected:
                return False, "No conectado a qBittorrent"
            try:
                if not magnet.startswith("magnet:?"):
                    return False, "Enlace magnet no válido (debe empezar con 'magnet:?')"
                if "xt=urn:btih:" not in magnet.lower():
                    return False, "Enlace magnet no contiene hash válido"
                data = {"urls": magnet}
                if save_path:
                    data["savepath"] = save_path
                    try:
                        os.makedirs(save_path, exist_ok=True)
                        test_path = os.path.join(save_path, ".test_permission")
                        with open(test_path, 'w') as f:
                            f.write("test")
                        os.remove(test_path)
                    except PermissionError:
                        return False, f"Error de permisos en ruta: {save_path}"
                    except OSError as e:
                        logger.warning(f"Advertencia al verificar ruta '{save_path}': {e}")
                    except Exception:
                        pass
                for attempt in range(2):
                    try:
                        resp = self.session.post(
                            f"{self.base_url}/torrents/add",
                            data=data,
                            timeout=30
                        )
                        if 200 <= resp.status_code < 300:
                            response_text = resp.text.strip().lower()
                            if response_text and "fail" in response_text:
                                if "duplicate" in response_text:
                                    return True, "⚠️ Torrent ya existe en la lista"
                                return False, f"qBittorrent rechazó el torrent: {resp.text}"
                            time.sleep(2)
                            torrents = self.get_torrents()
                            for t in torrents:
                                if t['hash'] in magnet.lower():
                                    return True, f"✅ Torrent añadido: {t['name'][:40]}..."
                            return True, "✅ Torrent enviado (verificando...)"
                        elif resp.status_code == 409:
                            return True, "⚠️ Torrent ya está en la lista"
                        elif resp.status_code == 403:
                            self.connected = False
                            return False, "Sesión expirada, reconecta en Configuración"
                        else:
                            return False, f"Error HTTP {resp.status_code}: {resp.text[:100] if resp.text else 'Sin mensaje'}"
                    except requests.exceptions.ConnectionError:
                        if attempt == 0:
                            time.sleep(1)
                            continue
                        return False, "Error de conexión con qBittorrent"
                    except Exception as e:
                        return False, f"Error: {str(e)}"
            except Exception as e:
                import traceback
                logger.error(f"Error en add_magnet: {traceback.format_exc()}")
                return False, f"Error inesperado: {str(e)[:100]}"
        return False, "Error inesperado"

    def control_torrent(self, action: str, hash_str: str) -> bool:
        if not self.connected:
            return False
        try:
            data = {"hashes": hash_str}
            if action == "delete":
                data["deleteFiles"] = "false"
            resp = self.session.post(f"{self.base_url}/torrents/{action}", data=data, timeout=5)
            return 200 <= resp.status_code < 300
        except Exception as e:
            logger.error(f"Error control_torrent: {e}")
            return False

    def get_peers(self, hash_str: str) -> List[Dict]:
        with self._lock:
            if not self.connected:
                return []
            try:
                resp = self.session.get(
                    f"{self.base_url}/sync/torrentPeers",
                    params={"hash": hash_str}, timeout=5
                )
                if 200 <= resp.status_code < 300:
                    data = resp.json()
                    peers = data.get('peers', {})
                    return list(peers.values())[:20]
            except Exception:
                pass
            return []

    def get_trackers(self, hash_str: str) -> List[Dict]:
        with self._lock:
            if not self.connected:
                return []
            try:
                resp = self.session.get(
                    f"{self.base_url}/torrents/trackers",
                    params={"hash": hash_str}, timeout=5
                )
                if 200 <= resp.status_code < 300:
                    return resp.json()
            except Exception:
                pass
            return []

    def get_global_transfer_info(self) -> Dict:
        with self._lock:
            if not self.connected:
                return {}
            try:
                resp = self.session.get(f"{self.base_url}/transfer/info", timeout=5)
                if 200 <= resp.status_code < 300:
                    return resp.json()
            except Exception:
                pass
            return {}


# ═══════════════════════════════════════════════════════════════
# GESTOR DE VIDEOS MEJORADO CON SISTEMA DE COLAS
# ═══════════════════════════════════════════════════════════════
class VideoManager:
    def __init__(self, page: ft.Page = None, max_concurrent: int = 3):
        self._downloads: Dict[int, VideoDownload] = {}
        self._lock = threading.RLock()
        self._callbacks: List[Callable] = []
        self._next_id = 0
        self._page = page
        self._active_threads: Dict[int, threading.Thread] = {}
        self._cleanup_timer = None
        self._last_notify_time = 0
        self._max_concurrent = max_concurrent
        self._download_queue: List[int] = []
        self._queue_lock = threading.RLock()
        self._active_count = 0
        self._config_ref = None

    def set_max_concurrent(self, max_concurrent: int):
        self._max_concurrent = max_concurrent

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def shutdown(self):
        self._page = None
        self._callbacks.clear()

    def _notify(self, force: bool = False):
        if not self._page:
            return
        current_time = time.time()
        if not force and current_time - self._last_notify_time < 0.5:
            return
        self._last_notify_time = current_time
        for cb in list(self._callbacks):
            try:
                cb()
            except Exception as e:
                logger.error(f"Error en callback: {e}")
        try:
            async def update_ui():
                if self._page:
                    self._page.update()
            self._page.run_task(update_ui)
        except Exception as e:
            logger.error(f"Error en update_ui: {e}")

    def get_downloads(self) -> List[VideoDownload]:
        with self._lock:
            return list(self._downloads.values())

    def get_download(self, download_id: int) -> Optional[VideoDownload]:
        with self._lock:
            return self._downloads.get(download_id)

    def cancel_download(self, download_id: int) -> bool:
        with self._lock:
            if download_id in self._downloads:
                d = self._downloads[download_id]
                d._cancel_requested = True
                proc = getattr(d, 'subprocess', None)
                if proc and proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                d.cancel()
                return True
            return False

    def pause_download(self, download_id: int) -> bool:
        with self._lock:
            if download_id in self._downloads:
                self._downloads[download_id].pause()
                return True
            return False

    def _process_queue(self):
        with self._queue_lock:
            while self._active_count < self._max_concurrent and self._download_queue:
                next_id = self._download_queue.pop(0)
                if next_id in self._downloads:
                    download = self._downloads[next_id]
                    if download.status == DownloadStatus.QUEUED:
                        self._start_download_thread(next_id)

    def _start_download_thread(self, download_id: int):
        download = self._downloads.get(download_id)
        if not download:
            return
        scheduled = getattr(download, 'scheduled_time', None)
        if scheduled:
            def _wait_and_start():
                try:
                    h, m = map(int, scheduled.split(':'))
                    now = datetime.now()
                    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    if target <= now:
                        target += timedelta(days=1)
                    wait_secs = (target - datetime.now()).total_seconds()
                    download.status = DownloadStatus.QUEUED
                    download.speed = f"⏰ Programada {scheduled}"
                    self._notify()
                    time.sleep(max(0, wait_secs))
                    download.scheduled_time = None
                except Exception:
                    pass
                self._run_download(download_id)
            t = threading.Thread(target=_wait_and_start, daemon=True, name=f"Scheduled-{download_id}")
            t.start()
            return
        self._run_download(download_id)

    def _run_download(self, download_id: int):
        download = self._downloads.get(download_id)
        if not download:
            return
        download.status = DownloadStatus.DOWNLOADING
        download.started_at = datetime.now()
        with self._queue_lock:
            self._active_count += 1
        try:
            thread = threading.Thread(
                target=self._download_thread,
                args=(download_id,),
                daemon=True,
                name=f"Download-{download_id}"
            )
            self._active_threads[download_id] = thread
            thread.start()
            if self._cleanup_timer is None:
                self._start_cleanup_timer()
        except Exception as e:
            logger.error(f"Error iniciando hilo: {e}")
            download.status = DownloadStatus.ERROR
            download.error_msg = f"Error iniciando: {str(e)[:50]}"
            with self._queue_lock:
                self._active_count -= 1
            self._notify()
            self._process_queue()

    def cleanup_completed(self) -> int:
        with self._lock:
            to_remove = [
                k for k, v in self._downloads.items()
                if v.status in (DownloadStatus.COMPLETED, DownloadStatus.ERROR, DownloadStatus.CANCELLED)
            ]
            for k in to_remove:
                if k in self._active_threads:
                    del self._active_threads[k]
                thumb = self._downloads[k].thumbnail
                if thumb and os.path.exists(thumb):
                    try:
                        os.remove(thumb)
                    except Exception:
                        pass
                dl = self._downloads[k]
                if dl.filepath and os.path.exists(dl.filepath + ".part"):
                    try:
                        os.remove(dl.filepath + ".part")
                    except Exception:
                        pass
                del self._downloads[k]
            if not self._active_threads and self._cleanup_timer:
                self._cleanup_timer = None
            return len(to_remove)

    def _start_cleanup_timer(self):
        def cleanup_old_threads():
            while True:
                time.sleep(60)
                with self._lock:
                    to_remove = []
                    for dl_id, thread in list(self._active_threads.items()):
                        if not thread.is_alive():
                            to_remove.append(dl_id)
                            with self._queue_lock:
                                self._active_count = max(0, self._active_count - 1)
                    for dl_id in to_remove:
                        if dl_id in self._active_threads:
                            del self._active_threads[dl_id]
                    if not self._active_threads:
                        self._cleanup_timer = None
                        break
        self._cleanup_timer = threading.Thread(target=cleanup_old_threads, daemon=True)
        self._cleanup_timer.start()

    def download(self, url: str, path: str, use_cookies: bool = False, cookies_path: str = "",
                 quality: str = "1080", audio_only: bool = False, audio_format: str = "mp3",
                 scheduled_time: str = None) -> Optional[int]:
        try:
            import yt_dlp
        except ImportError:
            logger.error("yt-dlp no está instalado")
            return None

        with self._lock:
            self._next_id += 1
            download_id = self._next_id
            download = VideoDownload(
                id=download_id,
                name="Analizando URL...",
                url=url,
                status=DownloadStatus.PENDING,
                quality=quality,
                use_cookies=use_cookies,
                cookies_path=cookies_path,
                audio_only=audio_only,
                audio_format=audio_format,
                scheduled_time=scheduled_time,
            )
            self._downloads[download_id] = download
            download.save_path = path

        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creando directorio: {e}")
            download.status = DownloadStatus.ERROR
            download.error_msg = f"Error creando directorio: {str(e)[:50]}"
            self._notify()
            return download_id

        if not DiskSpaceMonitor.has_enough_space(path, 500):
            download.status = DownloadStatus.ERROR
            download.error_msg = "Espacio insuficiente en disco"
            self._notify()
            return download_id

        with self._queue_lock:
            if self._active_count < max(1, self._max_concurrent):
                self._start_download_thread(download_id)
            else:
                download.status = DownloadStatus.QUEUED
                self._download_queue.append(download_id)
                self._notify()
        return download_id

    def _download_thread(self, download_id: int):
        download = self._downloads.get(download_id)
        if not download:
            return
        _lf = open(os.path.join(os.path.expanduser("~"), "vf_dl.log"), "a", encoding="utf-8")
        try:
            import subprocess, sys
            from collections import deque
            download.status = DownloadStatus.DOWNLOADING
            download.name = "Analizando URL..."
            self._notify()
            cookies = os.path.join(os.path.expanduser("~"), ".videoflex_cookies.txt")
            if not os.path.exists(cookies):
                cookies = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_cookies.txt")
            outdir = os.path.dirname(download.filepath) if download.filepath else (getattr(download, "save_path", None) or os.path.join(os.path.expanduser("~"), "Videos"))
            os.makedirs(outdir, exist_ok=True)
            cfgs = [["--extractor-args", "youtube:player_client=web"],
                    ["--extractor-args", "youtube:player_client=tv"],
                    ["--extractor-args", "youtube:player_client=mweb"],
                    []]
            rc = 1
            buf = deque(maxlen=8)
            cancelado = False
            pausado = False
            _last_ui = 0.0
            for cfg in cfgs:
                cmd = [sys.executable, "-u", "-m", "yt_dlp", "--js-runtime", "node",
                       "--remote-components", "ejs:github", "--newline",
                       "--socket-timeout", "30", "--retries", "2"]
                if os.path.exists(cookies):
                    cmd += ["--cookies", cookies]
                cmd += cfg
                cmd += ["-o", os.path.join(outdir, "%(title)s.%(ext)s"), download.url]
                buf.clear()
                download.progress = 0
                listo = False
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace",
                                        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
                download.subprocess = proc
                for line in proc.stdout:
                    _lf.write(f"{datetime.now().strftime('%H:%M:%S')} {line.rstrip()}\n")
                    _lf.flush()
                    buf.append(line.rstrip())
                    if getattr(download, "_cancel_requested", False):
                        cancelado = True
                        proc.terminate()
                        break
                    if getattr(download, "_pause_requested", False):
                        pausado = True
                        proc.terminate()
                        break
                    if not listo and ("[Merger]" in line or "[Fixup" in line or
                                      ("[download]" in line and " in 00:" in line)):
                        listo = True
                        download.status = DownloadStatus.COMPLETED
                        download.speed = ""
                        download.progress = 100
                        self._notify(force=True)
                    if "[download]" in line and "%" in line:
                        try:
                            download.progress = float(line.split("%")[0].split()[-1])
                        except Exception:
                            pass
                        if not listo and " at " in line and "/s" in line:
                            try:
                                download.speed = line.split(" at ")[1].split(" ETA")[0].strip()
                            except Exception:
                                pass
                        if download.progress >= 100 and not listo:
                            listo = True
                            download.status = DownloadStatus.COMPLETED
                            download.speed = ""
                            download.progress = 100
                            self._notify(force=True)
                        if time.time() - _last_ui >= 1.0:
                            _last_ui = time.time()
                            self._notify()
                    if "Destination:" in line:
                        _dest = line.split("Destination:")[-1].strip()
                        download.name = os.path.basename(_dest)
                        download.filepath = _dest
                        self._notify()
                proc.wait()
                rc = proc.returncode
                if cancelado or pausado or rc == 0:
                    break
            if pausado:
                download.status = DownloadStatus.PAUSED
                download.speed = ""
                download._pause_requested = False
            elif cancelado:
                pass
            elif rc == 0:
                download.status = DownloadStatus.COMPLETED
                download.progress = 100
                download.speed = ""
            else:
                download.status = DownloadStatus.ERROR
                download.error_msg = " | ".join(list(buf)[-2:])[:120]
            self._notify(force=True)
        except Exception as e:
            logger.error(f"Error descarga: {e}")
            download.status = DownloadStatus.ERROR
            download.error_msg = str(e)
            self._notify(force=True)
        finally:
            _lf.close()
    def _get_path_from_config(self):
        if self._config_ref:
            return self._config_ref.video_path
        return get_default_video_path()


# ═══════════════════════════════════════════════════════════════
# CLASE PRINCIPAL DE LA APLICACIÓN MEJORADA
# ═══════════════════════════════════════════════════════════════
class VideoFlexApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._splash_status = ft.Text("Inicializando sistema...", color="#94a3b8", size=11)
        self._splash_progress = ft.ProgressBar(width=320, color="#6366f1", bgcolor="#334155")
        self.qbit = QBittorrentAPI()
        self.config = self.load_config()
        self.video_mgr = VideoManager(page=page, max_concurrent=self.config.max_concurrent_downloads)
        self.video_mgr._config_ref = self.config
        self.history = DownloadHistory()
        self.clipboard_history = ClipboardHistory()
        self.has_ytdlp = False
        self.ytdlp_version = "Cargando..."
        self._current_section = "dashboard"
        self._qbit_torrents: List[Dict] = []
        self._transfer_info: Dict = {}
        self._speed_history: List[Dict] = []
        self._notified_hashes = set()
        self._selected_torrent_site = "LimeTorrents"
        self._magnet_input_text = ""
        self._detected_video_url = ""
        self._session_alive = True
        self._history_saved_ids = set()
        self._torrents_list_ctrl: Optional[ft.Column] = None
        self._downloads_list_ctrl: Optional[ft.Column] = None
        self._help_dialog = None
        self._selected_download_id: Optional[int] = None
        self._setup_page()
        self.video_mgr.register_callback(self._on_video_update)
        self.page.run_task(self._async_init)

    def _check_ytdlp(self):
        try:
            import yt_dlp
            return True
        except ImportError:
            return False

    def _get_ytdlp_version(self):
        try:
            import yt_dlp
            return yt_dlp.version.__version__
        except Exception:
            return "Desconocida"

    def _setup_page(self):
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.padding = 0
        _t0 = self.config.theme
        if _t0 == "auto":
            _h0 = datetime.now().hour
            _t0 = "dark" if _h0 >= 20 or _h0 < 7 else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if _t0 == "dark" else ft.ThemeMode.LIGHT
        self.page.on_keyboard_event = self._on_keyboard
        self.page.on_close = self._on_session_close
        self.page.on_disconnect = self._on_session_close
        try:
            self.page.window.title_bar_hidden = True
            self.page.window.frameless = True
            self.page.window.bgcolor = ft.Colors.TRANSPARENT
            self.page.bgcolor = ft.Colors.TRANSPARENT
            self.page.window.width = 460
            self.page.window.height = 520
            self.page.window.min_width = 460
            self.page.window.min_height = 520
            self.page.window.alignment = ft.Alignment(0, 0)
        except AttributeError:
            pass
        self.page.theme = ft.Theme(
            color_scheme_seed="#6366f1",
            visual_density=ft.VisualDensity.COMFORTABLE
        )

    def _on_session_close(self, e=None):
        if self.config.minimize_to_tray:
            try:
                self.page.window.minimized = True
                self.page.update()
                return
            except Exception:
                pass
        logger.info("Sesión cerrada — deteniendo loops de fondo")
        self._session_alive = False
        if hasattr(self, 'video_mgr'):
            self.video_mgr.shutdown()

    def load_config(self) -> AppConfig:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = AppConfig()
                    if 'qbittorrent' in data:
                        qb = data['qbittorrent']
                        config.qb_host = qb.get('host', config.qb_host)
                        config.qb_port = qb.get('port', config.qb_port)
                        config.qb_user = qb.get('username', config.qb_user)
                        config.qb_pass = qb.get('password', config.qb_pass)
                        config.auto_connect = qb.get('auto_connect', config.auto_connect)
                    config.video_path = data.get('paths', {}).get('video', config.video_path)
                    config.torrent_path = data.get('paths', {}).get('torrent', config.torrent_path)
                    config.theme = data.get('theme', 'dark')
                    config.use_cookies = data.get('use_cookies', False)
                    config.cookies_path = data.get('cookies_path', str(Path.home() / ".videoflex_cookies.txt"))
                    config.video_quality = data.get('video_quality', '1080')
                    config.max_concurrent_downloads = data.get('max_concurrent_downloads', 3)
                    config.notifications_enabled = data.get('notifications_enabled', True)
                    config.auto_start_downloads = data.get('auto_start_downloads', True)
                    config.minimize_to_tray = data.get('minimize_to_tray', False)
                    config.check_updates = data.get('check_updates', True)
                    config.auto_update_ytdlp = data.get('auto_update_ytdlp', False)
                    config.proxy_enabled = data.get('proxy_enabled', False)
                    config.proxy_url = data.get('proxy_url', '')
                    config.proxy_username = data.get('proxy_username', '')
                    config.proxy_password = data.get('proxy_password', '')
                    config.auto_detect_cookies = data.get('auto_detect_cookies', False)
                    config.cookies_browser = data.get('cookies_browser', 'chrome')
                    config.subtitles_enabled = data.get('subtitles_enabled', False)
                    config.subtitles_langs = data.get('subtitles_langs', 'es')
                    config.subtitles_format = data.get('subtitles_format', 'srt')
                    config.embed_subtitles = data.get('embed_subtitles', False)
                    config.auto_convert_to_mp4 = data.get('auto_convert_to_mp4', True)
                    return config
        except Exception as e:
            logger.error(f"Error cargando config: {e}")
        return AppConfig()

    def save_config(self):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "qbittorrent": {
                    "host": self.config.qb_host,
                    "port": self.config.qb_port,
                    "username": self.config.qb_user,
                    "password": self.config.qb_pass,
                    "auto_connect": self.config.auto_connect
                },
                "paths": {
                    "video": self.config.video_path,
                    "torrent": self.config.torrent_path
                },
                "theme": self.config.theme,
                "use_cookies": self.config.use_cookies,
                "cookies_path": self.config.cookies_path,
                "video_quality": self.config.video_quality,
                "max_concurrent_downloads": self.config.max_concurrent_downloads,
                "notifications_enabled": self.config.notifications_enabled,
                "auto_start_downloads": self.config.auto_start_downloads,
                "minimize_to_tray": self.config.minimize_to_tray,
                "check_updates": self.config.check_updates,
                "auto_update_ytdlp": self.config.auto_update_ytdlp,
                "proxy_enabled": self.config.proxy_enabled,
                "proxy_url": self.config.proxy_url,
                "proxy_username": self.config.proxy_username,
                "proxy_password": self.config.proxy_password,
                "auto_detect_cookies": self.config.auto_detect_cookies,
                "cookies_browser": self.config.cookies_browser,
                "subtitles_enabled": self.config.subtitles_enabled,
                "subtitles_langs": self.config.subtitles_langs,
                "subtitles_format": self.config.subtitles_format,
                "embed_subtitles": self.config.embed_subtitles,
                "auto_convert_to_mp4": self.config.auto_convert_to_mp4,
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Configuración guardada")
        except Exception as e:
            logger.error(f"Error guardando config: {e}")

    async def _async_init(self):
        splash = self._create_splash()
        self.page.add(splash)
        self.page.update()
        await asyncio.sleep(0.3)
        
        # Animar mensajes de estado
        messages = [
            "Cargando módulos...",
            "Inicializando servicios...",
            "Conectando a qBittorrent...",
            "Preparando interfaz...",
        ]
        async def update_status():
            for msg in messages:
                self._splash_status.value = msg
                self._splash_progress.value = (messages.index(msg) + 1) / len(messages)
                self.page.update()
                await asyncio.sleep(0.8)
        status_task = asyncio.create_task(update_status())
        await asyncio.sleep(0.2)
        try:
            sw = self.page.window.screen_width or 1920
            sh = self.page.window.screen_height or 1080
            self.page.window.left = (sw - 460) // 2
            self.page.window.top = (sh - 520) // 2
            self.page.update()
        except Exception:
            try:
                await self.page.window.center()
            except Exception:
                pass
        prefetch_task = asyncio.create_task(
            asyncio.to_thread(self._prefetch_slow_data)
        )
        if self.config.auto_connect:
            asyncio.create_task(self._connect_qbittorrent_async())
        for _ in range(25):
            await asyncio.sleep(0.1)
        await prefetch_task
        await status_task
        self._splash_status.value = "✓ ¡Listo!"
        self._splash_progress.value = 1.0
        self.page.update()
        await asyncio.sleep(0.9)
        try:
            splash.opacity = 0
            self.page.update()
            await asyncio.sleep(0.7)
        except Exception:
            pass
        self.page.controls.clear()
        self.page.update()
        await asyncio.sleep(0.05)
        try:
            self.page.window.title_bar_hidden = False
            self.page.window.frameless = False
        except AttributeError:
            pass
        _t1 = self.config.theme
        if _t1 == "auto":
            _h1 = datetime.now().hour
            _t1 = "dark" if _h1 >= 20 or _h1 < 7 else "light"
        self.page.bgcolor = "#0f172a" if _t1 == "dark" else "#f8fafc"
        try:
            self.page.window.bgcolor = ft.Colors.TRANSPARENT
            self.page.window.min_width = 900
            self.page.window.min_height = 580
            self.page.window.width = 1100
            self.page.window.height = 680
        except AttributeError:
            pass
        self.page.update()
        await asyncio.sleep(0.15)
        try:
            await self.page.window.center()
        except Exception:
            pass
        await asyncio.sleep(0.05)
        self._build_layout()
        await asyncio.sleep(0)
        self.page.update()
        await asyncio.sleep(0)
        self._start_monitoring()
        await asyncio.sleep(0)
        self.navigate_to("dashboard")
        await asyncio.sleep(0)
        self.page.update()

    def _prefetch_slow_data(self):
        try:
            import yt_dlp
            self.has_ytdlp = True
            self.ytdlp_version = yt_dlp.version.__version__
            if self.config.auto_update_ytdlp:
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                        capture_output=True, timeout=60
                    )
                    if result.returncode == 0:
                        import importlib
                        import yt_dlp as yt_dlp2
                        importlib.reload(yt_dlp2)
                        self.ytdlp_version = yt_dlp2.version.__version__
                        logger.info(f"yt-dlp actualizado a v{self.ytdlp_version}")
                except Exception as ex:
                    logger.warning(f"No se pudo actualizar yt-dlp: {ex}")
        except ImportError:
            self.has_ytdlp = False
            self.ytdlp_version = "No instalado"
        try:
            self._cached_disk = DiskSpaceMonitor.get_free_space(self.config.video_path)
        except Exception:
            self._cached_disk = (0.0, 1.0, 0.0)
        self._system_status = {
            'yt_dlp': self.has_ytdlp,
            'ffmpeg': shutil.which('ffmpeg') is not None or os.path.exists(get_ffmpeg_path()),
            'vlc': shutil.which('vlc') is not None or os.path.exists(get_vlc_executable()),
            'qbittorrent': False,
        }
        logger.info(f"Prefetch listo — yt_dlp={self.has_ytdlp}")

    async def _connect_qbittorrent_async(self):
        try:
            success, msg = await asyncio.to_thread(
                self.qbit.connect,
                self.config.qb_host,
                self.config.qb_port,
                self.config.qb_user,
                self.config.qb_pass
            )
            if not success and ("No se puede conectar" in msg or "Timeout" in msg):
                _qb_exe = get_qbittorrent_executable()
                if _qb_exe:
                    try:
                        subprocess.Popen([_qb_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info("qBittorrent no estaba activo; iniciando automaticamente...")
                        await asyncio.sleep(6)
                        success, msg = await asyncio.to_thread(
                            self.qbit.connect,
                            self.config.qb_host,
                            self.config.qb_port,
                            self.config.qb_user,
                            self.config.qb_pass,
                        )
                    except Exception as _ex:
                        logger.error(f"Error auto-inicio qBittorrent: {_ex}")
            if success:
                self._system_status['qbittorrent'] = True
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.bgcolor = "green"
                    self.status_text.value = "Conectado"
                    self.status_text.color = "green"
                    self.page.update()
        except Exception as e:
            logger.error(f"Error conectando a qBittorrent: {e}")

    def _create_splash(self):
        # Logo con efecto glow
        logo_container = ft.Container(
            width=72, height=72, border_radius=18,
            content=ft.Container(
                width=72, height=72, border_radius=18, bgcolor="#6366f1",
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.BOLT, size=38, color="white"),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=30, color="#6366f160",
                    offset=ft.Offset(0, 0),
                ),
            ),
        )
        
        about_card = ft.Container(
            width=420,
            padding=ft.Padding.symmetric(horizontal=32, vertical=28),
            bgcolor="#1e293b",
            border_radius=20,
            border=ft.Border.all(1.5, "#334155"),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=50, color="#00000090", offset=ft.Offset(0, 12),
            ),
            content=ft.Column([
                # Header centrado con logo grande
                ft.Container(
                    content=logo_container,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Column([
                        ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(APP_DESCRIPTION, size=11, color="#94a3b8"),
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(height=20),
                ft.Container(height=1, bgcolor="#334155"),
                ft.Container(height=20),
                # Info en grid 2x2
                ft.Row([
                    ft.Column([
                        ft.Text("Versión", size=9, color="#6366f1", weight=ft.FontWeight.W_600),
                        ft.Container(
                            content=ft.Text(APP_VERSION, size=13, color="white", weight=ft.FontWeight.W_600),
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            bgcolor="#6366f120", border_radius=8,
                        ),
                    ], spacing=4, expand=True),
                    ft.Column([
                        ft.Text("Desarrollado por", size=9, color="#6366f1", weight=ft.FontWeight.W_600),
                        ft.Text(APP_AUTHOR, size=12, color="white"),
                    ], spacing=4, expand=True),
                ]),
                ft.Container(height=12),
                ft.Text(f"{APP_COMPANY}  ·  © {APP_YEAR}", size=11, color="#64748b"),
                ft.Container(height=20),
                ft.Container(height=1, bgcolor="#334155"),
                ft.Container(height=16),
                # Novedades con iconos de check
                ft.Text(f"Novedades v{APP_VERSION}", size=10, color="#6366f1", weight=ft.FontWeight.W_700),
                ft.Container(height=10),
                *[
                    ft.Row([
                        ft.Container(
                            width=18, height=18, border_radius=9, bgcolor="#10b98120",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.CHECK, size=11, color="#10b981"),
                        ),
                        ft.Text(txt, size=11, color="#cbd5e1"),
                    ], spacing=8)
                    for txt in [
                        "Sistema de colas inteligente",
                        "Notificaciones nativas del sistema",
                        "Historial con búsqueda y filtros",
                        "Monitor de espacio en disco",
                    ]
                ],
                ft.Container(height=20),
                # Barra de progreso animada
                self._splash_progress,
                ft.Container(height=10),
                ft.Container(
                    content=self._splash_status,
                    alignment=ft.Alignment(0, 0),
                ),
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
        return ft.Container(
            expand=True, bgcolor="#0f172a", alignment=ft.Alignment(0, 0),
            padding=ft.Padding.all(10), content=about_card,
            animate_opacity=ft.Animation(600, "easeOut"),
        )

    def _build_layout(self):
        self._folder_picker = None
        self.status_indicator = ft.Container(
            width=10, height=10, border_radius=5,
            bgcolor="green" if self.qbit.connected else "red",
            animate=ft.Animation(300, "easeInOut"),
        )
        self.status_text = ft.Text(
            "Conectado" if self.qbit.connected else "Desconectado",
            size=10,
            color="green" if self.qbit.connected else "red"
        )
        self.notification_badge = ft.Container(
            content=ft.Text("0", size=9, color="white", weight=ft.FontWeight.BOLD),
            bgcolor="#ef4444", border_radius=10,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            visible=False
        )
        nav_items = [
            ("Dashboard", ft.Icons.DASHBOARD, "dashboard"),
            ("Torrents", ft.Icons.LINK, "torrents"),
            ("Videos", ft.Icons.VIDEO_LIBRARY, "videos"),
            ("Explorar", ft.Icons.TRAVEL_EXPLORE, "explorar"),
                        ("Descargas", ft.Icons.DOWNLOAD, "downloads"),
            ("Historial", ft.Icons.HISTORY, "history"),
            ft.Divider(height=1),
            ("Configuración", ft.Icons.SETTINGS, "settings"),
            ("Acerca de", ft.Icons.INFO, "about"),
            ("Ayuda (F1)", ft.Icons.HELP, "help"),
        ]

        def _toggle_theme(e):
            new_theme = "light" if self.config.theme == "dark" else "dark"
            self._change_theme(new_theme)

        theme_toggle = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.DARK_MODE if self.config.theme == "dark" else ft.Icons.LIGHT_MODE,
                    size=16, color="#94a3b8"
                ),
                ft.Text(
                    "Oscuro" if self.config.theme == "dark" else "Claro",
                    size=11, color="#94a3b8"
                ),
                ft.Container(expand=True),
                ft.Switch(
                    value=self.config.theme == "dark",
                    on_change=lambda e: _toggle_theme(e),
                    active_color="#6366f1",
                    scale=0.75,
                ),
            ], spacing=6),
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            border_radius=8, ink=True,
        )
        self._theme_toggle = theme_toggle

        nav_controls = []
        for item in nav_items:
            if isinstance(item, tuple):
                text, icon, section = item
                is_selected = section == self._current_section
                nav_controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(icon, size=18, color="#6366f1" if is_selected else "#94a3b8"),
                            ft.Text(text, color="white" if is_selected else "#94a3b8", size=12,
                                    weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL),
                        ], spacing=10),
                        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                        border_radius=8,
                        bgcolor="#334155" if is_selected else None,
                        on_click=lambda _, s=section: self.navigate_to(s),
                        ink=True,
                        animate=ft.Animation(200, "easeOut"),
                    )
                )
            else:
                nav_controls.append(item)

        nav_controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.POWER_SETTINGS_NEW, size=18, color="#ef4444"),
                    ft.Text("Salir", color="#ef4444", size=12, weight=ft.FontWeight.W_500)
                ], spacing=10),
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                border_radius=8,
                on_click=self._salir_aplicacion,
                ink=True
            )
        )
        nav_controls.append(ft.Divider(height=1, color="#334155"))
        nav_controls.append(theme_toggle)

        shortcuts_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.KEYBOARD_ROUNDED, size=14, color="#6366f1"),
                    ft.Text("Atajos", size=12, weight=ft.FontWeight.W_600, color="#6366f1"),
                ], spacing=6),
                ft.Container(height=8),
                *[
                    ft.Row([
                        ft.Container(
                            content=ft.Text(k, size=9, color="#e2e8f0", weight=ft.FontWeight.W_600),
                            bgcolor="#334155",
                            padding=ft.Padding(left=6, right=6, top=3, bottom=3),
                            border_radius=4,
                            border=ft.Border.all(1, "#475569"),
                        ),
                        ft.Text(v, size=10, color="#94a3b8", expand=True),
                    ], spacing=8)
                    for k, v in [
                        ("F1", "Ayuda"), ("Ctrl+N", "Nueva descarga"),
                        ("Ctrl+D", "Dashboard"), ("Ctrl+T", "Torrents"),
                        ("Ctrl+V", "Videos"), ("Ctrl+H", "Historial"),
                        ("Ctrl+S", "Guardar config"), ("Ctrl+Q", "Salir"),
                        ("Del", "Cancelar sel."),
                    ]
                ],
            ], spacing=6, tight=True),
            padding=ft.Padding(left=14, right=14, top=12, bottom=12),
            bgcolor=with_opacity(0.08, "#6366f1"),
            border_radius=12,
            border=ft.Border.all(1, with_opacity(0.2, "#6366f1")),
            margin=ft.Margin.only(top=12),
        )

        if hasattr(self, '_cached_disk'):
            free_space, total_space, _ = self._cached_disk
        else:
            try:
                free_space, total_space, _ = DiskSpaceMonitor.get_free_space(self.config.video_path)
            except Exception:
                free_space, total_space = 0.0, 1.0

        space_percent = (1 - free_space / total_space) * 100 if total_space > 0 else 0
        space_indicator = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STORAGE, size=14, color="#64748b"),
                    ft.Text("Espacio disponible", size=10, color="#64748b"),
                ], spacing=6),
                ft.Container(height=4),
                ft.ProgressBar(
                    value=space_percent / 100,
                    color="#ef4444" if space_percent > 90 else "#f59e0b" if space_percent > 70 else "#10b981",
                    bgcolor="#334155", height=4, border_radius=2
                ),
                ft.Container(height=4),
                ft.Text(f"{free_space:.1f} GB libres", size=9, color="#64748b"),
            ], spacing=0),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            bgcolor="#1e293b", border_radius=8,
            margin=ft.Margin.only(top=8),
        )

        sidebar = ft.Container(
            width=200,
            padding=ft.Padding.only(left=12, right=12, top=12, bottom=8),
            bgcolor="#1e293b" if self.config.theme == "dark" else "#f1f5f9",
            content=ft.Column(
                nav_controls + [
                    shortcuts_panel,
                    ft.Container(expand=True),
                    space_indicator,
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([self.status_indicator, self.status_text], spacing=8),
                        bgcolor=with_opacity(0.1, "black"),
                        padding=10, border_radius=8
                    )
                ],
                expand=True, scroll=ft.ScrollMode.AUTO, spacing=0,
            )
        )

        self.content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
        content_wrapper = ft.Container(
            content=self.content_area, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        self.page.add(
            ft.Row(
                [sidebar, ft.VerticalDivider(width=1, color="#334155"), content_wrapper],
                expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )

    async def _salir_aplicacion(self, e):
        self._session_alive = False
        self.video_mgr.shutdown()
        try:
            await self.page.window.close()
        except Exception:
            self.page.window_close()

    def navigate_to(self, section: str):
        try:
            self._current_section = section
            self.content_area.controls.clear()
            builders = {
                "dashboard": self._build_dashboard_compact,
                "torrents": self._build_torrents_compact,
                "videos": self._build_videos_compact,
                "downloads": self._build_downloads_compact,
                "history": self._build_history_compact,
                "settings": self._build_settings_compact,
                "about": self._build_about_compact,
                "explorar": getattr(self, "_build_explorar_compact", None),
                "help": self._show_help_section_compact,
            }
            fn = builders.get(section)
            if fn:
                fn()
            self.page.update()
        except Exception as e:
            import traceback
            print(f"ERROR navigate_to({section}): {e}")
            traceback.print_exc()
            try:
                self._show_snack(f"❌ Error: {str(e)[:60]}", "red")
            except Exception:
                pass


    def _start_monitoring(self):
        def _safe_run_task(coro_fn):
            try:
                if self._session_alive and self.page:
                    self.page.run_task(coro_fn)
            except Exception:
                pass

        def data_loop():
            while self._session_alive:
                try:
                    if self.qbit.connected:
                        self._qbit_torrents = self.qbit.get_torrents()
                        self._transfer_info = self.qbit.get_global_transfer_info()
                        dl = self._transfer_info.get('dl_info_speed', 0) / 1024
                        ul = self._transfer_info.get('up_info_speed', 0) / 1024
                        self._speed_history.append({'dl': dl, 'ul': ul})
                        if len(self._speed_history) > 60:
                            self._speed_history.pop(0)
                        if self._current_section == "torrents":
                            async def refresh_torrents_list():
                                if not self._session_alive:
                                    return
                                try:
                                    if self._torrents_list_ctrl is not None:
                                        self._torrents_list_ctrl.controls.clear()
                                        for t in self._qbit_torrents:
                                            self._torrents_list_ctrl.controls.append(
                                                self._torrent_item_compact(t))
                                        self.page.update()
                                    else:
                                        self.navigate_to("torrents")
                                except Exception as e:
                                    logger.error(f"Error refresh_torrents_list: {e}")
                            _safe_run_task(refresh_torrents_list)
                        elif self._current_section == "dashboard":
                            async def refresh_dashboard():
                                if self._session_alive:
                                    self._update_status_ui()
                            _safe_run_task(refresh_dashboard)
                    if self._session_alive:
                        self._update_status_ui()
                except Exception as e:
                    if self._session_alive:
                        logger.error(f"Error en data_loop: {e}")
                time.sleep(3)

        def notification_loop():
            while self._session_alive:
                try:
                    if self.qbit.connected:
                        for t in list(self._qbit_torrents):
                            size_mb = t.get('size', 0) / (1024 * 1024)
                            downloaded_mb = t.get('completed', 0) / (1024 * 1024)
                            if (t['progress'] >= 1.0 and
                                    t['hash'] not in self._notified_hashes and
                                    size_mb > 1.0 and downloaded_mb > 1.0):
                                self._notified_hashes.add(t['hash'])
                                notification_mgr.notify("VideoFlex", f"Torrent completado: {t['name'][:30]}...")
                                play_notification_sound()
                                name = t['name'][:30]
                                async def show_notification(n=name):
                                    if self._session_alive:
                                        self._show_snack(f"✅ Torrent completado: {n}...", "green")
                                _safe_run_task(show_notification)
                except Exception as e:
                    if self._session_alive:
                        logger.error(f"Error en notification_loop: {e}")
                time.sleep(3)

        threading.Thread(target=data_loop, daemon=True).start()
        threading.Thread(target=notification_loop, daemon=True).start()
        threading.Thread(target=self._clipboard_monitor_loop, daemon=True).start()
        threading.Thread(target=self._auto_theme_loop, daemon=True).start()
        
    def _clipboard_monitor_loop(self):
        last_clipboard = ""

        def is_video_url(text: str) -> bool:
            video_patterns = [
                'youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com',
                'twitter.com', 'x.com', 'facebook.com', 'fb.watch',
                'vimeo.com', 'dailymotion.com', 'twitch.tv', 'reddit.com'
            ]
            text_lower = text.lower().strip()
            return any(pattern in text_lower for pattern in video_patterns)

        def is_magnet_link(text: str) -> bool:
            return text.strip().lower().startswith('magnet:?')

        while self._session_alive:
            try:
                time.sleep(1.5)
                if not self._session_alive:
                    break
                current_clipboard = ""
                try:
                    if platform.system() == "Windows":
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                            future = ex.submit(pyperclip.paste)
                            try:
                                current_clipboard = future.result(timeout=0.8)
                            except concurrent.futures.TimeoutError:
                                continue
                    else:
                        current_clipboard = pyperclip.paste()
                except Exception:
                    continue
                if current_clipboard and current_clipboard != last_clipboard:
                    last_clipboard = current_clipboard
                    text = current_clipboard.strip()
                    if is_magnet_link(text):
                        self._magnet_input_text = text
                        self.clipboard_history.add(text)
                        async def show_magnet_detected():
                            if self._session_alive:
                                self._show_snack("🧲 Enlace magnet detectado", "blue")
                                self.navigate_to("torrents")
                        if self.page:
                            self.page.run_task(show_magnet_detected)
                    elif is_video_url(text):
                        self._detected_video_url = text
                        self.clipboard_history.add(text)
                        async def show_video_detected():
                            if self._session_alive:
                                self._show_snack("🎥 Enlace de video detectado", "purple")
                                self.navigate_to("videos")
                        if self.page:
                            self.page.run_task(show_video_detected)
            except Exception as e:
                if self._session_alive:
                    logger.error(f"Error en clipboard_monitor: {e}")

    def _auto_theme_loop(self):
        while self._session_alive:
            try:
                if self.config.theme == "auto":
                    _h = datetime.now().hour
                    _eff = "dark" if _h >= 20 or _h < 7 else "light"
                    _cur = "dark" if self.page.theme_mode == ft.ThemeMode.DARK else "light"
                    if _eff != _cur:
                        async def _switch():
                            if not self._session_alive:
                                return
                            self.page.theme_mode = ft.ThemeMode.DARK if _eff == "dark" else ft.ThemeMode.LIGHT
                            self.page.bgcolor = "#0f172a" if _eff == "dark" else "#f8fafc"
                            self.page.update()
                        if self.page:
                            self.page.run_task(_switch)
            except Exception as e:
                logger.error(f"Error auto_theme: {e}")
            time.sleep(300)

    def _update_status_ui(self):
        if not self._session_alive:
            return
        try:
            if self.qbit.connected:
                self.status_indicator.bgcolor = "green"
                self.status_text.value = "Conectado"
                self.status_text.color = "green"
            else:
                self.status_indicator.bgcolor = "red"
                self.status_text.value = "Desconectado"
                self.status_text.color = "red"
            self.page.update()
        except Exception:
            pass

    def _on_video_update(self):
        if not self._session_alive:
            return
        try:
            downloads = self.video_mgr.get_downloads()
            for d in downloads:
                if d.status == DownloadStatus.COMPLETED and d.id not in self._history_saved_ids:
                    self._history_saved_ids.add(d.id)
                    if d.filepath and os.path.exists(d.filepath):
                        file_size = os.path.getsize(d.filepath)
                        self.history.add_entry(
                            name=d.name, url=d.url, filepath=d.filepath,
                            size_bytes=file_size, quality=d.quality
                        )

            async def update_section():
                if not self._session_alive:
                    return
                try:
                    active = [d for d in self.video_mgr.get_downloads()
                              if d.status == DownloadStatus.DOWNLOADING]
                    if active:
                        avg = sum(d.progress for d in active) / len(active)
                        self.page.title = f"{APP_NAME} — ⬇ {len(active)} descarga{'s' if len(active) > 1 else ''} ({avg:.0f}%)"
                    else:
                        self.page.title = f"{APP_NAME} v{APP_VERSION}"
                    if self._current_section == "downloads":
                        if self._downloads_list_ctrl is not None:
                            self._downloads_list_ctrl.controls.clear()
                            for d in self.video_mgr.get_downloads():
                                self._downloads_list_ctrl.controls.append(self._download_item_card(d))
                            self.page.update()
                        else:
                            self.navigate_to("downloads")
                    elif self._current_section == "videos":
                        self.page.update()
                    elif self._current_section == "dashboard":
                        self.page.update()
                    elif hasattr(self, 'page') and self.page:
                        self.page.update()
                except Exception as e:
                    logger.error(f"Error en update_section: {e}")

            if hasattr(self, 'page') and self.page:
                self.page.run_task(update_section)
        except Exception as e:
            logger.error(f"Error actualizando UI: {e}")

    # ═══════════════════════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════════════════════
    def _build_dashboard_compact(self):
        is_dark = self.config.theme == "dark"
        bg_container = "#1e293b" if is_dark else "#ffffff"
        text_primary = "white" if is_dark else "black"
        dl_speed = self._transfer_info.get('dl_info_speed', 0) / 1024
        ul_speed = self._transfer_info.get('up_info_speed', 0) / 1024
        active_torrents = len([t for t in self._qbit_torrents if t['state'] in ('downloading', 'metaDL', 'checkingUP')])
        video_downloads = self.video_mgr.get_downloads()
        active_videos = len([d for d in video_downloads if d.status == DownloadStatus.DOWNLOADING])
        queued_videos = len([d for d in video_downloads if d.status == DownloadStatus.QUEUED])

        stats_row = ft.Row([
            self._stat_card_compact("⬇️", f"{dl_speed:.0f} KB/s", "Descarga BT", "blue"),
            self._stat_card_compact("⬆️", f"{ul_speed:.0f} KB/s", "Subida BT", "green"),
            self._stat_card_compact("🧲", str(active_torrents), "Torrents", "orange"),
            self._stat_card_compact("🎥", f"{active_videos}/{queued_videos}", "Videos (Act/Cola)", "purple"),
        ], spacing=8, expand=True)

        if hasattr(self, '_cached_disk'):
            free_gb, total_gb, _ = self._cached_disk
        else:
            try:
                free_gb, total_gb, _ = DiskSpaceMonitor.get_free_space(self.config.video_path)
            except Exception:
                free_gb, total_gb = 0.0, 1.0
        space_percent = (1 - free_gb / total_gb) * 100 if total_gb > 0 else 0

        space_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STORAGE, color="#64748b"),
                    ft.Text("Almacenamiento", size=12, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.Text(f"{free_gb:.1f} GB libres", size=11, color="#64748b"),
                ]),
                ft.Container(height=8),
                ft.ProgressBar(
                    value=space_percent / 100,
                    color="#ef4444" if space_percent > 90 else "#f59e0b" if space_percent > 70 else "#10b981",
                    bgcolor="#334155", height=6, border_radius=3
                ),
                ft.Container(height=4),
                ft.Text(f"{space_percent:.1f}% usado de {total_gb:.1f} GB", size=10, color="#64748b"),
            ], spacing=0),
            padding=14, bgcolor=bg_container, border_radius=12,
            border=ft.Border.all(1, with_opacity(0.1, text_primary)),
        )

        quick_actions = ft.Container(
            content=ft.Row([
                ft.Button(
                    "Nuevo Video", icon=ft.Icons.ADD_LINK,
                    on_click=lambda e: self.navigate_to("videos"),
                    bgcolor="#6366f1", color="white", height=38
                ),
                ft.Button(
                    "Nuevo Torrent", icon=ft.Icons.ADD_CIRCLE,
                    on_click=lambda e: self.navigate_to("torrents"),
                    bgcolor="#475569", color="white", height=38
                ),
                ft.Button(
                    "Ver Descargas", icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda e: self._open_downloads_folder(),
                    bgcolor="#059669", color="white", height=38
                ),
            ], spacing=8, wrap=True, run_spacing=8),
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            bgcolor=bg_container, border_radius=12,
            border=ft.Border.all(1, with_opacity(0.1, text_primary))
        )

        recent_activity = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=220)
        downloads = self.video_mgr.get_downloads()
        all_activity = []
        for d in downloads[-5:]:
            all_activity.append({'type': 'video', 'name': d.name, 'progress': d.progress, 'status': d.status.value})
        for t in self._qbit_torrents[:5]:
            all_activity.append({'type': 'torrent', 'name': t['name'], 'progress': t['progress'] * 100,
                                 'status': t['state'] if t['progress'] < 1.0 else 'Completado'})

        if not all_activity:
            recent_activity.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, size=40, color="grey"),
                        ft.Text("No hay actividad reciente", color="grey", size=12)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0), padding=30
                )
            )
        else:
            for item in all_activity:
                recent_activity.controls.append(self._activity_item_compact(item))

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=16, vertical=16),
                expand=True,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Dashboard", size=22, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(f"v{APP_VERSION}", color="grey", size=11),
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            bgcolor=bg_container, border_radius=20,
                        )
                    ]),
                    ft.Container(height=12),
                    stats_row,
                    ft.Container(height=10),
                    space_card,
                    ft.Container(height=10),
                    ft.Text("Acciones Rápidas", size=13, weight=ft.FontWeight.W_600, color="grey"),
                    ft.Container(height=6),
                    quick_actions,
                    ft.Container(height=12),
                    ft.Row([
                        ft.Text("Actividad Reciente", size=13, weight=ft.FontWeight.W_600, color="grey"),
                        ft.Container(expand=True),
                        ft.TextButton("Ver Todo →", on_click=lambda e: self.navigate_to("downloads"))
                    ]),
                    ft.Container(height=6),
                    ft.Container(
                        content=recent_activity, padding=14, bgcolor=bg_container,
                        border_radius=12,
                        border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black"))
                    ),
                    ft.Container(height=12),
                    self._build_usage_stats(),
                ], spacing=0, tight=True)
            )
        ]

    def _build_usage_stats(self):
        is_dark = self.config.theme == "dark"
        bg = "#1e293b" if is_dark else "#f1f5f9"
        border = with_opacity(0.1, "white" if is_dark else "black")
        stats = self.history.get_stats()
        total = stats.get('total_downloads', 0)
        total_gb = stats.get('total_size_gb', 0.0)
        last7 = stats.get('last_7_days', 0)
        avg_mb = stats.get('average_size_mb', 0.0)
        by_platform = stats.get('by_platform', {})
        top = sorted(by_platform.items(), key=lambda x: x[1], reverse=True)[:3]
        platform_chips = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Text(p, size=10, color="#94a3b8"),
                    ft.Text(str(c), size=11, weight=ft.FontWeight.BOLD, color="#6366f1"),
                ], spacing=4),
                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                bgcolor="#334155" if is_dark else "#e2e8f0", border_radius=20,
            ) for p, c in top
        ], spacing=6)
        return ft.Container(
            padding=14, bgcolor=bg, border_radius=12,
            border=ft.Border.all(1, border),
            content=ft.Column([
                ft.Row([
                    ft.Text("Estadísticas de Uso", size=13, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.TextButton("Ver Historial →", on_click=lambda e: self.navigate_to("history")),
                ]),
                ft.Container(height=10),
                ft.Row([
                    ft.Column([
                        ft.Text(str(total), size=22, weight=ft.FontWeight.BOLD, color="#6366f1"),
                        ft.Text("Total descargas", size=10, color="#64748b"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    ft.VerticalDivider(width=1, color="#334155"),
                    ft.Column([
                        ft.Text(f"{total_gb:.1f} GB", size=22, weight=ft.FontWeight.BOLD, color="#3b82f6"),
                        ft.Text("Total descargado", size=10, color="#64748b"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    ft.VerticalDivider(width=1, color="#334155"),
                    ft.Column([
                        ft.Text(str(last7), size=22, weight=ft.FontWeight.BOLD, color="#10b981"),
                        ft.Text("Últimos 7 días", size=10, color="#64748b"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    ft.VerticalDivider(width=1, color="#334155"),
                    ft.Column([
                        ft.Text(f"{avg_mb:.0f} MB", size=22, weight=ft.FontWeight.BOLD, color="#f59e0b"),
                        ft.Text("Tamaño promedio", size=10, color="#64748b"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ], expand=True, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Container(height=10),
                platform_chips if top else ft.Container(),
            ], spacing=0, tight=True)
        )

    def _stat_card_compact(self, icon: str, value: str, title: str, color):
        is_dark = self.config.theme == "dark"
        _color_hex = {
            "blue": "#3b82f6", "green": "#10b981",
            "orange": "#f59e0b", "purple": "#8b5cf6",
            "red": "#ef4444", "cyan": "#06b6d4",
        }
        glow_hex = _color_hex.get(color, color if isinstance(color, str) and color.startswith("#") else "#6366f1")
        base_bg = "#1e293b" if is_dark else "#ffffff"
        base_border = with_opacity(0.1, "white" if is_dark else "black")
        card = ft.Container(
            padding=10, bgcolor=base_bg, border_radius=10,
            border=ft.Border.all(1, base_border), expand=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            content=ft.Column([
                ft.Row([
                    ft.Text(icon, size=18),
                    ft.Container(expand=True),
                    ft.Text(value, size=16, weight=ft.FontWeight.BOLD, color=color),
                ], spacing=4),
                ft.Container(height=6),
                ft.Text(title, size=10, color="grey")
            ], spacing=0, tight=True)
        )

        def on_hover(e):
            if e.data == "true":
                card.border = ft.Border.all(2, glow_hex)
                card.bgcolor = with_opacity(0.12, glow_hex) if is_dark else with_opacity(0.07, glow_hex)
            else:
                card.border = ft.Border.all(1, base_border)
                card.bgcolor = base_bg
            try:
                card.update()
            except Exception:
                pass

        card.on_hover = on_hover
        return card

    def _activity_item_compact(self, item):
        bg_color = "#334155" if self.config.theme == "dark" else "#f1f5f9"
        if item['type'] == 'video':
            icon = ft.Icons.VIDEO_FILE
            icon_color = "purple"
        else:
            icon = ft.Icons.LINK
            icon_color = "blue"
        progress = item.get('progress', 0)
        status_color = "green" if progress >= 100 else "blue"
        return ft.Container(
            padding=12, bgcolor=bg_color, border_radius=10,
            border=ft.Border.all(1, with_opacity(0.05, "white" if self.config.theme == "dark" else "black")),
            content=ft.Row([
                ft.Icon(icon, color=icon_color, size=20),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(item['name'][:40] + "..." if len(item['name']) > 40 else item['name'],
                            size=12, weight=ft.FontWeight.W_500, no_wrap=True),
                    ft.Row([
                        ft.ProgressBar(value=min(1.0, progress / 100), color=status_color,
                                       bgcolor=with_opacity(0.2, status_color), width=100, height=4,
                                       border_radius=2),
                        ft.Container(width=8),
                        ft.Text(f"{progress:.0f}%", size=10, color="grey"),
                    ], spacing=0)
                ], expand=True, spacing=4, tight=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _open_downloads_folder(self):
        try:
            path = self.config.video_path
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            open_folder_externally(path)
        except Exception as e:
            self._show_snack(f"Error: {str(e)}", "red")

    def _cleanup_all(self):
        count_videos = self.video_mgr.cleanup_completed()
        count_torrents = 0
        if self.qbit.connected:
            hashes = [t['hash'] for t in self._qbit_torrents if t['progress'] >= 1.0]
            for h in hashes:
                if self.qbit.control_torrent("delete", h):
                    count_torrents += 1
        total = count_videos + count_torrents
        self._show_snack(f"Limpiados {total} elementos", "green")
        if self._current_section == "dashboard":
            self.navigate_to("dashboard")

    # ═══════════════════════════════════════════════════════════
    # TORRENTS (sección compacta)
    # ═══════════════════════════════════════════════════════════
    def _build_torrents_compact(self):
        sites = {
            "LimeTorrents": "https://www.limetorrents.to/",
            "1377x": "https://www.1377x.to/",
            "YTS": "https://yts-official.org/",
            "ThePirateBay": "https://www.pirateproxy-bay.com/es/"
        }
        self.magnet_input = ft.TextField(
            hint_text="Pegar enlace Magnet...", value=self._magnet_input_text,
            expand=True, border_radius=10, text_size=13, content_padding=14,
            prefix_icon=ft.Icons.LINK, bgcolor="#334155",
            border_color="transparent", color="white", height=44
        )

        def on_magnet_change(e):
            self._magnet_input_text = self.magnet_input.value

        self.magnet_input.on_change = on_magnet_change

        site_dropdown = ft.Dropdown(
            hint_text="Elegir sitio...",
            options=[ft.dropdown.Option(k) for k in sites.keys()],
            value=self._selected_torrent_site, width=160, border_radius=10,
            bgcolor="#334155", border_color="transparent", text_size=12,
            content_padding=ft.Padding(left=12, right=6, top=8, bottom=8), height=40,
        )

        def on_site_change(e):
            self._selected_torrent_site = site_dropdown.value

        site_dropdown.on_change = on_site_change

        def add_magnet_improved(e):
            if not self.magnet_input.value or not self.magnet_input.value.strip():
                self._show_snack("⚠️ Ingresa un enlace magnet", "orange")
                return
            if not self.qbit.connected:
                self._show_error_dialog("qBittorrent Desconectado",
                                        "No hay conexión con qBittorrent.",
                                        "1. qBittorrent está ejecutándose\n2. WebUI está habilitada\n3. Credenciales correctas")
                return
            magnet = self.magnet_input.value.strip()
            self._show_snack("🔗 Procesando...", "blue")

            def process_magnet():
                success, msg = self.qbit.add_magnet(magnet, self.config.torrent_path)

                async def update_result():
                    if success:
                        self.magnet_input.value = ""
                        self._magnet_input_text = ""
                        self._show_snack(msg, "green")
                        await asyncio.sleep(2)
                        self._qbit_torrents = self.qbit.get_torrents()
                        if self._current_section == "torrents":
                            self.navigate_to("torrents")
                    else:
                        self._show_error_dialog("Error al Añadir Torrent",
                                                "No se pudo añadir el torrent.", f"Error: {msg}")
                    self.page.update()

                self.page.run_task(update_result)

            threading.Thread(target=process_magnet, daemon=True).start()

        def clear_finished(e):
            if not self.qbit.connected:
                self._show_snack("No conectado", "red")
                return
            hashes = [t['hash'] for t in self._qbit_torrents if t['progress'] >= 1.0]
            count = 0
            for h in hashes:
                if self.qbit.control_torrent("delete", h):
                    count += 1
            if count > 0:
                self._show_snack(f"Eliminados {count} completados", "green")
                self.navigate_to("torrents")

        self._torrents_list_ctrl = None

        def _empty(icon, color, title, sub, btn=None, btn_fn=None):
            items = [
                ft.Container(
                    content=ft.Icon(icon, size=52, color=color),
                    width=96, height=96, bgcolor=with_opacity(0.08, color),
                    border_radius=48, alignment=ft.Alignment(0, 0),
                ),
                ft.Container(height=14),
                ft.Text(title, size=15, weight=ft.FontWeight.W_600, color="#64748b"),
                ft.Container(height=4),
                ft.Text(sub, size=12, color="#475569"),
            ]
            if btn:
                items += [ft.Container(height=14),
                          ft.Button(btn, icon=ft.Icons.SETTINGS, on_click=btn_fn,
                                            bgcolor="#6366f1", color="white", height=38)]
            return ft.Container(
                content=ft.Column(items, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.symmetric(horizontal=24, vertical=40),
                bgcolor="#0f172a", border_radius=16,
                border=ft.Border.all(1, with_opacity(0.08, "white")),
            )

        if self.qbit.connected:
            if self._qbit_torrents:
                _tlist = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=340)
                self._torrents_list_ctrl = _tlist
                for t in self._qbit_torrents:
                    _tlist.controls.append(self._torrent_item_compact(t))
                torrents_container = ft.Container(
                    content=_tlist, padding=14, bgcolor="#0f172a", border_radius=16,
                    height=376, border=ft.Border.all(1, with_opacity(0.1, "white")),
                )
            else:
                torrents_container = _empty(
                    ft.Icons.CLOUD_DOWNLOAD_OUTLINED, "#6366f1",
                    "Sin torrents activos", "Añade un magnet link para comenzar")
        else:
            torrents_container = _empty(
                ft.Icons.LINK_OFF, "#ef4444",
                "qBittorrent desconectado", "Configura la conexión en Ajustes",
                "Ir a Ajustes", lambda e: self.navigate_to("settings"))

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=24, vertical=20),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Gestión de Torrents", size=24, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE_SWEEP, icon_size=20,
                                      tooltip="Limpiar completados", on_click=clear_finished),
                        ft.IconButton(icon=ft.Icons.REFRESH, icon_size=20,
                                      tooltip="Recargar",
                                      on_click=lambda e: self.navigate_to("torrents")),
                    ]),
                    ft.Container(height=16),
                    ft.Container(
                        padding=20, bgcolor="#1e293b", border_radius=16,
                        border=ft.Border.all(1, with_opacity(0.1, "white")),
                        content=ft.Column([
                            ft.Text("Añadir Nuevo Torrent", size=14, weight=ft.FontWeight.W_600, color="grey"),
                            ft.Container(height=12),
                            ft.Row([
                                self.magnet_input,
                                ft.Button("Añadir", icon=ft.Icons.ADD, on_click=add_magnet_improved,
                                                  bgcolor="#6366f1", color="white", height=44)
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Container(height=16),
                            ft.Container(
                                padding=ft.Padding(left=14, right=14, top=10, bottom=10),
                                bgcolor="#0f172a", border_radius=10,
                                border=ft.Border.all(1, with_opacity(0.08, "white")),
                                content=ft.Row([
                                    ft.Row([
                                        ft.Icon(ft.Icons.TRAVEL_EXPLORE, size=16, color="#6366f1"),
                                        ft.Text("Accesos Directos", size=13, weight=ft.FontWeight.W_600, color="#94a3b8"),
                                    ], spacing=8),
                                    ft.Container(expand=True),
                                    site_dropdown,
                                    ft.Container(width=8),
                                    ft.Button("Copiar URL", icon=ft.Icons.COPY,
                                                      on_click=lambda e: self._copy_site_url(
                                                          sites.get(site_dropdown.value, "")),
                                                      bgcolor="#334155", color="white", height=38),
                                    ft.Container(width=8),
                                    ft.Button("Ir al Sitio", icon=ft.Icons.OPEN_IN_NEW,
                                                      on_click=lambda e: self._open_site_url(
                                                          sites.get(site_dropdown.value, "")),
                                                      bgcolor="#6366f1", color="white", height=38),
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
                            ),
                        ], spacing=0, tight=True)
                    ),
                    ft.Container(height=16),
                    ft.Row([
                        ft.Text("Descargas Activas", size=17, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.Button("Limpiar Completados", icon=ft.Icons.DELETE_SWEEP,
                                          on_click=clear_finished, bgcolor="#dc2626",
                                          color="white", height=36,
                                          tooltip="Elimina los torrents completados (100%)"),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=10),
                    torrents_container,
                    ft.Container(height=16),
                    self._build_speed_chart(),
                ], spacing=0, tight=True)
            )
        ]

    def _build_speed_chart(self):
        is_dark = self.config.theme == "dark"
        bg = "#1e293b" if is_dark else "#f1f5f9"
        border = with_opacity(0.1, "white" if is_dark else "black")
        history = self._speed_history[-30:] if self._speed_history else []
        if not history:
            return ft.Container(
                padding=14, bgcolor=bg, border_radius=12,
                border=ft.Border.all(1, border),
                content=ft.Column([
                    ft.Text("Velocidad en Tiempo Real", size=13, weight=ft.FontWeight.W_600, color="#64748b"),
                    ft.Container(height=8),
                    ft.Text("Sin datos — conectá qBittorrent para ver el gráfico", size=11, color="#475569"),
                ], spacing=0)
            )
        last = history[-1]
        dl_now = last['dl']
        ul_now = last['ul']
        # Usar barras simples en lugar de SVG para compatibilidad con Flet
        max_val = max((max(p['dl'] for p in history), max(p['ul'] for p in history), 1))
        bars = []
        for i, p in enumerate(history[-20:]):
            h_dl = int((p['dl'] / max_val) * 60) if max_val > 0 else 0
            bars.append(
                ft.Container(
                    width=8, height=max(h_dl, 2), bgcolor="#3b82f6",
                    border_radius=2, margin=ft.Margin.only(right=2)
                )
            )
        return ft.Container(
            padding=14, bgcolor=bg, border_radius=12,
            border=ft.Border.all(1, border),
            content=ft.Column([
                ft.Row([
                    ft.Text("Velocidad en Tiempo Real", size=13, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Container(width=10, height=3, bgcolor="#3b82f6", border_radius=2),
                        ft.Text(f"⬇ {dl_now:.0f} KB/s", size=11, color="#3b82f6"),
                        ft.Container(width=12),
                        ft.Container(width=10, height=3, bgcolor="#f59e0b", border_radius=2),
                        ft.Text(f"⬆ {ul_now:.0f} KB/s", size=11, color="#f59e0b"),
                    ], spacing=4),
                ]),
                ft.Container(height=8),
                ft.Row(bars, spacing=0, height=60, vertical_alignment=ft.CrossAxisAlignment.END),
            ], spacing=0)
        )

    def _copy_site_url(self, url):
        if url:
            pyperclip.copy(url)
            self._show_snack("URL copiada al portapapeles", "blue")

    def _open_site_url(self, url):
        if url:
            try:
                webbrowser.open(url)
                self._show_snack("🌐 Abriendo sitio en el navegador...", "blue")
            except Exception as e:
                self._show_snack(f"Error abriendo sitio: {str(e)[:50]}", "red")

    def _torrent_item_compact(self, torrent: Dict):
        progress = torrent['progress']
        is_finished = progress >= 1.0
        size_gb = torrent.get('size', 0) / (1024 ** 3)
        downloaded_gb = size_gb * progress
        dl_speed_kb = torrent.get('dlspeed', 0) / 1024
        ul_speed_kb = torrent.get('upspeed', 0) / 1024
        eta = torrent.get('eta', 8640000)
        state = torrent.get('state', '')
        if is_finished:
            status_color, status_bg, status_icon, status_text = "#10b981", with_opacity(0.15, "#10b981"), ft.Icons.CHECK_CIRCLE, "Completado"
        elif state == 'downloading':
            status_color, status_bg, status_icon, status_text = "#3b82f6", with_opacity(0.15, "#3b82f6"), ft.Icons.DOWNLOADING, "Descargando"
        elif state == 'uploading':
            status_color, status_bg, status_icon, status_text = "#f59e0b", with_opacity(0.15, "#f59e0b"), ft.Icons.UPLOAD, "Subiendo"
        elif state == 'pausedDL':
            status_color, status_bg, status_icon, status_text = "#6b7280", with_opacity(0.15, "#6b7280"), ft.Icons.PAUSE_CIRCLE, "Pausado"
        elif state == 'error':
            status_color, status_bg, status_icon, status_text = "#ef4444", with_opacity(0.15, "#ef4444"), ft.Icons.ERROR, "Error"
        elif state == 'metaDL':
            status_color, status_bg, status_icon, status_text = "#8b5cf6", with_opacity(0.15, "#8b5cf6"), ft.Icons.HOURGLASS_TOP, "Metadatos"
        else:
            status_color, status_bg, status_icon, status_text = "#64748b", with_opacity(0.15, "#64748b"), ft.Icons.INFO, state[:10] if state else "Desconocido"

        def format_eta(seconds):
            if seconds >= 8640000 or seconds < 0:
                return "∞"
            if seconds < 60:
                return f"{int(seconds)}s"
            elif seconds < 3600:
                return f"{int(seconds / 60)}m"
            elif seconds < 86400:
                return f"{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m"
            else:
                return f"{int(seconds / 86400)}d"

        name = torrent['name']
        if len(name) > 60:
            name = name[:57] + "..."
        return ft.Container(
            padding=ft.Padding(left=18, right=18, top=16, bottom=16),
            bgcolor="#1e293b", border_radius=14,
            border=ft.Border.all(1, with_opacity(0.08, "white")),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(status_icon, size=18, color=status_color),
                        bgcolor=status_bg, width=36, height=36, border_radius=10,
                        alignment=ft.Alignment(0, 0), margin=ft.Margin.only(right=14),
                    ),
                    ft.Column([
                        ft.Text(name, weight=ft.FontWeight.W_500, size=14, color="white", no_wrap=True, expand=True),
                        ft.Row([
                            ft.Text(f"{downloaded_gb:.2f} / {size_gb:.2f} GB", size=12, color="#64748b"),
                            ft.Text(" • ", size=12, color="#475569"),
                            ft.Text(f"{progress * 100:.1f}%", size=12, color=status_color, weight=ft.FontWeight.W_500),
                        ], spacing=0),
                    ], spacing=4, expand=True),
                    ft.Container(
                        content=ft.Text(status_text, size=11, color=status_color, weight=ft.FontWeight.W_500),
                        bgcolor=status_bg,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6), border_radius=20,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                ft.Container(height=14),
                ft.Container(
                    content=ft.ProgressBar(value=progress, color=status_color, bgcolor="#334155",
                                           height=6, border_radius=3),
                    border_radius=3,
                ),
                ft.Container(height=14),
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.ARROW_DOWNWARD, size=14, color="#3b82f6"),
                        ft.Text(f"{dl_speed_kb:.0f} KB/s" if dl_speed_kb > 0 else "—", size=12, color="#94a3b8"),
                    ], spacing=6),
                    ft.Text("  ", size=12),
                    ft.Row([
                        ft.Icon(ft.Icons.ARROW_UPWARD, size=14, color="#f59e0b"),
                        ft.Text(f"{ul_speed_kb:.0f} KB/s" if ul_speed_kb > 0 else "—", size=12, color="#94a3b8"),
                    ], spacing=6),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Icon(ft.Icons.SCHEDULE, size=14, color="#64748b"),
                        ft.Text(f"ETA: {format_eta(eta)}", size=12, color="#64748b"),
                    ], spacing=6),
                    ft.Container(width=8),
                    ft.IconButton(icon=ft.Icons.INFO_OUTLINE, icon_size=18, icon_color="#6366f1",
                                  tooltip="Pares y Trackers",
                                  on_click=lambda e, t=torrent: self._show_torrent_details(t)),
                ], spacing=0),
            ], spacing=0, tight=True)
        )

    def _show_torrent_details(self, torrent: Dict):
        hash_str = torrent.get('hash', '')
        name = torrent.get('name', 'Torrent')[:50]

        def fetch_details():
            peers = self.qbit.get_peers(hash_str)
            trackers = self.qbit.get_trackers(hash_str)
            return peers, trackers

        def show_dialog(result):
            peers, trackers = result
            peer_rows = []
            for p in peers[:10]:
                ip = p.get('ip', '?')
                country = p.get('country_code', '??')
                dl = p.get('dl_speed', 0) / 1024
                prog = p.get('progress', 0) * 100
                peer_rows.append(
                    ft.Row([
                        ft.Text(f"{country}", size=11, color="#6366f1", width=28),
                        ft.Text(f"{ip}", size=11, color="#94a3b8", expand=True),
                        ft.Text(f"⬇ {dl:.0f} KB/s", size=11, color="#3b82f6", width=80),
                        ft.Text(f"{prog:.0f}%", size=11, color="#10b981", width=40),
                    ], spacing=8)
                )
            if not peer_rows:
                peer_rows.append(ft.Text("Sin pares conectados", size=11, color="#64748b"))
            tracker_rows = []
            for t in trackers:
                url = t.get('url', '')[:50]
                status = t.get('status', 0)
                seeds = t.get('num_seeds', 0)
                color = "#10b981" if status == 2 else "#ef4444" if status == 4 else "#64748b"
                status_txt = "OK" if status == 2 else "Error" if status == 4 else "..."
                tracker_rows.append(
                    ft.Row([
                        ft.Container(
                            content=ft.Text(status_txt, size=9, color=color),
                            bgcolor=with_opacity(0.15, color),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2), border_radius=4,
                        ),
                        ft.Text(url, size=11, color="#94a3b8", expand=True),
                        ft.Text(f"🌱{seeds}", size=11, color="#64748b"),
                    ], spacing=8)
                )
            if not tracker_rows:
                tracker_rows.append(ft.Text("Sin trackers", size=11, color="#64748b"))
            dialog = ft.AlertDialog(
                modal=True, title=ft.Text(name, size=14, weight=ft.FontWeight.W_600),
                content=ft.Container(
                    width=480,
                    content=ft.Column([
                        ft.Text(f"Pares ({len(peers)})", size=12, weight=ft.FontWeight.W_600, color="#6366f1"),
                        ft.Container(height=6),
                        ft.Column(peer_rows, spacing=4),
                        ft.Divider(height=16, color="#334155"),
                        ft.Text(f"Trackers ({len(trackers)})", size=12, weight=ft.FontWeight.W_600, color="#f59e0b"),
                        ft.Container(height=6),
                        ft.Column(tracker_rows, spacing=4),
                    ], scroll=ft.ScrollMode.AUTO, spacing=0),
                    height=320,
                ),
                shape=ft.RoundedRectangleBorder(radius=12),
                actions=[ft.TextButton("Cerrar", on_click=lambda e: (setattr(dialog, 'open', False) or self.page.update()))],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        async def _run():
            result = await asyncio.to_thread(fetch_details)
            show_dialog(result)

        self._show_snack("Cargando detalles...", "blue")
        self.page.run_task(_run)

    # ═══════════════════════════════════════════════════════════
    # VIDEOS
    # ═══════════════════════════════════════════════════════════
    def _build_videos_compact(self):
        initial_url = self._detected_video_url
        if initial_url:
            self._detected_video_url = ""
        recent_urls = self.clipboard_history.get_recent(5)
        url_input = ft.TextField(
            hint_text="URL de YouTube, TikTok, Instagram...", value=initial_url,
            expand=True, height=48, border_radius=10, prefix_icon=ft.Icons.LINK,
            text_size=14, content_padding=14,
            border_color=with_opacity(0.2, "white") if self.config.theme == "dark" else None
        )
        quality_options = ["720", "1080", "1440", "2160", "best"]
        quality_dropdown = ft.Dropdown(
            label="Calidad", options=[ft.dropdown.Option(q) for q in quality_options],
            value=self.config.video_quality, width=110, border_radius=10,
            text_size=13, content_padding=10, height=48
        )
        audio_format_dropdown = ft.Dropdown(
            label="Formato audio",
            options=[
                ft.dropdown.Option("video", "🎬 Video (MP4)"),
                ft.dropdown.Option("mp3", "🎵 MP3 (320kbps)"),
                ft.dropdown.Option("m4a", "🎵 M4A (AAC)"),
                ft.dropdown.Option("flac", "🎵 FLAC (sin pérdida)"),
                ft.dropdown.Option("ogg", "🎵 OGG (Vorbis)"),
                ft.dropdown.Option("opus", "🎵 OPUS"),
                ft.dropdown.Option("wav", "🎵 WAV"),
            ],
            value="video", width=180, border_radius=10, text_size=13, content_padding=10, height=48,
        )
        schedule_field = ft.TextField(
            label="⏰ Programar (HH:MM)", hint_text="Ej: 23:30", width=150, height=48,
            border_radius=10, text_size=13, content_padding=10, max_length=5,
        )

        def download_click(e):
            url = url_input.value.strip()
            if not url:
                return
            quality = quality_dropdown.value
            fmt = audio_format_dropdown.value
            audio_only = fmt != "video"
            audio_fmt = fmt if audio_only else None
            is_playlist = ("playlist" in url.lower() or "list=" in url.lower()) and \
                          ("youtube" in url.lower() or "youtu.be" in url.lower())
            if is_playlist:
                self._confirm_playlist_download(url, quality, audio_only, audio_fmt)
                url_input.value = ""
                self.page.update()
                return
            self._show_snack(f"Iniciando descarga ({quality}p)...", "blue")
            sched = schedule_field.value.strip() if schedule_field.value else None
            if sched:
                if not re.match(r'^\d{1,2}:\d{2}$', sched):
                    self._show_snack("⚠️ Formato de hora inválido. Usa HH:MM", "orange")
                    return
            download_id = self.video_mgr.download(
                url, self.config.video_path,
                use_cookies=self.config.use_cookies, cookies_path=self.config.cookies_path,
                quality=quality, audio_only=audio_only, audio_format=audio_fmt,
                scheduled_time=sched,
            )
            if download_id is None:
                self._show_snack("yt-dlp no instalado", "red")
            else:
                url_input.value = ""
                schedule_field.value = ""
                self.config.video_quality = quality
                self.save_config()
                if sched:
                    self._show_snack(f"⏰ Descarga programada para las {sched}", "green")
                self.navigate_to("downloads")

        def update_ytdlp(e):
            self._show_snack("Actualizando yt-dlp...", "blue")

            def run_update():
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                                   check=True, capture_output=True, timeout=120)
                    self.has_ytdlp = self._check_ytdlp()
                    self.ytdlp_version = self._get_ytdlp_version()
                    self._show_snack(f"✅ Actualizado a v{self.ytdlp_version}", "green")
                except Exception as ex:
                    self._show_snack(f"❌ Error: {str(ex)[:80]}", "red")
                self.page.update()

            threading.Thread(target=run_update, daemon=True).start()

        def use_recent_url(url):
            url_input.value = url
            self.page.update()

        recent_urls_chips = ft.Row([
            ft.Container(
                content=ft.Text(url[:35] + "..." if len(url) > 35 else url, size=11, color="#e2e8f0"),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                bgcolor="#334155", border_radius=20,
                border=ft.Border.all(1, "#475569"),
                tooltip="Clic para usar esta URL",
                on_click=lambda e, u=url: use_recent_url(u), ink=True,
            ) for url in recent_urls[:3]
        ], spacing=8, scroll=ft.ScrollMode.AUTO, visible=len(recent_urls) > 0)

        recent_section = ft.Column([
            ft.Text("URLs recientes:", size=11, color="#94a3b8"),
            ft.Container(height=6),
            recent_urls_chips,
        ], spacing=0, visible=len(recent_urls) > 0)

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=24, vertical=20),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Descargar Videos", size=24, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Button("Actualizar yt-dlp", icon=ft.Icons.UPDATE, on_click=update_ytdlp,
                                          bgcolor="#c2410c", color="white", height=40)
                    ]),
                    ft.Container(height=16),
                    ft.Row([
                        url_input, quality_dropdown,
                        ft.Button("Descargar", icon=ft.Icons.DOWNLOAD, on_click=download_click,
                                          bgcolor="#6366f1", color="white", height=48)
                    ], spacing=10),
                    ft.Container(height=10),
                    ft.Row([audio_format_dropdown, ft.Container(width=10), schedule_field, ft.Container(expand=True)]),
                    ft.Container(height=12),
                    recent_section,
                    ft.Container(height=16),
                    ft.Container(
                        padding=20, bgcolor="#1e293b", border_radius=16,
                        border=ft.Border.all(1, with_opacity(0.1, "white")),
                        content=ft.Column([
                            ft.Text("ℹ️ Información y Consejos", weight=ft.FontWeight.W_600, size=14, color="#60a5fa"),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color="#10b981"),
                                ft.Text("Soporta: YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo", size=12, expand=True),
                            ], spacing=8),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Icon(ft.Icons.COOKIE, size=16, color="#f59e0b"),
                                ft.Text("Para videos restringidos: Usa Cookies en Configuración", size=12, expand=True),
                            ], spacing=8),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Icon(ft.Icons.SETTINGS, size=16, color="#8b5cf6"),
                                ft.Text("Instala ffmpeg para mejor calidad y formato MP4", size=12, expand=True),
                            ], spacing=8),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Icon(ft.Icons.SPEED, size=16, color="#3b82f6"),
                                ft.Text(f"Máximo {self.config.max_concurrent_downloads} descargas simultáneas", size=12, expand=True),
                            ], spacing=8),
                            ft.Container(height=8),
                            ft.Divider(height=1, color="#334155"),
                            ft.Container(height=8),
                            ft.Text(f"Versión instalada: yt-dlp {self.ytdlp_version}", size=11, color="grey")
                        ], spacing=4, tight=True)
                    )
                ], spacing=0, tight=True)
            )
        ]

    # ═══════════════════════════════════════════════════════════
    # DESCARGAS
    # ═══════════════════════════════════════════════════════════
    def _build_downloads_compact(self):
        downloads = self.video_mgr.get_downloads()
        is_dark = self.config.theme == "dark"
        total_downloads = len(downloads)
        active_downloads = len([d for d in downloads if d.status == DownloadStatus.DOWNLOADING])
        queued_downloads = len([d for d in downloads if d.status == DownloadStatus.QUEUED])
        completed_downloads = len([d for d in downloads if d.status == DownloadStatus.COMPLETED])
        error_downloads = len([d for d in downloads if d.status == DownloadStatus.ERROR])

        def clear_completed(e):
            count = self.video_mgr.cleanup_completed()
            self._show_snack(f"✅ Limpiados {count} elementos" if count > 0 else "ℹ️ No hay elementos para limpiar",
                             "green" if count > 0 else "blue")
            self.navigate_to("downloads")
            self.page.update()

        def pause_all(e):
            paused = 0
            for d in downloads:
                if d.status == DownloadStatus.DOWNLOADING:
                    if self.video_mgr.pause_download(d.id):
                        paused += 1
            if paused > 0:
                self._show_snack(f"⏸️ Pausadas {paused} descargas", "orange")
                self.page.update()

        def _stat_card(icon, icon_color, value, label):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=18, color=icon_color),
                        width=36, height=36, bgcolor=with_opacity(0.15, icon_color),
                        border_radius=10, alignment=ft.Alignment(0, 0)
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=icon_color),
                        ft.Text(label, size=11, color="#64748b"),
                    ], spacing=0)
                ], spacing=0),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                bgcolor="#1e293b" if is_dark else "#ffffff", border_radius=12,
                border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black")),
                expand=True
            )

        stats_row = ft.Row([
            _stat_card(ft.Icons.DOWNLOADING, "#3b82f6", active_downloads, "Activas"),
            _stat_card(ft.Icons.QUEUE, "#f59e0b", queued_downloads, "En Cola"),
            _stat_card(ft.Icons.CHECK_CIRCLE_OUTLINE, "#10b981", completed_downloads, "Completadas"),
            _stat_card(ft.Icons.ERROR_OUTLINE, "#ef4444" if error_downloads > 0 else "#64748b", error_downloads, "Errores"),
        ], spacing=10)

        controls_row = ft.Row([
            ft.TextButton("Limpiar completadas", icon=ft.Icons.CLEANING_SERVICES, on_click=clear_completed,
                          style=ft.ButtonStyle(color="#10b981")),
            ft.TextButton("Pausar/Reanudar todo", icon=ft.Icons.PAUSE_CIRCLE, on_click=pause_all,
                          style=ft.ButtonStyle(color="#f59e0b")),
            ft.TextButton("Reintentar fallidas", icon=ft.Icons.REPLAY,
                          on_click=lambda e: self._retry_all_failed(),
                          style=ft.ButtonStyle(color="#ef4444" if error_downloads > 0 else "#64748b")),
            ft.Container(expand=True),
            ft.IconButton(ft.Icons.REFRESH_ROUNDED, tooltip="Actualizar", icon_color="#6366f1", icon_size=22,
                          on_click=lambda e: self.navigate_to("downloads")),
        ], spacing=8)

        list_height = 420
        if downloads:
            list_items = [self._download_item_card(d) for d in downloads]
        else:
            list_items = [
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=40),
                        ft.Container(
                            content=ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, size=72, color="#334155"),
                            width=120, height=120, bgcolor=with_opacity(0.1, "#334155"),
                            border_radius=60, alignment=ft.Alignment(0, 0)
                        ),
                        ft.Container(height=24),
                        ft.Text("No hay descargas activas", size=18, weight=ft.FontWeight.W_500, color="#64748b"),
                        ft.Text("Pega un enlace de video para comenzar", size=13, color="#475569"),
                        ft.Container(height=12),
                        ft.Text("YouTube • TikTok • Instagram • Twitter • Vimeo", size=11, color="#64748b"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    alignment=ft.Alignment(0, 0), padding=30
                )
            ]

        list_column = ft.Column(list_items, spacing=10, scroll=ft.ScrollMode.AUTO, height=list_height)
        self._downloads_list_ctrl = list_column
        list_container = ft.Container(
            content=list_column, padding=18,
            bgcolor="#0f172a" if is_dark else "#f8fafc", border_radius=16,
            border=ft.Border.all(1, with_opacity(0.08, "white" if is_dark else "black")),
            height=list_height + 36,
        )

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=24, vertical=20),
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=24, color="white"),
                            width=48, height=48, bgcolor="#6366f1", border_radius=14,
                            alignment=ft.Alignment(0, 0)
                        ),
                        ft.Container(width=14),
                        ft.Column([
                            ft.Text("Descargas de Video", size=22, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{total_downloads} elementos • {queued_downloads} en cola", size=12, color="#64748b"),
                        ], spacing=4),
                        ft.Container(expand=True),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=20),
                    stats_row,
                    ft.Container(height=14),
                    controls_row,
                    ft.Container(height=18),
                    list_container,
                ], spacing=0, tight=True)
            )
        ]

    def _download_item_card(self, d: VideoDownload):
        is_dark = self.config.theme == "dark"
        status_value = d.status.value if hasattr(d.status, 'value') else str(d.status)
        is_completed = d.status == DownloadStatus.COMPLETED
        is_error = d.status == DownloadStatus.ERROR
        is_cancelled = d.status == DownloadStatus.CANCELLED
        is_downloading = d.status == DownloadStatus.DOWNLOADING
        is_queued = d.status == DownloadStatus.QUEUED
        is_paused = d.status == DownloadStatus.PAUSED

        if is_completed:
            accent_color, status_icon, status_text = "#10b981", ft.Icons.CHECK_CIRCLE, "Completado"
        elif is_error:
            accent_color, status_icon, status_text = "#ef4444", ft.Icons.ERROR, "Error"
        elif is_cancelled:
            accent_color, status_icon, status_text = "#6b7280", ft.Icons.CANCEL, "Cancelado"
        elif is_downloading:
            accent_color, status_icon, status_text = "#3b82f6", ft.Icons.DOWNLOADING, "Descargando"
        elif is_queued:
            accent_color, status_icon, status_text = "#f59e0b", ft.Icons.QUEUE, "En Cola"
        elif is_paused:
            accent_color, status_icon, status_text = "#6b7280", ft.Icons.PAUSE_CIRCLE, "Pausado"
        else:
            accent_color, status_icon, status_text = "#f59e0b", ft.Icons.SCHEDULE, "Pendiente"
        status_bg = with_opacity(0.15, accent_color)

        if d.thumbnail and os.path.exists(d.thumbnail):
            thumb_content = ft.Image(src=d.thumbnail, width=110, height=75, fit="cover", border_radius=10)
        else:
            thumb_content = ft.Container(
                content=None,
                width=110, height=75, bgcolor="#1e293b" if is_dark else "#e2e8f0",
                border_radius=10, alignment=ft.Alignment(0, 0)
            )

        action_widgets = []
        if is_completed:
            action_widgets.append(ft.IconButton(icon=ft.Icons.FOLDER_OPEN, icon_color="#6366f1", icon_size=28,
                                                tooltip="Abrir carpeta", on_click=lambda e: self._open_downloads_folder()))
            if d.filepath and os.path.exists(d.filepath):
                action_widgets.insert(0, ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILL, icon_color="#10b981",
                                                       icon_size=40, tooltip="Reproducir video",
                                                       on_click=lambda e, fp=d.filepath: self._play_video(fp)))
        elif is_downloading or is_queued or is_paused:
            action_widgets.append(ft.IconButton(icon=ft.Icons.PAUSE if not is_paused else ft.Icons.PLAY_ARROW,
                                                icon_color="#f59e0b", icon_size=28, tooltip="Pausar/Reanudar",
                                                on_click=lambda e, dl=d: self._toggle_pause_download(dl)))
            action_widgets.append(ft.IconButton(icon=ft.Icons.CANCEL, icon_color="#ef4444", icon_size=28,
                                                tooltip="Cancelar",
                                                on_click=lambda e, dl=d: self._handle_download_action(e, dl)))
        elif is_error:
            action_widgets.append(ft.IconButton(icon=ft.Icons.REFRESH, icon_color="#f59e0b", icon_size=28,
                                                tooltip="Reintentar",
                                                on_click=lambda e, dl=d: self._retry_download(dl)))

        main_content = ft.Row([
            ft.Container(content=thumb_content, border_radius=10, clip_behavior="hardEdge"),
            ft.Container(width=16),
            ft.Column([
                ft.Text(d.name[:70] + ("..." if len(d.name) > 70 else ""), size=14, weight=ft.FontWeight.W_500,
                        color="white" if is_dark else "#1e293b", max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                ft.Container(height=8),
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(status_icon, size=14, color=accent_color),
                            ft.Container(width=6),
                            ft.Text(status_text, size=11, color=accent_color, weight=ft.FontWeight.W_500),
                        ], spacing=0),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                        bgcolor=status_bg, border_radius=8
                    ),
                    ft.Container(width=10),
                    ft.Text(d.speed if is_downloading else (f"✓ {d.progress:.0f}%" if is_completed else f"{d.progress:.0f}%"),
                            size=11, color="#64748b") if not is_error else ft.Container(),
                ], spacing=0),
                ft.Container(height=10),
                ft.Container(
                    content=ft.ProgressBar(
                        value=d.progress / 100 if is_downloading else (1.0 if is_completed else 0),
                        color=accent_color, bgcolor=with_opacity(0.15, accent_color),
                        height=5, border_radius=3, expand=True
                    ) if not is_error and not is_cancelled else ft.ProgressBar(
                        value=0, color=accent_color, bgcolor=with_opacity(0.15, accent_color),
                        height=5, border_radius=3, expand=True
                    ),
                ) if not is_error and not is_cancelled else ft.Container(),
            ], expand=True, spacing=0),
            ft.Container(width=10),
            ft.Row(action_widgets, spacing=6, alignment=ft.MainAxisAlignment.END) if action_widgets else ft.Container(width=20)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        error_section = ft.Container()
        if is_error and d.error_msg:
            error_section = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=16, color="#f59e0b"),
                    ft.Container(width=8),
                    ft.Text(d.error_msg[:100], size=11, color="#fbbf24", expand=True),
                ], spacing=0),
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                bgcolor=with_opacity(0.1, "#f59e0b"), border_radius=10,
                margin=ft.Margin.only(top=12, left=126)
            )
            main_content = ft.Column([main_content, error_section], spacing=0)

        return ft.Container(
            content=ft.Container(content=main_content, padding=14),
            bgcolor="#1e293b" if is_dark else "#ffffff", border_radius=16,
            border=ft.Border.all(1, with_opacity(0.08, "white" if is_dark else "black")),
            on_click=lambda e, did=d.id: self._select_download(did),
        )

    def _select_download(self, download_id: int):
        self._selected_download_id = download_id

    def _toggle_pause_download(self, d: VideoDownload):
        if d.status == DownloadStatus.PAUSED:
            d.status = DownloadStatus.DOWNLOADING
            threading.Thread(target=self.video_mgr._download_thread, args=(d.id,), daemon=True).start()
            self._show_snack("▶️ Descarga reanudada", "blue")
        else:
            d._pause_requested = True
            proc = getattr(d, "subprocess", None)
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
            self._show_snack("⏸️ Descarga pausada", "orange")
        self.page.update()

    # ═══════════════════════════════════════════════════════════
    # HISTORIAL
    # ═══════════════════════════════════════════════════════════
    def _build_history_compact(self):
        is_dark = self.config.theme == "dark"
        bg_card = "#1e293b" if is_dark else "#f1f5f9"
        border = with_opacity(0.1, "white" if is_dark else "black")
        stats = self.history.get_stats()
        by_date = stats.get('by_date', {})
        today = datetime.now().date()
        days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        day_counts = [by_date.get(d.strftime('%Y-%m-%d'), 0) for d in days]
        max_count = max(day_counts) if any(day_counts) else 1

        # Gráfico de barras con Containers en vez de SVG
        bar_controls = []
        for i, count in enumerate(day_counts):
            h = int((count / max_count) * 50) if max_count > 0 else 2
            color = "#6366f1" if i == 6 else "#334155" if is_dark else "#e2e8f0"
            bar_controls.append(
                ft.Column([
                    ft.Container(width=30, height=max(h, 2), bgcolor=color, border_radius=4),
                    ft.Container(height=4),
                    ft.Text(days[i].strftime('%d'), size=9, color="#64748b"),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        activity_chart = ft.Row(bar_controls, spacing=6, vertical_alignment=ft.CrossAxisAlignment.END, height=70)

        by_platform = stats.get('by_platform', {})
        total_pl = sum(by_platform.values()) or 1
        platform_bars = []
        for plat, count in sorted(by_platform.items(), key=lambda x: -x[1])[:5]:
            pct = count / total_pl
            p_colors = {'YouTube': '#ef4444', 'TikTok': '#000000', 'Instagram': '#e1306c',
                        'Twitter': '#1da1f2', 'Facebook': '#1877f2', 'Vimeo': '#1ab7ea'}
            col = p_colors.get(plat, "#6366f1")
            platform_bars.append(ft.Column([
                ft.Row([
                    ft.Text(plat, size=11, color="#94a3b8", expand=True),
                    ft.Text(str(count), size=11, color=col, weight=ft.FontWeight.BOLD),
                ], spacing=0),
                ft.ProgressBar(value=pct, color=col, bgcolor=with_opacity(0.15, col), height=4, border_radius=2),
            ], spacing=3, tight=True))

        stats_panel = ft.Container(
            padding=14, bgcolor=bg_card, border_radius=12,
            border=ft.Border.all(1, border),
            content=ft.Row([
                ft.Column([
                    ft.Text("Actividad (7 días)", size=11, weight=ft.FontWeight.W_600, color="#64748b"),
                    ft.Container(height=6),
                    activity_chart,
                ], spacing=0),
                ft.Container(width=20),
                ft.Column([
                    ft.Text("Por Plataforma", size=11, weight=ft.FontWeight.W_600, color="#64748b"),
                    ft.Container(height=6),
                    ft.Column(platform_bars, spacing=6, tight=True),
                ] if platform_bars else [
                    ft.Text("Sin datos de plataforma", size=11, color="#475569")
                ], spacing=0, expand=True),
                ft.Container(width=20),
                ft.Column([
                    ft.Text("Resumen", size=11, weight=ft.FontWeight.W_600, color="#64748b"),
                    ft.Container(height=6),
                    ft.Text(f"Total: {stats['total_downloads']}", size=12, color="#e2e8f0" if is_dark else "#1e293b"),
                    ft.Text(f"Descargado: {stats['total_size_gb']:.2f} GB", size=12, color="#3b82f6"),
                    ft.Text(f"Promedio: {stats['average_size_mb']:.1f} MB", size=12, color="#10b981"),
                    ft.Text(f"Esta semana: {stats['last_7_days']}", size=12, color="#f59e0b"),
                ], spacing=4, tight=True),
            ], vertical_alignment=ft.CrossAxisAlignment.START)
        )

        search_field = ft.TextField(hint_text="Buscar en historial...", prefix_icon=ft.Icons.SEARCH,
                                    border_radius=10, height=40, content_padding=10, expand=True)
        date_filter = ft.Dropdown(
            hint_text="Filtrar por fecha",
            options=[
                ft.dropdown.Option("", "Todas las fechas"),
                ft.dropdown.Option(datetime.now().strftime("%Y-%m-%d"), "Hoy"),
                ft.dropdown.Option((datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"), "Última semana"),
                ft.dropdown.Option((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), "Último mes"),
            ], width=150, border_radius=8
        )

        platform_stats = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Text(plat, size=10, color="#94a3b8"),
                    ft.Text(str(count), size=12, weight=ft.FontWeight.BOLD, color="#6366f1"),
                ], spacing=4),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                bgcolor="#334155", border_radius=20
            ) for plat, count in list(stats.get('by_platform', {}).items())[:4]
        ], spacing=8, wrap=True)

        by_platform = stats.get('by_platform', {})
        top_platform = max(by_platform, key=by_platform.get) if by_platform else "—"
        top_count = by_platform.get(top_platform, 0)
        stats_row = ft.Row([
            self._stat_card_compact("📊", str(stats['total_downloads']), f"Total {stats['trend']}", "#8b5cf6"),
            self._stat_card_compact("💾", f"{stats['total_size_gb']:.2f} GB", "Descargado", "#3b82f6"),
            self._stat_card_compact("📈", f"{stats['average_size_mb']:.1f} MB", "Promedio", "#10b981"),
            self._stat_card_compact("📅", str(stats['last_7_days']), "Últimos 7 días", "#f59e0b"),
            self._stat_card_compact("🏆", f"{top_platform[:8]} ({top_count})", "Top sitio", "#ef4444"),
        ], spacing=8)

        def clear_history(e):
            dialog = ft.AlertDialog(
                modal=True, title=ft.Text("¿Limpiar historial?", size=16),
                content=ft.Text("Esta acción no se puede deshacer. ¿Continuar?"),
                shape=ft.RoundedRectangleBorder(radius=12),
            )

            def do_cancel(ev):
                dialog.open = False
                self.page.update()

            def do_confirm(ev):
                dialog.open = False
                self.page.update()
                self.history.clear_history()
                self._show_snack("Historial limpiado", "green")
                self.navigate_to("history")

            dialog.actions = [
                ft.TextButton("Cancelar", on_click=do_cancel),
                ft.Button("Sí, limpiar", bgcolor="#dc2626", color="white", on_click=do_confirm),
            ]
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        def export_history(e):
            def export_csv(ev):
                path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialfile="videoflex_history.csv"
                )
                if path:
                    if self.history.export_to_csv(path):
                        self._show_snack(f"✅ Exportado a: {path}", "green")
                    else:
                        self._show_snack("❌ Error al exportar", "red")
                dialog.open = False
                self.page.update()

            def export_json(ev):
                try:
                    path = filedialog.asksaveasfilename(
                        defaultextension=".json",
                        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                        initialfile="videoflex_history.json"
                    )
                    if path:
                        items = self.history.get_history()
                        with open(path, 'w', encoding='utf-8') as f:
                            json.dump(items, f, indent=2, ensure_ascii=False)
                        self._show_snack(f"✅ Exportado a: {path}", "green")
                except Exception as ex:
                    self._show_snack(f"❌ Error: {str(ex)[:50]}", "red")
                dialog.open = False
                self.page.update()

            dialog = ft.AlertDialog(
                modal=True, title=ft.Text("Exportar Historial", size=16),
                content=ft.Text("Selecciona el formato de exportación:"),
                shape=ft.RoundedRectangleBorder(radius=12),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda ev: (setattr(dialog, 'open', False) or self.page.update())),
                    ft.Button("CSV", icon=ft.Icons.TABLE_CHART, on_click=export_csv),
                    ft.Button("JSON", icon=ft.Icons.CODE, on_click=export_json),
                ]
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        def apply_filters(e):
            filtered = self.history.get_history(
                search_query=search_field.value or "",
                date_filter=date_filter.value or ""
            )
            history_list.controls.clear()
            for item in filtered[:50]:
                history_list.controls.append(self._history_item_compact(item))
            self.page.update()

        search_field.on_submit = apply_filters

        controls_row = ft.Row([
            ft.FilledButton("Limpiar Historial", icon=ft.Icons.DELETE_SWEEP, on_click=clear_history,
                            style=ft.ButtonStyle(bgcolor="#dc2626", color="white",
                                                 shape=ft.RoundedRectangleBorder(radius=8)), height=38),
            ft.FilledButton("Exportar", icon=ft.Icons.DOWNLOAD, on_click=export_history,
                            style=ft.ButtonStyle(bgcolor="#059669", color="white",
                                                 shape=ft.RoundedRectangleBorder(radius=8)), height=38),
            ft.Container(expand=True),
            search_field, ft.Container(width=10), date_filter,
            ft.IconButton(ft.Icons.FILTER_LIST, tooltip="Aplicar filtros", icon_color="#6366f1", on_click=apply_filters),
            ft.IconButton(ft.Icons.REFRESH_ROUNDED, tooltip="Actualizar", icon_color="#6366f1", icon_size=22,
                          on_click=lambda e: self.navigate_to("history")),
        ], spacing=10)

        history_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=340)
        history_items = self.history.get_history()
        if not history_items:
            history_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.HISTORY, size=56, color="#64748b"),
                        ft.Text("Sin historial de descargas", size=16, color="#64748b"),
                        ft.Text("Los videos descargados aparecerán aquí automáticamente", size=12, color="#475569"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
                    alignment=ft.Alignment(0, 0), padding=50
                )
            )
        else:
            for item in history_items[:50]:
                history_list.controls.append(self._history_item_compact(item))

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=24, vertical=20),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY, size=28, color="#8b5cf6"),
                        ft.Container(width=12),
                        ft.Text("Historial de Descargas", size=24, weight=ft.FontWeight.BOLD),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=16),
                    stats_row,
                    ft.Container(height=12),
                    platform_stats,
                    ft.Container(height=16),
                    controls_row,
                    ft.Container(height=16),
                    ft.Container(
                        content=history_list, padding=14,
                        bgcolor="#1e293b" if is_dark else "#f1f5f9", border_radius=16,
                        border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black")),
                        clip_behavior="hardEdge",
                    )
                ], spacing=0, tight=True)
            )
        ]

    def _history_item_compact(self, item: Dict):
        is_dark = self.config.theme == "dark"
        name = item.get('name', 'Video desconocido')[:55]
        date = item.get('completed_at', 'Fecha desconocida')
        size_mb = item.get('size_bytes', 0) / (1024 * 1024)
        filepath = item.get('filepath', '')
        url = item.get('url', '')
        plat = item.get('platform', 'Otro')
        quality = item.get('quality', '1080')
        file_exists = filepath and os.path.exists(filepath)
        platform_colors = {
            'YouTube': '#ef4444', 'TikTok': '#000000', 'Instagram': '#e1306c',
            'Twitter': '#1da1f2', 'Facebook': '#1877f2', 'Vimeo': '#1ab7ea'
        }
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(plat[0], size=14, weight=ft.FontWeight.BOLD, color="white"),
                    width=36, height=36, bgcolor=platform_colors.get(plat, "#6366f1"),
                    border_radius=10, alignment=ft.Alignment(0, 0)
                ),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(name, size=13, weight=ft.FontWeight.W_500, no_wrap=True, expand=True),
                    ft.Row([
                        ft.Text(date, size=10, color="#64748b"),
                        ft.Text("•", size=10, color="#64748b"),
                        ft.Text(f"{size_mb:.1f} MB", size=10, color="#3b82f6"),
                        ft.Text("•", size=10, color="#64748b"),
                        ft.Text(plat, size=10, color="#8b5cf6"),
                    ], spacing=6)
                ], expand=True, spacing=4),
                ft.IconButton(icon=ft.Icons.PLAY_ARROW, icon_size=20,
                              icon_color="#10b981" if file_exists else "#64748b",
                              tooltip="Reproducir" if file_exists else "Archivo no disponible",
                              on_click=lambda e, fp=filepath: self._play_video(fp) if fp and os.path.exists(fp) else None,
                              disabled=not file_exists),
                ft.IconButton(icon=ft.Icons.FOLDER_OPEN, icon_size=20, icon_color="#6366f1",
                              tooltip="Abrir ubicación",
                              on_click=lambda e, fp=filepath: self._open_file_location_path(fp)),
                ft.IconButton(icon=ft.Icons.DOWNLOAD, icon_size=20, icon_color="#f59e0b",
                              tooltip="Volver a descargar",
                              on_click=lambda e, u=url, q=quality: self._redownload_from_history(u, q)) if url else ft.Container(),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=12, bgcolor="#334155" if is_dark else "#e2e8f0", border_radius=12,
            border=ft.Border.all(1, with_opacity(0.05, "white" if is_dark else "black")),
        )

    def _confirm_playlist_download(self, url: str, quality: str, audio_only: bool, audio_fmt):
        def do_fetch():
            try:
                import yt_dlp
                opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'skip_download': True, 'playlistend': 50}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                entries = info.get('entries', []) if info else []
                title = info.get('title', 'Playlist') if info else 'Playlist'
                return title, entries
            except Exception:
                return None, []

        def show_dialog(result):
            title, entries = result
            if not entries:
                self._show_snack("No se encontraron videos en la playlist", "red")
                return
            count = len(entries)
            dialog = ft.AlertDialog(
                modal=True, title=ft.Text(f"Playlist: {title[:40]}", size=16),
                content=ft.Column([
                    ft.Text(f"Se encontraron {count} videos.", size=13),
                    ft.Text("¿Descargar toda la playlist?", size=13),
                    ft.Container(height=6),
                    ft.Text(f"Calidad: {quality}p  •  {'Audio' if audio_only else 'Video'}", size=11, color="#64748b"),
                ], tight=True, spacing=4),
                shape=ft.RoundedRectangleBorder(radius=12),
            )

            def do_cancel(e):
                dialog.open = False
                self.page.update()

            def do_confirm(e):
                dialog.open = False
                self.page.update()
                queued = 0
                for entry in entries:
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if not video_url:
                        continue
                    if not video_url.startswith('http'):
                        video_url = f"https://www.youtube.com/watch?v={video_url}"
                    self.video_mgr.download(
                        video_url, self.config.video_path,
                        use_cookies=self.config.use_cookies, cookies_path=self.config.cookies_path,
                        quality=quality, audio_only=audio_only, audio_format=audio_fmt,
                    )
                    queued += 1
                self._show_snack(f"✅ {queued} videos agregados a la cola", "green")
                self.navigate_to("downloads")

            dialog.actions = [
                ft.TextButton("Cancelar", on_click=do_cancel),
                ft.Button(f"Descargar {count} videos", bgcolor="#6366f1", color="white", on_click=do_confirm),
            ]
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        self._show_snack("Analizando playlist...", "blue")

        async def _run():
            result = await asyncio.to_thread(do_fetch)
            show_dialog(result)

        self.page.run_task(_run)

    def _redownload_from_history(self, url: str, quality: str):
        if not url:
            self._show_snack("URL no disponible", "red")
            return
        self._show_snack("Agregando a la cola...", "blue")
        self.video_mgr.download(url, self.config.video_path,
                                use_cookies=self.config.use_cookies, cookies_path=self.config.cookies_path,
                                quality=quality)
        self.navigate_to("downloads")

    def _open_file_location_path(self, filepath: str):
        if filepath and os.path.exists(filepath):
            open_folder_externally(filepath)
        else:
            self._show_snack("Archivo no encontrado", "red")

    def _retry_all_failed(self):
        downloads = self.video_mgr.get_downloads()
        failed = [d for d in downloads if d.status == DownloadStatus.ERROR]
        if not failed:
            self._show_snack("No hay descargas fallidas", "blue")
            return
        count = 0
        for d in failed:
            new_id = self.video_mgr.download(d.url, self.config.video_path,
                                             use_cookies=self.config.use_cookies,
                                             cookies_path=self.config.cookies_path, quality=d.quality)
            if new_id:
                count += 1
        if count > 0:
            self._show_snack(f"Reintentando {count} descargas", "blue")
            self.navigate_to("downloads")

    def _handle_download_action(self, e, d: VideoDownload):
        if d.status == DownloadStatus.COMPLETED:
            if d.filepath and os.path.exists(d.filepath):
                self._play_video(d.filepath)
            else:
                self._show_snack("Archivo no encontrado", "red")
        else:
            if self.video_mgr.cancel_download(d.id):
                self._show_snack("Descarga cancelada", "orange")
                self.page.update()

    def _retry_download(self, d: VideoDownload):
        if d.url:
            self._show_snack("Reintentando descarga...", "blue")
            new_id = self.video_mgr.download(d.url, self.config.video_path,
                                             use_cookies=self.config.use_cookies,
                                             cookies_path=self.config.cookies_path, quality=d.quality)
            if new_id:
                self.video_mgr.cancel_download(d.id)
                self.navigate_to("downloads")
            else:
                self._show_snack("yt-dlp no instalado", "red")
        else:
            self._show_snack("URL no disponible", "red")

    def _play_video(self, video_path: str):
        if not video_path or not os.path.exists(video_path):
            self._show_snack("Archivo no encontrado", "red")
            return
        self._open_internal_player(video_path)

    def _open_internal_player(self, video_path: str):
        video_name = os.path.basename(video_path)
        try:
            vlc_exe = get_vlc_executable()
            if vlc_exe and os.path.exists(vlc_exe):
                subprocess.Popen([vlc_exe, video_path])
                self._show_snack(f"▶️ Reproduciendo: {video_name[:35]}...", "green")
            else:
                if open_file_externally(video_path):
                    self._show_snack(f"Abriendo: {video_name[:35]}...", "blue")
                else:
                    self._show_snack("No se pudo abrir el archivo", "red")
        except Exception as e:
            logger.error(f"Error abriendo VLC: {e}")
            if open_file_externally(video_path):
                self._show_snack(f"Abriendo: {video_name[:35]}...", "blue")
            else:
                self._show_snack(f"Error: {e}", "red")

    # ═══════════════════════════════════════════════════════════
    # CONFIGURACIÓN
    # ═══════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════
    # EXPLORAR — Top 3: búsqueda, canal completo y audio local
    # ═══════════════════════════════════════════════════════
    def _build_explorar_compact(self):
        is_dark = self.config.theme == "dark"
        bg_card = "#1e293b" if is_dark else "#f1f5f9"
        border = with_opacity(0.1, "white" if is_dark else "black")
        self._search_input = ft.TextField(
            hint_text="Buscar en YouTube (ej: lofi hip hop, tutorial python)...",
            expand=True, height=48, border_radius=10,
            prefix_icon=ft.Icons.SEARCH, text_size=14, content_padding=14,
            on_submit=lambda e: self._do_video_search(),
        )
        self._search_results = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=320)
        self._channel_input = ft.TextField(
            hint_text="URL del canal (ej: https://youtube.com/@canal)",
            expand=True, height=44, border_radius=10,
            prefix_icon=ft.Icons.SUBSCRIPTIONS, text_size=13, content_padding=14,
        )
        self._channel_limit = ft.Dropdown(
            label="Últimos", width=100, height=44, border_radius=10,
            text_size=12, content_padding=10, value="10",
            options=[ft.dropdown.Option(v) for v in ["5", "10", "25", "50", "100"]],
        )
        self._audio_format_dd = ft.Dropdown(
            label="Formato", width=110, height=44, border_radius=10,
            text_size=12, content_padding=10, value="mp3",
            options=[ft.dropdown.Option(v) for v in ["mp3", "m4a", "flac", "wav"]],
        )
        self._audio_status = ft.Text("", size=11, color="#64748b", expand=True)
        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=24, vertical=20),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.TRAVEL_EXPLORE, size=26, color="#6366f1"),
                        ft.Container(width=10),
                        ft.Text("Explorar", size=24, weight=ft.FontWeight.BOLD),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=16),
                    ft.Container(
                        padding=16, bgcolor=bg_card, border_radius=14,
                        border=ft.Border.all(1, border),
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.SEARCH, size=16, color="#6366f1"),
                                ft.Text("Buscar en YouTube", size=13, weight=ft.FontWeight.W_600, color="#6366f1"),
                            ], spacing=8),
                            ft.Container(height=10),
                            ft.Row([
                                self._search_input,
                                ft.Button("Buscar", icon=ft.Icons.SEARCH,
                                                  on_click=lambda e: self._do_video_search(),
                                                  bgcolor="#6366f1", color="white", height=48),
                            ], spacing=10),
                            ft.Container(height=12),
                            ft.Container(content=self._search_results, height=340),
                        ], spacing=0, tight=True),
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        padding=16, bgcolor=bg_card, border_radius=14,
                        border=ft.Border.all(1, border),
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.SUBSCRIPTIONS, size=16, color="#ef4444"),
                                ft.Text("Descargar canal completo", size=13, weight=ft.FontWeight.W_600, color="#ef4444"),
                            ], spacing=8),
                            ft.Container(height=10),
                            ft.Row([
                                self._channel_input,
                                self._channel_limit,
                                ft.Button("Descargar", icon=ft.Icons.DOWNLOAD,
                                                  on_click=lambda e: self._do_channel_download(),
                                                  bgcolor="#ef4444", color="white", height=44),
                            ], spacing=10),
                            ft.Container(height=6),
                            ft.Text("Añade a la cola los últimos N videos del canal.", size=11, color="#64748b"),
                        ], spacing=0, tight=True),
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        padding=16, bgcolor=bg_card, border_radius=14,
                        border=ft.Border.all(1, border),
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.AUDIO_FILE, size=16, color="#10b981"),
                                ft.Text("Extraer audio de un video local", size=13, weight=ft.FontWeight.W_600, color="#10b981"),
                            ], spacing=8),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Button("Elegir archivo…", icon=ft.Icons.FOLDER_OPEN,
                                                  on_click=lambda e: self._extract_local_audio(),
                                                  bgcolor="#10b981", color="white", height=40),
                                ft.Container(width=10),
                                self._audio_format_dd,
                                ft.Container(width=10),
                                self._audio_status,
                            ]),
                            ft.Container(height=6),
                            ft.Text("Convierte MP4/MKV/WebM/AVI a audio con FFmpeg.", size=11, color="#64748b"),
                        ], spacing=0, tight=True),
                    ),
                ], spacing=0, tight=True),
            )
        ]

    def _do_video_search(self):
        query = self._search_input.value.strip() if self._search_input else ""
        if not query:
            self._show_snack("⚠️ Escribe algo para buscar", "orange")
            return
        self._show_snack(f"🔎 Buscando '{query}'...", "blue")

        def do_search():
            results = []
            try:
                import yt_dlp
                opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True,
                        'playlistend': 12, 'skip_download': True}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(f"ytsearch12:{query}", download=False)
                for e_ in (info.get('entries') or [])[:12]:
                    vid = e_.get('id') or ''
                    url = e_.get('url') or (f"https://www.youtube.com/watch?v={vid}" if vid else '')
                    if not url:
                        continue
                    thumbs = e_.get('thumbnails') or []
                    results.append({
                        'title': e_.get('title') or 'Sin título',
                        'url': url,
                        'duration': e_.get('duration'),
                        'uploader': e_.get('uploader') or e_.get('channel') or '',
                        'thumb': thumbs[-1].get('url') if thumbs else '',
                    })
            except Exception as ex:
                logger.error(f"Error búsqueda: {ex}")

            async def update():
                if not self._session_alive:
                    return
                ctrl = getattr(self, '_search_results', None)
                if ctrl is None:
                    return
                ctrl.controls.clear()
                if not results:
                    ctrl.controls.append(ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=36, color="#64748b"),
                            ft.Text("Sin resultados", size=12, color="#94a3b8"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.Alignment(0, 0), padding=30))
                else:
                    for r in results:
                        ctrl.controls.append(self._search_result_card(r))
                self.page.update()
            self.page.run_task(update)

        threading.Thread(target=do_search, daemon=True).start()

    def _search_result_card(self, r):
        is_dark = self.config.theme == "dark"
        dur = r.get('duration')
        dur_txt = f"{int(dur)//60}:{int(dur)%60:02d}" if dur else ""
        if r.get('thumb'):
            thumb = ft.Image(src=r['thumb'], width=120, height=68, fit="cover", border_radius=8)
        else:
            thumb = ft.Container(
                content=None,
                width=120, height=68,
                bgcolor="#1e293b" if is_dark else "#e2e8f0",
                border_radius=8, alignment=ft.Alignment(0, 0))

        def dl(e):
            self._show_snack(f"⬇️ Descarga iniciada: {r['title'][:40]}...", "green")
            def work():
                try:
                    self.video_mgr.download(
                        r['url'], self.config.video_path,
                        use_cookies=self.config.use_cookies,
                        cookies_path=self.config.cookies_path,
                        quality=self.config.video_quality)
                    async def go():
                        self.navigate_to("downloads")
                    self.page.run_task(go)
                except Exception as ex:
                    async def err():
                        self._show_snack(f"❌ Error: {str(ex)[:60]}", "red")
                    self.page.run_task(err)
            threading.Thread(target=work, daemon=True).start()
        return ft.Container(
            padding=10, bgcolor="#334155" if is_dark else "#e2e8f0", border_radius=10,
            content=ft.Row([
                ft.Container(content=thumb, border_radius=8, clip_behavior="hardEdge"),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(r['title'][:70], size=13, weight=ft.FontWeight.W_500, max_lines=2, expand=True),
                    ft.Row([
                        ft.Text(r.get('uploader', '')[:30], size=10, color="#94a3b8"),
                        ft.Text(f"  •  {dur_txt}" if dur_txt else "", size=10, color="#64748b"),
                    ]),
                ], expand=True, spacing=4),
                ft.IconButton(icon=ft.Icons.DOWNLOAD, icon_color="#6366f1", icon_size=24,
                              tooltip="Descargar", on_click=dl),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def _do_channel_download(self):
        url = self._channel_input.value.strip() if self._channel_input else ""
        if not url or ('youtube.com' not in url.lower() and 'youtu.be' not in url.lower()):
            self._show_snack("⚠️ Pega una URL de canal de YouTube válida", "orange")
            return
        try:
            limit = int(self._channel_limit.value or 10)
        except Exception:
            limit = 10
        self._show_snack(f"📡 Analizando canal (últimos {limit})...", "blue")

        def do_fetch():
            entries = []
            try:
                import yt_dlp
                opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True,
                        'playlistend': limit, 'skip_download': True}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                for e_ in (info.get('entries') or [])[:limit]:
                    vid = e_.get('id') or ''
                    u = e_.get('url') or (f"https://www.youtube.com/watch?v={vid}" if vid else '')
                    if u:
                        entries.append(u)
            except Exception as ex:
                logger.error(f"Error canal: {ex}")

            async def after():
                if not self._session_alive:
                    return
                if not entries:
                    self._show_snack("❌ No se encontraron videos en el canal", "red")
                    return
                for u in entries:
                    self.video_mgr.download(
                        u, self.config.video_path,
                        use_cookies=self.config.use_cookies,
                        cookies_path=self.config.cookies_path,
                        quality=self.config.video_quality)
                self._show_snack(f"✅ {len(entries)} videos del canal añadidos a la cola", "green")
                self.navigate_to("downloads")
            self.page.run_task(after)

        threading.Thread(target=do_fetch, daemon=True).start()

    def _extract_local_audio(self):
        def run_dialog():
            try:
                root = tk.Tk()
                root.withdraw()
                root.wm_attributes('-topmost', True)
                root.update()
                path = filedialog.askopenfilename(
                    parent=root,
                    filetypes=[("Video", "*.mp4 *.mkv *.webm *.avi *.mov"), ("Todos", "*.*")])
                root.destroy()
            except Exception as ex:
                logger.error(f"Error selector audio: {ex}")
                return
            if not path:
                return

            def convert():
                try:
                    fmt = "mp3"
                    if hasattr(self, '_audio_format_dd') and self._audio_format_dd.value:
                        fmt = self._audio_format_dd.value
                    dst = os.path.splitext(path)[0] + f".{fmt}"
                    cmd = [get_ffmpeg_path(), '-y', '-i', path, '-vn']
                    if fmt == "mp3":
                        cmd += ['-acodec', 'libmp3lame', '-q:a', '0']
                    elif fmt == "m4a":
                        cmd += ['-acodec', 'aac', '-b:a', '320k']
                    elif fmt == "flac":
                        cmd += ['-acodec', 'flac']
                    else:
                        cmd += ['-acodec', 'pcm_s16le']
                    cmd += [dst]
                    r = subprocess.run(cmd, capture_output=True, timeout=600)
                    okc = r.returncode == 0 and os.path.exists(dst)
                    msg = f"✅ Audio guardado: {os.path.basename(dst)}" if okc else "❌ Error al extraer (¿FFmpeg instalado?)"
                    col = "green" if okc else "red"

                    async def show():
                        self._show_snack(msg, col)
                        if hasattr(self, '_audio_status'):
                            self._audio_status.value = msg
                            self._audio_status.color = col
                            self.page.update()
                    self.page.run_task(show)
                except Exception as ex:
                    self.page.run_task(lambda: self._show_snack(f"❌ {str(ex)[:60]}", "red"))

            self.page.run_task(lambda: self._show_snack(f"🎵 Extrayendo audio de {os.path.basename(path)[:30]}...", "blue"))
            threading.Thread(target=convert, daemon=True).start()

        threading.Thread(target=run_dialog, daemon=True).start()

    def _build_settings_compact(self):
        is_dark = self.config.theme == "dark"
        bg_container = "#1e293b" if is_dark else "#ffffff"

        theme_section = ft.Container(
            content=ft.Column([
                ft.Text("Apariencia", size=16, weight=ft.FontWeight.W_600, color="grey" if is_dark else "black"),
                ft.Container(height=10),
                ft.Row([
                    self._theme_option_compact("Claro", ft.Icons.LIGHT_MODE, "light", self.config.theme == "light"),
                    self._theme_option_compact("Oscuro", ft.Icons.DARK_MODE, "dark", self.config.theme == "dark"),
                    self._theme_option_compact("Auto", ft.Icons.AUTO_MODE, "auto", self.config.theme == "auto"),
                ], spacing=10)
            ], tight=True),
            padding=18, bgcolor=bg_container, border_radius=12,
            border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black"))
        )

        self.settings_connection_status = ft.Container(
            content=ft.Row([
                ft.Container(width=10, height=10, border_radius=5,
                             bgcolor="green" if self.qbit.connected else "red"),
                ft.Container(width=8),
                ft.Text("Conectado" if self.qbit.connected else "Desconectado", size=12,
                        color="green" if self.qbit.connected else "red"),
                ft.Container(expand=True),
                ft.Text(self.qbit.last_error[:40] if not self.qbit.connected else "", size=11, color="grey", italic=True)
            ]),
            padding=14,
            bgcolor=with_opacity(0.1, "green" if self.qbit.connected else "red"),
            border_radius=10,
            border=ft.Border.all(1, "green" if self.qbit.connected else "red")
        )

        qbt_host = ft.TextField(label="Host", value=self.config.qb_host, expand=True,
                                prefix_icon=ft.Icons.COMPUTER, text_size=13, content_padding=12,
                                height=44, border_radius=10)
        qbt_port = ft.TextField(label="Puerto", value=self.config.qb_port, width=120,
                                prefix_icon=ft.Icons.NUMBERS, text_size=13, content_padding=12,
                                height=44, border_radius=10)
        qbt_user = ft.TextField(label="Usuario", value=self.config.qb_user, expand=True,
                                prefix_icon=ft.Icons.PERSON, text_size=13, content_padding=12,
                                height=44, border_radius=10)
        qbt_pass = ft.TextField(label="Contraseña", value=self.config.qb_pass, password=True,
                                can_reveal_password=True, expand=True, prefix_icon=ft.Icons.LOCK,
                                text_size=13, content_padding=12, height=44, border_radius=10)

        def test_connection(e):
            self._show_snack("Probando conexión...", "blue")
            def do_test():
                success, msg = self.qbit.connect(qbt_host.value, qbt_port.value, qbt_user.value, qbt_pass.value)
                if not success and ("No se puede conectar" in msg or "Timeout" in msg):
                    qb_exe = get_qbittorrent_executable()
                    if qb_exe:
                        try:
                            subprocess.Popen([qb_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            self._show_snack("🚀 qBittorrent no estaba activo: iniciándolo...", "orange")
                            time.sleep(6)
                            success, msg = self.qbit.connect(qbt_host.value, qbt_port.value, qbt_user.value, qbt_pass.value)
                        except Exception as ex:
                            logger.error(f"Error al iniciar qBittorrent: {ex}")
                async def apply_ui():
                    try:
                        self.settings_connection_status.content.controls[0].bgcolor = "green" if success else "red"
                        self.settings_connection_status.content.controls[2].value = "Conectado" if success else "Desconectado"
                        self.settings_connection_status.content.controls[2].color = "green" if success else "red"
                        self.settings_connection_status.content.controls[4].value = msg[:40] if not success else ""
                        self.settings_connection_status.bgcolor = with_opacity(0.1, "green" if success else "red")
                        self.settings_connection_status.border = ft.Border.all(1, "green" if success else "red")
                    except Exception:
                        pass
                    self._show_snack(msg, "green" if success else "red")
                    self._update_status_ui()
                self.page.run_task(apply_ui)
            threading.Thread(target=do_test, daemon=True).start()

        qb_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("qBittorrent", size=16, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.Button("Probar Conexión", icon=ft.Icons.NETWORK_CHECK, on_click=test_connection,
                                      bgcolor="#6366f1", color="white", height=40)
                ]),
                ft.Container(height=10),
                self.settings_connection_status,
                ft.Container(height=10),
                ft.Row([qbt_host, qbt_port], spacing=10),
                ft.Container(height=10),
                ft.Row([qbt_user, qbt_pass], spacing=10),
            ], tight=True),
            padding=18, bgcolor=bg_container, border_radius=12,
            border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black"))
        )

        path_video = ft.TextField(label="Ruta Videos", value=self.config.video_path, expand=True,
                                  prefix_icon=ft.Icons.FOLDER, text_size=13, content_padding=12,
                                  height=44, border_radius=10)
        path_torrent = ft.TextField(label="Ruta Torrents", value=self.config.torrent_path, expand=True,
                                    prefix_icon=ft.Icons.FOLDER, text_size=13, content_padding=12,
                                    height=44, border_radius=10)

        def select_folder_flet(callback):
            def run_dialog():
                try:
                    result = subprocess.run(
                        ["zenity", "--file-selection", "--directory", "--title=Seleccionar carpeta"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        folder = result.stdout.strip()
                        if folder:
                            self.page.run_task(lambda: callback(folder) or self.page.update())
                    return
                except FileNotFoundError:
                    pass
                except Exception as ex:
                    logger.error(f"Error zenity: {ex}")
                    return
                try:
                    root = tk.Tk()
                    root.withdraw()
                    root.wm_attributes('-topmost', True)
                    root.update()
                    folder = filedialog.askdirectory(parent=root)
                    root.destroy()
                    if folder:
                        self.page.run_task(lambda: callback(folder) or self.page.update())
                except Exception as ex:
                    logger.error(f"Error tkinter: {ex}")

            threading.Thread(target=run_dialog, daemon=True).start()

        def pick_video_path(e):
            def update_path(folder):
                path_video.value = folder
                self._show_snack("Ruta videos actualizada", "green")
                self.page.update()

            select_folder_flet(update_path)

        def pick_torrent_path(e):
            def update_path(folder):
                path_torrent.value = folder
                self._show_snack("Ruta torrents actualizada", "green")
                self.page.update()

            select_folder_flet(update_path)

        paths_section = ft.Container(
            content=ft.Column([
                ft.Text("Rutas de Descarga", size=16, weight=ft.FontWeight.W_600),
                ft.Container(height=10),
                ft.Row([
                    path_video,
                    ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Seleccionar carpeta",
                                  on_click=pick_video_path, icon_size=20)
                ]),
                ft.Container(height=10),
                ft.Row([
                    path_torrent,
                    ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Seleccionar carpeta",
                                  on_click=pick_torrent_path, icon_size=20)
                ]),
            ], tight=True),
            padding=18, bgcolor=bg_container, border_radius=12,
            border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black"))
        )

        concurrent_slider = ft.Slider(min=1, max=5, divisions=4,
                                      value=self.config.max_concurrent_downloads,
                                      label="{value} descargas", on_change=lambda e: None)
        use_cookies = ft.Checkbox(label="Usar Cookies para videos restringidos",
                                  value=self.config.use_cookies, label_style=ft.TextStyle(size=13))
        notifications_enabled = ft.Checkbox(label="Mostrar notificaciones del sistema",
                                            value=self.config.notifications_enabled,
                                            label_style=ft.TextStyle(size=13))
        auto_start = ft.Checkbox(label="Iniciar descargas automáticamente",
                                 value=self.config.auto_start_downloads, label_style=ft.TextStyle(size=13))
        cookies_path = ft.TextField(label="Ruta cookies.txt", value=self.config.cookies_path, expand=True,
                                    hint_text="Archivo cookies exportado del navegador",
                                    text_size=13, content_padding=12, height=44, border_radius=10)
        auto_detect_cookies = ft.Checkbox(label="Detectar cookies del navegador automáticamente",
                                          value=self.config.auto_detect_cookies, label_style=ft.TextStyle(size=13))
        browser_dropdown = ft.Dropdown(
            label="Navegador",
            options=[
                ft.dropdown.Option("chrome", "Chrome / Chromium"),
                ft.dropdown.Option("firefox", "Firefox"),
                ft.dropdown.Option("brave", "Brave"),
                ft.dropdown.Option("edge", "Edge"),
                ft.dropdown.Option("opera", "Opera"),
            ],
            value=self.config.cookies_browser, width=180, height=44, border_radius=10,
            text_size=13, content_padding=10,
        )
        subs_enabled_cb = ft.Checkbox(label="📝 Descargar subtítulos", value=self.config.subtitles_enabled, label_style=ft.TextStyle(size=13))
        subs_lang_dd = ft.Dropdown(label="Idioma", options=[ft.dropdown.Option("es","Español"),ft.dropdown.Option("en","Inglés"),ft.dropdown.Option("pt","Portugués"),ft.dropdown.Option("fr","Francés"),ft.dropdown.Option("de","Alemán"),ft.dropdown.Option("it","Italiano"),ft.dropdown.Option("es,en","ES+EN"),ft.dropdown.Option("all","Todos")], value=self.config.subtitles_langs, width=140, height=44, border_radius=10, text_size=12, content_padding=10)
        subs_fmt_dd = ft.Dropdown(label="Formato", options=[ft.dropdown.Option("srt","SRT"),ft.dropdown.Option("vtt","VTT"),ft.dropdown.Option("ass","ASS")], value=self.config.subtitles_format, width=110, height=44, border_radius=10, text_size=12, content_padding=10)
        embed_subs_cb = ft.Checkbox(label="Incrustar en video (hardsub)", value=self.config.embed_subtitles, label_style=ft.TextStyle(size=11))
        auto_convert_cb = ft.Checkbox(label="🎬 Convertir MKV/WebM/AVI a MP4 automáticamente", value=self.config.auto_convert_to_mp4, label_style=ft.TextStyle(size=13))
        auto_update_ytdlp = ft.Checkbox(label="Actualizar yt-dlp automáticamente al iniciar",
                                        value=self.config.auto_update_ytdlp, label_style=ft.TextStyle(size=13))
        proxy_enabled = ft.Checkbox(label="Usar proxy para descargas",
                                    value=self.config.proxy_enabled, label_style=ft.TextStyle(size=13))
        proxy_url = ft.TextField(label="URL del proxy", value=self.config.proxy_url,
                                 hint_text="http://host:puerto", expand=True,
                                 text_size=13, content_padding=12, height=44, border_radius=10)
        proxy_user = ft.TextField(label="Usuario proxy", value=self.config.proxy_username, width=180,
                                  text_size=13, content_padding=12, height=44, border_radius=10)
        proxy_pass = ft.TextField(label="Contraseña proxy", value=self.config.proxy_password,
                                  password=True, can_reveal_password=True, width=180,
                                  text_size=13, content_padding=12, height=44, border_radius=10)

        def save(e):
            self.config.qb_host = qbt_host.value
            self.config.qb_port = qbt_port.value
            self.config.qb_user = qbt_user.value
            self.config.qb_pass = qbt_pass.value
            self.config.video_path = path_video.value
            self.config.torrent_path = path_torrent.value
            self.config.use_cookies = use_cookies.value
            self.config.cookies_path = cookies_path.value
            self.config.max_concurrent_downloads = int(concurrent_slider.value)
            self.config.notifications_enabled = notifications_enabled.value
            self.config.auto_start_downloads = auto_start.value
            self.config.auto_update_ytdlp = auto_update_ytdlp.value
            self.config.subtitles_enabled = subs_enabled_cb.value
            self.config.subtitles_langs = subs_lang_dd.value
            self.config.subtitles_format = subs_fmt_dd.value
            self.config.embed_subtitles = embed_subs_cb.value
            self.config.auto_convert_to_mp4 = auto_convert_cb.value
            self.config.auto_detect_cookies = auto_detect_cookies.value
            self.config.cookies_browser = browser_dropdown.value
            self.config.proxy_enabled = proxy_enabled.value
            self.config.proxy_url = proxy_url.value
            self.config.proxy_username = proxy_user.value
            self.config.proxy_password = proxy_pass.value
            self.video_mgr._config_ref = self.config
            self.video_mgr.set_max_concurrent(self.config.max_concurrent_downloads)
            notification_mgr.enabled = self.config.notifications_enabled
            self.save_config()
            self._show_snack("✅ Configuración guardada correctamente", "green")

        advanced_section = ft.Container(
            content=ft.Column([
                ft.Text("Configuración Avanzada", size=16, weight=ft.FontWeight.W_600),
                ft.Container(height=10),
                ft.Text("Descargas simultáneas máximas", size=12),
                concurrent_slider,
                ft.Container(height=10),
                use_cookies, ft.Container(height=6),
                notifications_enabled, ft.Container(height=6),
                auto_start, ft.Container(height=6),
                auto_update_ytdlp, ft.Container(height=10),
                ft.Row([subs_enabled_cb, ft.Container(width=8), embed_subs_cb], spacing=0),
                ft.Container(height=6),
                ft.Row([ft.Text("Idioma:", size=12), ft.Container(width=8), subs_lang_dd, ft.Container(width=8), ft.Text("Formato:", size=12), ft.Container(width=8), subs_fmt_dd], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                auto_convert_cb,
                cookies_path,
                ft.Text("Extensión 'Get cookies.txt' en Chrome para exportar", size=11, color="grey", italic=True),
                ft.Container(height=10),
                ft.Divider(height=1, color="#334155"),
                ft.Container(height=10),
                ft.Text("Cookies Automáticas", size=13, weight=ft.FontWeight.W_600),
                ft.Container(height=6),
                auto_detect_cookies, ft.Container(height=6),
                ft.Row([
                    ft.Text("Navegador:", size=12), ft.Container(width=10), browser_dropdown,
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Divider(height=1, color="#334155"),
                ft.Container(height=10),
                ft.Text("Proxy", size=13, weight=ft.FontWeight.W_600),
                ft.Container(height=6),
                proxy_enabled, ft.Container(height=8),
                proxy_url, ft.Container(height=6),
                ft.Row([proxy_user, ft.Container(width=8), proxy_pass], spacing=0),
            ], tight=True),
            padding=18, bgcolor=bg_container, border_radius=12,
            border=ft.Border.all(1, with_opacity(0.1, "white" if is_dark else "black"))
        )

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=24, vertical=20),
                content=ft.Column([
                    ft.Text("Configuración", size=26, weight=ft.FontWeight.BOLD),
                    ft.Container(height=16),
                    theme_section, ft.Container(height=14),
                    qb_section, ft.Container(height=14),
                    paths_section, ft.Container(height=14),
                    advanced_section, ft.Container(height=24),
                    ft.Button("💾 Guardar Configuración", icon=ft.Icons.SAVE, on_click=save,
                                      bgcolor="#6366f1", color="white", height=52, expand=True)
                ], spacing=0, tight=True)
            )
        ]

    def _theme_option_compact(self, label: str, icon, theme_value: str, is_selected: bool):
        bg_color = "#334155" if is_selected else "#1e293b" if self.config.theme == "dark" else "#f1f5f9"
        border_color = "#f59e0b" if theme_value == "light" and is_selected else "#6366f1" if theme_value == "dark" and is_selected else "transparent"
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=28, color="#f59e0b" if theme_value == "light" else "#6366f1"),
                ft.Text(label, size=12, weight=ft.FontWeight.W_500),
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=18) if is_selected else ft.Container(width=18, height=18)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=16, bgcolor=bg_color, border_radius=12,
            border=ft.Border.all(2, border_color), expand=True,
            on_click=lambda e: self._change_theme(theme_value), ink=True,
            animate=ft.Animation(200, "easeOut"),
        )

    def _change_theme(self, theme):
        self.config.theme = theme
        if theme == "auto":
            _h = datetime.now().hour
            _eff = "dark" if _h >= 20 or _h < 7 else "light"
        else:
            _eff = theme
        self.page.theme_mode = ft.ThemeMode.DARK if _eff == "dark" else ft.ThemeMode.LIGHT
        self.page.bgcolor = "#0f172a" if _eff == "dark" else "#f8fafc"
        self.save_config()
        self.page.controls.clear()
        self._build_layout()
        self.navigate_to(self._current_section)
        self.page.update()
        if theme == "auto":
            self._show_snack("🌓 Modo automático activado (oscuro 20:00-07:00)", "green")
        else:
            self._show_snack(f"Tema {'Oscuro' if theme == 'dark' else 'Claro'}", "green")

    # ═══════════════════════════════════════════════════════════
    # ACERCA DE
    # ═══════════════════════════════════════════════════════════
    def _build_about_compact(self):
        is_dark = self.config.theme == "dark"
        bg_card = "#1e293b" if is_dark else "#f1f5f9"
        border_col = with_opacity(0.1, "white" if is_dark else "black")
        deps = [
            ("yt-dlp", self.ytdlp_version if self.has_ytdlp else "No instalado", self.has_ytdlp),
            ("FFmpeg", "Instalado" if shutil.which('ffmpeg') or os.path.exists(get_ffmpeg_path()) else "No encontrado",
             shutil.which('ffmpeg') is not None or os.path.exists(get_ffmpeg_path())),
            ("VLC", "Instalado" if shutil.which('vlc') or os.path.exists(get_vlc_executable()) else "No encontrado",
             shutil.which('vlc') is not None or os.path.exists(get_vlc_executable())),
            ("qBittorrent", f"v{self.qbit.version}" if self.qbit.connected else "Desconectado", self.qbit.connected),
        ]
        deps_rows = []
        for name, version, ok in deps:
            deps_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE if ok else ft.Icons.WARNING,
                            color="#10b981" if ok else "#ef4444", size=18),
                    ft.Container(width=10),
                    ft.Text(name, size=13, weight=ft.FontWeight.W_500, expand=True),
                    ft.Text(version, size=12, color="#64748b"),
                ], spacing=0)
            )
            deps_rows.append(ft.Container(height=8))

        self.content_area.controls = [
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.BOLT, size=32, color="white"),
                            width=60, height=60, bgcolor="#6366f1", border_radius=16,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(width=14),
                        ft.Column([
                            ft.Text(APP_NAME, size=24, weight=ft.FontWeight.BOLD),
                            ft.Text(f"v{APP_VERSION} · Licencia {APP_LICENSE}", size=12, color="grey"),
                            ft.Text(f"{APP_AUTHOR} · © {APP_COMPANY} {APP_YEAR}", size=11, color="#64748b"),
                        ], spacing=2, tight=True),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=12),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                        bgcolor=bg_card, border_radius=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Estado del Sistema", size=12, weight=ft.FontWeight.W_600),
                                ft.Container(expand=True),
                                ft.TextButton("Ver logs", icon=ft.Icons.FOLDER,
                                              on_click=lambda e: open_file_externally(str(LOG_FILE)) if LOG_FILE.exists() else self._show_snack("No hay logs", "orange")),
                            ], spacing=0),
                            ft.Container(height=6),
                            *deps_rows,
                        ], spacing=0, tight=True)
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                        bgcolor=bg_card, border_radius=12,
                        border=ft.Border.all(1, border_col),
                        content=ft.Column([
                            ft.Row([
                                ft.Button("Ayuda  F1", icon=ft.Icons.HELP,
                                                  on_click=lambda e: self._show_help_dialog(),
                                                  bgcolor="#6366f1", color="white", height=34),
                                ft.Container(width=8),
                                ft.Button("GitHub", icon=ft.Icons.CODE,
                                                  on_click=lambda e: webbrowser.open(APP_GITHUB_URL),
                                                  bgcolor="#24292e", color="white", height=34),
                            ], spacing=0, wrap=True, run_spacing=6),
                            ft.Container(height=10),
                            ft.Row([
                                ft.Icon(ft.Icons.FAVORITE, color="#ef4444", size=13),
                                ft.Container(width=6),
                                ft.Text("¿Te gusta VideoFlex? ¡Apoyá el proyecto!",
                                        size=11, weight=ft.FontWeight.W_600, color="#94a3b8"),
                            ], spacing=0),
                            ft.Container(height=8),
                            ft.Row([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Text("💙", size=13), ft.Container(width=5),
                                        ft.Text("PayPal", size=12, weight=ft.FontWeight.W_600, color="white"),
                                    ], spacing=0, tight=True),
                                    bgcolor="#003087", border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=7),
                                    on_click=lambda e: webbrowser.open("https://www.paypal.com/donate/?business=KLV6YNFPEP4BA&no_recurring=0&item_name=Seguir+desarrollando+aplicaciones+de+Software+Libre.&currency_code=USD"),
                                    ink=True,
                                ),
                                ft.Container(width=8),
                                ft.Container(
                                    content=ft.Row([
                                        ft.Text("💚", size=13), ft.Container(width=5),
                                        ft.Text("Mercado Pago", size=12, weight=ft.FontWeight.W_600, color="white"),
                                    ], spacing=0, tight=True),
                                    bgcolor="#00b1ea", border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=14, vertical=7),
                                    on_click=lambda e: webbrowser.open("https://link.mercadopago.com.ar/pfecomputacion"),
                                    ink=True,
                                ),
                            ], spacing=0, wrap=True, run_spacing=6),
                        ], spacing=0, tight=True),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
            )
        ]

    # ═══════════════════════════════════════════════════════════
    # AYUDA
    # ═══════════════════════════════════════════════════════════
    def _show_help_section_compact(self):
        is_dark = self.config.theme == "dark"
        bg_card = "#1e293b" if is_dark else "#f1f5f9"
        bg_key = "#334155" if is_dark else "#e2e8f0"
        text_col = "white" if is_dark else "#1e293b"
        help_content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.HELP, size=32, color="#6366f1"),
                ft.Text("Centro de Ayuda", size=24, weight=ft.FontWeight.BOLD),
            ], spacing=12),
            ft.Container(height=16),
            ft.Container(
                padding=18, bgcolor=bg_card, border_radius=12,
                content=ft.Column([
                    ft.Text("📥 DESCARGA DE VIDEOS", size=15, weight=ft.FontWeight.W_600, color="#60a5fa"),
                    ft.Container(height=8),
                    ft.Text("• Soporta: YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo", size=12, color=text_col),
                    ft.Text("• Formatos: MP4 (video) o MP3 (audio solo)", size=12, color=text_col),
                    ft.Text("• Calidades: 720p, 1080p, 1440p, 4K, o mejor disponible", size=12, color=text_col),
                    ft.Text("• Las descargas se encolan automáticamente si hay muchas", size=12, color=text_col),
                ], spacing=4, tight=True)
            ),
            ft.Container(height=12),
            ft.Container(
                padding=18, bgcolor=bg_card, border_radius=12,
                content=ft.Column([
                    ft.Text("🧲 GESTIÓN DE TORRENTS", size=15, weight=ft.FontWeight.W_600, color="#f59e0b"),
                    ft.Container(height=8),
                    ft.Text("• Requiere qBittorrent con WebUI habilitada", size=12, color=text_col),
                    ft.Text("• Configura host, puerto y credenciales", size=12, color=text_col),
                    ft.Text("• Añade enlaces magnet directamente", size=12, color=text_col),
                    ft.Text("• Monitorea velocidad y progreso en tiempo real", size=12, color=text_col),
                ], spacing=4, tight=True)
            ),
            ft.Container(height=12),
            ft.Container(
                padding=18, bgcolor=bg_card, border_radius=12,
                content=ft.Column([
                    ft.Text("🔧 SOLUCIÓN DE PROBLEMAS", size=15, weight=ft.FontWeight.W_600, color="#ef4444"),
                    ft.Container(height=8),
                    ft.Text("❌ Error 'Sign in': Usa cookies del navegador", size=12, color=text_col),
                    ft.Text("❌ Error 'DRM': El video está protegido, no se puede descargar", size=12, color=text_col),
                    ft.Text("❌ 'FFmpeg not found': Instala FFmpeg y reinicia", size=12, color=text_col),
                    ft.Text("❌ qBittorrent no conecta: Verifica WebUI y credenciales", size=12, color=text_col),
                ], spacing=4, tight=True)
            ),
            ft.Container(height=12),
            ft.Container(
                padding=18, bgcolor=bg_card, border_radius=12,
                content=ft.Column([
                    ft.Text("⌨️ ATAJOS DE TECLADO", size=15, weight=ft.FontWeight.W_600, color="#10b981"),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Container(content=ft.Text("F1", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Ayuda rápida", size=12, expand=True, color=text_col),
                        ft.Container(content=ft.Text("Ctrl+N", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Nueva descarga", size=12, expand=True, color=text_col),
                    ]),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(content=ft.Text("Ctrl+D", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Dashboard", size=12, expand=True, color=text_col),
                        ft.Container(content=ft.Text("Ctrl+T", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Torrents", size=12, expand=True, color=text_col),
                    ]),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(content=ft.Text("Ctrl+V", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Videos", size=12, expand=True, color=text_col),
                        ft.Container(content=ft.Text("Ctrl+H", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Historial", size=12, expand=True, color=text_col),
                    ]),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(content=ft.Text("Ctrl+S", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Guardar config", size=12, expand=True, color=text_col),
                        ft.Container(content=ft.Text("Ctrl+Q", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Salir", size=12, expand=True, color=text_col),
                    ]),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(content=ft.Text("Delete", size=11, weight=ft.FontWeight.BOLD, color=text_col),
                                     bgcolor=bg_key, padding=6, border_radius=4),
                        ft.Text("Cancelar selección", size=12, expand=True, color=text_col),
                    ]),
                ], spacing=0, tight=True)
            ),
            ft.Container(height=20),
            ft.Row([
                ft.Button("Documentación yt-dlp", icon=ft.Icons.OPEN_IN_NEW,
                                  on_click=lambda e: webbrowser.open("https://github.com/yt-dlp/yt-dlp"),
                                  bgcolor="#475569", color="white", height=42),
                ft.Container(width=12),
                ft.Button("Ayuda Rápida", icon=ft.Icons.HELP_OUTLINE,
                                  on_click=self._show_help_dialog, bgcolor="#6366f1", color="white", height=42),
            ]),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

        self.content_area.controls = [
            ft.Container(padding=ft.Padding.symmetric(horizontal=24, vertical=20), content=help_content)
        ]

    def _show_help_dialog(self, e=None):
        help_text = ft.Column([
            ft.Text("🎯 AYUDA RÁPIDA", size=20, weight=ft.FontWeight.BOLD, color="#6366f1"),
            ft.Divider(height=12),
            ft.Text("📥 DESCARGAS DE VIDEO:", size=14, weight=ft.FontWeight.W_600),
            ft.Text("• YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo", size=12),
            ft.Text("• MP4 automático con la calidad seleccionada", size=12),
            ft.Text("• Las descargas se encolan si hay muchas simultáneas", size=12),
            ft.Divider(height=12),
            ft.Text("🧲 TORRENTS:", size=14, weight=ft.FontWeight.W_600),
            ft.Text("• qBittorrent debe estar ejecutándose con WebUI", size=12),
            ft.Text("• Configura en Ajustes → qBittorrent", size=12),
            ft.Divider(height=12),
            ft.Text("⚙️ CONFIGURACIÓN:", size=14, weight=ft.FontWeight.W_600),
            ft.Text("1. Instala FFmpeg para mejor compatibilidad", size=12),
            ft.Text("2. Exporta cookies si videos requieren login", size=12),
            ft.Text("3. Ajusta descargas simultáneas según tu conexión", size=12),
            ft.Divider(height=12),
            ft.Text("📋 ATAJOS:", size=14, weight=ft.FontWeight.W_600),
            ft.Text("• F1: Esta ayuda", size=12),
            ft.Text("• Esc: Cerrar ventanas", size=12),
            ft.Text("• Ctrl+N: Nueva descarga", size=12),
            ft.Text("• Ctrl+H: Historial", size=12),
            ft.Text("• Ctrl+S: Guardar configuración", size=12),
            ft.Text("• Ctrl+Q: Salir", size=12),
            ft.Text("• Delete: Cancelar descarga seleccionada", size=12),
        ], scroll=ft.ScrollMode.AUTO, height=400)

        def close_dialog(e=None):
            dialog.open = False
            self._help_dialog = None
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text("Ayuda de VideoFlex", size=18),
            content=ft.Container(content=help_text, padding=14),
            actions=[ft.TextButton("Cerrar", on_click=close_dialog)],
            shape=ft.RoundedRectangleBorder(radius=12),
            on_dismiss=close_dialog, open=True,
        )
        self._help_dialog = dialog
        self.page.overlay.append(dialog)
        self.page.update()

    async def _show_help_dialog_async(self):
        self._show_help_dialog()

    def _show_snack(self, message: str, color):
        try:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message, size=14), bgcolor=color,
                show_close_icon=True, close_icon_color="white",
                behavior=ft.SnackBarBehavior.FLOATING, duration=4000
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass

    def _show_error_dialog(self, title: str, message: str, details: str = ""):
        content_parts = [ft.Text(message, size=14)]
        if details:
            content_parts.extend([
                ft.Container(height=12),
                ft.Text("Detalles técnicos:", size=12, weight=ft.FontWeight.BOLD, color="grey"),
                ft.Container(
                    content=ft.Text(details, size=11, selectable=True),
                    padding=12, bgcolor="#1e293b", border_radius=8
                )
            ])

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text(title, color="red", size=16),
            content=ft.Column(content_parts, tight=True, spacing=0),
            actions=[ft.TextButton("Cerrar", on_click=close_dialog)],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_keyboard(self, e: ft.KeyboardEvent):
        key = e.key.upper() if e.key else ""
        if key == "ESCAPE" and self._help_dialog is not None:
            dlg = self._help_dialog
            self._help_dialog = None
            dlg.open = False
            self.page.update()
            return
        if key == "F1" and not e.ctrl and not e.shift and not e.alt:
            self.page.run_task(self._show_help_dialog_async)
            return
        elif e.ctrl and key == "N":
            self.navigate_to("videos")
            self.page.update()
        elif e.ctrl and key == "H":
            self.navigate_to("history")
            self.page.update()
        elif e.ctrl and key == "R":
            self.navigate_to(self._current_section)
            self._show_snack("Refrescado", "blue")
            self.page.update()
        elif e.ctrl and key == "S" and self._current_section == "settings":
            self._show_snack("Guardando...", "blue")
            self.save_config()
            self._show_snack("Configuración guardada", "green")
            self.page.update()
        elif e.ctrl and key == "Q":
            async def salir_async():
                await self._salir_aplicacion(None)
            self.page.run_task(salir_async)
        elif e.ctrl and key == "D":
            self.navigate_to("dashboard")
            self.page.update()
        elif e.ctrl and key == "T":
            self.navigate_to("torrents")
            self.page.update()
        elif e.ctrl and key == "V":
            self.navigate_to("videos")
            self.page.update()
        elif key == "DELETE" and self._selected_download_id:
            d = self.video_mgr.get_download(self._selected_download_id)
            if d:
                self._handle_download_action(None, d)
            self._selected_download_id = None


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════
def main(page: ft.Page):
    app = VideoFlexApp(page)


if __name__ == "__main__":
    ft.run(main)