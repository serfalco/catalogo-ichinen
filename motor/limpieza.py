"""
Limpieza y normalización de los datos crudos del Excel de Mercado Libre.
Todo lo que entra sucio acá sale presentable o marcado como "a verificar".
"""
import re
import unicodedata
from unidecode import unidecode

# --- Clasificación por género -------------------------------------------------
# NOTA IMPORTANTE sobre la fuente:
# La columna NARRATION_TYPE del Excel de Mercado Libre casi no tiene información
# de género. El 94 % del catálogo cae en tres valores que describen la FORMA:
#   "Novela" (2785), "Manual" (933) y "Cuento" (524).
# Y "Manual" no son manuales: es el cajón residual de la no ficción — ahí están
# Félix Luna, Fidel Castro, Nietzsche, Fromm, Kandinski, nutrición y biología.
# Por eso el género se deduce combinando autor, editorial, colección y título,
# y NARRATION_TYPE queda solo como desempate final.
#
# Criterio: preferimos precisión antes que cobertura. Ante la duda un libro cae
# en "Narrativa" (si es ficción) u "Otros", que son honestos, en vez de arriesgar
# una categoría equivocada que ensucia la página de esa categoría.

from categorias import SIN_CLASIFICAR


def _norm(s: str) -> str:
    """minúsculas, sin acentos, sin espacios extra — para comparar."""
    s = unidecode((s or "").strip().lower())
    return re.sub(r"\s+", " ", s)


def _tiene(texto, palabras):
    """True si alguna palabra aparece como palabra entera en el texto normalizado."""
    return any(re.search(r"\b" + re.escape(p) + r"\b", texto) for p in palabras)


# Editoriales de historieta. Se listan tokens inequívocos: "norma" y "planeta"
# quedan fuera a propósito porque publican de todo y arrastrarían falsos positivos.
ED_HISTORIETA = ["dc", "marvel", "zinco", "novaro", "vid", "ecc", "vertigo",
                 "image", "dark horse", "panini", "ovni", "forum", "bongo",
                 "columba", "toutain", "deagostini"]

ED_INFANTIL = ["sigmar", "robin hood", "barco de vapor", "altea", "cantaro",
               "del mirador", "estrada", "guadal", "beascoa"]

ED_ESPIRITUAL = ["soka gakkai", "obelisco", "kier", "errepar new age", "dharma"]

# Autores agrupados por el género con el que se los busca. No pretende ser
# exhaustivo: cubre a los que tienen volumen real en este catálogo.
AUTORES_POLICIAL = [
    "agatha christie", "arthur conan doyle", "conan doyle", "patricia highsmith",
    "raymond chandler", "dashiell hammett",
    "ruth rendell", "georges simenon", "edgar allan poe", "james hadley chase",
    "ellery queen", "john dickson carr", "eric ambler", "rex stout",
]
AUTORES_CIFI = [
    "julio verne", "jules verne", "isaac asimov", "ray bradbury", "h g wells",
    "arthur c clarke", "philip k dick", "ursula k le guin", "j r r tolkien",
    "tolkien", "edgard rice burroughs",
    "edgar rice burroughs", "stanislaw lem", "frank herbert", "michael ende",
]
AUTORES_FILOSOFIA = [
    "friedrich nietzsche", "nietzsche", "aristoteles", "platon", "seneca",
    "immanuel kant", "kant", "hegel", "schopenhauer", "jean paul sartre",
    "sartre", "michel foucault", "foucault", "jose ingenieros",
    "baruch spinoza", "spinoza", "confucio", "marco aurelio", "epicteto",
    "soren kierkegaard", "bertrand russell",
]
AUTORES_HISTORIA = [
    "felix luna", "felipe pigna", "jose maria rosa", "tulio halperin donghi",
    "norberto galasso", "marcos aguinis", "maria saenz quesada", "eric hobsbawm",
    "fidel castro", "ernesto che guevara", "che guevara", "arturo jauretche",
    "rodolfo walsh", "osvaldo bayer",
]
AUTORES_TEATRO = [
    "william shakespeare", "shakespeare", "florencio sanchez", "moliere",
    "federico garcia lorca", "roberto cossa", "henrik ibsen", "anton chejov",
    "bertolt brecht", "sofocles", "esquilo", "euripides", "aristofanes",
]
AUTORES_POESIA = [
    "pablo neruda", "federico garcia lorca", "antonio machado", "ruben dario",
    "alfonsina storni", "walt whitman", "charles baudelaire", "rimbaud",
    "jose hernandez", "olegario victor andrade", "gustavo adolfo becquer",
]
# Clásicos de dominio público: es la subcategoría con demanda de búsqueda más
# clara dentro de la narrativa general ("clásicos de la literatura usados").
AUTORES_CLASICOS = [
    "oscar wilde", "mark twain", "robert louis stevenson", "charles dickens",
    "louisa may alcott", "henry james", "franz kafka", "jane austen",
    "honore de balzac", "fiodor dostoievski", "dostoievski", "leon tolstoi",
    "tolstoi", "victor hugo", "alejandro dumas", "alexandre dumas",
    "emily bronte", "charlotte bronte", "gustave flaubert", "herman melville",
    "daniel defoe", "jonathan swift", "miguel de cervantes", "cervantes",
    "anton chejov", "guy de maupassant", "nathaniel hawthorne", "joseph conrad",
]
AUTORES_THRILLER = [
    "sidney sheldon", "morris west", "wilbur smith", "frederick forsyth",
    "ken follett", "robin cook", "michael crichton", "tom clancy",
    "john grisham", "dean koontz", "clive cussler", "john le carre", "mary higgins clark",
]
AUTORES_ROMANTICA = [
    "danielle steel", "victoria holt", "guy des cars", "corin tellado",
    "barbara cartland", "nora roberts", "rosamunde pilcher", "johanna lindsey",
]
AUTORES_HISTORICA = [
    "valerio massimo manfredi", "manfredi", "robert graves", "marguerite yourcenar",
    "gore vidal", "colleen mccullough", "noah gordon", "arturo perez reverte",
]
# Autores mal clasificados por la columna del Excel: son dramaturgos, poetas
# o autores infantiles cuyos libros venían marcados como "Novela".
AUTORES_TEATRO_EXTRA = ["gregorio de laferrere", "laferrere", "alejandro casona",
                        "armando discepolo", "roberto arlt teatro", "samuel beckett"]
AUTORES_TERROR = ["stephen king", "h p lovecraft", "lovecraft", "anne rice",
                  "v c andrews", "r l stine", "william peter blatty", "bram stoker"]
AUTORES_PSICOLOGIA = ["sigmund freud", "freud", "jacques lacan", "lacan", "carl jung",
                      "melanie klein", "jean piaget", "piaget", "donald winnicott",
                      "erich fromm", "jose bleger", "anna freud", "maud mannoni"]
AUTORES_AUTOAYUDA = ["jorge bucay", "bernardo stamateas", "louise hay", "wayne dyer",
                     "og mandino", "napoleon hill", "dale carnegie", "brian tracy",
                     "john gray", "walter riso", "deepak chopra", "osho",
                     "anthony de mello", "leo buscaglia", "spencer johnson"]
AUTORES_INFANTIL = ["luis pescetti", "maria elena walsh", "graciela montes",
                    "elsa bornemann", "roald dahl", "gustavo roldan",
                    "ema wolf", "silvia schujer", "liliana bodoc"]

# Palabras del título. Se aplican después de autor y editorial, y solo a la
# no ficción. Psicología (disciplina, Thema JM / CDU 159.9) y autoayuda
# (divulgación y desarrollo personal, Thema VS) son materias distintas y van
# separadas; lo mismo religión (QR / CDU 2) y esoterismo (VX / CDU 133).
TIT_DICCIONARIO = ["diccionario", "enciclopedia", "gramatica", "vocabulario", "ortografia"]
TIT_HISTORIA = ["historia", "guerra", "revolucion", "malvinas", "dictadura",
                "independencia", "imperio", "batallas", "conquista"]
TIT_POLITICA = ["politica", "politico", "geopolitica", "peron", "peronismo",
                "economia", "economico", "finanzas", "mercado", "empresa",
                "management", "productividad", "marketing", "negocios",
                "sociologia", "sociedad", "capitalismo", "socialismo", "estado"]
TIT_PSICOLOGIA = ["psicologia", "psicoanalisis", "psiquiatria", "freud", "lacan",
                  "jung", "neurosis", "psicoterapia"]
TIT_AUTOAYUDA = ["autoestima", "autoayuda", "exito", "felicidad", "feliz",
                 "inteligencia emocional", "superacion", "pensamiento positivo",
                 "ansiedad", "depresion", "emociones", "liderazgo", "lider"]
TIT_RELIGION = ["budismo", "buda", "biblia", "jesus", "cristo", "evangelio",
                "evangelios", "dios", "oracion", "islam", "coran", "iglesia",
                "catolicismo", "judaismo", "teologia", "zen"]
TIT_ESOTERISMO = ["tarot", "astrologia", "angeles", "reiki", "karma", "numerologia",
                  "metafisica", "feng shui", "chakras", "esoterismo", "esoterico",
                  "ocultismo", "ovnis", "reencarnacion", "meditacion", "yoga"]
TIT_SALUD = ["nutricion", "salud", "dieta", "adelgazar", "embarazo", "bebe",
             "crianza", "sexualidad", "celulitis"]
TIT_CIENCIA = ["biologia", "fisica", "quimica", "matematica", "matematicas",
               "anatomia", "fisiologia", "medicina", "astronomia", "genetica",
               "ecologia", "cosmos", "evolucion", "relatividad"]
TIT_ARTE = ["arte", "pintura", "pintor", "musica", "cine", "fotografia",
            "arquitectura", "escultura", "tango", "opera", "danza"]
TIT_COCINA = ["cocina", "recetas", "reposteria", "vinos", "gastronomia",
              "jardineria", "ajedrez", "manualidades", "tejido"]
TIT_VIAJE = ["guia de", "guia turistica", "guia verde", "lonely planet"]
TIT_INFANTIL = ["cuentos infantiles", "para chicos", "para ninos"]

# Valores de NARRATION_TYPE que sí son confiables cuando aparecen. "Ensayo"
# no está: Mercado Libre lo usa para cualquier no ficción y no nombra materia.
TIPO_DIRECTO = {
    "poesia": "Poesía", "aforismos": "Poesía", "cancionero": "Poesía",
    "teatro": "Teatro", "dialogo": "Teatro",
    "filosofia": "Filosofía y pensamiento",
    "ensayo politico": "Política, sociedad y economía",
    "capitalismo": "Política, sociedad y economía",
    "historia": "Historia",
    "psicologia": "Psicología y psicoanálisis",
    "autoayuda": "Autoayuda y desarrollo personal",
    "esoterismo": "Esoterismo y espiritualidad alternativa",
    "arte": "Arte, música y cine", "pintura / arte": "Arte, música y cine",
    "tango": "Arte, música y cine",
    "mitologia": "Mitología y épica clásica",
    "literatura clasica griega": "Mitología y épica clásica",
    "textos antiguos,clasicos y medievales": "Mitología y épica clásica",
    "diccionario": "Lengua y diccionarios",
    "matematicas": "Ciencias y medicina",
    "biografia": "Biografías y memorias",
    "biografias y relatos": "Biografías y memorias",
    "jovenes lectores": "Juvenil",
    "literatura juvenil": "Juvenil",
    "fabula": "Infantil",
}

FICCION = {"novela", "novelas", "cuento", "cuentos", "narrativa", "ficcion",
           "libros de ficcion", "literatura universal", "clasicos", "escrito",
           "escrita", "obra", "libro"}


# Temas que devuelven Open Library y Google Books, mapeados a nuestras categorías.
# Se comparan como subcadena sobre el tema normalizado. El orden importa: el
# primero que matchea gana, así que van de más específico a más general.
# Los temas genéricos ("fiction", "literature", "general") se ignoran a propósito:
# no dicen nada y arrastrarían medio catálogo a una categoría equivocada.
TEMAS_MAPA = [
    ("comic", "Historieta y cómic"), ("graphic novel", "Historieta y cómic"),
    ("cartoons", "Historieta y cómic"), ("superhero", "Historieta y cómic"),
    ("detective", "Policial y misterio"), ("mystery", "Policial y misterio"),
    ("crime", "Policial y misterio"), ("policial", "Policial y misterio"),
    ("suspense", "Thriller y suspenso"), ("thriller", "Thriller y suspenso"),
    ("espionage", "Thriller y suspenso"), ("spy stories", "Thriller y suspenso"),
    ("horror", "Terror"), ("ghost stories", "Terror"),
    ("science fiction", "Ciencia ficción y fantasía"), ("fantasy", "Ciencia ficción y fantasía"),
    ("ciencia ficcion", "Ciencia ficción y fantasía"),
    ("romance", "Novela romántica"), ("love stories", "Novela romántica"),
    ("historical fiction", "Novela histórica"),
    ("young adult", "Juvenil"), ("juvenile", "Infantil"), ("children", "Infantil"),
    ("picture books", "Infantil"), ("infantil", "Infantil"),
    ("humor", "Humor"),
    ("poetry", "Poesía"), ("poesia", "Poesía"),
    ("drama", "Teatro"), ("plays", "Teatro"), ("theater", "Teatro"), ("teatro", "Teatro"),
    ("literary criticism", "Ensayo y crítica literaria"),
    ("philosophy", "Filosofía y pensamiento"), ("filosofia", "Filosofía y pensamiento"),
    ("ethics", "Filosofía y pensamiento"), ("logic", "Filosofía y pensamiento"),
    ("self-help", "Autoayuda y desarrollo personal"),
    ("psychoanalysis", "Psicología y psicoanálisis"),
    ("psychology", "Psicología y psicoanálisis"), ("psicologia", "Psicología y psicoanálisis"),
    ("occult", "Esoterismo y espiritualidad alternativa"),
    ("new age", "Esoterismo y espiritualidad alternativa"),
    ("astrology", "Esoterismo y espiritualidad alternativa"),
    ("religion", "Religión"), ("buddhism", "Religión"), ("bible", "Religión"),
    ("christian", "Religión"),
    ("mythology", "Mitología y épica clásica"),
    ("biography", "Biografías y memorias"), ("autobiography", "Biografías y memorias"),
    ("history", "Historia"), ("historia", "Historia"),
    ("political", "Política, sociedad y economía"), ("politics", "Política, sociedad y economía"),
    ("business", "Política, sociedad y economía"), ("economics", "Política, sociedad y economía"),
    ("social science", "Política, sociedad y economía"),
    ("health", "Salud y vida familiar"), ("family", "Salud y vida familiar"),
    ("medical", "Ciencias y medicina"), ("science", "Ciencias y medicina"),
    ("cooking", "Cocina, hogar y ocio"), ("games", "Cocina, hogar y ocio"),
    ("travel", "Viajes y guías"),
    ("language", "Lengua y diccionarios"), ("dictionaries", "Lengua y diccionarios"),
    ("art", "Arte, música y cine"), ("music", "Arte, música y cine"),
    ("film", "Arte, música y cine"),
]
TEMAS_IGNORADOS = {"fiction", "literature", "general", "spanish", "espanol",
                   "argentina", "books", "readers", "translations", "classics"}


def _por_temas(temas):
    """Devuelve la categoría sugerida por los temas de la API, o None."""
    for t in (temas or []):
        tn = _norm(t)
        if not tn or tn in TEMAS_IGNORADOS:
            continue
        for clave, categoria in TEMAS_MAPA:
            if clave in tn:
                return categoria
    return None


def clasificar(tipo_narracion: str, titulo: str = "", autor: str = "",
               editorial: str = "", coleccion: str = "", temas=None) -> str:
    """
    Reglas para los libros que todavía no están en clasificacion_manual.tsv
    (stock nuevo). El archivo manual, revisado libro por libro, tiene prioridad
    sobre todo esto (ver lector.py). El orden importa: las señales más
    confiables se evalúan primero.
    """
    t   = _norm(tipo_narracion)
    tit = _norm(titulo)
    au  = _norm(autor)
    ed  = _norm(editorial)
    col = _norm(coleccion)

    # 1) Editorial — la señal más fuerte y menos ambigua.
    if _tiene(ed, ED_HISTORIETA):
        return "Historieta y cómic"
    if _tiene(ed, ED_INFANTIL) or _tiene(col, ["barco de vapor"]):
        return "Infantil"
    if _tiene(ed, ["soka gakkai", "dharma"]) or _tiene(col, ["budismo"]):
        return "Religión"
    if _tiene(ed, ["kier", "obelisco", "errepar new age"]):
        return "Esoterismo y espiritualidad alternativa"

    # 2) Autor — para los que tienen volumen real en el catálogo.
    if _tiene(au, AUTORES_POLICIAL):  return "Policial y misterio"
    if _tiene(au, AUTORES_TERROR):    return "Terror"
    if _tiene(au, AUTORES_CIFI):      return "Ciencia ficción y fantasía"
    if _tiene(au, AUTORES_THRILLER):  return "Thriller y suspenso"
    if _tiene(au, AUTORES_ROMANTICA): return "Novela romántica"
    if _tiene(au, AUTORES_HISTORICA): return "Novela histórica"
    if _tiene(au, AUTORES_INFANTIL):  return "Infantil"
    if _tiene(au, AUTORES_PSICOLOGIA): return "Psicología y psicoanálisis"
    if _tiene(au, AUTORES_AUTOAYUDA): return "Autoayuda y desarrollo personal"
    if _tiene(au, AUTORES_TEATRO_EXTRA): return "Teatro"
    if _tiene(au, AUTORES_CLASICOS):  return "Clásicos de la literatura"
    if _tiene(au, AUTORES_TEATRO) and t not in ("poesia",): return "Teatro"
    if _tiene(au, AUTORES_POESIA) and t in ("poesia", "aforismos", "cancionero"):
        return "Poesía"
    if _tiene(au, AUTORES_FILOSOFIA): return "Filosofía y pensamiento"
    if _tiene(au, AUTORES_HISTORIA):  return "Historia"

    # 3) Temas que devolvió la API por ISBN. Van después de las listas curadas
    #    de autores (que son más precisas) y antes de todo lo demás.
    por_tema = _por_temas(temas)
    if por_tema:
        return por_tema

    # 4) Colección, cuando dice algo real.
    if _tiene(col, ["pensadores universales", "aprender a pensar"]):
        return "Filosofía y pensamiento"
    if _tiene(col, ["mitologia", "mitologia novelada", "grecia y roma"]):
        return "Mitología y épica clásica"
    if _tiene(col, ["septimo circulo"]):
        return "Policial y misterio"
    if _tiene(col, ["hombres y mujeres que hicieron"]):
        return "Biografías y memorias"

    # 5) Tipo de narración, solo los valores que sí informan.
    if t in TIPO_DIRECTO:
        return TIPO_DIRECTO[t]

    # 6) Título — última red, y solo para la no ficción, donde el título
    #    suele nombrar la materia. En ficción el título no dice el género.
    if t not in FICCION:
        if _tiene(tit, TIT_DICCIONARIO): return "Lengua y diccionarios"
        if _tiene(tit, TIT_VIAJE):       return "Viajes y guías"
        if _tiene(tit, TIT_PSICOLOGIA):  return "Psicología y psicoanálisis"
        if _tiene(tit, TIT_ESOTERISMO):  return "Esoterismo y espiritualidad alternativa"
        if _tiene(tit, TIT_RELIGION):    return "Religión"
        if _tiene(tit, TIT_AUTOAYUDA):   return "Autoayuda y desarrollo personal"
        if _tiene(tit, TIT_COCINA):      return "Cocina, hogar y ocio"
        if _tiene(tit, TIT_SALUD):       return "Salud y vida familiar"
        if _tiene(tit, TIT_CIENCIA):     return "Ciencias y medicina"
        if _tiene(tit, TIT_ARTE):        return "Arte, música y cine"
        if _tiene(tit, TIT_POLITICA):    return "Política, sociedad y economía"
        if _tiene(tit, TIT_HISTORIA):    return "Historia"
        if _tiene(tit, TIT_INFANTIL):    return "Infantil"
        # No ficción sin materia identificable: no se inventa una. Queda
        # para revisión manual (el build la lista).
        return SIN_CLASIFICAR

    # 7) Ficción sin género identificable.
    return "Narrativa"

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
    # El Excel trae dobles espacios ("DC /  Zinco"), que se ven feos en el
    # <title> y en la ficha. Se colapsan acá, una sola vez, para todo el sitio.
    e = re.sub(r"\s+", " ", e)
    e = re.sub(r"\s*/\s*", " / ", e)
    if not e:
        return ""
    letras = re.sub(r"[^a-zA-ZáéíóúñÁÉÍÓÚÑ]", "", e)
    if letras and (letras.isupper() or letras.islower()):
        e = _title_es(e)
    return e

def _dv_isbn13(doce: str) -> str:
    """Dígito verificador de un ISBN-13 a partir de sus primeros 12 dígitos."""
    suma = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(doce))
    return str((10 - suma % 10) % 10)


def _isbn10_correcto(d: str) -> bool:
    """Valida el dígito verificador de un ISBN-10 (el último puede ser X)."""
    if len(d) != 10:
        return False
    total = 0
    for i, c in enumerate(d[:9]):
        if not c.isdigit():
            return False
        total += (10 - i) * int(c)
    ultimo = d[9].upper()
    if ultimo == "X":
        total += 10
    elif ultimo.isdigit():
        total += int(ultimo)
    else:
        return False
    return total % 11 == 0


def isbn_valido(g: str) -> str:
    """Devuelve ISBN-13 si parece válido, sino ''. Para buscar tapas.

    El Excel de Mercado Libre trae el GTIN en tres formas: ISBN-13 tal cual,
    ISBN-10 (los libros anteriores a 2007, que en una librería de usados son
    muchos) y cualquiera de los dos con ceros a la izquierda que agrega Excel
    al tratar la celda como número. Las tres se aceptan; el ISBN-10 se convierte
    a 13 validando antes su dígito verificador, para no inventar códigos.

    Lo que NO es ISBN se sigue descartando: códigos 977 (publicaciones
    periódicas), códigos internos de barras y celdas en cero.
    """
    d = re.sub(r"[^0-9Xx]", "", (g or ""))

    # Ceros de relleno de Excel: solo se quitan si dejan un código de largo útil.
    if len(d) > 13:
        sin_ceros = d.lstrip("0")
        if len(sin_ceros) in (10, 13):
            d = sin_ceros
    if len(d) > 10:
        sin_ceros = d.lstrip("0")
        if len(sin_ceros) == 10:
            d = sin_ceros

    if len(d) == 13 and d.startswith(("978", "979")):
        return d
    if len(d) == 10 and _isbn10_correcto(d):
        base = "978" + d[:9]
        return base + _dv_isbn13(base)
    return ""

# --- Slug para URL ------------------------------------------------------------

def slugify(texto: str) -> str:
    s = unidecode((texto or "").lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "libro"
