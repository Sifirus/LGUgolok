(() => {
    window.__approvalPendingState = window.__approvalPendingState || {
        currentBookingId: null,
        currentScope: null
    };

    const approvalState = window.__approvalPendingState;

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeHtmlWithBreaks(value) {
        return escapeHtml(value).replace(/\n/g, '<br>');
    }

    function showMessage(text, type) {
        const messageDiv = document.getElementById('approval-message');
        if (!messageDiv) return;

        const className = type === 'success' ? 'alert-success' : 'alert-danger';
        messageDiv.innerHTML = `<div class="alert ${className}" style="background:${type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)'}; border:1px solid ${type === 'success' ? '#86efac' : '#FECACA'}; color:${type === 'success' ? 'var(--success)' : 'var(--danger)'}; padding:12px; border-radius:var(--r-sm)">${escapeHtml(text)}</div>`;
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, 5000);
    }

    function renderBaseEmptyState() {
        return `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-folder2-open" style="font-size:48px;opacity:0.5"></i>
                <p class="mt-3 mb-0">Выберите заявку из списка слева,<br>чтобы просмотреть детали и принять решение</p>
            </div>
        `;
    }

    function renderEquipment(list) {
        const items = list || [];
        if (!items.length) {
            return '<span class="text-muted">-</span>';
        }
        return items.map(eq => `<span class="equipment-tag"><i class="bi bi-laptop"></i>${escapeHtml(eq)}</span>`).join('');
    }

    function renderBookingCard(item) {
        const initiatorName = item.initiator_name || [item.initiator_first_name, item.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';

        if (item.scope === 'group') {
            return `
                <div class="appr-card ${approvalState.currentBookingId === item.id ? 'selected' : ''}" data-id="${item.id}" onclick="selectBooking(${item.id})">
                    <div class="appr-card-head">
                        <span class="appr-num">Г${escapeHtml(item.group_id)}</span>
                        <div style="flex:1">
                            <div class="appr-title">${escapeHtml(item.group_title || 'Групповая заявка')}</div>
                            <div class="appr-meta">
                                <span><i class="bi bi-person"></i>${escapeHtml(initiatorName)}</span>
                                <span><i class="bi bi-calendar3"></i>${escapeHtml(item.group_date_from)} – ${escapeHtml(item.group_date_to)}</span>
                                <span><i class="bi bi-collection"></i>${escapeHtml(item.group_pending_count)} из ${escapeHtml(item.group_total_count)} требуют согласования</span>
                            </div>
                        </div>
                        <span class="pill pill--processing">Группа</span>
                    </div>
                    <div class="appr-card-body">
                        <div class="group-badges">
                            <span class="group-badge"><i class="bi bi-list-check"></i>${escapeHtml(item.group_total_count)} подзаявок</span>
                            <span class="group-badge"><i class="bi bi-hourglass-split"></i>${escapeHtml(item.group_pending_count)} на согласовании</span>
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="appr-card ${approvalState.currentBookingId === item.id ? 'selected' : ''}" data-id="${item.id}" onclick="selectBooking(${item.id})">
                <div class="appr-card-head">
                    <span class="appr-num">#${escapeHtml(item.id)}</span>
                    <div style="flex:1">
                        <div class="appr-title">${escapeHtml(item.event_type || '—')}</div>
                        <div class="appr-meta">
                            <span><i class="bi bi-person"></i>${escapeHtml(initiatorName)}</span>
                            <span><i class="bi bi-calendar3"></i>${escapeHtml(item.event_date)}</span>
                            <span><i class="bi bi-clock"></i>${escapeHtml((item.event_start_time || '').substring(0, 5))}–${escapeHtml((item.event_end_time || '').substring(0, 5))}</span>
                        </div>
                    </div>
                    <span class="pill pill--pending">Ожидает</span>
                </div>
                <div class="appr-card-body">
                    <div class="d-flex gap-3 text-muted small flex-wrap">
                        <span><i class="bi bi-building"></i> ${escapeHtml(item.room_name || '—')}</span>
                        <span><i class="bi bi-people"></i> ${escapeHtml(item.participants)} чел.</span>
                    </div>
                </div>
            </div>
        `;
    }

    function renderGroupBookingItem(item) {
        const initiatorName = [item.initiator_first_name, item.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';
        const equipmentHtml = renderEquipment(item.equipment_list || []);
        const needsApproval = ['created', 'pending'].includes(item.status);
        const pillClass = item.status === 'approved'
            ? 'pill--approved'
            : item.status === 'rejected'
                ? 'pill--rejected'
                : 'pill--processing';

        return `
            <div class="subbooking-item ${needsApproval ? 'subbooking-item--needs-approval' : ''}">
                <div class="subbooking-item__head">
                    <div>
                        <div class="subbooking-item__title">Заявка #${escapeHtml(item.id)} · ${escapeHtml(item.event_type || '—')}</div>
                        <div class="subbooking-item__meta">
                            <span><i class="bi bi-person"></i>${escapeHtml(initiatorName)}</span>
                            <span><i class="bi bi-calendar3"></i>${escapeHtml(item.event_date)}</span>
                            <span><i class="bi bi-clock"></i>${escapeHtml((item.event_start_time || '').substring(0, 5))}–${escapeHtml((item.event_end_time || '').substring(0, 5))}</span>
                            <span><i class="bi bi-building"></i>${escapeHtml(item.room_name || '—')}</span>
                            <span><i class="bi bi-people"></i>${escapeHtml(item.participants)} чел.</span>
                        </div>
                    </div>
                    <span class="pill ${pillClass}">${escapeHtml(item.status_display || '—')}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-lbl">Подразделение</span>
                    <span class="detail-val">${escapeHtml(item.department || '—')}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-lbl">Аудитория</span>
                    <span class="detail-val">
                        ${escapeHtml(item.room_name || '—')}
                        ${item.room_building ? `, корпус ${escapeHtml(item.room_building)}` : ''}
                        ${item.room_floor ? `, этаж ${escapeHtml(item.room_floor)}` : ''}
                        ${item.room_capacity ? `, вместимость ${escapeHtml(item.room_capacity)}` : ''}
                    </span>
                </div>

                <div class="detail-row">
                    <span class="detail-lbl">Оборудование</span>
                    <div class="detail-val">${equipmentHtml}</div>
                </div>

                ${item.comment ? `
                    <div class="detail-row">
                        <span class="detail-lbl">Комментарий</span>
                        <div class="detail-val comment-box">${escapeHtmlWithBreaks(item.comment)}</div>
                    </div>
                ` : ''}

                ${item.approval_decision ? `
                    <div class="detail-row">
                        <span class="detail-lbl">Решение</span>
                        <span class="detail-val">${escapeHtml(item.approval_decision)}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function renderDetailPanel(data) {
        const groupMode = data.scope === 'group';
        const groupBookings = data.group_bookings || [];
        const initiatorName = [data.initiator_first_name, data.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';
        const equipmentHtml = renderEquipment(data.equipment_list || []);
        const submittedAt = typeof formatDate === 'function' ? formatDate(data.created_at) : (data.created_at || '');
        const groupInfoHtml = groupMode ? `
            <div class="group-summary">
                <div class="group-summary__head">
                    <div>
                        <div class="group-summary__title">${escapeHtml(data.group_title || 'Групповая заявка')}</div>
                        <div class="text-muted small">Группа #${escapeHtml(data.group_id)}</div>
                    </div>
                    <span class="pill pill--processing">${escapeHtml(data.group_pending_count)} из ${escapeHtml(data.group_total_count)} требуют согласования</span>
                </div>

                <div class="group-summary__meta">
                    <div><strong>Период:</strong> ${escapeHtml(data.group_date_from)} – ${escapeHtml(data.group_date_to)}</div>
                    <div><strong>Инициатор:</strong> ${escapeHtml(initiatorName)}</div>
                    ${data.group_comment ? `<div><strong>Комментарий к группе:</strong> ${escapeHtmlWithBreaks(data.group_comment)}</div>` : ''}
                </div>
            </div>
        ` : '';

        const groupBookingsHtml = groupMode ? `
            <div style="margin-top:18px">
                <div style="font-size:14px;font-weight:800;margin-bottom:12px">Подзаявки группы</div>
                <div class="subbooking-list">
                    ${groupBookings.map(renderGroupBookingItem).join('')}
                </div>
            </div>
        ` : '';

        const singleBookingHtml = !groupMode ? `
            <div style="margin-bottom:20px;border:1px solid var(--border);border-radius:var(--r)">
                <div style="padding:12px 16px;background:var(--bg);border-bottom:1px solid var(--border);font-size:12px;font-weight:700">Параметры мероприятия</div>
                <div style="padding:4px 16px">
                    <div class="detail-row"><span class="detail-lbl">Инициатор</span><span class="detail-val">${escapeHtml(initiatorName)}</span></div>
                    <div class="detail-row"><span class="detail-lbl">Тип</span><span class="detail-val">${escapeHtml(data.event_type || '—')}</span></div>
                    <div class="detail-row"><span class="detail-lbl">Дата</span><span class="detail-val">${escapeHtml(data.event_date)}</span></div>
                    <div class="detail-row"><span class="detail-lbl">Время</span><span class="detail-val">${escapeHtml((data.event_start_time || '').substring(0, 5))}–${escapeHtml((data.event_end_time || '').substring(0, 5))}</span></div>
                    <div class="detail-row"><span class="detail-lbl">Аудитория</span><span class="detail-val" style="color:var(--blue)">${escapeHtml(data.room_name || '—')}</span></div>
                    <div class="detail-row"><span class="detail-lbl">Участников</span><span class="detail-val">${escapeHtml(data.participants)} чел.</span></div>
                    <div class="detail-row"><span class="detail-lbl">Оборудование</span><span class="detail-val">${equipmentHtml}</span></div>
                    ${data.comment ? `<div class="detail-row" style="border-bottom:0"><span class="detail-lbl">Комментарий</span><div class="detail-val comment-box">${escapeHtmlWithBreaks(data.comment)}</div></div>` : ''}
                </div>
            </div>
        ` : '';

        return `
            <div class="d-flex justify-content-between align-items-start mb-4">
                <div>
                    <div style="font-size:18px;font-weight:800;margin-bottom:4px">
                        ${groupMode ? `Групповая заявка #${escapeHtml(data.group_id)}` : `Заявка #${escapeHtml(data.id)}`}
                    </div>
                    <span class="pill pill--processing">На согласовании</span>
                </div>
                <div class="d-flex gap-2 align-items-center">
                    ${submittedAt ? `<div class="small text-muted">Поступила<br><strong>${escapeHtml(submittedAt)}</strong></div>` : ''}
                    <button class="btn-sec" onclick="cancelBooking()" style="padding:6px 12px;" title="Отменить блокировку">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            </div>

            ${groupInfoHtml}
            ${singleBookingHtml}
            ${groupBookingsHtml}

            <div style="margin-bottom:18px;margin-top:18px">
                <label class="fl">Комментарий к решению <span style="color:var(--danger)">*</span></label>
                <textarea class="fc" id="decisionComment" rows="3" placeholder="Укажите причину при отклонении..."></textarea>
            </div>

            <div class="d-flex gap-2">
                <button class="btn-blue flex-fill" onclick="submitApproval('approved')"><i class="bi bi-check-circle"></i> Одобрить</button>
                <button class="btn-reject flex-fill" onclick="submitApproval('rejected')"><i class="bi bi-x-circle"></i> Отклонить</button>
            </div>

            <div class="group-actions-note">
                При принятии решения оно будет применено ко всей группе, если заявка групповая.
            </div>
        `;
    }

    function loadApprovalList() {
        const listEl = document.getElementById('approval-list');
        listEl.innerHTML = '<div class="text-center py-4">Загрузка...</div>';
        return fetchApprovalList(listEl);
    }

    async function fetchApprovalList(listEl) {
        try {
            const params = new URLSearchParams();
            if (approvalState.currentBookingId) params.set('exclude_booking_id', approvalState.currentBookingId);

            const url = params.toString() ? `/api/approval/pending/?${params}` : '/api/approval/pending/';
            const response = await fetch(url);
            const data = await response.json();

            if (response.ok) {
                const bookings = data.results || data;

                if (!bookings.length) {
                    listEl.innerHTML = `<div class="text-muted text-center py-4">Нет заявок</div>`;
                    return;
                }

                listEl.innerHTML = bookings.map(renderBookingCard).join('');
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

            approvalState.currentBookingId = data.id;
            approvalState.currentScope = data.scope || 'booking';

            document.querySelectorAll('.appr-card').forEach(card => {
                if (parseInt(card.dataset.id) === bookingId) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });

            const panel = document.getElementById('decisionPanel');
            panel.innerHTML = renderDetailPanel(data);

            if (window.innerWidth <= 1199) {
                panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        } catch {
            showMessage('Ошибка загрузки деталей', 'error');
        }
    }

    async function submitApproval(decision) {
        if (!approvalState.currentBookingId) return;

        const comment = document.getElementById('decisionComment')?.value || '';

        if (decision === 'rejected' && !comment.trim()) {
            showMessage('Введите причину отклонения', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/approval/${approvalState.currentBookingId}/decision`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ decision, comment })
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(data.detail || 'Ошибка при отправке', 'error');
                return;
            }

            showMessage(data.detail, 'success');
            approvalState.currentBookingId = null;
            approvalState.currentScope = null;
            await loadApprovalList();

            document.getElementById('decisionPanel').innerHTML = renderBaseEmptyState();
        } catch {
            showMessage('Ошибка отправки решения', 'error');
        }
    }

    async function cancelBooking() {
        if (!approvalState.currentBookingId) return;

        try {
            const response = await fetch(`/api/approval/${approvalState.currentBookingId}/cancel`, {
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
            approvalState.currentBookingId = null;
            approvalState.currentScope = null;
            await loadApprovalList();

            document.getElementById('decisionPanel').innerHTML = renderBaseEmptyState();
        } catch {
            showMessage('Ошибка отмены блокировки', 'error');
        }
    }

    window.loadApprovalList = loadApprovalList;
    window.selectBooking = selectBooking;
    window.submitApproval = submitApproval;
    window.cancelBooking = cancelBooking;

    document.addEventListener('DOMContentLoaded', loadApprovalList);
})();