from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notifications.models import Notification


@login_required(login_url='login')
def notification_list(request):
    notifications = request.user.notifications.select_related('booking__room')[:50]
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
    })


@login_required(login_url='login')
def notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])

    if notif.booking_id:
        return redirect('booking_detail', booking_id=notif.booking_id)
    return redirect('notification_list')


@require_POST
@login_required(login_url='login')
def notification_read_all(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})


@login_required(login_url='login')
def notification_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})