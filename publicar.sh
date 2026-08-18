cd ~/Documents/VideoFlex

# 1. Ver qué cambió
git status

# 2. Agregar archivos de parche al .gitignore (para no subirlos)
echo "parche_*.py" >> .gitignore
echo "aplicar_*.py" >> .gitignore

# 3. Agregar todos los cambios
git add .

# 4. Commit con mensaje descriptivo
git commit -m "Fix: soporte qBittorrent 5.x (HTTP 204) + buscador real de torrents

- Parche para aceptar respuestas HTTP 204 de qBittorrent 5.x
- Botón 'Probar Conexión' convertido a síncrono (funciona correctamente)
- Búsqueda real de torrents (YTS + Pirate Bay)
- Descarga directa a qBittorrent desde resultados de búsqueda
- URL GitHub actualizada a pfecomputacion/videoflex"

# 5. Push al repositorio
git push