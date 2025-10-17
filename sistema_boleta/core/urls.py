from django.urls import path
from . import views, views_auth

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('gestion_crud/', views.gestion_crud, name='gestion_crud'),
]