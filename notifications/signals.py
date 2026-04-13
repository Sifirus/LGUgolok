from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from booking.models import Booking, Comments
from notifications.service import NotificationService

# TODO Храним старый статус до сохранения
_old_status_cache = {}


@receiver(pre_save, sender=Booking)
def capture_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Booking.objects.get(pk=instance.pk)
            _old_status_cache[instance.pk] = old.status
        except Booking.DoesNotExist:
            pass


@receiver(post_save, sender=Booking)
def on_booking_saved(sender, instance, created, **kwargs):
    if created:
        return

    old_status = _old_status_cache.pop(instance.pk, None)
    if old_status and old_status != instance.status and instance.status != Booking.Status.PENDING:
        NotificationService.booking_status_changed(instance, old_status)


@receiver(post_save, sender=Comments)
def on_comment_saved(sender, instance, created, **kwargs):
    if created:
        NotificationService.comment_added(instance)