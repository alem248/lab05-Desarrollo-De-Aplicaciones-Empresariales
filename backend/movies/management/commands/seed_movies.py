"""
Carga de datos de prueba - paso 8.

El enunciado pide cargar diez peliculas, cuatro generos y valoraciones en al
menos cinco de ellas "desde el panel". Eso se puede hacer a mano, pero para
poder repetir la entrega tantas veces como haga falta, el mismo conjunto de
datos se carga con un comando:

    py manage.py seed_movies

El comando es idempotente: si una pelicula ya existe la actualiza en lugar de
duplicarla, asi que se puede ejecutar las veces que haga falta. Para empezar
de cero, con --flush borra primero todo lo cargado.

Para reproducir la carga a mano desde el panel, se imprime el detalle con:

    py manage.py seed_movies --show
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie, Person, Rating

# --- Los cuatro generos del paso 8 -----------------------------------------
GENEROS = [
    "Ciencia ficcion",
    "Drama",
    "Accion",
    "Animacion",
]

# --- Diez peliculas ---------------------------------------------------------
# (titulo, anio, [(persona, papel)], [generos], sinopsis)
PELICULAS = [
    (
        "Interestelar",
        2014,
        [("Christopher Nolan", "Director"), ("Jonathan Nolan", "Guion")],
        ["Ciencia ficcion", "Drama"],
        "Un equipo de exploradores atraviesa un agujero de gusano en busca de "
        "un nuevo hogar para la humanidad.",
    ),
    (
        "La llegada",
        2016,
        [("Denis Villeneuve", "Director"), ("Eric Heisserer", "Guion")],
        ["Ciencia ficcion", "Drama"],
        "Cuando Landing Extraterrestres llegan a la Tierra, una linguista es "
        "la unica que puede aprender a comunicarse con ellos.",
    ),
    (
        "Dune: Parte dos",
        2024,
        [("Denis Villeneuve", "Director"), ("Greta Gerwig", "Productora")],
        ["Ciencia ficcion", "Accion"],
        "Paul Atreides se une a los Fremen para luchar contra quienes "
        "destruyeron a su familia.",
    ),
    (
        "Pulp Fiction",
        1994,
        [("Quentin Tarantino", "Director"), ("Quentin Tarantino", "Guion")],
        ["Accion", "Drama"],
        "Las vidas de dos asesinos de mafia, un boxeador y una pareja se "
        "entrelazan en varias historias de violencia y humor negro.",
    ),
    (
        "La ladrona de libros",
        2019,
        [("Greta Gerwig", "Directora"), ("Greta Gerwig", "Guionista")],
        ["Drama"],
        "En el Massachusetts de 1856, una criada se convierte en institutriz "
        "de la hija de un acaudalado.",
    ),
    (
        "Perdida",
        2006,
        [("Alejandro G. Inarritu", "Director")],
        ["Drama"],
        "Un fotografo de moda queda atrapado en el patio de una casa "
        "abandonada y entabla una batalla psychological contra el lugar.",
    ),
    (
        "La quebranta",
        2000,
        [("Lucrecia Martel", "Directora"), ("Lucrecia Martel", "Guionista")],
        ["Drama"],
        "La historia de una familia en una comunidad aislada del campo, donde "
        "los impulsos se reprimen a la fuerza.",
    ),
    (
        "Viaje a la luna",
        2010,
        [("Hayao Miyazaki", "Director")],
        ["Animacion", "Drama"],
        "Un heroe de papel envejece en una casa rural junto a una anciana y "
        "una niña de siete anos.",
    ),
    (
        "Amarcord",
        1973,
        [("Federico Fellini", "Director")],
        ["Drama"],
        "La memoria documentada de la vida en un pueblo del norte de Italia "
        "durante los anos treinta.",
    ),
    (
        "Bones and All",
        2022,
        [("Denis Villeneuve", "Director"), ("Silvia Liuzzo", "Guion")],
        ["Ciencia ficcion", "Drama"],
        "Una joven que huye de casa descubre que su padre y ella comparten "
        "una misma hambre.",
    ),
]

# --- Valoraciones: siete peliculas valoradas (el paso 8 pide al menos 5) ----
# (indice de la pelicula dentro de PELICULAS, [(puntuacion, autor, comentario)])
VALORACIONES = [
    (0, [
        (10, "ana", "La mejor pelicula de ciencia ficcion que he visto."),
        (9, "beto", "La banda sonora de Zimmer se lleva el premio."),
        (8, "carla", "Se toma su tiempo, pero llega."),
    ]),
    (1, [
        (9, "ana", "El problema del lenguaje, tratado con seriedad."),
        (8, "diego", "Actuacion impecable de Amy Adams."),
    ]),
    (2, [
        (9, "carla", "Villeneuve ha mejorado la adaptacion."),
        (7, "diego", "Visualmente impecable, algo larga."),
    ]),
    (3, [
        (10, "beto", "Un hito del cine de referencia."),
        (9, "ana", "Los dialogos son memorables."),
        (7, "frank", "Divertida, aunque violentas algunas escenas."),
    ]),
    (5, [
        (8, "frank", "Un thriller sobrio y bien resuelto."),
        (6, "ana", "Mas lento de lo que parece, pero aguanta."),
    ]),
    (7, [
        (9, "ana", "La pelicula de animacion que mas me ha gustado."),
        (8, "beto", "Un viaje visual de pura imaginacion."),
    ]),
    (8, [
        (8, "carla", "Muy asumible de Fellini."),
        (7, "diego", "Menos ambiciosa que Ocho y medio."),
    ]),
]

# Credenciales de prueba que crea el paso 9.
CREDENCIALES = {
    "superusuario": ("alem248", "Cinevault2026!"),
    "editor": ("editor01", "Editor2026!"),
}


class Command(BaseCommand):
    help = "Carga los datos de prueba del paso 8 de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--show",
            action="store_true",
            help="Muestra el detalle de los datos y termina sin escribir nada.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Borra las peliculas, generos, personas y valoraciones existentes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["show"]:
            self.mostrar_datos()
            return

        if options["flush"]:
            Movie.objects.all().delete()
            Person.objects.all().delete()
            Genre.objects.all().delete()
            self.stdout.write("Datos anteriores borrados.")

        generos = {nombre: Genre.objects.get_or_create(name=nombre)[0] for nombre in GENEROS}

        for _, _, reparto, _, _ in PELICULAS:
            for nombre, _papel in reparto:
                Person.objects.get_or_create(name=nombre)

        peliculas = []
        for titulo, anio, reparto, generos_pelicula, sinopsis in PELICULAS:
            pelicula, creada = Movie.objects.get_or_create(
                title=titulo, defaults={"year": anio, "summary": sinopsis}
            )
            if not creada:
                pelicula.year = anio
                pelicula.summary = sinopsis
                pelicula.save()
            pelicula.genres.set([generos[g] for g in generos_pelicula])
            pelicula.people.set([Person.objects.get(name=nombre) for nombre, _ in reparto])
            peliculas.append(pelicula)

        for indice, lista in VALORACIONES:
            for puntuacion, autor, comentario in lista:
                Rating.objects.update_or_create(
                    movie=peliculas[indice],
                    author=autor,
                    defaults={"score": puntuacion, "comment": comentario},
                )

        valoradas = Movie.objects.filter(ratings__isnull=False).distinct().count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Datos cargados: {Genre.objects.count()} generos, "
                f"{Person.objects.count()} personas, "
                f"{Movie.objects.count()} peliculas, "
                f"{Rating.objects.count()} valoraciones."
            )
        )
        self.stdout.write(
            f"Peliculas con al menos una valoracion: {valoradas} "
            f"(el paso 8 pide al menos 5)."
        )
        self.stdout.write("")
        self.stdout.write("Cuentas de prueba:")
        for etiqueta, (usuario, clave) in CREDENCIALES.items():
            self.stdout.write(f"  {etiqueta:<13} {usuario} / {clave}")

    def mostrar_datos(self):
        """Imprime el detalle, util para reproducir la carga a mano."""
        self.stdout.write(f"GENEROS ({len(GENEROS)}):")
        for nombre in GENEROS:
            self.stdout.write(f"  - {nombre}")

        personas = sorted({n for _, _, reparto, _, _ in PELICULAS for n, _ in reparto})
        self.stdout.write("")
        self.stdout.write(f"PERSONAS ({len(personas)}):")
        for nombre in personas:
            self.stdout.write(f"  - {nombre}")

        self.stdout.write("")
        self.stdout.write(f"PELICULAS ({len(PELICULAS)}):")
        for titulo, anio, reparto, generos_pelicula, sinopsis in PELICULAS:
            self.stdout.write(f"  - {titulo} ({anio})")
            self.stdout.write(f"      generos:  {', '.join(generos_pelicula)}")
            self.stdout.write(
                "      personas: " + ", ".join(f"{n} ({p})" for n, p in reparto)
            )
            self.stdout.write(f"      sinopsis: {sinopsis}")

        self.stdout.write("")
        self.stdout.write("VALORACIONES:")
        for indice, lista in VALORACIONES:
            self.stdout.write(f"  {PELICULAS[indice][0]}:")
            for puntuacion, autor, comentario in lista:
                self.stdout.write(f"      {puntuacion}/10 - {autor}: {comentario}")
