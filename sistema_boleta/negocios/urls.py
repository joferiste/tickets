from django.urls import path
from . import views
from .views import PerfilNegocioView

app_name = 'negocios'

urlpatterns = [
    path('crear/', views.CreacionNegocios, name='create_negocio'),
    path('crear_estado/', views.crear_estado, name='crear_estado'),
    path('crear_categoria/', views.crear_categoria, name='crear_categoria'),
    path('visualizar_negocio/', views.visualizar_negocio, name='visualizar_negocio'),
    path('editar_negocio/<int:id>/', views.editar_negocio, name='editar_negocio'),
    path('actualizar_negocio/', views.actualizar_negocio, name='actualizar_negocio'),
    path('delete_negocio/', views.delete_negocio, name='delete_negocio'),
    path('negocio_local/', views.negocio_local, name='negocio_local'),
    path('desasignar_local/<int:ocupacion_id>/', views.desasignar_local, name='desasignar_local'),
    path('<int:pk>/perfil/', views.PerfilNegocioView.as_view(), name='perfil_negocio'),
    path('enviar_recibo/<int:recibo_id>/', views.enviar_recibo, name='enviar_recibo'),
    path('reenviar_recibo/<int:recibo_id>/', views.reenviar_recibo, name='reenviar_recibo'),
    path('recibo_detalles/<int:recibo_id>/', views.recibo_detalles, name='recibo_detalles'),
    path('mantenimientos/', views.mantenimiento_negocios, name='mantenimiento_negocios'),
    path('mantenimientos/eliminar/', views.eliminar_elemento_negocio, name='eliminar_elemento_negocio'),

]