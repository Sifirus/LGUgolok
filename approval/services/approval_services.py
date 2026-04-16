from booking.models import Booking


class ApprovalEngine:
    @staticmethod
    def get_status(room, equipment, event_type, participants):
        pending_event_types = [
            Booking.EventType.STATE_EXAM,
            Booking.EventType.THESIS_DEFENSE,
            Booking.EventType.CONFERENCE
        ]

        if event_type in pending_event_types:
            return Booking.Status.CREATED

        if equipment and equipment.exists():
            return Booking.Status.CREATED

        if room.type in [room.RoomType.CONF, room.RoomType.LAB, room.RoomType.HALL]:
            return Booking.Status.CREATED

        MASS_THRESHOLD = 100
        if participants >= MASS_THRESHOLD:
            return Booking.Status.CREATED

        # Неэффективное использование вместимости:
        # если участников * 1.5 < вместимости — аудитория явно избыточна
        if room.capacity and participants * 1.5 < room.capacity:
            return Booking.Status.CREATED

        return Booking.Status.APPROVED

