from booking.models import Booking
from equipment.models import Equipment


def get_available_equipment(event_date, event_start_time, event_end_time):
    busy_equipment = Booking.objects.filter(
        event_date__exact=event_date,
        event_start_time__lt=event_end_time,
        event_end_time__gt=event_start_time,
    ).values_list('equipment__id', flat=True)

    available_equipment = Equipment.objects.exclude(id__in=busy_equipment).filter(status='active', is_stationary=False)

    return available_equipment