from notifications.models import Notification
from django.contrib.auth import get_user_model


class NotificationService:

    @staticmethod
    def _send(recipient, kind, title, body='', booking=None):
        Notification.objects.create(
            recipient=recipient,
            kind=kind,
            title=title,
            body=body,
            booking=booking,
        )

    @classmethod
    def booking_status_changed(cls, booking, old_status): #TODO ???
        status = booking.status
        STATUS_META = {
            'pending':   ('На согласовании', 'Заявка #{pk} отправлена на согласование'),
            'approved':  ('Одобрена',         'Заявка #{pk} одобрена'),
            'rejected':  ('Отклонена',         'Заявка #{pk} отклонена'),
            'canceled':  ('Отменена',          'Заявка #{pk} отменена'),
            'completed': ('Завершена',         'Заявка #{pk} завершена'),
        }
        meta = STATUS_META.get(status)
        if not meta:
            return

        status_label, title_tpl = meta
        title = title_tpl.format(pk=booking.pk)
        body  = f'{booking.get_event_type_display()} · {booking.room} · {booking.event_date}'

        if status == 'pending':
            approvers = get_user_model().objects.filter(
                role='approver', is_active=True, is_blocked=False
            )
            for approver in approvers:
                cls._send(approver, Notification.Kind.BOOKING_STATUS, title, body, booking)
        else:
            cls._send(booking.initiator, Notification.Kind.BOOKING_STATUS, title, body, booking)

            approval = getattr(booking, 'approval', None)
            if approval and status == 'canceled':
                cls._send(
                    approval.approver,
                    Notification.Kind.BOOKING_STATUS,
                    f'Заявка #{booking.pk} отменена инициатором',
                    body,
                    booking,
                )

    @classmethod
    def comment_added(cls, comment):
        booking  = comment.booking
        approval = getattr(booking, 'approval', None)

        if comment.author == booking.initiator:
            if approval:
                recipient = approval.approver
            else:
                return
        else:
            recipient = booking.initiator

        cls._send(
            recipient,
            Notification.Kind.COMMENT_ADDED,
            f'Новый комментарий к заявке #{booking.pk}',
            comment.text[:120],
            booking,
        )