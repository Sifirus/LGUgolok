from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.shortcuts import reverse

from users.models import User

VALID_ROLES = [role.value for role in User.Roles]


def require_role_decorator(roles: list):
    for role in roles:
        if role not in VALID_ROLES:
            raise ValueError('Invalid role')
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('login'))
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return wrapper
    return decorator
