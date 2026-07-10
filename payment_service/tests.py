from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from tax_service.models import Tax
from room_service.models import Room, RoomType
from customer_service.models import Customer
from booking_service.models import Booking
from payment_service.models import FinalBill

class FinalBillAndCheckoutTestCase(TestCase):
    def setUp(self):
        # Create standard superuser to log in if needed
        self.user = User.objects.create_superuser(username="admin", password="password123", email="admin@test.com")
        self.client = Client()
        self.client.login(username="admin", password="password123")

        # Create a tax record
        self.tax_room = Tax.objects.create(
            name="Room Tax",
            percentage=Decimal("12.00"),
            category="room",
            active=True
        )

        # Create RoomType
        self.room_type = RoomType.objects.create(
            name="Deluxe Suite",
            capacity=2,
            base_rate=Decimal("1000.00"),
            ac_rate=Decimal("1200.00")
        )

        # Create Room
        self.room = Room.objects.create(
            id="101",
            room_type=self.room_type,
            floor=1,
            status=Room.Status.AVAILABLE
        )

        # Create Customer
        self.customer = Customer.objects.create(
            first_name="Jane",
            last_name="Doe",
            phone="1234567890",
            address="123 Main St",
            id_proof_document_number="ID123456"
        )

    def test_calculate_totals_non_ac(self):
        """Test final bill calculation for non-AC booking uses base_rate."""
        today = timezone.localdate()
        booking = Booking.objects.create(
            customer=self.customer,
            room=self.room,
            checkin_date=today,
            checkout_date=today + timedelta(days=2),
            is_ac=False,
            booking_status=Booking.BookingStatus.CHECKIN
        )

        bill = FinalBill.objects.create(booking=booking)
        bill.calculate_totals()

        # Expected calculation:
        # room_days = 2 (date difference)
        # room_rate = base_rate = 1000.00
        # subtotal_room = 1000.00 * 2 = 2000.00
        # tax = 12% of 2000.00 = 240.00
        # total = 2240.00
        self.assertEqual(bill.subtotal_room, Decimal("2000.00"))
        self.assertEqual(bill.tax, Decimal("240.00"))
        self.assertEqual(bill.total, Decimal("2240.00"))

    def test_calculate_totals_ac(self):
        """Test final bill calculation for AC booking uses ac_rate directly (not surcharge)."""
        today = timezone.localdate()
        booking = Booking.objects.create(
            customer=self.customer,
            room=self.room,
            checkin_date=today,
            checkout_date=today + timedelta(days=2),
            is_ac=True,
            booking_status=Booking.BookingStatus.CHECKIN
        )

        bill = FinalBill.objects.create(booking=booking)
        bill.calculate_totals()

        # Expected calculation:
        # room_days = 2 (date difference)
        # room_rate = ac_rate = 1200.00 (not base_rate + ac_rate)
        # subtotal_room = 1200.00 * 2 = 2400.00
        # tax = 12% of 2400.00 = 288.00
        # total = 2688.00
        self.assertEqual(bill.subtotal_room, Decimal("2400.00"))
        self.assertEqual(bill.tax, Decimal("288.00"))
        self.assertEqual(bill.total, Decimal("2688.00"))

    def test_calculate_totals_early_checkout_preview(self):
        """Test that early checkout view (GET) calculates totals dynamically based on actual days in memory."""
        checkin_date = timezone.localdate() - timedelta(days=5)
        planned_checkout = timezone.localdate() + timedelta(days=5) # 10 days total planned
        
        # Room status needs to be updated to checkin properly
        self.room.status = Room.Status.OCCUPIED
        self.room.save()

        booking = Booking.objects.create(
            customer=self.customer,
            room=self.room,
            checkin_date=checkin_date,
            checkout_date=planned_checkout,
            is_ac=False,
            booking_status=Booking.BookingStatus.CHECKIN
        )

        # GET request to checkout_room view
        url = reverse("checkout_room", args=[booking.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # The view should warning-log early checkout, set the in-memory checkout_date to today,
        # and recalculate bill subtotal dynamically.
        # Checkin was 5 days ago, planned checkout was 5 days from now.
        # Today is checkout. So actual days = 5.
        bill = FinalBill.objects.get(booking=booking)
        
        # Check that the in-memory modification on the GET view preview calculated room charges for 5 days:
        # room_rate = 1000.00 * 5 days = 5000.00
        context_bill = response.context['bill']
        self.assertEqual(context_bill.subtotal_room, Decimal("5000.00"))
        
        # Verify the database booking checkout_date hasn't changed yet on GET
        db_booking = Booking.objects.get(id=booking.id)
        self.assertEqual(db_booking.checkout_date, planned_checkout)

    def test_calculate_totals_early_checkout_confirm(self):
        """Test that early checkout confirmation (POST) updates booking checkout_date, num_days, and persists the correct bill."""
        checkin_date = timezone.localdate() - timedelta(days=5)
        planned_checkout = timezone.localdate() + timedelta(days=5)
        
        self.room.status = Room.Status.OCCUPIED
        self.room.save()

        booking = Booking.objects.create(
            customer=self.customer,
            room=self.room,
            checkin_date=checkin_date,
            checkout_date=planned_checkout,
            is_ac=False,
            booking_status=Booking.BookingStatus.CHECKIN
        )

        # POST request to confirm checkout and apply no discount
        url = reverse("checkout_room", args=[booking.id])
        response = self.client.post(url, {"discount": "0.00"})
        
        # Should redirect to changelist on successful checkout
        self.assertEqual(response.status_code, 302)

        # Check DB updates:
        # 1. Booking checkout_date should now be today
        db_booking = Booking.objects.get(id=booking.id)
        self.assertEqual(db_booking.checkout_date, timezone.localdate())
        self.assertEqual(db_booking.num_days, 5)
        self.assertEqual(db_booking.booking_status, Booking.BookingStatus.CHECKOUT)
        
        # 2. Room should be available
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, Room.Status.AVAILABLE)

        # 3. Bill total should be calculated and persisted based on 5 days (1000.00 * 5 = 5000.00 room charges)
        bill = FinalBill.objects.get(booking=booking)
        self.assertEqual(bill.subtotal_room, Decimal("5000.00"))
        self.assertEqual(bill.total, Decimal("5600.00")) # 5000 + 12% tax = 5600
