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
        qs = Room.objects.all()

        if cleaned_data.get('is_available'):
            qs = AvailableRoomsService.get_available_rooms(
                qs,
                cleaned_data.get('event_date'),
                cleaned_data.get('event_start_time'),
                cleaned_data.get('event_end_time')
            )

        qs = RoomsFiltersService.apply_filters(qs, cleaned_data)

        serializer = RoomSerializer(qs, many=True)

        return Response(serializer.data)


class RoomLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        qs = Room.objects.all().order_by('building', 'floor', 'name')

        if q:
            filters = Q(name__icontains=q) | Q(building__icontains=q)
            if q.isdigit():
                filters |= Q(pk=int(q))
            qs = qs.filter(filters)

        data = []
        for room in qs[:10]:
            data.append({
                'id': room.id,
                'label': f'{room.id} · {room.name} · {room.building}, этаж {room.floor}',
                'name': room.name,
                'building': room.building,
                'floor': room.floor,
            })

        return Response(data)


@login_required(login_url='login')
@require_role_decorator(roles=['operator'])
def rooms_list(request):
    qs = Room.objects.all().order_by('building', 'floor', 'name')

    filters = {
        'search_query': request.GET.get('search', ''),
        'type': request.GET.get('type', ''),
        'capacity': request.GET.get('capacity', ''),
        'building': request.GET.get('building', ''),
        'status': request.GET.get('status', ''),
        'equipment': ','.join(request.GET.getlist('equipment', '')),
    }

    filters = {k: v for k, v in filters.items() if v}

    if filters:
        qs = RoomsFiltersService.apply_filters(qs, filters)

    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    # TODO Для каждой аудитории проверяем, занята ли она сейчас N+1
    rooms_with_status = []
    for room in qs:
        try:
            available_rooms = AvailableRoomsService.get_available_rooms(
                Room.objects.filter(pk=room.pk),
                current_date,
                current_time,
                current_time
            )
            is_available = available_rooms.exists()
        except ValueError:
            is_available = True

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


@login_required(login_url='login')
@require_role_decorator(roles=['operator'])
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

        qs = Room.objects.all().order_by('building', 'floor', 'name')
        rooms_data = []
        for room in qs: #TODO ???
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


@login_required(login_url='login')
@require_role_decorator(roles=['operator'])
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


@login_required(login_url='login')
@require_role_decorator(roles=['operator'])
def room_edit(request, room_id):
    room = get_object_or_404(Room, pk=room_id)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()

            messages.success(request, f'Аудитория {room.name} успешно обновлена')

            return redirect(request.META.get('HTTP_REFERER', 'rooms_list'))

        qs = Room.objects.all().order_by('building', 'floor', 'name')
        rooms_data = []

        for r in qs: #TODO ??? Логика определения доступности (заглушка или вызов сервиса)
            rooms_data.append({'room': r, 'is_available': True})

        paginator = Paginator(rooms_data, 10)
        rooms_page = paginator.get_page(1)

        return render(request, 'rooms/rooms.html', {
            'rooms': rooms_page,
            'add_form': RoomForm(),
            'edit_form': form,
            'edit_room_id': room_id,
            'open_edit_modal': True,
            'room_types': Room.RoomType.choices,
            'room_statuses': Room.RoomStatus.choices,
            'total': qs.count(),
            'current_date': timezone.now().strftime('%d.%m.%Y'),
            'current_time': timezone.now().strftime('%H:%M'),
        })

    return redirect('rooms_list')


@login_required(login_url='login')
@require_role_decorator(roles=['operator'])
def room_delete(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(Room, pk=room_id)
        room_name = room.name
        room.delete()
        messages.success(request, f'Аудитория {room_name} удалена')
    return redirect('rooms_list')
