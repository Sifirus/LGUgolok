function normalizeText(value) {
    return String(value ?? '').replace(/\s+/g, ' ').trim().toLowerCase();
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

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal-backdrop.open, .modal-ugolok-backdrop.open');
    modals.forEach(modal => {
        modal.classList.remove('open');
    });
    document.body.style.overflow = '';
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeAllModals();
    }
});