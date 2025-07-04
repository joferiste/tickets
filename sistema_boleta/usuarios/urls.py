from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('crear/', views.CreacionUsuarios, name='create_usuario'),
    path('crear_estado/', views.crear_estado, name='crear_estado'),
    path('visualizar_usuario/', views.visualizar_usuario, name='visualizar_usuario'),
    path('editar_usuario/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('actualizar_usuario/', views.actualizar_usuario, name='actualizar_usuario'),
    path('delete_usuario/', views.delete_usuario, name='delete_usuario'),
    path('usuario_negocio/', views.usuario_negocio, name='usuario_negocio'),
    path('desasignar_negocio/<int:negocio_id>/', views.desasignar_negocio, name='desasignar_negocio'),
]
