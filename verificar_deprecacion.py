"""
Script de Verificación para VideoFlex
Ejecuta este script para verificar si tu archivo tiene errores de deprecación
"""

import re
import sys
from pathlib import Path

def verificar_archivo(filepath):
    """Verifica si un archivo tiene sintaxis deprecada"""
    
    print("="*60)
    print("VERIFICADOR DE DEPRECACIÓN - VideoFlex")
    print("="*60)
    print(f"\nArchivo: {filepath}")
    print(f"Ruta completa: {Path(filepath).absolute()}\n")
    
    if not Path(filepath).exists():
        print(f"❌ ERROR: El archivo '{filepath}' no existe")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Patrones deprecados a buscar
    deprecated = {
        r'ft\.border\.all\(': 'ft.border.all() → Debe ser ft.Border.all()',
        r'ft\.margin\.only\(': 'ft.margin.only() → Debe ser ft.Margin.only()',
        r'ft\.padding\.symmetric\(': 'ft.padding.symmetric() → Debe ser ft.Padding.symmetric()',
        r'ft\.padding\.only\(': 'ft.padding.only() → Debe ser ft.Padding.only()',
    }
    
    errores_encontrados = []
    
    for i, line in enumerate(lines, 1):
        for pattern, mensaje in deprecated.items():
            if re.search(pattern, line):
                errores_encontrados.append({
                    'linea': i,
                    'mensaje': mensaje,
                    'codigo': line.strip()
                })
    
    if errores_encontrados:
        print("❌ SE ENCONTRARON ERRORES DE DEPRECACIÓN:\n")
        for error in errores_encontrados:
            print(f"Línea {error['linea']}: {error['mensaje']}")
            print(f"   {error['codigo']}")
            print()
        print(f"\n⚠️  Total de errores: {len(errores_encontrados)}")
        return False
    else:
        print("✅ ¡PERFECTO! No se encontraron errores de deprecación")
        print("\nTu archivo está actualizado y compatible con Flet 0.80.5+")
        
        # Verificar características implementadas
        content = ''.join(lines)
        print("\n" + "="*60)
        print("CARACTERÍSTICAS IMPLEMENTADAS:")
        print("="*60)
        
        if '_connect_qbittorrent_async' in content:
            print("✅ Inicio optimizado (conexión asíncrona)")
        else:
            print("❌ Inicio NO optimizado")
        
        if 'timeout = 5' in content or 'timeout=5' in content:
            print("✅ Timeouts reducidos (5 segundos)")
        else:
            print("⚠️  Timeouts sin optimizar")
        
        if 'expand=True' in content:
            print("✅ Contenedores expandibles implementados")
        else:
            print("❌ Contenedores NO están expandidos")
        
        if 'height=320' in content or 'height = 320' in content:
            print("✅ Altura de lista optimizada (320px)")
        else:
            print("⚠️  Altura de lista sin optimizar")
        
        return True

if __name__ == "__main__":
    # Archivos a verificar
    archivos = [
        "appg15CL5.py",
        "appg17DS.py",
        "appg15CL4.py"
    ]
    
    print("\nBuscando archivos Python en el directorio actual...\n")
    
    archivos_encontrados = []
    for archivo in archivos:
        if Path(archivo).exists():
            archivos_encontrados.append(archivo)
    
    # Buscar TODOS los archivos .py
    todos_py = list(Path('.').glob('*.py'))
    
    if not todos_py:
        print("❌ No se encontraron archivos .py en este directorio")
        print(f"Directorio actual: {Path.cwd()}")
        sys.exit(1)
    
    print(f"Archivos .py encontrados: {len(todos_py)}")
    for f in todos_py:
        print(f"  - {f.name}")
    
    print("\n" + "="*60)
    
    # Verificar cada archivo
    for archivo in todos_py:
        if archivo.name == Path(__file__).name:
            continue  # Saltar este mismo script
        
        verificar_archivo(str(archivo))
        print("\n" + "="*60 + "\n")
    
    print("\n📋 RECOMENDACIÓN:")
    print("Si encuentras errores, usa el archivo appg15CL5_VERIFICADO.py")
    print("que está libre de errores de deprecación.")
