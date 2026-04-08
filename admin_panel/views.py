from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q

from admin_panel.forms import AddUserForm
from core.decorators import require_role_decorator
from admin_panel.utils import send_new_user_email

User = get_user_model()


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_users(request):
    qs = User.objects.select_related('profile').order_by(
        '-is_active', 'is_blocked', '-created_at'
    )

    search = request.GET.get('search', '').strip()
    role   = request.GET.get('role', '')
    status = request.GET.get('status', '')

    if search:
        qs = qs.filter(
            Q(email__icontains=search) |
            Q(profile__first_name__icontains=search) |
            Q(profile__last_name__icontains=search)
        )

    if role:
        qs = qs.filter(role=role)

    if status == 'active':
        qs = qs.filter(is_active=True, is_blocked=False)
    elif status == 'blocked':
        qs = qs.filter(is_blocked=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    paginator = Paginator(qs, 10)
    page      = request.GET.get('page', 1)
    users     = paginator.get_page(page)

    add_form  = AddUserForm()

    context = {
        'users':      users,
        'add_form':   add_form,
        'roles':      User.Roles.choices,
        'search':     search,
        'filter_role':   role,
        'filter_status': status,
        'total':      paginator.count,
    }
    return render(request, 'admin_panel/users.html', context)


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_users_add(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            temp_password = User.objects.make_random_password()

            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                role=form.cleaned_data['role'],
                password=temp_password,
            )
            profile = user.profile
            profile.first_name  = form.cleaned_data['first_name']
            profile.last_name   = form.cleaned_data['last_name']
            profile.second_name = form.cleaned_data.get('second_name', '')
            profile.department  = form.cleaned_data.get('department', '')
            profile.save()

            send_new_user_email(
                email=form.cleaned_data['email'],
                temp_password=temp_password
            )
            messages.success(request, f'Пользователь {user.email} создан, письмо отправлено')
            return redirect('admin_panel_users')

        qs    = User.objects.select_related('profile').order_by('-created_at')
        users = Paginator(qs, 15).get_page(1)
        return render(request, 'admin_panel/users.html', {
            'users':    users,
            'add_form': form,
            'open_add_modal': True,
            'roles':  User.Roles.choices,
            'total':  qs.count(),
        })

    return redirect('admin_panel_users')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_detail(request, user_id):
    user = get_object_or_404(User.objects.select_related('profile'), pk=user_id)
    return render(request, 'admin_panel/user_detail.html', {'target_user': user})


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_edit(request, user_id):
    user = get_object_or_404(User.objects.select_related('profile'), pk=user_id)

    if request.method == 'POST':
        form = AddUserForm(request.POST, instance=user)  # Reusing AddUserForm with instance for edit
        if form.is_valid():
            cd = form.cleaned_data

            user.email = cd['email']
            user.role  = cd['role']
            user.save(update_fields=['email', 'role'])

            profile = user.profile
            profile.first_name  = cd['first_name']
            profile.last_name   = cd['last_name']
            profile.second_name = cd.get('second_name', '')
            profile.department  = cd.get('department', '')
            profile.save()

            messages.success(request, f'Пользователь {user.email} обновлён')
            return redirect('admin_panel_users')

        qs    = User.objects.select_related('profile').order_by('-created_at')
        users = Paginator(qs, 15).get_page(1)
        return render(request, 'admin_panel/users.html', {
            'users':          users,
            'add_form':       AddUserForm(),
            'edit_form':      form,  # Now using AddUserForm for edit as well
            'edit_user_id':   user_id,
            'open_edit_modal': True,
            'roles':  User.Roles.choices,
            'total':  qs.count(),
        })

    return redirect('admin_panel_users')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_delete(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        if user == request.user:
            messages.error(request, 'Нельзя деактивировать самого себя')
        else:
            user.is_active = False
            user.save(update_fields=['is_active'])
            messages.success(request, f'Пользователь {user.email} деактивирован')
    return redirect('admin_panel_users')


@require_role_decorator(roles=['operator'])
@login_required(login_url='login')
def admin_user_ban_toggle(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        if user == request.user:
            messages.error(request, 'Нельзя заблокировать самого себя')
        elif user.is_blocked:
            user.unblock()
            messages.success(request, f'{user.email} разблокирован')
        else:
            user.block()
            messages.warning(request, f'{user.email} заблокирован')
    return redirect('admin_panel_users')