function initLookup(root) {
    const url = root.getAttribute('data-url');
    const input = root.querySelector('.lookup-input');
    const hidden = root.querySelector('[data-id]');
    const menu = root.querySelector('[data-menu]');
    const clearBtn = root.querySelector('[data-clear]');
    let timer = null;

    function closeMenu() {
        if (menu) menu.classList.remove('open');
    }

    function render(items) {
        if (!menu) return;

        if (!items.length) {
            menu.innerHTML = '<div class="lookup-empty">Ничего не найдено</div>';
            menu.classList.add('open');
            return;
        }

        menu.innerHTML = items.map(function (item) {
            return (
                '<button type="button" class="lookup-item" data-item="' + item.id + '" data-label="' + item.label.replace(/"/g, '&quot;') + '">' +
                '<div class="lookup-item-title">' + item.label + '</div>' +
                '</button>'
            );
        }).join('');

        menu.classList.add('open');
    }

    function search(q) {
        fetch(url + '?q=' + encodeURIComponent(q))
            .then(resp => resp.json())
            .then(render)
            .catch(() => {
                if (menu) {
                    menu.innerHTML = '<div class="lookup-empty">Ошибка поиска</div>';
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
                search(value);
            }, 180);
        });

        input.addEventListener('focus', function () {
            const value = input.value.trim();
            if (value) search(value);
        });
    }

    if (menu) {
        menu.addEventListener('click', function (e) {
            const item = e.target.closest('[data-item]');
            if (!item) return;

            if (hidden) hidden.value = item.getAttribute('data-item') || '';
            if (input) input.value = item.getAttribute('data-label') || '';
            closeMenu();
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            if (hidden) hidden.value = '';
            if (input) input.value = '';
            closeMenu();
            input.focus();
        });
    }

    document.addEventListener('click', function (e) {
        if (!root.contains(e.target)) closeMenu();
    });
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-lookup]').forEach(initLookup);
});