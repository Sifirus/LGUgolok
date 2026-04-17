(() => {
    'use strict';

    window.__approvalPendingState = window.__approvalPendingState || {
        currentBookingId: null,
        currentScope:     null,
        activeTab:        localStorage.getItem('appr_tab') || 'pending',
    };
    const S = window.__approvalPendingState;

    // Восстановить текущую заявку из localStorage
    const _storedId = parseInt(localStorage.getItem('appr_current_id') || '0', 10);
    if (_storedId && !S.currentBookingId) S.currentBookingId = _storedId;

    /* ── utils ── */
    function escH(v) {
        return String(v ?? '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }
    function escBr(v) { return escH(v).replace(/\n/g,'<br>'); }

    function showMessage(text, type) {
        const el = document.getElementById('approval-message');
        if (!el) return;
        const cls = type === 'success' ? 'alert-success' : 'alert-danger';
        const bg  = type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)';
        const col = type === 'success' ? 'var(--success)'    : 'var(--danger)';
        el.innerHTML = `<div class="alert ${cls}" style="background:${bg};color:${col};padding:12px;border-radius:var(--r-sm)">${escH(text)}</div>`;
        setTimeout(() => { el.innerHTML = ''; }, 5000);
    }

    function emptyPanel() {
        return `
<div class="text-center py-5 text-muted">
  <i class="bi bi-folder2-open" style="font-size:48px;opacity:0.5"></i>
  <p class="mt-3 mb-0">Выберите заявку из списка слева,<br>чтобы просмотреть детали и принять решение</p>
</div>`;
    }

    function renderEquipmentTags(list) {
        if (!(list || []).length) return '<span class="text-muted">—</span>';
        return (list || []).map(e => {
            const id = e.id || (typeof e === 'object' ? e.id : null);
            const name = e.name || e;
            if (id) {
                return `<a class="link" href="/equipment/${id}/" target="_blank" rel="noopener noreferrer" class="equipment-tag" style="text-decoration:none;">
                    <i class="bi bi-laptop"></i>${escH(name)}
                </a>`;
            }
            return `<span class="equipment-tag"><i class="bi bi-laptop"></i>${escH(name)}</span>`;
        }).join('');
    }

    /* ════════════════ СПИСОК ЗАЯВОК ════════════════ */

    function renderCard(item) {
        const name = item.initiator_name
            || [item.initiator_first_name, item.initiator_last_name].filter(Boolean).join(' ')
            || 'Не указан';
        const isCurrent = S.currentBookingId === item.id;

        if (item.scope === 'group') {
            return `
<div class="appr-card ${isCurrent?'selected':''}" data-id="${item.id}" onclick="selectBooking(${item.id})">
  <div class="appr-card-head">
    <span class="appr-num">Г${escH(item.group_id)}</span>
    <div style="flex:1">
      <div class="appr-title">${escH(item.group_title || 'Групповая заявка')}</div>
      <div class="appr-meta">
        <span><i class="bi bi-person"></i>${escH(name)}</span>
        <span><i class="bi bi-calendar3"></i>${escH(item.group_date_from)} – ${escH(item.group_date_to)}</span>
        <span><i class="bi bi-collection"></i>${escH(item.group_pending_count)} из ${escH(item.group_total_count)} требуют согласования</span>
      </div>
    </div>
    <span class="pill pill--processing">Группа</span>
  </div>
  <div class="appr-card-body">
    <div class="group-badges">
      <span class="group-badge"><i class="bi bi-list-check"></i>${escH(item.group_total_count)} подзаявок</span>
      <span class="group-badge"><i class="bi bi-hourglass-split"></i>${escH(item.group_pending_count)} на согласовании</span>
    </div>
  </div>
</div>`;
        }

        return `
<div class="appr-card ${isCurrent?'selected':''}" data-id="${item.id}" onclick="selectBooking(${item.id})">
  <div class="appr-card-head">
    <span class="appr-num">#${escH(item.id)}</span>
    <div style="flex:1">
      <div class="appr-title">${escH(item.event_type||'—')}</div>
      <div class="appr-meta">
        <span><i class="bi bi-person"></i>${escH(name)}</span>
        <span><i class="bi bi-calendar3"></i>${escH(item.event_date)}</span>
        <span><i class="bi bi-clock"></i>${escH((item.event_start_time||'').substring(0,5))}–${escH((item.event_end_time||'').substring(0,5))}</span>
      </div>
    </div>
    <span class="pill pill--pending">Ожидает</span>
  </div>
  <div class="appr-card-body">
    <div class="d-flex gap-3 text-muted small flex-wrap">
      <span><i class="bi bi-building"></i> ${escH(item.room_name||'—')}</span>
      <span><i class="bi bi-people"></i> ${escH(item.participants)} чел.</span>
    </div>
  </div>
</div>`;
    }

    /* ════════════════ ПОДЗАЯВКА ВНУТРИ ГРУППЫ ════════════════ */

    function renderSubBooking(item) {
        const name      = [item.initiator_first_name, item.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';
        const eqHtml    = renderEquipmentTags(item.equipment_list || []);
        const pending   = ['created','pending'].includes(item.status);

        const pillCls = {
            approved: 'pill--approved',
            rejected: 'pill--rejected',
            completed:'pill--done',
            canceled: 'pill--draft',
        }[item.status] || 'pill--processing';

        /* Кнопки индивидуального решения — только для ожидающих подзаявок */
        const actionBtns = pending ? `
<div class="subbooking-actions">
  <button class="btn-sm-approve" onclick="submitApprovalSingle(${item.id}, 'approved')">
    <i class="bi bi-check-lg"></i> Одобрить
  </button>
  <button class="btn-sm-reject" onclick="promptRejectSingle(${item.id})">
    <i class="bi bi-x-lg"></i> Отклонить
  </button>
</div>` : '';

        return `
<div class="subbooking-item ${pending ? 'subbooking-item--needs-approval' : ''}" id="subbooking-${item.id}">
  <div class="subbooking-item__head">
    <div>
      <div class="subbooking-item__title">Заявка #${escH(item.id)} · ${escH(item.event_type || '—')}</div>
      <div class="subbooking-item__meta">
        <span><i class="bi bi-calendar3"></i>${escH(item.event_date)}</span>
        <span><i class="bi bi-clock"></i>${escH((item.event_start_time || '').substring(0, 5))}–${escH((item.event_end_time || '').substring(0, 5))}</span>
        <span><i class="bi bi-building"></i>${escH(item.room_name || '—')}</span>
        <span><i class="bi bi-people"></i>${escH(item.participants)} чел.</span>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
      <span class="pill ${pillCls}">${escH(item.status_display || '—')}</span>
    </div>
  </div>

    <div class="detail-row">
      <span class="detail-lbl">Аудитория</span>
      <span class="detail-val">
        <a class="link" href="rooms/${item.room_id}/" target="_blank" rel="noopener noreferrer">
          ${escH(item.room_name || '—')}
        </a>
        ${item.room_building ? `, корп. ${escH(item.room_building)}` : ''}${item.room_floor ? `, эт. ${escH(item.room_floor)}` : ''}${item.room_capacity ? `, ${escH(item.room_capacity)} мест` : ''}
      </span>
    </div>

  <div class="detail-row">
    <span class="detail-lbl">Оборудование</span>
    <div class="detail-val">${eqHtml}</div>
  </div>

  ${item.comment ? `
  <div class="detail-row">
    <span class="detail-lbl">Комментарий</span>
    <div class="detail-val comment-box">${escBr(item.comment)}</div>
  </div>` : ''}

  ${actionBtns}
</div>`;
    }

    /* ════════════════ ПАНЕЛЬ ДЕТАЛИ ════════════════ */

    function renderDetailPanel(data) {
        const isGroup    = data.scope === 'group';
        const name       = [data.initiator_first_name, data.initiator_last_name].filter(Boolean).join(' ') || 'Не указан';
        const eqHtml     = renderEquipmentTags(data.equipment_list || []);
        const submittedAt = typeof formatDate === 'function' ? formatDate(data.created_at) : (data.created_at || '');
        const remaining  = data.group_pending_count || 0;

        const groupHead = isGroup ? `
<div class="group-summary">
  <div class="group-summary__head">
    <div>
      <div class="group-summary__title">${escH(data.group_title||'Групповая заявка')}</div>
      <div class="text-muted small">Группа #${escH(data.group_id)}</div>
    </div>
    <span class="pill pill--processing" id="pending-badge">${escH(remaining)} ожидают</span>
  </div>
  <div class="group-summary__meta">
    <div><strong>Период:</strong> ${formatDate(data.group_date_from)} – ${formatDate(data.group_date_to)}</div>
    <div><strong>Инициатор:</strong> ${escH(name)}</div>
    ${data.group_comment ? `<div><strong>Комментарий:</strong> ${escBr(data.group_comment)}</div>` : ''}
  </div>
</div>` : '';

        const singleInfo = !isGroup ? `
<div style="margin-bottom:20px;border:1px solid var(--border);border-radius:var(--r)">
  <div style="padding:12px 16px;background:var(--bg);border-bottom:1px solid var(--border);font-size:12px;font-weight:700">Параметры мероприятия</div>
  <div style="padding:4px 16px">
    <div class="detail-row"><span class="detail-lbl">Инициатор</span><span class="detail-val">${escH(name)}</span></div>
    <div class="detail-row"><span class="detail-lbl">Тип</span><span class="detail-val">${escH(data.event_type||'—')}</span></div>
    <div class="detail-row"><span class="detail-lbl">Дата</span><span class="detail-val">${escH(data.event_date)}</span></div>
    <div class="detail-row"><span class="detail-lbl">Время</span><span class="detail-val">${escH((data.event_start_time||'').substring(0,5))}–${escH((data.event_end_time||'').substring(0,5))}</span></div>
    <div class="detail-row">
        <span class="detail-lbl">Аудитория</span>
        <span class="detail-val">
            <a class="link" href="/rooms/${data.room_id}/" target="_blank" rel="noopener noreferrer" style="color:var(--blue);">
                ${escH(data.room_name||'—')}
            </a>
        </span>
    </div>
    <div class="detail-row"><span class="detail-lbl">Участников</span><span class="detail-val">${escH(data.participants)} чел.</span></div>
    <div class="detail-row"><span class="detail-lbl">Оборудование</span><span class="detail-val">${eqHtml}</span></div>
    ${data.comment ? `<div class="detail-row" style="border-bottom:0"><span class="detail-lbl">Комментарий</span><div class="detail-val comment-box">${escBr(data.comment)}</div></div>` : ''}
  </div>
</div>` : '';

        const groupBookingsHtml = isGroup ? `
<div style="margin-top:18px">
  <div style="font-size:14px;font-weight:800;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between">
    Подзаявки группы
    <span style="font-size:12px;font-weight:400;color:var(--muted)">(Синяя рамка — ожидает)</span>
  </div>
  <div class="subbooking-list" id="subbooking-list">
    ${(data.group_bookings || []).map(renderSubBooking).join('')}
  </div>
</div>` : '';

        /* Глобальный комментарий и кнопки "Одобрить все / Отклонить все" */
        const globalActions = `
<div style="margin-top:20px">
  <div style="margin-bottom:14px">
    <label class="fl">Комментарий к решению ${isGroup?'<span style="font-size:11px;color:var(--muted)">(применится ко всей группе)</span>':''} <span style="color:var(--danger)">*</span></label>
    <textarea class="fc" id="decisionComment" rows="3" placeholder="Укажите причину при отклонении..."></textarea>
  </div>
  <div class="d-flex gap-2">
    <button class="btn-blue flex-fill" onclick="submitApproval('approved')">
      <i class="bi bi-check-circle"></i> ${isGroup ? 'Одобрить все' : 'Одобрить'}
    </button>
    <button class="btn-reject flex-fill" onclick="submitApproval('rejected')">
      <i class="bi bi-x-circle"></i> ${isGroup ? 'Отклонить все' : 'Отклонить'}
    </button>
  </div>
  ${isGroup ? `<div class="group-actions-note">Применится ко всем ожидающим подзаявкам группы. Для индивидуального решения используйте кнопки в каждой строке выше.</div>` : ''}
</div>`;

        return `
<div class="d-flex justify-content-between align-items-start mb-4">
  <div>
    <div style="font-size:18px;font-weight:800;margin-bottom:4px">
      ${isGroup ? `Группа #${escH(data.group_id)}` : `Заявка #${escH(data.id)}`}
    </div>
    <span class="pill pill--processing">На согласовании</span>
  </div>
  <div class="d-flex gap-2 align-items-center">
    ${submittedAt ? `<div class="small text-muted">Поступила<br><strong>${escH(submittedAt)}</strong></div>` : ''}
    <button class="btn-sec" onclick="cancelBooking()" style="padding:6px 12px" title="Снять блокировку">
      <i class="bi bi-x-lg"></i>
    </button>
  </div>
</div>

${groupHead}
${singleInfo}
${groupBookingsHtml}
${globalActions}`;
    }

    /* ════════════════ ЗАГРУЗКА СПИСКА ════════════════ */

    function loadApprovalList() {
        const el = document.getElementById('approval-list');
        el.innerHTML = '<div class="text-center py-4">Загрузка...</div>';
        return fetchApprovalList(el);
    }

    async function fetchApprovalList(el) {
        try {
            const params = new URLSearchParams();
            if (S.currentBookingId) params.set('exclude_booking_id', S.currentBookingId);
            const url = params.toString() ? `/api/approval/pending/?${params}` : '/api/approval/pending/';
            const resp = await fetch(url);
            const data = await resp.json();
            if (resp.ok) {
                const list = data.results || data;
                el.innerHTML = list.length
                    ? list.map(renderCard).join('')
                    : '<div class="text-muted text-center py-4">Нет заявок</div>';
            } else {
                showMessage(data.detail || 'Ошибка загрузки', 'error');
            }
        } catch {
            showMessage('Ошибка соединения', 'error');
        }
    }

    /* ════════════════ ВЫБОР ЗАЯВКИ ════════════════ */

    async function selectBooking(bookingId) {
        try {
            const resp = await fetch(`/api/approval/${bookingId}`);
            const data = await resp.json();
            if (!resp.ok) { showMessage(data.detail || 'Ошибка загрузки', 'error'); return; }

            S.currentBookingId = data.id;
            S.currentScope     = data.scope || 'booking';
            localStorage.setItem('appr_current_id', data.id);

            document.querySelectorAll('.appr-card').forEach(c => {
                c.classList.toggle('selected', parseInt(c.dataset.id) === bookingId);
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

    /* ════════════════ РЕШЕНИЕ: ВСЕ ════════════════ */

    async function submitApproval(decision) {
        if (!S.currentBookingId) return;
        const comment = (document.getElementById('decisionComment')?.value || '').trim();

        if (decision === 'rejected' && !comment) {
            showMessage('Введите причину отклонения', 'error');
            return;
        }

        try {
            const resp = await fetch(`/api/approval/${S.currentBookingId}/decision`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body:    JSON.stringify({ decision, comment, scope: 'all' }),
            });
            const data = await resp.json();

            if (!resp.ok) { showMessage(data.detail || 'Ошибка', 'error'); return; }

            showMessage(data.detail, 'success');
            S.currentBookingId = null;
            S.currentScope     = null;
            localStorage.removeItem('appr_current_id');
            await loadApprovalList();
            if (S.activeTab === 'mine') await loadMyApprovals();
            document.getElementById('decisionPanel').innerHTML = emptyPanel();
        } catch {
            showMessage('Ошибка отправки', 'error');
        }
    }

    /* ════════════════ РЕШЕНИЕ: ОДНА ПОДЗАЯВКА ════════════════ */

    window.submitApprovalSingle = async function(bookingId, decision, comment) {
        const c = comment || (document.getElementById(`comment-single-${bookingId}`)?.value || '').trim();

        if (decision === 'rejected' && !c) {
            showMessage('Введите причину отклонения', 'error');
            return;
        }

        try {
            const resp = await fetch(`/api/approval/${bookingId}/decision`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body:    JSON.stringify({ decision, comment: c, scope: 'single' }),
            });
            const data = await resp.json();

            if (!resp.ok) { showMessage(data.detail || 'Ошибка', 'error'); return; }
            showMessage(data.detail, 'success');

            /* Если остались ожидающие — перезагрузить детальную панель */
            if (data.remaining > 0) {
                await selectBooking(S.currentBookingId);
            } else {
                /* Все решены — перейти к пустому состоянию */
                S.currentBookingId = null;
                S.currentScope     = null;
                await loadApprovalList();
                document.getElementById('decisionPanel').innerHTML = emptyPanel();
            }

            /* Обновить badge */
            const badge = document.getElementById('pending-badge');
            if (badge) badge.textContent = `${data.remaining} ожидают`;

        } catch {
            showMessage('Ошибка отправки', 'error');
        }
    };

    window.promptRejectSingle = function(bookingId) {
        /* Вставить инлайн-поле ввода причины под кнопкой */
        const card = document.getElementById(`subbooking-${bookingId}`);
        if (!card) return;

        /* Если уже открыто — ничего не делать */
        if (card.querySelector('.reject-inline')) return;

        const el = document.createElement('div');
        el.className = 'reject-inline';
        el.style.cssText = 'padding:10px 0;display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap';
        el.innerHTML = `
<textarea id="comment-single-${bookingId}" class="fc" rows="2" placeholder="Причина отклонения *"
          style="flex:1;font-size:13px"></textarea>
<button class="btn-sm-reject" onclick="submitApprovalSingle(${bookingId},'rejected')">
  Подтвердить
</button>
<button class="btn-sec" style="padding:5px 10px;font-size:12px"
        onclick="this.closest('.reject-inline').remove()">
  Отмена
</button>`;
        card.appendChild(el);
        el.querySelector('textarea').focus();
    };

    /* ════════════════ СНЯТЬ БЛОКИРОВКУ ════════════════ */

    async function cancelBooking() {
        if (!S.currentBookingId) return;
        try {
            const resp = await fetch(`/api/approval/${S.currentBookingId}/cancel`, {
                method:  'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });
            const data = await resp.json();
            if (!resp.ok) { showMessage(data.detail || 'Ошибка', 'error'); return; }

            showMessage(data.detail, 'success');
            S.currentBookingId = null;
            S.currentScope     = null;
            localStorage.removeItem('appr_current_id');
            await loadApprovalList();
            if (S.activeTab === 'mine') await loadMyApprovals();
            document.getElementById('decisionPanel').innerHTML = emptyPanel();
        } catch {
            showMessage('Ошибка', 'error');
        }
    }

    /* ════════════════ МОИ ЗАЯВКИ (вкладка) ════════════════ */

    async function loadMyApprovals() {
        const el = document.getElementById('approval-list');
        el.innerHTML = '<div class="text-center py-4">Загрузка...</div>';
        try {
            const resp = await fetch('/api/approval/my-locked/');
            const data = await resp.json();
            if (resp.ok) {
                const list = Array.isArray(data) ? data : [];
                el.innerHTML = list.length
                    ? list.map(item => renderCard({...item, _isMyTab: true})).join('')
                    : '<div class="text-muted text-center py-4">Нет взятых заявок</div>';
            } else {
                showMessage(data.detail || 'Ошибка загрузки', 'error');
            }
        } catch {
            showMessage('Ошибка соединения', 'error');
        }
    }

    /* ════════════════ ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК ════════════════ */

    window.switchTab = function(tab) {
        S.activeTab = tab;
        localStorage.setItem('appr_tab', tab);
        // Обновить классы кнопок
        document.querySelectorAll('.appr-tab-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tab);
        });
        if (tab === 'pending') {
            loadApprovalList();
        } else {
            loadMyApprovals();
        }
    };

    /* ════════════════ ЭКСПОРТ ════════════════ */

    window.loadApprovalList = loadApprovalList;
    window.loadMyApprovals  = loadMyApprovals;
    window.selectBooking    = selectBooking;
    window.submitApproval   = submitApproval;
    window.cancelBooking    = cancelBooking;

    document.addEventListener('DOMContentLoaded', async function() {
        // Восстановить активную вкладку
        document.querySelectorAll('.appr-tab-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === S.activeTab);
        });

        if (S.activeTab === 'mine') {
            await loadMyApprovals();
        } else {
            await loadApprovalList();
        }

        // Восстановить открытую заявку
        if (S.currentBookingId) {
            try { await selectBooking(S.currentBookingId); } catch {}
        }
    });
})();