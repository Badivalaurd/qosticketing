from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import IsAuthenticated
from apps.dashboard import views as views_home
from apps.accounts.permissions import IsAdminRole
from apps.accounts import registration_views


urlpatterns = [
    path('admin/', admin.site.urls),
    # Intercepter avant allauth : signup → flux CUID, reset → reset par CUID
    path('accounts/signup/', RedirectView.as_view(url='/accounts/register/', permanent=False)),
    path('accounts/password/reset/', registration_views.custom_password_reset, name='account_reset_password'),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('projects/', include('apps.projects.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('knowledge-base/', include('apps.knowledge_base.urls')),
    path('reporting/', include('apps.reporting.urls')),
    path('api/', include('apps.api.urls')),
    # Swagger/OpenAPI — admin uniquement
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[IsAdminRole]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[IsAdminRole]), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[IsAdminRole]), name='redoc'),
    path('', views_home.home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Handlers d'erreurs personnalisés (actifs uniquement en DEBUG=False)
handler400 = 'django.views.defaults.bad_request'
handler403 = 'django.views.defaults.permission_denied'
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
