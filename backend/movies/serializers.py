"""
Serializadores de la API - paso 10.

La API es de solo lectura: el panel de administracion es el unico sitio donde
se escriben los datos. Por eso todos los ModelViewSet usan ReadOnlyModelViewSet.
"""

from rest_framework import serializers

from .models import Genre, Movie, Person, Rating


class GenreSerializer(serializers.ModelSerializer):
    movie_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Genre
        fields = ["id", "name", "movie_count"]


class PersonSerializer(serializers.ModelSerializer):
    movie_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Person
        fields = ["id", "name", "movie_count"]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "score", "comment", "author", "created_at"]
        read_only_fields = fields


class MovieSerializer(serializers.ModelSerializer):
    """Pelicula completa, con generos, reparto, media y numero de valoraciones."""

    genres = GenreSerializer(many=True, read_only=True)
    people = PersonSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    # `source` traduce el alias de la anotacion (media / total_valoraciones)
    # al nombre publico del JSON. Ver movies.views.peliculas_con_notas().
    average_score = serializers.FloatField(source="media", read_only=True)
    ratings_count = serializers.IntegerField(source="total_valoraciones", read_only=True)
    cover = serializers.ImageField(read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "year",
            "summary",
            "cover",
            "genres",
            "people",
            "ratings",
            "average_score",
            "ratings_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MovieRecommendationSerializer(serializers.ModelSerializer):
    """
    Version ligera para la vista de recomendacion del paso 10.

    No arrastra las valoraciones una a una: el frontend solo necesita la
    media y el numero de valores, no todos los comentarios.
    """

    genres = GenreSerializer(many=True, read_only=True)
    average_score = serializers.FloatField(source="media", read_only=True)
    ratings_count = serializers.IntegerField(source="total_valoraciones", read_only=True)
    cover = serializers.ImageField(read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "year",
            "summary",
            "cover",
            "genres",
            "average_score",
            "ratings_count",
        ]
        read_only_fields = fields
