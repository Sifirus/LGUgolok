from django.db import models
from django.contrib.auth import get_user_model


class Notification(models.Model):

    class Kind(models.TextChoices):
        BOOKING_STATUS  = 'booking_status',  'Изменение статуса заявки'
        COMMENT_ADDED   = 'comment_added',   'Новый комментарий'

    recipient  = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE,
        related_name='notifications'
    )
    kind       = models.CharField(max_length=30, choices=Kind.choices)
    title      = models.CharField(max_length=200)
    body       = models.TextField(blank=True)
    booking    = models.ForeignKey(
        'booking.Booking', on_delete=models.CASCADE,
        null=True, blank=True, related_name='notifications'
    )
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return f'{self.kind} → {self.recipient.email}'