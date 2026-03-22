from django.db import models

from booking.models import Booking
from django.contrib.auth import get_user_model



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
