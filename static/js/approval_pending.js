let currentBookingId = null;

function showMessage(text, type) {
    const messageDiv = document.getElementById('approval-message');
    if (!messageDiv) return;

    const className = type === 'success' ? 'alert-success' : 'alert-danger';
    messageDiv.innerHTML = `<div class="alert ${className}" style="background:${type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)'}; border:1px solid ${type === 'success' ? '#86efac' : '#FECACA'}; color:${type === 'success' ? 'var(--success)' : 'var(--danger)'}; padding:12px; border-radius:var(--r-sm)">${text}</div>`;
    setTimeout(() => {
        messageDiv.innerHTML = '';
    }, 5000);
}

function loadApprovalList() {
    const listEl = document.getElementById('approval-list');
    listEl.innerHTML = '<div class="text-center py-4">Загрузка...</div>';

    return fetchApprovalList(listEl);
}

async function fetchApprovalList(listEl) {
    try {
        const params = new URLSearchParams();
        if (currentBookingId) params.set('exclude_booking_id', currentBookingId);

        const url = params.toString() ? `/api/approval/pending/?${params}` : '/api/approval/pending/';
        const response = await fetch(url);
        const data = await response.json();

        if (response.ok) {
            const bookings = data.results || data;
            if (!bookings.length) {
                listEl.innerHTML = `<div class="text-muted text-center py-4">Нет заявок</div>`;
                return;
            }

            listEl.innerHTML = bookings.map(b => {
                const initiatorName = [b.initiator_first_name, b.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';
                return `
<div class="appr-card ${currentBookingId === b.id ? 'selected' : ''}" data-id="${b.id}" onclick="selectBooking(${b.id})">
    <div class="appr-card-head">
        <span class="appr-num">#${b.id}</span>
        <div style="flex:1">
            <div class="appr-title">${b.event_type || '—'}</div>
            <div class="appr-meta">
                <span><i class="bi bi-person"></i>${initiatorName}</span>
                <span><i class="bi bi-calendar3"></i>${formatDate(b.event_date)}</span>
                <span><i class="bi bi-clock"></i>${(b.event_start_time || '').substring(0, 5)}–${(b.event_end_time || '').substring(0, 5)}</span>
            </div>
        </div>
        <span class="pill pill--pending">Ожидает</span>
    </div>
    <div class="appr-card-body">
        <div class="d-flex gap-3 text-muted small">
            <span><i class="bi bi-building"></i> ${b.room_name || '—'}</span>
            <span><i class="bi bi-people"></i> ${b.participants} чел.</span>
        </div>
    </div>
</div>
`;
            }).join('');
        } else {
            showMessage(data.detail || 'Ошибка при загрузке заявок', 'error');
        }
    } catch {
        showMessage('Ошибка соединения', 'error');
    }
}

async function selectBooking(bookingId) {
    try {
        const response = await fetch(`/api/approval/${bookingId}`);
        const data = await response.json();

        if (!response.ok) {
            showMessage(data.detail || 'Ошибка при загрузке', 'error');
            return;
        }

        currentBookingId = data.id;

        document.querySelectorAll('.appr-card').forEach(card => {
            if (parseInt(card.dataset.id) === bookingId) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });

        const panel = document.getElementById('decisionPanel');
        const initiatorName = [data.initiator_first_name, data.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';
        const equipmentHtml = (data.equipment_list || []).map(eq =>
            `<span class="equipment-tag"><i class="bi bi-laptop"></i>${escapeHtml(eq)}</span>`
        ).join('') || '-';
        const submittedAt = formatDateTime(data.created_at);

        panel.innerHTML = `
<div class="d-flex justify-content-between align-items-start mb-4">
    <div>
        <div style="font-size:18px;font-weight:800;margin-bottom:4px">Заявка #${data.id}</div>
        <span class="pill pill--processing">На согласовании</span>
    </div>
    <div class="d-flex gap-2 align-items-center">
        ${submittedAt ? `<div class="small text-muted">Поступила<br><strong>${submittedAt}</strong></div>` : ''}
        <button class="btn-sec" onclick="cancelBooking()" style="padding:6px 12px;" title="Отменить блокировку">
            <i class="bi bi-x-lg"></i>
        </button>
    </div>
</div>

<div style="margin-bottom:20px;border:1px solid var(--border);border-radius:var(--r)">
    <div style="padding:12px 16px;background:var(--bg);border-bottom:1px solid var(--border);font-size:12px;font-weight:700">Параметры мероприятия</div>
    <div style="padding:4px 16px">
        <div class="detail-row"><span class="detail-lbl">Инициатор</span><span class="detail-val">${initiatorName}</span></div>
        <div class="detail-row"><span class="detail-lbl">Тип</span><span class="detail-val">${data.event_type || '—'}</span></div>
        <div class="detail-row"><span class="detail-lbl">Дата</span><span class="detail-val">${formatDate(data.event_date)}</span></div>
        <div class="detail-row"><span class="detail-lbl">Время</span><span class="detail-val">${(data.event_start_time || '').substring(0, 5)}–${(data.event_end_time || '').substring(0, 5)}</span></div>
        <div class="detail-row"><span class="detail-lbl">Аудитория</span><span class="detail-val" style="color:var(--blue)">${data.room_name || '—'}</span></div>
        <div class="detail-row"><span class="detail-lbl">Участников</span><span class="detail-val">${data.participants} чел.</span></div>
        <div class="detail-row"><span class="detail-lbl">Оборудование</span><span class="detail-val">${equipmentHtml}</span></div>
        ${data.comment ? `<div class="detail-row" style="border-bottom:0"><span class="detail-lbl">Комментарий</span><div class="detail-val comment-box">${data.comment}</div></div>` : ''}
    </div>
</div>

<div style="margin-bottom:18px">
    <label class="fl">Комментарий к решению <span style="color:var(--danger)">*</span></label>
    <textarea class="fc" id="decisionComment" rows="3" placeholder="Укажите причину при отклонении..."></textarea>
</div>

<div class="d-flex gap-2">
    <button class="btn-blue flex-fill" onclick="submitApproval('approved')"><i class="bi bi-check-circle"></i> Одобрить</button>
    <button class="btn-reject flex-fill" onclick="submitApproval('rejected')"><i class="bi bi-x-circle"></i> Отклонить</button>
</div>

<div class="small text-muted text-center mt-3">После принятия решения инициатор получит уведомление</div>
`;

        if (window.innerWidth <= 1199) {
            panel.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    } catch {
        showMessage('Ошибка загрузки деталей', 'error');
    }
}

async function submitApproval(decision) {
    if (!currentBookingId) return;

    const comment = document.getElementById('decisionComment')?.value || '';

    if (decision === 'rejected' && !comment.trim()) {
        showMessage('Введите причину отклонения', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/approval/${currentBookingId}/decision`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({decision, comment})
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.detail || 'Ошибка при отправке', 'error');
            return;
        }

        showMessage(data.detail, 'success');
        currentBookingId = null;
        await loadApprovalList();

        document.getElementById('decisionPanel').innerHTML = `
<div class="text-center py-5 text-muted">
    <i class="bi bi-folder2-open" style="font-size:48px;opacity:0.5"></i>
    <p class="mt-3 mb-0">Выберите заявку из списка слева,<br>чтобы просмотреть детали и принять решение</p>
</div>
`;
    } catch {
        showMessage('Ошибка отправки решения', 'error');
    }
}

async function cancelBooking() {
    if (!currentBookingId) return;

    try {
        const response = await fetch(`/api/approval/${currentBookingId}/cancel`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.detail || 'Ошибка при отмене блокировки', 'error');
            return;
        }

        showMessage(data.detail, 'success');
        currentBookingId = null;
        await loadApprovalList();

        document.getElementById('decisionPanel').innerHTML = `
<div class="text-center py-5 text-muted">
    <i class="bi bi-folder2-open" style="font-size:48px;opacity:0.5"></i>
    <p class="mt-3 mb-0">Выберите заявку из списка слева,<br>чтобы просмотреть детали и принять решение</p>
</div>
`;
    } catch {
        showMessage('Ошибка отмены блокировки', 'error');
    }
}

document.addEventListener('DOMContentLoaded', loadApprovalList);