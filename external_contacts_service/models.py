from django.db import models
import uuid

class ContactInformation(models.Model):
    class ServiceType(models.TextChoices):
        VEHICLE_PROVIDER = "vehicle_provider", "Vehicle Provider"
        TOURIST_GUIDE = "tourist_guide", "Tourist Guide"
        HOTEL = "hotel", "Hotel"
        CAR_SERVICE = "car_service", "Car Service"
        BIKE_SERVICE = "bike_service", "Bike Service"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    service_type = models.CharField(max_length=50, choices=ServiceType.choices)
    phone = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"
        ordering = ["service_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

