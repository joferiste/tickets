from django.urls import path
from . import views

app_name = 'locales'

urlpatterns = [
    path('crear/', views.crear_local, name='create_local'),
    path('crear_estado/', views.crear_estado, name='create_estado'),
    path('crear_nivel/', views.crear_nivel, name='create_nivel'),
    path('crear_ubicacion/', views.crear_ubicacion, name='create_ubicacion'),
    path('visualizar_local/', views.visualizar_local, name='visualizar_local'),
    path('editar_local/<int:id>/', views.editar_local, name='editar_local'),
    path('actualizar_local/', views.actualizar_local, name='actualizar_local'),
    path('delete_local/', views.delete_local, name='delete_local'),

]
