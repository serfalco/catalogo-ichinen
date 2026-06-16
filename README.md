# Catálogo Librería Ichinén

Catálogo online de la librería, publicado en **https://catalogo.ichinen.com.ar**

Se genera solo a partir del Excel de Mercado Libre. Nadie tiene que tocar código.

---

## Cómo actualizar el catálogo (para el dueño)

Cuando tengas un Excel nuevo de Mercado Libre con los libros:

1. Entrá al **administrador de archivos de Hostinger**.
2. Abrí la carpeta **`datos`** (dentro de `public_html`).
3. Subí el Excel ahí, con el nombre **`listado.xlsx`**, reemplazando el anterior.
4. Listo. No hay que hacer nada más.

El catálogo se actualiza solo dentro de la semana siguiente. Si querés que se actualice
en el momento, avisale a quien maneja la cuenta de GitHub para apretar el botón de
actualización manual (ver más abajo).

**Importante:** el archivo se tiene que llamar exactamente `listado.xlsx` y estar en la
carpeta `datos`. Si cambiás el nombre o la carpeta, el catálogo no lo va a encontrar.

---

## Cómo funciona (resumen técnico)

- Una vez por semana, GitHub revisa si el Excel de Hostinger cambió.
- Si cambió: lo descarga, lo limpia, clasifica los libros por categoría, busca tapas
  por ISBN, y genera el sitio completo (grilla + una página por libro + sitemap para Google).
- Publica el resultado en la carpeta `docs/`, que es lo que sirve GitHub Pages.
- Si no cambió, no hace nada.

### Forzar una actualización manual

1. En GitHub, ir a la pestaña **Actions**.
2. Elegir el workflow **"Actualizar catálogo"**.
3. Botón **"Run workflow"**.

### Activar o desactivar la búsqueda de tapas

En el archivo `.github/workflows/catalogo.yml`, en el paso "Construir el catálogo",
la variable `BUSCAR_TAPAS` controla esto: `"1"` busca tapas, `"0"` usa el placeholder
para todos. `LIMITE_TAPAS` es cuántas tapas nuevas busca por corrida (para no demorar).

---

## Estructura del proyecto

```
motor/
  limpieza.py    Limpieza y clasificación de los datos sucios del Excel
  lector.py      Lee el Excel de Mercado Libre
  tapas.py       Busca y cachea tapas por ISBN
  generador.py   Genera el sitio (HTML, CSS, JS, sitemap)
  build.py       Orquesta todo el proceso
.github/workflows/
  catalogo.yml   La automatización semanal de GitHub
docs/            El sitio publicado (generado automáticamente, no editar a mano)
tapas/           Tapas descargadas (dentro de docs/, cacheadas entre corridas)
```

---

## Configuración inicial (una sola vez)

Esto ya quedó configurado, se documenta por si hay que rehacerlo:

1. **GitHub Pages**: Settings → Pages → Source "Deploy from a branch" → rama `main`,
   carpeta `/docs`. Custom domain: `catalogo.ichinen.com.ar`.
2. **Variable EXCEL_URL**: Settings → Secrets and variables → Actions → pestaña
   "Variables" → New variable: nombre `EXCEL_URL`,
   valor `https://ichinen.com.ar/datos/listado.xlsx`.
3. **DNS**: registro CNAME `catalogo` → `serfalco.github.io` (en Hostinger).
4. **Carpeta en Hostinger**: `public_html/datos/` con el `listado.xlsx` adentro.
