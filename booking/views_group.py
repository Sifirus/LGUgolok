"""
booking/views_group.py
"""
import json
from datetime import date, time as dt_time, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from booking.models import Booking, BookingGroup
from booking.services.group_booking_services import GroupConflictService, GroupCreateService
from core.decorators import require_role_decorator
from equipment.models import Equipment
from rooms.models import Room


@require_role_decorator(roles=['initiator'])
@login_required(login_url='login')
def booking_group_create(request):
    return render(request, 'booking/create_booking_group.html', {
        'event_types': Booking.EventType.choices,
    })


@require_role_decorator(roles=['initiator'])
@login_required(login_url='login')
def booking_group_conflicts(request):
    """AJAX POST: проверить конфликты для переданных слотов."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'bad json'}, status=400)

    raw_slots = payload.get('slots', [])
    if not raw_slots:
        return JsonResponse({'rooms': [], 'equipment': []})

    slots = []
    for s in raw_slots:
        try:
            slots.append({
                'date': date.fromisoformat(s['date']),
                'start': dt_time.fromisoformat(s['start']),
                'end': dt_time.fromisoformat(s['end']),
                'participants': int(s.get('participants', 0) or 0),
            })
        except (KeyError, ValueError):
            continue

    if not slots:
        return JsonResponse({'rooms': [], 'equipment': []})

    data = GroupConflictService.check(slots)
    return JsonResponse(data)

import json
from datetime import date, time as dt_time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from booking.models import Booking, BookingGroup
from booking.services.group_booking_services import GroupConflictService, GroupCreateService
from core.decorators import require_role_decorator
from equipment.models import Equipment
from rooms.models import Room


@require_role_decorator(roles=['initiator'])
@login_required(login_url='login')
def booking_group_submit(request):
    """AJAX POST: создать группу."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'bad json'}, status=400)

    title = (payload.get('title') or '').strip()
    comment = (payload.get('comment') or '').strip()

    if not title:
        return JsonResponse({'error': 'Укажите название серии'}, status=400)

    try:
        date_from = date.fromisoformat(payload['date_from'])
        date_to = date.fromisoformat(payload['date_to'])
    except (KeyError, ValueError):
        return JsonResponse({'error': 'Неверные даты периода'}, status=400)

    today = date.today()
    now = datetime.now().time()

    if date_from < today:
        return JsonResponse({'error': 'Дата серии не может быть в прошлом'}, status=400)

    if date_to < date_from:
        return JsonResponse({'error': 'Дата окончания серии не может быть раньше даты начала'}, status=400)

    raw_slots = payload.get('slots', [])
    if not raw_slots:
        return JsonResponse({'error': 'Нет слотов'}, status=400)

    slots = []
    for s in raw_slots:
        try:
            slot_date = date.fromisoformat(s['date'])
            start = dt_time.fromisoformat(s['start'])
            end = dt_time.fromisoformat(s['end'])

            # Проверка что дата не в прошлом
            if slot_date < today:
                return JsonResponse(
                    {'error': f'Дата {slot_date.isoformat()} уже прошла'},
                    status=400
                )

            # Проверка что время не в прошлом для сегодняшней даты
            if slot_date == today and start <= now:
                return JsonResponse(
                    {'error': f'Время начала {start} на сегодня уже прошло'},
                    status=400
                )

            if slot_date < date_from or slot_date > date_to:
                return JsonResponse(
                    {'error': f'Дата слота {slot_date.isoformat()} вне периода серии'},
                    status=400
                )

            if end <= start:
                return JsonResponse(
                    {'error': f'Для {slot_date.isoformat()} время окончания должно быть позже времени начала'},
                    status=400
                )

            room_id = s.get('room_id')
            if not room_id:
                return JsonResponse(
                    {'error': f'Не выбрана аудитория для {s.get("date", "?")}'},
                    status=400
                )

            slots.append({
                'date': slot_date,
                'start': start,
                'end': end,
                'event_type': s.get('event_type', 'lecture'),
                'participants': int(s.get('participants', 60)),
                'comment': s.get('comment', ''),
                'room_id': int(room_id),
                'equipment_ids': [int(i) for i in s.get('equipment_ids', [])],
            })
        except (KeyError, ValueError, TypeError) as e:
            return JsonResponse({'error': f'Ошибка в слоте: {e}'}, status=400)

    try:
        group = GroupCreateService.create(
            initiator=request.user,
            title=title,
            comment=comment,
            date_from=date_from,
            date_to=date_to,
            slots=slots,
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'ok': True, 'group_id': group.pk})


@login_required(login_url='login')
def booking_group_detail(request, group_id):
    group = get_object_or_404(
        BookingGroup.objects.prefetch_related(
            'booking_set__room',
            'booking_set__equipment',
            'booking_set__approval__approver__profile',
        ),
        pk=group_id,
    )
    role = getattr(request.user, 'role', None)
    if role == 'initiator' and group.initiator != request.user:
        raise PermissionDenied

    bookings = group.booking_set.order_by('event_date', 'event_start_time')

    # Заявки которые можно отменить
    cancelable_statuses = [
        Booking.Status.CREATED,
        Booking.Status.PENDING,
        Booking.Status.APPROVED,
    ]
    can_cancel = (
            role in ['operator', 'initiator']
            and group.approval_required_count > 0  # хоть что-то активное есть
            and bookings.filter(status__in=cancelable_statuses).exists()
    )

    return render(request, 'booking/booking_group_detail.html', {
        'group': group,
        'bookings': bookings,
        'can_cancel': can_cancel,
    })


@login_required(login_url='login')
@require_POST
def booking_group_cancel(request, group_id):
    group = get_object_or_404(BookingGroup, pk=group_id)
    role = getattr(request.user, 'role', None)
    if role == 'initiator' and group.initiator != request.user:
        raise PermissionDenied

    cancelable = group.booking_set.filter(
        status__in=[Booking.Status.CREATED, Booking.Status.PENDING, Booking.Status.APPROVED]
    )
    n = cancelable.count()
    for b in cancelable:
        b.status = Booking.Status.CANCELED
        b.save(update_fields=['status', 'updated_at'])

    messages.success(request, f'Отменено {n} заявок из серии «{group.title}»')
    return redirect('booking_group_detail', group_id=group.pk)