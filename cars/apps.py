from django.apps import AppConfig

class CarsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cars'

    def ready(self):
        # This acts as the "On Switch" for your signals
        import cars.signals