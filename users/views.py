from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import UserProfile
from .forms import UserProfileForm


@login_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    # If profile does not exist → no form here
    if not profile:
        return render(request, "users/profile.html", {
            "profile": None
        })

    edit_mode = request.GET.get("edit") == "true"

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "users/profile.html", {
        "profile": profile,
        "form": form,
        "edit_mode": edit_mode
    })

def dashboard(request):
    return render(request, 'users/dashboard.html')
