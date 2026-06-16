"""
Limpieza y normalización de los datos crudos del Excel de Mercado Libre.
Todo lo que entra sucio acá sale presentable o marcado como "a verificar".
"""
import re
import unicodedata
from unidecode import unidecode

# --- Mapa de categorías -------------------------------------------------------
# Agrupa los "tipos de narración" sucios del Excel en pocas categorías limpias.
# Todo lo que no matchee cae en "Otros" (categoría residual, esencial).
MAPA_CATEGORIAS = {
    "Literatura": [
        "novela", "novelas", "cuento", "cuentos", "narrativa", "ficcion",
        "libros de ficcion", "literatura universal", "literatura clasica griega",
        "clasicos", "fabula", "jovenes lectores", "biografias y relatos",
        "textos antiguos,clasicos y medievales", "escrito", "escrita", "obra",
    ],
    "Poesía": ["poesia", "aforismos", "cancionero"],
    "Teatro": ["teatro", "dialogo"],
    "Ensayo y Filosofía": [
        "filosofia", "ensayo", "ensayo politico", "capitalismo", "psicologia",
        "historia", "biografia",
    ],
    "Arte": ["arte", "pintura / arte", "mitologia", "tango"],
    "Referencia": ["manual", "diccionario", "matematicas", "general"],
}

# Etiquetas que claramente NO son un tipo (nombres de colección, basura)
# se ignoran y el libro cae en "Otros".

def _norm(s: str) -> str:
    """minúsculas, sin acentos, sin espacios extra — para comparar."""
    s = unidecode((s or "").strip().lower())
    return re.sub(r"\s+", " ", s)

def clasificar(tipo_narracion: str) -> str:
    t = _norm(tipo_narracion)
    if not t:
        return "Otros"
    for categoria, claves in MAPA_CATEGORIAS.items():
        if t in claves:
            return categoria
    return "Otros"

# --- Limpieza de texto --------------------------------------------------------

def limpiar_titulo(t: str) -> str:
    t = (t or "").strip()
    if not t:
        return ""
    # Defensa: la fila de ayuda de la plantilla MELI no es un libro.
    if "Si tienes variantes" in t or t.startswith("Título del libro"):
        return ""
    # sacar símbolos sueltos al inicio/fin y asteriscos de marcado interno
    t = re.sub(r"[\*•·]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -—–·.")
    # si viene todo en minúscula o todo en mayúscula, pasar a Capitalización por palabra
    letras = re.sub(r"[^a-zA-ZáéíóúñÁÉÍÓÚÑ]", "", t)
    if letras and (letras.islower() or letras.isupper()):
        t = _title_es(t)
    return t.strip()

def _title_es(t: str) -> str:
    """Capitaliza tipo título en español: primera palabra y nombres, minúsculas para conectores."""
    menores = {"de","del","la","las","el","los","y","o","a","en","un","una",
               "para","por","con","sin","al","que","su","sus","lo","e"}
    palabras = t.lower().split()
    out = []
    for i, p in enumerate(palabras):
        if i != 0 and p in menores:
            out.append(p)
        else:
            out.append(p[:1].upper() + p[1:])
    return " ".join(out)

# Valores que aparecen en AUTHOR pero NO son autores reales
AUTOR_NO_CONFIABLE = {
    "", "aa vv", "aavv", "no aplica", "anonimo", "varios", "varios autores",
    "perfil criminal", "mente criminal", "coleccion mitologia", "nat geo",
    "aprender a pensar", "rba", "gredos", "libro sagrado de los mayas",
}

def limpiar_autor(a: str):
    """Devuelve (autor_mostrado, confiable: bool)."""
    a = (a or "").strip()
    a = re.sub(r"^[•·\*\-\s]+", "", a).strip()
    # Forma "Apellido, Nombre" -> "Nombre Apellido"
    if a.count(",") == 1 and not any(ch.isdigit() for ch in a):
        ap, no = [x.strip() for x in a.split(",")]
        if ap and no:
            a = f"{no} {ap}"
    base = _norm(a)
    if base in AUTOR_NO_CONFIABLE or len(base) < 2:
        return ("Autor a verificar", False)
    # normalizar mayúsculas si viene gritado
    letras = re.sub(r"[^a-zA-ZáéíóúñÁÉÍÓÚÑ]", "", a)
    if letras and (letras.isupper() or letras.islower()):
        a = _title_es(a)
    return (a, True)

def limpiar_anio(x: str):
    x = (x or "").strip()
    m = re.search(r"(1[5-9]\d{2}|20[0-4]\d)", x)
    return m.group(1) if m else ""

def limpiar_editorial(e: str):
    e = (e or "").strip().strip(" .-")
    if not e:
        return ""
    letras = re.sub(r"[^a-zA-ZáéíóúñÁÉÍÓÚÑ]", "", e)
    if letras and (letras.isupper() or letras.islower()):
        e = _title_es(e)
    return e

def isbn_valido(g: str) -> str:
    """Devuelve ISBN-13 si parece válido, sino ''. Para buscar tapas."""
    d = re.sub(r"[^0-9Xx]", "", (g or ""))
    if len(d) == 13 and d.startswith(("978", "979")):
        return d
    return ""

# --- Slug para URL ------------------------------------------------------------

def slugify(texto: str) -> str:
    s = unidecode((texto or "").lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "libro"
