from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # <- Ruta del home
    path('usuarios/', include('usuarios.urls')),# <- Ruta de usuarios
    path('negocios/', include('negocios.urls')),# <- Ruta de negocios
    path('locales/', include('locales.urls'))# <- Ruta de locales
]