from django.db import models,transaction
from django.core.exceptions import ValidationError
import uuid
from room_service.models import Room
from django.utils import timezone
from decimal import Decimal

class Booking(models.Model):
    class BookingStatus(models.TextChoices):
        RESERVED = "reserved", "Reserved"
        OCCUPIED = "occupied", "Occupied"
        CHECKIN = "checkin", "checkin"
        CHECKOUT = "checkout", "checkout"
        CANCELLED = "cancelled","cancelled"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey('customer_service.Customer', on_delete=models.CASCADE, related_name='bookings',null=False)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings',null=False)
    checkin_date = models.DateField(null=True, blank=True,db_index=True)
    checkout_date = models.DateField(null=True, blank=True,db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0,null=True, blank=True)
    is_ac = models.BooleanField(default=False, help_text="Did the customer opt for AC?")
    notes = models.TextField(blank=True, null=True)
    num_days = models.PositiveIntegerField(editable=False, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booking_status=models.CharField(max_length=20, choices=BookingStatus.choices, db_index=True)

    class Meta:
        ordering = ['-created_at']


    def __str__(self):
        return f"Booking {self.id} - {self.room.id} ({self.customer.first_name }_{self.customer.last_name})"


    def clean(self):
        if self.checkin_date and self.checkout_date and self.checkin_date >= self.checkout_date:
            raise ValidationError("Checkout date must be after check-in date.")

        today = timezone.now().date()
        if self.checkin_date and self.checkin_date < today:
            raise ValidationError("Check-in date cannot be earlier than today.")

        if self.room and (self.room.status in ["reserved","maintenance"]):
            raise ValidationError(f"Room is currently not available for booking.")

        else:
            overlapping = Booking.objects.filter(
                room=self.room,
                checkin_date__lt=self.checkout_date,
                checkout_date__gt=self.checkin_date
            ).exclude(
                id=self.id
            ).exclude(
                booking_status__in=[Booking.BookingStatus.CANCELLED, Booking.BookingStatus.CHECKOUT]
            )

            if overlapping.exists():
                raise ValidationError(f"Room {self.room.id} is already booked for the selected dates.")


    def save(self, *args, **kwargs):
        skip_status_update = kwargs.pop('skip_status_update', False)
        is_new = self._state.adding
        if not skip_status_update:
            if self.checkin_date and self.checkout_date:
                self.num_days = max((self.checkout_date - self.checkin_date).days, 1)

            if self.checkin_date <= timezone.now().date() < self.checkout_date:
                new_room_status = Room.Status.OCCUPIED
                new_booking_status = self.BookingStatus.CHECKIN
            else:
                new_room_status = Room.Status.RESERVED
                new_booking_status = self.BookingStatus.RESERVED

            with transaction.atomic():
                super().save(*args, **kwargs)
                if self.room and self.room.status != new_room_status:
                    self.room.status = new_room_status
                    self.room.save(update_fields=["status"])

                if self.booking_status != new_booking_status:
                    type(self).objects.filter(pk=self.pk).update(booking_status=new_booking_status)

                # Auto-create initial booking segment for new bookings
                if is_new and self.checkin_date:
                    BookingSegment.objects.get_or_create(
                        booking=self,
                        start_date=self.checkin_date,
                        defaults={
                            'room': self.room,
                            'is_ac': self.is_ac,
                            'end_date': None,
                            'reason': 'Initial booking',
                        }
                    )
        else:
            with transaction.atomic():
                super().save(*args, **kwargs)


class Guest(models.Model):
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='guests'
    )
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    unique_id = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.age})"


class BookingSegment(models.Model):
    """Tracks each phase of a booking where room or AC preference changes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='segments')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='booking_segments')
    is_ac = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null = ongoing (current segment)
    reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date', 'created_at']
        verbose_name = "Booking Segment"
        verbose_name_plural = "Booking Segments"

    def __str__(self):
        ac_label = "AC" if self.is_ac else "Non-AC"
        end = self.end_date or "ongoing"
        return f"Room {self.room.id} ({ac_label}) : {self.start_date} → {end}"

    @property
    def days(self):
        """Number of days in this segment."""
        end = self.end_date or self.booking.checkout_date
        if end and self.start_date:
            return max((end - self.start_date).days, 0)
        return 0

    @property
    def rate(self):
        """Per-day rate for this segment based on room type and AC preference."""
        if self.is_ac and self.room.room_type.ac_rate:
            return self.room.room_type.ac_rate
        return self.room.room_type.base_rate

    @property
    def amount(self):
        """Total amount for this segment."""
        return self.rate * Decimal(max(self.days, 1))


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile = models.CharField(max_length=20)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} - {self.email}"
