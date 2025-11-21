from django.contrib import admin
from .models import RoomType, Room, RoomPhoto,Amenity
from utils.images.image_utils import image_view
from utils.colors.color_utils import colored_status


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "description","image_preview")
    search_fields = ()
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        return image_view(obj)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "base_rate")
    search_fields = ()
    list_filter = ()



class RoomPhotoInline(admin.TabularInline):
    model = RoomPhoto
    extra = 1
    fields = ("image", "caption", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        return image_view(obj)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_type", "floor","status_color", "housekeeping_status")
    search_fields = ("id", "room_type__name")
    list_filter = ("status", "housekeeping_status", "floor", "room_type")
    inlines = [RoomPhotoInline]
    readonly_fields = ("created_at",)

    def status_color(self, obj):
        return colored_status(obj)
