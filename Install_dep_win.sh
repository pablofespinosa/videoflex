#!/bin/bash
#===============================================================================
#  VideoFlex — Instalador Completo Windows (Git Bash)
#  Versión: 2.0.0
#  Uso:     clic derecho → "Open Git Bash here" → ./install_deps_win.sh
#===============================================================================

set -e

# ─── Colores ──────────────────────────────────────────────────────────────────
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'
B='\033[0;34m'; P='\033[0;35m'; C='\033[0;36m'
W='\033[1;37m'; N='\033[0m'

ok()   { echo -e "  ${G}✔${N} $1"; }
info() { echo -e "  ${C}➤${N} $1"; }
warn() { echo -e "  ${Y}⚠${N} $1"; }
err()  { echo -e "  ${R}✘${N} $1"; }
head() { echo -e "\n${P}━━━ $1 ━━━${N}"; }

# ─── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${B}╔══════════════════════════════════════════════════════════╗${N}"
echo -e "${B}║${N}   ${W}⚡ VideoFlex — Instalador Windows v2.0${N}                 ${B}║${N}"
echo -e "${B}║${N}   ${C}Descargador Universal de Videos y Torrents${N}           ${B}║${N}"
echo -e "${B}║${N}   ${C}Ejecutando desde Git Bash${N}                             ${B}║${N}"
echo -e "${B}╚══════════════════════════════════════════════════════════╝${N}"

# ─── 1. Verificar entorno Git Bash / MSYS2 ────────────────────────────────────
head "1/10  Verificando entorno"

if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" && "$OS" != "Windows_NT" ]]; then
    err "Este script debe ejecutarse en Windows desde Git Bash."
    err "Clic derecho en la carpeta del proyecto → 'Open Git Bash here'"
    exit 1
fi
ok "Entorno Git Bash detectado (${OSTYPE:-MSYS})"

# ─── 2. Verificar versión de Windows ──────────────────────────────────────────
head "2/10  Verificando versión de Windows"

WIN_VER=$(powershell.exe -NoProfile -Command "[System.Environment]::OSVersion.Version.Major" 2>/dev/null | tr -d '\r')
WIN_BUILD=$(powershell.exe -NoProfile -Command "[System.Environment]::OSVersion.Version.Build" 2>/dev/null | tr -d '\r')

if [ "$WIN_VER" -ge 10 ] 2>/dev/null; then
    ok "Windows $WIN_VER (Build $WIN_BUILD) — compatible"
elif [ "$WIN_VER" -ge 6 ] 2>/dev/null; then
    warn "Windows $WIN_VER detectado. Se recomienda Windows 10 o superior."
else
    warn "No se pudo determinar la versión de Windows."
fi

# ─── 3. Detectar gestor de paquetes ──────────────────────────────────────────
head "3/10  Detectando gestor de paquetes"

PKG_MGR=""
PKG_INSTALL=""

if command -v winget &>/dev/null; then
    PKG_MGR="winget"
    PKG_INSTALL="winget install --accept-package-agreements --accept-source-agreements -e"
    ok "Gestor: ${W}winget${N}"
elif command -v choco &>/dev/null; then
    PKG_MGR="choco"
    PKG_INSTALL="choco install -y"
    ok "Gestor: ${W}Chocolatey${N}"
elif command -v scoop &>/dev/null; then
    PKG_MGR="scoop"
    PKG_INSTALL="scoop install"
    ok "Gestor: ${W}Scoop${N}"
else
    warn "No se encontró winget, choco ni scoop."
    warn "Las dependencias del sistema se verificarán manualmente."
    warn "Para instalar winget: Microsoft Store → 'App Installer'"
fi

install_pkg() {
    local winget_id="$1" choco_id="$2" scoop_id="$3" check_cmd="$4" label="$5"
    if command -v "$check_cmd" &>/dev/null; then
        ok "$label ya instalado"
        return 0
    fi
    case $PKG_MGR in
        winget)  info "Instalando $label…"; $PKG_INSTALL "$winget_id" 2>/dev/null && ok "$label instalado" || warn "No se pudo instalar $label automáticamente" ;;
        choco)   info "Instalando $label…"; $PKG_INSTALL "$choco_id" 2>/dev/null && ok "$label instalado" || warn "No se pudo instalar $label automáticamente" ;;
        scoop)   info "Instalando $label…"; $PKG_INSTALL "$scoop_id" 2>/dev/null && ok "$label instalado" || warn "No se pudo instalar $label automáticamente" ;;
        *)       warn "Instala manualmente: ${W}$label${N}" ;;
    esac
}

# ─── 4. Verificar / instalar Python ──────────────────────────────────────────
head "4/10  Verificando Python"

PYTHON_CMD=""

# Detectar Python de Microsoft Store (problemático)
MSSTORE_PYTHON=false
if command -v python &>/dev/null; then
    PY_PATH=$(command -v python 2>/dev/null)
    if [[ "$PY_PATH" == *"WindowsApps"* ]]; then
        MSSTORE_PYTHON=true
        warn "Se detectó Python de Microsoft Store (puede causar problemas)."
    fi
fi

for cmd in python python3 py; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | awk '{print $2}')
        if [[ "$ver" =~ ^3\.[8-9] ]] || [[ "$ver" =~ ^3\.1[0-9] ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    warn "Python 3.8+ no encontrado."
    install_pkg "Python.Python.3.12" "python3" "python" "python" "Python 3.12"
    for cmd in python python3 py; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON_CMD="$cmd"
            break
        fi
    done
fi

if [ -z "$PYTHON_CMD" ]; then
    err "Python no está instalado."
    err "Descárgalo de: ${W}https://www.python.org/downloads/${N}"
    err "${Y}IMPORTANTE: Marca 'Add Python to PATH' durante la instalación.${N}"
    exit 1
fi

ok "Python: ${W}$($PYTHON_CMD --version 2>&1)${N} → ${PYTHON_CMD}"

# Verificar pip
if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
    info "Instalando pip…"
    "$PYTHON_CMD" -m ensurepip --upgrade 2>/dev/null || {
        err "No se pudo instalar pip. Reinstala Python marcando 'pip'."
        exit 1
    }
fi
ok "pip: ${W}$($PYTHON_CMD -m pip --version 2>&1 | awk '{print $2}')${N}"

# Verificar venv
if ! "$PYTHON_CMD" -c "import venv" &>/dev/null; then
    err "El módulo venv no está disponible. Reinstala Python."
    exit 1
fi
ok "venv disponible"

# Verificar tkinter
if "$PYTHON_CMD" -c "import tkinter" &>/dev/null; then
    ok "tkinter disponible"
else
    warn "tkinter no disponible. Los diálogos de archivos usarán fallback."
fi

# Verificar winsound (solo Windows)
if "$PYTHON_CMD" -c "import winsound" &>/dev/null; then
    ok "winsound disponible (sonidos nativos)"
else
    warn "winsound no disponible (opcional)"
fi

# ─── 5. Verificar / instalar FFmpeg ──────────────────────────────────────────
head "5/10  Verificando FFmpeg"

FFMPEG_FOUND=false
FFMPEG_PATH=""

if command -v ffmpeg &>/dev/null; then
    FFMPEG_FOUND=true
    FFMPEG_PATH=$(command -v ffmpeg)
    ok "FFmpeg: ${W}$(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')${N}"
elif [ -f "/c/ffmpeg/bin/ffmpeg.exe" ]; then
    FFMPEG_FOUND=true
    FFMPEG_PATH="/c/ffmpeg/bin/ffmpeg.exe"
    ok "FFmpeg encontrado en C:\\ffmpeg"
    # Agregar al PATH de la sesión actual
    export PATH="/c/ffmpeg/bin:$PATH"
elif [ -f "$HOME/scoop/apps/ffmpeg/current/bin/ffmpeg.exe" ]; then
    FFMPEG_FOUND=true
    FFMPEG_PATH="$HOME/scoop/apps/ffmpeg/current/bin/ffmpeg.exe"
    ok "FFmpeg encontrado en Scoop"
else
    install_pkg "Gyan.FFmpeg" "ffmpeg" "ffmpeg" "ffmpeg" "FFmpeg"
    if command -v ffmpeg &>/dev/null; then
        FFMPEG_FOUND=true
        FFMPEG_PATH=$(command -v ffmpeg)
        ok "FFmpeg instalado correctamente"
    else
        warn "FFmpeg no se pudo instalar automáticamente."
        warn "Descárgalo de: ${W}https://ffmpeg.org/download.html${N}"
        warn "Descomprime en ${W}C:\\ffmpeg${N} y añade ${W}C:\\ffmpeg\\bin${N} al PATH."
        warn "O ejecuta: ${C}winget install Gyan.FFmpeg${N}"
    fi
fi

if [ "$FFMPEG_FOUND" = false ]; then
    warn "Sin FFmpeg: no se podrán generar thumbnails ni convertir formatos."
fi

# ─── 6. Verificar / instalar VLC ─────────────────────────────────────────────
head "6/10  Verificando VLC"

VLC_FOUND=false
VLC_PATHS=(
    "/c/Program Files/VideoLAN/VLC/vlc.exe"
    "/c/Program Files (x86)/VideoLAN/VLC/vlc.exe"
    "$PROGRAMFILES/VideoLAN/VLC/vlc.exe"
    "$HOME/AppData/Local/Programs/VLC/vlc.exe"
    "$LOCALAPPDATA/Programs/VLC/vlc.exe"
)

for p in "${VLC_PATHS[@]}"; do
    if [ -f "$p" ]; then
        VLC_FOUND=true
        ok "VLC encontrado en: ${W}${p}${N}"
        break
    fi
done

if [ "$VLC_FOUND" = false ]; then
    install_pkg "VideoLAN.VLC" "vlc" "vlc" "vlc" "VLC"
    for p in "${VLC_PATHS[@]}"; do
        if [ -f "$p" ]; then
            VLC_FOUND=true
            ok "VLC instalado correctamente"
            break
        fi
    done
    if [ "$VLC_FOUND" = false ]; then
        warn "VLC no se pudo instalar automáticamente."
        warn "Descárgalo de: ${W}https://www.videolan.org/${N}"
        warn "O ejecuta: ${C}winget install VideoLAN.VLC${N}"
    fi
fi

# ─── 7. Verificar / instalar qBittorrent ──────────────────────────────────────
head "7/10  Verificando qBittorrent"

QB_FOUND=false
QB_PATHS=(
    "/c/Program Files/qBittorrent/qbittorrent.exe"
    "/c/Program Files (x86)/qBittorrent/qbittorrent.exe"
    "$PROGRAMFILES/qBittorrent/qbittorrent.exe"
    "$LOCALAPPDATA/qBittorrent/qbittorrent.exe"
)

for p in "${QB_PATHS[@]}"; do
    if [ -f "$p" ]; then
        QB_FOUND=true
        ok "qBittorrent encontrado en: ${W}${p}${N}"
        break
    fi
done

if [ "$QB_FOUND" = false ]; then
    install_pkg "qBittorrent.qBittorrent" "qbittorrent" "qbittorrent" "qbittorrent" "qBittorrent"
    for p in "${QB_PATHS[@]}"; do
        if [ -f "$p" ]; then
            QB_FOUND=true
            ok "qBittorrent instalado correctamente"
            break
        fi
    done
    if [ "$QB_FOUND" = false ]; then
        warn "qBittorrent no se pudo instalar automáticamente."
        warn "Descárgalo de: ${W}https://www.qbittorrent.org/${N}"
        warn "O ejecuta: ${C}winget install qBittorrent.qBittorrent${N}"
    fi
fi

# ─── 8. Crear entorno virtual + instalar librerías Python ─────────────────────
head "8/10  Entorno virtual y librerías de Python"

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${INSTALL_DIR}/.venv"

if [ -d "$VENV_DIR" ]; then
    warn "Ya existe un entorno virtual en ${VENV_DIR}"
    read -rp "  ¿Recrear? [s/N] " REPLY
    if [[ "$REPLY" =~ ^[Ss]$ ]]; then
        rm -rf "$VENV_DIR"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
        ok "Entorno virtual recreado"
    else
        ok "Usando entorno virtual existente"
    fi
else
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    ok "Entorno virtual creado en ${VENV_DIR}"
fi

source "${VENV_DIR}/Scripts/activate"

# Actualizar pip
pip install --upgrade pip setuptools wheel -q
ok "pip actualizado a $(pip --version | awk '{print $2}')"

# Generar requirements.txt
cat > "${INSTALL_DIR}/requirements.txt" << 'REQS'
flet>=0.21.0
yt-dlp>=2024.1.1
requests>=2.28.0
pyperclip>=1.8.2
psutil>=5.9.0
win10toast>=0.9; sys_platform == "win32"
REQS
ok "requirements.txt generado"

# Instalar dependencias
info "Instalando flet (interfaz gráfica)…"
pip install "flet>=0.21.0" -q
ok "flet $(pip show flet 2>/dev/null | grep Version | awk '{print $2}')"

info "Instalando yt-dlp (motor de descarga)…"
pip install "yt-dlp" -q
ok "yt-dlp $(pip show yt-dlp 2>/dev/null | grep Version | awk '{print $2}')"

info "Instalando requests (HTTP)…"
pip install "requests>=2.28.0" -q
ok "requests $(pip show requests 2>/dev/null | grep Version | awk '{print $2}')"

info "Instalando pyperclip (portapapeles)…"
pip install "pyperclip>=1.8.2" -q
ok "pyperclip $(pip show pyperclip 2>/dev/null | grep Version | awk '{print $2}')"

info "Instalando psutil (monitor de sistema)…"
pip install "psutil>=5.9.0" -q
ok "psutil $(pip show psutil 2>/dev/null | grep Version | awk '{print $2}')"

info "Instalando win10toast (notificaciones Windows)…"
pip install "win10toast" -q 2>/dev/null
if pip show win10toast &>/dev/null; then
    ok "win10toast $(pip show win10toast 2>/dev/null | grep Version | awk '{print $2}')"
else
    warn "win10toast no se instaló (opcional, se usará winsound)"
fi

# ─── 9. Crear directorios, lanzadores y acceso directo ────────────────────────
head "9/10  Creando directorios y lanzadores"

# Crear carpetas de descarga
DOWNLOADS_BASE="$HOME/Downloads/VideoFlex"
mkdir -p "${DOWNLOADS_BASE}/Videos"
mkdir -p "${DOWNLOADS_BASE}/Torrents"
ok "Carpetas de descarga creadas en ${DOWNLOADS_BASE}"

# Lanzador .bat (doble clic en Windows)
cat > "${INSTALL_DIR}/VideoFlex.bat" << 'BATCH'
@echo off
title VideoFlex - Descargador de Videos y Torrents
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Entorno virtual no encontrado. Ejecuta install_deps_win.sh primero.
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
python VideoFlex.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] VideoFlex terminó con un error.
    pause
)
BATCH
ok "Lanzador creado: VideoFlex.bat"

# Lanzador .sh (Git Bash)
cat > "${INSTALL_DIR}/videoflex" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "${DIR}/.venv/Scripts/activate" ]; then
    echo "[ERROR] Entorno virtual no encontrado. Ejecuta install_deps_win.sh primero."
    exit 1
fi
source "${DIR}/.venv/Scripts/activate"
cd "${DIR}"
exec python VideoFlex.py "$@"
LAUNCHER
chmod +x "${INSTALL_DIR}/videoflex"
ok "Lanzador Git Bash: ./videoflex"

# Script de desinstalación
cat > "${INSTALL_DIR}/uninstall_videoflex.bat" << 'UNINSTALL'
@echo off
echo Desinstalando VideoFlex...
echo.
set /p CONFIRM="Eliminar entorno virtual y configuracion? [S/N]: "
if /i "%CONFIRM%"=="S" (
    rmdir /s /q "%~dp0.venv" 2>nul
    del "%USERPROFILE%\.videoflex_config.json" 2>nul
    del "%USERPROFILE%\.videoflex_history.json" 2>nul
    del "%USERPROFILE%\.videoflex_clipboard.json" 2>nul
    del "%USERPROFILE%\.videoflex_cookies.txt" 2>nul
    del "%USERPROFILE%\.videoflex_errors.log" 2>nul
    del "%USERPROFILE%\.videoflex_app.log" 2>nul
    echo Datos eliminados.
) else (
    echo Solo se eliminara el entorno virtual.
    rmdir /s /q "%~dp0.venv" 2>nul
)
echo VideoFlex desinstalado.
pause
UNINSTALL
ok "Desinstalador creado: uninstall_videoflex.bat"

# Acceso directo en el escritorio
DESKTOP_DIR=$(cygpath -u "$USERPROFILE/Desktop" 2>/dev/null || echo "$HOME/Desktop")
if [ -d "$DESKTOP_DIR" ]; then
    BAT_PATH=$(cygpath -w "${INSTALL_DIR}/VideoFlex.bat")
    WORK_DIR=$(cygpath -w "${INSTALL_DIR}")
    powershell.exe -NoProfile -Command "
        \$ws = New-Object -ComObject WScript.Shell
        \$sc = \$ws.CreateShortcut('${DESKTOP_DIR}\\VideoFlex.lnk')
        \$sc.TargetPath = '${BAT_PATH}'
        \$sc.WorkingDirectory = '${WORK_DIR}'
        \$sc.Description = 'VideoFlex - Descargador de Videos y Torrents'
        \$sc.IconLocation = 'shell32.dll,137'
        \$sc.Save()
    " 2>/dev/null && ok "Acceso directo creado en el escritorio" || warn "No se pudo crear el acceso directo"
else
    warn "No se encontró el escritorio"
fi

# ─── 10. Verificación final ──────────────────────────────────────────────────
head "10/10  Verificación final"

PASS=0; FAIL=0

check() {
    local label="$1"; shift
    if "$@" &>/dev/null; then
        ok "$label"
        ((PASS++))
    else
        err "$label"
        ((FAIL++))
    fi
}

check "Python 3"          "$PYTHON_CMD" --version
check "pip"               pip --version
check "flet"              python -c "import flet"
check "yt-dlp"            python -c "import yt_dlp"
check "requests"          python -c "import requests"
check "pyperclip"         python -c "import pyperclip"
check "psutil"            python -c "import psutil"
check "tkinter"           python -c "import tkinter"
check "winsound"          python -c "import winsound"
check "win10toast"        python -c "import win10toast"
check "FFmpeg"            command -v ffmpeg
check "VLC"               test -f "/c/Program Files/VideoLAN/VLC/vlc.exe"
check "qBittorrent"       test -f "/c/Program Files/qBittorrent/qbittorrent.exe"
check "Carpeta Videos"    test -d "${DOWNLOADS_BASE}/Videos"
check "Carpeta Torrents"  test -d "${DOWNLOADS_BASE}/Torrents"
check "Lanzador .bat"     test -f "${INSTALL_DIR}/VideoFlex.bat"
check "Lanzador .sh"      test -f "${INSTALL_DIR}/videoflex"

# ─── Resumen ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${B}╔══════════════════════════════════════════════════════════╗${N}"
if [ $FAIL -eq 0 ]; then
echo -e "${B}║${N}   ${G}✅  Todo instalado correctamente  (${PASS}/${PASS})${N}               ${B}║${N}"
else
echo -e "${B}║${N}   ${Y}⚠️  ${PASS} correctas / ${FAIL} fallidas${N}                        ${B}║${N}"
fi
echo -e "${B}╠══════════════════════════════════════════════════════════╣${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}   ${W}Para ejecutar VideoFlex:${N}                              ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}   Opción 1:  Doble clic en ${C}VideoFlex.bat${N}               ${B}║${N}"
echo -e "${B}║${N}   Opción 2:  Acceso directo en el escritorio             ${B}║${N}"
echo -e "${B}║${N}   Opción 3:  Desde Git Bash:                             ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}     ${C}./videoflex${N}                                         ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}   Opción 4:  Manual:                                     ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}     ${C}source .venv/Scripts/activate${N}                       ${B}║${N}"
echo -e "${B}║${N}     ${C}python VideoFlex.py${N}                                 ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}╠══════════════════════════════════════════════════════════╣${N}"
echo -e "${B}║${N}   ${W}Archivos creados:${N}                                     ${B}║${N}"
echo -e "${B}║${N}     • VideoFlex.bat        → Lanzador Windows            ${B}║${N}"
echo -e "${B}║${N}     • videoflex            → Lanzador Git Bash           ${B}║${N}"
echo -e "${B}║${N}     • requirements.txt     → Dependencias Python         ${B}║${N}"
echo -e "${B}║${N}     • uninstall_videoflex.bat → Desinstalador            ${B}║${N}"
echo -e "${B}║${N}     • .venv/               → Entorno virtual             ${B}║${N}"
echo -e "${B}║${N}     • ~/Downloads/VideoFlex/ → Descargas                 ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}╠══════════════════════════════════════════════════════════╣${N}"
echo -e "${B}║${N}   ${Y}Nota sobre qBittorrent:${N}                               ${B}║${N}"
echo -e "${B}║${N}   Para usar torrents, habilita la WebUI:                ${B}║${N}"
echo -e "${B}║${N}   qBittorrent → Herramientas → Opciones → Web UI        ${B}║${N}"
echo -e "${B}║${N}   Puerto: 8080 | Usuario: admin | Pass: adminadmin      ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}   ${Y}Nota sobre FFmpeg:${N}                                    ${B}║${N}"
echo -e "${B}║${N}   Si FFmpeg no está en el PATH, descárgalo de:          ${B}║${N}"
echo -e "${B}║${N}   https://ffmpeg.org/download.html                      ${B}║${N}"
echo -e "${B}║${N}   Descomprime en C:\\ffmpeg y añade al PATH:             ${B}║${N}"
echo -e "${B}║${N}   C:\\ffmpeg\\bin                                         ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}╚══════════════════════════════════════════════════════════╝${N}"
echo ""

exit $FAIL