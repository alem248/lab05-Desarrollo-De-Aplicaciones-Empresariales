# CineVault — Laboratorio 06

Panel de administración de Django personalizado y vista pública de
recomendaciones en React.

El laboratorio trata de dos cosas que parecen distintas pero están juntas: el
panel de administración de Django sirve para **gestionar** datos sin escribir
una sola vista, y en cuanto hace falta **presentarlos** con un criterio
—«las películas del mismo género mejor valoradas»— hay que escribir una vista
propia.

- **Informe completo del laboratorio:** [`documento/INFORME.md`](documento/INFORME.md)
- **Capturas del entregable:** [`documento/capturas/`](documento/capturas/)

---

## Estructura

```
lab06/
├── backend/     Django 6.1 · DRF · Pillow — modelos, panel y API
├── frontend/    React 19 + Vite 6 — la vista pública
└── documento/   INFORME.md y las 9 capturas
```

## Puesta en marcha

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

py manage.py migrate
py manage.py seed_movies                      # 4 géneros, 10 películas, 16 valoraciones
py manage.py setup_editores --reset-password   # grupo "editores" + su usuario
py manage.py createsuperuser                  # si aún no tienes uno
py manage.py runserver
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

| Qué | Dónde |
|---|---|
| Panel de administración | <http://127.0.0.1:8000/admin/> |
| API (solo lectura) | <http://127.0.0.1:8000/api/> |
| Vista pública | <http://localhost:5173/> |

### 3. Cuentas de prueba

| Rol | Usuario | Clave |
|---|---|---|
| Superusuario | `alem248` | `Cinevault2026!` |
| Editor (grupo `editores`) | `editor01` | `Editor2026!` |

> Credenciales de laboratorio. Cámbialas si el repositorio se hace público.

---

## Comprobaciones

```bash
# 41 pruebas que cubren los pasos 4, 5, 6, 7, 9 y 10
cd backend
py manage.py test movies -v 2

# avisos de configuración
py manage.py check

# compila la SPA
cd frontend
npm run build

# regenera las 9 capturas del entregable (necesita los dos servidores en marcha)
node scripts/capturas.mjs
```

---

## Comandos de gestión

```bash
py manage.py seed_movies              # carga los datos del paso 8 (idempotente)
py manage.py seed_movies --flush      # borra y vuelve a cargar
py manage.py seed_movies --show       # imprime el detalle para cargarlo a mano

py manage.py setup_editores                 # grupo "editores" (no cambia claves)
py manage.py setup_editores --reset-password # y restablece la clave del editor
```

## Endpoints de la API

Todos son de **solo lectura**: un `POST` devuelve `405`. Los datos se escriben
desde el panel.

| Método | Ruta | Qué devuelve |
|---|---|---|
| `GET` | `/api/recomendaciones/` | Películas valoradas, de más a menos media |
| `GET` | `/api/recomendaciones/?genre=<id>` | **Paso 10:** las del mismo género, mejor valoradas |
| `GET` | `/api/movies/` | Listado, con `?genre=<id>` y `?search=<texto>` |
| `GET` | `/api/movies/<id>/` | Detalle con reparto y valoraciones |
| `GET` | `/api/genres/` | Géneros con su número de películas |
| `GET` | `/api/people/` | Reparto con su número de películas |
| `GET` | `/api/ratings/` | Valoraciones |

---

## Historial

Cada paso del enunciado es un commit, con su mensaje describiendo qué se hizo
y por qué:

```bash
git log --oneline
```

```
chore(paso-1)  inicializa proyecto Django y app movies
feat(paso-2-3) modelos Movie, Genre, Person y Rating con migraciones y superusuario
feat(paso-4)   registra los cuatro modelos en el panel con admin.site.register
feat(paso-5)   sustituye el registro simple por clases ModelAdmin
feat(paso-6)   añade las valoraciones como inline del formulario de la película
feat(paso-7)   marca los campos de auditoría como solo lectura
feat(paso-8)   comando seed_movies con los datos de prueba del panel
feat(paso-9)   crea el grupo "editores" con permiso de añadir y cambiar, no eliminar
feat(paso-10)  API de solo lectura con la vista pública de recomendación
feat(paso-10)  frontend React con la vista pública de recomendaciones
feat(paso-11)  script de capturas y nueve imágenes del entregable
```
