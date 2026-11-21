# Clasificación del catálogo

Cada categoría corresponde a un código de **Thema**, el estándar internacional
de clasificación temática de libros de EDItEUR (el que usan editoriales,
distribuidoras y librerías para describir sus fondos), con su equivalente en la
**CDU** (Clasificación Decimal Universal, la de las bibliotecas) cuando es una
disciplina académica.

Regla general: **un libro va donde lo pondría ese estándar por su contenido**,
no por cómo lo cargó Mercado Libre ni por cuántos libros tiene la categoría.
No hay fusiones automáticas de categorías chicas.

Criterios que más se confunden, y por qué van separados:

- **Psicología y psicoanálisis** (Thema JM, CDU 159.9) es una disciplina
  científica: Freud, Lacan, Klein, Piaget, Winnicott, manuales de psicología.
  **Autoayuda y desarrollo personal** (Thema VS) son libros de consejo práctico
  para la vida personal: Bucay, Louise Hay, Wayne Dyer, Stamateas. No se
  mezclan.
- **Religión** (Thema QR, CDU 2): Biblia, teología, historia de las religiones,
  budismo, espiritualidad de una tradición religiosa.
  **Esoterismo y espiritualidad alternativa** (Thema VX): tarot, astrología,
  ángeles, energía, ovnis, parapsicología, nueva era.
- **Ciencias y medicina** (Thema P y M, CDU 5 y 61): obras de divulgación
  científica o técnicas. **Salud y vida familiar** (Thema VF): dietas, crianza,
  embarazo, bienestar práctico.
- **Historia** (Thema N, CDU 9) estudia el pasado. **Política, sociedad y
  economía** (Thema J, K, L, CDU 3) es ciencias sociales: política, economía,
  sociología, derecho, educación, periodismo de actualidad.
- **Filosofía** (Thema QD, CDU 1) es la disciplina. Un ensayo literario sobre
  literatura va en **Ensayo y crítica literaria** (Thema DS).
- **Biografías y memorias** (Thema DN, CDU 929): la vida de una persona contada
  como no ficción. Una novela sobre una persona real es novela histórica.
- **Clásicos de la literatura** (Thema FBC): ficción canónica anterior al
  siglo XX o consagrada como clásico universal (Dickens, Tolstói, Cervantes,
  Verne). La ficción del siglo XX en adelante sin género específico es
  **Narrativa contemporánea** (Thema FBA).
- La épica y los mitos grecolatinos (Homero, Ovidio, mitologías) van en
  **Mitología y épica clásica** (Thema DBS). La tragedia griega es **Teatro**;
  Platón y Aristóteles, **Filosofía**.
- **Infantil** (Thema Y, edad hasta 11 años) y **Juvenil** (Thema YF con
  calificador de edad 12+) se separan por la edad del lector, no por el tema.
- Una historieta o novela gráfica va en **Historieta y novela gráfica**
  (Thema X) aunque sea infantil, de humor o una adaptación de un clásico.

## Categorías

| Código | Categoría | Thema | CDU |
|---|---|---|---|
| NAR | Narrativa | FBA | 821-3 |
| CLA | Clásicos de la literatura | FBC | 821-3 |
| POL | Policial y misterio | FF | 821-312.4 |
| THR | Thriller y suspenso | FH | 821-312.4 |
| TER | Terror | FK | 821-3 |
| CFF | Ciencia ficción y fantasía | FL, FM | 821-312.9 |
| ROM | Novela romántica | FR | 821-3 |
| NHI | Novela histórica | FV | 821-311.6 |
| POE | Poesía | DC | 821-1 |
| TEA | Teatro | DD | 821-2 |
| MIT | Mitología y épica clásica | DBS | 821.14 / 398 |
| ECL | Ensayo y crítica literaria | DS | 82.09 |
| HUM | Humor | WH | 821-7 |
| HQ | Historieta y cómic | X | 741.5 |
| INF | Infantil | Y (hasta 11 años) | 087.5 |
| JUV | Juvenil | YF (12+) | 087.5 |
| FIL | Filosofía y pensamiento | QD | 1 |
| PSI | Psicología y psicoanálisis | JM | 159.9 |
| AUT | Autoayuda y desarrollo personal | VS | 159.947 (aplicada) |
| REL | Religión | QR | 2 |
| ESO | Esoterismo y espiritualidad alternativa | VX | 133 |
| HIS | Historia | N | 9 |
| SOC | Política, sociedad y economía | J, K, L | 3 |
| BIO | Biografías y memorias | DN | 929 |
| CIE | Ciencias y medicina | P, M | 5, 61 |
| SAL | Salud y vida familiar | VF | 613 |
| ART | Arte, música y cine | A | 7 |
| LEN | Lengua y diccionarios | C, G | 80/81, 03 |
| VIA | Viajes y guías | WT | 910 |
| OCI | Cocina, hogar y ocio | W, S | 64, 79 |

## Dónde vive

- `motor/clasificacion_manual.tsv`: la clasificación revisada a mano, una obra
  por línea (título normalizado + autor normalizado → código). Tiene prioridad
  sobre todo lo demás.
- `motor/limpieza.py` (`clasificar`): reglas para los libros que todavía no
  están en el archivo manual (los que entran con un Excel nuevo). Usan las
  mismas categorías.
- `motor/categorias.py`: los nombres visibles de cada código y las URLs de la
  taxonomía anterior que redirigen a la nueva.
- Stock nuevo que las reglas no pueden ubicar con certeza queda en
  "Temas varios" y el build lo lista ("Sin revisión manual de categoría"):
  se revisa y se agrega al archivo manual.
- No hay fusión automática de categorías chicas: una categoría existe por su
  materia, no por cuántos ejemplares tiene en un momento dado.
