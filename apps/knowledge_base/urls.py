from django.urls import path
from . import views

app_name = 'knowledge_base'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='list'),
    path('new/', views.article_create, name='create'),
    path('<int:pk>/', views.ArticleDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.article_update, name='update'),
    path('<int:pk>/delete/', views.article_delete, name='delete'),
]
