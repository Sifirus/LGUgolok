import os
import json
import random
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LGUgolok.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from users.models import User

DEFAULT_PASSWORD = "password123"
HASHED_PASSWORD = make_password(DEFAULT_PASSWORD)

NUM_INITIATORS = 10
NUM_APPROVERS = 5
NUM_OPERATORS = 2
NUM_ROOMS = 15
NUM_EQUIPMENT = 40
TARGET_BOOKINGS_COUNT = 300

TODAY = date.today()

FIRST_NAMES = ["Александр", "Михаил", "Иван", "Дмитрий", "Сергей", "Алексей", "Елена", "Ольга", "Анна", "Татьяна"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Соколов", "Новиков",
              "Морозов"]
SECOND_NAMES = ["Александрович", "Иванович", "Дмитриевич", "Сергеевич", "Алексеевич", "Михайлович", "Владимирович"]
DEPARTMENTS = ["Кафедра ИТ", "Кафедра Физики", "Кафедра Высшей математики", "Деканат", "Лаборатория ИИ"]

ROOM_TYPES = ['lecture', 'seminar', 'lab', 'conference', 'hall']
BUILDINGS = ["Главный корпус (А)", "Лабораторный корпус (Б)", "IT-центр (В)"]

EQ_MODELS = {
    'projector': [("Epson EB-2250U", "Epson"), ("BenQ MH535", "BenQ")],
    'microphone': [("Shure SM58", "Shure"), ("Sennheiser EW 100", "Sennheiser")],
    'laptop': [("ThinkPad T14", "Lenovo"), ("Latitude 5520", "Dell")],
    'screen': [("Projecta Elpro", "Projecta")],
    'camera': [("Rally Bar", "Logitech")]
}

EVENT_TYPES = ['lecture', 'practice', 'state_exam', 'thesis_defense', 'scientific_seminar', 'conference']

TIME_SLOTS = [
    ("08:30:00", "10:00:00"),
    ("10:15:00", "11:45:00"),
    ("12:00:00", "13:30:00"),
    ("14:00:00", "15:30:00"),
    ("15:45:00", "17:15:00"),
    ("17:30:00", "19:00:00")
]
SLOT_WEIGHTS = [10, 25, 35, 35, 20, 10]

fixtures = []

users_initiators = []
users_approvers = []
user_id = 1


def create_user_fixture(uid, email, role, is_staff=False, is_superuser=False):
    fixtures.append({
        "model": "users.user",
        "pk": uid,
        "fields": {
            "password": HASHED_PASSWORD,
            "email": email,
            "role": role,
            "must_change_password": False,
            "is_blocked": False,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
            "is_active": True,
            "created_at": f"{TODAY - timedelta(days=30)}T09:00:00Z",
            "updated_at": f"{TODAY - timedelta(days=30)}T09:00:00Z"
        }
    })
    fixtures.append({
        "model": "users.profile",
        "pk": uid,
        "fields": {
            "user": uid,
            "first_name": random.choice(FIRST_NAMES),
            "second_name": random.choice(SECOND_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "department": random.choice(DEPARTMENTS),
            "avatar": None,
            "created_at": f"{TODAY - timedelta(days=30)}T09:00:00Z",
            "updated_at": f"{TODAY - timedelta(days=30)}T09:00:00Z"
        }
    })


for i in range(NUM_INITIATORS):
    create_user_fixture(user_id, f"initiator{i + 1}@univ.ru", User.Roles.INITIATOR)
    users_initiators.append(user_id)
    user_id += 1

for i in range(NUM_APPROVERS):
    create_user_fixture(user_id, f"approver{i + 1}@univ.ru", User.Roles.APPROVER, is_staff=True)
    users_approvers.append(user_id)
    user_id += 1

for i in range(NUM_OPERATORS):
    create_user_fixture(user_id, f"operator{i + 1}@univ.ru", User.Roles.OPERATOR, is_staff=True, is_superuser=True)
    user_id += 1

room_ids = []
for r in range(1, NUM_ROOMS + 1):
    r_type = ROOM_TYPES[r % len(ROOM_TYPES)]
    fixtures.append({
        "model": "rooms.room",
        "pk": r,
        "fields": {
            "name": f"Аудитория {100 + r}",
            "building": random.choice(BUILDINGS),
            "floor": (r % 3) + 1,
            "capacity": 30 if r_type in ['lab', 'seminar'] else 100,
            "status": "active",
            "type": r_type,
            "created_at": f"{TODAY - timedelta(days=30)}T09:00:00Z",
            "updated_at": f"{TODAY - timedelta(days=30)}T09:00:00Z"
        }
    })
    room_ids.append(r)

eq_ids = []
eq_types = list(EQ_MODELS.keys())
for e in range(1, NUM_EQUIPMENT + 1):
    eq_type = eq_types[e % len(eq_types)]
    model, name = random.choice(EQ_MODELS[eq_type])
    fixtures.append({
        "model": "equipment.equipment",
        "pk": e,
        "fields": {
            "inventory_number": f"EQ-{2000 + e}",
            "name": name,
            "model": model,
            "type": eq_type,
            "status": "active",
            "is_stationary": (e % 2 == 0),
            "room": random.choice(room_ids) if (e % 2 == 0) else None,
            "created_at": f"{TODAY - timedelta(days=30)}T09:00:00Z",
            "updated_at": f"{TODAY - timedelta(days=30)}T09:00:00Z"
        }
    })
    eq_ids.append(e)

group_ids = []
for g in range(1, 10):
    fixtures.append({
        "model": "booking.bookinggroup",
        "pk": g,
        "fields": {
            "initiator": random.choice(users_initiators),
            "title": f"Семестровый курс №{g}",
            "comment": "Регулярное проведение занятий",
            "date_from": str(TODAY - timedelta(days=10)),
            "date_to": str(TODAY + timedelta(days=10)),
            "created_at": f"{TODAY - timedelta(days=12)}T10:00:00Z",
            "updated_at": f"{TODAY - timedelta(days=12)}T10:00:00Z"
        }
    })
    group_ids.append(g)

booking_id = 1
approval_id = 1
comment_id = 1
notification_id = 1

occupied_slots = set()

available_dates = [TODAY + timedelta(days=offset) for offset in range(-14, 15)]

while booking_id <= TARGET_BOOKINGS_COUNT:
    event_date = random.choice(available_dates)
    event_date_str = str(event_date)
    room_id = random.choice(room_ids)

    slot_index = random.choices(range(len(TIME_SLOTS)), weights=SLOT_WEIGHTS)[0]
    slot_start, slot_end = TIME_SLOTS[slot_index]

    slot_key = (room_id, event_date_str, slot_index)
    if slot_key in occupied_slots:
        continue
    occupied_slots.add(slot_key)

    days_diff = (event_date - TODAY).days

    if days_diff <= -7:
        status = random.choices(['completed', 'approved', 'rejected', 'canceled'], weights=[50, 20, 20, 10])[0]
    elif days_diff < 0:
        status = random.choices(['approved', 'rejected', 'canceled'], weights=[50, 30, 20])[0]
    else:
        status = random.choices(['created', 'pending', 'approved', 'rejected'], weights=[30, 30, 30, 10])[0]

    initiator = random.choice(users_initiators)
    approver = random.choice(users_approvers)

    use_group = (random.random() < 0.25)
    group_fk = random.choice(group_ids) if use_group else None

    fixtures.append({
        "model": "booking.booking",
        "pk": booking_id,
        "fields": {
            "group": group_fk,
            "initiator": initiator,
            "room": room_id,
            "equipment": random.sample(eq_ids, k=random.randint(0, 2)),
            "event_type": random.choice(EVENT_TYPES),
            "event_date": event_date_str,
            "event_start_time": slot_start,
            "event_end_time": slot_end,
            "participants": random.randint(15, 60),
            "comment": "Необходим проектор и кликер.",
            "status": status,
            "created_at": f"{event_date_str}T08:00:00Z",
            "updated_at": f"{event_date_str}T08:30:00Z"
        }
    })

    if status in ['pending', 'approved', 'rejected', 'completed']:
        if status == 'pending':
            decision = 'in_process'
            decided_at = None
        elif status in ['approved', 'completed']:
            decision = 'approved'
            decided_at = f"{event_date_str}T08:30:00Z"
        else:
            decision = 'rejected'
            decided_at = f"{event_date_str}T08:30:00Z"

        fixtures.append({
            "model": "approval.approval",
            "pk": approval_id,
            "fields": {
                "booking": booking_id,
                "approver": approver,
                "decision": decision,
                "decided_at": decided_at,
                "created_at": f"{event_date_str}T08:05:00Z",
                "updated_at": f"{event_date_str}T08:30:00Z"
            }
        })
        approval_id += 1

    if status == 'rejected':
        fixtures.append({
            "model": "booking.comments",
            "pk": comment_id,
            "fields": {
                "text": "Аудитория зарезервирована под заседание кафедры.",
                "booking": booking_id,
                "author": approver,
                "created_at": f"{event_date_str}T08:25:00Z"
            }
        })
        comment_id += 1

    if status in ['approved', 'rejected']:
        fixtures.append({
            "model": "notifications.notification",
            "pk": notification_id,
            "fields": {
                "recipient": initiator,
                "kind": "booking_status",
                "title": "Изменение статуса",
                "body": f"Ваша заявка #{booking_id} переведена в статус {status}.",
                "booking": booking_id,
                "is_read": True,
                "created_at": f"{event_date_str}T08:31:00Z"
            }
        })
        notification_id += 1

    booking_id += 1

with open('initial_data.json', 'w', encoding='utf-8') as f:
    json.dump(fixtures, f, ensure_ascii=False, indent=2)

print(f"Успешно сформировано {len(fixtures)} объектов в initial_data.json")