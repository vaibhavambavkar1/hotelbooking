from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ServiceOrderItem


@receiver(post_save, sender=ServiceOrderItem)
def update_order_total_on_save(sender, instance, **kwargs):
    """Recalculate order total when a ServiceOrderItem is created or updated."""
    if instance.order:
        instance.order.update_total()


@receiver(post_delete, sender=ServiceOrderItem)
def update_order_total_on_delete(sender, instance, **kwargs):
    """Recalculate order total when a ServiceOrderItem is deleted."""
    if instance.order:
        instance.order.update_total()
