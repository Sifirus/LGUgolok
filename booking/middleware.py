from django.utils import timezone
from django.db.models import Q
from .models import Booking


class AutoCompleteBookingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.update_completed_bookings()

        response = self.get_response(request)
        return response

    def update_completed_bookings(self):
        current_datetime = timezone.now()
        current_time = current_datetime.time()
        current_date = current_datetime.date()
        #TODO notif
        bookings_to_complete = Booking.objects.filter(
            status=Booking.Status.APPROVED
        ).filter(
            Q(event_date__lt=current_date) |
            Q(event_date=current_date, event_end_time__lt=current_time)
        )

        bookings_to_complete.update(status=Booking.Status.COMPLETED)
