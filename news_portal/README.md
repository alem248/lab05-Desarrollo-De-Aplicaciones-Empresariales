# Portal de Noticias — Laboratorio 05

Sitio de noticias con plantillas de Django: portada, detalle de noticia y
listado por categoría, con panel de administración, archivos estáticos y de
medios.

## Estructura

```
news_portal/
├── config/          # proyecto (settings, urls con media en desarrollo)
├── news/            # app del laboratorio
│   ├── models.py    # Author, Category, Article
│   ├── admin.py     # panel personalizado
│   ├── views.py     # portada / detalle / categoría
│   ├── urls.py      # rutas con nombre propio
│   └── management/commands/seed_news.py
├── templates/       # base.html, portada, detalle, categoria, _article_card
├── static/news/css/ # hoja de estilos
└── documento_escapado.md  # prueba del paso 12
```

## Puesta en marcha

```bash
cd news_portal
pip install -r requirements.txt
py manage.py migrate
py manage.py seed_news          # 6 noticias, 3 categorías, 1 autor
py manage.py createsuperuser    # si no existe
py manage.py runserver
```

| Qué | Dónde |
|---|---|
| Portada | http://127.0.0.1:8000/ |
| Detalle | http://127.0.0.1:8000/noticia/<slug>/ |
| Categoría | http://127.0.0.1:8000/categoria/<slug>/ |
| Panel | http://127.0.0.1:8000/admin/ |

## Qué se hizo (pasos del enunciado)

1. Proyecto `config` + app `news`, Pillow instalado y declarada la app.
2. `TEMPLATES['DIRS']`, `STATICFILES_DIRS`, `MEDIA_URL/MEDIA_ROOT` y media
   servida en desarrollo desde `config/urls.py`.
3. Modelos `Article` (imagen, `published_at`, FK a `Author`, M2M a
   `Category`), migraciones y superusuario.
4. `base.html` con bloques `title`, `content` y `sidebar`.
5. Fragmento `_article_card.html` reutilizado por portada y categoría.
6. Portada con `for`, `empty` y filtros `date` / `truncatechars`.
7. Plantilla de detalle con imagen, autor y categorías.
8. Plantilla de categoría reutilizando la tarjeta.
9. Rutas con nombres (`news:home`, `news:detail`, `news:category`) y enlaces
   con `{% url %}`, sin direcciones a mano.
10. `{% load static %}` en todas las plantillas; CSS e imágenes verificadas.
11. Admin con `list_display`, `list_filter`, `search_fields`; seis noticias
    en tres categorías cargadas con `seed_news`.
12. Prueba de escapado: el `<script>` guardado en `Article.body` se muestra
    como texto (`&lt;script&gt;`), porque Django escapa las variables de
    plantilla; ver `documento_escapado.md`.
13. Proyecto subido al repositorio del equipo.

## Conclusiones

- Las **plantillas heredadas** (`{% extends %}`) y los **fragmentos**
  (`{% include %}`) evitan repetir HTML entre portada, detalle y categoría.
- Los **nombres de ruta** (`{% url %}`) desacoplan las plantillas de las
  direcciones: cambiar una URL no rompe los enlaces.
- El **escapado automático** de Django convierte HTML en entidades, lo que
  previene XSS sin esfuerzo; usarlo con `|safe` sobre datos de usuarios sería
  una vulnerabilidad.
- Servir `media/` desde `urls.py` solo aplica en desarrollo; en producción lo
  hace el servidor web o un almacenamiento externo.
