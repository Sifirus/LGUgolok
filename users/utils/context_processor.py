from users.models import Profile


def user_profile_context_processor(request):
    try:
        profile = Profile.objects.get(user=request.user)
        avatar = profile.avatar
        avatar_alt = f'{profile.first_name[0]}{profile.last_name[0]}'
        return {'avatar': avatar, 'avatar_alt': avatar_alt}
    except:
        return {'avatar': None, 'avatar_alt': '??'}
