'use strict';

/* ══════════════════════════════════════════════════════════
   UTILS
══════════════════════════════════════════════════════════ */
function byId(id) {
    return document.getElementById(id);
}

function escapeHtml(v) {
    return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function escapeJs(v) {
    return String(v ?? '').replace(/\\/g, '\\\\').replace(/'/g, "\\'")
        .replace(/"/g, '\\"').replace(/\n/g, ' ').replace(/\r/g, ' ');
}

/** ISO (yyyy-mm-dd) → дд.мм.гг */
function fmtDate(iso) {
    if (!iso) return '';
    var p = String(iso).split('-');
    if (p.length !== 3) return iso;
    return p[2] + '.' + p[1] + '.' + p[0].slice(2);
}

function toISO(d) {
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function buildUrl(path, params) {
    var parts = [];
    Object.keys(params).forEach(function (k) {
        if (params[k] !== null && params[k] !== undefined && params[k] !== '') {
            parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
        }
    });
    return path + (parts.length ? '?' + parts.join('&') : '');
}

function loadClass(val, bad, warn, ok) {
    if ((val ?? 0) > bad) return 'rep-pill--bad';
    if ((val ?? 0) > warn) return 'rep-pill--warn';
    if ((val ?? 0) > ok) return 'rep-pill--ok';
    return 'rep-pill--muted';
}

/* ══════════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════════ */
var state = {
    type: 'rooms',
    mode: 'overview',
    currentData: null,
    currentResource: null,
    searchTimer: null,
    _skipPush: false,

    charts: {
        overviewTrend: null, overviewPie: null, overviewSecondary: null,
        resourceTrend: null, resourcePie: null, resourceCapacity: null, resourceSecondary: null
    },

    PAGE_SIZE: 20,

    allOverviewItems: [],
    overviewPage: 1,
    overviewFilter: {search: '', type_key: ''},

    allDetailRows: [],
    detailPage: 1,
    detailFilter: {search: '', status: '', dateFrom: '', dateTo: '', eventType: ''},
};

/* ══════════════════════════════════════════════════════════
   BROWSER BACK BUTTON
══════════════════════════════════════════════════════════ */
function _pushHistory() {
    if (state._skipPush) return;
    history.pushState({
        mode: state.mode,
        type: state.type,
        resource: state.currentResource
    }, '');
}

window.addEventListener('popstate', function (e) {
    if (!e.state) return;
    state._skipPush = true;
    state.mode = e.state.mode || 'overview';
    state.type = e.state.type || 'rooms';
    state.currentResource = e.state.resource || null;

    byId('card-rooms').classList.toggle('sel', state.type === 'rooms');
    byId('card-equipment').classList.toggle('sel', state.type === 'equipment');
    byId('mode-overview').classList.toggle('sel', state.mode === 'overview');
    byId('mode-resource').classList.toggle('sel', state.mode === 'resource');

    byId('overview-block').style.display = state.mode === 'overview' ? '' : 'none';
    byId('resource-block').style.display = state.mode === 'resource' ? '' : 'none';
    byId('resourceSearchPanel').style.display = state.mode === 'resource' ? '' : 'none';
    byId('btn-clear-resource').style.display = state.mode === 'resource' ? '' : 'none';

    destroyCharts();
    clearSearchResults();

    if (state.mode === 'overview') {
        byId('selectedResourceChip').style.display = 'none';
        loadReport();
    } else {
        if (state.currentResource) {
            byId('resourceSearchInput').value = state.currentResource.label || '';
            byId('selectedResourceChip').style.display = '';
            byId('selectedResourceChip').textContent = state.currentResource.label || '';
            loadReport();
        } else {
            renderEmptyResourceState();
        }
    }
    state._skipPush = false;
});

/* ══════════════════════════════════════════════════════════
   TYPE / MODE SELECTION
══════════════════════════════════════════════════════════ */
function selectType(type) {
    state.type = type;
    byId('card-rooms').classList.toggle('sel', type === 'rooms');
    byId('card-equipment').classList.toggle('sel', type === 'equipment');
    clearSearchResults();
    if (state.mode === 'resource') clearResource(true);
    _pushHistory();
    loadReport();
}

function selectMode(mode) {
    state.mode = mode;
    byId('mode-overview').classList.toggle('sel', mode === 'overview');
    byId('mode-resource').classList.toggle('sel', mode === 'resource');
    byId('overview-block').style.display = mode === 'overview' ? '' : 'none';
    byId('resource-block').style.display = mode === 'resource' ? '' : 'none';
    byId('resourceSearchPanel').style.display = mode === 'resource' ? '' : 'none';
    byId('btn-clear-resource').style.display = mode === 'resource' ? '' : 'none';
    destroyCharts();
    clearSearchResults();

    if (mode === 'overview') {
        byId('selectedResourceChip').style.display = 'none';
        byId('selectedResourceChip').textContent = '';
        byId('resourceTitle').textContent = 'Ресурс не выбран';
        byId('resourceSubtitle').textContent = 'Выберите объект через поиск сверху';
        var linkEl = byId('resourcePageLink');
        if (linkEl) linkEl.style.display = 'none';
        byId('roomEquipmentBlock').style.display = 'none';
        _pushHistory();
        loadReport();
    } else {
        if (state.currentResource) {
            _pushHistory();
            loadReport();
        } else {
            _pushHistory();
            renderEmptyResourceState();
        }
    }
}

function setPreset(preset) {
    var today = new Date(), from = new Date();
    if (preset === 'month') {
        from.setDate(1);
    } else if (preset === 'quarter') {
        from.setMonth(today.getMonth() - 2);
        from.setDate(1);
    } else if (preset === 'year') {
        from = new Date(today.getFullYear(), 0, 1);
    }
    byId('date_from').value = toISO(from);
    byId('date_to').value = toISO(today);
    loadReport();
}

/* ══════════════════════════════════════════════════════════
   DATA LOADING
══════════════════════════════════════════════════════════ */
function loadReport() {
    var df = byId('date_from').value;
    var dt = byId('date_to').value;
    if (!df || !dt) {
        alert('Укажите период');
        return;
    }
    if (state.mode === 'overview') {
        loadOverviewReport(df, dt);
    } else {
        if (!state.currentResource) {
            renderEmptyResourceState();
            return;
        }
        loadResourceReport(df, dt, state.currentResource);
    }
}

function loadOverviewReport(df, dt) {
    var url = buildUrl('/api/reports/overview/', {type: state.type, date_from: df, date_to: dt});
    setLoadingOverview();
    fetch(url, {credentials: 'same-origin'})
        .then(function (r) {
            if (!r.ok) throw new Error();
            return r.json();
        })
        .then(function (d) {
            state.currentData = d;
            renderOverview(d);
        })
        .catch(renderOverviewError);
}

function loadResourceReport(df, dt, resource) {
    var url = buildUrl('/api/reports/resource/' + encodeURIComponent(resource.kind) + '/' +
        encodeURIComponent(resource.id) + '/', {date_from: df, date_to: dt});
    setLoadingResource(resource.kind);
    fetch(url, {credentials: 'same-origin'})
        .then(function (r) {
            if (!r.ok) throw new Error();
            return r.json();
        })
        .then(function (d) {
            state.currentData = d;
            renderResource(d);
            if (resource.kind === 'rooms') {
                byId('roomEquipmentBlock').style.display = '';
                loadRoomEquipmentTableSelected();
            } else {
                byId('roomEquipmentBlock').style.display = 'none';
            }
        })
        .catch(renderResourceError);
}

/* ══════════════════════════════════════════════════════════
   LOADING / ERROR / EMPTY STATES
══════════════════════════════════════════════════════════ */
function setLoadingOverview() {
    byId('overviewTblBody').innerHTML = _emptyRow(7, 'Загрузка...', 'bi-hourglass-split');
    byId('overviewHeatmap').innerHTML = _emptyDiv('Загрузка...', 'bi-hourglass-split');
}

function setLoadingResource(kind) {
    byId('resourceTblBody').innerHTML = _emptyRow(8, 'Загрузка...', 'bi-hourglass-split');
    byId('resourceHeatmap').innerHTML = _emptyDiv('Загрузка...', 'bi-hourglass-split');
    byId('resourceCapacityCol').style.display = kind === 'rooms' ? '' : 'none';
}

function renderOverviewError() {
    byId('overviewTblBody').innerHTML = _emptyRow(7, 'Ошибка загрузки', 'bi-exclamation-triangle');
    byId('overviewHeatmap').innerHTML = _emptyDiv('Ошибка загрузки', 'bi-exclamation-triangle');
}

function renderResourceError() {
    byId('resourceTblBody').innerHTML = _emptyRow(8, 'Ошибка загрузки', 'bi-exclamation-triangle');
}

function renderEmptyResourceState() {
    destroyCharts();
    byId('resourceTblBody').innerHTML = _emptyRow(8, 'Выберите ресурс для просмотра детального отчёта', 'bi-folder2-open');
    byId('resourceHeatmap').innerHTML = _emptyDiv('Нет выбранного ресурса', 'bi-folder2-open');
}

function _emptyRow(cols, text, icon) {
    return '<tr><td colspan="' + cols + '"><div class="rep-empty rep-empty--table">' +
        '<i class="bi ' + icon + '"></i><div>' + escapeHtml(text) + '</div></div></td></tr>';
}

function _emptyDiv(text, icon) {
    return '<div class="rep-empty"><i class="bi ' + icon + '"></i><div>' + escapeHtml(text) + '</div></div>';
}

/* ══════════════════════════════════════════════════════════
   OVERVIEW RENDERING
══════════════════════════════════════════════════════════ */
function renderOverview(data) {
    byId('m-hours').textContent = (data.total_hours ?? 0) + ' ч';
    byId('m-avg').textContent = (data.avg_load ?? 0) + '%';
    byId('m-bookings').textContent = data.total_bookings ?? 0;
    byId('m-special').textContent = data.canceled_count ?? 0;

    if (state.type === 'rooms') {
        byId('m-hours-lbl').textContent = 'Часов занятости';
        byId('m-avg-lbl').textContent = 'Средняя загрузка';
        byId('m-bookings-lbl').textContent = 'Заявок за период';
        byId('m-special-lbl').textContent = 'Отменённых заявок';
    } else {
        byId('m-hours-lbl').textContent = 'Часов использования';
        byId('m-avg-lbl').textContent = 'Средняя востребованность';
        byId('m-bookings-lbl').textContent = 'Использований';
        byId('m-special-lbl').textContent = 'Отменённых заявок';
    }

    state.allOverviewItems = data.items || [];
    state.overviewPage = 1;
    state.overviewFilter = {search: '', type_key: ''};

    renderOverviewTablePaged();
    renderOverviewCharts(data);
    renderHeatmap('overviewHeatmap', data.heatmap_days || [], data.heatmap_hours || [], data.heatmap || []);
}

/* ── Overview filter bar ── */
function _buildOverviewFilterBar() {
    var seen = {}, types = [];
    state.allOverviewItems.forEach(function (item) {
        if (item.type_key && !seen[item.type_key]) {
            seen[item.type_key] = true;
            types.push({key: item.type_key, label: item.type || item.type_key});
        }
    });

    var typeOpts = '<option value="">Все типы</option>' + types.map(function (t) {
        return '<option value="' + escapeHtml(t.key) + '"' +
            (state.overviewFilter.type_key === t.key ? ' selected' : '') + '>' +
            escapeHtml(t.label) + '</option>';
    }).join('');

    return '<div style="padding:14px 16px;border-bottom:1px solid var(--border);background:var(--surface)">' +
        '<div class="row g-2 align-items-end">' +
        '<div class="col-sm-4 col-md-3">' +
        '<label class="fl">Поиск</label>' +
        '<div class="sw"><i class="bi bi-search si"></i>' +
        '<input type="text" class="fc" placeholder="Поиск по названию..." ' +
        'value="' + escapeHtml(state.overviewFilter.search) + '" ' +
        'oninput="state.overviewFilter.search=this.value;state.overviewPage=1;renderOverviewTablePaged()">' +
        '</div></div>' +
        (types.length > 1 ?
            '<div class="col-sm-3 col-md-2">' +
            '<label class="fl">Тип</label>' +
            '<select class="fc" onchange="state.overviewFilter.type_key=this.value;state.overviewPage=1;renderOverviewTablePaged()">' +
            typeOpts + '</select></div>' : '') +
        '<div class="col-auto d-flex align-items-end gap-2">' +
        '<button class="btn-sec" onclick="exportOverviewCSV()">' +
        '<i class="bi bi-download"></i>CSV</button>' +
        '<span id="overview-count" style="font-size:12px;color:var(--muted);line-height:38px"></span>' +
        '</div>' +
        '</div></div>';
}

function _filterOverviewItems() {
    var s = state.overviewFilter.search.toLowerCase();
    var t = state.overviewFilter.type_key;
    return state.allOverviewItems.filter(function (item) {
        if (t && item.type_key !== t) return false;
        if (s) {
            var src = [item.name, item.building, item.type, item.inventory_number, item.model]
                .filter(Boolean).join(' ').toLowerCase();
            if (src.indexOf(s) === -1) return false;
        }
        return true;
    });
}

window.renderOverviewTablePaged = function () {
    var filterWrap = byId('overview-filter-wrap');
    if (filterWrap) filterWrap.innerHTML = _buildOverviewFilterBar();

    var filtered = _filterOverviewItems();
    var total = filtered.length;
    var pages = Math.ceil(total / state.PAGE_SIZE) || 1;
    if (state.overviewPage > pages) state.overviewPage = 1;

    var page = filtered.slice((state.overviewPage - 1) * state.PAGE_SIZE, state.overviewPage * state.PAGE_SIZE);

    var head = byId('overviewTblHead');
    var body = byId('overviewTblBody');

    if (state.type === 'rooms') {
        head.innerHTML = '<tr><th>Аудитория</th><th>Корпус</th><th>Тип</th><th>Статус</th>' +
            '<th>Заявок</th><th>Часов</th><th>Загрузка</th></tr>';
        body.innerHTML = page.length
            ? page.map(function (item) {
                return '<tr class="rep-link-row" onclick="openResource(' + item.id + ',\'rooms\',\'' + escapeJs(item.name || '') + '\')">' +
                    '<td class="rep-name">' + escapeHtml(item.name || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.building || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.type || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.status || '') + '</td>' +
                    '<td>' + (item.bookings_count || 0) + '</td>' +
                    '<td>' + (item.total_hours || 0) + ' ч</td>' +
                    '<td><span class="rep-pill ' + loadClass(item.load_pct, 70, 40, 15) + '">' +
                    (item.load_pct || 0) + '%</span></td></tr>';
            }).join('')
            : _emptyRow(7, 'Нет данных', 'bi-inboxes');
    } else {
        head.innerHTML = '<tr><th>Инв. номер</th><th>Наименование</th><th>Тип</th><th>Место</th>' +
            '<th>Заявок</th><th>Часов</th><th>Загрузка</th></tr>';
        body.innerHTML = page.length
            ? page.map(function (item) {
                return '<tr class="rep-link-row" onclick="openResource(' + item.id + ',\'equipment\',\'' + escapeJs(item.name || '') + '\')">' +
                    '<td><code class="rep-table__mono">' + escapeHtml(item.inventory_number || '') + '</code></td>' +
                    '<td><div class="rep-name">' + escapeHtml(item.name || '') + '</div>' +
                    '<div class="rep-sub">' + escapeHtml(item.model || '') + '</div></td>' +
                    '<td class="rep-sub">' + escapeHtml(item.type || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.room || '') + '</td>' +
                    '<td>' + (item.bookings_count || 0) + '</td>' +
                    '<td>' + (item.total_hours || 0) + ' ч</td>' +
                    '<td><span class="rep-pill ' + loadClass(item.load_pct, 70, 40, 15) + '">' +
                    (item.load_pct || 0) + '%</span></td></tr>';
            }).join('')
            : _emptyRow(7, 'Нет данных', 'bi-inboxes');
    }

    var pager = byId('overview-pagination');
    if (pager) pager.innerHTML = _buildPager(state.overviewPage, pages, 'goOverviewPage');

    var countEl = byId('overview-count');
    if (countEl) countEl.textContent = total + ' записей';
};

window.goOverviewPage = function (p) {
    state.overviewPage = p;
    renderOverviewTablePaged();
};

/* ══════════════════════════════════════════════════════════
   RESOURCE RENDERING
══════════════════════════════════════════════════════════ */
function renderResource(data) {
    var resource = data.resource || {};
    var summary = data.summary || {};

    byId('resourceTitle').textContent = resource.kind === 'rooms'
        ? (resource.name || 'Аудитория')
        : ((resource.name || '') + (resource.model ? ' | ' + resource.model : ''));

    var subtitle = resource.kind === 'rooms'
        ? [resource.building, resource.type, resource.floor ? 'этаж ' + resource.floor : ''].filter(Boolean).join(' | ')
        : [resource.inventory_number, resource.room, resource.type].filter(Boolean).join(' | ');
    byId('resourceSubtitle').textContent = subtitle;

    // Ссылка на страницу ресурса
    var linkEl = byId('resourcePageLink');
    if (linkEl) {
        linkEl.href = resource.kind === 'rooms'
            ? '/rooms/' + resource.id + '/'
            : '/equipment/' + resource.id + '/';
        linkEl.style.display = '';
    }

    byId('resourceStatusChip').textContent = resource.status || '';
    byId('resourceMetaChip').textContent = resource.kind === 'rooms'
        ? ('Вместимость ' + (resource.capacity ?? 0))
        : ('Инв. № ' + (resource.inventory_number || ''));

    byId('selectedResourceChip').style.display = '';
    byId('selectedResourceChip').textContent = resource.name || '';

    byId('m-hours').textContent = (summary.total_hours ?? 0) + ' ч';
    byId('m-avg').textContent = (summary.load_pct ?? 0) + '%';
    byId('m-bookings').textContent = summary.total_bookings ?? 0;
    byId('m-special').textContent = summary.canceled_count ?? 0;
    byId('m-hours-lbl').textContent = 'Часов занятости';
    byId('m-avg-lbl').textContent = 'Загрузка ресурса';
    byId('m-bookings-lbl').textContent = 'Заявок';
    byId('m-special-lbl').textContent = 'Отменённых';

    state.allDetailRows = data.detail_rows || [];
    state.detailPage = 1;
    state.detailFilter = {search: '', status: '', dateFrom: '', dateTo: '', eventType: ''};

    renderDetailTablePaged();
    renderResourceCharts(data);
    renderHeatmap('resourceHeatmap', data.heatmap_days || [], data.heatmap_hours || [], data.heatmap || []);
}

/* ── Detail filter bar ── */
function _buildDetailFilterBar() {
    var seenSt = {}, statuses = [];
    var seenEt = {}, eventTypes = [];
    state.allDetailRows.forEach(function (row) {
        if (row.status_key && !seenSt[row.status_key]) {
            seenSt[row.status_key] = true;
            statuses.push({key: row.status_key, label: row.status || row.status_key});
        }
        if (row.event_type_key && !seenEt[row.event_type_key]) {
            seenEt[row.event_type_key] = true;
            eventTypes.push({key: row.event_type_key, label: row.event_type || row.event_type_key});
        }
    });

    var statusOpts = '<option value="">Все статусы</option>' + statuses.map(function (s) {
        return '<option value="' + escapeHtml(s.key) + '"' +
            (state.detailFilter.status === s.key ? ' selected' : '') + '>' +
            escapeHtml(s.label) + '</option>';
    }).join('');

    var etOpts = '<option value="">Все типы</option>' + eventTypes.map(function (e) {
        return '<option value="' + escapeHtml(e.key) + '"' +
            (state.detailFilter.eventType === e.key ? ' selected' : '') + '>' +
            escapeHtml(e.label) + '</option>';
    }).join('');

    return '<div style="padding:14px 16px;border-bottom:1px solid var(--border);background:var(--bg)">' +
        '<div class="row g-2 align-items-end">' +
        '<div class="col-sm-4 col-md-3">' +
        '<label class="fl">Поиск</label>' +
        '<div class="sw"><i class="bi bi-search si"></i>' +
        '<input type="text" class="fc" placeholder="ID, дата, комментарий..." ' +
        'value="' + escapeHtml(state.detailFilter.search) + '" ' +
        'oninput="state.detailFilter.search=this.value;state.detailPage=1;renderDetailTablePaged()">' +
        '</div></div>' +
        '<div class="col-sm-3 col-md-2">' +
        '<label class="fl">Тип заявки</label>' +
        '<select class="fc" onchange="state.detailFilter.eventType=this.value;state.detailPage=1;renderDetailTablePaged()">' +
        etOpts + '</select></div>' +
        '<div class="col-sm-3 col-md-2">' +
        '<label class="fl">Статус</label>' +
        '<select class="fc" onchange="state.detailFilter.status=this.value;state.detailPage=1;renderDetailTablePaged()">' +
        statusOpts + '</select></div>' +
        '<div class="col-sm-2 col-md-2">' +
        '<label class="fl">Дата от</label>' +
        '<input type="date" class="fc" ' +
        'value="' + escapeHtml(state.detailFilter.dateFrom) + '" ' +
        'onchange="state.detailFilter.dateFrom=this.value;state.detailPage=1;renderDetailTablePaged()">' +
        '</div>' +
        '<div class="col-sm-2 col-md-2">' +
        '<label class="fl">Дата до</label>' +
        '<input type="date" class="fc" ' +
        'value="' + escapeHtml(state.detailFilter.dateTo) + '" ' +
        'onchange="state.detailFilter.dateTo=this.value;state.detailPage=1;renderDetailTablePaged()">' +
        '</div>' +
        '<div class="col-auto d-flex align-items-end gap-2">' +
        '<button class="btn-sec" onclick="exportDetailCSV()"><i class="bi bi-download"></i>CSV</button>' +
        '<button class="btn-sec" onclick="state.detailFilter={search:\'\',status:\'\',dateFrom:\'\',dateTo:\'\',eventType:\'\',};state.detailPage=1;renderDetailTablePaged()">' +
        '<i class="bi bi-arrow-counterclockwise"></i></button>' +
        '<span id="detail-count" style="font-size:12px;color:var(--muted);line-height:38px"></span>' +
        '</div>' +
        '</div></div>';
}

function _filterDetailRows() {
    var s = state.detailFilter.search.toLowerCase();
    var st = state.detailFilter.status;
    var et = state.detailFilter.eventType;
    var dfr = state.detailFilter.dateFrom;
    var dto = state.detailFilter.dateTo;
    return state.allDetailRows.filter(function (row) {
        if (st && row.status_key !== st) return false;
        if (et && row.event_type_key !== et) return false;
        if (dfr && row.date < dfr) return false;
        if (dto && row.date > dto) return false;
        if (s) {
            var src = [row.date, row.event_type, row.status, row.comment, row.room || '']
                .filter(Boolean).join(' ').toLowerCase();
            if (src.indexOf(s) === -1) return false;
        }
        return true;
    });
}

window.renderDetailTablePaged = function () {
    var filterWrap = byId('detail-filter-wrap');
    if (filterWrap) filterWrap.innerHTML = _buildDetailFilterBar();

    var filtered = _filterDetailRows();
    var total = filtered.length;
    var pages = Math.ceil(total / state.PAGE_SIZE) || 1;
    if (state.detailPage > pages) state.detailPage = 1;

    var page = filtered.slice((state.detailPage - 1) * state.PAGE_SIZE, state.detailPage * state.PAGE_SIZE);
    var isEq = state.currentResource && state.currentResource.kind === 'equipment';
    var cols = isEq ? 8 : 7;

    var head = byId('resourceTblHead');
    var body = byId('resourceTblBody');

    head.innerHTML = '<tr><th>Дата</th><th>Время</th><th>Тип события</th>' +
        (isEq ? '<th>Аудитория</th>' : '') +
        '<th>Участников</th><th>Статус</th><th>Часов</th><th>Комментарий</th></tr>';

    body.innerHTML = page.length
        ? page.map(function (row) {
            return '<tr class="rep-link-row" onclick="window.location.href=\'/bookings/' + row.id + '\'">' +
                '<td>' + fmtDate(row.date) + '</td>' +
                '<td>' + escapeHtml((row.start || '') + ' – ' + (row.end || '')) + '</td>' +
                '<td class="rep-sub">' + escapeHtml(row.event_type || '') + '</td>' +
                (isEq ? '<td class="rep-sub">' + escapeHtml(row.room || '') + '</td>' : '') +
                '<td>' + (row.participants ?? 0) + '</td>' +
                '<td class="rep-sub">' + escapeHtml(row.status || '') + '</td>' +
                '<td>' + (row.hours ?? 0) + ' ч</td>' +
                '<td class="rep-sub" style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" ' +
                'title="' + escapeHtml(row.comment || '') + '">' +
                escapeHtml(row.comment || '') + '</td></tr>';
        }).join('')
        : _emptyRow(cols, 'Нет данных', 'bi-inboxes');

    var pager = byId('detail-pagination');
    if (pager) pager.innerHTML = _buildPager(state.detailPage, pages, 'goDetailPage');

    var countEl = byId('detail-count');
    if (countEl) countEl.textContent = total + ' записей';
};

window.goDetailPage = function (p) {
    state.detailPage = p;
    renderDetailTablePaged();
};

/* ══════════════════════════════════════════════════════════
   PAGINATION
══════════════════════════════════════════════════════════ */
function _buildPager(current, total, fn) {
    if (total <= 1) return '';
    var html = '<div class="pager"><span class="pager-i">Страница ' + current + ' из ' + total + '</span>' +
        '<div class="pagination-buttons">';

    if (current > 1) html += '<button class="pg-btn" onclick="' + fn + '(' + (current - 1) + ')"><i class="bi bi-chevron-left"></i></button>';
    else html += '<button class="pg-btn" disabled><i class="bi bi-chevron-left"></i></button>';

    var from = Math.max(1, current - 2);
    var to = Math.min(total, current + 2);
    for (var p = from; p <= to; p++) {
        if (p === current) html += '<button class="pg-btn active">' + p + '</button>';
        else html += '<button class="pg-btn" onclick="' + fn + '(' + p + ')">' + p + '</button>';
    }

    if (current < total) html += '<button class="pg-btn" onclick="' + fn + '(' + (current + 1) + ')"><i class="bi bi-chevron-right"></i></button>';
    else html += '<button class="pg-btn" disabled><i class="bi bi-chevron-right"></i></button>';

    return html + '</div></div>';
}

/* ══════════════════════════════════════════════════════════
   CHARTS
══════════════════════════════════════════════════════════ */
function _pieConfig(data) {
    var hoursVals = data.pie_hours_values || data.pie_values || [];
    var countsVals = data.pie_counts_values || [];
    return {
        type: 'doughnut',
        data: {
            labels: data.pie_labels || [],
            datasets: [{data: hoursVals, _counts: countsVals}]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {position: 'bottom'},
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            var h = ctx.raw ?? 0;
                            var n = (ctx.dataset._counts || [])[ctx.dataIndex];
                            return ' ' + h + ' ч' + (n != null ? ' (' + n + ' заявок)' : '');
                        }
                    }
                },
                subtitle: {display: true, text: 'Часы занятости по типам мероприятий', padding: {bottom: 6}}
            }
        }
    };
}

function _hourLabels() {
    var arr = [];
    for (var h = 0; h < 24; h++) arr.push(String(h).padStart(2, '0') + ':00');
    return arr;
}

function renderOverviewCharts(data) {
    destroyChart('overviewTrend');
    destroyChart('overviewPie');
    destroyChart('overviewSecondary');

    state.charts.overviewTrend = new Chart(byId('overviewTrendChart'), {
        type: 'line',
        data: {
            labels: (data.trend_labels || []).map(fmtDate),
            datasets: [{label: 'Часов занятости', data: data.trend_values || [], tension: 0.35}]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {display: false},
                subtitle: {display: true, text: 'Суммарные часы занятости всех ресурсов по дням', padding: {bottom: 6}}
            },
            scales: {y: {beginAtZero: true, title: {display: true, text: 'Часы'}}}
        }
    });

    state.charts.overviewPie = new Chart(byId('overviewPieChart'), _pieConfig(data));

    state.charts.overviewSecondary = new Chart(byId('overviewSecondaryChart'), {
        type: 'bar',
        data: {
            labels: _hourLabels(),
            datasets: [{label: 'Часов', data: data.hour_distribution || [], barPercentage: 0.85}]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {display: false},
                subtitle: {
                    display: true,
                    text: 'Распределение часов заявок по часам дня (суммарно за период)',
                    padding: {bottom: 6}
                }
            },
            scales: {
                y: {beginAtZero: true, title: {display: true, text: 'Часы'}},
                x: {title: {display: true, text: 'Час дня'}}
            }
        }
    });
}

function renderResourceCharts(data) {
    destroyChart('resourceTrend');
    destroyChart('resourcePie');
    destroyChart('resourceCapacity');
    destroyChart('resourceSecondary');

    state.charts.resourceTrend = new Chart(byId('resourceTrendChart'), {
        type: 'line',
        data: {
            labels: (data.trend_labels || []).map(fmtDate),
            datasets: [{label: 'Часов', data: data.trend_values || [], tension: 0.35}]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {display: false},
                subtitle: {display: true, text: 'Суммарные часы использования ресурса по дням', padding: {bottom: 6}}
            },
            scales: {y: {beginAtZero: true, title: {display: true, text: 'Часы'}}}
        }
    });

    state.charts.resourcePie = new Chart(byId('resourcePieChart'), _pieConfig(data));

    if (state.currentResource && state.currentResource.kind === 'rooms') {
        byId('resourceCapacityCol').style.display = '';

        var capData = data.capacity_compare || [];
        var capLabels = capData.map(function (x) {
            var parts = (x.label || '').split(' ');
            return fmtDate(parts[0]) + (parts[1] ? ' ' + parts[1] : '');
        });

        // Растягиваем canvas по ширине для многих точек — скролл обеспечивает HTML
        var canvas = byId('resourceCapacityChart');
        var wrapEl = canvas.parentNode;
        var minWidth = Math.max(wrapEl.offsetWidth || 600, capData.length * 40);
        canvas.width = minWidth;
        canvas.style.width = minWidth + 'px';
        // Высота пропорционально количеству точек, но не меньше 300px
        var dynHeight = Math.max(300, Math.min(500, capData.length * 6));
        canvas.height = dynHeight;
        canvas.style.height = dynHeight + 'px';

        state.charts.resourceCapacity = new Chart(byId('resourceCapacityChart'), {
            type: 'bar',
            data: {
                labels: capLabels,
                datasets: [
                    {
                        label: 'Участники',
                        data: capData.map(function (x) {
                            return x.participants;
                        }),
                        barPercentage: 0.6
                    },
                    {
                        label: 'Вместимость',
                        data: capData.map(function (x) {
                            return x.capacity;
                        }),
                        type: 'line',          // линия поверх столбцов — всегда видна
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {position: 'bottom'},
                    subtitle: {
                        display: true,
                        text: 'Фактическое число участников (столбцы) vs вместимость (линия)',
                        padding: {bottom: 6}
                    }
                },
                scales: {
                    y: {beginAtZero: true, title: {display: true, text: 'Чел.'}},
                    x: {ticks: {maxRotation: 45, font: {size: 10}}}
                }
            }
        });
    } else {
        byId('resourceCapacityCol').style.display = 'none';
    }

    state.charts.resourceSecondary = new Chart(byId('resourceSecondaryChart'), {
        type: 'bar',
        data: {
            labels: data.hour_labels || _hourLabels(),
            datasets: [{label: 'Часов', data: data.hour_values || [], barPercentage: 0.85}]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {display: false},
                subtitle: {display: true, text: 'Распределение часов заявок по часам дня', padding: {bottom: 6}}
            },
            scales: {
                y: {beginAtZero: true, title: {display: true, text: 'Часы'}},
                x: {title: {display: true, text: 'Час дня'}}
            }
        }
    });
}

function destroyChart(key) {
    if (state.charts[key]) {
        state.charts[key].destroy();
        state.charts[key] = null;
    }
}

function destroyCharts() {
    Object.keys(state.charts).forEach(destroyChart);
}

/* ══════════════════════════════════════════════════════════
   HEATMAP
══════════════════════════════════════════════════════════ */
function renderHeatmap(containerId, days, hours, matrix) {
    var container = byId(containerId);
    if (!container) return;
    if (!matrix || !matrix.length) {
        container.innerHTML = _emptyDiv('Нет данных', 'bi-inboxes');
        return;
    }

    var max = 0;
    matrix.forEach(function (row) {
        row.forEach(function (v) {
            if (v > max) max = v;
        });
    });
    if (!max) max = 1;

    // Инфо-строка остается вне скролла
    var infoHtml = '<div style="font-size:11px;color:var(--muted);margin-bottom:8px">' +
        '<i class="bi bi-info-circle"></i> ' +
        'Значение — средний % времени, когда ресурс занят в данный день недели и час. ' +
        '<strong>100%</strong> = занят каждый такой день периода весь час. ' +
        '</div>';

    // Сама сетка внутри скролл-контейнера
    var gridHtml = '<div class="heatmap-scroll-container">' +
        '<div class="heatmap-grid">' +
        '<div class="heatmap-head"></div>';

    for (var h = 0; h < hours.length; h++) {
        gridHtml += '<div class="heatmap-head">' + String(hours[h]).padStart(2, '0') + '</div>';
    }
    for (var d = 0; d < days.length; d++) {
        gridHtml += '<div class="heatmap-label">' + escapeHtml(days[d]) + '</div>';
        for (var hh = 0; hh < 24; hh++) {
            var value = (matrix[d] && matrix[d][hh]) ? matrix[d][hh] : 0;
            var alpha = Math.max(0.06, Math.min(value / max, 1));
            gridHtml += '<div class="heatmap-cell" title="' + escapeHtml(days[d]) + ' ' + hh +
                ':00 — ' + value + '%" style="background:rgba(30,75,163,' + alpha + ')">' +
                (value ? value : '') + '</div>';
        }
    }
    gridHtml += '</div></div>';

    container.innerHTML = infoHtml + gridHtml;
}

/* ══════════════════════════════════════════════════════════
   EXPORT (client-side CSV)
══════════════════════════════════════════════════════════ */
function _downloadCSV(rows, filename) {
    var blob = new Blob(['\uFEFF' + rows.join('\n')], {type: 'text/csv;charset=utf-8'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function _csvRow(vals) {
    return vals.map(function (v) {
        return '"' + String(v ?? '').replace(/"/g, '""') + '"';
    }).join(',');
}

window.exportOverviewCSV = function () {
    var items = _filterOverviewItems();
    var df = byId('date_from').value, dt = byId('date_to').value;
    var rows, filename;
    if (state.type === 'rooms') {
        rows = [_csvRow(['Аудитория', 'Корпус', 'Этаж', 'Тип', 'Статус', 'Заявок', 'Отмен', 'Часов', 'Загрузка %', 'Пик'])].concat(
            items.map(function (i) {
                return _csvRow([i.name, i.building, i.floor, i.type, i.status,
                    i.bookings_count, i.canceled_count, i.total_hours, i.load_pct, fmtDate(i.peak_day)]);
            }));
        filename = 'rooms_' + df + '_' + dt + '.csv';
    } else {
        rows = [_csvRow(['Инв.номер', 'Наименование', 'Модель', 'Тип', 'Статус', 'Место', 'Заявок', 'Отмен', 'Часов', 'Загрузка %'])].concat(
            items.map(function (i) {
                return _csvRow([i.inventory_number, i.name, i.model, i.type, i.status,
                    i.room, i.bookings_count, i.canceled_count, i.total_hours, i.load_pct]);
            }));
        filename = 'equipment_' + df + '_' + dt + '.csv';
    }
    _downloadCSV(rows, filename);
};

window.exportDetailCSV = function () {
    var rows_data = _filterDetailRows();
    var df = byId('date_from').value, dt = byId('date_to').value;
    var name = (state.currentResource && state.currentResource.label) || 'resource';
    var isEq = state.currentResource && state.currentResource.kind === 'equipment';
    var hdr = ['Дата', 'Начало', 'Конец', 'Тип события'];
    if (isEq) hdr.push('Аудитория');
    hdr = hdr.concat(['Участников', 'Статус', 'Часов', 'Комментарий']);

    var rows = [_csvRow(hdr)].concat(rows_data.map(function (r) {
        var arr = [fmtDate(r.date), r.start, r.end, r.event_type];
        if (isEq) arr.push(r.room || '');
        return _csvRow(arr.concat([r.participants, r.status, r.hours, r.comment || '']));
    }));
    _downloadCSV(rows, name.replace(/[\s\/]/g, '_') + '_' + df + '_' + dt + '.csv');
};

/* ══════════════════════════════════════════════════════════
   SEARCH
══════════════════════════════════════════════════════════ */
function searchResources() {
    var q = (byId('resourceSearchInput').value || '').trim();
    clearTimeout(state.searchTimer);
    if (!q) {
        clearSearchResults();
        return;
    }
    state.searchTimer = setTimeout(function () {
        fetch(buildUrl('/api/reports/search/', {type: state.type, q: q}), {credentials: 'same-origin'})
            .then(function (r) {
                return r.json();
            })
            .then(function (d) {
                renderSearchResults(d.items || []);
            })
            .catch(clearSearchResults);
    }, 250);
}

function renderSearchResults(items) {
    var box = byId('resourceSearchResults');
    box.style.display = '';
    if (!items.length) {
        box.innerHTML = '<div class="rep-search-item"><div class="rep-search-item-label">Ничего не найдено</div></div>';
        return;
    }
    box.innerHTML = items.map(function (item) {
        return '<div class="rep-search-item" onclick="pickResource(' + item.id + ',\'' +
            escapeJs(item.kind) + '\',\'' + escapeJs(item.label || '') + '\',\'' +
            escapeJs(item.subtitle || '') + '\')">' +
            '<div class="rep-search-item-label">' + escapeHtml(item.label || '') + '</div>' +
            '<div class="rep-search-item-sub">' + escapeHtml(item.subtitle || '') + '</div></div>';
    }).join('');
}

function clearSearchResults() {
    var box = byId('resourceSearchResults');
    if (box) {
        box.style.display = 'none';
        box.innerHTML = '';
    }
}

function pickResource(id, kind, label, subtitle) {
    state.currentResource = {id: id, kind: kind, label: label, subtitle: subtitle};
    byId('selectedResourceChip').style.display = '';
    byId('selectedResourceChip').textContent = label || '';
    byId('resourceSearchInput').value = label || '';
    clearSearchResults();
    _pushHistory();
    loadReport();
}

function openResource(id, kind, label) {
    state.currentResource = {id: id, kind: kind, label: label};
    byId('selectedResourceChip').style.display = '';
    byId('selectedResourceChip').textContent = label || '';
    byId('resourceSearchInput').value = label || '';
    clearSearchResults();
    selectMode('resource');
}

function clearResource(skipLoad) {
    state.currentResource = null;
    byId('selectedResourceChip').style.display = 'none';
    byId('selectedResourceChip').textContent = '';
    byId('resourceTitle').textContent = 'Ресурс не выбран';
    byId('resourceSubtitle').textContent = 'Выберите объект через поиск сверху';
    byId('resourceStatusChip').textContent = 'Статус';
    byId('resourceMetaChip').textContent = 'Метаданные';
    byId('resourceSearchInput').value = '';
    byId('roomEquipmentBlock').style.display = 'none';
    var linkEl = byId('resourcePageLink');
    if (linkEl) linkEl.style.display = 'none';
    if (!skipLoad && state.mode === 'resource') renderEmptyResourceState();
}

/* ══════════════════════════════════════════════════════════
   ROOM EQUIPMENT TABLE
══════════════════════════════════════════════════════════ */
function loadRoomEquipmentTableSelected() {
    if (!state.currentResource || state.currentResource.kind !== 'rooms') return;
    var dateVal = byId('room_equipment_date').value;
    var timeVal = byId('room_equipment_time').value;
    if (!dateVal || !timeVal) return;

    fetch(buildUrl('/api/reports/room/' + encodeURIComponent(state.currentResource.id) + '/equipment/',
        {date: dateVal, time: timeVal}), {credentials: 'same-origin'})
        .then(function (r) {
            return r.json();
        })
        .then(function (data) {
            var head = byId('roomEquipmentHead');
            var body = byId('roomEquipmentBody');
            head.innerHTML = '<tr><th>Инв. номер</th><th>Наименование</th><th>Модель</th><th>Статус</th><th>Местоположение</th></tr>';
            if (!data.items || !data.items.length) {
                body.innerHTML = _emptyRow(5, 'Нет техники', 'bi-inboxes');
                return;
            }
            body.innerHTML = data.items.map(function (item) {
                return '<tr class="rep-link-row" onclick="window.location.href=\'/equipment/' + item.id + '\'">' +
                    '<td><code class="rep-table__mono">' + escapeHtml(item.inventory_number || '') + '</code></td>' +
                    '<td class="rep-name">' + escapeHtml(item.name || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.model || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.status || '') + '</td>' +
                    '<td class="rep-sub">' + escapeHtml(item.location_label || '') + '</td></tr>';
            }).join('');
        })
        .catch(function () {
            byId('roomEquipmentBody').innerHTML = _emptyRow(5, 'Ошибка загрузки', 'bi-exclamation-triangle');
        });
}

window.exportReportPDF = function () {
    var df = byId('date_from').value;
    var dt = byId('date_to').value;

    if (!df || !dt) {
        alert('Укажите период');
        return;
    }

    if (!window.REPORTS_EXPORT_PDF_URL) {
        alert('Не задан URL экспорта PDF');
        return;
    }

    var params = {
        date_from: df,
        date_to: dt,
        type: state.type,
        mode: state.mode
    };

    if (state.mode === 'resource') {
        if (!state.currentResource) {
            alert('Выберите ресурс');
            return;
        }
        params.resource_type = state.currentResource.kind;
        params.resource_id = state.currentResource.id;
    }

    window.location.href = buildUrl(window.REPORTS_EXPORT_PDF_URL, params);
};

/* ══════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', function () {
    byId('resourceSearchInput').addEventListener('input', searchResources);
    byId('resourceSearchInput').addEventListener('focus', function () {
        if ((this.value || '').trim()) searchResources();
    });
    document.addEventListener('click', function (e) {
        var panel = byId('resourceSearchPanel');
        if (panel && !panel.contains(e.target)) clearSearchResults();
    });

    // Записать начальное состояние в history (чтобы первый popstate работал корректно)
    history.replaceState({mode: 'overview', type: 'rooms', resource: null}, '');

    selectMode('overview');
    loadReport();
});

