"""
Pruebas del laboratorio.

Comprueban lo que el enunciado pide verificar en cada paso, sin necesitar un
servidor en marcha ni capturas manuales:

    paso 4  los cuatro modelos aparecen en el panel sin ninguna vista escrita
    paso 5  list_display, list_filter y search_fields funcionan de verdad
    paso 6  las valoraciones se dan de alta dentro del formulario de la pelicula
    paso 7  los campos de auditoria ya no se pueden editar
    paso 9  el grupo "editores" puede anadir y cambiar, pero no eliminar
    paso 10 la vista de recomendacion devuelve las peliculas mejor valoradas
            del mismo genero

Ejecucion:  py manage.py test movies -v 2
"""

from urllib.parse import urlencode

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Movie, Person, Rating

User = get_user_model()


class AdminTestCase(TestCase):
    """Utilidades comunes: login y assertContains sin volcar el HTML entero.

    assertContains imprime la respuesta completa cuando falla, que con el
    panel de Django son varios kilobytes. Estos helpers fallan con un
    mensaje corto y el fragmento relevante.
    """

    def setUp(self):
        super().setUp()
        self.superusuario = User.objects.create_superuser("root", "root@test.local", "x")
        self.client.force_login(self.superusuario)

    def texto(self, response) -> str:
        return response.content.decode()

    def assertTexto(self, response, needle, msg=""):
        texto = self.texto(response)
        self.assertTrue(
            needle in texto,
            f"{msg} no se encontro {needle!r} en la respuesta ({len(texto)} bytes)",
        )

    def assertSinTexto(self, response, needle, msg=""):
        texto = self.texto(response)
        self.assertTrue(
            needle not in texto,
            f"{msg} se encontro {needle!r} y no deberia estar",
        )

    def crear_usuario_staff(self, username, **kwargs):
        return User.objects.create_user(
            username=username, password="prueba-123", is_staff=True, **kwargs
        )


class MovieFactoryMixin:
    """Datos minimos para que las pruebas no dependan del seed del paso 8."""

    @classmethod
    def setUpTestData(cls):
        cls.ficcion = Genre.objects.create(name="Ciencia ficcion")
        cls.drama = Genre.objects.create(name="Drama")
        cls.persona = Person.objects.create(name="Ada Example")

    def crear_pelicula(self, title, year, genres=(), people=(), **kwargs):
        movie = Movie.objects.create(title=title, year=year, **kwargs)
        if genres:
            movie.genres.set(genres)
        if people:
            movie.people.set(people)
        return movie


# ---------------------------------------------------------------------------
# Paso 4 - los cuatro modelos estan registrados sin ninguna vista propia
# ---------------------------------------------------------------------------
class Paso4ModelosRegistradosTests(AdminTestCase):
    def test_los_cuatro_modelos_estan_registrados(self):
        from django.contrib import admin as django_admin

        from .admin import GenreAdmin, MovieAdmin, PersonAdmin, RatingAdmin

        esperados = {
            Movie: MovieAdmin,
            Genre: GenreAdmin,
            Person: PersonAdmin,
            Rating: RatingAdmin,
        }
        for modelo, admin_class in esperados.items():
            with self.subTest(modelo=modelo.__name__):
                # @admin.register registra en el sitio por defecto, no en uno nuevo.
                self.assertIn(modelo, django_admin.site._registry)
                self.assertIsInstance(django_admin.site._registry[modelo], admin_class)

    def test_el_panel_lista_las_cuatro_operaciones(self):
        respuesta = self.client.get(reverse("admin:index"))
        self.assertEqual(respuesta.status_code, 200)
        for etiqueta in ["Peliculas", "Generos", "Personas", "Valoraciones"]:
            with self.subTest(etiqueta=etiqueta):
                self.assertTexto(respuesta, etiqueta)

    def test_las_cuatro_vistas_de_listado_responden_200(self):
        nombres = [
            "admin:movies_movie_changelist",
            "admin:movies_genre_changelist",
            "admin:movies_person_changelist",
            "admin:movies_rating_changelist",
        ]
        for nombre in nombres:
            with self.subTest(vista=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)
                # El formulario de login solo aparece si la sesion no esta iniciada.
                self.assertSinTexto(respuesta, 'name="username"', "redirige al login")

    def test_las_urls_de_panel_usan_el_nombre_singular_del_modelo(self):
        # El panel sirve /admin/movies/movie/, no /admin/movies/movies/.
        respuesta = self.client.get("/admin/movies/movie/")
        self.assertEqual(respuesta.status_code, 200)
        respuesta = self.client.get("/admin/movies/movies/")
        self.assertEqual(respuesta.status_code, 404)

    def test_las_urls_de_panel_usan_el_nombre_singular_del_modelo(self):
        # El panel sirve /admin/movies/movie/, no /admin/movies/movies/.
        respuesta = self.client.get("/admin/movies/movie/")
        self.assertEqual(respuesta.status_code, 200)
        respuesta = self.client.get("/admin/movies/movies/")
        self.assertEqual(respuesta.status_code, 404)


# ---------------------------------------------------------------------------
# Paso 5 - list_display, list_filter y search_fields
# ---------------------------------------------------------------------------
class Paso5PersonalizacionListadoTests(MovieFactoryMixin, AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.pelicula = Movie.objects.create(
            title="Interstellar", year=2014, summary="Espacio y tiempo."
        )
        cls.pelicula.genres.set([cls.ficcion])
        cls.pelicula.people.set([cls.persona])
        cls.pelicula.ratings.create(score=9, author="ana")
        cls.pelicula.ratings.create(score=7, author="beto")

    def url_listado(self, **params):
        return f"{reverse('admin:movies_movie_changelist')}?{urlencode(params)}"

    def test_el_listado_muestra_las_columnas_de_list_display(self):
        respuesta = self.client.get(reverse("admin:movies_movie_changelist"))
        # Columnas de list_display, en el orden declarado.
        self.assertTexto(respuesta, "Interstellar")
        self.assertTexto(respuesta, "2014")
        self.assertTexto(respuesta, "Ciencia ficcion")  # genres_list
        self.assertTexto(respuesta, "8.0")               # average_score
        self.assertTexto(respuesta, "Nº de valores")     # ratings_count
        for cabecera in ["Title", "Year", "Generos", "Media"]:
            with self.subTest(cabecera=cabecera):
                self.assertTexto(respuesta, cabecera)

    def test_list_filter_por_genero(self):
        drama = self.crear_pelicula("Kimono", 1955, [self.drama])
        respuesta = self.client.get(self.url_listado(genres__id__exact=self.ficcion.pk))
        self.assertTexto(respuesta, "Interstellar")
        self.assertSinTexto(respuesta, "Kimono")

        respuesta = self.client.get(self.url_listado(genres__id__exact=self.drama.pk))
        self.assertTexto(respuesta, "Kimono")
        self.assertSinTexto(respuesta, "Interstellar")

    def test_list_filter_por_anio(self):
        respuesta = self.client.get(self.url_listado(year=2014))
        self.assertTexto(respuesta, "Interstellar")
        self.assertSinTexto(respuesta, "Kimono")

        respuesta = self.client.get(self.url_listado(year=1999))
        self.assertSinTexto(respuesta, "Interstellar")

    def test_search_fields_busca_por_titulo(self):
        respuesta = self.client.get(self.url_listado(q="Interst"))
        self.assertTexto(respuesta, "Interstellar")

    def test_search_fields_busca_por_nombre_de_persona(self):
        # Busca por el nombre de la persona del reparto, no por el titulo.
        respuesta = self.client.get(self.url_listado(q="Ada Example"))
        self.assertTexto(respuesta, "Interstellar")

    def test_la_busqueda_no_encuentra_nada_con_texto_inexistente(self):
        respuesta = self.client.get(self.url_listado(q="zzzz-no-existe"))
        self.assertSinTexto(respuesta, "Interstellar")

    def test_el_orden_por_anio_funciona(self):
        self.crear_pelicula("Kimono", 1955, [self.drama])
        respuesta = self.client.get(self.url_listado())
        texto = self.texto(respuesta)
        # ordering = ("-year", "title"): Kimono (1955) va despues de Interstellar (2014).
        self.assertLess(texto.index("Interstellar"), texto.index("Kimono"))


# ---------------------------------------------------------------------------
# Paso 6 - valoraciones como inline dentro del formulario de la pelicula
# ---------------------------------------------------------------------------
class Paso6ValoracionesInlineTests(MovieFactoryMixin, AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.pelicula = Movie.objects.create(title="Arrival", year=2016)
        cls.pelicula.genres.set([cls.ficcion])

    def test_el_admin_registra_el_inline_de_valoraciones(self):
        from .admin import MovieAdmin

        inlines = MovieAdmin.inlines
        self.assertEqual(len(inlines), 1)
        self.assertEqual(inlines[0].model, Rating)

    def test_el_formulario_de_la_pelicula_muestra_el_inline(self):
        respuesta = self.client.get(
            reverse("admin:movies_movie_change", args=[self.pelicula.pk])
        )
        self.assertEqual(respuesta.status_code, 200)
        # Django capitaliza el heading a partir de verbose_name_plural.
        self.assertTexto(respuesta, "Valoraciones")
        self.assertTexto(respuesta, 'id="ratings-heading"')
        # La gestion de inline de Django usa estos inputs ocultos.
        for campo in ["TOTAL_FORMS", "INITIAL_FORMS", "MIN_NUM_FORMS", "MAX_NUM_FORMS"]:
            with self.subTest(campo=campo):
                self.assertTexto(respuesta, f'name="ratings-{campo}"')
        # Y las columnas del inline declaradas en fields.
        self.assertTexto(respuesta, "comment")
        self.assertTexto(respuesta, "author")

    def test_el_formulario_de_anadir_tambien_muestra_el_inline(self):
        respuesta = self.client.get(reverse("admin:movies_movie_add"))
        self.assertTexto(respuesta, 'name="ratings-TOTAL_FORMS"')

    def test_se_puede_crear_una_valoracion_desde_el_formulario_de_la_pelicula(self):
        url = reverse("admin:movies_movie_change", args=[self.pelicula.pk])
        datos = {
            "title": "Arrival",
            "year": 2016,
            "summary": "",
            "cover": "",
            "genres": [self.ficcion.pk],
            "people": [],
            # Formulario de solo lectura: Django espera los campos aunque no se editen.
            "created_at_0": "2024-01-01 00:00:00",
            "created_at_1": "00:00:00",
            "updated_at_0": "2024-01-01 00:00:00",
            "updated_at_1": "00:00:00",
            # Una linea nueva de inline.
            "ratings-TOTAL_FORMS": "1",
            "ratings-INITIAL_FORMS": "0",
            "ratings-MIN_NUM_FORMS": "0",
            "ratings-MAX_NUM_FORMS": "1000",
            "ratings-0-id": "",
            "ratings-0-movie": self.pelicula.pk,
            "ratings-0-score": "9",
            "ratings-0-comment": "El lenguaje es el tema.",
            "ratings-0-author": "ana",
            "ratings-0-created_at_0": "2024-01-01 00:00:00",
            "ratings-0-created_at_1": "00:00:00",
            "ratings-0-updated_at_0": "2024-01-01 00:00:00",
            "ratings-0-updated_at_1": "00:00:00",
        }
        respuesta = self.client.post(url, datos)
        self.assertEqual(respuesta.status_code, 302)

        valoracion = Rating.objects.get(movie=self.pelicula)
        self.assertEqual(valoracion.score, 9)
        self.assertEqual(valoracion.author, "ana")
        self.assertEqual(valoracion.comment, "El lenguaje es el tema.")
        self.assertEqual(self.pelicula.average_score, 9)

    def test_el_inline_permite_borrar_una_valoracion_existente(self):
        valoracion = self.pelicula.ratings.create(score=5, author="beto")
        url = reverse("admin:movies_movie_change", args=[self.pelicula.pk])
        datos = {
            "title": "Arrival",
            "year": 2016,
            "summary": "",
            "cover": "",
            "genres": [self.ficcion.pk],
            "people": [],
            "created_at_0": "2024-01-01 00:00:00",
            "created_at_1": "00:00:00",
            "updated_at_0": "2024-01-01 00:00:00",
            "updated_at_1": "00:00:00",
            "ratings-TOTAL_FORMS": "1",
            "ratings-INITIAL_FORMS": "1",
            "ratings-MIN_NUM_FORMS": "0",
            "ratings-MAX_NUM_FORMS": "1000",
            "ratings-0-id": str(valoracion.pk),
            "ratings-0-movie": str(self.pelicula.pk),
            "ratings-0-score": "5",
            "ratings-0-comment": "",
            "ratings-0-author": "beto",
            "ratings-0-created_at_0": "2024-01-01 00:00:00",
            "ratings-0-created_at_1": "00:00:00",
            "ratings-0-updated_at_0": "2024-01-01 00:00:00",
            "ratings-0-updated_at_1": "00:00:00",
            "ratings-0-DELETE": "on",  # marcar la linea para eliminar
        }
        respuesta = self.client.post(url, datos)
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Rating.objects.filter(pk=valoracion.pk).exists())


# ---------------------------------------------------------------------------
# Paso 7 - los campos de auditoria solo lectura
# ---------------------------------------------------------------------------
class Paso7CamposAuditoriaSoloLecturaTests(MovieFactoryMixin, AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.pelicula = Movie.objects.create(title="Dune", year=2021)
        cls.pelicula.genres.set([cls.ficcion])

    def test_el_admin_marca_la_auditoria_como_solo_lectura(self):
        from .admin import MovieAdmin

        admin_instance = MovieAdmin(Movie, AdminSite())
        self.assertIn("created_at", admin_instance.readonly_fields)
        self.assertIn("updated_at", admin_instance.readonly_fields)

    def test_el_formulario_muestra_la_auditoria_pero_sin_input_editable(self):
        respuesta = self.client.get(
            reverse("admin:movies_movie_change", args=[self.pelicula.pk])
        )
        contenido = self.texto(respuesta)
        # La caja del campo existe...
        self.assertIn("field-created_at", contenido)
        self.assertIn("field-updated_at", contenido)
        # ...pero sin los widgets de fecha que permitirian editarlos.
        self.assertSinTexto(respuesta, 'name="created_at_0"')
        self.assertSinTexto(respuesta, 'name="updated_at_0"')

    def test_el_formulario_de_anadir_tampoco_permite_fijar_la_fecha(self):
        respuesta = self.client.get(reverse("admin:movies_movie_add"))
        self.assertSinTexto(respuesta, 'name="created_at_0"')
        self.assertSinTexto(respuesta, 'name="updated_at_0"')

    def test_auto_now_add_fija_la_fecha_de_creacion(self):
        movie = Movie.objects.create(title="Blade Runner", year=1982)
        self.assertIsNotNone(movie.created_at)
        self.assertIsNotNone(movie.updated_at)

    def test_auto_now_actualiza_la_fecha_al_guardar(self):
        movie = Movie.objects.create(title="Solaris", year=1972)
        primera = movie.updated_at
        movie.title = "Solaris (1972)"
        movie.save()
        movie.refresh_from_db()
        self.assertGreater(movie.updated_at, primera)

    def test_postear_la_fecha_a_mano_no_altera_nada(self):
        # Aunque se envien las fechas en el POST, auto_now_add las descarta.
        creada_original = self.pelicula.created_at
        url = reverse("admin:movies_movie_change", args=[self.pelicula.pk])
        datos = {
            "title": "Dune",
            "year": 2021,
            "summary": "",
            "cover": "",
            "genres": [self.ficcion.pk],
            "people": [],
            "created_at_0": "1999-12-31 00:00:00",
            "created_at_1": "00:00:00",
            "updated_at_0": "1999-12-31 00:00:00",
            "updated_at_1": "00:00:00",
            "ratings-TOTAL_FORMS": "0",
            "ratings-INITIAL_FORMS": "0",
            "ratings-MIN_NUM_FORMS": "0",
            "ratings-MAX_NUM_FORMS": "1000",
        }
        respuesta = self.client.post(url, datos)
        self.assertEqual(respuesta.status_code, 302)
        self.pelicula.refresh_from_db()
        self.assertEqual(self.pelicula.created_at, creada_original)


# ---------------------------------------------------------------------------
# Paso 9 - el grupo "editores" puede anadir y cambiar, pero no eliminar
# ---------------------------------------------------------------------------
class Paso9GrupoEditoresTests(MovieFactoryMixin, AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.grupo = Group.objects.create(name="editores")
        cls.permisos = {
            clave: Permission.objects.get(codename=f"{clave}_movie", content_type__app_label="movies")
            for clave in ["add", "change", "delete", "view"]
        }
        # El paso 9 pide anadir y cambiar, pero NO eliminar.
        cls.grupo.permissions.set(
            [cls.permisos["add"], cls.permisos["change"], cls.permisos["view"]]
        )

    def editor(self, nombre="editor"):
        user = self.crear_usuario_staff(nombre, email=f"{nombre}@test.local")
        user.groups.add(self.grupo)
        return user

    def test_el_grupo_no_tiene_permiso_de_borrar(self):
        self.assertNotIn(self.permisos["delete"], self.grupo.permissions.all())

    def test_el_grupo_tiene_permiso_de_anadir_cambiar_y_ver(self):
        for clave in ["add", "change", "view"]:
            with self.subTest(permiso=clave):
                self.assertIn(self.permisos[clave], self.grupo.permissions.all())

    def test_el_usuario_editor_ve_el_panel_sin_el_boton_de_eliminar(self):
        self.client.force_login(self.editor())
        pelicula = self.crear_pelicula("Alien", 1979, [self.ficcion])

        respuesta = self.client.get(reverse("admin:movies_movie_change", args=[pelicula.pk]))
        self.assertEqual(respuesta.status_code, 200)
        url_borrar = reverse("admin:movies_movie_delete", args=[pelicula.pk])
        self.assertSinTexto(respuesta, url_borrar, "el boton de eliminar sigue visible")

    def test_el_usuario_editor_no_ve_el_borrado_masivo_en_el_listado(self):
        self.client.force_login(self.editor())
        self.crear_pelicula("Alien", 1979, [self.ficcion])
        respuesta = self.client.get(reverse("admin:movies_movie_changelist"))
        self.assertSinTexto(respuesta, "delete_selected", "el borrado masivo sigue visible")

    def test_el_usuario_editor_ve_el_panel_y_el_listado(self):
        self.client.force_login(self.editor())
        self.crear_pelicula("Alien", 1979, [self.ficcion])
        for nombre in ["admin:index", "admin:movies_movie_changelist"]:
            with self.subTest(vista=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)

    def test_el_usuario_editor_puede_anadir_una_pelicula(self):
        self.client.force_login(self.editor("editor_add"))
        respuesta = self.client.post(
            reverse("admin:movies_movie_add"),
            {
                "title": "Blade Runner",
                "year": 1982,
                "summary": "",
                "cover": "",
                "genres": [self.ficcion.pk],
                "people": [],
                "ratings-TOTAL_FORMS": "0",
                "ratings-INITIAL_FORMS": "0",
                "ratings-MIN_NUM_FORMS": "0",
                "ratings-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Movie.objects.filter(title="Blade Runner").exists())

    def test_el_usuario_editor_puede_cambiar_una_pelicula(self):
        self.client.force_login(self.editor("editor_change"))
        pelicula = self.crear_pelicula("Solaris", 1972, [self.ficcion])
        respuesta = self.client.post(
            reverse("admin:movies_movie_change", args=[pelicula.pk]),
            {
                "title": "Solaris (1972)",
                "year": 1972,
                "summary": "Una estacion espacial.",
                "cover": "",
                "genres": [self.ficcion.pk],
                "people": [],
                "created_at_0": "2024-01-01 00:00:00",
                "created_at_1": "00:00:00",
                "updated_at_0": "2024-01-01 00:00:00",
                "updated_at_1": "00:00:00",
                "ratings-TOTAL_FORMS": "0",
                "ratings-INITIAL_FORMS": "0",
                "ratings-MIN_NUM_FORMS": "0",
                "ratings-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        pelicula.refresh_from_db()
        self.assertEqual(pelicula.title, "Solaris (1972)")

    def test_el_usuario_editor_recibe_403_al_borrar_directamente_por_url(self):
        self.client.force_login(self.editor("editor_delete"))
        pelicula = self.crear_pelicula("Solaris", 1972, [self.ficcion])
        respuesta = self.client.post(
            reverse("admin:movies_movie_delete", args=[pelicula.pk]), {"post": "yes"}
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(Movie.objects.filter(pk=pelicula.pk).exists())

    def test_el_superusuario_si_ve_el_boton_de_eliminar(self):
        pelicula = self.crear_pelicula("Alien", 1979, [self.ficcion])
        respuesta = self.client.get(reverse("admin:movies_movie_change", args=[pelicula.pk]))
        self.assertTexto(respuesta, reverse("admin:movies_movie_delete", args=[pelicula.pk]))

    def test_comparacion_superusuario_frente_a_editor(self):
        # Es la comprobacion que pide el paso 9 y que ilustra el paso 11.
        pelicula = self.crear_pelicula("Alien", 1979, [self.ficcion])
        url_borrar = reverse("admin:movies_movie_delete", args=[pelicula.pk])
        url_cambiar = reverse("admin:movies_movie_change", args=[pelicula.pk])

        def ver_panel(usuario):
            self.client.force_login(usuario)
            return self.texto(self.client.get(url_cambiar))

        texto_super = ver_panel(self.superusuario)
        ver_panel(self.editor("editor_cmp"))
        texto_editor = self.texto(self.client.get(url_cambiar))

        self.assertIn(url_borrar, texto_super)
        self.assertNotIn(url_borrar, texto_editor)
        # Ambos ven la pelicula y el formulario de cambio.
        self.assertIn(url_cambiar, texto_super)
        self.assertIn(url_cambiar, texto_editor)


# ---------------------------------------------------------------------------
# Paso 10 - la vista publica de recomendacion
# ---------------------------------------------------------------------------
class Paso10VistaRecomendacionTests(MovieFactoryMixin, AdminTestCase):
    @classmethod
    def setUpTestData(cls):
        # Del mismo genero, claramente mejor y peor valoradas.
        cls.mejor = Movie.objects.create(title="La mejor", year=2020)
        cls.mejor.genres.set([cls.ficcion])
        cls.mejor.ratings.create(score=10, author="ana")
        cls.mejor.ratings.create(score=8, author="beto")

        cls.intermedia = Movie.objects.create(title="La intermedia", year=2019)
        cls.intermedia.genres.set([cls.ficcion])
        cls.intermedia.ratings.create(score=6, author="ana")

        cls.peor = Movie.objects.create(title="La peor", year=2018)
        cls.peor.genres.set([cls.ficcion])
        cls.peor.ratings.create(score=3, author="ana")

        # De otro genero, con la maxima puntuacion: no debe aparecer al filtrar.
        cls.otra = Movie.objects.create(title="Otra", year=2021)
        cls.otra.genres.set([cls.drama])
        cls.otra.ratings.create(score=10, author="ana")

    def test_recomienda_las_peliculas_del_genero_ordenadas_por_media(self):
        respuesta = self.client.get(reverse("movie-recommendations"), {"genre": self.ficcion.pk})
        self.assertEqual(respuesta.status_code, 200)
        titulos = [p["title"] for p in respuesta.json()["results"]]
        self.assertEqual(titulos, ["La mejor", "La intermedia", "La peor"])

    def test_sin_genero_devuelve_todas_ordenadas_por_media(self):
        respuesta = self.client.get(reverse("movie-recommendations"))
        titulos = [p["title"] for p in respuesta.json()["results"]]
        self.assertEqual(titulos[0], "La mejor")
        self.assertIn("Otra", titulos)

    def test_excluye_peliculas_sin_valoracion(self):
        Movie.objects.create(title="Sin valorar", year=2022).genres.set([self.ficcion])
        respuesta = self.client.get(reverse("movie-recommendations"), {"genre": self.ficcion.pk})
        titulos = [p["title"] for p in respuesta.json()["results"]]
        self.assertNotIn("Sin valorar", titulos)

    def test_incluye_la_media_y_el_numero_de_valoraciones(self):
        respuesta = self.client.get(reverse("movie-recommendations"), {"genre": self.ficcion.pk})
        primera = respuesta.json()["results"][0]
        self.assertEqual(primera["average_score"], 9.0)
        self.assertEqual(primera["ratings_count"], 2)

    def test_solo_lectura_no_deja_crear_peliculas_desde_la_api(self):
        # El panel es el unico sitio de escritura.
        respuesta = self.client.post(
            reverse("movie-list"), {"title": "Intrusa", "year": 2023}, content_type="application/json"
        )
        self.assertEqual(respuesta.status_code, 405)
        self.assertFalse(Movie.objects.filter(title="Intrusa").exists())
