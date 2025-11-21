from django.apps import AppConfig


class AdditionalServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'additional_service'
    icon = 'fa fa-cart-plus'
    priority = 3

    def ready(self):
        import additional_service.signals  # noqa
