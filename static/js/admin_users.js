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