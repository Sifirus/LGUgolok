var currentType = 'rooms';
var currentData = null;

function selectType(type) {
    currentType = type;
    document.getElementById('card-rooms').classList.toggle('sel', type === 'rooms');
    document.getElementById('card-equipment').classList.toggle('sel', type === 'equipment');
    if (currentData) {
        loadReport();
    }
}

function setPreset(preset) {
    var today = new Date();
    var from = new Date();

    if (preset === 'month') {
        from.setDate(1);
    } else if (preset === 'quarter') {
        from.setMonth(today.getMonth() - 2);
        from.setDate(1);
    } else if (preset === 'year') {
        from = new Date(today.getFullYear(), 0, 1);
    }

    document.getElementById('date_from').value = toISO(from);
    document.getElementById('date_to').value = toISO(today);
    loadReport();
}

function toISO(d) {
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function loadReport() {
    var df = document.getElementById('date_from').value;
    var dt = document.getElementById('date_to').value;

    if (!df || !dt) {
        alert('Укажите период');
        return;
    }

    var url = currentType === 'rooms'
        ? '/api/reports/rooms/?date_from=' + encodeURIComponent(df) + '&date_to=' + encodeURIComponent(dt)
        : '/api/reports/equipment/?date_from=' + encodeURIComponent(df) + '&date_to=' + encodeURIComponent(dt);

    document.getElementById('bars-wrap').innerHTML =
        '<div class="rep-empty"><i class="bi bi-hourglass-split"></i><div>Загрузка...</div></div>';

    document.getElementById('tbl-body').innerHTML =
        '<tr><td colspan="7"><div class="rep-empty rep-empty--table"><i class="bi bi-hourglass-split"></i><div>Загрузка...</div></div></td></tr>';

    fetch(url, { credentials: 'same-origin' })
        .then(function (r) {
            if (!r.ok) {
                throw new Error('HTTP ' + r.status);
            }
            return r.json();
        })
        .then(function (data) {
            currentData = data;
            renderMetrics(data);
            renderBars(data);
            renderTable(data);
        })
        .catch(function () {
            document.getElementById('bars-wrap').innerHTML =
                '<div class="rep-empty"><i class="bi bi-exclamation-triangle"></i><div>Ошибка загрузки</div></div>';
            document.getElementById('tbl-body').innerHTML =
                '<tr><td colspan="7"><div class="rep-empty rep-empty--table"><i class="bi bi-exclamation-triangle"></i><div>Ошибка загрузки</div></div></td></tr>';
        });
}

function renderMetrics(data) {
    document.getElementById('m-hours').textContent = (data.total_hours ?? 0) + ' ч';
    document.getElementById('m-avg').textContent = (data.avg_load ?? 0) + '%';
    document.getElementById('m-bookings').textContent = data.total_bookings ?? 0;

    if (currentType === 'rooms') {
        document.getElementById('m-hours-lbl').textContent = 'Часов занятости';
        document.getElementById('m-avg-lbl').textContent = 'Средняя загруженность';
        document.getElementById('m-bookings-lbl').textContent = 'Мероприятий';
        document.getElementById('m-special').textContent = data.high_load_count ?? 0;
        document.getElementById('m-special-lbl').textContent = 'Аудиторий с загр. > 70%';
    } else {
        document.getElementById('m-hours-lbl').textContent = 'Часов использования';
        document.getElementById('m-avg-lbl').textContent = 'Средняя востребованность';
        document.getElementById('m-bookings-lbl').textContent = 'Всего использований';
        document.getElementById('m-special').textContent = data.popular_count ?? 0;
        document.getElementById('m-special-lbl').textContent = 'Популярных позиций > 50%';
    }
}

function barGradient(pct) {
    if (pct > 80) return 'linear-gradient(90deg,#B91C1C,#F87171)';
    if (pct > 60) return 'linear-gradient(90deg,#E8751A,#F5A461)';
    if (pct > 30) return 'linear-gradient(90deg,#1E4BA3,#5B8CE8)';
    return 'linear-gradient(90deg,#64748B,#94A3B8)';
}

function renderBars(data) {
    var title = currentType === 'rooms' ? 'Загруженность аудиторий' : 'Востребованность оборудования';
    document.getElementById('bars-title').textContent = title;

    var items = (data.items || []).slice(0, 10);

    if (!items.length) {
        document.getElementById('bars-wrap').innerHTML =
            '<div class="rep-empty"><i class="bi bi-inboxes"></i><div>Нет данных за период</div></div>';
        return;
    }

    var html = items.map(function (item) {
        var label = currentType === 'rooms'
            ? (item.name || '')
            : ((item.name || '') + ' ' + (item.model || '')).trim();

        return (
            '<div class="rep-bar">' +
                '<div class="rep-bar__head">' +
                    '<span class="rep-bar__name" title="' + escapeHtml(label) + '">' + escapeHtml(label) + '</span>' +
                    '<strong>' + (item.load_pct ?? 0) + '%</strong>' +
                '</div>' +
                '<div class="rep-bar__track">' +
                    '<div class="rep-bar__fill" style="width:' + (item.load_pct ?? 0) + '%;background:' + barGradient(item.load_pct ?? 0) + '"></div>' +
                '</div>' +
            '</div>'
        );
    }).join('');

    document.getElementById('bars-wrap').innerHTML = html;
}

function renderTable(data) {
    var head = document.getElementById('tbl-head');
    var body = document.getElementById('tbl-body');
    var items = data.items || [];

    if (currentType === 'rooms') {
        document.getElementById('table-title').textContent = 'Детальная таблица по аудиториям';
        head.innerHTML = '<tr>' +
            '<th>Аудитория</th><th>Корпус</th><th>Тип</th>' +
            '<th>Мероприятий</th><th>Часов</th><th>Загруженность</th><th>Пиковый день</th>' +
            '</tr>';

        if (!items.length) {
            body.innerHTML = '<tr><td colspan="7"><div class="rep-empty rep-empty--table"><i class="bi bi-inboxes"></i><div>Нет данных за период</div></div></td></tr>';
            return;
        }

        body.innerHTML = items.map(function (item) {
            var pillClass = item.load_pct > 80 ? 'rep-pill--bad' : item.load_pct > 60 ? 'rep-pill--warn' : item.load_pct > 30 ? 'rep-pill--ok' : 'rep-pill--muted';
            return '<tr>' +
                '<td class="rep-name">' + escapeHtml(item.name || '') + '</td>' +
                '<td class="rep-sub">' + escapeHtml(item.building || '') + '</td>' +
                '<td class="rep-sub">' + escapeHtml(item.type || '') + '</td>' +
                '<td>' + (item.bookings_count ?? 0) + '</td>' +
                '<td>' + (item.total_hours ?? 0) + ' ч</td>' +
                '<td><span class="rep-pill ' + pillClass + '">' + (item.load_pct ?? 0) + '%</span></td>' +
                '<td class="rep-sub">' + escapeHtml(item.peak_day || '') + '</td>' +
                '</tr>';
        }).join('');
    } else {
        document.getElementById('table-title').textContent = 'Детальная таблица по оборудованию';
        head.innerHTML = '<tr>' +
            '<th>Инв. номер</th><th>Наименование</th><th>Тип</th>' +
            '<th>Использований</th><th>Часов</th><th>Востребованность</th><th>Аудитория</th>' +
            '</tr>';

        if (!items.length) {
            body.innerHTML = '<tr><td colspan="7"><div class="rep-empty rep-empty--table"><i class="bi bi-inboxes"></i><div>Нет данных за период</div></div></td></tr>';
            return;
        }

        body.innerHTML = items.map(function (item) {
            var pillClass = item.load_pct > 70 ? 'rep-pill--bad' : item.load_pct > 40 ? 'rep-pill--warn' : item.load_pct > 15 ? 'rep-pill--ok' : 'rep-pill--muted';
            var inv = '<code class="rep-table__mono" style="font-size:11px;background:var(--bg);padding:2px 6px;border-radius:4px;border:1px solid var(--border)">' + escapeHtml(item.inventory_number || '') + '</code>';

            return '<tr>' +
                '<td>' + inv + '</td>' +
                '<td>' +
                    '<div class="rep-name">' + escapeHtml(item.name || '') + '</div>' +
                    '<div class="rep-sub">' + escapeHtml(item.model || '') + '</div>' +
                '</td>' +
                '<td class="rep-sub">' + escapeHtml(item.type || '') + '</td>' +
                '<td>' + (item.bookings_count ?? 0) + '</td>' +
                '<td>' + (item.total_hours ?? 0) + ' ч</td>' +
                '<td><span class="rep-pill ' + pillClass + '">' + (item.load_pct ?? 0) + '%</span></td>' +
                '<td class="rep-sub">' + escapeHtml(item.room || '') + '</td>' +
                '</tr>';
        }).join('');
    }
}

function doExport(format) {
    var df = document.getElementById('date_from').value;
    var dt = document.getElementById('date_to').value;

    if (!df || !dt || !currentData) {
        alert('Сначала сформируйте отчёт');
        return;
    }

    var url = '/api/reports/export/' + encodeURIComponent(format) +
        '/?type=' + encodeURIComponent(currentType) +
        '&date_from=' + encodeURIComponent(df) +
        '&date_to=' + encodeURIComponent(dt);

    window.location.href = url;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

document.addEventListener('DOMContentLoaded', function () {
    loadReport();
});