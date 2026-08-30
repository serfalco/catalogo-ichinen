"""
Lee el Excel de Mercado Libre y devuelve una lista de libros limpios,
clasificados, con slug único. Ningún libro con título se descarta.
"""
import pandas as pd
from limpieza import (
    clasificar, limpiar_titulo, limpiar_autor, limpiar_anio,
    limpiar_editorial, isbn_valido, slugify,
)

def _celda(row, col):
    v = row.get(col)
    return "" if pd.isna(v) else str(v).strip()

def leer_excel(path: str):
    df = pd.read_excel(path, sheet_name="Libros", header=None)
    # localizar la fila de encabezados reales
    hdr = None
    for i in range(len(df)):
        if str(df.iloc[i, 0]).strip() == "VARIATION_ID":
            hdr = i
            break
    if hdr is None:
        raise ValueError("No se encontró la fila de encabezados (VARIATION_ID).")
    cols = df.iloc[hdr].tolist()
    # Saltar las filas de cabecera: FIXED/ATTRIBUTE, vacía, y la de ayuda en español.
    # Detectar la primera fila de datos reales (la de ayuda contiene "Si tienes variantes").
    inicio = hdr + 1
    for i in range(hdr + 1, min(hdr + 8, len(df))):
        celda = str(df.iloc[i, 6])  # columna BOOK_TITLE
        if "Si tienes variantes" in celda or celda.strip() in ("nan", "Características del producto"):
            inicio = i + 1
        elif str(df.iloc[i, 0]).strip() in ("FIXED", "nan"):
            inicio = i + 1
    data = df.iloc[inicio:].copy()
    data.columns = cols

    libros = []
    slugs_usados = {}
    for _, r in data.iterrows():
        titulo_raw = _celda(r, "BOOK_TITLE")
        if not titulo_raw:
            continue  # sin título no hay libro
        titulo = limpiar_titulo(titulo_raw)
        autor, autor_ok = limpiar_autor(_celda(r, "AUTHOR"))
        anio = limpiar_anio(_celda(r, "PUBLICATION_YEAR"))
        editorial = limpiar_editorial(_celda(r, "BOOK_PUBLISHER"))
        # El autor crudo se conserva aunque no sea publicable: aun cuando no
        # sirva para mostrar, puede llevar señal de género para clasificar.
        autor_raw = autor if autor_ok else _celda(r, "AUTHOR")
        categoria = clasificar(
            _celda(r, "NARRATION_TYPE"),
            titulo=titulo,
            autor=autor_raw,
            editorial=_celda(r, "BOOK_PUBLISHER"),
            coleccion=_celda(r, "BOOK_COLLECTION"),
        )
        isbn = isbn_valido(_celda(r, "GTIN"))

        # slug único (si se repite, sufijo incremental)
        base = slugify(f"{titulo}-{autor if autor_ok else ''}")
        slug = base
        n = slugs_usados.get(base, 0)
        if n:
            slug = f"{base}-{n+1}"
        slugs_usados[base] = n + 1

        faltantes = []
        if not anio: faltantes.append("año")
        if not editorial: faltantes.append("editorial")
        if not autor_ok: faltantes.append("autor")

        libros.append({
            "titulo": titulo,
            "autor": autor,
            "autor_ok": autor_ok,
            "editorial": editorial,
            "anio": anio,
            "categoria": categoria,
            "isbn": isbn,
            "slug": slug,
            "tapa": _celda(r, "BOOK_COVER"),
            "paginas": _celda(r, "PAGES_NUMBER"),
            "coleccion": _celda(r, "BOOK_COLLECTION"),
            "faltantes": faltantes,
            # Campos crudos guardados para poder reclasificar después del
            # enriquecimiento, cuando aparecen los temas que devuelve la API.
            "_tipo": _celda(r, "NARRATION_TYPE"),
            "_autor_raw": autor_raw,
            "temas": [],
        })

    _fusionar_categorias_chicas(libros)
    return libros


def reclasificar(libros):
    """
    Vuelve a clasificar después del enriquecimiento. Se llama desde build.py,
    una vez que los temas de la API están cargados en cada libro.
    Devuelve cuántos libros cambiaron de categoría.
    """
    # Se compara contra el estado final, después de fusionar las categorías
    # chicas. Si se contara dentro del bucle se registrarían idas y vueltas que
    # la fusión cancela, y el número del log sería más alto que los cambios reales.
    antes = [l["categoria"] for l in libros]
    for l in libros:
        l["categoria"] = clasificar(
            l["_tipo"],
            titulo=l["titulo"],
            autor=l["autor"] if l["autor_ok"] else l.get("_autor_raw", ""),
            editorial=l["editorial"],
            coleccion=l["coleccion"],
            temas=l.get("temas"),
        )
    _fusionar_categorias_chicas(libros)
    return sum(1 for a, l in zip(antes, libros) if a != l["categoria"])


# Una categoría con muy pocos libros genera una página flaca, que es justo lo
# que estamos tratando de evitar. Las que no llegan al mínimo se absorben en
# su categoría madre. El umbral es el tamaño mínimo para que una página de
# listado tenga sentido para el visitante y para Google.
MIN_POR_CATEGORIA = 20
CATEGORIA_MADRE = {
    "Cocina y hogar":           "Ensayo y no ficción",
    "Biografías y testimonios": "Ensayo y no ficción",
    "Diccionarios y consulta":  "Ensayo y no ficción",
    "Ciencia y salud":          "Ensayo y no ficción",
    "Economía y sociedad":      "Ensayo y no ficción",
    "Psicología y autoayuda":   "Ensayo y no ficción",
    "Arte y música":            "Ensayo y no ficción",
    "Mitología y clásicos":     "Clásicos de la literatura",
    "Novela histórica":         "Narrativa",
    "Novela romántica":         "Narrativa",
    "Thriller y suspenso":      "Narrativa",
    "Ciencia ficción y fantasía": "Narrativa",
    "Policial y misterio":      "Narrativa",
    "Clásicos de la literatura": "Narrativa",
    "Infantil y juvenil":       "Narrativa",
    "Espiritualidad y religión": "Ensayo y no ficción",
    "Historia y política":      "Ensayo y no ficción",
    "Filosofía y pensamiento":  "Ensayo y no ficción",
    "Poesía":                   "Narrativa",
    "Teatro":                   "Narrativa",
}


def _fusionar_categorias_chicas(libros):
    from collections import Counter
    for _ in range(5):  # puede hacer falta más de una pasada en cascada
        cuenta = Counter(l["categoria"] for l in libros)
        chicas = {c for c, n in cuenta.items()
                  if n < MIN_POR_CATEGORIA and c in CATEGORIA_MADRE}
        if not chicas:
            break
        for l in libros:
            if l["categoria"] in chicas:
                l["categoria"] = CATEGORIA_MADRE[l["categoria"]]

if __name__ == "__main__":
    import sys, json
    libros = leer_excel(sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/listado.xlsx")
    from collections import Counter
    print(f"Total libros: {len(libros)}")
    print("Por categoría:", dict(Counter(l["categoria"] for l in libros).most_common()))
    print("Con ISBN válido (buscable tapa):", sum(1 for l in libros if l["isbn"]))
    print("Autor a verificar:", sum(1 for l in libros if not l["autor_ok"]))
    print("\nEjemplos:")
    for l in libros[:3]:
        print(" ", l["titulo"], "·", l["autor"], "·", l["categoria"], "·", l["slug"])
