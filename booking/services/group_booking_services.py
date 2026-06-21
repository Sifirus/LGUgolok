from datetime import date, time

from django.db import transaction

from rooms.services.rooms_service import AvailableRoomsService
from equipment.services.equipment_service import AvailableEquipmentService
from rooms.models import Room
from equipment.models import Equipment

from booking.models import Booking, BookingGroup
from approval.services.approval_services import ApprovalEngine


class GroupConflictService:

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

    @staticmethod
    def create(
            initiator,
            title: str,
            comment: str,
            date_from: date,
            date_to: date,
            slots: list[dict],
    ):

        if date_from < date.today():
            raise ValueError('Дата серии не может быть в прошлом')
        if date_to < date_from:
            raise ValueError('Дата окончания не может быть раньше начала')

        for slot in slots:
            if slot['end'] <= slot['start']:
                raise ValueError(
                    f"Слот {slot['date'].isoformat()}: время окончания должно быть позже начала"
                )
            if not (date_from <= slot['date'] <= date_to):
                raise ValueError(
                    f"Дата слота {slot['date'].isoformat()} вне периода серии"
                )

        with transaction.atomic():

            room_ids = {int(s['room_id']) for s in slots}
            eq_ids = {int(i) for s in slots for i in s.get('equipment_ids', [])}

            locked_rooms = {
                r.pk: r
                for r in Room.objects.select_for_update().filter(pk__in=room_ids)
            }
            locked_equip = {
                e.pk: e
                for e in Equipment.objects.select_for_update().filter(pk__in=eq_ids)
            }

            conflict_messages = []
            slot_data = []

            for slot in slots:
                room_id = int(slot['room_id'])
                room = locked_rooms.get(room_id)
                if not room:
                    raise ValueError(f"Аудитория #{room_id} не найдена")

                participants = int(slot.get('participants', 0) or 0)

                if room.capacity is not None and participants > room.capacity:
                    conflict_messages.append(
                        f"{slot['date'].isoformat()}: аудитория «{room.name}» "
                        f"не вмещает {participants} участников (макс. {room.capacity})"
                    )
                    continue

                available_room = AvailableRoomsService.get_available_rooms(
                    Room.objects.filter(pk=room.pk),
                    slot['date'], slot['start'], slot['end'],
                )
                if not available_room.exists():
                    conflict_messages.append(
                        f"{slot['date'].isoformat()}: аудитория «{room.name}» уже занята"
                    )
                    continue

                slot_eq_ids = [int(i) for i in slot.get('equipment_ids', [])]
                unavailable_eq = []
                final_eq_ids = []

                for eid in slot_eq_ids:
                    eq = locked_equip.get(eid)
                    if not eq:
                        continue
                    available_eq = AvailableEquipmentService.get_available_equipment(
                        Equipment.objects.filter(pk=eq.pk),
                        slot['date'], slot['start'], slot['end'],
                    )
                    if available_eq.exists():
                        final_eq_ids.append(eid)
                    else:
                        unavailable_eq.append(eq.name)

                if unavailable_eq:
                    conflict_messages.append(
                        f"{slot['date'].isoformat()}: оборудование занято: "
                        f"{', '.join(unavailable_eq)} — исключено из заявки"
                    )

                slot_data.append({
                    'date': slot['date'],
                    'start': slot['start'],
                    'end': slot['end'],
                    'event_type': slot.get('event_type', 'lecture'),
                    'participants': participants,
                    'comment': slot.get('comment', '') or comment,
                    'room': room,
                    'equipment_ids': final_eq_ids,
                })

            if not slot_data:
                raise ValueError(
                    'Все слоты имеют конфликты: ' + '; '.join(conflict_messages)
                )

            group = BookingGroup.objects.create(
                initiator=initiator,
                title=title,
                comment=comment,
                date_from=date_from,
                date_to=date_to,
            )

            for sd in slot_data:
                eq_qs = Equipment.objects.filter(pk__in=sd['equipment_ids'])
                slot_status = ApprovalEngine.get_status(
                    sd['room'], eq_qs, sd['event_type'], sd['participants']
                )

                booking = Booking.objects.create(
                    initiator=initiator,
                    room=sd['room'],
                    event_type=sd['event_type'],
                    event_date=sd['date'],
                    event_start_time=sd['start'],
                    event_end_time=sd['end'],
                    participants=sd['participants'],
                    comment=sd['comment'],
                    status=slot_status,
                    group=group,
                )
                if sd['equipment_ids']:
                    booking.equipment.set(sd['equipment_ids'])

        group._conflict_warnings = conflict_messages
        return group
