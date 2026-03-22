from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from booking.forms import BookingForm
from django.contrib.auth.decorators import login_required

from equipment.models import Equipment
from equipment.services.equipment_service import AvailableEquipmentService
from rooms.services.rooms_service import AvailableRoomsService
from rooms.models import Room
from approval.services.approval_services import ApprovalEngine

@login_required(login_url='login')
def booking_create(request): #TODO fix architecture и гонки транзакций
    form = BookingForm(request.POST or None)
    room_types = Room.RoomType.choices
    context = {'form': form, 'room_types': room_types}

    if request.method == 'POST':
        is_conflict = False
        if form.is_valid():
            cleaned_data = form.cleaned_data

            available_room = AvailableRoomsService.get_available_rooms(
                Room.objects.filter(pk=cleaned_data['room'].pk),
                cleaned_data['event_date'],
                cleaned_data['event_start_time'],
                cleaned_data['event_end_time'],
            )
            if not available_room.exists():
                messages.warning(request, 'Аудиторию только что забронировали')
                is_conflict = True

            if cleaned_data['equipment']:
                selected_equipment = Equipment.objects.filter(pk__in=cleaned_data['equipment'])
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

                    messages.warning(request,f'Часть оборудования только что забронировали: {", ".join(unavailable_equipment_names)}')
                    context['unavailable_equipment_ids'] = unavailable_equipment_ids
                    is_conflict = True

            if is_conflict:
                return render(request, 'booking/create_booking.html', context)

            status = ApprovalEngine.get_status(
                cleaned_data['room'], cleaned_data['equipment'], cleaned_data['event_type']
            )

            booking = form.save(commit=False)
            booking.initiator = request.user
            booking.status = status
            booking.save()
            form.save_m2m()
            return redirect(reverse('index'))
    else:
        return render(request, 'booking/create_booking.html', context)