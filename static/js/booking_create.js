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

    const participants = parseInt(document.getElementById('id_participants')?.value || '0', 10);

    data.sort((a, b) => {
        // Выбранная аудитория всегда первая
        if (a.id === selectedId) return -1;
        if (b.id === selectedId) return 1;
        // Затем сортировка по ближайшей вместимости к числу участников
        if (participants > 0 && a.capacity != null && b.capacity != null) {
            return Math.abs(a.capacity - participants) - Math.abs(b.capacity - participants);
        }
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
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="room-name">${room.name}</div>
            <button type="button" class="btn-sec" 
                    onclick="event.stopPropagation(); showRoomInfo(${room.id})" 
                    style="padding: 2px 8px; font-size: 11px; min-width: auto;" 
                    title="Подробнее об аудитории">
                <i class="bi bi-info-circle"></i>
            </button>
        </div>
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
        <div style="display: flex; align-items: center; gap: 8px;">
            <span class="eq-name">${eq.name || ''}${eq.model ? ' - ' + eq.model : ''}</span>
            <button type="button" class="btn-sec" 
                    onclick="event.stopPropagation(); showEquipmentInfo(${eq.id})" 
                    style="padding: 2px 6px; font-size: 10px; min-width: auto;" 
                    title="Подробнее об оборудовании">
                <i class="bi bi-info-circle"></i>
            </button>
        </div>
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

// Вспомогательные функции для экранирования
function escH(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Показать информацию об аудитории
async function showRoomInfo(roomId) {
    const modal = document.getElementById('infoModal');
    const title = document.getElementById('infoModalTitle');
    const subtitle = document.getElementById('infoModalSubtitle');
    const body = document.getElementById('infoModalBody');
    const link = document.getElementById('infoModalLink');

    if (!modal) return;

    openModal('infoModal');
    title.textContent = 'Информация об аудитории';
    subtitle.textContent = `ID: ${roomId}`;
    body.innerHTML = `
        <div style="padding: 20px; text-align: center; color: var(--muted);">
            <div class="spinner-border" style="margin-bottom: 12px;"></div>
            <div>Загрузка данных...</div>
        </div>
    `;
    link.style.display = 'none';

    try {
        const resp = await fetch(`/api/room/${roomId}/`);
        const data = await resp.json();

        if (resp.ok) {
            body.innerHTML = `
                <div class="info-detail-grid">
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-door-open" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Название</div>
                            <div class="info-detail-value">${escH(data.name)}</div>
                        </div>
                    </div>
                    
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-geo-alt" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Расположение</div>
                            <div class="info-detail-value">${escH(data.building)}, ${data.floor} этаж</div>
                        </div>
                    </div>
                    
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-people" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Вместимость</div>
                            <div class="info-detail-value">${data.capacity} человек</div>
                        </div>
                    </div>
                    
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-tag" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Характеристики</div>
                            <div class="info-detail-value">
                                <span class="info-badge"><i class="bi bi-building"></i> ${escH(data.type)}</span>
                                <span class="info-badge"><i class="bi bi-circle-fill" style="font-size: 8px; color: ${data.status === 'Активна' ? 'var(--success)' : 'var(--warning)'};"></i> ${escH(data.status)}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${data.equipment && data.equipment.length > 0 ? `
                        <div style="margin-top: 8px;">
                            <div class="info-section-title">
                                <i class="bi bi-laptop"></i>
                                Стационарное оборудование
                                <span style="font-size: 11px; font-weight: 400; color: var(--muted); margin-left: auto;">${data.equipment.length} ед.</span>
                            </div>
                            <div class="info-equipment-list">
                                ${data.equipment.map(eq => `
                                    <span class="info-equipment-tag" onclick="showEquipmentInfo(${eq.id})" title="Нажмите для подробностей">
                                        <i class="bi bi-laptop"></i>
                                        ${escH(eq.name)}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    ` : `
                        <div class="info-detail-row">
                            <div class="info-detail-icon">
                                <i class="bi bi-laptop" style="font-size: 16px;"></i>
                            </div>
                            <div class="info-detail-content">
                                <div class="info-detail-label">Оборудование</div>
                                <div class="info-detail-value" style="color: var(--muted);">Отсутствует</div>
                            </div>
                        </div>
                    `}
                </div>
            `;

            link.href = `/rooms/${roomId}/`;
            link.style.display = 'inline-flex';
        } else {
            body.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <i class="bi bi-exclamation-triangle" style="font-size: 32px; color: var(--danger); margin-bottom: 12px;"></i>
                    <div style="color: var(--danger);">${escH(data.detail || 'Ошибка загрузки данных')}</div>
                </div>
            `;
        }
    } catch (e) {
        body.innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <i class="bi bi-wifi-off" style="font-size: 32px; color: var(--muted); margin-bottom: 12px;"></i>
                <div style="color: var(--muted);">Ошибка соединения с сервером</div>
            </div>
        `;
    }
}

// Показать информацию об оборудовании
async function showEquipmentInfo(equipId) {
    const modal = document.getElementById('infoModal');
    const title = document.getElementById('infoModalTitle');
    const subtitle = document.getElementById('infoModalSubtitle');
    const body = document.getElementById('infoModalBody');
    const link = document.getElementById('infoModalLink');

    if (!modal) return;

    openModal('infoModal');
    title.textContent = 'Информация об оборудовании';
    subtitle.textContent = `ID: ${equipId}`;
    body.innerHTML = `
        <div style="padding: 20px; text-align: center; color: var(--muted);">
            <div class="spinner-border" style="margin-bottom: 12px;"></div>
            <div>Загрузка данных...</div>
        </div>
    `;
    link.style.display = 'none';

    try {
        const resp = await fetch(`/api/equipment/${equipId}/`);
        const data = await resp.json();

        if (resp.ok) {
            const statusColor = data.status === 'Активно' ? 'var(--success)' :
                               data.status === 'На обслуживании' ? 'var(--warning)' : 'var(--danger)';

            body.innerHTML = `
                <div class="info-detail-grid">
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-upc-scan" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Инвентарный номер</div>
                            <div class="info-detail-value" style="font-family: monospace;">${escH(data.inventory_number)}</div>
                        </div>
                    </div>
                    
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-laptop" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Название</div>
                            <div class="info-detail-value">${escH(data.name)}</div>
                            ${data.model ? `<div class="info-detail-sub">Модель: ${escH(data.model)}</div>` : ''}
                        </div>
                    </div>
                    
                    <div class="info-detail-row">
                        <div class="info-detail-icon">
                            <i class="bi bi-tags" style="font-size: 16px;"></i>
                        </div>
                        <div class="info-detail-content">
                            <div class="info-detail-label">Характеристики</div>
                            <div class="info-detail-value">
                                <span class="info-badge"><i class="bi bi-diagram-3"></i> ${escH(data.type)}</span>
                                <span class="info-badge"><i class="bi bi-circle-fill" style="font-size: 8px; color: ${statusColor};"></i> ${escH(data.status)}</span>
                                <span class="info-badge"><i class="bi bi-pin${data.is_stationary ? '-fill' : ''}"></i> ${data.is_stationary ? 'Стационарное' : 'Переносное'}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${data.room_name ? `
                        <div class="info-detail-row">
                            <div class="info-detail-icon">
                                <i class="bi bi-geo-alt" style="font-size: 16px;"></i>
                            </div>
                            <div class="info-detail-content">
                                <div class="info-detail-label">Расположение</div>
                                <div class="info-detail-value">
                                    <a href="#" onclick="showRoomInfo(${data.room_id}); return false;" style="color: var(--blue); text-decoration: none;">
                                        ${escH(data.room_name)}
                                        <i class="bi bi-box-arrow-up-right" style="font-size: 11px; margin-left: 4px;"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    ` : `
                        <div class="info-detail-row">
                            <div class="info-detail-icon">
                                <i class="bi bi-box" style="font-size: 16px;"></i>
                            </div>
                            <div class="info-detail-content">
                                <div class="info-detail-label">Расположение</div>
                                <div class="info-detail-value" style="color: var(--muted);">На складе</div>
                            </div>
                        </div>
                    `}
                </div>
            `;

            link.href = `/equipment/${equipId}/`;
            link.style.display = 'inline-flex';
        } else {
            body.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <i class="bi bi-exclamation-triangle" style="font-size: 32px; color: var(--danger); margin-bottom: 12px;"></i>
                    <div style="color: var(--danger);">${escH(data.detail || 'Ошибка загрузки данных')}</div>
                </div>
            `;
        }
    } catch (e) {
        body.innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <i class="bi bi-wifi-off" style="font-size: 32px; color: var(--muted); margin-bottom: 12px;"></i>
                <div style="color: var(--muted);">Ошибка соединения с сервером</div>
            </div>
        `;
    }
}