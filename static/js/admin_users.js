function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

document.querySelectorAll('.modal-lgu-backdrop').forEach(function (backdrop) {
    backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) closeModal(backdrop.id);
    });
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-lgu-backdrop.open').forEach(function (m) {
            closeModal(m.id);
        });
    }
});

function openEditModal(userId, email, firstName, lastName, secondName, department, role) {
    var form = document.getElementById('edit-form-' + userId);
    if (!form) return;

    setVal(form, 'email', email);
    setVal(form, 'first_name', firstName);
    setVal(form, 'last_name', lastName);
    setVal(form, 'second_name', secondName || '');
    setVal(form, 'department', department || '');
    setVal(form, 'role', role);

    openModal('modal-edit-' + userId);
}

function setVal(form, name, value) {
    var el = form.querySelector('[name="' + name + '"]');
    if (el) el.value = value;
}

function confirmDelete(userId, email) {
    if (confirm('Деактивировать пользователя ' + email + '?\nВход будет заблокирован, данные сохранятся.')) {
        document.getElementById('delete-form-' + userId).submit();
    }
}

document.addEventListener('DOMContentLoaded', function () {
    var addFlag = document.getElementById('open-add-modal-flag');
    if (addFlag) openModal('modal-add');

    var editFlag = document.getElementById('open-edit-modal-flag');
    if (editFlag) {
        var uid = editFlag.dataset.userId;
        openModal('modal-edit-' + uid);
    }
});