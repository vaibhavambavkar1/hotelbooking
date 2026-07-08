from additional_service.models import ServiceOrder, ServiceOrderItem
from payment_service.models import FinalBill
from django.http import HttpResponse,JsonResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import Booking,Guest,ContactMessage
from django.shortcuts import render, get_object_or_404,redirect,reverse
from django.contrib import messages
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from booking_service.models import Room
from django.utils import timezone
from decimal import Decimal
from django.contrib import admin
from datetime import datetime,date,timedelta
from django.db.models import Exists, OuterRef, Q
from customer_service.models import Customer

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
        ["Service Total", f"{bill.subtotal_services} INR"],
        ["Tax", f"{bill.tax} INR"],
        ["Discount", f"- {bill.discount} INR"],
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
    context = admin.site.each_context(request)
    context.update({
        "title": "Booking Calendar",
    })
    return render(request, "admin/booking_calendar.html", context)


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
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Case: Already checked out
        if booking.booking_status == Booking.BookingStatus.CHECKOUT:
            messages.info(request, f"Booking {booking.id} is already checked out.")
            return redirect(reverse("admin:booking_service_booking_changelist"))

        # Case: Missing checkout date
        if not booking.checkout_date:
            messages.error(
                request,
                f"Cannot check out booking {booking.id} because it has no check-out date."
            )
            return redirect(reverse("admin:booking_service_booking_change", args=[booking.id]))

        today = timezone.localdate()
        # Case: Too early (optional - usually hotels allow early checkout, but we follow existing logic)
        if today < booking.checkout_date:
            messages.warning(
                request,
                f"Note: Early Check-Out. Planned date was {booking.checkout_date}."
            )

        # Get or Create FinalBill to show preview
        bill, created = FinalBill.objects.get_or_create(booking=booking)
        bill.calculate_totals() # Refresh totals based on current room days and services

        if request.method == "POST":
            # 1. Update Discount from POST data
            discount_amount = request.POST.get("discount", "0")
            try:
                bill.discount = Decimal(discount_amount)
            except:
                bill.discount = Decimal("0.00")
            
            # 2. Finalize Bill
            bill.save() # This calls calculate_totals() internally which applies discount

            # 3. Perform Checkout
            if booking.booking_status == Booking.BookingStatus.CHECKIN:
                booking.booking_status = Booking.BookingStatus.CHECKOUT
                if booking.room:
                    booking.room.status = Room.Status.AVAILABLE
                    booking.room.save(update_fields=["status"])
                booking.save(update_fields=["booking_status"], skip_status_update=True)
                
                messages.success(request, f"Booking {booking.id} checked out. Final Total: {bill.total} INR")
                return redirect(reverse("admin:booking_service_booking_changelist"))
            else:
                messages.error(request, f"Booking cannot be checked out (Status: {booking.booking_status})")
                return redirect(reverse("admin:booking_service_booking_changelist"))

        # GET: Show confirmation page with bill preview
        context = {
            "booking": booking,
            "bill": bill,
            "title": f"Checkout - {booking.customer}",
            "today": today,
        }
        # We need to make sure the admin context is available if we want it to look like admin
        context.update(admin.site.each_context(request))
        return render(request, "booking/checkout_confirm.html", context)
            
    except Exception as e:
        messages.error(request, f"An error occurred during check-out: {str(e)}")
        return redirect(reverse("admin:booking_service_booking_changelist"))


@transaction.atomic
def checkin_room(request, booking_id):
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Case: Already checked in or checked out
        if booking.booking_status == Booking.BookingStatus.CHECKIN:
            messages.info(request, f"Booking {booking.id} is already checked in.")
            return redirect(reverse("admin:booking_service_booking_changelist"))
        
        if booking.booking_status == Booking.BookingStatus.CHECKOUT:
            messages.error(request, f"Cannot check in booking {booking.id} as it is already checked out.")
            return redirect(reverse("admin:booking_service_booking_changelist"))

        # Case: Missing check-in date (e.g. cancelled)
        if not booking.checkin_date:
            messages.error(
                request,
                f"Cannot check in booking {booking.id} because it has no check-in date (Status: {booking.booking_status})."
            )
            return redirect(reverse("admin:booking_service_booking_change", args=[booking.id]))

        today = timezone.localdate()

        # Case 1: Too early
        if today < booking.checkin_date:
            messages.error(
                request,
                f"Check-in allowed only on {booking.checkin_date}. You are early."
            )
            return redirect(reverse("admin:booking_service_booking_change", args=[booking.id]))

        # Case 2: Too late
        if today > booking.checkin_date:
            messages.error(
                request,
                f"Check-in date was {booking.checkin_date}. Cannot check in after the check-in date."
            )
            return redirect(reverse("admin:booking_service_booking_change", args=[booking.id]))

        if booking.booking_status == Booking.BookingStatus.RESERVED:
            booking.booking_status = Booking.BookingStatus.CHECKIN
            if booking.room:
                booking.room.status = Room.Status.OCCUPIED
                booking.room.save(update_fields=["status"])
            booking.save(update_fields=["booking_status"], skip_status_update=True)
            messages.success(request, f"Booking {booking.id} has been checked in successfully!")
        else:
            messages.warning(
                request,
                f"Booking {booking.id} cannot be checked in because it is currently in '{booking.get_booking_status_display()}' status."
            )
            
    except Exception as e:
        messages.error(request, f"An error occurred during check-in: {str(e)}")
        
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
    # Check for new booking confirmation
    new_booking_id = request.session.pop('new_booking_id', None)
    if new_booking_id:
        try:
            context['new_booking'] = Booking.objects.get(id=new_booking_id)
        except Booking.DoesNotExist:
            pass

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


def sample(request):
    context = {
        "adult_range": range(1, 11),
        "child_range": range(0, 6)
    }

def search_rooms(request):
    context={}
    checkin = request.GET.get("checkin")
    checkout = request.GET.get("checkout")
    adults= request.GET.get("adults")
    children= request.GET.get("children")

    available_rooms = Room.objects.all()

    if checkin and checkout:
        checkin = datetime.strptime(checkin, "%Y-%m-%d").date()
        checkout = datetime.strptime(checkout, "%Y-%m-%d").date()

        overlapping = Booking.objects.filter(
            room_id=OuterRef("id"),
            checkin_date__lt=checkout,
            checkout_date__gt=checkin,
        ).exclude(
            booking_status="cancelled"
        )

        available_rooms = available_rooms.annotate(
            has_overlap=Exists(overlapping)
        ).filter(has_overlap=False).select_related("room_type").prefetch_related("photos","room_type__amenities")                   # load all room photos

        context = {
            "rooms": available_rooms,
            "checkin_dt":checkin,
            "checkout_dt":checkout,
            "adults": adults,
            "children":children,
        }

    return render(request, "admin/room_search.html", context)

@transaction.atomic
def create_booking(request):
    if request.method == "POST":
        room_number = request.POST.get("room_number")
        if not Room.objects.filter(id=room_number).exists():
            messages.error(request, f"Error: Room '{room_number}' does not exist in the system.")
            return redirect(request.get_full_path())
        
        # 1. Create or Update customer
        adults_str = request.POST.get("adults")
        num_persons = int(adults_str) if adults_str and adults_str.isdigit() else 1
        
        email = request.POST.get("email") or None
        phone = request.POST.get("phone", "")
        
        customer_data = {
            "first_name": request.POST.get("first_name", ""),
            "last_name": request.POST.get("last_name", ""),
            "phone": phone,
            "dob": request.POST.get("dob") or None,
            "country": request.POST.get("country") or "Other",
            "state": request.POST.get("state") or "Other",
            "city": request.POST.get("city") or "Other",
            "address": request.POST.get("address", ""),
            "id_proof_document_number": request.POST.get("id_proof_document_number", ""),
        }
        
        if request.FILES.get("image"):
            customer_data["image"] = request.FILES.get("image")
        if request.FILES.get("id_proof"):
            customer_data["id_proof"] = request.FILES.get("id_proof")
            
        if email:
            customer, _ = Customer.objects.update_or_create(
                email=email,
                defaults=customer_data
            )
        else:
            existing_customer = Customer.objects.filter(phone=phone).first() if phone else None
            if existing_customer:
                for key, value in customer_data.items():
                    setattr(existing_customer, key, value)
                existing_customer.save()
                customer = existing_customer
            else:
                customer = Customer.objects.create(email=None, **customer_data)

        # 2. Create booking
        # Helper to parse different date formats
        def parse_date(date_str):
            for fmt in ("%b. %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Time data '{date_str}' does not match any known format")

        checkin_date = request.POST["checkin_dt"].strip()
        checkout_date = request.POST["checkout_dt"].strip()
        try:
            checkin_d = parse_date(checkin_date)
            checkout_d = parse_date(checkout_date)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect(request.get_full_path())
            
        booking = Booking.objects.create(
            customer=customer,
            room_id=request.POST["room_number"],
            checkin_date=checkin_d,
            checkout_date=checkout_d,
            notes=request.POST.get("notes", ""),
            booking_status=Booking.BookingStatus.RESERVED
        )

        #3 Create Guest Details
        for i in range(1, num_persons + 1):
            name = request.POST.get(f"person_{i}_name")
            age = request.POST.get(f"person_{i}_age")
            unique_id = request.POST.get(f"person_{i}_id")

            if name and age and unique_id:  # Validate data
                Guest.objects.create(
                    booking=booking,
                    name=name,
                    age=age,
                    unique_id=unique_id
                )
        messages.success(request, "Booking created successfully!")
        request.session['new_booking_id'] = str(booking.id)
        return redirect("advertisement")

    else:
        checkin_dt=request.GET.get("checkin_dt")
        checkout_dt=request.GET.get("checkout_dt")
        room_id=request.GET.get("room_id")
        adults = request.GET.get("adults")
        children = request.GET.get("children")
        context={}
        countries= Customer.COUNTRY_CHOICES
        cities=Customer.INDIAN_STATE_CHOICES
        context={"countries":countries,"cities":cities,"checkin_dt":checkin_dt,
            "checkout_dt":checkout_dt,"room_id":room_id,"adults": adults,
            "children":children,}
        return render(request, "booking/create_booking.html",context)

def save_contact_message(request):
    name=request.POST.get("name")
    email = request.POST.get("email")
    mobile = request.POST.get("mobile")
    message = request.POST.get("message")
    ContactMessage.objects.create(name=name,email=email,mobile=mobile,message=message)
    messages.success(request, "Message Sent successfully!")
    return redirect("advertisement")

