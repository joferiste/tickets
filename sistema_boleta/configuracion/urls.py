from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    path('configuracion_sistema/', views.configuracion_sistema, name='configuracion_sistema'),
    path('crear_banco/', views.crear_banco, name='crear_banco'),
    path('mantenimientos/', views.mantenimientos, name='mantenimientos'),
    path('editar/<int:banco_id>/', views.editar_banco, name='editar_banco'),
    path('eliminar/<int:banco_id>/', views.eliminar_banco, name='eliminar_banco'),
]
