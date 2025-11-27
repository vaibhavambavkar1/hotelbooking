from django.db import models

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=False)
    image = models.ImageField(upload_to='rooms/amenity/photos/')

    def __str__(self):
        return self.name


class RoomType(models.Model):
    id = models.AutoField(primary_key=True,db_index=True)
    name = models.CharField(max_length=50)  # e.g., Deluxe, Suite
    description = models.TextField(blank=True)
    capacity = models.IntegerField()  # guests
    base_rate = models.DecimalField(max_digits=10, decimal_places=2,help_text="Rate per person")
    amenities = models.ManyToManyField('Amenity', related_name='rooms', blank=True)

    def __str__(self):
        return f"Room {self.name}"

class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        OCCUPIED = "occupied", "Occupied"
        MAINTENANCE = "maintenance", "Maintenance"
    id = models.CharField(max_length=10, primary_key=True,null=False,unique=True,db_index=True)  # room number
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    floor = models.IntegerField()
    status = models.CharField(max_length=20, choices=Status.choices)
    housekeeping_status = models.CharField(max_length=20, choices=[('clean','clean'),('dirty','dirty')], default='clean')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.id}"


class RoomPhoto(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='rooms/photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo of Room {self.room.id}"


