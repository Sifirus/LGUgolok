from django.db import models

from rooms.models import Room


class Equipment(models.Model):
    class TypeChoices(models.TextChoices):  # TODO many to many
        PROJECTOR = "projector", "Проектор"
        MICROPHONE = "microphone", "Микрофон"
        LAPTOP = "laptop", "Ноутбук"
        SCREEN = "screen", "Экран"
        CAMERA = "camera", "Веб-камера"

    class StatusChoices(models.TextChoices):  # TODO how to get
        ACTIVE = "active", "Активна"
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

    class Meta:
        verbose_name = 'Оборудование'
        verbose_name_plural = verbose_name
# TODO class avatar
