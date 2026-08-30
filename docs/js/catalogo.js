
let LIBROS=[], filtrados=[], mostrados=0, cat="", q="", listo=false;
const PASO=48, PRERENDER=48;
const grid=document.getElementById('grid');
const cont=document.getElementById('contador');
const masWrap=document.getElementById('mas');
const norm=s=>(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
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
