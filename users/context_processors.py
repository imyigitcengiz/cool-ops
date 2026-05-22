from .utils import get_or_create_user_profile


def user_profile_card(request):
    user = request.user
    if not user.is_authenticated:
        return {'user_profile_card': None}

    profile = get_or_create_user_profile(user)
    avatar_url = profile.avatar.url if profile.avatar else None
    return {
        'user_profile_card': {
            'display_name': user.display_name,
            'subtitle': profile.subtitle(),
            'role_label': user.role_label,
            'email': user.email or '',
            'phone': profile.phone or '',
            'bio': profile.bio or '',
            'avatar_url': avatar_url,
            'initials': user.initials,
            'username': user.username,
        },
    }
