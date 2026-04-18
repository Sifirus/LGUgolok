import csv
import io
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from booking.models import Booking
from core.decorators import require_role_decorator
from equipment.models import Equipment
from reports.services.reports_service import OverviewReportService, ResourceReportService, RoomReportService, EquipmentReportService
from rooms.models import Room


def _get_date_range(request):
    today = date.today()
    default_from = today.replace(day=1)
    default_to = today

    try:
        date_from = date.fromisoformat(request.GET.get('date_from', ''))
    except (ValueError, TypeError):
        date_from = default_from

    try:
        date_to = date.fromisoformat(request.GET.get('date_to', ''))
    except (ValueError, TypeError):
        date_to = default_to

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    return date_from, date_to


@login_required(login_url='login')
@require_role_decorator(roles=['operator', 'approver'])
def reports_page(request):
    date_from, date_to = _get_date_range(request)
    return render(request, 'reports/reports.html', {
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
    })


@login_required(login_url='login')
@require_role_decorator(roles=['operator', 'approver'])
def reports_overview_data(request):
    date_from, date_to = _get_date_range(request)
    report_type = request.GET.get('type', 'rooms')
    data = OverviewReportService.get_report(report_type, date_from, date_to)
    return JsonResponse(data)


@login_required(login_url='login')
@require_role_decorator(roles=['operator', 'approver'])
def reports_resource_data(request, resource_type, pk):
    date_from, date_to = _get_date_range(request)
    data = ResourceReportService.get_report(resource_type, pk, date_from, date_to)
    return JsonResponse(data)


@login_required(login_url='login')
@require_role_decorator(roles=['operator', 'approver'])
def reports_search(request):
    q = (request.GET.get('q') or '').strip()
    resource_type = request.GET.get('type', 'rooms')
    items = []

    if resource_type == 'rooms':
        # Берём больше из БД, потом фильтруем тип по display-label в Python
        qs = Room.objects.all().order_by('building', 'name')
        if q:
            from django.db.models import Q as _Q
            db_filters = (
                    _Q(name__icontains=q) |
                    _Q(building__icontains=q) |
                    _Q(type__icontains=q)  # raw key search (обратная совместимость)
            )
            if q.isdigit():
                db_filters |= _Q(pk=int(q))
            qs = qs.filter(db_filters)

        all_rooms = list(qs[:100])

        # Дополнительно: поиск по display-label типа (например «Лекционная» вместо «lecture_hall»)
        if q:
            q_lower = q.lower()
            extra = [
                r for r in Room.objects.all().order_by('building', 'name')[:200]
                if q_lower in r.get_type_display().lower()
                   and r.id not in {x.id for x in all_rooms}
            ]
            all_rooms = (all_rooms + extra)[:50]

        for room in all_rooms[:20]:
            items.append({
                'id': room.id,
                'kind': 'rooms',
                'label': room.name,
                'subtitle': f'{room.building}, {room.get_type_display()}, {room.get_status_display()}',
            })

    else:
        qs = Equipment.objects.select_related('room').all().order_by('name')
        if q:
            from django.db.models import Q as _Q
            db_filters = (
                    _Q(name__icontains=q) |
                    _Q(model__icontains=q) |
                    _Q(inventory_number__icontains=q) |
                    _Q(type__icontains=q) |
                    _Q(room__name__icontains=q)
            )
            if q.isdigit():
                db_filters |= _Q(pk=int(q))
            qs = qs.filter(db_filters)

        all_eq = list(qs[:100])

        # Поиск по display-label типа оборудования
        if q:
            q_lower = q.lower()
            extra = [
                e for e in Equipment.objects.select_related('room').all()[:200]
                if q_lower in e.get_type_display().lower()
                   and e.id not in {x.id for x in all_eq}
            ]
            all_eq = (all_eq + extra)[:50]

        for eq in all_eq[:20]:
            items.append({
                'id': eq.id,
                'kind': 'equipment',
                'label': f'{eq.name} {eq.model}',
                'subtitle': f'{eq.inventory_number}, {eq.room.name if eq.room else "Склад"}, {eq.get_status_display()}',
            })

    return JsonResponse({'items': items})


# ── reports/views.py — заменить функцию room_equipment_at_datetime целиком ──

@login_required(login_url='login')
@require_role_decorator(roles=['operator', 'approver'])
def room_equipment_at_datetime(request, room_id):
    on_date = request.GET.get('date')
    at_time = request.GET.get('time')

    if not on_date or not at_time:
        return JsonResponse({'detail': 'date and time are required'}, status=400)

    try:
        d = date.fromisoformat(on_date)
        t = datetime.strptime(at_time, '%H:%M').time()
    except ValueError:
        return JsonResponse({'detail': 'invalid date or time'}, status=400)

    from booking.models import Booking

    room = Room.objects.get(pk=room_id)

    # 1. Оборудование постоянно приписанное к этой аудитории
    permanent_ids = set(room.equipment.values_list('id', flat=True))

    # 2. Переносное оборудование, которое находится здесь через активную заявку
    #    (заявка на ЭТУ аудиторию, перекрывает указанное время)
    booked_ids = set(
        Equipment.objects.filter(
            bookings__room_id=room_id,
            bookings__event_date=d,
            bookings__event_start_time__lte=t,
            bookings__event_end_time__gt=t,
            bookings__status__in=[
                Booking.Status.APPROVED,
                Booking.Status.PENDING,
                Booking.Status.CREATED,
            ],
        ).values_list('id', flat=True)
    )

    all_ids = permanent_ids | booked_ids

    rows = []
    for eq in Equipment.objects.select_related('room').filter(id__in=all_ids).order_by('name'):
        location = eq.get_current_location(d, t)
        rows.append({
            'id':               eq.id,
            'inventory_number': eq.inventory_number,
            'name':             eq.name,
            'model':            eq.model,
            'status':           eq.get_status_display(),
            'location_label':   location['label'],
            'location_type':    location['location_type'],
        })

    return JsonResponse({'items': rows})


@login_required(login_url='login')
@require_role_decorator(roles=['operator', 'approver'])
def export_csv(request):
    date_from, date_to = _get_date_range(request)
    report_type = request.GET.get('type', 'rooms')

    if report_type == 'rooms':
        data = RoomReportService.get_overview(date_from, date_to)
        fields = ['name', 'building', 'floor', 'type', 'status', 'bookings_count', 'canceled_count', 'total_hours', 'load_pct', 'peak_day']
        headers = ['Аудитория', 'Корпус', 'Этаж', 'Тип', 'Статус', 'Заявок', 'Отмен', 'Часов', 'Загрузка %', 'Пиковый день']
        filename = f'rooms_report_{date_from}_{date_to}.csv'
    else:
        data = EquipmentReportService.get_overview(date_from, date_to)
        fields = ['name', 'model', 'inventory_number', 'type', 'status', 'room', 'bookings_count', 'canceled_count', 'total_hours', 'load_pct', 'peak_day']
        headers = ['Наименование', 'Модель', 'Инв. номер', 'Тип', 'Статус', 'Аудитория', 'Заявок', 'Отмен', 'Часов', 'Загрузка %', 'Пиковый день']
        filename = f'equipment_report_{date_from}_{date_to}.csv'

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for item in data.get('items', []):
        writer.writerow([item.get(f, '') for f in fields])

    return response