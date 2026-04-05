from django.db import models

from booking.models import Booking
from django.contrib.auth import get_user_model



class Approval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'одобрена'
        IN_PROCESS = 'in_process', 'в процессе'
        REJECTED = 'rejected', 'отклонена'

    id = models.AutoField(primary_key=True)

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='approval')
    approver = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    decision = models.CharField(choices=Decision.choices, max_length=20)
    decided_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.decision} {self.approver.email} {self.booking}"

    class Meta:
        verbose_name = 'Согласование заявки'
        verbose_name_plural = 'Согласования заявок'



