from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from admin_panel.forms import AddUserForm
from core.decorators import require_role_decorator

from admin_panel.utils import send_new_user_email

user_model = get_user_model()


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_users(request):
    users = user_model.objects.all()
    return render(request, 'admin_panel/users.html', {'users': users})


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_users_add(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            temp_password = get_user_model().objects.make_random_password()

            user = get_user_model().objects.create_user(
                email=form.cleaned_data['email'],
                role=form.cleaned_data['role'],
                password=temp_password,

            )

            profile = user.profile
            profile.first_name = form.cleaned_data['first_name']
            profile.last_name = form.cleaned_data['last_name']
            profile.department = form.cleaned_data['department']
            profile.save()

            send_new_user_email(email=form.cleaned_data['email'], temp_password=temp_password)  # TODO Сделать с письмом

            return redirect('admin_panel_users')

        return render(request, 'admin_panel/user_add.html', {'form': form})

    form = AddUserForm()
    return render(request, 'admin_panel/user_add.html', {'form': form})


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_detail(request, user_id):
    pass


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_edit(request, user_id):
    pass


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_delete(request, user_id):
    pass


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_ban(request, user_id):
    pass
