from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('tickets', views.TicketViewSet, basename='ticket')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('projects', views.ProjectViewSet, basename='project')
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
