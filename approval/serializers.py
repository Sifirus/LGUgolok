from rest_framework import serializers

from booking.models import Booking


class EquipmentBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return str(obj)


class BookingApprovalDetailItemSerializer(serializers.ModelSerializer):
    initiator_first_name = serializers.CharField(source='initiator.profile.first_name', read_only=True)
    initiator_last_name = serializers.CharField(source='initiator.profile.last_name', read_only=True)
    department = serializers.CharField(source='initiator.profile.department', read_only=True)
    event_type = serializers.CharField(source='get_event_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_building = serializers.CharField(source='room.building', read_only=True)
    room_floor = serializers.CharField(source='room.floor', read_only=True)
    room_capacity = serializers.IntegerField(source='room.capacity', read_only=True)

    equipment_list = EquipmentBriefSerializer(many=True, source='equipment', read_only=True)

    approval_decision = serializers.SerializerMethodField()
    approval_decided_at = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'room_id',
            'initiator_first_name',
            'initiator_last_name',
            'department',
            'event_type',
            'event_date',
            'event_start_time',
            'event_end_time',
            'room_name',
            'room_building',
            'room_floor',
            'room_capacity',
            'participants',
            'equipment_list',
            'comment',
            'status',
            'status_display',
            'approval_decision',
            'approval_decided_at',
            'created_at',
        ]

    def get_approval_decision(self, obj):
        approval = getattr(obj, 'approval', None)
        return approval.decision if approval else None

    def get_approval_decided_at(self, obj):
        approval = getattr(obj, 'approval', None)
        return approval.decided_at if approval else None


class BookingApprovalDetailSerializer(serializers.ModelSerializer):
    initiator_first_name = serializers.CharField(source='initiator.profile.first_name', read_only=True)
    initiator_last_name = serializers.CharField(source='initiator.profile.last_name', read_only=True)
    department = serializers.CharField(source='initiator.profile.department', read_only=True)
    event_type = serializers.CharField(source='get_event_type_display', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    room_building = serializers.CharField(source='room.building', read_only=True)
    room_floor = serializers.CharField(source='room.floor', read_only=True)
    room_capacity = serializers.IntegerField(source='room.capacity', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    equipment_list = EquipmentBriefSerializer(many=True, source='equipment', read_only=True)

    scope = serializers.SerializerMethodField()
    group_id = serializers.SerializerMethodField()
    group_title = serializers.SerializerMethodField()
    group_comment = serializers.SerializerMethodField()
    group_date_from = serializers.SerializerMethodField()
    group_date_to = serializers.SerializerMethodField()
    group_total_count = serializers.SerializerMethodField()
    group_pending_count = serializers.SerializerMethodField()
    group_bookings = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'room_id',
            'scope',
            'initiator_first_name',
            'initiator_last_name',
            'department',
            'event_type',
            'event_date',
            'event_start_time',
            'event_end_time',
            'room_name',
            'room_building',
            'room_floor',
            'room_capacity',
            'participants',
            'equipment_list',
            'comment',
            'status',
            'status_display',
            'created_at',
            'group_id',
            'group_title',
            'group_comment',
            'group_date_from',
            'group_date_to',
            'group_total_count',
            'group_pending_count',
            'group_bookings',
        ]

    def get_scope(self, obj):
        return 'group' if obj.group_id else 'booking'

    def get_group_id(self, obj):
        return obj.group_id

    def get_group_title(self, obj):
        return obj.group.title if obj.group_id else None

    def get_group_comment(self, obj):
        return obj.group.comment if obj.group_id else None

    def get_group_date_from(self, obj):
        return obj.group.date_from if obj.group_id else None

    def get_group_date_to(self, obj):
        return obj.group.date_to if obj.group_id else None

    def get_group_total_count(self, obj):
        return self.context.get('group_total_count', 1 if not obj.group_id else obj.group.total_count)

    def get_group_pending_count(self, obj):
        return self.context.get('group_pending_count', 1 if not obj.group_id else obj.group.approval_required_count)

    def get_group_bookings(self, obj):
        bookings = self.context.get('group_bookings')
        if bookings is None:
            bookings = [obj]
        return BookingApprovalDetailItemSerializer(bookings, many=True, context=self.context).data
