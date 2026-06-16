#!/usr/bin/env python3
"""
Build del catálogo Ichinén. Es el script que corre GitHub Actions cada mes.

Pasos:
  1. Descarga el Excel desde la URL de Hostinger (o usa uno local si se pasa --excel).
  2. Lee y limpia los libros.
  3. Busca tapas por ISBN (si BUSCAR_TAPAS=1), cacheando en tapas/.
  4. Genera el sitio estático completo.

Variables de entorno:
  EXCEL_URL      URL del Excel en Hostinger (ej. https://ichinen.com.ar/datos/listado.xlsx)
  BUSCAR_TAPAS   "1" para activar búsqueda de tapas, "0" para placeholder en todos.
  LIMITE_TAPAS   (opcional) máximo de búsquedas nuevas por corrida, para no demorar de más.
"""
import os, sys, argparse, urllib.request, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lector import leer_excel
from generador import generar_sitio
from tapas import buscar_tapas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raíz del repo
SALIDA = os.path.join(RAIZ, "docs")        # GitHub Pages puede servir desde /docs
DIR_TAPAS = os.path.join(SALIDA, "tapas")
REGISTRO_FALLIDOS = os.path.join(RAIZ, ".tapas_fallidas.json")

def descargar_excel(url, destino):
    print(f"Descargando Excel desde {url} …")
    req = urllib.request.Request(url, headers={"User-Agent": "IchinenBuild/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(destino, "wb") as f:
        f.write(r.read())
    print(f"  Excel guardado ({os.path.getsize(destino)//1024} KB)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", help="ruta local a un Excel (si no, usa EXCEL_URL)")
    args = ap.parse_args()

    excel_local = os.path.join(RAIZ, "_listado.xlsx")
    if args.excel:
        shutil.copy(args.excel, excel_local)
    else:
        url = os.environ.get("EXCEL_URL")
        if not url:
            print("ERROR: falta EXCEL_URL (o pasá --excel).", file=sys.stderr)
            sys.exit(1)
        descargar_excel(url, excel_local)

    print("Leyendo y limpiando libros …")
    libros = leer_excel(excel_local)
    print(f"  {len(libros)} libros")

    # Conservar tapas ya descargadas entre corridas: mover de la salida anterior
    tapas_previas = DIR_TAPAS
    cache_tmp = os.path.join(RAIZ, "_tapas_cache")
    if os.path.exists(tapas_previas):
        if os.path.exists(cache_tmp):
            shutil.rmtree(cache_tmp)
        shutil.move(tapas_previas, cache_tmp)

    if os.environ.get("BUSCAR_TAPAS", "0") == "1":
        os.makedirs(cache_tmp, exist_ok=True)
        limite = os.environ.get("LIMITE_TAPAS")
        limite = int(limite) if limite else None
        print(f"Buscando tapas (límite nuevas: {limite or 'sin límite'}) …")
        stats = buscar_tapas(libros, cache_tmp, REGISTRO_FALLIDOS, limite=limite)
        print(f"  tapas: {stats['nuevas']} nuevas, {stats['cacheadas']} cacheadas, "
              f"{stats['sin_tapa']} sin tapa")
    else:
        print("Búsqueda de tapas desactivada (BUSCAR_TAPAS != 1). Todos con placeholder.")

    print("Generando sitio …")
    generar_sitio(libros, SALIDA)

    # Restaurar/colocar las tapas dentro de la salida
    if os.path.exists(cache_tmp):
        destino = DIR_TAPAS
        if os.path.exists(destino):
            shutil.rmtree(destino)
        shutil.move(cache_tmp, destino)

    n_tapas = len(os.listdir(DIR_TAPAS)) if os.path.exists(DIR_TAPAS) else 0
    print(f"Listo. Sitio en {SALIDA} · {len(libros)} libros · {n_tapas} tapas en disco")

if __name__ == "__main__":
    main()
