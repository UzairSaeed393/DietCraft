from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from users.models import UserProfile


def profile_required(view_func=None, login_url=None, redirect_field_name='next'):
    """Decorator for views that requires the user to have a completed UserProfile.

    Usage:
      @profile_required
      def my_view(request):
          ...

    or with parameters:
      @profile_required(login_url='/auth/login/')
      def my_view(request):
          ...
    """

    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url or settings.LOGIN_URL, redirect_field_name)

            # Check if profile exists
            try:
                has_profile = UserProfile.objects.filter(user=request.user).exists()
            except Exception:
                has_profile = False

            if not has_profile:
                return redirect('profileform')

            return view(request, *args, **kwargs)

        return _wrapped_view

    if view_func:
        return decorator(view_func)

    return decorator
