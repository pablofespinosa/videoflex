# ⚡ VideoFlex

Gestor de descargas todo-en-uno: torrents (qBittorrent) + videos de YouTube/TikTok/Instagram (yt-dlp).

**Versión actual: 1.6.11** · Licencia GPL-3.0 · © PFE Computación 2025-2026

## ✨ Características

- 🎬 Descarga de videos hasta 4K con cola inteligente, pausa/reanudación y cancelación
- 🧲 Gestión completa de torrents con gráfico de velocidad en vivo
- 📜 Historial con búsqueda, filtros y exportación CSV
- 🎨 Temas claro/oscuro/automático + 5 colores de acento personalizables
- 🔔 Notificaciones del sistema y monitor de espacio en disco
- 🌊 Splash animado, transiciones suaves e iconos con pulso de actividad

## 🚀 Instalación (Windows)

1. Ejecutar `Install_dep_win.sh` desde Git Bash (instala Python, ffmpeg, yt-dlp y Node.js)
2. `python VideoFlex_Q.py`

## 🐧 Instalación (Linux)

Ejecutar `./install_videoflex.sh`

## 🔧 Requisitos

Python 3.10+, ffmpeg, yt-dlp y Node.js (para los desafíos JS de YouTube).

## 📦 Publicar una versión

`python release.py patch "mensaje"` → arreglos (1.6.7 → 1.6.8)
`python release.py minor "mensaje"` → features (1.6.7 → 1.7.0)
`python release.py major "mensaje"` → cambios grandes (→ 2.0.0)

Actualiza la versión en la app, README y LICENSE; hace commit, tag y push.
