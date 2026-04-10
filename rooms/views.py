from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rooms.models import Room
from rooms.serializers import RoomFiltersSerializer, RoomSerializer
from rooms.services.rooms_service import AvailableRoomsService, RoomsFiltersService

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone

from core.decorators import require_role_decorator
from rooms.forms import RoomForm

from equipment.models import Equipment


class RoomSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        serializer = RoomFiltersSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        cleaned_data = serializer.validated_data
        queryset = Room.objects.all()

        if cleaned_data.get('is_available'):
            queryset = AvailableRoomsService.get_available_rooms(
                queryset,
                cleaned_data.get('event_date'),
                cleaned_data.get('event_start_time'),
                cleaned_data.get('event_end_time')
            )

        queryset = RoomsFiltersService.apply_filters(queryset, cleaned_data)

        serializer = RoomSerializer(queryset, many=True)

        return Response(serializer.data)


class RoomLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
                'name': room.name,
                'building': room.building,
                'floor': room.floor,
            })

        return Response(data)


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def rooms_list(request):
    qs = Room.objects.all().order_by('building', 'floor', 'name')

    # Применяем фильтры
    filters = {
        'search_query': request.GET.get('search', ''),
        'type': request.GET.get('type', ''),
        'capacity': request.GET.get('capacity', ''),
        'building': request.GET.get('building', ''),
        'status': request.GET.get('status', ''),
        'equipment': ','.join(request.GET.getlist('equipment', '')),
    }

    # Убираем пустые значения
    filters = {k: v for k, v in filters.items() if v}

    if filters:
        qs = RoomsFiltersService.apply_filters(qs, filters)

    # Получаем текущее время для проверки занятости
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    # Для каждой аудитории проверяем, занята ли она сейчас
    rooms_with_status = []
    for room in qs:
        # Проверяем, свободна ли аудитория сейчас
        try:
            available_rooms = AvailableRoomsService.get_available_rooms(
                Room.objects.filter(pk=room.pk),
                current_date,
                current_time,
                current_time
            )
            is_available = available_rooms.exists()
        except ValueError:
            is_available = True  # Если ошибка в времени, считаем свободной

        rooms_with_status.append({
            'room': room,
            'is_available': is_available,
        })

    paginator = Paginator(rooms_with_status, 10)
    page = request.GET.get('page', 1)
    rooms_data = paginator.get_page(page)

    context = {
        'rooms': rooms_data,
        'add_form': RoomForm(),
        'room_types': Room.RoomType.choices,
        'room_statuses': Room.RoomStatus.choices,
        'equipment_choices': Equipment.TypeChoices.choices,
        'search': request.GET.get('search', ''),
        'filter_type': request.GET.get('type', ''),
        'filter_capacity': request.GET.get('capacity', ''),
        'filter_building': request.GET.get('building', ''),
        'filter_status': request.GET.get('status', ''),
        'filter_equipment': ','.join(request.GET.getlist('equipment', '')),
        'total': paginator.count,
        'current_time': current_time.strftime('%H:%M'),
        'current_date': current_date.strftime('%d.%m.%Y'),
    }
    return render(request, 'rooms/rooms.html', context)


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def room_add(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = Room.objects.create(
                name=form.cleaned_data['name'],
                building=form.cleaned_data['building'],
                floor=form.cleaned_data['floor'],
                capacity=form.cleaned_data['capacity'],
                type=form.cleaned_data['type'],
                status=form.cleaned_data['status'],
            )
            messages.success(request, f'Аудитория {room.name} успешно создана')
            return redirect('rooms_list')

        # Если форма не валидна, показываем список с ошибками
        qs = Room.objects.all().order_by('building', 'floor', 'name')
        rooms_data = []
        for room in qs:
            rooms_data.append({'room': room, 'is_available': True})

        rooms = Paginator(rooms_data, 10).get_page(1)
        return render(request, 'rooms/rooms.html', {
            'rooms': rooms,
            'add_form': form,
            'open_add_modal': True,
            'room_types': Room.RoomType.choices,
            'room_statuses': Room.RoomStatus.choices,
            'total': qs.count(),
        })

    return redirect('rooms_list')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def room_detail(request, room_id):
    room = get_object_or_404(
        Room.objects.annotate(
            equipment_count=Count('equipment', distinct=True),
            bookings_count=Count('bookings', distinct=True),
        ),
        pk=room_id
    )
    equipment = room.equipment.order_by('type', 'name')
    recent_bookings = room.bookings.select_related(
        'initiator'
    ).order_by('-event_date')[:8]

    return render(request, 'rooms/rooms_detailed.html', {
        'room': room,
        'equipment': equipment,
        'recent_bookings': recent_bookings,
        'room_types': Room.RoomType.choices,
        'room_statuses': Room.RoomStatus.choices,
        'eq_types': Equipment.TypeChoices.choices,
    })


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def room_edit(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            # Сохраняем форму напрямую (instance=room уже связан, save() обновит поля)
            form.save()

            messages.success(request, f'Аудитория {room.name} успешно обновлена')

            # Пытаемся вернуть пользователя туда, откуда он пришел
            # Если Referer нет, отправляем на список аудиторий
            return redirect(request.META.get('HTTP_REFERER', 'rooms_list'))

        # Если форма НЕВАЛИДНА (ошибки валидации)
        # Нужно подготовить данные для рендера списка, чтобы модалка открылась с ошибками
        qs = Room.objects.all().order_by('building', 'floor', 'name')
        rooms_data = []
        for r in qs:
            # Логика определения доступности (заглушка или вызов сервиса)
            rooms_data.append({'room': r, 'is_available': True})

        paginator = Paginator(rooms_data, 10)
        rooms_page = paginator.get_page(1)

        return render(request, 'rooms/rooms.html', {
            'rooms': rooms_page,
            'add_form': RoomForm(),
            'edit_form': form,  # Передаем форму с ошибками
            'edit_room_id': room_id,
            'open_edit_modal': True,
            'room_types': Room.RoomType.choices,
            'room_statuses': Room.RoomStatus.choices,
            'total': qs.count(),
            # Добавьте контекст для даты/времени, если они используются в шаблоне
            'current_date': timezone.now().strftime('%d.%m.%Y'),
            'current_time': timezone.now().strftime('%H:%M'),
        })

    # Если это GET запрос, просто уходим на список
    return redirect('rooms_list')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def room_delete(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        room_name = room.name
        room.delete()
        messages.success(request, f'Аудитория {room_name} удалена')
    return redirect('rooms_list')