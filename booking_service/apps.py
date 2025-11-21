from django.apps import AppConfig


class BookingServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking_service'
    label= 'booking_service'
    icon = 'fa fa-sign-in'
    priority = 2

    def ready(self):
        import booking_service.signals  # noqa
