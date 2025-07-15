from django.urls import path
from . import views

app_name = 'boletas'

urlpatterns = [
    path('revisar/', views.revisar_correo, name='revisar_correo')
]
