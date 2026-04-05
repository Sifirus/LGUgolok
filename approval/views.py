from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db import transaction
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

from core.decorators import require_role_decorator
from core.permisions import IsApprover

from booking.models import Booking, Comments
from approval.models import Approval
from approval.serializers import BookingApprovalSerializer, BookingApprovalDetailSerializer


@require_role_decorator(['approver'])
@login_required(login_url='login')
def approval_page(request):
    return render(request, 'approval/pending.html')


class ApprovalPendingListAPIView(ListAPIView):
    permission_classes = [IsApprover]
    serializer_class = BookingApprovalSerializer

    @transaction.atomic
    def get_queryset(self):
        exclude_booking_id = self.request.query_params.get('exclude_booking_id')

        user_approvals = Approval.objects.select_for_update().filter(
            approver=self.request.user,
            decision='in_process'
        )

        if exclude_booking_id:
            user_approvals_to_clear = user_approvals.exclude(booking_id=exclude_booking_id)
        else:
            user_approvals_to_clear = user_approvals

        Booking.objects.filter(
            approval__in=user_approvals_to_clear
        ).update(status=Booking.Status.CREATED)

        user_approvals_to_clear.delete()

        return Booking.objects.filter(
            status=Booking.Status.CREATED
        ).order_by('-created_at')


class ApprovalDetailAPIView(RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingApprovalDetailSerializer
    permission_classes = [IsApprover]

    @transaction.atomic
    def get_object(self):
        obj = super().get_object()

        # Блокируем запись для предотвращения гонки
        obj = Booking.objects.select_for_update().get(pk=obj.pk)

        approval = getattr(obj, 'approval', None)

        if approval:
            if approval.approver != self.request.user:
                raise PermissionDenied('Заявка уже в работе')
        else:
            old_approvals = Approval.objects.select_for_update().filter(
                approver=self.request.user,
                decision='in_process'
            )
            Booking.objects.filter(
                approval__in=old_approvals
            ).update(status=Booking.Status.CREATED)
            old_approvals.delete()

            approval, created = Approval.objects.get_or_create(
                booking=obj,
                defaults={
                    'approver': self.request.user,
                    'decision': 'in_process'
                }
            )

            if created:
                obj.status = Booking.Status.PENDING
                obj.save(update_fields=['status'])

        return obj


class ApprovalDecisionAPIView(GenericAPIView):
    permission_classes = [IsApprover]
    serializer_class = None

    @transaction.atomic
    def post(self, request, pk):
        booking = Booking.objects.select_for_update().get(pk=pk)
        approval = getattr(booking, 'approval', None)

        if not approval or approval.approver != request.user:
            raise PermissionDenied('Эта заявка не назначена вам для согласования')

        decision = request.data.get('decision')
        comment_text = request.data.get('comment', '').strip()

        if comment_text:
            Comments.objects.create(booking=booking, author=request.user, text=comment_text)

        if decision == 'approved':
            booking.status = Booking.Status.APPROVED
            approval.decision = 'approved'
        elif decision == 'rejected':
            if not comment_text:
                return Response({'detail': 'Введите причину отклонения'}, status=status.HTTP_400_BAD_REQUEST)
            booking.status = Booking.Status.REJECTED
            approval.decision = 'rejected'
        else:
            return Response({'detail': 'Неверное решение'}, status=status.HTTP_400_BAD_REQUEST)

        booking.save(update_fields=['status'])
        approval.save(update_fields=['decision'])

        decision_display = approval.get_decision_display()

        return Response({'detail': f'Заявка {decision_display}'}, status=status.HTTP_200_OK)


# approval/views.py (добавить в конец файла)

class ApprovalDetailCancelAPIView(GenericAPIView):
    permission_classes = [IsApprover]

    @transaction.atomic
    def post(self, request, pk):
        booking = Booking.objects.select_for_update().get(pk=pk)
        approval = getattr(booking, 'approval', None)

        if not approval or approval.approver != request.user:
            raise PermissionDenied('Заявка не была заблокирована вами')

        if approval.decision != 'in_process':
            raise PermissionDenied('Заявка уже обработана')

        # Возвращаем статус заявки в CREATED
        booking.status = Booking.Status.CREATED
        booking.save(update_fields=['status'])

        # Удаляем запись о согласовании (снимаем блокировку)
        approval.delete()

        return Response({'detail': 'Блокировка снята, заявка возвращена в список ожидания'},
                        status=status.HTTP_200_OK)