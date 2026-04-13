from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Approval


@receiver(pre_save, sender=Approval)
def set_approval_decided_at(sender, instance, **kwargs):
    if not instance.pk:
        instance.decision = Approval.Decision.IN_PROCESS
        instance.decided_at = None
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if (old_instance.decision == Approval.Decision.IN_PROCESS and
            instance.decision != Approval.Decision.IN_PROCESS):
        instance.decided_at = timezone.now()