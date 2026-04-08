from notifications.models import Notification


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

    # ── Статус заявки ─────────────────────────────────────

    @classmethod
    def booking_status_changed(cls, booking, old_status):
        """
        Один метод на все переходы статуса.
        Логика: кто получает и что написать — определяется здесь.
        """
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
            # Уведомляем всех согласующих
            from django.contrib.auth import get_user_model
            approvers = get_user_model().objects.filter(
                role='approver', is_active=True, is_blocked=False
            )
            for approver in approvers:
                cls._send(approver, Notification.Kind.BOOKING_STATUS, title, body, booking)
        else:
            # Уведомляем инициатора
            cls._send(booking.initiator, Notification.Kind.BOOKING_STATUS, title, body, booking)

            # Если есть согласующий и статус изменил инициатор — уведомить согласующего
            approval = getattr(booking, 'approval', None)
            if approval and status == 'canceled':
                cls._send(
                    approval.approver,
                    Notification.Kind.BOOKING_STATUS,
                    f'Заявка #{booking.pk} отменена инициатором',
                    body,
                    booking,
                )

    # ── Комментарий ───────────────────────────────────────

    @classmethod
    def comment_added(cls, comment):
        booking  = comment.booking
        approval = getattr(booking, 'approval', None)

        if comment.author == booking.initiator:
            # Пишет инициатор — уведомить согласующего
            if approval:
                recipient = approval.approver
            else:
                return
        else:
            # Пишет согласующий — уведомить инициатора
            recipient = booking.initiator

        cls._send(
            recipient,
            Notification.Kind.COMMENT_ADDED,
            f'Новый комментарий к заявке #{booking.pk}',
            comment.text[:120],
            booking,
        )