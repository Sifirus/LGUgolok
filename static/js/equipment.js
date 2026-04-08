function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('open');
    document.body.style.overflow = '';
}

function closeAllModals() {
    document.querySelectorAll('.modal-backdrop.open').forEach(function (modal) {
        modal.classList.remove('open');
    });
    document.body.style.overflow = '';
}

function confirmEquipmentDelete(id, name) {
    if (confirm('Удалить оборудование "' + name + '"?')) {
        const form = document.getElementById('delete-form-' + id);
        if (form) form.submit();
    }
}

function setRoomValue(root, id, label) {
    const hidden = root.querySelector('[data-room-id]');
    const input = root.querySelector('.room-lookup__input');
    if (hidden) hidden.value = id || '';
    if (input) input.value = label || '';
}

function renderRoomMenu(root, items) {
    const menu = root.querySelector('[data-room-menu]');
    if (!menu) return;

    if (!items.length) {
        menu.innerHTML = '<div class="room-lookup__empty">Ничего не найдено</div>';
        menu.classList.add('open');
        return;
    }

    menu.innerHTML = items.map(function (item) {
        return (
            '<button type="button" class="room-lookup__item" ' +
            'data-room-item="' + item.id + '" ' +
            'data-room-label="' + item.label.replace(/"/g, '&quot;') + '">' +
            '<div class="room-lookup__item-title">' + item.label + '</div>' +
            '</button>'
        );
    }).join('');

    menu.classList.add('open');
}

function initRoomLookup(root) {
    const url = root.getAttribute('data-room-url');
    const input = root.querySelector('.room-lookup__input');
    const hidden = root.querySelector('[data-room-id]');
    const menu = root.querySelector('[data-room-menu]');
    const clearBtn = root.querySelector('[data-room-clear]');
    let timer = null;

    function closeMenu() {
        if (menu) menu.classList.remove('open');
    }

    function searchRooms(query) {
        if (!url) return;
        fetch(url + '?q=' + encodeURIComponent(query))
            .then(resp => resp.json())
            .then(items => renderRoomMenu(root, items))
            .catch(() => {
                if (menu) {
                    menu.innerHTML = '<div class="room-lookup__empty">Ошибка поиска</div>';
                    menu.classList.add('open');
                }
            });
    }

    if (input) {
        input.addEventListener('input', function () {
            const value = input.value.trim();
            if (hidden) hidden.value = '';

            clearTimeout(timer);
            if (!value) {
                closeMenu();
                return;
            }

            timer = setTimeout(function () {
                searchRooms(value);
            }, 180);
        });

        input.addEventListener('focus', function () {
            const value = input.value.trim();
            if (value) {
                searchRooms(value);
            }
        });
    }

    if (menu) {
        menu.addEventListener('click', function (e) {
            const item = e.target.closest('[data-room-item]');
            if (!item) return;

            const roomId = item.getAttribute('data-room-item');
            const roomLabel = item.getAttribute('data-room-label') || '';
            setRoomValue(root, roomId, roomLabel);
            closeMenu();
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            setRoomValue(root, '', '');
            closeMenu();
            if (input) input.focus();
        });
    }

    document.addEventListener('click', function (e) {
        if (!root.contains(e.target)) {
            closeMenu();
        }
    });
}

function openEquipmentEdit(button) {
    const id = button.getAttribute('data-equipment-id');
    const modal = document.getElementById('modal-edit-' + id);
    if (!modal) return;

    const form = modal.querySelector('form');
    if (form) {
        form.setAttribute('action', button.getAttribute('data-action'));

        const setVal = function (name, value) {
            const el = form.querySelector('[name="' + name + '"]');
            if (el) el.value = value || '';
        };

        setVal('inventory_number', button.getAttribute('data-inventory-number'));
        setVal('name', button.getAttribute('data-name'));
        setVal('model', button.getAttribute('data-model'));
        setVal('type', button.getAttribute('data-type'));
        setVal('status', button.getAttribute('data-status'));
        setVal('room_id', button.getAttribute('data-room-id'));
        setVal('room_query', button.getAttribute('data-room-label'));

        const stationary = form.querySelector('[name="is_stationary"]');
        if (stationary) stationary.checked = button.getAttribute('data-is-stationary') === '1';

        const lookup = form.querySelector('[data-room-lookup]');
        if (lookup) {
            const hidden = lookup.querySelector('[data-room-id]');
            const input = lookup.querySelector('.room-lookup__input');
            if (hidden) hidden.value = button.getAttribute('data-room-id') || '';
            if (input) input.value = button.getAttribute('data-room-label') || '';
        }
    }

    openModal('modal-edit-' + id);
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-room-lookup]').forEach(initRoomLookup);

    const addFlag = document.getElementById('open-add-modal-flag');
    if (addFlag) openModal('modal-add');

    const editFlag = document.getElementById('open-edit-modal-flag');
    if (editFlag) {
        const equipmentId = editFlag.getAttribute('data-equipment-id');
        if (equipmentId) openModal('modal-edit-' + equipmentId);
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeAllModals();
    });
});