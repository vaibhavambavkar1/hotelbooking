from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render
from booking_service.models import Room, Booking,ContactMessage
from django.utils import timezone
from django.contrib import admin

@staff_member_required
def room_dashboard(request):
    context = admin.site.each_context(request)
    today = timezone.now().date()

    rooms = Room.objects.all()

    bookings = Booking.objects.filter(
        Q(booking_status=Booking.BookingStatus.RESERVED) |
        Q(booking_status=Booking.BookingStatus.CHECKIN)
    ).select_related("room", "customer")
    contact_messages = ContactMessage.objects.all()
    context.update({
        "total_rooms": rooms.count(),
        "available": rooms.filter(status=Room.Status.AVAILABLE).count(),
        "reserved": rooms.filter(status=Room.Status.RESERVED).count(),
        "occupied": rooms.filter(status=Room.Status.OCCUPIED).count(),
        "maintenance": rooms.filter(status=Room.Status.MAINTENANCE).count(),
        "checkout_today": Booking.objects.filter(checkout_date=today).count(),
        "rooms": rooms,
        "bookings": bookings,
        "contact_messages":contact_messages,
    })
    return render(request, "admin/rooms_dashboard.html", context)
