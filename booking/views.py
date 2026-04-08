from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from booking.forms import BookingForm
from django.contrib.auth.decorators import login_required
from django.db import transaction

from core.decorators import require_role_decorator
from equipment.models import Equipment
from equipment.services.equipment_service import AvailableEquipmentService
from rooms.services.rooms_service import AvailableRoomsService
from rooms.models import Room
from approval.services.approval_services import ApprovalEngine


@require_role_decorator(['initiator'])
@login_required(login_url='login')
def booking_create(request):
    form = BookingForm(request.POST or None)
    room_types = Room.RoomType.choices
    context = {'form': form, 'room_types': room_types}

    if request.method == 'POST':
        is_conflict = False
        if form.is_valid():
            cleaned_data = form.cleaned_data

            with transaction.atomic():
                # Блокируем выбранную аудиторию
                room_qs = Room.objects.select_for_update().filter(pk=cleaned_data['room'].pk)
                available_room = AvailableRoomsService.get_available_rooms(
                    room_qs,
                    cleaned_data['event_date'],
                    cleaned_data['event_start_time'],
                    cleaned_data['event_end_time'],
                )
                if not available_room.exists():
                    messages.warning(request, 'Аудиторию только что забронировали')
                    is_conflict = True

                # Блокируем выбранное оборудование
                if cleaned_data['equipment']:
                    selected_equipment = Equipment.objects.select_for_update().filter(pk__in=cleaned_data['equipment'])
                    available_equipment = AvailableEquipmentService.get_available_equipment(
                        selected_equipment,
                        cleaned_data['event_date'],
                        cleaned_data['event_start_time'],
                        cleaned_data['event_end_time'],
                    )
                    unavailable_equipment = list(
                        selected_equipment.exclude(pk__in=available_equipment).values_list('pk', 'name')
                    )

                    if unavailable_equipment:
                        unavailable_equipment_ids = [pk for pk, name in unavailable_equipment]
                        unavailable_equipment_names = [name for pk, name in unavailable_equipment]

                        messages.warning(request,
                                         f'Часть оборудования только что забронировали: {", ".join(unavailable_equipment_names)}')
                        context['unavailable_equipment_ids'] = unavailable_equipment_ids
                        is_conflict = True

                if is_conflict:
                    return render(request, 'booking/create_booking.html', context)

                # Вычисляем статус через ApprovalEngine
                status = ApprovalEngine.get_status(
                    cleaned_data['room'], cleaned_data['equipment'], cleaned_data['event_type'],
                    cleaned_data['participants']
                )

                # Создаём бронирование
                booking = form.save(commit=False)
                booking.initiator = request.user
                booking.status = status
                booking.save()
                form.save_m2m()

            return redirect(reverse('index'))
        else:
            return render(request, 'booking/create_booking.html', context)
    else:
        return render(request, 'booking/create_booking.html', context)


from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.models import Booking
from approval.models import Approval
from booking.services.booking_services import BookingAccessService, BookingFiltersService
from core.decorators import require_role_decorator
from rooms.models import Room

User = get_user_model()


class RoomLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        queryset = Room.objects.all().order_by('building', 'floor', 'name')

        if q:
            filters = Q(name__icontains=q) | Q(building__icontains=q)
            if q.isdigit():
                filters |= Q(pk=int(q))
            queryset = queryset.filter(filters)

        data = []
        for room in queryset[:10]:
            data.append({
                'id': room.id,
                'label': f'{room.id} · {room.name} · {room.building}, этаж {room.floor}',
            })

        return Response(data)


class ApproverLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        queryset = User.objects.select_related('profile').all().order_by('email')

        if q:
            filters = (
                    Q(email__icontains=q) |
                    Q(profile__first_name__icontains=q) |
                    Q(profile__second_name__icontains=q) |
                    Q(profile__last_name__icontains=q) |
                    Q(profile__department__icontains=q)
            )
            if q.isdigit():
                filters |= Q(pk=int(q))
            queryset = queryset.filter(filters)

        data = []
        for user in queryset[:10]:
            profile = getattr(user, 'profile', None)
            full_name = ''
            if profile:
                parts = [profile.last_name, profile.first_name, profile.second_name or '']
                full_name = ' '.join(part for part in parts if part).strip()

            label = f'{user.id} · {user.email}'
            if full_name:
                label += f' · {full_name}'

            data.append({
                'id': user.id,
                'label': label,
            })

        return Response(data)


@require_role_decorator(roles=['initiator', 'operator', 'approver'])
@login_required(login_url='login')
def booking_list(request):
    qs = (
        Booking.objects
        .select_related(
            'room',
            'initiator',
            'initiator__profile',
            'approval',
            'approval__approver',
            'approval__approver__profile' #TODO fix approver
        )
        .prefetch_related('equipment')
        .annotate(equipment_count=Count('equipment', distinct=True))
        .order_by('-created_at')
    )

    qs = BookingAccessService.visible_queryset(request.user, qs)

    filters = {
        'search': request.GET.get('search', ''),
        'event_type': request.GET.get('event_type', ''),
        'status': request.GET.get('status', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'room_id': request.GET.get('room_id', ''),
        'approver_id': request.GET.get('approver_id', ''),
        'approval_decision': request.GET.get('approval_decision', ''),
    }
    filters = {k: v for k, v in filters.items() if v}

    if filters:
        qs = BookingFiltersService.apply_filters(qs, filters)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)

    room_id = request.GET.get('room_id', '')
    approver_id = request.GET.get('approver_id', '')

    room_obj = Room.objects.filter(pk=room_id).first() if room_id else None
    approver_obj = User.objects.select_related('profile').filter(pk=approver_id).first() if approver_id else None

    role = getattr(request.user, 'role', None)
    is_initiator_view = role == 'initiator'

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'bookings': page_obj,
        'total': paginator.count,
        'page_title': 'Мои заявки' if is_initiator_view else 'Все заявки',
        'is_initiator_view': is_initiator_view,
        'event_types': Booking.EventType.choices,
        'statuses': Booking.Status.choices,
        'approval_choices': Approval.Decision.choices,
        'search': request.GET.get('search', ''),
        'filter_event_type': request.GET.get('event_type', ''),
        'filter_status': request.GET.get('status', ''),
        'filter_date_from': request.GET.get('date_from', ''),
        'filter_date_to': request.GET.get('date_to', ''),
        'filter_room_id': room_id,
        'filter_room_label': room_obj.name if room_obj else '',
        'filter_approver_id': approver_id,
        'filter_approver_label': approver_obj.email if approver_obj else '',
        'filter_approval_decision': request.GET.get('approval_decision', ''),
        'current_date': timezone.localdate().strftime('%d.%m.%Y'),
        'current_time': timezone.localtime().strftime('%H:%M'),
        'room_lookup_url': 'room_lookup_api',
        'approver_lookup_url': 'approver_lookup_api',
        'query_string': query_params.urlencode(),
    }
    return render(request, 'booking/bookings_list.html', context)


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from booking.forms import BookingCommentForm
from booking.models import Booking, Comments
from core.decorators import require_role_decorator


def booking_can_view(user, booking: Booking) -> bool:
    role = getattr(user, 'role', None)

    if role == 'operator':
        return True

    if role == 'initiator' and booking.initiator_id == user.id:
        return True

    if role == 'approver' and booking.approval and booking.approval.approver_id == user.id:
        return True

    return False


def booking_can_comment(user, booking: Booking) -> bool:
    role = getattr(user, 'role', None)

    if role == 'initiator' and booking.initiator_id == user.id:
        return True

    if role == 'approver' and booking.approval and booking.approval.approver_id == user.id:
        return True

    return False


def booking_can_cancel(user, booking: Booking) -> bool:
    role = getattr(user, 'role', None)

    if booking.status in (Booking.Status.CANCELED, Booking.Status.COMPLETED):
        return False

    if role == 'operator':
        return True

    if role == 'initiator' and booking.initiator_id == user.id:
        return True

    return False

@require_role_decorator(roles=['initiator', 'operator', 'approver'])
@login_required(login_url='login')
def booking_detail(request, booking_id):
    booking_qs = (
        Booking.objects
        .select_related(
            'initiator__profile',
            'room',
            'approval__approver__profile',
        )
        .prefetch_related(
            'equipment',
            Prefetch(
                'comments',
                queryset=Comments.objects.select_related('author__profile').order_by('created_at')
            )
        )
    )

    booking = get_object_or_404(booking_qs, pk=booking_id)
    approval = getattr(booking, 'approval', None)  # Получаем approval, может быть None

    if not booking_can_view(request.user, booking):
        raise PermissionDenied

    comment_form = BookingCommentForm()
    can_comment = booking_can_comment(request.user, booking)
    can_cancel = booking_can_cancel(request.user, booking)

    if request.method == 'POST':
        action = request.POST.get('action', 'comment')

        if action == 'comment':
            if not can_comment:
                raise PermissionDenied

            comment_form = BookingCommentForm(request.POST)
            if comment_form.is_valid():
                Comments.objects.create(
                    booking=booking,
                    author=request.user,
                    text=comment_form.cleaned_data['text'],
                )
                messages.success(request, 'Комментарий добавлен')
                return redirect('booking_detail', booking_id=booking.id)

        elif action == 'cancel':
            return redirect('booking_cancel', booking_id=booking.id)

    comments = booking.comments.all()

    context = {
        'booking': booking,
        'comments': comments,
        'comment_form': comment_form,
        'can_comment': can_comment,
        'can_cancel': can_cancel,
        'is_initiator': request.user.id == booking.initiator_id,
        'approval': approval,
        'is_approver': bool(approval and approval.approver_id == request.user.id),
        'current_date': timezone.localdate().strftime('%d.%m.%Y'),
        'current_time': timezone.localtime().strftime('%H:%M'),
        'approval_choices': Approval.Decision.choices,
    }
    return render(request, 'booking/booking_detail.html', context)

@require_role_decorator(roles=['initiator', 'operator', 'approver'])
@login_required(login_url='login')
def booking_cancel(request, booking_id):
    if request.method != 'POST':
        return redirect('booking_detail', booking_id=booking_id)

    booking = get_object_or_404(
        Booking.objects.select_related('initiator__profile', 'room'),
        pk=booking_id
    )

    if not booking_can_view(request.user, booking):
        raise PermissionDenied

    if not booking_can_cancel(request.user, booking):
        messages.error(request, 'У вас нет прав на отмену этой заявки')
        return redirect('booking_detail', booking_id=booking.id)

    booking.status = Booking.Status.CANCELED
    booking.save(update_fields=['status', 'updated_at'])

    messages.success(request, 'Заявка отменена')
    return redirect('booking_detail', booking_id=booking.id)