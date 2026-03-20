from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import Booking,Guest,ContactMessage
from room_service.models import Room
from import_export.formats.base_formats import XLSX, CSV
from django.urls import path
from .services import room_dashboard
from .views import booking_dashboard
from .forms import GuestInlineFormset

class GuestInline(admin.TabularInline):
    model = Guest
    extra = 0
    formset = GuestInlineFormset

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "mobile", "created_at")
    search_fields = ("name", "email", "mobile")
    list_filter = ("created_at",)


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age', 'unique_id', 'booking')
    search_fields = ('name', 'unique_id')
    list_filter = ('booking',)


@admin.register(Booking)
class BookingAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    inlines = [GuestInline]

    list_display = (
        'id',
        'customer',
        'room',
        'checkin_date',
        'checkout_date',
        'num_days',
        'booking_status',
        'total_amount',
        'cancel_reservation',
        'checkin_room',
        'view_bill_link',
        'checkout_room',
    )
    list_filter = ('checkin_date', 'checkout_date', 'room__room_type','booking_status')
    search_fields = ('customer__first_name', 'customer__last_name', 'room__id')
    autocomplete_fields = ('customer', 'room')
    readonly_fields = ('booking_status','created_at', 'updated_at')
    date_hierarchy = 'checkin_date'
    ordering = ('-created_at',)
    list_per_page = 10

    class Meta:
        widgets = {
            "checkin_date": AdminSplitDateTime(),
            "checkout_date": AdminSplitDateTime(),
        }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # When creating new booking
        if obj is None:
            form.base_fields['booking_status'].choices = [
                (Booking.BookingStatus.RESERVED, "Reserved"),
                (Booking.BookingStatus.CHECKIN, "Checkin"),
            ]
        return form


    def has_import_permission(self, request):
        return False

    def get_export_formats(self):
        return [XLSX, CSV]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            if request.resolver_match.kwargs.get("object_id"):
                kwargs["queryset"] = Room.objects.all()
            else:
                kwargs["queryset"] = Room.objects.filter(status="available")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "customer",
                "room",
                "checkin_date",
                "checkout_date",
                "num_days",
                "total_amount",
                "booking_status",
            ]
        return []

    def has_change_permission(self, request, obj=None):
        if obj:
            if obj.booking_status and obj.booking_status in [Booking.BookingStatus.CANCELLED,Booking.BookingStatus.CHECKOUT]:
                return False

        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def room_status(self, obj):
        return obj.room.status if obj.room else "-"

    def cancel_reservation(self, obj):
        if obj.booking_status not in [Booking.BookingStatus.CANCELLED, Booking.BookingStatus.CHECKOUT, Booking.BookingStatus.CHECKIN]:
            url = reverse("cancel_reservation", args=[obj.id])
            return format_html(
                f'<a href="{url}" '
                'style="background-color:#dc2626; color:white; padding:4px 10px; '
                'border-radius:6px; text-decoration:none; font-size:0.9em;">❌ Cancel</a>'
            )
        else:
            return format_html(
                '<span style="color:gray;">—</span>'
            )

    def checkout_room(self, obj):
        if obj.booking_status in [Booking.BookingStatus.CHECKIN]:
            url = reverse("checkout_room", args=[obj.id])
            return format_html(
                f'<a href="{url}" '
                'style="background-color:teal; color:white; padding:4px 10px; '
                'border-radius:6px; text-decoration:none; font-size:0.9em;">❌ Checkout</a>'
            )
        else:
            return format_html(
                '<span style="color:gray;">—</span>'
            )

    def checkin_room(self, obj):
        if obj.booking_status in [Booking.BookingStatus.RESERVED]:
            url = reverse("checkin_room", args=[obj.id])
            return format_html(
                f'<a href="{url}" '
                'style="background-color:blue; color:white; padding:4px 10px; '
                'border-radius:6px; text-decoration:none; font-size:0.9em;"> Checkin</a>'
            )
        else:
            return format_html(
                '<span style="color:gray;">—</span>'
            )


    def view_bill_link(self, obj):
        if obj.booking_status == Booking.BookingStatus.CHECKOUT and hasattr(obj, 'final_bill'):
            url = reverse('download_bill_pdf', args=[obj.id])
            return format_html(
                f'<a href="{url}" target="_blank" '
                'style="background-color:teal; color:white; padding:4px 10px; '
                'border-radius:6px; text-decoration:none; font-size:0.9em;">Download</a>'
            )
        else:
            return format_html('<span style="color:gray;">---</span>')

class MyAdminSite(admin.AdminSite):

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_links'] = [
            {
                "name": "Booking Dashboard",
                "url": reverse("room_dashboard")
            }
        ]
        return context

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("room-dashboard/", self.admin_view(booking_dashboard), name="room_dashboard"),
        ]
        return custom_urls + urls

admin_site = MyAdminSite()
# admin_site.register(Room)
# admin_site.register(Booking)
#
#     # class DashboardAdminSite(admin.AdminSite):
#     #     site_header = "Hotel Management Admin"
#     #
#     #     def each_context(self, request):
#     #         context = super().each_context(request)
#     #         context['dashboard_url'] = reverse("room_dashboard")
#     #         return context
#     #
#     # admin_site = DashboardAdminSite(name="custom_admin")

admin.site.site_header = format_html(
    'Hotel Management Admin '
    '<a href="/billing/room-dashboard" style="margin-left: 15px; background: #0d9488; color: white; padding: 5px 12px; border-radius: 6px; font-size: 0.7em; text-decoration: none; vertical-align: middle;">📊 Room Dashboard</a>'
    '<a href="/billing/calendar/" style="margin-left: 10px; background: #3b82f6; color: white; padding: 5px 12px; border-radius: 6px; font-size: 0.7em; text-decoration: none; vertical-align: middle;">📅 Calendar View</a>'
)
admin.site.site_title = "Hotel Admin Portal"
admin.site.index_title = "Welcome to Hotel Dashboard"