from django.urls import path
from . import views

app_name = 'historiales'

urlpatterns = [
    path('metricas/', views.dashboard_metricas, name="dashboard_metricas"),
    path('api/buscar_negocios/', views.buscar_negocios_ajax, name="buscar_negocios_ajax"),
]
