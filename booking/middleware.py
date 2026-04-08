from django.utils import timezone
from django.db.models import Q
from .models import Booking


class AutoCompleteBookingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Обновляем статусы при каждом запросе
        self.update_completed_bookings()

        response = self.get_response(request)
        return response

    def update_completed_bookings(self):
        current_datetime = timezone.now()
        current_time = current_datetime.time()
        current_date = current_datetime.date()

        # Находим заявки, которые нужно завершить:
        # 1. Статус APPROVED
        # 2. Дата мероприятия меньше текущей ИЛИ
        #    (дата равна текущей И время окончания меньше текущего времени)
        bookings_to_complete = Booking.objects.filter(
            status=Booking.Status.APPROVED
        ).filter(
            Q(event_date__lt=current_date) |
            Q(event_date=current_date, event_end_time__lt=current_time)
        )

        # Обновляем найденные заявки
        count = bookings_to_complete.update(status=Booking.Status.COMPLETED)

        if count > 0:
            print(f"Автоматически завершено {count} мероприятий")