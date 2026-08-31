from notifications.models import Notification


def notifications_processor(request):
    if not request.user.is_authenticated:
        return {}
    count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return {'unread_notifications_count': count}