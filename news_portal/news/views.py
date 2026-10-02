from django.shortcuts import get_object_or_404, render

from .models import Article, Category


def home(request):
    """Portada: las noticias mas recientes."""
    articles = Article.objects.select_related('author').prefetch_related('categories')
    return render(request, 'portada.html', {'articles': articles})


def article_detail(request, slug):
    """Detalle de una noticia."""
    article = get_object_or_404(
        Article.objects.select_related('author').prefetch_related('categories'),
        slug=slug,
    )
    return render(request, 'detalle.html', {'article': article})


def category_list(request, slug):
    """Listado de noticias por categoria."""
    category = get_object_or_404(Category, slug=slug)
    articles = category.articles.select_related('author').prefetch_related('categories')
    return render(
        request, 'categoria.html', {'category': category, 'articles': articles}
    )
