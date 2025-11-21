from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Customer
from utils.images.image_utils import image_view,id_image_view
from import_export.formats.base_formats import XLSX, CSV

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone","address","id_proof_document_number", "image_preview","idimage_preview")
    search_fields = ("first_name", "last_name", "email", "phone","id_proof_document_number")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at","image_preview","idimage_preview")


    def has_import_permission(self, request):
        return False

    def get_export_formats(self):
        return [XLSX, CSV]

    def image_preview(self, obj):
        return image_view(obj)

    def idimage_preview(self, obj):
        return id_image_view(obj)




