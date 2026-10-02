"""Comando para cargar datos de prueba del laboratorio."""
from datetime import timedelta
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from news.models import Article, Author, Category


def placeholder(category: str, color: tuple) -> bytes:
    import io
    img = Image.new('RGB', (800, 450), color)
    d = ImageDraw.Draw(img)
    d.text((40, 200), category, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


DATA = {
    'author': {'name': 'Redaccion Campus', 'email': 'redaccion@example.com'},
    'categories': [
        ('Tecnologia', 'tecnologia'),
        ('Deportes', 'deportes'),
        ('Cultura', 'cultura'),
    ],
    'articles': [
        ('tecnologia', 'Nuevas aulas digitales en la universidad',
         'La facultad inaugura aulas con realidad mixta para las practicas de laboratorio.'),
        ('tecnologia', 'Hackathon de software con 120 participantes',
         'El evento reune a equipos de todo el pais durante dos dias de programacion.'),
        ('deportes', 'El equipo de futbol gana el campeonato interfacultades',
         'Un gol en el minuto noventa decidio la final del torneo.'),
        ('deportes', 'Taller gratuito de ajedrez cada miercoles',
         'El club estudiantil abre sus puertas a principiantes y avanzados.'),
        ('cultura', 'Exposicion de fotografia andina en la biblioteca',
         'Una muestra recorre los paisajes de Cusco y Puno.'),
        ('cultura', 'Concierto de orquesta el viernes en el auditorio',
         'Entrada libre hasta cubrir aforo; programa de musica peruana.'),
    ],
}

COLORS = {'tecnologia': (13, 59, 102), 'deportes': (33, 122, 62), 'cultura': (148, 59, 26)}


class Command(BaseCommand):
    help = 'Carga seis noticias, tres categorias y un autor de prueba'

    def handle(self, *args, **options):
        author, _ = Author.objects.get_or_create(
            name=DATA['author']['name'], defaults={'email': DATA['author']['email']}
        )
        cats = {}
        for name, slug in DATA['categories']:
            cats[slug], _ = Category.objects.get_or_create(name=name, slug=slug)

        for i, (cat_slug, title, summary) in enumerate(DATA['articles']):
            slug = title.lower().replace(' ', '-')[:80]
            article, created = Article.objects.get_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'summary': summary,
                    'body': f'{summary}\n\nCuerpo de ejemplo de "{title}".',
                    'author': author,
                    'published_at': timezone.now() - timedelta(days=i),
                },
            )
            article.categories.set([cats[cat_slug]])
            if not article.image:
                png = placeholder(cat_slug, COLORS[cat_slug])
                article.image.save(f'{slug}.png', ContentFile(png), save=True)
            article.save()
            self.stdout.write(f'  {title} ({"nueva" if created else "existente"})')

        self.stdout.write(self.style.SUCCESS('Datos de prueba cargados.'))
