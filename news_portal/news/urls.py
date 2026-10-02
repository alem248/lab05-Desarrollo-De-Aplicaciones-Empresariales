from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    path('', views.home, name='home'),
    path('noticia/<slug:slug>/', views.article_detail, name='detail'),
    path('categoria/<slug:slug>/', views.category_list, name='category'),
]
