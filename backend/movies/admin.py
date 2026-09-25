"""
Personalizacion del panel de administracion - pasos 5, 6 y 7.

El paso 4 registro los modelos con `admin.site.register(Model)`. Aqui se
sustituye cada registro por una clase ModelAdmin que declara:

    list_display  -> que columnas se ven en el listado
    list_filter   -> que filtros aparecen en la barra lateral
    search_fields -> sobre que campos funciona el buscador

Ademas:

    RatingInline    -> paso 6, las valoraciones se dan de alta dentro de la pelicula
    readonly_fields -> paso 7, la auditoria se muestra pero no se puede editar
"""

from django.contrib import admin

from .models import Genre, Movie, Person, Rating


class RatingInline(admin.TabularInline):
    """
    Paso 6: bloque de lineas de valoraciones dentro del formulario de la pelicula.

    Asi se dan de alta sin salir del registro padre, en lugar de tener que ir
    a "Valoraciones", pulsar "Anadir" y buscar la pelicula a mano.
    """

    model = Rating
    # Cada linea muestra solo la nota, el comentario y quien valora.
    # created_at / updated_at se anaden como solo lectura en el paso 7.
    fields = ("score", "comment", "author")
    extra = 1  # Una linea en blanco para anadir una valoracion nueva.
    verbose_name = "valoracion"
    verbose_name_plural = "valoraciones"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """Listado de peliculas con columnas utiles, filtro y buscador."""

    # Columnas del listado: lo primero que ve el usuario al entrar.
    list_display = ("title", "year", "genres_list", "average_score", "ratings_count")
    list_display_links = ("title",)

    # Paso 5: filtro por genero y por ano, como pide el enunciado.
    list_filter = ("genres", "year")

    # Paso 5: busqueda por titulo y por nombre de persona del reparto.
    search_fields = ("title", "people__name", "genres__name")

    # Orden estable del listado.
    ordering = ("-year", "title")

    # Paso 6: las valoraciones se editan dentro de la pelicula.
    inlines = [RatingInline]

    # Paso 7: la auditoria se muestra, pero no se puede escribir a mano.
    # Los campos auto_now_add / auto_now ya los fija Django; marcar aqui solo
    # evita que el panel parezca un formulario editable que no lo es.
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="generos", ordering="genres__name")
    def genres_list(self, obj: Movie) -> str:
        """Muestra todos los generos de la pelicula separados por comas."""
        return ", ".join(genre.name for genre in obj.genres.all())

    @admin.display(description="nº de valores", ordering="ratings__score")
    def ratings_count(self, obj: Movie) -> int:
        """Cuantas valoraciones ha recibido la pelicula."""
        return obj.ratings.count()

    @admin.display(description="media")
    def average_score(self, obj: Movie) -> str:
        """Puntuacion media, o un guion si la pelicula aun no esta valorada."""
        average = obj.average_score
        return "-" if average is None else f"{average}"


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """Listado de generos con el numero de peliculas de cada uno."""

    list_display = ("id", "name", "movie_count")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="peliculas")
    def movie_count(self, obj: Genre) -> int:
        """Cuantas peliculas usan este genero."""
        return obj.movies.count()


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """Listado de personas del reparto y el equipo tecnico."""

    list_display = ("id", "name", "movie_count")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="peliculas")
    def movie_count(self, obj: Person) -> int:
        """En cuantas peliculas aparece esta persona."""
        return obj.movies.count()


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Listado de valoraciones."""

    list_display = ("movie", "score", "author", "created_at")
    list_filter = ("score", "movie__genres")
    search_fields = ("movie__title", "author", "comment")
    autocomplete_fields = ("movie",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
