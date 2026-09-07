"""
Búsqueda de tapas de libros por ISBN, con verificación de coherencia.
Corre en GitHub Actions (internet abierto), NO en el entorno de desarrollo.

Estrategia:
  1. Por cada ISBN válido, consulta Google Books (trae imagen + título).
  2. VERIFICA que el título devuelto coincida con el título del Excel.
     Esto evita tapas cruzadas por ISBN mal cargado en el Excel.
  3. Si Google no tiene tapa, prueba Open Library (verificando su título aparte).
  4. Descarga la imagen a tapas/<isbn>.jpg. Cachea entre corridas.
  5. Registra ISBN fallidos para no reintentarlos cada vez.

Las tapas cacheadas se re-verifican contra el título por si quedaron cruces viejos.
Cobertura parcial esperable (usados argentinos); el resto queda placeholder.
"""
import os, json, time, re, unicodedata, urllib.request, urllib.error
import datetime

UA = {"User-Agent": "Mozilla/5.0 (IchinenCatalog; +https://ichinen.com.ar)"}
TIMEOUT = 12

# --- normalización y comparación de títulos ----------------------------------
_STOP = {"el","la","los","las","un","una","de","del","y","o","a","en","the","of",
         "and","tomo","vol","volumen","edicion","ed"}

def _palabras(texto):
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return {w for w in t.split() if len(w) > 2 and w not in _STOP}

def _coincide(titulo_excel, titulo_api):
    """True si los títulos comparten suficientes palabras significativas."""
    a, b = _palabras(titulo_excel), _palabras(titulo_api)
    if not a or not b:
        return False
    comunes = a & b
    # acepta si comparten al menos 1 palabra significativa y esa
    # representa una porción razonable del título más corto
    menor = min(len(a), len(b))
    if not comunes:
        return False
    return len(comunes) / menor >= 0.5 or len(comunes) >= 2

# --- consultas a las APIs -----------------------------------------------------
class ApiNoDisponible(Exception):
    """La API no contestó: cuota agotada, error del servidor o red caída.

    Es distinto de "el libro no está en la base". Si se confunden, una corrida
    con la cuota de Google agotada marca cientos de ISBN como fallidos para
    siempre, y esos libros no vuelven a intentarse nunca.
    """


def _get_json(url):
    """Devuelve el JSON, o None si la API respondió que no hay nada.

    Lanza ApiNoDisponible cuando el problema es de la API, no del libro.
    """
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT)
        return json.load(r)
    except urllib.error.HTTPError as e:
        # 429 = cuota. 401/403 = credencial o bloqueo. 5xx = el servidor falló.
        if e.code in (401, 402, 403, 429) or e.code >= 500:
            raise ApiNoDisponible(f"HTTP {e.code}") from None
        return None
    except Exception:
        # Timeout, DNS, conexión cortada: tampoco es culpa del libro.
        raise ApiNoDisponible("sin respuesta") from None

def _descargar(url, destino):
    try:
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT)
        data = r.read()
        if len(data) < 1500:
            return False
        with open(destino, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False

def _google(isbn):
    """Devuelve (url_imagen, titulo_api) o (None, None)."""
    d = _get_json(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&country=AR")
    if not d or d.get("totalItems", 0) == 0:
        return None, None
    for item in d.get("items", []):
        vi = item.get("volumeInfo", {})
        img = vi.get("imageLinks", {})
        titulo = vi.get("title", "")
        for clave in ("thumbnail", "smallThumbnail", "small", "medium", "large"):
            if img.get(clave):
                return img[clave].replace("&edge=curl", ""), titulo
    return None, None

def _openlibrary(isbn):
    """Devuelve (url_imagen, titulo_api) o (None, None)."""
    d = _get_json(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data")
    if not d:
        return None, None
    rec = d.get(f"ISBN:{isbn}")
    if not rec:
        return None, None
    titulo = rec.get("title", "")
    cover = rec.get("cover", {})
    url = cover.get("medium") or cover.get("large") or cover.get("small")
    return (url, titulo) if url else (None, None)

def _buscar_una(isbn, titulo_excel, destino):
    """Busca una tapa que COINCIDA con el título.

    Devuelve "ok" si la bajó, "sin_tapa" si las APIs contestaron y no la tienen,
    y "error" si alguna no contestó. Solo "sin_tapa" justifica dar el ISBN por
    perdido; "error" se reintenta en la próxima corrida.
    """
    hubo_error = False
    for fuente in (_google, _openlibrary):
        try:
            url, titulo_api = fuente(isbn)
        except ApiNoDisponible:
            hubo_error = True
            continue
        if url and _coincide(titulo_excel, titulo_api):
            if _descargar(url, destino):
                return "ok"
    return "error" if hubo_error else "sin_tapa"

# --- proceso principal --------------------------------------------------------
def _hoy():
    return datetime.date.today().isoformat()


def _caducado(fecha, dias):
    """True si el fallo es viejo y conviene reintentarlo."""
    try:
        d = datetime.date.fromisoformat(fecha)
    except Exception:
        return True
    return (datetime.date.today() - d).days >= dias


def buscar_tapas(libros, dir_tapas, registro_fallidos, limite=None, pausa=0.15,
                 dias_reintento=120):
    """Busca tapas faltantes.

    `registro_fallidos` guarda {isbn: fecha del último intento fallido}. Un fallo
    caduca a los `dias_reintento` días: las APIs incorporan registros con el
    tiempo, y un libro que hoy no está puede estar en unos meses. Se acepta
    también el formato viejo (lista simple), estampándolo con la fecha de hoy.
    """
    os.makedirs(dir_tapas, exist_ok=True)
    fallidos = {}
    if os.path.exists(registro_fallidos):
        try:
            crudo = json.load(open(registro_fallidos))
            if isinstance(crudo, list):
                fallidos = {str(i): _hoy() for i in crudo}
            elif isinstance(crudo, dict):
                fallidos = {str(k): str(v) for k, v in crudo.items()}
        except Exception:
            fallidos = {}

    # Registro de tapas ya verificadas (para no re-chequear las buenas cada vez)
    reg_ok_path = os.path.join(dir_tapas, ".verificadas.json")
    verificadas = set()
    if os.path.exists(reg_ok_path):
        try:
            verificadas = set(json.load(open(reg_ok_path)))
        except Exception:
            verificadas = set()

    nuevas, cacheadas, sin_tapa, intentos, descartadas, errores = 0, 0, 0, 0, 0, 0
    for l in libros:
        isbn = l.get("isbn")
        if not isbn:
            continue
        destino = os.path.join(dir_tapas, f"{isbn}.jpg")
        rel = f"/tapas/{isbn}.jpg"

        if os.path.exists(destino):
            if isbn in verificadas:
                l["tapa_url"] = rel
                cacheadas += 1
                continue
            # tapa vieja sin verificar: validar coherencia ahora
            if limite is not None and intentos >= limite:
                # sin presupuesto para verificar: la dejamos por ahora
                l["tapa_url"] = rel
                cacheadas += 1
                continue
            intentos += 1
            titulo_api, falla = None, False
            for fuente in (_google, _openlibrary):
                try:
                    _, titulo_api = fuente(isbn)
                except ApiNoDisponible:
                    falla = True
                    titulo_api = None
                if titulo_api:
                    break
            if titulo_api and _coincide(l["titulo"], titulo_api):
                verificadas.add(isbn)
                l["tapa_url"] = rel
                cacheadas += 1
            elif falla:
                # La API no contestó. NO se borra la tapa: no sabemos si está
                # cruzada. Sin esto, una corrida con la cuota agotada borraba
                # tapas buenas que ya habían costado una consulta cada una.
                l["tapa_url"] = rel
                cacheadas += 1
                errores += 1
            else:
                os.remove(destino)        # tapa cruzada: la borramos
                fallidos[isbn] = _hoy()
                descartadas += 1
            time.sleep(pausa)
            continue

        if isbn in fallidos and not _caducado(fallidos[isbn], dias_reintento):
            sin_tapa += 1
            continue
        if limite is not None and intentos >= limite:
            continue
        intentos += 1
        resultado = _buscar_una(isbn, l["titulo"], destino)
        if resultado == "ok":
            verificadas.add(isbn)
            l["tapa_url"] = rel
            nuevas += 1
        elif resultado == "sin_tapa":
            fallidos[isbn] = _hoy()
            sin_tapa += 1
        else:
            # error de API: se reintenta en la próxima corrida
            errores += 1
        time.sleep(pausa)

    json.dump(dict(sorted(fallidos.items())), open(registro_fallidos, "w"),
              ensure_ascii=False, indent=0)
    json.dump(sorted(verificadas), open(reg_ok_path, "w"))
    return {"nuevas": nuevas, "cacheadas": cacheadas, "sin_tapa": sin_tapa,
            "intentos": intentos, "descartadas": descartadas, "errores": errores}
