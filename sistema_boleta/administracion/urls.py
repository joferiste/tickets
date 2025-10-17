from django.urls import path
from . import views


app_name = 'administracion'
 
urlpatterns = [ 
    path('sandbox/', views.boletas_sandbox, name='boletas_sandbox'), 
    path('revisar/', views.revisar_correos, name='revisar_correos'),
    path('boleta/<int:boleta_id>/', views.boleta_detalle, name='boleta_detalle'),
    path('boleta-parcial/', views.boletas_sandbox_parcial, name='boleta-parcial'),
    path('boleta_revisar/<int:sandbox_id>/', views.revisar_boletas, name='boleta_revisar'), 
    path('procesar_boleta/<int:boleta_id>/', views.procesar_boleta, name='procesar_boleta'),
    path('eliminar_sandbox/<int:boleta_id>/', views.eliminar_sandbox, name='eliminar_sandbox'),
    path("transaccion/<int:transaccion_id>/", views.perfil_transaccion, name='perfil_transaccion'),
    path('validar_transaccion/<int:transaccion_id>/', views.validar_transaccion, name='validar_transaccion'),
    path('generar_recibo/<int:transaccion_id>/', views.generar_recibo, name='generar_recibo'),
]


