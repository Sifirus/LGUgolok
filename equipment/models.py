from django.db import models
from rooms.models import Room


class Equipment(models.Model):
    class TypeChoices(models.TextChoices):
        PROJECTOR = "projector", "Проектор"
        MICROPHONE = "microphone", "Микрофон"
        LAPTOP = "laptop", "Ноутбук"
        SCREEN = "screen", "Экран"
        CAMERA = "camera", "Веб-камера"

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "Активно"
        MAINTENANCE = "maintenance", "На обслуживании"
        WRITTEN_OFF = "written_off", "Списано"

    id = models.AutoField(primary_key=True)
    inventory_number = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TypeChoices.choices)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    is_stationary = models.BooleanField(default=False)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, related_name='equipment', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.get_type_display()} {self.name} {self.model}'

    def get_current_location(self, on_date, at_time):
        """
        Возвращает местонахождение оборудования на указанные дату и время.

        Возвращает словарь:
          {
            'location_type': 'booking' | 'home' | 'storage',
            'room':    Room instance or None,
            'booking': Booking instance or None,
            'label':   str — человекочитаемое описание
          }

        Логика:
          1. Если есть активная заявка на эти дату/время → в аудитории заявки
          2. Иначе если оборудование стационарное и привязано к room → дома
          3. Иначе → на складе / местоположение не определено
        """
        from booking.models import Booking

        active = (
            Booking.objects
            .filter(
                equipment=self,
                event_date=on_date,
                event_start_time__lte=at_time,
                event_end_time__gt=at_time,
                status__in=[
                    Booking.Status.APPROVED,
                    Booking.Status.PENDING,
                    Booking.Status.CREATED,
                ],
            )
            .select_related('room')
            .order_by('event_start_time')
            .first()
        )

        if active:
            return {
                'location_type': 'booking',
                'room':    active.room,
                'booking': active,
                'label':   f'{active.room.name} (заявка #{active.pk})',
            }

        if self.room_id:
            return {
                'location_type': 'home',
                'room':    self.room,
                'booking': None,
                'label':   f'{self.room.name} (постоянное место)',
            }

        return {
            'location_type': 'storage',
            'room':    None,
            'booking': None,
            'label':   'Склад / не определено',
        }

    class Meta:
        verbose_name = 'Оборудование'
        verbose_name_plural = verbose_name