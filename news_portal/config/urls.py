from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Paso 9: las rutas propias de la app news.
    path('', include('news.urls')),
]

# En desarrollo se sirven los archivos de media desde el propio servidor.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
