from booking.models import Booking
from django.db.models import Q

from equipment.models import Equipment


class AvailableEquipmentService:
    BLOCKING_STATES = (
        Booking.Status.APPROVED,
        Booking.Status.PENDING,
        Booking.Status.CREATED,
    )

    @staticmethod
    def get_available_equipment(queryset, event_date, event_start_time, event_end_time):
        if not all([event_date, event_start_time, event_end_time]):
            raise ValueError('Не заполнены дата и время события')

        busy_equipment = Booking.objects.filter(
            status__in=AvailableEquipmentService.BLOCKING_STATES,
            event_date__exact=event_date,
            event_start_time__lt=event_end_time,
            event_end_time__gt=event_start_time,
        ).values_list('equipment__id', flat=True)

        available_equipment = queryset.exclude(id__in=busy_equipment).filter(status='active', is_stationary=False)

        return available_equipment


class EquipmentFiltersService:
    @staticmethod
    def apply_filters(queryset, data):

        if data.get('search_query'):
            search_query = data.get('search_query')
            for word in search_query.split():
                matching_types = [
                    value for value, label in Equipment.TypeChoices.choices
                    if word.lower() in label.lower()
                ]
                queryset = queryset.filter(
                    Q(name__icontains=word) |
                    Q(model__icontains=word) |
                    Q(type__in=matching_types)
                )

        if data.get('room_id'):
            room_id = data.get('room_id')
            queryset = queryset.filter(room_id=room_id)

        return queryset
