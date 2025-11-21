from django.contrib import admin
from .models import FinalBill
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import XLSX, CSV

@admin.register(FinalBill)
class FinalBillAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('booking', 'subtotal_room', 'subtotal_services', 'tax', 'total', 'is_paid', 'generated_at')
    readonly_fields = ('booking','subtotal_room', 'subtotal_services', 'tax', 'total', 'generated_at')
    search_fields = ('booking__id', 'booking__customer__first_name', 'booking__customer__last_name')
    list_filter = ('is_paid','generated_at')

    def has_import_permission(self, request):
        return False

    def get_export_formats(self):
        return [XLSX, CSV]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj:  # Change view
            return False  # disables save buttons + prevents edits
        return True

    def has_add_permission(self, request):
        return False