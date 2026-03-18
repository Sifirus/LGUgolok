from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from equipment.services.equipment_service import get_available_equipment


@login_required(login_url='login')
def available_equipment_json(request):
    event_date = request.GET.get('event_date')
    event_start_time = request.GET.get('event_start_time')
    event_end_time = request.GET.get('event_end_time')

    if not all([event_date, event_start_time, event_end_time]):
        return JsonResponse({'error': 'Event date, event start and end time are required'}, status=400)

    try:
        equipment = get_available_equipment(event_date, event_start_time, event_end_time)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    data = [
        {
            'id': item.id,
            'inventory_number': item.inventory_number,
            'type': item.type,
            'name': item.name,
            'model': item.model,

        }
        for item in equipment
    ]

    return JsonResponse({'equipment_available': data})

#TODO фильтры и поля