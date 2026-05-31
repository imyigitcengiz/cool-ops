from users.impersonation import get_impersonator, is_impersonating


def impersonation_banner(request):
    if not request.user.is_authenticated or not is_impersonating(request):
        return {
            'impersonation_active': False,
            'impersonation_actor': None,
            'impersonation_target': None,
        }

    actor = get_impersonator(request)
    target = request.user
    return {
        'impersonation_active': True,
        'impersonation_actor': actor,
        'impersonation_target': target,
    }
