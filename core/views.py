from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date

from booking.models import Booking
from rooms.models import Room
from equipment.models import Equipment

from django.contrib.auth import get_user_model


user_model = get_user_model()

@login_required(login_url='login')
def index(request):
    user = request.user
    role = user.role
    ctx  = {'role': role}

    if role == 'initiator':
        ctx.update(_initiator_context(user))
        return render(request, 'core/dashboard_initiator.html', ctx)

    elif role == 'approver':
        ctx.update(_approver_context(user))
        return render(request, 'core/dashboard_approver.html', ctx)

    elif role == 'operator':
        ctx.update(_operator_context())
        return render(request, 'core/dashboard_operator.html', ctx)

    return render(request, 'core/dashboard_initiator.html', ctx)


def _initiator_context(user):
    bookings = Booking.objects.filter(initiator=user).order_by('-created_at')
    return {
        'total':     bookings.count(),
        'pending':   bookings.filter(status='pending').count(),
        'approved':  bookings.filter(status='approved').count(),
        'rejected':  bookings.filter(status='rejected').count(),
        'recent':    bookings.select_related('room')[:5],
    }


def _approver_context(user):
    from approval.models import Approval
    pending_qs = Booking.objects.filter(
        status='created'
    ).select_related('initiator', 'room').order_by('-created_at')

    decided = Approval.objects.filter(
        approver=user
    ).exclude(decision='in_process').count()

    return {
        'pending_count':  pending_qs.count(),
        'pending_list':   pending_qs[:5],
        'decided_count':  decided,
    }


def _operator_context():
    today = date.today()
    month_start = today.replace(day=1)
    return {
        'users_total':     user_model.objects.count(),
        'users_blocked':   user_model.objects.filter(is_blocked=True).count(),
        'rooms_total':     Room.objects.count(),
        'rooms_active':    Room.objects.filter(status='active').count(),
        'equip_total':     Equipment.objects.count(),
        'equip_maintenance': Equipment.objects.filter(status='maintenance').count(),
        'bookings_month':  Booking.objects.filter(
            created_at__date__gte=month_start
        ).count(),
        'bookings_pending': Booking.objects.filter(status='pending').count(),
        'recent_bookings': Booking.objects.select_related(
            'initiator', 'room'
        ).order_by('-created_at')[:5],
    }


def no_access(request, exception=None):
    return render(request, 'core/403.html', status=403)


def page_not_found(request, exception=None):
    return render(request, 'core/404.html', status=404)