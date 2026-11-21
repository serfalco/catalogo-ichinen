"""
Taxonomía del catálogo. Criterio y fuentes en CLASIFICACION.md (Thema de
EDItEUR + CDU). Cada código corto se usa en clasificacion_manual.tsv; el
nombre es lo que se ve en el sitio y de él sale la URL de la categoría.
"""
import os
import re
import unicodedata

# código -> nombre visible. El orden es el de la portada del catálogo.
CATEGORIAS = {
    "NAR": "Narrativa",
    "CLA": "Clásicos de la literatura",
    "POL": "Policial y misterio",
    "THR": "Thriller y suspenso",
    "TER": "Terror",
    "CFF": "Ciencia ficción y fantasía",
    "ROM": "Novela romántica",
    "NHI": "Novela histórica",
    "POE": "Poesía",
    "TEA": "Teatro",
    "MIT": "Mitología y épica clásica",
    "ECL": "Ensayo y crítica literaria",
    "HUM": "Humor",
    "HQ":  "Historieta y cómic",
    "INF": "Infantil",
    "JUV": "Juvenil",
    "FIL": "Filosofía y pensamiento",
    "PSI": "Psicología y psicoanálisis",
    "AUT": "Autoayuda y desarrollo personal",
    "REL": "Religión",
    "ESO": "Esoterismo y espiritualidad alternativa",
    "HIS": "Historia",
    "SOC": "Política, sociedad y economía",
    "BIO": "Biografías y memorias",
    "CIE": "Ciencias y medicina",
    "SAL": "Salud y vida familiar",
    "ART": "Arte, música y cine",
    "LEN": "Lengua y diccionarios",
    "VIA": "Viajes y guías",
    "OCI": "Cocina, hogar y ocio",
}
# Solo para libros nuevos que las reglas no pueden ubicar con certeza. Se
# listan en el log del build para revisarlos y pasarlos al archivo manual.
SIN_CLASIFICAR = "Temas varios"

# URLs de la taxonomía anterior -> la categoría que hereda su contenido
# principal. El generador deja en cada una una redirección.
SLUGS_VIEJOS = {
    "ensayo-y-no-ficcion": "ensayo-y-critica-literaria",
    "espiritualidad-y-religion": "religion",
    "historia-y-politica": "historia",
    "infantil-y-juvenil": "infantil",
    "mitologia-y-clasicos": "mitologia-y-epica-clasica",
    "psicologia-y-autoayuda": "psicologia-y-psicoanalisis",
}

RUTA_MANUAL = os.path.join(os.path.dirname(__file__), "clasificacion_manual.tsv")


def normalizar(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def clave(titulo, autor):
    return f"{normalizar(titulo)}|{normalizar(autor)}"


def cargar_manual(ruta=RUTA_MANUAL):
    """{clave: nombre de categoría}. Columnas: clave, código, título, autor."""
    manual = {}
    if not os.path.exists(ruta):
        return manual
    for n, linea in enumerate(open(ruta, encoding="utf-8"), 1):
        if n == 1 or not linea.strip() or linea.startswith("#"):
            continue
        partes = linea.rstrip("\n").split("\t")
        k, cod = partes[0], partes[1].strip()
        if cod not in CATEGORIAS:
            raise ValueError(f"clasificacion_manual.tsv línea {n}: código desconocido {cod!r}")
        manual[k] = CATEGORIAS[cod]
    return manual
