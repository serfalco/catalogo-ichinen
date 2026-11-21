
let LIBROS=[], filtrados=[], mostrados=0, cat="", q="", listo=false;
const WA="5491159952089";
const PASO=48, PRERENDER=48;
const grid=document.getElementById('grid');
const cont=document.getElementById('contador');
const masWrap=document.getElementById('mas');
const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
// El link de WhatsApp se arma acá (antes venía en datos.json y era la mitad
// del archivo). Mismo texto que wa_link() en generador.py.
function waLink(l){
  let m='Hola! Me interesa el libro "'+l.t+'"';
  if(l.a&&l.a!=='Autor a verificar')m+=' de '+l.a;
  m+='. ¿Está disponible?';
  return 'https://wa.me/'+WA+'?text='+encodeURIComponent(m);
}
function tarjeta(l){
  const cover=l.tapa_url
    ?`<div class="cover"><div class="tc"></div><img src="${l.tapa_url}" alt="Tapa de ${l.t}" loading="lazy"></div>`
    :`<div class="cover"><img src="/ph/${l.cs}.svg" alt="${l.c}" loading="lazy"></div>`;
  const meta=[l.ed,l.an].filter(Boolean).join(' · ');
  const verif=l.v?`<span class="verif">A verificar</span>`:'';
  const au=l.ok?l.a:(l.c==='Historieta y cómic'?(l.ed||''):'Autor a verificar');
  return `<article class="card"><a href="/libro/${l.s}.html" style="color:inherit">
    ${cover}<div class="cat">${l.c}</div>${verif}
    <div class="t">${l.t}</div><div class="a">${au}</div>
    <div class="meta">${meta}</div></a>
    <a class="btn-wa" href="${waLink(l)}" target="_blank" rel="noopener">Consultar</a></article>`;
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
// datos.json (~250 KB comprimido) se baja recién cuando hace falta: al
// buscar, filtrar o pedir más libros. Quien solo mira la portada no lo baja.
// Al enfocar el buscador o pasar por un filtro se empieza a bajar, así cuando
// la persona escribe ya está (o casi).
let cargando=null;
function cargar(){
  if(!cargando) cargando=fetch('/datos.json').then(r=>r.json()).then(d=>{LIBROS=d;continuar();})
    .catch(e=>{cargando=null;throw e;});
  return cargando;
}
const btnMas=document.getElementById('btn-mas');
btnMas.onclick=()=>{
  if(listo){render();return;}
  const txt=btnMas.textContent; btnMas.textContent='Cargando…'; btnMas.disabled=true;
  cargar().then(render).finally(()=>{btnMas.textContent=txt;btnMas.disabled=false;});
};
const inputQ=document.getElementById('q');
inputQ.addEventListener('focus',()=>{cargar().catch(()=>{});},{once:true});
inputQ.addEventListener('input',e=>{ q=e.target.value; cargar().then(aplicar); });
document.querySelectorAll('.chip').forEach(ch=>{
  ch.addEventListener('pointerenter',()=>{cargar().catch(()=>{});},{once:true});
  ch.onclick=()=>{
    document.querySelectorAll('.chip').forEach(c=>c.classList.remove('on'));
    ch.classList.add('on'); cat=ch.dataset.cat; cargar().then(aplicar);
  };
});
