
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
