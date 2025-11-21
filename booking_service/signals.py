from django.db.models.signals import post_save
from django.dispatch import receiver
from payment_service.models import FinalBill
from .models import Booking

@receiver(post_save, sender=Booking)
def create_final_bill_on_checkout(sender, instance, **kwargs):
    if instance.booking_status == Booking.BookingStatus.CHECKOUT:
        FinalBill.objects.get_or_create(booking=instance)
        bill = FinalBill.objects.get(booking=instance)
        Booking.objects.filter(pk=instance.pk).update(total_amount=bill.total)