from django.apps import AppConfig


class TransaccionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transacciones'
    verbose_name = 'Transacciones'

    def ready(self):
        # Importar signals cuando la app este lista
        import transacciones.signals