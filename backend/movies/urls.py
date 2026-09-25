"""Rutas de la API REST - las consume el frontend React (paso 10)."""

from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register("genres", views.GenreViewSet, basename="genre")
router.register("people", views.PersonViewSet, basename="person")
router.register("movies", views.MovieViewSet, basename="movie")
router.register("ratings", views.RatingViewSet, basename="rating")

urlpatterns = [
    # La vista de recomendacion del enunciado, con nombre propio.
    path("recomendaciones/", views.movie_recommendations, name="movie-recommendations"),
    path("", include(router.urls)),
]
