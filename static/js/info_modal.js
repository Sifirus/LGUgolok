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
    const modal    = document.getElementById('infoModal');
    const title    = document.getElementById('infoModalTitle');
    const subtitle = document.getElementById('infoModalSubtitle');
    const body     = document.getElementById('infoModalBody');
    const link     = document.getElementById('infoModalLink');
    if (!modal) return;

    openModal('infoModal');
    title.textContent    = 'Информация об аудитории';
    subtitle.textContent = `ID: ${roomId}`;
    body.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)"><div class="spinner-border" style="margin-bottom:12px;"></div><div>Загрузка данных...</div></div>`;
    link.style.display = 'none';

    try {
        const resp = await fetch(`/api/room/${roomId}/`);
        const data = await resp.json();
        if (resp.ok) {
            body.innerHTML = `
<div class="info-detail-grid">
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-door-open" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Название</div>
      <div class="info-detail-value">${escH(data.name)}</div>
    </div>
  </div>
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-geo-alt" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Расположение</div>
      <div class="info-detail-value">${escH(data.building)}, ${data.floor} этаж</div>
    </div>
  </div>
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-people" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Вместимость</div>
      <div class="info-detail-value">${data.capacity} человек</div>
    </div>
  </div>
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-tag" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Характеристики</div>
      <div class="info-detail-value">
        <span class="info-badge"><i class="bi bi-building"></i> ${escH(data.type)}</span>
        <span class="info-badge"><i class="bi bi-circle-fill" style="font-size:8px;color:${data.status==='Активна'?'var(--success)':'var(--warning)'}"></i> ${escH(data.status)}</span>
      </div>
    </div>
  </div>
  ${data.equipment && data.equipment.length > 0 ? `
  <div style="margin-top:8px">
    <div class="info-section-title"><i class="bi bi-laptop"></i> Стационарное оборудование <span style="font-size:11px;font-weight:400;color:var(--muted);margin-left:auto">${data.equipment.length} ед.</span></div>
    <div class="info-equipment-list">
      ${data.equipment.map(eq => `<span class="info-equipment-tag" onclick="showEquipmentInfo(${eq.id})" title="Нажмите для подробностей"><i class="bi bi-laptop"></i>${escH(eq.name)}</span>`).join('')}
    </div>
  </div>` : `
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-laptop" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Оборудование</div>
      <div class="info-detail-value" style="color:var(--muted)">Отсутствует</div>
    </div>
  </div>`}
</div>`;
            link.href = `/rooms/${roomId}/`;
            link.style.display = 'inline-flex';
        } else {
            body.innerHTML = `<div style="padding:20px;text-align:center"><i class="bi bi-exclamation-triangle" style="font-size:32px;color:var(--danger);margin-bottom:12px"></i><div style="color:var(--danger)">${escH(data.detail||'Ошибка загрузки данных')}</div></div>`;
        }
    } catch {
        body.innerHTML = `<div style="padding:20px;text-align:center"><i class="bi bi-wifi-off" style="font-size:32px;color:var(--muted);margin-bottom:12px"></i><div style="color:var(--muted)">Ошибка соединения с сервером</div></div>`;
    }
}

// Показать информацию об оборудовании
async function showEquipmentInfo(equipId) {
    const modal    = document.getElementById('infoModal');
    const title    = document.getElementById('infoModalTitle');
    const subtitle = document.getElementById('infoModalSubtitle');
    const body     = document.getElementById('infoModalBody');
    const link     = document.getElementById('infoModalLink');
    if (!modal) return;

    openModal('infoModal');
    title.textContent    = 'Информация об оборудовании';
    subtitle.textContent = `ID: ${equipId}`;
    body.innerHTML = `<div style="padding:20px;text-align:center;color:var(--muted)"><div class="spinner-border" style="margin-bottom:12px;"></div><div>Загрузка данных...</div></div>`;
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
    <div class="info-detail-icon"><i class="bi bi-upc-scan" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Инвентарный номер</div>
      <div class="info-detail-value" style="font-family:monospace">${escH(data.inventory_number)}</div>
    </div>
  </div>
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-laptop" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Название</div>
      <div class="info-detail-value">${escH(data.name)}</div>
      ${data.model?`<div class="info-detail-sub">Модель: ${escH(data.model)}</div>`:''}
    </div>
  </div>
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-tags" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Характеристики</div>
      <div class="info-detail-value">
        <span class="info-badge"><i class="bi bi-diagram-3"></i> ${escH(data.type)}</span>
        <span class="info-badge"><i class="bi bi-circle-fill" style="font-size:8px;color:${statusColor}"></i> ${escH(data.status)}</span>
        <span class="info-badge"><i class="bi bi-pin${data.is_stationary?'-fill':''}"></i> ${data.is_stationary?'Стационарное':'Переносное'}</span>
      </div>
    </div>
  </div>
  ${data.room_name?`
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-geo-alt" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Расположение</div>
      <div class="info-detail-value">
        <a href="#" onclick="showRoomInfo(${data.room_id}); return false;" style="color:var(--blue);text-decoration:none">
          ${escH(data.room_name)} <i class="bi bi-box-arrow-up-right" style="font-size:11px;margin-left:4px"></i>
        </a>
      </div>
    </div>
  </div>` : `
  <div class="info-detail-row">
    <div class="info-detail-icon"><i class="bi bi-box" style="font-size:16px"></i></div>
    <div class="info-detail-content">
      <div class="info-detail-label">Расположение</div>
      <div class="info-detail-value" style="color:var(--muted)">На складе</div>
    </div>
  </div>`}
</div>`;
            link.href = `/equipment/${equipId}/`;
            link.style.display = 'inline-flex';
        } else {
            body.innerHTML = `<div style="padding:20px;text-align:center"><i class="bi bi-exclamation-triangle" style="font-size:32px;color:var(--danger);margin-bottom:12px"></i><div style="color:var(--danger)">${escH(data.detail||'Ошибка загрузки данных')}</div></div>`;
        }
    } catch {
        body.innerHTML = `<div style="padding:20px;text-align:center"><i class="bi bi-wifi-off" style="font-size:32px;color:var(--muted);margin-bottom:12px"></i><div style="color:var(--muted)">Ошибка соединения с сервером</div></div>`;
    }
}