from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('consolidado_ingresos/', views.consolidado_ingresos, name='consolidado_ingresos'),
    path('historial_negocio/<int:negocio_id>/', views.historial_negocio, name='historial_negocio'),
    path('historial_local/<int:local_id>/', views.historial_local, name='historial_local'),
]

