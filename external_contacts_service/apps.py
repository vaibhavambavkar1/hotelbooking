from django.apps import AppConfig


class ExternalContactsServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'external_contacts_service'
    icon='fa fa-mobile'
    priority=5
