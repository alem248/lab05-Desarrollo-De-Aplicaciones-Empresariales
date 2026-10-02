from django.db import models
from django.urls import reverse
from django.utils import timezone


class Author(models.Model):
    """Autor de las noticias."""

    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = 'autor'
        verbose_name_plural = 'autores'

    def __str__(self):
        return self.name


class Category(models.Model):
    """Categoria tematica de la noticia."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)

    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('news:category', kwargs={'slug': self.slug})


class Article(models.Model):
    """Noticia del portal."""

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    summary = models.CharField(max_length=280, blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='articles/%Y/%m/', blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='articles'
    )
    categories = models.ManyToManyField(Category, related_name='articles')

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'noticia'
        verbose_name_plural = 'noticias'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:detail', kwargs={'slug': self.slug})
