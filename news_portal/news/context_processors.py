from .models import Category


def sidebar_categories(request):
    """Expone las categorias en la barra lateral de todas las paginas."""
    return {'sidebar_categories': Category.objects.all()}
