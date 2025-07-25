from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    path('configuracion_sistema/', views.configuracion_sistema, name='configuracion_sistema'),
    path('crear_banco/', views.crear_banco, name='crear_banco'),
    path('mantenimientos/', views.mantenimientos, name='mantenimientos'),

]
