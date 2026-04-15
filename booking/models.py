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

    group = models.ForeignKey(
        'BookingGroup',
        on_delete=models.CASCADE,
        related_name='booking_set',
        blank=True,
        null=True
    )

    initiator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    equipment = models.ManyToManyField(Equipment, related_name='bookings', blank=True)

    event_type = models.CharField(max_length=30, choices=EventType.choices, default=EventType.LECTURE)
    event_date = models.DateField()
    event_start_time = models.TimeField()
    event_end_time = models.TimeField()

    participants = models.IntegerField(default=60)

    comment = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.name} {self.initiator.email}"

    class Meta:
        verbose_name = 'Заявка на бронирование'
        verbose_name_plural = 'Заявки на бронирование'


class BookingGroup(models.Model):
    initiator = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='booking_groups')
    title = models.CharField(max_length=200)
    comment = models.TextField(blank=True)
    date_from = models.DateField()
    date_to = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Групповая заявка'
        verbose_name_plural = 'Групповые заявки'

    def __str__(self):
        return f'Группа #{self.pk} — {self.title}'

    @property
    def total_count(self):
        return self.booking_set.count()


class Comments(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.TextField()
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        snippet = (self.text[:50] + '...') if len(self.text) > 50 else self.text
        return f"{self.author.email} - {self.booking}: {snippet}"