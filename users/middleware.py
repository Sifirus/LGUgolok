from django.contrib import messages
from django.shortcuts import redirect, reverse


class MustChangePasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if getattr(request.user, 'must_change_password', False):
                if request.path not in [reverse('profile'), reverse('logout')]:
                    messages.warning(request, 'Пожалуйста, измените временный пароль')
                    return redirect('profile')

        response = self.get_response(request)

        return response
