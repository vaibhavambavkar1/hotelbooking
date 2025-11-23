
from django.urls import path
from .views import download_bill_pdf,booking_calendar,booking_events,cancel_reservation,checkout_room,checkin_room,advertisement
from .services import room_dashboard


urlpatterns = [
    path('download-bill/<uuid:booking_id>/', download_bill_pdf, name='download_bill_pdf'),
    path('calendar/', booking_calendar, name='booking_calendar'),
    path('calendar/events/', booking_events, name='booking_events'),
    path("cancel_reservation/<uuid:booking_id>/", cancel_reservation, name="cancel_reservation"),
    path("checkout_room/<uuid:booking_id>/", checkout_room, name="checkout_room"),
    path("checkin_room/<uuid:booking_id>/", checkin_room, name="checkin_room"),
    path("room-dashboard", room_dashboard, name="room_dashboard"),
    path("advertise", advertisement, name="advertise"),
]
