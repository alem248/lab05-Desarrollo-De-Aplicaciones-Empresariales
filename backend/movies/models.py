"""
Modelos del laboratorio - aplicacion `movies`.

Este archivo implementa el paso 2 del enunciado: declarar Movie, Genre,
Person y Rating con sus campos, su Meta y su __str__, enlazando

    peliculas <-> generos   (relacion ManyToManyField)
    valoraciones -> pelicula (relacion ForeignKey)
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Escala de valoracion usada por el laboratorio: de 1 a 10.
RATING_MIN = 1
RATING_MAX = 10


class Genre(models.Model):
    """Genero cinematografico. Se relaciona con Movie por muchos a muchos."""

    name = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="nombre",
        help_text="Nombre del genero, por ejemplo: Ciencia ficcion.",
    )

    class Meta:
        # El panel lista los generos en orden alfabetico.
        ordering = ["name"]
        verbose_name = "Genero"
        verbose_name_plural = "Generos"

    def __str__(self) -> str:
        return self.name


class Person(models.Model):
    """Persona del reparto o del equipo tecnico (actor, director, guion)."""

    name = models.CharField(
        max_length=120,
        verbose_name="nombre",
        help_text="Nombre completo de la persona.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Persona"
        verbose_name_plural = "Personas"

    def __str__(self) -> str:
        return self.name


class Movie(models.Model):
    """Pelicula. Es la entidad central del laboratorio."""

    title = models.CharField(
        max_length=200,
        verbose_name="titulo",
        help_text="Titulo original de la pelicula.",
    )
    year = models.PositiveIntegerField(
        verbose_name="ano",
        validators=[MinValueValidator(1888)],
        help_text="Ano de estreno. 1888 es la primera proyeccion filmica.",
    )
    summary = models.TextField(
        blank=True,
        verbose_name="sinopsis",
        help_text="Sinopsis breve.",
    )
    cover = models.ImageField(
        upload_to="covers/",
        blank=True,
        null=True,
        verbose_name="portada",
        help_text="Portada de la pelicula. Requiere Pillow.",
    )

    # Paso 2: relacion muchos a muchos con los generos.
    # related_name="movies" permite listar desde el genero que peliculas lo usan.
    genres = models.ManyToManyField(
        Genre,
        related_name="movies",
        blank=True,
        verbose_name="generos",
        help_text="Generos de la pelicula.",
    )

    # Reparto y equipo tecnico. La relacion tambien es muchos a muchos:
    # una pelicula tiene varias personas y una persona aparece en varias peliculas.
    people = models.ManyToManyField(
        Person,
        related_name="movies",
        blank=True,
        verbose_name="reparto",
        help_text="Reparto y equipo tecnico.",
    )

    # Paso 7: campos de auditoria. El admin los mostrara en solo lectura.
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="creada el",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="ultima modificacion",
    )

    class Meta:
        # El panel y la API ordenan de la pelicula mas reciente a la mas antigua.
        ordering = ["-created_at"]
        verbose_name = "Pelicula"
        verbose_name_plural = "Peliculas"
        indexes = [
            # El paso 5 filtra el panel por ano y el paso 10 ordena por valoracion.
            models.Index(fields=["year"], name="movie_year_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.year})"

    @property
    def average_score(self) -> float | None:
        """Puntuacion media de las valoraciones, o None si no tiene ninguna.

        El paso 10 usa este valor para ordenar "las peliculas del mismo
        genero mejor valoradas".
        """
        aggregate = self.ratings.aggregate(average=models.Avg("score"))
        average = aggregate["average"]
        return round(average, 2) if average is not None else None

    @property
    def ratings_count(self) -> int:
        """Numero de valoraciones recibidas."""
        return self.ratings.count()


class Rating(models.Model):
    """Valoracion de una pelicula. Es una linea dentro de la pelicula (paso 6)."""

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name="pelicula",
    )
    score = models.PositiveSmallIntegerField(
        verbose_name="puntuacion",
        validators=[MinValueValidator(RATING_MIN), MaxValueValidator(RATING_MAX)],
        help_text=f"Puntuacion de {RATING_MIN} a {RATING_MAX}.",
    )
    comment = models.TextField(
        blank=True,
        verbose_name="comentario",
        help_text="Comentario opcional de quien valora.",
    )
    author = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="autor",
        help_text="Nombre de quien emite la valoracion.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="creada el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="ultima modificacion")

    class Meta:
        # Dentro del inline del admin las valoraciones mas recientes van primero.
        ordering = ["-created_at"]
        verbose_name = "Valoracion"
        verbose_name_plural = "Valoraciones"
        constraints = [
            # Una persona no puede valorar dos veces la misma pelicula.
            models.UniqueConstraint(
                fields=["movie", "author"],
                condition=~models.Q(author=""),
                name="unique_rating_per_author_and_movie",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.score}/10 - {self.movie} (por {self.author or 'anonimo'})"
