from django.contrib import admin
from .models import Tax

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("name", "percentage", "category", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)
    ordering = ("category", "name")
