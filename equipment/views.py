from equipment.serializers import EquipmentFiltersSerializer, EquipmentSerializer

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.decorators import require_role_decorator
from equipment.forms import EquipmentForm
from equipment.models import Equipment
from equipment.services.equipment_service import AvailableEquipmentService, EquipmentFiltersService
from rooms.models import Room

from django.db.models import Q

class EquipmentSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        serializer = EquipmentFiltersSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        cleaned_data = serializer.validated_data
        queryset = Equipment.objects.all()

        if cleaned_data.get('is_available'):
            queryset = AvailableEquipmentService.get_available_equipment(
                queryset,
                cleaned_data.get('event_date'),
                cleaned_data.get('event_start_time'),
                cleaned_data.get('event_end_time')
            )

        queryset = EquipmentFiltersService.apply_filters(queryset, cleaned_data)

        serializer = EquipmentSerializer(queryset, many=True)

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
def equipment_list(request):
    qs = Equipment.objects.select_related('room').all().order_by('type', 'name', 'inventory_number')

    filters = {
        'search_query': request.GET.get('search', ''),
        'type': request.GET.get('type', ''),
        'status': request.GET.get('status', ''),
        'room_id': request.GET.get('room_id', ''),
        'location': request.GET.get('location', ''),
    }
    filters = {k: v for k, v in filters.items() if v}

    if filters:
        qs = EquipmentFiltersService.apply_filters(qs, filters)

    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    equipment_with_status = []
    for item in qs:
        try:
            available_equipment = AvailableEquipmentService.get_available_equipment(
                Equipment.objects.filter(pk=item.pk),
                current_date,
                current_time,
                current_time,
            )
            is_available = available_equipment.exists()
        except ValueError:
            is_available = True

        equipment_with_status.append({
            'equipment': item,
            'is_available': is_available,
        })

    paginator = Paginator(equipment_with_status, 10)
    page = request.GET.get('page', 1)
    page_data = paginator.get_page(page)

    room_id = request.GET.get('room_id', '')
    selected_room = Room.objects.filter(pk=room_id).first() if room_id else None

    context = {
        'equipment': page_data,
        'add_form': EquipmentForm(),
        'equipment_types': Equipment.TypeChoices.choices,
        'equipment_statuses': Equipment.StatusChoices.choices,
        'search': request.GET.get('search', ''),
        'filter_type': request.GET.get('type', ''),
        'filter_status': request.GET.get('status', ''),
        'filter_location': request.GET.get('location', ''),
        'filter_room_id': room_id,
        'filter_room_label': selected_room.name if selected_room else '',
        'total': paginator.count,
        'current_date': current_date.strftime('%d.%m.%Y'),
        'current_time': current_time.strftime('%H:%M'),
        'room_lookup_url': 'room_lookup_api',
    }
    return render(request, 'equipment/equipment.html', context)


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def equipment_add(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            Equipment.objects.create(
                inventory_number=cd['inventory_number'],
                name=cd['name'],
                model=cd['model'],
                type=cd['type'],
                status=cd['status'],
                is_stationary=cd['is_stationary'],
                room_id=cd['room_id'] or None,
            )
            messages.success(request, 'Оборудование успешно создано')
            return redirect('equipment_list')

        qs = Equipment.objects.select_related('room').all().order_by('type', 'name', 'inventory_number')
        equipment_data = [{'equipment': item, 'is_available': True} for item in qs]
        page = Paginator(equipment_data, 10).get_page(1)

        return render(request, 'equipment/equipment.html', {
            'equipment': page,
            'add_form': form,
            'open_add_modal': True,
            'equipment_types': Equipment.TypeChoices.choices,
            'equipment_statuses': Equipment.StatusChoices.choices,
            'total': qs.count(),
        })

    return redirect('equipment_list')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def equipment_detail(request, equipment_id):
    from rooms.models import Room
    equip = get_object_or_404(Equipment.objects.select_related('room'), pk=equipment_id)
    recent_bookings = equip.bookings.select_related(
        'initiator', 'room'
    ).order_by('-event_date')[:8]

    rooms = Room.objects.filter(status='active').order_by('building', 'name')

    return render(request, 'equipment/equipment_detail.html', {
        'equip': equip,
        'recent_bookings': recent_bookings,
        'rooms': rooms,
        'eq_types': Equipment.TypeChoices.choices,
        'eq_statuses': Equipment.StatusChoices.choices,
        'room_lookup_url': 'room_lookup_api',

    })


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def equipment_edit(request, equipment_id):
    item = get_object_or_404(Equipment, pk=equipment_id)

    if request.method == 'POST':
        # ВАЖНО: передаем instance=item, чтобы отработала логика clean_inventory_number
        form = EquipmentForm(request.POST, instance=item)

        if form.is_valid():
            cd = form.cleaned_data
            # Обновляем поля объекта из очищенных данных формы
            item.inventory_number = cd['inventory_number']
            item.name = cd['name']
            item.model = cd['model']
            item.type = cd['type']
            item.status = cd['status']
            item.is_stationary = cd['is_stationary']
            item.room_id = cd['room_id']  # Если там None, Django запишет NULL
            item.save()

            messages.success(request, f'Оборудование "{item.name}" успешно обновлено')
            # Перенаправляем на страницу, с которой пришли (Referer) или на детальную
            return redirect(request.META.get('HTTP_REFERER', 'equipment_list'))

        # Если форма НЕВАЛИДНА (например, номер уже занят кем-то другим)
        # Собираем данные для рендера списка, чтобы модалка открылась поверх таблицы
        qs = Equipment.objects.select_related('room').all().order_by('type', 'name', 'inventory_number')

        # Используем твой метод определения доступности (как в equipment_list)
        now = timezone.now()
        equipment_with_status = []
        for row in qs:
            equipment_with_status.append({
                'equipment': row,
                'is_available': True  # Или вызови здесь AvailableEquipmentService, если критично
            })

        paginator = Paginator(equipment_with_status, 10)
        page = paginator.get_page(1)

        return render(request, 'equipment/equipment.html', {
            'equipment': page,
            'add_form': EquipmentForm(),  # Пустая форма для кнопки "Добавить"
            'edit_form': form,  # Форма с ошибками
            'edit_equipment_id': item.pk,
            'open_edit_modal': True,  # Флаг для JS, чтобы модалка не закрылась
            'equipment_types': Equipment.TypeChoices.choices,
            'equipment_statuses': Equipment.StatusChoices.choices,
            'total': qs.count(),
            'room_lookup_url': 'room_lookup_api',
        })

    return redirect('equipment_list')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def equipment_delete(request, equipment_id):
    if request.method == 'POST':
        item = get_object_or_404(Equipment, pk=equipment_id)
        name = item.name
        item.delete()
        messages.success(request, f'Оборудование {name} удалено')
    return redirect('equipment_list')