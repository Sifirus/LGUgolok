from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from booking.models import Booking, Comments
from notifications.service import NotificationService


@receiver(pre_save, sender=Booking)
def capture_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._pre_status = Booking.objects.values_list(
                'status', flat=True
            ).get(pk=instance.pk)
        except Booking.DoesNotExist:
            instance._pre_status = None
    else:
        instance._pre_status = None


@receiver(post_save, sender=Booking)
def on_booking_saved(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, '_pre_status', None)
    if (
        old_status
        and old_status != instance.status
        and instance.status != Booking.Status.PENDING
    ):
        NotificationService.booking_status_changed(instance, old_status)


@receiver(post_save, sender=Comments)
def on_comment_saved(sender, instance, created, **kwargs):
    if created:
        NotificationService.comment_added(instance)