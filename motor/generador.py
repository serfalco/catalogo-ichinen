"""
Genera el sitio estático del catálogo a partir de la lista de libros limpia.
Produce:
  - index.html              (grilla con buscador; las primeras 48 fichas van en el HTML)
  - libro/<slug>.html       (una página por libro)
  - categoria/<slug>/       (listados paginados por categoría, con enlaces reales)
  - autor/<slug>/           (una página por autor con 3 libros o más)
  - datos.json              (datos para el buscador del navegador)
  - sitemap.xml             (índice) + sitemap-libros.xml + sitemap-listas.xml
  - robots.txt, css/, js/, ph/, CNAME

Criterio de indexación (importante):
  Google no debe recibir 4.558 fichas de calidad despareja. Se marcan como
  `noindex, follow` —y se excluyen del sitemap— las fichas cuyo dato principal
  no es confiable (autor sin verificar). Siguen visibles y buscables para el
  visitante; simplemente no se ofrecen al índice. Es reversible: cuando el dato
  se corrige, la ficha vuelve a entrar sola en la próxima corrida.
"""
import os, json, html, shutil
from datetime import date
from urllib.parse import quote

WA_NUMERO = "5491159952089"  # WhatsApp de la librería (+54 9 11 5995-2089)
DOMINIO = "https://catalogo.ichinen.com.ar"
SITIO_HOME = "https://ichinen.com.ar"
ID_LIBRERIA = f"{SITIO_HOME}/#libreria"   # el @id del BookStore declarado en la home
OG_FALLBACK = f"{SITIO_HOME}/img/og.jpg"  # para compartir fichas sin tapa real

POR_PAGINA = 48        # tamaño de los listados
MIN_LIBROS_AUTOR = 3   # menos que esto no justifica una página propia
RELACIONADOS = 6       # cuántos libros se enlazan al pie de cada ficha


def esc(s):
    return html.escape(str(s or ""), quote=True)


def wa_link(titulo, autor):
    msg = f"Hola! Me interesa el libro \"{titulo}\""
    if autor and autor != "Autor a verificar":
        msg += f" de {autor}"
    msg += ". ¿Está disponible?"
    return f"https://wa.me/{WA_NUMERO}?text={quote(msg)}"


def indexable(libro):
    """¿Se le ofrece esta ficha a Google? Ver nota de criterio arriba."""
    return bool(libro.get("autor_ok"))


# ---------------------------------------------------------------------------
# Placeholders por categoría: cada una con color de la paleta Ichinén y un
# ornamento tipográfico. Se generan como SVG (peso casi nulo, nítidos siempre).
# (fondo, texto, ornamento)
ESTILO_CATEGORIA = {
    "Literatura":         ("#f3e7e7", "#7a0c10", "✦"),  # ✦
    "Poesía":             ("#e7edf6", "#1b4078", "❧"),  # ❧
    "Teatro":             ("#faf3df", "#8a6a12", "⁘"),  # ⁘
    "Ensayo y Filosofía": ("#eae6dd", "#4a463b", "❖"),  # ❖
    "Arte":               ("#f3e7e7", "#7a0c10", "◈"),  # ◈
    "Referencia":         ("#e7edf6", "#1b4078", "※"),  # ※
    "Otros":              ("#efe9d9", "#5b5648", "❦"),  # ❦
}
DEFAULT_ESTILO = ("#efe9d9", "#5b5648", "❦")


def _slug_cat(categoria):
    from limpieza import slugify
    return slugify(categoria)


def placeholder_svg(categoria):
    """SVG de tapa para una categoría, con su color y ornamento."""
    fondo, color, orn = ESTILO_CATEGORIA.get(categoria, DEFAULT_ESTILO)
    nombre = esc(categoria.upper())
    if len(categoria) > 12 and " " in categoria:
        partes = categoria.upper().split(" ")
        mitad = len(partes) // 2 + len(partes) % 2
        l1 = esc(" ".join(partes[:mitad]))
        l2 = esc(" ".join(partes[mitad:]))
        texto = (f'<text x="100" y="205" text-anchor="middle" font-family="Cinzel,serif" font-size="15" '
                 f'letter-spacing="2" fill="{color}">{l1}</text>'
                 f'<text x="100" y="228" text-anchor="middle" font-family="Cinzel,serif" font-size="15" '
                 f'letter-spacing="2" fill="{color}">{l2}</text>')
    else:
        texto = (f'<text x="100" y="215" text-anchor="middle" font-family="Cinzel,serif" font-size="16" '
                 f'letter-spacing="2" fill="{color}">{nombre}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300" preserveAspectRatio="xMidYMid slice">
<rect width="200" height="300" fill="{fondo}"/>
<rect x="0" y="0" width="66.66" height="4" fill="#2459A8"/>
<rect x="66.66" y="0" width="66.66" height="4" fill="#E0B52B"/>
<rect x="133.32" y="0" width="66.68" height="4" fill="#B31217"/>
<text x="100" y="150" text-anchor="middle" font-family="Cinzel,serif" font-size="40" fill="{color}" opacity="0.55">{orn}</text>
{texto}
</svg>'''


# ---------------------------------------------------------------------------
CSS = """
:root{
  --bordo:#B31217;--bordo-osc:#7a0c10;--azul:#2459A8;--amarillo:#E0B52B;
  --papel:#F6F2E8;--papel2:#efe9d9;--tinta:#222;--suave:#5b5648;--linea:#d8cfb8;--max:1140px;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;background:var(--papel);color:var(--tinta);
  font-family:'Lora',Georgia,serif;font-size:18px;line-height:1.6;}
img{max-width:100%;display:block;}
a{color:var(--bordo);text-decoration:none;}
a:hover{text-decoration:underline;}
h1,h2,h3{font-family:'Cinzel',serif;line-height:1.2;margin:0 0 .4em;font-weight:600;}
.wrap{max-width:var(--max);margin:0 auto;padding:0 22px;}
.tricolor{height:4px;border:0;margin:0;background:linear-gradient(90deg,
  var(--azul) 0 33.33%,var(--amarillo) 33.33% 66.66%,var(--bordo) 66.66% 100%);}

/* header */
.topbar{position:sticky;top:0;z-index:40;background:rgba(246,242,232,.95);
  backdrop-filter:blur(6px);border-bottom:1px solid var(--linea);}
.topbar .wrap{display:flex;align-items:center;justify-content:space-between;height:62px;gap:16px;}
.brand{font-family:'Cinzel',serif;font-weight:700;color:var(--bordo);font-size:1.05rem;letter-spacing:1px;}
.topbar nav a{color:var(--tinta);font-family:'Cinzel',serif;font-size:.74rem;
  letter-spacing:1px;text-transform:uppercase;margin-left:20px;}
.topbar nav a:hover{color:var(--bordo);text-decoration:none;}

/* migas */
.bc{font-size:.78rem;color:var(--suave);padding:16px 0 0;font-family:'Lora',serif;}
.bc a{color:var(--suave);text-decoration:underline;text-underline-offset:2px;}
.bc a:hover{color:var(--bordo);}
.bc span{margin:0 6px;color:#b3aa93;}

/* buscador */
.buscador{padding:18px 0 10px;}
.buscador h1{font-size:1.7rem;color:var(--bordo);margin-bottom:14px;}
#q{width:100%;padding:13px 16px;border:1.5px solid var(--linea);background:#fff;
  font-family:'Lora',serif;font-size:16px;color:var(--tinta);}
#q:focus{outline:none;border-color:var(--azul);}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 6px;}
.chip{font-family:'Cinzel',serif;font-size:.66rem;letter-spacing:.5px;text-transform:uppercase;
  padding:7px 13px;border:1px solid var(--linea);color:var(--suave);background:#fff;cursor:pointer;}
.chip.on{background:var(--bordo);color:#fff;border-color:var(--bordo);}
.contador{color:var(--suave);font-style:italic;font-size:.9rem;padding:6px 0 0;}

/* grilla */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:18px;padding:22px 0 50px;}
.card{background:#fff;border:1px solid var(--linea);padding:12px;display:flex;flex-direction:column;}
.card:hover{box-shadow:0 8px 20px rgba(34,20,8,.10);}
.cover{aspect-ratio:2/3;width:100%;background:var(--papel2);border:1px solid var(--linea);
  margin-bottom:10px;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;}
.cover img{width:100%;height:100%;object-fit:cover;}
.cover .tc{position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,
  var(--azul) 0 33.33%,var(--amarillo) 33.33% 66.66%,var(--bordo) 66.66% 100%);}
.cat{font-family:'Cinzel',serif;font-size:.55rem;letter-spacing:1px;text-transform:uppercase;color:var(--azul);margin-bottom:4px;}
.t{font-family:'Cinzel',serif;font-size:.84rem;color:var(--tinta);line-height:1.25;margin-bottom:3px;}
.a{font-size:.82rem;color:var(--suave);font-style:italic;margin-bottom:5px;}
.meta{font-size:.72rem;color:#8a8472;margin-bottom:10px;flex-grow:1;}
.verif{display:inline-block;font-size:.6rem;color:#9a7d1e;background:#faf3da;
  border:1px solid #ecd99b;padding:1px 6px;margin-bottom:6px;}
.btn-wa{display:block;text-align:center;font-family:'Cinzel',serif;font-size:.66rem;
  letter-spacing:1px;text-transform:uppercase;padding:10px 6px;background:#1f8a4c;color:#fff;}
.btn-wa:hover{background:#176c3b;text-decoration:none;}
.vacio{text-align:center;color:var(--suave);font-style:italic;padding:50px 0;grid-column:1/-1;}

/* paginación */
.mas{text-align:center;padding:0 0 50px;}
.mas button{font-family:'Cinzel',serif;font-size:.74rem;letter-spacing:1px;text-transform:uppercase;
  padding:13px 30px;border:1.5px solid var(--bordo);background:transparent;color:var(--bordo);cursor:pointer;}
.mas button:hover{background:var(--bordo);color:#fff;}
.pag{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;padding:0 0 50px;align-items:center;}
.pag a,.pag strong{font-family:'Cinzel',serif;font-size:.72rem;letter-spacing:1px;
  padding:9px 14px;border:1px solid var(--linea);background:#fff;color:var(--suave);}
.pag strong{background:var(--bordo);color:#fff;border-color:var(--bordo);}
.pag a:hover{border-color:var(--bordo);color:var(--bordo);text-decoration:none;}

/* hubs de navegación (categorías y autores) */
.hub{padding:6px 0 40px;border-top:1px solid var(--linea);margin-top:10px;}
.hub h2{font-size:1rem;color:var(--bordo);margin:24px 0 12px;}
.hub .lista{display:flex;gap:8px;flex-wrap:wrap;}
.hub .lista a{font-size:.84rem;background:#fff;border:1px solid var(--linea);
  padding:6px 12px;color:var(--suave);}
.hub .lista a:hover{border-color:var(--bordo);color:var(--bordo);text-decoration:none;}
.hub .lista a b{color:var(--tinta);font-weight:600;}
.intro{max-width:70ch;color:var(--suave);margin:0 0 6px;}

/* página de libro */
.libro{display:grid;grid-template-columns:300px 1fr;gap:40px;padding:26px 0 40px;align-items:start;}
.libro .cover{max-width:300px;}
.libro h1{font-size:1.9rem;color:var(--bordo);}
.libro .au{font-size:1.15rem;color:var(--suave);font-style:italic;margin:0 0 20px;}
.ficha{border-top:1px solid var(--linea);margin-top:8px;}
.ficha div{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--linea);font-size:.92rem;}
.ficha .k{font-family:'Cinzel',serif;font-size:.7rem;letter-spacing:1px;text-transform:uppercase;color:var(--azul);}
.cta{margin-top:26px;}
.volver{display:inline-block;margin:24px 0 0;font-family:'Cinzel',serif;font-size:.72rem;
  letter-spacing:1px;text-transform:uppercase;}
.rel{border-top:1px solid var(--linea);padding:26px 0 10px;}
.rel h2{font-size:1rem;color:var(--bordo);}
.rel .grid{padding:14px 0 24px;}

/* footer */
.footer{background:var(--tinta);color:#e9e4d6;padding:36px 0;text-align:center;}
.footer a{color:var(--amarillo);}
.footer .fr{font-family:'Cinzel',serif;color:var(--amarillo);letter-spacing:1px;margin-top:14px;display:block;}

@media(max-width:680px){
  body{font-size:17px;}
  .topbar nav{display:none;}
  .grid{grid-template-columns:1fr 1fr;gap:12px;}
  .libro{grid-template-columns:1fr;gap:24px;}
  .libro .cover{max-width:220px;margin:0 auto;}
}
"""


def _head(titulo, descripcion, canonical, extra="", robots="index,follow,max-image-preview:large",
          og_image=None, og_type="website"):
    img = og_image or OG_FALLBACK
    return f"""<!DOCTYPE html>
<html lang="es-AR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(descripcion)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#B31217">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(descripcion)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="es_AR">
<meta property="og:site_name" content="Librería Ichinén">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/catalogo.css">
{extra}
</head>
<body>
<header class="topbar"><div class="wrap">
  <a class="brand" href="{SITIO_HOME}">LIBRERÍA ICHINÉN</a>
  <nav>
    <a href="{SITIO_HOME}">Inicio</a>
    <a href="/">Catálogo</a>
    <a href="{SITIO_HOME}/#visitanos">Visitanos</a>
  </nav>
</div></header>
<hr class="tricolor">
"""


_FOOTER = f"""
<footer class="footer"><div class="wrap">
  <p>Librería Ichinén · Av. Triunvirato 4015, Local 3 — Villa Urquiza, CABA</p>
  <small><a href="{SITIO_HOME}">ichinen.com.ar</a> · <a href="https://www.instagram.com/ichinen_libreria">Instagram</a> · <a href="https://wa.me/{WA_NUMERO}">WhatsApp</a></small>
  <span class="fr">Cada libro tiene una historia.</span>
</div></footer>
</body></html>"""


def _migas(items):
    """items: [(texto, url|None), ...]. El último va sin enlace."""
    partes = []
    for texto, url in items:
        partes.append(f'<a href="{url}">{esc(texto)}</a>' if url else esc(texto))
    return '<nav class="bc wrap" aria-label="Migas de pan">' + '<span>›</span>'.join(partes) + '</nav>'


def _schema_migas(items):
    elems = []
    for i, (texto, url) in enumerate(items, start=1):
        e = {"@type": "ListItem", "position": i, "name": texto}
        if url:
            e["item"] = url if url.startswith("http") else DOMINIO + url
        elems.append(e)
    return {"@type": "BreadcrumbList", "itemListElement": elems}


def _cover_html(libro, lazy=True):
    lz = ' loading="lazy"' if lazy else ""
    if libro.get("tapa_url"):
        return (f'<div class="cover"><div class="tc"></div>'
                f'<img src="{esc(libro["tapa_url"])}" alt="Tapa de {esc(libro["titulo"])}"{lz}></div>')
    return (f'<div class="cover"><img src="/ph/{_slug_cat(libro["categoria"])}.svg" '
            f'alt="{esc(libro["categoria"])}"{lz}></div>')


def _tarjeta_html(l):
    """Una tarjeta de la grilla, renderizada del lado del servidor."""
    meta = " · ".join([x for x in (l["editorial"], l["anio"]) if x])
    autor = esc(l["autor"]) if l["autor_ok"] else "Autor a verificar"
    verif = '<span class="verif">A verificar</span>' if [f for f in l["faltantes"] if f != "autor"] else ""
    return (f'<article class="card"><a href="/libro/{l["slug"]}.html" style="color:inherit">'
            f'{_cover_html(l)}<div class="cat">{esc(l["categoria"])}</div>{verif}'
            f'<div class="t">{esc(l["titulo"])}</div><div class="a">{autor}</div>'
            f'<div class="meta">{esc(meta)}</div></a>'
            f'<a class="btn-wa" href="{wa_link(l["titulo"], l["autor"])}" target="_blank" rel="noopener">Consultar</a>'
            f'</article>')


# ---------------------------------------------------------------------------
def generar_pagina_libro(libro, autores_idx):
    titulo_seo = f'{libro["titulo"]} — {libro["autor"]} | Librería Ichinén'
    desc = f'{libro["titulo"]}'
    if libro["autor_ok"]:
        desc += f' de {libro["autor"]}'
    if libro["editorial"]:
        desc += f', editorial {libro["editorial"]}'
    desc += '. Libro usado disponible en Librería Ichinén, Villa Urquiza, CABA. Consultá por WhatsApp.'
    canonical = f'{DOMINIO}/libro/{libro["slug"]}.html'
    cat_slug = _slug_cat(libro["categoria"])
    au_slug = autores_idx.get(libro["autor"], {}).get("slug") if libro["autor_ok"] else None

    migas = [("Catálogo", "/"), (libro["categoria"], f"/categoria/{cat_slug}/")]
    if au_slug:
        migas.append((libro["autor"], f"/autor/{au_slug}/"))
    migas.append((libro["titulo"], None))

    # --- Schema: Book + Offer + migas -------------------------------------
    book = {
        "@type": "Book",
        "@id": canonical + "#libro",
        "name": libro["titulo"],
        "url": canonical,
        "bookFormat": "https://schema.org/Paperback",
        "inLanguage": "es",
    }
    if libro["autor_ok"]:
        book["author"] = {"@type": "Person", "name": libro["autor"]}
    if libro["editorial"]:
        book["publisher"] = {"@type": "Organization", "name": libro["editorial"]}
    if libro["anio"]:
        book["datePublished"] = libro["anio"]
    if libro["isbn"]:
        book["isbn"] = libro["isbn"]
    if libro["paginas"] and libro["paginas"].isdigit() and libro["paginas"] != "0":
        book["numberOfPages"] = int(libro["paginas"])
    # Solo declaramos imagen si es la tapa real; el placeholder no describe el libro.
    if libro.get("tapa_url"):
        book["image"] = DOMINIO + libro["tapa_url"]
    # Oferta sin precio: afirma disponibilidad y retiro en el local, que es lo cierto.
    book["offers"] = {
        "@type": "Offer",
        "availability": "https://schema.org/InStock",
        "itemCondition": "https://schema.org/UsedCondition",
        "priceCurrency": "ARS",
        "availableDeliveryMethod": "https://schema.org/OnSitePickup",
        "seller": {"@id": ID_LIBRERIA},
        "areaServed": {"@type": "Place", "name": "Villa Urquiza, Ciudad Autónoma de Buenos Aires"},
        "url": canonical,
    }
    grafo = {"@context": "https://schema.org", "@graph": [book, _schema_migas(migas)]}
    extra = f'<script type="application/ld+json">{json.dumps(grafo, ensure_ascii=False)}</script>'

    # --- Ficha ------------------------------------------------------------
    filas = [("Categoría", libro["categoria"])]
    if libro["editorial"]: filas.append(("Editorial", libro["editorial"]))
    if libro["anio"]: filas.append(("Año", libro["anio"]))
    if libro["paginas"] and libro["paginas"] not in ("0", ""): filas.append(("Páginas", libro["paginas"]))
    if libro["tapa"]: filas.append(("Encuadernación", libro["tapa"]))
    if libro["isbn"]: filas.append(("ISBN", libro["isbn"]))
    ficha = "".join(f'<div><span class="k">{esc(k)}</span><span>{esc(v)}</span></div>' for k, v in filas)

    faltantes_visibles = [f for f in libro["faltantes"] if f != "autor"]
    verif = (f'<p class="verif">Datos a verificar: {esc(", ".join(faltantes_visibles))} · '
             f'consultá y te confirmamos</p>') if faltantes_visibles else ""

    autor_linea = (f'<a href="/autor/{au_slug}/">{esc(libro["autor"])}</a>' if au_slug
                   else (esc(libro["autor"]) if libro["autor_ok"] else "Autor a verificar"))

    # --- Relacionados: enlaces internos reales ----------------------------
    rel_html = ""
    if au_slug:
        otros = [x for x in autores_idx[libro["autor"]]["libros"] if x["slug"] != libro["slug"]][:RELACIONADOS]
        if otros:
            rel_html += (f'<section class="rel wrap"><h2>Más libros de {esc(libro["autor"])}</h2>'
                         f'<div class="grid">{"".join(_tarjeta_html(x) for x in otros)}</div>'
                         f'<p><a href="/autor/{au_slug}/">Ver los '
                         f'{len(autores_idx[libro["autor"]]["libros"])} libros de {esc(libro["autor"])} →</a></p>'
                         f'</section>')
    rel_html += (f'<section class="rel wrap"><p><a href="/categoria/{cat_slug}/">'
                 f'← Ver todo {esc(libro["categoria"])}</a></p></section>')

    og_img = (DOMINIO + libro["tapa_url"]) if libro.get("tapa_url") else None
    robots = ("index,follow,max-image-preview:large" if indexable(libro)
              else "noindex,follow")

    body = f"""{_migas(migas)}
<main class="wrap libro">
  {_cover_html(libro, lazy=False)}
  <div>
    <h1>{esc(libro["titulo"])}</h1>
    <p class="au">{autor_linea}</p>
    {verif}
    <div class="ficha">{ficha}</div>
    <div class="cta"><a class="btn-wa" href="{wa_link(libro["titulo"], libro["autor"])}" target="_blank" rel="noopener" style="display:inline-block;padding:13px 30px;">Consultar por WhatsApp</a></div>
    <a class="volver" href="/">← Volver al catálogo</a>
  </div>
</main>
{rel_html}
"""
    return _head(titulo_seo, desc, canonical, extra, robots=robots,
                 og_image=og_img, og_type="article") + body + _FOOTER


# ---------------------------------------------------------------------------
def generar_pagina_listado(titulo_h1, intro, libros, canonical, migas, titulo_seo, desc,
                           pagina, total_paginas, url_pagina, robots):
    """Listado paginado genérico (sirve para categorías y autores)."""
    tarjetas = "".join(_tarjeta_html(l) for l in libros)

    pag = ""
    if total_paginas > 1:
        partes = []
        if pagina > 1:
            partes.append(f'<a href="{url_pagina(pagina - 1)}" rel="prev">← Anterior</a>')
        for n in range(1, total_paginas + 1):
            # ventana de páginas alrededor de la actual, para no imprimir 71 enlaces
            if n == 1 or n == total_paginas or abs(n - pagina) <= 2:
                partes.append(f'<strong>{n}</strong>' if n == pagina
                              else f'<a href="{url_pagina(n)}">{n}</a>')
            elif abs(n - pagina) == 3:
                partes.append('<span>…</span>')
        if pagina < total_paginas:
            partes.append(f'<a href="{url_pagina(pagina + 1)}" rel="next">Siguiente →</a>')
        pag = f'<nav class="pag wrap" aria-label="Paginación">{"".join(partes)}</nav>'

    schema = {"@context": "https://schema.org",
              "@graph": [_schema_migas(migas),
                         {"@type": "CollectionPage", "name": titulo_h1, "url": canonical,
                          "isPartOf": {"@type": "WebSite", "name": "Catálogo Librería Ichinén",
                                       "url": DOMINIO + "/"}}]}
    extra = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'

    body = f"""{_migas(migas)}
<main class="wrap">
  <section class="buscador">
    <h1>{esc(titulo_h1)}</h1>
    <p class="intro">{intro}</p>
  </section>
  <section class="grid">{tarjetas}</section>
</main>
{pag}
"""
    return _head(titulo_seo, desc, canonical, extra, robots=robots) + body + _FOOTER


def generar_index(libros, categorias, autores_orden):
    titulo = "Catálogo — Librería Ichinén | Libros usados en Villa Urquiza, CABA"
    desc = (f"Explorá {len(libros)} libros usados de Librería Ichinén en Villa Urquiza, CABA. "
            f"Literatura, ensayo, poesía, teatro y más. Buscá por título o autor y consultá por WhatsApp.")
    chips = '<span class="chip on" data-cat="">Todos</span>'
    for c in categorias:
        chips += f'<span class="chip" data-cat="{esc(c)}">{esc(c)}</span>'

    # Las primeras POR_PAGINA fichas van en el HTML: Google las ve sin ejecutar JS.
    primeras = "".join(_tarjeta_html(l) for l in libros[:POR_PAGINA])

    # Hubs: enlaces reales a cada categoría y a los autores con página propia.
    cats_links = "".join(
        f'<a href="/categoria/{_slug_cat(c)}/">{esc(c)} <b>{sum(1 for l in libros if l["categoria"] == c)}</b></a>'
        for c in categorias)
    aut_links = "".join(
        f'<a href="/autor/{d["slug"]}/">{esc(nombre)} <b>{len(d["libros"])}</b></a>'
        for nombre, d in autores_orden[:60])

    schema = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": "Catálogo de libros usados — Librería Ichinén",
              "url": DOMINIO + "/",
              "isPartOf": {"@type": "WebSite", "name": "Catálogo Librería Ichinén", "url": DOMINIO + "/"},
              "about": {"@id": ID_LIBRERIA}}
    extra = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'

    body = f"""
<main class="wrap">
  <section class="buscador">
    <h1>Catálogo de libros</h1>
    <input type="search" id="q" placeholder="Buscar por título o autor…" autocomplete="off">
    <div class="chips">{chips}</div>
    <p class="contador" id="contador">{len(libros)} libros · mostrando {min(POR_PAGINA, len(libros))}</p>
  </section>
  <section class="grid" id="grid">{primeras}</section>
  <div class="mas" id="mas"><button id="btn-mas">Ver más libros</button></div>

  <div class="hub">
    <h2>Explorá por categoría</h2>
    <div class="lista">{cats_links}</div>
    <h2>Autores con más libros en el catálogo</h2>
    <div class="lista">{aut_links}</div>
  </div>
</main>
<script src="/js/catalogo.js" defer></script>
"""
    return _head(titulo, desc, DOMINIO + "/", extra) + body + _FOOTER


JS = """
let LIBROS=[], filtrados=[], mostrados=0, cat="", q="", listo=false;
const PASO=48, PRERENDER=48;
const grid=document.getElementById('grid');
const cont=document.getElementById('contador');
const masWrap=document.getElementById('mas');
const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
function tarjeta(l){
  const cover=l.tapa_url
    ?`<div class="cover"><div class="tc"></div><img src="${l.tapa_url}" alt="Tapa de ${l.t}" loading="lazy"></div>`
    :`<div class="cover"><img src="/ph/${l.cs}.svg" alt="${l.c}" loading="lazy"></div>`;
  const meta=[l.ed,l.an].filter(Boolean).join(' · ');
  const verif=l.v?`<span class="verif">A verificar</span>`:'';
  const au=l.ok?l.a:'Autor a verificar';
  return `<article class="card"><a href="/libro/${l.s}.html" style="color:inherit">
    ${cover}<div class="cat">${l.c}</div>${verif}
    <div class="t">${l.t}</div><div class="a">${au}</div>
    <div class="meta">${meta}</div></a>
    <a class="btn-wa" href="${l.wa}" target="_blank" rel="noopener">Consultar</a></article>`;
}
function aplicar(){
  const nq=norm(q);
  filtrados=LIBROS.filter(l=>{
    if(cat && l.c!==cat) return false;
    if(nq){const h=norm(l.t+' '+l.a);return h.includes(nq);}
    return true;
  });
  mostrados=0; grid.innerHTML='';
  if(!filtrados.length){grid.innerHTML='<p class="vacio">No encontramos libros con esa búsqueda. Probá con otra palabra o consultá por WhatsApp.</p>';cont.textContent='';masWrap.style.display='none';return;}
  render();
}
function render(){
  const lote=filtrados.slice(mostrados,mostrados+PASO);
  grid.insertAdjacentHTML('beforeend',lote.map(tarjeta).join(''));
  mostrados+=lote.length;
  cont.textContent=`${filtrados.length} libros · mostrando ${mostrados}`;
  masWrap.style.display = mostrados<filtrados.length ? 'block':'none';
}
// Las primeras tarjetas ya vienen en el HTML. No las repintamos al cargar:
// se conservan y el JS sigue desde ahí. Solo se rehace la grilla al filtrar.
function continuar(){
  filtrados=LIBROS; mostrados=Math.min(PRERENDER,LIBROS.length);
  cont.textContent=`${LIBROS.length} libros · mostrando ${mostrados}`;
  masWrap.style.display = mostrados<LIBROS.length ? 'block':'none';
  listo=true;
}
document.getElementById('btn-mas').onclick=()=>{ if(listo) render(); };
document.getElementById('q').addEventListener('input',e=>{ if(!listo) return; q=e.target.value; aplicar(); });
document.querySelectorAll('.chip').forEach(ch=>ch.onclick=()=>{
  if(!listo) return;
  document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));
  ch.classList.add('on'); cat=ch.dataset.cat; aplicar();
});
fetch('/datos.json').then(r=>r.json()).then(d=>{LIBROS=d;continuar();});
"""


# ---------------------------------------------------------------------------
def _indice_autores(libros):
    """Autores con página propia: nombre -> {slug, libros}. Slugs únicos."""
    from limpieza import slugify
    porautor = {}
    for l in libros:
        if l["autor_ok"]:
            porautor.setdefault(l["autor"], []).append(l)
    idx, usados = {}, set()
    # orden estable: más libros primero, después alfabético
    for nombre, ls in sorted(porautor.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(ls) < MIN_LIBROS_AUTOR:
            continue
        base = slugify(nombre) or "autor"
        slug, n = base, 2
        while slug in usados:
            slug, n = f"{base}-{n}", n + 1
        usados.add(slug)
        idx[nombre] = {"slug": slug, "libros": ls}
    return idx


def _paginar(items, tam):
    return [items[i:i + tam] for i in range(0, len(items), tam)] or [[]]


def generar_sitio(libros, salida):
    if os.path.exists(salida):
        shutil.rmtree(salida)
    for sub in ("libro", "css", "js", "ph", "categoria", "autor"):
        os.makedirs(os.path.join(salida, sub))

    categorias = sorted({l["categoria"] for l in libros},
                        key=lambda c: (c == "Otros", c))  # Otros al final
    autores_idx = _indice_autores(libros)
    autores_orden = sorted(autores_idx.items(), key=lambda kv: (-len(kv[1]["libros"]), kv[0]))

    for c in categorias:
        open(os.path.join(salida, "ph", f"{_slug_cat(c)}.svg"), "w").write(placeholder_svg(c))

    open(os.path.join(salida, "css", "catalogo.css"), "w").write(CSS)
    open(os.path.join(salida, "js", "catalogo.js"), "w").write(JS)

    datos = [{
        "t": l["titulo"], "a": l["autor"], "ok": l["autor_ok"],
        "ed": l["editorial"], "an": l["anio"], "c": l["categoria"],
        "s": l["slug"], "v": bool([f for f in l["faltantes"] if f != "autor"]),
        "tapa_url": l.get("tapa_url", ""), "cs": _slug_cat(l["categoria"]),
        "wa": wa_link(l["titulo"], l["autor"]),
    } for l in libros]
    json.dump(datos, open(os.path.join(salida, "datos.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))

    open(os.path.join(salida, "index.html"), "w").write(
        generar_index(libros, categorias, autores_orden))

    for l in libros:
        open(os.path.join(salida, "libro", f'{l["slug"]}.html'), "w").write(
            generar_pagina_libro(l, autores_idx))

    urls_listas = []

    # --- categorías -------------------------------------------------------
    for c in categorias:
        cs = _slug_cat(c)
        ls = [l for l in libros if l["categoria"] == c]
        paginas = _paginar(ls, POR_PAGINA)
        os.makedirs(os.path.join(salida, "categoria", cs), exist_ok=True)
        for i, lote in enumerate(paginas, start=1):
            url = f"/categoria/{cs}/" if i == 1 else f"/categoria/{cs}/{i}.html"
            canonical = DOMINIO + url
            # Solo la página 1 se ofrece al índice; el resto se rastrea pero no se indexa.
            robots = "index,follow,max-image-preview:large" if i == 1 else "noindex,follow"
            suf = "" if i == 1 else f" — página {i}"
            html_pag = generar_pagina_listado(
                titulo_h1=f"{c}{suf}",
                intro=(f"{len(ls)} libros usados de {c.lower()} disponibles en Librería Ichinén, "
                       f"Av. Triunvirato 4015, Villa Urquiza. Consultá disponibilidad por WhatsApp "
                       f"o acercate al local."),
                libros=lote, canonical=canonical,
                migas=[("Catálogo", "/"), (f"{c}{suf}", None)],
                titulo_seo=f"{c} — libros usados{suf} | Librería Ichinén",
                desc=(f"{len(ls)} libros usados de {c.lower()} en Librería Ichinén, Villa Urquiza, CABA. "
                      f"Buscá por título o autor y consultá por WhatsApp."),
                pagina=i, total_paginas=len(paginas),
                url_pagina=lambda n, cs=cs: f"/categoria/{cs}/" if n == 1 else f"/categoria/{cs}/{n}.html",
                robots=robots)
            destino = (os.path.join(salida, "categoria", cs, "index.html") if i == 1
                       else os.path.join(salida, "categoria", cs, f"{i}.html"))
            open(destino, "w").write(html_pag)
            if i == 1:
                urls_listas.append((url, "0.8"))

    # --- autores ----------------------------------------------------------
    for nombre, d in autores_orden:
        ls, slug = d["libros"], d["slug"]
        paginas = _paginar(ls, POR_PAGINA)
        os.makedirs(os.path.join(salida, "autor", slug), exist_ok=True)
        for i, lote in enumerate(paginas, start=1):
            url = f"/autor/{slug}/" if i == 1 else f"/autor/{slug}/{i}.html"
            canonical = DOMINIO + url
            robots = "index,follow,max-image-preview:large" if i == 1 else "noindex,follow"
            suf = "" if i == 1 else f" — página {i}"
            cats = sorted({x["categoria"] for x in ls})
            html_pag = generar_pagina_listado(
                titulo_h1=f"Libros de {nombre}{suf}",
                intro=(f"Tenemos {len(ls)} libros usados de {esc(nombre)} en el local de "
                       f"Av. Triunvirato 4015, Villa Urquiza"
                       f"{' — ' + esc(', '.join(cats)) if cats else ''}. "
                       f"Los títulos y las ediciones cambian seguido: consultá por WhatsApp antes de venir."),
                libros=lote, canonical=canonical,
                migas=[("Catálogo", "/"), (f"{nombre}{suf}", None)],
                titulo_seo=f"{nombre} — {len(ls)} libros usados{suf} | Librería Ichinén",
                desc=(f"{len(ls)} libros usados de {nombre} disponibles en Librería Ichinén, "
                      f"Villa Urquiza, CABA. Consultá disponibilidad por WhatsApp."),
                pagina=i, total_paginas=len(paginas),
                url_pagina=lambda n, slug=slug: f"/autor/{slug}/" if n == 1 else f"/autor/{slug}/{n}.html",
                robots=robots)
            destino = (os.path.join(salida, "autor", slug, "index.html") if i == 1
                       else os.path.join(salida, "autor", slug, f"{i}.html"))
            open(destino, "w").write(html_pag)
            if i == 1:
                urls_listas.append((url, "0.7"))

    # --- sitemaps ---------------------------------------------------------
    hoy = date.today().isoformat()
    NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    NSIMG = 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"'

    filas = [f"<url><loc>{DOMINIO}/</loc><lastmod>{hoy}</lastmod>"
             f"<changefreq>weekly</changefreq><priority>1.0</priority></url>"]
    for url, pri in urls_listas:
        filas.append(f"<url><loc>{DOMINIO}{url}</loc><lastmod>{hoy}</lastmod>"
                     f"<changefreq>weekly</changefreq><priority>{pri}</priority></url>")
    open(os.path.join(salida, "sitemap-listas.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset {NS}>\n' + "\n".join(filas) + "\n</urlset>")

    filas = []
    n_indexables = 0
    for l in libros:
        if not indexable(l):
            continue          # las fichas sin dato confiable no se le ofrecen a Google
        n_indexables += 1
        img = ""
        if l.get("tapa_url"):
            img = (f'<image:image><image:loc>{DOMINIO}{l["tapa_url"]}</image:loc>'
                   f'<image:title>{esc("Tapa de " + l["titulo"])}</image:title></image:image>')
        filas.append(f'<url><loc>{DOMINIO}/libro/{l["slug"]}.html</loc><lastmod>{hoy}</lastmod>'
                     f'<changefreq>monthly</changefreq><priority>0.6</priority>{img}</url>')
    open(os.path.join(salida, "sitemap-libros.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset {NS} {NSIMG}>\n' + "\n".join(filas) + "\n</urlset>")

    indice = (f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex {NS}>\n'
              f'<sitemap><loc>{DOMINIO}/sitemap-listas.xml</loc><lastmod>{hoy}</lastmod></sitemap>\n'
              f'<sitemap><loc>{DOMINIO}/sitemap-libros.xml</loc><lastmod>{hoy}</lastmod></sitemap>\n'
              f'</sitemapindex>')
    open(os.path.join(salida, "sitemap.xml"), "w").write(indice)

    open(os.path.join(salida, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {DOMINIO}/sitemap.xml\n")
    open(os.path.join(salida, "CNAME"), "w").write("catalogo.ichinen.com.ar\n")
    open(os.path.join(salida, ".nojekyll"), "w").write("")

    print(f"  categorías: {len(categorias)} · autores con página: {len(autores_idx)} · "
          f"fichas indexables: {n_indexables} de {len(libros)}")
    return categorias
