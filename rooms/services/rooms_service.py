from django.core.exceptions import ValidationError
from django.db.models import Q

from booking.models import Booking


class AvailableRoomsService:
    BLOCKING_STATES = (
        Booking.Status.APPROVED,
        Booking.Status.PENDING,

    )

    @staticmethod
    def get_available_rooms(queryset, event_date, event_start_time, event_end_time):
        if not all([event_date, event_start_time, event_end_time]):
            raise ValueError('Не заполнены дата и время события')

        busy_rooms = Booking.objects.filter(
            status__in=AvailableRoomsService.BLOCKING_STATES,
            event_date__exact=event_date,
            event_start_time__lt=event_end_time,
            event_end_time__gt=event_start_time
        ).values_list('room_id', flat=True)

        available_rooms = queryset.exclude(id__in=busy_rooms).filter(status='active')

        return available_rooms


class RoomsFiltersService:
    @staticmethod
    def apply_filters(queryset, data):
        if data.get('capacity'):
            capacity = data.get('capacity')
            queryset = queryset.filter(capacity__gte=capacity)

        if data.get('search_query'):
            search_query = data.get('search_query')
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(type__icontains=search_query))

        if data.get('type'):
            room_type = data.get('type')
            queryset = queryset.filter(type__iexact=room_type)

        if data.get('equipment'):
            equipment_types = data.get('equipment').split(',')
            queryset = queryset.prefetch_related('equipment')

            for item in equipment_types:
                queryset = queryset.filter(equipment__type__iexact=item.strip())

        return queryset


