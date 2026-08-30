"""
Completa datos faltantes de los libros consultando Open Library y Google Books
por ISBN. Corre en GitHub Actions (internet abierto), NO en desarrollo.

Qué completa, y con qué criterio:
  - autor        solo si el Excel no traía uno confiable
  - editorial    solo si falta
  - año          solo si falta
  - páginas      solo si falta
  - temas        siempre que la API los dé (alimentan la clasificación por género)

REGLA CENTRAL: nunca se pisa un dato que el Excel ya traía bien. La API completa
huecos, no corrige al librero. Si hay conflicto, gana el Excel.

Qué NO hace: no busca por título ni por autor, solo por ISBN exacto. Buscar por
título traería la tapa y los datos de OTRA edición, y en una librería de usados
la edición concreta es parte de lo que se vende. Preferimos el hueco al dato
plausible pero falso.

Expectativa realista de cobertura: la tasa de éxito de estas APIs sigue la
agencia nacional del ISBN. Medido sobre este catálogo:
    EE.UU./Reino Unido 68 % · España 47 % · Argentina (950) 33 %
    Argentina (987) 20 % · México 17 % · Chile 0 %
Como el 69 % de los ISBN de esta librería son argentinos, esperar más de un
35-45 % de completitud sobre los libros con ISBN es engañarse. El resto
necesita trabajo humano.

Todo lo consultado se cachea en `.enriquecido.json` (raíz del repo), así cada
corrida solo pregunta por los libros nuevos.
"""
import os, json, time, re, unicodedata, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (IchinenCatalog; +https://ichinen.com.ar)"}
TIMEOUT = 12


# --- utilidades ---------------------------------------------------------------
def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def _get_json(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT)
        return json.load(r)
    except Exception:
        return None


def _anio(texto):
    m = re.search(r"(1[5-9]\d{2}|20[0-4]\d)", str(texto or ""))
    return m.group(1) if m else ""


# --- consultas ----------------------------------------------------------------
def _openlibrary(isbn):
    d = _get_json(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data")
    rec = (d or {}).get(f"ISBN:{isbn}")
    if not rec:
        return None
    return {
        "titulo":    rec.get("title", ""),
        "autores":   [a.get("name", "") for a in rec.get("authors", []) if a.get("name")],
        "editorial": (rec.get("publishers") or [{}])[0].get("name", ""),
        "anio":      _anio(rec.get("publish_date", "")),
        "paginas":   str(rec.get("number_of_pages") or ""),
        "temas":     [t.get("name", "") for t in rec.get("subjects", []) if t.get("name")],
        "fuente":    "openlibrary",
    }


def _googlebooks(isbn):
    d = _get_json(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&country=AR")
    if not d or not d.get("items"):
        return None
    vi = d["items"][0].get("volumeInfo", {})
    return {
        "titulo":    vi.get("title", ""),
        "autores":   vi.get("authors", []) or [],
        "editorial": vi.get("publisher", ""),
        "anio":      _anio(vi.get("publishedDate", "")),
        "paginas":   str(vi.get("pageCount") or ""),
        "temas":     vi.get("categories", []) or [],
        "fuente":    "googlebooks",
    }


def consultar(isbn):
    """Combina ambas fuentes. Open Library primero (mejor cobertura de temas)."""
    a = _openlibrary(isbn)
    b = _googlebooks(isbn)
    if not a and not b:
        return None
    if not a:
        return b
    if not b:
        return a
    # fusión: se prefiere el valor no vacío, con Open Library como primario
    out = dict(a)
    for k in ("titulo", "editorial", "anio", "paginas"):
        if not out.get(k):
            out[k] = b.get(k, "")
    if not out.get("autores"):
        out["autores"] = b.get("autores", [])
    out["temas"] = list(dict.fromkeys((a.get("temas") or []) + (b.get("temas") or [])))
    out["fuente"] = "ambas"
    return out


# --- aplicación ---------------------------------------------------------------
# El título que devuelve la API sirve de control: si no se parece en nada al del
# Excel, el ISBN está mal cargado y no aplicamos NADA de ese registro.
def _coincide_titulo(excel, api):
    if not api:
        return True  # sin título de control, seguimos (el ISBN es la clave)
    a = {w for w in _norm(excel).split() if len(w) > 3}
    b = {w for w in _norm(api).split() if len(w) > 3}
    if not a or not b:
        return True
    return len(a & b) >= 1


def aplicar(libro, datos):
    """Completa huecos del libro. Devuelve la lista de campos que se llenaron."""
    if not datos:
        return []
    if not _coincide_titulo(libro.get("titulo", ""), datos.get("titulo", "")):
        return []

    llenados = []
    if not libro.get("autor_ok") and datos.get("autores"):
        nombre = datos["autores"][0].strip()
        if nombre and len(nombre) > 2:
            libro["autor"] = nombre
            libro["autor_ok"] = True
            if "autor" in libro.get("faltantes", []):
                libro["faltantes"].remove("autor")
            llenados.append("autor")
    if not libro.get("editorial") and datos.get("editorial"):
        libro["editorial"] = datos["editorial"].strip()
        if "editorial" in libro.get("faltantes", []):
            libro["faltantes"].remove("editorial")
        llenados.append("editorial")
    if not libro.get("anio") and datos.get("anio"):
        libro["anio"] = datos["anio"]
        if "año" in libro.get("faltantes", []):
            libro["faltantes"].remove("año")
        llenados.append("año")
    if (not libro.get("paginas") or libro["paginas"] in ("0", "")) and datos.get("paginas"):
        libro["paginas"] = datos["paginas"]
        llenados.append("páginas")
    if datos.get("temas"):
        libro["temas"] = datos["temas"]
        llenados.append("temas")
    return llenados


def enriquecer(libros, cache_path, limite=None, pausa=0.2):
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path, encoding="utf-8"))
        except Exception:
            cache = {}

    consultas, stats = 0, {}
    for l in libros:
        isbn = l.get("isbn")
        if not isbn:
            continue
        if isbn not in cache:
            if limite is not None and consultas >= limite:
                continue
            consultas += 1
            cache[isbn] = consultar(isbn) or {}
            time.sleep(pausa)
        for campo in aplicar(l, cache[isbn]):
            stats[campo] = stats.get(campo, 0) + 1

    json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
    conocidos = sum(1 for v in cache.values() if v)
    return {"consultas_nuevas": consultas, "en_cache": len(cache),
            "con_datos": conocidos, "campos": stats}
