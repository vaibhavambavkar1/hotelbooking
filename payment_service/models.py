from django.db import models
from uuid import uuid4
from decimal import Decimal
from booking_service.models import Booking
from additional_service.models import ServiceOrder
from tax_service.models import Tax
from tax_service.helper import calculate_tax,get_gst_taxes

class FinalBill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False,db_index=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='final_bill',db_index=True)
    subtotal_room = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_services = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Final Bill for Booking {self.booking.id}"


    def calculate_totals(self):
        base_rate = getattr(self.booking.room.room_type, 'base_rate', Decimal('0.00'))
        if getattr(self.booking, 'is_ac', False) and getattr(self.booking.room.room_type, 'ac_rate', None) is not None:
            ac_surcharge = getattr(self.booking.room.room_type, 'ac_rate', Decimal('0.00'))
            room_rate = base_rate + ac_surcharge
        else:
            room_rate = base_rate
            
        room_days = getattr(self.booking, 'num_days', 1)
        self.subtotal_room = room_rate * Decimal(room_days)

        service_orders = ServiceOrder.objects.filter(
            booking_id=self.booking.id,
        )

        self.subtotal_services = Decimal(sum(
            float(order.total or 0) for order in service_orders
        ))

        tax= Decimal(get_gst_taxes("room")/100)
        subtotal = self.subtotal_room + self.subtotal_services
        self.tax = subtotal * Decimal(tax)
        self.total = subtotal + self.tax - self.discount
        self.booking.total_amount=self.total
        return self.total

    # subtotal_room_with_gst_amt = calculate_tax("room", self.subtotal_room)
    # subtotal_services_with_gst_amt = calculate_tax("service", self.subtotal_services)
    # subtotal = subtotal_room_with_gst_amt + subtotal_services_with_gst_amt
    # self.total = subtotal - self.discount
    # self.booking.total_amount = self.total
    # return self.total

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)
