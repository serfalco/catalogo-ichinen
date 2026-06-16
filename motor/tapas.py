"""
Búsqueda de tapas de libros por ISBN.
Corre en GitHub Actions (internet abierto), NO en el entorno de desarrollo.

Estrategia:
  1. Por cada ISBN válido, consulta Google Books; si no, Open Library.
  2. Descarga la imagen encontrada a tapas/<isbn>.jpg dentro del repo.
  3. Cachea: si la tapa ya existe en disco, no la vuelve a buscar.
  4. Registra los ISBN ya intentados sin éxito para no repetir esfuerzo cada mes.

Resultado: el motor le pone a cada libro su 'tapa_url' si existe el archivo.
Pensado para usados argentinos: la cobertura será parcial; el resto queda placeholder.
"""
import os, json, time, urllib.request, urllib.error

UA = {"User-Agent": "Mozilla/5.0 (IchinenCatalog; +https://ichinen.com.ar)"}
TIMEOUT = 12

def _get_json(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT)
        return json.load(r)
    except Exception:
        return None

def _descargar(url, destino):
    try:
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT)
        data = r.read()
        if len(data) < 1500:   # imágenes diminutas suelen ser "no disponible"
            return False
        with open(destino, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False

def _url_google(isbn):
    d = _get_json(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&country=AR")
    if not d or d.get("totalItems", 0) == 0:
        return None
    for item in d.get("items", []):
        img = item.get("volumeInfo", {}).get("imageLinks", {})
        # preferir la más grande disponible
        for clave in ("thumbnail", "smallThumbnail", "small", "medium", "large"):
            if img.get(clave):
                return img[clave].replace("&edge=curl", "")
    return None

def _url_openlibrary(isbn):
    # Open Library devuelve la imagen directo; default=false => 404 si no hay
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false"

def buscar_tapas(libros, dir_tapas, registro_fallidos, limite=None, pausa=0.15):
    """
    Descarga tapas faltantes. Modifica cada libro agregando 'tapa_url' relativa
    si encontró archivo. Devuelve estadísticas.
    """
    os.makedirs(dir_tapas, exist_ok=True)
    fallidos = set()
    if os.path.exists(registro_fallidos):
        try:
            fallidos = set(json.load(open(registro_fallidos)))
        except Exception:
            fallidos = set()

    nuevas, cacheadas, sin_tapa, intentos = 0, 0, 0, 0
    for l in libros:
        isbn = l.get("isbn")
        if not isbn:
            continue
        destino = os.path.join(dir_tapas, f"{isbn}.jpg")
        rel = f"/tapas/{isbn}.jpg"
        # ya está descargada
        if os.path.exists(destino):
            l["tapa_url"] = rel
            cacheadas += 1
            continue
        # ya se intentó y falló antes
        if isbn in fallidos:
            sin_tapa += 1
            continue
        if limite is not None and intentos >= limite:
            continue
        intentos += 1
        url = _url_google(isbn)
        bajada = _descargar(url, destino) if url else False
        if not bajada:
            bajada = _descargar(_url_openlibrary(isbn), destino)
        if bajada:
            l["tapa_url"] = rel
            nuevas += 1
        else:
            fallidos.add(isbn)
            sin_tapa += 1
        time.sleep(pausa)  # amable con las APIs

    json.dump(sorted(fallidos), open(registro_fallidos, "w"))
    return {"nuevas": nuevas, "cacheadas": cacheadas, "sin_tapa": sin_tapa, "intentos": intentos}
