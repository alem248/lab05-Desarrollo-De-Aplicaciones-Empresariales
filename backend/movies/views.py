"""
API de solo lectura - paso 10.

Esta es la "vista propia" que el enunciado contrasta con el panel:

    El panel de administracion es una herramienta de BACK OFFICE.
        Solo la ven quien tiene cuenta en el sistema, sirve para CARGAR y
        CORREGIR datos, y su interfaz la decide quien administra el sitio.

    Esta API + el frontend React es una vista PUBLICA.
        La ve cualquiera sin iniciar sesion, sirve para CONSULTAR datos, y su
        interfaz la decide quien programa.

Por eso los ModelViewSet son de solo lectura: se escribe desde el panel y se
lee desde el sitio publico.
"""

from django.db.models import Avg, Count, Q
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Genre, Movie, Person, Rating
from .serializers import (
    GenreSerializer,
    MovieRecommendationSerializer,
    MovieSerializer,
    PersonSerializer,
    RatingSerializer,
)


class RecommendationPagination(PageNumberPagination):
    """Paginacion de la vista de recomendacion, con page_size ajustable."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


def peliculas_con_notas():
    """
    Consulta base del paso 10: peliculas con su media y su nº de valoraciones.

    Con annotate se calculan en la base de datos, en una sola consulta, en
    lugar de recorrer las valoraciones en Python. El filtro `ratings__isnull=False`
    descarta las peliculas sin ninguna valoracion, porque no pueden ser
    "las mejor valoradas" de nada.

    Los alias son `media` y `total_valoraciones` y no `average_score` ni
    `ratings_count` porque en el modelo esos dos nombres son properties de solo
    lectura: `annotate()` no puede asignarlos sobre la instancia. Los
    serializadores los renombran con `source=` al montar el JSON.
    """
    return (
        Movie.objects.filter(ratings__isnull=False)
        .annotate(
            media=Avg("ratings__score"),
            total_valoraciones=Count("ratings", distinct=True),
        )
        .prefetch_related("genres")
    )


def ordenar_por_valoracion(queryset):
    """De mas a menos valorada, y a igualdad de media por titulo."""
    return queryset.order_by("-media", "title")


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """Generos, con el numero de peliculas de cada uno."""

    serializer_class = GenreSerializer
    queryset = Genre.objects.annotate(movie_count=Count("movies")).order_by("name")


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """Personas del reparto y el equipo tecnico."""

    serializer_class = PersonSerializer
    queryset = Person.objects.annotate(movie_count=Count("movies")).order_by("name")


class RatingViewSet(viewsets.ReadOnlyModelViewSet):
    """Valoraciones, de la mas reciente a la mas antigua."""

    serializer_class = RatingSerializer
    queryset = Rating.objects.select_related("movie").order_by("-created_at")


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Peliculas, por defecto las mejor valoradas primero.

    Parametros de consulta:
        ?genre=<id>      solo las peliculas de ese genero
        ?search=<texto> busca en el titulo y en el nombre del reparto
    """

    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = ordenar_por_valoracion(peliculas_con_notas())

        genero = self.request.query_params.get("genre")
        if genero:
            queryset = queryset.filter(genres__id=genero)

        busqueda = self.request.query_params.get("search")
        if busqueda:
            queryset = queryset.filter(
                Q(title__icontains=busqueda) | Q(people__name__icontains=busqueda)
            ).distinct()

        return queryset

    def get_serializer_class(self):
        # En el listado no hacen falta los comentarios: usa el serializador ligero.
        if self.action == "list":
            return MovieRecommendationSerializer
        return MovieSerializer


@api_view(["GET"])
def movie_recommendations(request):
    """
    Vista publica de recomendacion del paso 10: peliculas del mismo genero
    mejor valoradas.

    Acepta ?genre=<id>. Sin genero, devuelve todas las peliculas valoradas
    ordenadas por media descendente.
    """
    genero = request.query_params.get("genre")
    if genero is not None and not str(genero).isdigit():
        return Response(
            {"detail": "El parametro 'genre' debe ser el id numerico de un genero."},
            status=400,
        )

    queryset = ordenar_por_valoracion(peliculas_con_notas())
    if genero is not None:
        queryset = queryset.filter(genres__id=int(genero))

    paginador = RecommendationPagination()
    pagina = paginador.paginate_queryset(queryset, request)
    serializer = MovieRecommendationSerializer(pagina, many=True)
    return paginador.get_paginated_response(serializer.data)
