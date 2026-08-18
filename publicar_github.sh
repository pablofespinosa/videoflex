#!/bin/bash
#===============================================================================
#  VideoFlex — Publicador en GitHub v3.0
#  Uso: ./publicar_github.sh   (desde Git Bash, en la carpeta del proyecto)
#===============================================================================

R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'
B='\033[0;34m'; P='\033[0;35m'; C='\033[0;36m'
W='\033[1;37m'; N='\033[0m'

ok()   { echo -e "  ${G}✔${N} $1"; }
info() { echo -e "  ${C}➤${N} $1"; }
warn() { echo -e "  ${Y}⚠${N} $1"; }
err()  { echo -e "  ${R}✘${N} $1"; }
head() { echo -e "\n${P}━━━ $1 ━━━${N}"; }

GH_USER="pfecomputacion"
REPO="videoflex"
REPO_URL="https://github.com/${GH_USER}/${REPO}"

echo ""
echo -e "${B}╔══════════════════════════════════════════════════════════╗${N}"
echo -e "${B}║${N}   ${W}🚀 VideoFlex — Publicador en GitHub v3.0${N}               ${B}║${N}"
echo -e "${B}║${N}   ${C}Destino: ${REPO_URL}${N}   ${B}║${N}"
echo -e "${B}╚══════════════════════════════════════════════════════════╝${N}"

cd "$(dirname "$0")" || exit 1

# ─── 1) Verificaciones ───────────────────────────────────────────────────────
head "1/6  Verificaciones"

command -v git &>/dev/null && ok "Git $(git --version | awk '{print $3}')" || { err "Git no instalado"; exit 1; }
ls VideoFlex*.py &>/dev/null && ok "Código encontrado" || { err "No hay VideoFlex*.py aquí"; exit 1; }

PYTHON="$(command -v python || command -v python3)"
[ -n "$PYTHON" ] && ok "Python: $PYTHON" || warn "Python no detectado (el parche final se omitirá)"

if curl -sI --max-time 10 https://github.com &>/dev/null; then
    ok "Conexión con github.com: OK"
else
    warn "No hay conexión con github.com — revisa red/VPN/antivirus"
fi

# Identidad git (si falta)
[ -z "$(git config --global user.name 2>/dev/null)" ] && git config --global user.name "Pablo F. Espinosa"
[ -z "$(git config --global user.email 2>/dev/null)" ] && git config --global user.email "pfecomputacion@users.noreply.github.com"
ok "Identidad: $(git config --global user.name)"

# ─── 2) Archivos del proyecto ────────────────────────────────────────────────
head "2/6  Generando archivos"

if [ ! -f .gitignore ]; then
cat > .gitignore << 'GI_EOF'
.venv/
venv/
__pycache__/
*.pyc
*.pyo
*.log
build/
dist/
*.spec
*.egg-info/
GI_EOF
ok ".gitignore creado"
else ok ".gitignore ya existe"; fi

if [ ! -f LICENSE ]; then
    if curl -sL --max-time 20 -o LICENSE https://www.gnu.org/licenses/gpl-3.0.txt && [ -s LICENSE ]; then
        ok "LICENSE GPL-3.0 descargado"
    else
        printf '%s\n' "VideoFlex - Copyright (C) 2025-2026 Pablo F. Espinosa - PFE Computacion" "" "Licensed under the GNU General Public License v3.0 or later." "See <https://www.gnu.org/licenses/>." > LICENSE
        warn "LICENSE corto (no se pudo descargar el texto completo)"
    fi
else ok "LICENSE ya existe"; fi

if [ ! -f README.md ]; then
cat > README.md << 'README_EOF'
# ⚡ VideoFlex

**Descargador Universal de Videos y Torrents** — YouTube, TikTok, Instagram, Twitter/X, Facebook, Vimeo + qBittorrent.

![Licencia](https://img.shields.io/badge/licencia-GPL--3.0-green) ![Python](https://img.shields.io/badge/python-3.8–3.13-yellow) ![UI](https://img.shields.io/badge/UI-Flet-purple)

## ✨ Características
- 🎥 Videos en 720p/1080p/1440p/4K · 🎵 Audio MP3/M4A/FLAC/OGG/WAV
- 🧲 Torrents vía qBittorrent · 📋 Detección de URLs en portapapeles
- ⏰ Descargas programadas y cola inteligente · 📊 Historial con estadísticas
- 🌙 Tema oscuro/claro · 🖥️ Windows y Linux

## 📦 Instalación
**Windows (Git Bash):** `./install_deps_win.sh` y luego `./videoflex` (o `VideoFlex.bat`)
**Linux:** `./install_deps.sh` y luego `./videoflex`

## 🔧 Requisitos
Python 3.8–3.13 · FFmpeg · VLC · qBittorrent (opcional)

## 👨‍💻 Autor
Pablo F. Espinosa — PFE Computación © 2025-2026 · Licencia GPL-3.0
README_EOF
ok "README.md creado"
else ok "README.md ya existe"; fi

# ─── 3) Commit local ─────────────────────────────────────────────────────────
head "3/6  Commit local"

[ -d .git ] || { git init && ok "git init"; }
git branch -M main
git add -A
if git diff --cached --quiet; then
    info "Sin cambios nuevos que confirmar"
else
    git commit -m "VideoFlex v1.5.1 — Descargador universal de videos y torrents (GPL-3.0)"
    ok "Commit creado"
fi

# ─── 4) Método de autenticación ──────────────────────────────────────────────
head "4/6  Elegí método de publicación"
echo -e "  ${G}1)${N} GitHub CLI (gh) — recomendado"
echo -e "  ${G}2)${N} Token personal (funciona aunque el navegador del PC falle)"
echo -e "  ${G}3)${N} Ya creé el repo en otro dispositivo — solo subir código"
read -rp "  Opción [1-3]: " MODO

CREADO=false

if [ "$MODO" = "1" ]; then
    # ── Método gh ──
    if ! command -v gh &>/dev/null; then
        info "Instalando GitHub CLI con winget…"
        winget install --accept-package-agreements --accept-source-agreements -e GitHub.cli &>/dev/null
        export PATH="$PATH:/c/Program Files/GitHub CLI:/c/Program Files (x86)/GitHub CLI"
    fi
    if command -v gh &>/dev/null; then
        gh auth status &>/dev/null || gh auth login -h github.com -p https -w
        gh auth setup-git 2>/dev/null
        ok "Sesión: $(gh api user --jq .login 2>/dev/null)"
        if gh repo view "${GH_USER}/${REPO}" &>/dev/null; then
            warn "El repo ya existe — se usará el existente"
        else
            gh repo create "${GH_USER}/${REPO}" --public \
                --description "⚡ VideoFlex — Descargador Universal de Videos y Torrents" && ok "Repo creado"
        fi
        CREADO=true
    else
        err "gh no disponible — probá la opción 2"
        exit 1
    fi

elif [ "$MODO" = "2" ]; then
    # ── Método token ──
    echo -e "  ${Y}Creá el token en:${N} https://github.com/settings/tokens (puede ser desde el celular)"
    echo -e "  ${Y}Marcá el scope 'repo' y pegalo acá:${N}"
    read -rsp "  Token: " TOKEN; echo
    [ -z "$TOKEN" ] && { err "Token vacío"; exit 1; }

    HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -H "Authorization: token ${TOKEN}" \
        -H "Accept: application/vnd.github+json" \
        https://api.github.com/user/repos \
        -d "{\"name\":\"${REPO}\",\"description\":\"VideoFlex - Descargador Universal de Videos y Torrents\",\"private\":false}")
    if [ "$HTTP" = "201" ]; then ok "Repo creado vía API"; CREADO=true
    elif [ "$HTTP" = "422" ]; then warn "El repo ya existe — se usará el existente"; CREADO=true
    else err "La API devolvió HTTP $HTTP — revisá el token (scope 'repo')"; exit 1; fi
    PUSH_URL="https://${GH_USER}:${TOKEN}@github.com/${GH_USER}/${REPO}.git"

elif [ "$MODO" = "3" ]; then
    CREADO=true
else
    err "Opción inválida"; exit 1
fi

# ─── 5) Remote + push ────────────────────────────────────────────────────────
head "5/6  Subiendo código"

git remote remove origin 2>/dev/null
if [ "$MODO" = "2" ]; then
    git remote add origin "$PUSH_URL"
else
    git remote add origin "${REPO_URL}.git"
fi

info "Push a main… (si pide credenciales, autorizá en el navegador)"
if git push -u origin main; then
    ok "Código publicado"
else
    err "Push fallido — verificá credenciales/permisos"
    exit 1
fi

# Dejar el remote limpio (sin token embebido)
if [ "$MODO" = "2" ]; then
    git remote set-url origin "${REPO_URL}.git"
    ok "Remote limpio configurado para futuros push"
fi

# ─── 6) Parche del botón GitHub en la app ────────────────────────────────────
head "6/6  Actualizando la app"

APP_FILE="$(ls VideoFlex_Q.py 2>/dev/null || ls VideoFlex.py 2>/dev/null)"

if [ -n "$APP_FILE" ] && [ -n "$PYTHON" ]; then
    "$PYTHON" - "$APP_FILE" "$REPO_URL" << 'PATCH'
import io, sys, re
p, url = sys.argv[1], sys.argv[2]
src = io.open(p, encoding='utf-8').read()
orig = src
if 'APP_GITHUB_URL' not in src:
    anchor = 'APP_DESCRIPTION = "Descargador Universal de Videos y Torrents"'
    if anchor in src:
        src = src.replace(anchor, anchor + '\nAPP_GITHUB_URL = "' + url + '"', 1)
else:
    src = re.sub(r'APP_GITHUB_URL\s*=\s*"[^"]*"', 'APP_GITHUB_URL = "' + url + '"', src)
src = src.replace('webbrowser.open("https://github.com/pfecomputacion/videoflex")',
                  'webbrowser.open(APP_GITHUB_URL)')
if src != orig:
    io.open(p, 'w', encoding='utf-8').write(src)
    print("  ✔ Botón GitHub de la app actualizado")
else:
    print("  ⚠ Sin cambios que aplicar en la app")
PATCH
    git add "$APP_FILE"
    if ! git diff --cached --quiet; then
        git commit -m "App: botón GitHub apunta al repo publicado" && git push
    fi
fi

cmd //c start "" "$REPO_URL" 2>/dev/null

echo ""
echo -e "${G}╔══════════════════════════════════════════════════════════╗${N}"
echo -e "${G}║${N}   ${G}✅ ¡VideoFlex publicado!${N}                               ${G}║${N}"
echo -e "${G}║${N}   ${C}${REPO_URL}${N}   ${G}║${N}"
echo -e "${G}║${N}   Futuros cambios: ${C}git add -A && git commit -m \"msg\" && git push${N}  ${G}║${N}"
echo -e "${G}╚══════════════════════════════════════════════════════════╝${N}"
echo ""