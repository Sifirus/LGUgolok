from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

from equipment.models import Equipment
from rooms.models import Room


class Booking(models.Model):

    class Status(models.TextChoices):
        CREATED = 'created', 'создана'
        PENDING = 'pending', 'на согласовании'
        APPROVED = 'approved', 'одобрена'
        REJECTED = 'rejected', 'отклонена'
        COMPLETED = 'completed', 'завершена'
        CANCELED = 'canceled', 'отменена'

    class EventType(models.TextChoices):
        LECTURE = 'lecture', 'Лекция'
        PRACTICE = 'practice', 'Практическое занятие'
        STATE_EXAM = 'state_exam', 'Государственный экзамен'
        THESIS_DEFENSE = 'thesis_defense', 'Защита ВКР'
        SCIENTIFIC_SEMINAR = 'scientific_seminar', 'Научный семинар'
        CONFERENCE = 'conference', 'Конференция'
        ORGANIZATIONAL_MEETING = 'organizational_meeting', 'Организационное собрание'

    id = models.AutoField(primary_key=True)

    initiator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    equipment = models.ManyToManyField(Equipment, related_name='bookings', blank=True)

    event_type = models.CharField(max_length=30, choices=EventType.choices, default=EventType.LECTURE)
    event_date = models.DateField()
    event_start_time = models.TimeField()
    event_end_time = models.TimeField()

    participants = models.IntegerField()

    comment = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.name} {self.initiator.email}"

    def clean(self):
        super().clean()
        if self.event_date < datetime.today().date():
            raise ValidationError('Дата бронирования не может быть в прошлом')
        if self.event_start_time > self.event_end_time:
            raise ValidationError('Время конца бронирования должно быть позже начала')


    class Meta:
        verbose_name = 'Заявка на бронирование'
        verbose_name_plural = 'Заявки на бронирование'


class Approval(models.Model):
    class Decision(models.TextChoices):
        PENDING = 'pending', 'ожидает'
        APPROVED = 'approved', 'одобрено'
        REJECTED = 'rejected', 'отклонено'

    id = models.AutoField(primary_key=True)

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='decisions')
    approver = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='decisions')

    decision = models.CharField(choices=Decision.choices, max_length=20, default=Decision.PENDING)
    decided_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.decision} {self.approver.email} {self.booking}"

    class Meta:
        verbose_name = 'Согласование заявки'
        verbose_name_plural = 'Согласования заявок'


class Comments(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.TextField()
    approval = models.ForeignKey(Approval, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        snippet = (self.text[:50] + '...') if len(self.text) > 50 else self.text
        return f"{self.author.email} - {self.approval}: {snippet}"