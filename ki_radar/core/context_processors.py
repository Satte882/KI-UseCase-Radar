from ki_radar.accounts.permissions import is_coordinator, is_technical_admin


def navigation_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "nav_is_coordinator": is_coordinator(request.user),
        "nav_is_technical_admin": is_technical_admin(request.user),
    }
