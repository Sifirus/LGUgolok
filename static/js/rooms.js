function confirmRoomDelete(roomId, roomName) {
    if (confirm('Удалить аудиторию "' + roomName + '"?')) {
        const form = document.getElementById('delete-form-' + roomId);
        if (form) form.submit();
    }
}

function initMultiDropdown(dropdown) {
    const button = dropdown.querySelector('[data-multi-toggle]');
    const panel = dropdown.querySelector('[data-multi-panel]');
    const label = dropdown.querySelector('[data-multi-label]');
    const checkboxes = Array.from(dropdown.querySelectorAll('[data-equipment-checkbox]'));
    const selectAllBtn = dropdown.querySelector('[data-select-all]');
    const clearAllBtn = dropdown.querySelector('[data-clear-all]');

    function updateLabel() {
        const checked = checkboxes.filter(cb => cb.checked);
        if (checked.length === 0) {
            label.textContent = 'Выберите оборудование';
            return;
        }

        if (checked.length === 1) {
            const item = checked[0].closest('label');
            label.textContent = item ? item.innerText.trim() : '1 выбранный пункт';
            return;
        }

        label.textContent = 'Выбрано: ' + checked.length;
    }

    function setOpen(state) {
        dropdown.classList.toggle('open', state);
    }

    button.addEventListener('click', function (e) {
        e.preventDefault();
        setOpen(!dropdown.classList.contains('open'));
    });

    checkboxes.forEach(function (cb) {
        cb.addEventListener('change', updateLabel);
    });

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function () {
            checkboxes.forEach(cb => cb.checked = true);
            updateLabel();
        });
    }

    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function () {
            checkboxes.forEach(cb => cb.checked = false);
            updateLabel();
        });
    }

    document.addEventListener('click', function (e) {
        if (!dropdown.contains(e.target)) {
            setOpen(false);
        }
    });

    updateLabel();
}

document.addEventListener('DOMContentLoaded', function () {
    const addFlag = document.getElementById('open-add-modal-flag');
    if (addFlag) openModal('modal-add');

    const editFlag = document.getElementById('open-edit-modal-flag');
    if (editFlag) {
        const roomId = editFlag.getAttribute('data-room-id');
        if (roomId) openModal('modal-edit-' + roomId);
    }

    document.querySelectorAll('[data-multi-dropdown]').forEach(initMultiDropdown);

});