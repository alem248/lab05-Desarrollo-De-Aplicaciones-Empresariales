# Paso 12 — Prueba de escapado automático

Se guardó en el cuerpo de una noticia (`Article.body`) la cadena:

```html
<p>Este parrafo lleva <b>negrita</b> incrustada y una etiqueta script:</p>
<script>alert("xss")</script>
```

## Qué muestra la página

Al abrir `/noticia/prueba-escapado-html/`, el navegador **muestra el texto
literal** `<p>...</p><script>alert("xss")</script>` como parte del cuerpo de
la noticia. No se ejecuta ningún `alert` y la etiqueta `<script>` no crea un
elemento en el DOM.

```html
<!-- respuesta HTML enviada por Django -->
&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;
```

## Por qué

Django escapa automáticamente el contenido de las variables que salen en una
plantilla: convierte `<`, `>`, `&` y `"` en sus entidades HTML
(`&lt;`, `&gt;`, `&amp;`, `&quot;`). Por eso el texto se ve literal en vez de
interpretarse como marcado. Esto protege el portal frente a ataques XSS
(scripting entre sitios) sin que escribamos nada extra.

Solo se desactivaría con el filtro `|safe`, que **no** debemos aplicar a
contenido escrito por usuarios.
