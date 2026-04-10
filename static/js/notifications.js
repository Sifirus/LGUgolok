(function () {
  'use strict';

  const bell  = document.getElementById('notif-bell-count');
  const dot   = document.getElementById('notif-dot');

  if (!bell && !dot) return;

  function fetchCount() {
    fetch('/api/notifications/count/', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        var count = data.count || 0;

        if (bell) {
          bell.textContent   = count > 0 ? count : '';
          bell.style.display = count > 0 ? 'inline-flex' : 'none';
        }
        if (dot) {
          dot.style.display = count > 0 ? 'block' : 'none';
        }
      })
      .catch(function () {});
  }

  fetchCount();
  setInterval(fetchCount, 30000);
})();


/* Кнопка «Прочитать все» */
(function () {
  var btn = document.getElementById('btn-read-all');
  if (!btn) return;

  btn.addEventListener('click', function () {
    fetch('/notifications/read-all/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        // Визуально помечаем все как прочитанные
        document.querySelectorAll('.notif-item--unread').forEach(function (el) {
          el.classList.remove('notif-item--unread');
        });
        var badge = document.getElementById('notif-bell-count');
        var dot2  = document.getElementById('notif-dot');
        if (badge) { badge.textContent = ''; badge.style.display = 'none'; }
        if (dot2)  { dot2.style.display = 'none'; }
        // Убираем синие точки на странице уведомлений
        document.querySelectorAll('.notif-unread-dot').forEach(function (el) {
          el.style.display = 'none';
        });
      }
    })
    .catch(function () {});
  });
})();


function getCookie(name) {
  var match = document.cookie.match(new RegExp('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)'));
  return match ? decodeURIComponent(match[2]) : '';
}