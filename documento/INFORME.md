# Informe del laboratorio 06 — Panel de administración de Django y vista pública

**Proyecto:** CineVault
**Autor:** alem248 — ximenaperu13@gmail.com
**Tecnologías:** Django 6.1.1 · Django REST Framework 3.18.1 · Pillow 12.3.0 · React 19 · Vite 6

---

## 1. Qué es este proyecto

CineVault es un catálogo de películas con valoraciones. Tiene dos partes
deliberadamente separadas, y esa separación es el tema del laboratorio:

| | **Panel de administración** | **Vista pública** |
|---|---|---|
| Dónde vive | `backend/movies/admin.py` | `backend/movies/views.py` + `frontend/` |
| Quién la ve | Solo quien tiene cuenta | Cualquiera, sin cuenta |
| Para qué sirve | Cargar y corregir datos | Consultar datos |
| Quién decide su aspecto | Django (es una herramienta genérica) | Nosotros (es código a medida) |
| Cómo se escriben los datos | Escribiendo | No: la API es de solo lectura |

La idea del enunciado es que el panel resuelve el 90 % del trabajo de gestión
sin escribir una sola línea de vista, y la vista pública es lo que hace falta
cuando el panel ya no sirve: cuando el visitante necesita una pantalla pensada
para él, y no una tabla de administración.

```
lab06/
├── backend/                  Django: modelos, panel y API
│   ├── cinevault/            proyecto (settings, urls)
│   ├── movies/               aplicación del laboratorio
│   │   ├── models.py         Movie, Genre, Person, Rating
│   │   ├── admin.py          el panel personalizado
│   │   ├── views.py          la API de solo lectura
│   │   ├── serializers.py    la traducción modelos → JSON
│   │   ├── tests.py          41 pruebas de los pasos 4 a 10
│   │   └── management/commands/
│   │       ├── seed_movies.py    datos de prueba (paso 8)
│   │       └── setup_editores.py grupo "editores" (paso 9)
│   └── requirements.txt
├── frontend/                 React + Vite: la vista pública
│   ├── src/
│   │   ├── api.js            cliente de la API
│   │   ├── App.jsx           selector de género y rejilla
│   │   └── components/       MovieCard, MovieDetail
│   └── scripts/capturas.mjs  genera las capturas del entregable
└── documento/
    ├── INFORME.md            este documento
    └── capturas/             las 9 capturas
```

---

## 2. Cómo se ejecuta

```bash
# --- Backend ---
cd backend
pip install -r requirements.txt
py manage.py migrate
py manage.py seed_movies                    # paso 8
py manage.py setup_editores --reset-password # paso 9
py manage.py createsuperuser                # si aún no existe
py manage.py runserver

# --- Frontend (en otra terminal) ---
cd frontend
npm install
npm run dev
```

| Qué | Dónde |
|---|---|
| Panel de administración | http://127.0.0.1:8000/admin/ |
| API | http://127.0.0.1:8000/api/ |
| Vista pública | http://localhost:5173/ |

### Cuentas de prueba

| Rol | Usuario | Clave |
|---|---|---|
| Superusuario | `alem248` | `Cinevault2026!` |
| Editor (grupo "editores") | `editor01` | `Editor2026!` |

> Son credenciales de laboratorio. Si el repositorio se hace público, cámbialas
> o quita las de `seed_movies` y `setup_editores`.

### Comprobaciones

```bash
cd backend
py manage.py test movies -v 2     # 41 pruebas, todas en verde
py manage.py check                 # 0 avisos

cd frontend
npm run build                      # compila la SPA
node scripts/capturas.mjs          # regenera las 9 capturas
```

---

## 3. Los doce pasos, uno a uno

### Paso 1 — Proyecto, Pillow y la aplicación `movies`

Se creó el proyecto `cinevault` y la aplicación `movies`, se instaló Pillow
(obligatorio para que `ImageField` funcione) y se declaró la aplicación en
`INSTALLED_APPS`. Ademas:
- fijó `MEDIA_ROOT` para las portadas,
- sirvio `MEDIA_URL` en desarrollo para que las imágenes se vean en el panel,
- declaro `rest_framework` y `corsheaders`, con `CorsMiddleware` **antes** de
  `CommonMiddleware` (si no, CORS no se aplica),
- fijó `es-pe` y `America/Lima` para que las fechas del panel salgan en hora
  local, y no en UTC.

### Paso 2 — Los cuatro modelos

`Genre` y `Person` son las dos tablas "pequeñas" de la taxonomía. `Movie` es el
centro, y `Rating` cuelga de ella.

**Muchos a muchos.** `Movie.genres` es un `ManyToManyField` a `Genre`, así que
una película tiene varios géneros y un género está en varias películas. La tabla
intermedia la crea Django sola, sin escribirla a mano. Con
`related_name="movies"` se puede asking al revés: `genre.movies.all()`.

**Clave foránea.** `Rating.movie` es un `ForeignKey` a `Movie` con
`on_delete=CASCADE`: si se borra la película, sus valoraciones se borran con
ella, que es lo correcto porque una valoración sin película no significa nada.
`related_name="ratings"` da `movie.ratings.all()`, que es lo que usan la
propiedad `average_score` y el inline del paso 6.

Dos detalles que se anadieron despues:

- `Movie.people` es también muchos a muchos, para el reparto. Así una persona
  aparece en varias películas y una película tiene varias personas, que es la
  realidad del cine.
- `Rating` lleva un `UniqueConstraint` que impide que la misma persona valore
  dos veces la misma película, salvo que `author` esté vacío (valoraciones
  anónimas no se pueden deduplicar así).

### Paso 3 — Migraciones y superusuario

`makemigrations movies` generó `0001_initial` y `migrate` la aplicó. El
superusuario `alem248` se creó con `createsuperuser`.

La migración `0002` (mucho después, en el paso 11) solo traduce al español los
`verbose_name` de los campos: **no cambia el esquema de la base de datos**.

### Paso 4 — Los cuatro modelos en el panel, sin escribir ninguna vista

Esto es lo primero que pide el enunciado y conviene subrayarlo: **no se
escribió ninguna vista**. Cuatro líneas bastan:

```python
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Person)
admin.site.register(Rating)
```

Con solo eso ya existen las cuatro secciones del panel, con su listado, su
formulario de alta, su formulario de edición, su confirmación de borrado y su
búsqueda. Todo eso lo genera Django a partir del modelo.

→ **Captura 01.**

### Paso 5 — De `register` a `ModelAdmin`

Cada registro se sustituyó por una clase `ModelAdmin`:

```python
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display  = ("title", "year", "genres_list", "average_score", "ratings_count")
    list_filter   = ("genres", "year")
    search_fields = ("title", "people__name", "genres__name")
    ordering      = ("-year", "title")
```

- `list_display` — las columnas del listado. `genres_list`, `average_score` y
  `ratings_count` no son campos: son métodos decorados con `@admin.display`, y
  por eso aparecen en el listado sin existir en la base de datos.
- `list_filter` — el filtro de la barra lateral, por género y por año, como
  pide el enunciado.
- `search_fields` — el buscador. Se declara `people__name` para poder buscar
  por el nombre de alguien del reparto, no solo por el título.

Un detalle que costó tiempo: `date_hierarchy` **no** admite un `PositiveIntegerField`,
solo `DateField` o `DateTimeField`. Aplicado a `year` el `manage.py check`
falla con `admin.E128`. El filtro por año se consigue con `list_filter`, que es
lo que pedía el enunciado.

→ **Capturas 02 y 03.**

### Paso 6 — Las valoraciones, dentro de la película

```python
class RatingInline(admin.TabularInline):
    model   = Rating
    fields  = ("score", "comment", "author")
    extra   = 1
```

Con `inlines = [RatingInline]`, el formulario de la película lleva un bloque
**Valoraciones** con las existentes y una línea en blanco para añadir otra.

Lo que gana: el alta de una valoración deja de ser un viaje de tres pasos (ir a
Valoraciones → Añadir → buscar la película en un desplegable de cientos de
entradas) y pasa a ser rellenar una fila y guardar. Las dos operaciones, crear
y borrar, funcionan también desde ahí.

→ **Captura 04.**

### Paso 7 — La auditoría en solo lectura

```python
readonly_fields = ("created_at", "updated_at")
```

`created_at` y `updated_at` usan `auto_now_add` y `auto_now`, así que Django ya
los rellenaba solo. Marcarlos en solo lectura **no cambia el dato**: cambia lo
que el panel sugiere. Sin esto, el formulario ofrece dos campos de fecha que
parecen editables y que no lo son, que es la peor forma de confundir a quien
usa la herramienta.

Comprobado: en el formulario no aparece ningún `input` de fecha, y postear las
fechas a mano no altera nada.

`Genre` y `Person` **no** llevan `readonly_fields`: no tienen campos de
auditoría, y el `check` de Django lo rechaza con `admin.E035` / `admin.E108`.

→ **Captura 04** (las fechas salen en gris, sin widget de calendario).

### Paso 8 — Datos de prueba

El enunciado pide cargarlos "desde el panel". Se puede hacer a mano, y para eso
está `py manage.py seed_movies --show`, que imprime el detalle. Pero para poder
repetir la entrega sin volver a hacer clic a clic, el mismo conjunto de datos
está en un comando:

```bash
py manage.py seed_movies            # carga (idempotente)
py manage.py seed_movies --flush    # borra y vuelve a cargar
py manage_movies --show             # imprime el detalle para carga manual
```

Carga **4 géneros, 11 personas, 10 películas y 16 valoraciones**, repartidas en
**7 películas** valoradas (el enunciado pide al menos 5).

El comando es **idempotente**: usa `get_or_create` y `update_or_create`, así que
se puede ejecutar las veces que haga falta sin duplicar nada.

### Paso 9 — El grupo «editores»

```bash
py manage.py setup_editores --reset-password
```

Crea el grupo con `view_movie`, `add_movie` y `change_movie`, y **quita
explícitamente** `delete_movie`, que es lo que el enunciado pide. El usuario
`editor01` se crea con `is_staff=True` (para poder entrar al panel) pero
`is_superuser=False`.

Al entrar con esa cuenta, esto desaparece del panel:

1. **El botón «Eliminar»** de la ficha de la película.
2. **La acción masiva «Eliminar seleccionados»** del listado.
3. **El bloque inline de valoraciones** del paso 6.
4. **Las secciones Géneros, Personas y Valoraciones** del menú lateral, e
   incluso la de *Autenticación y autorización*.

El punto 3 es el interesante, y no estaba previsto: **Django solo pinta un
inline si el usuario puede ver o cambiar el modelo relacionado**, y el grupo
«editores» no tiene permisos sobre `Rating`. No es que el inline se esconda
porque sí — es que, para ese usuario, el inline no tiene sentido, porque sus
valoraciones no podría tocarlas.

Lo mismo explica el punto 4: el menú lateral solo lista los modelos sobre los
que el usuario tiene algún permiso.

Hay una prueba que confirma la causa: si al grupo se le añaden `view_rating` y
`change_rating`, el inline vuelve a aparecer sin tocar nada más.

Y un detalle importante: ocultar el botón **no es** lo mismo que impedir el
borrado. Con la sesión del editor, un `POST` directo a
`/admin/movies/movie/<id>/delete/` devuelve **403** y la película sigue ahí.
La protección está en el permiso, no en el botón.

→ **Capturas 05 y 06**, comparadas con la 04 del superusuario.

### Paso 10 — La vista pública de recomendación

Aquí está el contraste que pide el enunciado.

**Lo que hace el panel.** Es una herramienta genérica que alguien decidió
comprar en lugar de construir. Aparece sola al registrar el modelo, no la
diseña nadie para este proyecto, y sirve para cualquier tarea de gestión:
cargar, corregir, borrar. Su interfaz es la que impone Django, y adaptarla es
trabajar dentro de unos límites que no elegimos.

**Lo que exige una vista propia.** «Las películas del mismo género mejor
valoradas» no existe en ningún panel. Requiere una **consulta** —filtrar por
género y ordenar por la media de las valoraciones—, y una consulta con criterio
no se puede pedir en un panel. Además necesita un **formato de salida** que no
sea una tabla de administración: tarjetas con la media destacada, un selector de
género, y una presentación que se parezca a un sitio y no a una consola.

**El reparto de responsabilidades que se ha usado:**

- El panel escribe los datos. Es su función.
- La API los sirve, **solo en lectura**. Un `POST` a `/api/movies/` devuelve
  **405**: no hay forma de dar de alta una película desde la API.
- React decide cómo se ven.

```bash
curl http://127.0.0.1:8000/api/recomendaciones/
curl "http://127.0.0.1:8000/api/recomendaciones/?genre=1"   # ciencia ficción
```

La consulta no recorre las valoraciones en Python: usa `annotate` con `Avg` y
`Count` para que la media y el número de valores se calculen **en la base de
datos, en una sola consulta**. Además descarta las películas sin ninguna
valoración, porque no pueden ser «las mejor valoradas» de nada.

**Un choque de nombres que vale la pena mencionar.** El modelo tiene dos
propiedades, `average_score` y `ratings_count`. `annotate()` no puede asignar
un atributo que sea una property de solo lectura, y falla con
`property 'average_score' of 'Movie' object has no setter`. La solución fue
anotar con otros alias (`media`, `total_valoraciones`) y renombrarlos en el
serializador con `source=`, de modo que el JSON siga llamándose igual:

```python
average_score = serializers.FloatField(source="media", read_only=True)
```

→ **Capturas 07, 08 y 09.**

### Paso 11 — Las capturas del entregable

Están en `documento/capturas/` y las genera `frontend/scripts/capturas.mjs`
con Playwright, de forma reproducible:

```bash
cd frontend
node scripts/capturas.mjs
```

| Captura | Qué demuestra | Paso |
|---|---|---|
| `01-admin-cuatro-operaciones.png` | Las cuatro secciones sin escribir ninguna vista | 4 |
| `02-admin-listado-peliculas-personalizado.png` | `list_display`, `list_filter` y buscador | 5 |
| `03-admin-buscador-por-nombre-de-persona.png` | El buscador por nombre de persona | 5 |
| `04-admin-formulario-con-inline-y-auditoria.png` | El inline y la auditoría en gris | 6, 7 |
| `05-comparacion-editor-sin-borrar.png` | El editor, sin «Eliminar» y sin inline | 9 |
| `06-comparacion-editor-listado-sin-borrado-masivo.png` | El editor, sin borrado masivo | 9 |
| `07-vista-publica-recomendaciones.png` | La vista pública de React | 10 |
| `08-vista-publica-filtrada-por-genero.png` | Filtrada por ciencia ficción | 10 |
| `09-vista-publica-detalle-con-valoraciones.png` | El detalle con sus valoraciones | 10 |

**Las capturas 04 y 05 son la comparación que pide el enunciado.** Son la misma
página, la misma película (Dune: Parte dos) y el mismo servidor; lo único que
cambia es la cuenta con la que se ha entrado:

| | Superusuario (`04`) | Editor (`05`) |
|---|---|---|
| Botón «Eliminar» | Sí | **No** |
| Acción masiva de borrado | Sí | **No** |
| Bloque de valoraciones | Sí | **No** |
| Menú lateral | 4 secciones + autenticación | Solo «Películas» |
| Editar la película | Sí | Sí |

El código de cada personalizedstep está en un commit con su mensaje
correspondiente, así que el historial de `git log` recorre el laboratorio paso a
paso.

### Paso 12 — Entrega

Ver la sección «Qué hay que entregar» de este mismo documento y el `README.md`
de la raíz, que trae los comandos exactos para subir el proyecto al repositorio
del equipo y el entregable al campus virtual.

---

## 4. Qué se ha verificado

Las comprobaciones de este laboratorio **no son solo capturas**: hay 41 pruebas
automáticas que comprueban exactamente lo que el enunciado pide verificar.

```bash
cd backend
py manage.py test movies -v 2
```

| Clase de pruebas | Qué comprueba | Nº |
|---|---|---|
| `Paso4ModelosRegistradosTests` | Los cuatro modelos registrados, las cuatro secciones y sus cuatro listados responden 200 | 4 |
| `Paso5PersonalizacionListadoTests` | Las columnas, el filtro por género, el filtro por año, la búsqueda por título y por persona, y el orden | 7 |
| `Paso6ValoracionesInlineTests` | El inline aparece, permite crear una valoración y permite borrar una existente | 5 |
| `Paso7CamposAuditoriaSoloLecturaTests` | La auditoría se ve pero no se puede escribir, ni al añadir ni al cambiar | 6 |
| `Paso9GrupoEditoresTests` | Permisos del grupo, alta, cambio, borrado por URL (403), menú lateral y la comparación de ambos usuarios | 12 |
| `Paso10VistaRecomendacionTests` | Orden por media, filtro por género, exclusión de las no valoradas, error 400 y solo lectura de la API | 7 |

Además, a mano y con el servidor en marcha:

- `manage.py check` → 0 avisos.
- Un `POST` a `/api/movies/` → **405**.
- `/api/recomendaciones/?genre=1` → Interestelar 9.0, La llegada 8.5, Dune 8.0.
- El buscador del panel buscando «Villeneuve» encuentra Dune: Parte dos.
- La SPA compilada (`npm run build`) y sin errores en la consola del navegador.

---

## 5. Conclusión

La lección del laboratorio no es «Django hace el panel gratis» (que ya se vio
en el paso 4), sino la que aparece al llegar al paso 10: **el panel resuelve
gestionar, no presentar**. En cuanto hace falta una consulta con criterio o
una pantalla pensada para quien visita el sitio, el panel se queda corto y hay
que escribir la vista. Por eso la separación de este proyecto es deliberada: el
panel escribe, la API solo lee, y React presenta.

Un segundo aprendizaje, menos obvio: **el comportamiento del panel depende de
los permisos, no solo del código**. El paso 9 obligó a leer el HTML de la misma
página con dos cuentas distintas, y así se vio que el inline del paso 6
desaparece para el editor. Eso no lo dice ningún `admin.py`: sale de que Django
comprueba los permisos del modelo relacionado antes de pintar el inline. Es un
buen argumento a favor de las pruebas automáticas de esta clase, que fue lo
que destapó el caso.
