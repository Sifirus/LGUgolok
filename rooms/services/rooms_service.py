from booking.models import Booking
from rooms.models import Room


def get_available_rooms(event_date, event_start_time, event_end_time):
    busy_rooms = Booking.objects.filter(
        event_date__exact=event_date,
        event_start_time__lt=event_end_time,
        event_end_time__gt=event_start_time
    ).values_list('room_id', flat=True)

    available_rooms = Room.objects.exclude(id__in=busy_rooms).filter(status='active')

    return available_rooms