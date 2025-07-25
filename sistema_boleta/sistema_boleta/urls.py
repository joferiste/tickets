from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # <- Ruta del home
    path('usuarios/', include('usuarios.urls')),# <- Ruta de usuarios
    path('negocios/', include('negocios.urls')),# <- Ruta de negocios
    path('locales/', include('locales.urls')),# <- Ruta de locales
    path('administracion/', include('administracion.urls')),# <- Ruta de administracion
    path('configuracion/', include('configuracion.urls')), # Ruta de configuracion
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)