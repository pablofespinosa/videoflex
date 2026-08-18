#!/bin/bash
#===============================================================================
# VideoFlex Installer - Linux (Debian/Ubuntu/Arch)
# Versión: 1.0.0
# Autor: PFE Computación
#===============================================================================

set -e

# ─── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Funciones de utilidad ────────────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${BLUE}⚡ VideoFlex Installer${NC}                                      ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  Descargador Universal de Videos y Torrents                  ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}[➤]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

# ─── Detección de distribución ────────────────────────────────────────────────
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID=$ID
        DISTRO_NAME=$NAME
        DISTRO_LIKE=$ID_LIKE
    else
        print_error "No se pudo detectar la distribución"
        exit 1
    fi
    
    print_info "Distribución detectada: ${DISTRO_NAME}"
    
    # Determinar familia
    if [[ "$DISTRO_ID" == "ubuntu" || "$DISTRO_ID" == "debian" || \
          "$DISTRO_ID" == "linuxmint" || "$DISTRO_ID" == "pop" || \
          "$DISTRO_ID" == "elementary" || "$DISTRO_ID" == "zorin" || \
          "$DISTRO_LIKE" == *"debian"* ]]; then
        PKG_MANAGER="apt"
        PKG_FAMILY="debian"
    elif [[ "$DISTRO_ID" == "arch" || "$DISTRO_ID" == "manjaro" || \
            "$DISTRO_ID" == "endeavouros" || "$DISTRO_ID" == "garuda" || \
            "$DISTRO_LIKE" == *"arch"* ]]; then
        PKG_MANAGER="pacman"
        PKG_FAMILY="arch"
    else
        print_warning "Distribución no reconocida: $DISTRO_ID"
        print_info "Intentando con apt..."
        PKG_MANAGER="apt"
        PKG_FAMILY="debian"
    fi
    
    print_info "Familia: ${PKG_FAMILY} | Gestor: ${PKG_MANAGER}"
}

# ─── Verificar privilegios root ───────────────────────────────────────────────
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_warning "Este script necesita privilegios de root para instalar dependencias"
        read -p "¿Deseas continuar con sudo? [S/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            exec sudo "$0" "$@"
        else
            print_error "Se requieren privilegios de root"
            exit 1
        fi
    fi
}

# ─── Actualizar sistema ───────────────────────────────────────────────────────
update_system() {
    print_step "Actualizando lista de paquetes..."
    
    case $PKG_MANAGER in
        "apt")
            apt-get update -qq
            ;;
        "pacman")
            pacman -Sy --noconfirm
            ;;
    esac
    
    print_success "Sistema actualizado"
}

# ─── Instalar dependencias del sistema ────────────────────────────────────────
install_system_deps() {
    print_step "Instalando dependencias del sistema..."
    
    case $PKG_FAMILY in
        "debian")
            apt-get install -y -qq \
                python3 python3-pip python3-venv python3-dev \
                ffmpeg vlc qbittorrent \
                build-essential libffi-dev libssl-dev \
                xclip xsel zenity \
                curl wget git \
                2>/dev/null || {
                    print_warning "Algunos paquetes no se encontraron, continuando..."
                }
            ;;
        "arch")
            pacman -S --noconfirm --needed \
                python python-pip \
                ffmpeg vlc qbittorrent \
                base-devel libffi openssl \
                xclip xsel zenity \
                curl wget git \
                2>/dev/null || {
                    print_warning "Algunos paquetes no se encontraron, continuando..."
                }
            ;;
    esac
    
    print_success "Dependencias del sistema instaladas"
}

# ─── Crear entorno virtual ────────────────────────────────────────────────────
create_venv() {
    INSTALL_DIR="/opt/videoflex"
    VENV_DIR="${INSTALL_DIR}/venv"
    
    print_step "Creando directorio de instalación..."
    mkdir -p "$INSTALL_DIR"
    
    print_step "Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
    
    print_step "Activando entorno virtual..."
    source "${VENV_DIR}/bin/activate"
    
    print_step "Actualizando pip..."
    pip install --upgrade pip setuptools wheel -q
    
    print_success "Entorno virtual creado en ${VENV_DIR}"
}

# ─── Instalar dependencias Python ─────────────────────────────────────────────
install_python_deps() {
    print_step "Instalando dependencias de Python..."
    
    pip install -q \
        "flet>=0.21.0" \
        "yt-dlp>=2024.1.1" \
        "requests>=2.31.0" \
        "pyperclip>=1.8.2" \
        "psutil>=5.9.0" \
        "win10toast; sys_platform == 'win32'" \
        2>/dev/null
    
    # Instalar yt-dlp con actualizaciones automáticas
    pip install -q --upgrade yt-dlp
    
    print_success "Dependencias de Python instaladas"
}

# ─── Instalar aplicación ──────────────────────────────────────────────────────
install_app() {
    print_step "Instalando VideoFlex..."
    
    INSTALL_DIR="/opt/videoflex"
    
    # Copiar archivo principal
    if [ -f "VideoFlex.py" ]; then
        cp VideoFlex.py "${INSTALL_DIR}/"
    elif [ -f "$(dirname "$0")/VideoFlex.py" ]; then
        cp "$(dirname "$0")/VideoFlex.py" "${INSTALL_DIR}/"
    else
        print_error "No se encontró VideoFlex.py"
        print_info "Asegúrate de ejecutar el instalador desde el directorio del proyecto"
        exit 1
    fi
    
    # Crear script de inicio
    cat > "${INSTALL_DIR}/videoflex" << 'EOF'
#!/bin/bash
source /opt/videoflex/venv/bin/activate
cd /opt/videoflex
python3 VideoFlex.py "$@"
EOF
    chmod +x "${INSTALL_DIR}/videoflex"
    
    # Crear symlink
    ln -sf "${INSTALL_DIR}/videoflex" /usr/local/bin/videoflex
    
    print_success "Aplicación instalada en ${INSTALL_DIR}"
}

# ─── Crear entrada de escritorio ──────────────────────────────────────────────
create_desktop_entry() {
    print_step "Creando entrada de escritorio..."
    
    DESKTOP_FILE="/usr/share/applications/videoflex.desktop"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.5.1
Type=Application
Name=VideoFlex
GenericName=Video Downloader
Comment=Descargador Universal de Videos y Torrents
Exec=/opt/videoflex/videoflex
Icon=video-x-generic
Terminal=false
Categories=Network;Download;Video;
Keywords=video;download;youtube;torrent;
StartupWMClass=videoflex
StartupNotify=true
EOF
    
    chmod 644 "$DESKTOP_FILE"
    
    # Actualizar base de datos de escritorio
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications/ 2>/dev/null || true
    fi
    
    print_success "Entrada de escritorio creada"
}

# ─── Crear configuración inicial ──────────────────────────────────────────────
create_default_config() {
    print_step "Creando configuración por defecto..."
    
    CONFIG_FILE="$HOME/.videoflex_config.json"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        cat > "$CONFIG_FILE" << EOF
{
  "qbittorrent": {
    "host": "http://localhost",
    "port": "8080",
    "username": "admin",
    "password": "adminadmin",
    "auto_connect": true
  },
  "paths": {
    "video": "$HOME/Downloads/VideoFlex/Videos",
    "torrent": "$HOME/Downloads/VideoFlex/Torrents"
  },
  "theme": "dark",
  "use_cookies": false,
  "cookies_path": "$HOME/.videoflex_cookies.txt",
  "video_quality": "1080",
  "max_concurrent_downloads": 3,
  "notifications_enabled": true,
  "auto_start_downloads": true,
  "minimize_to_tray": false,
  "check_updates": true,
  "auto_update_ytdlp": true,
  "proxy_enabled": false,
  "proxy_url": "",
  "proxy_username": "",
  "proxy_password": "",
  "auto_detect_cookies": false,
  "cookies_browser": "chrome"
}
EOF
        print_success "Configuración creada en ${CONFIG_FILE}"
    else
        print_info "Ya existe una configuración previa, no se sobrescribirá"
    fi
    
    # Crear directorios de descarga
    mkdir -p "$HOME/Downloads/VideoFlex/Videos"
    mkdir -p "$HOME/Downloads/VideoFlex/Torrents"
}

# ─── Configurar qBittorrent ───────────────────────────────────────────────────
setup_qbittorrent() {
    print_step "Verificando qBittorrent..."
    
    if command -v qbittorrent &> /dev/null; then
        print_success "qBittorrent está instalado"
        print_info "Recuerda habilitar la WebUI en:"
        print_info "  qBittorrent → Herramientas → Opciones → Web UI"
        print_info "  Puerto: 8080 | Usuario: admin | Contraseña: adminadmin"
    else
        print_warning "qBittorrent no está instalado"
        print_info "Instálalo manualmente si deseas funcionalidad de torrents"
    fi
}

# ─── Verificar FFmpeg ─────────────────────────────────────────────────────────
verify_ffmpeg() {
    print_step "Verificando FFmpeg..."
    
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version 2>/dev/null | head -n1 | cut -d' ' -f3)
        print_success "FFmpeg ${FFMPEG_VERSION} instalado"
    else
        print_warning "FFmpeg no está instalado"
        print_info "Algunas funciones de conversión no estarán disponibles"
    fi
}

# ─── Verificar VLC ────────────────────────────────────────────────────────────
verify_vlc() {
    print_step "Verificando VLC..."
    
    if command -v vlc &> /dev/null; then
        print_success "VLC está instalado"
    else
        print_warning "VLC no está instalado"
        print_info "El reproductor integrado no estará disponible"
    fi
}

# ─── Crear script de desinstalación ───────────────────────────────────────────
create_uninstaller() {
    print_step "Creando script de desinstalación..."
    
    UNINSTALL_FILE="/usr/local/bin/videoflex-uninstall"
    
    cat > "$UNINSTALL_FILE" << 'EOF'
#!/bin/bash
echo "Desinstalando VideoFlex..."

# Remover aplicación
sudo rm -rf /opt/videoflex
sudo rm -f /usr/local/bin/videoflex
sudo rm -f /usr/share/applications/videoflex.desktop

# Actualizar base de datos de escritorio
sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo "¿Deseas eliminar la configuración y datos? [S/n]"
read -r REPLY
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    rm -f ~/.videoflex_config.json
    rm -f ~/.videoflex_history.json
    rm -f ~/.videoflex_clipboard.json
    rm -f ~/.videoflex_cookies.txt
    rm -f ~/.videoflex_errors.log
    rm -f ~/.videoflex_app.log
    rm -rf ~/Downloads/VideoFlex
    echo "Datos eliminados"
fi

echo "VideoFlex desinstalado correctamente"
EOF
    chmod +x "$UNINSTALL_FILE"
    
    print_success "Desinstalador creado: videoflex-uninstall"
}

# ─── Mostrar resumen ──────────────────────────────────────────────────────────
show_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  ${GREEN}✓ Instalación completada exitosamente${NC}                        ${GREEN}║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  ${BLUE}Comandos disponibles:${NC}                                       ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}    • ${CYAN}videoflex${NC}          → Iniciar aplicación                ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}    • ${CYAN}videoflex-uninstall${NC} → Desinstalar                     ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  ${BLUE}Ubicaciones:${NC}                                                ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}    • App: ${CYAN}/opt/videoflex${NC}                                    ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}    • Config: ${CYAN}~/.videoflex_config.json${NC}                       ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}    • Descargas: ${CYAN}~/Downloads/VideoFlex${NC}                       ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}  ${YELLOW}Nota:${NC} Busca 'VideoFlex' en tu menú de aplicaciones         ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ─── Menú de opciones ─────────────────────────────────────────────────────────
show_menu() {
    echo ""
    echo -e "${PURPLE}Selecciona una opción:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Instalación completa (recomendado)"
    echo -e "  ${GREEN}2)${NC} Solo instalar dependencias"
    echo -e "  ${GREEN}3)${NC} Solo instalar la aplicación"
    echo -e "  ${GREEN}4)${NC} Crear entrada de escritorio"
    echo -e "  ${GREEN}5)${NC} Desinstalar VideoFlex"
    echo -e "  ${RED}0)${NC} Salir"
    echo ""
    read -p "Opción [1-5]: " choice
    
    case $choice in
        1) full_install ;;
        2) install_system_deps; install_python_deps ;;
        3) install_app ;;
        4) create_desktop_entry ;;
        5) videoflex-uninstall ;;
        0) exit 0 ;;
        *) print_error "Opción inválida"; show_menu ;;
    esac
}

# ─── Instalación completa ─────────────────────────────────────────────────────
full_install() {
    detect_distro
    check_root
    update_system
    install_system_deps
    create_venv
    install_python_deps
    install_app
    create_desktop_entry
    create_default_config
    setup_qbittorrent
    verify_ffmpeg
    verify_vlc
    create_uninstaller
    show_summary
}

# ─── Punto de entrada ─────────────────────────────────────────────────────────
main() {
    print_header
    
    # Verificar si ya está instalado
    if [ -f "/opt/videoflex/videoflex" ]; then
        print_warning "VideoFlex ya está instalado"
        read -p "¿Deseas reinstalar? [S/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            print_info "Instalación cancelada"
            exit 0
        fi
    fi
    
    # Si hay argumento --yes, instalar directamente
    if [[ "$1" == "--yes" || "$1" == "-y" ]]; then
        full_install
    else
        show_menu
    fi
}

# Ejecutar
main "$@"