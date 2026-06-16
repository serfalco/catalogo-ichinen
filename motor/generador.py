"""
Genera el sitio estático del catálogo a partir de la lista de libros limpia.
Produce:
  - index.html           (grilla con buscador y filtro por categoría)
  - libro/<slug>.html     (una página por libro, para SEO)
  - datos.json            (datos para el buscador del navegador)
  - sitemap.xml           (lista de todas las URLs para Google)
  - robots.txt
  - css/catalogo.css
  - CNAME                 (dominio para GitHub Pages)
"""
import os, json, html, shutil
from datetime import date

WA_NUMERO = "5491159952089"  # WhatsApp de la librería (+54 9 11 5995-2089)
DOMINIO = "https://catalogo.ichinen.com.ar"
SITIO_HOME = "https://ichinen.com.ar"

def esc(s):
    return html.escape(str(s or ""), quote=True)

def wa_link(titulo, autor):
    msg = f"Hola! Me interesa el libro \"{titulo}\""
    if autor and autor != "Autor a verificar":
        msg += f" de {autor}"
    msg += ". ¿Está disponible?"
    from urllib.parse import quote
    return f"https://wa.me/{WA_NUMERO}?text={quote(msg)}"

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

/* buscador */
.buscador{padding:26px 0 10px;}
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
.cover .ph{font-family:'Cinzel',serif;color:#c9bfa3;font-size:.62rem;letter-spacing:1px;text-align:center;padding:0 8px;}
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

/* página de libro */
.libro{display:grid;grid-template-columns:300px 1fr;gap:40px;padding:40px 0 60px;align-items:start;}
.libro .cover{max-width:300px;}
.libro h1{font-size:1.9rem;color:var(--bordo);}
.libro .au{font-size:1.15rem;color:var(--suave);font-style:italic;margin:0 0 20px;}
.ficha{border-top:1px solid var(--linea);margin-top:8px;}
.ficha div{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--linea);font-size:.92rem;}
.ficha .k{font-family:'Cinzel',serif;font-size:.7rem;letter-spacing:1px;text-transform:uppercase;color:var(--azul);}
.cta{margin-top:26px;}
.volver{display:inline-block;margin:24px 0 0;font-family:'Cinzel',serif;font-size:.72rem;
  letter-spacing:1px;text-transform:uppercase;}

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

def _head(titulo, descripcion, canonical, extra=""):
    return f"""<!DOCTYPE html>
<html lang="es-AR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(descripcion)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#B31217">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(descripcion)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_AR">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/catalogo.css">
{extra}
</head>
<body>
<header class="topbar"><div class="wrap">
  <a class="brand" href="/">LIBRERÍA ICHINÉN</a>
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
  <p>Librería Ichinén · Av. Triunvirato 4015, Local 3 — CABA</p>
  <small><a href="{SITIO_HOME}">ichinen.com.ar</a> · <a href="https://www.instagram.com/ichinen_libreria">Instagram</a> · <a href="https://wa.me/{WA_NUMERO}">WhatsApp</a></small>
  <span class="fr">Cada libro tiene una historia.</span>
</div></footer>
</body></html>"""

def _cover_html(libro):
    if libro.get("tapa_url"):
        return f'<div class="cover"><div class="tc"></div><img src="{esc(libro["tapa_url"])}" alt="Tapa de {esc(libro["titulo"])}" loading="lazy"></div>'
    return '<div class="cover"><div class="tc"></div><div class="ph">SIN<br>TAPA</div></div>'

def generar_pagina_libro(libro):
    titulo_seo = f'{libro["titulo"]} — {libro["autor"]} | Librería Ichinén'
    desc = f'{libro["titulo"]}'
    if libro["autor_ok"]:
        desc += f' de {libro["autor"]}'
    if libro["editorial"]:
        desc += f', editorial {libro["editorial"]}'
    desc += '. Libro usado disponible en Librería Ichinén, Villa Urquiza, CABA. Consultá por WhatsApp.'
    canonical = f'{DOMINIO}/libro/{libro["slug"]}.html'

    # Schema.org Book
    schema = {
        "@context": "https://schema.org", "@type": "Book",
        "name": libro["titulo"], "url": canonical,
        "bookFormat": "https://schema.org/Paperback",
        "inLanguage": "es",
    }
    if libro["autor_ok"]:
        schema["author"] = {"@type": "Person", "name": libro["autor"]}
    if libro["editorial"]:
        schema["publisher"] = libro["editorial"]
    if libro["anio"]:
        schema["datePublished"] = libro["anio"]
    if libro["isbn"]:
        schema["isbn"] = libro["isbn"]
    extra = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'

    ficha = ""
    filas = [("Categoría", libro["categoria"])]
    if libro["editorial"]: filas.append(("Editorial", libro["editorial"]))
    if libro["anio"]: filas.append(("Año", libro["anio"]))
    if libro["paginas"] and libro["paginas"] not in ("0", ""): filas.append(("Páginas", libro["paginas"]))
    if libro["tapa"]: filas.append(("Encuadernación", libro["tapa"]))
    if libro["isbn"]: filas.append(("ISBN", libro["isbn"]))
    for k, v in filas:
        ficha += f'<div><span class="k">{esc(k)}</span><span>{esc(v)}</span></div>'

    verif = ""
    # Solo avisar "a verificar" cuando falta info realmente útil para el comprador.
    # Que falte el autor (típico en guías/colecciones) no amerita el cartel.
    faltantes_visibles = [f for f in libro["faltantes"] if f != "autor"]
    if faltantes_visibles:
        verif = f'<p class="verif">Datos a verificar: {esc(", ".join(faltantes_visibles))} · consultá y te confirmamos</p>'

    autor_linea = esc(libro["autor"]) if libro["autor_ok"] else "Autor a verificar"

    body = f"""
<main class="wrap libro">
  {_cover_html(libro)}
  <div>
    <h1>{esc(libro["titulo"])}</h1>
    <p class="au">{autor_linea}</p>
    {verif}
    <div class="ficha">{ficha}</div>
    <div class="cta"><a class="btn-wa" href="{wa_link(libro["titulo"], libro["autor"])}" target="_blank" rel="noopener" style="display:inline-block;padding:13px 30px;">Consultar por WhatsApp</a></div>
    <a class="volver" href="/">← Volver al catálogo</a>
  </div>
</main>
"""
    return _head(titulo_seo, desc, canonical, extra) + body + _FOOTER

def generar_index(libros, categorias):
    titulo = "Catálogo — Librería Ichinén | Libros usados en CABA"
    desc = f"Explorá {len(libros)} libros usados de Librería Ichinén en Villa Urquiza, CABA. Literatura, ensayo, poesía, teatro y más. Buscá por título o autor y consultá por WhatsApp."
    chips = '<span class="chip on" data-cat="">Todos</span>'
    for c in categorias:
        chips += f'<span class="chip" data-cat="{esc(c)}">{esc(c)}</span>'
    body = f"""
<main class="wrap">
  <section class="buscador">
    <h1>Catálogo de libros</h1>
    <input type="search" id="q" placeholder="Buscar por título o autor…" autocomplete="off">
    <div class="chips">{chips}</div>
    <p class="contador" id="contador"></p>
  </section>
  <section class="grid" id="grid"></section>
  <div class="mas" id="mas" style="display:none;"><button id="btn-mas">Ver más libros</button></div>
</main>
<script src="/js/catalogo.js"></script>
"""
    return _head(titulo, desc, DOMINIO + "/") + body + _FOOTER

JS = """
let LIBROS=[], filtrados=[], mostrados=0, cat="", q="";
const PASO=40;
const grid=document.getElementById('grid');
const cont=document.getElementById('contador');
const masWrap=document.getElementById('mas');
const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
function tarjeta(l){
  const cover=l.tapa_url
    ?`<div class="cover"><div class="tc"></div><img src="${l.tapa_url}" alt="Tapa de ${l.t}" loading="lazy"></div>`
    :`<div class="cover"><div class="tc"></div><div class="ph">SIN<br>TAPA</div></div>`;
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
document.getElementById('btn-mas').onclick=render;
document.getElementById('q').addEventListener('input',e=>{q=e.target.value;aplicar();});
document.querySelectorAll('.chip').forEach(ch=>ch.onclick=()=>{
  document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));
  ch.classList.add('on'); cat=ch.dataset.cat; aplicar();
});
fetch('/datos.json').then(r=>r.json()).then(d=>{LIBROS=d;aplicar();});
"""

def generar_sitio(libros, salida):
    if os.path.exists(salida):
        shutil.rmtree(salida)
    os.makedirs(os.path.join(salida, "libro"))
    os.makedirs(os.path.join(salida, "css"))
    os.makedirs(os.path.join(salida, "js"))

    categorias = sorted({l["categoria"] for l in libros},
                        key=lambda c: (c == "Otros", c))  # Otros al final

    # css y js
    open(os.path.join(salida, "css", "catalogo.css"), "w").write(CSS)
    open(os.path.join(salida, "js", "catalogo.js"), "w").write(JS)

    # datos.json compacto para el buscador
    datos = [{
        "t": l["titulo"], "a": l["autor"], "ok": l["autor_ok"],
        "ed": l["editorial"], "an": l["anio"], "c": l["categoria"],
        "s": l["slug"], "v": bool([f for f in l["faltantes"] if f != "autor"]),
        "tapa_url": l.get("tapa_url", ""),
        "wa": wa_link(l["titulo"], l["autor"]),
    } for l in libros]
    json.dump(datos, open(os.path.join(salida, "datos.json"), "w"), ensure_ascii=False, separators=(",", ":"))

    # index
    open(os.path.join(salida, "index.html"), "w").write(generar_index(libros, categorias))

    # páginas individuales
    for l in libros:
        open(os.path.join(salida, "libro", f'{l["slug"]}.html'), "w").write(generar_pagina_libro(l))

    # sitemap
    hoy = date.today().isoformat()
    urls = [f"<url><loc>{DOMINIO}/</loc><lastmod>{hoy}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>"]
    for l in libros:
        urls.append(f'<url><loc>{DOMINIO}/libro/{l["slug"]}.html</loc><lastmod>{hoy}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>"
    open(os.path.join(salida, "sitemap.xml"), "w").write(sitemap)

    # robots y CNAME
    open(os.path.join(salida, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMINIO}/sitemap.xml\n")
    open(os.path.join(salida, "CNAME"), "w").write("catalogo.ichinen.com.ar\n")

    return categorias

if __name__ == "__main__":
    import sys
    from lector import leer_excel
    libros = leer_excel("/mnt/user-data/uploads/listado.xlsx")
    cats = generar_sitio(libros, "/home/claude/sitio")
    print(f"Sitio generado: {len(libros)} libros, {len(cats)} categorías: {cats}")
    import subprocess
    n = subprocess.run(["find","/home/claude/sitio","-type","f"],capture_output=True,text=True).stdout.count("\n")
    print(f"Archivos generados: {n}")
