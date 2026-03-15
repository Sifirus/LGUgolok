from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from core.decorators import require_role_decorator

user_model = get_user_model()

@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_users(request):
    users = user_model.objects.all()
    return render(request, 'admin_panel/users.html', {'users':users})
