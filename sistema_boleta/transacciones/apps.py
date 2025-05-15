from django.apps import AppConfig


class TransaccionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transacciones'

    def ready(self):
        # Importar señales aquí para asegurarse de que se registren al iniciar la aplicación
        # Esto asegura que las señales se registren cuando la aplicación esté lista
        import transacciones.signals