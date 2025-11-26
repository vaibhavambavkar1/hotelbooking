from additional_service.models import ServiceOrder, ServiceOrderItem
from payment_service.models import FinalBill
from django.http import HttpResponse,JsonResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import Booking
from django.shortcuts import render, get_object_or_404,redirect,reverse
from django.contrib import messages
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from booking_service.models import Room
from django.utils import timezone
from django.contrib import admin
from datetime import datetime,date,timedelta

def download_bill_pdf(request, booking_id):
    bill = FinalBill.objects.get(booking_id=booking_id)
    service_orders = ServiceOrder.objects.filter(
        booking_id=booking_id,
    )

    service_order_items = ServiceOrderItem.objects.filter(order__booking=booking_id)
    booking = bill.booking

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="bill_{booking.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []


    story.append(Paragraph("<b>Hotel Final Bill</b>", styles['Title']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Booking ID:</b> {booking.id}", styles['Normal']))
    story.append(Paragraph(f"<b>Customer:</b> {booking.customer.first_name} {booking.customer.last_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Room Number:</b> {booking.room.id}", styles['Normal']))
    story.append(Paragraph(f"<b>Check-in:</b> {booking.checkin_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Check-out:</b> {booking.checkout_date}", styles['Normal']))
    story.append(Spacer(1, 12))

    room_data = [
        ["Description", "Days", "Rate", "Amount"],
        [f"Room {booking.room.id} ({booking.room.room_type.name})",
         booking.num_days, f"{booking.room.room_type.base_rate} INR", f"{bill.subtotal_room} INR"]
    ]
    room_table = Table(room_data, colWidths=[200, 60, 80, 80])
    room_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER')
    ]))
    story.append(Paragraph("<b>Room Charges</b>", styles['Heading3']))
    story.append(room_table)
    story.append(Spacer(1, 12))

    if service_order_items:
        service_data = [["Service", "Qty", "Unit Price", "Amount"]]
        for s in service_order_items:
            service_data.append([s.service_item.name, s.quantity, f"{s.price} INR", f"{s.subtotal} INR"])

        service_table = Table(service_data, colWidths=[200, 60, 80, 80])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER')
        ]))
        story.append(Paragraph("<b>Additional Services</b>", styles['Heading3']))
        story.append(service_table)
        story.append(Spacer(1, 12))

    totals_data = [
        ["Room Total", f"{bill.subtotal_room} INR"],
        ["Service Total", f" {bill.subtotal_services} INR"],
        ["Tax", f" {bill.tax} INR"],
        ["Total Payable", f"{bill.total} INR"]
    ]
    totals_table = Table(totals_data, colWidths=[200, 120])
    totals_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT')
    ]))
    story.append(Paragraph("<b>Summary</b>", styles['Heading3']))
    story.append(totals_table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Thank you for staying with us!</i>", styles['Italic']))

    doc.build(story)
    return response

def booking_calendar(request):
    return render(request, "admin/booking_calendar.html")


def booking_events(request):
    events = []

    rooms = Room.objects.all()
    bookings = Booking.objects.select_related('room').all()

    # 1. Create booking events
    for booking in bookings:
        events.append({
            "title": f"Room {booking.room.id} – {booking.booking_status}",
            "room": booking.room.id,
            "status": booking.booking_status,
            "start": str(booking.checkin_date),
            "end": str(booking.checkout_date),
            "backgroundColor": (
                "teal" if booking.booking_status == Booking.BookingStatus.CHECKIN else
                "orange" if booking.booking_status == Booking.BookingStatus.RESERVED else
                "blue" if booking.booking_status == Booking.BookingStatus.CANCELLED else
                "gray"
            ),
            "borderColor": "black",
        })

    # 2. Generate availability for each room for next 30 days
    today = date.today()
    next_30_days = [today + timedelta(days=i) for i in range(180)]

    for room in rooms:
        for day in next_30_days:
            # Check if this room is booked on this date
            is_booked = bookings.filter(
                room=room,
                checkin_date__lte=day,
                checkout_date__gt=day
            ).exists()

            if not is_booked:
                # Create "Available" entry
                events.append({
                    "title": f"Room {room.id} – Available",
                    "room": room.id,
                    "status": "available",
                    "start": str(day),
                    "end": str(day + timedelta(days=1)),
                    "backgroundColor": "green",
                    "borderColor": "darkgreen",
                })

    return JsonResponse(events, safe=False)


@transaction.atomic
def cancel_reservation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.booking_status in [Booking.BookingStatus.CHECKOUT, Booking.BookingStatus.CANCELLED]:
        messages.warning(request, "This booking cannot be cancelled.")
    else:
        booking.booking_status = Booking.BookingStatus.CANCELLED
        if booking.room:
            booking.room.status = "available"
            booking.room.save(update_fields=["status"])
            cancel_msg=f"Reservation cancelled with status Room checkin: {booking.checkin_date} Room checkout: {booking.checkout_date}"
            booking.notes=cancel_msg
            booking.checkin_date=None
            booking.checkout_date=None
            booking.save(update_fields=["booking_status","checkin_date","checkout_date","notes"],skip_status_update=True)

        messages.success(request, f"Booking {booking.id} has been cancelled successfully!")
    return redirect(reverse("admin:booking_service_booking_changelist"))


@transaction.atomic
def checkout_room(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.booking_status in [Booking.BookingStatus.CHECKIN]:
        booking.booking_status = Booking.BookingStatus.CHECKOUT
        if booking.room:
            booking.room.status = "available"
            booking.room.save(update_fields=["status"])
            booking.save(update_fields=["booking_status"],skip_status_update=True)

        messages.success(request, f"Booking {booking.id} has been checked out successfully!")
    return redirect(reverse("admin:booking_service_booking_changelist"))


@transaction.atomic
def checkin_room(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.booking_status in [Booking.BookingStatus.RESERVED]:
        booking.booking_status = Booking.BookingStatus.CHECKIN
        if booking.room:
            booking.room.status = Room.Status.OCCUPIED
            booking.room.save(update_fields=["status"])
            booking.save(update_fields=["booking_status"],skip_status_update=True)

        messages.success(request, f"Booking {booking.id} has been checked in successfully!")
    return redirect(reverse("admin:booking_service_booking_changelist"))


@staff_member_required
def booking_dashboard(request):
    today = timezone.now().date()

    rooms = Room.objects.all()

    bookings = Booking.objects.filter(
        Q(booking_status=Booking.BookingStatus.RESERVED) |
        Q(booking_status=Booking.BookingStatus.CHECKIN)
    ).select_related("room", "customer")

    context = {
        "total_rooms": rooms.count(),
        "available": rooms.filter(status=Room.Status.AVAILABLE).count(),
        "reserved": rooms.filter(status=Room.Status.RESERVED).count(),
        "occupied": rooms.filter(status=Room.Status.OCCUPIED).count(),
        "maintenance": rooms.filter(status=Room.Status.MAINTENANCE).count(),
        "checkout_today": Booking.objects.filter(checkout_date=today).count(),
        "rooms": rooms,
        "bookings": bookings,
    }
    return render(request, "admin/rooms_dashboard.html", context)

def advertisement(request):
    context = admin.site.each_context(request)
    rooms = (
        Room.objects
        .select_related("room_type")                  # load RoomType in same query
        .prefetch_related("photos")                   # load all room photos
        .prefetch_related("room_type__amenities")     # load amenities
        # .filter(status=Room.Status.AVAILABLE)         # show only available rooms
        .order_by("floor")                            # optional sorting
    )
    context.update({
        "rooms": rooms,
        "hotel_name": "Hotel Paradise",
        "adult_range": range(1, 11),
        "child_range": range(0, 6)
    })
    return render(request, "admin/advertise.html", context)

def availability_for_date(request):
    date_str = request.GET.get("date")
    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    rooms = Room.objects.all()
    booked = Booking.objects.filter(
        Q(check_in__lte=date) & Q(check_out__gt=date)
    ).values_list("room_id", flat=True)

    available_rooms = rooms.exclude(id__in=booked)

    return render(request, "availability.html", {
        "date": date,
        "available_rooms": available_rooms,
        "booked_rooms": rooms.filter(id__in=booked),
    })


def availability_calendar(request):
    today = date.today()
    days = [today + timedelta(days=i) for i in range(30)]
    rooms = Room.objects.all()

    calendar = []

    for d in days:
        booked_ids = list(
            Booking.objects.filter(
                checkin_date__lte=d,
                checkout_date__gt=d
            ).values_list("room_id", flat=True)
        )

        calendar.append({
            "date": d,
            "available": rooms.exclude(id__in=booked_ids),
            "booked": rooms.filter(id__in=booked_ids),
            "available_count": rooms.exclude(id__in=booked_ids).count(),
            "booked_count": rooms.filter(id__in=booked_ids).count(),
        })

    return render(request, "schedule/availability_calendar.html", {
        "calendar": calendar
    })


# def booking_events(request):
#     events = []
#     bookings = Booking.objects.select_related("room")
#
#     for b in bookings:
#         status_color = {
#             "reserved": "#FFA500",    # Orange
#             "checkin": "#008000",     # Green
#             "occupied": "#0000FF",    # Blue
#             "checkout": "#FF0000",    # Red
#             "cancelled": "#808080"    # Gray
#         }.get(b.status, "#999999")
#
#         events.append({
#             "id": b.id,
#             "title": f"{b.room.name} ({b.status})",
#             "start": str(b.check_in),
#             "end": str(b.check_out),
#             "backgroundColor": status_color,
#             "borderColor": status_color,
#         })
#
#     return JsonResponse(events, safe=False)

def sample(request):
    context = {
        "adult_range": range(1, 11),
        "child_range": range(0, 6)
    }
    return render(request, "admin/arbnb_form.html",context)