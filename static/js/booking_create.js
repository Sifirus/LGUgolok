const selectedEquipmentMeta = new Map();

function buildEquipmentSummary(eq) {
    const typeLabel = (eq.type_label || eq.type || '').trim();
    const name = (eq.name || '').trim();
    const model = (eq.model || '').trim();

    if (typeLabel) return typeLabel;
    if (name && model) return `${name} ${model}`;
    if (name) return name;
    if (model) return model;
    return `Оборудование ${eq.id}`;
}

function rememberEquipmentMeta(id, label) {
    const normalized = normalizeText(label);
    if (!normalized) return;
    selectedEquipmentMeta.set(id, {
        label: label.trim(),
        normalized
    });
}

function forgetEquipmentMeta(id) {
    selectedEquipmentMeta.delete(id);
}

function SelectedEquipmentFromField() {
    const select = document.getElementById('id_equipment');
    if (!select) return;

    [...select.options].forEach(opt => {
        const id = parseInt(opt.value, 10);
        if (!Number.isNaN(id) && opt.selected) {
            const label = (opt.dataset.summary || opt.textContent || opt.label || '').trim();
            if (label) rememberEquipmentMeta(id, label);
        }
    });
}

function getSelectedEquipmentIds() {
    const ids = new Set();

    document.querySelectorAll('input[name="equipment"]').forEach(i => {
        const n = parseInt(i.value, 10);
        if (!Number.isNaN(n)) ids.add(n);
    });

    const select = document.getElementById('id_equipment');
    if (select) {
        [...select.options].forEach(opt => {
            if (opt.selected) {
                const n = parseInt(opt.value, 10);
                if (!Number.isNaN(n)) ids.add(n);
            }
        });
    }

    return ids;
}

function getEquipmentSummaryText() {
    const labels = [];
    const ids = getSelectedEquipmentIds();

    ids.forEach(id => {
        const meta = selectedEquipmentMeta.get(id);
        if (meta?.label) labels.push(meta.label);
    });

    if (labels.length === 0) return '-';

    const counts = new Map();
    labels.forEach(label => {
        const key = normalizeText(label);
        const current = counts.get(key);
        if (current) {
            current.count += 1;
        } else {
            counts.set(key, {label, count: 1});
        }
    });

    const parts = [...counts.values()].map(item => item.count > 1 ? `${item.label} ×${item.count}` : item.label);
    if (parts.length <= 2) return parts.join(', ');
    return `${parts.slice(0, 2).join(', ')} и ещё ${parts.length - 2}`;
}

function updateSummary() {
    const eventType = document.getElementById('id_event_type');
    const participants = document.getElementById('id_participants');
    const eventDate = document.getElementById('id_event_date');
    const startTime = document.getElementById('id_event_start_time');
    const endTime = document.getElementById('id_event_end_time');

    const sumType = document.getElementById('sum-type');
    const sumDate = document.getElementById('sum-date');
    const sumTime = document.getElementById('sum-time');
    const sumParticipants = document.getElementById('sum-participants');
    const sumRoom = document.getElementById('sum-room');
    const sumEquipment = document.getElementById('sum-equipment');

    if (sumType && eventType) {
        sumType.textContent = eventType.options[eventType.selectedIndex]?.text || '-';
    }

    if (sumDate && eventDate) {
        sumDate.textContent = formatDate(eventDate.value);
    }

    if (sumTime && startTime && endTime) {
        const start = startTime.value || '-';
        const end = endTime.value || '-';
        sumTime.textContent = `${start} - ${end}`;
    }

    if (sumParticipants && participants) {
        sumParticipants.textContent = participants.value ? `${participants.value} чел.` : '-';
    }

    const selectedRoomEl = document.querySelector('.room-card-sel.selected .room-name');
    if (sumRoom) {
        sumRoom.textContent = selectedRoomEl ? selectedRoomEl.textContent : '-';
    }

    if (sumEquipment) {
        const text = getEquipmentSummaryText();
        sumEquipment.textContent = text;
        sumEquipment.title = text;
    }
}

function selectRoom(card) {
    document.querySelectorAll('.room-card-sel').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');

    const roomInput = document.getElementById('id_room');
    if (roomInput) roomInput.value = card.dataset.id;

    updateSummary();
}

function setEquipmentSelected(id, selected) {
    const existing = document.querySelector(`input[name="equipment"][value="${id}"]`);
    if (selected) {
        if (!existing) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'equipment';
            input.value = id;
            document.getElementById('booking-form').appendChild(input);
        }
    } else if (existing) {
        existing.remove();
    }
}

async function loadRooms(btn) {
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Загрузка...';
    }

    const listEl = document.getElementById('rooms-list');

    try {
        const params = new URLSearchParams({
            is_available: true,
            event_date: document.getElementById('id_event_date').value,
            event_start_time: document.getElementById('id_event_start_time').value,
            event_end_time: document.getElementById('id_event_end_time').value,
            capacity: document.getElementById('id_participants').value,
            type: document.getElementById('id_type').value,
            search_query: document.getElementById('id_room_search_query').value
        });

        for (const [key, value] of [...params]) {
            if (!value) params.delete(key);
        }

        const response = await fetch(`/api/rooms?${params}`);
        const data = await response.json();

        if (response.ok) {
            renderRooms(data);
        } else {
            const message = data['non_field_errors']?.[0] ?? 'Произошла ошибка, попробуйте снова';
            listEl.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        }
    } catch {
        listEl.innerHTML = '<div class="alert alert-danger">Произошла ошибка, попробуйте снова</div>';
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Подобрать';
        }
    }

    updateSummary();
}

function renderRooms(data) {
    const roomsList = document.getElementById('rooms-list');

    if (!Array.isArray(data) || data.length === 0) {
        roomsList.innerHTML = '<div class="text-muted">Ничего не найдено</div>';
        return;
    }

    const selectedId = parseInt(document.getElementById('id_room').value, 10);

    data.sort((a, b) => {
        if (a.id === selectedId) return -1;
        if (b.id === selectedId) return 1;
        return 0;
    });

    roomsList.innerHTML = data.map(room => {
        const isSelected = room.id === selectedId;
        const typeLabel = room.type_label || room.type || '';

        return `
<div class="room-card-sel ${isSelected ? 'selected' : ''}"
     data-id="${room.id}"
     onclick="selectRoom(this)">
    <div class="room-sel-radio"><i class="bi bi-check-lg" style="font-size:11px"></i></div>
    <div class="room-info">
        <div class="room-name">${room.name}</div>
        <div class="room-meta">
            ${room.capacity !== undefined && room.capacity !== null ? `<span><i class="bi bi-people"></i> до ${room.capacity} чел.</span>` : ''}
            ${typeLabel ? `<span><i class="bi bi-tag"></i> ${typeLabel}</span>` : ''}
        </div>
    </div>
</div>
`;
    }).join('');
}

let equipmentDebounceTimer;

function debounceEquipmentSearch() {
    clearTimeout(equipmentDebounceTimer);
    equipmentDebounceTimer = setTimeout(loadEquipment, 300);
}

async function loadEquipment() {
    const listEl = document.getElementById('equipment-list');
    listEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Загрузка...';

    if (document.getElementById('id_equipment_search_query').value) {
        try {
            const params = new URLSearchParams({
                is_available: true,
                event_date: document.getElementById('id_event_date').value,
                event_start_time: document.getElementById('id_event_start_time').value,
                event_end_time: document.getElementById('id_event_end_time').value,
                search_query: document.getElementById('id_equipment_search_query').value
            });

            for (const [key, value] of [...params]) {
                if (!value) params.delete(key);
            }

            const response = await fetch(`/api/equipment?${params}`);
            const data = await response.json();

            if (response.ok) {
                renderEquipment(data);
            } else {
                const message = data['non_field_errors']?.[0] ?? 'Произошла ошибка при поиске';
                listEl.innerHTML = `<div class="alert alert-danger">${message}</div>`;
            }
        } catch {
            listEl.innerHTML = '<div class="alert alert-danger">Произошла ошибка при поиске</div>';
        }

        updateSummary();
    } else {
        listEl.innerHTML = '<span class="text-muted">Начните вводить</span>';
    }
}

function renderEquipment(data) {
    const listEl = document.getElementById('equipment-list');

    if (!Array.isArray(data) || data.length === 0) {
        listEl.innerHTML = '<div class="text-muted">Ничего не найдено</div>';
        return;
    }

    const selectedIds = getSelectedEquipmentIds();

    data.sort((a, b) => {
        const aSelected = selectedIds.has(a.id);
        const bSelected = selectedIds.has(b.id);
        if (aSelected && !bSelected) return -1;
        if (!aSelected && bSelected) return 1;
        return 0;
    });

    listEl.innerHTML = data.map(eq => {
        const isSelected = selectedIds.has(eq.id);
        const label = buildEquipmentSummary(eq);
        const typeLabel = eq.type_label || eq.type || '';

        if (isSelected) {
            rememberEquipmentMeta(eq.id, label);
        }

        return `
<div class="eq-row equipment-card ${isSelected ? 'selected' : ''}"
     data-id="${eq.id}"
     data-summary="${label}"
     data-title="${eq.name || ''}"
     onclick="selectEquipment(${eq.id})"
     style="cursor:pointer">
    <input type="checkbox" class="eq-chk" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); selectEquipment(${eq.id})">
    <div class="eq-icon"><i class="bi bi-laptop"></i></div>
    <div style="flex:1;min-width:0">
        <div class="eq-name">${eq.name || ''}${eq.model ? ' - ' + eq.model : ''}</div>
        <div class="eq-loc">
            ${typeLabel ? `<span class="eq-inv">${typeLabel}</span>` : ''}
            ${eq.inventory_number ? `<span class="eq-inv">${eq.inventory_number}</span>` : ''}
        </div>
    </div>
</div>
`;
    }).join('');
}

function selectEquipment(id) {
    const card = document.querySelector(`.equipment-card[data-id="${id}"]`);
    const checkbox = card ? card.querySelector('.eq-chk') : null;
    const existing = document.querySelector(`input[name="equipment"][value="${id}"]`);

    if (existing) {
        existing.remove();
        forgetEquipmentMeta(id);
        if (card) card.classList.remove('selected');
        if (checkbox) checkbox.checked = false;
    } else {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'equipment';
        input.value = id;
        document.getElementById('booking-form').appendChild(input);

        if (card) card.classList.add('selected');
        if (checkbox) checkbox.checked = true;

        const summary = card?.dataset.summary || card?.dataset.title || '';
        if (summary) {
            rememberEquipmentMeta(id, summary);
        }
    }

    updateSummary();
}

function syncSelectedEquipmentFromForm() {
    const ids = getSelectedEquipmentIds();
    ids.forEach(id => {
        const card = document.querySelector(`.equipment-card[data-id="${id}"]`);
        if (card) {
            const summary = card.dataset.summary || card.dataset.title || '';
            if (summary) rememberEquipmentMeta(id, summary);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const eventType = document.getElementById('id_event_type');
    const participants = document.getElementById('id_participants');
    const eventDate = document.getElementById('id_event_date');
    const startTime = document.getElementById('id_event_start_time');
    const endTime = document.getElementById('id_event_end_time');

    [eventType, participants, eventDate, startTime, endTime].forEach(el => {
        if (el) {
            el.addEventListener('change', updateSummary);
            el.addEventListener('input', updateSummary);
        }
    });

    SelectedEquipmentFromField();
    syncSelectedEquipmentFromForm();

    const roomId = document.getElementById('id_room').value;
    if (roomId) loadRooms();

    const selectedEquipmentIds = getSelectedEquipmentIds();
    if (selectedEquipmentIds.size > 0) loadEquipment();

    updateSummary();
});