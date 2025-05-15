from django.apps import AppConfig


class RecibosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recibos'


    def ready(self):
        import recibos.signals