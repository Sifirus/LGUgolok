from django.db import models


class Room(models.Model):
    class RoomType(models.TextChoices):
        LECTURE = "lecture", "Лекционная"
        SEMINAR = "seminar", "Семинарская"
        LAB = "lab", "Лаборатория"
        CONF = "conference", "Конференц-зал"
        HALL = "hall", "Актовый зал"

    class RoomStatus(models.TextChoices):
        ACTIVE = "active", "Активна"
        MAINTENANCE = "maintenance", "На обслуживании"
        CLOSED = "closed", "Закрыта"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    building = models.CharField(max_length=100) #TODO Choises
    floor = models.IntegerField()
    capacity = models.IntegerField()
    status = models.CharField(choices=RoomStatus.choices, default=RoomStatus.ACTIVE, max_length=100)
    type = models.CharField(choices=RoomType.choices, default=RoomType.LECTURE, max_length=100) #TODO model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Аудитория'
        verbose_name_plural = 'Аудитории'

#TODO class avatar