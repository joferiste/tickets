from django.contrib import admin
from usuarios.models import Usuario, EstadoUsuario


admin.site.register(Usuario)
admin.site.register(EstadoUsuario)