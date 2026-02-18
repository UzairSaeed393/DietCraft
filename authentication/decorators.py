from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from users.models import UserProfile


def profile_required(view_func=None, login_url=None, redirect_field_name='next'):
    """
    Decorator that requires the user to be authenticated
    AND have a completed UserProfile.
    """

    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url or settings.LOGIN_URL,
                    redirect_field_name
                )

            # Check if profile exists
            has_profile = UserProfile.objects.filter(user=request.user).exists()

            if not has_profile:
                messages.warning(
                    request,
                    "You must complete your profile before accessing this feature."
                )
                return redirect('profileform')

            return view(request, *args, **kwargs)

        return _wrapped_view

    if view_func:
        return decorator(view_func)

    return decorator
