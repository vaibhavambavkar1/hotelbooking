from django.contrib import admin

from booking_service.models import Booking
from .models import ServiceItem, ServiceOrder, ServiceOrderItem

class ServiceOrderItemInline(admin.TabularInline):
    model = ServiceOrderItem
    extra = 0
    readonly_fields = ("subtotal",)

@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "service_type", "price", "unit", "display_attributes")
    search_fields = ()
    list_filter = ()

    def display_attributes(self, obj):
        if isinstance(obj.attributes, list):
            return ", ".join(map(str, obj.attributes))
        return str(obj.attributes)


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "booking__id", "status", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("customer__first_name", "booking__id")
    inlines = [ServiceOrderItemInline]
    readonly_fields = ("total","customer",)

    # def get_fields(self, request, obj=None):
    #     fields = super().get_fields(request, obj)
    #     if obj is None:  # Add form
    #         fields = [f for f in fields if f != "customer"]
    #     return fields

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_total()

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "customer",
                "booking",
            ]
        return []
    def has_change_permission(self, request, obj=None):
        if obj:
            if obj.booking and obj.booking.booking_status == Booking.BookingStatus.CHECKOUT:
                return False  # prevent edits, hide save buttons

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False