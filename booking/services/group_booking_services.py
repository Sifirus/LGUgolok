from datetime import date, time

from rooms.services.rooms_service import AvailableRoomsService
from equipment.services.equipment_service import AvailableEquipmentService
from rooms.models import Room
from equipment.models import Equipment


class GroupConflictService:
    """
    Для набора слотов (дата+время+participants) возвращает матрицу доступности
    всех активных аудиторий и переносного оборудования.
    """

    @staticmethod
    def check(slots: list[dict]) -> dict:
        rooms = Room.objects.filter(status='active').order_by('building', 'name')
        equip = Equipment.objects.filter(
            status='active', is_stationary=False
        ).order_by('type', 'name')

        rooms_result = []
        for room in rooms:
            free, conflicts = [], []

            for slot in slots:
                try:
                    participants = int(slot.get('participants', 0) or 0)
                    slot_date = slot['date']
                    slot_start = slot['start']
                    slot_end = slot['end']

                    if room.capacity is not None and participants > room.capacity:
                        conflicts.append(slot_date.isoformat())
                        continue

                    qs = AvailableRoomsService.get_available_rooms(
                        Room.objects.filter(pk=room.pk),
                        slot_date, slot_start, slot_end,
                    )
                    (free if qs.exists() else conflicts).append(slot_date.isoformat())
                except ValueError:
                    free.append(slot['date'].isoformat())

            rooms_result.append({
                'id': room.pk,
                'name': room.name,
                'building': room.building,
                'floor': room.floor,
                'capacity': room.capacity,
                'type_key': room.type,
                'type': room.get_type_display(),
                'free': free,
                'conflicts': conflicts,
                'conflict_count': len(conflicts),
            })

        rooms_result.sort(key=lambda r: r['conflict_count'])

        equip_result = []
        for eq in equip:
            free, conflicts = [], []
            for slot in slots:
                try:
                    qs = AvailableEquipmentService.get_available_equipment(
                        Equipment.objects.filter(pk=eq.pk),
                        slot['date'], slot['start'], slot['end'],
                    )
                    (free if qs.exists() else conflicts).append(slot['date'].isoformat())
                except ValueError:
                    free.append(slot['date'].isoformat())

            equip_result.append({
                'id': eq.pk,
                'name': eq.name,
                'model': eq.model,
                'type': eq.get_type_display(),
                'type_key': eq.type,
                'inventory': eq.inventory_number,
                'free': free,
                'conflicts': conflicts,
                'conflict_count': len(conflicts),
            })

        equip_result.sort(key=lambda e: e['conflict_count'])

        return {'rooms': rooms_result, 'equipment': equip_result}


class GroupCreateService:
    """Создаёт BookingGroup и все подзаявки из финального набора слотов."""

    @staticmethod
    def create(initiator, title: str, comment: str,
               date_from: date, date_to: date,
               slots: list[dict]):
        from booking.models import Booking, BookingGroup
        from approval.services.approval_services import ApprovalEngine

        if date_from < date.today():
            raise ValueError('Дата серии не может быть в прошлом')
        if date_to < date_from:
            raise ValueError('Дата окончания серии не может быть раньше даты начала')

        normalized_slots = []
        engine_statuses = []

        for slot in slots:
            if slot['end'] <= slot['start']:
                raise ValueError(
                    f"В слоте {slot['date'].isoformat()} время окончания должно быть позже времени начала"
                )

            if not (date_from <= slot['date'] <= date_to):
                raise ValueError(
                    f"Дата слота {slot['date'].isoformat()} вне периода серии"
                )

            room = Room.objects.get(pk=slot['room_id'])
            participants = int(slot.get('participants', 0) or 0)

            if room.capacity is not None and participants > room.capacity:
                raise ValueError(
                    f"Аудитория «{room.name}» в слоте {slot['date'].isoformat()} "
                    f"не вмещает {participants} участников. Вместимость: {room.capacity}"
                )

            eq_qs = Equipment.objects.filter(pk__in=slot.get('equipment_ids', []))

            engine_status = ApprovalEngine.get_status(
                room, eq_qs, slot['event_type'], participants
            )
            engine_statuses.append(engine_status)

            normalized_slots.append({
                'date': slot['date'],
                'start': slot['start'],
                'end': slot['end'],
                'event_type': slot['event_type'],
                'participants': participants,
                'comment': slot.get('comment', ''),
                'room': room,
                'equipment_ids': list(slot.get('equipment_ids', [])),
            })

        needs_approval = any(status == Booking.Status.CREATED for status in engine_statuses)

        group = BookingGroup.objects.create(
            initiator=initiator,
            title=title,
            comment=comment,
            date_from=date_from,
            date_to=date_to,
        )

        for slot in normalized_slots:
            room = slot['room']
            eq_qs = Equipment.objects.filter(pk__in=slot['equipment_ids'])

            status = Booking.Status.CREATED if needs_approval else Booking.Status.APPROVED

            booking = Booking.objects.create(
                initiator=initiator,
                room=room,
                event_type=slot['event_type'],
                event_date=slot['date'],
                event_start_time=slot['start'],
                event_end_time=slot['end'],
                participants=slot['participants'],
                comment=slot['comment'] or comment,
                status=status,
                group=group,
            )
            if eq_qs.exists():
                booking.equipment.set(eq_qs)

        return group