function confirmBookingCancel(bookingId) {
    if (confirm('Отменить заявку #' + bookingId + '?')) {
        const form = document.querySelector('form[action*="/cancel/"]');
        if (form) form.submit();
    }
}