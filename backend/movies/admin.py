"""
Personalizacion del panel de administracion - paso 5.

El paso 4 registro los modelos con `admin.site.register(Model)`. Aqui se
sustituye cada registro por una clase ModelAdmin que declara:

    list_display  -> que columnas se ven en el listado
    list_filter   -> que filtros aparecen en la barra lateral
    search_fields -> sobre que campos funciona la buscador

Los pasos 6 y 7 (inline de valoraciones y campos de solo lectura) se anaden
en los commits posteriores, siguiendo el orden del enunciado.
"""

from django.contrib import admin
from django.db.models import Count

from .models import Genre, Movie, Person, Rating


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
