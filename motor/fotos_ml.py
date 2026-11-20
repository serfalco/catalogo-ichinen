"""
Tapas sacadas de las fotos que el librero subió a sus publicaciones de
Mercado Libre (vendedor ROLO1938).

Las fotos se bajan una sola vez fuera del build (con el navegador, porque la API
de Mercado Libre pide autenticación) y quedan guardadas en docs/tapas/ml/.
El índice `.fotos_ml.json` dice qué foto corresponde a qué publicación:

    {"<título de la publicación normalizado>": "ml/<archivo>.jpg", ...}

La llave es el título de la publicación (columna TITLE del Excel), que es el
mismo texto que se ve en Mercado Libre. Solo se usan fotos subidas por el
vendedor (las de catálogo genérico de Mercado Libre quedan afuera).

Se usa solo como respaldo: si el libro ya tiene tapa por ISBN, se respeta.
"""
import os, json, re, unicodedata


def normalizar(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def aplicar_fotos_ml(libros, dir_tapas, indice_path):
    """Asigna tapa_url a los libros sin tapa que tienen foto propia en ML."""
    if not os.path.exists(indice_path):
        return {"asignadas": 0, "indice": 0}
    try:
        indice = json.load(open(indice_path, encoding="utf8"))
    except Exception:
        return {"asignadas": 0, "indice": 0}
    asignadas = 0
    for l in libros:
        if l.get("tapa_url"):
            continue
        rel = indice.get(normalizar(l.get("titulo_ml")))
        if rel and os.path.exists(os.path.join(dir_tapas, rel)):
            l["tapa_url"] = f"/tapas/{rel}"
            asignadas += 1
    return {"asignadas": asignadas, "indice": len(indice)}
