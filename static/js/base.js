function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function normalizeText(value) {
    return String(value ?? '').replace(/\s+/g, ' ').trim().toLowerCase(); //TODO мусор
}

function getCookie(name) {
    let value = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return value;
}

function formatDate(value) {
    if (!value) return '-';
    const d = new Date(value);
    return d.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

function formatDateTime(value) {
    if (!value) return '';
    const d = new Date(value);
    return d.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function openTopnav() {
    const menu = document.getElementById('topnavMobile');
    const overlay = document.getElementById('topnavOverlay');
    if (!menu || !overlay) return;
    menu.classList.add('open');
    overlay.classList.add('show');
}

function closeTopnav() {
    const menu = document.getElementById('topnavMobile');
    const overlay = document.getElementById('topnavOverlay');
    if (!menu || !overlay) return;
    menu.classList.remove('open');
    overlay.classList.remove('show');
}

function toggleTopnav() {
    const menu = document.getElementById('topnavMobile');
    if (!menu) return;
    if (menu.classList.contains('open')) {
        closeTopnav();
    } else {
        openTopnav();
    }
}

document.addEventListener('click', (event) => {
    const menu = document.getElementById('topnavMobile');
    const burger = document.querySelector('.burger');
    if (!menu || !burger) return;

    if (!menu.contains(event.target) && !burger.contains(event.target)) {
        closeTopnav();
    }
});