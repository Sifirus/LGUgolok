from django.db.models import Q


class BookingAccessService:
    @staticmethod
    def visible_queryset(user, queryset):
        role = getattr(user, 'role', None)
        if role == 'initiator':
            return queryset.filter(initiator=user)
        return queryset


class BookingFiltersService:
    @staticmethod
    def apply_filters(queryset, data):
        search_query = (data.get('search') or '').strip()
        if search_query:
            for word in search_query.split():
                q = (
                    Q(comment__icontains=word) |
                    Q(initiator__email__icontains=word) |
                    Q(initiator__profile__first_name__icontains=word) |
                    Q(initiator__profile__second_name__icontains=word) |
                    Q(initiator__profile__last_name__icontains=word) |
                    Q(room__name__icontains=word) |
                    Q(room__building__icontains=word) |
                    Q(room__floor__icontains=word) |
                    Q(equipment__name__icontains=word) |
                    Q(equipment__model__icontains=word) |
                    Q(equipment__inventory_number__icontains=word) |
                    Q(approval__approver__email__icontains=word) |
                    Q(approval__approver__profile__first_name__icontains=word) |
                    Q(approval__approver__profile__second_name__icontains=word) |
                    Q(approval__approver__profile__last_name__icontains=word)
                )

                if word.isdigit():
                    num = int(word)
                    q |= (
                        Q(id=num) |
                        Q(room_id=num) |
                        Q(participants=num) |
                        Q(initiator__profile__id=num) |
                        Q(approval__approver__id=num) |
                        Q(approval__approver__profile__id=num)
                    )

                queryset = queryset.filter(q)

        if data.get('event_type'):
            queryset = queryset.filter(event_type=data['event_type'])

        if data.get('status'):
            queryset = queryset.filter(status=data['status'])

        if data.get('date_from'):
            queryset = queryset.filter(event_date__gte=data['date_from'])

        if data.get('date_to'):
            queryset = queryset.filter(event_date__lte=data['date_to'])

        if data.get('room_id'):
            queryset = queryset.filter(room_id=data['room_id'])

        if data.get('approver_id'):
            queryset = queryset.filter(approval__approver_id=data['approver_id'])

        if data.get('approval_decision'):
            queryset = queryset.filter(approval__decision=data['approval_decision'])

        return queryset.distinct()