from django import forms
from .models import Booking


from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

class GuestInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        # Count non-deleted forms
        total_guests = len([
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ])

        # Get room capacity
        room = self.instance.room
        if room and total_guests > room.room_type.capacity:
            raise ValidationError(
                f"Room capacity is {room.capacity}. You cannot add {total_guests} guests."
            )


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "customer",
            "room",
            "checkin_date",
            "checkout_date",
            "total_amount",
            "notes",
            "booking_status",
        ]

        widgets = {
            "customer": forms.Select(attrs={
                "class": "select select-bordered w-full"
            }),
            "room": forms.Select(attrs={
                "class": "select select-bordered w-full"
            }),
            "checkin_date": forms.DateInput(attrs={
                "type": "date",
                "class": "input input-bordered w-full"
            }),
            "checkout_date": forms.DateInput(attrs={
                "type": "date",
                "class": "input input-bordered w-full"
            }),
            "total_amount": forms.NumberInput(attrs={
                "class": "input input-bordered w-full"
            }),
            "notes": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 3,
            }),
            "booking_status": forms.Select(attrs={
                "class": "select select-bordered w-full"
            }),
        }

    # ------------------------
    # Custom validation
    # ------------------------
    def clean(self):
        cleaned = super().clean()
        checkin = cleaned.get("checkin_date")
        checkout = cleaned.get("checkout_date")

        if checkin and checkout and checkout <= checkin:
            raise forms.ValidationError("Checkout must be after check-in.")

        return cleaned
