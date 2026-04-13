from datetime import date, datetime

from booking.models import Booking


REPORT_STATUSES = [
    Booking.Status.APPROVED,
    Booking.Status.COMPLETED,
]


def _hours_between(t_start, t_end):
    dt_start = datetime.combine(date.today(), t_start)
    dt_end   = datetime.combine(date.today(), t_end)
    delta = dt_end - dt_start
    return round(delta.total_seconds() / 3600, 1)


class RoomReportService:

    @staticmethod
    def get_report(date_from: date, date_to: date) -> dict:
        bookings = Booking.objects.filter(
            status__in=REPORT_STATUSES,
            event_date__gte=date_from,
            event_date__lte=date_to,
        ).select_related('room')

        period_days = (date_to - date_from).days + 1
        working_hours = period_days * 8 * 5 / 7

        room_stats = {}
        for b in bookings:
            rid = b.room_id
            if rid not in room_stats:
                room_stats[rid] = {
                    'room':      b.room,
                    'bookings':  [],
                    'hours':     0.0,
                    'dates':     [],
                }
            hours = _hours_between(b.event_start_time, b.event_end_time)
            room_stats[rid]['bookings'].append(b)
            room_stats[rid]['hours']  += hours
            room_stats[rid]['dates'].append(b.event_date)

        items = []
        for rid, s in room_stats.items():
            room = s['room']
            total_hours = round(s['hours'], 1)
            load_pct    = min(round(total_hours / working_hours * 100, 1), 100) if working_hours else 0

            from collections import Counter
            date_counts = Counter(s['dates'])
            peak_date   = max(date_counts, key=date_counts.get) if date_counts else None

            items.append({
                'id':             room.id,
                'name':           room.name,
                'building':       room.building,
                'type':           room.get_type_display(),
                'type_key':       room.type,
                'capacity':       room.capacity,
                'bookings_count': len(s['bookings']),
                'total_hours':    total_hours,
                'load_pct':       load_pct,
                'peak_day':       peak_date.strftime('%d.%m.%Y') if peak_date else '—',
            })

        items.sort(key=lambda x: x['load_pct'], reverse=True)

        total_hours    = round(sum(i['total_hours'] for i in items), 1)
        total_bookings = sum(i['bookings_count'] for i in items)
        avg_load       = round(sum(i['load_pct'] for i in items) / len(items), 1) if items else 0
        high_load      = len([i for i in items if i['load_pct'] > 70])

        return {
            'items':          items,
            'total_hours':    total_hours,
            'total_bookings': total_bookings,
            'avg_load':       avg_load,
            'high_load_count': high_load,
            'period_days':    period_days,
        }


class EquipmentReportService:

    @staticmethod
    def get_report(date_from: date, date_to: date) -> dict:
        bookings = Booking.objects.filter(
            status__in=REPORT_STATUSES,
            event_date__gte=date_from,
            event_date__lte=date_to,
        ).prefetch_related('equipment')

        period_days   = (date_to - date_from).days + 1
        working_hours = period_days * 8 * 5 / 7

        equip_stats = {}
        for b in bookings:
            hours = _hours_between(b.event_start_time, b.event_end_time)
            for eq in b.equipment.all():
                if eq.id not in equip_stats:
                    equip_stats[eq.id] = {
                        'equip':    eq,
                        'count':    0,
                        'hours':    0.0,
                    }
                equip_stats[eq.id]['count'] += 1
                equip_stats[eq.id]['hours'] += hours

        items = []
        for eid, s in equip_stats.items():
            eq         = s['equip']
            total_h    = round(s['hours'], 1)
            load_pct   = min(round(total_h / working_hours * 100, 1), 100) if working_hours else 0
            items.append({
                'id':               eq.id,
                'inventory_number': eq.inventory_number,
                'name':             eq.name,
                'model':            eq.model,
                'type':             eq.get_type_display(),
                'type_key':         eq.type,
                'is_stationary':    eq.is_stationary,
                'room':             eq.room.name if eq.room else 'Склад',
                'bookings_count':   s['count'],
                'total_hours':      total_h,
                'load_pct':         load_pct,
            })

        items.sort(key=lambda x: x['load_pct'], reverse=True)

        total_hours    = round(sum(i['total_hours'] for i in items), 1)
        total_bookings = sum(i['bookings_count'] for i in items)
        avg_load       = round(sum(i['load_pct'] for i in items) / len(items), 1) if items else 0
        popular_count  = len([i for i in items if i['load_pct'] > 50])

        return {
            'items':          items,
            'total_hours':    total_hours,
            'total_bookings': total_bookings,
            'avg_load':       avg_load,
            'popular_count':  popular_count,
            'period_days':    period_days,
        }