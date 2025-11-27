from django.db import models
from uuid import uuid4
from decimal import Decimal
from booking_service.models import Booking

class ServiceItem(models.Model):
    name = models.CharField(max_length=200,db_index=True)
    service_type = models.CharField(
        max_length=50,
        choices=[('meal', 'Meal'), ('travel', 'Travel'), ('other', 'Other')]
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='per_item')
    attributes = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name


class ServiceOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False,db_index=True)
    customer = models.ForeignKey(
        'customer_service.Customer',
        on_delete=models.CASCADE,
        related_name='service_orders'
    )
    booking = models.ForeignKey(
        'booking_service.Booking',
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name='service_orders',
        limit_choices_to={"booking_status":Booking.BookingStatus.CHECKIN},
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('ordered', 'Ordered'),
            ('cancelled', 'Cancelled')
        ],
        default='ordered'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total = total
        self.save(update_fields=['total'])


    def __str__(self):
        return f"ServiceOrder {self.id} - {self.customer.first_name}"


class ServiceOrderItem(models.Model):
    order = models.ForeignKey(
        ServiceOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    service_item = models.ForeignKey(ServiceItem, on_delete=models.PROTECT,db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    @property
    def subtotal(self):
        price = self.price or Decimal('0.00')
        return price * self.quantity

    def save(self, *args, **kwargs):
        if self.price is None and self.service_item:
            self.price = self.service_item.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service_item.name} × {self.quantity}"
