from booking.models import Booking

class ApprovalEngine:
    @staticmethod
    def get_status(room, equipment, event_type, participants):
        # Список типов событий, требующих согласования
        pending_event_types = [
            Booking.EventType.STATE_EXAM,
            Booking.EventType.THESIS_DEFENSE,
            Booking.EventType.CONFERENCE
        ]

        # Критические события
        if event_type in pending_event_types:
            return Booking.Status.CREATED

        # Если выбрано оборудование
        if equipment and equipment.exists():
            return Booking.Status.CREATED

        # Особые аудитории
        if room.type in [room.RoomType.CONF, room.RoomType.LAB, room.RoomType.HALL]:
            return Booking.Status.CREATED

        # Массовые мероприятия
        MASS_THRESHOLD = 100
        if participants >= MASS_THRESHOLD:
            return Booking.Status.CREATED

        return Booking.Status.APPROVED