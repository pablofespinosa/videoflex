#!/bin/bash
#===============================================================================
#  VideoFlex — Instalador de Dependencias
#  Soporta: Debian, Ubuntu, Linux Mint, Pop!_OS, Arch, Manjaro, EndeavourOS
#  Uso:     chmod +x install_deps.sh && ./install_deps.sh
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
echo -e "${B}║${N}   ${W}⚡ VideoFlex — Instalador de Dependencias${N}              ${B}║${N}"
echo -e "${B}║${N}   ${C}Descargador Universal de Videos y Torrents${N}           ${B}║${N}"
echo -e "${B}╚══════════════════════════════════════════════════════════╝${N}"

# ─── Detección de distribución ────────────────────────────────────────────────
head "Detectando sistema"

if [ ! -f /etc/os-release ]; then
    err "No se pudo detectar la distribución."
    exit 1
fi

. /etc/os-release
DISTRO_ID="$ID"
DISTRO_LIKE="${ID_LIKE:-}"

info "Distribución: ${W}${PRETTY_NAME:-$DISTRO_ID}${N}"

PKG=""
if [[ "$DISTRO_ID" =~ ^(debian|ubuntu|linuxmint|pop|elementary|zorin|kali|raspbian)$ ]] || [[ "$DISTRO_LIKE" == *"debian"* ]]; then
    PKG="apt"
elif [[ "$DISTRO_ID" =~ ^(arch|manjaro|endeavouros|garuda|arcolinux)$ ]] || [[ "$DISTRO_LIKE" == *"arch"* ]]; then
    PKG="pacman"
else
    warn "Distribución no reconocida ($DISTRO_ID). Intentando con apt…"
    PKG="apt"
fi

info "Gestor de paquetes: ${W}${PKG}${N}"

# ─── Verificar root / sudo ────────────────────────────────────────────────────
SUDO=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo &>/dev/null; then
        SUDO="sudo"
    else
        err "Necesitas ejecutar como root o tener sudo instalado."
        exit 1
    fi
fi

# ─── Actualizar repositorios ─────────────────────────────────────────────────
head "Actualizando repositorios"

case $PKG in
    apt)
        $SUDO apt-get update -qq
        ok "Repositorios actualizados"
        ;;
    pacman)
        $SUDO pacman -Sy --noconfirm
        ok "Repositorios actualizados"
        ;;
esac

# ─── Dependencias del sistema ────────────────────────────────────────────────
head "Instalando dependencias del sistema"

case $PKG in
    apt)
        $SUDO apt-get install -y -qq \
            python3 python3-pip python3-venv python3-dev python3-tk \
            build-essential gcc g++ make \
            libffi-dev libssl-dev zlib1g-dev libbz2-dev \
            libreadline-dev libsqlite3-dev libncursesw5-dev \
            xclip xsel \
            zenity \
            ffmpeg \
            vlc \
            qbittorrent \
            libnotify-bin \
            curl wget git \
            2>/dev/null || true
        ;;
    pacman)
        $SUDO pacman -S --noconfirm --needed \
            python python-pip tk \
            base-devel \
            libffi openssl zlib bzip2 readline sqlite ncurses \
            xclip xsel \
            zenity \
            ffmpeg \
            vlc \
            qbittorrent \
            libnotify \
            curl wget git \
            2>/dev/null || true
        ;;
esac

ok "Dependencias del sistema instaladas"

# ─── Entorno virtual ─────────────────────────────────────────────────────────
head "Creando entorno virtual de Python"

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${INSTALL_DIR}/.venv"

if [ -d "$VENV_DIR" ]; then
    warn "Ya existe un entorno virtual en ${VENV_DIR}"
    read -rp "  ¿Recrear? [s/N] " REPLY
    if [[ "$REPLY" =~ ^[Ss]$ ]]; then
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        ok "Entorno virtual recreado"
    else
        ok "Usando entorno virtual existente"
    fi
else
    python3 -m venv "$VENV_DIR"
    ok "Entorno virtual creado en ${VENV_DIR}"
fi

# Activar
source "${VENV_DIR}/bin/activate"

# ─── Actualizar pip ──────────────────────────────────────────────────────────
head "Actualizando pip, setuptools y wheel"

pip install --upgrade pip setuptools wheel -q
ok "pip $(pip --version | awk '{print $2}')"

# ─── Dependencias de Python ──────────────────────────────────────────────────
head "Instalando librerías de Python"

info "flet (interfaz gráfica)…"
pip install "flet>=0.21.0" -q
ok "flet $(pip show flet 2>/dev/null | grep Version | awk '{print $2}')"

info "yt-dlp (descarga de videos)…"
pip install "yt-dlp" -q
ok "yt-dlp $(pip show yt-dlp 2>/dev/null | grep Version | awk '{print $2}')"

info "requests (HTTP)…"
pip install "requests>=2.28.0" -q
ok "requests $(pip show requests 2>/dev/null | grep Version | awk '{print $2}')"

info "pyperclip (portapapeles)…"
pip install "pyperclip>=1.8.2" -q
ok "pyperclip $(pip show pyperclip 2>/dev/null | grep Version | awk '{print $2}')"

info "psutil (monitor de sistema)…"
pip install "psutil>=5.9.0" -q
ok "psutil $(pip show psutil 2>/dev/null | grep Version | awk '{print $2}')"

# ─── Crear script de arranque ────────────────────────────────────────────────
head "Creando lanzador"

cat > "${INSTALL_DIR}/videoflex" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
source "${DIR}/.venv/bin/activate"
cd "${DIR}"
exec python3 VideoFlex.py "$@"
LAUNCHER
chmod +x "${INSTALL_DIR}/videoflex"
ok "Lanzador creado: ${INSTALL_DIR}/videoflex"

# ─── Verificación final ──────────────────────────────────────────────────────
head "Verificación final"

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

check "Python 3"          python3 --version
check "pip"               pip --version
check "flet"              python3 -c "import flet"
check "yt-dlp"            python3 -c "import yt_dlp"
check "requests"          python3 -c "import requests"
check "pyperclip"         python3 -c "import pyperclip"
check "psutil"            python3 -c "import psutil"
check "tkinter"           python3 -c "import tkinter"
check "FFmpeg"            command -v ffmpeg
check "VLC"               command -v vlc
check "qBittorrent"       command -v qbittorrent
check "xclip"             command -v xclip
check "zenity"            command -v zenity
check "notify-send"       command -v notify-send

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
echo -e "${B}║${N}     ${C}./videoflex${N}                                         ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}   ${W}O manualmente:${N}                                        ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}║${N}     ${C}source .venv/bin/activate${N}                           ${B}║${N}"
echo -e "${B}║${N}     ${C}python3 VideoFlex.py${N}                                ${B}║${N}"
echo -e "${B}║${N}                                                          ${B}║${N}"
echo -e "${B}╚══════════════════════════════════════════════════════════╝${N}"
echo ""

exit $FAIL