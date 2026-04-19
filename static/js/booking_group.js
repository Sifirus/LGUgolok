'use strict';

const GS = {
    dateFrom: null,
    dateTo: null,
    slots: [],

    roomsMatrix: [],
    equipMatrix: [],

    primaryRoomId: null,
    conflictOverrides: {},
    roomTypeFilter: '',

    calYear: null,
    calMonth: null,

    equipmentCache: new Map(),
    equipmentModal: {
        slotIndex: null,
        items: [],
        tempSelection: new Set()
    },

    globalEquipment: new Set(),
    _equipSearchQuery: ''
};

function getDefaults() {
    return {
        start: document.getElementById('def-start')?.value || '08:00',
        end: document.getElementById('def-end')?.value || '09:30',
        eventType: document.getElementById('def-type')?.value || 'lecture',
        participants: parseInt(document.getElementById('def-participants')?.value || '60', 10),
        comment: document.getElementById('def-comment')?.value || '',
    };
}

function buildEquipmentSummary(eq) {
    const typeLabel = String(eq.type_label || eq.type || '').trim();
    const name = String(eq.name || '').trim();
    const model = String(eq.model || '').trim();

    if (typeLabel) return typeLabel;
    if (name && model) return `${name} ${model}`;
    if (name) return name;
    if (model) return model;
    return `Оборудование ${eq.id}`;
}

function rememberEquipmentFromItem(eq) {
    if (!eq || eq.id == null) return;
    GS.equipmentCache.set(eq.id, {
        id: eq.id,
        name: eq.name || '',
        model: eq.model || '',
        type: eq.type || '',
        type_label: eq.type_label || eq.type || '',
        inventory_number: eq.inventory_number || '',
    });
}

function getEquipmentLabelById(id) {
    const meta = GS.equipmentCache.get(id);
    if (meta) return buildEquipmentSummary(meta);
    return `#${id}`;
}

function getEquipmentSummaryText(slot) {
    if (!slot || !Array.isArray(slot.equipmentIds) || slot.equipmentIds.length === 0) {
        return 'Оборудование не выбрано';
    }

    const labels = slot.equipmentIds.map(getEquipmentLabelById);
    if (labels.length <= 2) return labels.join(', ');
    return `${labels.slice(0, 2).join(', ')} и ещё ${labels.length - 2}`;
}

function getEventTypeOptions() {
    return window.__EVENT_TYPES__ || [];
}

function escH(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function toISO(d) {
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function formatDateRu(iso) {
    if (!iso) return '-';
    const [y, m, d] = iso.split('-');
    const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
    return `${parseInt(d, 10)} ${months[parseInt(m, 10) - 1]}`;
}

function fmtShort(iso) {
    const [y, m, d] = iso.split('-');
    return `${d}.${m}`;
}

function getRoomLabel(roomId) {
    if (!roomId) return null;
    const r = GS.roomsMatrix.find(x => x.id === roomId);
    return r ? `${r.name} · ${r.building}` : null;
}

function resetRooms() {
    GS.roomsMatrix = [];
    GS.equipMatrix = [];
    GS.primaryRoomId = null;
    GS.conflictOverrides = {};
    GS.globalEquipment.clear();
    GS._equipSearchQuery = '';

    GS.slots.forEach(s => {
        s.equipmentIds = [];
        s._individualEquipment = [];
    });

    document.getElementById('bg-rooms-section')?.classList.remove('visible');
    document.getElementById('bg-equip-section')?.classList.remove('visible');
    document.getElementById('bg-submit-section')?.classList.remove('visible');
    document.getElementById('bg-conflict-wrap')?.replaceChildren();

    const eqCount = document.getElementById('bg-eq-count');
    if (eqCount) eqCount.textContent = '';
}

function renderCal() {
    const grid = document.getElementById('bg-cal-cells');
    const title = document.getElementById('bg-cal-month');
    if (!grid || !title) return;

    const MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    title.textContent = MONTHS[GS.calMonth] + ' ' + GS.calYear;

    const first = new Date(GS.calYear, GS.calMonth, 1);
    const last = new Date(GS.calYear, GS.calMonth + 1, 0);

    const dfFrom = GS.dateFrom ? new Date(GS.dateFrom) : null;
    const dfTo = GS.dateTo ? new Date(GS.dateTo) : null;

    let dow = first.getDay();
    if (dow === 0) dow = 7;

    let html = '';
    for (let i = 1; i < dow; i++) {
        html += '<div class="bg-cal-cell bg-cal-out"></div>';
    }

    for (let d = 1; d <= last.getDate(); d++) {
        const dt = new Date(GS.calYear, GS.calMonth, d);
        const iso = toISO(dt);
        let cls = 'bg-cal-cell';
        let disabled = false;

        if (!GS.dateFrom) {
            cls += ' bg-cal-dis';
            disabled = true;
        } else {
            const currentDateStr = iso;
            const fromDateStr = GS.dateFrom;
            const toDateStr = GS.dateTo;

            if (fromDateStr && currentDateStr < fromDateStr) {
                cls += ' bg-cal-dis';
                disabled = true;
            } else if (toDateStr && currentDateStr > toDateStr) {
                cls += ' bg-cal-dis';
                disabled = true;
            }
        }

        if (!disabled && GS.slots.some(s => s.date === iso)) cls += ' sel';

        html += `<div class="${cls}" data-date="${iso}">${d}</div>`;
    }

    grid.innerHTML = html;

    grid.querySelectorAll('.bg-cal-cell:not(.bg-cal-out):not(.bg-cal-dis)')
        .forEach(el => el.addEventListener('click', () => toggleDay(el.dataset.date)));
}

function initCal() {
    const today = new Date();
    GS.calYear = today.getFullYear();
    GS.calMonth = today.getMonth();
    renderCal();
}

window.calPrev = function() {
    if (GS.calMonth === 0) {
        GS.calMonth = 11;
        GS.calYear--;
    } else {
        GS.calMonth--;
    }
    renderCal();
};

window.calNext = function() {
    if (GS.calMonth === 11) {
        GS.calMonth = 0;
        GS.calYear++;
    } else {
        GS.calMonth++;
    }
    renderCal();
};

function toggleDay(iso) {
    const idx = GS.slots.findIndex(s => s.date === iso);
    if (idx !== -1) {
        GS.slots.splice(idx, 1);
    } else {
        const d = getDefaults();
        GS.slots.push({
            date: iso,
            start: d.start,
            end: d.end,
            eventType: d.eventType,
            participants: d.participants,
            comment: d.comment,
            equipmentIds: [],
            _individualEquipment: [],
            roomId: null,
        });
        GS.slots.sort((a, b) => a.date.localeCompare(b.date));
    }
    renderCal();
    renderSlots();
    resetRooms();
}

function renderSlots() {
    const container = document.getElementById('bg-slots');
    if (!container) return;

    const cnt = document.getElementById('bg-slots-count');
    if (cnt) cnt.textContent = GS.slots.length + ' дн.';

    if (GS.slots.length === 0) {
        container.innerHTML = `
<div class="bg-slots-empty">
  <i class="bi bi-calendar3"></i>
  <div>Выберите дни на календаре слева</div>
</div>`;
        return;
    }

    const eventOptions = getEventTypeOptions();

    container.innerHTML = GS.slots.map((slot, i) => {
        const dt = new Date(slot.date);
        const dow = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'][dt.getDay()];
        const roomLabel = getRoomLabel(slot.roomId);
        const eqText = getEquipmentSummaryText(slot);

        return `
<div class="bg-slot-card" id="slot-card-${i}">
  <div class="bg-slot-main">
    <div>
      <div class="bg-slot-date-lbl">${formatDateRu(slot.date)}</div>
      <div class="bg-slot-date-dow">${dow}</div>
    </div>

    <input type="time" class="bg-slot-fc" value="${slot.start}"
           onchange="updateSlotField(${i},'start',this.value)">

    <input type="time" class="bg-slot-fc" value="${slot.end}"
           onchange="updateSlotField(${i},'end',this.value)">

    <select class="bg-slot-fc" onchange="updateSlotField(${i},'eventType',this.value)">
      ${eventOptions.map(([v, l]) =>
          `<option value="${v}" ${slot.eventType === v ? 'selected' : ''}>${l}</option>`
      ).join('')}
    </select>

    <input type="number" class="bg-slot-fc" min="1" value="${slot.participants}"
           style="width:64px" onchange="updateSlotField(${i},'participants',+this.value)">

    <button class="bg-slot-eq-btn ${slot.equipmentIds.length ? 'has-eq' : ''}"
            title="Оборудование на этот день"
            onclick="openEquipmentModal(${i})">
      <i class="bi bi-laptop"></i>
      ${slot.equipmentIds.length ? `<span style="position:absolute;top:-4px;right:-4px;width:14px;height:14px;background:var(--orange);border-radius:50%;font-size:9px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700">${slot.equipmentIds.length}</span>` : ''}
    </button>

    <button class="bg-slot-rm-btn" title="Удалить" onclick="removeSlot(${i})">
      <i class="bi bi-x"></i>
    </button>
  </div>

  ${roomLabel ? `<div class="bg-slot-line"><i class="bi bi-building"></i> ${escH(roomLabel)}</div>` : ''}
  <div class="bg-slot-line">
    <i class="bi bi-laptop"></i>
    <button type="button" class="bg-slot-link" onclick="openEquipmentModal(${i})">
      ${escH(eqText)}
    </button>
  </div>

  <div class="bg-slot-comment">
    <textarea class="bg-slot-fc" rows="2"
              placeholder="Комментарий к этому дню"
              onchange="updateSlotField(${i},'comment',this.value)">${escH(slot.comment || '')}</textarea>
  </div>
</div>`;
    }).join('');
}

window.updateSlotField = function(i, field, value) {
    const slot = GS.slots[i];
    if (!slot) return;

    if (field === 'participants') {
        slot[field] = Math.max(1, parseInt(value, 10) || 1);
    } else {
        slot[field] = value;
    }

    if (['start', 'end', 'eventType', 'participants'].includes(field)) {
        resetRooms();
    }
};

window.removeSlot = function(i) {
    GS.slots.splice(i, 1);
    renderCal();
    renderSlots();
    resetRooms();
};

window.checkRooms = function() {
    if (GS.slots.length === 0) {
        alert('Выберите хотя бы одну дату');
        return;
    }

    const btn = document.getElementById('btn-check-rooms');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Проверяем...';
    }

    const section = document.getElementById('bg-rooms-section');
    if (section) section.classList.add('visible');

    const loading = document.getElementById('bg-rooms-loading');
    if (loading) loading.style.display = 'block';

    const roomsCont = document.getElementById('bg-rooms-list');
    if (roomsCont) roomsCont.innerHTML = '';

    const payload = {
        slots: GS.slots.map(s => ({
            date: s.date,
            start: s.start,
            end: s.end,
            participants: s.participants
        }))
    };

    fetch('/bookings/group/check-conflicts/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload),
    })
    .then(r => r.json())
    .then(data => {
        GS.roomsMatrix = data.rooms || [];
        GS.equipMatrix = data.equipment || [];

        if (loading) loading.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Обновить';
        }

        renderRoomsList();
        renderSlots();
        section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    })
    .catch(() => {
        if (loading) loading.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-building"></i> Проверить аудитории';
        }
        alert('Ошибка загрузки');
    });
};

window.setRoomTypeFilter = function(key) {
    GS.roomTypeFilter = (GS.roomTypeFilter === key) ? '' : key;
    renderRoomsList();
};

function renderRoomsList() {
    const container = document.getElementById('bg-rooms-list');
    if (!container) return;

    if (!GS.roomsMatrix.length) {
        container.innerHTML = '<div style="padding:16px;color:var(--muted);text-align:center">Нет доступных аудиторий</div>';
        return;
    }

    const avgP = GS.slots.length
        ? Math.round(GS.slots.reduce((s, x) => s + (x.participants || 60), 0) / GS.slots.length)
        : 60;

    const allDates = GS.slots.map(s => s.date);

    const typeMap = new Map();
    GS.roomsMatrix.forEach(r => { if (r.type_key) typeMap.set(r.type_key, r.type); });
    const types = [...typeMap.entries()];

    const filterBar = types.length > 1 ? `
<div style="padding:8px 14px;border-bottom:1px solid var(--border);background:var(--bg);display:flex;align-items:center;gap:8px">
  <label style="font-size:12px;font-weight:600;color:var(--muted);white-space:nowrap">Тип аудитории</label>
  <select class="fc" style="max-width:220px;font-size:13px;padding:5px 8px"
          onchange="setRoomTypeFilter(this.value)">
    <option value="">Все типы</option>
    ${types.map(([k, l]) => `<option value="${k}" ${GS.roomTypeFilter === k ? 'selected' : ''}>${escH(l)}</option>`).join('')}
  </select>
</div>` : '';

    let rooms = GS.roomTypeFilter
        ? GS.roomsMatrix.filter(r => r.type_key === GS.roomTypeFilter)
        : [...GS.roomsMatrix];

    rooms.sort((a, b) => {
        if (a.conflict_count !== b.conflict_count) return a.conflict_count - b.conflict_count;
        return Math.abs(a.capacity - avgP) - Math.abs(b.capacity - avgP);
    });

    const rows = rooms.map(room => {
        const isPrimary = GS.primaryRoomId === room.id;
        const chips = allDates.map(d => {
            const isFree = room.free.includes(d);
            return `<span class="bg-chip ${isFree ? 'bg-chip-free' : 'bg-chip-conflict'}">${fmtShort(d)}</span>`;
        }).join('');

        return `
<div class="bg-room-row ${isPrimary ? 'primary-selected' : ''}" onclick="selectPrimary(${room.id})">
  <div style="flex:1;min-width:0">
    <div style="display: flex; align-items: center; gap: 8px;">
      <span class="bg-room-name">${escH(room.name)}</span>
      <button type="button" class="btn-sec" 
              onclick="event.stopPropagation(); showRoomInfo(${room.id})" 
              style="padding: 2px 4px; font-size: 11px; min-width: auto; border-radius: 100%;" 
              title="Подробнее об аудитории">
        <i class="bi bi-info-circle"></i>
      </button>
    </div>
    <div class="bg-room-meta">${escH(room.building)}, ${room.floor} эт. · ${room.capacity} мест · ${escH(room.type)}</div>
  </div>
  <div class="bg-date-chips">${chips}</div>
  ${isPrimary ? '<i class="bi bi-check-circle-fill" style="color:var(--blue);flex-shrink:0"></i>' : ''}
</div>`;
    }).join('');

    container.innerHTML = filterBar + (rooms.length
        ? rows
        : '<div style="padding:14px;text-align:center;color:var(--muted)">Нет аудиторий этого типа</div>');
}

window.selectPrimary = function(roomId) {
    GS.primaryRoomId = roomId;
    GS.conflictOverrides = {};

    const room = GS.roomsMatrix.find(r => r.id === roomId);
    if (!room) return;

    GS.slots.forEach(s => {
        s.roomId = room.free.includes(s.date) ? roomId : null;
    });

    renderRoomsList();
    renderConflictResolve(room);
    renderSlots();
};

function renderConflictResolve(primaryRoom) {
    const wrap = document.getElementById('bg-conflict-wrap');
    if (!wrap) return;

    const conflictDates = primaryRoom.conflicts || [];

    if (conflictDates.length === 0) {
        wrap.innerHTML = `
<div style="background:var(--success-bg);border-radius:var(--r-sm);padding:10px 14px;font-size:13px;color:var(--success);display:flex;gap:8px;align-items:center;margin-top:12px">
  <i class="bi bi-check-circle-fill"></i>
  Аудитория свободна на все выбранные даты
</div>`;
        checkAllResolved();
        return;
    }

    const avgPconflict = GS.slots.length
        ? Math.round(GS.slots.reduce((s, x) => s + (x.participants || 60), 0) / GS.slots.length)
        : 60;

    const rowsHtml = conflictDates.map(d => {
        let alts = GS.roomsMatrix.filter(r => r.id !== primaryRoom.id && r.free.includes(d));
        const currentSlot = GS.slots.find(s => s.date === d);
        const currentRoom = currentSlot?.roomId ? GS.roomsMatrix.find(r => r.id === currentSlot.roomId) : null;

        const slotP = GS.slots.find(s => s.date === d)?.participants || avgPconflict;
        alts.sort((a, b) => Math.abs(a.capacity - slotP) - Math.abs(b.capacity - slotP));

        const buttons = alts.length
            ? alts.map(r => {
                const isActive = currentRoom?.id === r.id;
                return `
        <div style="display: flex; align-items: center; gap: 8px;">
            <button type="button"
                    class="bg-room-choice ${isActive ? 'active' : ''}"
                    style="flex: 1;"
                    onclick="setConflictOverride('${d}', ${r.id}); renderConflictResolve(GS.roomsMatrix.find(x=>x.id===GS.primaryRoomId))">
                <span>${escH(r.name)}</span>
                <small>${escH(r.building)}, ${r.capacity} м. · ${escH(r.type)}</small>
            </button>
            <button type="button" 
                    class="btn-sec" 
                    onclick="event.stopPropagation(); showRoomInfo(${r.id})" 
                    style="padding: 2px 4px; font-size: 11px; min-width: auto; border-radius: 100%;" 
                    title="Подробнее об аудитории">
                <i class="bi bi-info-circle"></i>
            </button>
        </div>`;
              }).join('')
            : `<div style="font-size:12px;color:var(--muted);padding:6px 0">Нет свободных аудиторий</div>`;

        return `
<div class="bg-conflict-date-row">
  <div class="bg-conflict-date-col">
    <span class="bg-conflict-date-lbl">${formatDateRu(d)}</span>
    <span class="bg-conflict-current">${currentRoom ? escH(currentRoom.name + ' · ' + currentRoom.building) : 'не выбрано'}</span>
  </div>
  <div class="bg-conflict-room-list">
    ${buttons}
  </div>
</div>`;
    }).join('');

    wrap.innerHTML = `
<div class="bg-conflict-resolve mt-3">
  <div class="bg-conflict-resolve-head">
    <i class="bi bi-exclamation-triangle-fill"></i>
    Конфликт на ${conflictDates.length} дат. Выберите замену прямо в списке
  </div>
  ${rowsHtml}
</div>`;
}

window.setConflictOverride = function(date, roomId) {
    if (roomId) {
        GS.conflictOverrides[date] = roomId;
    } else {
        delete GS.conflictOverrides[date];
    }

    const slot = GS.slots.find(s => s.date === date);
    if (slot) slot.roomId = roomId || null;

    renderSlots();
    checkAllResolved();
};

function checkAllResolved() {
    if (!GS.primaryRoomId) return;

    const primaryRoom = GS.roomsMatrix.find(r => r.id === GS.primaryRoomId);
    if (!primaryRoom) return;

    const allDates = GS.slots.map(s => s.date);
    const unresolved = (primaryRoom.conflicts || []).filter(
        d => allDates.includes(d) && !GS.conflictOverrides[d]
    );

    const submitSection = document.getElementById('bg-submit-section');

    if (unresolved.length === 0) {
        showEquipBlock();
        syncAllSlotsEquipment();
        submitSection?.classList.add('visible');
        renderSummary();
        submitSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        document.getElementById('bg-equip-section')?.classList.remove('visible');
        submitSection?.classList.remove('visible');
    }
}

function renderSummary() {
    const container = document.getElementById('bg-summary');
    if (!container) return;

    syncAllSlotsEquipment();

    container.innerHTML = GS.slots.map(slot => {
        const room = GS.roomsMatrix.find(r => r.id === slot.roomId);
        const roomLabel = room ? `${room.name} · ${room.building}` : '—';
        const isOverride = slot.roomId !== GS.primaryRoomId;

        const eqNames = (slot.equipmentIds || []).map(id => {
            const eq = GS.equipMatrix.find(e => e.id === id);
            return eq ? buildEquipmentSummary(eq) : `#${id}`;
        });
        const eqText = eqNames.length ? eqNames.join(', ') : 'Без оборудования';

        return `
<div class="bg-summary-row">
  <span style="font-weight:600;min-width:90px">${formatDateRu(slot.date)}</span>
  <span style="color:var(--muted);font-size:12px">${slot.start}–${slot.end}</span>
  <span class="bg-room-badge ${isOverride ? 'bg-room-badge-alt' : ''}">
    ${isOverride ? '<i class="bi bi-arrow-left-right" title="Запасная"></i> ' : ''}${escH(roomLabel)}
  </span>
  <span class="bg-eq-badge" title="${escH(eqText)}">
    <i class="bi bi-laptop"></i>
    ${escH(eqText.length > 45 ? eqText.slice(0, 45) + '…' : eqText)}
  </span>
</div>`;
    }).join('');
}

window.submitGroup = function() {
    const title = (document.getElementById('group-title')?.value || '').trim();
    const comment = (document.getElementById('group-comment')?.value || '').trim();
    const dfFrom = document.getElementById('date-from')?.value;
    const dfTo = document.getElementById('date-to')?.value;

    if (!title) {
        alert('Введите название серии');
        return;
    }
    if (!dfFrom || !dfTo) {
        alert('Укажите период');
        return;
    }

    const now = new Date();
    const todayStr = toISO(now);
    const currentTimeStr = now.toTimeString().slice(0, 5); // HH:MM

    // Проверка даты начала периода
    if (dfFrom < todayStr) {
        alert('Дата начала серии не может быть в прошлом');
        return;
    }
    if (dfTo < dfFrom) {
        alert('Дата окончания серии не может быть раньше даты начала');
        return;
    }

    // Проверка каждого слота на прошедшее время
    for (const slot of GS.slots) {
        const slotDateTime = new Date(`${slot.date}T${slot.start}`);
        const nowDateTime = new Date();

        // Если дата слота в прошлом
        if (slot.date < todayStr) {
            alert(`Дата ${formatDateRu(slot.date)} уже прошла. Удалите этот день или измените дату.`);
            return;
        }

        // Если дата слота сегодня и время начала уже прошло
        if (slot.date === todayStr && slot.start < currentTimeStr) {
            alert(`Время начала ${slot.start} на ${formatDateRu(slot.date)} уже прошло. Измените время начала.`);
            return;
        }

        // Проверка что время окончания позже времени начала
        if (slot.end <= slot.start) {
            alert(`На ${formatDateRu(slot.date)} время окончания (${slot.end}) должно быть позже времени начала (${slot.start})`);
            return;
        }

        // Проверка что дата слота входит в период серии
        if (slot.date < dfFrom || slot.date > dfTo) {
            alert(`Дата ${formatDateRu(slot.date)} выходит за пределы периода серии (${formatDateRu(dfFrom)} – ${formatDateRu(dfTo)})`);
            return;
        }
    }

    const noRoom = GS.slots.find(s => !s.roomId);
    if (noRoom) {
        alert('Не назначена аудитория для ' + formatDateRu(noRoom.date));
        return;
    }

    syncAllSlotsEquipment();

    const btn = document.getElementById('btn-submit');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Создание...';
    }

    fetch('/bookings/group/submit/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            title,
            comment,
            date_from: dfFrom,
            date_to: dfTo,
            slots: GS.slots.map(s => ({
                date: s.date,
                start: s.start,
                end: s.end,
                event_type: s.eventType,
                participants: s.participants,
                comment: s.comment,
                room_id: s.roomId,
                equipment_ids: s.equipmentIds,
            })),
        }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            window.location.href = '/bookings/group/' + data.group_id + '/';
        } else {
            alert(data.error || 'Ошибка');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check-circle"></i> Создать заявки';
            }
        }
    })
    .catch(() => {
        alert('Ошибка соединения');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-circle"></i> Создать заявки';
        }
    });
};

// ==================== ОБОРУДОВАНИЕ ====================

function finalEquipForSlot(slot) {
    // Комбинируем: индивидуальное (из модалки) + глобальное (которое свободно)
    const result = new Set(slot._individualEquipment || []);

    // Добавляем глобальное оборудование, которое свободно в эту дату
    for (const eqId of GS.globalEquipment) {
        const eq = GS.equipMatrix.find(e => e.id === eqId);
        if (eq && eq.free && eq.free.includes(slot.date)) {
            result.add(eqId);
        }
    }

    return [...result];
}

function syncAllSlotsEquipment() {
    GS.slots.forEach(slot => {
        slot.equipmentIds = finalEquipForSlot(slot);
    });
}

function showEquipBlock() {
    const section = document.getElementById('bg-equip-section');
    if (!section) return;
    section.classList.add('visible');
    renderEquipList();
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderEquipList() {
    const container = document.getElementById('bg-equip-list');
    if (!container) return;

    const q = (GS._equipSearchQuery || '').toLowerCase();
    const allDates = GS.slots.map(s => s.date);

    const filtered = GS.equipMatrix.filter(eq => {
        if (!q) return true;
        return (eq.name + ' ' + (eq.model || '') + ' ' + eq.type + ' ' + eq.inventory)
            .toLowerCase().includes(q);
    });

    if (!filtered.length) {
        container.innerHTML = '<div style="padding:14px;text-align:center;color:var(--muted);font-size:13px">Ничего не найдено</div>';
        return;
    }

    container.innerHTML = filtered.map(eq => {
        const isSelected = GS.globalEquipment.has(eq.id);
        const hasAnyConflict = eq.conflict_count > 0 && isSelected;

        const chips = allDates.map(d => {
            const isFree = eq.free && eq.free.includes(d);
            const slot = GS.slots.find(s => s.date === d);
            const hasIndividual = slot?._individualEquipment?.includes(eq.id);

            const cls = hasIndividual ? 'bg-chip bg-chip-specific'
                      : isFree ? 'bg-chip bg-chip-free'
                      : 'bg-chip bg-chip-conflict';

            const title = hasIndividual ? 'Выбрано индивидуально'
                        : isFree ? 'Свободно' : 'Занято — не добавится';

            return `<span class="${cls}" title="${title}">${fmtShort(d)}</span>`;
        }).join('');

        return `
<div class="bg-eq-row ${isSelected ? 'eq-selected' : ''}" onclick="toggleGlobalEquip(${eq.id})">
  <input type="checkbox" class="bg-eq-check" ${isSelected ? 'checked' : ''}
         onclick="event.stopPropagation(); toggleGlobalEquip(${eq.id})">
  <div style="flex:1;min-width:0">
    <div style="display: flex; align-items: center; gap: 8px;">
      <span class="bg-eq-name">${escH(eq.name)}${eq.model ? ` <span style="font-weight:400;color:var(--muted)">— ${escH(eq.model)}</span>` : ''}</span>
      <button type="button" class="btn-sec" 
              onclick="event.stopPropagation(); showEquipmentInfo(${eq.id})" 
              style="padding: 2px 4px; font-size: 10px; min-width: auto; border-radius: 100%;" 
              title="Подробнее об оборудовании">
        <i class="bi bi-info-circle"></i>
      </button>
    </div>
    <div class="bg-eq-meta">${escH(eq.type)} · инв. ${escH(eq.inventory)}</div>
    ${hasAnyConflict ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">На ${eq.conflict_count} дат — не добавится (занято)</div>` : ''}
  </div>
  <div class="bg-date-chips">${chips}</div>
  ${isSelected ? '<i class="bi bi-check-circle-fill" style="color:var(--orange);flex-shrink:0"></i>' : ''}
</div>`;
    }).join('');
}

window.toggleGlobalEquip = function(eqId) {
    if (GS.globalEquipment.has(eqId)) {
        GS.globalEquipment.delete(eqId);
    } else {
        GS.globalEquipment.add(eqId);
    }

    updateEquipCount();

    // Применяем глобальное оборудование КО ВСЕМ слотам, ДОБАВЛЯЯ к индивидуальному
    GS.slots.forEach(slot => {
        slot.equipmentIds = finalEquipForSlot(slot);
    });

    renderEquipList();
    renderSlots();

    if (document.getElementById('bg-submit-section')?.classList.contains('visible')) {
        renderSummary();
    }
};

window.filterEquip = function(value) {
    GS._equipSearchQuery = value;
    renderEquipList();
};

function updateEquipCount() {
    const el = document.getElementById('bg-eq-count');
    if (!el) return;
    const n = GS.globalEquipment.size;
    el.textContent = n ? `${n} выбрано` : '';
}

// ==================== МОДАЛЬНОЕ ОКНО ОБОРУДОВАНИЯ ====================

let equipmentDebounceTimer = null;

window.debounceEquipmentSearchGroup = function() {
    clearTimeout(equipmentDebounceTimer);
    equipmentDebounceTimer = setTimeout(loadEquipmentModal, 300);
};

window.openEquipmentModal = function(slotIdx) {
    const slot = GS.slots[slotIdx];
    if (!slot) return;

    GS.equipmentModal.slotIndex = slotIdx;
    GS.equipmentModal.items = [];

    // Инициализируем временную выборку ТОЛЬКО индивидуальным оборудованием слота
    GS.equipmentModal.tempSelection = new Set(slot._individualEquipment || []);

    const input = document.getElementById('id_equipment_search_query_group');
    if (input) input.value = '';

    const title = document.getElementById('eq-modal-title');
    if (title) title.textContent = formatDateRu(slot.date);

    openModal('eq-modal');
    loadEquipmentModal();
};

async function loadEquipmentModal() {
    const slot = GS.slots[GS.equipmentModal.slotIndex];
    const listEl = document.getElementById('equipment-list-group');
    if (!slot || !listEl) return;

    listEl.innerHTML = '<div style="padding:14px;color:var(--muted)">Загрузка...</div>';

    try {
        const query = document.getElementById('id_equipment_search_query_group')?.value.trim() || '';
        const params = new URLSearchParams({
            is_available: 'true',
            event_date: slot.date,
            event_start_time: slot.start,
            event_end_time: slot.end
        });

        if (query) params.set('search_query', query);

        const response = await fetch(`/api/equipment?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
            const message = data?.non_field_errors?.[0] || data?.error || 'Произошла ошибка при поиске';
            listEl.innerHTML = `<div class="alert alert-danger">${escH(message)}</div>`;
            return;
        }

        const items = Array.isArray(data) ? data : [];
        GS.equipmentModal.items = items;

        items.forEach(rememberEquipmentFromItem);
        renderEquipmentModal();
    } catch {
        listEl.innerHTML = '<div class="alert alert-danger">Произошла ошибка при поиске</div>';
    }
}

function renderEquipmentModal() {
    const slot = GS.slots[GS.equipmentModal.slotIndex];
    const listEl = document.getElementById('equipment-list-group');
    if (!slot || !listEl) return;

    const selectedIds = GS.equipmentModal.tempSelection;

    if (!GS.equipmentModal.items.length) {
        listEl.innerHTML = '<div style="padding:14px;color:var(--muted)">Ничего не найдено</div>';
        return;
    }

    listEl.innerHTML = GS.equipmentModal.items.map(eq => {
        const isSelected = selectedIds.has(eq.id);
        const isGlobal = GS.globalEquipment.has(eq.id);
        const hint = isGlobal
            ? '<span style="font-size:10px;color:var(--orange);margin-left:4px">(глобальное)</span>'
            : '';

        return `
<div class="eq-row equipment-card ${isSelected ? 'selected' : ''}"
     data-id="${eq.id}"
     onclick="toggleEquipInModal(${eq.id})"
     style="cursor:pointer">
    <input type="checkbox" class="eq-chk" ${isSelected ? 'checked' : ''} 
           onclick="event.stopPropagation(); toggleEquipInModal(${eq.id})">
    <div class="eq-icon"><i class="bi bi-laptop"></i></div>
    <div style="flex:1;min-width:0">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span class="eq-name">${escH(eq.name || '')}${eq.model ? ' — ' + escH(eq.model) : ''} ${hint}</span>
            <button type="button" class="btn-sec" 
                    onclick="event.stopPropagation(); showEquipmentInfo(${eq.id})" 
                    style="padding: 2px 4px; font-size: 10px; min-width: auto; border-radius: 100%;" 
                    title="Подробнее об оборудовании">
                <i class="bi bi-info-circle"></i>
            </button>
        </div>
        <div class="eq-loc">
            ${eq.type_label || eq.type ? `<span class="eq-inv">${escH(eq.type_label || eq.type)}</span>` : ''}
            ${eq.inventory_number ? `<span class="eq-inv">${escH(eq.inventory_number)}</span>` : ''}
        </div>
    </div>
</div>`;
    }).join('');
}

window.toggleEquipInModal = function(id) {
    const sel = GS.equipmentModal.tempSelection;
    if (sel.has(id)) {
        sel.delete(id);
    } else {
        sel.add(id);
    }
    renderEquipmentModal();
};

window.applyEquipmentSelection = function() {
    const slot = GS.slots[GS.equipmentModal.slotIndex];
    if (slot) {
        // Сохраняем индивидуальный выбор
        slot._individualEquipment = [...GS.equipmentModal.tempSelection];
        // Обновляем полный список (индивидуальное + глобальное)
        slot.equipmentIds = finalEquipForSlot(slot);
    }
    closeModal('eq-modal');
    renderSlots();
    renderEquipList();

    if (document.getElementById('bg-submit-section')?.classList.contains('visible')) {
        renderSummary();
    }
};

// ==================== СТИЛИ ====================

(function injectEquipStyles() {
    if (document.getElementById('bg-equip-inline-styles')) return;
    const s = document.createElement('style');
    s.id = 'bg-equip-inline-styles';
    s.textContent = `
#bg-equip-section { display: none; }
#bg-equip-section.visible { display: block; }

.bg-eq-row {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    cursor: pointer; transition: background .12s; user-select: none;
}
.bg-eq-row:last-child { border-bottom: 0; }
.bg-eq-row:hover { background: var(--orange-lt, #fff7ed); }
.bg-eq-row.eq-selected { background: var(--orange-lt, #fff7ed); border-left: 3px solid var(--orange); }

.bg-eq-check { width: 16px; height: 16px; accent-color: var(--orange); flex-shrink: 0; cursor: pointer; }
.bg-eq-name { font-weight: 600; font-size: 13px; }
.bg-eq-meta { font-size: 11px; color: var(--muted); margin-top: 1px; }

.bg-chip-specific { background: var(--orange-lt, #fff7ed); color: var(--orange); }
`;
    document.head.appendChild(s);
})();

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

document.addEventListener('DOMContentLoaded', function() {
    const dfEl = document.getElementById('date-from');
    const dtEl = document.getElementById('date-to');

    function onPeriodChange() {
        GS.dateFrom = dfEl?.value || null;
        GS.dateTo = dtEl?.value || null;
        renderCal();
    }

    dfEl?.addEventListener('change', onPeriodChange);
    dtEl?.addEventListener('change', onPeriodChange);

    const today = toISO(new Date());
    if (dfEl) dfEl.min = today;
    if (dtEl) dtEl.min = today;

    initCal();
    renderSlots();
});

window.showRoomInfo = showRoomInfo;
window.showEquipmentInfo = showEquipmentInfo;