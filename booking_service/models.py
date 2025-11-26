from django.db import models,transaction
from django.core.exceptions import ValidationError
import uuid
from room_service.models import Room
from django.utils import timezone

class Booking(models.Model):
    class BookingStatus(models.TextChoices):
        RESERVED = "reserved", "Reserved"
        OCCUPIED = "occupied", "Occupied"
        CHECKIN = "checkin", "checkin"
        CHECKOUT = "checkout", "checkout"
        CANCELLED = "cancelled","cancelled"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey('customer_service.Customer', on_delete=models.CASCADE, related_name='bookings',null=False)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings',null=False,limit_choices_to={'status': Room.Status.AVAILABLE})
    checkin_date = models.DateField(null=True, blank=True)
    checkout_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0,null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    num_days = models.PositiveIntegerField(editable=False, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booking_status=models.CharField(choices=BookingStatus.choices)

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
