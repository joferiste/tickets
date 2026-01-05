from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # <- Ruta del home
    path('usuarios/', include('usuarios.urls')),# <- Ruta de usuarios
    path('negocios/', include('negocios.urls')),# <- Ruta de negocios
    path('locales/', include('locales.urls')),# <- Ruta de locales
    path('administracion/', include('administracion.urls')),# <- Ruta de administracion
    path('configuracion/', include('configuracion.urls')), # Ruta de configuracion
    path('historiales/', include('historiales.urls')), # Ruta de historiales
    path('reportes/', include('reportes.urls')), # Ruta de reportes
]

# IMPORTANTE: Servir media files SIEMPRE (incluso con DEBUG=False)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)