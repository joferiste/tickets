from django.urls import path
from . import views

app_name = 'negocios'

urlpatterns = [
    path('crear/', views.CreacionNegocios, name='create_negocio'),
    path('crear_estado/', views.crear_estado, name='crear_estado'),
    path('crear_categoria/', views.crear_categoria, name='crear_categoria'),
    path('visualizar_negocio/', views.visualizar_negocio, name='visualizar_negocio'),
    path('editar_negocio/<int:id>/', views.editar_negocio, name='editar_negocio'),
    path('actualizar_negocio/', views.actualizar_negocio, name='actualizar_negocio'),
    path('delete_negocio/', views.delete_negocio, name='delete_negocio'),

]