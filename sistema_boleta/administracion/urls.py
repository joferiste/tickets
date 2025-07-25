from django.urls import path
from . import views


app_name = 'administracion'

urlpatterns = [
    path('sandbox/', views.boletas_sandbox, name='boletas_sandbox'),
    path('revisar/', views.revisar_correos, name='revisar_correos'),
    path('boleta/<int:boleta_id>/', views.boleta_detalle, name='boleta_detalle'),
    path('boleta-parcial/', views.boletas_sandbox_parcial, name='boleta_parcial')
]
