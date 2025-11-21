from django.db import models
from decimal import Decimal

class Tax(models.Model):
    CATEGORY_CHOICES = (
        ("room", "Room"),
        ("food", "Food"),
        ("service", "Extra Service"),
        ("misc", "Miscellaneous")
    )

    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


    def get_room_gst_percentage(self,room_rate):
        if room_rate <= 1000:
            return Decimal('0')
        elif room_rate <= 7500:
            return Decimal('12')
        else:
            return Decimal('18')
