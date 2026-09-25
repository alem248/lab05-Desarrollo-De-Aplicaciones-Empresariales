"""
Registro en el panel de administracion - paso 4.

En este punto se registran los cuatro modelos con la forma mas simple
posible: `admin.site.register(Model)`. No hay ninguna vista escrita a mano;
todo lo que se ve en el panel lo genera Django automaticamente.

El paso 5 sustituye estas cuatro lineas por clases ModelAdmin.
"""

from django.contrib import admin

from .models import Genre, Movie, Person, Rating

admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Person)
admin.site.register(Rating)
