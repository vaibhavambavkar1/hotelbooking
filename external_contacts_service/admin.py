from django.contrib import admin
from .models import ContactInformation
from import_export.formats.base_formats import XLSX, CSV
from import_export.admin import ImportExportModelAdmin

@admin.register(ContactInformation)
class ContactInformationAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ("name", "service_type", "phone","whatsapp_number", "email", "city", "active")
    list_filter = ("service_type", "active", "city")
    search_fields = ("name", "phone", "email", "city", "state")
    ordering = ("service_type", "name")

    def has_import_permission(self, request):
        return False

    def get_export_formats(self):
        return [XLSX, CSV]