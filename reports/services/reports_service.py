from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from booking.models import Booking
from equipment.models import Equipment
from rooms.models import Room


ACTIVE_STATUSES = [
    Booking.Status.APPROVED,
    Booking.Status.COMPLETED,
]

STATUS_LABELS      = dict(Booking.Status.choices)
EVENT_TYPE_LABELS  = dict(Booking.EventType.choices)
WEEKDAY_LABELS     = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']


def _hours_between(t_start, t_end):
    dt_start = datetime.combine(date.today(), t_start)
    dt_end   = datetime.combine(date.today(), t_end)
    delta    = dt_end - dt_start
    return max(round(delta.total_seconds() / 3600, 1), 0)


def _date_range(date_from, date_to):
    cur = date_from
    while cur <= date_to:
        yield cur
        cur += timedelta(days=1)


def _period_working_hours(date_from, date_to):
    period_days = (date_to - date_from).days + 1
    return period_days * 8 * 5 / 7 if period_days > 0 else 0


def _booking_hour_parts(booking):
    start_dt = datetime.combine(date.today(), booking.event_start_time)
    end_dt   = datetime.combine(date.today(), booking.event_end_time)
    if end_dt <= start_dt:
        return []
    current = start_dt.replace(minute=0, second=0, microsecond=0)
    if current > start_dt:
        current -= timedelta(hours=1)
    result = []
    while current < end_dt:
        next_hour    = current + timedelta(hours=1)
        overlap_start = max(start_dt, current)
        overlap_end   = min(end_dt, next_hour)
        if overlap_end > overlap_start:
            minutes = int((overlap_end - overlap_start).total_seconds() / 60)
            result.append((current.hour, minutes))
        current = next_hour
    return result


def _empty_heatmap():
    return [[0.0 for _ in range(24)] for _ in range(7)]


def _build_heatmap(bookings, date_from, date_to):
    weekday_total_days = [0] * 7
    for d in _date_range(date_from, date_to):
        weekday_total_days[d.weekday()] += 1

    matrix_minutes = _empty_heatmap()
    for b in bookings:
        if b.status == Booking.Status.CANCELED:
            continue
        for hour, minutes in _booking_hour_parts(b):
            matrix_minutes[b.event_date.weekday()][hour] += minutes

    matrix_pct = []
    for w in range(7):
        denom_days = weekday_total_days[w] or 1
        row = []
        for h in range(24):
            row.append(round(matrix_minutes[w][h] / (denom_days * 60) * 100, 1))
        matrix_pct.append(row)
    return matrix_pct


def _event_hours_pie_from_bookings(bookings):
    """
    Распределение по типам мероприятий — считаем ЧАСЫ, а не количество заявок.
    Возвращает (labels, hours_values, counts_values).
    """
    hours_by_type  = defaultdict(float)
    counts_by_type = Counter()
    for b in bookings:
        if b.status in ACTIVE_STATUSES:
            h = _hours_between(b.event_start_time, b.event_end_time)
            hours_by_type[b.event_type]  += h
            counts_by_type[b.event_type] += 1

    sorted_types  = sorted(hours_by_type.keys(), key=lambda k: hours_by_type[k], reverse=True)
    labels        = [EVENT_TYPE_LABELS.get(k, k) for k in sorted_types]
    hours_values  = [round(hours_by_type[k], 1) for k in sorted_types]
    counts_values = [counts_by_type[k] for k in sorted_types]
    return labels, hours_values, counts_values


def _build_hour_distribution(bookings):
    """
    Суммарные часы по часам дня (0-23) для всех активных заявок.
    Даёт «параболу» — большинство заявок утром/днём.
    """
    hourly = defaultdict(float)
    for b in bookings:
        if b.status in ACTIVE_STATUSES:
            for hour, minutes in _booking_hour_parts(b):
                hourly[hour] += minutes / 60
    return [round(hourly.get(h, 0), 2) for h in range(24)]


def _booking_remaining_hours(booking):
    start_dt = datetime.combine(booking.event_date, booking.event_start_time)
    now = datetime.now()
    if start_dt <= now:
        return 0.0
    return round((start_dt - now).total_seconds() / 3600, 1)


class OverviewReportService:
    @staticmethod
    def get_report(resource_type, date_from, date_to):
        if resource_type == 'rooms':
            return RoomReportService.get_overview(date_from, date_to)
        return EquipmentReportService.get_overview(date_from, date_to)


class ResourceReportService:
    @staticmethod
    def get_report(resource_type, resource_id, date_from, date_to):
        if resource_type == 'rooms':
            room = Room.objects.get(pk=resource_id)
            return RoomReportService.get_resource_report(room, date_from, date_to)
        equipment = Equipment.objects.select_related('room').get(pk=resource_id)
        return EquipmentReportService.get_resource_report(equipment, date_from, date_to)


class RoomReportService:
    @staticmethod
    def get_overview(date_from, date_to):
        rooms    = list(Room.objects.all().order_by('building', 'name'))
        bookings = list(
            Booking.objects.filter(
                room__isnull=False,
                event_date__gte=date_from,
                event_date__lte=date_to,
            ).select_related('room').prefetch_related('equipment')
            .order_by('event_date', 'event_start_time', 'id')
        )

        stats = {
            room.id: {
                'room': room, 'all_bookings': 0, 'canceled': 0,
                'active_hours': 0.0,
                'daily_hours': defaultdict(float),
                'peak_day_hours': defaultdict(float),
            }
            for room in rooms
        }

        daily_totals = defaultdict(float)

        for b in bookings:
            row = stats.get(b.room_id)
            if not row:
                continue
            row['all_bookings'] += 1
            if b.status == Booking.Status.CANCELED:
                row['canceled'] += 1
                continue
            duration = _hours_between(b.event_start_time, b.event_end_time)
            row['active_hours']               += duration
            row['daily_hours'][b.event_date]   += duration
            row['peak_day_hours'][b.event_date] += duration
            daily_totals[b.event_date]         += duration

        period_days  = (date_to - date_from).days + 1
        working_hours = _period_working_hours(date_from, date_to)

        items = []
        for room in rooms:
            row      = stats[room.id]
            peak_day = max(row['peak_day_hours'], key=row['peak_day_hours'].get) if row['peak_day_hours'] else None
            total_hours  = round(row['active_hours'], 1)
            load_pct     = round(min(total_hours / working_hours * 100, 100), 1) if working_hours else 0
            canceled_pct = round(row['canceled'] / row['all_bookings'] * 100, 1) if row['all_bookings'] else 0
            items.append({
                'id': room.id, 'name': room.name, 'building': room.building,
                'floor': room.floor, 'type': room.get_type_display(), 'type_key': room.type,
                'capacity': room.capacity, 'status': room.get_status_display(),
                'bookings_count': row['all_bookings'], 'canceled_count': row['canceled'],
                'canceled_pct': canceled_pct, 'total_hours': total_hours,
                'load_pct': load_pct,
                'peak_day': peak_day.isoformat() if peak_day else '',
                'peak_day_hours': round(row['peak_day_hours'][peak_day], 1) if peak_day else 0,
            })

        items.sort(key=lambda x: x['load_pct'], reverse=True)

        trend_labels = [d.isoformat() for d in _date_range(date_from, date_to)]
        trend_values = [round(daily_totals.get(d, 0), 1) for d in _date_range(date_from, date_to)]
        peak_day     = max(daily_totals, key=daily_totals.get) if daily_totals else None

        pie_labels, pie_hours, pie_counts = _event_hours_pie_from_bookings(bookings)
        heatmap          = _build_heatmap(bookings, date_from, date_to)
        hour_distribution = _build_hour_distribution(bookings)

        return {
            'items': items,
            'total_hours':   round(sum(i['total_hours'] for i in items), 1),
            'total_bookings': sum(i['bookings_count'] for i in items),
            'avg_load':       round(sum(i['load_pct'] for i in items) / len(items), 1) if items else 0,
            'canceled_count': sum(i['canceled_count'] for i in items),
            'canceled_pct':   round(
                sum(i['canceled_count'] for i in items) / sum(i['bookings_count'] for i in items) * 100, 1
            ) if sum(i['bookings_count'] for i in items) else 0,
            'peak_day':    peak_day.isoformat() if peak_day else '',
            'trend_labels': trend_labels,
            'trend_values': trend_values,
            'pie_labels':        pie_labels,
            'pie_hours_values':  pie_hours,    # ← часы (для площади сектора)
            'pie_counts_values': pie_counts,   # ← количество заявок (для тултипа)
            'pie_values':        pie_hours,    # обратная совместимость
            'hour_distribution': hour_distribution,
            'heatmap_days':  WEEKDAY_LABELS,
            'heatmap_hours': list(range(24)),
            'heatmap':       heatmap,
            'period_days':   period_days,
            'working_hours': round(working_hours, 1),
        }

    @staticmethod
    def get_resource_report(room, date_from, date_to):
        bookings = list(
            Booking.objects.filter(
                room=room, event_date__gte=date_from, event_date__lte=date_to,
            ).select_related('room', 'initiator').prefetch_related('equipment')
            .order_by('event_date', 'event_start_time', 'id')
        )

        active   = [b for b in bookings if b.status in ACTIVE_STATUSES]
        canceled = [b for b in bookings if b.status == Booking.Status.CANCELED]

        total_hours     = round(sum(_hours_between(b.event_start_time, b.event_end_time) for b in active), 1)
        total_bookings  = len(bookings)
        canceled_count  = len(canceled)
        canceled_pct    = round(canceled_count / total_bookings * 100, 1) if total_bookings else 0
        avg_participants = round(sum(b.participants for b in active) / len(active), 1) if active else 0
        capacity_fill   = round(avg_participants / room.capacity * 100, 1) if room.capacity else 0

        working_hours   = _period_working_hours(date_from, date_to)
        load_pct        = round(min(total_hours / working_hours * 100, 100), 1) if working_hours else 0

        daily_totals    = defaultdict(float)
        hourly_minutes  = defaultdict(int)
        capacity_compare = []
        detail_rows      = []

        for b in bookings:
            duration = _hours_between(b.event_start_time, b.event_end_time)
            if b.status in ACTIVE_STATUSES:
                daily_totals[b.event_date] += duration
                for hour, minutes in _booking_hour_parts(b):
                    hourly_minutes[hour] += minutes
                capacity_compare.append({
                    'label': f'{b.event_date.isoformat()} {b.event_start_time.strftime("%H:%M")}',
                    'participants': b.participants, 'capacity': room.capacity,
                })

            detail_rows.append({
                'id': b.id,
                'date':  b.event_date.isoformat(),
                'start': b.event_start_time.strftime('%H:%M'),
                'end':   b.event_end_time.strftime('%H:%M'),
                'event_type':     b.get_event_type_display(),
                'event_type_key': b.event_type,
                'participants':   b.participants,
                'status':     b.get_status_display(),
                'status_key': b.status,
                'hours':      duration,
                'remaining_to_start_hours': _booking_remaining_hours(b),
                'comment':    b.comment or '',
            })

        trend_labels = [d.isoformat() for d in _date_range(date_from, date_to)]
        trend_values = [round(daily_totals.get(d, 0), 1) for d in _date_range(date_from, date_to)]
        hour_labels  = [f'{h:02d}:00' for h in range(24)]
        hour_values  = [round(hourly_minutes.get(h, 0) / 60, 1) for h in range(24)]

        pie_labels, pie_hours, pie_counts = _event_hours_pie_from_bookings(bookings)
        heatmap  = _build_heatmap(bookings, date_from, date_to)
        peak_day = max(daily_totals, key=daily_totals.get) if daily_totals else None
        peak_hour = max(range(24), key=lambda h: hour_values[h]) if hour_values else 0

        return {
            'resource': {
                'id': room.id, 'kind': 'rooms', 'name': room.name,
                'building': room.building, 'floor': room.floor,
                'capacity': room.capacity, 'type': room.get_type_display(),
                'type_key': room.type, 'status': room.get_status_display(),
            },
            'summary': {
                'total_hours': total_hours, 'total_bookings': total_bookings,
                'avg_participants': avg_participants, 'capacity_fill': capacity_fill,
                'load_pct': load_pct, 'canceled_count': canceled_count,
                'canceled_pct': canceled_pct,
                'peak_day': peak_day.isoformat() if peak_day else '',
                'peak_hour': peak_hour,
            },
            'trend_labels': trend_labels, 'trend_values': trend_values,
            'hour_labels': hour_labels,   'hour_values': hour_values,
            'pie_labels':        pie_labels,
            'pie_hours_values':  pie_hours,
            'pie_counts_values': pie_counts,
            'pie_values':        pie_hours,
            'capacity_compare': capacity_compare,  # без ограничений
            'detail_rows':      detail_rows,
            'heatmap_days':  WEEKDAY_LABELS,
            'heatmap_hours': list(range(24)),
            'heatmap':       heatmap,
        }


class EquipmentReportService:
    @staticmethod
    def get_overview(date_from, date_to):
        equipment_list = list(Equipment.objects.select_related('room').all().order_by('type', 'name'))
        bookings = list(
            Booking.objects.filter(
                equipment__isnull=False, event_date__gte=date_from, event_date__lte=date_to,
            ).select_related('room').prefetch_related('equipment')
            .order_by('event_date', 'event_start_time', 'id')
        )

        stats = {
            eq.id: {
                'equipment': eq, 'all_bookings': 0, 'canceled': 0,
                'active_hours': 0.0, 'peak_day_hours': defaultdict(float),
            }
            for eq in equipment_list
        }

        daily_totals = defaultdict(float)

        for b in bookings:
            duration = _hours_between(b.event_start_time, b.event_end_time)
            for eq in b.equipment.all():
                row = stats.get(eq.id)
                if not row:
                    continue
                row['all_bookings'] += 1
                if b.status == Booking.Status.CANCELED:
                    row['canceled'] += 1
                    continue
                row['active_hours']                += duration
                row['peak_day_hours'][b.event_date] += duration
                daily_totals[b.event_date]          += duration

        period_days   = (date_to - date_from).days + 1
        working_hours = _period_working_hours(date_from, date_to)

        items = []
        for eq in equipment_list:
            row      = stats[eq.id]
            peak_day = max(row['peak_day_hours'], key=row['peak_day_hours'].get) if row['peak_day_hours'] else None
            total_hours  = round(row['active_hours'], 1)
            load_pct     = round(min(total_hours / working_hours * 100, 100), 1) if working_hours else 0
            canceled_pct = round(row['canceled'] / row['all_bookings'] * 100, 1) if row['all_bookings'] else 0
            items.append({
                'id': eq.id, 'inventory_number': eq.inventory_number,
                'name': eq.name, 'model': eq.model,
                'type': eq.get_type_display(), 'type_key': eq.type,
                'is_stationary': eq.is_stationary,
                'room': eq.room.name if eq.room else 'Склад',
                'status': eq.get_status_display(),
                'bookings_count': row['all_bookings'], 'canceled_count': row['canceled'],
                'canceled_pct': canceled_pct, 'total_hours': total_hours, 'load_pct': load_pct,
                'peak_day': peak_day.isoformat() if peak_day else '',
                'peak_day_hours': round(row['peak_day_hours'][peak_day], 1) if peak_day else 0,
            })

        items.sort(key=lambda x: x['load_pct'], reverse=True)

        trend_labels = [d.isoformat() for d in _date_range(date_from, date_to)]
        trend_values = [round(daily_totals.get(d, 0), 1) for d in _date_range(date_from, date_to)]
        peak_day     = max(daily_totals, key=daily_totals.get) if daily_totals else None

        pie_labels, pie_hours, pie_counts = _event_hours_pie_from_bookings(bookings)
        heatmap           = _build_heatmap(bookings, date_from, date_to)
        hour_distribution = _build_hour_distribution(bookings)

        return {
            'items': items,
            'total_hours':    round(sum(i['total_hours'] for i in items), 1),
            'total_bookings': sum(i['bookings_count'] for i in items),
            'avg_load':       round(sum(i['load_pct'] for i in items) / len(items), 1) if items else 0,
            'canceled_count': sum(i['canceled_count'] for i in items),
            'canceled_pct':   round(
                sum(i['canceled_count'] for i in items) / sum(i['bookings_count'] for i in items) * 100, 1
            ) if sum(i['bookings_count'] for i in items) else 0,
            'peak_day':   peak_day.isoformat() if peak_day else '',
            'trend_labels': trend_labels, 'trend_values': trend_values,
            'pie_labels':        pie_labels,
            'pie_hours_values':  pie_hours,
            'pie_counts_values': pie_counts,
            'pie_values':        pie_hours,
            'hour_distribution': hour_distribution,
            'heatmap_days':  WEEKDAY_LABELS,
            'heatmap_hours': list(range(24)),
            'heatmap':       heatmap,
            'period_days':   period_days,
            'working_hours': round(working_hours, 1),
        }

    @staticmethod
    def get_resource_report(equipment, date_from, date_to):
        bookings = list(
            Booking.objects.filter(
                equipment=equipment, event_date__gte=date_from, event_date__lte=date_to,
            ).select_related('room').prefetch_related('equipment')
            .order_by('event_date', 'event_start_time', 'id')
        )

        active   = [b for b in bookings if b.status in ACTIVE_STATUSES]
        canceled = [b for b in bookings if b.status == Booking.Status.CANCELED]

        total_hours    = round(sum(_hours_between(b.event_start_time, b.event_end_time) for b in active), 1)
        total_bookings = len(bookings)
        canceled_count = len(canceled)
        canceled_pct   = round(canceled_count / total_bookings * 100, 1) if total_bookings else 0

        working_hours = _period_working_hours(date_from, date_to)
        load_pct      = round(min(total_hours / working_hours * 100, 100), 1) if working_hours else 0

        daily_totals   = defaultdict(float)
        hourly_minutes = defaultdict(int)
        room_counter   = Counter()
        detail_rows    = []

        for b in bookings:
            duration = _hours_between(b.event_start_time, b.event_end_time)
            if b.status in ACTIVE_STATUSES:
                daily_totals[b.event_date] += duration
                room_counter[b.room.name]  += 1
                for hour, minutes in _booking_hour_parts(b):
                    hourly_minutes[hour] += minutes

            detail_rows.append({
                'id': b.id,
                'date':  b.event_date.isoformat(),
                'start': b.event_start_time.strftime('%H:%M'),
                'end':   b.event_end_time.strftime('%H:%M'),
                'room':           b.room.name,
                'event_type':     b.get_event_type_display(),
                'event_type_key': b.event_type,
                'participants':   b.participants,
                'status':     b.get_status_display(),
                'status_key': b.status,
                'hours':      duration,
                'remaining_to_start_hours': _booking_remaining_hours(b),
                'comment':    b.comment or '',
            })

        trend_labels = [d.isoformat() for d in _date_range(date_from, date_to)]
        trend_values = [round(daily_totals.get(d, 0), 1) for d in _date_range(date_from, date_to)]
        hour_labels  = [f'{h:02d}:00' for h in range(24)]
        hour_values  = [round(hourly_minutes.get(h, 0) / 60, 1) for h in range(24)]

        pie_labels, pie_hours, pie_counts = _event_hours_pie_from_bookings(bookings)
        heatmap   = _build_heatmap(bookings, date_from, date_to)
        peak_day  = max(daily_totals, key=daily_totals.get) if daily_totals else None
        peak_hour = max(range(24), key=lambda h: hour_values[h]) if hour_values else 0

        return {
            'resource': {
                'id': equipment.id, 'kind': 'equipment',
                'name': equipment.name, 'inventory_number': equipment.inventory_number,
                'model': equipment.model, 'type': equipment.get_type_display(),
                'type_key': equipment.type, 'status': equipment.get_status_display(),
                'room': equipment.room.name if equipment.room else 'Склад',
                'is_stationary': equipment.is_stationary,
            },
            'summary': {
                'total_hours': total_hours, 'total_bookings': total_bookings,
                'load_pct': load_pct, 'canceled_count': canceled_count,
                'canceled_pct': canceled_pct,
                'peak_day': peak_day.isoformat() if peak_day else '',
                'peak_hour': peak_hour,
            },
            'trend_labels': trend_labels, 'trend_values': trend_values,
            'hour_labels': hour_labels,   'hour_values': hour_values,
            'pie_labels':        pie_labels,
            'pie_hours_values':  pie_hours,
            'pie_counts_values': pie_counts,
            'pie_values':        pie_hours,
            'room_usage':  [{'label': k, 'value': v} for k, v in room_counter.most_common(12)],
            'detail_rows': detail_rows,
            'heatmap_days':  WEEKDAY_LABELS,
            'heatmap_hours': list(range(24)),
            'heatmap':       heatmap,
        }