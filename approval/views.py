from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from core.decorators import require_role_decorator
from core.permisions import IsApprover

from booking.models import Booking, BookingGroup, Comments
from approval.models import Approval
from approval.serializers import BookingApprovalDetailSerializer
from users.models import User


@login_required(login_url='login')
@require_role_decorator(['approver'])
def approval_page(request):
    return render(request, 'approval/pending.html')


def _safe_full_name(user):
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return ''

    parts = [
        getattr(profile, 'last_name', '') or '',
        getattr(profile, 'first_name', '') or '',
        getattr(profile, 'second_name', '') or '',
    ]
    return ' '.join(part for part in parts if part).strip()


def _safe_profile_value(user, field_name):
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return ''
    return getattr(profile, field_name, '') or ''


class ApproverLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['get']

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        queryset = User.objects.select_related('profile').all().order_by('email')

        if q:
            filters = (
                Q(email__icontains=q) |
                Q(profile__first_name__icontains=q) |
                Q(profile__second_name__icontains=q) |
                Q(profile__last_name__icontains=q) |
                Q(profile__department__icontains=q)
            )
            if q.isdigit():
                filters |= Q(pk=int(q))
            queryset = queryset.filter(filters)

        data = []
        for user in queryset[:10]:
            full_name = _safe_full_name(user)
            label = f'{user.id} · {user.email}'
            if full_name:
                label += f' · {full_name}'

            data.append({
                'id': user.id,
                'label': label,
            })

        return Response(data)


class ApprovalPendingListAPIView(APIView):
    permission_classes = [IsApprover]

    @transaction.atomic
    def get(self, request):
        exclude_booking_id = request.query_params.get('exclude_booking_id')
        excluded_ids = set()

        if exclude_booking_id:
            try:
                excluded_booking = Booking.objects.select_related('group').get(pk=int(exclude_booking_id))
                if excluded_booking.group_id:
                    excluded_ids = set(
                        Booking.objects.filter(group_id=excluded_booking.group_id).values_list('id', flat=True)
                    )
                else:
                    excluded_ids = {excluded_booking.id}
            except (ValueError, Booking.DoesNotExist):
                excluded_ids = set()

        user_approvals = Approval.objects.select_for_update().filter(
            approver=request.user,
            decision=Approval.Decision.IN_PROCESS
        )

        if excluded_ids:
            user_approvals_to_clear = user_approvals.exclude(booking_id__in=excluded_ids)
        else:
            user_approvals_to_clear = user_approvals

        Booking.objects.filter(
            approval__in=user_approvals_to_clear
        ).update(status=Booking.Status.CREATED)

        user_approvals_to_clear.delete()

        pending_bookings = list(
            Booking.objects.filter(status=Booking.Status.CREATED)
            .select_related('initiator', 'room', 'group', 'group__initiator')
            .prefetch_related('equipment')
            .order_by('created_at', 'id')
        )

        grouped = defaultdict(list)
        standalone = []

        for booking in pending_bookings:
            if booking.group_id:
                grouped[booking.group_id].append(booking)
            else:
                standalone.append({
                    'id': booking.id,
                    'scope': 'booking',
                    'event_type': booking.get_event_type_display(),
                    'initiator_first_name': _safe_profile_value(booking.initiator, 'first_name'),
                    'initiator_last_name': _safe_profile_value(booking.initiator, 'last_name'),
                    'initiator_name': _safe_full_name(booking.initiator),
                    'room_name': booking.room.name,
                    'participants': booking.participants,
                    'event_date': booking.event_date,
                    'event_start_time': booking.event_start_time,
                    'event_end_time': booking.event_end_time,
                    'group_id': None,
                    'group_title': None,
                    'group_date_from': None,
                    'group_date_to': None,
                    'group_total_count': 1,
                    'group_pending_count': 1,
                    '_sort_key': booking.created_at,
                })

        results = []

        for group_id, bookings in grouped.items():
            group = bookings[0].group
            pending_count = sum(
                1 for b in bookings
                if b.status in [Booking.Status.CREATED, Booking.Status.PENDING]
            )

            representative = next(
                (b for b in bookings if b.status in [Booking.Status.CREATED, Booking.Status.PENDING]),
                bookings[0]
            )

            results.append({
                'id': representative.id,
                'scope': 'group',
                'group_id': group.id,
                'group_title': group.title,
                'group_comment': group.comment,
                'group_date_from': group.date_from,
                'group_date_to': group.date_to,
                'group_total_count': len(bookings),
                'group_pending_count': pending_count,
                'initiator_first_name': _safe_profile_value(group.initiator, 'first_name'),
                'initiator_last_name': _safe_profile_value(group.initiator, 'last_name'),
                'initiator_name': _safe_full_name(group.initiator),
                'representative_booking_id': representative.id,
                '_sort_key': representative.created_at,
            })

        results.extend(standalone)
        results.sort(key=lambda item: item['_sort_key'])

        for item in results:
            item.pop('_sort_key', None)

        return Response(results)


class ApprovalDetailAPIView(APIView):
    permission_classes = [IsApprover]

    @transaction.atomic
    def get(self, request, pk):
        booking = Booking.objects.select_for_update().select_related(
            'initiator__profile',
            'room',
            'group__initiator__profile'
        ).prefetch_related('equipment').get(pk=pk)

        if booking.group_id:
            scope_qs = Booking.objects.select_for_update().filter(group_id=booking.group_id)
        else:
            scope_qs = Booking.objects.select_for_update().filter(pk=booking.pk)

        scope_ids = list(scope_qs.values_list('id', flat=True))

        old_approvals = Approval.objects.select_for_update().filter(
            approver=request.user,
            decision=Approval.Decision.IN_PROCESS
        ).exclude(booking_id__in=scope_ids)

        Booking.objects.filter(
            approval__in=old_approvals
        ).update(status=Booking.Status.CREATED)

        old_approvals.delete()

        if booking.group_id:
            other_locks = Approval.objects.select_for_update().filter(
                booking__group_id=booking.group_id,
                decision=Approval.Decision.IN_PROCESS
            ).exclude(approver=request.user)

            if other_locks.exists():
                raise PermissionDenied('Групповая заявка уже в работе')

            need_approval_ids = list(
                Booking.objects.filter(
                    group_id=booking.group_id,
                    status__in=[Booking.Status.CREATED, Booking.Status.PENDING]
                ).values_list('id', flat=True)
            )

            for b in Booking.objects.filter(id__in=need_approval_ids):
                approval, created = Approval.objects.get_or_create(
                    booking=b,
                    defaults={
                        'approver': request.user,
                        'decision': Approval.Decision.IN_PROCESS
                    }
                )

                if not created:
                    if approval.decision == Approval.Decision.IN_PROCESS and approval.approver != request.user:
                        raise PermissionDenied('Групповая заявка уже в работе')
                    if approval.decision != Approval.Decision.IN_PROCESS:
                        approval.approver = request.user
                        approval.decision = Approval.Decision.IN_PROCESS
                        approval.save()

                if b.status == Booking.Status.CREATED:
                    b.status = Booking.Status.PENDING
                    b.save(update_fields=['status'])
        else:
            approval, created = Approval.objects.get_or_create(
                booking=booking,
                defaults={
                    'approver': request.user,
                    'decision': Approval.Decision.IN_PROCESS
                }
            )

            if not created:
                if approval.decision == Approval.Decision.IN_PROCESS and approval.approver != request.user:
                    raise PermissionDenied('Заявка уже в работе')
                if approval.decision != Approval.Decision.IN_PROCESS:
                    approval.approver = request.user
                    approval.decision = Approval.Decision.IN_PROCESS
                    approval.save()

            if booking.status == Booking.Status.CREATED:
                booking.status = Booking.Status.PENDING
                booking.save(update_fields=['status'])

        scope_bookings = list(
            Booking.objects.filter(id__in=scope_ids)
            .select_related(
                'initiator__profile',
                'room',
                'group__initiator__profile',
                'approval'
            )
            .prefetch_related('equipment')
            .order_by('created_at', 'id')
        )

        group_total_count = len(scope_bookings)
        group_pending_count = sum(
            1 for b in scope_bookings
            if b.status in [Booking.Status.CREATED, Booking.Status.PENDING]
        )

        serializer = BookingApprovalDetailSerializer(
            booking,
            context={
                'group_bookings': scope_bookings,
                'group_total_count': group_total_count,
                'group_pending_count': group_pending_count,
            }
        )
        return Response(serializer.data)


class ApprovalDecisionAPIView(APIView):
    permission_classes = [IsApprover]

    @transaction.atomic
    def post(self, request, pk):
        booking = Booking.objects.select_for_update().select_related('group').get(pk=pk)

        if booking.group_id:
            scope_qs = Booking.objects.select_for_update().filter(group_id=booking.group_id)
        else:
            scope_qs = Booking.objects.select_for_update().filter(pk=booking.pk)

        scope_bookings = list(scope_qs.order_by('created_at', 'id'))
        scope_ids = [b.id for b in scope_bookings]

        approvals = Approval.objects.select_for_update().filter(booking_id__in=scope_ids)

        if approvals.filter(decision=Approval.Decision.IN_PROCESS).exclude(approver=request.user).exists():
            raise PermissionDenied('Эта заявка не назначена вам для согласования')

        own_lock_exists = approvals.filter(
            approver=request.user,
            decision=Approval.Decision.IN_PROCESS
        ).exists()

        if not own_lock_exists:
            raise PermissionDenied('Эта заявка не назначена вам для согласования')

        decision = request.data.get('decision')
        comment_text = (request.data.get('comment') or '').strip()

        if decision not in ['approved', 'rejected']:
            return Response({'detail': 'Неверное решение'}, status=status.HTTP_400_BAD_REQUEST)

        if decision == 'rejected' and not comment_text:
            return Response({'detail': 'Введите причину отклонения'}, status=status.HTTP_400_BAD_REQUEST)

        first_requires_approval = next(
            (b for b in scope_bookings if b.status in [Booking.Status.CREATED, Booking.Status.PENDING]),
            scope_bookings[0] if scope_bookings else None
        )

        if comment_text and first_requires_approval:
            Comments.objects.create(
                booking=first_requires_approval,
                author=request.user,
                text=comment_text
            )

        new_status = Booking.Status.APPROVED if decision == 'approved' else Booking.Status.REJECTED
        Booking.objects.filter(id__in=scope_ids).update(status=new_status)

        for b in scope_bookings:
            approval, created = Approval.objects.get_or_create(
                booking=b,
                defaults={
                    'approver': request.user,
                    'decision': Approval.Decision.IN_PROCESS
                }
            )
            approval.approver = request.user
            approval.decision = new_status
            approval.save()

        return Response({'detail': f'Заявка {"одобрена" if decision == "approved" else "отклонена"}'}, status=status.HTTP_200_OK)


class ApprovalDetailCancelAPIView(APIView):
    permission_classes = [IsApprover]

    @transaction.atomic
    def post(self, request, pk):
        booking = Booking.objects.select_for_update().select_related('group').get(pk=pk)

        if booking.group_id:
            scope_qs = Booking.objects.select_for_update().filter(group_id=booking.group_id)
        else:
            scope_qs = Booking.objects.select_for_update().filter(pk=booking.pk)

        scope_ids = list(scope_qs.values_list('id', flat=True))

        approvals = Approval.objects.select_for_update().filter(
            booking_id__in=scope_ids,
            approver=request.user,
            decision=Approval.Decision.IN_PROCESS
        )

        if not approvals.exists():
            raise PermissionDenied('Заявка не была заблокирована вами')

        Booking.objects.filter(approval__in=approvals).update(status=Booking.Status.CREATED)
        approvals.delete()

        return Response({'detail': 'Блокировка снята, заявка возвращена в список ожидания'}, status=status.HTTP_200_OK)